DIYNECO — WORLD-CLASS HOTEL OPERATIONS, GUEST SERVICES & BILLING PLATFORM

ROLE

You are a senior staff-level software architect, product engineer, UI/UX designer, security engineer, database architect, DevOps engineer and QA engineer.

Build Diyneco, a production-ready, multi-tenant hotel and guest-house operations platform.

Diyneco is not merely a room-service ordering application. It is a complete hotel operations platform connecting:

- Guests
- Hotel rooms
- In-room tablets
- Kitchen staff
- Room-service staff
- Reception/management
- Hotel billing
- Accommodation charges
- Food & beverage
- Corporate billing
- Guest checkout
- Invoices and receipts
- Hotel analytics
- Diyneco platform administration

The architecture must be scalable from a small guest house with 5–20 rooms to hotels with hundreds or thousands of rooms.

Do not create a prototype that will need to be rewritten later. Build the foundation as a serious SaaS product.

---

1. CORE PRODUCT PRINCIPLE

Diyneco must operate as:

«One hotel platform. One source of truth. Multiple specialized interfaces.»

There will be FIVE interfaces:

1. Guest App
2. Kitchen App
3. Room-Service App
4. Merchant/Hotel Management App
5. Diyneco Admin Panel

All five interfaces must use the SAME central backend and PostgreSQL database.

Do NOT create separate databases for each application.

Architecture:

Guest App
↓
Central Diyneco API
↓
PostgreSQL / Supabase
↑
Kitchen App
↑
Room-Service App
↑
Merchant App
↑
Diyneco Admin Panel

---

2. TECHNOLOGY STACK

Use the following technology stack.

Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic migrations
- PostgreSQL
- Supabase PostgreSQL
- Supabase Storage where appropriate
- REST API
- WebSockets and/or Supabase Realtime for live order updates
- JWT/session-based authentication as appropriate
- RBAC
- MFA for sensitive management/admin operations
- Background jobs where required

Do not put business logic directly into frontend applications.

All important business rules must be enforced server-side.

---

3. FRONTEND TECHNOLOGY

Guest App

Use:

- React Native
- Expo
- Expo Router
- TypeScript
- NativeWind/Tailwind
- TanStack Query
- Secure device storage
- Offline-aware state handling where appropriate

The Guest App is primarily designed for Android tablets mounted/provided inside hotel rooms.

It must support kiosk/tablet mode architecture.

---

Kitchen App

Use:

- Next.js
- TypeScript
- Tailwind CSS
- Responsive UI
- TanStack Query
- WebSockets/Supabase Realtime

It should work on:

- Android tablets
- iPads
- Touchscreen computers
- Desktop browsers

The kitchen interface should be optimized for large touch targets and fast operation.

---

Room-Service App

Use:

- React Native
- Expo
- TypeScript
- Expo Router
- NativeWind/Tailwind
- TanStack Query
- Secure authentication

This is optimized for staff mobile phones/tablets.

---

Merchant App

Use:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui or an equivalent high-quality component system
- TanStack Query
- Charts/analytics library
- Responsive desktop/tablet design

This is the hotel's primary management platform.

---

Diyneco Admin Panel

Use:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Secure RBAC
- MFA

This is completely separate from the merchant management interface from a permission perspective.

---

4. BRAND

Product name:

Diyneco

Positioning:

«Hotel Operations. Guest Services. One Platform.»

Design should feel:

- Premium
- Modern
- Professional
- Hospitality-focused
- Trustworthy
- Elegant
- Simple
- International
- Enterprise-ready

Do NOT make the UI childish, overly colorful or generic.

Use the Diyneco brand identity consistently across all applications.

Primary design direction:

- Clean white/light backgrounds
- Deep navy
- Blue
- Teal/green accent
- Generous spacing
- Premium typography
- Rounded but professional components
- Clear status indicators

The interface should look like a serious SaaS product used by professional hotels.

---

5. MULTI-TENANT ARCHITECTURE

Diyneco is a multi-tenant SaaS.

Each hotel is a tenant.

Every hotel-owned entity must be associated with a "hotel_id".

Never allow one hotel to access another hotel's data.

Examples:

