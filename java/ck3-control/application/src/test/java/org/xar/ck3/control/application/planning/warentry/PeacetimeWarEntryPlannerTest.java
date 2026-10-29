package org.xar.ck3.control.application.planning.warentry;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Complete original AST branch and real pure producers, with explicitly synthetic same-frame unit inputs. */
final class PeacetimeWarEntryPlannerTest {
    @Test void originalSelectorProducerGolden() throws IOException {
        JsonNode fixture=fixture();int count=0;
        for(JsonNode row:fixture.get("cases")) {
            Obj snapshot=object(row.get("snapshot"));List<Obj> history=new ArrayList<>();row.get("history").forEach(value->history.add(object(value)));
            Set<String> steps=new java.util.LinkedHashSet<>();row.get("steps").forEach(value->steps.add(value.textValue()));
            var actual=PeacetimeWarEntryPlanner.select(snapshot,history,steps);JsonNode expected=row.get("expected");String name=row.get("name").textValue();
            if(expected.isNull())assertTrue(actual.isEmpty(),name);else {
                ObjectNode observed=(ObjectNode)OpportunityJson.toNode(actual.orElseThrow());
                // Added complete selected identity is the sole intentional migration metadata extension.
                JsonNode selected=observed.remove("selected_declaration");
                if(selected!=null)for(String key:List.of("declaration_id","target_character_id","casus_belli_index","casus_belli_key","configuration_index","claimant_character_id","target_title_ids"))assertEquals(observed.get("declaration").get(key),selected.get(key),name+" selected identity "+key);
                if(OPTIONAL_FACTION_READ_CASES.contains(name))optionalFactionRead(expected,observed,name);
                else if(name.equals("faction-query")) {
                    ObjectNode updated=(ObjectNode)expected.deepCopy();
                    updated.put("reason","read current targeting and county-exposure faction danger before the bounded battle prior");
                    equivalent(updated,observed,name);
                } else equivalent(expected,observed,name);
            }
            count++;
        }
        assertTrue(count>=39,"all bounded producer cases must be present");
    }
    @Test void actualBoundedBattlePriorProducerGolden() throws IOException {
        JsonNode fixture=fixture();int count=0;
        for(JsonNode row:fixture.get("prior_cases")) {
            Obj forecast=PrewarBattlePrior.forecast(object(row.get("assessment")),row.get("declaration_id").textValue());
            equivalent(row.get("forecast"),OpportunityJson.toNode(forecast),row.get("name").textValue());
            equivalent(row.get("admission"),OpportunityJson.toNode(PrewarBattlePrior.admission(forecast)),"proxy admission never authorizes declaration");
            assertFalse(PrewarBattlePrior.admission(forecast).get("admitted") instanceof OpportunityJson.Bool b && b.value());count++;
        }
        assertTrue(count>=4);
    }
    @Test void integerAndReadinessDriftRemainUnobserved() throws IOException {
        JsonNode fixture=fixture();JsonNode original=null;
        for(JsonNode row:fixture.get("cases"))if(row.get("name").textValue().equals("general-actual-force-declare"))original=row.get("snapshot");
        assertNotNull(original);
        for(String fault:List.of("bool","float","readiness","source","overflow","extra")) {
            ObjectNode snapshot=(ObjectNode)original.deepCopy();ObjectNode payload=(ObjectNode)snapshot.get("war_entry_assessments");ObjectNode power=(ObjectNode)payload.get("assessments").get(0);
            switch(fault) {
                case "bool" -> power.put("native_flags_raw",true);
                case "float" -> power.set("actor_power_base_raw",new DecimalTokenNode("200000000.0"));
                case "readiness" -> ((ObjectNode)payload.get("readiness")).put("ready",false);
                case "source" -> ((ObjectNode)payload.get("provenance")).put("assessment_rva","0x1A23240");
                case "overflow" -> {power.put("actor_power_base_raw",Long.MAX_VALUE);power.put("actor_network_contribution_raw",1);power.put("actor_power_total_raw",Long.MIN_VALUE);}
                case "extra" -> power.put("uncontracted",1);
                default -> throw new AssertionError(fault);
            }
            Obj encoded=object(snapshot);
            if(fault.equals("float")) {
                Obj assessment=WarEntryJson.objects(WarEntryJson.child(encoded,"war_entry_assessments").get("assessments")).getFirst();
                var decimal=assertInstanceOf(OpportunityJson.DecimalValue.class,assessment.get("actor_power_base_raw"),
                        "the original floating-point fault must reach the real collector");
                assertEquals("200000000.0",decimal.token());
            }
            var recovered=WarEntryCollector.collect(encoded,List.of());assertTrue(recovered.assessments().isEmpty(),fault);
        }
    }
    @Test void completeCountyAlertOverridesTheZeroTargetingCountFastPath() throws IOException {
        JsonNode suite=fixture();JsonNode source=namedCase(suite,"general-actual-force-declare");
        ObjectNode baseline=(ObjectNode)source.get("snapshot").deepCopy();
        Set<String> steps=new java.util.LinkedHashSet<>();source.get("steps").forEach(value->steps.add(value.textValue()));
        assertEquals(new OpportunityJson.Text("query-player-faction-alerts-v1"),
                PeacetimeWarEntryPlanner.select(object(baseline),List.of(),steps).orElseThrow().get("selected_step"),
                "the installed optional read runs before treating count-only scope as complete");
        for(boolean exposed:List.of(true,false)) {
            ObjectNode snapshot=baseline.deepCopy();snapshot.set("player_faction_alerts",zeroTargetAlert(suite,exposed));
            var collected=WarEntryCollector.collect(object(snapshot),List.of());
            Obj context=WarEntryCollector.factionContext(collected.campaignRoot().orElseThrow(),collected.factionAlert().orElseThrow());
            assertEquals(new OpportunityJson.Text(exposed?"dangerous":"watch"),context.get("status"));
            assertEquals(new OpportunityJson.Bool(!exposed),context.get("prior_scope_eligible"));
            Obj selected=PeacetimeWarEntryPlanner.select(object(snapshot),List.of(),steps).orElseThrow();
            assertEquals(new OpportunityJson.Text(exposed?"NO_DECLARE":"DECLARE"),
                    OpportunityJson.object(selected.get("decision"),"decision").get("outcome"));
            assertEquals(new OpportunityJson.Text(exposed?"life-advance":"declare-war-909-17-0"),selected.get("selected_step"));
            assertEquals(context,selected.get("war_entry_faction_context"));
            if(exposed)assertEquals(new OpportunityJson.Arr(List.of(new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(2231)))),
                    context.get("exposed_county_title_ids"));
        }
    }
    @Test void aCurrentPartialCountyAlertIsRetainedWhenTheTargetingCountIsZero() throws IOException {
        JsonNode suite=fixture();JsonNode source=namedCase(suite,"general-actual-force-declare");
        ObjectNode snapshot=(ObjectNode)source.get("snapshot").deepCopy(),alert=zeroTargetAlert(suite,false);
        ((ObjectNode)alert.get("readiness")).put("county_exposure_ready",false).put("alert_ready",false);
        ((ObjectNode)alert.get("component_unavailable_reasons")).put("county_exposure","county_exposure_native_reader_not_frozen");
        ((ObjectNode)alert.get("planner_projection")).put("status","unavailable").putNull("present").putNull("dangerous");
        snapshot.set("player_faction_alerts",alert);
        Set<String> steps=new java.util.LinkedHashSet<>();source.get("steps").forEach(value->steps.add(value.textValue()));
        Obj selected=PeacetimeWarEntryPlanner.select(object(snapshot),List.of(),steps).orElseThrow();
        assertEquals(new OpportunityJson.Text("NO_DECLARE"),OpportunityJson.object(selected.get("decision"),"decision").get("outcome"));
        assertEquals(new OpportunityJson.Text("life-advance"),selected.get("selected_step"),
                "a current refusal is consumed instead of issuing the same optional query again");
        Obj context=OpportunityJson.object(selected.get("war_entry_faction_context"),"faction context");
        assertEquals(new OpportunityJson.Text("unavailable"),context.get("status"));
        assertEquals(new OpportunityJson.Bool(false),context.get("prior_scope_eligible"));
    }
    @Test void absentOptionalReadKeepsTheExistingCountOnlyFallback() throws IOException {
        JsonNode suite=fixture();
        for(String name:List.of("general-actual-force-declare","faction-query")) {
            JsonNode source=namedCase(suite,name);
            Set<String> steps=new java.util.LinkedHashSet<>();source.get("steps").forEach(value->steps.add(value.textValue()));
            assertTrue(steps.remove("query-player-faction-alerts-v1"));
            Obj selected=PeacetimeWarEntryPlanner.select(object(source.get("snapshot")),List.of(),steps).orElseThrow();
            assertEquals(new OpportunityJson.Text(name.equals("general-actual-force-declare")?
                    "declare-war-909-17-0":"life-advance"),selected.get("selected_step"),name);
        }
    }
    @Test void staleForeignAndUnboundAlertsRequireTheInstalledCurrentRead() throws IOException {
        JsonNode suite=fixture(),source=namedCase(suite,"general-actual-force-declare");
        ObjectNode baseline=(ObjectNode)source.get("snapshot").deepCopy();
        Set<String> steps=new java.util.LinkedHashSet<>();source.get("steps").forEach(value->steps.add(value.textValue()));
        for(String fault:List.of("revision","date","actor","provenance")) {
            ObjectNode snapshot=baseline.deepCopy(),alert=zeroTargetAlert(suite,true);
            switch(fault) {
                case "revision" -> alert.put("snapshot_revision",baseline.get("native_revision").bigIntegerValue().add(java.math.BigInteger.ONE));
                case "date" -> alert.put("date_raw",baseline.get("date_raw").intValue()+24);
                case "actor" -> alert.put("player_character_id",909);
                case "provenance" -> ((ObjectNode)alert.get("provenance")).put("executable_sha256","0".repeat(64));
                default -> throw new AssertionError(fault);
            }
            snapshot.set("player_faction_alerts",alert);
            assertTrue(WarEntryCollector.collect(object(snapshot),List.of()).factionAlert().isEmpty(),fault);
            assertEquals(new OpportunityJson.Text("query-player-faction-alerts-v1"),
                    PeacetimeWarEntryPlanner.select(object(snapshot),List.of(),steps).orElseThrow().get("selected_step"),fault);
        }
        for(String role:List.of("snapshot_id","revision","native_revision")) {
            ObjectNode result=StrictJson.object();result.set("player_faction_alerts",zeroTargetAlert(suite,true));
            for(String field:List.of("snapshot_id","revision","native_revision"))result.set("queried_"+field,baseline.get(field));
            if(role.equals("snapshot_id"))result.put("queried_snapshot_id","foreign-frame");
            else result.put("queried_"+role,baseline.get(role).bigIntegerValue().add(java.math.BigInteger.ONE));
            ObjectNode row=StrictJson.object().put("index",1).put("command","query-player-faction-alerts-v1").put("ok",true);
            row.set("result",result);List<Obj> history=List.of(object(row));
            assertTrue(WarEntryCollector.collect(object(baseline),history).factionAlert().isEmpty(),role);
            assertEquals(new OpportunityJson.Text("query-player-faction-alerts-v1"),
                    PeacetimeWarEntryPlanner.select(object(baseline),history,steps).orElseThrow().get("selected_step"),role);
            result.set("queried_"+role,baseline.get(role));history=List.of(object(row));
            Obj consumed=PeacetimeWarEntryPlanner.select(object(baseline),history,steps).orElseThrow();
            assertEquals(new OpportunityJson.Text("life-advance"),consumed.get("selected_step"),role+" bound danger");
            assertEquals(new OpportunityJson.Text("dangerous"),OpportunityJson.object(consumed.get("war_entry_faction_context"),"context").get("status"));
            assertEquals(consumed,OpportunityJson.object(OpportunityJson.parse(OpportunityJson.encode(consumed)),"roundtrip"));
        }
    }
    @Test void currentUnavailableReadIsConsumedInsteadOfReissued() throws IOException {
        JsonNode suite=fixture(),source=namedCase(suite,"general-actual-force-declare");
        ObjectNode snapshot=(ObjectNode)source.get("snapshot").deepCopy(),alert=zeroTargetAlert(suite,false);
        alert.put("status","unavailable").put("unavailable_reason","state_changed");
        alert.putNull("player_character_id");alert.putNull("targeting_faction_count");
        alert.remove("player_subrealm_geographic_counties_v1");
        ObjectNode ready=(ObjectNode)alert.get("readiness");
        for(String field:List.of("targeting_count_ready","identity_ready","targeting_rows_ready","county_exposure_ready",
                "stock_dangerous_predicate_ready","same_frame_ready","alert_ready","exact_ultimatum_timing_ready"))ready.put(field,false);
        ObjectNode projection=(ObjectNode)alert.get("planner_projection");
        projection.put("status","unavailable");projection.putNull("present");projection.putNull("dangerous");
        snapshot.set("player_faction_alerts",alert);
        Obj current=object(snapshot);
        assertTrue(WarEntryCollector.collect(current,List.of()).factionAlert().isPresent(),"valid same-frame refusal is retained");
        for(boolean canAdvance:List.of(true,false)) {
            Set<String> steps=new java.util.LinkedHashSet<>();source.get("steps").forEach(value->steps.add(value.textValue()));
            if(!canAdvance)assertTrue(steps.remove("life-advance"));
            Obj selected=PeacetimeWarEntryPlanner.select(current,List.of(),steps).orElseThrow();
            assertEquals(canAdvance?new OpportunityJson.Text("life-advance"):OpportunityJson.Nil.INSTANCE,
                    selected.get("selected_step"),"a retained refusal never selects the same query");
            if(canAdvance)assertEquals(new OpportunityJson.Text("NO_DECLARE"),
                    OpportunityJson.object(selected.get("decision"),"decision").get("outcome"));
            else assertEquals(new OpportunityJson.Text("native_war_entry_evidence_required"),selected.get("phase"));
            assertEquals(new OpportunityJson.Text("unavailable"),
                    OpportunityJson.object(selected.get("war_entry_faction_context"),"context").get("status"));
            assertEquals(selected,PeacetimeWarEntryPlanner.select(current,List.of(),steps).orElseThrow(),
                    "retrying the same DATA selector cannot turn a retained refusal into another query");
        }
    }
    private static final Set<String> OPTIONAL_FACTION_READ_CASES=Set.of(
            "general-actual-force-declare","general-force-query-required","claim-outside-county-general",
            "assessment-history-wins","root-legacy-game-rules-exception");
    /** Intentional strategy extension; the source-bound legacy archive remains unchanged. */
    private static void optionalFactionRead(JsonNode expected,ObjectNode actual,String name) {
        assertEquals(Set.of("policy","phase","selected_step","reason","declaration","war_entry_assessment",
                "war_entry_faction_context","required_capabilities"),fieldNames(actual),name+" query fields");
        assertEquals("one-life-turn-v1",actual.path("policy").textValue(),name);
        assertEquals("native_war_entry_faction_assessment",actual.path("phase").textValue(),name);
        assertEquals("query-player-faction-alerts-v1",actual.path("selected_step").textValue(),name);
        assertEquals("read current targeting and county-exposure faction danger before the bounded battle prior",
                actual.path("reason").textValue(),name);
        assertEquals(StrictJson.object().putArray("caps").add("game.command.query-player-faction-alerts-v1"),
                actual.get("required_capabilities"),name+" capability");
        for(String field:List.of("declaration","war_entry_assessment","war_entry_faction_context"))
            equivalent(expected.get(field),actual.get(field),name+" retained "+field);
    }
    private static Set<String> fieldNames(JsonNode value) {
        var fields=new java.util.TreeSet<String>();value.fieldNames().forEachRemaining(fields::add);return fields;
    }
    private static JsonNode namedCase(JsonNode suite,String name) {
        for(JsonNode candidate:suite.get("cases"))if(name.equals(candidate.get("name").textValue()))return candidate;
        throw new AssertionError("missing original producer case "+name);
    }
    /** Synthetic same-frame DATA for the existing native count/exposure independence contract. */
    private static ObjectNode zeroTargetAlert(JsonNode suite,boolean exposed) {
        ObjectNode alert=(ObjectNode)namedCase(suite,"faction-False-False").get("snapshot").get("player_faction_alerts").deepCopy();
        alert.put("targeting_faction_count",0);alert.putArray("targeting_factions");alert.putArray("county_exposures");
        ObjectNode planner=(ObjectNode)alert.get("planner_projection");
        planner.put("present",exposed).put("dangerous",exposed);planner.putArray("dangerous_faction_ids");planner.putArray("watch_faction_ids");
        planner.putArray("war_handoff_faction_ids");var counties=planner.putArray("exposed_county_title_ids");
        if(exposed) {
            ObjectNode row=StrictJson.object().put("county_title_id",2231).put("faction_id",33554434)
                    .put("faction_type_key","populist_faction").put("target_character_id",909)
                    .put("dangerous_by_stock_rule",true).put("danger_reason","player_county_in_powerful_liege_targeting_populist_faction");
            row.set("power",StrictJson.object().put("raw",8000000).put("scale",100000));
            row.set("power_threshold",StrictJson.object().put("raw",7500000).put("scale",100000));
            alert.withArray("county_exposures").add(row);counties.add(2231);
        }
        return alert;
    }
    private static Obj object(JsonNode value) {return OpportunityJson.object(OpportunityJson.parse(value.toString().getBytes(StandardCharsets.UTF_8)),"original producer input");}
    private static JsonNode fixture() throws IOException {
        try(InputStream source=PeacetimeWarEntryPlannerTest.class.getResourceAsStream("/warentry/original-producer-golden.zip")) {
            if(source==null)throw new IOException("missing source-bound original producer fixture");
            try(ZipInputStream zip=new ZipInputStream(source)) {
                var entry=zip.getNextEntry();if(entry==null || !entry.getName().equals("original-producer-golden.json"))throw new IOException("unexpected golden archive entry");
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int read;
                while((read=zip.read(buffer))!=-1) {if(bytes.size()+read>1048576)throw new IOException("bounded fixture exceeded");bytes.write(buffer,0,read);}
                if(zip.getNextEntry()!=null)throw new IOException("unexpected extra golden archive entry");return StrictJson.parse(bytes.toByteArray(),1048576);
            }
        }
    }
    private static void equivalent(JsonNode expected,JsonNode actual,String path) {
        assertNotNull(actual,path);
        if(expected.isObject()) {
            assertTrue(actual.isObject(),path);Set<String> a=new java.util.TreeSet<>(),b=new java.util.TreeSet<>();expected.fieldNames().forEachRemaining(a::add);actual.fieldNames().forEachRemaining(b::add);assertEquals(a,b,path+" fields");
            expected.fieldNames().forEachRemaining(key->equivalent(expected.get(key),actual.get(key),path+"."+key));
        }else if(expected.isArray()) {assertTrue(actual.isArray(),path);assertEquals(expected.size(),actual.size(),path);for(int i=0;i<expected.size();i++)equivalent(expected.get(i),actual.get(i),path+"["+i+"]");}
        else if(expected.isFloatingPointNumber()) {assertTrue(actual.isNumber(),path);assertEquals(expected.doubleValue(),actual.doubleValue(),1e-14,path);}
        else assertEquals(expected,actual,path);
    }
}
