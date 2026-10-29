package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReadCodec.*;

/** Source-admitted original H2743 DATA projection. Only the installed private Work port can use
 * this result for a live read. A VerifiedData constructor or decoded observation grants no permit. */
public final class ArmyWarSupplementalStockCodec {
    private ArmyWarSupplementalStockCodec(){ }
    public record StockEvidence(BigInteger applicationMainThreadId,BigInteger pumpEpoch,BigInteger mailboxSequence,
            boolean doubleSampleStable,boolean partiesBound){
        public StockEvidence{range(applicationMainThreadId,BigInteger.ONE,new BigInteger("4294967295"));range(pumpEpoch,BigInteger.ONE,StrictJson.UINT64_MAX);range(mailboxSequence,BigInteger.ONE,StrictJson.UINT64_MAX);}
    }
    private static final List<String> STOCK=List.of("short","long","border_raid_pair");
    private static final List<String> PREDICATES=List.of("attacker_flexible_truces_perk","attacker_government_is_nomadic","defender_government_is_nomadic","nomad_both","short","long","border_raid_pair");
    private static final Set<String> REASONS=Set.of("reader_disabled","wrong_session","read_failed","stale_identity","cache_unavailable","bounded_extent_exceeded","identifier_unavailable","phase_unavailable","definition_unavailable","unstable_sample");
    private static final Set<String> EVIDENCE=Set.of("schema","native_revision","date_raw","actor_character_id","war_id","attacker_character_id","defender_character_id","paused","map_ready","application_main_thread_id","pump_epoch","mailbox_sequence","executor_invocations","same_frame_stable","stock_double_sample_stable","stock_parties_bound","material_complete");

