# Handoff

The original single-photo FP8 exercise is archived in `workflows/original-fp8.json`. Its completion was previously confirmed by the author, and no original output image was available for independent inspection. Current-machine renders are tracked separately.

The quantized executable graph and editable UI graph have been wired to the same FLUX.1 Kontext reference-conditioning structure. Five regression tests check the reference path, API/UI agreement, request validation, output integrity and incomplete batches. A live headless browser imported the 13 nodes into the pinned ComfyUI frontend and exported exactly the same execution graph. A real 512 × 512 HTTP upload/save probe returned every input RGB channel unchanged. The source photographs and four model assets have pinned hashes.

Start from the README's two-terminal recipe. To rerun the studio on a machine with a prepared server, use `python run.py demo --out work/portrait`. To verify a full saved comparison, use `python run.py evaluate --out results`.
