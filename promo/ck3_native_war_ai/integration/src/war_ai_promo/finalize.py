"""Add navigable chapter bookmarks without re-encoding the rendered film."""
from pathlib import Path

from xar_promo.process import CommandSpec, run_command


def add_chapters(source, destination, rows, config, *, audit_directory):
    source, destination = Path(source), Path(destination)
    titles = {chapter["id"]: chapter["title"]["zh-CN"] for chapter in config["chapters"]}
    chapters = []
    cursor = 0
    for row in rows:
        frames = round(row["duration_seconds"] * 30)
        if not chapters or chapters[-1]["id"] != row["chapter_id"]:
            chapters.append({"id": row["chapter_id"], "start": cursor, "end": cursor})
        cursor += frames
        chapters[-1]["end"] = cursor
    metadata = destination.with_suffix(".ffmetadata")

    def escape(value):
        return value.replace("\\", "\\\\").replace("=", r"\=").replace(";", r"\;").replace("#", r"\#").replace("\n", " ")

    text = [";FFMETADATA1", "title=" + escape(config["project"]["title"])]
    for chapter in chapters:
        text.extend(["[CHAPTER]", "TIMEBASE=1/30", f"START={chapter['start']}",
                     f"END={chapter['end']}", "title=" + escape(titles[chapter["id"]])])
    with metadata.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(text) + "\n")
    result = run_command(CommandSpec.create([
        "ffmpeg", "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
        "-i", source, "-i", metadata, "-map", "0:v:0", "-map", "0:a:0",
        "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", destination,
    ], label="add-full-film-chapter-bookmarks", partial_artifacts=[destination]), audit_directory=audit_directory)
    if result.returncode:
        raise RuntimeError(f"Chapter mux failed; retain {audit_directory}")
    return metadata
