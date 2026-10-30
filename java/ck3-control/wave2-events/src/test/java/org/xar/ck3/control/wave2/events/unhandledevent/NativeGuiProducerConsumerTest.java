package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;

/** Actual Native freeze03 serializer bytes in a software-only frame wrapper; no Game or Bridge. */
final class NativeGuiProducerConsumerTest {
    private record Result(byte[] original, ObjectValue context, UnhandledEventFallback.Plan plan, ObjectValue before) { }
    private static byte[] resource(String name) throws Exception {
        try(InputStream input=NativeGuiProducerConsumerTest.class.getResourceAsStream("/event-gui-v2/"+name)) {
            assertNotNull(input,"mandatory exact Native serializer fixture");return input.readAllBytes();
        }
    }
    private static Result consume(String name,String sha) throws Exception {
        byte[] original=resource(name);
        assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        ObjectValue context=object(parse(original));
        var binding=new EventWindowModels.Binding(EventWindowModels.Build.CROZIER2,integer(context.get("snapshot_revision")),
                integer(context.get("date_raw")).intValueExact(),integer(context.get("current_event_instance_id")).intValueExact());
        var typed=assertInstanceOf(EventWindowModels.Available.class,EventWindowCodec.decode(new RawJson(original),binding));
        assertArrayEquals(original,EventWindowCodec.encode(typed).bytes(),"typed Native codec retains original producer bytes");
        ObjectValue snapshot=obj(f("snapshot_id",s("software-freeze03-frame")),f("revision",i(1)),
                f("native_revision",context.get("snapshot_revision")),f("date_raw",context.get("date_raw")),
                f("episode_run_id",s("software-freeze03-not-Game")),f("connection_generation",i(1)),f("bridge_pid",i(1)),
                f("paused",b(true)),f("map_ready",b(true)),f("played_character",obj(f("character_id",i(42)))),
                f("active_event",obj(f("instance_id",context.get("current_event_instance_id")),f("option_count",i(1)))));
        ObjectValue request=obj(f("schema",s(UnhandledEventCodec.PLAN_SCHEMA)),f("snapshot",snapshot),f("event_context",context),
                f("event_summary",obj()),f("registry_decision",NULL),f("action_steps",new ArrayValue(List.of(s("select-event-option-1")))));
        var input=UnhandledEventCodec.decodePlan(encode(request));
        assertEquals(context,input.context().retainedWindowContext(),"all original context fields survive the consumer projection");
        assertEquals(typed.options().getFirst().guiAvailability(),input.context().options().getFirst().guiAvailability());
        assertEquals(input,UnhandledEventCodec.decodePlan(UnhandledEventCodec.encodeRequest(input)));
        var plan=UnhandledEventFallback.planFirstDisplayed(input).orElseThrow();
        ObjectValue planned=obj(f("snapshot_id",snapshot.get("snapshot_id")),f("revision",snapshot.get("revision")),
                f("plan",UnhandledEventCodec.legacyPlan(plan)));
        ObjectValue before=UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(planned),
                name,"2026-10-31T00:00:00Z")).orElseThrow();
        ObjectValue roundTrip=object(parse(UnhandledEventEvidenceJson.encodeBody(Optional.of(before))));
        assertEquals(before,roundTrip);
        assertEquals(context,o(roundTrip,"window_context"),"durable body retains the actual serializer context");
        assertArrayEquals(original,resource(name),"consumer never mutates the original Native fixture");
        assertFalse(yes(before,"dispatch_attempted"));
        return new Result(original,context,plan,before);
    }
    @Test void actualNativeObservedFalseRawTrueReachesBlockedPlanAndPersistentObservation() throws Exception {
        Result result=consume("callback-false-raw-enabled.v2.json","aecedbaae3c7765e2a392cbe2c7945ce9d6b384ca97c4c76b65b1d62c32c726b");
        assertTrue(result.plan().selection().enabled());
        assertEquals(new GuiAvailabilityObservation.Observed(false),result.plan().selection().guiAvailability());
        assertNull(result.plan().selectedStep());
        assertEquals(UnhandledEventFallback.Phase.FIRST_RENDERED_DISABLED,result.plan().phase());
        assertEquals(b(false),o(o(result.before(),"selection"),"gui_availability").get("is_valid"));
        assertEquals(BigInteger.ZERO,result.plan().selection().nativeOptionIndex());
    }
    @Test void actualNativeObservedTrueRawFalseFallbackTrueReachesSelectedPlanWithoutFlagRewrite() throws Exception {
        Result result=consume("raw-disabled-fallback-valid.v2.json","cedf65a62fc28ece6ee7a8bf013c05a2a964a11442a9683951cf8d0c4c4e4dde");
        ObjectValue originalRow=o(((ArrayValue)result.context().get("options")).values().getFirst());
        assertEquals(b(true),originalRow.get("fallback"));
        assertFalse(result.plan().selection().enabled());
        assertEquals(new GuiAvailabilityObservation.Observed(true),result.plan().selection().guiAvailability());
        assertEquals("select-event-option-1",result.plan().selectedStep());
        assertEquals(b(false),o(result.before(),"selection").get("enabled"));
        assertEquals(b(true),o(o(result.before(),"selection"),"gui_availability").get("is_valid"));
        assertEquals("Not today",text(originalRow,"unavailable_reason"));
    }
}
