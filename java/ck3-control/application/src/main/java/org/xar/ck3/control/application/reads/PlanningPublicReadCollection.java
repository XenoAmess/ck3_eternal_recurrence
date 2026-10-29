package org.xar.ck3.control.application.reads;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.PlanningReadCoordinator.FailedReadAttempt;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One actual public collection. A native rejection is retained DATA, never a successful read receipt. */
public final class PlanningPublicReadCollection {
    private PlanningPublicReadCollection() { }
    public static final String SCHEMA="xar.public-rejected-read-originals/v1";
    @FunctionalInterface public interface ReadWork<T> { PlanningReadResult<T> run() throws IOException; }
    public sealed interface Result<T> permits Positive,Rejected { }
    public static final class Positive<T> implements Result<T> {
        private final PlanningReadResult.Known<T> actual;
        private final ReadContract<?> contract;
        private Positive(PlanningReadResult.Known<T> actual,ReadContract<?> contract){this.actual=actual;this.contract=contract;}
        public PlanningReadResult.Known<T> actual(){return actual;}
        public ReadContract<?> contract(){return contract;}
    }
    public static final class Rejected<T> implements Result<T> {
        private final PlanningReadResult.Unavailable<T> actual;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final FailedReadAttempt custody;
        private Rejected(PlanningReadResult.Unavailable<T> actual,ReadContract<?> contract,
                PlanningReadRequest request,FailedReadAttempt custody){
            this.actual=actual;this.contract=contract;this.request=request;this.custody=custody;
        }
        public PlanningReadResult.Unavailable<T> actual(){return actual;}
        public ReadContract<?> contract(){return contract;}
        public PlanningReadRequest request(){return request;}
        public PlanningReadGuard before(){return custody.before();}
        public NativeRequest prepared(){return custody.prepared();}
        public NativeActionPort.AckReceived acknowledgement(){return requireRejectedAck(custody.original());}
        public void requireOriginal(Session same,OutcomeArchive bound)throws IOException {
            custody.requireOriginal(same,contract,request,actual,bound);
            bound.verifyReadAttemptOriginals(request,custody.requestId(),custody.before(),custody.prepared(),custody.original());
            requireRejectedAck(custody.original());
        }
        /** Retains two small immutable DATA artifacts. No canonical event, attempt count or Driver publication is created. */
        public Recorded record(Session same,RootReadContractCatalog catalog,OutcomeArchive bound)throws IOException {
            requireOriginal(same,bound);
            var installed=installed(catalog,contract.contractId());
            require(installed.contract()==contract,"rejected collection changed its identical installed contract");
            var args=new RawJson(OpportunityJson.encode(request.arguments()));
            ExactRef arguments=bound.preserveMaterial(args);
            require(arguments.equals(bound.materialReferenceOf(args)),"rejected collection arguments archive differs");
            var value=new Recorded(request,before(),actual.reason(),custody.requestId(),contract.contractId(),arguments,
                    custody.preparedRef(),custody.originalRef(),contract.sourceRef(),installed.decoderSource(),
                    contract.permissionMode(),contract.wireProfile(),contract.requiredCapability(),custody.headSequence(),custody.headDigest());
            RawJson encoded=encode(value);ExactRef ref=bound.preserveMaterial(encoded);
            require(ref.equals(bound.materialReferenceOf(encoded))&&bound.loadMaterial(ref).equals(encoded),"rejected collection metadata archive differs");
            requireOriginal(same,bound);return replay(catalog,bound,encoded);
        }
    }
    /** Cold DATA has no FailedReadAttempt, Session, live permission, successful after frame or Known value. */
    public record Recorded(PlanningReadRequest request,PlanningReadGuard before,String reason,String requestId,String contractId,
            ExactRef arguments,ExactRef prepared,ExactRef original,ExactRef definitionSource,ExactRef decoderSource,
            ReadContract.PermissionMode permissionMode,ReadContract.WireProfile wireProfile,Optional<String> requiredCapability,
            long headSequence,String headDigest) {
        public Recorded {
            Objects.requireNonNull(request);Objects.requireNonNull(before);StrictJson.text(reason);StrictJson.text(requestId);StrictJson.text(contractId);
            require(reason.length()<=2048,"bounded original rejected-read diagnostic required");
            for(ExactRef ref:List.of(arguments,prepared,original,definitionSource,decoderSource))require(Objects.requireNonNull(ref).bytes()>0,"actual original reference required");
            Objects.requireNonNull(permissionMode);Objects.requireNonNull(wireProfile);requiredCapability=Objects.requireNonNull(requiredCapability);
            requiredCapability.ifPresent(StrictJson::text);StrictJson.safe(headSequence,0);
            require(headDigest!=null&&headDigest.matches("[0-9a-f]{64}"),"actual original writer-head digest required");
        }
        public NativeActionPort.AckReceived acknowledgement(OutcomeArchive originals){return requireRejectedAck(originals.load(original));}
    }
    private static final class Scope {
        final Session same;final Thread thread=Thread.currentThread();Capture captured;
        Scope(Session same){this.same=same;}
    }
    private record Capture(ReadContract<?> contract,PlanningReadRequest request,PlanningReadResult.Unavailable<?> result,
            Optional<FailedReadAttempt> custody) { }
    private static final ThreadLocal<Scope> ACTIVE=new ThreadLocal<>();

