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
        current.requireActiveGame();
        StrictJson.require(current.game().machineId().equals(owner.machineId())
                && current.game().generation().equals(owner.game()) && current.game().sessionId().equals(owner.sessionId())
                && verified.session().equals(owner) && material.session().equals(owner)
                && verified.pair().equals(material.pair()) && verified.proof().equals(material.proof())
                && verified.originalHeadDigest().equals(material.originalHeadDigest())
                && verified.originalHeadDigest().equals(borrowed.head().digest()),
                "M7 checkpoint callback crossed its actual current Game, original private pair or source material");
        material.requirePhysical(borrowed);
        historical.capture(borrowed, verified, material.witness());
        current.requireActiveGame();
        StrictJson.require(borrowed.head().digest().equals(verified.originalHeadDigest()), "M7 input capture must not change the actual SAVE writer head");
    }

    /** Replays actual original SAVE/material/source evidence under the sole writer. Call outside a held writer. */
    public M7CheckpointInputs.Saved requireSaved(CheckpointPair pair, FileWitness originalMaterial) throws IOException {
        Objects.requireNonNull(pair); Objects.requireNonNull(originalMaterial);
        // A memory hit cannot replace retained-original FileID or canonical ancestry verification.
        M7CheckpointInputs.Saved recovered = historical.recover(pair, originalMaterial);
        return recovered;
    }
}
