# Guest tablet

Mobile-first web app for the in-room tablet (installable full screen). A tablet belongs to one hotel and one room.

- **Pairing:** a manager creates a 6-digit room-tablet code in the Merchant app (Devices);
  the credential is kept by the kiosk browser and swapped for 1-hour device tokens.
- **Welcome:** while nobody is checked in, the tablet shows the hotel and room only.
- **Ordering:** large-touch menu by category with allergens and dietary tags, options with
  min/max rules, notes, a cart priced by the server (the guest confirms that exact total),
  charged to the room; orders above the hotel's limit wait for approval.
- **Tracking and bill:** live order progress, the bill by category with tips shown apart,
  hotel information (checkout time, Wi-Fi, reception).
- **Privacy between guests:** on checkout or a manager's reset (`RESET_ROOM_SESSION`) the
  tablet drops everything about the previous guest; the API only ever answers for the room's
  current stay. An unattended cart is cleared after 3 minutes.
- **Kiosk (v1):** add the app to the home screen (full screen), keep the screen on in the
  tablet's display settings and turn on Android screen pinning; MDM device-owner mode comes
  in v1.1 (CLAUDE.md).

```
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3005
```
