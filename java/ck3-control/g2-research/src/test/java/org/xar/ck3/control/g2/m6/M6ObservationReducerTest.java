package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceCompositionTest.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Historical resource bytes stay historical. Prospective controls below are explicitly synthetic. */
public final class M6ObservationReducerTest {
    @Test void originalHistoricalPacketsStayUnknownAndOriginalLedgerBytesStayExact() throws Exception {
        var evidence = evidence(); byte[] held = evidence.originalLedger().bytes();
        var rows = evidence.episodes().stream().map(episode -> new M6ObservationReducer.Input(
                episode.identity().actionId(), Optional.empty(), inputs(completion(episode), null, null, null))).toList();
        var report = M6ServiceIntegration.observeCampaign(evidence, rows);
        assertEquals(2, report.observations().size());
        for (var row : report.observations()) {
            assertTrue(row.cause().isEmpty()); assertFalse(row.usefulSchemeComplete());
            assertEquals(M6ObservationReducer.MaterialChange.BASELINE_NOT_PROVIDED, row.materialChange());
        }
        assertArrayEquals(held, report.originalLedger().bytes()); assertFalse(report.actionAuthorized());
        assertFalse(report.ledgerCommitted()); assertFalse(report.requestRetried()); assertFalse(report.wholeM6Complete());
    }

