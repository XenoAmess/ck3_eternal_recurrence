package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.governance.GovernanceCollector;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.lifestylesource.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic copied native inputs traverse the actual main normalizer and application consumer. No game qualification. */
final class LifestyleSourceProducerConsumerTest {
    private static final String EXE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final BigInteger BASE=new BigInteger("9223372036854780000");
    private static PlanningReadRequest request() {
        var now=Instant.parse("2026-10-23T19:00:00Z");var ref=new ExactRef("synthetic-lifestyle-input-no-native-qualification",1,"a".repeat(64));var source=new G2Source("xenoamess-full-tower-eb9d2c1186",now.toString(),"1.20.0.4",ref);
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(23),BigInteger.valueOf(100)),"public:100",BigInteger.valueOf(100),"source-facts-software"),1);
        return new PlanningReadRequest(before,source,"source-facts-session",new OperationKey(GovernancePlanningReads.STATE),new OpportunityJson.Obj(java.util.Map.of()),now.plusSeconds(30));
    }
    private static ObjectNode nativeLife() {
        return (ObjectNode)StrictJson.parse("""
            {"step":"private-query-player-lifestyle-current-state-v1","private_build":true,"advertised":false,"status":"available","episode_run_id":"source-facts-software","snapshot":{
              "private_build":true,"advertised":false,"status":"available","snapshot_id":"native:23","public_revision":23,"native_revision":23,"proof_epoch":23,"date_raw":100,"player_character_id":29829,
              "current_focus":{"presence":"absent"},"current_lifestyle_progress":{"presence":"absent"},"owned_perk_keys":[],"actor_traits":{"status":"available","observed_keys":[]},
              "legal_focus_candidates":{"status":"unavailable","reason":"not_requested","items":[]},"legal_perk_candidates":{"status":"unavailable","reason":"not_requested","items":[]},
              "readiness":{"current_focus_ready":true,"lifestyle_progress_ready":true,"owned_perks_ready":true,"legal_focus_candidates_ready":false,"legal_perk_candidates_ready":false,"same_frame_ready":true}}}
            """.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    private static ObjectNode predicate() {
        var packet=StrictJson.object().put("schema",LifestylePredicateSourceCodec.SCHEMA).put("read_only",true).put("target_key","cutting_corners_perk");var frame=packet.putObject("read_frame");
        frame.put("executable_sha256",EXE).put("module_base",BASE).put("snapshot_identity","native:23").putNull("frame_identity").put("query_sequence",71).put("mailbox_before_accepted",true).put("mailbox_after_accepted",true)
                .put("module_image_size",65536).put("module_time_date_stamp",123).put("public_revision",11).put("native_revision",23).put("proof_epoch",37).put("date_raw",100).put("played_character_id",29829).put("caller_domain","stock_perk_legality_12004").put("caller_snapshot_confirmed",true);
        packet.putNull("current_thread_tls_array_identity");var inputs=packet.putObject("inputs");for(String field:List.of("registry_identity","requested_full_character_id_u32","registry_capacity_u32","indexed_character_identity","indexed_character_full_id_u32","used_fallback","selected_character_identity","selected_character_magic_u32","selected_character_full_id_u32","selected_character_field_1d0_u64","selected_perk_identity","selected_perk_magic_u32","prefix_admitted"))inputs.putNull(field);
        inputs.put("command_identity",BASE.add(BigInteger.ONE)).put("registry_identity",0).put("used_fallback",true).put("selected_character_identity",BASE.add(BigInteger.TWO)).put("selected_character_magic_u32",0).put("prefix_admitted",false).put("unavailable_reason","");
        packet.putNull("tail").putNull("truth_trace").put("value",false).put("unavailable_reason","").put("native_can_select_before",false).put("native_can_select_after",false).put("repeated_source_match",true);return packet;
    }
    private static void consume(ObjectNode query) {GovernanceCollector.verifyLifestyleSourceFacts(request().before(),(OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(query)));}
    @Test void mainProducerAndConsumerPreserveRawUInt64AndRecomputeDecimalFactsUnderNativeIdentity() {
        var original=nativeLife();var copied=predicate();original.set(LifestylePredicateSourceCodec.WIRE_KEY,copied);original.set(LifestyleTriggerFrontierCodec.WIRE_KEY,StrictJson.object());byte[] before=StrictJson.canonical(original);
        var normalized=GovernancePlanningReads.life(original,request(),GovernancePlanningReads.STATE);assertArrayEquals(before,StrictJson.canonical(original));assertEquals("public:100",normalized.get("snapshot").get("snapshot_id").textValue());
        assertEquals(BASE,normalized.get(LifestylePredicateSourceCodec.WIRE_KEY).get("read_frame").get("module_base").bigIntegerValue());var facts=normalized.get(LifestylePredicateSourceCodec.FACTS_KEY);
        assertEquals(BASE.toString(),facts.get("read_frame").get("module_base").textValue());assertEquals("native:23",facts.get("read_frame").get("snapshot_identity").textValue());assertEquals("decoded",facts.get("status").textValue());assertFalse(facts.get("whole_parent_legality_decoded").booleanValue());
        assertEquals("invalid",normalized.get(LifestyleTriggerFrontierCodec.FACTS_KEY).get("status").textValue());assertDoesNotThrow(()->consume(normalized));
        var changed=normalized.deepCopy();((ObjectNode)changed.get(LifestylePredicateSourceCodec.FACTS_KEY).get("read_frame")).put("module_base",BASE);assertThrows(IllegalArgumentException.class,()->consume(changed));
    }
    @Test void optionalMissingAndExplicitNullKeepDifferentRawShapesAndNeitherCreatesFacts() {
        var missing=GovernancePlanningReads.life(nativeLife(),request(),GovernancePlanningReads.STATE);assertFalse(missing.has(LifestylePredicateSourceCodec.WIRE_KEY));assertFalse(missing.has(LifestylePredicateSourceCodec.FACTS_KEY));assertDoesNotThrow(()->consume(missing));
        var original=nativeLife();original.putNull(LifestylePredicateSourceCodec.WIRE_KEY).putNull(LifestyleTriggerFrontierCodec.WIRE_KEY);var nul=GovernancePlanningReads.life(original,request(),GovernancePlanningReads.STATE);
        assertTrue(nul.get(LifestylePredicateSourceCodec.WIRE_KEY).isNull());assertFalse(nul.has(LifestylePredicateSourceCodec.FACTS_KEY));assertFalse(nul.has(LifestyleTriggerFrontierCodec.FACTS_KEY));assertDoesNotThrow(()->consume(nul));
        nul.set(LifestylePredicateSourceCodec.FACTS_KEY,StrictJson.object().put("status","absent"));assertThrows(IllegalArgumentException.class,()->consume(nul));
    }
    @Test void publicSnapshotAliasCannotQualifyTheCopiedNativeInputAndPresetFactsAreRejected() {
        var original=nativeLife();var copied=predicate();((ObjectNode)copied.get("read_frame")).put("snapshot_identity","public:100");original.set(LifestylePredicateSourceCodec.WIRE_KEY,copied);
        var normalized=GovernancePlanningReads.life(original,request(),GovernancePlanningReads.STATE);assertEquals("invalid",normalized.get(LifestylePredicateSourceCodec.FACTS_KEY).get("status").textValue());assertDoesNotThrow(()->consume(normalized));
        original.set(LifestylePredicateSourceCodec.FACTS_KEY,StrictJson.object());assertThrows(IllegalArgumentException.class,()->GovernancePlanningReads.life(original,request(),GovernancePlanningReads.STATE));
    }
}
