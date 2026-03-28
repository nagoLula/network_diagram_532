#!/usr/bin/env python3
"""
generate_mermaid_from_csv.py

Reads a CSV with columns:
Activity,Immediate Predecessor,Duration,ES,EF,LS,LF,Slack,Critical

Generates:
- diagrams/pdm_network.mmd   (Mermaid code only)
- diagrams/pdm_network.md    (Markdown file with ```mermaid fenced block for VS Code preview)
"""

import csv
import os
import sys

# Input CSV path (first CLI arg) or default
csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/network_activities.csv"
out_dir = "diagrams"
os.makedirs(out_dir, exist_ok=True)

activities = {}
edges = []

# Helper to split predecessor field
def split_preds(s):
    if not s:
        return []
    s = s.strip()
    # Accept separators ; or , or space
    for sep in [";", ","]:
        if sep in s:
            return [p.strip() for p in s.split(sep) if p.strip()]
    return [s] if s else []

with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        act = row.get("Activity", "").strip()
        pred = row.get("Immediate Predecessor", "").strip()
        dur = row.get("Duration", "").strip()
        ES = row.get("ES", "").strip()
        EF = row.get("EF", "").strip()
        LS = row.get("LS", "").strip()
        LF = row.get("LF", "").strip()
        Slack = row.get("Slack", "").strip()
        Critical = row.get("Critical", "").strip()

        # Build label with safe <br> line breaks
        label_lines = []
        if dur:
            label_lines.append(f"{act} ({dur})")
        else:
            label_lines.append(f"{act}")
        if ES or EF:
            label_lines.append(f"ES{ES} EF{EF}")
        if LS or LF:
            label_lines.append(f"LS{LS} LF{LF}")
        if Slack:
            label_lines.append(f"Slack{Slack}")
        label = "<br>".join(label_lines)

        activities[act] = {
            "label": label,
            "critical": Critical.lower() in ("yes", "true", "1")
        }

        preds = split_preds(pred)
        for p in preds:
            edges.append((p, act))

# Build Mermaid PDM code
lines: list[str] = []
lines.append('flowchart TD')
lines.append('    classDef critical fill=#ffcccc,stroke=#ff0000,stroke-width=2px;')

# Nodes
for act, info in activities.items():
    # Escape double quotes in label
    safe_label = info["label"].replace('"', '\\"')
    node_line = f'    {act}["{safe_label}"]'
    if info["critical"]:
        node_line += ':::critical'
    lines.append(node_line)

# Edges
for a, b in edges:
    if a not in activities:
        # If predecessor not in CSV, create a simple node for it
        lines.append(f'    {a}["{a}"]')
        activities[a] = {"label": a, "critical": False}
    lines.append(f'    {a} --> {b}')

pdm_mmd = "\n".join(lines) + "\n"

# Write .mmd (Mermaid code only)
mmd_path = os.path.join(out_dir, "pdm_network.mmd")
with open(mmd_path, "w", encoding="utf-8") as f:
    f.write(pdm_mmd)

# Also write a Markdown file with fenced block for VS Code preview
md_path = os.path.join(out_dir, "pdm_network.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("```mermaid\n")
    f.write(pdm_mmd)
    f.write("```\n")

print(f"Wrote: {mmd_path}")
print(f"Wrote: {md_path}")
