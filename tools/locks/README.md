# P00 dependency preparation

These are dependency inputs, locks and original upstream manifests prepared in P00. They are not implemented applications, Terraform infrastructure roots, or applied Kubernetes resources.

- `web/package.json` and `web/package-lock.json`: exact frontend dependency graph, resolved with project-local Node 24.22.0 and its bundled npm. A separate clean `npm ci --ignore-scripts --engine-strict` check passed under `.local/p00-npm-check`; lifecycle scripts and application builds have not been tested.
- `catalog`, `journey`, `importer`, `quality`, `checkov`, and `ops`: `.in` files declare exact direct versions; `.txt` files freeze the Linux/Python 3.13 transitive graphs with official PyPI artifact SHA-256s. Use `pip --require-hashes` for installation. These are Linux locks; Windows development environments require their own platform resolution. The Windows host bootstrap itself uses only the standard library.
- `terraform/providers.tf` exists only to select the Kubernetes provider in the approved `~> 3.2` band. Its `.terraform.lock.hcl` includes signed upstream checksums verified for `windows_amd64` and `linux_amd64`. No infrastructure was planned or applied.
- `vendor/` contains unchanged, versioned upstream Calico/Argo manifests, licenses and `SHA256SUMS`. Required platform/security patches belong to P12/P17. The upstream Argo file includes optional components that will be disabled. Its Redis reference will use the equivalent locked Docker Hub Redis digest; no AWS registry was contacted. These manifests must not be applied directly.

The authoritative provenance manifest is `tools/toolchain.lock.json`. It records downloaded Windows tools, published Linux tool checksums, image digests and action commits. Linux native binaries were not downloaded or executed. Data, application, scanner and cluster integration acceptance remain in their specified later phases.

From the repository directory, use `python tools/run.py doctor --json` for read-only host probes and `python tools/run.py tools-lock --json` to resume P00 dependency preparation. Login/MFA remains with the operator. Run host probes in a normal session when sandbox access is denied; do not reinstall working tools in response to a sandbox error.

P01 will place these prepared locks in the final application layout. P01 has not started.
