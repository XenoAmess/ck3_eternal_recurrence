package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Original three cash query arguments; missing and explicit null remain distinct DATA. */
public final class CashObservationPublicCodec {
    private CashObservationPublicCodec() { }
    public enum Presence { MISSING,NULL,VALUE }
    public record Nullable<T>(Presence presence,Optional<T> value) {
        public Nullable {Objects.requireNonNull(presence);Objects.requireNonNull(value);require((presence==Presence.VALUE)==value.isPresent(),"nullable cash argument presence differs");}
    }
    public enum Sampling { ENABLE("enable"),DISABLE("disable"),QUERY("query");
        private final String wire;Sampling(String value){wire=value;}public String wire(){return wire;}
    }
    public enum Window { SAME_OWNED_PROCESS_NO_LOAD("same_owned_process_no_load_v1");
        private final String wire;Window(String value){wire=value;}public String wire(){return wire;}
    }
    public enum Outcome { ENFORCE_DEMANDS("enforce_demands"),SURRENDER("surrender"),WHITE_PEACE("white_peace");
        private final String wire;Outcome(String value){wire=value;}public String wire(){return wire;}
    }
    public sealed interface Request permits Current,Construction,Termination { BigInteger expectedRevision(); }
    public record Current(BigInteger expectedRevision,Nullable<Sampling> sampling,Nullable<Window> window) implements Request {
        public Current {revision(expectedRevision);Objects.requireNonNull(sampling);Objects.requireNonNull(window);
            require(sampling.value().orElse(null)==Sampling.ENABLE?window.value().isPresent():window.value().isEmpty(),"enable alone requires the exact no-load window contract");}
    }
    public record Construction(BigInteger expectedRevision,BigInteger reserve,BigInteger commitments,int horizonMonths) implements Request {
        public Construction {revision(expectedRevision);require(reserve!=null&&commitments!=null&&reserve.signum()>=0&&commitments.signum()>=0&&horizonMonths>=1&&horizonMonths<=24,"nonnegative cash policy and horizon1..24 required");}
    }
    public record Termination(BigInteger expectedRevision,int warId,Outcome outcome) implements Request {
        public Termination {revision(expectedRevision);require(warId>0,"full positive native WarID required");Objects.requireNonNull(outcome);}
    }
    public record Response(RawJson originalNormalized) {public Response {Objects.requireNonNull(originalNormalized);PublicDataJson.object(originalNormalized);}}
    public static Current current(PublicBindings.Arguments args) {var n=input(args);shape(n,Set.of("expected_revision"),Set.of("payment_sampling","payment_window_contract"));
        return new Current(revision(n),nullable(n,"payment_sampling",Sampling.values()),nullable(n,"payment_window_contract",Window.values()));}
    public static Construction construction(PublicBindings.Arguments args) {var n=input(args);shape(n,Set.of("expected_revision","reserve_gold_raw","existing_commitment_gold_raw","horizon_months"),Set.of());
        require(n.get("horizon_months").isIntegralNumber(),"integer horizon required");int months=n.get("horizon_months").bigIntegerValue().intValueExact();
        return new Construction(revision(n),policy(n.get("reserve_gold_raw")),policy(n.get("existing_commitment_gold_raw")),months);}
    public static Termination termination(PublicBindings.Arguments args) {var n=input(args);shape(n,Set.of("expected_revision","war_id","outcome"),Set.of());
        require(n.get("war_id").isIntegralNumber(),"native int32 WarID required");return new Termination(revision(n),n.get("war_id").bigIntegerValue().intValueExact(),parse(n.get("outcome"),Outcome.values()));}
    private static ObjectNode input(PublicBindings.Arguments args) {require(args instanceof PublicBindings.Value,"cash query requires exact named arguments");return PublicDataJson.object(((PublicBindings.Value)args).original());}
    private static void shape(ObjectNode n,Set<String> required,Set<String> optional) {require(required.stream().allMatch(n::has),"required cash arguments missing");n.fieldNames().forEachRemaining(k->require(required.contains(k)||optional.contains(k),"unknown cash argument: "+k));}
    private static BigInteger revision(ObjectNode n){return PublicUnsigned64.parse(n.get("expected_revision"),PublicUnsigned64.Minimum.ONE,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);}
    private static void revision(BigInteger value){PublicUnsigned64.canonical(value,PublicUnsigned64.Minimum.ONE);}
    private static BigInteger policy(JsonNode n){require(n!=null&&!n.isNull(),"cash policy missing/null");if(n.isTextual()){require(n.textValue().matches("0|[1-9][0-9]{0,127}"),"canonical nonnegative cash policy required");return new BigInteger(n.textValue());}
        require(n.isIntegralNumber()&&n.bigIntegerValue().signum()>=0&&n.bigIntegerValue().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"unsafe policy integer must use exact decimal text");return n.bigIntegerValue();}
    private static <T extends Enum<T>> Nullable<T> nullable(ObjectNode n,String key,T[] values){return !n.has(key)?new Nullable<>(Presence.MISSING,Optional.empty()):n.get(key).isNull()?new Nullable<>(Presence.NULL,Optional.empty()):new Nullable<>(Presence.VALUE,Optional.of(parse(n.get(key),values)));}
    private static <T extends Enum<T>> T parse(JsonNode n,T[] values){require(n!=null&&n.isTextual(),"literal cash query choice required");for(T x:values){String v=x instanceof Sampling s?s.wire():x instanceof Window w?w.wire():((Outcome)x).wire();if(v.equals(n.textValue()))return x;}throw new IllegalArgumentException("unknown cash query literal");}
    public static RawJson encode(Response response){return CashObservationCodec.publicWire(response.originalNormalized());}
}
