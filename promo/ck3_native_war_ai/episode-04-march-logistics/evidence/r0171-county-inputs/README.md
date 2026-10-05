# R0171 county current-input runtime evidence

This portable package contains complete original JSON bytes, a compact summary,
their SHA-256 index and a stdlib-only verifier. It contains no media, game saves,
native binaries or SDK dependency. Historical paths inside raw JSON are preserved
as evidence; verification uses package-relative paths only.

Run from any directory:

```text
python /path/to/r0171-county-inputs/verify_package.py
```

The observed paused pair is native:2/public3 to native:3/public4 at date_raw
53147376, actor33388, Army0/native0, 6746/6747 soldiers, 27 actual regiments and
37 DATA records. The native current county budget is 236 in both frames. The
condition changes from unknown `no_stored_route` to available with actor33388,
source1506, route-first target725, mode1 and `passes=false` after the actual stored
route becomes [725,1009,2174]. Current first-edge duration is30 days, progress0.

This proves current-input runtime availability. It does not record arrival,
applied loss236, deaths, a loss/refill event ledger, the executor special flag,
the loaded movement lock threshold, starvation crossing or filming signoff.
The selected ready record is one full unchanged original JSONL record from a
still-growing session log. Source version/hash fields in Strength are null;
the exact version/source binding is supplied by the pinned a08 build and actual
session paths plus matching SDK module origins.
