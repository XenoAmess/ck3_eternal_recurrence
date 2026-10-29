package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.service.mcp.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/** Original descriptors are mandatory. These software fixtures grant no Native, install, or Game acceptance. */
final class RootReligionPublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("D:/software-fixture/Religion.java",1,"a".repeat(64));
    @Test void originalFiftySixNamesAndAllArgumentContractsRemainDistinct() throws Exception {
        var descriptors=RootOriginalPublicTestInputs.tools();
        var originalNames=descriptors.stream().map(PublicMcpDirectory.ToolDescriptor::name).collect(java.util.stream.Collectors.toSet());
        assertEquals(56,ReligionCodec.methods().size());assertEquals(56,ReligionCodec.methods().stream().map(Method::name).distinct().count());
        for(Method method:ReligionCodec.methods()) {
            assertTrue(originalNames.contains(method.name()),"missing actual original descriptor: "+method.name());
            ObjectNode input=minimal(method);var value=ReligionCodec.decode(method.name(),ReligionCodec.raw(input));
            assertEquals(value,ReligionCodec.decode(method.name(),ReligionCodec.encode(value)),method.name());
            var wrong=input.deepCopy().put("alias",1);assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(method.name(),ReligionCodec.raw(wrong)));
        }
        assertNotEquals(ReligionCodec.method("ck3_query_player_holy_site_adoption_detail_v1"),ReligionCodec.method("ck3_query_player_holy_site_decision_detail_v1"));
    }
    @Test void actualPublicBindingProducerDispatchesOnlyItsThirteenRealReadAdapters() throws Exception {
        var calls=new ArrayList<String>();
        var bindings=RootReligionPublicProducts.bindings(SOURCE,request->{calls.add(request.method().name());return new Response(request.method(),ReligionCodec.raw(StrictJson.object().put("fixture",true)));});
        assertEquals(13,bindings.size());
        assertEquals(Set.copyOf(ReligionService.actualReadNames()),bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet()));
        for(var binding:bindings)exercise(binding);
        assertEquals(Set.copyOf(ReligionService.actualReadNames()),Set.copyOf(calls));
        assertFalse(bindings.stream().anyMatch(b->b.name().startsWith("ck3_submit_")||b.name().startsWith("ck3_confirm_")));
    }
    private static <Q,R> void exercise(McpExecutableDirectory.DirectBinding<Q,R> binding) throws Exception {
        var method=ReligionCodec.method(binding.name());var call=new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(ReligionCodec.raw(minimal(method)))),Optional.empty(),new McpCancellation());
        Q request=binding.decoder().decode(call);R result=binding.actual().invoke(request);assertNotNull(binding.encoder().encode(result));
    }
    @Test void publicRevisionUsesTheSharedExactU64GrammarAndKeepsOptionalPresence() {
        String name="ck3_query_player_religion_context_v1";
        var input=StrictJson.object().put("expected_revision","18446744073709551615");var request=ReligionCodec.decode(name,ReligionCodec.raw(input));
        assertEquals(new BigInteger("18446744073709551615"),request.expectedRevision());assertEquals(input,ReligionCodec.object(ReligionCodec.encode(request)));
        for(ObjectNode bad:List.of(StrictJson.object().put("expected_revision",true),StrictJson.object().put("expected_revision",1.0),StrictJson.object().put("expected_revision",9007199254740992L),StrictJson.object().putNull("expected_revision"),StrictJson.object()))assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(bad)));
        String tenets="ck3_query_player_religion_tenets_v1";
        var missing=ReligionCodec.decode(tenets,ReligionCodec.raw(StrictJson.object().put("expected_revision",1)));
        var explicitNull=ReligionCodec.decode(tenets,ReligionCodec.raw(StrictJson.object().put("expected_revision",1).putNull("target_rite_id")));
        assertNotEquals(missing,explicitNull);assertEquals(new Absent(Presence.MISSING),missing.value(Field.TARGET_RITE_ID));assertEquals(new Absent(Presence.NULL),explicitNull.value(Field.TARGET_RITE_ID));
        assertEquals(explicitNull,ReligionCodec.decode(tenets,ReligionCodec.encode(explicitNull)));
    }
    @Test void eventInstanceRetainsItsActualSigned32DomainAndSelectorsRejectAmbiguity() {
        String epidemic="ck3_query_player_epidemic_recovery_private_v1";
        var list=StrictJson.object().put("expected_revision",1).put("expected_event_instance_id",2147483647);assertNotNull(ReligionCodec.decode(epidemic,ReligionCodec.raw(list)));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(epidemic,ReligionCodec.raw(list.deepCopy().put("expected_event_instance_id",2147483648L))));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(epidemic,ReligionCodec.raw(list.deepCopy().put("requested_title_id",2))));
        String graph="ck3_query_confucian_challenger_graph_v1";var duplicate=StrictJson.object().put("expected_revision",1);duplicate.putArray("faith_full_ids").add(1).add(1);assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(graph,ReligionCodec.raw(duplicate)));
    }
    @Test void originalReadAlgorithmsAreReusedWithExplicitOriginalOnlyReplay() {
        var reads=new ArrayList<ReligionCapabilities.ReadSource>();for(var kind:ReligionCapabilities.ReadKind.values())reads.add(new ReligionCapabilities.ReadSource(kind,SOURCE));
        var actions=new ArrayList<ReligionCapabilities.ActionSource>();for(var kind:ReligionCapabilities.MutationSource.values())actions.add(new ReligionCapabilities.ActionSource(kind,SOURCE));
        var original=new ReligionCapabilities.Registration(reads,actions,List.of(),(kind,request)->{throw new AssertionError("no live read in a pure installation test");},(kind,command)->{throw new AssertionError("no action registration in this READ migration");});
        var fixed=ReligionService.fixedReads(original);assertEquals(12,fixed.size());
        for(var migrated:fixed){var base=original.readContracts().stream().filter(c->c.operation().value().equals(migrated.kind().step())).findFirst().orElseThrow();assertSame(base,migrated.contract());assertTrue(migrated.contract().hasPureReplay());}
        assertSame(original.creationContract(),fixed.stream().filter(r->r.kind()==ReligionCapabilities.ReadKind.CREATION).findFirst().orElseThrow().contract());
        assertSame(original.conversionResultContract(),fixed.stream().filter(r->r.kind()==ReligionCapabilities.ReadKind.RELIGION_RESULT).findFirst().orElseThrow().contract());
        for(var recon:List.of(original.conversionReconciliationContract(),original.countyReconciliationContract())){
            assertEquals(org.xar.ck3.control.application.action.ReadContract.GuardMode.RECONCILIATION_OBSERVATION,recon.guardMode());assertTrue(recon.hasPureReplay());
            assertFalse(fixed.stream().anyMatch(r->r.contract()==recon||r.contract().contractId().equals(recon.contractId())));
            var ordinary=fixed.stream().filter(r->r.contract().operation().equals(recon.operation())).findFirst().orElseThrow().contract();
            assertEquals(ordinary.sourceRef(),recon.sourceRef());assertEquals(ordinary.permissionKey(),recon.permissionKey());assertEquals(ordinary.wireProfile(),recon.wireProfile());
        }
    }
    @Test void fullNativeSelectorsRetainMethodSpecificSentinelAndProvinceBoundaries() {
        for(String suffix:List.of("hostility","conversion_inputs","conversion_terms","conversion_reasons")){
            String name="ck3_query_player_religion_"+suffix+"_v1";
            var input=StrictJson.object().put("expected_revision",1).put("target_rite_id",4294967295L);
            assertEquals(new BigInteger("4294967295"),ReligionCodec.decode(name,ReligionCodec.raw(input)).integer(Field.TARGET_RITE_ID));
            assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(input.deepCopy().put("target_rite_id",4294967296L))));
        }
        for(String name:List.of("ck3_query_player_religion_conversion_outcome_v1","ck3_convert_player_religion_private_v1")){
            var input=minimal(ReligionCodec.method(name)).put("target_rite_id",4294967295L);assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(input)));
        }
        for(String name:List.of("ck3_query_player_pilgrimage_planner_v1","ck3_submit_player_pilgrimage_planner_v1")){
            var input=minimal(ReligionCodec.method(name)).put("province_id",4294967294L);var exact=ReligionCodec.decode(name,ReligionCodec.raw(input));
            assertEquals(new BigInteger("4294967294"),exact.integer(Field.PROVINCE_ID));assertEquals(exact,ReligionCodec.decode(name,ReligionCodec.encode(exact)));
            assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(input.deepCopy().put("province_id",4294967295L))));
        }
        var county=minimal(ReligionCodec.method("ck3_submit_county_conversion_task")).put("province_id",2147483648L);assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode("ck3_submit_county_conversion_task",ReligionCodec.raw(county)));
    }
    @Test void resourceInputUsesExactCanonicalSigned64RangeAndPreservesNativeIntegerOperands() {
        String name="ck3_submit_player_pilgrimage_planner_v1";
        for(String field:List.of("reserve_gold_raw","reserve_treasury_raw","reserve_piety_raw","reserve_barter_goods_raw")){
            var input=minimal(ReligionCodec.method(name)).put(field,Long.toString(Long.MAX_VALUE));var request=ReligionCodec.decode(name,ReligionCodec.raw(input));
            assertEquals(Long.toString(Long.MAX_VALUE),ReligionCodec.object(ReligionCodec.encode(request)).get(field).textValue());assertTrue(ReligionCodec.nativeArguments(request).get(field).isIntegralNumber());
            for(ObjectNode bad:List.of(input.deepCopy().put(field,9007199254740992L),input.deepCopy().put(field,true),input.deepCopy().put(field,1.0),input.deepCopy().put(field,"01"),input.deepCopy().put(field,"9223372036854775808"),input.deepCopy().put(field,"-1")))assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(bad)));
            assertEquals(request,ReligionCodec.decode(name,ReligionCodec.encode(request)));
        }
    }
    @Test void tenetSelectorAndOriginalKnowledgeKeyValidationAreExact() {
        String name="ck3_query_player_religion_tenets_v1";var input=StrictJson.object().put("expected_revision",1).put("target_rite_id",4294967295L).put("tenet_key"," ");
        assertNotNull(ReligionCodec.decode(name,ReligionCodec.raw(input)));assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(input.deepCopy().putNull("target_rite_id"))));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(input.deepCopy().put("tenet_key",""))));assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(name,ReligionCodec.raw(input.deepCopy().put("tenet_key","界".repeat(43)))));
        String knowledge="ck3_query_player_religion_doctrine_knowledge_v1";assertNotNull(ReligionCodec.decode(knowledge,ReligionCodec.raw(StrictJson.object().put("expected_revision",1).put("doctrine_key"," "))));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(knowledge,ReligionCodec.raw(StrictJson.object().put("expected_revision",1).put("doctrine_key",""))));
        String creation="ck3_select_holy_site_creation_type_v1";
        assertNotNull(ReligionCodec.decode(creation,ReligionCodec.raw(StrictJson.object().put("expected_revision",1).put("type_key","界".repeat(53)))));
        assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(creation,ReligionCodec.raw(StrictJson.object().put("expected_revision",1).put("type_key","界".repeat(54)))));
    }
    @Test void everyRealReadUsesItsExactTypedU64PathsWithoutChangingNativeOriginals() {
        BigInteger maximum=new BigInteger("18446744073709551615");
        for(String name:ReligionService.actualReadNames()) {
            Method method=ReligionCodec.method(name);ObjectNode original=StrictJson.object().put("status",name.equals("ck3_query_player_religion_conversion_result_private_v1")?"submitted_verification_pending":"observed");
            for(var selected:ReligionCodec.resultIntegerPaths(method))at(original,selected.path()).put(selected.path().getLast(),maximum);
            original.putObject("unrelated").put("capture_epoch",2).putNull("snapshot_revision");
            ObjectNode presented=ReligionCodec.publicResult(method,original);
            for(var selected:ReligionCodec.resultIntegerPaths(method)) {
                var path=selected.path();assertTrue(at(original,path).get(path.getLast()).isIntegralNumber(),"native/archive operands must remain integers");
                assertEquals(maximum.toString(),at(presented,path).get(path.getLast()).textValue(),name+" "+path);
            }
            assertTrue(presented.get("unrelated").get("capture_epoch").isIntegralNumber());assertTrue(presented.get("unrelated").get("snapshot_revision").isNull());
            assertNotNull(PublicMcpDirectory.CallResult.fromBusinessJson(ReligionCodec.raw(presented)));
            assertEquals(presented,ReligionCodec.object(ReligionCodec.encode(new Response(method,ReligionCodec.raw(presented)))));
        }
    }
    @Test void resultCounterWrongTypesAndMissingFieldsDoNotBecomeDefaults() {
        Method method=ReligionCodec.method("ck3_query_player_holy_site_creation_context_v1");var source=StrictJson.object().put("queried_revision",1).put("queried_native_revision",2).put("snapshot_revision",2).put("capture_epoch",3);
        for(ObjectNode bad:List.of(source.deepCopy().put("capture_epoch",true),source.deepCopy().put("capture_epoch",1.0),source.deepCopy().putNull("capture_epoch"),source.deepCopy().put("capture_epoch",0),source.deepCopy().put("capture_epoch","01")))assertThrows(IllegalArgumentException.class,()->ReligionCodec.publicResult(method,bad));
        var missing=source.deepCopy();missing.remove("capture_epoch");assertThrows(IllegalArgumentException.class,()->ReligionCodec.publicResult(method,missing));
    }
    private static ObjectNode at(ObjectNode root,List<String> path) {
        ObjectNode current=root;
        for(int i=0;i<path.size()-1;i++){String part=path.get(i);if(!current.has(part))current.putObject(part);assertTrue(current.get(part).isObject());current=(ObjectNode)current.get(part);}
        return current;
    }
    @Test void liveCreationAndArtifactConsumersShareOneStrictPureComponentNormalizer() {
        ObjectNode unavailable=creationUnavailable();
        var value=HolySiteDecoders.creationBody(unavailable,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(29829));
        assertFalse(value.frame().availability().available());assertFalse(value.selectionAvailable());assertNull(value.selectedArtifacts());assertNull(value.nativeEnabled().value());
        var bad=unavailable.deepCopy().put("native_create_button_enabled",false);assertThrows(IllegalArgumentException.class,()->HolySiteDecoders.creationBody(bad,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(29829)));
        var missing=unavailable.deepCopy();missing.remove("selected_artifact_ids");assertThrows(IllegalArgumentException.class,()->HolySiteDecoders.creationBody(missing,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(29829)));
        var fractional=unavailable.deepCopy().put("capture_epoch",1.0);assertThrows(IllegalArgumentException.class,()->HolySiteDecoders.creationBody(fractional,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(29829)));
        var full=unavailable.deepCopy().put("played_character_id",-2);assertEquals(BigInteger.valueOf(-2),HolySiteDecoders.creationBody(full,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(-2)).frame().playerId());
        assertThrows(IllegalArgumentException.class,()->HolySiteDecoders.creationBody(full,BigInteger.valueOf(7),BigInteger.ONE,new BigInteger("4294967294")));
        var sentinel=unavailable.deepCopy().put("played_character_id",-1);assertThrows(IllegalArgumentException.class,()->HolySiteDecoders.creationBody(sentinel,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(-1)));
        var low=unavailable.deepCopy().put("played_character_id",Integer.MIN_VALUE);assertEquals(BigInteger.valueOf(Integer.MIN_VALUE),HolySiteDecoders.creationBody(low,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(Integer.MIN_VALUE)).frame().playerId());
        assertEquals(HolySiteDecoders.creationBody(full,BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(-2)),HolySiteDecoders.creationBody(ReligionCodec.object(ReligionCodec.raw(full)),BigInteger.valueOf(7),BigInteger.ONE,BigInteger.valueOf(-2)));
        assertThrows(IllegalArgumentException.class,()->HolySiteDecoders.creationBody(unavailable,BigInteger.valueOf(7),BigInteger.TWO,BigInteger.valueOf(29829)));
    }
    private static ObjectNode creationUnavailable() {
        var n=StrictJson.object().put("schema","ck3_12004_player_holy_site_creation_context_v1").put("game_version","1.20.0.4").put("executable_sha256",ReligionModels.Build.CROZIER4.sha256()).put("available",false).put("unavailable_reason","root_absent").put("capture_epoch",1).put("date_raw",1).put("played_character_id",29829).put("raw_scale",100000).put("read_only",true);
        for(String field:List.of("player_faith_id","window_present","root_present","window_faith_id","player_faith_matches","available_holy_site_types","potential_barony_title_ids","enshrinable_artifact_ids","selected_type_key","selected_barony_title_id","selected_artifact_ids","native_rarity_sum_raw","native_create_button_enabled","bypass_requirements_raw","normal_requirements_can_create","create_tooltip","cached_resource_vector_raw","native_affordable"))n.putNull(field);
        for(String field:List.of("models_available","models_complete","selection_available","native_rarity_sum_observed","native_enabled_observed","bypass_requirements_observed","normal_requirements_legality_observed","create_tooltip_available","cached_resource_quote_available","cached_quote_freshness_observed","native_affordability_observed","rendered_visibility_observed","action_ready","create_invoked"))n.put(field,false);
        return n;
    }
    private static ObjectNode minimal(Method method) {
        ObjectNode n=StrictJson.object();
        for(Field f:method.required())switch(f) {
            case EXPECTED_REVISION -> n.put(f.wire(),1);
            case ACTION -> n.put(f.wire(),"adopt");
            case FAITH_FULL_IDS -> n.putArray(f.wire()).add(1);
            case REPLACE_EXISTING_TASK -> n.put(f.wire(),false);
            case ACTION_ID,REQUEST_ID,SUBMITTED_REQUEST_ID -> n.put(f.wire(),"request-fixture");
            case EXPECTED_PREVIEW_IDENTITY_SHA256 -> n.put(f.wire(),"a".repeat(64));
            case TYPE_KEY -> n.put(f.wire(),"sacred_land");
            case OPERATION -> n.put(f.wire(),method.name().startsWith("ck3_submit_")?"open":"read");
            default -> n.put(f.wire(),1);
        }
        if(method.name().equals("ck3_query_player_epidemic_recovery_private_v1"))n.put("expected_event_instance_id",1);
        return n;
    }
}
