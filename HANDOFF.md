# Handoff

The original single-photo FP8 exercise is archived in `workflows/original-fp8.json`. Its completion was previously confirmed by the author. Its source photo and original generated image were unavailable for independent inspection.

## Verified compact workflow

The new Q4_K_S Kontext workflow produced four archived images via the local ComfyUI HTTP API. The source PNG, generated PNG, graph and receipt are included for each case in [results](results/manifest.json). Five regression tests passed. A live headless browser imported the 13 nodes into the pinned frontend and exported an executable graph identical to the shipped API graph. A real 512 × 512 image upload/save probe preserved every RGB channel. The formal graph then ran FLUX.1 Kontext editing on both real photographs and both prompts.

The model digests in `configs/model-manifest.json` all matched. The server ran in an independent Python 3.11 environment, with torch 2.4.1+cu121 and ComfyUI v0.3.50 on a GeForce RTX 4060 Laptop 8 GB. The 0.5-megapixel comparison used the original seed 42, twenty steps and model guidance 2.5. Four completed receipts were checked offline. No timing here describes the old FP8 practice.

Next offline check from a fresh clone: `python run.py evaluate --out results`. Next GPU reproduction after server startup: `python run.py reproduce --out work/independent`. To view a single new instance, use `python run.py render photo.jpg --preset transparent-wash --out work/new-painting`. The server requires the pinned core and custom-node revisions. The historical FP8 workflow has different weight requirements from the archived comparison.

## Independent acceptance

A clean, dissociated clone of commit `71df568a8e45757dba812282d2d0cbeff7582630` ran five tests, regenerated the archived gallery and summary, and reran all four edits on a fresh ComfyUI server using the durable model cache. Every sampler executed. The four PNG files matched byte for byte, with maximum RGB-channel difference zero. The second comparison sheet had SHA-256 `64fc5a1083f255a3c32bb8168994fc9b9a095b5c1481ace5f7d9b81d054eabc6`. Rerun durations were 140.407, 123.547, 127.813 and 122.156 seconds in manifest order. The [verification record](results/clean-clone-verification.json) includes both sets of output hashes, cache evidence and pixel counts.

To compare a subsequent four-image run, use `python scripts/compare_runs.py results work/independent`. Review the measured deltas if a different device, quantization or software stack is used.
