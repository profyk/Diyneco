# shared-ui

Design tokens and React components for the web apps (Merchant, Kitchen, Admin).

- `tokens.css`: the prototype's colours as a Tailwind v4 theme (`bg-surface`, `text-ink`,
  `border-line`, …), light and dark, plus `data-contrast="high"` for the kitchen display.
- Components: `Button` (with an `xl` size for touch screens), `Card`, `Field`, `Input`,
  `Select`, `Badge`, `Table`, `StatTile`, `EmptyState`, `Dialog`, `ErrorNotice`, and the
  `StepUpProvider` that asks for a PIN when the API answers `STEP_UP_REQUIRED`.

In an app's global CSS:

```css
@import "tailwindcss";
@import "@diyneco/shared-ui/tokens.css";
@source "../../../packages/shared-ui/src";
```