    /** Called only in addition to the existing sole coordinator observer; an inactive scope does nothing. */
    public static void afterUnavailable(Session same,ReadContract<?> identical,PlanningReadRequest request,
            PlanningReadResult.Unavailable<?> actual,Optional<FailedReadAttempt> custody) {
        Scope active=ACTIVE.get();if(active==null)return;
        require(active.thread==Thread.currentThread()&&active.same==same,"rejected collection crossed its actual writer callback/thread");
        require(active.captured==null,"one actual unavailable callback per public collection required");
        active.captured=new Capture(Objects.requireNonNull(identical),Objects.requireNonNull(request),Objects.requireNonNull(actual),Objects.requireNonNull(custody));
    }
    /** The work must invoke the already installed read port. This helper cannot issue a permit or install a decoder. */
    public static <T> Result<T> collect(Session same,RootReadContractCatalog catalog,OutcomeArchive bound,ReadWork<T> work)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(catalog);Objects.requireNonNull(bound);Objects.requireNonNull(work);
        require(ACTIVE.get()==null,"public read collection cannot nest or replace its original callback");
        Scope active=new Scope(same);ACTIVE.set(active);
        try {
            PlanningReadResult<T> actual=Objects.requireNonNull(work.run());
            if(actual instanceof PlanningReadResult.Known<T> known){
                require(active.captured==null,"successful public collection hid an earlier actual unavailable attempt");
                var installed=installed(catalog,known.receipt().contractId());
                require(known.originalReceipt().equals(bound.readReferenceOf(known.receipt()))
                        &&known.receipt().equals(bound.loadRead(known.originalReceipt())),"positive collection lost its exact original read receipt");
                Object replayed=installed.contract().replay(known.receipt());
                require(replayed.equals(known.value()),"positive collection changed its installed pure replay");
                return new Positive<>(known,installed.contract());
            }
            PlanningReadResult.Unavailable<T> unavailable=(PlanningReadResult.Unavailable<T>)actual;
            Capture captured=active.captured;
            if(captured==null||captured.result()!=unavailable||captured.custody().isEmpty())
                throw new IOException("original rejected public READ custody unavailable: "+unavailable.reason());
            require(catalog.containsIdentity(captured.contract()),"rejected collection callback is not the identical installed contract");
            var rejected=new Rejected<>(unavailable,captured.contract(),captured.request(),captured.custody().orElseThrow());
            rejected.requireOriginal(same,bound);return rejected;
        } finally {ACTIVE.remove();}
    }
    public static RawJson encode(Recorded value) {
        Objects.requireNonNull(value);ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);
        row.put("contract_id",value.contractId()).put("request_id",value.requestId()).put("reason",value.reason());
        row.set("request",CommandOriginCodec.planningRequest(value.request(),value.arguments()));
        row.set("guard",CommandOriginCodec.planningGuard(value.before()));
        row.set("prepared",value.prepared().toJson());row.set("original",value.original().toJson());
        row.set("definition_source",value.definitionSource().toJson());row.set("decoder_source",value.decoderSource().toJson());
        row.put("permission_mode",value.permissionMode().name()).put("wire_profile",value.wireProfile().name());
        if(value.requiredCapability().isPresent())row.put("required_capability",value.requiredCapability().orElseThrow());else row.putNull("required_capability");
        row.put("head_sequence",Long.toString(value.headSequence())).put("head_digest",value.headDigest());
        return new RawJson(StrictJson.canonical(row,RawJson.MAXIMUM_BYTES));
    }
    /** Strict decoder plus read-only original-artifact replay. It cannot recreate live callback custody. */
    public static Recorded replay(RootReadContractCatalog catalog,OutcomeArchive bound,RawJson metadata) {
        ObjectNode row=StrictJson.object(StrictJson.parse(metadata.bytes(),RawJson.MAXIMUM_BYTES),Set.of("schema","contract_id","request_id","reason",
                "request","guard","prepared","original","definition_source","decoder_source","permission_mode","wire_profile","required_capability","head_sequence","head_digest"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact rejected collection schema required");
        ExactRef arguments=ExactRef.fromJson(row.get("request").get("arguments_ref"));RawJson args=bound.loadMaterial(arguments);
        require(arguments.equals(bound.materialReferenceOf(args)),"rejected collection original arguments changed");
        var request=CommandOriginCodec.planningRequest(row.get("request"),DriverJson.object(args.bytes(),RawJson.MAXIMUM_BYTES));
        String sequence=StrictJson.text(row.get("head_sequence"));require(sequence.matches("0|[1-9][0-9]*"),"canonical original head sequence required");
        var result=new Recorded(request,CommandOriginCodec.planningGuard(row.get("guard")),StrictJson.text(row.get("reason")),
                StrictJson.text(row.get("request_id")),StrictJson.text(row.get("contract_id")),arguments,
                ExactRef.fromJson(row.get("prepared")),ExactRef.fromJson(row.get("original")),ExactRef.fromJson(row.get("definition_source")),ExactRef.fromJson(row.get("decoder_source")),
                ReadContract.PermissionMode.valueOf(StrictJson.text(row.get("permission_mode"))),ReadContract.WireProfile.valueOf(StrictJson.text(row.get("wire_profile"))),
                row.get("required_capability").isNull()?Optional.empty():Optional.of(StrictJson.text(row.get("required_capability"))),Long.parseLong(sequence),StrictJson.text(row.get("head_digest")));
        require(StrictJson.parse(encode(result).bytes(),RawJson.MAXIMUM_BYTES).equals(row),"rejected collection typed serde changed its original metadata");
        var installed=installed(catalog,result.contractId());ReadContract<?> contract=installed.contract();
        require(contract.sourceRef().equals(result.definitionSource())&&installed.decoderSource().equals(result.decoderSource())
                &&contract.operation().equals(request.operation())&&contract.permissionMode()==result.permissionMode()
                &&contract.wireProfile()==result.wireProfile()&&contract.requiredCapability().equals(result.requiredCapability()),"rejected collection changed its installed source/permission/operation");
        NativeRequest prepared=bound.loadRequest(result.prepared());NativeActionPort.AckReceived ack=result.acknowledgement(bound);
        require(result.prepared().equals(bound.requestReferenceOf(prepared))&&result.original().equals(bound.referenceOf(ack))
                &&ack.requestId().equals(result.requestId()),"rejected collection lost its original prepared/outcome identity");
        bound.verifyReadAttemptOriginals(request,result.requestId(),result.before(),prepared,ack);return result;
    }
    private static RootReadContractCatalog.InstalledRead installed(RootReadContractCatalog catalog,String id) {
        var matches=catalog.installed().stream().filter(entry->entry.contract().contractId().equals(id)).toList();
        require(matches.size()==1&&catalog.containsIdentity(matches.getFirst().contract()),"one identical installed original read contract required");return matches.getFirst();
    }
    private static NativeActionPort.AckReceived requireRejectedAck(NativeActionPort.DispatchOutcome original) {
        require(original instanceof NativeActionPort.AckReceived,"rejected public READ has no actual received ACK; UNKNOWN/pre-dispatch is not a negative result");
        var ack=(NativeActionPort.AckReceived)original;
        require(!ack.nativeOk()&&ack.outbound().isPresent()&&ack.custody().isPresent(),"actual negative native ACK with complete outbound/chronology required");return ack;
    }
    private static void require(boolean value,String reason){StrictJson.require(value,reason);}
}
