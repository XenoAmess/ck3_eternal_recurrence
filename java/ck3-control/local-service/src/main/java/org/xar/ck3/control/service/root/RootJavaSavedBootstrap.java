package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.RootProcessAttach;

/** New-daemon Java SAVE qualification. Old canonical DATA never grants new physical Game custody. */
public final class RootJavaSavedBootstrap {
    private static final int MAX_STATE=1<<20;
    private static final String KIND="JAVA_CONFIRMED_SAVED_GAME_ENTRY";
    private RootJavaSavedBootstrap(){ }

    /** Source-only factory. No managed Game, snapshot supplier, SAVE or live issuer is manufactured. */
    public static ConfirmedSource qualify(RootApplicationAssembly.Core sourceCore,CheckpointFiles actualFiles,
            Path materialRoot,String originalPipeName,CheckpointPair pair,WriterContracts.Pin confirmation)throws IOException {
        Objects.requireNonNull(sourceCore);Objects.requireNonNull(actualFiles);Objects.requireNonNull(pair);
        StrictJson.text(originalPipeName);
        var writer=sourceCore.writer();
        var snapshots=new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> unused)throws IOException {
                throw new IOException("confirmed historical source factory cannot publish a Driver or submit SAVE");
            }
        };
        var drivers=new DriverCheckpointStore(actualFiles,Path.of(pair.driver().reference().path()),originalPipeName,snapshots);
        var saves=new CanonicalSaveReceiptVerifier(writer,sourceCore.actions(),sourceCore.archive(),actualFiles,drivers);
        var verifier=new CheckpointCommitVerifier(actualFiles,drivers,
                (same,owner,semantic)->sourceCore.semanticVerifier().verify(same,owner,semantic).materialDigest(),
                writer.originalLockPath(),writer::requireSession,saves);
        long target=writer.locked(same->same.head().state().origin().targetDays());
        var cycles=new OrdinaryCycleTransitions(sourceCore.archive(),sourceCore.semanticVerifier()::verify,
                verifier::verify,new OriginalWindowReducer.Policy(target),writer::requireSession);
        cycles.bindTerminalFrameLoader(sourceCore.frameLoader());
        var store=new SavedAttachmentSourceStore(actualFiles,drivers,verifier,writer::borrowedSession,materialRoot,
                cycles::verifyCompletedCycleProof,cycles::verifyHistoricalCompletedCycleProof);
        return writer.locked(same->{
            writer.requireSession(same);
            for(var action:ContinuityActionJournal.receipts(same.head().state(),sourceCore.archive().withSession(same)))
                StrictJson.require(action.settled(),"confirmed saved source cannot erase an unresolved canonical action");
            var actual=store.requalifyConfirmed(same,confirmation,pair);
            var material=actual.requireCurrent(same);
            return new ConfirmedSource(writer,store,actual,material);
        });
    }

    /** Opaque qualification of old original DATA and present files; never a replacement or Ready permit. */
    public static final class ConfirmedSource {
        private final ContinuityWriter writer;
        private final SavedAttachmentSourceStore store;
        private final SavedAttachmentSourceStore.RequalifiedConfirmed qualified;
        private final SavedAttachmentSourceStore.SavedMaterial material;
        private ConfirmedSource(ContinuityWriter writer,SavedAttachmentSourceStore store,
                SavedAttachmentSourceStore.RequalifiedConfirmed qualified,SavedAttachmentSourceStore.SavedMaterial material) {
            this.writer=writer;this.store=store;this.qualified=qualified;this.material=material;
        }
        public CheckpointPair pair(){return material.pair();}
        public ContinuityState savedState(){return qualified.confirmation().after();}
        public ContinuityState sourceHead(){return qualified.sourceHead();}
        public WriterContracts.HistoricalTransition confirmation(){return qualified.confirmation();}
        private DriverStateSnapshot.Complete requireCurrent()throws IOException {
            return writer.locked(same->{
                writer.requireSession(same);var current=qualified.requireCurrent(same);
                StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair())
                        &&Arrays.equals(current.savedDriver().encode(),material.savedDriver().encode()),
                        "confirmed source changed its actual saved Driver or session");
                return current.savedDriver();
            });
        }
        private DriverStateSnapshot.Complete requireRetained()throws IOException {
            return writer.locked(same->{
                writer.requireSession(same);var current=qualified.requireRetained(same);
                StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair())
                        &&Arrays.equals(current.savedDriver().encode(),material.savedDriver().encode()),
                        "retained source changed its actual saved Driver or session");
                return current.savedDriver();
            });
        }
    }

    /** The new managed creator, two genuine independent READs and the exact new writer are all required. */
    public static Admission admit(ConfirmedSource source,RootRuntimeContext context,JavaGameLifecycle creator,
            JavaGameLifecycle.Started started,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(source);Objects.requireNonNull(context);Objects.requireNonNull(creator);
        Objects.requireNonNull(started);Objects.requireNonNull(deadline);
        var game=context.game();
        StrictJson.require(game==started.session()&&game.mode()==ManagedGameSession.Mode.OWNED
                &&source.writer!=context.writer()
                &&!source.writer.originalLockPath().equals(context.writer().originalLockPath())
                &&!source.pair().frame().game().equals(game.generation()),
                "new saved admission requires a distinct actual owned Game and independent writer");
        StrictJson.require(game.launchPlan().load() instanceof NativeLaunchPlan.SavedGame saved
                &&new ExactRef(saved.save().path(),saved.save().bytes(),saved.save().sha256()).equals(source.pair().save().reference()),
                "new saved admission did not launch the exact confirmed physical SAVE");
        source.requireCurrent();game.verify();
        Path evidence=game.launchPlan().evidenceRoot().resolve("java-confirmed-saved-"+UUID.randomUUID());
        RootProcessAttach.Custody actual=RootProcessAttach.retain(creator,started,source.pair(),evidence,deadline);
        return completeAdmission(source,context,proof(actual),deadline);
    }

    public static Admission admitLoaded(ConfirmedSource source,RootRuntimeContext context,RootProcessAttach.LoadedCustody actual,
            Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(source);Objects.requireNonNull(context);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
        var game=context.game();
        StrictJson.require(game==actual.game()&&game.mode()==ManagedGameSession.Mode.ATTACHED
                &&actual.pair().equals(source.pair())&&source.writer!=context.writer()
                &&!source.writer.originalLockPath().equals(context.writer().originalLockPath())
                &&!source.pair().frame().game().equals(game.generation()),
                "loaded saved admission requires exact current attached custody and independent new writer");
        source.requireCurrent();actual.requireCurrent();
        Instant bounded=deadline.isBefore(actual.deadline())?deadline:actual.deadline();
        return completeAdmission(source,context,proof(actual),bounded);
    }

    private interface PhysicalProof extends AutoCloseable {
        void requireCurrent()throws IOException;
        void requireEvidence()throws IOException;
        void releasePreparation()throws IOException;
        @Override void close()throws IOException;
    }
    private static PhysicalProof proof(RootProcessAttach.Custody actual) {
        return new PhysicalProof() {
            public void requireCurrent()throws IOException{actual.requireCurrent();}
            public void requireEvidence()throws IOException{actual.requireEvidence();}
            public void releasePreparation()throws IOException{actual.releasePreparation();}
            public void close()throws IOException{actual.close();}
        };
    }
    private static PhysicalProof proof(RootProcessAttach.LoadedCustody actual) {
        return new PhysicalProof() {
            public void requireCurrent()throws IOException{actual.requireCurrent();}
            public void requireEvidence()throws IOException{actual.requireEvidence();}
            public void releasePreparation()throws IOException{actual.releasePreparation();}
            public void close()throws IOException{actual.close();}
        };
    }
    private static Admission completeAdmission(ConfirmedSource source,RootRuntimeContext context,PhysicalProof physical,
            Instant deadline)throws IOException,InterruptedException {
        try {
            var first=fresh(context,deadline);var second=fresh(context,deadline);
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            requireRaw(source,context,first);requireRaw(source,context,second);
            StrictJson.require(first.originalFrame().session().equals(second.originalFrame().session())
                    &&first.originalFrame().nativeRevision().equals(second.originalFrame().nativeRevision())
                    &&Arrays.equals(first.originalFrame().state().bytes(),second.originalFrame().state().bytes()),
                    "two actual loaded paused READs did not retain the same original full map");
            source.requireCurrent();physical.requireCurrent();
            return context.withSession(same->{
                context.writer().requireSession(same);var head=same.head();
                StrictJson.require(head.state().status()==ContinuityState.Status.AWAITING_INITIAL_ENTRY,
                        "new saved admission requires the exact unconsumed fresh writer");
                var archive=context.archive().withSession(same);var refs=new ArrayList<ExactRef>();
                for(var read:List.of(first,second)) {
                    archive.preserve(read.acknowledgement());refs.add(archive.referenceOf(read.acknowledgement()));
                    refs.add(archive.preserveNativeFrame(read.originalFrame()));
                }
                ExactRef savedState= context.archive().preserveArtifact(same,ContinuityJson.canonical(source.savedState().toJson()),MAX_STATE);
                ExactRef sourceHead=context.archive().preserveArtifact(same,ContinuityJson.canonical(source.sourceHead().toJson()),MAX_STATE);
                refs.add(savedState);refs.add(sourceHead);
                var frame=second.originalFrame();ExactRef secondFrame=refs.get(3);
                var qualification=context.sources().verifyPhysicalOrigin(same,frame.session(),context.source(),secondFrame,
                        context.transport().diagnostics(),deadline);
                qualification.assertCurrent(same);qualification.proof().ifPresent(refs::add);
                var pins=new ArrayList<WriterContracts.Pin>();
                for(var ref:refs){var pin=same.capturePin(ref,Math.toIntExact(ref.bytes()));same.verifyPin(pin);pins.add(pin);}
                StrictJson.require(head.digest().equals(same.head().digest()),"saved admission preparation changed the new writer head");
                return new Admission(source,context,physical,first,second,qualification,head,savedState,sourceHead,List.copyOf(pins),deadline);
            });
        }catch(IOException|RuntimeException|Error|InterruptedException failure) {
            try{physical.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;
        }
    }

    /** Private new-daemon capability, with separate precommit and retained actual-entry phases. */
    public static final class Admission {
        private final ConfirmedSource source;
        private final RootRuntimeContext context;
        private final PhysicalProof physical;
        private final NativeFreshSnapshotPort.Received first,second;
        private final NativeReadinessCollector.SourceQualification qualification;
        private final WriterContracts.Head before;
        private final ExactRef savedState,sourceHead;
        private final List<WriterContracts.Pin> originals;
        private final Instant deadline;
        private WriterContracts.Prepared prepared;
        private WriterContracts.Receipt receipt;
        private Admission(ConfirmedSource source,RootRuntimeContext context,PhysicalProof physical,
                NativeFreshSnapshotPort.Received first,NativeFreshSnapshotPort.Received second,
                NativeReadinessCollector.SourceQualification qualification,WriterContracts.Head before,
                ExactRef savedState,ExactRef sourceHead,List<WriterContracts.Pin> originals,Instant deadline) {
            this.source=source;this.context=context;this.physical=physical;this.first=first;this.second=second;
            this.qualification=qualification;this.before=before;this.savedState=savedState;this.sourceHead=sourceHead;
            this.originals=originals;this.deadline=deadline;
        }
        public ConfirmedSource source(){return source;}
        public SessionIdentity session(){return new SessionIdentity(game().machineId(),game().generation(),game().sessionId());}
        public DriverStateSnapshot.Complete savedDriver(){return source.material.savedDriver();}
        public ManagedGameSession game(){return context.game();}
        public NativeFreshSnapshotPort.Received firstRead(){return first;}
        public NativeFreshSnapshotPort.Received secondRead(){return second;}
        public ExactRef savedStateReference(){return savedState;}
        public ExactRef sourceHeadReference(){return sourceHead;}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(receipt==null&&before.digest().equals(same.head().digest())
                    &&context.clock().instant().isBefore(deadline),"saved admission escaped its exact precommit new writer point");
            physical.requireCurrent();qualification.assertCurrent(same);requireOriginals(same);source.requireCurrent();
        }
        /** Only the exact real new-writer transaction can enter the retained phase. */
        public synchronized void recordCommitted(ContinuityStorePort.Session same,WriterContracts.Prepared actual,
                WriterContracts.Receipt committed)throws IOException {
            context.writer().requireSession(same);Objects.requireNonNull(actual);Objects.requireNonNull(committed);
            StrictJson.require(receipt==null&&actual.predecessor().digest().equals(before.digest())&&KIND.equals(actual.request().kind()),
                    "saved admission was consumed or supplied another predecessor/event kind");
            same.requireCommitted(actual,committed);
            var row=actual.request().detailsObject();
            StrictJson.require(savedState.equals(ExactRef.fromJson(row.get("saved_state_reference")))
                    &&sourceHead.equals(ExactRef.fromJson(row.get("source_head_reference")))
                    &&source.confirmation().eventPin().reference().equals(ExactRef.fromJson(row.get("confirmation_reference")))
                    &&source.pair().equals(CheckpointPairCodec.decode(ContinuityJson.canonical(row.get("checkpoint_pair"))))
                    &&session().equals(OrdinaryCycleTransitions.sessionFromJson(row.get("session"))),
                    "saved admission actual transaction differs from its private source snapshots/pair/owner");
            requireOriginals(same);source.requireCurrent();physical.requireCurrent();
            physical.releasePreparation();prepared=actual;receipt=committed;
        }
        public synchronized void requireRetained(ContinuityStorePort.Session same,WriterContracts.Receipt committed)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(receipt!=null&&committed==receipt&&prepared!=null,"saved admission lacks its exact actual committed entry");
            same.requireCommitted(prepared,receipt);game().verify();physical.requireEvidence();requireOriginals(same);source.requireRetained();
        }
        private void requireOriginals(ContinuityStorePort.Session same)throws IOException {
            for(var pin:originals)same.verifyPin(pin);
            NativeFreshSnapshotPort.verifyOriginal(first.acknowledgement(),first.originalFrame(),first.snapshotReceived());
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            requireRaw(source,context,first);requireRaw(source,context,second);
            StrictJson.require(Arrays.equals(ContinuityJson.canonical(source.savedState().toJson()),same.readPinned(find(savedState),MAX_STATE))
                    &&Arrays.equals(ContinuityJson.canonical(source.sourceHead().toJson()),same.readPinned(find(sourceHead),MAX_STATE)),
                    "new archive saved/source snapshots differ from their actual old canonical states");
        }
        private WriterContracts.Pin find(ExactRef ref)throws IOException {
            return originals.stream().filter(pin->pin.reference().equals(ref)).findFirst().orElseThrow(()->new IOException("saved admission original pin is missing"));
        }
    }

    private static NativeFreshSnapshotPort.Received fresh(RootRuntimeContext context,Instant deadline)throws IOException,InterruptedException {
        var result=context.transport().readFreshFullState(deadline);
        if(result instanceof NativeFreshSnapshotPort.Received received) {
            NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(),received.originalFrame(),received.snapshotReceived());return received;
        }
        var unavailable=(NativeFreshSnapshotPort.Unavailable)result;
        context.withSession(same->{var archive=context.archive().withSession(same);archive.preserve(unavailable.dispatch());
            if(unavailable.originalFrame().isPresent())archive.preserveNativeFrame(unavailable.originalFrame().orElseThrow());return null;});
        throw new IOException("actual saved cold READ unavailable, no retry or dispatch permission: "+unavailable.reason());
    }
    private static void requireRaw(ConfirmedSource source,RootRuntimeContext context,NativeFreshSnapshotPort.Received read)throws IOException {
        var frame=read.originalFrame();var session=frame.session();DriverObservationAssembler.originalNativeState(frame);
        StrictJson.require(session.machineId().equals(context.game().machineId())&&session.game().equals(context.game().generation())
                &&session.sessionId().equals(context.game().sessionId())&&!session.game().equals(source.pair().frame().game()),
                "cold saved READ crossed its actual new managed Game/session");
        var raw=FullJsonTree.parse(frame.state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(raw instanceof ObjectNode,"cold saved full state object is absent");var state=(ObjectNode)raw;
        StrictJson.trueValue(state.get("paused"));StrictJson.trueValue(state.get("map_ready"));
        StrictJson.require(state.get("played_character") instanceof ObjectNode,"cold saved living actor is absent");
        var player=(ObjectNode)state.get("played_character");StrictJson.trueValue(player.get("alive"));
        StrictJson.require(NativeCharacterId.fromJson(player.get("character_id")).asBigInteger().equals(source.pair().frame().frame().identity().player())
                &&StrictJson.integer(state.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)==source.pair().frame().frame().identity().dateRaw().longValueExact(),
                "actual loaded SAVE changed its paired actor/date");
    }
}