    @Test void syntheticTwoRawNamedSamplesMeasureIncreaseWithoutInventingAnEndCause() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        var row = observe(evidence, episode, sample(episode, 100, 10), sample(episode, 124, 25));
        assertEquals(M6ObservationReducer.MaterialChange.INCREASE, row.materialChange());
        assertEquals(BigInteger.valueOf(15), row.namedDelta().orElseThrow());
        assertTrue(row.positiveNamedGainObserved()); assertTrue(row.cause().isEmpty());
        assertEquals(M6ObservationReducer.Terminal.UNKNOWN, row.terminal()); assertFalse(row.usefulSchemeComplete());
    }

    @Test void syntheticKnownAbsenceIsZeroButUnreadMaterialStaysUnknown() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        var before = sample(episode, 100, 10); ObjectNode opinion = raw(before.opinion().orElseThrow());
        ((ObjectNode)opinion.get("scheme_sway_opinion")).put("present", false).putNull("value");
        var absent = inputs(raw(before.completion().orElseThrow()), null, null, opinion);
        assertEquals(BigInteger.valueOf(25), observe(evidence, episode, absent, sample(episode, 124, 25)).namedDelta().orElseThrow());
        ((ObjectNode)opinion.get("scheme_sway_opinion")).put("observed", false);
        var unread = inputs(raw(before.completion().orElseThrow()), null, null, opinion);
        var row = observe(evidence, episode, unread, sample(episode, 124, 25));
        assertEquals(M6ObservationReducer.MaterialChange.MODIFIER_UNREAD, row.materialChange()); assertTrue(row.namedDelta().isEmpty());
    }

    @Test void syntheticQueryRevisionIncreaseCannotReplaceAnOrderedNativeDate() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        for (int date : List.of(100, 99)) {
            var row = observe(evidence, episode, sample(episode, 100, 10), sample(episode, date, 25));
            assertEquals(M6ObservationReducer.MaterialChange.DATE_ORDER_UNAVAILABLE, row.materialChange());
            assertTrue(row.namedDelta().isEmpty()); assertFalse(row.positiveNamedGainObserved());
        }
    }

    @Test void syntheticSameValueRefreshCannotRearmMaterialGainOrConsumption() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        var row = observe(evidence, episode, sample(episode, 100, 25), sample(episode, 124, 25));
        assertEquals(M6ObservationReducer.MaterialChange.NO_INCREASE, row.materialChange());
        assertEquals(BigInteger.ZERO, row.namedDelta().orElseThrow()); assertFalse(row.positiveNamedGainObserved());
        assertFalse(row.usefulSchemeComplete());
    }

    @Test void syntheticExactDynamicParentAndEndProveCauseWithoutSupplyingMaterial() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        execution.withArray("records").add(parent(episode)); termination.withArray("records").add(end(episode, true));
        var report = M6ServiceIntegration.observeCampaign(evidence, List.of(new M6ObservationReducer.Input(
                episode.identity().actionId(), Optional.empty(), inputs(null, execution, termination, null))));
        var row = report.observations().getFirst();
        assertEquals(M6ObservationReducer.Terminal.AUTHORED_COMPLETE_TRANSITION, row.terminal());
        assertEquals(new BigInteger("18446744073709551001"), row.cause().orElseThrow().session());
        assertTrue(row.current().isEmpty()); assertFalse(row.positiveNamedGainObserved());
        assertFalse(row.usefulSchemeComplete()); assertFalse(report.ledgerCommitted());
    }

    @Test void syntheticForeignSessionAndNearestToastBarrierCannotSupplyACause() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        ObjectNode branch = parent(episode);
        ((ObjectNode)branch.get("native_invocation")).put("observer_session_identity", 7);
        execution.withArray("records").add(branch); termination.withArray("records").add(end(episode, true));
        assertTrue(report(evidence, episode, inputs(null, execution, termination, null)).observations().getFirst().cause().isEmpty());
        execution.withArray("records").removeAll().add(parent(episode));
        ObjectNode ended = (ObjectNode)termination.withArray("records").get(0);
        ((ObjectNode)ended.get("cause_relation")).putArray("native_return_rvas")
                .add(0x2d67c04).add(0x2cc93cc).add(0x3766146).add(0x2cc93cc);
        assertThrows(IllegalArgumentException.class, () -> report(evidence, episode, inputs(null, execution, termination, null)));
    }

    @Test void syntheticBadTypesMissingFieldsAndReusedStorageCannotBecomeGain() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        var after = sample(episode, 124, 25); ObjectNode completion = raw(after.completion().orElseThrow());
        completion.put("storage_slot_reused", true);
        var reused = inputs(completion, null, null, raw(after.opinion().orElseThrow()));
        var row = observe(evidence, episode, sample(episode, 100, 10), reused);
        assertEquals(M6ObservationReducer.MaterialChange.CURRENT_INSTANCE_UNOBSERVED, row.materialChange());
        for (int mode = 0; mode < 3; mode++) {
            ObjectNode bad = raw(after.opinion().orElseThrow());
            if (mode == 0) ((ObjectNode)bad.get("scheme_sway_opinion")).put("observed", 1);
            if (mode == 1) ((ObjectNode)bad.get("scheme_sway_opinion")).remove("value");
            if (mode == 2) bad.put("snapshot_revision", 1.5);
            assertThrows(IllegalArgumentException.class, () -> observe(evidence, episode, sample(episode, 100, 10),
                    inputs(raw(after.completion().orElseThrow()), null, null, bad)));
        }
    }

    @Test void existingServiceConsumerChecksOriginalActionAndRejectsDuplicateOrBorrowedBaseline() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        var one = new M6ObservationReducer.Input(episode.identity().actionId(), Optional.of(sample(episode, 100, 10)),
                sample(episode, 124, 25));
        assertThrows(IllegalArgumentException.class, () -> M6ServiceIntegration.observeCampaign(evidence, List.of(one, one)));
        var unknown = new M6ObservationReducer.Input("not-an-original-action", Optional.empty(), one.current());
        assertThrows(IllegalArgumentException.class, () -> M6ServiceIntegration.observeCampaign(evidence, List.of(unknown)));
        assertThrows(IllegalArgumentException.class, () -> new M6ObservationReducer.Input(episode.identity().actionId(),
                Optional.of(inputs(null, journal(episode, true), null, null)), one.current()));
        byte[] held = evidence.originalLedger().bytes();
        var result = M6ServiceIntegration.observeCampaign(evidence, List.of(one));
        assertArrayEquals(held, evidence.originalLedger().bytes()); assertArrayEquals(held, result.originalLedger().bytes());
    }

    @Test void reportSerializationRetainsDecimalUint64AndNeverAdvertisesExecutionOrSuccess() throws Exception {
        var evidence = evidence(); var episode = evidence.episodes().get(1);
        ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        execution.withArray("records").add(parent(episode)); termination.withArray("records").add(end(episode, true));
        var report = report(evidence, episode, inputs(null, execution, termination, null));
        byte[] encoded = M6ObservationReducer.toJson(report).bytes();
        JsonNode json = StrictJson.parse(encoded, M6SourceProducer.MAX_BYTES);
        assertEquals(M6ObservationReducer.SCHEMA, json.get("schema").textValue());
        assertTrue(json.at("/observations/0/cause/observer_session_identity").isTextual());
        assertEquals("18446744073709551001", json.at("/observations/0/cause/observer_session_identity").textValue());
        assertFalse(json.get("whole_m6_complete").booleanValue()); assertFalse(json.get("ledger_committed").booleanValue());
        assertFalse(json.get("action_authorized").booleanValue()); assertFalse(json.get("request_retried").booleanValue());
        assertFalse(json.at("/observations/0/useful_scheme_complete").booleanValue());
        assertArrayEquals(encoded, StrictJson.canonical(StrictJson.parse(encoded, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES));
    }

    private static M6ObservationReducer.Report report(G2M6Contracts.CampaignEvidence evidence,
            G2M6Contracts.Episode episode, M6TerminalSourceComposition.Inputs current) {
        return M6ServiceIntegration.observeCampaign(evidence, List.of(new M6ObservationReducer.Input(
                episode.identity().actionId(), Optional.empty(), current)));
    }
    private static M6ObservationReducer.Observation observe(G2M6Contracts.CampaignEvidence evidence,
            G2M6Contracts.Episode episode, M6TerminalSourceComposition.Inputs before,
            M6TerminalSourceComposition.Inputs current) {
        return M6ServiceIntegration.observeCampaign(evidence, List.of(new M6ObservationReducer.Input(
                episode.identity().actionId(), Optional.of(before), current))).observations().getFirst();
    }
    private static M6TerminalSourceComposition.Inputs sample(G2M6Contracts.Episode episode, int date, int points) {
        ObjectNode completion = completion(episode);
        int nativeDate = Math.addExact(episode.start().orElseThrow().independentActive().dateRaw(), date);
        completion.put("date_raw", nativeDate); completion.put("snapshot_revision", new BigInteger("18446744073709551000"));
        ObjectNode opinion = M6TerminalSourceComposition.identityJson(episode.identity()); opinion.remove("action_id");
        opinion.put("schema", "xar.ck3.sway-outcome-opinion-v1"); opinion.put("available", true);
        opinion.put("build_version", M6SourceProducer.BUILD); opinion.put("executable_sha256", M6SourceProducer.EXE);
        opinion.set("snapshot_revision", completion.get("snapshot_revision")); opinion.put("date_raw", nativeDate);
        opinion.putObject("scheme_sway_opinion").put("observed", true).put("present", true).put("value", points);
        opinion.putObject("sway_blocker_opinion").put("observed", true).put("present", false).putNull("value");
        return inputs(completion, null, null, opinion);
    }
    private static ObjectNode raw(ProjectionJson value) { return (ObjectNode)StrictJson.parse(value.bytes(), M6SourceProducer.MAX_BYTES); }
}
