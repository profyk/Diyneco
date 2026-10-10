"""POPIA data subject requests: export and anonymise a guest, and the retention job."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services import privacy
from tests.api.test_room_service import idem


async def checked_out_guest(factory, owner_engine, hotel) -> dict:
    """A guest with a finished stay, an order with notes and an email in the log."""
    rows = await factory.stay_with_folio(hotel, status="checked_out")
    order_id = await factory.order(hotel, rows["stay_id"])
    async with owner_engine.begin() as conn:
        p = {"h": hotel.id, "g": rows["guest_id"], "s": rows["stay_id"], "o": order_id}
        await conn.execute(
            text(
                "UPDATE app.guests SET email = 'Thandi@Example.com', phone = '+27821234567' "
                "WHERE hotel_id = :h AND id = :g"
            ),
            p,
        )
        await conn.execute(
            text("UPDATE app.stays SET traveller_name = 'Thandi M' WHERE id = :s"),
            p,
        )
        await conn.execute(
            text("UPDATE app.orders SET special_instructions = 'Allergic to nuts' WHERE id = :o"), p
        )
        await conn.execute(text("UPDATE app.order_items SET note = 'No onion' WHERE order_id = :o"), p)
        await conn.execute(
            text(
                "INSERT INTO app.notifications (hotel_id, channel, template, recipient, status) "
                "VALUES (:h, 'email', 'invoice', 'thandi@example.com', 'sent')"
            ),
            p,
        )
    return {**rows, "order_id": order_id}


async def test_export_returns_everything_held_about_the_guest(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    rows = await checked_out_guest(factory, owner_engine, hotel)
    gm = await factory.auth(hotel, "general_manager")
    url = f"/guests/{rows['guest_id']}/export"

    without_step_up = await client.get(url, headers=gm)
    assert without_step_up.status_code == 403, without_step_up.text
    r = await client.get(url, headers=await factory.step_up(hotel, "general_manager", gm))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["guest"]["email"] == "Thandi@Example.com"
    assert body["stays"][0]["traveller_name"] == "Thandi M"
    assert body["orders"][0]["special_instructions"] == "Allergic to nuts"
    assert body["folio_entries"][0]["description"] == "Breakfast"
    assert body["emails"][0]["template"] == "invoice"

    async with owner_engine.connect() as conn:
        audited = (
            await conn.execute(
                text("SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND action = 'guest.export'"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert audited == 1


async def test_only_privacy_managers_can_export_or_anonymise(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    rows = await checked_out_guest(factory, owner_engine, hotel)
    rec = await factory.auth(hotel, "receptionist")
    rec_s = await factory.step_up(hotel, "receptionist", rec)
    assert (await client.get(f"/guests/{rows['guest_id']}/export", headers=rec_s)).status_code == 403
    r = await client.post(
        f"/guests/{rows['guest_id']}/anonymise", json={"reason": "Guest asked"}, headers={**rec_s, **idem()}
    )
    assert r.status_code == 403


async def test_other_hotels_guests_are_not_found(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    other = await factory.hotel(rooms=1)
    rows = await checked_out_guest(factory, owner_engine, other)
    gm = await factory.auth(hotel, "general_manager")
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    assert (await client.get(f"/guests/{rows['guest_id']}/export", headers=gm_s)).status_code == 404
    r = await client.post(
        f"/guests/{rows['guest_id']}/anonymise", json={"reason": "Guest asked"}, headers={**gm_s, **idem()}
    )
    assert r.status_code == 404


async def test_anonymise_clears_personal_data_and_keeps_amounts(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    rows = await checked_out_guest(factory, owner_engine, hotel)
    gm = await factory.auth(hotel, "general_manager")
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    url = f"/guests/{rows['guest_id']}/anonymise"

    no_step_up = await client.post(url, json={"reason": "Guest asked"}, headers={**gm, **idem()})
    assert no_step_up.status_code == 403
    key = idem()
    r = await client.post(url, json={"reason": "Guest asked by email"}, headers={**gm_s, **key})
    assert r.status_code == 200, r.text
    assert r.json() == {"id": str(rows["guest_id"]), "anonymised": True}
    replay = await client.post(url, json={"reason": "Guest asked by email"}, headers={**gm_s, **key})
    assert replay.status_code == 200 and replay.json() == r.json()
    again = await client.post(url, json={"reason": "Guest asked by email"}, headers={**gm_s, **idem()})
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"

    async with owner_engine.connect() as conn:
        p = {"h": hotel.id, "g": rows["guest_id"], "s": rows["stay_id"], "o": rows["order_id"]}
        guest = (await conn.execute(text("SELECT * FROM app.guests WHERE id = :g"), p)).mappings().one()
        assert guest["full_name"] == privacy.ANONYMOUS_NAME
        assert guest["email"] is None and guest["phone"] is None and guest["anonymised_at"] is not None
        stay = (await conn.execute(text("SELECT traveller_name FROM app.stays WHERE id = :s"), p)).one()
        assert stay.traveller_name is None
        order = (
            await conn.execute(text("SELECT special_instructions FROM app.orders WHERE id = :o"), p)
        ).one()
        assert order.special_instructions == privacy.REDACTED
        notes = (
            await conn.execute(text("SELECT note FROM app.order_items WHERE order_id = :o"), p)
        ).scalars()
        assert all(n in (None, privacy.REDACTED) for n in notes)
        recipient = (
            await conn.execute(text("SELECT recipient FROM app.notifications WHERE hotel_id = :h"), p)
        ).scalar_one()
        assert recipient.startswith("sha256:") and "thandi" not in recipient
        amount = (
            await conn.execute(
                text("SELECT amount_minor FROM app.folio_entries WHERE folio_id = :f"),
                {"f": rows["folio_id"]},
            )
        ).scalar_one()
        assert amount == 15000
        audit = (
            await conn.execute(
                text(
                    "SELECT reason, new_value::text FROM app.audit_logs "
                    "WHERE hotel_id = :h AND action = 'guest.anonymise'"
                ),
                p,
            )
        ).one()
    assert audit.reason == "Guest asked by email" and "thandi" not in audit.new_value.lower()


async def test_anonymise_waits_until_the_stay_has_ended(client, factory):
    hotel = await factory.hotel(rooms=1)
    rows = await factory.stay_with_folio(hotel, status="active")
    gm = await factory.auth(hotel, "general_manager")
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    r = await client.post(
        f"/guests/{rows['guest_id']}/anonymise", json={"reason": "Guest asked"}, headers={**gm_s, **idem()}
    )
    assert r.json()["error"]["code"] == "INVALID_TRANSITION", r.text


async def test_retention_job_anonymises_guests_whose_last_stay_is_old(factory, owner_engine, worker_engine):
    hotel = await factory.hotel(rooms=1)
    old = await checked_out_guest(factory, owner_engine, hotel)
    recent = await factory.stay_with_folio(hotel, status="checked_out")
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_settings SET guest_data_retention_days = 365 WHERE hotel_id = :h"),
            {"h": hotel.id},
        )
        await conn.execute(
            text("UPDATE app.stays SET arrival_date = :a, departure_date = :d WHERE id = :s"),
            {
                "a": date.today() - timedelta(days=400),
                "d": date.today() - timedelta(days=398),
                "s": old["stay_id"],
            },
        )

    done = await privacy.run_retention(async_sessionmaker(worker_engine, expire_on_commit=False))
    assert done >= 1
    async with owner_engine.connect() as conn:
        states = dict(
            (
                await conn.execute(
                    text("SELECT id, anonymised_at IS NOT NULL FROM app.guests WHERE hotel_id = :h"),
                    {"h": hotel.id},
                )
            ).all()
        )
    assert states[old["guest_id"]] is True
    assert states[recent["guest_id"]] is False


async def test_id_numbers_are_refused_unless_enabled_and_stored_encrypted(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    body = {"name": "Sipho Dlamini", "id_number": "a1234567"}
    off = await client.post("/guests", json=body, headers={**gm, **idem()})
    assert off.json()["error"]["code"] == "VALIDATION_FAILED", off.text
    assert off.json()["error"]["details"]["fields"][0]["field"] == "id_number"

    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_settings SET guest_id_number_enabled = true WHERE hotel_id = :h"),
            {"h": hotel.id},
        )
    created = await client.post("/guests", json=body, headers={**gm, **idem()})
    assert created.status_code == 201, created.text
    guest = created.json()
    assert guest["has_id_number"] is True and "id_number" not in guest
    async with owner_engine.connect() as conn:
        sealed = (
            await conn.execute(text("SELECT id_number_enc FROM app.guests WHERE id = :g"), {"g": guest["id"]})
        ).scalar_one()
    assert b"A1234567" not in bytes(sealed) and b"a1234567" not in bytes(sealed)

    # Only a step-up export shows it; a plain read never does.
    read = await client.get(f"/guests/{guest['id']}", headers=gm)
    assert "id_number" not in read.json() and read.json()["has_id_number"] is True
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    export = (await client.get(f"/guests/{guest['id']}/export", headers=gm_s)).json()
    assert export["guest"]["id_number"] == "A1234567"

    bad = await client.patch(f"/guests/{guest['id']}", json={"id_number": "<script>"}, headers=gm)
    assert bad.status_code in (400, 422)
    cleared = await client.patch(f"/guests/{guest['id']}", json={"id_number": None}, headers=gm)
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["has_id_number"] is False
