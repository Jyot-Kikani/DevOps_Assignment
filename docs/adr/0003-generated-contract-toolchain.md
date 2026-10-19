# API contracts and isolated generator

P02 exports OpenAPI from installed service wheels and commits the documents and generated TypeScript types. `contracts --check` compares both without modifying them. IDs remain strings; renderer ordinals are separate uint32 values.

The pinned `openapi-typescript` 7.13.0 declares a TypeScript 5 peer dependency. Its isolated `tools/codegen` package therefore pins TypeScript 5.9.3. The application keeps the P00 TypeScript 7.0.2 compiler and checks the generated output with that compiler. Both npm dependency graphs have committed integrity lockfiles; peer checks are enabled.

P02 service routes validate requests and return structured 503 responses until P06/P07 implement their dependencies. Their process health route is live; readiness and version metadata cannot fabricate a deployment. Common primitives are stdlib-only, built as a wheel, and installed into each service/job environment. Python tests import installed packages rather than repository source paths.
