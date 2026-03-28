from __future__ import annotations

from typing import Dict, List, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    try:
        from scripts.generate_diagrams import Activity
    except ModuleNotFoundError:  # when run directly from scripts/
        from generate_diagrams import Activity


def assign_events(order: Sequence[str], activities_by_name: Dict[str, Activity]) -> Tuple[Dict[int, str], List[Tuple[int, int]]]:
    event_labels: Dict[int, str] = {1: "1"}
    next_event_id = 1
    merge_cache: Dict[Tuple[int, ...], int] = {}
    dummy_edges: List[Tuple[int, int]] = []
    dummy_seen: set[Tuple[int, int]] = set()

    for name in order:
        act = activities_by_name[name]
        if not act.predecessors:
            start_event = 1
        else:
            pred_events = tuple(sorted(activities_by_name[p].end_event for p in act.predecessors)) # type: ignore
            if any(event is None for event in pred_events):     # pyright: ignore[reportUnknownVariableType]

                raise ValueError(
                    f"Predecessor events missing while processing activity '{name}'"
                )

            if len(set(pred_events)) == 1: # type: ignore
                start_event = pred_events[0] # type: ignore
            else:
                key = pred_events # type: ignore
                if key not in merge_cache:
                    next_event_id += 1
                    merge_cache[key] = next_event_id
                    event_labels[next_event_id] = str(next_event_id)
                    for event_id in pred_events: # type: ignore
                        dummy_key = (event_id, next_event_id) # pyright: ignore[reportUnknownVariableType]
                        if dummy_key not in dummy_seen:
                            dummy_edges.append(dummy_key) # pyright: ignore[reportUnknownArgumentType]
                            dummy_seen.add(dummy_key) # pyright: ignore[reportUnknownArgumentType]
                start_event = merge_cache[key]

        next_event_id += 1
        end_event = next_event_id
        event_labels[end_event] = str(end_event)
        act.start_event = start_event
        act.end_event = end_event

    return event_labels, dummy_edges