# R10 runtime total and actual payload

Default total remains 512MiB. A/B CLI opt-in is `--max-runtime-total-bytes N --runtime-capacity-admission PATH SHA256`; C uses `runtime_total_budget_input` with those two dictionary keys and requires N to equal its existing `runtime_request_budget_bytes`. Larger N requires fresh exact Root admission: actual machine/source/scene/deadline, driver ceiling >= N, aggregate >= driver. No future scene or N is authorized by source or fixture tests.

The meter now includes original requests/responses, complete state-a01 Driver sidecars and scene ledgers once. It reserves a response plus the full 16/32MiB sidecar before querying. Original once-claims, full DATA and runtime guards remain. Per-file32MiB and total opt-ins are separate. The B stage ledger still has its own 1MiB bound.

R180 ordinary sample: 9,657,525 logical bytes. Its largest current-input fields are pending-update 3,450,823, post-admission 1,427,276 and assault-roster 1,318,606 bytes. Ten identical original rosters contribute only about173KB avoidable duplication. Ordinary omits nine retained journals; it retains these current inputs.

At the sampled size, 453 new sidecars would use4,374,858,825 logical bytes, excluding packets/state/actions. This is a conditional estimate, not270-day execution. Existing same-frame cache reuse can reduce the number of newly created files; different days cannot share one current observation.

In-RAM LZNT1 with actual4KiB clusters/64KiB units roundtrips every unit. Ordinary rounded allocation estimate is2,965,504 bytes (30.7%); full sample3,067,904. No compression setting or payload was written. Only future new-sidecar directory compression could preserve raw bytes/SHA/path; actual allocated size must then be measured. Logical quotas remain unchanged. NTFS uses16-cluster compression units: [Microsoft](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/707cdf5a-9d5f-4a40-ae88-fb7331d1aa33).

C already reuses the previous complete post as the next pre within one batch. Cross-stage reuse needs complete frame/identity/observer-fence equality. No such complete fence vector is currently published, so date/revision alone cannot waive a fresh query.
