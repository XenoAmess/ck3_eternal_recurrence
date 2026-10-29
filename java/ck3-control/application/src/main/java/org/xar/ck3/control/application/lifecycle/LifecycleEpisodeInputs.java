package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier;
import org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier.VerifiedFirstCheckpoint;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SameGameTransportContinuity;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Joins the unique lifecycle service's real private episode proof to its published Driver
 * and a subsequent original SEM. The shared cycle authority consumes this input and owns
 * its single zero-credit branch transition. This class never reduces or writes a cycle.
 */
public final class LifecycleEpisodeInputs {
    private enum CurrentRole { ORIGINAL_ADMISSION, TRANSPORTED_ADMISSION }
    private final ContinuityStorePort writer;
    private final SessionAuthority writerAuthority;
    private final LifecycleComposites lifecycle;
    private final DriverStateAssembler drivers;
    private final ActionPorts.OutcomeArchive archive;
    private final OrdinaryCycleTransitions.SemanticVerifier semantics;

    public LifecycleEpisodeInputs(ContinuityStorePort soleWriter, SessionAuthority actualWriterAuthority, LifecycleComposites soleLifecycle,
            DriverStateAssembler actualDrivers, ActionPorts.OutcomeArchive originalArchive,
            OrdinaryCycleTransitions.SemanticVerifier actualSemanticVerifier) {
        writer = Objects.requireNonNull(soleWriter); writerAuthority = Objects.requireNonNull(actualWriterAuthority); lifecycle = Objects.requireNonNull(soleLifecycle);
        drivers = Objects.requireNonNull(actualDrivers); archive = Objects.requireNonNull(originalArchive);
        semantics = Objects.requireNonNull(actualSemanticVerifier);
    }

