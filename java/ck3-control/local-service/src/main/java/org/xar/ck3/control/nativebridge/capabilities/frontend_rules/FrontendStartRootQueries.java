package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.GameplayEntryRoot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.root.RootRuntimeContext;
import org.xar.ck3.control.service.root.RootRuntimeStorageGuard;

/** One actual Start root-query journal. All native IDs come from the sole coordinator's real preparation callback.
 * Original decimal timing tokens and integer identities remain data; they never supply a guard or replay permission. */
public final class FrontendStartRootQueries implements PlanningReadCoordinator.ReadLifecycleObserver {
    public enum Status { PREPARED_NOT_SUBMITTED,NATIVE_RESULT_RECEIVED,QUERY_FAILED,NATIVE_RESULT_PENDING_AT_DEADLINE,CAMPAIGN_ROOT_FRAME_VERIFIED }
    private record Result(Value status,Value querySequence) { }
    private record Record(PlanningReadRequest request,String nativeRequestId,BigDecimal deadlineMonotonic,
            BigDecimal initialRemainingSeconds,Status status,Optional<Result> result,Optional<String> error) { }
    public static final class Captured {
        private final FrontendStartRootQueries owner;private final Record record;private final Optional<ExactRef> original;
        private Captured(FrontendStartRootQueries owner,Record record,Optional<ExactRef> original){this.owner=owner;this.record=record;this.original=original;}
        public Optional<Obj> field(){return record==null?Optional.empty():Optional.of(encode(record));}
        public Optional<ExactRef> original(){return original;}
    }
    private static final int MAXIMUM_BYTES=16384;
    private final RootRuntimeContext context;
    private final ReadContract<?> campaignRoot;
    private final RootRuntimeStorageGuard storage;
    private Captured latest=new Captured(this,null,Optional.empty());
    private boolean unavailable;
    public FrontendStartRootQueries(RootRuntimeContext actual,ReadContract<?> actualRoot,RootRuntimeStorageGuard actualStorage){
        context=Objects.requireNonNull(actual);campaignRoot=Objects.requireNonNull(actualRoot);storage=Objects.requireNonNull(actualStorage);
        if(!campaignRoot.operation().equals(GameplayEntryRoot.OPERATION))throw new IllegalArgumentException("actual Start campaign-root contract required");
    }
    public void requireOwner(ContinuityWriter writer,NativeOutcomeArchive archive,ReadContract<?> actualRoot)throws IOException {
        if(context.writer()!=writer||context.archive()!=archive||campaignRoot!=actualRoot)
            throw new IOException("Start root-query custody crossed its sole actual writer/archive/contract");
    }
    @Override public synchronized void prepared(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,
            String actualRequestId,NativeRequest prepared)throws IOException {
        require(same,contract,request);Objects.requireNonNull(prepared);
        if(actualRequestId==null||actualRequestId.isEmpty()||actualRequestId.length()>256)
            throw new IOException("actual bounded coordinator root-query request ID required");
        Duration remaining=Duration.between(context.clock().instant(),request.deadline());
        if(remaining.isNegative()||remaining.isZero())throw new IOException("Start root query deadline expired before submission");
        BigDecimal remainingSeconds=seconds(BigInteger.valueOf(remaining.getSeconds()).multiply(BigInteger.valueOf(1000000000L)).add(BigInteger.valueOf(remaining.getNano())));
        BigDecimal deadline=seconds(BigInteger.valueOf(System.nanoTime())).add(remainingSeconds);
        publish(same,new Record(request,actualRequestId,deadline,remainingSeconds,Status.PREPARED_NOT_SUBMITTED,Optional.empty(),Optional.empty()));
    }
    @Override public synchronized void received(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,
            String actualRequestId,NativeActionPort.DispatchOutcome actual)throws IOException {
        Record original=selected(same,contract,request,actualRequestId);Objects.requireNonNull(actual);
        if(actual instanceof NativeActionPort.AckReceived ack){
            Result result=ack.originalResultToken().isEmpty()?new Result(Nil.INSTANCE,Nil.INSTANCE):header(ack.originalResultToken().orElseThrow());
            publish(same,new Record(request,original.nativeRequestId(),original.deadlineMonotonic(),original.initialRemainingSeconds(),
                    Status.NATIVE_RESULT_RECEIVED,Optional.of(result),Optional.empty()));
        }
    }
    @Override public synchronized void known(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadResult.Known<?> actual)throws IOException {
        Objects.requireNonNull(actual);selected(same,contract,actual.receipt().request(),actual.receipt().requestId());
        if(latest.record.status()!=Status.NATIVE_RESULT_RECEIVED)throw new IOException("actual Start root query did not retain its native result before decode");
    }
    @Override public synchronized void failed(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,
            Optional<NativeActionPort.DispatchOutcome> actual,String reason)throws IOException {
        require(same,contract,request);Objects.requireNonNull(actual);Objects.requireNonNull(reason);
        if(unavailable)throw new IOException("actual Start root-query journal has an original unresolved persistence failure");
        // A guard refusal before native preparation did not create a native request. Never fabricate its ID.
        if(latest.record==null||!latest.record.request().equals(request))return;
        // As in the original producer, a received malformed result remains visibly received until full frame validation.
        if(latest.record.status()==Status.NATIVE_RESULT_RECEIVED)return;
        Record original=latest.record;
        boolean pending=actual.filter(value->value instanceof NativeActionPort.Unknown unknown&&unknown.rawReturn().isEmpty()).isPresent()
                &&!context.clock().instant().isBefore(request.deadline());
        String error=reason.length()<=2048?reason:reason.substring(0,2048);
        publish(same,new Record(request,original.nativeRequestId(),original.deadlineMonotonic(),original.initialRemainingSeconds(),
                pending?Status.NATIVE_RESULT_PENDING_AT_DEADLINE:Status.QUERY_FAILED,original.result(),Optional.of(error)));
    }
    /** Called by the actual effect only after strict same-frame root normalization/retention succeeded. */
    public synchronized void frameVerified(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadResult.Known<?> actual)throws IOException {
        Record original=selected(same,contract,actual.receipt().request(),actual.receipt().requestId());
        if(original.status()!=Status.NATIVE_RESULT_RECEIVED)throw new IOException("Start frame verification lacks its retained actual native result");
        GameplayEntryRoot.decode(actual.receipt());
        publish(same,new Record(original.request(),original.nativeRequestId(),original.deadlineMonotonic(),original.initialRemainingSeconds(),
                Status.CAMPAIGN_ROOT_FRAME_VERIFIED,original.result(),Optional.empty()));
    }
    public synchronized Captured capture(ContinuityStorePort.Session same)throws IOException {
        context.writer().requireSession(same);if(unavailable)throw new IOException("actual Start query record persistence is unresolved");return latest;
    }
    public synchronized void requireCurrent(ContinuityStorePort.Session same,Captured captured)throws IOException {
        context.writer().requireSession(same);
        if(unavailable||captured==null||captured.owner!=this||captured!=latest)throw new IOException("Start query custody changed during actual diagnostic capture");
        if(captured.original.isPresent()){
            RawJson actual=context.archive().withSession(same).loadMaterial(captured.original.orElseThrow());
            if(!java.util.Arrays.equals(actual.bytes(),OpportunityJson.encode(encode(captured.record))))
                throw new IOException("actual Start root query original bytes differ from sole retained record");
        }
    }
    private Record selected(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,String requestId)throws IOException {
        require(same,contract,request);
        if(unavailable||latest.record==null||!latest.record.request().equals(request)||!latest.record.nativeRequestId().equals(requestId))
            throw new IOException("Start root query callback lost its actual sole prepared request identity");return latest.record;
    }
    private void require(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(request);
        if(contract!=campaignRoot||!context.readCatalog().containsIdentity(campaignRoot)||!request.source().equals(context.source())
                ||!request.sessionId().equals(context.game().sessionId())||!request.before().game().equals(context.game().generation())
                ||!request.operation().equals(campaignRoot.operation())||!(request.origin() instanceof CommandOrigin.Gameplay))
            throw new IOException("actual Start root query crossed installed contract/source/Game/session/origin");
    }
    private void publish(ContinuityStorePort.Session same,Record record)throws IOException {
        byte[] bytes=OpportunityJson.encode(encode(record));if(bytes.length>MAXIMUM_BYTES)throw new IOException("bounded Start query diagnostic record exceeded");
        try{
            storage.incidentGuard(List.of(context.core().configuration().artifactRoot())).require(bytes.length);
            var archive=context.archive().withSession(same);ExactRef original=archive.preserveMaterial(new RawJson(bytes));
            if(!java.util.Arrays.equals(bytes,archive.loadMaterial(original).bytes()))throw new IOException("actual Start query original did not roundtrip");
            context.writer().requireSession(same);latest=new Captured(this,record,Optional.of(original));
        }catch(IOException|RuntimeException failure){unavailable=true;throw failure;}
    }
    private static Result header(RawJson actual)throws IOException {
        // The source envelope is already retained by the real transport. Read only the two scalar original header fields.
        Value status=Nil.INSTANCE,sequence=Nil.INSTANCE;
        try(var parser=org.xar.ck3.control.build.ControlBuild.strictMapper().getFactory().createParser(actual.bytes())){
            if(parser.nextToken()!=com.fasterxml.jackson.core.JsonToken.START_OBJECT)throw new IOException("actual campaign root result is not an object");
            while(parser.nextToken()!=com.fasterxml.jackson.core.JsonToken.END_OBJECT){
                String field=parser.currentName();parser.nextToken();
                if(field.equals("status")||field.equals("query_sequence")){
                    Value value=switch(parser.currentToken()){
                        case VALUE_NULL->Nil.INSTANCE;
                        case VALUE_STRING->new Text(parser.getText());
                        case VALUE_NUMBER_INT->new IntegerValue(parser.getBigIntegerValue());
                        case VALUE_TRUE->new Bool(true);case VALUE_FALSE->new Bool(false);
                        case VALUE_NUMBER_FLOAT->new DecimalValue(parser.getText());
                        default->throw new IOException("non-scalar actual campaign root diagnostic result header");
                    };
                    if(field.equals("status"))status=value;else sequence=value;
                }else parser.skipChildren();
            }
            return new Result(status,sequence);
        }
    }
    private static Obj encode(Record actual){
        var fields=new LinkedHashMap<String,Value>();fields.put("native_request_id",new Text(actual.nativeRequestId()));
        fields.put("status",new Text(actual.status().name().toLowerCase(java.util.Locale.ROOT)));
        fields.put("deadline_monotonic",decimal(actual.deadlineMonotonic()));fields.put("initial_remaining_seconds",decimal(actual.initialRemainingSeconds()));
        var frame=actual.request().before().frame();fields.put("snapshot_id",new Text(frame.snapshotId()));
        fields.put("native_revision",new IntegerValue(frame.identity().nativeRevision()));fields.put("date_raw",new IntegerValue(frame.identity().dateRaw()));
        fields.put("original_request_replayed",new Bool(false));
        actual.result().ifPresent(result->{fields.put("native_result_status",result.status());fields.put("native_query_sequence",result.querySequence());});
        actual.error().ifPresent(error->fields.put("error",new Text(error)));return new Obj(fields);
    }
    private static BigDecimal seconds(BigInteger nanos){return new BigDecimal(nanos,9);}
    private static DecimalValue decimal(BigDecimal value){String token=value.toPlainString();return new DecimalValue(token.indexOf('.')>=0?token:token+".0");}
}
