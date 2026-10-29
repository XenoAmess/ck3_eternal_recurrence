package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier.VerifiedCheckpoint;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore.SavedMaterial;
import org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Same global checkpoint callback, resolving the actual physical runtime on every SAVE. No Game is captured. */
public final class RootM7CheckpointCapture implements RootCheckpointVerifier.SavedCapture {
    @FunctionalInterface public interface RuntimeAuthority {
        RootRuntimeContext require(SessionIdentity actualOwner) throws IOException;
    }
    private final M7CheckpointInputs inputs;
    private final RuntimeAuthority runtimes;
    private final RootM7HistoricalCheckpointInputs historical;

    public RootM7CheckpointCapture(M7CheckpointInputs sameCheckpointInputs, RuntimeAuthority actualRuntimes,
            RootM7HistoricalCheckpointInputs actualHistoricalInputs) {
        inputs = Objects.requireNonNull(sameCheckpointInputs); runtimes = Objects.requireNonNull(actualRuntimes);
        historical = Objects.requireNonNull(actualHistoricalInputs);
    }

    @Override public void capture(ContinuityStorePort.Session borrowed, SessionIdentity owner,
            VerifiedCheckpoint verified, SavedMaterial material) throws IOException {
        Objects.requireNonNull(owner); Objects.requireNonNull(verified); Objects.requireNonNull(material);
        RootRuntimeContext current = Objects.requireNonNull(runtimes.require(owner));
        current.writer().requireSession(borrowed);
        StrictJson.require(current.game().machineId().equals(owner.machineId())
                && current.game().generation().equals(owner.game()) && current.game().sessionId().equals(owner.sessionId())
                && verified.session().equals(owner) && material.session().equals(owner)
                && verified.pair().equals(material.pair()) && verified.proof().equals(material.proof())
                && verified.digest().equals(material.checkpointDigest()),
                "M7 checkpoint callback crossed its actual current Game, original private pair or source material");
        String head = borrowed.head().digest();
        Instant deadline = current.adopted().authority().withFrozenFacts(borrowed, frozen -> {
            var candidates = frozen.actions().actions().stream()
                    .filter(receipt -> receipt.command().actionId().equals(verified.pair().saveActionId())).toList();
            StrictJson.require(candidates.size() == 1 && frozen.actions().headSha256().equals(head),
                    "unique actual canonical SAVE parent at the original writer head is required");
            ActionReceipt actual = candidates.getFirst();
            StrictJson.require(actual.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                    && actual.command().origin() instanceof CommandOrigin.Gameplay
                    && actual.command().operation().value().equals("save-checkpoint")
                    && actual.command().origin().machineId().equals(owner.machineId())
                    && actual.command().origin().game().equals(owner.game())
                    && actual.command().sessionId().equals(owner.sessionId()),
                    "M7 source capture requires the actual confirmed same-owner SAVE operation");
            Instant action = actual.command().deadline();
            Instant reviewed = current.game().launchPlan().sources().review().expiresAt();
            return action.isBefore(reviewed) ? action : reviewed;
        });
        current.requireCurrent(deadline);
        var diagnostics = current.transport().diagnostics();
        var transport = diagnostics.session().orElseThrow(() -> new IOException("actual current SAVE transport unavailable"));
        var qualification = current.sources().verifyPhysicalOrigin(borrowed, transport, current.source(),
                verified.proof().semantic().originalNativePacket(), diagnostics, deadline);
        Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata = current.sources().optionalMetadata(borrowed, qualification);
        inputs.saved(borrowed, verified, material.witness(), current.source(),
                metadata.map(m -> m.ownerSourceEpoch()), metadata.map(m -> m.gameExecutable()), Optional.empty());
        qualification.assertCurrent(borrowed);
        if (metadata.isPresent()) metadata.orElseThrow().requireCurrent(borrowed);
        StrictJson.require(head.equals(borrowed.head().digest()), "M7 input capture must not change the actual SAVE writer head");
    }

    /** Replays actual original SAVE/material/source evidence under the sole writer. Call outside a held writer. */
    public M7CheckpointInputs.Saved requireSaved(CheckpointPair pair, FileWitness originalMaterial) throws IOException {
        Objects.requireNonNull(pair); Objects.requireNonNull(originalMaterial);
        // A memory hit cannot replace retained-original FileID or canonical ancestry verification.
        M7CheckpointInputs.Saved recovered = historical.recover(pair, originalMaterial);
        return recovered;
    }
}
