package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Single native Gathering sampling parser. Sampling is capture control, never Army readiness. */
public final class ArmyGatheringCodec {
    public static final String QUERY="query-army-gathering-research-sampling-v1";
    public static final String ENABLE="enable-army-gathering-research-sampling-v1";
    public static final String DISABLE="disable-army-gathering-research-sampling-v1";
    public enum Status { ENABLED, DISABLED, BUSY, CLEAR_PENDING }
    public enum Readiness { OFF, INFLIGHT, AWAITING_SAMPLE, RETAINED_OBSERVATION }
    public record State(boolean accepted,Status status,boolean enabled,boolean busy,boolean clearCompleted,
            BigInteger epoch,BigInteger activeCaptures,BigInteger retained,BigInteger qualified,Readiness readiness) {
        public State {
            Objects.requireNonNull(status);Objects.requireNonNull(readiness);
            for(BigInteger number:List.of(epoch,activeCaptures,retained,qualified))
                StrictJson.require(number!=null && number.signum()>=0 && number.bitLength()<=64,"native sampling uint64 required");
        }
    }
    private ArmyGatheringCodec() { }
    public static State decode(byte[] raw,String expectedStep) {
        StrictJson.require(Set.of(QUERY,ENABLE,DISABLE).contains(expectedStep),"unknown native Gathering sampling step");
        ObjectNode n=StrictJson.object(StrictJson.parse(raw),Set.of("step","accepted","status","army_gathering_research_sampling_v1","backend_id"));
        same(n.get("step"),expectedStep);same(n.get("backend_id"),"native-headless");
        ObjectNode v=StrictJson.object(n.get("army_gathering_research_sampling_v1"),Set.of("capture_enabled","busy","clear_completed","epoch","active_captures","retained_records","qualified_records","readiness"));
        boolean enabled=bool(v.get("capture_enabled")),busy=bool(v.get("busy")),clear=bool(v.get("clear_completed"));
        BigInteger epoch=u64(v.get("epoch")),active=u64(v.get("active_captures")),retained=u64(v.get("retained_records")),qualified=u64(v.get("qualified_records"));
        StrictJson.require(qualified.compareTo(retained)<=0 && retained.compareTo(BigInteger.valueOf(64))<=0,"gathering journal bounds");
        StrictJson.require(busy==(active.signum()>0),"gathering busy counter mismatch");
        StrictJson.require(!clear || !enabled && active.signum()==0 && retained.signum()==0,"gathering clear state mismatch");
        Status status=enabled?Status.ENABLED:busy?Status.BUSY:clear?Status.DISABLED:Status.CLEAR_PENDING;
        same(n.get("status"),status.name().toLowerCase(Locale.ROOT));
        Readiness readiness=!enabled?Readiness.OFF:busy?Readiness.INFLIGHT:qualified.signum()==0?Readiness.AWAITING_SAMPLE:Readiness.RETAINED_OBSERVATION;
        same(v.get("readiness"),readiness.name().toLowerCase(Locale.ROOT));
        boolean accepted=bool(n.get("accepted"));
        StrictJson.require(accepted==(expectedStep.equals(QUERY)||status==Status.ENABLED||status==Status.DISABLED),"gathering accepted/status mismatch");
        if(!expectedStep.equals(QUERY) && accepted)
            StrictJson.require(enabled==expectedStep.equals(ENABLE) && (enabled || clear),"gathering control actual state differs from selected operation");
        return new State(accepted,status,enabled,busy,clear,epoch,active,retained,qualified,readiness);
    }
    private static BigInteger u64(JsonNode value) { return StrictJson.integer(value,BigInteger.ZERO,StrictJson.UINT64_MAX); }
    private static boolean bool(JsonNode value) { StrictJson.require(value!=null && value.isBoolean(),"explicit native sampling Boolean required");return value.booleanValue(); }
    private static void same(JsonNode value,String expected) { StrictJson.require(expected.equals(StrictJson.text(value)),"native sampling token differs"); }
}
