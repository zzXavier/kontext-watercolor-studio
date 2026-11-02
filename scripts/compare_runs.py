"""Compare two completed watercolor runs using their saved images and submitted graphs."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file,"sha256").hexdigest()


def verified_case(folder):
    receipt=read_json(folder/"run.json")
    for filename,key in (("workflow.json","graph_sha256"),("source.png","uploaded_png_sha256"),("watercolor.png","output_png_sha256")):
        if digest(folder/filename)!=receipt[key]:
            raise ValueError(f"{folder.name}/{filename} does not match its receipt")
    return receipt


def compare(first,second):
    left,right=(read_json(path/"manifest.json") for path in (first,second))
    if left["status"]!="completed" or right["status"]!="completed" or left["cases"]!=right["cases"]:
        raise ValueError("Expected identical completed case lists")
    rows=[]
    for case in left["cases"]:
        if Path(case).name!=case or case in (".",".."):raise ValueError("Invalid case identifier")
        a,b=first/case,second/case
        receipt,rerun=verified_case(a),verified_case(b)
        for key in ("source_file_sha256","graph_sha256","seed","steps","megapixels","guidance","output_size"):
            if receipt[key]!=rerun[key]:raise ValueError(f"Different experiment input: {case}/{key}")
        if "11" in rerun.get("cached_nodes",[]):raise ValueError(f"Second sampler was cached for {case}")
        with Image.open(a/"watercolor.png") as x, Image.open(b/"watercolor.png") as y:
            if x.size!=y.size:raise ValueError(f"Different image dimensions for {case}")
            diff=ImageChops.difference(x.convert("RGB"),y.convert("RGB"))
            histogram=diff.histogram()
            changed=x.width*x.height*3-sum(histogram[i] for i in (0,256,512))
            rows.append({"case":case,"rgb_mean_absolute_difference_0_to_255":sum(ImageStat.Stat(diff).mean)/3,
                "max_absolute_channel_difference":max(top for _,top in diff.getextrema()),
                "changed_channels":changed,"total_channels":x.width*x.height*3,
                "identical_png_bytes":receipt["output_png_sha256"]==rerun["output_png_sha256"],
                "first_output_sha256":receipt["output_png_sha256"],"rerun_output_sha256":rerun["output_png_sha256"],
                "rerun_seconds":rerun["elapsed_seconds"],"cached_nodes":rerun["cached_nodes"]})
    return {"cases":rows,"all_pixels_identical":all(row["changed_channels"]==0 for row in rows),
            "all_png_files_identical":all(row["identical_png_bytes"] for row in rows)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("first",type=Path);p.add_argument("second",type=Path)
    p.add_argument("--json",type=Path,help="Save the pixel comparison as JSON")
    args=p.parse_args()
    report=json.dumps(compare(args.first,args.second),indent=2)+"\n"
    if args.json:args.json.write_text(report,encoding="utf-8")
    print(report,end="")
