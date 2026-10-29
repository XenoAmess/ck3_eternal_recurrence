package org.xar.ck3.control.wave2.military.forecast;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;

final class ForecastWireCodecTest {
    private static ObjectNode estimate() throws Exception {
        var value = FixedContactForecastTest.liveCase();
        var forecast = FixedContactForecast.forecast(value.payload(), value.request());
        var decoded = ForecastWireCodec.fromForecast(forecast);
        assertEquals(forecast.toJson(), decoded.toJson());
        assertEquals(decoded, ForecastWireCodec.decode(ForecastWireCodec.encode(decoded)));
        return decoded.toJson();
    }
    @Test void realProducerToStrictCodecToAdmissionRoundTrip() throws Exception {
        var value = FixedContactForecastTest.liveCase();
        for (int version = 1; version <= 3; version++) {
            if (version == 2) FixedContactForecastTest.nativeV2(value);
            if (version == 3) FixedContactForecastTest.nativeV3(value, -600_000);
            var forecast = FixedContactForecast.forecast(value.payload(), value.request());
            var decoded = ForecastWireCodec.fromForecast(forecast);
            assertInstanceOf(ForecastWireCodec.Estimate.class, decoded);
            assertEquals(forecast.toJson(), ForecastWireCodec.decode(ForecastWireCodec.encode(decoded)).toJson());
            for (boolean relief : List.of(false, true)) assertEquals(FixedContactForecast.contactAdmission(forecast, relief),
                    ForecastWireCodec.contactAdmission(decoded, relief));
        }
    }
    @Test void unavailableBranchesKeepExactRequiredErrorAndDoNotBecomeEstimates() {
        for (var reason : FixedContactForecast.UnavailableReason.values()) {
            if (reason == FixedContactForecast.UnavailableReason.MODEL_UNAVAILABLE) {
                for (var error : FixedContactForecast.ModelError.values()) {
                    var source = new FixedContactForecast.Unavailable(reason, error);
                    assertEquals(source.toJson(), ForecastWireCodec.fromForecast(source).toJson());
                }
            } else {
                var source = new FixedContactForecast.Unavailable(reason);
                var decoded = ForecastWireCodec.fromForecast(source);
                assertEquals(source.toJson(), decoded.toJson());
                assertFalse(ForecastWireCodec.contactAdmission(decoded, false).admitted());
                var wrong = source.toJson(); wrong.putNull("error_type");
                assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(wrong));
            }
        }
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(object().put("status", "unknown")));
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(object().put("status", "model_unavailable")));
    }
    @Test void missingNullWrongAndUnknownFieldsAreDistinct() throws Exception {
        var good = estimate();
        for (String key : List.of("capture", "advantage_input", "sample_count", "commander_or_knight_death_probability", "resolved_win_wilson95")) {
            var missing = good.deepCopy(); missing.remove(key);
            assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(missing), key);
        }
        var changed = good.deepCopy(); changed.put("typo_field", 1);
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(changed));
        var capture = good.deepCopy(); capture.set("capture", array());
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(capture));
        var missingDomains = good.deepCopy(); missingDomains.putNull("missing_required_domains");
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(missingDomains));
        var falseDeath = good.deepCopy(); falseDeath.put("commander_or_knight_death_probability", 0);
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(falseDeath));
    }
    @Test void integerFieldsRejectBooleanAndEqualFloatingNumbers() throws Exception {
        var good = estimate();
        for (String key : List.of("sample_count", "horizon_days", "player_wins", "player_losses", "no_resolution")) {
            var bool = good.deepCopy(); bool.put(key, true);
            assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(bool), key);
            var floating = good.deepCopy(); floating.put(key, good.path(key).doubleValue());
            assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(floating), key);
        }
        var wrongCensus = good.deepCopy(); wrongCensus.put("no_resolution", -1);
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(wrongCensus));
        var wrongProbability = good.deepCopy(); wrongProbability.put("player_win_probability_unconditional_lower", 0.123456789);
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(wrongProbability));
    }
    @Test void legalPublicSlotAndV2CharacterZeroRoundTripButV3SelectedZeroRejects() {
        var selected = new ResearchEnvelope.SelectedCommanders(BigInteger.ZERO, null);
        var v2 = new FixedContactForecast.AdvantageInput(ConstructorAdvantage.Source.V2_CONSTRUCTOR, BigInteger.ZERO,
                "A".repeat(64), null, selected, List.of(BigInteger.ZERO, BigInteger.ONE));
        var base = object(); base.put("snapshot_id", "zero-public-slot");
        var distribution = new ForecastWireCodec.Distribution(4, 0, 0, 4, null, 0.0, 1.0, null, BigInteger.ZERO, 0.0, 0.0);
        var metadata = new ForecastWireCodec.Metadata("research-only-bounded-core", false, "A".repeat(64), "test-source", 4);
        var message = new ForecastWireCodec.Estimate(metadata, distribution, v2, List.of(), new CombatInputs.Capture(base));
        assertEquals(message, ForecastWireCodec.decode(ForecastWireCodec.encode(message)));
        assertFalse(ForecastWireCodec.contactAdmission(message, false).admitted());
        var wrong = message.toJson(); var advantage = object(wrong.get("advantage_input"), "advantage");
        advantage.put("source", ConstructorAdvantage.Source.V3_NATIVE.wire()); advantage.remove(List.of("scope", "complete_encounter_advantage_ready"));
        assertThrows(CombatInputException.class, () -> ForecastWireCodec.decode(wrong));
        assertThrows(CombatInputException.class, () -> new ConstructorAdvantage.Selection(BigInteger.ZERO, BigInteger.ONE,
                BigInteger.ZERO, selected, "A".repeat(64), ConstructorAdvantage.Source.V3_NATIVE));
    }
    @Test void exactRaw64AndOpaqueCaptureStayInOriginalJsonDomain() throws Exception {
        var good = estimate(); var value = object(good.get("advantage_input"), "advantage");
        value.put("source", ConstructorAdvantage.Source.V3_NATIVE.wire()); value.put("zero_roll_raw", BigInteger.ONE.shiftLeft(63).negate());
        value.put("model_sha256", "B".repeat(64)); value.putNull("fallback_reason");
        value.set("selected_commander_character_ids", array().addNull().addNull());
        var assumptions = array(); FixedContactForecast.assumptions(new FixedContactForecast.AdvantageInput(ConstructorAdvantage.Source.V3_NATIVE,
                BigInteger.ZERO, "B".repeat(64), null, new ResearchEnvelope.SelectedCommanders(null, null), List.of(BigInteger.ZERO, BigInteger.ONE))).forEach(assumptions::add);
        good.set("assumptions", assumptions);
        var capture = object(good.get("capture"), "capture");
        capture.put("revision", new BigInteger("9007199254740993")); capture.put("file_id", "18446744073709551615"); capture.putNull("optional");
        var decoded = ForecastWireCodec.decode(CombatJson.canonical(good));
        assertEquals(good, decoded.toJson());
        assertEquals(new BigInteger("9007199254740993"), decoded.toJson().path("capture").path("revision").bigIntegerValue());
        assertTrue(decoded.toJson().path("capture").path("file_id").isTextual());
        var detached = decoded.toJson(); object(detached.get("capture"), "capture").put("revision", 1);
        assertEquals(new BigInteger("9007199254740993"), decoded.toJson().path("capture").path("revision").bigIntegerValue());
    }
    @Test void invalidNegativeRiskCannotGrantAdmission() {
        var forecast = object(); forecast.put("status", "estimated"); forecast.set("resolved_win_wilson95", object().put("lower", .8));
        forecast.put("player_p90_hard_loss_fraction", .1); forecast.put("player_stack_wipe_probability", .01);
        forecast.put("no_resolution", 0); forecast.put("sample_count", 100); forecast.putNull("commander_or_knight_death_probability");
        assertTrue(FixedContactForecast.contactAdmission(forecast).admitted());
        for (String key : List.of("player_p90_hard_loss_fraction", "player_stack_wipe_probability", "no_resolution")) {
            var wrong = forecast.deepCopy(); wrong.put(key, -1);
            assertFalse(FixedContactForecast.contactAdmission(wrong).admitted(), key);
        }
        var upper = forecast.deepCopy(); object(upper.get("resolved_win_wilson95"), "interval").put("lower", 2);
        assertFalse(FixedContactForecast.contactAdmission(upper).admitted());
        var death = forecast.deepCopy(); death.put("commander_or_knight_death_probability", -0.1);
        assertEquals("invalid_character_death_risk", FixedContactForecast.contactAdmission(death).toJson().path("reason").textValue());
    }
}
