package org.xar.ck3.control.wave2.military.disembark;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.ArrayValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.DecimalValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.NullValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.ObjectValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.TextValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.Value;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

final class DisembarkPenaltyTest {
    private static ObjectValue golden() throws IOException {
        try (var stream = DisembarkPenaltyTest.class.getResourceAsStream("/disembark/original-producer-golden.json")) {
            assertNotNull(stream, "original producer golden must be captured by the shared Job owner; absence is not a skip");
            return EvidenceJson.object(EvidenceJson.parse(stream.readAllBytes()));
        }
    }
    private static ArrayValue array(ObjectValue object, String key) { return assertInstanceOf(ArrayValue.class, object.required(key)); }
    private static byte[] bytes(Value value) { return EvidenceJson.encode(value); }
    private static byte[] raw(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    @Test void originalProducerAndSerializationRoundTrips() throws IOException {
        ObjectValue golden = golden();
        assertFalse(((TextValue) golden.required("machine_id")).value().isBlank());
        assertFalse(((TextValue) golden.required("observed_at_utc")).value().isBlank());
        for (Value value : array(golden, "samples").values()) {
            ObjectValue sample = EvidenceJson.object(value); ObjectValue input = EvidenceJson.object(sample.required("input"));
            var projection = DisembarkCodec.decodeProjectionRequest(bytes(input));
            assertEquals(sample.required("expected_projection"), EvidenceJson.parse(DisembarkCodec.encodeProjection(projection)));
            assertFalse(projectionValueFlag(projection));
            if (input.required("raw") != NullValue.INSTANCE) {
                var observed = DisembarkCodec.normalize(bytes(input.required("raw")));
                assertEquals(sample.required("expected_normalized"), EvidenceJson.parse(DisembarkCodec.encodeObservation(observed)));
                assertEquals(observed, DisembarkCodec.normalize(DisembarkCodec.encodeObservation(observed)));
            }
        }
    }

    @Test void realWholeRowAndServiceConsumersUseHeldSnapshotEvidence() throws IOException {
        for (Value value : array(golden(), "service_rows").values()) {
            ObjectValue sample = EvidenceJson.object(value);
            var source = DisembarkCodec.sourceFromSnapshot(sample.required("snapshot"), sample.required("hello"));
            assertEquals(sample.required("expected_service_row"), DisembarkCodec.projectServiceRow(sample.required("row"), source));
            Optional<DisembarkPenalty.Observation> normalized = DisembarkCodec.normalizeRowProjection(sample.required("row"));
            assertEquals(sample.required("expected_normalized_leaf"), normalized.<Value>map(DisembarkCodec::observationValue).orElse(NullValue.INSTANCE));
        }
    }

    @Test void rawTokenRejectionsMatchOriginalProducer() throws IOException {
        for (Value value : array(golden(), "rejections").values()) {
            ObjectValue sample = EvidenceJson.object(value); String json = ((TextValue) sample.required("raw_json")).value();
            assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.normalize(raw(json)), sample.required("id").toString());
        }
    }

    @Test void omittedAndPresentNullRemainDifferent() {
        assertEquals(Optional.empty(), DisembarkCodec.normalizeRowProjection(EvidenceJson.parse(raw("{\"status\":\"available\",\"sdk_extra\":1.0}"))));
        assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.normalizeRowProjection(EvidenceJson.parse(raw("{\"status\":\"available\",\"current_disembark_penalty_v1\":null}"))));
        assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.normalize(raw("null")));
    }

    @Test void wrongBuildCannotPublishEvenUnavailableObservation() {
        String unavailable = "{\"schema_version\":1,\"source\":\"native_current_disembark_penalty_days_12003\",\"status\":\"unavailable\",\"remaining_days\":null,\"unavailable_reason\":\"not_bound\"}";
        assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.decodeProjectionRequest(raw("{\"raw\":" + unavailable + ",\"source_provenance\":{}}")));
        assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.normalizeRowProjection(EvidenceJson.parse(raw("{\"status\":\"unavailable\",\"current_disembark_penalty_v1\":" + unavailable + "}"))));
    }

    @Test void opaqueDecimalEvidenceRetainsItsJsonDomain() {
        var projection = DisembarkCodec.decodeProjectionRequest(raw("{\"raw\":null,\"source_provenance\":{\"extra\":1.0,\"integer\":18446744073709551615}}"));
        ObjectValue encoded = EvidenceJson.object(EvidenceJson.parse(DisembarkCodec.encodeProjection(projection)));
        assertInstanceOf(DecimalValue.class, EvidenceJson.object(encoded.required("source_provenance")).required("extra"));
        assertEquals("1.0", ((DecimalValue) projection.sourceProvenance().document().required("extra")).token());
    }

    @Test void declaredSourceScalarsRejectIntegerSubstitutesWithoutNarrowingExtensions() {
        for (String source : new String[]{"{\"revision\":true}", "{\"revision\":1.0}", "{\"native_revision\":\"7\"}",
                "{\"date_raw\":1.0}", "{\"date_raw\":2147483648}", "{\"snapshot_id\":false}", "{\"game_version\":3}"}) {
            assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.decodeProjectionRequest(raw("{\"raw\":null,\"source_provenance\":" + source + "}")));
        }
        var projection = DisembarkCodec.decodeProjectionRequest(raw("{\"raw\":null,\"source_provenance\":{\"revision\":18446744073709551615,\"native_revision\":null,\"extra_float\":1.0}}"));
        assertEquals("18446744073709551615", ((EvidenceJson.IntegerValue) projection.sourceProvenance().document().required("revision")).value().toString());
        assertInstanceOf(DecimalValue.class, projection.sourceProvenance().document().required("extra_float"));
    }

    @Test void sdkServiceRowChecksTheDeclaredPublicCunitIdIncludingZero() {
        var source = new DisembarkPenalty.SourceProvenance(EvidenceJson.object(EvidenceJson.parse(raw("{}"))));
        for (String id : new String[]{"true", "1.0", "-1", "2147483648", "\"1\""}) {
            assertThrows(IllegalArgumentException.class, () -> DisembarkCodec.projectServiceRow(EvidenceJson.parse(raw("{\"status\":\"available\",\"army_id\":" + id + "}")), source));
        }
        ObjectValue row = DisembarkCodec.projectServiceRow(EvidenceJson.parse(raw("{\"status\":\"available\",\"army_id\":0,\"sdk_extension\":1.0}")), source);
        assertEquals(EvidenceJson.integer(0), row.required("army_id"));
    }

    @Test void malformedJsonAndDuplicateFieldsFailBeforeDomainConstruction() {
        for (String value : new String[]{"{\"raw\":null,\"raw\":null}", "{}{}", "[1", "{\"x\":NaN}"}) {
            assertThrows(IllegalArgumentException.class, () -> EvidenceJson.parse(raw(value)));
        }
        assertThrows(IllegalArgumentException.class, () -> EvidenceJson.parse(new byte[]{(byte) 0xc3, 0x28}));
    }

    private static boolean projectionValueFlag(DisembarkPenalty.Projection projection) {
        return ((EvidenceJson.BooleanValue) DisembarkCodec.projectionValue(projection).required("future_route_landing_days_ready")).value();
    }
}
