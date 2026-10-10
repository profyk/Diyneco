<!-- Copied verbatim from docs/04-security-and-compliance.md, lines 77-130. Do not edit by hand: if the spec changes, copy it again. -->
| Permission               | Own | Adm | GM  | RM  | Rec | Fin | KM  | KS  | SM  | SS  |
|--------------------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| `hotel.read`             | ●   | ●   | ●   | ●   | ●   | ●   | ●   |     | ●   |     |
| `hotel.update`           | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `settings.read`          | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `settings.update` †      | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `rooms.read`             | ●   | ●   | ●   | ●   | ●   | ●   |     |     | ●   |     |
| `rooms.manage`           | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `rooms.status`           | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `devices.read`           | ●   | ●   | ●   | ●   | ●   |     | ●   |     |     |     |
| `devices.manage`         | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `staff.read`             | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `staff.manage` †         | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `roles.manage` †         | ●   | ●   |     |     |     |     |     |     |     |     |
| `guests.read`            | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `guests.manage`          | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `privacy.manage` †       | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `billing.manage`         | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `stays.read`             | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `stays.manage`           | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `stays.rate_override`    | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `menu.read`              | ●   | ●   | ●   | ●   | ●   |     | ●   | ●   | ●   |     |
| `menu.manage`            | ●   | ●   | ●   |     |     |     | ●   |     |     |     |
| `menu.price.update` †    | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `menu.availability`      | ●   | ●   | ●   | ●   |     |     | ●   | ●   |     |     |
| `menu.certify`           | ●   | ●   | ●   |     |     |     | ●   |     |     |     |
| `kitchen.manage`         | ●   | ●   | ●   |     |     |     | ●   |     |     |     |
| `kitchen.view`           | ●   | ●   | ●   |     |     |     | ●   | ●   |     |     |
| `kitchen.update`         | ●   | ●   | ●   |     |     |     | ●   | ●   |     |     |
| `orders.read`            | ●   | ●   | ●   | ●   | ●   | ●   | ●   |     | ●   |     |
| `orders.create`          | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `orders.approve` †       | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `orders.cancel` †        | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `deliveries.view`        | ●   | ●   | ●   | ●   | ●   |     |     |     | ●   | ●   |
| `deliveries.update`      | ●   | ●   | ●   |     |     |     |     |     | ●   | ●   |
| `deliveries.manage`      | ●   | ●   | ●   |     |     |     |     |     | ●   |     |
| `folio.read`             | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `folio.charge`           | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `folio.discount` †       | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `folio.adjust.request`   | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `folio.adjust.approve` † | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `payments.record`        | ●   | ●   | ●   | ●   | ●   | ●   |     |     | ●   | ●   |
| `payments.read`          | ●   | ●   | ●   | ●   | ●   | ●   |     |     | ●   |     |
| `checkout.perform` †     | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `checkout.override` †    | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `invoices.read`          | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `invoices.send`          | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `invoices.credit` †      | ●   | ●   | ●   |     |     | ●   |     |     |     |     |
| `reports.read`           | ●   | ●   | ●   | ●   |     | ●   | ●   |     | ●   |     |
| `reports.finance`        | ●   | ●   | ●   |     |     | ●   |     |     |     |     |
| `audit.read`             | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `subscription.read`      | ●   | ●   | ●   |     |     | ●   |     |     |     |     |
| `subscription.manage`    | ●   |     |     |     |     |     |     |     |     |     |
| `integrations.manage` †  | ●   | ●   |     |     |     |     |     |     |     |     |
