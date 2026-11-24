package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure Java DATA tests only. No object or roundtrip here is a C++ frame, Native receipt or private action permission. */
final class NativeCurrentRmtmPostSuccessionEventDataTest {
    private static final int ACTOR = -2;
    private static final int INSTANCE = 41;
    private static final CurrentRmtmEvent.Action CHOOSE = CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE;
    private static final List<String> DEDICATED = List.of("rmtm.1001", "tgp_dynastic_cycle.0081", "lyd.1", "lyd.1000",
            "lyd.1002", "lyd.1032", "ep3_laamps.0003", "bookmark.1070", "gdp_guelph_ghibelline.0500",
            "xqol.100", "sxat.2", "sxat.4", "xccc.1001");
    private static CoreFrame.Prefix prefix(int actor) {
        return new CoreFrame.Prefix(-24, 3, true, 0, true, true, actor, true);
    }
    private static CurrentLydSource.EventOption option(int index, boolean can, String text) {
        return new CurrentLydSource.EventOption(index, can, text, "", Optional.empty(), Optional.empty());
    }
    private static CurrentLydSource.EventRow row(int instance, int actor, String definition, int authored,
            boolean visible, boolean enabled, List<CurrentLydSource.EventOption> options) {
        return new CurrentLydSource.EventRow(instance, actor, authored, definition, "opening\u0000", "description\n",
                true, visible, enabled, options);
    }
    private static CurrentRmtmEventSource source(boolean bound, CurrentLydSource.EventRow... rows) {
        return new CurrentRmtmEventSource(new CurrentLydSource.Events(true, rows.length, List.of(rows)),
                Optional.empty(), bound, false, true);
    }
    private static CurrentRmtmEventSource eligible() {
        return source(true, row(INSTANCE, ACTOR, "java_data_unclassified.777", 4, true, true,
                List.of(option(3, true, "vector first"), option(1, true, "minimum authored"))));
    }
    private static CurrentLetterResult.OwnerWitness owner() {
        return new CurrentLetterResult.OwnerWitness(BigInteger.ONE, NativeWire.UINT64_MAX, BigInteger.TWO, 1);
    }
    private static CurrentRmtmEventResult dispatched(CurrentRmtmEvent.Action action, CurrentRmtmEventSource source,
            int actor, int instance) {
        return new CurrentRmtmEventResult(action, CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,
                true, true, true, NativeWire.UINT64_MAX, NativeWire.UINT64_MAX, BigInteger.ONE,
                Optional.of(prefix(actor)), Optional.of(owner()), Optional.of(source), Optional.empty(), Optional.of(instance));
    }

    @Test void derivesMinimumAuthoredIndexForTheActualInstanceRatherThanVectorPosition() {
        for (int actor : new int[] {0, -2}) {
            var unrelated = row(7, actor, "unrelated.1", 1, true, true, List.of(option(0, true, "other instance")));
            var target = row(INSTANCE, actor, "java_data_unclassified.777", 6, true, true,
                    List.of(option(5, true, "first vector row"), option(3, true, "middle"), option(1, true, "actual minimum")));
            var actual = source(true, unrelated, target);
            assertFalse(actual.ackAdmissible()); assertTrue(actual.fixedInstanceId().isEmpty());
            var choice = CurrentRmtmEvent.postSuccessionChoice(actual, actor, INSTANCE).orElseThrow();
            assertEquals(INSTANCE, choice.instanceId()); assertEquals(1, choice.authoredOptionIndex());
            assertEquals(5, target.options().get(0).authoredOptionIndex());
        }
    }

