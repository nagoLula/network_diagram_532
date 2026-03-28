# Network Diagram Project

Create Activity-on-Node (PDM) and Activity-on-Arrow (ADM) network diagrams directly from the CPM schedule data tracked in `data/network_activities.csv`.

## Requirements

- Python 3.10+ (a `.venv` is provided; activate it or rely on VS Code's default interpreter)

## Usage

1. Update `data/network_activities.csv` with the latest activities, predecessors, and timing data.
2. Generate both diagrams:

```bash
python scripts/generate_diagrams.py --csv data/network_activities.csv --out-dir diagrams
```(VS Code terminals that know about the workspace `venv` can also run the command shown above without the explicit interpreter path.)
1. Open `diagrams/pdm_network.md` and `diagrams/adm_network.md` in the Markdown preview (`Ctrl+Shift+V`) to inspect or export the Mermaid diagrams.

## Files
- `scripts/generate_diagrams.py` – reads the CSV and emits the Mermaid markdown.
- `data/network_activities.csv` – authoritative activity table.
- `diagrams/*.md` – generated diagram sources you can preview or embed elsewhere.

**Course:** HHA 531.01-02 Health Information Systems  
**Student:** Naira Khergiani  
**Assignment:** Lab 2 — Training Plan Development (Network Diagram and CPM Analysis)  
**Due Date:** March 31, 2026

## Purpose

This repository contains the Activity-on-Node (PDM) and Activity-on-Arrow (ADM) network diagrams, the CPM analysis, and supporting data for the network diagram assignment.

## Structure

- `diagrams/` — Mermaid `.md` files with PDM and ADM diagrams.
- `data/` — `network_activities.csv` (activity table with ES/EF/LS/LF/Slack).
- `docs/` — submission-ready exports (PDF/PNG).
- `examples/` — minimal example to verify Mermaid preview.
- `README.md`, `LICENSE`, `.gitignore` — repo metadata.

## How to preview diagrams (VS Code)

1. Open the repository folder in VS Code.  
2. Install **Markdown Preview Mermaid Support** extension.  
3. Open a `.md` file in `diagrams/` and press **Ctrl+Shift+V** to preview.

## How to export for submission

- Quick: preview and take a screenshot.  
- Full document: install **Markdown PDF** extension and use **Markdown PDF: Export (pdf)**.

## Git workflow (recommended)

```bash
git checkout -b feature/diagrams
git add .
git commit -m "Add diagrams and data"
git push origin feature/diagrams
# When ready:
git tag -a v1.0-submission -m "Submission v1.0"
git push origin v1.0-submission
