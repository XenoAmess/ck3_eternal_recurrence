package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.StrictJson;

/** Restarts reconstruct old kernel facts only from the canonical SAVE, its original source role and real saved-material verifier. */
public final class RootM7HistoricalCheckpointInputs {
    record OriginalSource(Optional<RootM7HistoricalSource.Decoded> metadata, Optional<Pin> proof, Optional<Pin> manifest) {
        OriginalSource {
            Objects.requireNonNull(metadata); Objects.requireNonNull(proof); Objects.requireNonNull(manifest);
            StrictJson.require(metadata.isPresent() == proof.isPresent() && proof.isPresent() == manifest.isPresent(),
                    "historical source metadata and its original witness pins must be present together");
        }
        void verifyPins(ContinuityStorePort.Session borrowed) throws IOException {
            if (proof.isPresent()) {
                borrowed.verifyPin(proof.orElseThrow()); borrowed.verifyPin(manifest.orElseThrow());
            }
        }
    }
    private final ContinuityStorePort writer;
    private final SessionAuthority sessions;
    private final ActionJournal actions;
    private final ActionPorts.OutcomeArchive archive;
    private final SavedAttachmentSourceStore sources;
    private final M7CheckpointInputs inputs;

    public RootM7HistoricalCheckpointInputs(ContinuityStorePort soleWriter, SessionAuthority actualWriterAuthority,
            ActionJournal actualJournal, ActionPorts.OutcomeArchive originalArchive,
            SavedAttachmentSourceStore actualSources, M7CheckpointInputs sameInputs) {
        writer = Objects.requireNonNull(soleWriter); sessions = Objects.requireNonNull(actualWriterAuthority);
        actions = Objects.requireNonNull(actualJournal); archive = Objects.requireNonNull(originalArchive);
        sources = Objects.requireNonNull(actualSources); inputs = Objects.requireNonNull(sameInputs);
    }