Hotel A must never be able to access:

- Hotel B rooms
- Hotel B guests
- Hotel B orders
- Hotel B menus
- Hotel B staff
- Hotel B payments
- Hotel B reports

Enforce tenant isolation at:

1. API layer
2. Database queries
3. Authorization layer
4. Frontend routing
5. Device authentication

Never rely only on frontend filtering.

---

6. APPLICATION 1 — GUEST APP

Build a dedicated Guest App using React Native + Expo.

The Guest App runs on a tablet assigned to a specific room.

Example:

Hotel:
"Grand Example Hotel"

Room:
"259"

Device:
"DY-259-01"

The guest must NEVER manually enter the room number.

The backend determines:

Device → Hotel → Room → Active Stay

---

7. TABLET PAIRING

Merchant management can register a tablet.

Flow:

Merchant App:

Settings
→ Devices
→ Add Device

Generate:

- Device ID
- Pairing code
- QR pairing code

Hotel administrator installs the Guest App.

Guest App:

"Pair this device"

The administrator scans the QR code or enters the pairing code.

The backend permanently associates:

Hotel
+
Room
+
Device

The device receives a secure device credential.

Do not store raw pairing secrets unnecessarily.

Use secure device storage.

---

8. GUEST APP HOME SCREEN

Example:

WELCOME TO

Grand Example Hotel

Room 259

[ Food & Beverage ]

[ Room Service ]

[ View My Orders ]

[ My Bill ]

[ Hotel Information ]

The interface should be simple enough that any guest can immediately understand it.

---

9. GUEST MENU

The hotel controls the menu through the Merchant App.

Guest sees:

Categories:

- Breakfast
- Lunch
- Dinner
- Snacks
- Drinks
- Desserts

Menu item:

Chicken Burger

R145

Description

Chicken breast, cheese, lettuce and sauce.

[Add to Order]

Support:

- Photos
- Modifiers
- Add-ons
- Dietary information
- Allergens
- Availability
- Scheduled availability
- Item notes
- Quantity

---

10. GUEST ORDERING

Guest:

Browse
→ Select items
→ Add to cart
→ Review
→ Confirm order

Display:

Room: 259

Items:
Chicken Burger ×2
Coke ×2

Subtotal
R310

Room-service fee
R50

Amount due
R360

Payment/charge method:
Charge to Room

[Place Order]

---

11. ROOM CHARGE

Initial product phase should support:

Charge to Room

Do not require an online payment gateway for the initial version.

However, architect payment services so online payments can be added later.

Before approving a room charge, backend should verify:

- Device belongs to hotel
- Device belongs to room
- Room exists
- Active stay exists
- Hotel allows room charging
- Guest/stay is authorized
- Order is within configured limits
- No blocked account condition exists

Hotels can configure room-charge rules.

Example:

Orders below R500:
Auto-authorize.

Orders above R500:
Require manager approval.

---

12. GUEST ORDER STATUS

Guest sees live status:

Order #10482

✓ Order received
✓ Kitchen accepted
✓ Preparing
✓ Ready
✓ Room service delivering
✓ Delivered

Use real-time updates.

Do not require the guest to repeatedly refresh.

---

13. GUEST BILL

Guest can see current stay charges.

Separate categories:

Accommodation

Room:
R1,500 × 3 nights

R4,500

Food & Beverage

Food:
R2,950

Room-service fee:
R50

F&B:
R3,000

Other Services

Laundry:
R350

Tips

R1,000

Do not combine categories internally.

---

14. APPLICATION 2 — KITCHEN APP

Create a dedicated Kitchen Display System.

Use:

Next.js
TypeScript
Tailwind
Realtime/WebSockets

Kitchen staff should not use the Guest App.

They use a dedicated kitchen interface.

The hotel can place a tablet, touchscreen computer or monitor in the kitchen.

---

15. KITCHEN DEVICE

Merchant App:

Kitchen
→ Devices
→ Add Kitchen Device

Assign:

Hotel
→ Kitchen
→ Device

Example:

Main Kitchen
KITCHEN-01

Kitchen staff authenticate using authorized staff credentials/PIN.

---

16. KITCHEN DASHBOARD

