# XINGYU Mac Video Toolkit

**An experimental Apple Silicon ComfyUI workflow for MiniMax H3 video generation followed by Real-ESRGAN 4K upscaling, plus independent diagnostic tools.**

Maintainer: **XINGYU** ([zhuxingyu191-dot](https://github.com/zhuxingyu191-dot))

## Main public workflow

Open `workflows/XINGYU_MiniMax_H3_RealESRGAN_4K_Public.json` in ComfyUI. This 27-node, 26-link template preserves the local video generation and 4K upscale graph. It intentionally does **not** include an input image, a personal prompt, generated outputs, model weights, or the original author's promotional notes. The missing-media warning is expected until you select your own input file.

**Status:** This is an experimental publicly shareable template, not a verified turnkey installation. A clean-machine end-to-end 4K run has **not** been confirmed. Some custom nodes, MLX model files, and software dependencies must be installed separately.

### Workflow at a glance

1. Load compatible MiniMax H3 UNET, Qwen3-VL CLIP, video/audio VAEs and optional LoRAs.
2. Choose your own image and enter your own prompt.
3. Generate video through the MiniMax H3 Image to Video node.
4. Upscale video frames with RealESRGAN_x4plus and export via VideoHelperSuite.

The model names in the workflow are references, not bundled downloads. They may require compatible versions or adaptation to your system. The included workflow is derived/adapted from an existing AISEEK-branded local workflow: **XINGYU does not claim original authorship of its upstream workflow design or custom nodes.** See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Additional tools

Independent Python CLI functions:
- `check-env`: inspect local macOS architecture, Python, FFmpeg and MLX availability.
- `inspect-workflow`: list node types and model names, and flag potential leaked paths and credentials (heuristic only; manual review is still required).
- `probe-video`: use ffprobe to summarize media export specifications.

A separate `XINGYU_SeedVR2_Portrait_4K_Experimental.json` illustrates another upscaling path; this is **not** the primary full workflow.

## Setup and tests

Python 3.10+ for the CLI; actual video generation also requires ComfyUI, third-party nodes and separately licensed model weights. For CLI-only local checks:

```bash
PYTHONPATH=src python3.11 -m xingyu_video_tools.cli check-env
PYTHONPATH=src python3.11 -m xingyu_video_tools.cli inspect-workflow workflows/XINGYU_MiniMax_H3_RealESRGAN_4K_Public.json --strict
python3.11 -m unittest discover -s tests -v
```

Optional CLI installation:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
xingyu-video check-env
```

The basic CLI unit tests passed in the maintainer's local environment. That is **not** proof that every GPU workflow node executes successfully.

## Privacy and attribution

Before publishing your own workflow, remove private prompts, filenames, account IDs, embedded previews, paths and generated outputs. `--strict` is not a security guarantee. No personal media or models are included here. XINGYU's original code/documentation is MIT-licensed; upstream nodes, models, and source workflows remain governed by their respective licenses and attributions.

## Roadmap

- Reproduce clean Mac setup and document dependencies.
- Run a full generation-to-4K benchmark and report verified timings.
- Improve privacy scanning and test coverage.
- Triage issues and review community contributions.