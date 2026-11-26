# Normal launcher installation for the Byzantine867 side mod

Status: source-prepared normal-profile registration, 2026-10-07. Root owns
execution and launcher UI verification. This owner made no database/profile
write, game launch/input, process inspection, EXE read or SDK query.

Root's earlier installation helper installs the outer descriptor, inner
descriptor and on_action file, and adds the normal profile's enabled_mod entry.
Its receipt explicitly records launcher_database_modified=false. This makes
the installed files and direct game load different facts from launcher
registration or selected-playset verification.

The original launcher-log result is a historical preinstallation diagnostic.
A necessary current read-only schema/target query now confirms the exact
normal database is launcher-v2_openbeta.sqlite in the resolved normal CK3
Documents profile. The exact target gameRegistryId has zero records; there
are no active playsets. Existing local mod rows establish source=local,
status=ready_to_play, a mod/<outer>.mod registry ID and absolute payload dirPath.
The actual target descriptor defines name "Byzantium 867 - Conqueror",
version1.0.1, supported_version1.20.* and tagGameplay.

Held project/install helpers do not contain a launcher database registration
path. The available source does not prove whether the next launcher discovery
will register this descriptor or whether active-playset zero will preserve the
enabled_mods fallback. Do not promise automatic discovery or claim "Launcher
verified" from the direct R71 mod outcome.

## Concrete Root-only completion recipe

The prepared script is
[register_byzantium_normal_launcher_once.py](Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/root-only-source/register_byzantium_normal_launcher_once.py).
Root invokes it with a fresh output directory; it performs:

1. SQLite Connection.backup to the exact database name inside that directory.
   This includes the committed WAL state; copying only the .sqlite file would
   not be the chosen backup.
2. BEGIN IMMEDIATE and reuse/create one exact local mods record.
   The record uses the installed normal descriptor metadata and absolute
   normal payload path. No workshop/subscription identifiers are added.
3. Reuse/create a dedicated private "Byzantium 867 - Conqueror" playset,
   containing only the exact target mod, enabled at position0, and activate it.
   The observed old playsets all have isActive0. If another playset has become
   active, the script preserves it rather than deactivating it.
4. Check every unrelated mod/playset/membership row inside the transaction
   before commit. Preserve dlc_load.json, all unrelated files, global
   preferences, subscriptions and workshop cache.
5. Write the exact IDs, counts, SQLite backup path and preservation result.

The helper was authored but not executed by this owner. Root's eventual
receipt establishes database registration/activation; actual normal launcher
selection and visibility remain separate observations. No further game run is
needed merely to inspect that launcher selection.

The SQLite backup is the pretransaction recovery artifact. If Root needs to
restore it, close the normal launcher using the database first; restoration is
not performed by this source-only lane.

Exact argv and source conventions are in
[NORMAL-LAUNCHER-INSTALL-ROOT-RECIPE.json](Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/frontend-main-reachability-12004/NORMAL-LAUNCHER-INSTALL-ROOT-RECIPE.json)
and its adjacent SOURCE-METADATA.json. The original normal-profile diagnostic,
R71 actual game result and source-only registration recipe remain distinct.
