"""Photo editing over the local ComfyUI HTTP API. The graph is stored as editable JSON."""
import copy
import hashlib
import io
import json
import time
import uuid
from pathlib import Path

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / "configs/studio.json").read_text(encoding="utf-8"))
API = json.loads((ROOT / "workflows/watercolor-api.json").read_text(encoding="utf-8"))
MODEL_INPUTS = (("10", "unet_name"), ("5", "clip_name1"), ("5", "clip_name2"), ("3", "vae_name"))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def graph_for(image, prompt, seed, steps, megapixels):
    if not prompt.strip():
        raise ValueError("An edit instruction is required")
    if not 0 <= seed < 2**64 or not 1 <= steps <= 100 or not 0.10 <= megapixels <= 1.1:
        raise ValueError("Expected a 64-bit seed, 1–100 steps and 0.10–1.10 megapixels")
    graph = copy.deepcopy(API)
    graph["1"]["inputs"]["image"] = image
    graph["2"]["inputs"]["megapixels"] = megapixels
    graph["6"]["inputs"]["text"] = prompt
    graph["11"]["inputs"].update(seed=seed, steps=steps)
    return graph


class Comfy:
    def __init__(self, server):
        self.url = server.rstrip("/")
        self.http = requests.Session()
        self.http.trust_env = False

    def check(self):
        response = self.http.get(self.url + "/object_info", timeout=30)
        response.raise_for_status()
        nodes = response.json()
        missing = {n["class_type"] for n in API.values()} - nodes.keys()
        if missing:
            raise RuntimeError("Server is missing nodes: " + ", ".join(sorted(missing)))
        for node, key in MODEL_INPUTS:
            spec = API[node]
            options = nodes[spec["class_type"]]["input"]["required"][key][0]
            target = spec["inputs"][key]
            if target not in options:
                raise RuntimeError(f"Server cannot find {target}; check its extra-model-paths configuration and restart.")
        stats=self.http.get(self.url + "/system_stats",timeout=20)
        stats.raise_for_status()
        info=stats.json()
        system=info.get("system",{})
        return {"server":{k:system.get(k) for k in ("comfyui_version","python_version","pytorch_version")},
                "devices":[{k:d.get(k) for k in ("name","type","vram_total")} for d in info.get("devices",[])],
                "models":{k:API[n]["inputs"][k] for n,k in MODEL_INPUTS}}

    def upload(self, image_bytes):
        name = "kontext-watercolor-" + sha256(image_bytes)[:24] + ".png"
        response = self.http.post(self.url + "/upload/image",
            files={"image": (name, image_bytes, "image/png")},
            data={"type": "input", "overwrite": "true"}, timeout=60)
        response.raise_for_status()
        got = response.json()
        if got.get("type") != "input" or got.get("subfolder") not in ("", None) or got.get("name") != name:
            raise RuntimeError("Server returned an unexpected uploaded filename")
        return name

    def execute(self, graph, deadline):
        submitted = time.monotonic()
        response = self.http.post(self.url + "/prompt",
            json={"prompt":graph,"client_id":str(uuid.uuid4())}, timeout=30)
        if not response.ok:
            raise RuntimeError(f"Queue rejected workflow ({response.status_code}): {response.text[:1800]}")
        job = response.json()["prompt_id"]
        while time.monotonic() - submitted < deadline:
            response = self.http.get(f"{self.url}/history/{job}", timeout=30)
            response.raise_for_status()
            event = response.json().get(job)
            if event is None:
                time.sleep(.7)
                continue
            status = event.get("status", {})
            messages = status.get("messages", [])
            if status.get("status_str") != "success":
                details = next((x for t,x in messages if t == "execution_error"), {})
                raise RuntimeError(f"ComfyUI failed at {details.get('node_type','unknown node')}: {details.get('exception_message',status)}")
            images = event.get("outputs",{}).get("13",{}).get("images",[])
            if len(images)!=1 or images[0].get("type")!="output":
                raise RuntimeError("Expected one completed SaveImage result")
            cached = [str(n) for kind, params in messages if kind=="execution_cached" for n in params.get("nodes",[])]
            image = self.http.get(self.url+"/view",params=images[0],timeout=90)
            image.raise_for_status()
            with Image.open(io.BytesIO(image.content)) as png:
                if png.format!="PNG":
                    raise ValueError("ComfyUI did not return a PNG")
                png.load()
            return image.content, {"prompt_id":job, "elapsed_seconds":round(time.monotonic()-submitted,3),"cached_nodes":cached}
        raise TimeoutError(f"Job {job} is still queued or running; check the server history")


def normalized_png(raw):
    with Image.open(io.BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        stream = io.BytesIO()
        im.save(stream,format="PNG")
        return stream.getvalue()


def render_case(client, photo, dest, prompt, seed, steps, megapixels, deadline):
    raw = photo.read_bytes()
    source = normalized_png(raw)
    graph = graph_for("pending.png", prompt, seed, steps, megapixels)
    graph["1"]["inputs"]["image"] = client.upload(source)
    generated, timing = client.execute(graph,deadline)
    dest.mkdir()
    (dest/"source.png").write_bytes(source)
    (dest/"watercolor.png").write_bytes(generated)
    (dest/"workflow.json").write_text(json.dumps(graph,indent=2)+"\n",encoding="utf-8")
    with Image.open(io.BytesIO(source)) as a, Image.open(io.BytesIO(generated)) as b:
        receipt = {"source_file": photo.name, "source_file_sha256":sha256(raw),
            "uploaded_png_sha256":sha256(source),"output_png_sha256":sha256(generated),
            "source_size":list(a.size),"output_size":list(b.size),"seed":seed,"steps":steps,
            "megapixels":megapixels,"guidance":graph["8"]["inputs"]["guidance"],"instruction":prompt,
            "graph_sha256":sha256((dest/"workflow.json").read_bytes()),**timing}
    (dest/"run.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    return receipt
