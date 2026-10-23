import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from run import rebuild
from src.studio import ROOT, graph_for, sha256


class SavedRun(unittest.TestCase):
    def test_rebuild_enforces_graph_and_pixels(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);case=root/"fixture";case.mkdir()
            output=io.BytesIO();Image.new("RGB",(4,4),"#cc8844").save(output,format="PNG")
            png=output.getvalue();sig=sha256(png)
            (case/"source.png").write_bytes(png);(case/"watercolor.png").write_bytes(png)
            graph=graph_for("kontext-watercolor-"+sig[:24]+".png","Paint a watercolor",42,20,.5)
            data=json.dumps(graph).encode();(case/"workflow.json").write_bytes(data)
            rec={"source_file":"fixture.png","instruction":"Paint a watercolor","seed":42,"steps":20,"megapixels":.5,
                 "graph_sha256":sha256(data),"uploaded_png_sha256":sig,"output_png_sha256":sig}
            (case/"run.json").write_text(json.dumps(rec))
            (root/"manifest.json").write_text(json.dumps({"status":"completed","cases":["fixture"]}))
            rebuild(root)
            self.assertTrue((root/"comparison.jpg").is_file())
            rec["seed"]=7;(case/"run.json").write_text(json.dumps(rec))
            with self.assertRaisesRegex(ValueError,"Workflow mismatch"):rebuild(root)
            rec["seed"]=42;(case/"run.json").write_text(json.dumps(rec))
            (case/"watercolor.png").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"Image checksum"):rebuild(root)

    def test_incomplete_batch_is_not_evaluated(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"manifest.json").write_text(json.dumps({"status":"in_progress","cases":[]}))
            with self.assertRaisesRegex(ValueError,"complete run"):rebuild(root)
