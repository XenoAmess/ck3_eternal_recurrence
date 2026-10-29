package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.PublicEventResolution;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Wire/metadata fixtures cross the actual shared codecs. They are not canonical Root or native authority. */
final class EventResolutionPublicResponseTest {
    @Test void actualMetadataAndExistingReceiptCodecKeepAckSeparateFromWindowAdvancement() {
        for(var outcome:ActionReceipt.Outcome.values())if(outcome!=ActionReceipt.Outcome.APPLIED_CONFIRMED)
            for(boolean ack:List.of(false,true)) {
                var base=EventOptionPublicResponse.parse(raw(packet(outcome,ack)));
                var result=EventResolutionPublicResponse.append(base,row("user-first-displayed-event-v1"));
                assertEquals(result.original(),EventResolutionPublicResponse.parse(result.original()).original());
                ObjectNode n=node(result.original());assertEquals(ack,n.path("action_receipt").path("ack_received").booleanValue());
                assertTrue(n.path("action_receipt").path("old_instance_advanced").isNull());
                assertTrue(n.path("action_receipt").path("after").isNull());assertFalse(n.path("event_material_result_available").booleanValue());
                assertEquals("user-first-displayed-event-v1",n.path("ordinary_events").get(0).path("strategy").textValue());
            }
    }
    @Test void originalVisibleOptionsAndNumericTokenDomainSurviveTheResolverExtension() {
        var original=DriverJson.object(("{\"event_index\":1,\"event_instance_id\":17,\"title\":null,\"visible_options\":["
                +"{\"index\":0,\"option_number\":1,\"label\":\"a\",\"enabled\":true,\"strategy_score\":-0.0},"
                +"{\"index\":1,\"option_number\":2,\"label\":\"b\",\"enabled\":true,\"strategy_score\":9007199254740993}],"
                +"\"selected_option_number\":2,\"selected_option_index\":1,\"selected_visible_text\":\"b\","
                +"\"strategy\":\"backend-neutral-event-v1\",\"source\":\"native\"}").getBytes(StandardCharsets.UTF_8),16384);
        var base=EventOptionPublicResponse.parse(raw(packet(ActionReceipt.Outcome.UNRESOLVED,true)));
        var output=EventResolutionPublicResponse.append(base,original);var domain=DriverJson.object(output.original().bytes(),1048576);
        assertEquals(original,((OpportunityJson.Arr)domain.get("ordinary_events")).items().getFirst());
        assertTrue(new String(output.original().bytes(),StandardCharsets.UTF_8).contains("-0.0"));
        assertTrue(new String(output.original().bytes(),StandardCharsets.UTF_8).contains("9007199254740993"));
        assertEquals(output.original(),EventResolutionPublicResponse.parse(output.original()).original());
    }
    @Test void appliedResultUsesTheOriginalMaterialInverseWithoutTreatingMetadataAsNativeMaterial() {
        ObjectNode packet=packet(ActionReceipt.Outcome.APPLIED_CONFIRMED,true);
        packet.put("event_material_result_available",true).put("event_material_wire_encoding",EventOptionPublicResponse.MATERIAL_ENCODING).put("progress_status","postcondition");
        var receipt=(ObjectNode)packet.get("action_receipt");receipt.put("old_instance_advanced",true);
        var after=((ObjectNode)receipt.get("before")).deepCopy();after.put("snapshot_id","wire-only-after").put("revision","18");receipt.set("after",after);
        packet.set("event_selection",StrictJson.object().put("selected_option_number",2).put("selected_native_option_index",1).put("old_event_instance_id",17)
                .put("postcondition_verified",true).put("status","event_instance_advanced").put("starting_revision","17").put("ending_revision","18")
                .put("starting_snapshot_id","wire-only-before").put("ending_snapshot_id","wire-only-after").put("episode_run_id","wire-only-episode"));
        var base=EventOptionPublicResponse.parse(raw(packet));var output=EventResolutionPublicResponse.append(base,row("registered-native-event-v1"));
        assertEquals(output.original(),EventResolutionPublicResponse.parse(output.original()).original());
        ObjectNode round=node(output.original());round.remove("ordinary_events");
        assertEquals(node(base.original()),round);
        var wrong=node(output.original());((ObjectNode)wrong.get("action_receipt")).putNull("old_instance_advanced");
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(wrong)));
    }
    @Test void changedSelectionMissingRowsAndUnknownMetadataFieldsRejectBeforePresentation() {
        var valid=EventResolutionPublicResponse.append(EventOptionPublicResponse.parse(raw(packet(ActionReceipt.Outcome.UNRESOLVED,true))),row("user-first-displayed-event-v1"));
        for(String field:List.of("event_index","event_instance_id","title","visible_options","selected_option_number","selected_option_index","selected_visible_text","strategy","source")) {
            var n=node(valid.original());((ObjectNode)n.get("ordinary_events").get(0)).remove(field);
            assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(n)),field);
        }
        for(String field:List.of("event_instance_id","selected_option_number","selected_option_index")) {
            var n=node(valid.original());((ObjectNode)n.get("ordinary_events").get(0)).put(field,true);
            assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(n)),field);
        }
        var extra=node(valid.original());((ObjectNode)extra.get("ordinary_events").get(0)).put("effect_verified",true);
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(extra)));
        var changed=node(valid.original());((ObjectNode)changed.get("ordinary_events").get(0)).put("selected_visible_text","changed");
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(changed)));
        var disabled=node(valid.original());((ObjectNode)disabled.get("ordinary_events").get(0).get("visible_options").get(1)).put("enabled",false);
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(disabled)));
        var duplicate=node(valid.original());((com.fasterxml.jackson.databind.node.ArrayNode)duplicate.get("ordinary_events")).add(duplicate.get("ordinary_events").get(0).deepCopy());
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(duplicate)));
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicResponse.parse(raw(packet(ActionReceipt.Outcome.UNRESOLVED,true))));
    }
    @Test void actualResolverRegistryUsesItsOwnTypedCodecAndNeverRegistersAnExplicitSelectorAlias()throws Exception {
        var result=EventResolutionPublicResponse.append(EventOptionPublicResponse.parse(raw(packet(ActionReceipt.Outcome.UNRESOLVED,true))),row("user-first-displayed-event-v1"));
        PublicBindings registry=new PublicBindings();AtomicInteger calls=new AtomicInteger();AtomicReference<EventResolutionPublicCodec.Request> observed=new AtomicReference<>();
        var binding=RootEventWindowPublicProducts.registerResolver(registry,request->{observed.set(request);calls.incrementAndGet();return result;},
                new ExactRef("wire-only-selected-helper-source",1,"a".repeat(64)));
        assertEquals(EventResolutionPublicCodec.Request.class,binding.requestType());assertEquals(EventResolutionPublicResponse.Payload.class,binding.resultType());
        assertEquals(PublicRoutes.Status.DELEGATED,binding.info().status());assertEquals("resolve_active_event",binding.info().target().orElseThrow().actualMethod());
        registry.freeze(Set.of(PublicMethod.RESOLVE_ACTIVE_EVENT));
        assertEquals(result.original(),binding.invoke(new PublicBindings.Missing()));assertEquals(1,calls.get());assertTrue(observed.get().expectedInstance().isEmpty());
        assertEquals(result.original(),binding.invoke(PublicBindings.present(raw("{\"event_instance_id\":17,\"expected_revision\":\"18446744073709551615\"}"))));
        assertEquals("18446744073709551615",observed.get().expectedPublicRevision().orElseThrow().toString());
        assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw("{\"expected_revision\":17}"))));assertEquals(2,calls.get());
        assertTrue(registry.lookup(PublicMethod.SELECT_EVENT_OPTION).isEmpty());assertTrue(registry.lookup(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1).isEmpty());
        assertThrows(IllegalArgumentException.class,()->RootEventWindowPublicProducts.registerResolver(registry,request->result,new ExactRef("source",1,"b".repeat(64))));
    }
    private static OpportunityJson.Obj row(String strategy) {
        var n=StrictJson.object().put("event_index",1).put("event_instance_id",17).putNull("title").put("selected_option_number",2)
                .put("selected_option_index",1).put("selected_visible_text","b").put("strategy",strategy).put("source","native");
        n.putArray("visible_options").add(StrictJson.object().put("index",0).put("option_number",1).put("label","a").put("enabled",true))
                .add(StrictJson.object().put("index",1).put("option_number",2).put("label","b").put("enabled",true));
        return PublicEventResolution.validateOrdinaryEvent(DriverJson.object(DriverJson.encodeNode(n),16384),17,2);
    }
    private static ObjectNode packet(ActionReceipt.Outcome outcome,boolean ack) {
        var n=StrictJson.object().put("step","select-event-option-2").put("option_number",2).put("option_index",1).put("event_instance_id",17)
                .put("event_material_result_available",false).put("status",outcome==ActionReceipt.Outcome.UNRESOLVED?"action_state_unknown":"event_action_not_applied");
        var r=n.putObject("action_receipt").put("schema",EventOptionPublicResponse.RECEIPT_SCHEMA).put("action_id","wire-only-action")
                .put("command_body_sha256","a".repeat(64)).put("sequence","1").put("canonical_outcome",outcome.name()).put("settled",outcome!=ActionReceipt.Outcome.UNRESOLVED)
                .put("ack_received",ack).put("machine_id","synthetic-machine").put("session_id","synthetic-session");
        if(ack)r.put("native_ok",true);else r.putNull("native_ok");r.putNull("old_instance_advanced").putNull("after");
        r.set("before",StrictJson.object().put("snapshot_id","wire-only-before").put("episode_run_id","wire-only-episode").put("revision","17")
                .put("native_revision","41").put("date_raw","24000").put("actor_character_id",707));
        r.set("original_receipt",new ExactRef("wire-only-not-canonical-proof",1,"b".repeat(64)).toJson());return n;
    }
    private static ObjectNode node(RawJson value) { return (ObjectNode)DriverJson.toNode(DriverJson.object(value.bytes(),1048576)); }
    private static RawJson raw(ObjectNode value) { return new RawJson(DriverJson.encodeNode(value)); }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
}
