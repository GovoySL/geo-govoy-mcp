// Marca dist/cjs como CommonJS (el paquete raíz es "type": "module").
import { writeFileSync } from "node:fs";
writeFileSync(new URL("../dist/cjs/package.json", import.meta.url), JSON.stringify({ type: "commonjs" }) + "\n");
