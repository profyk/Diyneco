// Regenerate src/api.d.ts from openapi.json (written by backend/scripts/export_openapi.py).
//   pnpm --filter @diyneco/shared-types generate
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const pkg = join(here, "..");
const backend = join(pkg, "..", "..", "backend");

execFileSync("uv", ["run", "python", "scripts/export_openapi.py", join(pkg, "openapi.json")], {
  cwd: backend,
  stdio: "inherit",
});
const schema = JSON.parse(readFileSync(join(pkg, "openapi.json"), "utf8"));
const ast = await openapiTS(schema);
const header = "// Generated from the Diyneco OpenAPI document. Do not edit by hand.\n\n";
writeFileSync(join(pkg, "src", "api.d.ts"), header + astToString(ast));
console.log("wrote src/api.d.ts");
