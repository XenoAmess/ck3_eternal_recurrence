# Saved Faith semantics v2

This is a versioned reader observation model for CK3 1.20.0.3. Original R14 B4/B5
results, frozen business contracts and failed protection receipts remain unchanged.

The actual saved Faith `religious_head` field contains a landed Title identity.
The reader preserves every raw `heads` field, complete entries and AST digest,
then derives `typed_religious_title_reference` and a saved Title/full-AST/holder
join. It rejects the earlier authored two-field Character/Title fixture shape.
That synthetic producer now explicitly authors the observed single-field model.
Wrong Faith, result Title, holder, missing entity, noncanonical scalar and digest
drift cannot qualify this join. This saved observation grants no native getter credit.

Schema `lyd.i3b.checkpoint-reader-request.v2` adds a closed
`saved_faith_semantics_binding` containing schema
`lyd.saved-Faith-semantics-binding.v2` and the exact SHA-256 of
`reader/dependencies/saved_faith_semantics_12003.json`. The captured Faith baseline
must also retain its complete `entries`, matching `AST_sha256` and doctrine rows.
Requests using v1 preserve their original direct-doctrine check expectations.

The v2 doctrine model derives the head-of-faith group from the current saved Faith,
its exact main Rite identity, and the Rite's parent Faith. Stock group membership
and exact installed .3 getter spans are frozen in the semantic descriptor. A
main Rite entry for this group takes precedence; an unoccupied Rite group uses
the Faith entry. Ambiguous or missing group state and wrong main/parent joins fail.
The output shows direct Faith `doctrine_no_head` separately from the derived
effective `doctrine_temporal_head`. `native_predicate_observed` and native credit
remain null: source bytes and saved ASTs do not constitute a current native query.

Successful postcommit v2 Faith checks permit exactly the source-declared changes:
the explicit headless Title sentinel becomes the discovered actual result Title,
and absent `lyd_c3_recognized_leader` becomes one exact typed Character row for the
actor. All other Faith entries, variable rows, their relative order, direct doctrine
rows and tenet/status rows must remain identical. A pre-existing baseline leader,
duplicate, wrong discriminator or identity is rejected. Political Title ASTs and
the actor's political landed projection receive no exception.

The small fixtures reconstruct selected already-parsed R14 rows into synthetic
save text. They do not reopen a checkpoint or authenticate a live world frame.
The v1 reconstruction retains seven failed checks after the two head-field errors
are corrected; the v2 reconstruction retains five political AST failures.
Original R14 reader 38/47 and protection 80/87 results are permanent historical RED.
Future new source HEAD, native build, metadata, profile, SDK frames and actual
checkpoint evidence must be independently produced and qualified.

Run the reader tests with the selected interpreter:

```text
python -B -m unittest discover -s tools/lyd_i3b_checkpoint_readback/tests -p test_*.py -v
```
