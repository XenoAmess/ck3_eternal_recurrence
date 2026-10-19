import argparse, hashlib, json, pathlib, zipfile
def need(ok, message):
    if not ok:
        raise ValueError(message)
def main():
    parser = argparse.ArgumentParser(description="Verify small R217 retained evidence; no game/media access")
    parser.add_argument("--index", type=pathlib.Path)
    parser.add_argument("--root", type=pathlib.Path)
    args = parser.parse_args()
    root = (args.root or pathlib.Path(__file__).resolve().parent).resolve()
    index = json.loads((args.index or root / "index.json").read_bytes())
    need(index["schema"] == "xar.e04.r217-final-portable-index.v1", "schema")
    need(index["credit"] == {"R04_closed": False, "research": "10/14", "business": "7/11", "formal_dynamic": "0/11", "ABC": "0/3", "B_qualified_sites": 0}, "credit boundary")
    need(0 < len(index["files"]) <= 24, "file count")
    total = 0
    for item in index["files"]:
        rel = pathlib.PurePosixPath(item["path"])
        need(not rel.is_absolute() and ".." not in rel.parts, "relative path")
        path = (root / rel).resolve()
        need(path.is_relative_to(root), "path escape")
        data = path.read_bytes()
        total += len(data)
        need(total <= 262144, "small package budget")
        need(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"], "pin: " + item["path"])
    partial = json.loads((root / index["archive"]["index"]).read_bytes())
    with zipfile.ZipFile(root / index["archive"]["path"]) as archive:
        need(set(archive.namelist()) == set(partial["originals"]), "archive member set")
        for name, pin in partial["originals"].items():
            data = archive.read(name)
            need(len(data) == pin["bytes"] and hashlib.sha256(data).hexdigest() == pin["sha256"], "archive pin: " + name)
    release = json.loads((root / "close/screen-release.json").read_bytes())
    task = release["task_readback"]
    need(release["released_confirmed"] is True and task["state"] == "done" and task["resources"] == [] and task["last_sequence"] == 6803, "Root release")
    media = json.loads((root / "media/media-qa.json").read_bytes())
    need(media["full_decode_performed"] is False and media["human_1x_approval"] is False and media["formal_episode_shot_qualified"] is False, "media boundary")
    print(json.dumps({"portable_small_evidence_pass": True, "files": len(index["files"]), "bytes": total, "SDK_calls": 0, "media_body_reads": 0}))
if __name__ == "__main__":
    main()
