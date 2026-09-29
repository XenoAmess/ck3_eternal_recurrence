# H2743 existing truce: R0110 RED and dynamic paused-frame claim

## Immutable R0110 observation

The managed read-only run `desktop-3fevhd2-1c74096080--vanilla--R0110` used PR #448 HEAD `8363c02d6979adf839ba1558c4d8818e4418c82e`. Its one-use GO, fresh Steam offline frame, live identity, source pair, preflight, binary audit, request/error, and cleanup are preserved under `D:/ck3-research-artifacts/h2743-existing-truce-readonly-20260929/`. The append-only postcheck is `admission-06/attempt6-red-postcheck.json`, SHA-256 `A55C6A1C54CE4F2A3D8F782F0CF3D8D0167F89E0C872EF01599F43C91EEEBE71`; that receipt hashes the individual evidence files.

The actual paused before frame had `snapshot_id=native:4`, public revision `5`, native revision `4`, date raw `53217264`, actor `29829`, episode `native-29829-2bc2d599f7f9`, and `map_ready=true`. The first old-truce read returned `exact H2743 native source/frame claim unavailable`: the Python driver and C++ bridge still required `native:3`. This is a source/frame claim RED, not an old-truce result. There is no first old-slot payload, second old-slot request, options request, date advance, surrender, peace, or other gameplay action. The R0110 CK3 PID `25984` exited, its supervisor returned `0`, and its task bus entry reached `done/resources=[]` at sequence `2441`. The postcheck also records another agent's later CK3 PID without attributing that process to R0110.

## Candidate correction

The read-only runner now derives an explicit claim from the actual paused before snapshot. The claim binds `snapshot_id`, public/native revisions, date, actor, episode, WarID, and connection generation. The Python service permits this claim only for the H2743 existing-truce query; it requires the current native snapshot to match exactly and passes its values to the C++ bridge. C++ checks the requested revision against its current state revision, checks a fresh paused admission frame against the previous frame, and checks the dynamic claim and fixed source identity before touching the old-truce getter. Neither layer substitutes a new `native:4` constant for `native:3`; any drift fails closed.

The same claim and public revision are retained for both old-slot reads and the intervening options read. Recording a command does not advance the public revision; a changed state snapshot or connection does. A change therefore rejects the later query rather than silently refreshing the evidence frame. The R0110 `native:4` case and mismatched snapshot/public/native revision/date/actor/WarID/episode cases have focused positive and negative tests in Python and C++.

This candidate still needs a new exact Release DLL/C++ test, independent static review, fresh no-launch admission, and a new managed read-only live run after the H3937 screen owner releases the resource. R0110 remains RED. No exit decision or reusable exit completion follows from the static tests.