Display:

NEW — 3
PREPARING — 5
READY — 2

Order card:

ORDER #10482
ROOM 259

Chicken Burger ×2
Coke ×2
Chocolate Cake ×1

Special instructions:
No onions. Extra sauce.

Order time:
18:21

Buttons:

[Accept]
[Start Preparing]
[Ready]

---

17. KITCHEN WORKFLOW

Order statuses:

NEW
→ ACCEPTED
→ PREPARING
→ READY

Once ready:

Room-Service App receives a real-time notification.

Kitchen should NOT be able to:

- Change guest billing
- Change prices
- Give discounts
- Change payment amounts
- Edit historical financial records

Kitchen is an operational interface.

---

18. KITCHEN STATIONS

Support multiple preparation stations.

Example:

Main Kitchen
Bar
Dessert Station
Pool Bar

Menu item can have:

"preparation_station_id"

An order can therefore route items to different stations.

Example:

Room 259 order:

Main Kitchen:
Burger ×2

Bar:
Coke ×2

Dessert:
Cake ×1

The system should track item-level preparation status.

The order becomes fully READY when all required items are ready.

---

19. APPLICATION 3 — ROOM-SERVICE APP

Use:

React Native
Expo
TypeScript
Expo Router
NativeWind/Tailwind

Designed for hotel staff.

Workflow:

READY
→ ASSIGNED
→ PICKED UP
→ DELIVERING
→ DELIVERED
→ PAID/CLOSED

---

20. ROOM-SERVICE DASHBOARD

Staff sees:

READY FOR DELIVERY

Order #10482
Room 259

Items:
2 × Chicken Burger
2 × Coke
1 × Chocolate Cake

Amount due:
R3,000

[Accept Delivery]

---

21. DELIVERY

Staff picks up order.

Tap:

[PICKED UP]

Then:

[DELIVERED]

System records:

- Staff member
- Time picked up
- Time delivered
- Room
- Order
- Device
- Location context if later required
- Payment status

Do not collect unnecessary personal data.

---

22. CARD PAYMENT / OVERPAYMENT / TIP

Architect support for physical card payment through the hotel's existing card terminal.

The system does NOT store:

- Card number
- CVV
- PIN
- Full magnetic stripe data

Example:

Food & beverages:
R2,950

Room-service fee:
R50

Amount due:
R3,000

Guest pays by card:
R4,000

System calculates:

Amount due:
R3,000

Amount received:
R4,000

Difference:
R1,000

Tip:
R1,000

Show confirmation:

"Guest paid R1,000 above the amount due. Record R1,000 as a tip?"

[Cancel]
[Confirm Tip]

If confirmed:

Bill:
R3,000

Tip:
R1,000

Total collected:
R4,000

Hotel revenue remains:
R3,000

Tip remains a separate financial category.

---

23. IMMUTABLE BILLING

Once an order is accepted, its financial values should be effectively immutable.

If an adjustment is required:

Require authorized approval.

Record:

- Original amount
- New amount
- Reason
- Requested by
- Approved by
- Date/time
- Audit log

Staff must never be able to secretly alter the amount.

---

24. ANTI-THEFT / TRANSPARENT BILLING

This is a core product feature.

The guest tablet must show the official amount due.

Example:

Guest Tablet:

Food:
R2,950

Room-service fee:
R50

Amount due:
R3,000

Room-Service App:

Amount due:
R3,000

Amount received:
R4,000

Tip:
R1,000

Merchant App:

Food:
R2,950

Room-service fee:
R50

Bill:
R3,000

Tip:
R1,000

Total:
R4,000

The same transaction must exist in the backend.

Core principle:

«Guest sees the same amount.
Kitchen sees the same order.
Room service sees the same amount.
Management sees the same transaction.»

---

25. APPLICATION 4 — MERCHANT APP

Build the hotel management application with Next.js.

This is the main hotel control center.

Navigation:

Dashboard
Orders
Rooms
Guests & Stays
Menu
Kitchen
Room Service
Billing
Payments
Staff
Devices
Reports
Analytics
Settings
API
Subscription

---

26. MERCHANT DASHBOARD

Display:

