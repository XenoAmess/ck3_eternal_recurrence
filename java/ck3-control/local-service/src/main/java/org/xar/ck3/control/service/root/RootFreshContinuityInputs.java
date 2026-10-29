package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.continuity.writer.WriterContracts.InitialLayout;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual configured request -> sole original store initializer. No plan or predicted FileRef is an output. */
public final class RootFreshContinuityInputs {
    public static final String SCHEMA="xar.java-root-fresh-continuity-initialization-request/v1";
    public static final int MAXIMUM_REQUEST_BYTES=8192;
    private RootFreshContinuityInputs() { }
    public enum Mode { QUOTE,CREATE_NEW,QUERY_ORIGINAL }
    /** The request is configuration only. CREATE_NEW additionally needs the real existing runtime allocation lease. */
    public record Request(String schema,String machineId,String reviewAtUtc,Mode mode,FileRef planOriginal,
            String snapshot,String anchor,FileRef storageLease) {
        public Request {
            StrictJson.require(SCHEMA.equals(schema),"exact genesis initialization request version required");
            StrictJson.text(machineId);Objects.requireNonNull(mode);file(planOriginal,FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES);
            new InitialLayout(Path.of(snapshot),Path.of(anchor),machineId);
            StrictJson.require(Instant.parse(reviewAtUtc).toString().equals(reviewAtUtc),"canonical finite initialization review required");
            StrictJson.require((mode==Mode.CREATE_NEW)==(storageLease!=null),"only CREATE_NEW requires the actual runtime storage lease; query and quote issue no storage permit");
            if(storageLease!=null)file(storageLease,RootRuntimeDefinitions.MAXIMUM_BYTES);
        }
    }
    public record InitializationQuote(String snapshot,String anchor,String originalLock,String events,long canonicalBytesPerFile) { }
    public static byte[] encodeRequest(Request request) {
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);row.put("machine_id",request.machineId());
        row.put("review_at_utc",request.reviewAtUtc());row.put("mode",request.mode().name());
        row.set("plan_original",exact(request.planOriginal()).toJson());row.put("snapshot",request.snapshot());row.put("anchor",request.anchor());
        if(request.storageLease()==null)row.putNull("storage_lease");else row.set("storage_lease",exact(request.storageLease()).toJson());
        return StrictJson.canonical(row,MAXIMUM_REQUEST_BYTES);
    }
    public static Request decodeRequest(byte[] bytes) {
        var row=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_REQUEST_BYTES),
                Set.of("schema","machine_id","review_at_utc","mode","plan_original","snapshot","anchor","storage_lease"));
        FileRef lease=row.get("storage_lease").isNull()?null:file(ExactRef.fromJson(row.get("storage_lease")));
        return new Request(StrictJson.text(row.get("schema")),StrictJson.text(row.get("machine_id")),
                StrictJson.text(row.get("review_at_utc")),Mode.valueOf(StrictJson.text(row.get("mode"))),
                file(ExactRef.fromJson(row.get("plan_original"))),StrictJson.text(row.get("snapshot")),StrictJson.text(row.get("anchor")),lease);
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);current(request,clock);
        List<SharedSourceFiles.Witness> witnesses=new ArrayList<>();
        capture(request.planOriginal(),witnesses);var plan=readPlan(request.planOriginal());
        if(!plan.machineId().equals(request.machineId()))throw new IOException("genesis initialization and plan machine differ");
        RootRuntimeDefinitionModel.StorageLease lease=null;
        if(request.storageLease()!=null) {
            capture(request.storageLease(),witnesses);
            lease=RootRuntimeDefinitions.decodeStorageLease(RootRuntimeDefinitions.read(request.storageLease(),RootRuntimeDefinitions.MAXIMUM_BYTES));
            if(!lease.machineId().equals(request.machineId()))throw new IOException("genesis storage lease machine differs");
        }
        Prepared prepared=new Prepared(request,plan,lease,List.copyOf(witnesses),clock);prepared.requireCurrent();return prepared;
    }
    /** Shared bootstrap CLI consumer; closing this finite pre-Core scope requires a fresh census for another process. */
    public static byte[] execute(Request request,Clock clock)throws IOException {
        Prepared prepared=prepare(request,clock);
        var receipt=StrictJson.object().put("schema","xar.java-root-fresh-continuity-initialization-result/v1")
                .put("machine_id",request.machineId()).put("observed_at_utc",clock.instant().toString())
                .put("mode",request.mode().name()).put("scope","SOLE_CONTINUITY_STORE_INITIALIZATION_DATA_ONLY");
        receipt.set("plan_original",exact(request.planOriginal()).toJson());
        if(request.mode()==Mode.QUOTE) {
            var quote=prepared.quote();var row=receipt.putObject("quote");
            row.put("snapshot",quote.snapshot()).put("anchor",quote.anchor()).put("original_lock",quote.originalLock())
                    .put("events",quote.events()).put("canonical_bytes_per_file",quote.canonicalBytesPerFile());
            receipt.put("status","QUOTED_NOT_WRITTEN");
        }else {
            ContinuityWriter.Initialized actual;
            if(request.mode()==Mode.CREATE_NEW) {
                try(Created created=prepared.createNew()){actual=created.initialized();}
                receipt.put("status","CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION")
                        .put("next_process_requires_fresh_actual_storage_census",true);
            }else {
                actual=prepared.queryOriginal();
                receipt.put("status","ORIGINAL_INITIALIZATION_READ_ONLY_NOT_ALLOCATION_RECONCILED")
                        .put("allocation_unknown_reconciled",false).put("write_retry_permitted",false);
            }
            var layout=receipt.putObject("layout").put("snapshot",actual.layout().snapshot().toString())
                    .put("machine_id",actual.layout().machineId());
            layout.set("anchor",actual.layout().anchor().toJson());
            receipt.set("anchor",actual.anchor().toJson());receipt.set("snapshot",actual.snapshot().toJson());receipt.set("lock",actual.lock().toJson());
            receipt.put("head_digest",actual.initialHead().digest()).put("sequence",actual.initialHead().state().sequence());
        }
        prepared.requireCurrent();return StrictJson.canonical(receipt,MAXIMUM_REQUEST_BYTES);
    }
    public static final class Prepared {
        private final Request request;
        private final FreshContinuityGenesis.Plan plan;
        private final RootRuntimeDefinitionModel.StorageLease lease;
        private final List<SharedSourceFiles.Witness> originals;
        private final Clock clock;
        private boolean creationEntered;
        private Prepared(Request request,FreshContinuityGenesis.Plan plan,RootRuntimeDefinitionModel.StorageLease lease,
                List<SharedSourceFiles.Witness> originals,Clock clock){
            this.request=request;this.plan=plan;this.lease=lease;this.originals=originals;this.clock=clock;
        }
        public InitializationQuote quote()throws IOException {
            requireCurrent();var paths=paths();long bytes=Math.addExact(FreshContinuityGenesis.initial(plan,exact(request.planOriginal())).canonicalBytes().length,1);
            return new InitializationQuote(paths.snapshot().toString(),paths.anchor().toString(),paths.lock().toString(),paths.events().toString(),bytes);
        }
        /** Exactly one actual attempt. The retained storage guard owns any UNKNOWN write until it is closed or reconciled. */
        public synchronized Created createNew()throws IOException {
            requireCurrent();if(request.mode()!=Mode.CREATE_NEW||lease==null)throw new IOException("CREATE_NEW requires its explicit original allocation lease");
            if(creationEntered)throw new IOException("original genesis creation was already entered; query only, never replay");
            creationEntered=true;
            DeferredWriter binding=new DeferredWriter();
            RootRuntimeStorageGuard storage=RootRuntimeStorageGuard.readExact(lease,request.machineId(),binding::requireWriter,clock);
            try {
                var actual=ContinuityWriter.initializeFresh(plan,exact(request.planOriginal()),paths(),storage);
                requireCurrent();return new Created(actual,storage,binding);
            }catch(IOException|RuntimeException failure){
                try{storage.close();}catch(IOException closing){failure.addSuppressed(closing);}throw failure;
            }
        }
        /** Only reads exact already completed outputs. No allocation guard, repair, write or retry capability is opened. */
        public ContinuityWriter.Initialized queryOriginal()throws IOException {
            requireCurrent();if(request.mode()!=Mode.QUERY_ORIGINAL)throw new IOException("read-only query requires explicit QUERY_ORIGINAL mode");
            var result=ContinuityWriter.readFreshInitialization(plan,exact(request.planOriginal()),paths());requireCurrent();return result;
        }
        private InitialLayout paths(){return new InitialLayout(Path.of(request.snapshot()),Path.of(request.anchor()),request.machineId());}
        private void requireCurrent()throws IOException {current(request,clock);for(var witness:originals)SharedSourceFiles.assertUnchanged(witness);}
    }
    /** Actual pre-writer allocation custody may be continued only by the identical real Core, never an empty provider. */
    public static final class Created implements AutoCloseable {
        private final ContinuityWriter.Initialized initialized;
        private final RootRuntimeStorageGuard storage;
        private final DeferredWriter binding;
        private boolean closed;
        private Created(ContinuityWriter.Initialized initialized,RootRuntimeStorageGuard storage,DeferredWriter binding){
            this.initialized=initialized;this.storage=storage;this.binding=binding;
        }
        public ContinuityWriter.Initialized initialized(){return initialized;}
        public synchronized StorageWriteGuard storage()throws IOException {
            if(closed)throw new IOException("the actual genesis allocation custody is closed");return storage;
        }
        public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            if(closed)throw new IOException("closed initialization cannot bind a Core");
            Objects.requireNonNull(actual);
            if(!actual.configuration().ledger().equals(initialized.layout())||actual.storageGuard()!=storage
                    ||actual.writer().storageGuard()!=storage)throw new IOException("initialization can bind only the actual same-layout same-storage Core");
            binding.bind(actual.writer());
        }
        @Override public synchronized void close()throws IOException {
            if(closed)throw new IOException("genesis allocation custody already closed");closed=true;storage.close();
        }
    }
    private static final class DeferredWriter {
        private ContinuityWriter actual;
        synchronized ContinuityWriter requireWriter()throws IOException {
            if(actual==null)throw new IOException("the actual post-genesis Core writer has not been bound; pre-writer allocation grants no writer session");return actual;
        }
        synchronized void bind(ContinuityWriter supplied)throws IOException {
            if(actual!=null&&actual!=supplied)throw new IOException("original genesis writer binding cannot be replaced");actual=Objects.requireNonNull(supplied);
        }
    }
    public static ContinuityWriter.Initialized createNew(FileRef actualRequest,Path snapshot,Path anchor,
            StorageWriteGuard actualStorage)throws IOException {
        var plan=readPlan(actualRequest);
        return ContinuityWriter.initializeFresh(plan,exact(actualRequest),new InitialLayout(snapshot,anchor,plan.machineId()),actualStorage);
    }
    /** The returned DATA does not reconcile a failed allocation guard or allow an unknown initialization to replay. */
    public static ContinuityWriter.Initialized queryOriginal(FileRef actualRequest,Path snapshot,Path anchor)throws IOException {
        var plan=readPlan(actualRequest);
        return ContinuityWriter.readFreshInitialization(plan,exact(actualRequest),new InitialLayout(snapshot,anchor,plan.machineId()));
    }
    public static FreshContinuityGenesis.Plan readPlan(FileRef actualRequest)throws IOException {
        try {
            var plan=FreshContinuityGenesis.decode(RootRuntimeDefinitions.read(actualRequest,FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES));
            if(!plan.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("genesis request belongs to another execution machine");
            if(plan.targetDays()!=org.xar.ck3.control.continuity.OriginalWindowReducer.TARGET_DAYS)
                throw new IOException("genesis must use the installed original stability-window policy, independent of campaign calendar goals");
            return plan;
        }catch(IllegalArgumentException invalid){throw new IOException("actual genesis request is invalid",invalid);}
    }
    private static void current(Request request,Clock clock)throws IOException {
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("genesis initialization request is foreign or expired");
    }
    private static void capture(FileRef reference,List<SharedSourceFiles.Witness> witnesses)throws IOException {
        var observed=SharedSourceFiles.observe(Path.of(reference.path()));
        if(!observed.source().equals(reference))throw new IOException("genesis initialization input differs from its real original");witnesses.add(observed);
    }
    private static void file(FileRef ref,int maximum) {
        Objects.requireNonNull(ref);Path path=Path.of(ref.path());
        StrictJson.require(path.isAbsolute()&&path.normalize().equals(path)&&ref.bytes()>0&&ref.bytes()<=maximum
                &&ref.sha256().matches("[0-9a-f]{64}"),"canonical bounded actual initialization input required");
    }
    private static FileRef file(ExactRef actual){return new FileRef(actual.path(),actual.bytes(),actual.sha256());}
    private static ExactRef exact(FileRef actual){return new ExactRef(actual.path(),actual.bytes(),actual.sha256());}
}
