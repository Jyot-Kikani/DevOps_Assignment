# DevOps topics mapped to our implementation

Stellar Atlas implements the eight DevOps topics listed as **DV01–DV08** in
[the project requirements](PRD.md#8-devops-acceptance-requirements).

| Topic | How we implemented it |
|---|---|
| **1. Microservices** | Six backend APIs: **Catalog, Search, Atlas Map, Snapshot, Calculation and Journey**, each with its own contract, image and Kubernetes Deployment. Journey calls Calculation, which requests positions from Catalog over HTTP. The four catalog readers share read-only access; Journey has its separate database role. See [the service map](SIX_SERVICES.md). |
| **2. Docker** | Dockerfiles package the services; **Docker Compose** runs the local application. Images use pinned bases, non-root users and health checks. Release images are published to **GitHub Container Registry (GHCR)**. |
| **3. Infrastructure as Code (IaC)** | **kind configuration** defines the local cluster. **Terraform** defines platform resources, including namespaces, PostgreSQL storage and monitoring. We demonstrated apply, a no-change plan, and detection/repair of configuration drift. |
| **4. Kubernetes** | **kind** runs Kubernetes on the laptop. Deployments, Services, probes, resource limits, Jobs, a CronJob and persistent storage manage the application. We demonstrated pod replacement and scaling Journey **1 → 2 → 1**. |
| **5. CI/CD** | **GitHub Actions** checks pull requests, then builds, scans and publishes release images. The release updates the **`deploy` branch**; **Argo CD** reconciles those manifests into Kubernetes. We demonstrated a failed-test gate and Git rollback. |
| **6. DevSecOps** | **Gitleaks** checks for secrets; **Grype** scans images. Applications run as non-root, credentials stay outside Git, and administrative services remain private. Grype's failed severity thresholds remain documented. |
| **7. Local deployment and operations** | The application runs on the existing laptop with documented start/stop commands. **Prometheus + Grafana** provide monitoring; a **PVC** preserves database data; host backups and an isolated restore demonstrate recovery. |
| **8. Public URL** | **Cloudflare Quick Tunnel** provides a temporary public HTTPS URL to the local web gateway. External phone access was demonstrated. Availability depends on the laptop, cluster, tunnel and internet remaining active. |

## Evidence and scope

The [course-topic evidence table](P23_SUBMISSION.md#course-topic-evidence) links
each topic to its recorded demonstrations. That table has nine rows because it
also includes **Product/data**; the formal DevOps requirements contain eight topics.
Monitoring, backup and recovery are included under local deployment and operations.

These are implemented capabilities with recorded evidence, not a claim that the
deployment or public URL is currently running. See the
[acceptance register](ACCEPTANCE.md) and batch reports for validation and limitations.
