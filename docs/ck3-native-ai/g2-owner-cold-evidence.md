# Offline owner cold evidence

Public offline evidence tool; no runtime gate or M7 completion. From the repository:

    python -B tools/extract_g2_owner_cold_evidence.py --owner-load-receipt launch.json --cold-input-receipt inputs.json --relocation-receipt migration.json --semantic-receipt sem.json --output owner.json

Reference its output with the existing public Goal CLI; the latter retains the explicit custody receipt pin:

    python -B tools/extract_g2_goal_continuity.py --save-receipt save.json --semantic-receipt sem.json --plan-receipt plan.json --existing-custody-evidence owner.json --output goal.json

Optional --plan-goal-pointer defaults to /result/structured_content/plan/campaign_goal_plan_used; for the published projection use /normal_plan_goal_used/value.

Goal source() supplies <=256KiB checks/pins. Forced exit 1 stays; initial control missing is null; camera is not CAP; later hot/plan is separate. No save revalidation, OS/discovery or government inference.

The three new portable compounds passed once after public import (0.005 seconds); old Goal and government matrices were not repeated. They cover matching fields and missing closure, wrong named load/SHA/size, separate later hot/plan observations, camera exclusion and the size guard refusing before read.

One use on the already closed N42 launch/input/migration/P02-semantic receipts returns eight consistent supplied-field checks. Separate P05 hot and P06 plan observations return three matching optional checks. Initial cold-control remains null, and forced prior exit code 1 remains non-normal. No new physical cold operation, government qualification, M7 completion or stable-window days follow from this offline result.

The existing [permanent evidence](g2-remaining-evidence-2026-10-16/README.md) retains the actual source pins and qualification boundary. A focused static-CI step covers this new tool test; exact-commit CI is recorded separately. open_kaishek is inapplicable to Python/closed JSON.
