package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

final class DeadlineTransportTest {
    private static final int CORPUS_MAX_BYTES = 196_608;
    private static final String CORPUS_PROFILE = "deadline-transport-producer-corpus/v1";
    private static final JsonNode GOLDEN = golden();

    @TestFactory
    Stream<DynamicTest> actualOriginalTransportAndAllItsReturnedProofs() {
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : GOLDEN.get("transport_cases")) {
            tests.add(DynamicTest.dynamicTest(row.get("id").textValue(), () -> {
                DeadlineTransport.PreparedRequest prepared = DeadlineTransportCodec.prepare(raw(row.get("request")));
                AtomicInteger calls = new AtomicInteger();
                DeadlineTransportAdapter.Invocation invocation = new DeadlineTransportAdapter.Invocation(prepared);
                DeadlineTransportAdapter.OriginalDeadlineAuthority authority = request -> {
                    assertEquals(prepared, request); calls.incrementAndGet();
                    if (row.at("/outcome/status").textValue().equals("failed")) {
                        throw new IOException(row.at("/outcome/error").textValue());
                    }
                    return raw(row.get("completion"));
                };
                if (row.at("/outcome/status").textValue().equals("failed")) {
                    DeadlineTransportAdapter.UnknownOutcomeException unknown = assertThrows(
                            DeadlineTransportAdapter.UnknownOutcomeException.class, () -> invocation.run(authority));
                    assertEquals(prepared.invocationId(), unknown.invocationId());
                    assertFalse(unknown.replayAllowed());
                    assertEquals(DeadlineTransportAdapter.State.UNKNOWN, invocation.state());
                } else {
                    DeadlineTransport.Observation observation = invocation.run(authority);
                    assertEquals(row.at("/outcome/value"), StrictJson.parse(DeadlineTransportCodec.encodeClock(observation.completion().clock())));
                    assertEquals(DeadlineTransportAdapter.State.OBSERVED, invocation.state());
                    assertFalse(observation.replayAllowed()); assertFalse(observation.nativeAdmissionGranted());
                    assertEquals(0, observation.savedDayCredit());
                }
                assertEquals(1, calls.get());
                assertThrows(IllegalStateException.class, () -> invocation.run(authority));
                assertEquals(1, calls.get());
            }));
        }
        return tests.stream();
    }

    @TestFactory
    Stream<DynamicTest> actualOriginalSentinelNormalizerInputsIncludingRawFloats() {
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : GOLDEN.get("normalizer_cases")) {
            tests.add(DynamicTest.dynamicTest(row.get("id").textValue(), () -> {
                // The actual Python producer serialized this string before any JSON tree normalization.
                byte[] input = bytes(row.get("input_json").textValue());
                if (row.at("/expected/status").textValue().equals("rejected")) {
                    assertThrows(IllegalArgumentException.class, () -> SentinelObservation.decode(input));
                } else {
                    Status value = SentinelObservation.decode(input);
                    assertEquals(row.at("/expected/value"), StrictJson.parse(raw(SentinelObservation.toJson(value))));
                    assertEquals(value, SentinelObservation.decode(raw(SentinelObservation.toJson(value))));
                }
            }));
        }
        return tests.stream();
    }

    @Test
    void goldenIsActualWholeDriverFakeWireAndHasNoLiveCredit() {
        assertEquals("actual_existing_driver_transport_fake_wire_no_game", GOLDEN.get("method").textValue());
        assertEquals(9, GOLDEN.get("transport_cases").size());
        assertEquals(18, GOLDEN.get("normalizer_cases").size());
        assertTrue(GOLDEN.get("original_tests").intValue() > 0);
        assertEquals(0, GOLDEN.get("original_skipped").intValue());
        assertEquals(0, GOLDEN.get("game_rpc").intValue()); assertEquals(0, GOLDEN.get("native_calls").intValue());
        assertEquals(0, GOLDEN.get("ledger_writes").intValue()); assertEquals(0, GOLDEN.get("saved_day_credit").intValue());
        assertSourceProvenance(GOLDEN);
    }

    @Test
    void sourceProvenanceRejectsIncompleteOrUntypedImportClosure() {
        ObjectNode absent = (ObjectNode) GOLDEN.deepCopy();
        absent.remove("source_provenance");
        assertThrows(AssertionError.class, () -> assertSourceProvenance(absent));
        ObjectNode wrongCount = (ObjectNode) GOLDEN.deepCopy();
        ((ObjectNode) wrongCount.get("source_provenance")).put("recorded_repo_sources", true);
        assertThrows(AssertionError.class, () -> assertSourceProvenance(wrongCount));
        ObjectNode unchecked = (ObjectNode) GOLDEN.deepCopy();
        ((ObjectNode) unchecked.get("source_provenance")).put("source_pre_post_equal", false);
        assertThrows(AssertionError.class, () -> assertSourceProvenance(unchecked));
        ObjectNode uncovered = (ObjectNode) GOLDEN.deepCopy();
        ((ObjectNode) uncovered.get("source_provenance")).putArray("unrecorded_repo_sources").add("unobserved.py");
        assertThrows(AssertionError.class, () -> assertSourceProvenance(uncovered));
        ObjectNode floatBytes = (ObjectNode) GOLDEN.deepCopy();
        ((ObjectNode) floatBytes.get("source_refs").get(0)).put("bytes", 1.0);
        assertThrows(AssertionError.class, () -> assertSourceProvenance(floatBytes));
        ObjectNode badHash = (ObjectNode) GOLDEN.deepCopy();
        ((ObjectNode) badHash.get("source_refs").get(0)).put("sha256", "not-a-source-hash");
        assertThrows(AssertionError.class, () -> assertSourceProvenance(badHash));
        ObjectNode duplicate = (ObjectNode) GOLDEN.deepCopy();
        ((com.fasterxml.jackson.databind.node.ArrayNode) duplicate.get("source_refs"))
                .add(duplicate.get("source_refs").get(0).deepCopy());
        assertThrows(AssertionError.class, () -> assertSourceProvenance(duplicate));
    }

    @Test
    void exactNativeUint64GenerationDoesNotPassThroughDoubleOrLong() {
        JsonNode row = GOLDEN.get("normalizer_cases").get(2);
        JsonNode input = StrictJson.parse(bytes(row.get("input_json").textValue()));
        Status value = SentinelObservation.decode(input);
        assertEquals("18446744073709551615", value.generation().decimal());
        assertEquals(new BigInteger("18446744073709551615"), SentinelObservation.nativeGeneration(value));
        assertEquals(value, SentinelObservation.decode(raw(SentinelObservation.toJson(value))));
        ObjectNode overflow = (ObjectNode) input.deepCopy();
        overflow.put("generation", new BigInteger("18446744073709551616"));
        assertThrows(IllegalArgumentException.class, () -> SentinelObservation.decode(StrictJson.parse(raw(overflow))));
        ObjectNode counter = (ObjectNode) input.deepCopy();
        counter.put("completed_daily_ticks", 4_294_967_296L);
        assertThrows(IllegalArgumentException.class, () -> SentinelObservation.decode(StrictJson.parse(raw(counter))));
    }

    @Test
    void wrongNumericRequestTokensReallyReachTheStrictEntry() {
        JsonNode original = returned().get("request");
        for (String token : List.of("true", "5.0", "\"5\"", "null")) {
            ObjectNode bad = (ObjectNode) original.deepCopy(); bad.set("speed", StrictJson.parse(bytes(token)));
            assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.prepare(raw(bad)), token);
        }
        ObjectNode missing = (ObjectNode) original.deepCopy(); missing.remove("cap");
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.prepare(raw(missing)));
        ObjectNode unknown = (ObjectNode) original.deepCopy(); unknown.put("native_admission_green", true);
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.prepare(raw(unknown)));
    }

    @Test
    void unknownAcceptedCannotBecomeNativeProofOrAuthorizeRetry() {
        JsonNode original = returned(); ObjectNode completion = (ObjectNode) original.get("completion").deepCopy();
        int arm = armIndex(completion);
        ((ObjectNode) completion.at("/actions/" + arm + "/result")).putNull("accepted");
        DeadlineTransportAdapter.Invocation invocation = new DeadlineTransportAdapter.Invocation(
                DeadlineTransportCodec.prepare(raw(original.get("request"))));
        AtomicInteger calls = new AtomicInteger();
        DeadlineTransportAdapter.OriginalDeadlineAuthority authority = request -> { calls.incrementAndGet(); return raw(completion); };
        assertThrows(DeadlineTransportAdapter.UnknownOutcomeException.class, () -> invocation.run(authority));
        assertEquals(DeadlineTransportAdapter.State.UNKNOWN, invocation.state());
        assertThrows(IllegalStateException.class, () -> invocation.run(authority)); assertEquals(1, calls.get());
    }

    @Test
    void changedGenerationTargetTicksPauseAndSpeedBindingsAreRejected() {
        JsonNode original = returned();
        for (String pointer : List.of("/clock/stopped/generation", "/clock/stopped/target_date_raw",
                "/clock/stopped/completed_daily_ticks")) {
            ObjectNode malformed = (ObjectNode) original.get("completion").deepCopy();
            JsonNode previous = malformed.at(pointer);
            assertTrue(previous.isIntegralNumber(), "actual mutation target must exist:" + pointer);
            int slash = pointer.lastIndexOf('/');
            ((ObjectNode) malformed.at(pointer.substring(0, slash))).put(pointer.substring(slash + 1), previous.bigIntegerValue().add(BigInteger.ONE));
            assertThrows(IllegalArgumentException.class,
                    () -> DeadlineTransportCodec.observe(raw(original.get("request")), raw(malformed)), pointer);
        }
        ObjectNode unpaused = (ObjectNode) original.get("completion").deepCopy();
        ((ObjectNode) unpaused.get("current_frame")).put("paused", false);
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.observe(raw(original.get("request")), raw(unpaused)));
        JsonNode observed = row("already-observed-speed");
        ObjectNode wrongSource = (ObjectNode) observed.get("completion").deepCopy();
        ObjectNode speedSource = (ObjectNode) wrongSource.at("/clock/speed_configuration");
        speedSource.put("source_date_raw", speedSource.get("source_date_raw").intValue() + 24);
        assertThrows(IllegalArgumentException.class,
                () -> DeadlineTransportCodec.observe(raw(observed.get("request")), raw(wrongSource)));
    }

    @Test
    void repeatedResumeAndExtraActionsCannotBeNormalizedAway() {
        JsonNode original = returned(); ObjectNode malformed = (ObjectNode) original.get("completion").deepCopy();
        ArrayNode actions = (ArrayNode) malformed.get("actions");
        for (int index = 0; index < actions.size(); index++) {
            if (actions.get(index).get("step").textValue().equals("resume-map")) {
                actions.insert(index, actions.get(index).deepCopy()); break;
            }
        }
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.observe(raw(original.get("request")), raw(malformed)));
    }

    @Test
    void zeroDayEarlyBoundaryKeepsActualCancelAndDoesNotClaimClockProgressCredit() {
        JsonNode row = row("early-event-zero-days");
        DeadlineTransport.Observation observation = DeadlineTransport.observe(DeadlineTransportCodec.prepare(raw(row.get("request"))),
                DeadlineTransportCodec.completion(raw(row.get("completion"))));
        assertEquals(DeadlineTransport.ObservationKind.EARLY_BOUNDARY_CANCEL_RETURNED, observation.kind());
        assertEquals(observation.request().starting().dateRaw(), observation.completion().current().dateRaw());
        assertTrue(observation.completion().clock().earlyBoundaryCancel().isPresent());
        assertEquals(0, observation.savedDayCredit()); assertFalse(observation.nativeAdmissionGranted());
    }

    @Test
    void missingCancelNullClockAndDuplicateFieldsAreRejected() {
        JsonNode early = row("early-event-two-days");
        ObjectNode missingCancel = (ObjectNode) early.get("completion").deepCopy();
        ((ObjectNode) missingCancel.get("clock")).putNull("early_boundary_cancel");
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.observe(raw(early.get("request")), raw(missingCancel)));
        ObjectNode missing = (ObjectNode) early.get("completion").deepCopy(); missing.remove("clock");
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.completion(raw(missing)));
        assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.completion(bytes("{\"clock\":null,\"clock\":null}")));
    }

    @Test
    void opaqueCancelRoundTripUsesJsonValuesRatherThanObjectKeyOrder() {
        JsonNode row = row("early-event-two-days");
        ObjectNode completion = (ObjectNode) row.get("completion").deepCopy();
        ObjectNode cancel = (ObjectNode) completion.at("/clock/early_boundary_cancel");
        List<String> names = new ArrayList<>(); cancel.fieldNames().forEachRemaining(names::add);
        ObjectNode reordered = StrictJson.object();
        for (int index = names.size() - 1; index >= 0; index--) { reordered.set(names.get(index), cancel.get(names.get(index))); }
        ((ObjectNode) completion.get("clock")).set("early_boundary_cancel", reordered);
        assertEquals(row.at("/outcome/value"), StrictJson.parse(DeadlineTransportCodec.observe(raw(row.get("request")), raw(completion))));
    }

    @Test
    void malformedEndingRawCannotBeTrustedByModelTypesAlone() {
        JsonNode original = returned();
        for (String token : List.of("true", "53144352.0", "\"53144352\"", "null")) {
            ObjectNode bad = (ObjectNode) original.get("completion").deepCopy();
            ((ObjectNode) bad.get("current_frame")).set("date_raw", StrictJson.parse(bytes(token)));
            assertThrows(IllegalArgumentException.class, () -> DeadlineTransportCodec.completion(raw(bad)), token);
        }
    }

    @Test
    void typedReceiptCannotContradictTheRetainedPrimitiveDocument() {
        DeadlineTransport.Completion completion = DeadlineTransportCodec.completion(raw(returned().get("completion")));
        DeadlineTransport.NativeReceipt actual = completion.ownActions().get(0).result();
        assertThrows(IllegalArgumentException.class, () -> new DeadlineTransport.NativeReceipt(actual.step(),
                !actual.accepted(), actual.status(), actual.sentinel(), actual.original()));
        assertThrows(IllegalArgumentException.class, () -> new DeadlineTransport.NativeReceipt("pause-map",
                actual.accepted(), actual.status(), actual.sentinel(), actual.original()));
    }

    @Test
    void opaqueDecimalExtensionsRetainTheirJsonTypeAcrossTheClockRoundTrip() {
        JsonNode row = row("early-event-two-days");
        ObjectNode completion = (ObjectNode) row.get("completion").deepCopy();
        ObjectNode diagnostic = StrictJson.object(); diagnostic.set("ratio", StrictJson.parse(bytes("1.0")));
        ObjectNode clockCancel = (ObjectNode) completion.at("/clock/early_boundary_cancel");
        clockCancel.set("diagnostic", diagnostic);
        boolean bound = false;
        for (JsonNode action : completion.get("actions")) {
            if (action.get("step").textValue().startsWith(DeadlineTransport.CANCEL_PREFIX)) {
                ((ObjectNode) action.get("result")).set("diagnostic", diagnostic.deepCopy()); bound = true;
            }
        }
        assertTrue(bound, "actual cancel action required");
        JsonNode observed = StrictJson.parse(DeadlineTransportCodec.observe(raw(row.get("request")), raw(completion)));
        assertTrue(observed.at("/early_boundary_cancel/diagnostic/ratio").isFloatingPointNumber());
        assertEquals(diagnostic, observed.at("/early_boundary_cancel/diagnostic"));
        ObjectNode wrong = StrictJson.object(); wrong.put("ratio", 1);
        clockCancel.set("diagnostic", wrong);
        assertThrows(IllegalArgumentException.class,
                () -> DeadlineTransportCodec.observe(raw(row.get("request")), raw(completion)));
    }

    @Test
    void nativeStopObservationIsOnlyConstructedByTheValidatedFactory() {
        assertEquals(0, DeadlineTransport.Observation.class.getConstructors().length);
        JsonNode row = returned();
        assertEquals(DeadlineTransport.ObservationKind.NATIVE_STOP_OBSERVED,
                DeadlineTransport.observe(DeadlineTransportCodec.prepare(raw(row.get("request"))),
                        DeadlineTransportCodec.completion(raw(row.get("completion")))).kind());
    }

    private static void assertSourceProvenance(JsonNode golden) {
        JsonNode provenance = golden.path("source_provenance");
        assertTrue(provenance.isObject());
        assertEquals(8, provenance.size());
        assertEquals("xar.ck3.measured-repo-import-closure/v1", provenance.path("schema").textValue());
        assertEquals("repo-python-excluding-interpreter-prefixes/v1", provenance.path("scope").textValue());
        assertEquals(0, nonnegativeCount(provenance.path("initial_repo_sources")));
        int afterImports = nonnegativeCount(provenance.path("after_imports_repo_sources"));
        int afterSuite = nonnegativeCount(provenance.path("after_suite_repo_sources"));
        int recorded = nonnegativeCount(provenance.path("recorded_repo_sources"));
        assertTrue(afterImports > 0 && afterSuite > 0 && afterImports <= recorded && afterSuite <= recorded);
        assertTrue(provenance.path("source_pre_post_equal").isBoolean());
        assertTrue(provenance.path("source_pre_post_equal").booleanValue());
        assertTrue(provenance.path("unrecorded_repo_sources").isArray());
        assertEquals(0, provenance.path("unrecorded_repo_sources").size());
        JsonNode refs = golden.path("source_refs");
        assertTrue(refs.isArray());
        Set<String> paths = new HashSet<>();
        int pythonSources = 0;
        int abiSources = 0;
        for (JsonNode ref : refs) {
            assertTrue(ref.isObject());
            assertEquals(3, ref.size());
            assertTrue(ref.path("path").isTextual());
            String path = ref.path("path").textValue();
            assertTrue(!path.isBlank() && !path.startsWith("/") && !path.contains("\\") && !path.contains(":"));
            assertTrue(!List.of(path.split("/")).contains(".."));
            assertTrue(paths.add(path));
            assertTrue(ref.path("bytes").isIntegralNumber() && ref.path("bytes").canConvertToLong()
                    && ref.path("bytes").longValue() >= 0);
            assertTrue(ref.path("sha256").isTextual()
                    && ref.path("sha256").textValue().matches("[0-9a-f]{64}"));
            if (path.endsWith(".py")) {
                pythonSources++;
                assertTrue(!path.contains("/.venv/"));
            } else {
                assertEquals("ck3_autonomous_player/native_bridge/include/xar_bridge/tactical_daily_sentinel_v1.hpp", path);
                abiSources++;
            }
        }
        assertEquals(recorded, pythonSources);
        assertEquals(1, abiSources);
        assertTrue(paths.containsAll(Set.of(
                "tools/ck3_live_run_id.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_deadline_transport_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_deadline_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
                "ck3_autonomous_player/tests/unit/test_campaign_deadline_transport_v1.py",
                "ck3_autonomous_player/tests/unit/test_native_bridge_driver.py",
                "ck3_autonomous_player/tests/unit/test_war_termination_terms_contract.py",
                "ck3_autonomous_player/tests/unit/test_raiktor_war_bound_regiment_contract.py")));
    }

    private static int nonnegativeCount(JsonNode value) {
        assertTrue(value.isIntegralNumber() && value.canConvertToInt());
        int count = value.intValue();
        assertTrue(count >= 0);
        return count;
    }

    private static int armIndex(JsonNode completion) {
        JsonNode actions = completion.get("actions");
        for (int index = 0; index < actions.size(); index++) {
            if (actions.get(index).get("step").textValue().startsWith(DeadlineTransport.ARM_PREFIX)) { return index; }
        }
        throw new IllegalStateException("actual Arm fixture absent");
    }
    private static JsonNode returned() { return row("changed-speed-five-day"); }
    private static JsonNode row(String id) {
        for (JsonNode row : GOLDEN.get("transport_cases")) { if (row.get("id").textValue().equals(id)) { return row; } }
        throw new IllegalStateException("missing actual producer fixture:" + id);
    }
    private static byte[] raw(JsonNode node) { return LegacyJsonValues.encode(node); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() {
        try (InputStream stream = DeadlineTransportTest.class.getResourceAsStream("/deadlinetransport/producer-golden.json")) {
            if (stream == null) { throw new IllegalStateException("actual producer golden missing; no skipped pass permitted"); }
            byte[] raw = stream.readNBytes(CORPUS_MAX_BYTES + 1);
            if (raw.length > CORPUS_MAX_BYTES) { throw new IllegalStateException("deadline corpus exceeds its independent byte profile"); }
            JsonNode corpus = StrictJson.parse(raw, CORPUS_MAX_BYTES);
            if (!CORPUS_PROFILE.equals(corpus.path("corpus_profile").textValue())
                    || !corpus.path("corpus_maximum_bytes").isIntegralNumber()
                    || !corpus.path("corpus_maximum_bytes").canConvertToInt()
                    || corpus.path("corpus_maximum_bytes").intValue() != CORPUS_MAX_BYTES) {
                throw new IllegalStateException("actual deadline corpus profile is missing or differs");
            }
            return corpus;
        } catch (IOException error) { throw new IllegalStateException("cannot read actual producer golden", error); }
    }
}
