"""Load test for the hot paths (database spec, Hot queries; operations runbook, SLOs).

Runs against a staging environment seeded with `scripts/seed_dev.py`-style data, never
production. Install and run without adding locust to the project:

    uvx --from locust locust -f infra/loadtest/locustfile.py --host https://staging-api.example \
        --users 300 --spawn-rate 20 --run-time 15m --headless --csv loadtest

Environment:
    DY_TABLET_TOKENS   comma-separated device access tokens of paired guest tablets
    DY_KITCHEN_TOKEN   an access token for a kitchen manager (board polling)
    DY_STAFF_TOKEN     an access token for a receptionist (folio and stays)
    DY_MENU_ITEM       a menu item id that is available all day
    DY_STAY_ID         an active stay id the receptionist can read

Targets (p95): guest session 5 ms of database time, guest orders 10 ms, kitchen board 30 ms,
folio 20 ms; API p95 under 300 ms at 300 concurrent users with no errors other than 409/422
business rules.
"""

from __future__ import annotations

import os
import random
import uuid

from locust import HttpUser, between, task

API = "/api/v1"
TABLETS = [t for t in os.environ.get("DY_TABLET_TOKENS", "").split(",") if t]


class GuestTablet(HttpUser):
    """A guest browsing the menu and now and then ordering one item."""

    weight = 6
    wait_time = between(2, 8)

    def on_start(self) -> None:
        if not TABLETS:
            raise RuntimeError("set DY_TABLET_TOKENS")
        self.headers = {"Authorization": f"Bearer {random.choice(TABLETS)}"}  # noqa: S311 - load test

    @task(5)
    def session_and_menu(self) -> None:
        self.client.get(f"{API}/guest/session", headers=self.headers, name="guest session")
        self.client.get(f"{API}/guest/menu", headers=self.headers, name="guest menu")

    @task(2)
    def orders_and_bill(self) -> None:
        self.client.get(f"{API}/guest/orders", headers=self.headers, name="guest orders")
        self.client.get(f"{API}/guest/folio", headers=self.headers, name="guest folio")

    @task(1)
    def place_order(self) -> None:
        item = os.environ["DY_MENU_ITEM"]
        quote = self.client.post(
            f"{API}/guest/orders/quote",
            json={"lines": [{"menu_item_id": item, "quantity": 1}]},
            headers=self.headers,
            name="guest quote",
        )
        if quote.status_code != 200:
            return
        with self.client.post(
            f"{API}/guest/orders",
            json={"lines": [{"menu_item_id": item, "quantity": 1}], "quoted_total": quote.json()["total"]},
            headers={**self.headers, "Idempotency-Key": str(uuid.uuid4())},
            name="guest order",
            catch_response=True,
        ) as r:
            if r.status_code in (201, 409, 422):  # limits and approvals are business outcomes
                r.success()


class KitchenDisplay(HttpUser):
    weight = 1
    wait_time = between(5, 10)  # displays poll only while their socket is down

    def on_start(self) -> None:
        self.headers = {"Authorization": f"Bearer {os.environ['DY_KITCHEN_TOKEN']}"}

    @task
    def board(self) -> None:
        self.client.get(f"{API}/kitchen/orders", headers=self.headers, name="kitchen board")


class Reception(HttpUser):
    weight = 1
    wait_time = between(3, 12)

    def on_start(self) -> None:
        self.headers = {"Authorization": f"Bearer {os.environ['DY_STAFF_TOKEN']}"}

    @task(3)
    def folio(self) -> None:
        self.client.get(f"{API}/folios/{os.environ['DY_STAY_ID']}", headers=self.headers, name="folio")

    @task(1)
    def stays(self) -> None:
        self.client.get(f"{API}/stays", params={"status": "active"}, headers=self.headers, name="stays")