    /** Captures current genuine private VerifiedCheckpoint under the already-held writer, joining it to the actual archived canonical SAVE guard/source. */
    public M7CheckpointInputs.Saved capture(ContinuityStorePort.Session borrowed, CheckpointCommitVerifier.VerifiedCheckpoint verified, FileWitness originalMaterial) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(verified); Objects.requireNonNull(originalMaterial);
        sessions.require(borrowed);
        String head = borrowed.head().digest();
        var material = sources.loadRetainedOriginal(borrowed, originalMaterial, verified.pair());
        StrictJson.require(material.pair().equals(verified.pair()) && material.session().equals(verified.session())
                && material.proof().equals(verified.proof()) && material.originalHeadDigest().equals(verified.originalHeadDigest())
                && material.witness().equals(originalMaterial),
                "private SAVE and retained original material differ in pair, owner, complete proof, head or witness");
        ActionReceipt save = actions.locked(borrowed, journal -> {
            var snapshot = journal.snapshot();
            StrictJson.require(snapshot.headSha256().equals(head), "historical SAVE must be read from the original current canonical writer");
            var matches = snapshot.actions().stream().filter(value -> value.command().actionId().equals(verified.pair().saveActionId())).toList();
            StrictJson.require(matches.size() == 1, "unique canonical original SAVE parent is unavailable");
            return matches.getFirst();
        });
        var command = save.command();
        StrictJson.require(save.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                && save.sequence() <= material.originalHeadSequence()
                && command.operation().value().equals("save-checkpoint") && command.origin() instanceof CommandOrigin.Gameplay
                && command.sessionId().equals(material.session().sessionId())
                && command.origin().machineId().equals(material.session().machineId())
                && command.origin().game().equals(material.session().game())
                && command.before().frame().episodeRunId().equals(verified.pair().frame().frame().episodeRunId())
                && command.before().frame().identity().player().equals(verified.pair().frame().frame().identity().player()),
                "historical source requires the actual confirmed original same-owner SAVE parent");
        GuardEvidence guard = switch (save.state()) {
            case ActionState.Settled settled -> settled.attempt().guard();
            case ActionState.CompositeSettled settled -> settled.execution().guard();
            default -> throw new IllegalArgumentException("confirmed SAVE lacks its original durable guard");
        };
        StrictJson.require(guard.origin() instanceof CommandOrigin.Gameplay
                && guard.source().equals(command.source()) && guard.operation().equals(command.operation())
                && guard.sessionId().equals(command.sessionId()) && guard.observed().machineId().equals(command.before().machineId())
                && guard.observed().game().equals(command.before().game())
                && guard.observed().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                && guard.observed().frame().identity().player().equals(command.before().frame().identity().player()),
                "canonical SAVE guard crossed its original operation, source or episode owner");
        OriginalSource original;
        try { original = archive.inSession(borrowed, bound -> readOriginalSource(borrowed, guard, bound, save.sequence(), material.originalHeadSequence())); }
        catch (UncheckedIOException failure) { throw failure.getCause(); }
        M7CheckpointInputs.Saved recovered = inputs.saved(borrowed, verified, originalMaterial, command.source(),
                original.metadata().map(m -> m.epoch()), original.metadata().map(m -> m.executable()), Optional.empty());
        var retained = sources.loadRetainedOriginal(borrowed, originalMaterial, verified.pair());
        StrictJson.require(material.witness().equals(retained.witness())
                && material.checkpointDigest().equals(retained.checkpointDigest()) && head.equals(borrowed.head().digest()),
                "historical source reconstruction changed the original saved material or writer head");
        original.verifyPins(borrowed);
        sessions.require(borrowed); return recovered;
    }

    /** Acquires the original writer. Invoke outside any already-held writer scope; no SAVE, query or restore is submitted. */
    public M7CheckpointInputs.Saved recover(CheckpointPair exactPair, FileWitness originalMaterial) throws IOException {
        Objects.requireNonNull(exactPair); Objects.requireNonNull(originalMaterial);
        try { return writer.locked(borrowed -> {
            sessions.require(borrowed);
            String head = borrowed.head().digest();
            var material = sources.loadRetainedOriginal(borrowed, originalMaterial, exactPair);
            ActionReceipt save = actions.locked(borrowed, journal -> {
                var snapshot = journal.snapshot();
                StrictJson.require(snapshot.headSha256().equals(head), "historical SAVE must be read from the original current canonical writer");
                var matches = snapshot.actions().stream().filter(value -> value.command().actionId().equals(exactPair.saveActionId())).toList();
                StrictJson.require(matches.size() == 1, "unique canonical original SAVE parent is unavailable");
                return matches.getFirst();
            });
            var command = save.command();
            StrictJson.require(save.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                    && save.sequence() <= material.originalHeadSequence()
                    && command.operation().value().equals("save-checkpoint") && command.origin() instanceof CommandOrigin.Gameplay
                    && command.sessionId().equals(material.session().sessionId())
                    && command.origin().machineId().equals(material.session().machineId())
                    && command.origin().game().equals(material.session().game())
                    && command.before().frame().episodeRunId().equals(exactPair.frame().frame().episodeRunId())
                    && command.before().frame().identity().player().equals(exactPair.frame().frame().identity().player()),
                    "historical source requires the actual confirmed original same-owner SAVE parent");
            GuardEvidence guard = switch (save.state()) {
                case ActionState.Settled settled -> settled.attempt().guard();
                case ActionState.CompositeSettled settled -> settled.execution().guard();
                default -> throw new IllegalArgumentException("confirmed SAVE lacks its original durable guard");
            };
            StrictJson.require(guard.origin() instanceof CommandOrigin.Gameplay
                    && guard.source().equals(command.source()) && guard.operation().equals(command.operation())
                    && guard.sessionId().equals(command.sessionId()) && guard.observed().machineId().equals(command.before().machineId())
                    && guard.observed().game().equals(command.before().game())
                    && guard.observed().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                    && guard.observed().frame().identity().player().equals(command.before().frame().identity().player()),
                    "canonical SAVE guard crossed its original operation, source or episode owner");
            OriginalSource original = archive.inSession(borrowed, bound -> readOriginalSource(borrowed, guard, bound, save.sequence(), material.originalHeadSequence()));
            M7CheckpointInputs.Saved recovered = inputs.recovered(borrowed, sources, exactPair, originalMaterial, command.source(),
                    original.metadata().map(m -> m.epoch()), original.metadata().map(m -> m.executable()), Optional.empty());
            var retained = sources.loadRetainedOriginal(borrowed, originalMaterial, exactPair);
            StrictJson.require(material.witness().equals(retained.witness())
                    && material.checkpointDigest().equals(retained.checkpointDigest()) && head.equals(borrowed.head().digest()),
                    "historical source reconstruction changed the original saved material or writer head");
            original.verifyPins(borrowed);
            sessions.require(borrowed); return recovered;
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }

    /** Shared ordinary/first-SAVE original source path. Both branches require the same guard history capability. */
    static OriginalSource readOriginalSource(ContinuityStorePort.Session borrowed, GuardEvidence guard,
            ActionPorts.OutcomeArchive bound, long saveSequence, long savedHeadSequence) {
        try {
            requireOriginalGuardHistory(borrowed, guard, bound, saveSequence, savedHeadSequence);
            var sourceProofOpt = RootGuardEvidence.sourceQualification(guard, bound);
            if (sourceProofOpt.isEmpty()) {
                return new OriginalSource(Optional.empty(), Optional.empty(), Optional.empty());
            }
            var sourceProof = sourceProofOpt.get();
            byte[] proofBytes = bound.loadMaterial(sourceProof).bytes();
            var manifest = RootM7HistoricalSource.manifest(sourceProof, proofBytes, guard);
            var decoded = RootM7HistoricalSource.decode(sourceProof, proofBytes, guard, bound.loadMaterial(manifest).bytes());
            var proofPin = borrowed.capturePin(sourceProof, 16 << 20);
            var manifestPin = borrowed.capturePin(manifest, 16 << 20);
            borrowed.verifyPin(proofPin); borrowed.verifyPin(manifestPin);
            return new OriginalSource(Optional.of(decoded), Optional.of(proofPin), Optional.of(manifestPin));
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }

    /** A retained source role is DATA until its original guard point is joined to this canonical writer. */
    static void requireOriginalGuardHistory(ContinuityStorePort.Session borrowed, GuardEvidence guard,
            ActionPorts.OutcomeArchive bound, long saveSequence, long savedHeadSequence) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(guard); Objects.requireNonNull(bound);
        StrictJson.safe(saveSequence, 1); StrictJson.safe(savedHeadSequence, 1);
        var point = RootGuardEvidence.writerPoint(guard, bound);
        StrictJson.require(point.sequence() < saveSequence && saveSequence <= savedHeadSequence,
                "historical SAVE source guard must precede the original canonical SAVE and saved head");
        RootGuardEvidence.requireHistory(guard, bound, borrowed);
    }
}
