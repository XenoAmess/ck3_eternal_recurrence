# G2 native production helpers

These Windows Python tools build the selected 917-owner native source closure.
Root supplies explicit immutable inputs, output paths, deadlines, CPU/RAM/storage
reservations and six separate reviewed admissions. Their outputs distinguish
metadata preparation, actual production compilation and whole-build proof from
Game/SDK adoption or live family qualification.

1. `render_native_fresh_manifest.py --config <Root-config> --config-sha256 <sha>`
   writes one fresh manifest and six review drafts. It binds actual Native88
   owner/command/RSP metadata and component mappings; missing historical commands
   use an explicitly selected new compilation policy. Root reviews all 917 jobs
   and supplies the admissions at the predetermined paths.
2. `produce_native_parallel_candidate.py <manifest>` launches the actual compiler
   jobs, followed by the exact archive, member listing and DLL link. Root selects
   concurrency from 1 to 64; jobs have private output, dependency, PDB and temporary
   paths. The first error stops dispatch, retains prior files and observes every
   submitted worker. There is no automatic retry. The actual output packet status
   is `BUILD_OUTPUTS_VERIFIED_NO_RUNTIME_CREDIT`.
3. `normalize_actual_native_whole.py <input-manifest>` checks the actual 917
   compiler/dependency/owner chains, 597-member archive order and selected link
   inputs. It writes a bounded closure proof. Root separately records the actual
   normalizer exit and proof readback. Raw production files remain the references
   in that proof; loader-compatible derivatives must preserve their provenance.

An explicitly admitted continuation can finish a stopped production build:

- `close_verified_native_rsp_candidate.py <config> <config-sha256>` revalidates
  the original 917 successful compilations and admits fresh archive/LIST/link
  jobs with exactly preserved response-file tokens. Its config schema is
  `xar.native.closure.rsp/v1`. Native89's original archive process never started
  because its direct command exceeded the Windows process command limit.
- `link_verified_native_rc_candidate.py <config> <config-sha256>` revalidates
  the original compilations and the successful 597-member archive/LIST, then
  launches one fresh link job. Its schema is `xar.native.link.rc/v1`. The previous
  link actually returned LNK1158 because `rc.exe` was unavailable in its PATH;
  the new job prepends one explicitly pinned installed Windows SDK directory.
  It retains manifest embedding and the original options, and verifies the four
  resource-tool input files before and after the actual link.

These continuations require separate Root admissions, fresh job/result paths and
the original finite budget and deadline. They never resend an old job or execute
compilers again. Aggregate compile/dependency counts remain 917; this step's
invocation counts are recorded separately. Original STOP records remain intact.
An available tool pin is not evidence that the linker invoked that tool.

The original source was fully reviewed by Root and two independent reviewers.
Native89's actual run uses a separately pinned Root copy and frozen SDK91 source
`50a1a5451227d1b30f42394dd02ddfbaea26a1ff`. Current master changes do not alter
that run. Future changed private DTO/header definitions need their own freeze and
complete consumer compilation. Tests, fixtures and FIRST were not run for this
source adoption. Runtime credit comes only from subsequent actual operation.

Apply the repository's [common storage policy](../../docs/storage-retention-policy.md)
and its versioned parameters at admission and closure. Research-leaf reservations
do not qualify production output; deadlines and finite reservations are explicit
Root inputs and are never renewed by these tools.
