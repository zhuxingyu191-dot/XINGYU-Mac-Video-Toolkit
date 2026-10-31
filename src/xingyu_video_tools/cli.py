"""Dependency-free diagnostics for local ComfyUI video workflows.

This module never runs a workflow, downloads model weights, or uploads files.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PRIVATE_PATTERNS = {
    "absolute user path": re.compile(r"(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\\\Users\\\\[^\\\\\s]+\\\\)"),
    "credential-shaped text": re.compile(r"(?:sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9_.-]{12,}|gh[pousr]_[A-Za-z0-9]{15,})", re.I),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
MEDIA_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".pth", ".onnx", ".gguf")


def _string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _string_values(child)


def analyze_workflow(document: dict[str, Any]) -> dict[str, Any]:
    """Summarize a ComfyUI UI workflow or API-format prompt without dumping prompts."""
    if isinstance(document.get("nodes"), list):
        nodes = document["nodes"]
        types = [n.get("type", "unknown") for n in nodes if isinstance(n, dict)]
    else:
        nodes = [n for n in document.values() if isinstance(n, dict) and "class_type" in n]
        types = [n.get("class_type", "unknown") for n in nodes]
    if not nodes:
        raise ValueError("No ComfyUI nodes found in workflow JSON")

    detected = set()
    models = set()
    for value in _string_values(document):
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(value):
                detected.add(label)
        if value.lower().endswith(MEDIA_EXTENSIONS) and len(value) < 255:
            models.add(Path(value).name)

    return {
        "node_count": len(nodes),
        "node_types": dict(sorted(Counter(map(str, types)).items())),
        "referenced_model_filenames": sorted(models),
        "privacy_warnings": sorted(detected),
    }


def probe_metadata(filename: Path) -> dict[str, Any]:
    """Return video stream facts reported by ffprobe (no decoding or network)."""
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is not installed; install FFmpeg first")
    process = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(filename)],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(process.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("No video stream found")
    return {
        "width": video.get("width"),
        "height": video.get("height"),
        "codec": video.get("codec_name"),
        "pixel_format": video.get("pix_fmt"),
        "frame_rate": video.get("avg_frame_rate"),
        "duration_seconds": data.get("format", {}).get("duration"),
        "has_audio": any(s.get("codec_type") == "audio" for s in data.get("streams", [])),
        "alpha_possible": "a" in (video.get("pix_fmt") or "").lower()
        and (video.get("pix_fmt") or "").lower() not in {"yuv420p", "yuv422p", "yuv444p"},
    }


def environment_report() -> dict[str, Any]:
    try:
        mlx_present = importlib.util.find_spec("mlx") is not None
    except (ModuleNotFoundError, ValueError):
        mlx_present = False
    return {
        "system": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "mlx_python_package_detected": mlx_present,
        "note": "Package detection does not establish GPU or model compatibility.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xingyu-video", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-env", help="Report local Python, FFmpeg and MLX availability")
    workflow = sub.add_parser("inspect-workflow", help="Summarize and privacy-check a ComfyUI JSON")
    workflow.add_argument("path", type=Path)
    workflow.add_argument("--strict", action="store_true", help="Exit with code 2 if privacy warnings are detected")
    video = sub.add_parser("probe-video", help="Inspect a local video using ffprobe")
    video.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check-env":
            result = environment_report()
        elif args.command == "inspect-workflow":
            if args.path.stat().st_size > 10_000_000:
                raise ValueError("Workflow file exceeds the 10 MB safety limit")
            result = analyze_workflow(json.loads(args.path.read_text(encoding="utf-8")))
        else:
            if not args.path.is_file():
                raise FileNotFoundError(args.path)
            result = probe_metadata(args.path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == "inspect-workflow" and args.strict and result["privacy_warnings"]:
            return 2
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
