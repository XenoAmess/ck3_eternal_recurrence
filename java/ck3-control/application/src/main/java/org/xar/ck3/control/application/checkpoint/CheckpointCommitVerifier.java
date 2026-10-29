package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real original-lease SAVE verification. Its private result can seed immutable restore materials. */
public final class CheckpointCommitVerifier {
    @FunctionalInterface public interface WriterLeaseVerifier {
        /** Root installs the exact ContinuityWriter instance's requireSession method. */
        void require(ContinuityStorePort.Session borrowed) throws IOException;
    }
    @FunctionalInterface public interface SemanticVerifier {
        /** The same archived native/semantic/full-Driver verifier used by Root readiness. */
        String verify(ContinuityStorePort.Session borrowed, SessionIdentity source, SemanticEvidence actual) throws IOException;
    }
    @FunctionalInterface public interface SaveReceiptVerifier {
        /** Real canonical SAVE, original request/ACK and independently observed pair; ACK alone is insufficient. */
        String verify(ContinuityStorePort.Session borrowed, SessionIdentity source, CheckpointPair pair, CompletedCycleProof proof) throws IOException;
        default String verifyRetained(ContinuityStorePort.Session borrowed,SessionIdentity source,CheckpointPair pair,CompletedCycleProof proof)throws IOException {
            throw new IOException("historical canonical SAVE original verifier is unavailable");
        }
        default DriverStateSnapshot.Complete retainedDriver(ContinuityStorePort.Session borrowed,CheckpointPair pair)throws IOException {
            throw new IOException("immutable complete saved Driver original is unavailable");
        }
    }
    public static final class VerifiedCheckpoint {
        private final CheckpointCommitVerifier issuer;
        private final SessionIdentity session;
        private final CheckpointPair pair;
        private final CompletedCycleProof proof;
        private final ContinuityState originalHead;
        private final String originalHeadDigest, digest;
        private VerifiedCheckpoint(CheckpointCommitVerifier issuer, SessionIdentity session, CheckpointPair pair,
                CompletedCycleProof proof, ContinuityState originalHead, String originalHeadDigest, String digest) {
            this.issuer=issuer; this.session=session; this.pair=pair; this.proof=proof;
            this.originalHead=originalHead; this.originalHeadDigest=originalHeadDigest; this.digest=digest;
        }
        public SessionIdentity session() { return session; }
        public CheckpointPair pair() { return pair; }
        public CompletedCycleProof proof() { return proof; }
        public String originalHeadDigest() { return originalHeadDigest; }
        public ContinuityState originalHead() { return originalHead; }
        public String digest() { return digest; }
    }
    private final CheckpointFiles files;
    private final DriverCheckpointStore drivers;
    private final SemanticVerifier semantics;
    private final WriterLeaseVerifier leases;
    private final SaveReceiptVerifier saves;
    private final Path originalWriterLock;
    public CheckpointCommitVerifier(CheckpointFiles files, DriverCheckpointStore drivers, SemanticVerifier semantics,
            Path originalWriterLock, WriterLeaseVerifier leases, SaveReceiptVerifier saves) {
        this.files=Objects.requireNonNull(files); this.drivers=Objects.requireNonNull(drivers);
        this.semantics=Objects.requireNonNull(semantics); this.leases=Objects.requireNonNull(leases);
        this.originalWriterLock=Objects.requireNonNull(originalWriterLock); this.saves=Objects.requireNonNull(saves);
        StrictJson.require(originalWriterLock.isAbsolute(),"exact configured canonical writer lock required");
    }
    public String verify(ContinuityStorePort.Session borrowed, SessionIdentity session, CheckpointPair pair,
            CompletedCycleProof proof) throws IOException {
        return verifyCheckpoint(borrowed,session,pair,proof).digest();
    }
    public VerifiedCheckpoint verifyCheckpoint(ContinuityStorePort.Session borrowed, SessionIdentity session,
            CheckpointPair pair, CompletedCycleProof proof) throws IOException {
        requireLease(borrowed); var original=borrowed.head(); String head=original.digest();
        String binding=historicalDigest(borrowed,session,pair,proof,head);
        StrictJson.require(head.equals(borrowed.head().digest()),"original writer head changed during SAVE validation");
        requireLease(borrowed); return new VerifiedCheckpoint(this,session,pair,proof,original.state(),head,binding);
    }
    /** Revalidate the original archived proof under today's same writer lease; grants no new credit or live readiness. */
    public String verifyHistorical(ContinuityStorePort.Session borrowed, SessionIdentity sourceSession, CheckpointPair pair,
            CompletedCycleProof proof, String originalHeadDigest, String expectedDigest) throws IOException {
        WriterContracts.requireDigest(expectedDigest);
        String actual=historicalDigest(borrowed,sourceSession,pair,proof,originalHeadDigest);
        StrictJson.require(actual.equals(expectedDigest),"immutable original SAVE semantic binding changed"); return actual;
    }
    /** Historical original sources only; never the current physical reload qualification. */
    public String verifyRetainedOriginal(ContinuityStorePort.Session borrowed,SessionIdentity source,CheckpointPair pair,
            CompletedCycleProof proof,String originalHeadDigest,String expectedDigest)throws IOException {
        WriterContracts.requireDigest(expectedDigest);String actual=historicalDigest(borrowed,source,pair,proof,originalHeadDigest,true);
        StrictJson.require(actual.equals(expectedDigest),"retained original SAVE binding changed");return actual;
    }
    public void requireIssued(ContinuityStorePort.Session borrowed, VerifiedCheckpoint verified) throws IOException {
        Objects.requireNonNull(verified); requireLease(borrowed);
        StrictJson.require(verified.issuer==this && borrowed.head().digest().equals(verified.originalHeadDigest),
                "original verifier and original SAVE writer head required before material capture");
        verifyHistorical(borrowed,verified.session,verified.pair,verified.proof,verified.originalHeadDigest,verified.digest);
    }
    /** Package-owned saved-material producer calls only after the full retained binding was reverified. */
    DriverStateSnapshot.Complete retainedDriver(ContinuityStorePort.Session borrowed,CheckpointPair pair)throws IOException {
        requireLease(borrowed);return saves.retainedDriver(borrowed,pair);
    }
    private void requireLease(ContinuityStorePort.Session borrowed) throws IOException {
        Objects.requireNonNull(borrowed); leases.require(borrowed); borrowed.requireWriter(originalWriterLock);
    }
    private String historicalDigest(ContinuityStorePort.Session borrowed, SessionIdentity session, CheckpointPair pair,
            CompletedCycleProof proof, String originalHeadDigest) throws IOException {
        return historicalDigest(borrowed,session,pair,proof,originalHeadDigest,false);
    }
    private String historicalDigest(ContinuityStorePort.Session borrowed,SessionIdentity session,CheckpointPair pair,
            CompletedCycleProof proof,String originalHeadDigest,boolean retained)throws IOException {
        requireLease(borrowed); Objects.requireNonNull(session); Objects.requireNonNull(pair); Objects.requireNonNull(proof);
        WriterContracts.requireDigest(originalHeadDigest);
        var savedFrame=pair.frame(); var actualFrame=proof.semantic().frame();
        StrictJson.require(borrowed.head().state().machineId().equals(session.machineId())
                && session.machineId().equals(savedFrame.machineId()) && session.game().equals(savedFrame.game())
                && actualFrame.machineId().equals(savedFrame.machineId()) && actualFrame.game().equals(savedFrame.game())
                && actualFrame.frame().episodeRunId().equals(savedFrame.frame().episodeRunId())
                && actualFrame.frame().identity().player().equals(savedFrame.frame().identity().player())
                && actualFrame.frame().identity().dateRaw().equals(savedFrame.frame().identity().dateRaw())
                && savedFrame.frame().revision().compareTo(actualFrame.frame().revision())>=0
                && savedFrame.frame().identity().nativeRevision().compareTo(actualFrame.frame().identity().nativeRevision())>=0,
                "actual cycle semantic and physical SAVE must share machine/Game/episode/actor/date and monotonic actual SAVE revisions");
        for (ExactRef ref:proof.semantic().references()) readExact(ref);
        String semanticDigest=semantics.verify(borrowed,session,proof.semantic()); WriterContracts.requireDigest(semanticDigest);
        DriverStateSnapshot.Complete before=DriverStateSnapshot.decodeComplete(readExact(proof.semantic().originalDriver()));
        DriverStateSnapshot.Complete saved=retained?saves.retainedDriver(borrowed,pair):drivers.readVerifiedOriginal(pair,before.session());
        requireSaveProjection(before,saved,pair); if(!retained)drivers.verifyOriginal(pair,before.session());
        String saveDigest=retained?saves.verifyRetained(borrowed,session,pair,proof):saves.verify(borrowed,session,pair,proof); WriterContracts.requireDigest(saveDigest); requireLease(borrowed);
        ObjectNode binding=StrictJson.object(); binding.put("writer_head_sha256",originalHeadDigest);
        binding.put("session_id",session.sessionId()); binding.put("canonical_save_sha256",saveDigest); binding.put("semantic_verifier_sha256",semanticDigest);
        binding.put("cycle_state_sha256",proof.cycleStateDigest()); binding.put("completed_cycles",proof.completedCycles());
        binding.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
        var refs=binding.putArray("semantic_sources"); proof.semantic().references().forEach(ref->refs.add(ref.toJson()));
        return ContinuityJson.digest(binding);
    }
    private byte[] readExact(ExactRef ref) throws IOException {
        var actual=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("original checkpoint semantic source unavailable"));
        StrictJson.require(actual.reference().equals(ref),"original checkpoint semantic evidence changed");
        return files.read(actual,DriverCheckpointStore.MAX_DRIVER_BYTES);
    }
    static void requireSaveProjection(DriverStateSnapshot.Complete before, DriverStateSnapshot.Complete saved, CheckpointPair pair) {
        if (Arrays.equals(before.encode(),saved.encode())) return;
        StrictJson.require(before.session().equals(saved.session()) && saved.commandHistory().size()==before.commandHistory().size()+1,
                "SAVE may append exactly one row to the complete semantic Driver");
        for(int i=0;i<before.commandHistory().size();i++)
            StrictJson.require(Arrays.equals(before.commandHistory().get(i).originalRow().json(),saved.commandHistory().get(i).originalRow().json()),"SAVE changed prior history");
        StrictJson.require(saved.commandHistory().getLast().index()==pair.historyIndex(),"actual pair anchor is the appended SAVE row");
        StrictJson.require(same(before.managedRestoreTransaction(),saved.managedRestoreTransaction())
                &&same(before.successionExpectation(),saved.successionExpectation())&&same(before.successionLifecycle(),saved.successionLifecycle())
                &&same(before.campaignGoal(),saved.campaignGoal()),"SAVE changed unrelated full Driver state");
        StrictJson.require(saved.rollbackWarFailure() instanceof DriverStateSnapshot.NullValue
                &&saved.rollbackWarFailures() instanceof DriverStateSnapshot.Value value
                &&StrictJson.parse(value.json()).isArray()&&StrictJson.parse(value.json()).isEmpty(),"new SAVE clears only original rollback advisory scope");
    }
    private static boolean same(DriverStateSnapshot.Slot left, DriverStateSnapshot.Slot right) {
        if(left instanceof DriverStateSnapshot.Value first&&right instanceof DriverStateSnapshot.Value second)
            return StrictJson.parse(first.json()).equals(StrictJson.parse(second.json()));
        return left.getClass().equals(right.getClass());
    }
}
