"""Render photographs or rebuild the source/output contact sheet."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageOps

from src.studio import Comfy, ROOT, SETTINGS, graph_for, render_case, sha256


def rebuild(folder):
    manifest = json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed" or not manifest["cases"] or len(set(manifest["cases"])) != len(manifest["cases"]):
        raise ValueError("A complete run with distinct cases is required")
    groups = {}
    for case in manifest["cases"]:
        if Path(case).name!=case or case in (".",".."):
            raise ValueError("Invalid case identifier")
        dest=folder/case
        receipt=json.loads((dest/"run.json").read_text(encoding="utf-8"))
        source=(dest/"source.png").read_bytes()
        graph=graph_for("kontext-watercolor-"+sha256(source)[:24]+".png",receipt["instruction"],
                        receipt["seed"],receipt["steps"],receipt["megapixels"])
        graph_data=(dest/"workflow.json").read_bytes()
        if sha256(graph_data)!=receipt["graph_sha256"] or json.loads(graph_data)!=graph:
            raise ValueError(f"Workflow mismatch for {case}")
        for filename,digest in [("source.png","uploaded_png_sha256"),("watercolor.png","output_png_sha256")]:
            if sha256((dest/filename).read_bytes())!=receipt[digest]:
                raise ValueError(f"Image checksum mismatch for {case}/{filename}")
        if manifest.get("action") in ("demo","reproduce"):
            name=receipt["source_file"]
            if name not in SETTINGS["photos"] or sha256((ROOT/"examples"/name).read_bytes())!=receipt["source_file_sha256"]:
                raise ValueError("Bundled photograph no longer matches the recorded source")
        label=case.removeprefix(Path(receipt["source_file"]).stem+"-").replace("-"," ").capitalize()
        row=groups.setdefault(receipt["uploaded_png_sha256"],[(dest/"source.png","Original / "+receipt["source_file"])])
        row.append((dest/"watercolor.png",label))
    width,height=360,300
    board=Image.new("RGB",(width*max(map(len,groups.values())),height*len(groups)),"#f7f6f2")
    draw=ImageDraw.Draw(board)
    for y,row in enumerate(groups.values()):
        for x,(path,label) in enumerate(row):
            with Image.open(path) as im:
                tile=ImageOps.contain(im.convert("RGB"),(width-16,height-32),Image.Resampling.LANCZOS)
                board.paste(tile,(x*width+(width-tile.width)//2,y*height+24+(height-32-tile.height)//2))
            draw.text((x*width+8,y*height+5),label,fill="#26323a")
    board.save(folder/"comparison.jpg",quality=92,subsampling=0)
    print(folder/"comparison.jpg")


def verify_models(folder):
    manifest=json.loads((ROOT/"configs/model-manifest.json").read_text(encoding="utf-8-sig"))
    entries=manifest if isinstance(manifest,list) else manifest["files"]
    for item in entries:
        file=folder/item["path"]
        with file.open("rb") as fp:
            digest=hashlib.file_digest(fp,"sha256").hexdigest()
        if digest!=item["sha256"] or file.stat().st_size!=item["size"]:
            raise ValueError(f"Model does not match the pinned release: {file.name}")
        print(digest,file.name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["render","demo","reproduce","evaluate","verify-models"])
    parser.add_argument("photo",nargs="?",type=Path)
    parser.add_argument("--out",type=Path)
    parser.add_argument("--server",default="http://127.0.0.1:8188")
    parser.add_argument("--models",type=Path)
    parser.add_argument("--preset",choices=SETTINGS["presets"],default="transparent-wash")
    parser.add_argument("--prompt",help="Replace the preset instruction for a custom render")
    parser.add_argument("--seed",type=int,default=SETTINGS["seed"])
    parser.add_argument("--steps",type=int,default=SETTINGS["steps"])
    parser.add_argument("--megapixels",type=float,default=SETTINGS["megapixels"])
    parser.add_argument("--timeout",type=int,default=3600)
    a=parser.parse_args()
    if a.action=="verify-models":
        if a.models is None:parser.error("Pass --models MODEL_ROOT")
        verify_models(a.models); return
    out=a.out or (ROOT/"results" if a.action=="evaluate" else ROOT/"work"/a.action)
    if a.action=="evaluate":
        rebuild(out);return
    if out.exists():parser.error("Choose an unused --out directory to preserve the existing run")
    if a.action=="render":
        if a.photo is None or not a.photo.is_file():parser.error("Pass an existing photograph")
        jobs=[("painting",a.photo,a.prompt or SETTINGS["presets"][a.preset])]
    else:
        if a.photo is not None or a.prompt is not None:parser.error("Use render for a custom photograph or prompt")
        photos=SETTINGS["photos"][:1] if a.action=="demo" else SETTINGS["photos"]
        presets=[a.preset] if a.action=="demo" else SETTINGS["presets"]
        jobs=[(f"{Path(name).stem}-{preset}",ROOT/"examples"/name,SETTINGS["presets"][preset]) for name in photos for preset in presets]
    client=Comfy(a.server);environment=client.check()
    out.parent.mkdir(exist_ok=True,parents=True)
    with TemporaryDirectory(dir=out.parent) as temp:
        stage=Path(temp)/"run";stage.mkdir()
        for case,photo,prompt in jobs:
            print(f"Rendering {case}",flush=True)
            receipt=render_case(client,photo,stage/case,prompt,a.seed,a.steps,a.megapixels,a.timeout)
            print(f"{case}: {receipt['elapsed_seconds']} s",flush=True)
        (stage/"manifest.json").write_text(json.dumps({"status":"completed","action":a.action,"cases":[j[0] for j in jobs],"environment":environment},indent=2)+"\n",encoding="utf-8")
        rebuild(stage)
        os.rename(stage,out)
    print(out)


if __name__=="__main__":
    main()
