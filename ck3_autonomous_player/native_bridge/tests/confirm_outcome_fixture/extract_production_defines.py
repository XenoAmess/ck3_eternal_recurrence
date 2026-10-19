from pathlib import Path
import sys,json,re
commands=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
source=Path(sys.argv[2]).resolve()
units={"ingame_decision_item_v1","game_adapter","zhongguo_case_snapshot_v1","zhongguo_scoreboard_action_v1","zhongguo_scoreboard_state_v1"}
rows=[]
for row in commands:
    p=Path(row["file"])
    if p.stem in units and "/xar_ck3_bridge.dir/" in row["output"].replace("\\","/"):
        actual=source/"src"/p.name
        if actual.read_bytes()!=p.read_bytes():raise RuntimeError("Current production source differs from referenced build source: "+p.name)
        defs=re.findall(r'(?:^|\s)[-/]D([A-Za-z_][A-Za-z0-9_]*(?:=[^\s\"]+)?)',row["command"])
        defs=[x for x in defs if x.split("=")[0]!="NDEBUG"]
        rows.append('set_property(SOURCE "'+actual.as_posix()+'" APPEND PROPERTY COMPILE_DEFINITIONS '+' '.join(defs)+')')
if len(rows)!=5:raise RuntimeError("Expected exactly five actual production command entries")
Path(sys.argv[3]).write_text("\n".join(rows)+"\n",encoding="utf-8")
