# Astro-Health-Companion

An offline-capable, evidence-grounded astronaut health monitoring and
decision-support prototype for NASA Space Apps Challenge 2026.

## Repository structure

```text
Astro-Health-Companion/
├── frontend/       # User interface and client-side application
├── backend/        # API, services, and application business logic
├── rag/            # Retrieval-augmented generation pipeline
├── research/       # Research notes, sources, and domain findings
├── data/           # Curated datasets and data-processing assets
├── tests/          # Cross-component and integration tests
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   └── limitations.md
├── assets/         # Shared images, diagrams, and other static assets
├── README.md
├── CONTRIBUTING.md
└── .gitignore
```

Each top-level area has an `OWNERS.md` file describing its initial owner and
scope. Keep component-specific setup instructions in that component's folder
as implementation begins.

## Getting started

The project is currently scaffolded. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the planned workflow and [docs/architecture.md](docs/architecture.md) for
the initial component boundaries.
