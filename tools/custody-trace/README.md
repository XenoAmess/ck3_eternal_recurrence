# Finite custody trace analysis

This Python 3.13 standard-library tool explains first-N and FIFO retention arithmetic
for an explicitly supplied synthetic trace. It does not collect a live trace or grant
file-custody, identity, permission, close-success, cache-hit or performance authority.

Keep `custody_trace_analysis.py` and `custody_trace.py` together. The analyzer locates
the producer beside its resolved source file, independently of the command's current directory.
It verifies the producer's exact source SHA-256 before loading it under a non-main
name. The adjacent `.gitattributes` disables Git text/EOL conversion for these Python
files; the exact producer SHA-256 is still checked on each load. The producer is an
unchanged dependency with SHA-256
`2d2d54a77a3527c7aa37c04e6c1670fc0eff1536aa38fe89be793020aa432544`.

An input file contains exactly these three fields:

```json
{"kind":"DATA","caps":[2,1000,8],"trace":[["A",10,20],["B",10,20]]}
```

`caps` gives the entry, byte and handle limits. A trace row contains an identity,
payload bytes and retained-pair bytes. Repeated identities must keep the same sizes.
These are arithmetic identities and frozen charges, not operating-system objects.

Run from any directory, supplying the tool and input paths:

```text
python path/to/custody-trace/custody_trace_analysis.py trace.json
python path/to/custody-trace/custody_trace_analysis.py trace.json --detail-limit 2 --window-size 3
python path/to/custody-trace/custody_trace_analysis.py trace.json --producer path/to/custody_trace.py --output result.json
```

The default output is one UTF-8 JSON document plus a newline on stdout. `--output`
instead creates a new file; it refuses to overwrite an existing file and does not
create parent directories. Successful file output leaves stdout empty. Output is
fully encoded and checked against the byte limit before the file is opened. A write
failure may leave a partial newly created file; output publication is not atomic.
Relative input paths, relative explicit producer paths and relative output paths
are interpreted relative to the current directory; absolute paths remain absolute. An explicit producer never falls back to the adjacent producer.

Input is read and its outer JSON envelope validated before the producer is read.
The producer's caps and row validation follows its hash check. Analysis and encoded
output-size validation precede opening the output file. Handled failures print a
diagnostic on stderr and exit with status 2.

Detail defaults to zero and is limited to the first 128 requests. If detail omits a
suffix, full-trace reacquisition remains `UNKNOWN_UNEXPLAINED_SUFFIX`. At most eight
windows of size 1 through 8192 may be requested. Input and encoded output are each
limited to 1 MiB; the trace is limited to 100000 rows. These limits are not an OS
memory, CPU or process sandbox.

Acquisition attempts, prior-fallback requests and true same-trace reacquisitions are
separate quantities. Current retention, cumulative retention events and peak
occupancy are also separate. Reuse distance counts distinct other identities in the
finite supplied trace. Window charge counts each identity once within a request
window; neither quantity establishes FIFO miss behavior on an actual workload.
The underlying arithmetic assumes successful double-close when a pair is retired.

The neighboring `portable_cli_witness.py` is a developer check for relocation, explicit
producer/output selection and failure ordering. Its new CLI scenarios are separate
from the older three arithmetic examples and the producer's older vector suite.
Use an existing owned work directory:

```text
python path/to/custody-trace/portable_cli_witness.py --work-root path/to/owned-existing-dir
```

The witness defaults to its neighboring analyzer and producer; `--source-dir` can
instead select their directory. It creates a fresh subdirectory within the work
root and retains its files for review. It never recursively removes the given root.
Software results,
repository publication, non-Windows operation and Runtime adoption are distinct
qualifications; no benchmark or live integration is provided here.
