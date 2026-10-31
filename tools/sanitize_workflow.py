"""Make a public-review copy of a ComfyUI MiniMax H3 workflow.

This leaves the source untouched and removes embedded media references,
prompts, prompt history, cached previews and free-form author notes.
It does not read or delete the referenced media on disk.
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path


SAFE_NOTES = {
    249: "XINGYU public template. Install all required ComfyUI nodes and model files separately. No user images, prompts, or generated results are included.",
    251: "Workflow adapted for public demonstration by XINGYU. Original AISEEK workflow material and third-party nodes retain their own attribution. See THIRD_PARTY_NOTICES.md.",
    304: "Real-ESRGAN 4K output is experimental. Replace the example input and supply your own prompt before testing.",
}


def sanitize(document: dict) -> tuple[dict, dict]:
    if not isinstance(document.get("nodes"), list) or not isinstance(document.get("links"), list):
        raise ValueError("Expected ComfyUI UI workflow with nodes and links")

    output = json.loads(json.dumps(document))
    output["id"] = str(uuid.uuid4())
    output["revision"] = 0
    summary = {"input_images_cleared": 0, "prompt_states_cleared": 0,
               "notes_replaced": 0, "video_previews_cleared": 0}

    for group in output.get("groups", []):
        group["title"] = "MiniMax H3 generation and 4K upscale"

    extra = output.get("extra", {})
    output["extra"] = {key: extra[key] for key in
                       ("frontendVersion", "workflowRendererVersion", "node_versions")
                       if key in extra}
    output["extra"]["VHS_MetadataImage"] = False

    for node in output["nodes"]:
        kind = node.get("type")
        node_id = node.get("id")
        # Custom titles and notes can contain personally written material.
        node.pop("title", None)
        props = node.get("properties") or {}
        props.pop("aux_id", None)  # Do not reuse local video preview cache identity.

        if kind == "LoadImage":
            node["title"] = "Input image - choose your own file"
            node["widgets_values"] = ["example_input.png", "image"]
            summary["input_images_cleared"] += 1

        elif kind == "PixaromaPrompt":
            node["title"] = "Your prompt (blank in public template)"
            node["widgets_values"] = [""]
            props["promptState"] = {
                "text": "", "lastRun": "", "order": "keep", "sep": ", ",
                "accent": None, "showExpanded": False,
            }
            summary["prompt_states_cleared"] += 1

        elif kind == "MiniMaxH3ImageToVideo":
            values = node.get("widgets_values", [])
            if isinstance(values, list) and values and isinstance(values[0], str):
                values[0] = ""

        elif kind in {"MarkdownNote", "Note"}:
            node["widgets_values"] = [SAFE_NOTES.get(node_id,
                                         "Public template: personal data removed.")]
            summary["notes_replaced"] += 1

        elif kind == "Label (rgthree)":
            node["title"] = {
                247: "XINGYU MiniMax H3 to 4K",
                248: "Required models",
                253: "XINGYU",
            }.get(node_id, "XINGYU public workflow")

        elif kind == "VHS_VideoCombine":
            values = node.get("widgets_values", {})
            if not isinstance(values, dict):
                raise ValueError("Unexpected VHS_VideoCombine widget format")
            values["filename_prefix"] = "XINGYU/PublicDemo"
            values["videopreview"] = ""
            values["save_metadata"] = False
            summary["video_previews_cleared"] += 1

        elif kind == "PixaromaDuration":
            state = props.get("durationState")
            if isinstance(state, dict):
                state["recipeName"] = "Default"
                state["formula"] = ""

        # Preserve model names, numeric settings, link IDs and positions.
        node["properties"] = props

    return output, summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("destination", type=Path)
    args = ap.parse_args()
    if args.source.resolve() == args.destination.resolve():
        ap.error("Source and destination must differ")
    if args.destination.exists():
        ap.error("Destination already exists; will not overwrite")

    source = json.loads(args.source.read_text(encoding="utf-8"))
    cleaned, report = sanitize(source)
    if (len(cleaned["nodes"]) != len(source["nodes"]) or
            cleaned["links"] != source["links"] or
            [n["type"] for n in cleaned["nodes"]] !=
            [n["type"] for n in source["nodes"]]):
        raise AssertionError("Sanitization changed workflow topology")

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with args.destination.open("x", encoding="utf-8") as handle:
        json.dump(cleaned, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(json.dumps({"nodes_preserved": len(cleaned["nodes"]),
                      "links_preserved": len(cleaned["links"]), **report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())