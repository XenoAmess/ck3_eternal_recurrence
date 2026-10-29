package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Original Python Driver result for four existing typed reads, before the public Service projection.
 * Pure receipt consumption: no frame acquisition, query, permit, cache publication or action submission.
 * Internal JSON retains exact integer roles; the public boundary must use its shared role-aware codec.
 */
public final class ArmyWarOriginalResultCodec {
    private ArmyWarOriginalResultCodec() { }
    private static final Set<PublicMethod> METHODS=Set.of(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
            PublicMethod.QUERY_WAR_TERMINATION_TERMS,PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS);

    public static RawJson encode(ArmyWarReadCodec.Scope scope,PlanningReadReceipt original,
            ArmyWarReadCodec.Observation observed) {
        Objects.requireNonNull(scope);Objects.requireNonNull(original);Objects.requireNonNull(observed);
        require(METHODS.contains(observed.method())&&scope.call().method()==observed.method(),
                "original war result requires one of the four actual typed reads");
        require(original.request().arguments().equals(DriverJson.object(ArmyCallCodec.encode(scope.call()).bytes(),DriverJson.MAX_NATIVE_BYTES)),
                "original war result changed its typed request");
        require(ArmyWarReadCodec.decode(scope,original).equals(observed),
                "original war result differs from the sole receipt decoder");
        ObjectNode raw=ArmyNativeReadEvidence.result(scope.context(),original);
        String domain=switch(observed.method()) {
            case QUERY_WAR_OCCUPATION_TARGETS_V1 -> "war_occupation_targets_v1";
            case QUERY_WAR_TERMINATION_OPTIONS -> "war_termination_options";
            case QUERY_WAR_TERMINATION_TERMS -> "war_termination_terms";
            case QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS -> "outbound_war_white_peace_status";
            default -> throw new IllegalArgumentException("original war read domain unavailable");
        };
        // Occupation has its own full original envelope decoder and permits the raw producer fields.
        // The other three original Driver methods explicitly close their six-field primitive result.
        if(!(observed instanceof ArmyWarReadCodec.Occupation)) {
            if(raw.has("backend_id"))closed(raw,"step","accepted","status","query_sequence",domain,"backend_id");
            else closed(raw,"step","accepted","status","query_sequence",domain);
        }
        ObjectNode result=object(OpportunityJson.toNode(observed.normalizedResult())).deepCopy();
        // Driver returns no Service-added outer war_id; the selected ID remains in the original domain.
        require(!result.has("war_id")||(raw.has("war_id")&&get(result,"war_id").equals(get(raw,"war_id"))),
                "Service war_id cannot replace the original Driver result");
        bind(result,"backend_id",empty().textNode("native-headless"));
        bind(result,"queried_snapshot_id",empty().textNode(scope.context().before().frame().snapshotId()));
        bind(result,"queried_revision",empty().numberNode(scope.context().before().frame().revision()));
        bind(result,"queried_native_revision",empty().numberNode(scope.context().nativeRevision()));
        if(observed instanceof ArmyWarReadCodec.Occupation) {
            bind(result,"read_only",empty().booleanNode(true));
            ObjectNode snapshot=object(OpportunityJson.toNode(scope.currentSnapshot()));
            var episode=snapshot.get("episode_run_id");
            if(episode!=null&&!episode.isNull())equal(episode,scope.context().before().frame().episodeRunId());
            bind(result,"queried_episode_run_id",episode==null?empty().nullNode():episode);
            var diagnostics=snapshot.get("diagnostics");
            var connection=diagnostics!=null&&diagnostics.isObject()?diagnostics.get("connection_generation"):null;
            if(connection!=null&&!connection.isNull()) {
                u64(connection);equal(connection,original.before().binding().connectionGeneration());
            }
            bind(result,"queried_connection_generation",connection==null?empty().nullNode():connection);
        }
        if(observed instanceof ArmyWarReadCodec.WhitePeace white) {
            equal(get(result,"status"),"available");positive(get(result,"query_sequence"));
            ObjectNode snapshot=object(OpportunityJson.toNode(scope.currentSnapshot()));
            var matches=array(get(snapshot,"active_wars"),ArmyJson::object).stream()
                    .filter(row->i32(get(row,"war_id"))==white.war()).toList();
            require(matches.size()==1&&full(get(matches.getFirst(),"primary_opponent_character_id")).equals(white.recipient()),
                    "original white-peace recipient differs from the actual selected war");
        }
        return new RawJson(bytes(result));
    }
    private static void bind(ObjectNode result,String field,com.fasterxml.jackson.databind.JsonNode exact) {
        if(result.has(field))require(get(result,field).equals(exact),"original Driver metadata conflicts with actual source: "+field);
        else result.set(field,exact.deepCopy());
    }
}
