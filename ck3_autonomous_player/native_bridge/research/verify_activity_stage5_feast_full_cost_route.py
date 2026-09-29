"""Check that the private feast-cost step passes execute_step admission.

This source contract covers the outer rejection path as well as its handler;
compiling the handler alone does not prove that protocol requests reach it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    bridge = Path(sys.argv[1]).read_text(encoding="utf-8")
    rejection = bridge.index('"unsupported native gameplay step"')
    feature = "XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1"
    step = "kActivityStage5FeastFullCostPrivateStepV1"
    admission = re.compile(
        rf"#if defined\({feature}\)\s*"
        rf"&& step != xar::ck3_11906::\s*{step}\s*#endif"
    )
    handler = re.compile(
        rf"#if defined\({feature}\)\s*"
        rf"if \(step == xar::ck3_11906::\s*{step}\) \{{"
    )
    if len(admission.findall(bridge[:rejection])) != 1:
        raise AssertionError("feast full-cost step is not admitted before reject")
    if len(handler.findall(bridge[rejection:])) != 1:
        raise AssertionError("feast full-cost step has no reachable handler branch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
