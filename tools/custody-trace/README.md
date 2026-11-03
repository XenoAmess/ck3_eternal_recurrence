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

The neighboring `test_custody_trace_portable_boundaries.py` provides a Python
unittest entry. Its source defines five methods and six public CLI invocations,
separate from the six scenarios in the `portable_cli_witness.py` driver above.
Keep the Test beside the analyzer and pinned producer, and use this command:

```text
python path/to/custody-trace/test_custody_trace_portable_boundaries.py --work-root ABSOLUTE_EXISTING_OWNED_DIRECTORY -v PortableCliBoundaryTests
```

Replace `ABSOLUTE_EXISTING_OWNED_DIRECTORY` with an existing absolute owned
directory. Normal unittest progress and its final summary go to stderr; interpret
its exit status and summary as the Test result. That standard stderr output is
expected and does not by itself indicate a business CLI failure.

Each method creates a disposable `TemporaryDirectory` inside the work root and
registers unittest cleanup for that child. The supplied work root remains. The
portable driver above retains its fresh child and files for review. These are
different evidence-retention behaviors. Current execution qualification comes
from the actual receipt for the named entry; source counts and this README do not
establish a run, passed checks, publication or Runtime adoption.

The neighboring `default_producer_search_witness.py` is a separate single-scenario
developer check. It puts the pinned analyzer in a tool-only directory, puts the
pinned producer in a different working directory, and invokes the analyzer without
`--producer`. A missing adjacent default producer must not be rescued by the
producer in the working directory. Choose one invocation form:

```text
python path/to/custody-trace/default_producer_search_witness.py --work-root ABSOLUTE_EXISTING_OWNED_DIRECTORY
python path/to/custody-trace/default_producer_search_witness.py --source-dir path/to/custody-trace --work-root ABSOLUTE_EXISTING_OWNED_DIRECTORY
```

`--source-dir` defaults to the resolved witness file directory; an override selects
the directory containing the exact analyzer and producer peers. `--work-root` is
required and must name an existing absolute owned directory. The witness creates
one unique child there, retains its fixture files and raw `cli.stdout.bin` and
`cli.stderr.bin` logs, and does not delete the supplied root.

The intended outcome of its one business CLI child is exit 2 with an empty stdout
and a `FileNotFoundError` for the missing tool-side producer. It also checks that
no output was created and the copied analyzer and working-directory producer bytes
are unchanged. Only after those assertions does the outer witness exit 0 and print
its JSON manifest. On ordinary bounded-output or timeout failure, a bounded raw
prefix is retained when cleanup and log creation succeed. If cleanup or log
creation itself fails, evidence may be incomplete. Read the actual outer result and retained logs for this named entry;
these source expectations do not establish a passed run, native custody, another
platform qualification or Runtime adoption.
