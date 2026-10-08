# @diyneco/shared-types

TypeScript types for every request and response of the Diyneco API, generated from FastAPI's
OpenAPI document so frontends cannot drift from the backend.

```
pnpm install
pnpm gen:types        # from the repo root
```

`openapi.json` and `src/api.d.ts` are generated and committed; CI fails if they are stale.
