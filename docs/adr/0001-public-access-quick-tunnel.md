# ADR 0001: Accountless Cloudflare Quick Tunnel for public access

Status: accepted by the user on 19 October 2026.

The user selected Quick Tunnel after comparing it with Tailscale Funnel and Vercel. Their instruction, "ok then let's use quick tunnel", replaces the original Tailscale-first routing decision in PRD/implementation plan version 1.0.

Use the pinned project-local cloudflared 2026.10.1 binary to forward public HTTPS requests only to `http://127.0.0.1:8080`, the existing local Kubernetes gateway contract. The accountless Quick Tunnel requires no login/MFA, auth key, Cloudflare account, purchased domain, DNS setup or Tailscale installation. It changes only public routing; compute, persistence, Kubernetes, monitoring and delivery architecture remain as specified.

The assigned `*.trycloudflare.com` hostname changes on each new tunnel process. There is no uptime guarantee. The official service is intended for testing/development, caps concurrent in-flight requests at 200, and does not support SSE. These constraints fit the course demonstration; no SSE feature is required. Keep actual PUBLIC_BASE_URL/operator state and assessment links current. The local host, cluster, tunnel process and internet must remain available.

P00 verifies binary provenance/execution and records the selected free route. P16 starts the actual application tunnel after Kubernetes gateway smoke passes, records the assigned URL and verifies the real application externally. Preparing cloudflared does not establish a deployed or publicly verified application. Admin surfaces remain excluded from routing.

The downloaded Tailscale MSI is retained as historical local preparation, uninstalled and no longer required. Previous P00 documents/reports are archived under ignored `.local/reports/p00-before-quick-tunnel/`. Original validation data and design references remain preserved.

Sources: [Quick Tunnel setup and limits](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), [official cloudflared release](https://github.com/cloudflare/cloudflared/releases/tag/2026.10.1).
