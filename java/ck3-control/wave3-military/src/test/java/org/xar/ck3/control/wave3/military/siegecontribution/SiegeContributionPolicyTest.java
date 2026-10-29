package org.xar.ck3.control.wave3.military.siegecontribution;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Decision;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Occurrence;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Province;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Reason;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Request;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Selection;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Status;
import org.xar.ck3.control.wave3.military.siegecontribution.SiegeContributionPolicy.Subject;

final class SiegeContributionPolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = SiegeContributionPolicyTest.class.getResourceAsStream("/siegecontribution/original-producer-golden-v1.json")) {
            assertNotNull(input, "unchanged real producer and normalizers must be captured; absence is RED");
            return StrictJson.parse(input.readNBytes(71_681), 71_680);
        }
    }
    private static Request request(List<Occurrence> occurrences, Selection selection) {
        return new Request(new Province(7, selection, occurrences), new Subject(true, 4, 7, null, List.of()));
    }
    private static Occurrence row(int index, Integer nativeId, Boolean eligible, List<Integer> regiments) {
        return new Occurrence(index, 4, nativeId, eligible, regiments);
    }

    @TestFactory
    Stream<DynamicTest> originalProducerAndBothNativeNormalizers() throws IOException {
        JsonNode fixture = golden(); assertFalse(fixture.get("actual_live_qualification").booleanValue());
        assertEquals(37, fixture.get("cases").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                // Decode the original JSON token stream. Recanonicalizing a float could mask a wrong raw type.
                byte[] raw = vector.get("request_raw").textValue().getBytes(StandardCharsets.UTF_8);
                if (vector.get("expected_rejection").booleanValue()) {
                    assertEquals("ValueError", vector.get("legacy_error_type").textValue());
                    assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode(raw));
                } else {
                    Request decoded = SiegeContributionCodec.decode(raw);
                    assertEquals(vector.get("expected_decision"), StrictJson.parse(SiegeContributionCodec.evaluate(raw)));
                    Request roundTrip = SiegeContributionCodec.decode(SiegeContributionCodec.encodeRequest(decoded));
                    assertEquals(decoded, roundTrip);
                    assertEquals(SiegeContributionPolicy.observe(decoded), SiegeContributionPolicy.observe(roundTrip));
                    if (vector.get("name").textValue().equals("actual6356_excluded")) {
                        assertEquals("historical_actual_consumed_projection", vector.get("origin").textValue());
                        Decision actual = SiegeContributionPolicy.observe(decoded);
                        assertEquals(Status.EXCLUDED, actual.status()); assertEquals(Integer.valueOf(33_554_783), actual.nativeCarmyId());
                    }
                }
            }));
        }
        return tests.stream();
    }

    @Test
    void preservesNativeOrderAndDuplicatePublicIdentitiesRatherThanTreatingThemAsASet() {
        Request input = request(List.of(row(0, 10, true, List.of(7, 7, 3)), row(1, 11, true, null)), new Selection(10, null, null));
        Decision decision = SiegeContributionPolicy.observe(input);
        assertEquals(Status.ELIGIBLE, decision.status()); assertEquals(List.of(0, 1), decision.occurrenceIndices());
        assertEquals(Integer.valueOf(10), decision.nativeCarmyId()); assertEquals(Boolean.TRUE, decision.matchesCurrentSelection());
        assertEquals(List.of(7, 7, 3), input.province().provinceUnitOccurrences().getFirst().qualifiedRegimentIds());
        assertEquals(Status.EXCLUDED, SiegeContributionPolicy.observe(request(List.of(row(0, 10, true, List.of()), row(1, 11, false, List.of())), null)).status());
    }

    @Test
    void unknownMeasurementStaysUnknownAndNeverFallsBackToTheOrdinaryArmyIdentity() {
        Request unknown = request(List.of(row(0, null, null, null)), new Selection(99, 4, true));
        Decision unavailable = SiegeContributionPolicy.observe(unknown);
        assertEquals(Status.UNAVAILABLE, unavailable.status()); assertEquals(Reason.SUBJECT_MEASUREMENT_UNAVAILABLE, unavailable.reason());
        assertNull(unavailable.nativeCarmyId()); assertNull(unavailable.matchesCurrentSelection()); assertNull(unavailable.occurrenceIndices());
        Decision excludedWithoutNativeId = SiegeContributionPolicy.observe(request(List.of(row(0, null, false, List.of())), new Selection(99, 4, true)));
        assertEquals(Status.EXCLUDED, excludedWithoutNativeId.status()); assertNull(excludedWithoutNativeId.nativeCarmyId());
        assertEquals(Boolean.FALSE, excludedWithoutNativeId.matchesCurrentSelection());
        assertEquals(Reason.PROVINCE_UNAVAILABLE, SiegeContributionPolicy.observe(request(null, null)).reason());
        assertEquals(Reason.SUBJECT_MEASUREMENT_UNAVAILABLE, SiegeContributionPolicy.observe(request(List.of(), null)).reason());
    }

    @Test
    void arrivedSubjectRequiresAnActualKnownEmptyRouteAndNoCommittedTarget() {
        Province province = new Province(7, null, List.of(row(0, 10, true, List.of())));
        for (Subject subject : List.of(new Subject(true, 4, 8, null, List.of()), new Subject(true, 4, 7, 8, List.of()),
                new Subject(true, 4, 7, null, null), new Subject(true, 4, 7, null, List.of(8)))) {
            assertEquals(Reason.SUBJECT_NOT_ARRIVED, SiegeContributionPolicy.observe(new Request(province, subject)).reason());
        }
        assertEquals(Reason.SUBJECT_UNAVAILABLE, SiegeContributionPolicy.observe(new Request(province, null)).reason());
        assertEquals(Reason.SUBJECT_UNAVAILABLE, SiegeContributionPolicy.observe(new Request(province, new Subject(null, 4, 7, null, List.of()))).reason());
    }

    @Test
    void normalizersKeepSlotZeroAndNullableCollectionsButRejectInvalidCrossFieldClaims() {
        Request slotZero = new Request(new Province(7, new Selection(0, 0, null), List.of(new Occurrence(0, 0, 0, true, null))),
                new Subject(true, 0, 7, null, List.of()));
        assertEquals(Status.ELIGIBLE, SiegeContributionPolicy.observe(slotZero).status());
        assertEquals(Integer.valueOf(0), SiegeContributionPolicy.observe(slotZero).nativeCarmyId());
        assertThrows(IllegalArgumentException.class, () -> row(0, null, true, List.of()));
        assertThrows(IllegalArgumentException.class, () -> row(0, 4, false, null));
        assertThrows(IllegalArgumentException.class, () -> row(0, 4, null, List.of()));
        assertThrows(IllegalArgumentException.class, () -> request(List.of(row(1, 4, true, List.of())), null));
        assertThrows(IllegalArgumentException.class, () -> new Selection(-1, null, null));
        assertThrows(IllegalArgumentException.class, () -> new Subject(true, 4, 0, null, List.of()));
        assertThrows(IllegalArgumentException.class, () -> row(0, 4, true, List.of(-1)));
    }

    @Test
    void immutableRecordsCopyNativeCollectionsAndRoundTripAllThreeNullableMeanings() {
        List<Integer> regiments = new ArrayList<>(List.of(5)); List<Occurrence> occurrences = new ArrayList<>(List.of(row(0, 10, true, regiments)));
        Request input = request(occurrences, null); regiments.add(6); occurrences.clear();
        assertEquals(List.of(5), input.province().provinceUnitOccurrences().getFirst().qualifiedRegimentIds());
        assertEquals(1, input.province().provinceUnitOccurrences().size());
        assertThrows(UnsupportedOperationException.class, () -> input.province().provinceUnitOccurrences().clear());
        for (Request variant : List.of(input, request(null, null), request(List.of(), null), request(List.of(row(0, null, null, null)), null))) {
            assertEquals(variant, SiegeContributionCodec.decode(SiegeContributionCodec.encodeRequest(variant)));
        }
    }

    @Test
    void wrapperAndRawNativeTypesAreStrictWhileNormalizerOptionalFieldsAndSdkExtensionsStayCompatible() {
        ObjectNode input = (ObjectNode) StrictJson.parse(SiegeContributionCodec.encodeRequest(request(List.of(row(0, 10, false, List.of())), new Selection(10, 4, true))));
        ObjectNode occurrence = (ObjectNode) input.get("province").get("active_siege").get("province_unit_occurrences").get(0);
        occurrence.remove("native_carmy_id"); ((ObjectNode) input.get("province").get("current_besieging_army_selection")).remove("public_unit_id");
        Request normalized = SiegeContributionCodec.decode(StrictJson.canonical(input));
        assertNull(normalized.province().provinceUnitOccurrences().getFirst().nativeCarmyId());
        assertNull(normalized.province().currentBesiegingArmySelection().publicUnitId());
        String raw = new String(StrictJson.canonical(input), StandardCharsets.UTF_8);
        String sdkExtension = raw.replace("\"province\":{", "\"province\":{\"future_sdk_fraction\":1.0,");
        assertFalse(sdkExtension.equals(raw)); assertEquals(normalized, SiegeContributionCodec.decode(sdkExtension.getBytes(StandardCharsets.UTF_8)));
        for (String token : List.of("0.0", "true", "\"0\"", "null", "2147483648", "-1")) {
            String wrong = raw.replace("\"occurrence_index\":0", "\"occurrence_index\":" + token);
            assertFalse(raw.equals(wrong)); assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode(wrong.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode extra = input.deepCopy(); extra.put("native_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode(StrictJson.canonical(extra)));
        for (String required : List.of("schema", "province", "subject")) {
            ObjectNode missing = input.deepCopy(); missing.remove(required);
            assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode(StrictJson.canonical(missing)));
        }
        assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode("{\"schema\":1,\"schema\":1}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> SiegeContributionCodec.decode(new byte[65_537]));
        assertTrue(StrictJson.parse(SiegeContributionCodec.encodeDecision(SiegeContributionPolicy.observe(request(null, null)))).get("occurrence_indices") == null);
    }
}