Today's orders
Today's accommodation revenue
Today's F&B revenue
Other services
Tips
Total collected
Active stays
Occupied rooms
Available rooms
Preparing orders
Deliveries
Average preparation time

Charts:

- Revenue by day
- Accommodation vs F&B
- Orders by day
- Popular menu items
- Average order value
- Tips
- Room-service performance

---

27. ROOM MANAGEMENT

Merchant can create:

Room number
Floor
Room type
Rate
Status
Amenities
Capacity

Statuses:

Available
Occupied
Reserved
Cleaning
Maintenance
Out of Service

Allow bulk room creation.

Example:

101–120
201–220
301–350

---

28. DEVICE MANAGEMENT

Display:

Device
Room
Type
Status
Last seen
OS
App version

Guest device states:

Online
Offline
Needs pairing
Disabled
Reset required

Management actions:

Pair
Assign
Reassign
Lock
Reset
Disable
Unpair

Never allow a guest to change the assigned room.

---

29. MENU MANAGEMENT

Merchant creates:

Categories
Menu items
Modifiers
Add-ons
Prices
Photos
Availability
Preparation station
Allergen information
Dietary information

Support:

Breakfast hours
Lunch hours
Dinner hours
24-hour items

Example:

Breakfast:
06:00–11:00

Lunch:
11:00–16:00

Dinner:
17:00–22:00

---

30. GUEST STAYS

Create a Stay/Folio system.

Stay contains:

Guest
Room
Check-in
Expected checkout
Actual checkout
Status
Accommodation charges
F&B charges
Other charges
Payments
Balance

Stay statuses:

Reserved
Checked In
Active
Checkout Pending
Checked Out
Cancelled

---

31. ACCOMMODATION BILLING

Support:

Room rate
Number of nights
Taxes
Fees
Discounts
Corporate rates
Manual authorized adjustments

Example:

Room:
R1,500 × 3 nights

R4,500

Accommodation tax:
R675

Accommodation total:
R5,175

Keep accommodation separate from F&B.

---

32. FOOD & BEVERAGE BILLING

F&B includes:

Food
Beverages
Room-service fees
Other F&B charges

Tips must be separate.

Example:

Food:
R2,950

Room-service fee:
R50

F&B:
R3,000

Tip:
R1,000

---

33. OTHER HOTEL SERVICES

Architect the system so additional charge categories can be added.

Examples:

Laundry
Spa
Transport
Minibar
Activities
Extra bed
Other services

Do not hard-code the system to food only.

---

34. CHECKOUT SYSTEM

Merchant App:

Rooms
→ Room 259
→ Current Stay

Button:

GUEST CHECK OUT

Require authorization PIN or appropriate secure authentication.

Before checkout:

Display:

Accommodation:
R5,175

F&B:
R3,000

Other services:
R350

Tips:
R1,000

Total:
R9,525

Outstanding balance:
R0

Then:

[Cancel]
[Confirm Guest Checkout]

---

35. CHECKOUT VALIDATION

If outstanding balance exists:

Show warning:

"Outstanding balance: R850"

Do not silently allow checkout.

Allow authorized manager override only if hotel policy permits.

Record override in audit log.

---

36. BILL / INVOICE GENERATION

At checkout allow:

Print
Email
Print + Email
Download PDF

Generate professional PDF guest statement/bill.

Include:

Hotel logo
Hotel name
Hotel address
Contact information
Tax/VAT details where applicable
Bill/invoice number
Guest name
Room
Check-in date
Check-out date
Accommodation
F&B
Other services
Tips
Taxes
Payments
Balance

Do not label something as a tax invoice unless the hotel's configuration/legal requirements support it.

---

37. CORPORATE BILLING

During check-in allow billing type:

Personal
Company

If company:

Company name
Registration number
VAT number
Billing address
Company email
Purchase order/reference
Traveller/employee name

Example:

Billed to:
ABC Technologies (Pty) Ltd

Traveller:
John Smith

Reference:
TRAVEL-10482

Generate the final bill accordingly.

---

38. APPLICATION 5 — DIYNECO ADMIN PANEL

This is the platform owner's control center.

Do NOT mix platform administration with hotel management.

