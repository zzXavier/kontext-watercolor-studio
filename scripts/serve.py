"""Start a pinned ComfyUI instance on loopback with an external model directory."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

COMFY = "d5c1954d5cd4a789bbf84d2b75a955a5a3f93de8"
GGUF = "cf0573351ac260d629d460d97f09b09ac17d3726"


def revision(directory):
    return subprocess.check_output(["git","-C",str(directory),"rev-parse","HEAD"],text=True).strip()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--comfy",required=True,type=Path)
    p.add_argument("--models",required=True,type=Path)
    p.add_argument("--port",type=int, default=8188)
    p.add_argument("--data",type=Path,default=Path("work/server"),help="Server uploads, results and local settings")
    a=p.parse_args(); src=a.comfy.resolve();data=a.data.resolve()
    if revision(src)!=COMFY or revision(src/"custom_nodes/ComfyUI-GGUF")!=GGUF:
        raise SystemExit("ComfyUI and ComfyUI-GGUF must match the revisions in UPSTREAM.md.")
    if not (1 <=a.port <=65535):p.error("Invalid TCP port")
    data.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix="watercolor-paths-") as td:
        cfg=Path(td)/"paths.yaml"
        cfg.write_text(json.dumps({"watercolor":{"base_path":str(a.models.resolve()),"is_default":True,
            "diffusion_models":"diffusion_models","text_encoders":"text_encoders","vae":"vae"}}),encoding="utf-8")
        for kind in ("input","output","temp","user"):
            (data/kind).mkdir(exist_ok=True)
        args=[sys.executable,str(src/"main.py"),"--listen","127.0.0.1","--port",str(a.port),
              "--disable-auto-launch","--lowvram","--preview-method","none",
              "--extra-model-paths-config",str(cfg),"--database-url","sqlite:///"+(data/"user/comfy.sqlite").as_posix()]
        for kind in ("input","output","temp","user"):
            args += ["--"+kind+"-directory",str(data/kind)]
        try:
            subprocess.run(args,cwd=src,check=True)
        except KeyboardInterrupt:
            pass


if __name__=="__main__":
    main()
