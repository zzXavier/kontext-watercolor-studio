# Workflow and model provenance

The original author's watercolor exercise was built from the official ComfyUI FLUX.1 Kontext two-reference template. The archived single-input graph is byte-identical to that practice file (SHA-256 `a4c0cf60a5241002ace4c462cbc9dab8e2a52aaf496b0bf376e05987fe7c2703`). It uses the standard FP8 Kontext weights and the original watercolor prompt. This repository adds a lower-memory GGUF graph, an editable version of that graph, two attributed photo fixtures, a second style instruction, local HTTP execution, checksummed outputs and paired visual review.

| Component | Fixed source | Use |
|---|---|---|
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI/tree/d5c1954d5cd4a789bbf84d2b75a955a5a3f93de8) | v0.3.50 | Original server, FLUX denoiser, reference conditioning, VAE, sampler and image API |
| [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF/tree/cf0573351ac260d629d460d97f09b09ac17d3726) | cf0573351ac260d629d460d97f09b09ac17d3726 | Quantized denoiser and dual text-encoder loading |
| [Official Kontext template](https://github.com/Comfy-Org/workflow_templates/blob/cf21215380f6c22ddcea68568006f502a3ae355d/templates/flux_kontext_dev_basic.json) | cf21215380f6c22ddcea68568006f502a3ae355d | Reference graph, positive-conditioning route, guidance and Euler/simple sampling |

The server and custom nodes are installed separately with their own license notices. The [immutable weight manifest](configs/model-manifest.json) records repository IDs, revisions, original filenames, sizes and publisher hashes. The four large files stay outside Git.

- The FLUX.1 Kontext [dev] quantization comes from [QuantStack](https://huggingface.co/QuantStack/FLUX.1-Kontext-dev-GGUF/tree/2d083027732f81e5548620b57ac47da22d30aa5a). The original model is [Black Forest Labs FLUX.1 Kontext [dev]](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev). Consult the FLUX.1 [dev] non-commercial license and usage policy linked by the publisher.
- The T5 encoder is released by [city96](https://huggingface.co/city96/t5-v1_1-xxl-encoder-gguf/tree/005a6ea51a7d0b84d677b3e633bb52a8c85a83d9). CLIP-L is distributed in [Comfy Anonymous' FLUX text encoders](https://huggingface.co/comfyanonymous/flux_text_encoders/tree/6af2a98e3f615bdfa612fbd85da93d1ed5f69ef5). The FLUX VAE is the unmodified `ae.safetensors` released in [Comfy-Org's split bundle](https://huggingface.co/Comfy-Org/Lumina-Image-2/tree/5b072540ef86570fecb8249c505f23d5bdeb88cd).
- The two packaged photographs and their credits are documented in [SOURCES.md](examples/SOURCES.md).
