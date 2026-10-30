package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

final class EventOptionAvailabilityTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static ObjectValue json(String text) { return object(parse(text.getBytes(StandardCharsets.UTF_8))); }
    private static ObjectValue observed(boolean valid) { return json("{\"status\":\"observed\",\"is_valid\":"+valid+"}"); }
    private static ObjectValue context() { return json("{\"schema\":\"current-event-window-context-v2\",\"schema_version\":2}"); }
    private static ObjectValue row(boolean enabled, ObjectValue gui) { return json("{\"enabled\":"+enabled+"}").with("gui_availability",gui); }
    private static ObjectNode request(boolean enabled, ObjectValue gui) throws Exception {
        try (InputStream resource=EventOptionAvailabilityTest.class.getResourceAsStream("/unhandledevent/unhandled-event-golden-v1.json.gz")) {
            assertNotNull(resource);
            try (var input=new GZIPInputStream(resource)) {
                ObjectNode request=((ObjectNode)JSON.readTree(input).get("plan_cases").get(0).get("request")).deepCopy();
                ObjectNode context=(ObjectNode)request.get("event_context");
                context.put("schema","current-event-window-context-v2").put("schema_version",2);
                ObjectNode row=context.putArray("options").addObject().put("rendered_index",0).put("native_option_index",0)
                    .put("shown",true).put("enabled",enabled).put("resolved_name","actual-option");
                row.set("gui_availability",JSON.readTree(encode(gui)));
                request.putArray("action_steps").add("select-event-option-1");
                return request;
            }
        }
    }
    private static UnhandledEventFallback.Plan plan(ObjectNode raw) throws Exception {
        return UnhandledEventFallback.planFirstDisplayed(UnhandledEventCodec.decodePlan(JSON.writeValueAsBytes(raw))).orElseThrow();
    }
    private static ObjectValue planned(UnhandledEventFallback.Plan plan) {
        return obj(f("plan",UnhandledEventCodec.legacyPlan(plan)), f("snapshot_id",RetainedJson.value(plan.binding().snapshotId())),
                f("revision",RetainedJson.value(plan.binding().revision())));
    }

    @Test void observedFalseBlocksRawTrueAcrossDecodePlanAndPersistedBefore() throws Exception {
        var plan=plan(request(true,observed(false)));
        assertNull(plan.selectedStep());
        assertEquals(UnhandledEventFallback.Phase.FIRST_RENDERED_DISABLED,plan.phase());
        assertEquals(Boolean.TRUE,plan.selection().enabled());
        assertEquals(new GuiAvailabilityObservation.Observed(false),plan.selection().guiAvailability());
        ObjectValue before=UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(planned(plan)),"v2-false","2026-10-31T00:00:00Z")).orElseThrow();
        assertEquals(observed(false),o(before,"selection").get("gui_availability"));
        assertEquals(before,parse(encode(before)));
        assertEquals(observed(false),o(((ArrayValue)o(before,"window_context").get("options")).values().getFirst()).get("gui_availability"));
    }
    @Test void observedTrueOverridesRawFalseWithoutChangingRawField() throws Exception {
        var plan=plan(request(false,observed(true)));
        assertEquals("select-event-option-1",plan.selectedStep());
        assertEquals(Boolean.FALSE,plan.selection().enabled());
        ObjectValue before=UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(planned(plan)),"v2-true","2026-10-31T00:00:00Z")).orElseThrow();
        assertEquals(b(false),o(before,"selection").get("enabled"));
        assertEquals(observed(true),o(before,"selection").get("gui_availability"));
    }
    @Test void unavailableReasonRetainsRawFallbackAndRoundTripsRequest() throws Exception {
        ObjectValue gui=json("{\"status\":\"unobserved\",\"reason\":\"native_read_unavailable\"}");
        var raw=request(true,gui); var input=UnhandledEventCodec.decodePlan(JSON.writeValueAsBytes(raw));
        assertEquals(input,UnhandledEventCodec.decodePlan(UnhandledEventCodec.encodeRequest(input)));
        assertEquals("select-event-option-1",plan(raw).selectedStep());
        assertNull(plan(request(false,gui)).selectedStep());
        assertEquals(gui,EventOptionAvailability.wire(input.context().options().getFirst().guiAvailability()));
    }
    @Test void v2MissingNullWrongBooleanUnknownReasonAndExtraKeysReject() throws Exception {
        for (Value invalid:List.of(NULL,new IntegerValue(java.math.BigInteger.ONE),
                json("{\"status\":\"observed\",\"is_valid\":1}"),
                json("{\"status\":\"observed\",\"is_valid\":false,\"reason\":\"native_read_unavailable\"}"),
                json("{\"status\":\"unobserved\",\"reason\":\"unknown\"}"))) {
            assertThrows(IllegalArgumentException.class,()->EventOptionAvailability.observation(context(),json("{\"enabled\":true}").with("gui_availability",invalid)));
        }
        assertThrows(IllegalArgumentException.class,()->EventOptionAvailability.observation(context(),json("{\"enabled\":true}")));
        ObjectNode raw=request(true,observed(false)); ((ObjectNode)raw.get("event_context").get("options").get(0)).remove("gui_availability");
        assertThrows(IllegalArgumentException.class,()->UnhandledEventCodec.decodePlan(JSON.writeValueAsBytes(raw)));
        ObjectValue legacy=json("{\"schema\":\"current-event-window-context-v1\",\"schema_version\":1}");
        assertInstanceOf(GuiAvailabilityObservation.LegacyNotReported.class,EventOptionAvailability.observation(legacy,json("{\"enabled\":true}")));
        assertThrows(IllegalArgumentException.class,()->EventOptionAvailability.observation(legacy,row(true,observed(false))));
    }
    @Test void persistedSelectionCannotReplaceBoundFalseWithTrue() throws Exception {
        var plan=plan(request(true,observed(false))); ObjectValue full=UnhandledEventCodec.legacyPlan(plan);
        ObjectValue capture=o(full,"unhandled_event_fallback"),selection=o(capture,"selection");
        full=full.with("selected_step",s("select-event-option-1")).with("unhandled_event_fallback",capture.with("selection",selection.with("gui_availability",observed(true))));
        ObjectValue forged=planned(plan).with("plan",full);
        assertThrows(IllegalArgumentException.class,()->UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(forged),"forged","2026-10-31T00:00:00Z")));
    }
    @Test void dedicatedIndependenceRouteUsesActualGuiAndCopiesRawObservationWhenChangingOption() throws Exception {
        ObjectValue fixture=objects(SourceReviewedEventConsumerTest.golden(),"cases").stream()
                .filter(value->"independence-false-none".equals(text(value,"name"))).findFirst().orElseThrow();
        ObjectValue plan=o(fixture,"plan"),capture=o(plan,"unhandled_event_fallback"),context=o(capture,"window_context");
        List<Value> rows=objects(context,"options").stream().map(value->(Value)value.with("enabled",b(false)).with("gui_availability",observed(true))).toList();
        context=context.with("schema",s("current-event-window-context-v2")).with("schema_version",i(2)).with("options",new ArrayValue(rows));
        ObjectValue original=capture.with("window_context",context).with("selection",o(capture,"selection").with("enabled",b(false)).with("gui_availability",observed(true)));
        plan=plan.with("unhandled_event_fallback",original);
        ObjectValue chosen=ExistingFactionEventPolicies.choose(plan,o(fixture,"snapshot"),SourceReviewedEventConsumerTest.steps(fixture));
        assertEquals(s("active_event_source_reviewed_independence_refusal"),chosen.get("phase"));
        ObjectValue selected=o(o(chosen,"unhandled_event_fallback"),"selection");
        assertEquals(i(2),selected.get("native_option_index"));assertEquals(b(false),selected.get("enabled"));
        assertEquals(observed(true),selected.get("gui_availability"));
        List<Value> blockedRows=rows.stream().map(value->i(2).equals(o(value).get("native_option_index"))?o(value).with("gui_availability",observed(false)):value).toList();
        ObjectValue negative=plan.with("unhandled_event_fallback",original.with("window_context",context.with("options",new ArrayValue(blockedRows))));
        assertEquals(negative,ExistingFactionEventPolicies.choose(negative,o(fixture,"snapshot"),SourceReviewedEventConsumerTest.steps(fixture)));
    }
}
