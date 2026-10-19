# Storage commit boundaries

Storage producers prepare observations outside all shared coordination locks.
This includes process enumeration and command lines, machine/OS probes, volume
queries, inventories, content reads and hashes, serialization, writes and fsync.
`tools/storage_short_commit.py` is the publication entry: an immutable report is
fully staged first; the task-bus critical section performs only a fixed set of
exact metadata comparisons, a head revision CAS, and at most two atomic renames.
It accepts no caller callback. A conflict or busy lock requires preparation to
be repeated outside the lock. Unknown observations never become capacity credit.

Existing historical storage scripts which directly acquire `bus_lock` are
retired execution inputs. Preserve their bytes and receipts for provenance;
do not rerun them or copy their broad lock bodies into a new producer. Run
`tools/audit_storage_lock_boundaries.py --source <exact-producer>` before reuse.
The shared short-commit implementation is the sole reviewed exception to that
static rule. This source audit does not grant any maintenance or write scope.

The account-v14 adapter compiles only the exact sealed v13 source, removes its
broad lock and old output tail, and executes observation before CAS publication.
It does not alter the approved owner/media scope. Its execution remains paused
until the coordinator explicitly resumes maintenance and supplies the then
current approved scope. Old direct entry points are historical only.

The head is the adoption pointer. A crash between report and head renames may
leave a complete unadopted report. Preserve and diagnose it; do not overwrite it
or replay deletion. This module itself performs no asset reclamation. Any future
reclaimer must acquire its exact no-writer handles and collect system inputs
outside the global lock, commit a small pending intent with CAS, perform the
authorized operation outside that lock, then CAS-publish actual results. An
unknown outcome requires diagnosis, not an automatic retry.

The 0.25-second check is a fail-before-next-step guard, not a promise that Windows
can preempt a blocked metadata syscall. The fixed critical section has no scans,
callbacks, body reads, serialization, fsync, subprocesses or process queries.
Tests use a separately owned temporary bus and actual competing processes;
the production bus and active Game are never used to reproduce the incident.
