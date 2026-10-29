package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Assessment;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Field;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Kind;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Presence;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Reason;

final class TimelineOwnerTest {
    private static final JsonNode GOLDEN = golden();

    @TestFactory
    Stream<DynamicTest> originalProducerAndExplicitlyDocumentedTypeAndMissingHardening() {
        List<DynamicTest> cases = new ArrayList<>();
        for (JsonNode row : GOLDEN.get("cases")) {
            cases.add(DynamicTest.dynamicTest(row.get("id").textValue(), () -> {
                byte[] input = bytes(row.get("input_json").textValue());
                String expected = row.get("java_expected").textValue();
                if (expected.equals("rejected")) {
                    assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(input));
                } else {
                    byte[] before = input.clone();
                    Assessment observed = TimelineOwnerCodec.assess(input);
                    assertEquals(Kind.valueOf(expected.toUpperCase(Locale.ROOT)), observed.kind());
                    assertEquals(observed, TimelineOwnerCodec.decode(TimelineOwnerCodec.encode(observed)));
                    assertEquals(new String(before, StandardCharsets.UTF_8), new String(input, StandardCharsets.UTF_8));
                    assertFalse(observed.replayAllowed()); assertFalse(observed.actionAdmissionGranted());
                    assertFalse(observed.sourceAdmissionGranted()); assertEquals(0, observed.savedDayCredit());
                    String compatibility = row.get("compatibility").textValue();
                    if (compatibility.equals("equivalent")) {
                        assertEquals(row.get("legacy_result").booleanValue(), observed.sameFacts());
                    } else {
                        assertTrue(row.get("legacy_result").booleanValue(), "real old producer must demonstrate the documented gap");
                        assertFalse(observed.sameFacts());
                    }
                }
            }));
        }
        return cases.stream();
    }

    @Test
    void actualCaptureIncludesAllFiveOwnedProducersThroughExistingConsumers() {
        assertEquals("xar.ck3.java-timeline-owner-producer-golden/v1", GOLDEN.get("schema").textValue());
        assertEquals("actual_native_driver_pure_owner_leaves_and_existing_fake_wire_consumers", GOLDEN.get("method").textValue());
        assertEquals(38, GOLDEN.get("cases").size());
        assertEquals("LifeAdvancePauseMapUnavailableRetryTests", GOLDEN.get("full_pause_test_case").textValue());
        assertEquals(25, GOLDEN.get("original_tests").intValue());
        assertEquals(17, GOLDEN.get("selected_native_driver_tests").size());
        assertEquals(0, GOLDEN.get("original_skipped").intValue());
        JsonNode calls = GOLDEN.get("consumer_calls"); assertEquals(5, calls.size());
        for (JsonNode row : calls) {
            assertTrue(row.get("calls").intValue() > 0);
            assertEquals(row.get("calls").intValue(), row.get("true").intValue() + row.get("false").intValue());
        }
        for (String name : List.of("game_rpc", "native_calls", "ledger_writes", "saved_day_credit")) {
            assertEquals(0, GOLDEN.get(name).intValue());
        }
        JsonNode provenance = GOLDEN.get("source_provenance");
        assertEquals("repo-python-excluding-interpreter-prefixes/v1", provenance.get("scope").textValue());
        assertEquals("not_granted_by_repo_source_observer", provenance.get("external_dependency_qualification").textValue());
        assertEquals(0, provenance.get("initial_repo_sources").intValue());
        assertEquals(0, provenance.get("unrecorded_repo_sources").size());
        assertTrue(provenance.get("source_pre_post_equal").isBoolean());
        assertTrue(provenance.get("source_pre_post_equal").booleanValue());
        int recorded = provenance.get("recorded_repo_sources").intValue();
        assertTrue(recorded > 0); assertEquals(recorded, GOLDEN.get("source_refs").size());
        for (String key : List.of("after_imports_repo_sources", "after_suite_repo_sources")) {
            assertTrue(provenance.get(key).intValue() > 0 && provenance.get(key).intValue() <= recorded);
        }
        assertTrue(provenance.get("interpreter_prefixes").isArray());
        assertTrue(provenance.get("interpreter_prefixes").size() > 0);
        for (JsonNode prefix : provenance.get("interpreter_prefixes")) { assertFalse(StrictJson.text(prefix).isEmpty()); }
        Set<String> sourcePaths = new HashSet<>();
        for (JsonNode source : GOLDEN.get("source_refs")) {
            String path = StrictJson.text(source.get("path"));
            assertTrue(path.endsWith(".py") && sourcePaths.add(path));
            assertTrue(source.get("bytes").isIntegralNumber() && source.get("bytes").bigIntegerValue().signum() > 0);
            assertTrue(StrictJson.text(source.get("sha256")).matches("[0-9a-f]{64}"));
        }
        assertEquals(0, GOLDEN.get("java_calls").get("manual_cases").intValue());
        assertEquals(0, GOLDEN.get("java_calls").get("consumers").intValue());
        assertEquals("0", GOLDEN.get("fixture_environment").get("XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1").textValue());
        assertEquals("0", GOLDEN.get("fixture_environment").get("PYTHONOPTIMIZE").textValue());
        assertEquals(0, GOLDEN.get("fixture_environment").get("python_optimize_level").intValue());
        assertFalse(GOLDEN.get("machine_id").textValue().isEmpty());
    }

    @Test
    void missingExplicitNullAndPresentRemainDifferentImmutableFields() {
        assertNotEquals(Field.<BigInteger>missing(), Field.<BigInteger>explicitNull());
        assertNotEquals(Field.<BigInteger>explicitNull(), Field.of(BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> new Field<>(Presence.MISSING, Optional.of(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class, () -> new Field<BigInteger>(Presence.PRESENT, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> Field.missing().required());
    }

    @Test
    void scalarLookalikesAreRejectedFromTheOriginalRawTokens() {
        String original = row("same-paused-episode").get("input_json").textValue();
        assertTrue(original.contains("\"paused\":true"));
        for (String token : List.of("1", "1.0", "\"true\"")) {
            String malformed = original.replace("\"paused\":true", "\"paused\":" + token);
            assertNotEquals(original, malformed);
            assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(bytes(malformed)), token);
        }
        String rawFloat = row("decimal-generation-not-integer").get("input_json").textValue();
        assertTrue(rawFloat.contains("\"connection_generation\":1.0"));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(bytes(rawFloat)));
    }

    @Test
    void completeUiIdentityUsesValuesAndJsonKindsAndCannotBeMutatedThroughInputTree() {
        JsonNode first = StrictJson.parse(bytes("{\"instance_id\":1,\"option_count\":1,\"extra\":{\"x\":1,\"text\":\"汉字\"}}"));
        JsonNode reordered = StrictJson.parse(bytes("{\"extra\":{\"text\":\"汉字\",\"x\":1},\"option_count\":1,\"instance_id\":1}"));
        UiIdentity immutable = UiIdentity.fromJson(first, true);
        assertEquals(immutable, UiIdentity.fromJson(reordered, true));
        JsonNode decimal = StrictJson.parse(bytes("{\"instance_id\":1,\"option_count\":1,\"extra\":{\"x\":1.0,\"text\":\"汉字\"}}"));
        assertNotEquals(immutable, UiIdentity.fromJson(decimal, true));
        ((com.fasterxml.jackson.databind.node.ObjectNode) first.get("extra")).put("x", 2);
        assertEquals(immutable, UiIdentity.fromJson(reordered, true));
        assertNotEquals(immutable, UiIdentity.fromJson(first, true));
        assertEquals(UiIdentity.fromJson(StrictJson.parse(bytes("{\"x\":1.0}")), false),
                UiIdentity.fromJson(StrictJson.parse(bytes("{\"x\":1.00}")), false));
    }

    @Test
    void strictOuterRequestAndDuplicateFieldsCannotBecomeFacts() {
        String original = row("same-paused-episode").get("input_json").textValue();
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(bytes("{\"schema\":null,\"schema\":null}")));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(bytes(original.replaceFirst("\\{", "{\"admission_green\":true,"))));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(bytes(original.replace("\"resume_owner\"", "\"resume_and_retry\""))));
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.assess(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void matchingOwnerAndZeroElapsedPopupCannotGrantReplayOrSavedProgress() {
        Assessment zero = TimelineOwnerCodec.assess(bytes(row("zero-day-popup-owner").get("input_json").textValue()));
        assertEquals(Reason.SAME_POPUP_OWNER, zero.reason());
        assertFalse(zero.replayAllowed()); assertFalse(zero.actionAdmissionGranted()); assertEquals(0, zero.savedDayCredit());
        byte[] observed = TimelineOwnerCodec.encode(zero);
        String forged = new String(observed, StandardCharsets.UTF_8).replace("\"replay_allowed\":false", "\"replay_allowed\":true");
        assertThrows(IllegalArgumentException.class, () -> TimelineOwnerCodec.decode(bytes(forged)));
        assertThrows(IllegalArgumentException.class, () -> new Assessment(Kind.CHANGED, Reason.SAME_POPUP_OWNER));
    }

    @Test
    void nativeSizedAndLargerIntegerFactsAreNeverRoundedToDouble() {
        JsonNode request = StrictJson.parse(bytes(row("integer-date-beyond-double-exact").get("input_json").textValue()));
        assertEquals(new BigInteger("9007199254740993"), TimelineOwnerCodec.frame(request.get("previous")).dateRaw().required());
        assertEquals(new BigInteger("9007199254740994"), TimelineOwnerCodec.frame(request.get("refreshed")).dateRaw().required());
        assertEquals(Kind.SAME_FACTS, TimelineOwnerCodec.assess(bytes(row("exact-huge-revisions").get("input_json").textValue())).kind());
    }

    @Test
    void unrelatedSdkExtensionsAreProjectedWithoutBecomingAdmission() {
        String original = row("same-paused-episode").get("input_json").textValue();
        String extended = original.replace("\"previous\":{", "\"previous\":{\"unrelated_sdk_cache\":{\"admission_green\":true},");
        assertNotEquals(original, extended);
        Assessment observed = TimelineOwnerCodec.assess(bytes(extended));
        assertEquals(TimelineOwnerCodec.assess(bytes(original)), observed);
        assertFalse(observed.actionAdmissionGranted()); assertFalse(observed.sourceAdmissionGranted());
    }

    @Test
    void actualProbeReturnsCodecFactsAndKeepsInvalidRequestsSeparate() throws IOException {
        String request = row("same-paused-episode").get("input_json").textValue();
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        TimelineOwnerProbe.run(new ByteArrayInputStream(bytes(request + "\n{\"schema\":null}\n")), output);
        String[] lines = output.toString(StandardCharsets.UTF_8).split("\n", -1);
        assertEquals(3, lines.length); assertEquals("", lines[2]);
        assertEquals(TimelineOwnerCodec.assess(bytes(request)), TimelineOwnerCodec.decode(bytes(lines[0])));
        assertEquals("invalid_contract", StrictJson.parse(bytes(lines[1])).get("test_transport_status").textValue());
    }

    @Test
    void actualProbeRejectsMalformedUtf8WithoutManufacturingFacts() throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        TimelineOwnerProbe.run(new ByteArrayInputStream(new byte[] {(byte) 0xff, '\n'}), output);
        JsonNode result = StrictJson.parse(output.toByteArray());
        assertEquals(1, result.size()); assertEquals("invalid_contract", result.get("test_transport_status").textValue());
    }

    @Test
    void actualProbeBoundsRequestsAndRequiresCompleteLineBeforeResponding() throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        assertThrows(IOException.class, () -> TimelineOwnerProbe.run(new ByteArrayInputStream(bytes("{}")), output));
        assertEquals(0, output.size());
        assertThrows(IOException.class, () -> TimelineOwnerProbe.run(new ByteArrayInputStream(new byte[TimelineOwnerProbe.MAX_REQUEST_BYTES + 1]), output));
        assertEquals(0, output.size());
        TimelineOwnerProbe.run(new ByteArrayInputStream(new byte[0]), output);
        assertEquals(0, output.size());
    }

    private static JsonNode row(String id) {
        for (JsonNode value : GOLDEN.get("cases")) { if (id.equals(value.get("id").textValue())) { return value; } }
        throw new IllegalStateException("actual producer fixture absent:" + id);
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() {
        try (InputStream stream = TimelineOwnerTest.class.getResourceAsStream("/timelineowner/producer-golden.json")) {
            if (stream == null) { throw new IllegalStateException("actual timeline-owner producer golden missing; no skipped pass"); }
            JsonNode golden = StrictJson.parse(stream.readNBytes(98_305), 98_304);
            TimelineOwnerSourceView.readProvenance(golden);
            return golden;
        } catch (IOException error) { throw new IllegalStateException("cannot read actual timeline-owner golden", error); }
    }
}
