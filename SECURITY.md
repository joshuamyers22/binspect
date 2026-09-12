# Security policy

`binspect` is an in-process statistical library. It has no network listener, but
caller inputs, dependencies, builds and published artifacts cross trust boundaries.
See the [threat model](docs/THREAT_MODEL.md) for current checks and open risks.

Please do not file vulnerability details or sensitive reproductions in public
issues, discussions or pull requests. GitHub private vulnerability reporting was
**disabled when checked on 2026-09-12**; no alternative private channel has been
verified. Josh Myers must enable that feature or publish a verified private route
before release (G1/R1). If the repository's Security tab offers “Report a
vulnerability,” use that private flow; otherwise withhold sensitive details until
a private route is available. This documented gap does not make public disclosure
the recommended reporting channel.

Once a private route is available, include affected versions, impact and a minimal
synthetic reproduction. Until a stable release exists, only the latest development
version receives security fixes. There is no promised response-time SLA.

The library does not automatically transmit inputs or collect usage telemetry.
Returned tables, JSON, figures, warnings and errors can contain names, ranges or
other sensitive information; summaries are not anonymization, and exceptions are
not guaranteed to be redacted. Callers own redaction, retention and access control.
Applications accepting hostile workloads must impose resource limits and isolation;
general allocation limits remain open under P1.
