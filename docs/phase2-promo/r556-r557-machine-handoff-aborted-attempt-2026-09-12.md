# R556-R557 machine-handoff aborted attempt

## Verdict

This attempt ended before loader readiness because the workstation returned to interactive human use. It is operationally aborted, produces no media, and contributes no Phase 2 span. It does not establish a product, native capability or vanilla-event RED.

P1 remains `9/9` GREEN and P2 remains `0/8`. No further CK3 round may start while the workstation is reserved for human use.

## Round and cleanup record

- R556/PID `163152` was the Frontend warm-up. It reached an authenticated responsive Frontend and was terminated by the managed handoff with cleanup GREEN.
- R557/PID `137916` was launched from the same isolated userdir with `-loadsave=autosave`, the promotion-only DLL and the frozen product projection.
- R557 exited with code `-805306369` before loader readiness. No gameplay acceptance, capability gate, event selection, gameplay input or FFmpeg recording ran.
- The attempt then reported `native_session_process_exit`. Its cleanup verdict also remains RED because the session ended by process exit instead of the expected managed stop semantics.
- The shutdown object independently proves the R557 tree gone, job empty, watchdog absent and final global CK3 inventory empty. A separate post-run inventory found zero CK3, FFmpeg and injector processes.
- No DLL, game file, launch configuration or load-order change was made between R555 and R557. The launch purpose was live verification of the `tgp_travel_events.0030` contract added by `f66937f`; that verification did not begin.

## Frozen evidence

- no-launch plan: `Z:\ck3_mod_rewrite\_runtime\p2-capture-r556-r563-40d0fa0-20260912\capture-plan.json`, SHA-256 `36C7275D581F4880C2D7B66290F8D88183DE1E41207B93F0D4A60E8ACF8F9962`
- attempt report: `Z:\ck3_mod_rewrite\_runtime\p2-capture-r556-r563-40d0fa0-20260912\capture\report.json`, SHA-256 `1340CCF4A445FCDB23BCDAA203AD0BAFAA592C4C85AE91B419F562A5392880F4`
- cleanup evidence: `Z:\ck3_mod_rewrite\_runtime\p2-capture-r556-r563-40d0fa0-20260912\capture\cell\09_phase2_native_session_cleanup.json`, SHA-256 `4688895FD6C190E51AE8CF95CB1B3AFDF5BB36D516789DBCC7C170E3FEBD7C9D`
- synchronized source: `40d0fa0554bee63dcb60001463e6d3b0e33775cd`
- CK3 build: `1.19.0.6`, executable SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- bridge DLL SHA-256: `54D46BD8211518D74FFFA055EF9A2D8270BEC3C2300A04701ED870E9C358CE27`

The next launch is R558. It is deferred until the workstation is explicitly available for CK3 again. Static and documentation work may continue meanwhile.
