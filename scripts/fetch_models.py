"""Fetch the four immutable public model files. Keep verified byte ranges for retries."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import time

import requests

ROOT=Path(__file__).resolve().parents[1]
CHUNK=8*1024*1024


def fetch_model(root, row, jobs):
    target=root/row["path"]
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file():
        with target.open("rb") as f:
            if target.stat().st_size==row["size"] and hashlib.file_digest(f,"sha256").hexdigest()==row["sha256"]:
                print("Already verified", row["path"]);return
        raise ValueError(f"Existing file differs from the manifest: {target}")
    parts=target.with_name(target.name+".parts");parts.mkdir(exist_ok=True)
    positions=list(range(0,row["size"],CHUNK))
    url=f"https://huggingface.co/{row['repo']}/resolve/{row['revision']}/{row['source']}"

    def transfer(start):
        end=min(start+CHUNK,row["size"])-1
        part=parts/f"{start:012d}.chunk"
        if part.is_file() and part.stat().st_size==end-start+1:return part
        for attempt in range(5):
            try:
                with requests.get(url,params={"segment":start},headers={"Range":f"bytes={start}-{end}","Accept-Encoding":"identity"},
                                  stream=True,timeout=(20,90)) as response:
                    response.raise_for_status()
                    if response.headers.get("Content-Range")!=f"bytes {start}-{end}/{row['size']}":
                        raise IOError("The download did not return the requested byte range")
                    partial=part.with_suffix(".partial")
                    with partial.open("wb") as out:
                        for block in response.iter_content(1024*1024):out.write(block)
                    if partial.stat().st_size!=end-start+1:raise IOError("Incomplete byte range")
                    partial.replace(part)
                    return part
            except (requests.RequestException, OSError):
                if attempt==4:raise
                time.sleep(2**attempt)

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as workers:
        chunks=list(workers.map(transfer,positions))
    assembled=target.with_name(target.name+".assembling")
    with assembled.open("wb") as out:
        for part in chunks:
            with part.open("rb") as f:shutil.copyfileobj(f,out,2*1024*1024)
    with assembled.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=row["sha256"]:
            raise ValueError(f"Digest mismatch for {target.name}; inspect or remove its local .parts directory before retrying")
    assembled.replace(target)
    for part in chunks:part.unlink()
    parts.rmdir()
    print("Verified",row["path"],flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models",type=Path,required=True)
    parser.add_argument("--jobs",type=int,default=8)
    args=parser.parse_args()
    if not 1<=args.jobs<=32:parser.error("--jobs must be 1–32")
    for item in json.loads((ROOT/"configs/model-manifest.json").read_text(encoding="utf-8-sig")):
        fetch_model(args.models,item,args.jobs)
