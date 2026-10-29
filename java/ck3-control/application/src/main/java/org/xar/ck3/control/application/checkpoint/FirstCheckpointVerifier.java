package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** First physical SAVE after canonical BEGIN. It never creates a cycle or submits SAVE. */
public final class FirstCheckpointVerifier {
    public static final class VerifiedFirstCheckpoint {
        private final FirstCheckpointVerifier issuer;
        private final SessionIdentity session;
        private final CheckpointPair pair;
        private final SemanticEvidence semantic;
        private final EpisodeWindow.CommittedBegin begin;
        private final ContinuityState originalHead;
        private final String originalHeadDigest,digest;
        private final FirstSaveReceiptVerifier.Original original;
        private final DriverStateSnapshot.Complete originalDriver;
        private VerifiedFirstCheckpoint(FirstCheckpointVerifier issuer,SessionIdentity session,CheckpointPair pair,
                SemanticEvidence semantic,EpisodeWindow.CommittedBegin begin,ContinuityState head,String headDigest,
                String digest,FirstSaveReceiptVerifier.Original original,DriverStateSnapshot.Complete originalDriver) {
            this.issuer=issuer;this.session=session;this.pair=pair;this.semantic=semantic;this.begin=begin;
            this.originalHead=head;this.originalHeadDigest=headDigest;this.digest=digest;this.original=original;this.originalDriver=originalDriver;
        }
        public SessionIdentity session(){return session;}
        public CheckpointPair pair(){return pair;}
        /** Actual opening originals before SAVE, not a fabricated completed-cycle semantic. */
        public SemanticEvidence semantic(){return semantic;}
        public EpisodeWindow.CommittedBegin begin(){return begin;}
        public ContinuityState originalHead(){return originalHead;}
        public String originalHeadDigest(){return originalHeadDigest;}
        public long originalHeadSequence(){return originalHead.sequence();}
        public String digest(){return digest;}
        public ActionReceipt canonicalSave(){return original.receipt();}
        public ExactRef canonicalSaveReference(){return original.receiptReference();}
        public ExactRef pairReference(){return original.pairReference();}
        public DriverStateSnapshot.Complete originalDriver(){return originalDriver;}
        public DriverStateSnapshot.Complete savedDriver(){return original.savedDriver();}
        public EpisodeWindow.Baseline baseline(){return new EpisodeWindow.Baseline(begin,pair.saveActionId(),pairReference(),
                pairReference().sha256(),canonicalSaveReference(),digest,begin.begin().after());}
    }
    /** Archived ancestry only. This object cannot be used as a physical first-SAVE or new-Game permit. */
    public static final class RetainedFirstCheckpoint {
        private final FirstCheckpointVerifier issuer;
        private final SessionIdentity session;private final CheckpointPair pair;private final SemanticEvidence semantic;
        private final EpisodeWindow.CommittedBegin begin;private final ContinuityState originalHead;
        private final String originalHeadDigest,digest;
        private final FirstSaveReceiptVerifier.Original original;
        private RetainedFirstCheckpoint(FirstCheckpointVerifier issuer,SessionIdentity session,CheckpointPair pair,
                SemanticEvidence semantic,EpisodeWindow.CommittedBegin begin,ContinuityState head,String headDigest,
                String digest,FirstSaveReceiptVerifier.Original original){
            this.issuer=issuer;this.session=session;this.pair=pair;this.semantic=semantic;this.begin=begin;
            this.originalHead=head;this.originalHeadDigest=headDigest;this.digest=digest;this.original=original;
        }
        public SessionIdentity session(){return session;}
        public CheckpointPair pair(){return pair;}
        public SemanticEvidence semantic(){return semantic;}
        public EpisodeWindow.CommittedBegin begin(){return begin;}
        public ContinuityState originalHead(){return originalHead;}
        public String originalHeadDigest(){return originalHeadDigest;}
        public String digest(){return digest;}
        public ActionReceipt canonicalSave(){return original.receipt();}
        public DriverStateSnapshot.Complete savedDriver(){return original.savedDriver();}
        public ExactRef canonicalSaveReference(){return original.receiptReference();}
        public ExactRef pairReference(){return original.pairReference();}
    }
    private record Checked(String digest,FirstSaveReceiptVerifier.Original original,DriverStateSnapshot.Complete before){ }
    private final CheckpointFiles files;private final DriverCheckpointStore drivers;
    private final CheckpointCommitVerifier.SemanticVerifier semantics;
    private final CheckpointCommitVerifier.WriterLeaseVerifier leases;
    private final FirstSaveReceiptVerifier saves;private final Path writerLock;
    public FirstCheckpointVerifier(CheckpointFiles files,DriverCheckpointStore drivers,CheckpointCommitVerifier.SemanticVerifier semantics,
            Path writerLock,CheckpointCommitVerifier.WriterLeaseVerifier leases,FirstSaveReceiptVerifier saves){
        this.files=Objects.requireNonNull(files);this.drivers=Objects.requireNonNull(drivers);this.semantics=Objects.requireNonNull(semantics);
        this.writerLock=Objects.requireNonNull(writerLock);this.leases=Objects.requireNonNull(leases);this.saves=Objects.requireNonNull(saves);
        StrictJson.require(writerLock.isAbsolute(),"actual original writer lock required");
    }
    public VerifiedFirstCheckpoint verifyCheckpoint(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,
            SemanticEvidence opening,EpisodeWindow.CommittedBegin begin)throws IOException {
        requireLease(same);same.requireEpisodeWindowBegin(begin);var original=same.head();
        var window=EpisodeWindow.state(original.state()).orElseThrow();
        StrictJson.require(window.phase()==EpisodeWindow.Phase.AWAITING_FIRST_SAVE,"first SAVE may qualify only this still-awaiting BEGIN");
        var checked=check(same,owner,pair,opening,begin,original.state(),original.digest(),false);
        StrictJson.require(original.digest().equals(same.head().digest()),"first SAVE validation changed canonical head");
        return new VerifiedFirstCheckpoint(this,owner,pair,opening,begin,original.state(),original.digest(),checked.digest(),checked.original(),checked.before());
    }
    /** Same private issuer and exact physical pair; canonical BASELINE suffix is permitted, no new SAVE is dispatched. */
    public void requireIssued(ContinuityStorePort.Session same,VerifiedFirstCheckpoint proof)throws IOException {
        Objects.requireNonNull(proof);StrictJson.require(proof.issuer==this,"foreign first SAVE private proof");
        var actual=check(same,proof.session,proof.pair,proof.semantic,proof.begin,proof.originalHead,proof.originalHeadDigest,false);
        StrictJson.require(proof.digest.equals(actual.digest())&&proof.original.receipt().equals(actual.original().receipt())
                &&Arrays.equals(proof.savedDriver().encode(),actual.original().savedDriver().encode()),"private first SAVE original binding changed");
    }
    public RetainedFirstCheckpoint verifyRetainedOriginal(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,
            SemanticEvidence opening,EpisodeWindow.CommittedBegin begin,ContinuityState originalHead,
            String originalHeadDigest,String expectedDigest)throws IOException {
        WriterContracts.requireDigest(expectedDigest);
        var checked=check(same,owner,pair,opening,begin,originalHead,originalHeadDigest,true);
        StrictJson.require(expectedDigest.equals(checked.digest()),"retained first SAVE archived binding changed");
        return new RetainedFirstCheckpoint(this,owner,pair,opening,begin,originalHead,originalHeadDigest,expectedDigest,checked.original());
    }
    public void requireRetained(ContinuityStorePort.Session same,RetainedFirstCheckpoint proof)throws IOException {
        Objects.requireNonNull(proof);StrictJson.require(proof.issuer==this,"foreign retained first SAVE issuer");
        verifyRetainedOriginal(same,proof.session,proof.pair,proof.semantic,proof.begin,proof.originalHead,proof.originalHeadDigest,proof.digest);
    }
    /** Fresh post-SAVE semantic originals, bound to the actual saved complete Driver, not opening SEM. */
    public String requireSavedSemantic(ContinuityStorePort.Session same,RetainedFirstCheckpoint proof,
            SemanticEvidence savedSemantic,boolean physical)throws IOException {
        requireRetained(same,proof);Objects.requireNonNull(savedSemantic);
        var saved=proof.savedDriver();var frame=savedSemantic.frame();var original=proof.pair.frame();
        StrictJson.require(frame.machineId().equals(original.machineId())&&frame.game().equals(original.game())
                &&frame.frame().episodeRunId().equals(original.frame().episodeRunId())
                &&frame.frame().identity().player().equals(original.frame().identity().player())
                &&frame.frame().identity().dateRaw().equals(original.frame().identity().dateRaw())
                &&frame.frame().revision().compareTo(original.frame().revision())>=0
                &&frame.frame().identity().nativeRevision().compareTo(original.frame().identity().nativeRevision())>=0,
                "post-SAVE SEM must retain the exact original episode/actor/date with actual later revisions");
        for(ExactRef ref:savedSemantic.references())readExact(ref);
        StrictJson.require(Arrays.equals(saved.encode(),readExact(savedSemantic.originalDriver()))
                &&!savedSemantic.originalDriver().equals(proof.semantic.originalDriver()),
                "post-SAVE SEM must archive the actual saved Driver, not the opening Driver");
        String digest=semantics.verify(same,proof.session,savedSemantic);WriterContracts.requireDigest(digest);
        if(physical)drivers.verifyOriginal(proof.pair,saved.session());requireLease(same);return digest;
    }
    private Checked check(ContinuityStorePort.Session same,SessionIdentity owner,CheckpointPair pair,SemanticEvidence opening,
            EpisodeWindow.CommittedBegin begin,ContinuityState originalHead,String originalHeadDigest,boolean retained)throws IOException {
        requireLease(same);Objects.requireNonNull(owner);Objects.requireNonNull(pair);Objects.requireNonNull(opening);Objects.requireNonNull(begin);
        WriterContracts.requireDigest(originalHeadDigest);same.requireHistoricalState(originalHead.sequence(),originalHeadDigest);
        StrictJson.require(ContinuityJson.digest(originalHead.toJson()).equals(originalHeadDigest),"actual first SAVE captured head differs");
        if(retained){
            var beginState=same.requireHistoricalState(begin.sequence(),begin.headDigest());
            var historical=EpisodeWindow.state(beginState).orElseThrow();
            StrictJson.require(historical.phase()==EpisodeWindow.Phase.AWAITING_FIRST_SAVE&&historical.begin().equals(begin.begin()),
                    "retained first SAVE lacks its exact canonical BEGIN ancestor");
            same.verifyPin(begin.eventPin());
        }else same.requireEpisodeWindowBegin(begin);
        var captured=EpisodeWindow.state(originalHead).orElseThrow();
        StrictJson.require(captured.phase()==EpisodeWindow.Phase.AWAITING_FIRST_SAVE&&captured.begin().equals(begin.begin())
                &&originalHead.sequence()>begin.sequence(),"first SAVE must descend from its actual awaiting BEGIN");
        var identity=begin.begin().after();var frame=opening.frame();
        StrictJson.require(owner.machineId().equals(identity.machineId())&&owner.game().equals(identity.game())&&owner.sessionId().equals(identity.sessionId())
                &&frame.machineId().equals(owner.machineId())&&frame.game().equals(owner.game())
                &&frame.frame().episodeRunId().equals(identity.episodeRunId())&&frame.frame().identity().player().longValueExact()==identity.actorId()
                &&frame.frame().identity().dateRaw().longValueExact()==identity.dateRaw()
                &&pair.frame().machineId().equals(frame.machineId())&&pair.frame().game().equals(frame.game())
                &&pair.frame().frame().episodeRunId().equals(identity.episodeRunId())&&pair.frame().frame().identity().player().longValueExact()==identity.actorId()
                &&pair.frame().frame().identity().dateRaw().longValueExact()==identity.dateRaw(),"first SAVE crossed new Game/session/episode/actor/opening date");
        for(ExactRef ref:opening.references())readExact(ref);
        String semanticDigest=semantics.verify(same,owner,opening);WriterContracts.requireDigest(semanticDigest);
        var before=DriverStateSnapshot.decodeComplete(readExact(opening.originalDriver()));
        StrictJson.require(Arrays.equals(before.encode(),readExact(begin.begin().adoptedDriverRef())),
                "first SAVE opening Driver is not the actual NEXT adopted full Driver");
        // A real first SAVE appends one row. An equal Driver or a prior Game's pair cannot be promoted.
        var original=saves.verifyFirst(same,owner,pair,frame,!retained);
        var saved=original.savedDriver();
        StrictJson.require(saved.commandHistory().size()==before.commandHistory().size()+1,"first SAVE must append exactly one actual row");
        CheckpointCommitVerifier.requireSaveProjection(before,saved,pair);
        if(!retained)drivers.verifyOriginal(pair,before.session());
        requireLease(same);var row=StrictJson.object();row.put("schema","xar.java-first-save-binding/v1");row.set("begin",begin.toJson());
        row.put("original_writer_head_sha256",originalHeadDigest);row.put("semantic_verifier_sha256",semanticDigest);
        row.put("canonical_save_sha256",original.digest());row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
        row.set("session",org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionToJson(owner));
        var refs=row.putArray("opening_sources");opening.references().forEach(ref->refs.add(ref.toJson()));
        return new Checked(ContinuityJson.digest(row),original,before);
    }
    private void requireLease(ContinuityStorePort.Session same)throws IOException {
        leases.require(Objects.requireNonNull(same));same.requireWriter(writerLock);
    }
    private byte[] readExact(ExactRef ref)throws IOException {
        var witness=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("first SAVE original source unavailable"));
        StrictJson.require(witness.reference().equals(ref),"first SAVE original source path/hash changed");return files.read(witness,DriverCheckpointStore.MAX_DRIVER_BYTES);
    }
}
