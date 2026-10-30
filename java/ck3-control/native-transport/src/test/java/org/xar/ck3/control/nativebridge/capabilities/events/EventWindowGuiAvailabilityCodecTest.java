package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

final class EventWindowGuiAvailabilityCodecTest {
    private static Binding binding() { return new Binding(Build.CROZIER4,BigInteger.valueOf(17),741221,0x01000029); }
    private static RawJson raw(ObjectNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
    static ObjectNode packet(int version,boolean rawEnabled,boolean fallback) {
        ObjectNode value=EventWindowCodec.parse(new RawJson(("""
            {"schema":"current-event-window-context-v1","schema_version":1,"status":"available",
             "snapshot_revision":17,"date_raw":741221,"current_event_instance_id":16777257,"window_match_count":1,
             "unavailable_reason":null,"event_definition_key":"sample.1","calculated_event_id":1,"runtime_stats_ordinal":3,
             "root_scope":{"status":"available","raw_type_index":4,"type_key":"character","subtype":0,
                 "typed_identity":{"status":"available","kind":"character","character_id":42}},
             "saved_scopes":[],"options":[{"rendered_index":0,"native_option_index":0,"shown":true,"enabled":true,
                 "fallback":false,"cancel":false,"resolved_name":"Wait","unavailable_reason":"",
                 "effect_indicators":{"status":"available","coverage":"played-character-event-icon-indicators-1.20.0.4-v1","complete_effect_set":false,"rows":[]},
                 "effect_preview":{"status":"unavailable","reason":"indicator_subset_has_no_completeness_signal"},
                 "resource_deltas":{"status":"unavailable"},"relationship_deltas":{"status":"unavailable"}}],
             "readiness":{"event_definition_identity_ready":true,"root_scope_ready":true,"saved_scopes_ready":true,
                 "option_presentation_ready":true,"effect_indicators_ready":true,"effect_preview_ready":false,"semantic_decision_ready":false},
             "provenance":{"root":"module+0x5C6A520->+0x10","idler_vtable_rva":"0x44BC418","manager_offset":"+0x28","backend_id":"ck3-1.20.0.4-native-event-window-v1"}}
            """).getBytes(StandardCharsets.UTF_8)));
        value.put("schema","current-event-window-context-v"+version).put("schema_version",version);
        row(value).put("enabled",rawEnabled).put("fallback",fallback);
        return value;
    }
    private static ObjectNode row(ObjectNode packet) { return (ObjectNode)packet.path("options").get(0); }
    private static Option option(ObjectNode packet) {
        return ((Available)EventWindowCodec.decode(raw(packet),binding())).firstDisplayed().orElseThrow();
    }
    private static ObjectNode observed(int version,boolean rawEnabled,boolean fallback,boolean valid) {
        ObjectNode value=packet(version,rawEnabled,fallback);
        row(value).putObject("gui_availability").put("status","observed").put("is_valid",valid);
        return value;
    }
    @Test void v1KeepsBothRawFlagsAndDistinctNotReportedState() {
        for(boolean enabled:List.of(false,true)) {
            ObjectNode original=packet(1,enabled,!enabled);
            Option option=option(original);
            assertEquals(enabled,option.enabled());
            assertEquals(!enabled,option.fallback());
            assertInstanceOf(GuiAvailabilityObservation.LegacyNotReported.class,option.guiAvailability());
            assertEquals(enabled,option.selectionAllowed());
            Context decoded=EventWindowCodec.decode(raw(original),binding());
            assertArrayEquals(raw(original).bytes(),EventWindowCodec.encode(decoded).bytes());
        }
    }
    @Test void observedValidityCanDenyRawEnabledAndAllowFallbackWithRawDisabled() {
        ObjectNode denied=observed(2,true,false,false);
        Option first=option(denied);
        assertTrue(first.enabled()); assertFalse(first.selectionAllowed());
        assertEquals(new GuiAvailabilityObservation.Observed(false),first.guiAvailability());
        ObjectNode fallback=observed(2,false,true,true);
        Option second=option(fallback);
        assertFalse(second.enabled()); assertTrue(second.fallback()); assertTrue(second.selectionAllowed());
        assertEquals(new GuiAvailabilityObservation.Observed(true),second.guiAvailability());
        Context decoded=EventWindowCodec.decode(raw(fallback),binding());
        assertArrayEquals(raw(fallback).bytes(),EventWindowCodec.encode(decoded).bytes());
        assertEquals(decoded,EventWindowCodec.decode(EventWindowCodec.encode(decoded),binding()));
    }
    @Test void explicitUnobservedKeepsReasonAndUsesOnlyExistingRawFallback() {
        for(GuiAvailabilityObservation.Reason reason:GuiAvailabilityObservation.Reason.values()) {
            for(boolean enabled:List.of(false,true)) {
                ObjectNode packet=packet(2,enabled,false);
                row(packet).putObject("gui_availability").put("status","unobserved").put("reason",reason.wire());
                Option option=option(packet);
                assertEquals(new GuiAvailabilityObservation.Unobserved(reason),option.guiAvailability());
                assertEquals(enabled,option.selectionAllowed());
                assertNotEquals(new GuiAvailabilityObservation.Observed(enabled),option.guiAvailability());
            }
        }
    }
    @Test void exactVersionAndObservationTypesRejectMalformedPackets() {
        List<ObjectNode> invalid=new ArrayList<>();
        ObjectNode value=packet(2,true,false); invalid.add(value);
        value=packet(2,true,false); row(value).putNull("gui_availability"); invalid.add(value);
        value=observed(2,true,false,true); ((ObjectNode)row(value).get("gui_availability")).put("is_valid",1); invalid.add(value);
        value=observed(2,true,false,true); ((ObjectNode)row(value).get("gui_availability")).put("is_valid",1.0); invalid.add(value);
        value=observed(2,true,false,true); ((ObjectNode)row(value).get("gui_availability")).putNull("is_valid"); invalid.add(value);
        value=observed(2,true,false,true); ((ObjectNode)row(value).get("gui_availability")).put("extra",true); invalid.add(value);
        value=packet(2,true,false); row(value).putObject("gui_availability").put("status","unknown").put("is_valid",true); invalid.add(value);
        value=packet(2,true,false); row(value).putObject("gui_availability").put("status","unobserved").put("reason","invented"); invalid.add(value);
        value=observed(1,true,false,true); invalid.add(value);
        value=observed(2,true,false,true); value.put("schema_version",1); invalid.add(value);
        value=observed(2,true,false,true); value.put("schema_version",true); invalid.add(value);
        value=observed(2,true,false,true); value.put("schema_version",2.0); invalid.add(value);
        for(ObjectNode malformed:invalid) assertThrows(IllegalArgumentException.class,()->option(malformed),malformed::toString);
    }
}