    public Binding bind(ContinuityStorePort.Session borrowed, SessionIdentity beforeOwner,
            SessionIdentity actualAfterOwner, ActionReceipt actualParent, SemanticEvidence freshAfter) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(beforeOwner); Objects.requireNonNull(actualAfterOwner);
        Objects.requireNonNull(actualParent); Objects.requireNonNull(freshAfter);
        writerAuthority.require(borrowed);
        var head = borrowed.head();
        LifecycleTransitionProof.Base live = lifecycle.requireCommittedEpisode(borrowed, actualParent);
        LifecycleTransitionProof proof = (LifecycleTransitionProof) live;
        LifecyclePublication publication = live.publication();
        return inArchive(borrowed, bound -> drivers.withFrozenFacts(borrowed, frozen -> {
            requirePublicationOriginals(borrowed, publication);
            DriverStateSnapshot.Complete predecessor = predecessor(bound, publication, actualParent);
            requireBranch(proof, actualParent, beforeOwner, actualAfterOwner, freshAfter, predecessor);
            DriverSnapshotFacts.Known known = requirePublished(frozen, actualAfterOwner, freshAfter, bound);
            requireCanonical(head.state(), actualParent, beforeOwner, actualAfterOwner, bound);
            var verified = semantics.verify(borrowed, actualAfterOwner, freshAfter);
            requireSemantic(freshAfter, verified);
            StrictJson.require(head.digest().equals(borrowed.head().digest()),
                    "episode input capture crossed the actual writer head");
            Binding result = new Binding(this, beforeOwner, actualAfterOwner, actualParent, proof, publication,
                    known.stamp(), predecessor, known.driver(), freshAfter, verified.materialDigest(), head.state().sequence(), head.digest());
            writerAuthority.require(borrowed);
            return result;
        }));
    }

    /** Shared cycle preview and commit both call this under their original writer Session. */
    public void requireCurrent(ContinuityStorePort.Session borrowed, Binding binding) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(binding);
        StrictJson.require(binding.issuer == this, "episode input belongs to another lifecycle input producer");
        writerAuthority.require(borrowed);
        StrictJson.require(binding.headDigest.equals(borrowed.head().digest()),
                "episode input must be consumed at its actual original writer head");
        LifecycleTransitionProof.Base live = lifecycle.requireCommittedEpisode(borrowed, binding.parent);
        StrictJson.require(live == binding.proof && live.publication() == binding.publication,
                "recorded lifecycle bytes cannot replace the original private committed episode proof");
        inArchive(borrowed, bound -> drivers.withFrozenFacts(borrowed, frozen -> {
            requirePublicationOriginals(borrowed, binding.publication);
            DriverStateSnapshot.Complete predecessor = predecessor(bound, binding.publication, binding.parent);
            requireBranch(binding.proof, binding.parent, binding.beforeOwner, binding.afterOwner, binding.semantic, predecessor);
            StrictJson.require(Arrays.equals(predecessor.encode(), binding.predecessorDriver.encode()),
                    "original committed predecessor Driver changed before episode input consumption");
            DriverSnapshotFacts.Known known = requirePublished(frozen, binding.afterOwner, binding.semantic, bound);
            StrictJson.require(known.stamp().equals(binding.driverStamp)
                    && Arrays.equals(known.driver().encode(), binding.driver.encode()),
                    "complete episode Driver changed before the cycle authority consumed it");
            requireCanonical(borrowed.head().state(), binding.parent, binding.beforeOwner, binding.afterOwner, bound);
            var verified = semantics.verify(borrowed, binding.afterOwner, binding.semantic);
            requireSemantic(binding.semantic, verified);
            StrictJson.require(verified.materialDigest().equals(binding.semanticDigest)
                    && binding.headDigest.equals(borrowed.head().digest()),
                    "actual episode original material or writer head changed during qualification");
            writerAuthority.require(borrowed);
            return null;
        }));
    }

    /**
     * A separate current role after a real canonical Cycle admission. Historical publication
     * DATA and the journal's private admission ticket never recreate the original exact-post Base.
     */
    public CurrentAdoptionBinding bindAdmittedCurrent(ContinuityStorePort.Session borrowed,
            ContinuityBatchJournal.HistoricalEpisodeAdoption historical, SemanticEvidence freshCurrent) throws IOException {
        return bindCurrent(borrowed,historical,freshCurrent,CurrentRole.ORIGINAL_ADMISSION);
    }

    /** Separate same-Game transport route. Only the actual journal can issue its canonical transport ticket. */
    public CurrentAdoptionBinding bindTransportedCurrent(ContinuityStorePort.Session borrowed,
            ContinuityBatchJournal.HistoricalEpisodeAdoption historical, SemanticEvidence freshCurrent) throws IOException {
        return bindCurrent(borrowed,historical,freshCurrent,CurrentRole.TRANSPORTED_ADMISSION);
    }

    private CurrentAdoptionBinding bindCurrent(ContinuityStorePort.Session borrowed,
            ContinuityBatchJournal.HistoricalEpisodeAdoption historical, SemanticEvidence freshCurrent, CurrentRole role) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(historical); Objects.requireNonNull(freshCurrent);
        writerAuthority.require(borrowed);
        var head = borrowed.head();
        historical.requireCurrent(borrowed);
        var recorded = historical.recorded();
        CurrentAdoptionBinding result = inArchive(borrowed, bound -> drivers.withFrozenFacts(borrowed, frozen -> {
            requireAdmittedBranch(borrowed, historical, recorded, freshCurrent, role);
            DriverSnapshotFacts.Known known = requirePublished(frozen, historical.owner(), freshCurrent, bound);
            requireAdmittedEpoch(known, recorded);
            requireCanonicalCurrent(head.state(),recorded.parent(),historical.owner(),bound,role);
            var verified = semantics.verify(borrowed, historical.owner(), freshCurrent);
            requireSemantic(freshCurrent, verified);
            StrictJson.require(head.digest().equals(borrowed.head().digest()),
                    "current admission capture crossed its actual original writer head");
            return new CurrentAdoptionBinding(this, historical, recorded, known.stamp(), known.driver(),
                    freshCurrent, verified.materialDigest(), head.state().sequence(), head.digest(),role);
        }));
        writerAuthority.require(borrowed);
        return result;
    }

    /** Rechecks this independent current role; never requests or relaxes an old exact-post Base. */
    public void requireCurrentAdoption(ContinuityStorePort.Session borrowed, CurrentAdoptionBinding binding) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(binding);
        StrictJson.require(binding.issuer == this, "current adoption belongs to another actual M7 producer");
        writerAuthority.require(borrowed);
        StrictJson.require(binding.headDigest.equals(borrowed.head().digest()),
                "current adoption must be consumed at its actual captured writer head");
        binding.historical.requireCurrent(borrowed);
        StrictJson.require(binding.historical.recorded() == binding.recorded,
                "current adoption lost the journal ticket's original historical publication");
        inArchive(borrowed, bound -> drivers.withFrozenFacts(borrowed, frozen -> {
            requireAdmittedBranch(borrowed, binding.historical, binding.recorded, binding.semantic,binding.role);
            DriverSnapshotFacts.Known known = requirePublished(frozen, binding.owner(), binding.semantic, bound);
            requireAdmittedEpoch(known, binding.recorded);
            StrictJson.require(known.stamp().equals(binding.driverStamp)
                    && Arrays.equals(known.driver().encode(), binding.driver.encode()),
                    "actual current Driver changed before admitted-episode consumption");
            requireCanonicalCurrent(borrowed.head().state(),binding.parent(),binding.owner(),bound,binding.role);
            var verified = semantics.verify(borrowed, binding.owner(), binding.semantic);
            requireSemantic(binding.semantic, verified);
            StrictJson.require(verified.materialDigest().equals(binding.semanticDigest)
                    && binding.headDigest.equals(borrowed.head().digest()),
                    "current admitted SEM, source material or original writer changed");
            return null;
        }));
        writerAuthority.require(borrowed);
    }

    private static void requireAdmittedBranch(ContinuityStorePort.Session borrowed,
            ContinuityBatchJournal.HistoricalEpisodeAdoption historical, LifecycleHistoricalPublication.Recorded recorded,
            SemanticEvidence semantic,CurrentRole role) throws IOException {
        StrictJson.require(historical.recorded() == recorded && historical.parent().equals(recorded.parent()),
                "journal admission must retain its actual original canonical lifecycle parent");
        var publication = recorded.publication();
        requirePublicationOriginals(borrowed, publication);
        var parent = recorded.parent(); var proof = recorded.proof();
        proof.validateParent(parent.command());
        StrictJson.require(proof.kind() == LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR
                && parent.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED,
                "admitted continuation requires the actual settled historical successor publication");
        var owner = historical.owner(); var original = parent.command().lifecycleBefore();
        var current = semantic.frame(); var cycle = historical.frame();
        if(role==CurrentRole.ORIGINAL_ADMISSION) {
            StrictJson.require(historical.transportEvidence().isEmpty()
                    &&owner.sessionId().equals(parent.command().sessionId()),
                    "original current admission cannot consume a transported ticket or another session");
        }else {
            var transport=historical.transportEvidence().orElseThrow(
                    ()->new IllegalArgumentException("transported current requires the actual journal-issued transport ticket"));
            StrictJson.require(transport.purpose()==SameGameTransportContinuity.Purpose.FINALIZED_METADATA_ONLY
                    &&transport.afterOwner().equals(owner)&&transport.canonicalParent().equals(parent)
                    &&transport.beforeOwner().machineId().equals(original.machineId())
                    &&transport.beforeOwner().game().equals(original.game()),
                    "transported current lost its actual finalized canonical parent or same-Game owner lineage");
            var transported=transport.semantic().frame();
            StrictJson.require(transported.machineId().equals(owner.machineId())&&transported.game().equals(owner.game())
                    &&transported.frame().episodeRunId().equals(current.frame().episodeRunId())
                    &&transported.frame().identity().player().equals(current.frame().identity().player())
                    &&current.frame().identity().dateRaw().compareTo(transported.frame().identity().dateRaw())>=0
                    &&current.frame().identity().nativeRevision().compareTo(transported.frame().identity().nativeRevision())>=0
                    &&current.frame().revision().compareTo(transported.frame().revision())>=0,
                    "transported current crossed or rewound its actual canonical transport semantic branch");
        }
        StrictJson.require(owner.machineId().equals(original.machineId()) && owner.game().equals(original.game())
                && owner.machineId().equals(current.machineId()) && owner.game().equals(current.game())
                && cycle.machineId().equals(current.machineId()) && cycle.game().equals(current.game())
                && cycle.frame().episodeRunId().equals(current.frame().episodeRunId())
                && cycle.frame().identity().player().equals(current.frame().identity().player()),
                "current qualification crossed the actual admitted Cycle actor, run, full Game or session");
        StrictJson.require(current.frame().identity().dateRaw().compareTo(cycle.frame().identity().dateRaw()) >= 0
                && current.frame().identity().nativeRevision().compareTo(cycle.frame().identity().nativeRevision()) >= 0
                && current.frame().revision().compareTo(cycle.frame().revision()) >= 0,
                "current SEM rewound the genuinely admitted current Cycle frontier");
        var result = LifecycleProofMaterialJson.result(proof.encodedResult());
        StrictJson.require(StrictJson.text(result.get("source_run_id")).equals(original.subject().episodeRunId())
                && StrictJson.text(result.get("episode_run_id")).equals(current.frame().episodeRunId())
                && !original.subject().episodeRunId().equals(current.frame().episodeRunId())
                && StrictJson.integer(result.get("predecessor_character_id"), 1, 0xffff_fffeL)
                        == original.subject().characterId().longValueExact()
                && StrictJson.integer(result.get("actual_successor_character_id"), 1, 0xffff_fffeL)
                        == current.frame().identity().player().longValueExact()
                && !original.subject().characterId().equals(current.frame().identity().player()),
                "current episode does not retain the actual admitted historical successor");
        StrictJson.require(recorded.predecessorDriverReference().equals(original.evidence().originalDriver())
                && current.frame().identity().dateRaw().compareTo(original.frame().dateRaw()) >= 0
                && current.frame().identity().nativeRevision().compareTo(original.frame().nativeRevision()) >= 0,
                "current admitted branch lost its exact causal predecessor or rewound Native history");
        java.time.Instant publishedAt = java.time.Instant.parse(StrictJson.utc(StrictJson.text(result.get("observed_at"))));
        StrictJson.require(semantic.observedAt().isAfter(publishedAt),
                "current admitted SEM must actually follow the original lifecycle observation");
    }

    private static void requireAdmittedEpoch(DriverSnapshotFacts.Known known, LifecycleHistoricalPublication.Recorded recorded) {
        long originalEpoch = StrictJson.integer(recorded.publication().detailsObject().get("driver_snapshot").get("next_epoch"),
                0, StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require(known.stamp().episodeEpoch() == originalEpoch,
                "current admitted Driver belongs to another actual episode epoch");
    }

    /** A distinct branch: BEGIN, one real first SAVE, committed BASELINE, and an actual post-SAVE SEM. */
    public NextBaselineBinding bindAfterBaseline(ContinuityStorePort.Session borrowed, Binding originalPreBegin,
            FirstCheckpointVerifier firstSaves, VerifiedFirstCheckpoint first,
            EpisodeWindow.CommittedBaseline baseline, SemanticEvidence freshPostSave) throws IOException {
        Objects.requireNonNull(originalPreBegin); Objects.requireNonNull(firstSaves); Objects.requireNonNull(first);
        Objects.requireNonNull(baseline); Objects.requireNonNull(freshPostSave);
        StrictJson.require(originalPreBegin.issuer == this && originalPreBegin.proof instanceof LifecycleTransitionProof.NextEpisode,
                "new-window baseline requires this producer's original private NEXT input");
        writerAuthority.require(borrowed);
        String head = borrowed.head().digest();
        NextBaselineBinding result = inArchive(borrowed, bound -> drivers.withFrozenFacts(borrowed, frozen -> {
            var known = requirePublished(frozen, originalPreBegin.afterOwner, freshPostSave, bound);
            var verified = semantics.verify(borrowed, originalPreBegin.afterOwner, freshPostSave);
            requireSemantic(freshPostSave, verified);
            var binding = new NextBaselineBinding(this, originalPreBegin, firstSaves, first, baseline,
                    known.stamp(), known.driver(), freshPostSave, verified.materialDigest(), head);
            requireBaselineOriginals(borrowed, binding, bound, known);
            StrictJson.require(head.equals(borrowed.head().digest()), "writer changed while capturing actual post-baseline input");
            return binding;
        }));
        writerAuthority.require(borrowed);
        return result;
    }

    /** Canonical descendants may include the sole cycle's rebind; full Driver and ACTIVE first pair remain exact. */
    public void requireCurrentBaseline(ContinuityStorePort.Session borrowed, NextBaselineBinding binding) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(binding);
        StrictJson.require(binding.issuer == this, "new-window input belongs to another producer");
        writerAuthority.require(borrowed); String head = borrowed.head().digest();
        inArchive(borrowed, bound -> drivers.withFrozenFacts(borrowed, frozen -> {
            var known = requirePublished(frozen, binding.afterOwner(), binding.semantic, bound);
            StrictJson.require(known.stamp().equals(binding.driverStamp) && Arrays.equals(known.driver().encode(), binding.driver.encode())
                    && frozen.actions().headSha256().equals(head), "first-SAVE Driver changed before new-window input consumption");
            requireBaselineOriginals(borrowed, binding, bound, known);
            var verified = semantics.verify(borrowed, binding.afterOwner(), binding.semantic);
            requireSemantic(binding.semantic, verified);
            StrictJson.require(verified.materialDigest().equals(binding.semanticDigest) && head.equals(borrowed.head().digest()),
                    "post-SAVE original SEM or canonical writer changed during baseline qualification");
            return null;
        }));
        writerAuthority.require(borrowed);
    }

    private void requireBaselineOriginals(ContinuityStorePort.Session borrowed, NextBaselineBinding binding,
            ActionPorts.OutcomeArchive bound, DriverSnapshotFacts.Known known) throws IOException {
        Binding original = binding.original;
        borrowed.requireHistoricalState(original.headSequence, original.headDigest);
        var proof = lifecycle.requireRetainedEpisode(borrowed, original.parent, (LifecycleTransitionProof.Base) original.proof);
        StrictJson.require(proof == original.proof && proof.publication() == original.publication,
                "baseline lost the actual original private lifecycle commit");
        requirePublicationOriginals(borrowed, original.publication);
        binding.firstSaves.requireIssued(borrowed, binding.first);
        borrowed.requireEpisodeWindowActive(binding.baseline);
        var first = binding.first; var baseline = binding.baseline.baseline(); var begin = baseline.begin().begin();
        StrictJson.require(first.baseline().equals(baseline) && first.begin().equals(baseline.begin())
                && first.session().equals(original.afterOwner) && begin.parentActionId().equals(original.parent.command().actionId())
                && begin.lifecycleEventIdentity().equals(original.commitDigest())
                && begin.lifecycleSequence() == original.publication.eventSequence()
                && begin.before().machineId().equals(original.beforeOwner.machineId()) && begin.before().game().equals(original.beforeOwner.game())
                && begin.before().sessionId().equals(original.beforeOwner.sessionId())
                && begin.after().machineId().equals(original.afterOwner.machineId()) && begin.after().game().equals(original.afterOwner.game())
                && begin.after().sessionId().equals(original.afterOwner.sessionId())
                && begin.after().epoch() == original.driverStamp.episodeEpoch()
                && begin.after().epoch() == known.stamp().episodeEpoch()
                && begin.adoptedDriverRef().equals(org.xar.ck3.control.contracts.ExactRef.fromJson(
                        original.publication.detailsObject().get("delta").get("adopted_driver_ref"))),
                "first-SAVE BASELINE crossed its original NEXT, BEGIN or full physical owner ancestry");
        var lifecycleEvent = original.publication.committedDocuments().stream()
                .filter(pin -> pin.reference().equals(begin.lifecycleEventRef())).findFirst()
                .orElseThrow(() -> new IOException("BEGIN does not retain the original lifecycle event file identity"));
        borrowed.verifyPin(lifecycleEvent);
        StrictJson.require(Arrays.equals(bound.loadFullMaterial(begin.adoptedDriverRef()).bytes(), original.driver.encode())
                && Arrays.equals(first.originalDriver().encode(), original.driver.encode())
                && Arrays.equals(first.savedDriver().encode(), known.driver().encode()),
                "new-window full Driver is not the exact original NEXT plus its one real first SAVE projection");
        requireBranch(original.proof, original.parent, original.beforeOwner, original.afterOwner, binding.semantic, original.predecessorDriver);
        requireCanonical(borrowed.head().state(), original.parent, original.beforeOwner, original.afterOwner, bound);
        var savedEffect = first.canonicalSave().applied().orElseThrow(
                () -> new IllegalArgumentException("first SAVE requires its actual applied postcondition")).observation();
        var after = binding.semantic.frame(); var savedFrame = savedEffect.after();
        StrictJson.require(binding.semantic.observedAt().isAfter(savedEffect.observedAt())
                && after.frame().identity().dateRaw().equals(savedFrame.frame().identity().dateRaw())
                && after.frame().identity().nativeRevision().compareTo(savedFrame.frame().identity().nativeRevision()) >= 0
                && after.frame().revision().compareTo(savedFrame.frame().revision()) >= 0,
                "new-window SEM must actually follow the same first SAVE without game advance or revision rewind");
    }

    private static void requireBranch(LifecycleTransitionProof proof, ActionReceipt parent,
            SessionIdentity before, SessionIdentity after, SemanticEvidence semantic, DriverStateSnapshot.Complete predecessor) {
        StrictJson.require(proof instanceof LifecycleTransitionProof.ContinueSuccessor
                || proof instanceof LifecycleTransitionProof.NextEpisode,
                "only the private committed successor or immutable-seed next episode may change the cycle owner");
        proof.validateParent(parent.command());
        StrictJson.require(parent.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED,
                "pending or UNKNOWN lifecycle outcome cannot hand off an episode");
        LifecycleIdentity original = parent.command().lifecycleBefore(); var current = semantic.frame();
        StrictJson.require(before.machineId().equals(original.machineId()) && before.game().equals(original.game())
                && before.sessionId().equals(parent.command().sessionId())
                && after.machineId().equals(before.machineId()) && after.machineId().equals(current.machineId())
                && after.game().equals(current.game()), "episode input crossed its actual original or replacement owner");
        StrictJson.require(!original.subject().episodeRunId().equals(current.frame().episodeRunId()),
                "a new episode requires the actual committed distinct episode identifier");
        StrictJson.require(predecessor.session().bridgePid() == before.game().pid()
                && predecessor.session().episodeRunId().equals(original.subject().episodeRunId())
                && predecessor.session().actorId().equals(original.subject().characterId()),
                "original lifecycle Driver differs from the actual predecessor Game and episode");
        if (proof instanceof LifecycleTransitionProof.ContinueSuccessor) {
            StrictJson.require(after.equals(before)
                    && !predecessor.session().actorId().equals(current.frame().identity().player())
                    && current.frame().identity().dateRaw().compareTo(original.frame().dateRaw()) >= 0
                    && current.frame().identity().nativeRevision().compareTo(original.frame().nativeRevision()) >= 0,
                    "natural succession must retain the exact Game/session and advance to the actual different actor");
        } else StrictJson.require(!after.game().equals(before.game()),
                "immutable-seed next episode must retain the real distinct replacement Game birth");
        var result = LifecycleProofMaterialJson.result(proof.encodedResult());
        StrictJson.require(StrictJson.text(result.get("source_run_id")).equals(original.subject().episodeRunId())
                && StrictJson.text(result.get("episode_run_id")).equals(current.frame().episodeRunId()),
                "fresh episode SEM differs from the actual committed lifecycle result");
        String actor = proof instanceof LifecycleTransitionProof.ContinueSuccessor
                ? "actual_successor_character_id" : "episode_character_id";
        StrictJson.require(StrictJson.integer(result.get(actor), 1, 0xffff_fffeL)
                == current.frame().identity().player().longValueExact(),
                "fresh episode actor differs from the actual committed result");
        if (proof instanceof LifecycleTransitionProof.ContinueSuccessor)
            StrictJson.require(StrictJson.integer(result.get("predecessor_character_id"), 1, 0xffff_fffeL)
                    == predecessor.session().actorId().longValueExact(),
                    "natural successor result differs from its actually archived predecessor Driver subject");
        java.time.Instant committedAt = java.time.Instant.parse(StrictJson.utc(StrictJson.text(result.get("observed_at"))));
        StrictJson.require(semantic.observedAt().isAfter(committedAt),
                "episode SEM must be collected after the real lifecycle observation/publication");
    }

    private static void requirePublicationOriginals(ContinuityStorePort.Session borrowed, LifecyclePublication publication) throws IOException {
        StrictJson.require(publication.eventSequence() == publication.after().sequence()
                && publication.eventSequence() == Math.addExact(publication.before().sequence(), 1)
                && publication.before().machineId().equals(publication.after().machineId())
                && publication.after().machineId().equals(borrowed.head().state().machineId())
                && publication.eventSequence() <= borrowed.head().state().sequence()
                && publication.eventIdentity().equals(StrictJson.text(publication.after().toJson().get("last_event_identity"))),
                "lifecycle publication must retain its original one-event canonical state edge");
        StrictJson.require(!publication.committedDocuments().isEmpty()
                && publication.proofDocuments().containsAll(publication.committedDocuments()),
                "lifecycle publication must retain the actual committed event and complete original proof pins");
        for (var pin : publication.proofDocuments()) borrowed.verifyPin(pin);
        var historical = borrowed.requireHistoricalState(publication.eventSequence(),
                org.xar.ck3.control.continuity.ContinuityJson.digest(publication.after().toJson()));
        StrictJson.require(Arrays.equals(historical.canonicalBytes(), publication.after().canonicalBytes()),
                "lifecycle publication differs from the actual canonical historical reducer result");
    }

    private static DriverStateSnapshot.Complete predecessor(ActionPorts.OutcomeArchive bound, LifecyclePublication publication, ActionReceipt parent) {
        var details = publication.detailsObject();
        var delta = details.get("delta");
        var reference = org.xar.ck3.control.contracts.ExactRef.fromJson(delta.get("original_driver_ref"));
        StrictJson.require(reference.sha256().equals(StrictJson.text(details.get("driver_snapshot").get("before_sha256"))),
                "original committed CAS Driver reference differs from its actual before digest");
        DriverStateSnapshot.Complete actualCasBefore = DriverStateSnapshot.decodeComplete(bound.loadFullMaterial(reference).bytes());
        if (!LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name().equals(StrictJson.text(details.get("phase"))))
            return actualCasBefore;
        // Finalization already published the successor. Its metadata-only CAS before Driver is
        // not the old subject against which the original parent and M7 branch must be checked.
        var causal = org.xar.ck3.control.contracts.ExactRef.fromJson(delta.get("causal_original_driver_ref"));
        StrictJson.require(causal.equals(parent.command().lifecycleBefore().evidence().originalDriver()),
                "finalized succession causal predecessor is not the exact original parent's Driver");
        var adopted = org.xar.ck3.control.contracts.ExactRef.fromJson(delta.get("adopted_driver_ref"));
        StrictJson.require(reference.sha256().equals(adopted.sha256())
                && reference.sha256().equals(StrictJson.text(details.get("driver_snapshot").get("after_sha256"))),
                "pending finalization must preserve its actually published full CAS Driver");
        return DriverStateSnapshot.decodeComplete(bound.loadFullMaterial(causal).bytes());
    }

    private static org.xar.ck3.control.contracts.ExactRef predecessorReference(LifecyclePublication publication) {
        var details = publication.detailsObject();
        String role = LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name().equals(StrictJson.text(details.get("phase")))
                ? "causal_original_driver_ref" : "original_driver_ref";
        return org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("delta").get(role));
    }

    private DriverSnapshotFacts.Known requirePublished(DriverStateAssembler.Frozen frozen,
            SessionIdentity owner, SemanticEvidence semantic, ActionPorts.OutcomeArchive boundArchive) {
        StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,
                "complete actual episode Driver publication is required");
        DriverSnapshotFacts.Known known = (DriverSnapshotFacts.Known) frozen.state();
        StrictJson.require(known.stamp().game().equals(owner.game())
                && known.stamp().episodeRunId().equals(semantic.frame().frame().episodeRunId())
                && known.driver().session().actorId().equals(semantic.frame().frame().identity().player())
                && Arrays.equals(boundArchive.loadFullMaterial(semantic.originalDriver()).bytes(), known.driver().encode()),
                "fresh episode SEM does not bind the full actually published Driver");
        var facts = known.observation().orElseThrow(
                () -> new IllegalArgumentException("actual fresh episode Driver observation facts absent"));
        StrictJson.require(facts.transport().machineId().equals(owner.machineId())
                && facts.transport().game().equals(owner.game()) && facts.transport().sessionId().equals(owner.sessionId())
                && facts.snapshotId().equals(semantic.frame().frame().snapshotId())
                && facts.nativeRevision().equals(semantic.frame().frame().identity().nativeRevision())
                && facts.publicRevision().equals(semantic.frame().frame().revision())
                && facts.observationVersion() == semantic.frame().observationVersion(),
                "fresh episode SEM crossed actual transport or public/native observation facts");
        return known;
    }

    private void requireCanonical(org.xar.ck3.control.continuity.ContinuityState state, ActionReceipt parent,
            SessionIdentity before, SessionIdentity after, ActionPorts.OutcomeArchive boundArchive) {
        List<ActionReceipt> receipts = ContinuityActionJournal.receipts(state, boundArchive);
        StrictJson.require(receipts.stream().anyMatch(parent::equals),
                "episode parent is not the actual canonical original receipt");
        StrictJson.require(receipts.stream().noneMatch(receipt -> !receipt.settled()
                && !receipt.command().actionId().equals(parent.command().actionId())
                && (ownedBy(receipt, before) || ownedBy(receipt, after))),
                "another original action remains pending or UNKNOWN; changing episode cannot clear it");
    }

    private void requireCanonicalCurrent(org.xar.ck3.control.continuity.ContinuityState state,ActionReceipt parent,
            SessionIdentity owner,ActionPorts.OutcomeArchive boundArchive,CurrentRole role) {
        if(role==CurrentRole.ORIGINAL_ADMISSION) {
            requireCanonical(state,parent,owner,owner,boundArchive);return;
        }
        // A transport can change session identity repeatedly within the one physical Game.
        // Unknown actions from any retained session remain unresolved under that same authority.
        List<ActionReceipt> receipts=ContinuityActionJournal.receipts(state,boundArchive);
        StrictJson.require(receipts.stream().anyMatch(parent::equals),
                "transported episode parent is not the actual canonical original receipt");
        StrictJson.require(receipts.stream().noneMatch(receipt->!receipt.settled()
                &&!receipt.command().actionId().equals(parent.command().actionId())
                &&receipt.command().origin().machineId().equals(owner.machineId())
                &&receipt.command().origin().game().equals(owner.game())),
                "transported current cannot clear another same-Game pending or UNKNOWN original action");
    }

    private static boolean ownedBy(ActionReceipt receipt, SessionIdentity owner) {
        return receipt.command().origin().machineId().equals(owner.machineId())
                && receipt.command().origin().game().equals(owner.game())
                && receipt.command().sessionId().equals(owner.sessionId());
    }
    private static void requireSemantic(SemanticEvidence semantic, OrdinaryCycleTransitions.VerifiedSemantic verified) {
        StrictJson.require(verified.frame().equals(semantic.frame()) && verified.observedAt().equals(semantic.observedAt()),
                "actual Root original SEM verification returned a different episode frame");
    }
    @FunctionalInterface private interface IoWork<T> { T run(ActionPorts.OutcomeArchive boundArchive) throws IOException; }
    private <T> T inArchive(ContinuityStorePort.Session borrowed, IoWork<T> work) throws IOException {
        try { return archive.inSession(borrowed, bound -> {
            try { return work.run(bound); } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }

    /** Opaque same-pair input for new-window cycle and callback consumers. It cannot mint a SAVE or cycle. */
    public static final class NextBaselineBinding {
        private final LifecycleEpisodeInputs issuer;
        private final Binding original;
        private final FirstCheckpointVerifier firstSaves;
        private final VerifiedFirstCheckpoint first;
        private final EpisodeWindow.CommittedBaseline baseline;
        private final DriverSnapshotFacts.Stamp driverStamp;
        private final DriverStateSnapshot.Complete driver;
        private final SemanticEvidence semantic;
        private final String semanticDigest, headDigest;
        private NextBaselineBinding(LifecycleEpisodeInputs issuer, Binding original, FirstCheckpointVerifier firstSaves,
                VerifiedFirstCheckpoint first, EpisodeWindow.CommittedBaseline baseline, DriverSnapshotFacts.Stamp driverStamp,
                DriverStateSnapshot.Complete driver, SemanticEvidence semantic, String semanticDigest, String headDigest) {
            this.issuer = issuer; this.original = original; this.firstSaves = firstSaves; this.first = first;
            this.baseline = baseline; this.driverStamp = driverStamp; this.driver = driver;
            this.semantic = semantic; this.semanticDigest = semanticDigest; this.headDigest = headDigest;
        }
        public void requireCurrent(ContinuityStorePort.Session borrowed) throws IOException { issuer.requireCurrentBaseline(borrowed, this); }
        public SessionIdentity beforeOwner() { return original.beforeOwner; }
        public SessionIdentity afterOwner() { return original.afterOwner; }
        public ActionReceipt parent() { return original.parent; }
        public LifecycleTransitionProof.NextEpisode proof() { return (LifecycleTransitionProof.NextEpisode) original.proof; }
        public DriverStateSnapshot.Complete predecessorDriver() { return original.predecessorDriver; }
        public DriverStateSnapshot.Complete driver() { return driver; }
        public DriverSnapshotFacts.Stamp driverStamp() { return driverStamp; }
        public SemanticEvidence semantic() { return semantic; }
        public VerifiedFirstCheckpoint firstCheckpoint() { return first; }
        public EpisodeWindow.CommittedBaseline baseline() { return baseline; }
        public String writerHeadDigest() { return headDigest; }
        public String semanticDigest() { return semanticDigest; }
        public long savedDayCredit() { return 0; }
        public long completedCycleCredit() { return 0; }
    }

    /** Opaque current qualification for a previously admitted branch; no Base, rebind or action authority. */
    public static final class CurrentAdoptionBinding {
        private final LifecycleEpisodeInputs issuer;
        private final ContinuityBatchJournal.HistoricalEpisodeAdoption historical;
        private final LifecycleHistoricalPublication.Recorded recorded;
        private final DriverSnapshotFacts.Stamp driverStamp;
        private final DriverStateSnapshot.Complete driver;
        private final SemanticEvidence semantic;
        private final String semanticDigest, headDigest;
        private final long headSequence;
        private final CurrentRole role;
        private CurrentAdoptionBinding(LifecycleEpisodeInputs issuer,
                ContinuityBatchJournal.HistoricalEpisodeAdoption historical, LifecycleHistoricalPublication.Recorded recorded,
                DriverSnapshotFacts.Stamp driverStamp, DriverStateSnapshot.Complete driver, SemanticEvidence semantic,
                String semanticDigest, long headSequence, String headDigest,CurrentRole role) {
            this.issuer = issuer; this.historical = historical; this.recorded = recorded;
            this.driverStamp = driverStamp; this.driver = driver; this.semantic = semantic;
            this.semanticDigest = semanticDigest; this.headSequence = headSequence; this.headDigest = headDigest;
            this.role=Objects.requireNonNull(role);
        }
        public void requireCurrent(ContinuityStorePort.Session borrowed) throws IOException { issuer.requireCurrentAdoption(borrowed, this); }
        public ContinuityBatchJournal.HistoricalEpisodeAdoption historical() { return historical; }
        public LifecycleHistoricalPublication.Recorded recorded() { return recorded; }
        public SessionIdentity owner() { return historical.owner(); }
        public ActionReceipt parent() { return recorded.parent(); }
        public DriverSnapshotFacts.Stamp driverStamp() { return driverStamp; }
        public DriverStateSnapshot.Complete driver() { return driver; }
        public SemanticEvidence semantic() { return semantic; }
        public String semanticDigest() { return semanticDigest; }
        public String writerHeadDigest() { return headDigest; }
        public long writerHeadSequence() { return headSequence; }
        public long savedDayCredit() { return 0; }
        public long completedCycleCredit() { return 0; }
    }

    /** Private input custody only. The cycle authority, action owner and original writer remain unique. */
    public static final class Binding {
        private final LifecycleEpisodeInputs issuer;
        private final SessionIdentity beforeOwner, afterOwner;
        private final ActionReceipt parent;
        private final LifecycleTransitionProof proof;
        private final LifecyclePublication publication;
        private final org.xar.ck3.control.contracts.ExactRef predecessorDriverReference;
        private final DriverSnapshotFacts.Stamp driverStamp;
        private final DriverStateSnapshot.Complete predecessorDriver, driver;
        private final SemanticEvidence semantic;
        private final String semanticDigest, headDigest;
        private final long headSequence;
        private Binding(LifecycleEpisodeInputs issuer, SessionIdentity beforeOwner, SessionIdentity afterOwner,
                ActionReceipt parent, LifecycleTransitionProof proof, LifecyclePublication publication,
                DriverSnapshotFacts.Stamp stamp, DriverStateSnapshot.Complete predecessorDriver, DriverStateSnapshot.Complete driver, SemanticEvidence semantic,
                String semanticDigest, long headSequence, String headDigest) {
            this.issuer = issuer; this.beforeOwner = beforeOwner; this.afterOwner = afterOwner; this.parent = parent;
            this.proof = proof; this.publication = publication; driverStamp = stamp; this.driver = driver;
            this.predecessorDriverReference = predecessorReference(publication);
            this.predecessorDriver = predecessorDriver;
            this.semantic = semantic; this.semanticDigest = semanticDigest; this.headSequence = headSequence; this.headDigest = headDigest;
        }
        public SessionIdentity beforeOwner() { return beforeOwner; }
        public SessionIdentity afterOwner() { return afterOwner; }
        public ActionReceipt parent() { return parent; }
        public LifecycleTransitionProof proof() { return proof; }
        public LifecyclePublication publication() { return publication; }
        /** Warm-only compatibility; a recorded event never supplies a fabricated Prepared. */
        public LifecycleCommit commit() { return publication.warmCommit().orElseThrow(
                () -> new IllegalStateException("recorded cold publication has no warm Prepared")); }
        public DriverSnapshotFacts.Stamp driverStamp() { return driverStamp; }
        public DriverStateSnapshot.Complete driver() { return driver; }
        public DriverStateSnapshot.Complete predecessorDriver() { return predecessorDriver; }
        public org.xar.ck3.control.contracts.ExactRef predecessorDriverReference() { return predecessorDriverReference; }
        public SemanticEvidence semantic() { return semantic; }
        public String commitDigest() { return publication.eventIdentity(); }
        public String semanticDigest() { return semanticDigest; }
        public String writerHeadDigest() { return headDigest; }
        public long writerHeadSequence() { return headSequence; }
        public long savedDayCredit() { return 0; }
        public long completedCycleCredit() { return 0; }
    }
}
