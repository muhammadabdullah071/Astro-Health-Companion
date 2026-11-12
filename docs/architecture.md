# Architecture

## Planned components

- **Frontend**: Presents health status, evidence, alerts, and decision-support
  recommendations to users.
- **Backend**: Exposes the application API, coordinates domain services, and
  validates requests.
- **RAG**: Ingests approved sources, retrieves relevant evidence, and prepares
  grounded context for responses.
- **Data**: Stores curated datasets and reproducible data-processing inputs.
- **Research**: Maintains source evaluations, domain assumptions, and research
  decisions.
- **Tests**: Contains cross-component checks and shared test fixtures.

The frontend should communicate with the backend through the interface defined
in [api-contract.md](api-contract.md). The backend may use the RAG and data
components, while research documentation provides provenance for the evidence
used by the system.

## Design principles

- Prefer offline-capable workflows where practical.
- Keep evidence provenance visible and traceable.
- Validate inputs at component boundaries.
- Treat health recommendations as decision support, not a replacement for
  professional medical judgment.
