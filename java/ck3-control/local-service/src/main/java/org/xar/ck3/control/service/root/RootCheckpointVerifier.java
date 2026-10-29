package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;

/** The actual SAVE verifier captures durable material through the one cycle-qualified source store. */
public final class RootCheckpointVerifier implements OrdinaryCycleTransitions.CheckpointVerifier {
    @FunctionalInterface public interface SavedCapture {
        /** Capture from the original verified SAVE and same-session physical source; no ledger mutation or new Game action. */
        void capture(ContinuityStorePort.Session borrowed, SessionIdentity actualOwner,
                CheckpointCommitVerifier.VerifiedCheckpoint verified, SavedAttachmentSourceStore.SavedMaterial material) throws IOException;
    }
    @FunctionalInterface public interface SavedCaptureFactory {
        /** Called after the genuine paired verifier/cycle/source store exist; neither a second verifier nor a synthetic store can qualify its private token. */
        SavedCapture create(CheckpointCommitVerifier actualPairs,DriverCheckpointStore actualDrivers,
                SavedAttachmentSourceStore actualSources)throws IOException;
    }
    private final ContinuityWriter writer;
    private final CheckpointCommitVerifier verifier;
    private volatile SavedCapture capture;
    private volatile SavedAttachmentSourceStore sources;
    public RootCheckpointVerifier(ContinuityWriter writer, CheckpointCommitVerifier verifier) {
        this.writer = Objects.requireNonNull(writer); this.verifier = Objects.requireNonNull(verifier);
    }
    /** Cycle -> checkpoint -> store -> cycle is closed before sealing the writer router. */
    public synchronized void bind(SavedAttachmentSourceStore actual) {
        if (sources != null) throw new IllegalStateException("saved source store already bound"); sources = Objects.requireNonNull(actual);
    }
    public synchronized void bindCapture(SavedCapture actual) {
        if(capture!=null)throw new IllegalStateException("actual saved input capture already bound");capture=Objects.requireNonNull(actual);
    }
    public boolean isBound() { return sources != null&&capture!=null; }
    public void requireOwner(ContinuityWriter actual)throws IOException {
        if(writer!=Objects.requireNonNull(actual)||!isBound())throw new IOException("checkpoint verifier is not the actual bound producer of this sole writer");
    }
    @Override public String verify(ContinuityStorePort.Session borrowed, SessionIdentity identity, CheckpointPair pair,
            CompletedCycleProof proof) throws IOException {
        writer.requireSession(borrowed); SavedAttachmentSourceStore store = sources;SavedCapture actual=capture;
        if (store == null||actual==null) throw new IOException("actual cycle-qualified saved source store/input producer is not bound");
        CheckpointCommitVerifier.VerifiedCheckpoint verified = verifier.verifyCheckpoint(borrowed, identity, pair, proof);
        SavedAttachmentSourceStore.SavedMaterial material = store.capture(verified);
        String originalHead = borrowed.head().digest(); actual.capture(borrowed, identity, verified, material);
        writer.requireSession(borrowed);
        if (!originalHead.equals(borrowed.head().digest())) throw new IOException("SAVE capture changed the original canonical writer during read-only verification");
        return verified.digest();
    }
}