Admin can manage:

Hotels
Subscriptions
Plans
Platform users
Usage
System health
API usage
Support
Feature flags
Security
Platform analytics

---

39. ADMIN HOTEL MANAGEMENT

Admin sees:

Hotel name
Status
Plan
Rooms
Devices
Users
Orders
Revenue metrics
Subscription status
Created date
Last activity

Actions:

Approve
Suspend
Reactivate
View
Support
Change plan

Admin must not unnecessarily expose sensitive guest information.

Follow privacy-by-design principles.

---

40. SUBSCRIPTIONS

Architect SaaS subscription support.

Hotel can have:

Plan
Status
Start date
Renewal date
Usage
Limits

Future plans can include:

Starter
Professional
Enterprise

Do not hard-code pricing into business logic.

---

41. ROLE-BASED ACCESS CONTROL

Create permissions rather than only simple roles.

Possible roles:

Platform Super Admin
Platform Support
Hotel Owner
Hotel Admin
General Manager
Reception Manager
Receptionist
Finance Manager
Kitchen Manager
Kitchen Staff
Room-Service Manager
Room-Service Staff

Examples:

Kitchen staff:
View kitchen orders
Update preparation status

Cannot:
View hotel financial reports
Change menu prices
Modify guest folios

Reception:
Manage stays
Check guests in/out
View bills

Finance:
View financial reports
Manage billing

Hotel Admin:
Full hotel control

---

42. AUTHENTICATION

Use secure authentication.

Staff accounts require:

Email/username
Password or secure authentication method

Sensitive actions can require:

MFA
PIN
Re-authentication

Admin Panel should require MFA.

Never store plain-text passwords or PINs.

Hash sensitive credentials appropriately.

Implement:

- Session expiration
- Refresh token rotation where applicable
- Account lockout/rate limiting
- Password reset
- Email verification
- Device/session management

---

43. DATABASE

Use PostgreSQL through Supabase.

Design normalized relational schema.

Core tables should include at minimum:

hotels
hotel_settings
rooms
room_types
devices
device_pairings
users
roles
permissions
user_roles
hotel_users
guests
stays
folios
folio_entries
menu_categories
menu_items
menu_modifiers
menu_item_modifiers
kitchen_stations
kitchen_devices
orders
order_items
order_item_modifiers
order_status_history
deliveries
payments
payment_allocations
tips
accommodation_charges
service_charges
discounts
billing_profiles
invoices
invoice_items
subscriptions
plans
api_keys
webhooks
notifications
audit_logs

Add supporting tables where architecturally appropriate.

---

44. MONEY STORAGE

Never use floating point for money.

Use:

Integer minor units

Example:

R3000 = 300000 cents

or a suitable fixed-precision PostgreSQL numeric strategy.

Be consistent throughout the entire system.

Currency must be stored per financial context.

Initial currency:

ZAR

Architecture must support future currencies.

---

45. ORDER SNAPSHOTS

When an order is placed, snapshot:

Item name
Description where necessary
Unit price
Tax
Fees
Modifiers
Quantity

Changing the menu later must NOT change historical orders.

---

46. AUDIT LOGGING

Create a robust audit system.

Record important actions:

Guest checkout
Bill adjustment
Discount
Refund
Payment
Tip
Room reassignment
Device pairing
Device reset
Menu price change
User creation
Permission change
Staff removal
Subscription change

Audit entry:

Actor
Hotel
Action
Entity
Old value
New value
Timestamp
IP/device context where appropriate

---

47. PRIVACY

Follow privacy-by-design principles.

The system should be suitable for South African hotels and should be architected with POPIA considerations.

Minimize guest personal data.

Do not expose previous guest information to the next guest.

Do not store unnecessary card information.

---

48. ROOM RESET

This is a critical feature.

When management checks out a guest:

1. Close active stay.
2. Finalize folio.
3. Generate requested bill.
4. Close financial records.
5. Invalidate guest tablet session.
6. Send real-time RESET_ROOM_SESSION command.
7. Tablet removes guest-visible history.
8. Tablet returns to welcome screen.
9. Room becomes available/cleaning depending on hotel workflow.
10. Historical data remains securely stored for management.

