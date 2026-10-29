package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.CombatEuJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Unchanged original producer -> all base and explicit three-action EU branches -> immutable JSON roundtrip. */
class CombatEntryEuContractParityTest {
    private static final ObjectMapper JSON=new ObjectMapper();
    private static ObjectNode original;
    private static final String CAPTURE="""
        import copy,json,runpy,sys
        from pathlib import Path
        root=Path(sys.argv[1]);m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_combat_decision_contract.py'))
        from xar_autoplayer.simulation.combat_decision_contract import assess_combat_entry_eu_contract,combat_entry_eu_contract,combat_entry_action_components_contract,COMBAT_ENTRY_EU_CONTRACT_SHA256,COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256,_canonical_digest
        high=m['_calculator_inputs']();low=m['_calculator_inputs'](wins=300,losses=650)
        fixtures={'empty':{'payload':{},'actions':None},'complete':{'payload':m['_complete_payload'](),'actions':None},'high':{'payload':high[0],'actions':high[1]},'low':{'payload':low[0],'actions':low[1]}}
        cases=[]
        def add(name,fixture,changes=(),rebind=False):
            pair=copy.deepcopy(fixtures[fixture]);p=pair['payload'];a=pair['actions']
            for target,path,value,delete in changes:
                current=p if target=='payload' else a;parts=path.strip('/').split('/')
                for key in parts[:-1]: current=current[int(key)] if isinstance(current,list) else current[key]
                key=int(parts[-1]) if isinstance(current,list) else parts[-1]
                if delete: del current[key]
                else: current[key]=value
            if rebind:
                digest=_canonical_digest(a['attack_trial_components_raw']);p['experiment']['per_trial_component_vector_sha256']=digest;a['per_trial_component_vector_sha256']=digest
            cases.append({'name':name,'fixture':fixture,'changes':changes,'rebind':rebind,'expected':assess_combat_entry_eu_contract(p,action_components=a)})
        def change(target,path,value=None,delete=False): return (target,path,value,delete)
        add('empty','empty');add('complete-base-off','complete');add('calculated-attack-off','high');add('calculated-wait-risk-off','low')
        add('missing-revision','complete',[change('payload','/identity/observation/revision',delete=True)])
        add('unknown-field','complete',[change('payload','/distribution/resolved_win_probability_raw',94736)])
        add('same-frame-drift','complete',[change('payload','/identity/forecast/native_revision',42)])
        add('bool-revision','complete',[change('payload','/identity/forecast/revision',True)])
        add('float-trial-count','complete',[change('payload','/experiment/trial_count',1000.0)])
        add('false-trial-count-double-error','complete',[change('payload','/experiment/trial_count',False)])
        add('named-false-fidelity','complete',[change('payload','/fidelity/ast_evaluator_ready',False),change('payload','/fidelity/original_trace_ready',False)])
        add('probability-and-accounting','complete',[change('payload','/distribution/no_resolution_probability_raw',0),change('payload','/experiment/no_resolution',0)])
        add('wrong-null-container','complete',[change('payload','/character_tails/player',None)])
        add('duplicate-army','complete',[change('payload','/identity/player_ordered_army_ids',[101,101])])
        add('lowercase-source-sha','complete',[change('payload','/experiment/input_sha256','a'*64)])
        add('quantile-order','complete',[change('payload','/distribution/battle_days/p10',99)])
        add('signed-campaign-boundary','complete',[change('payload','/campaign_feedback/reinforcement_route_raw',-(2**63))])
        add('signed-campaign-overflow','complete',[change('payload','/campaign_feedback/reinforcement_route_raw',2**63)])
        add('required-null-coefficient','complete',[change('payload','/utility_policy/coefficients_raw/player_win',None)])
        add('extra-coefficient','complete',[change('payload','/utility_policy/coefficients_raw/unmigrated_alias',0)])
        add('component-version','high',[change('actions','/version','old')])
        add('component-identity','high',[change('actions','/identity/target_province_id',2597)])
        add('component-source','high',[change('actions','/experiment_input_sha256','F'*64)])
        add('missing-alternative-costs','high',[change('actions','/alternatives/avoid/trial_components_raw',delete=True)])
        add('alternative-penalty-bool','high',[change('actions','/alternatives/avoid/uncertainty_penalty_raw',True)])
        add('alternative-negative-cost','high',[change('actions','/alternatives/wait_reinforce/opportunity_cost_raw',-1)])
        add('attack-negative-cost','high',[change('payload','/utility_policy/opportunity_cost_raw',-1)])
        add('distribution-counts','high',[change('payload','/distribution/player_win_probability_raw',89900),change('payload','/distribution/player_loss_probability_raw',5100)])
        add('wilson-counts','high',[change('payload','/distribution/resolved_win_wilson95/low_raw',87000)])
        add('trial-source-sha','high',[change('actions','/attack_trial_components_raw/0/player_win',0)])
        add('trial-one-hot','high',[change('actions','/attack_trial_components_raw/0/no_resolution',100000)],True)
        add('trial-boolean','high',[change('actions','/attack_trial_components_raw/0/battle_day',True)],True)
        add('trial-campaign-mean','high',[change('actions','/attack_trial_components_raw/0/battle_warscore',600000)],True)
        add('trial-day-noninteger','high',[change('actions','/attack_trial_components_raw/0/battle_day',1400001)],True)
        add('trial-tail-nonindicator','high',[change('actions','/attack_trial_components_raw/0/player_commander_death',1)],True)
        add('stack-wipe-risk','high',[change('payload','/distribution/player_stack_wipe_probability_raw',1001)])
        add('catastrophic-risk','high',[change('payload','/utility_policy/risk_constraints/max_player_one_life_catastrophic_probability_raw',0),change('payload','/character_tails/player_one_life_catastrophic_probability_raw',1)])
        add('strict-margin','high',[change('payload','/utility_policy/minimum_attack_margin_raw',230000)])
        add('tie-nonattack-source-order','high',[change('payload','/utility_policy/coefficients_raw/player_win',0),change('payload','/utility_policy/coefficients_raw/player_loss',0)])
        products=[(a,b,m['_signed_q100000_product'](a,b)) for a,b in [(-150000,1),(150000,-1),(-(2**63),2**63-1),(1,-99999),(-1,99999)]]
        print(json.dumps({'contract':combat_entry_eu_contract(),'action_contract':combat_entry_action_components_contract(),'contract_sha256':COMBAT_ENTRY_EU_CONTRACT_SHA256,'action_contract_sha256':COMBAT_ENTRY_ACTION_COMPONENTS_CONTRACT_SHA256,'fixtures':fixtures,'cases':cases,'products':products},separators=(',',':')))
        """;
    @BeforeAll static void captureActualOriginal() throws Exception {String root=required("xar.repository.root"),python=required("xar.python");pins(Path.of(root));Process p=new ProcessBuilder(python,"-I","-c",CAPTURE,root).redirectError(ProcessBuilder.Redirect.INHERIT).start();try{byte[] bytes=assertTimeoutPreemptively(Duration.ofSeconds(120),()->p.getInputStream().readAllBytes());assertTrue(p.waitFor(10,TimeUnit.SECONDS));assertEquals(0,p.exitValue(),"actual original EU producer failed");original=(ObjectNode)JSON.readTree(bytes);pins(Path.of(root));}finally{p.getInputStream().close();p.getOutputStream().close();if(p.isAlive()){p.destroyForcibly();assertTrue(p.waitFor(10,TimeUnit.SECONDS));}}}
    @Test void frozenActualInventoryAndSeparateActionContractHashesMatch(){assertTrue(same(original.get("contract"),OpportunityJson.toNode(CombatEntryEuContract.contract())));assertTrue(same(original.get("action_contract"),OpportunityJson.toNode(CombatEntryEuContract.actionComponentsContract())));assertEquals(original.path("contract_sha256").asText(),CombatEntryEuContract.CONTRACT_SHA256);assertEquals(original.path("action_contract_sha256").asText(),CombatEntryEuContract.ACTION_COMPONENTS_CONTRACT_SHA256);assertEquals(94,CombatEntryEuContract.REQUIRED.size());assertFalse(CombatEntryEuContract.ACTIVATION_ENABLED);for(JsonNode row:original.get("products"))assertEquals(row.get(2).bigIntegerValue(),product(row.get(0).bigIntegerValue(),row.get(1).bigIntegerValue()),"actual signed per-component product");}
    @Test void originalProducerAllBranchesAndAssessmentHashesMatch() throws Exception {assertTrue(original.path("cases").size()>=35);for(JsonNode c:original.get("cases")){ObjectNode pair=(ObjectNode)original.path("fixtures").get(c.path("fixture").asText()).deepCopy();for(JsonNode change:c.get("changes"))patch(pair,change);if(c.path("rebind").booleanValue()){ObjectNode payload=(ObjectNode)pair.get("payload"),actions=(ObjectNode)pair.get("actions");String sha=digest(actions.get("attack_trial_components_raw"));((ObjectNode)payload.get("experiment")).put("per_trial_component_vector_sha256",sha);actions.put("per_trial_component_vector_sha256",sha);}Obj payload=(Obj)value(pair.get("payload"));Value actions=pair.get("actions").isNull()?null:value(pair.get("actions"));Obj actual=CombatEntryEuContract.assess(payload,actions);JsonNode out=OpportunityJson.toNode(actual);assertTrue(same(c.get("expected"),out),()->c.path("name").asText()+"\nEXPECTED: "+c.get("expected")+"\nACTUAL: "+out);assertTrue(same(out,JSON.readTree(OpportunityJson.encode(actual))),"JSON roundtrip: "+c.path("name").asText());assertFalse(out.path("automatic_attack_enabled").booleanValue());assertTrue(out.get("selected_action").isNull());}}
    @Test void largeExplicitTapesBypassRequestParserLimitAndStillCalculate(){Obj payload=(Obj)value(original.path("fixtures").path("high").get("payload"));Value actions=value(original.path("fixtures").path("high").get("actions"));assertTrue(OpportunityJson.encode(actions).length>131072);JsonNode result=OpportunityJson.toNode(CombatEntryEuContract.assess(payload,actions));assertEquals("attack",result.path("candidate_action").asText());assertEquals(830000,result.path("eu_attack_raw").intValue());assertEquals(230000,result.path("attack_margin_raw").intValue());assertEquals("calculated_not_activated",result.path("status").asText());assertEquals(CombatEntryEuContract.assess(payload,null),CombatEntryEuContract.assess(payload,OpportunityJson.Nil.INSTANCE));}
    @Test void integerTokenContractRejectsLegacyFloatingSideEquality(){Obj payload=(Obj)value(original.path("fixtures").path("complete").get("payload"));Obj identity=(Obj)payload.get("identity");Obj malformed=payload.with("identity",identity.with("player_war_side",new OpportunityJson.DecimalValue("0.0")));JsonNode result=OpportunityJson.toNode(CombatEntryEuContract.assess(malformed));assertTrue(result.path("validation_errors").toString().contains("identity.player_war_side_invalid"));assertFalse(result.path("external_inputs_ready").booleanValue());assertThrows(IllegalArgumentException.class,()->CombatEntryEuContract.assess(null));}
    private static void patch(ObjectNode pair,JsonNode change){JsonNode current=pair.get(change.get(0).textValue().equals("payload")?"payload":"actions");String[] keys=change.get(1).textValue().substring(1).split("/");for(int i=0;i<keys.length-1;i++)current=current.isArray()?current.get(Integer.parseInt(keys[i])):current.get(keys[i]);String key=keys[keys.length-1];if(current.isArray()){ArrayNode row=(ArrayNode)current;int index=Integer.parseInt(key);if(change.get(3).booleanValue())row.remove(index);else row.set(index,change.get(2).deepCopy());}else{ObjectNode row=(ObjectNode)current;if(change.get(3).booleanValue())row.remove(key);else row.set(key,change.get(2).deepCopy());}}
    private static Value value(JsonNode node){if(node.isObject()){Map<String,Value> fields=new LinkedHashMap<>();node.properties().forEach(e->fields.put(e.getKey(),value(e.getValue())));return new Obj(fields);}if(node.isArray()){List<Value> items=new ArrayList<>();node.forEach(child->items.add(value(child)));return new OpportunityJson.Arr(items);}if(node.isIntegralNumber())return new OpportunityJson.IntegerValue(node.bigIntegerValue());if(node.isFloatingPointNumber())return new OpportunityJson.DecimalValue(node.toString());if(node.isBoolean())return new OpportunityJson.Bool(node.booleanValue());if(node.isNull())return OpportunityJson.Nil.INSTANCE;return new OpportunityJson.Text(node.textValue());}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException(key+" is required; original producer parity never skips");return value;}
    private static void pins(Path root) throws Exception {for(String pin:List.of("ck3_autonomous_player/src/xar_autoplayer/simulation/combat_decision_contract.py a2f008bbffb55e67c8dcab7974d3a7c52db882c8ce0c505cc9ba9e89f9b774f4","ck3_autonomous_player/src/xar_autoplayer/simulation/combat_core.py 15a9efce451e1830def6a7d93c87d0d00b7bb4e852fd75895780d289108a11b6","ck3_autonomous_player/tests/unit/test_combat_decision_contract.py 8f1eab391d4eac2da8b576fe2cf8c9a0f93fd4af8608e17d28c10712e89b4dd6")){String[] fields=pin.split(" ");Path file=root.resolve(fields[0]);assertTrue(Files.isRegularFile(file),"required source missing: "+file);byte[] bytes=Files.readAllBytes(file);String sha=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));assertEquals(fields[1],sha,"source SHA drifted: "+fields[0]);}}
}
