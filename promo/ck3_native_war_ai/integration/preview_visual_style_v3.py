"""Create three original procedural layout previews; no media or CK3 execution."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageColor, ImageDraw

from war_ai_promo.common import binding, load, write_new
from war_ai_promo.teaching_visuals import make_teaching_frame
from war_ai_promo.visuals import BG, INK, MUTED, GOLD, PAPER, PAPER_INK


ROOT = Path(__file__).resolve().parents[3]
TEACHING = "promo/ck3_native_war_ai/integration/src/war_ai_promo/teaching_visuals.py"


def mechanism_copy(source):
    """Freeze all Chinese string literals, not just the central SHOTS table."""
    tree = ast.parse(source)
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value,str)
            and re.search(r"[\u3400-\u9fff]",node.value)]


def contrast(foreground, background):
    def luminance(color):
        values = [v/255 for v in ImageColor.getrgb(color)]
        values = [v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4 for v in values]
        return sum(v*w for v,w in zip(values,(.2126,.7152,.0722)))
    a,b = sorted((luminance(foreground),luminance(background)))
    return (b+.05)/(a+.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    script_path = ROOT / "promo/ck3_native_war_ai/longform/narration.json"
    cues = {row["id"]:row for row in load(script_path)["cues"]}
    current_copy = mechanism_copy((ROOT / TEACHING).read_text(encoding="utf-8"))
    old = subprocess.run(["git","show",f"HEAD:{TEACHING}"],cwd=ROOT,capture_output=True,check=True)
    old_copy = mechanism_copy(old.stdout.decode("utf-8"))
    copy_unchanged = current_copy == old_copy
    selection = [
        ("01-candidate-folio.png","N30-013",2,"Six hypothetical positive candidates, existing copy"),
        ("02-map-margin-notes.png","N30-027",1,"Fictional teaching geography and province labels, existing copy"),
        ("03-peace-folios.png","N30-069",1,"Two role-bound ledgers and base scores, existing copy"),
    ]
    previews = []
    original_text = ImageDraw.ImageDraw.text
    for filename,cue_id,phase,purpose in selection:
        text_bounds = []
        def traced_text(draw, xy, value, *positional, **kwargs):
            if isinstance(value,str) and value.strip():
                face = kwargs.get("font")
                bounds = draw.textbbox(xy,value,font=face,anchor=kwargs.get("anchor"),
                                       stroke_width=kwargs.get("stroke_width",0))
                text_bounds.append({"text":value,"bounds":list(bounds),"font_size":getattr(face,"size",None)})
            return original_text(draw,xy,value,*positional,**kwargs)
        ImageDraw.ImageDraw.text = traced_text
        path = output / filename
        try:
            make_teaching_frame(cues[cue_id],path,phase)
        finally:
            ImageDraw.ImageDraw.text = original_text
        with Image.open(path) as image:
            dimensions = image.size
            subtitle = image.crop((0,1120,2560,1440))
            subtitle_clear = subtitle.getextrema() == tuple((v,v) for v in ImageColor.getrgb(BG))
            thumbnail = image.resize((320,180))
            blue_dashboard_pixels = sum(1 for r,g,b in thumbnail.get_flattened_data() if b > r+24 and b > g+10)
        overflow = [item for item in text_bounds if item["bounds"][0] < 64 or item["bounds"][1] < 35
                    or item["bounds"][2] > 2496 or item["bounds"][3] > 1120]
        overlaps = []
        for index,left in enumerate(text_bounds):
            a,b,c,d = left["bounds"]
            for right in text_bounds[index+1:]:
                e,f,g,h = right["bounds"]
                if min(c,g)-max(a,e) > 3 and min(d,h)-max(b,f) > 3:
                    overlaps.append({"first":left,"second":right})
        previews.append({"file":binding(path),"cue_id":cue_id,"shot_id":cues[cue_id]["shot_id"],
            "phase":phase,"purpose":purpose,"dimensions":list(dimensions),
            "subtitle_area_y1120_1440_clear":subtitle_clear,"text_bounds":text_bounds,
            "text_overflow":overflow,"text_overlaps":overlaps,"blue_dashboard_pixel_fraction":blue_dashboard_pixels/(320*180),
            "status":"layout-pass" if dimensions==(2560,1440) and subtitle_clear and not overflow and not overlaps else "layout-fail"})
    pairs = [("primary",INK,BG),("muted",MUTED,BG),("focus",GOLD,BG),("paper",PAPER_INK,PAPER)]
    contrasts = [{"name":name,"foreground":fg,"background":bg,"ratio":contrast(fg,bg)} for name,fg,bg in pairs]
    success = copy_unchanged and all(row["status"]=="layout-pass" for row in previews) and all(row["ratio"] >= 4.5 for row in contrasts)
    report = {"schema":"ck3-war-ai.visual-v3-layout-preview.v1",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),"result":"PASS" if success else "FAIL",
        "scope":"Three representative static layouts, actual font bounds/overlaps/contrast and subtitle clearance. Not all-shot visual validation or factual/script approval.",
        "original_procedural_art":True,"external_images_used":False,"ck3_assets_claimed":False,
        "ck3_started":False,"full_film_rendered":False,"human_signoff":False,
        "existing_chinese_mechanism_literals_unchanged":copy_unchanged,
        "existing_chinese_literal_count":len(current_copy),
        "existing_copy_status":"Old copy retained; this visual task does not implement the claim-ledger rewrites. New narration still pending.",
        "sources":[binding(script_path),binding(ROOT/TEACHING),binding(ROOT/'promo/ck3_native_war_ai/integration/src/war_ai_promo/visuals.py'),binding(Path(__file__).resolve())],
        "contrast":contrasts,"previews":previews}
    write_new(output / "layout-report.json",report)
    print(json.dumps({"result":report["result"],"report":(output/'layout-report.json').as_posix(),
                      "previews":[row["file"]["path"] for row in previews],
                      "copy_unchanged":copy_unchanged},ensure_ascii=False,indent=2))
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
