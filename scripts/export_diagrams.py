from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Sequence

MERMAID_BLOCK = re.compile(r"```mermaid\s*(.*?)```", re.DOTALL)


def default_mmdc_executable() -> str:
    windows_candidate = Path.home() / "AppData" / "Roaming" / "npm" / "mmdc.cmd"
    if windows_candidate.exists():
        return str(windows_candidate)
    return "mmdc"


def extract_mermaid(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = MERMAID_BLOCK.search(text)
    if not match:
        raise ValueError(f"No mermaid block found in {path}")
    return match.group(1).strip()


def read_mermaid_source(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return extract_mermaid(path)
    return path.read_text(encoding="utf-8").strip()


def download_diagram(code: str, fmt: str) -> bytes:
    url = f"https://kroki.io/mermaid/{fmt}"
    payload = json.dumps({"diagram_source": code}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "User-Agent": "network-diagram-export/1.0",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as err:
        details = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Render failed ({err.code}): {details}") from err


def render_with_mmdc(code: str, source: Path, fmt: str, out_path: Path, executable: str) -> None:
    tmp_path: Path | None = None
    input_path = source
    if source.suffix.lower() == ".md":
        handle = tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False, encoding="utf-8")
        handle.write(code + "\n")
        handle.flush()
        handle.close()
        tmp_path = Path(handle.name)
        input_path = tmp_path

    cmd = [executable, "-i", str(input_path), "-o", str(out_path), "--outputFormat", fmt]
    env = os.environ.copy()
    node_dir = Path("C:/Program Files/nodejs")
    if node_dir.exists() and str(node_dir) not in env.get("PATH", ""):
        env["PATH"] = f"{node_dir}{os.pathsep}{env.get('PATH', '')}"
    try:
        subprocess.run(cmd, check=True, env=env)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


def export_file(
    source: Path,
    out_path: Path,
    fmt: str,
    backend: str,
    executable: str,
) -> None:
    code = read_mermaid_source(source)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if backend == "kroki":
        payload = download_diagram(code, fmt)
        out_path.write_bytes(payload)
    else:
        render_with_mmdc(code, source, fmt, out_path, executable)
    print(f"Wrote {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Mermaid diagrams to PNG/SVG using Kroki or the Mermaid CLI",
    )
    parser.add_argument("--diagrams-dir", default="diagrams", help="Directory containing the diagram files")
    parser.add_argument("--out-dir", default="docs", help="Output directory for the exported assets")
    parser.add_argument("--pdm-file", default="pdm_network.mmd", help="PDM diagram file (.mmd or .md)")
    parser.add_argument("--adm-file", default="adm_network.mmd", help="ADM diagram file (.mmd or .md)")
    parser.add_argument("--formats", nargs="+", default=["png"], choices=["png", "svg"], help="Formats to export")
    parser.add_argument("--backend", choices=["kroki", "mmdc"], default="mmdc", help="Rendering backend")
    parser.add_argument(
        "--mmdc-bin",
        default=default_mmdc_executable(),
        help="Path to the Mermaid CLI executable (when using the mmdc backend)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    diagrams_dir = Path(args.diagrams_dir)
    out_dir = Path(args.out_dir)

    sources = {
        "pdm": diagrams_dir / args.pdm_file,
        "adm": diagrams_dir / args.adm_file,
    }

    for label, path in sources.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing diagram source: {path}")
        for fmt in args.formats:
            extension = "svg" if fmt == "svg" else "png"
            target = out_dir / f"{label}_network.{extension}"
            export_file(path, target, fmt, args.backend, args.mmdc_bin)


if __name__ == "__main__":
    main()
