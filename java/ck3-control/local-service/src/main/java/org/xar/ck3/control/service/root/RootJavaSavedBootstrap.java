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
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.checkpoint.CheckpointCommitVerifier;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
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
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
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
            return new ConfirmedSource(writer,store,actual,material,sourceCore.archive());
        });
    }

    /** Opaque qualification of old original DATA and present files; never a replacement or Ready permit. */
    public static final class ConfirmedSource {
        private final ContinuityWriter writer;
        private final SavedAttachmentSourceStore store;
        private final SavedAttachmentSourceStore.RequalifiedConfirmed qualified;
        private final SavedAttachmentSourceStore.SavedMaterial material;
        private final byte[] savedDriverCanonical;
        private final NativeOutcomeArchive sourceArchive;
        private ConfirmedSource(ContinuityWriter writer,SavedAttachmentSourceStore store,
                SavedAttachmentSourceStore.RequalifiedConfirmed qualified,SavedAttachmentSourceStore.SavedMaterial material,
                NativeOutcomeArchive sourceArchive) {
            this.writer=writer;this.store=store;this.qualified=qualified;this.material=material;
            this.savedDriverCanonical=material.savedDriver().encode();
            this.sourceArchive=Objects.requireNonNull(sourceArchive);
            StrictJson.require(sourceArchive.writer()==writer,"confirmed source archive must belong to the actual source writer");
        }
        public CheckpointPair pair(){return material.pair();}
        public ContinuityState savedState(){return qualified.confirmation().after();}
        public ContinuityState sourceHead(){return qualified.sourceHead();}
        public WriterContracts.HistoricalTransition confirmation(){return qualified.confirmation();}
        private DriverStateSnapshot.Complete requireCurrent()throws IOException {
            return writer.locked(same->{
                writer.requireSession(same);var current=qualified.requireCurrent(same);
                StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair())
                        &&Arrays.equals(current.savedDriver().encode(),savedDriverCanonical),
                        "confirmed source changed its actual saved Driver or session");
                return current.savedDriver();
            });
        }
        private DriverStateSnapshot.Complete requireRetained()throws IOException {
            return writer.locked(same->{
                writer.requireSession(same);var result=qualified.requireRetainedResult(same);
                var current=result.material();
                StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair()),
                        "retained source changed its actual saved Driver or session");
                StrictJson.require(result.matchesDriverEncoding(savedDriverCanonical),
                        "retained source changed its actual saved Driver or session");
                return current.savedDriver();
            });
        }
        private DriverStateSnapshot.Complete requireCurrent(ContinuityStorePort.Session activeNewSame)throws IOException {
            return writer.readOnlyFrom(activeNewSame, same->{
                writer.requireSession(same);
                return sourceArchive.inHistoricalReadScope(same, new ActionPorts.HistoricalReadLimits(1024, 64L * 1024 * 1024, 256),
                        ignoredArchive -> {
                    var current=qualified.requireCurrent(same);
                    StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair())
                            &&Arrays.equals(current.savedDriver().encode(),savedDriverCanonical),
                            "confirmed source changed its actual saved Driver or session");
                    return current.savedDriver();
                });
            });
        }
        private DriverStateSnapshot.Complete requireRetained(ContinuityStorePort.Session activeNewSame)throws IOException {
            return writer.readOnlyFrom(activeNewSame, same->{
                writer.requireSession(same);
                return sourceArchive.inHistoricalReadScope(same, new ActionPorts.HistoricalReadLimits(1024, 64L * 1024 * 1024, 256),
                        ignoredArchive -> {
                    var result=qualified.requireRetainedResult(same);
                    var current=result.material();
                    StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair()),
                            "retained source changed its actual saved Driver or session");
                    StrictJson.require(result.matchesDriverEncoding(savedDriverCanonical),
                            "retained source changed its actual saved Driver or session");
                    return current.savedDriver();
                });
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
            var readOriginals=context.withSession(same->{
                context.writer().requireSession(same);var before=same.head();
                StrictJson.require(before.state().status()==ContinuityState.Status.AWAITING_INITIAL_ENTRY,
                        "saved READ originals require the exact unconsumed fresh writer");
                var archive=context.archive().withSession(same);var originals=new ArrayList<ExactRef>();
                for(var read:List.of(first,second)) {
                    archive.preserve(read.acknowledgement());originals.add(archive.referenceOf(read.acknowledgement()));
                    originals.add(archive.preserveNativeFrame(read.originalFrame()));
                }
                StrictJson.require(before.digest().equals(same.head().digest()),"saved READ original capture changed the new writer head");
                return List.copyOf(originals);
            });
            try {
                RestoreCheckpointService.requireStableReadProgression(first.originalFrame(), second.originalFrame());
            } catch (RuntimeException failure) {
                throw new IOException("two actual loaded paused READs failed stable progression: first_ack=" + readOriginals.get(0)
                        + "; first_frame=" + readOriginals.get(1)
                        + "; second_ack=" + readOriginals.get(2)
                        + "; second_frame=" + readOriginals.get(3)
                        + "; first_native_revision=" + first.originalFrame().nativeRevision()
                        + "; second_native_revision=" + second.originalFrame().nativeRevision(), failure);
            }
            source.requireCurrent();physical.requireCurrent();
            return context.withSession(same->{
                context.writer().requireSession(same);var head=same.head();
                StrictJson.require(head.state().status()==ContinuityState.Status.AWAITING_INITIAL_ENTRY,
                        "new saved admission requires the exact unconsumed fresh writer");
                var refs=new ArrayList<ExactRef>(readOriginals);
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
            physical.requireCurrent();qualification.assertCurrent(same);requireOriginals(same);source.requireCurrent(same);
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
            requireOriginals(same);source.requireCurrent(same);physical.requireCurrent();
            physical.releasePreparation();prepared=actual;receipt=committed;
        }
        public synchronized void requireRetained(ContinuityStorePort.Session same,WriterContracts.Receipt committed)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(receipt!=null&&committed==receipt&&prepared!=null,"saved admission lacks its exact actual committed entry");
            same.requireCommitted(prepared,receipt);game().verify();physical.requireEvidence();requireOriginals(same);source.requireRetained(same);
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

    /** Recover only an already committed saved entry under new actual physical READ custody. */
    public static RetainedSaved reopenLoaded(ConfirmedSource source,RootRuntimeContext context,
            RootProcessAttach.LoadedCustody actual,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(source);Objects.requireNonNull(context);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
        var game=context.game();
        StrictJson.require(game==actual.game()&&game.mode()==ManagedGameSession.Mode.ATTACHED
                &&actual.pair().equals(source.pair())&&source.writer!=context.writer()
                &&!source.writer.originalLockPath().equals(context.writer().originalLockPath())
                &&!source.pair().frame().game().equals(game.generation()),
                "retained saved entry requires exact attached custody and independent writer");
        source.requireCurrent();actual.requireCurrent();
        Instant bounded=deadline.isBefore(actual.deadline())?deadline:actual.deadline();
        var physical=proof(actual);
        try {
            var entry=context.withSession(same->{
                context.writer().requireSession(same);var head=same.head();
                var marker=head.state().toJson().get(org.xar.ck3.control.continuity.SavedContinuityBootstrap.FIELD);
                StrictJson.require(marker instanceof ObjectNode,"retained saved entry marker is absent");
                StrictJson.require(!(head.state().pendingCycle() instanceof ContinuityState.Present)
                        &&ContinuityActionJournal.receipts(head.state(),context.archive().withSession(same)).isEmpty(),
                        "retained saved startup cannot erase a gameplay or pending cycle history");
                WriterContracts.HistoricalTransition found=null;
                for(var pin:head.documents()) {
                    var document=ContinuityJson.parseObject(same.readPinned(pin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
                    if(KIND.equals(document.path("kind").asText())&&ContinuityJson.same(marker,document.get("details"))) {
                        StrictJson.require(found==null,"retained saved entry is not unique in actual canonical history");
                        found=same.readHistoricalTransition(pin);
                    }
                }
                StrictJson.require(found!=null,"retained saved marker has no actual canonical entry");
                requireReadOnlySavedContinuation(same,found);
                requireSavedHistorical(source,context,same,found,true);
                StrictJson.require(head.digest().equals(same.head().digest()),"retained saved lookup changed current head");
                return found;
            });
            var first=fresh(context,bounded);var second=fresh(context,bounded);
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            requireRaw(source,context,first);requireRaw(source,context,second);
            var originals=context.withSession(same->{
                context.writer().requireSession(same);var head=same.head();
                requireSavedHistorical(source,context,same,entry,true);
                var archive=context.archive().withSession(same);var refs=new ArrayList<ExactRef>();
                for(var read:List.of(first,second)) {
                    archive.preserve(read.acknowledgement());refs.add(archive.referenceOf(read.acknowledgement()));
                    refs.add(archive.preserveNativeFrame(read.originalFrame()));
                }
                StrictJson.require(head.digest().equals(same.head().digest()),"retained READ capture changed current writer");
                return List.copyOf(refs);
            });
            try {RestoreCheckpointService.requireStableReadProgression(first.originalFrame(),second.originalFrame());}
            catch(RuntimeException failure) {throw new IOException("retained saved READ progression failed: originals="+originals,failure);}
            source.requireCurrent();physical.requireCurrent();
            return context.withSession(same->{
                context.writer().requireSession(same);var head=same.head();
                var row=requireSavedHistorical(source,context,same,entry,true);
                var historicalOpening=ContinuityJson.object(ContinuityJson.object(row.get("opening")).get("frame"));
                StrictJson.require(second.originalFrame().nativeRevision().compareTo(new java.math.BigInteger(
                        StrictJson.text(historicalOpening.get("native_revision"))))>=0,
                        "retained current READ regressed behind actual saved opening");
                var refs=new ArrayList<ExactRef>(originals);
                refs.addAll(org.xar.ck3.control.continuity.SavedContinuityBootstrap.request(row).evidence());
                var oldSource=ContinuityJson.object(row.get("source"));
                StrictJson.require(StrictJson.text(oldSource.get("machine_id")).equals(game.machineId())
                        &&StrictJson.text(oldSource.get("exact_build")).equals(context.source().exactBuild()),
                        "retained saved historical source belongs to another machine/build");
                refs.add(ExactRef.fromJson(oldSource.get("source_ref")));
                var qualification=context.sources().verifyPhysicalOrigin(same,second.originalFrame().session(),context.source(),
                        originals.get(3),context.transport().diagnostics(),bounded);
                qualification.assertCurrent(same);qualification.proof().ifPresent(refs::add);
                var pins=new ArrayList<WriterContracts.Pin>();
                for(var ref:refs.stream().distinct().toList()) {
                    var pin=same.capturePin(ref,Math.toIntExact(ref.bytes()));same.verifyPin(pin);pins.add(pin);
                }
                StrictJson.require(head.digest().equals(same.head().digest()),"retained qualification changed current writer");
                var suffix=requireReadOnlySavedContinuation(same,entry);pins.addAll(suffix.originalPins());
                var retained=new RetainedSaved(source,context,physical,first,second,qualification,entry,List.copyOf(pins),bounded,
                        suffix.reads(),head.state().status()==ContinuityState.Status.REPAIR_REQUIRED
                                ?List.of(StrictJson.text(ContinuityJson.object(head.state().toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).get("batch_id"))):List.of());
                retained.requireCurrent(same);physical.releasePreparation();return retained;
            });
        }catch(IOException|RuntimeException|Error|InterruptedException failure) {
            try{physical.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;
        }
    }

    /** Pure existing-ledger checks. This creates no physical/Native/dispatch qualification. */
    public static void requireRetainedSavedSourceSuffix(ConfirmedSource source,ContinuityStorePort.Session same,
            NativeOutcomeArchive archive)throws IOException {
        var original=existingSavedSource(source,same,archive,true);var head=original.getKey();var entry=original.getValue();
        requireReadOnlySavedContinuation(same,entry);
        StrictJson.require(head.digest().equals(same.head().digest()),"retained Saved preflight changed actual head");
    }
    /** Exact original canonical Entry/source DATA only; no new admission or pending-action permission. */
    static java.util.Map.Entry<WriterContracts.Head,WriterContracts.HistoricalTransition> existingSavedSource(
            ConfirmedSource source,ContinuityStorePort.Session same,NativeOutcomeArchive archive)throws IOException {
        return existingSavedSource(source,same,archive,false);
    }
    private static java.util.Map.Entry<WriterContracts.Head,WriterContracts.HistoricalTransition> existingSavedSource(
            ConfirmedSource source,ContinuityStorePort.Session same,NativeOutcomeArchive archive,boolean requireEmptyActions)throws IOException {
        Objects.requireNonNull(source);Objects.requireNonNull(same);Objects.requireNonNull(archive);
        archive.writer().requireSession(same);var head=same.head();var state=head.state();
        StrictJson.require(source.writer!=archive.writer()&&!source.writer.originalLockPath().equals(archive.writer().originalLockPath())
                &&!(state.pendingCycle() instanceof ContinuityState.Present)
                &&(!requireEmptyActions||ContinuityActionJournal.receipts(state,archive.withSession(same)).isEmpty()),
                "retained Saved startup requires independent writer and empty canonical action/pending history");
        var marker=ContinuityJson.object(state.toJson().get(org.xar.ck3.control.continuity.SavedContinuityBootstrap.FIELD));
        WriterContracts.HistoricalTransition entry=null;
        for(var pin:head.documents()) {
            var row=ContinuityJson.parseObject(same.readPinned(pin,ContinuityJson.LEDGER_MAX_BYTES),ContinuityJson.LEDGER_MAX_BYTES);
            if(KIND.equals(row.path("kind").asText())&&ContinuityJson.same(marker,row.get("details"))) {
                StrictJson.require(entry==null,"retained Saved marker has more than one canonical entry");
                entry=same.readHistoricalTransition(pin);
            }
        }
        StrictJson.require(entry!=null,"retained Saved marker lacks its actual canonical entry");
        var request=org.xar.ck3.control.continuity.SavedContinuityBootstrap.request(marker);
        StrictJson.require(request.identity().equals(entry.eventIdentity()),"retained Saved canonical request identity differs");
        org.xar.ck3.control.continuity.SavedContinuityBootstrap.requireSavedAdmissionReduction(entry.before(),entry.after(),request,true);
        var owner=OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
        StrictJson.require(state.machineId().equals(owner.machineId())
                &&ContinuityJson.same(state.toJson().get("game_binding"),entry.after().toJson().get("game_binding"))
                &&state.origin().equals(source.savedState().origin())&&state.origin().equals(entry.after().origin())
                &&state.settledCycles()==source.savedState().settledCycles()&&state.settledDateRaw()==source.savedState().settledDateRaw()
                &&ContinuityJson.same(marker.get("checkpoint_pair"),StrictJson.parse(CheckpointPairCodec.encode(source.pair())))
                &&ExactRef.fromJson(marker.get("confirmation_reference")).equals(source.confirmation().eventPin().reference())
                &&ContinuityJson.same(state.toJson().get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD),marker.get("full_driver")),
                "retained Saved startup changed source pair, owner, origin or saved frontier/baseline");
        StrictJson.require(head.digest().equals(same.head().digest()),"existing Saved source changed actual head");
        return java.util.Map.entry(head,entry);
    }

    /** One domain-import prefix, optionally followed by one closed actionless interrupted READ batch. */
    private record SavedReadOnlySuffix(List<WriterContracts.HistoricalTransition> reads,List<WriterContracts.Pin> originalPins) {
        private SavedReadOnlySuffix {reads=List.copyOf(reads);originalPins=List.copyOf(originalPins);}
    }
    private static SavedReadOnlySuffix requireReadOnlySavedContinuation(
            ContinuityStorePort.Session same,WriterContracts.HistoricalTransition entry)throws IOException {
        var head=same.head();var cursor=entry.after();
        same.requireHistoricalCanonicalState(entry.sequence(),ContinuityJson.digest(cursor.toJson()));
        var marker=ContinuityJson.parseObject(entry.details(),StrictJson.INPUT_MAX_BYTES);
        var owner=OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
        var directory=Path.of(same.persistedHead().path()).toAbsolutePath().normalize().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        var eventPins=new java.util.TreeMap<Long,WriterContracts.Pin>();
        for(var pin:head.documents()) {
            var path=Path.of(pin.reference().path()).toAbsolutePath().normalize();
            if(directory.equals(path.getParent())&&path.getFileName().toString().matches("[0-9]{8}\\.json")) {
                long sequence=Long.parseLong(path.getFileName().toString().substring(0,8));
                StrictJson.require(eventPins.putIfAbsent(sequence,pin)==null,"duplicate actual Saved continuation event");
            }
        }
        var requested=new ArrayList<WriterContracts.Pin>();
        for(long sequence=Math.addExact(entry.sequence(),1);sequence<=head.state().sequence();sequence++) {
            var pin=eventPins.get(sequence);StrictJson.require(pin!=null,"Saved continuation lacks contiguous canonical events");requested.add(pin);
        }
        var edges=requested.isEmpty()?List.<WriterContracts.HistoricalTransition>of():same.readHistoricalTransitions(requested);
        var reads=new ArrayList<WriterContracts.HistoricalTransition>();
        var originalPins=new ArrayList<WriterContracts.Pin>();
        int phase=0;String batch=null;long expectedSequence=entry.sequence();
        ExactRef driver=ExactRef.fromJson(marker.get("full_driver"));
        long version=StrictJson.integer(marker.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER);
        long epoch=StrictJson.integer(marker.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER);
        for(var edge:edges) {
            StrictJson.require(edge.sequence()==Math.addExact(expectedSequence,1)
                    &&ContinuityJson.same(cursor.toJson(),edge.before().toJson()),"Saved continuation changed its actual full predecessor");
            var row=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
            var projected=edge.before().toJson();
            if(edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)) {
                StrictJson.require(phase==0,"domain imports must precede the retained read-only batch");
                var body=org.xar.ck3.control.continuity.writer.DomainBodies.BodyRef.fromJson(row.get("domain_body"));
                var actual=same.requireHistoricalImport(body.slot(),edge.sequence(),ContinuityJson.digest(edge.after().toJson()));
                // Keep the original stronger attachment rule: the actual external original must still exist,
                // retain its native Pin, and be byte-identical to the exact durable registered body.
                var original=ExactRef.fromJson(ContinuityJson.object(row.get("source")).get("original_body"));
                StrictJson.require(original.bytes()>0&&original.bytes()<=WriterContracts.MAX_PIN_BYTES,"finite original domain body required");
                int maximum=Math.toIntExact(original.bytes());var originalPin=same.capturePin(original,maximum);
                var durablePin=new WriterContracts.Pin(body.payload(),body.identity());
                same.verifyPin(originalPin);same.verifyPin(durablePin);
                StrictJson.require(Arrays.equals(same.readPinned(originalPin,maximum),same.readPinned(durablePin,maximum)),
                        "retained original domain body differs from exact durable payload");
                originalPins.add(originalPin);originalPins.add(durablePin);
                StrictJson.require(ContinuityJson.same(actual.predecessor().state().toJson(),edge.before().toJson())
                        &&ContinuityJson.same(actual.receipt().head().toJson(),edge.after().toJson()),"Saved continuation domain reducer differs");
                projected=edge.after().toJson();
            }else if(edge.kind().equals(WriterContracts.ORDINARY_BATCH_KIND)) {
                StrictJson.object(row,java.util.Set.of("evidence_id","source","session","batch_id","boundary","checkpoint_pair","completed_cycle_proof"));
                StrictJson.require(OrdinaryCycleTransitions.sessionFromJson(row.get("session")).equals(owner)
                        &&row.get("checkpoint_pair").isNull()&&row.get("completed_cycle_proof").isNull(),
                        "Saved read-only batch changed owner or claimed a pair/cycle proof");
                String boundary=StrictJson.text(row.get("boundary"));String id=StrictJson.text(row.get("batch_id"));
                String evidence=StrictJson.text(row.get("evidence_id"));
                StrictJson.require(evidence.equals(id+":"+boundary),"Saved read-only batch evidence identity differs");
                if("BATCH_STARTED".equals(boundary)) {
                    StrictJson.require(phase==0&&edge.before().status()==ContinuityState.Status.RUNNING
                            &&!projected.has(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)
                            &&"java-ordinary-session/v1".equals(StrictJson.text(row.get("source"))),
                            "Saved startup cannot reuse an earlier or unfinished batch");
                    batch=id;phase=1;
                }else {
                    StrictJson.require("BATCH_INTERRUPTED".equals(boundary)&&phase==1&&id.equals(batch)
                            &&edge.before().status()==ContinuityState.Status.RUNNING
                            &&"java-ordinary-batch-interruption/v2".equals(StrictJson.text(row.get("source"))),
                            "Saved startup requires one matching original read-only interruption");
                    var interruption=StrictJson.object();interruption.put("evidence_id",evidence);interruption.set("source",row.get("source"));
                    interruption.put("machine_id",owner.machineId());interruption.put("completed_cycles",edge.before().settledCycles());
                    interruption.set("frame",edge.before().toJson().get("latest_binding"));
                    interruption.put("reason","ordinary Java batch interrupted; original unsettled actions remain retained without replay");
                    projected=OriginalWindowReducer.reduce(projected,"ordinary_batch_interrupted",interruption);phase=2;
                }
                var boundaryRow=StrictJson.object();boundaryRow.put("evidence_id",evidence);boundaryRow.set("session",row.get("session"));
                boundaryRow.put("batch_id",id);boundaryRow.put("boundary",boundary);
                projected.set(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD,boundaryRow);
            }else if(edge.kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND)) {
                StrictJson.require(phase==1,"Saved retained READ must belong to its one actual open batch");
                StrictJson.object(row,java.util.Set.of("schema","evidence_id","token","source","predecessor_head_sha256",
                        "read_head_sha256","read_head_sequence","before_version","after_version","episode_epoch","before_driver","after_driver","read_rows"));
                StrictJson.text(row.get("evidence_id"));StrictJson.text(row.get("token"));
                String predecessor=ContinuityJson.digest(edge.before().toJson());
                StrictJson.require("xar.driver-read-publication/v1".equals(StrictJson.text(row.get("schema")))
                        &&ContinuityJson.same(row.get("source"),marker.get("source"))
                        &&StrictJson.text(row.get("predecessor_head_sha256")).equals(predecessor)
                        &&StrictJson.text(row.get("read_head_sha256")).equals(predecessor)
                        &&StrictJson.integer(row.get("read_head_sequence"),0,StrictJson.MAX_SAFE_INTEGER)==edge.before().sequence()
                        &&ExactRef.fromJson(row.get("before_driver")).equals(driver)
                        &&StrictJson.integer(row.get("before_version"),0,StrictJson.MAX_SAFE_INTEGER)==version
                        &&StrictJson.integer(row.get("after_version"),1,StrictJson.MAX_SAFE_INTEGER)==Math.addExact(version,1)
                        &&StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)==epoch,
                        "Saved retained READ changed source or actual full Driver/version/epoch/head chain");
                var rows=row.get("read_rows");StrictJson.require(rows!=null&&rows.isArray()&&!rows.isEmpty()&&rows.size()<=128,
                        "finite original Saved READ rows required");
                for(var item:rows)StrictJson.object(item,java.util.Set.of("index","contract_id","row","read","definition_source","decoder_source"));
                driver=ExactRef.fromJson(row.get("after_driver"));version=Math.addExact(version,1);
                projected.set(WriterContracts.DRIVER_READ_HISTORY_FIELD,row);reads.add(edge);
            }else throw new IOException("Saved startup suffix contains a non-read-only canonical event: "+edge.kind());
            projected.put("sequence",edge.sequence());projected.put("last_event_identity",edge.eventIdentity());
            StrictJson.require(ContinuityJson.same(projected,edge.after().toJson()),"Saved continuation differs from complete actual reducer result");
            cursor=edge.after();expectedSequence=edge.sequence();
        }
        StrictJson.require((phase==0&&head.state().status()==ContinuityState.Status.RUNNING
                ||phase==2&&head.state().status()==ContinuityState.Status.REPAIR_REQUIRED)
                &&ContinuityJson.same(cursor.toJson(),head.state().toJson())
                &&head.digest().equals(same.head().digest()),"Saved startup did not retain its exact closed original continuation");
        return new SavedReadOnlySuffix(reads,originalPins);
    }

    private static ObjectNode requireSavedHistorical(ConfirmedSource source,RootRuntimeContext context,
            ContinuityStorePort.Session same,WriterContracts.HistoricalTransition original,boolean initial)throws IOException {
        context.writer().requireSession(same);
        var actual=same.readHistoricalTransition(original.eventPin());
        StrictJson.require(actual.sequence()==original.sequence()&&actual.eventIdentity().equals(original.eventIdentity())
                &&Arrays.equals(actual.details(),original.details())
                &&ContinuityJson.same(actual.before().toJson(),original.before().toJson())
                &&ContinuityJson.same(actual.after().toJson(),original.after().toJson()),
                "retained saved entry differs from actual complete canonical edge");
        var row=ContinuityJson.parseObject(actual.details(),StrictJson.INPUT_MAX_BYTES);
        var request=org.xar.ck3.control.continuity.SavedContinuityBootstrap.request(row);
        StrictJson.require(KIND.equals(actual.kind())&&request.identity().equals(actual.eventIdentity()),
                "retained saved canonical request identity differs");
        org.xar.ck3.control.continuity.SavedContinuityBootstrap.requireSavedAdmissionReduction(actual.before(),actual.after(),request,true);
        var owner=OrdinaryCycleTransitions.sessionFromJson(row.get("session"));
        var expectedOwner=new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
        var current=same.head().state();
        StrictJson.require(owner.equals(expectedOwner)&&ContinuityJson.same(current.toJson().get(
                org.xar.ck3.control.continuity.SavedContinuityBootstrap.FIELD),row)
                &&ContinuityJson.same(current.toJson().get("game_binding"),actual.after().toJson().get("game_binding"))
                &&current.origin().equals(actual.after().origin()),"retained saved current owner/origin/marker changed");
        if(initial) {
            requireReadOnlySavedContinuation(same,actual);
            StrictJson.require(current.settledCycles()==source.savedState().settledCycles()
                    &&current.settledDateRaw()==source.savedState().settledDateRaw()
                    &&ContinuityJson.same(current.toJson().get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD),row.get("full_driver")),
                    "retained saved startup no longer has original saved basis/baseline");
        }
        var savedRef=ExactRef.fromJson(row.get("saved_state_reference"));
        var headRef=ExactRef.fromJson(row.get("source_head_reference"));
        var input=new org.xar.ck3.control.continuity.SavedContinuityBootstrap.Input(source.savedState(),savedRef,
                source.confirmation().eventPin().reference(),source.sourceHead(),headRef,CheckpointPairCodec.encode(source.pair()),
                ContinuityJson.canonical(row.get("session")),ContinuityJson.canonical(row.get("opening")),
                ExactRef.fromJson(row.get("full_driver")),ExactRef.fromJson(row.get("driver_facts")),
                StrictJson.integer(row.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER));
        StrictJson.require(ContinuityJson.same(row,org.xar.ck3.control.continuity.SavedContinuityBootstrap.details(
                input,StrictJson.text(row.get("evidence_id")),row.get("source"))),"retained saved source details differ from qualified source");
        var archive=context.archive();
        StrictJson.require(Arrays.equals(ContinuityJson.canonical(source.savedState().toJson()),archive.readArtifact(same,savedRef,MAX_STATE))
                &&Arrays.equals(ContinuityJson.canonical(source.sourceHead().toJson()),archive.readArtifact(same,headRef,MAX_STATE)),
                "retained saved archived source snapshots differ from actual old states");
        for(var ref:List.of(input.fullDriver(),input.driverFacts()))archive.readArtifact(same,ref,WriterContracts.MAX_PIN_BYTES);
        return row;
    }

    /** A new private read qualification for an actual previously committed saved entry. */
    public static final class RetainedSaved implements org.xar.ck3.control.application.session.ContinuityBatchJournal.SavedReadOnlyRecoverySource {
        private final ConfirmedSource source;
        private final RootRuntimeContext context;
        private final PhysicalProof physical;
        private final NativeFreshSnapshotPort.Received first,second;
        private final NativeReadinessCollector.SourceQualification qualification;
        private final WriterContracts.HistoricalTransition entry;
        private final List<WriterContracts.Pin> originals;
        private final Instant deadline;
        private final ObjectNode row;
        private final List<WriterContracts.HistoricalTransition> readHistorySuffix;
        private final List<String> consumedBatchIds;
        private RetainedSaved(ConfirmedSource source,RootRuntimeContext context,PhysicalProof physical,
                NativeFreshSnapshotPort.Received first,NativeFreshSnapshotPort.Received second,
                NativeReadinessCollector.SourceQualification qualification,WriterContracts.HistoricalTransition entry,
                List<WriterContracts.Pin> originals,Instant deadline,List<WriterContracts.HistoricalTransition> readHistorySuffix,List<String> consumedBatchIds) {
            this.source=source;this.context=context;this.physical=physical;this.first=first;this.second=second;
            this.qualification=qualification;this.entry=entry;this.originals=originals;this.deadline=deadline;
            this.row=ContinuityJson.parseObject(entry.details(),StrictJson.INPUT_MAX_BYTES);
            this.readHistorySuffix=List.copyOf(readHistorySuffix);this.consumedBatchIds=List.copyOf(consumedBatchIds);
            nextSequence();
        }
        public ConfirmedSource source(){return source;}
        public SessionIdentity session(){return new SessionIdentity(game().machineId(),game().generation(),game().sessionId());}
        public ManagedGameSession game(){return context.game();}
        public NativeFreshSnapshotPort.Received firstRead(){return first;}
        public NativeFreshSnapshotPort.Received secondRead(){return second;}
        public WriterContracts.HistoricalTransition originalEntry(){return entry;}
        public List<WriterContracts.HistoricalTransition> readHistorySuffix(){return readHistorySuffix;}
        public List<String> consumedBatchIds(){return consumedBatchIds;}
        public long nextSequence(){
            if(consumedBatchIds.isEmpty())return 0;
            String id=consumedBatchIds.getLast();int separator=id.lastIndexOf('-');
            StrictJson.require(separator>0,"retained batch has no original prefix/sequence");
            String ordinal=id.substring(separator+1);StrictJson.require(ordinal.matches("0|[1-9][0-9]*"),"retained batch ordinal is not canonical");
            long value=new java.math.BigInteger(ordinal).longValueExact();StrictJson.safe(value,0);
            long next=Math.addExact(value,1);StrictJson.safe(next,0);return next;
        }
        public ExactRef fullDriverReference(){return ExactRef.fromJson(row.get("full_driver"));}
        public ExactRef driverFactsReference(){return ExactRef.fromJson(row.get("driver_facts"));}
        public ExactRef savedStateReference(){return ExactRef.fromJson(row.get("saved_state_reference"));}
        public ExactRef sourceHeadReference(){return ExactRef.fromJson(row.get("source_head_reference"));}
        public long driverVersion(){return StrictJson.integer(row.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER);}
        public long episodeEpoch(){return StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER);}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(context.clock().instant().isBefore(deadline),"retained saved preparation deadline expired");
            game().verify();physical.requireEvidence();qualification.assertCurrent(same);
            requireOriginals(same);requireSavedHistorical(source,context,same,entry,true);source.requireCurrent(same);
            var publication=same.head().state().toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD);
            StrictJson.require(readHistorySuffix.isEmpty()?publication==null||publication.isNull()
                    :ContinuityJson.same(publication,ContinuityJson.parseObject(readHistorySuffix.getLast().details(),ContinuityJson.LEDGER_MAX_BYTES)),
                    "retained preparation acquired another Driver READ after actual capture");
        }
        public void requireRetained(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);game().verify();physical.requireEvidence();
            requireOriginals(same);requireSavedHistorical(source,context,same,entry,false);source.requireRetained(same);
        }
        private void requireOriginals(ContinuityStorePort.Session same)throws IOException {
            for(var pin:originals)same.verifyPin(pin);
            for(var edge:readHistorySuffix) {
                var actual=same.readHistoricalTransition(edge.eventPin());
                StrictJson.require(actual.sequence()==edge.sequence()&&actual.kind().equals(edge.kind())
                        &&actual.eventIdentity().equals(edge.eventIdentity())&&Arrays.equals(actual.details(),edge.details())
                        &&ContinuityJson.same(actual.before().toJson(),edge.before().toJson())
                        &&ContinuityJson.same(actual.after().toJson(),edge.after().toJson()),
                        "retained READ suffix changed its complete original canonical edge");
            }
            NativeFreshSnapshotPort.verifyOriginal(first.acknowledgement(),first.originalFrame(),first.snapshotReceived());
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            requireRaw(source,context,first);requireRaw(source,context,second);
            RestoreCheckpointService.requireStableReadProgression(first.originalFrame(),second.originalFrame());
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
