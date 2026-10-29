package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit archived first-SAVE branch. Later ordinary SAVE or NEXT cannot turn it into a live first-SAVE permit. */
public final class RootM7HistoricalFirstCheckpointInputs {
    private final ContinuityStorePort writer;
    private final SessionAuthority sessions;
    private final ActionPorts.OutcomeArchive archive;
    private final SavedFirstCheckpointMaterialStore sources;
    private final M7CheckpointInputs inputs;

    public RootM7HistoricalFirstCheckpointInputs(ContinuityStorePort soleWriter, SessionAuthority actualSessions,
            ActionPorts.OutcomeArchive originalArchive, SavedFirstCheckpointMaterialStore actualFirstSources,
            M7CheckpointInputs sameInputs) {
        writer = Objects.requireNonNull(soleWriter); sessions = Objects.requireNonNull(actualSessions);
        archive = Objects.requireNonNull(originalArchive); sources = Objects.requireNonNull(actualFirstSources);
        inputs = Objects.requireNonNull(sameInputs);
    }

    /** Caller supplies the original material FileWitness retained in the typed cold proof. This acquires the writer once. */
    public M7CheckpointInputs.Saved recover(CheckpointPair pair, FileWitness originalMaterial) throws IOException {
        Objects.requireNonNull(pair); Objects.requireNonNull(originalMaterial);
        try { return writer.locked(borrowed -> {
            sessions.require(borrowed); String head = borrowed.head().digest();
            var material = sources.loadRetainedOriginal(borrowed, originalMaterial, pair);
            var first = material.checkpoint(); var save = first.canonicalSave(); var command = save.command();
            StrictJson.require(save.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                    && command.operation().value().equals("save-checkpoint") && command.origin() instanceof CommandOrigin.Gameplay
                    && command.origin().machineId().equals(first.session().machineId())
                    && command.origin().game().equals(first.session().game()) && command.sessionId().equals(first.session().sessionId())
                    && command.actionId().equals(pair.saveActionId()) && save.sequence() <= first.originalHead().sequence()
                    && save.state() instanceof ActionState.Settled,
                    "retained first SAVE requires its original confirmed canonical same-owner primitive parent");
            var guard = ((ActionState.Settled) save.state()).attempt().guard();
            StrictJson.require(guard.source().equals(command.source()) && guard.operation().equals(command.operation())
                    && guard.sessionId().equals(command.sessionId()) && guard.origin().equals(command.origin()),
                    "retained first SAVE guard crossed its original source or physical owner");
            var original = archive.inSession(borrowed, bound -> RootM7HistoricalCheckpointInputs.readOriginalSource(
                    borrowed, guard, bound, save.sequence(), first.originalHead().sequence()));
            var recovered = inputs.recoveredFirst(borrowed, sources, pair, originalMaterial, command.source(),
                    original.metadata().map(m -> m.epoch()), original.metadata().map(m -> m.executable()), Optional.empty());
            sources.requireRetained(borrowed, material);
            original.verifyPins(borrowed);
            sessions.require(borrowed);
            StrictJson.require(head.equals(borrowed.head().digest()), "retained first SAVE projection changed current writer head");
            return recovered;
        }); } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }
}
