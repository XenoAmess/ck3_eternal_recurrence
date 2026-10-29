package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.OriginalLegacyResume;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.service.root.RootFrozenRunProfile.FrozenRunProfile;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Reads the original runtime's one existing Driver/WAL pair under the original writer. Never submits, persists or consolidates. */
public final class RootOriginalDriverJournal {
    public enum Status { MISSING,BASE_ONLY,ALREADY_CONSOLIDATED,REPLAYED,JOURNAL_INVALID }
    public enum ManagedQueueStatus { MISSING,PRESENT,FAILED }
    public enum ManagedQueueReadIssue { FILE_READ_FAILED,INVALID_RESPONSE,RESOURCE_LIMIT }
    /** Original presence and normalized DATA only. No branch is a restore or fixture permission. */
    public sealed interface PersistedLifecycle permits MissingLegacyLifecycle,BoundPersistedLifecycle,ExplicitNullLifecycle { }
    public record MissingLegacyLifecycle() implements PersistedLifecycle { }
    public record BoundPersistedLifecycle(SuccessionLifecycleBinding binding) implements PersistedLifecycle {
        public BoundPersistedLifecycle {Objects.requireNonNull(binding);}
    }
    public record ExplicitNullLifecycle() implements PersistedLifecycle { }
    /** Pure reader used by the actual private load; null never goes through the ordinary object codec. */
    public static PersistedLifecycle readPersistedLifecycle(ObjectValue payload)throws IOException {
        Objects.requireNonNull(payload);
        if(!payload.contains("succession_lifecycle"))return new MissingLegacyLifecycle();
        var original=payload.get("succession_lifecycle");
        if(original instanceof org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.NullValue)
            return new ExplicitNullLifecycle();
        try{return new BoundPersistedLifecycle(SuccessionLifecycleCodec.decode(
                OriginalDriverJournal.canonical(original,SuccessionLifecycleCodec.MAX_BYTES).bytes()));}
        catch(IllegalArgumentException invalid){throw new IOException("original persisted lifecycle is malformed",invalid);}
    }
    /** Complete response reading is finite. Oversized or strictly rejected legacy JSON stays PRESENT. */
    public static final int MAXIMUM_QUEUE_RESPONSE_BYTES=64*1024*1024;
    private record QueueDirectory(Path path,Optional<SharedSourceFiles.DirectoryIdentity> identity) { }
    /** Actual read-only queue facts, privately retained by the original Driver issuer. Not a restore or disarm permission. */
    public static final class ManagedQueueObservation {
        private final OriginalJournalLoad original;private final Session scope;private final String requestId;
        private final ManagedQueueStatus status;private final List<QueueDirectory> directories;
        private final Optional<Inventory> inbox;private final Inventory outbox;private final Optional<SharedSourceFiles.Witness> response;
        private final Optional<ManagedQueueReadIssue> readIssue;
        private final Optional<String> readErrorType;
        private ManagedQueueObservation(OriginalJournalLoad original,Session scope,String requestId,ManagedQueueStatus status,
                List<QueueDirectory> directories,Optional<Inventory> inbox,Inventory outbox,
                Optional<SharedSourceFiles.Witness> response,Optional<ManagedQueueReadIssue> readIssue,Optional<String> readErrorType) {
            this.original=original;this.scope=scope;this.requestId=requestId;this.status=status;
            this.directories=List.copyOf(directories);this.inbox=inbox;this.outbox=outbox;
            this.response=response;this.readIssue=readIssue;this.readErrorType=readErrorType;
        }
        public ManagedQueueStatus status(){return status;}
        public String requestId(){return requestId;}
        public Optional<ManagedQueueReadIssue> readIssue(){return readIssue;}
        public Optional<String> readErrorType(){return readErrorType;}
        /** Immutable queue DATA identity across scopes. A matching digest grants no source, commit or restore authority. */
        public String identityDigest() {
            var row=StrictJson.object();row.put("schema","xar.java-original-managed-queue-identity/v1");
            row.put("request_id",requestId);row.put("status",status.name());
            var directoriesJson=row.putArray("directories");
            directories.stream().sorted(java.util.Comparator.comparing(value->value.path().toString())).forEach(value->{
                var entry=directoriesJson.addObject();entry.put("path",value.path().toString());
                if(value.identity().isEmpty())entry.putNull("identity");
                else {
                    var identity=value.identity().orElseThrow();var nativeIdentity=entry.putObject("identity");
                    nativeIdentity.put("volume_serial",identity.volumeSerialDecimal());
                    nativeIdentity.put("file_id",identity.fileIdDecimal());nativeIdentity.put("creation_filetime",identity.creationFiletimeDecimal());
                }
            });
            row.put("inbox_checked",inbox.isPresent());
            if(inbox.isPresent())row.set("inbox",inventoryIdentity(inbox.orElseThrow()));else row.putNull("inbox");
            row.set("outbox",inventoryIdentity(outbox));
            if(response.isPresent()) {
                var witness=response.orElseThrow();var content=row.putObject("response");var source=witness.source();
                content.set("reference",new ExactRef(source.path(),source.bytes(),source.sha256()).toJson());
                content.set("native_file",nativeIdentity(witness.nativeFile()));
            } else row.putNull("response");
            if(readIssue.isPresent())row.put("read_issue",readIssue.orElseThrow().name());else row.putNull("read_issue");
            if(readErrorType.isPresent())row.put("read_error_type",readErrorType.orElseThrow());else row.putNull("read_error_type");
            var originals=row.putArray("original_inputs");
            original.originalReferences().stream().sorted(java.util.Comparator.comparing(ExactRef::path)
                    .thenComparing(ExactRef::sha256).thenComparingLong(ExactRef::bytes)).forEach(ref->originals.add(ref.toJson()));
            return OriginalDriverJournal.sha256(StrictJson.canonical(row));
        }
        public Optional<ExactRef> originalResponse(){return response.map(value->{var ref=value.source();return new ExactRef(ref.path(),ref.bytes(),ref.sha256());});}
        public List<ExactRef> originalReferences(){var refs=new ArrayList<>(original.originalReferences());originalResponse().ifPresent(refs::add);return List.copyOf(refs);}
        public void requireCurrent(Session same,OriginalJournalLoad identical)throws IOException {
            if(identical!=original||same!=scope)throw new IOException("managed queue facts crossed their private original Driver or writer scope");
            original.requireRetained(same);original.issuer.requireQueueSource(same);
            for(var directory:directories)if(!queueDirectory(directory.path()).equals(directory))throw new IOException("original lifecycle queue directory identity or presence changed");
            if(inbox.isPresent())requireInventory(inbox.orElseThrow());requireInventory(outbox);
            if(response.isPresent())SharedSourceFiles.assertUnchanged(response.orElseThrow());
            original.requireRetained(same);
        }
        /** Physical input custody after the actual original-resume commit; never a replacement for the old-head guard. */
        public void requireCommittedInputs(Session same,OriginalJournalLoad identical,WriterContracts.Prepared transition,
                WriterContracts.Receipt receipt)throws IOException {
            if(identical!=original||same!=scope)throw new IOException("committed queue inputs crossed their original Driver or writer scope");
            original.requireCommittedInputs(same,transition,receipt);
            var delta=committedDelta(transition);
            if(delta.managedQueue().isEmpty()||!delta.originalInputs().containsAll(originalReferences()))
                throw new IOException("actual resume commit does not retain this complete original queue input closure");
            original.issuer.requireQueueSource(same);
            for(var directory:directories)if(!queueDirectory(directory.path()).equals(directory))throw new IOException("committed lifecycle queue directory identity or presence changed");
            if(inbox.isPresent())requireInventory(inbox.orElseThrow());requireInventory(outbox);
            if(response.isPresent())SharedSourceFiles.assertUnchanged(response.orElseThrow());
            original.requireCommittedInputs(same,transition,receipt);
        }
    }

