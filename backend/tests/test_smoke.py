async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Request-Id"]


async def test_factory_hotel(factory, client):
    hotel = await factory.hotel()
    headers = await factory.auth(hotel, "receptionist")
    r = await client.get("/hotel", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == str(hotel.id)
