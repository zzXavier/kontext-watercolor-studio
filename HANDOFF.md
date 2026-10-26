# Handoff

The original single-photo FP8 exercise is archived in `workflows/original-fp8.json`. Its completion was previously confirmed by the author. Its source photo and original generated image were unavailable for independent inspection.

## Verified compact workflow

The new Q4_K_S Kontext workflow produced four archived images via the local ComfyUI HTTP API. The source PNG, generated PNG, graph and receipt are included for each case in [results](results/manifest.json). Five regression tests passed. A live headless browser imported the 13 nodes into the pinned frontend and exported an executable graph identical to the shipped API graph. A real 512 × 512 image upload/save probe preserved every RGB channel. The formal graph then ran FLUX.1 Kontext editing on both real photographs and both prompts.

The model digests in `configs/model-manifest.json` all matched. The server ran in an independent Python 3.11 environment, with torch 2.4.1+cu121 and ComfyUI v0.3.50 on a GeForce RTX 4060 Laptop 8 GB. The 0.5-megapixel comparison used the original seed 42, twenty steps and model guidance 2.5. Four completed receipts were checked offline. No timing here describes the old FP8 practice.

Next offline check from a fresh clone: `python run.py evaluate --out results`. Next GPU reproduction after server startup: `python run.py reproduce --out work/independent`. To view a single new instance, use `python run.py render photo.jpg --preset transparent-wash --out work/new-painting`. The server requires the pinned core and custom-node revisions. The historical FP8 workflow has different weight requirements from the archived comparison.
