"""Linear variant of the observer reader; old snapshot code/artifacts stay intact."""

from collections import Counter
import re

import snapshot


def classify_linear(raw):
    headers = list(re.finditer(rb"(?m)^\[([^]\r\n]+)\]\[([A-Z])\][^\r\n]*", raw))
    groups = []
    counts = Counter()
    line = 1
    previous_start = 0
    for number, match in enumerate(headers):
        line += raw[previous_start:match.start()].count(b"\n")
        previous_start = match.start()
        if match[2] != b"E":
            continue
        start = match.start()
        end = headers[number + 1].start() if number + 1 < len(headers) else len(raw)
        group = raw[start:end]
        text = group.decode("utf-8", errors="replace")
        header = match[0].decode("utf-8", errors="replace")
        unused = re.search(r"Variable '(lyd_im_case_[0-9]+_(?:armed|acknowledged)|lyd_im_adopted)' is set but is never used\.", header)
        target = re.search(r"lyd_c2_(?:source_signed|check_count|check_rites|check_followers|check_players)\b", text)
        if unused:
            category = "known_fixture_unused_variable"
        elif target:
            category = "current_product_c2_target_variable_error"
        elif "lyd_c2_" in text:
            category = "other_current_product_c2_error"
        elif "lyd_im_" in text or "lyd_i2_" in text:
            category = "other_fixture_error_unreviewed"
        else:
            category = "other_error_unreviewed"
        counts[category] += 1
        groups.append({"category": category, "source_time": match[1].decode("ascii", errors="replace"),
                       "byte_start": start, "byte_end_exclusive": end, "line_start": line,
                       "raw_group_sha256": snapshot.sha(group), "header": header,
                       "fixture_variable": unused[1] if unused else None, "target_variable": target[0] if target else None,
                       "snippet": text if category != "known_fixture_unused_variable" else None})
    return {"error_headers": len(groups), "counts": dict(counts), "groups": groups,
            "prefix_final_line_complete": not raw or raw.endswith(b"\n"),
            "classification_rule": "Exact known fixture unused; source_signed/scratch error group references; other C2 retained separately. Linear byte/line scan; no final-log claim."}


snapshot.classify = classify_linear
snapshot.main()
