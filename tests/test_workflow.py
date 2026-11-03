import json
from pathlib import Path
import unittest

from src.studio import API, ROOT, SETTINGS, graph_for


class GraphContract(unittest.TestCase):
    def test_reference_source_reaches_positive_and_sampler(self):
        graph=graph_for("input.png","watercolor",2,12,.4)
        self.assertEqual(graph["7"]["class_type"],"ReferenceLatent")
        self.assertEqual(graph["7"]["inputs"]["latent"],["4",0])
        self.assertEqual(graph["11"]["inputs"]["positive"],["8",0])
        self.assertEqual(graph["8"]["inputs"]["conditioning"],["7",0])
        self.assertEqual(graph["11"]["inputs"]["latent_image"],["4",0])
        self.assertEqual(graph["4"]["inputs"]["pixels"],["2",0])
        self.assertEqual(graph["2"]["inputs"]["image"],["1",0])
        self.assertEqual(graph["11"]["inputs"]["seed"],2)
        self.assertNotEqual(graph["1"]["inputs"]["image"],API["1"]["inputs"]["image"])

    def test_editable_workflow_matches_the_api_graph(self):
        ui=json.loads((ROOT/"workflows/watercolor-ui.json").read_text(encoding="utf-8"))
        nodes={n["id"]:n for n in ui["nodes"]}
        self.assertEqual({str(n):m["type"] for n,m in nodes.items()},{n:x["class_type"] for n,x in API.items()})
        found=set()
        for lid,source,out,target,idx,typ in ui["links"]:
            name=nodes[target]["inputs"][idx]["name"]
            self.assertEqual(nodes[target]["inputs"][idx]["link"],lid)
            self.assertEqual(API[str(target)]["inputs"][name],[str(source),out])
            found.add((str(target),name))
        self.assertEqual(found,{(n,k) for n,node in API.items() for k,v in node["inputs"].items() if isinstance(v,list)})
        self.assertEqual(nodes[6]["widgets_values"],[SETTINGS["presets"]["transparent-wash"]])
        self.assertEqual(nodes[11]["widgets_values"],[SETTINGS["seed"],"fixed",SETTINGS["steps"],1.0,"euler","simple",1.0])
        models=json.loads((ROOT/"configs/model-manifest.json").read_text(encoding="utf-8-sig"))
        names={Path(row["path"]).name for row in models}
        self.assertEqual(names,{API["10"]["inputs"]["unet_name"],API["3"]["inputs"]["vae_name"],
            API["5"]["inputs"]["clip_name1"],API["5"]["inputs"]["clip_name2"]})

    def test_invalid_request_does_not_queue(self):
        for prompt,seed,steps,mps in [("",1,10,.5),("wash",-1,10,.5),("wash",2,0,.5),("wash",2,20,10)]:
            with self.assertRaises(ValueError):graph_for("in.png",prompt,seed,steps,mps)