Previous guest data must never be shown to the next guest.

The database history must NOT be deleted merely to clear the tablet.

---

49. DEVICE SECURITY
Guest tablets must be strongly bound to:
Hotel Room Device
Backend should reject requests if:
Device is disabled
Device belongs to another hotel
Device is assigned to another room
Device credential is invalid
Device is revoked
Implement device heartbeat:
last_seen_at
Merchant dashboard shows:
Online Offline Last seen
50. REAL-TIME SYSTEM
Use Supabase Realtime and/or WebSockets.
Real-time events should include:
NEW_ORDER ORDER_ACCEPTED ORDER_PREPARING ORDER_READY DELIVERY_ASSIGNED ORDER_DELIVERED PAYMENT_UPDATED STAY_CHECKED_OUT RESET_ROOM_SESSION DEVICE_LOCKED MENU_UPDATED
Do not rely solely on polling.
Provide fallback polling/reconnection logic.
51. NOTIFICATIONS
Support in-app notifications.
Future support:
Push notifications Email SMS WhatsApp integrations
Initial system should at minimum provide reliable real-time application updates.
52. OFFLINE / NETWORK FAILURE
Design for unreliable hotel Wi-Fi.
Guest tablet should:
Detect connection loss
Show offline state
Avoid creating duplicate orders
Reconnect automatically
Kitchen should reconnect automatically.
Room-Service App should cache relevant assigned deliveries.
Financial/payment actions should require strong server confirmation and idempotency.
Never allow a network retry to create duplicate orders or duplicate payments.
53. IDEMPOTENCY
Implement idempotency for:
Order creation Payment recording Checkout Device pairing Important state-changing operations
Every financial operation must be safely retryable.
54. API DESIGN
Create a clean versioned API:
/api/v1/...
Organize by domain:
/auth /hotels /rooms /devices /stays /guests /menu /orders /kitchen /deliveries /folios /payments /invoices /staff /reports /subscriptions /admin /api-keys /webhooks
Use OpenAPI documentation automatically through FastAPI.
55. API SECURITY
Implement:
Authentication Authorization Tenant isolation Rate limiting Request validation Input sanitization CORS configuration Secure headers Logging Error handling
Never expose internal database errors directly to users.
56. FILE STORAGE
Use Supabase Storage for:
Hotel logos Menu item images Invoice PDFs where necessary Other approved hotel assets
Use secure bucket policies.
Do not expose private files publicly unless intentionally configured.
57. EMAIL
Architect transactional email support.
Emails include:
Guest bill Invoice Payment receipt Password reset Email verification Staff invitation Hotel onboarding
Use a provider abstraction so email provider can be changed later.
58. REPORTING
Merchant reports:
Daily revenue Accommodation revenue F&B revenue Other service revenue Tips Orders Average order value Popular items Room-service performance Kitchen preparation time Cancelled orders Discounts Adjustments Payment breakdown
Allow date filtering.
Future:
CSV export PDF reports Accounting integrations
59. ADMIN ANALYTICS
Diyneco Admin sees platform metrics:
Total hotels Active hotels Total rooms Connected devices Active stays Orders today Orders this month Platform subscription revenue Active subscriptions Churn Usage System health
Do not expose tenant data unnecessarily.
60. API / INTEGRATIONS
Merchant App should include an API section.
Allow hotels to create:
Production API keys Sandbox API keys
Display:
API key Status Created date Last used Usage
Never show the full secret again after initial creation.
Support future webhooks.
Potential integrations:
PMS POS Accounting Payment terminals Online payment gateways
Do not implement every integration now, but design the architecture for them.
61. PAYMENT ARCHITECTURE
Initial payment model:
Charge to Room
Physical card payment recorded by room-service staff
Do not require an online payment gateway for initial release.
Future:
Online checkout Payment gateway Card terminal integration Refunds Partial payments Split payments Corporate payment
Create an abstract payment service layer.
62. BILLING DATA MODEL
Payment records should support:
amount_due amount_received tip_amount payment_method payment_status currency provider_reference external_transaction_id created_at
Never store raw card credentials.
63. HOTEL ONBOARDING
Merchant onboarding:
Create account → Create hotel → Configure hotel → Create room types → Create rooms → Configure menu → Create kitchen → Add devices → Invite staff → Pair tablets → Configure room charging → Ready
Build a guided onboarding wizard.
64. ROOM CREATION
Support:
Manual creation Bulk creation CSV import
Example:
101 102 103 104 ...
Allow floor assignment and room type assignment.
65. STAFF ONBOARDING
Merchant:
Staff → Invite Staff
Select:
Name Email Role Department Permissions
Send invitation.
Staff completes account setup.
66. UI/UX REQUIREMENTS
All interfaces must be:
Responsive Accessible Fast Touch-friendly where required Keyboard-friendly on desktop Mobile-friendly Professional
Kitchen:
Very large buttons.
Guest:
Extremely simple.
Merchant:
Information-rich but organized.
Admin:
Enterprise dashboard.
Avoid unnecessary animations.
Use loading skeletons.
Use clear error messages.
Use confirmation dialogs for destructive actions.
67. DARK/LIGHT MODE
Merchant and Admin can support:
Light Dark System
Guest tablet should prioritize a clean hospitality presentation.
Kitchen should support a high-visibility mode.
68. ERROR HANDLING
Never display raw stack traces.
Use:
Friendly message Error code Retry option
Log technical details securely on backend.
69. TESTING
Write tests.
Backend:
Unit tests Integration tests API tests Authorization tests Tenant isolation tests Financial calculation tests
Frontend:
Component tests Critical flow tests
End-to-end:
Guest order → Kitchen → Room service → Delivery → Checkout
Also test:
Two hotels cannot access each other's data.
70. CRITICAL TEST CASES
Test:
Room 259 orders R3,000.
Kitchen receives correct order.
Room-service receives correct amount.
Guest sees R3,000.
Staff enters R4,000.
System calculates R1,000 tip.
Merchant sees R3,000 F&B + R1,000 tip.
Guest checks out.
Manager enters PIN.
Tablet resets.
New guest cannot see previous orders.
Previous guest history remains available to authorized management.
71. SECURITY TESTING
Test:
Unauthorized hotel access Cross-tenant API requests Invalid device credentials Expired sessions Privilege escalation Unauthorized checkout Unauthorized bill modification Unauthorized discounts Unauthorized payment modification Replay requests Duplicate payment submissions Duplicate orders
72. DATABASE RULES
Use:
Foreign keys Indexes Unique constraints Check constraints Transactions Proper cascading rules
Avoid accidental cascading deletion of financial history.
Prefer soft deletion where appropriate.
Financial records should generally be retained rather than physically deleted.
73. PROJECT STRUCTURE
Use a monorepo.
Suggested structure:
diyneco/
apps/ guest/ kitchen/ room-service/ merchant/ admin/
backend/ app/ api/ core/ models/ schemas/ services/ repositories/ auth/ realtime/ payments/ billing/ notifications/ audit/ integrations/
database/ migrations/ seeds/
packages/ shared-types/ shared-ui/ config/
docs/ architecture/ api/ database/ security/
infra/ docker/ deployment/
tests/
Use clean separation between applications and backend domains.
74. ENVIRONMENT VARIABLES
Never hard-code secrets.
Examples:
DATABASE_URL SUPABASE_URL SUPABASE_ANON_KEY SUPABASE_SERVICE_ROLE_KEY JWT_SECRET EMAIL_PROVIDER_KEY STORAGE_BUCKET REDIS_URL if required SENTRY_DSN if used
Provide:
.env.example
Never commit actual secrets.
75. SUPABASE
Use Supabase primarily for:
PostgreSQL Storage Realtime Potential authentication support where appropriate
However, maintain the Python FastAPI backend as the authoritative business/API layer.
Do not expose privileged Supabase credentials to frontend applications.
Never put:
SUPABASE_SERVICE_ROLE_KEY
inside frontend applications.
76. DEPLOYMENT
Design production deployment.
Backend: FastAPI
Database: Supabase PostgreSQL
Frontend: Next.js deployments
Mobile: Expo / EAS
Use separate:
Development Staging Production
environments.
77. LOGGING & MONITORING
Implement structured backend logging.
Track:
API errors Authentication failures Database errors Realtime failures Payment failures Device connectivity Critical security events
Prepare architecture for Sentry or equivalent monitoring.
78. BACKUPS & RECOVERY
Database must have appropriate backup/recovery strategy.
Financial and operational records must not depend on local devices.
A tablet failure must not destroy hotel data.
79. NO FAKE FUNCTIONALITY
Do not create buttons that pretend to work.
If a feature is not implemented, either implement it properly or clearly mark it as coming later.
Do not use fake payment confirmations.
Do not use fake backend responses in production flows.
Do not hard-code demo hotel data into the production architecture.
Seed data can exist for development.
80. DEVELOPMENT APPROACH
Do not attempt to generate the entire project blindly in one huge step.
Work systematically.
PHASE 1: Architecture Database schema Authentication Tenant isolation Core backend
PHASE 2: Merchant onboarding Hotels Rooms Devices Staff
PHASE 3: Menu Guest tablet Ordering
PHASE 4: Kitchen
PHASE 5: Room service
PHASE 6: Billing Accommodation F&B Tips Checkout Invoice generation
PHASE 7: Admin panel
PHASE 8: Reports Analytics Notifications API
PHASE 9: Security hardening Testing Performance Production deployment
81. IMPORTANT PRODUCT RULES
Remember these throughout development:
A guest tablet belongs to ONE hotel and ONE room.
Guests cannot change their room number.
Guest tablet never exposes previous guest history.
Checkout requires appropriate authorization.
Checkout resets the guest tablet.
Historical data remains securely stored.
Accommodation and F&B are separate financial categories.
Tips are separate from hotel revenue.
Tip = amount received − amount due when positive.
Kitchen cannot change prices.
Room-service staff cannot secretly change bills.
Financial adjustments require authorization and audit trails.
All hotel data is tenant-scoped.
All five interfaces use the same central backend.
No raw card information is stored.
Money must never use floating-point arithmetic.
Important financial operations must be idempotent.
Backend is the source of truth.
Frontend must never be trusted for authorization.
Build for production, not merely a visual demo.
82. DEFINITION OF DONE
The platform is considered functionally complete when a hotel can:
Register.
Create its hotel.
Create rooms.
Create room types.
Configure room rates.
Create menu categories.
Create menu items.
Create kitchen stations.
Add kitchen devices.
Invite kitchen staff.
Invite room-service staff.
Register guest tablets.
Assign tablets to rooms.
Check a guest into a room.
Guest opens tablet.
Guest sees the hotel's menu.
Guest places an order.
Kitchen receives it instantly.
Kitchen prepares it.
Kitchen marks it ready.
Room-service staff receives it.
Staff delivers it.
Guest sees the official amount.
Staff records payment.
System calculates overpayment/tip correctly.
Management sees the transaction.
Accommodation charges are maintained separately.
F&B charges are maintained separately.
Other services can be added.
Guest can be checked out.
Authorized PIN/security confirmation is required.
Bill can be printed.
Bill can be emailed.
Corporate billing information can appear on the bill.
Guest tablet resets.
New guest cannot see old data.
Management can still access historical records.
Admin can manage the hotel tenant.
Reports work.
Audit logs work.
Tenant isolation is tested.
Security controls are tested.
The system is deployable to production.
FINAL INSTRUCTION
Build Diyneco as a serious, scalable SaaS platform.
Prioritize:
SECURITY MULTI-TENANCY RELIABILITY FINANCIAL ACCURACY PRIVACY REAL-TIME OPERATIONS SIMPLE UX SCALABILITY MAINTAINABILITY
Do not over-engineer the UI while neglecting the backend.
Do not build five disconnected applications.
Build one unified Diyneco platform with specialized interfaces sharing the same authoritative backend and PostgreSQL database.
Before writing large amounts of code, establish the architecture, database schema, API contracts and project structure.
After each major phase, verify that the existing functionality still works before continuing.
Every feature must be production-oriented and properly connected from frontend → API → database → realtime/events where applicable.
The final product should feel like a world-class hotel technology platform rather than a basic restaurant ordering application.