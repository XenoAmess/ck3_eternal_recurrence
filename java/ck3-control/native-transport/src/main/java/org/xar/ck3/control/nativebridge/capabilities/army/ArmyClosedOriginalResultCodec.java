package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Complete generic Driver projection from the same already installed Closed read. Pure replay, zero IO.
 * The original packet is retained; no dedicated Service result or synthetic reconstructed native DTO is used.
 */
public final class ArmyClosedOriginalResultCodec {
    private ArmyClosedOriginalResultCodec() { }
    public static RawJson encode(ArmyCalls.Call call,ArmyTypes.Context context,PlanningReadReceipt original,
            ArmyClosedReads.Observation observed,OpportunityJson.Obj actualSemantic) {
        Objects.requireNonNull(call);Objects.requireNonNull(context);Objects.requireNonNull(original);
        Objects.requireNonNull(observed);Objects.requireNonNull(actualSemantic);
        require(call.method()==PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1||call.method()==PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1,
                "original Closed result requires actual default-raise or directed truce selection");
        require(original.request().arguments().equals(DriverJson.object(ArmyCallCodec.encode(call).bytes(),DriverJson.MAX_NATIVE_BYTES)),
                "original Closed result changed its typed request");
        require(ArmyClosedReadCodec.decode(call,context,original).equals(observed),
                "original Closed result differs from the installed pure decoder");
        ObjectNode snapshot=object(OpportunityJson.toNode(actualSemantic));
        equal(get(snapshot,"snapshot_id"),context.before().frame().snapshotId());equal(get(snapshot,"revision"),context.before().frame().revision());
        equal(get(snapshot,"native_revision"),context.nativeRevision());equal(get(snapshot,"date_raw"),context.dateRaw());
        if(call instanceof ArmyCalls.Truce truce) {
            require(observed instanceof ArmyClosedReads.Truce,"actual typed directed-truce observation required");
            return ArmyLegacyTruceResultCodec.encode(truce,context,original);
        }
        require(observed instanceof ArmyClosedReads.DefaultRaise,"actual typed default-raise observation required");
        // normalize_player_default_raise_v1 returns dict(value); the sole native decoder already validates it.
        ObjectNode result=ArmyNativeReadEvidence.result(context,original).deepCopy();
        bind(result,"backend_id",empty().textNode("native-headless"));
        bind(result,"queried_snapshot_id",empty().textNode(context.before().frame().snapshotId()));
        bind(result,"queried_revision",empty().numberNode(context.before().frame().revision()));
        bind(result,"queried_native_revision",empty().numberNode(context.nativeRevision()));
        JsonNode episode=snapshot.get("episode_run_id");
        if(episode!=null&&!episode.isNull())equal(episode,context.before().frame().episodeRunId());
        bind(result,"queried_episode_run_id",nullable(episode));
        JsonNode diagnostics=snapshot.get("diagnostics");
        JsonNode connection=diagnostics!=null&&diagnostics.isObject()?diagnostics.get("connection_generation"):null;
        JsonNode pid=diagnostics!=null&&diagnostics.isObject()?diagnostics.get("bridge_pid"):null;
        if(connection!=null&&!connection.isNull()) {
            u64(connection);equal(connection,original.before().binding().connectionGeneration());
        }
        if(pid!=null&&!pid.isNull())range(pid,BigInteger.ZERO,BigInteger.valueOf(4294967295L));
        bind(result,"queried_connection_generation",nullable(connection));bind(result,"queried_bridge_pid",nullable(pid));
        return new RawJson(bytes(result));
    }
    private static JsonNode nullable(JsonNode value){return value==null?empty().nullNode():value;}
    private static void bind(ObjectNode result,String field,JsonNode exact) {
        if(result.has(field))require(get(result,field).equals(exact),"original Closed metadata conflicts with actual source: "+field);
        else result.set(field,exact.deepCopy());
    }
}
