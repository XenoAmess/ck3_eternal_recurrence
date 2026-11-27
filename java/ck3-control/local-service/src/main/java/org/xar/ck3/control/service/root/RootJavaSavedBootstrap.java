package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.time.Clock;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
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
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
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

    /** Resolves the explicit confirmation only through its own old writer's canonical history. */
    static ConfirmedSource qualifyOriginalConfirmation(RootApplicationAssembly.Core sourceCore, CheckpointFiles files,
            Path materialRoot, String originalPipeName, CheckpointPair pair, ExactRef confirmationReference)throws IOException {
        var confirmation=sourceCore.writer().locked(same->{
            var head=same.head();
            StrictJson.require(!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty(),
                    "old source requires explicit canonical repair");
            Path path=Path.of(confirmationReference.path()).toAbsolutePath().normalize();
            var matches=head.documents().stream().filter(pin->{
                var original=pin.reference();
                return Path.of(original.path()).toAbsolutePath().normalize().equals(path)
                        &&original.bytes()==confirmationReference.bytes()&&original.sha256().equals(confirmationReference.sha256());
            }).toList();
            StrictJson.require(matches.size()==1,"unique actual canonical confirmation Pin required");
            var captured=same.capturePin(matches.getFirst().reference(),MAX_STATE);
            StrictJson.require(captured.equals(matches.getFirst()),"original confirmation identity changed");
            return captured;
        });
        return qualify(sourceCore,files,materialRoot,originalPipeName,pair,confirmation);
    }

    /** Source-only factory. No managed Game, snapshot supplier, SAVE or live issuer is manufactured. */
    public static ConfirmedSource qualify(RootApplicationAssembly.Core sourceCore,CheckpointFiles actualFiles,
            Path materialRoot,String originalPipeName,CheckpointPair pair,WriterContracts.Pin confirmation)throws IOException {
        Objects.requireNonNull(sourceCore);Objects.requireNonNull(actualFiles);Objects.requireNonNull(pair);
        StrictJson.text(originalPipeName);
        var writer=sourceCore.writer();
        var sourceFiles=new PreReadCheckpointFiles(actualFiles);
        var stores=checkpointStores(sourceCore,sourceFiles,materialRoot,originalPipeName,pair);
        var store=stores.materials().ordinaryStore();
        return writer.locked(same->{
            writer.requireSession(same);
            // Pure old-source qualification only; the scope closes before replacement or new READ.
            return sourceCore.archive().inHistoricalReadScope(same,
                    new ActionPorts.HistoricalReadLimits(1024, 64L * 1024 * 1024, 2052), ignoredArchive -> {
                for(var action:ContinuityActionJournal.receipts(same.head().state(),sourceCore.archive().withSession(same)))
                    StrictJson.require(action.settled(),"confirmed saved source cannot erase an unresolved canonical action");
                var actual=store.requalifyConfirmed(same,confirmation,pair);
                var material=actual.requireCurrent(same);
                return new ConfirmedSource(writer,store,actual,material,sourceCore.archive(),stores.drivers(),stores.materials(),sourceFiles);
            });
        });
    }

    record CheckpointStores(DriverCheckpointStore drivers,SavedCheckpointMaterialStore materials) { }

    /** Uses the given real writer/files but the original physical Driver path and pipe. */
    static CheckpointStores checkpointStores(RootApplicationAssembly.Core sourceCore,CheckpointFiles sourceFiles,
            Path materialRoot,String originalPipeName,CheckpointPair pair)throws IOException {
        long target=sourceCore.writer().locked(same->same.head().state().origin().targetDays());
        return checkpointStores(sourceCore,sourceFiles,materialRoot,originalPipeName,Path.of(pair.driver().reference().path()),
                new OriginalWindowReducer.Policy(target));
    }

    static CheckpointStores checkpointStores(RootApplicationAssembly.Core sourceCore,CheckpointFiles sourceFiles,
            Path materialRoot,String originalPipeName,Path driverPath,OriginalWindowReducer.Policy cyclePolicy) {
        var writer=sourceCore.writer();
        var snapshots=new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> unused)throws IOException {
                throw new IOException("confirmed historical source factory cannot publish a Driver or submit SAVE");
            }
        };
        var drivers=new DriverCheckpointStore(sourceFiles,driverPath,originalPipeName,snapshots);
        var saves=new CanonicalSaveReceiptVerifier(writer,sourceCore.actions(),sourceCore.archive(),sourceFiles,drivers);
        var verifier=new CheckpointCommitVerifier(sourceFiles,drivers,
                (same,owner,semantic)->sourceCore.semanticVerifier().verify(same,owner,semantic).materialDigest(),
                writer.originalLockPath(),writer::requireSession,saves);
        var cycles=new OrdinaryCycleTransitions(sourceCore.archive(),sourceCore.semanticVerifier()::verify,
                verifier::verify,cyclePolicy,writer::requireSession);
        cycles.bindTerminalFrameLoader(sourceCore.frameLoader());
        var store=new SavedAttachmentSourceStore(sourceFiles,drivers,verifier,writer::borrowedSession,materialRoot,
                cycles::verifyCompletedCycleProof,cycles::verifyHistoricalCompletedCycleProof);
        var firstVerifier=new org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier(sourceFiles,drivers,
                (same,owner,semantic)->sourceCore.semanticVerifier().verify(same,owner,semantic).materialDigest(),
                writer.originalLockPath(),writer::requireSession,saves);
        var firstStore=new org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore(
                sourceFiles,firstVerifier,writer::borrowedSession,materialRoot.resolve("first"));
        return new CheckpointStores(drivers,new SavedCheckpointMaterialStore(store,firstStore));
    }

    /** Opaque qualification of old original DATA and present files; never a replacement or Ready permit. */
    public static final class ConfirmedSource {
        private final ContinuityWriter writer;
        private final SavedAttachmentSourceStore store;
        private final SavedAttachmentSourceStore.RequalifiedConfirmed qualified;
        private final SavedAttachmentSourceStore.SavedMaterial material;
        private final byte[] savedDriverCanonical;
        private final NativeOutcomeArchive sourceArchive;
        private final DriverCheckpointStore drivers;
        private final org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore materials;
        private final PreReadCheckpointFiles sourceFiles;
        private ConfirmedSource(ContinuityWriter writer,SavedAttachmentSourceStore store,
                SavedAttachmentSourceStore.RequalifiedConfirmed qualified,SavedAttachmentSourceStore.SavedMaterial material,
                NativeOutcomeArchive sourceArchive,DriverCheckpointStore drivers,
                org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore materials,PreReadCheckpointFiles sourceFiles) {
            this.writer=writer;this.store=store;this.qualified=qualified;this.material=material;
            this.savedDriverCanonical=material.savedDriver().encode();
            this.sourceArchive=Objects.requireNonNull(sourceArchive);
            this.drivers=Objects.requireNonNull(drivers);this.materials=Objects.requireNonNull(materials);
            this.sourceFiles=Objects.requireNonNull(sourceFiles);
            StrictJson.require(sourceArchive.writer()==writer,"confirmed source archive must belong to the actual source writer");
        }
        public CheckpointPair pair(){return material.pair();}
        SessionIdentity physicalSaveOwner(){return material.session();}
        DriverStateSnapshot.Complete physicalSavedDriver(){return material.savedDriver();}
        SavedAttachmentSourceStore.SavedMaterial originalMaterial(){return material;}
        <T> T withOriginalWriter(ContinuityStorePort.Session target,SavedAttachmentSourceStore.ImportedSourceWork<T> work)throws IOException {
            return withOriginalArchive(target,(old,archive)->work.read(old));
        }
        @FunctionalInterface interface ArchivedRead<T> {
            T read(ContinuityStorePort.Session old,ActionPorts.OutcomeArchive archive)throws IOException;
        }
        <T> T withOriginalArchive(ContinuityStorePort.Session target,ArchivedRead<T> work)throws IOException {
            return writer.readOnlyFrom(target,old->sourceArchive.inHistoricalReadScope(old,
                    new ActionPorts.HistoricalReadLimits(1024,64L*1024*1024,2052),archive->work.read(old,archive)));
        }
        RootRestoreMaterials.PhysicalSavedOriginal readOriginalPhysicalSave()throws IOException {
            return writer.locked(same->sourceArchive.inHistoricalReadScope(same,
                    new ActionPorts.HistoricalReadLimits(128,64L*1024*1024,260),ignored->
                            RootRestoreMaterials.readOriginalPhysicalSave(same,sourceArchive,materials,material)));
        }
        RootRestoreMaterials.PhysicalSavedOriginal readOriginalPhysicalSave(ContinuityStorePort.Session target)throws IOException {
            return withOriginalWriter(target,old->RootRestoreMaterials.readOriginalPhysicalSave(old,sourceArchive,materials,material));
        }
        /** Package-owned same-writer restore source; this exposes actual issuers, never a replacement or planning permit. */
        DriverCheckpointStore driverCheckpoints(){return drivers;}
        org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore materials(){return materials;}
        org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial material(ContinuityStorePort.Session same)throws IOException {
            writer.requireSession(same);var current=qualified.requireCurrent(same);
            return reuseCurrentMaterial(materials,material,current,savedDriverCanonical);
        }
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
        /** The full unchanged source proof completes before any new native READ begins. */
        private SourcePreReadProof preparePreRead(Clock clock,Instant expiry)throws IOException {
            var checkpoints=sourceFiles.capture(clock,expiry);
            SourcePreReadProof prepared=null;boolean detached=false;
            try{
                prepared=writer.locked(same->{
                    writer.requireSession(same);ExactRef canonical=same.persistedHead();
                    NativeOutcomeArchive.SavedPreReadReadSet<SavedAttachmentSourceStore.SavedMaterial> sealed=null;
                    try{
                        sealed=sourceArchive.sealSavedPreReadHistoryWithComponents(same,
                                new NativeOutcomeArchive.SavedDataReadsetLimits(new ActionPorts.HistoricalReadLimits(8192,256L*1024*1024,16384),16384,8192,256L*1024*1024),clock,expiry,
                                ignored->org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference.inReplayReadScope(
                                        new org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference.ReplayReadLimits(256,256L*1024*1024),
                                        clock,expiry,original->sourceArchive.retainSavedPreReadArmyOriginal(same,original),()->{
                            var current=qualified.requireCurrent(same);
                            StrictJson.require(current.session().equals(material.session())&&current.pair().equals(material.pair())
                                    &&current.witness().equals(material.witness())
                                    &&Arrays.equals(current.savedDriver().encode(),savedDriverCanonical),
                                    "Saved preRead changed its exact source-qualified Driver, pair or material witness");
                            sourceFiles.verify(material.witness());sourceFiles.verify(pair());
                            return current;
                        }));
                        return new SourcePreReadProof(this,sealed,checkpoints,canonical);
                    }catch(IOException|RuntimeException|Error failure){closeAfterFailure(sealed,failure);throw failure;}
                });
                checkpoints.seal();sourceFiles.detach(checkpoints);detached=true;
                prepared.requireCurrent();return prepared;
            }catch(IOException|RuntimeException|Error failure){
                if(!detached)try{sourceFiles.detach(checkpoints);}catch(IOException cleanup){failure.addSuppressed(cleanup);}
                closeAfterFailure(prepared,failure);closeAfterFailure(checkpoints,failure);throw failure;
            }
        }

    }


    /** Exact raw-byte SHA-256 DATA; no checkpoint issuer or eligibility is created. */
    private static String checkpointSha256(byte[] raw) {
        try {
            return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
        } catch (java.security.NoSuchAlgorithmException impossible) {
            throw new IllegalStateException(impossible);
        }
    }

    private static void rethrowCloseFailure(Throwable failure)throws IOException {
        if(failure instanceof IOException problem)throw problem;
        if(failure instanceof RuntimeException problem)throw problem;
        if(failure instanceof Error problem)throw problem;
        if(failure!=null)throw new IOException("Saved custody cleanup failed",failure);
    }

    private static void closeAfterFailure(AutoCloseable custody,Throwable primary) {
        if(custody!=null)try{custody.close();}catch(Exception|Error cleanup){if(cleanup!=primary)primary.addSuppressed(cleanup);}
    }

    /** Captures every real checkpoint read while the unchanged historical proof runs. */
    private static final class PreReadCheckpointFiles implements CheckpointFiles {
        private final CheckpointFiles actual;
        private final ThreadLocal<CheckpointReadSet> active=new ThreadLocal<>();
        private PreReadCheckpointFiles(CheckpointFiles actual){this.actual=Objects.requireNonNull(actual);}
        private CheckpointReadSet capture(Clock clock,Instant expiry)throws IOException {
            if(active.get()!=null)throw new IOException("Saved checkpoint capture cannot nest");
            var captured=new CheckpointReadSet(this,clock,expiry);active.set(captured);return captured;
        }
        private void detach(CheckpointReadSet captured)throws IOException {
            if(active.get()!=captured)throw new IOException("Saved checkpoint capture lost its exact issuer");
            active.remove();
        }
        private void failed(Throwable failure) {
            var captured=active.get();if(captured!=null)captured.recordFailure(failure);
        }
        private void retain(CheckpointPair.FileWitness witness)throws IOException {
            var captured=active.get();if(captured!=null)captured.retain(witness);
        }
        @Override public java.util.Optional<CheckpointPair.FileWitness> observe(Path path)throws IOException {
            try{
                var result=actual.observe(path);var captured=active.get();
                if(captured!=null){
                    if(result.isEmpty())throw captured.fail(new IOException("Saved preRead has an unheld absent checkpoint dependency"));
                    captured.retain(result.orElseThrow());
                }
                return result;
            }catch(IOException|RuntimeException|Error failure){failed(failure);throw failure;}
        }
        @Override public byte[] read(CheckpointPair.FileWitness expected,int maximum)throws IOException {
            try{
                retain(expected);byte[] raw=actual.read(expected,maximum);
                if(raw.length!=expected.reference().bytes()
                        ||!checkpointSha256(raw).equals(expected.reference().sha256()))
                    throw new IOException("Saved preRead checkpoint producer returned different original bytes");
                return raw;
            }catch(IOException|RuntimeException|Error failure){failed(failure);throw failure;}
        }
        @Override public void verify(CheckpointPair.FileWitness expected)throws IOException {
            try{retain(expected);actual.verify(expected);}
            catch(IOException|RuntimeException|Error failure){failed(failure);throw failure;}
        }
        @Override public void verify(CheckpointPair pair)throws IOException {verify(pair.save());verify(pair.driver());}
        private void requireNoCaptureWrites()throws IOException {
            var captured=active.get();
            if(captured!=null)throw captured.fail(new IOException("Saved historical preRead cannot publish checkpoint material"));
        }
        @Override public CheckpointPair.FileWitness replace(Path target,byte[] bytes)throws IOException {
            requireNoCaptureWrites();return actual.replace(target,bytes);
        }
        @Override public CheckpointPair.FileWitness createNew(Path target,byte[] bytes)throws IOException {
            requireNoCaptureWrites();return actual.createNew(target,bytes);
        }
        @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source,Path target)throws IOException {
            requireNoCaptureWrites();return actual.copyNew(source,target);
        }
        // The transparent adapter deliberately routes every proof read through this actual capture.
        @Override public Verification beginVerification(CheckpointPair pair)throws IOException {
            return CheckpointFiles.super.beginVerification(pair);
        }
    }

    /** Independent OS handles survive the old Session, never its mutable scope or a byte-only cache. */
    private static final class CheckpointReadSet implements AutoCloseable {
        private static final int MAXIMUM_FILES=256;
        private static final long MAXIMUM_BYTES=256L<<20;
        private static final BigInteger UNIX_EPOCH_FILETIME=new BigInteger("116444736000000000");
        private final PreReadCheckpointFiles issuer;
        private final Thread thread=Thread.currentThread();
        private final Clock clock;
        private final Instant expiry;
        private final Map<ExactRef,HeldCheckpoint> held=new LinkedHashMap<>();
        private long bytes;
        private boolean sealed;
        private volatile boolean closed;
        private volatile Throwable firstFailure;
        private Throwable closeFailure;
        private synchronized void recordFailure(Throwable failure){if(firstFailure==null)firstFailure=failure;}
        private CheckpointReadSet(PreReadCheckpointFiles issuer,Clock clock,Instant expiry)throws IOException {
            this.issuer=issuer;this.clock=Objects.requireNonNull(clock);this.expiry=Objects.requireNonNull(expiry);live();
        }
        private IOException fail(IOException failure){recordFailure(failure);return failure;}
        private void live()throws IOException {
            if(Thread.currentThread()!=thread||closed||firstFailure!=null||!clock.instant().isBefore(expiry))
                throw fail(new IOException("Saved checkpoint readset lost its original thread, lifetime or finite expiry",firstFailure));
        }
        private void retain(CheckpointPair.FileWitness witness)throws IOException {
            try{
                live();if(sealed||issuer.active.get()!=this)throw new IOException("Saved checkpoint dependency arrived after sealing");
                var prior=held.get(witness.reference());
                if(prior!=null){prior.requireCurrent(witness);return;}
                long size=witness.reference().bytes();
                if(size<1||size>MAXIMUM_BYTES-bytes||held.size()>=MAXIMUM_FILES)
                    throw new IOException("Saved checkpoint readset exceeds its finite physical custody bounds");
                var lease=IdentityBearingFileAttributes.leaseBoundedWindows(Path.of(witness.reference().path()),Math.toIntExact(size));
                boolean kept=false;Throwable failure=null;
                try{
                    var original=lease.originalRead();
                    String sha=checkpointSha256(original.bytes());
                    var captured=new HeldCheckpoint(witness,lease,sha);captured.requireCurrent(witness);
                    lease.releaseOriginalBytes();held.put(witness.reference(),captured);bytes=Math.addExact(bytes,size);kept=true;
                }catch(IOException|RuntimeException|Error problem){failure=problem;throw problem;}
                finally{if(!kept)try{lease.close();}catch(IOException|RuntimeException|Error cleanup){
                    if(failure!=null)failure.addSuppressed(cleanup);else throw cleanup;}}
            }catch(IOException failure){throw fail(failure);}
            catch(RuntimeException|Error failure){recordFailure(failure);throw failure;}
        }
        private void seal()throws IOException {
            live();if(sealed||issuer.active.get()!=this||held.isEmpty())throw fail(new IOException("Saved checkpoint readset was not actually captured"));
            requireCurrent(false);sealed=true;
        }
        private void requireCurrent()throws IOException {requireCurrent(true);}
        private void requireCurrent(boolean requireSealed)throws IOException {
            try{
                live();if(requireSealed&&!sealed)throw new IOException("Saved checkpoint readset is not sealed");
                for(var entry:held.values())entry.requireCurrent(entry.expected);
                live();
            }catch(IOException failure){throw fail(failure);}
            catch(RuntimeException|Error failure){recordFailure(failure);throw failure;}
        }
        @Override public void close()throws IOException {
            if(closed){if(closeFailure!=null)throw new IOException("Saved custody cleanup remains unconfirmed",closeFailure);return;}
            if(Thread.currentThread()!=thread)throw fail(new IOException("Saved checkpoint readset close crossed its owner thread"));
            Throwable failure=null;
            for(var entry:new ArrayList<>(held.values()).reversed())try{entry.lease.close();}
            catch(IOException|RuntimeException|Error cleanup){if(failure==null)failure=cleanup;else if(cleanup!=failure)failure.addSuppressed(cleanup);}
            held.clear();closeFailure=failure;if(failure!=null)recordFailure(failure);closed=true;
            rethrowCloseFailure(closeFailure);
        }
        private static final class HeldCheckpoint {
            private final CheckpointPair.FileWitness expected;
            private final IdentityBearingFileAttributes.ReadOnlyLease lease;
            private final String sha;
            private HeldCheckpoint(CheckpointPair.FileWitness expected,IdentityBearingFileAttributes.ReadOnlyLease lease,String sha){
                this.expected=expected;this.lease=lease;this.sha=sha;
            }
            private void requireCurrent(CheckpointPair.FileWitness supplied)throws IOException {
                if(!expected.equals(supplied))throw new IOException("Saved checkpoint dependency changed its original witness");
                Path path=Path.of(expected.reference().path());SharedSourceFiles.plainAncestors(path);
                SharedSourceFiles.NativeFile current=SharedSourceFiles.nativeFile(path);lease.verifyCurrent();
                String nanos=new BigInteger(current.lastWriteFiletimeDecimal()).subtract(UNIX_EPOCH_FILETIME)
                        .multiply(BigInteger.valueOf(100)).toString();
                var projected=new CheckpointPair.FileWitness(new ExactRef(expected.reference().path(),current.logicalBytes(),sha),
                        new FileStatIdentity(BigInteger.valueOf(current.logicalBytes()),current.fileIdDecimal(),nanos));
                if(!projected.equals(expected))throw new IOException("Saved checkpoint HANDLE/path/identity or original hash changed");
            }
        }
    }

    /** Private source issuer plus independently held archive and checkpoint closures, with no old Session retained. */
    private static final class SourcePreReadProof implements AutoCloseable {
        private final ConfirmedSource source;
        private final NativeOutcomeArchive.SavedPreReadReadSet<SavedAttachmentSourceStore.SavedMaterial> archive;
        private final CheckpointReadSet checkpoints;
        private final ExactRef canonicalHead;
        private final Thread thread=Thread.currentThread();
        private volatile boolean closed;
        private volatile Throwable firstFailure;
        private Throwable closeFailure;
        private synchronized void recordFailure(Throwable failure){if(firstFailure==null)firstFailure=failure;}
        private SourcePreReadProof(ConfirmedSource source,
                NativeOutcomeArchive.SavedPreReadReadSet<SavedAttachmentSourceStore.SavedMaterial> archive,
                CheckpointReadSet checkpoints,ExactRef canonicalHead){
            this.source=source;this.archive=archive;this.checkpoints=checkpoints;this.canonicalHead=canonicalHead;
        }
        private void requireSourceSession(ContinuityStorePort.Session same)throws IOException {
            if(closed||firstFailure!=null)throw new IOException("Saved source preRead custody is closed or already failed",firstFailure);
            source.writer.requireSession(same);
            StrictJson.require(canonicalHead.equals(same.persistedHead()),"Saved preRead source canonical head changed");
            archive.requireCurrent(source.sourceArchive,same);checkpoints.requireCurrent();
            StrictJson.require(canonicalHead.equals(same.persistedHead()),"Saved source changed during retained physical revalidation");
        }
        private void requireCurrent()throws IOException {
            try{source.writer.locked(same->{requireSourceSession(same);return null;});}
            catch(IOException|RuntimeException|Error failure){recordFailure(failure);throw failure;}
        }
        private void requireCurrent(ContinuityStorePort.Session newSame)throws IOException {
            try{source.writer.readOnlyFrom(newSame,same->{requireSourceSession(same);return null;});}
            catch(IOException|RuntimeException|Error failure){recordFailure(failure);throw failure;}
        }
        @Override public void close()throws IOException {
            if(closed){if(closeFailure!=null)throw new IOException("Saved custody cleanup remains unconfirmed",closeFailure);return;}
            if(Thread.currentThread()!=thread){
                var failure=new IOException("Saved source custody close crossed its owner thread");
                recordFailure(failure);throw failure;
            }
            Throwable failure=null;
            try{archive.close();}catch(IOException|RuntimeException|Error problem){failure=problem;}
            try{checkpoints.close();}catch(IOException|RuntimeException|Error problem){if(failure==null)failure=problem;else if(failure!=problem)failure.addSuppressed(problem);}
            closeFailure=failure;if(failure!=null)recordFailure(failure);closed=true;
            rethrowCloseFailure(closeFailure);
        }
    }

    /** The new managed creator, two genuine independent READs and the exact new writer are all required. */
    public static Admission admit(ConfirmedSource source,RootRuntimeContext context,JavaGameLifecycle creator,
            JavaGameLifecycle.Started started,Instant deadline)throws IOException,InterruptedException {
        return admit(source,context,creator,started,deadline,null);
    }
    /** Explicit mapped path binds policy to the actual retained Native source/clone custody. */
    public static Admission admit(ConfirmedSource source,RootRuntimeContext context,JavaGameLifecycle creator,
            JavaGameLifecycle.Started started,Instant deadline,org.xar.ck3.control.application.driver.InitialEpisodePolicy policy)throws IOException,InterruptedException {
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
        if(policy!=null)try{policy.requireInitialSavedProjection(game.launchPlan(),source.pair().save(),actual.savedClone());}
        catch(IOException|RuntimeException|Error problem){try{actual.close();}catch(IOException closing){problem.addSuppressed(closing);}throw problem;}
        return completeAdmission(source,context,proof(actual),deadline);
    }

    public static Admission admitLoaded(ConfirmedSource source,RootRuntimeContext context,RootProcessAttach.LoadedCustody actual,
            Instant deadline)throws IOException,InterruptedException {
        return admitLoaded(source,context,actual,deadline,null);
    }
    public static Admission admitLoaded(ConfirmedSource source,RootRuntimeContext context,RootProcessAttach.LoadedCustody actual,
            Instant deadline,org.xar.ck3.control.application.driver.InitialEpisodePolicy policy)throws IOException,InterruptedException {
        Objects.requireNonNull(source);Objects.requireNonNull(context);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
        var game=context.game();
        if(policy!=null)policy.requireInitialSavedProjection(game.launchPlan(),source.pair().save(),actual.savedClone());
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
        void requireInitialClone()throws IOException;
        void releasePreparation()throws IOException;
        @Override void close()throws IOException;
    }
    /** Pre-live physical DATA only; never reopens owner preparation or extends a Game deadline. */
    private static void requireInitialClone(NativeLaunchPlan same,CheckpointPair.FileWitness original,
            org.xar.ck3.control.platform.NativeSavedGameClone.Observation actual)throws IOException {
        Objects.requireNonNull(actual).requireCurrent(same,original);
    }
    private static PhysicalProof proof(RootProcessAttach.Custody actual) {
        return new PhysicalProof() {
            public void requireCurrent()throws IOException{actual.requireCurrent();}
            public void requireEvidence()throws IOException{actual.requireEvidence();}
            public void requireInitialClone()throws IOException{RootJavaSavedBootstrap.requireInitialClone(actual.game().launchPlan(),actual.pair().save(),actual.savedClone());}
            public void releasePreparation()throws IOException{actual.releasePreparation();}
            public void close()throws IOException{actual.close();}
        };
    }
    private static PhysicalProof proof(RootProcessAttach.LoadedCustody actual) {
        return new PhysicalProof() {
            public void requireCurrent()throws IOException{actual.requireCurrent();}
            public void requireEvidence()throws IOException{actual.requireEvidence();}
            public void requireInitialClone()throws IOException{RootJavaSavedBootstrap.requireInitialClone(actual.game().launchPlan(),actual.pair().save(),actual.savedClone());}
            public void releasePreparation()throws IOException{actual.releasePreparation();}
            public void close()throws IOException{actual.close();}
        };
    }
    private static Admission completeAdmission(ConfirmedSource source,RootRuntimeContext context,PhysicalProof physical,
            Instant deadline)throws IOException,InterruptedException {
        SourcePreReadProof preRead=null;
        try {
            preRead=source.preparePreRead(context.clock(),deadline);var sourceProof=preRead;
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
            sourceProof.requireCurrent();physical.requireCurrent();
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
                return new Admission(source,context,physical,sourceProof,first,second,qualification,head,savedState,sourceHead,List.copyOf(pins),deadline);
            });
        }catch(IOException|RuntimeException|Error|InterruptedException failure) {
            closeAfterFailure(preRead,failure);closeAfterFailure(physical,failure);throw failure;
        }
    }

    /** Private new-daemon capability, with separate precommit and retained actual-entry phases. */
    public static final class Admission implements AutoCloseable {
        private final ConfirmedSource source;
        private final RootRuntimeContext context;
        private final PhysicalProof physical;
        private final SourcePreReadProof sourceProof;
        private final NativeFreshSnapshotPort.Received first,second;
        private final NativeReadinessCollector.SourceQualification qualification;
        private final WriterContracts.Head before;
        private final ExactRef savedState,sourceHead;
        private final List<WriterContracts.Pin> originals;
        private final Instant deadline;
        private WriterContracts.Prepared prepared;
        private WriterContracts.Receipt receipt;
        private Admission(ConfirmedSource source,RootRuntimeContext context,PhysicalProof physical,SourcePreReadProof sourceProof,
                NativeFreshSnapshotPort.Received first,NativeFreshSnapshotPort.Received second,
                NativeReadinessCollector.SourceQualification qualification,WriterContracts.Head before,
                ExactRef savedState,ExactRef sourceHead,List<WriterContracts.Pin> originals,Instant deadline) {
            this.source=source;this.context=context;this.physical=physical;this.sourceProof=sourceProof;this.first=first;this.second=second;
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
            requireOriginals(same);sourceProof.requireCurrent(same);physical.requireCurrent();
            physical.releasePreparation();prepared=actual;receipt=committed;
        }
        public synchronized void requireRetained(ContinuityStorePort.Session same,WriterContracts.Receipt committed)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(receipt!=null&&committed==receipt&&prepared!=null,"saved admission lacks its exact actual committed entry");
            same.requireCommitted(prepared,receipt);game().verify();physical.requireEvidence();requireOriginals(same);source.requireRetained(same);
        }
        /** Closed projection custody never falls back to the legacy full-history methods. */
        public synchronized void requireProjectionCurrent(ContinuityStorePort.Session same,WriterContracts.Receipt expected)throws IOException {
            context.writer().requireSession(same);
            if(expected==null) {
                StrictJson.require(receipt==null&&before.digest().equals(same.head().digest())
                        &&context.clock().instant().isBefore(deadline),"Saved projection escaped its exact unconsumed precommit point");
                physical.requireCurrent();qualification.assertCurrent(same);requireOriginals(same);
            } else {
                StrictJson.require(receipt!=null&&expected==receipt&&prepared!=null,"Saved projection lacks its exact actual committed entry");
                same.requireCommitted(prepared,receipt);game().verify();physical.requireEvidence();physical.requireInitialClone();requireOriginals(same);
            }
            sourceProof.requireCurrent(same);
        }
        /** Destruction only; callable after writer failure and never grants retained/live eligibility. */
        public void closeProjectionCustody()throws IOException {sourceProof.close();}
        @Override public void close()throws IOException {closeProjectionCustody();}
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
        var physical=proof(actual);SourcePreReadProof preRead=null;
        try {
            preRead=source.preparePreRead(context.clock(),bounded);var sourceProof=preRead;
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
            sourceProof.requireCurrent();physical.requireCurrent();
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
                var retained=new RetainedSaved(source,context,physical,sourceProof,first,second,qualification,entry,List.copyOf(pins),bounded,
                        suffix.reads(),head.state().status()==ContinuityState.Status.REPAIR_REQUIRED
                                ?List.of(StrictJson.text(ContinuityJson.object(head.state().toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).get("batch_id"))):List.of());
                retained.requirePreparedProjectionCurrent(same);physical.releasePreparation();return retained;
            });
        }catch(IOException|RuntimeException|Error|InterruptedException failure) {
            closeAfterFailure(preRead,failure);closeAfterFailure(physical,failure);throw failure;
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

    /** Consumes the actual current result from the immediately preceding full physical producer call. DATA only. */
    static SavedAttachmentSourceStore.SavedMaterial reuseCurrentMaterial(
            org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore materials,
            SavedAttachmentSourceStore.SavedMaterial original,SavedAttachmentSourceStore.SavedMaterial current,byte[] savedDriverCanonical) {
        materials.requireOwn(original);materials.requireOwn(current);
        StrictJson.require(current.session().equals(original.session())&&current.pair().equals(original.pair())
                        &&current.witness().equals(original.witness())
                        &&current.originalHeadDigest().equals(original.originalHeadDigest())
                        &&current.checkpointDigest().equals(original.checkpointDigest())
                        &&Arrays.equals(current.savedDriver().encode(),savedDriverCanonical),
                "same-writer saved source changed its private original material");
        return original;
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
        requireSavedSourceOriginals(source,context.archive(),same,row);
        for(String field:List.of("full_driver","driver_facts"))
            context.archive().readArtifact(same,ExactRef.fromJson(row.get(field)),WriterContracts.MAX_PIN_BYTES);
        return row;
    }

    /** Relates the exact target marker to DATA requalified by the independent physical SAVE writer. */
    static void requireSavedSourceOriginals(ConfirmedSource source,NativeOutcomeArchive archive,
            ContinuityStorePort.Session same,ObjectNode row)throws IOException {
        var savedRef=ExactRef.fromJson(row.get("saved_state_reference"));
        var headRef=ExactRef.fromJson(row.get("source_head_reference"));
        var input=new SavedContinuityBootstrap.Input(source.savedState(),savedRef,
                source.confirmation().eventPin().reference(),source.sourceHead(),headRef,CheckpointPairCodec.encode(source.pair()),
                ContinuityJson.canonical(row.get("session")),ContinuityJson.canonical(row.get("opening")),
                ExactRef.fromJson(row.get("full_driver")),ExactRef.fromJson(row.get("driver_facts")),
                StrictJson.integer(row.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER));
        StrictJson.require(ContinuityJson.same(row,SavedContinuityBootstrap.details(
                input,StrictJson.text(row.get("evidence_id")),row.get("source"))),"retained saved source details differ from qualified source");
        StrictJson.require(Arrays.equals(ContinuityJson.canonical(source.savedState().toJson()),archive.readArtifact(same,savedRef,MAX_STATE))
                &&Arrays.equals(ContinuityJson.canonical(source.sourceHead().toJson()),archive.readArtifact(same,headRef,MAX_STATE)),
                "retained saved archived source snapshots differ from actual old states");
    }

    /** A new private read qualification for an actual previously committed saved entry. */
    public static final class RetainedSaved implements org.xar.ck3.control.application.session.ContinuityBatchJournal.SavedReadOnlyRecoverySource,AutoCloseable {
        private final ConfirmedSource source;
        private final RootRuntimeContext context;
        private final PhysicalProof physical;
        private final SourcePreReadProof sourceProof;
        private final NativeFreshSnapshotPort.Received first,second;
        private final NativeReadinessCollector.SourceQualification qualification;
        private final WriterContracts.HistoricalTransition entry;
        private final List<WriterContracts.Pin> originals;
        private final Instant deadline;
        private final ObjectNode row;
        private final List<WriterContracts.HistoricalTransition> readHistorySuffix;
        private final List<String> consumedBatchIds;
        private RetainedSaved(ConfirmedSource source,RootRuntimeContext context,PhysicalProof physical,SourcePreReadProof sourceProof,
                NativeFreshSnapshotPort.Received first,NativeFreshSnapshotPort.Received second,
                NativeReadinessCollector.SourceQualification qualification,WriterContracts.HistoricalTransition entry,
                List<WriterContracts.Pin> originals,Instant deadline,List<WriterContracts.HistoricalTransition> readHistorySuffix,List<String> consumedBatchIds) {
            this.source=source;this.context=context;this.physical=physical;this.sourceProof=sourceProof;this.first=first;this.second=second;
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
        public void requireProjectionCurrent(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);game().verify();physical.requireEvidence();physical.requireInitialClone();
            requireOriginals(same);requireSavedHistorical(source,context,same,entry,false);sourceProof.requireCurrent(same);
        }
        /** Preserve the original deadline and unconsumed READ-suffix publication cut before adoption. */
        public void requirePreparedProjectionCurrent(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(context.clock().instant().isBefore(deadline),"retained Saved projection preparation deadline expired");
            game().verify();physical.requireEvidence();physical.requireInitialClone();qualification.assertCurrent(same);
            requireOriginals(same);requireSavedHistorical(source,context,same,entry,true);sourceProof.requireCurrent(same);
            var publication=same.head().state().toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD);
            StrictJson.require(readHistorySuffix.isEmpty()?publication==null||publication.isNull()
                    :ContinuityJson.same(publication,ContinuityJson.parseObject(readHistorySuffix.getLast().details(),ContinuityJson.LEDGER_MAX_BYTES)),
                    "retained projection acquired another Driver READ after actual capture");
        }
        /** Journal recovery consumes this retained object's actual preRead custody, never a synthetic source. */
        public org.xar.ck3.control.application.session.ContinuityBatchJournal.SavedReadOnlyRecoverySource projectionRecoverySource() {
            return new org.xar.ck3.control.application.session.ContinuityBatchJournal.SavedReadOnlyRecoverySource() {
                @Override public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
                    requirePreparedProjectionCurrent(same);
                }
                @Override public WriterContracts.HistoricalTransition originalEntry(){return RetainedSaved.this.originalEntry();}
                @Override public List<WriterContracts.HistoricalTransition> readHistorySuffix(){return RetainedSaved.this.readHistorySuffix();}
                @Override public List<String> consumedBatchIds(){return RetainedSaved.this.consumedBatchIds();}
            };
        }
        public void closeProjectionCustody()throws IOException {sourceProof.close();}
        @Override public void close()throws IOException {closeProjectionCustody();}
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
