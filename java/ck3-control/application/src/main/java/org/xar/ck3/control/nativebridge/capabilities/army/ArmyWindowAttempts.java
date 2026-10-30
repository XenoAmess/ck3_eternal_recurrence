package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.math.BigInteger;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual read-attempt facts only. This store neither submits commands nor writes a second Driver state. */
public final class ArmyWindowAttempts {
    public enum Status { PENDING, OBSERVED, FAILED }
    public interface Source {
        Snapshot current(ContinuityStorePort.Session same, Complete actual) throws IOException;
        void recordUnavailable(ContinuityStorePort.Session same, ReadContract<?> exact, PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> actual) throws IOException;
    }
    public record Snapshot(Optional<Attempt> overview, Optional<Attempt> results) {
        public Snapshot { Objects.requireNonNull(overview); Objects.requireNonNull(results); }
    }
    public static final class Attempt {
        private final ArmyWindowCodec.Kind kind; private final Context context; private final BigInteger generation;
        private final ReadContract<?> contract; private final PlanningReadRequest request; private final String requestId;
        private final Status status; private final Optional<String> error; private final ExactRef preparedRequest;
        private final Optional<ExactRef> originalOutcome;
        private Attempt(ArmyWindowCodec.Kind kind, Context context, BigInteger generation, ReadContract<?> contract,
                PlanningReadRequest request, String requestId, Status status, Optional<String> error,
                ExactRef preparedRequest, Optional<ExactRef> originalOutcome) {
            this.kind=Objects.requireNonNull(kind);this.context=Objects.requireNonNull(context);this.generation=UInt64.positive(generation).value();
            this.contract=Objects.requireNonNull(contract);this.request=Objects.requireNonNull(request);this.requestId=StrictJson.text(requestId);
            this.status=Objects.requireNonNull(status);this.error=Objects.requireNonNull(error);this.preparedRequest=Objects.requireNonNull(preparedRequest);this.originalOutcome=Objects.requireNonNull(originalOutcome);
            require((status==Status.PENDING)==originalOutcome.isEmpty(),"only an actually prepared pending read may lack an outcome");
            require((status==Status.FAILED)==error.isPresent(),"only a failed attempt carries its actual failure reason");
        }
        public ArmyWindowCodec.Kind kind(){return kind;} public OperationKey operation(){return request.operation();}
        public String requestId(){return requestId;} public Status status(){return status;}
        public ExactRef preparedRequest(){return preparedRequest;} public Optional<ExactRef> originalOutcome(){return originalOutcome;}
        public List<ExactRef> supportingEvidence(){var refs=new java.util.ArrayList<ExactRef>();refs.add(preparedRequest);originalOutcome.ifPresent(refs::add);return List.copyOf(refs);}
        /** Exact original Python attempt fields; source and outcome custody remain separate typed facts. */
        public Obj normalized(){
            var n=ArmyJson.empty();String suffix=kind==ArmyWindowCodec.Kind.OVERVIEW?"war-declared-overview":"war-results-window";
            n.put("validation_schema",suffix+"-query-attempt-v1").put("step",operation().value()).put("native_request_id",requestId).put("status",status.name().toLowerCase(java.util.Locale.ROOT));
            if(error.isPresent())n.put("error",error.orElseThrow());else n.putNull("error");
            var frame=context.before().frame();n.put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision()).put("queried_native_revision",context.nativeRevision()).put("queried_date_raw",context.dateRaw()).put("queried_actor_character_id",context.playerId()).put("queried_connection_generation",generation);
            if(frame.episodeRunId()==null)n.putNull("queried_episode_run_id");else n.put("queried_episode_run_id",frame.episodeRunId());
            return OpportunityJson.object(OpportunityJson.parse(ArmyJson.bytes(n)),"actual fixed-window attempt");
        }
        private boolean same(Complete actual){return context.before().equals(actual.identity())&&context.source().equals(actual.source())&&context.sessionId().equals(actual.sessionId())&&generation.equals(actual.connectionGeneration());}
    }
    /** The native read owner holds this same instance across prepare, strict live decode and failed-read callbacks. */
    public static final class Store implements Source {
        private final OutcomeArchive archive; private final EnumMap<ArmyWindowCodec.Kind,Attempt> attempts=new EnumMap<>(ArmyWindowCodec.Kind.class);
        private final EnumMap<ArmyWindowCodec.Kind,String> unavailable=new EnumMap<>(ArmyWindowCodec.Kind.class);
        public Store(OutcomeArchive archive){this.archive=Objects.requireNonNull(archive);}
        public synchronized void prepared(ReadContract<?> exact, ArmyWindowCodec.Kind kind, Context context, BigInteger generation,
                PlanningReadRequest request, String actualRootRequestId, NativeRequest original){
            require(request.before().equals(context.before())&&request.source().equals(context.source())&&request.sessionId().equals(context.sessionId()),"window attempt prepare crossed actual source");
            require(request.operation().equals(exact.operation())&&original.step().equals(request.operation().value()),"window attempt prepare differs from its installed contract");
            require(kind.step(ArmyWindowCodec.Operation.QUERY).equals(original.step()),"window attempt kind differs from its actual prepared operation");
            ExactRef ref=archive.preserveRequest(original);require(archive.loadRequest(ref).equals(original),"prepared window request original did not round trip");
            attempts.put(kind,new Attempt(kind,context,generation,exact,request,actualRootRequestId,Status.PENDING,Optional.empty(),ref,Optional.empty()));unavailable.remove(kind);
        }
        public synchronized void observed(ReadContract<?> exact, PlanningReadReceipt receipt){
            Attempt old=find(exact,receipt.request());require(old!=null&&old.requestId.equals(receipt.requestId()),"observed window read has no identical actual prepared attempt");
            require(receipt.original().nativeOk(),"failed native response cannot be an observed strict window result");
            finish(old,Status.OBSERVED,Optional.empty(),receipt.original());
        }
        @Override public synchronized void recordUnavailable(ContinuityStorePort.Session same,ReadContract<?> exact,PlanningReadRequest request,PlanningReadResult.Unavailable<?> actual)throws IOException{
            Objects.requireNonNull(same).head();Objects.requireNonNull(actual);Attempt old=find(exact,request);if(old==null)return;
            // A later auxiliary publication failure cannot rewrite the already strictly observed native response.
            if(old.status!=Status.PENDING)return;
            if(actual.original().isEmpty()){unavailable.put(old.kind,"fixed-window failed read lacks its actual archived outcome: "+actual.reason());return;}
            if(!old.requestId.equals(actual.original().orElseThrow().requestId())){unavailable.put(old.kind,"fixed-window failed outcome request identity differs");return;}
            String error=actual.reason();if(error.length()>2048)error=error.substring(0,2048);finish(old,Status.FAILED,Optional.of(error),actual.original().orElseThrow());
        }
        private void finish(Attempt old,Status status,Optional<String> error,NativeActionPort.DispatchOutcome original){
            require(old.requestId.equals(original.requestId()),"window outcome request identity differs");ExactRef ref=archive.preserve(original);require(archive.load(ref).equals(original),"window actual outcome did not round trip");
            attempts.put(old.kind,new Attempt(old.kind,old.context,old.generation,old.contract,old.request,old.requestId,status,error,old.preparedRequest,Optional.of(ref)));unavailable.remove(old.kind);
        }
        private Attempt find(ReadContract<?> exact,PlanningReadRequest request){for(var value:attempts.values())if(value.contract==exact&&value.request.equals(request))return value;return null;}
        @Override public synchronized Snapshot current(ContinuityStorePort.Session same,Complete actual)throws IOException{
            Objects.requireNonNull(same).head();Objects.requireNonNull(actual);return new Snapshot(current(actual,ArmyWindowCodec.Kind.OVERVIEW),current(actual,ArmyWindowCodec.Kind.RESULTS));
        }
        private Optional<Attempt> current(Complete actual,ArmyWindowCodec.Kind kind)throws IOException{
            Attempt value=attempts.get(kind);if(value==null||!value.same(actual))return Optional.empty();if(unavailable.containsKey(kind))throw new IOException(unavailable.get(kind));
            return Optional.of(value);
        }
    }
    private ArmyWindowAttempts(){}
}
