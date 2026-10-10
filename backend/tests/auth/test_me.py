"""GET /auth/me: who is signed in and what they may do (apps hide what they cannot use)."""

from __future__ import annotations


async def test_me_for_staff_and_platform(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    rec = await factory.auth(hotel, "receptionist")
    me = (await client.get("/auth/me", headers=rec)).json()
    assert me["kind"] == "staff" and me["hotel"]["id"] == str(hotel.id)
    assert me["user"]["email"] == hotel.users["receptionist"].email
    assert "stays.manage" in me["permissions"] and "folio.discount" not in me["permissions"]
    assert me["roles"] and me["mfa"] is True

    admin = await factory.platform_user()
    token, _ = await factory.token(None, admin)
    pme = (await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})).json()
    assert pme["kind"] == "platform" and pme["hotel"] is None
    assert all(p.startswith("platform.") for p in pme["permissions"])
    assert (await client.get("/auth/me")).status_code == 401
