# R54 mutable shader cache reclaimed

ROOT completed all four exact batches with exit 0; the last batch finished 2026-10-10T23:55:10.535524+00:00. The original receipts record 3740 deleted files, 146942067 logical bytes and 155353904 bytes summed from the allocation API. Volume free space changed from 618599743488 to 618750332928; that delta is not exclusive cleanup credit.

Only the listed CASE5 mutable shadercache payload was retired. Each original deletion required distinct held source/target identities, unchanged FileID/size/birth/mtime and both SHA values equal to the retained immutable seed manifest. Old listed target bytes are now unavailable; directories and unlisted files were not recursively deleted. The seed, Source14, CASE6/R55 inputs, CASE5 prepared origin metadata and business snapshots remain retained.

`CREDIT-EVENT.actual.json` defines the one new 146942067-byte event `lyd-r54-mutable-cache-reclamation-20261010T235510Z`. It has not been claimed by a later reservation. Do not count the previous five-SAVE 458348713-byte or R52 146942031-byte events again.

This compact package contains original executor and batch/plan/protection receipts. Large identity/detail JSONL bodies remain external under their existing deadlines and are referenced by original pins; they were not copied, compressed, reread or removed here. The original cache review remains 2026-10-17T13:06:29.278808+00:00; this aggregation renews no TTL and grants no runtime/business credit.