    /** Source-defined Python layout: state_dir/native-session/bridge/{inbox,outbox}/{request_id}.json. No queue is created or written. */
    public static ManagedQueueObservation probeManagedQueue(Session same,OriginalJournalLoad original,String actualRequestId)throws IOException {
        Objects.requireNonNull(original);original.requireRetained(same);original.issuer.requireQueueSource(same);
        var marker=original.fullPayload().get("managed_restore_transaction");
        if(!(marker instanceof ObjectValue transaction)||actualRequestId==null
                ||!OriginalDriverJournal.textEquals(transaction.get("request_id"),actualRequestId))
            throw new IOException("queue request ID must be the retained original managed-restore marker");
        // The legacy normalizer requires restore-; unsafe path components cannot become a physical absence fact.
        if(!actualRequestId.matches("restore-[A-Za-z0-9_.-]{1,240}")||actualRequestId.endsWith(".")||actualRequestId.endsWith(" "))
            throw new IOException("original lifecycle request ID is outside the safe single-file legacy layout");
        var issuer=original.issuer;Path state=issuer.plan.stateDirectory(),session=state.resolve("native-session"),queue=session.resolve("bridge");
        var directories=new ArrayList<QueueDirectory>();
        for(Path path:List.of(state,session,queue,queue.resolve("outbox")))directories.add(queueDirectory(path));
        Inventory outbox=inventory(queue.resolve("outbox").resolve(actualRequestId+".json"));
        Optional<Inventory> inbox=Optional.empty();
        ManagedQueueStatus status;Optional<SharedSourceFiles.Witness> response=Optional.empty();
        Optional<ManagedQueueReadIssue> issue=Optional.empty();Optional<String> error=Optional.empty();
        if(outbox.nativeFile().isEmpty()) {
            directories.add(queueDirectory(queue.resolve("inbox")));
            inbox=Optional.of(inventory(queue.resolve("inbox").resolve(actualRequestId+".json")));
            status=inbox.orElseThrow().nativeFile().isPresent()?ManagedQueueStatus.PRESENT:ManagedQueueStatus.MISSING;
        }
        else {
            status=ManagedQueueStatus.PRESENT;
            long size=outbox.nativeFile().orElseThrow().logicalBytes();
            if(size>MAXIMUM_QUEUE_RESPONSE_BYTES)issue=Optional.of(ManagedQueueReadIssue.RESOURCE_LIMIT);
            else {
                byte[] raw=null;
                // Only the actual outbox file read is Python's soft OSError -> PRESENT branch.
                try(var stream=Files.newInputStream(outbox.path())){raw=stream.readNBytes(MAXIMUM_QUEUE_RESPONSE_BYTES+1);}
                catch(IOException unreadable){issue=Optional.of(ManagedQueueReadIssue.FILE_READ_FAILED);error=Optional.of(unreadable.getClass().getName());}
                if(raw!=null) {
                    if(raw.length!=size||raw.length>MAXIMUM_QUEUE_RESPONSE_BYTES)throw new IOException("original lifecycle response changed during complete read");
                    requireInventory(outbox);
                    var witness=SharedSourceFiles.observe(outbox.path());
                    if(witness.source().bytes()!=size||!witness.source().sha256().equals(OriginalDriverJournal.sha256(raw)))
                        throw new IOException("original lifecycle response bytes differ from their retained source");
                    response=Optional.of(witness);
                    try {
                        // Python reads utf-8-sig. A BOM is accepted only at the beginning of the actual file.
                        int offset=raw.length>=3&&(raw[0]&255)==239&&(raw[1]&255)==187&&(raw[2]&255)==191?3:0;
                        byte[] json=java.util.Arrays.copyOfRange(raw,offset,raw.length);
                        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(json));
                        var value=StrictJson.parse(json,MAXIMUM_QUEUE_RESPONSE_BYTES);
                        if(value.isObject()&&value.path("request_id").isTextual()&&actualRequestId.equals(value.path("request_id").textValue())
                                &&value.path("ok").isBoolean()&&!value.path("ok").booleanValue())status=ManagedQueueStatus.FAILED;
                    }catch(IOException|RuntimeException malformed){issue=Optional.of(ManagedQueueReadIssue.INVALID_RESPONSE);error=Optional.of(malformed.getClass().getName());}
                }
            }
        }
        var observed=new ManagedQueueObservation(original,same,actualRequestId,status,directories,inbox,outbox,response,issue,error);
        observed.requireCurrent(same,original);return observed;
    }
    private void requireQueueSource(Session same)throws IOException {
        writer.requireSession(same);storage.requireReadScope(same,files);profile.requireCurrent(plan,clock);
        plan.sources().requireLoadedClass(RootOriginalDriverJournal.class);
        plan.sources().requireLoadedClass(ManagedQueueObservation.class);
    }
    private static QueueDirectory queueDirectory(Path path)throws IOException {
        if(!path.isAbsolute()||!path.normalize().equals(path))throw new IOException("absolute normalized lifecycle directory required");
        SharedSourceFiles.plainAncestors(path);
        final BasicFileAttributes attributes;
        try{attributes=Files.readAttributes(path,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);}
        catch(NoSuchFileException absent){return new QueueDirectory(path,Optional.empty());}
        if(!attributes.isDirectory()||attributes.isSymbolicLink())throw new IOException("lifecycle queue ancestor must be an original plain directory");
        return new QueueDirectory(path,Optional.of(SharedSourceFiles.nativeDirectory(path)));
    }
    public static final class OriginalInputRejected extends IOException {
        private OriginalInputRejected(OriginalDriverJournal.InputRejected source){super("original Driver input rejected by strict Java source/resource validation",source);}
    }
    /** Pre-Core source/configuration supplier. It resolves no writer and reads no Driver until the actual borrowed call. */
    public static final class Prepared {
        private final CheckpointFiles files;private final RootRuntimeStorageGuard storage;private final NativeLaunchPlan plan;
        private final FrozenRunProfile profile;private final Clock clock;private ContinuityWriter writer;private RootOriginalDriverJournal importer;
        public Prepared(CheckpointFiles sameGuardedFiles,RootRuntimeStorageGuard sameStorage,NativeLaunchPlan sameRetainedPlan,
                FrozenRunProfile actualProfile,Clock actualClock)throws IOException {
            files=Objects.requireNonNull(sameGuardedFiles);storage=Objects.requireNonNull(sameStorage);plan=Objects.requireNonNull(sameRetainedPlan);
            profile=Objects.requireNonNull(actualProfile);clock=Objects.requireNonNull(actualClock);storage.requireFilePort(files);profile.requireCurrent(plan,clock);
        }
        public FrozenRunProfile frozenProfile(){return profile;}
        public synchronized OriginalJournalLoad load(ContinuityWriter actualWriter,Session same,NativeLaunchPlan identicalPlan)throws IOException {
            if(identicalPlan!=plan)throw new IOException("initial original Driver supplier cannot borrow another retained launch plan");
            Objects.requireNonNull(actualWriter).requireSession(same);
            if(writer!=null&&writer!=actualWriter)throw new IOException("original Driver supplier is already bound to its sole writer");
            if(importer==null){importer=new RootOriginalDriverJournal(actualWriter,files,storage,plan,profile,clock);writer=actualWriter;}
            return importer.load(same);
        }
    }
    private record Inventory(Path path,Optional<SharedSourceFiles.NativeFile> nativeFile) { }
    private static com.fasterxml.jackson.databind.node.ObjectNode inventoryIdentity(Inventory inventory) {
        var row=StrictJson.object();row.put("path",inventory.path().toString());
        if(inventory.nativeFile().isPresent())row.set("native_file",nativeIdentity(inventory.nativeFile().orElseThrow()));else row.putNull("native_file");
        return row;
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode nativeIdentity(SharedSourceFiles.NativeFile actual) {
        var row=StrictJson.object();row.put("volume_serial",actual.volumeSerialDecimal());row.put("file_id",actual.fileIdDecimal());
        row.put("legacy_volume_serial",actual.legacyVolumeSerialDecimal());row.put("legacy_file_id_hex",actual.legacyFileIdHex());
        row.put("creation_filetime",actual.creationFiletimeDecimal());row.put("last_write_filetime",actual.lastWriteFiletimeDecimal());
        row.put("change_filetime",actual.changeFiletimeDecimal());row.put("logical_bytes",Long.toString(actual.logicalBytes()));
        row.put("allocated_bytes",Long.toString(actual.allocatedBytes()));row.put("link_count",Long.toString(actual.linkCount()));return row;
    }
    private final ContinuityWriter writer;private final CheckpointFiles files;private final RootRuntimeStorageGuard storage;
    private final NativeLaunchPlan plan;private final FrozenRunProfile profile;private final Clock clock;
    public RootOriginalDriverJournal(ContinuityWriter actualWriter,CheckpointFiles sameGuardedFiles,
            RootRuntimeStorageGuard actualStorage,NativeLaunchPlan sameRetainedPlan,FrozenRunProfile actualFrozenProfile,Clock actualClock)throws IOException {
        writer=Objects.requireNonNull(actualWriter);files=Objects.requireNonNull(sameGuardedFiles);storage=Objects.requireNonNull(actualStorage);
        plan=Objects.requireNonNull(sameRetainedPlan);profile=Objects.requireNonNull(actualFrozenProfile);clock=Objects.requireNonNull(actualClock);
        storage.requireFilePort(files);profile.requireCurrent(plan,clock);
    }
    /** A private read issuer, not a deserializable restoration permission or a replacement Seed. */
    public static final class OriginalJournalLoad {
        private final RootOriginalDriverJournal issuer;private final Session scope;private final String headDigest;
        private final Inventory baseInventory,journalInventory;private final Optional<FileWitness> baseWitness,journalWitness;
        private final Status status;private final Optional<OriginalDriverJournal.Replayed> replay;private final Optional<String> journalError;
        private OriginalJournalLoad(RootOriginalDriverJournal issuer,Session scope,String headDigest,Inventory baseInventory,Inventory journalInventory,
                Optional<FileWitness> baseWitness,Optional<FileWitness> journalWitness,Status status,
                Optional<OriginalDriverJournal.Replayed> replay,Optional<String> journalError) {
            this.issuer=issuer;this.scope=scope;this.headDigest=headDigest;this.baseInventory=baseInventory;this.journalInventory=journalInventory;
            this.baseWitness=baseWitness;this.journalWitness=journalWitness;this.status=status;this.replay=replay;this.journalError=journalError;
        }
        public Status status(){return status;}
        public Optional<FileWitness> originalBase(){return baseWitness;}
        public Optional<FileWitness> originalJournal(){return journalWitness;}
        public Optional<String> journalError(){return journalError;}
        public FrozenRunProfile frozenProfile(){return issuer.profile;}
        public String pipeName(){return issuer.plan.pipeName();}
        /** Current admitted profile locator from this private load's identical launch plan; never the historical Driver's adjacent profile. */
        public Path profileDirectory(){return issuer.plan.profileDirectory();}
        public void requireActualProfile(Session same,Path actualProfile)throws IOException {
            requireRetained(same);
            if(!issuer.plan.profileDirectory().equals(Objects.requireNonNull(actualProfile)))
                throw new IOException("legacy physical material uses another current admitted profile directory");
            SharedSourceFiles.plainAncestors(actualProfile);var identity=SharedSourceFiles.nativeDirectory(actualProfile);
            issuer.profile.requireCurrent(issuer.plan,issuer.clock);requireRetained(same);
            if(!identity.equals(SharedSourceFiles.nativeDirectory(actualProfile)))throw new IOException("current admitted profile directory identity changed");
        }
        public List<ExactRef> originalReferences(){var refs=new ArrayList<ExactRef>(issuer.profile.originalReferences());baseWitness.ifPresent(ref->refs.add(ref.reference()));journalWitness.ifPresent(ref->refs.add(ref.reference()));return List.copyOf(refs);}
        /** Complete raw replay result; the shared canonical resume normalizers are still mandatory before adoption. */
        public ObjectValue fullPayload()throws IOException {return replay.orElseThrow(()->new IOException("no complete original Driver payload for "+status)).payload();}
        public byte[] fullBytes()throws IOException {
            try{return OriginalDriverJournal.canonical(fullPayload(),OriginalDriverJournal.MAXIMUM_DRIVER_BYTES).bytes();}
            catch(OriginalDriverJournal.InputRejected strict){throw new OriginalInputRejected(strict);}
        }
        public boolean lifecycleFieldWasMissing()throws IOException {return !fullPayload().contains("succession_lifecycle");}
        public java.math.BigInteger persistedBridgePid()throws IOException {
            try {var pid=OriginalDriverJournal.integer(fullPayload().get("bridge_pid"),"persisted bridge PID must be an exact integer");
                if(pid.signum()<=0)throw new IllegalArgumentException("positive persisted bridge PID required");return pid;}
            catch(IllegalArgumentException invalid){throw new IOException("original persisted bridge PID is malformed",invalid);}
        }
        public SuccessionLifecycleBinding persistedLifecycle()throws IOException {
            return switch(persistedLifecycleData()) {
                case MissingLegacyLifecycle ignored->SuccessionLifecycleBinding.legacyRogue();
                case BoundPersistedLifecycle bound->bound.binding();
                case ExplicitNullLifecycle ignored->throw new IOException("explicit native_campaign null has no ordinary lifecycle binding");
            };
        }
        public PersistedLifecycle persistedLifecycleData()throws IOException {return readPersistedLifecycle(fullPayload());}
        /** DATA projection from this load's actual private frozen profile, never from a nullable DTO. */
        public LegacyResumeMigration.FrozenLifecycle frozenLifecycleProjection()throws IOException {
            var frozen=frozenProfile();var binding=frozen.lifecycleBinding();
            if(binding.isPresent()) {
                if(frozen.fixture().isPresent())throw new IOException("bound original profile also claims a native fixture");
                return new LegacyResumeMigration.BoundLifecycle(binding.orElseThrow());
            }
            // Fresh fixture and actual SavedNative retain different private producers. Empty
            // public binding alone never selects either; the original Frozen issuer proves it.
            frozen.requireExplicitNativeCampaign();
            return new LegacyResumeMigration.ExplicitNativeCampaign();
        }
        /** Complete normalization under the identical real input/source scope; returns no adoption authority. */
        public LegacyResumeNormalizer.Result normalizeForFrozen(Session same)throws IOException {
            requireRetained(same);var projection=frozenLifecycleProjection();
            var kind=projection instanceof LegacyResumeMigration.ExplicitNativeCampaign
                    ?LegacyResumeNormalizer.LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN
                    :LegacyResumeNormalizer.LifecycleProjection.BOUND_OR_LEGACY;
            var normalized=LegacyResumeNormalizer.normalize(DriverJson.object(fullBytes(),
                    org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES),pipeName(),kind);
            requireRetained(same);return normalized;
        }
        public void requireRetained(Session identical)throws IOException {issuer.requireRetained(identical,this);}
        public void requireCommittedInputs(Session same,WriterContracts.Prepared transition,WriterContracts.Receipt receipt)throws IOException {
            issuer.requireCommittedInputs(same,this,transition,receipt);
        }
        /** Consumes the actual already received HELLO; it neither connects nor requests a snapshot. */
        public TransportSession requireActualHello(Session same,NativeGameTransport actual)throws IOException {
            requireRetained(same);Objects.requireNonNull(actual);
            var received=actual.diagnostics();var hello=received.session().orElseThrow(()->new IOException("actual original HELLO required before Driver import classification"));
            if(received.originalHello().isEmpty()||!actual.pipeName().equals(issuer.plan.pipeName())
                    ||!hello.machineId().equals(issuer.plan.sources().review().machineId())||!hello.sessionId().equals(issuer.plan.sessionId()))
                throw new IOException("original Driver import and actual received HELLO belong to different retained run identities");
            issuer.profile.initialPolicy().verifyGame(hello.game());
            requireRetained(same);return hello;
        }
        /** A later shared canonical payload failure is sticky only for an actually replayed/marked WAL. */
        public boolean canonicalFailureIsJournalInvalid(){return status==Status.REPLAYED||status==Status.ALREADY_CONSOLIDATED;}
    }
    public OriginalJournalLoad load(Session same)throws IOException {
        writer.requireSession(same);String head=same.head().digest();storage.requireReadScope(same,files);profile.requireCurrent(plan,clock);
        Path directory=plan.stateDirectory().resolve("native-session");storage.requireManagedRoots(List.of(plan.stateDirectory()));
        Inventory base=inventory(directory.resolve("driver-state.json")),journal=inventory(directory.resolve(OriginalDriverJournal.JOURNAL_FILENAME));
        // Even an explicitly fresh request must inspect a present pair. It cannot suppress original
        // refusal evidence, turn bad files into MISSING, or pass a fresh empty Seed to the caller.
        if(base.nativeFile().isEmpty()&&journal.nativeFile().isEmpty())
            return finish(same,head,base,journal,Optional.empty(),Optional.empty(),Status.MISSING,Optional.empty(),Optional.empty());
        if(base.nativeFile().isEmpty())
            return finish(same,head,base,journal,Optional.empty(),Optional.empty(),Status.JOURNAL_INVALID,Optional.empty(),Optional.of("Driver journal exists without its base state"));
        if(journal.nativeFile().filter(value->value.logicalBytes()>OriginalDriverJournal.MAXIMUM_JOURNAL_BYTES).isPresent())
            return finish(same,head,base,journal,Optional.empty(),Optional.empty(),Status.JOURNAL_INVALID,Optional.empty(),Optional.of("journal exceeds original bounded reader capacity"));
        long baseSize=base.nativeFile().orElseThrow().logicalBytes();
        if(baseSize>OriginalDriverJournal.MAXIMUM_DRIVER_BYTES)throw new IOException("original full Driver exceeds the complete importer resource lease");
        final byte[] baseBytes;final Optional<byte[]> journalBytes;
        try {
            // Only direct original file-open/read OSErrors inside this exact pair are Python's
            // load_pair unreadable condition. Guard, profile and custody errors stay outside it.
            baseBytes=readOriginal(base,OriginalDriverJournal.MAXIMUM_DRIVER_BYTES);
            journalBytes=journal.nativeFile().isPresent()?Optional.of(readOriginal(journal,OriginalDriverJournal.MAXIMUM_JOURNAL_BYTES)):Optional.empty();
        }catch(OriginalFileReadFailure unreadable) {
            if(journal.nativeFile().isEmpty())throw unreadable;
            return finish(same,head,base,journal,Optional.empty(),Optional.empty(),Status.JOURNAL_INVALID,Optional.empty(),Optional.of("original journal pair is unreadable: "+unreadable.getCause().getClass().getName()));
        }
        FileWitness originalBase=capture(base,baseBytes);
        Optional<FileWitness> originalJournal=journal.nativeFile().isPresent()?Optional.of(capture(journal,journalBytes.orElseThrow())):Optional.empty();
        try {
            var replay=OriginalDriverJournal.replay(baseBytes,journalBytes);
            return finish(same,head,base,journal,Optional.of(originalBase),originalJournal,Status.valueOf(replay.status().name()),Optional.of(replay),Optional.empty());
        }catch(OriginalDriverJournal.InputRejected strict) {throw new OriginalInputRejected(strict);}
        catch(OriginalDriverJournal.JournalInvalid invalid) {
            return finish(same,head,base,journal,Optional.of(originalBase),originalJournal,Status.JOURNAL_INVALID,Optional.empty(),Optional.of(invalid.getMessage()));
        }
    }
    public void requireRetained(Session same,OriginalJournalLoad original)throws IOException {
        Objects.requireNonNull(original);writer.requireSession(same);storage.requireReadScope(same,files);profile.requireCurrent(plan,clock);
        if(original.issuer!=this||original.scope!=same||!original.headDigest.equals(same.head().digest()))throw new IOException("original Driver import belongs to another issuer, writer scope or canonical predecessor");
        requireInventory(original.baseInventory);requireInventory(original.journalInventory);
        if(original.baseWitness.isPresent())files.verify(original.baseWitness.orElseThrow());
        if(original.journalWitness.isPresent())files.verify(original.journalWitness.orElseThrow());
    }
    private void requireCommittedInputs(Session same,OriginalJournalLoad original,WriterContracts.Prepared transition,
            WriterContracts.Receipt receipt)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(transition);Objects.requireNonNull(receipt);writer.requireSession(same);
        if(original.issuer!=this||original.scope!=same||!transition.predecessor().digest().equals(original.headDigest))
            throw new IOException("committed original inputs require their identical issuer, scope and actual original predecessor");
        var delta=committedDelta(transition);
        if(!delta.expectedHeadSha256().equals(original.headDigest)||!delta.originalInputs().containsAll(original.originalReferences())
                ||receipt.disposition()==WriterContracts.Disposition.NO_CHANGE)
            throw new IOException("actual original-resume commit does not retain the complete original input closure");
        // This is the real canonical event/history reader. A caller-created Prepared/Receipt pair cannot pass it.
        same.requireCommitted(transition,receipt);
        storage.requireReadScope(same,files);profile.requireCurrent(plan,clock);
        requireInventory(original.baseInventory);requireInventory(original.journalInventory);
        if(original.baseWitness.isPresent())files.verify(original.baseWitness.orElseThrow());
        if(original.journalWitness.isPresent())files.verify(original.journalWitness.orElseThrow());
        same.requireCommitted(transition,receipt);
    }
    private static OriginalLegacyResume.Delta committedDelta(WriterContracts.Prepared transition)throws IOException {
        if(!OriginalLegacyResume.KIND.equals(Objects.requireNonNull(transition).request().kind()))
            throw new IOException("postcommit original input custody is limited to the actual original legacy-resume transition");
        try{return OriginalLegacyResume.decode(transition.request().detailsObject());}
        catch(RuntimeException invalid){throw new IOException("actual committed legacy-resume descriptor failed its single typed codec",invalid);}
    }
    private OriginalJournalLoad finish(Session same,String head,Inventory base,Inventory journal,Optional<FileWitness> baseWitness,
            Optional<FileWitness> journalWitness,Status status,Optional<OriginalDriverJournal.Replayed> replay,Optional<String> error)throws IOException {
        var result=new OriginalJournalLoad(this,same,head,base,journal,baseWitness,journalWitness,status,replay,error);requireRetained(same,result);return result;
    }
    private FileWitness capture(Inventory original,byte[] readBytes)throws IOException {
        long size=original.nativeFile().orElseThrow(()->new IOException("missing original file")).logicalBytes();
        FileWitness witness=files.observe(original.path()).orElseThrow(()->new IOException("original Driver/WAL disappeared"));
        if(!Path.of(witness.reference().path()).equals(original.path())||witness.reference().bytes()!=size
                ||readBytes.length!=size||!OriginalDriverJournal.sha256(readBytes).equals(witness.reference().sha256()))throw new IOException("observed original differs from its complete captured bytes");
        requireInventory(original);return witness;
    }
    private static final class OriginalFileReadFailure extends IOException {
        private OriginalFileReadFailure(IOException source){super("actual Driver/WAL original file read failed",source);}
    }
    private static byte[] readOriginal(Inventory original,int maximum)throws IOException {
        final byte[] bytes;
        try(var stream=Files.newInputStream(original.path())){bytes=stream.readNBytes(maximum+1);}
        catch(IOException actualFileFailure){throw new OriginalFileReadFailure(actualFileFailure);}
        // A file changing or growing during capture is a custody failure, not a replay diagnosis.
        if(bytes.length!=original.nativeFile().orElseThrow().logicalBytes()||bytes.length>maximum)throw new IOException("original Driver/WAL changed during complete read");
        requireInventory(original);return bytes;
    }
    private static Inventory inventory(Path path)throws IOException {
        if(!path.isAbsolute()||!path.normalize().equals(path))throw new IOException("absolute normalized original Driver path required");
        SharedSourceFiles.plainAncestors(path);
        final BasicFileAttributes attributes;
        try{attributes=Files.readAttributes(path,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);}
        catch(NoSuchFileException absent){return new Inventory(path,Optional.empty());}
        if(!attributes.isRegularFile()||attributes.isSymbolicLink())throw new IOException("original Driver/WAL entry must be a regular file, not a link or directory");
        return new Inventory(path,Optional.of(SharedSourceFiles.nativeFile(path)));
    }
    private static void requireInventory(Inventory original)throws IOException {
        if(!inventory(original.path()).equals(original))throw new IOException("original Driver/WAL presence or native FileID/birth/content length changed");
    }
}
