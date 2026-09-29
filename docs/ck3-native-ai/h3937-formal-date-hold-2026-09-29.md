# H3937 formal date hold

The Robert H3937 source is episode `native-29829-2bc2d599f7f9`, actor
`29829`, WarID `16777231`, player ArmyID `83886367`, and source
`date_raw=53219928`. These values identify the frozen candidate. The episode
ID is the guard key; the other values are recorded as audit anchors. A later
date or changed actor/war/army row within that episode does **not** release
the guard.

No authenticated same-frame physical hostile inventory reaches the formal
bridge yet. The war cash and risk policy is also not accepted. For this exact
episode, the formal planner clears any selected date-control step. The native
driver omits date controls from capabilities and refuses public, composite,
and primitive date submission before a native timeline command is sent. This
covers `life-advance`, battle/committed-route/objective-hold sentinels,
`advance-route-contact-horizon`, direct `resume-map`, and speed controls.
The two advertised, parameterless committed-route and objective-hold sentinel
templates are date controls too; their concrete army/war/date tokens are
checked separately.
Frontend revision-zero execution rejects all date controls for every episode;
its synthetic frame cannot certify the H3937 episode identity.
Same-frame read-only route queries and snapshots remain available.

The separate route-contact inventory guard applies to all episodes. It does
not authenticate a bare completeness boolean or shaped JSON. Because there
is no native mailbox certificate producer, that typed exact-day path remains
closed everywhere. The H3937 episode guard additionally closes other date
paths; it does not claim that all war episodes are globally frozen.

Removing the H3937 hold requires a reviewed native main-thread inventory
receipt bound to the same public/native frame and connection generation,
including the full hostile list and retreating armies, plus accepted formal
war/cash inputs and risk policy. A new explicit implementation and tests must
make that decision. No current boolean or static report releases the hold.

Static verification: `test_h3937_date_hold.py` exercises source and drifted
frames, final planner selection, generic/sentinel/route date tokens, and an
older episode. `test_native_bridge_driver.py` checks capability projection,
direct execution denial, no native command submission, and read-only query
availability. The full three-file suite has one pre-existing R0118 assertion
about the old combat query token; it reproduces on base `0f9566b43` and is
outside this date hold.
