from __future__ import annotations

import argparse
import csv
import heapq
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from scripts.assign_events import assign_events


@dataclass
class Activity:
    name: str
    predecessors: List[str]
    duration: int
    es: int
    ef: int
    ls: int
    lf: int
    slack: int
    critical: bool
    start_event: int | None = None
    end_event: int | None = None


def parse_int(value: str) -> int:
    value = (value or "").strip()
    return int(value) if value else 0


def parse_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"y", "yes", "true", "1"}


def parse_predecessors(raw_value: str) -> List[str]:
    if not raw_value:
        return []
    parts = re.split(r"[;,]", raw_value)
    return [part.strip() for part in parts if part.strip()]


def load_activities(csv_path: Path) -> List[Activity]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find CSV data at {csv_path}")

    activities: List[Activity] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = [
            "Activity",
            "Immediate Predecessor",
            "Duration",
            "ES",
            "EF",
            "LS",
            "LF",
            "Slack",
            "Critical",
        ]
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing headers")
        missing = [field for field in expected if field not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV file is missing required columns: {', '.join(missing)}")

        for row in reader:
            name = (row.get("Activity") or "").strip()
            if not name:
                raise ValueError("Encountered an activity row without a name")
            activity = Activity(
                name=name,
                predecessors=parse_predecessors(row.get("Immediate Predecessor", "")),
                duration=parse_int(row.get("Duration", "0")),
                es=parse_int(row.get("ES", "0")),
                ef=parse_int(row.get("EF", "0")),
                ls=parse_int(row.get("LS", "0")),
                lf=parse_int(row.get("LF", "0")),
                slack=parse_int(row.get("Slack", "0")),
                critical=parse_bool(row.get("Critical", "")),
            )
            activities.append(activity)

    names = [act.name for act in activities]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        raise ValueError(f"Duplicated activity names found: {', '.join(sorted(duplicates))}")

    valid_names = {act.name for act in activities}
    for act in activities:
        for pred in act.predecessors:
            if pred not in valid_names:
                raise ValueError(
                    f"Activity '{act.name}' references missing predecessor '{pred}'"
                )
    return activities


def dependency_maps(
    activities: Sequence[Activity],
) -> Tuple[Dict[str, int], Dict[str, List[str]], Dict[str, int]]:
    order_index = {act.name: idx for idx, act in enumerate(activities)}
    successors: Dict[str, List[str]] = defaultdict(list)
    indegree: Dict[str, int] = {}
    for act in activities:
        indegree[act.name] = len(act.predecessors)
        for pred in act.predecessors:
            successors[pred].append(act.name)
    return order_index, successors, indegree


def topo_order(
    activities: Sequence[Activity],
) -> Tuple[List[str], Dict[str, List[str]]]:
    order_index, successors, indegree = dependency_maps(activities)
    heap: List[Tuple[int, str]] = []
    for name, degree in indegree.items():
        if degree == 0:
            heapq.heappush(heap, (order_index[name], name))

    order: List[str] = []
    while heap:
        _, name = heapq.heappop(heap)
        order.append(name)
        for child in successors.get(name, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(heap, (order_index[child], child))

    if len(order) != len(activities):
        raise ValueError(
            "Detected a cycle or orphaned dependency in the activity definitions"
        )
    return order, successors


def build_pdm_mermaid_lines(
    activities: Sequence[Activity], successors: Dict[str, List[str]]
) -> List[str]:
    lines = [
        "flowchart TD",
        "    classDef critical fill:#ffcccc,stroke:#ff0000,stroke-width:2px;",
        "",
    ]

    for act in activities:
        label = (
            f"{act.name} ({act.duration})<br>"
            f"ES{act.es} EF{act.ef}<br>"
            f"LS{act.ls} LF{act.lf}<br>"
            f"Slack{act.slack}"
        )
        node_line = f'    {act.name}["{label}"]'
        if act.critical:
            node_line += ":::critical"
        lines.append(node_line)

    lines.append("")
    for act in activities:
        for child in successors.get(act.name, []):
            lines.append(f"    {act.name} --> {child}")

    return lines


def build_adm_mermaid_lines(activities: Sequence[Activity], order: Sequence[str]) -> List[str]:
    activities_by_name = {act.name: act for act in activities}
    event_labels, dummy_edges = assign_events(order, activities_by_name)

    lines: List[str] = [
        "flowchart LR",
        "    classDef critical stroke:#ff0000,stroke-width:2px,color:#ff0000;",
        "",
    ]

    for event_id in sorted(event_labels):
        label = event_labels[event_id]
        lines.append(f"    E{event_id}(({label}))")

    lines.append("")

    def format_event(event_id: int | None) -> str:
        resolved = event_id or 1
        return f"E{resolved}"

    for act in activities:
        start_node = format_event(act.start_event)
        end_node = format_event(act.end_event)
        edge_line = f"    {start_node} -->|{act.name} ({act.duration})| {end_node}"
        lines.append(edge_line)

    for from_event, to_event in dummy_edges:
        start_node = format_event(from_event)
        end_node = format_event(to_event)
        lines.append(f"    {start_node} -->|dummy| {end_node}")

    return lines


def render_markdown(title: str, mermaid_lines: Sequence[str]) -> str:
    body = "\n".join(mermaid_lines)
    return "\n".join(
        [
            f"# {title}",
            "",
            "```mermaid",
            body,
            "```",
            "",
            "_Generated by scripts/generate_diagrams.py_",
        ]
    )




def write_output(content: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid network diagrams from CPM activity data",
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to the CSV file containing the activity data",
    )
    parser.add_argument(
        "--out-dir",
        default="diagrams",
        help="Directory where the diagram markdown files will be written",
    )
    parser.add_argument(
        "--pdm-name",
        default="pdm_network.md",
        help="Filename for the precedence diagram method output",
    )
    parser.add_argument(
        "--adm-name",
        default="adm_network.md",
        help="Filename for the activity-on-arrow output",
    )
    parser.add_argument(
        "--pdm-mmd-name",
        default="pdm_network.mmd",
        help="Filename for the raw PDM Mermaid definition",
    )
    parser.add_argument(
        "--adm-mmd-name",
        default="adm_network.mmd",
        help="Filename for the raw ADM Mermaid definition",
    )
    return parser


def main(args: Iterable[str] | None = None) -> None:
    parser = build_parser()
    parsed = parser.parse_args(args=args) # pyright: ignore[reportArgumentType]

    csv_path = Path(parsed.csv)
    activities = load_activities(csv_path)
    order, successors = topo_order(activities)

    pdm_lines = build_pdm_mermaid_lines(activities, successors)
    adm_lines = build_adm_mermaid_lines(activities, order)

    pdm_markdown = render_markdown("PDM Network Diagram", pdm_lines)
    adm_markdown = render_markdown("ADM Network Diagram", adm_lines)
    pdm_source = "\n".join(pdm_lines)
    adm_source = "\n".join(adm_lines)

    out_dir = Path(parsed.out_dir)
    pdm_path = out_dir / parsed.pdm_name
    adm_path = out_dir / parsed.adm_name
    pdm_mmd_path = out_dir / parsed.pdm_mmd_name
    adm_mmd_path = out_dir / parsed.adm_mmd_name

    write_output(pdm_markdown, pdm_path)
    write_output(pdm_source, pdm_mmd_path)
    write_output(adm_markdown, adm_path)
    write_output(adm_source, adm_mmd_path)

    print(f"Wrote {pdm_path}")
    print(f"Wrote {pdm_mmd_path}")
    print(f"Wrote {adm_path}")
    print(f"Wrote {adm_mmd_path}")


if __name__ == "__main__":
    main()
