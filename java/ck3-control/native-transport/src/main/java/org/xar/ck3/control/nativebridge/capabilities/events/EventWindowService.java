package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec.*;

import java.math.BigInteger;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Public query delegates to the same installed collector contract as the ordinary planner. */
public final class EventWindowService {
    public static final String PUBLIC64_WIRE_ENCODING="xar.event-window-public64/v1";
    public record Query(int eventInstanceId, BigInteger expectedRevision) {
        public Query { Objects.requireNonNull(expectedRevision); need(eventInstanceId>0 && expectedRevision.signum()>=0 && expectedRevision.bitLength()<=64,"event query instance/revision outside contract"); }
    }
    public record Response(PlanningReadResult<EventPolicies.ReadPublication> observation) { public Response { Objects.requireNonNull(observation); } }
    /** Supplied by Root; obtains the actual current frame and same held-session snapshot, never caller JSON. */
    @FunctionalInterface public interface CurrentFrame { PlanningReadRequest current(Query query); }
    /** Optional original-packet DATA consumer; never changes the event result or submits another read. */
    @FunctionalInterface public interface LocatorCapture {
        EventOptionLocatorDiagnostics.Result capture(org.xar.ck3.control.application.action.PlanningReadReceipt receipt) throws IOException;
    }
    /** Root identifies this from held original hello/guard evidence, never from the historical context card. */
    @FunctionalInterface public interface VerifiedBuild { EventWindowModels.Build identify(PlanningRequest request); }
    public static RegisteredEventCore.ContextValidator validator(VerifiedBuild actualBuild) {
        Objects.requireNonNull(actualBuild);
        return (request,context)-> {
            var build=Objects.requireNonNull(actualBuild.identify(request));
            try {
                var current=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),new org.xar.ck3.control.application.action.OperationKey(EventWindowRead.STEP),request.observations().snapshot(),request.deadline());
                int event=EventWindowRead.activeEvent(current); var frame=request.before().frame();
                var decoded=EventWindowCodec.decode(new RawJson(RetainedJson.encode(context)),new EventWindowModels.Binding(build,frame.identity().nativeRevision(),frame.identity().dateRaw().intValueExact(),event));
                return Optional.of(RetainedJson.object(RetainedJson.parse(EventWindowCodec.encode(decoded).bytes())));
            } catch (IllegalArgumentException malformed) { return Optional.empty(); }
        };
    }
    public static final class ReadUnavailable extends IllegalStateException {
        private static final long serialVersionUID=1L;
        private final transient PlanningReadResult.Unavailable<?> original;
        ReadUnavailable(PlanningReadResult.Unavailable<?> original) { super(original.reason()); this.original=original; }
        public PlanningReadResult.Unavailable<?> original() { return original; }
    }
    private final PlanningReadPort reads;
    private final ReadContract<EventPolicies.ReadPublication> contract;
    private final CurrentFrame current;
    private final LocatorCapture locatorCapture;
    private volatile EventOptionLocatorDiagnostics.Result latestLocatorDiagnostic = missingLocator("event query not observed");
    public EventWindowService(PlanningReadPort reads, ReadContract<EventPolicies.ReadPublication> contract, CurrentFrame current) {
        this(reads, contract, current, receipt -> missingLocator("original event diagnostic capture not installed"));
    }
    public EventWindowService(PlanningReadPort reads, ReadContract<EventPolicies.ReadPublication> contract, CurrentFrame current, LocatorCapture locatorCapture) {
        this.reads=Objects.requireNonNull(reads); this.contract=Objects.requireNonNull(contract); this.current=Objects.requireNonNull(current);
        this.locatorCapture=Objects.requireNonNull(locatorCapture);
        need(contract.operation().value().equals(EventWindowRead.STEP),"exact event collector contract required");
    }
    /** At most the latest query DATA. The embedded request/sequence must be retained; this is no action or current-frame authority. */
    public EventOptionLocatorDiagnostics.Result latestLocatorDiagnostic() { return latestLocatorDiagnostic; }
    private static EventOptionLocatorDiagnostics.Unavailable missingLocator(String detail) {
        return new EventOptionLocatorDiagnostics.Unavailable(EventOptionLocatorDiagnostics.Reason.NO_MATCHING_NOTICE, detail);
    }
    public Response query_current_event_window_context_v1(Query query) {
        PlanningReadRequest request=Objects.requireNonNull(current.current(Objects.requireNonNull(query)));
        need(request.before().frame().revision().equals(query.expectedRevision()) && EventWindowRead.activeEvent(request)==query.eventInstanceId(),"public query differs from actual current event/frame");
        var observation=reads.read(contract,request);
        if(observation instanceof PlanningReadResult.Known<?> known) {
            try { latestLocatorDiagnostic=Objects.requireNonNull(locatorCapture.capture(known.receipt())); }
            catch(IOException | RuntimeException failure) {
                latestLocatorDiagnostic=new EventOptionLocatorDiagnostics.Unavailable(EventOptionLocatorDiagnostics.Reason.INVALID_DIAGNOSTIC,
                        "optional event diagnostic capture failed: "+failure.getMessage());
            }
        } else latestLocatorDiagnostic=missingLocator("original event read unavailable");
        return new Response(observation);
    }
    public PublicBindings.TypedBinding<Query,Response> install(PublicBindings bindings, ExactRef actualSource) {
        return bindings.register(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1,Query.class,Response.class,this::query_current_event_window_context_v1,EventWindowService::decode,EventWindowService::encode,
            new PublicRoutes.Target(EventWindowService.class.getName(),"query_current_event_window_context_v1",actualSource),PublicRoutes.Status.DELEGATED,"complete native event presentation; no option submission or effect-completeness claim");
    }
    public static Query decode(PublicBindings.Arguments arguments) {
        need(arguments instanceof PublicBindings.Value,"event query requires present object arguments; missing/null are rejected");
        var node=parse(((PublicBindings.Value)arguments).original()); exact(node,"event_instance_id expected_revision");
        return new Query(integer(node,"event_instance_id",1,Integer.MAX_VALUE),PublicUnsigned64.parse(field(node,"expected_revision"),
                PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL));
    }
    public static RawJson encode(Response response) {
        if (response.observation() instanceof PlanningReadResult.Unavailable<?> unavailable) throw new ReadUnavailable(unavailable);
        var known=(PlanningReadResult.Known<?>)response.observation();
        var publication=EventPolicies.ReadPublication.class.cast(known.value());
        // Internal/native publications and archived bytes retain their numeric uint64 domain.
        // Only the declared public roles cross to canonical decimal text; native IDs stay numbers.
        var result=publication.result();
        result=public64(result,"query_sequence",PublicUnsigned64.Minimum.ONE);
        result=public64(result,"snapshot_revision",PublicUnsigned64.Minimum.ONE);
        result=public64(result,"queried_revision",PublicUnsigned64.Minimum.ZERO);
        result=public64(result,"queried_native_revision",PublicUnsigned64.Minimum.ONE);
        result=result.with("current_event_window_context",public64(object(result.get("current_event_window_context")),"snapshot_revision",PublicUnsigned64.Minimum.ONE));
        var source=public64(object(result.get("source")),"revision",PublicUnsigned64.Minimum.ZERO);
        source=public64(source,"native_revision",PublicUnsigned64.Minimum.ONE);result=result.with("source",source);
        var binding=public64(object(result.get("binding")),"revision",PublicUnsigned64.Minimum.ZERO);
        binding=public64(binding,"native_revision",PublicUnsigned64.Minimum.ONE);
        binding=public64(binding,"expected_revision",PublicUnsigned64.Minimum.ZERO);result=result.with("binding",binding);
        need(!result.members().containsKey("event_window_wire_encoding"),"native event publication must not contain a public encoding marker");
        result=result.with("event_window_wire_encoding",new OpportunityJson.Text(PUBLIC64_WIRE_ENCODING));
        safePublicNumbers(result);
        return new RawJson(DriverJson.encode(result));
    }
    private static OpportunityJson.Obj object(OpportunityJson.Value value){return OpportunityJson.object(value,"original event public projection");}
    private static OpportunityJson.Obj public64(OpportunityJson.Obj value,String field,PublicUnsigned64.Minimum minimum){
        var number=OpportunityJson.integer(value.get(field),"original event uint64 "+field);
        return value.with(field,new OpportunityJson.Text(PublicUnsigned64.canonical(number,minimum)));
    }
    private static void safePublicNumbers(OpportunityJson.Value value){
        if(value instanceof OpportunityJson.IntegerValue integer)
            StrictJson.require(integer.value().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"undeclared unsafe integer in event public result");
        else if(value instanceof OpportunityJson.Obj object)object.members().values().forEach(EventWindowService::safePublicNumbers);
        else if(value instanceof OpportunityJson.Arr array)array.items().forEach(EventWindowService::safePublicNumbers);
    }
}
