package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.checkpoint.CheckpointCombinedBinding210Support.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

final class CheckpointCombinedBinding210Test {
    @TempDir Path temporary;
    static final class Hook implements CheckpointCommitVerifier.SaveReceiptVerifier {
        Fixture actual;int calls;boolean changeHead;
        @Override public String verify(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,CompletedCycleProof proof){throw new AssertionError("opt-in must not fall back");}
        @Override public String verifyRetained(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,CompletedCycleProof proof){throw new AssertionError("opt-in must not fall back retained");}
        @Override public DriverStateSnapshot.Complete retainedDriver(ContinuityStorePort.Session same,CheckpointPair pair){throw new AssertionError("combined material must not reacquire archived Driver");}
        @Override public Optional<CheckpointCommitVerifier.SaveWithDriver> verifyWithDriver(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,CompletedCycleProof proof,boolean retained)throws IOException {
            calls++;if(changeHead)actual.same().changeHead();
            return Optional.of(new CheckpointCommitVerifier.SaveWithDriver(SAVE_DIGEST,actual.drivers().readArchivedSnapshot(pair,actual.archivedDriver())));
        }
    }
    Fixture ready(String name,Hook hook)throws Exception {Fixture f=fixture(temporary.resolve(name),hook);hook.actual=f;return f;}
    CheckpointCommitVerifier.VerifiedCheckpoint checked(Fixture f)throws IOException{return f.verifier().verifyCheckpoint(f.same(),f.owner(),f.pair(),f.proof());}
    @Test void physicalCompatibilityOnly() throws Exception { Fixture f = fixture(temporary.resolve("compat"), (same, owner, pair, proof) -> SAVE_DIGEST); var issued = checked(f); assertNotNull(issued); assertThrows(IOException.class, () -> f.store().capture(issued)); }
    @Test void explicitLoadOriginalAndRetained() throws Exception { Hook hook = new Hook(); Fixture f = ready("loads", hook); var material = f.store().capture(checked(f)); int before = hook.calls; var original = f.store().loadOriginal(f.same(), material.witness(), material.pair()); assertEquals(before+1,hook.calls); var retained = f.store().loadRetainedOriginal(f.same(), material.witness(), material.pair()); assertEquals(before + 2, hook.calls); assertArrayEquals(material.savedDriver().encode(), original.savedDriver().encode()); assertArrayEquals(material.savedDriver().encode(), retained.savedDriver().encode()); }
    @Test void saveFileReplacement() throws Exception { Hook hook = new Hook(); Fixture f = ready("save-replace", hook); var material = f.store().capture(checked(f)); Path save = Path.of(f.pair().save().reference().path()); byte[] bytes = Files.readAllBytes(save); Files.move(save, save.resolveSibling("moved.ck3")); Files.write(save, bytes); var witness = f.files().observe(save).orElseThrow(); assertEquals(f.pair().save().reference().path(), witness.reference().path()); assertEquals(f.pair().save().reference(),witness.reference()); assertNotEquals(f.pair().save().identity().fileId(),witness.identity().fileId()); assertThrows(IOException.class, () -> f.store().loadOriginal(f.same(), material.witness(), material.pair())); assertNotNull(f.store().loadRetainedOriginal(f.same(), material.witness(), material.pair())); }
    @Test void materialWitnessReplacement() throws Exception { Hook hook = new Hook(); Fixture f = ready("material-replace", hook); var material = f.store().capture(checked(f)); Path path = Path.of(material.witness().reference().path()); byte[] bytes = Files.readAllBytes(path); Files.move(path, path.resolveSibling("moved.json")); Files.write(path, bytes); var witness = f.files().observe(path).orElseThrow(); assertEquals(material.witness().reference(),witness.reference()); assertNotEquals(material.witness().identity().fileId(),witness.identity().fileId()); assertThrows(IOException.class, () -> f.store().loadOriginal(f.same(), material.witness(), material.pair())); assertThrows(IOException.class, () -> f.store().loadRetainedOriginal(f.same(), material.witness(), material.pair())); }
    @Test void headChangeDuringVerification() throws Exception { Hook hook = new Hook(); hook.changeHead = true; Fixture f = ready("head-change", hook); var ex = assertThrows(Exception.class, () -> checked(f)); assertTrue(ex.getMessage().contains("writer head")); assertEquals(1, hook.calls); }
    @Test void foreignScopeRejected() throws Exception { Hook hook = new Hook(); Fixture f = ready("foreign", hook); var foreign = new Scope(temporary.resolve("foreign.lock"), f.same().head().state()); assertThrows(IOException.class, () -> f.verifier().verifyCheckpoint(foreign, f.owner(), f.pair(), f.proof())); assertEquals(0, hook.calls); }
    @Test void materialDriverDigests() throws Exception { Hook hook = new Hook(); Fixture f = ready("driver-digests", hook); var issued = checked(f); assertNotNull(f.verifier().verifyMaterialDriver(f.same(), f.owner(), f.pair(), f.proof(), issued.originalHeadDigest(), issued.digest(), f.cycleAuthority(), false)); assertThrows(IOException.class, () -> f.verifier().verifyMaterialDriver(f.same(), f.owner(), f.pair(), f.proof(), issued.originalHeadDigest(), "c".repeat(64), f.cycleAuthority(), false)); assertThrows(IOException.class, () -> f.verifier().verifyMaterialDriver(f.same(), f.owner(), f.pair(), f.proof(), issued.originalHeadDigest(), issued.digest(), "c".repeat(64), false)); }
    @Test void semanticDriverTamper() throws Exception { Hook hook = new Hook(); Fixture f = ready("tamper", hook); var issued = checked(f); int before = hook.calls; Files.writeString(Path.of(f.proof().semantic().originalDriver().path()), "tampered"); assertThrows(Exception.class, () -> checked(f)); assertEquals(before, hook.calls); }
}
