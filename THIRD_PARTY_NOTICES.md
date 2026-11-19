# Third-party notices

The files in `catalog/` are **generated** from the two Microsoft npm packages below
(exact versions are recorded in `catalog/index.json` and pinned in `package.json`).
They contain data derived from those packages, which are licensed under the MIT License.
This project is not affiliated with or endorsed by Microsoft.

| Package | Used for | Source | License |
|---|---|---|---|
| [`@microsoft/powerbi-report-authoring-cli`](https://www.npmjs.com/package/@microsoft/powerbi-report-authoring-cli) | `catalog list` / `catalog describe`: roles, required/optional roles, max per role, formatting objects; `validate` / `scaffold` for the examples and CI | https://github.com/microsoft/skills-for-fabric | MIT |
| [`@microsoft/powerbi-core-visual-schema`](https://www.npmjs.com/package/@microsoft/powerbi-core-visual-schema) | `data/capabilities.json`: `requiredTypes`, `preferredTypes`, `noDuplicates`, allowed role combinations | https://github.com/microsoft/skills-for-fabric | MIT |

The JSON schemas referenced by the `$schema` fields in `examples/` are published by Microsoft at
https://github.com/microsoft/json-schemas (MIT) and are fetched at validation time; they are not copied into this repository.

Transitive npm dependencies are installed via `npm ci` and are not redistributed in this repository.

## License text (both packages, identical)

```text
MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
