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