    @Test void falseCanAndEmptyTextAreNotChosenButNulControlReadDataRemainsNonempty() throws IOException {
        String actualText = "\u0000\u0015#P actual#!\n";
        var actual = source(true, row(INSTANCE, ACTOR, "ordinary.1", 4, true, true,
                List.of(option(0, false, "unavailable"), option(1, true, ""), option(2, true, actualText))));
        assertEquals(2, CurrentRmtmEvent.postSuccessionChoice(actual, ACTOR, INSTANCE).orElseThrow().authoredOptionIndex());
        var roundtrip = CurrentRmtmEventSource.decode(actual.encode());
        assertEquals(actual, roundtrip); assertEquals(actualText, roundtrip.eventCensus().events().get(0).options().get(2).text());
        var none = source(true, row(INSTANCE, ACTOR, "ordinary.1", 2, true, true,
                List.of(option(0, false, "unavailable"), option(1, true, ""))));
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(none, ACTOR, INSTANCE).isEmpty());
    }

    @Test void foreignHiddenUnboundAndDuplicateDataCannotBecomeAPreparedChoice() {
        var actual = eligible();
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(actual, 0, INSTANCE).isEmpty());
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(actual, -1, INSTANCE).isEmpty());
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(actual, ACTOR, 0).isEmpty());
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(actual, ACTOR, INSTANCE + 1).isEmpty());
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(source(false, actual.eventCensus().events().get(0)), ACTOR, INSTANCE).isEmpty());
        for (boolean visible : new boolean[] {false, true}) {
            var hidden = source(true, row(INSTANCE, ACTOR, "ordinary.1", 1, visible, false, List.of(option(0, true, "actual"))));
            assertTrue(CurrentRmtmEvent.postSuccessionChoice(hidden, ACTOR, INSTANCE).isEmpty());
        }
        var invisible = source(true, row(INSTANCE, ACTOR, "ordinary.1", 1, false, true, List.of(option(0, true, "actual"))));
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(invisible, ACTOR, INSTANCE).isEmpty());
        var row = actual.eventCensus().events().get(0);
        // Real typed census/row constructors reject these malformed shapes before policy evaluation.
        assertThrows(IllegalArgumentException.class, () -> new CurrentLydSource.Events(true, 2, List.of(row, row)));
        assertThrows(IllegalArgumentException.class, () -> new CurrentLydSource.EventRow(INSTANCE, ACTOR, 1, "ordinary.1", "", "",
                false, true, true, List.of(option(0, true, "actual"))));
        assertThrows(IllegalArgumentException.class, () -> new CurrentRmtmEventSource(actual.eventCensus(), Optional.empty(), true, false, false));
    }

    @Test void dedicatedStrategiesAndAnySourceBoundOptionCannotBorrowTheNewPolicy() {
        for (String definition : DEDICATED) {
            var actual = source(true, row(INSTANCE, ACTOR, definition, 1, true, true, List.of(option(0, true, "actual"))));
            assertTrue(CurrentRmtmEvent.postSuccessionChoice(actual, ACTOR, INSTANCE).isEmpty(), definition);
        }
        var keyed = new CurrentLydSource.EventOption(0, true, "actual", "", Optional.of("other.actual-key"), Optional.empty());
        var keyedSource = source(true, row(INSTANCE, ACTOR, "ordinary.1", 1, true, true, List.of(keyed)));
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(keyedSource, ACTOR, INSTANCE).isEmpty());
        var role = new CurrentLydSource.EventOption(0, true, "continue", "", Optional.of("lyd_welcome_continue"),
                Optional.of(CurrentLyd.EventRole.WELCOME_CONTINUE));
        var dedicatedRole = source(true, row(INSTANCE, ACTOR, "lyd.1", 1, true, true, List.of(role)));
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(dedicatedRole, ACTOR, INSTANCE).isEmpty());
        // A recognized role cannot legally be attached to a different definition even in Java DATA.
        assertThrows(IllegalArgumentException.class, () -> row(INSTANCE, ACTOR, "ordinary.1", 1, true, true, List.of(role)));
        var fixedRow = row(INSTANCE, ACTOR, CurrentRmtmEvent.SUMMARY_DEFINITION, 1, true, true, List.of(option(0, true, "ack")));
        var admittedAck = new CurrentRmtmEventSource(new CurrentLydSource.Events(true, 1, List.of(fixedRow)), Optional.of(INSTANCE), true, true, true);
        assertTrue(admittedAck.ackAdmissible());
        assertTrue(CurrentRmtmEvent.postSuccessionChoice(admittedAck, ACTOR, INSTANCE).isEmpty());
    }

    @Test void fifthRequestKeepsNumericLeaseAndActualInstanceWithoutCallerIndexOrDefinition() throws IOException {
        var actual = new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313, prefix(ACTOR));
        var request = CurrentRmtmEvent.request(actual, CHOOSE, NativeWire.UINT64_MAX, NativeWire.UINT64_MAX, Optional.of(INSTANCE));
        assertEquals("choose-rmtm-post-succession-first-available-current-v1", request.step());
        assertEquals(Optional.of("game.command.choose-current-rmtm-post-succession-first-available.v1"), request.requiredCapability());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("rmtm_event", "arguments"));
        var claim = StrictJson.object(fields.get("rmtm_event"), Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                "backend", "action", "expected_core", "provider_generation", "query_sequence", "instance_id"));
        assertTrue(claim.get("provider_generation").isIntegralNumber()); assertTrue(claim.get("query_sequence").isIntegralNumber());
        assertEquals(NativeWire.UINT64_MAX, claim.get("provider_generation").bigIntegerValue());
        assertEquals(NativeWire.UINT64_MAX, claim.get("query_sequence").bigIntegerValue());
        assertEquals(INSTANCE, claim.get("instance_id").intValue()); assertEquals(ACTOR, claim.get("expected_core").get("played_character_id").intValue());
        assertEquals("choose_post_succession_first_available", claim.get("action").textValue());
        assertEquals(0, fields.get("arguments").size());
        assertThrows(IllegalArgumentException.class, () -> CurrentRmtmEvent.request(actual, CHOOSE, BigInteger.ZERO, BigInteger.ONE, Optional.of(INSTANCE)));
        assertThrows(IllegalArgumentException.class, () -> CurrentRmtmEvent.request(actual, CHOOSE, BigInteger.ONE, BigInteger.ZERO, Optional.of(INSTANCE)));
        assertThrows(IllegalArgumentException.class, () -> CurrentRmtmEvent.request(actual, CHOOSE, BigInteger.ONE, BigInteger.ONE, Optional.empty()));
        assertEquals(4, CHOOSE.ordinal());
        assertEquals(CurrentRmtmEvent.Action.QUERY_SUMMARY, CurrentRmtmEvent.Action.values()[0]);
        assertEquals(CurrentRmtmEvent.Action.ACK_CHAOS, CurrentRmtmEvent.Action.values()[3]);
    }

    @Test void dispatchedDataRetainsActualBeforeSourceWithoutFixedAckOrBusinessFlags() throws IOException {
        var before = eligible(); var result = dispatched(CHOOSE, before, ACTOR, INSTANCE);
        assertTrue(result.successful()); assertEquals(Optional.of(before), result.source());
        assertFalse(before.ackAdmissible()); assertTrue(before.fixedInstanceId().isEmpty());
        assertEquals(result, CurrentRmtmEventResult.decode(result.encode()));
        assertFalse(result.nativeHandled()); assertFalse(result.eventClosed());
        assertFalse(result.newDateObserved()); assertFalse(result.physicalSaveConfirmed());
        assertEquals(NativeWire.UINT64_MAX, result.providerGeneration());
        assertEquals(NativeWire.UINT64_MAX, result.querySequence());
    }

    @Test void wrongSourceActorInstanceOrFlagsDoNotRelaxOldFixedAcknowledgements() {
        var before = eligible();
        assertThrows(IllegalArgumentException.class, () -> dispatched(CHOOSE, before, 0, INSTANCE));
        assertThrows(IllegalArgumentException.class, () -> dispatched(CHOOSE, before, ACTOR, INSTANCE + 1));
        assertThrows(IllegalArgumentException.class, () -> dispatched(CurrentRmtmEvent.Action.ACK_SUMMARY, before, ACTOR, INSTANCE));
        assertThrows(IllegalArgumentException.class, () -> new CurrentRmtmEventResult(CHOOSE, CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,
                true, true, true, BigInteger.ONE, BigInteger.ONE, BigInteger.ONE, Optional.of(prefix(ACTOR)), Optional.of(owner()),
                Optional.empty(), Optional.empty(), Optional.of(INSTANCE)));
        assertThrows(IllegalArgumentException.class, () -> new CurrentRmtmEventResult(CHOOSE, CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,
                false, false, true, BigInteger.ONE, BigInteger.ONE, BigInteger.ONE, Optional.of(prefix(ACTOR)), Optional.of(owner()),
                Optional.of(before), Optional.empty(), Optional.of(INSTANCE)));
        var row = row(INSTANCE, ACTOR, CurrentRmtmEvent.SUMMARY_DEFINITION, 1, true, true, List.of(option(0, true, "ack")));
        var fixed = new CurrentRmtmEventSource(new CurrentLydSource.Events(true, 1, List.of(row)), Optional.of(INSTANCE), true, true, true);
        assertDoesNotThrow(() -> dispatched(CurrentRmtmEvent.Action.ACK_SUMMARY, fixed, ACTOR, INSTANCE));
        assertThrows(IllegalArgumentException.class, () -> dispatched(CHOOSE, fixed, ACTOR, INSTANCE));
    }

    @Test void unknownAndKnownRefusalKeepTheirOriginalFlagsAndSourceNull() throws IOException {
        var unknown = new CurrentRmtmEventResult(CHOOSE, CurrentRmtmEventResult.Status.INDETERMINATE,
                true, false, false, NativeWire.UINT64_MAX, BigInteger.TWO, BigInteger.ONE, Optional.of(prefix(ACTOR)),
                Optional.of(owner()), Optional.empty(), Optional.of("original cleanup UNKNOWN"), Optional.of(INSTANCE));
        assertEquals(unknown, CurrentRmtmEventResult.decode(unknown.encode()));
        assertFalse(unknown.successful()); assertTrue(unknown.effectAttempted()); assertFalse(unknown.nativeReturned());
        assertFalse(unknown.cleanupKnown()); assertTrue(unknown.source().isEmpty()); assertEquals(BigInteger.ONE, unknown.claimSequence());
        var refusal = new CurrentRmtmEventResult(CHOOSE, CurrentRmtmEventResult.Status.UNAVAILABLE,
                false, false, true, BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO, Optional.of(prefix(ACTOR)), Optional.of(owner()),
                Optional.empty(), Optional.of("known before-write refusal"), Optional.of(INSTANCE));
        assertEquals(refusal, CurrentRmtmEventResult.decode(refusal.encode())); assertFalse(refusal.effectAttempted());
        var withSource = (com.fasterxml.jackson.databind.node.ObjectNode) NativeWire.parse(unknown.encode().bytes());
        withSource.set("source", eligible().encode()); withSource.put("source_available", true);
        assertThrows(IOException.class, () -> CurrentRmtmEventResult.decode(new RawJson(StrictJson.canonical(withSource))));
        for (String field : List.of("native_handled", "event_closed", "new_date_observed", "physical_save_confirmed")) {
            var changed = (com.fasterxml.jackson.databind.node.ObjectNode) NativeWire.parse(refusal.encode().bytes()); changed.put(field, true);
            assertThrows(IOException.class, () -> CurrentRmtmEventResult.decode(new RawJson(StrictJson.canonical(changed))), field);
        }
    }
}