    public static DefenderStock normalize(Selection selected,RawJson original,RawJson beforeRaw,RawJson afterRaw,H2743StockPredicateAdmission.VerifiedData source){
        StrictJson.require(source!=null&&source.profile()==H2743StockPredicateAdmission.Profile.EXPLICIT_STOCK_RELEASE,"explicit verified stock source DATA required; no historical/boolean opt-in");
        H2743StockPredicateAdmission.validateSourceReceipt(source.sourceReceipt(),source.profile());
        StrictJson.require(kind(selected.operation())==Kind.DEFENDER_BASELINE&&id(selected.operation())==16777231,"original H2743 fixed target war required");
        ObjectNode before=object(beforeRaw),after=object(afterRaw);JsonNode war=target(before);StrictJson.require(war.equals(target(after)),"H2743 native baseline changed its paused war frame");
        for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))
            StrictJson.require(before.get(field).equals(after.get(field)),"H2743 native baseline crossed its original frame field: "+field);
        StrictJson.require(connection(before).equals(connection(after)),"H2743 native baseline crossed its original connection");
        exact(before.get("revision"),selected.original().before().frame().revision());exact(before.get("native_revision"),selected.context().nativeRevision());exact(before.get("date_raw"),selected.context().dateRaw());
        literal(before.get("snapshot_id"),selected.original().before().frame().snapshotId());literal(before.get("episode_run_id"),selected.original().before().frame().episodeRunId());
        ObjectNode raw=object(original);literal(raw.get("backend_id"),"native-headless");ObjectNode body=node(raw.get("defender_de_jure_exit_terms_v1"));
        exact(body.get("native_revision"),selected.context().nativeRevision());
        ObjectNode truce=node(body.get("truce_inputs_v1")).deepCopy();
        boolean observed=false;
        for(String name:PREDICATES){
            ObjectNode predicate=StrictJson.object(truce.get(name),Set.of("status","value","unavailable_reason"));
            String status=text(predicate.get("status"));
            if(status.equals("observed")){bool(predicate.get("value"));nil(predicate.get("unavailable_reason"));if(STOCK.contains(name))observed=true;}
            else{StrictJson.require(status.equals("unavailable"),"invalid admitted stock predicate status");nil(predicate.get("value"));String reason=text(predicate.get("unavailable_reason"));if(STOCK.contains(name))StrictJson.require(reason.startsWith("stock_condition_")&&REASONS.contains(reason.substring("stock_condition_".length())),"unknown admitted stock failure");}
        }
        ObjectNode evidence=StrictJson.object(body.get("h2743_stock_predicate_evidence_v1"),EVIDENCE);
        literal(evidence.get("schema"),H2743StockPredicateAdmission.EVIDENCE_SCHEMA);
        exact(evidence.get("native_revision"),selected.context().nativeRevision());exact(evidence.get("date_raw"),BigInteger.valueOf(53217264));
        for(String field:List.of("actor_character_id","defender_character_id"))exact(evidence.get(field),BigInteger.valueOf(29829));
        exact(evidence.get("attacker_character_id"),BigInteger.valueOf(30097));exact(evidence.get("war_id"),BigInteger.valueOf(16777231));
        for(String field:List.of("paused","map_ready","same_frame_stable"))StrictJson.require(bool(evidence.get(field)),"H2743 stock executor/frame evidence differs");
        StrictJson.require(!bool(evidence.get("material_complete")),"stock input is not complete material outcome");exact(evidence.get("executor_invocations"),BigInteger.ONE);
        var proof=new StockEvidence(integer(evidence.get("application_main_thread_id")),integer(evidence.get("pump_epoch")),integer(evidence.get("mailbox_sequence")),bool(evidence.get("stock_double_sample_stable")),bool(evidence.get("stock_parties_bound")));
        StrictJson.require(!observed||(proof.doubleSampleStable()&&proof.partiesBound()),"observed stock predicates lack stable bound native samples");
        ObjectNode storage=node(body.get("border_raid_storage_candidate_v1"));literal(storage.get("status"),"structural_candidate_only");

        // Reuse the existing sole Adapter for common baseline/parties/resources/storage/after-frame.
        // This explicit structural projection is DATA only; it is never archived as the native wire.
        // Admitted predicates/evidence stay separately validated above and are restored verbatim below.
        ObjectNode commonRaw=raw.deepCopy(),commonBody=(ObjectNode)commonRaw.get("defender_de_jure_exit_terms_v1");
        commonBody.remove("h2743_stock_predicate_evidence_v1");ObjectNode commonTruce=(ObjectNode)commonBody.get("truce_inputs_v1");
        for(String name:STOCK)commonTruce.set(name,StrictJson.object().put("status","unavailable").putNull("value").put("unavailable_reason","stock_condition_reader_unavailable"));
        DefenderBaseline common=normalizeBaseline(selected,json(commonRaw),beforeRaw,afterRaw);
        ObjectNode normalized=object(common.normalizedResult()),normalizedBody=(ObjectNode)normalized.get("defender_de_jure_exit_terms_v1");
        normalizedBody.set("truce_inputs_v1",truce);normalizedBody.set("h2743_stock_predicate_evidence_v1",evidence.deepCopy());
        normalized.put("queried_episode_run_id",text(before.get("episode_run_id"))).put("queried_connection_generation",connection(before));
        return new DefenderStock(selected,original,beforeRaw,afterRaw,common,source,proof,json(normalized));
    }
    /** The sole baseline formatter supplies all existing numeric roles, then only the declared new
     * stock uint64 paths are converted. Public shape is the original full response, with no marker. */
    public static RawJson fullDriverResult(DefenderStock actual){
        DefenderStock replay=normalize(actual.selection(),actual.nativeResult(),actual.before(),actual.after(),actual.source());
        StrictJson.require(replay.equals(actual),"admitted stock observation differs from its original source/frame normalizer");
        ObjectNode result=object(ArmyWarSupplementalReadCodec.fullDriverResult(actual.common()));
        ObjectNode body=(ObjectNode)result.get("defender_de_jure_exit_terms_v1"),normalized=object(actual.normalizedResult());
        ObjectNode actualBody=(ObjectNode)normalized.get("defender_de_jure_exit_terms_v1");body.set("truce_inputs_v1",actualBody.get("truce_inputs_v1").deepCopy());
        ObjectNode evidence=(ObjectNode)actualBody.get("h2743_stock_predicate_evidence_v1").deepCopy();
        for(String field:List.of("native_revision","pump_epoch","mailbox_sequence"))evidence.put(field,PublicUnsigned64.canonical(integer(evidence.get(field)),PublicUnsigned64.Minimum.ONE));
        body.set("h2743_stock_predicate_evidence_v1",evidence);result.set("queried_episode_run_id",normalized.get("queried_episode_run_id"));
        result.put("queried_connection_generation",PublicUnsigned64.canonical(integer(normalized.get("queried_connection_generation")),PublicUnsigned64.Minimum.ONE));
        return json(result);
    }
    private static JsonNode target(ObjectNode frame){
        StrictJson.require(bool(frame.get("map_ready"))&&bool(frame.get("paused")),"H2743 baseline requires map-ready paused frame");
        exact(frame.get("date_raw"),BigInteger.valueOf(53217264));literal(frame.get("episode_run_id"),"native-29829-2bc2d599f7f9");
        exact(frame.path("played_character").get("character_id"),BigInteger.valueOf(29829));
        StrictJson.require(integer(frame.get("revision")).signum()>0,"H2743 positive public revision required");range(integer(frame.get("native_revision")),BigInteger.ONE,StrictJson.UINT64_MAX);text(frame.get("snapshot_id"));connection(frame);
        JsonNode wars=frame.get("active_wars"),selected=null;int matches=0;StrictJson.require(wars!=null&&wars.isArray(),"H2743 actual active wars required");
        for(JsonNode war:wars)if(war.isObject()){
            JsonNode id=war.get("war_id");
            // Python's matching list uses numeric equality before its exact-integer check.
            // Equal float targets cannot disappear from duplicate detection.
            if(id!=null&&id.isNumber()&&id.decimalValue().compareTo(java.math.BigDecimal.valueOf(16777231))==0){
                selected=war;matches++;
            }
        }
        StrictJson.require(matches==1&&selected!=null,"H2743 target war absent or duplicated");exact(selected.get("war_id"),BigInteger.valueOf(16777231));literal(selected.get("player_side"),"defender");StrictJson.require(bool(selected.get("player_is_primary_war_leader")),"H2743 actual primary defender required");exact(selected.get("primary_opponent_character_id"),BigInteger.valueOf(30097));
        JsonNode titles=selected.get("targeted_title_ids");StrictJson.require(titles!=null&&titles.isArray()&&titles.size()==1,"H2743 target title differs");exact(titles.get(0),BigInteger.valueOf(2128));return selected;
    }
    private static BigInteger connection(ObjectNode frame){var value=integer(frame.path("diagnostics").get("connection_generation"));range(value,BigInteger.ONE,StrictJson.UINT64_MAX);return value;}
    private static ObjectNode node(JsonNode value){StrictJson.require(value instanceof ObjectNode,"stock object required");return (ObjectNode)value;}
    private static BigInteger integer(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber(),"exact stock integer required");return value.bigIntegerValue();}
    private static void exact(JsonNode value,BigInteger expected){StrictJson.require(integer(value).equals(expected),"stock native identity differs");}
    private static void range(BigInteger value,BigInteger low,BigInteger high){StrictJson.require(value!=null&&value.compareTo(low)>=0&&value.compareTo(high)<=0,"stock integer outside declared domain");}
    private static String text(JsonNode value){StrictJson.require(value!=null&&value.isTextual()&&!value.textValue().isEmpty(),"stock native text required");return value.textValue();}
    private static boolean bool(JsonNode value){StrictJson.require(value!=null&&value.isBoolean(),"stock boolean required");return value.booleanValue();}
    private static void nil(JsonNode value){StrictJson.require(value!=null&&value.isNull(),"stock explicit null required");}
    private static void literal(JsonNode value,String expected){StrictJson.require(text(value).equals(expected),"stock literal differs");}
}
