package org.xar.ck3.control.admission.deadlinecredit;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;

final class CampaignDeadlineTest {
    private static final JsonNode GOLDEN = loadGolden();

    @TestFactory
    Stream<DynamicTest> actualExistingProducerCases() {
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode entry : GOLDEN.get("cases")) {
            tests.add(DynamicTest.dynamicTest(entry.get("name").textValue(), () -> {
                if (entry.at("/outcome/status").textValue().equals("rejected")) {
                    assertThrows(IllegalArgumentException.class, () -> evaluate(entry));
                } else {
                    assertEquals(entry.at("/outcome/value"), evaluate(entry));
                }
            }));
        }
        return tests.stream();
    }

    @Test
    void fixtureCapturesActualProducerAndDoesNotGrantLiveCredit() {
        assertEquals("actual_existing_producers_no_game_no_runtime_mutation", GOLDEN.get("method").textValue());
        assertEquals(24, GOLDEN.get("cases").size());
        assertEquals(0, GOLDEN.get("new_game_rpc").intValue());
        assertEquals(0, GOLDEN.get("ledger_writes").intValue());
        assertEquals(0, GOLDEN.get("saved_day_credit").intValue());
        assertEquals(2, GOLDEN.get("sources").size());
        assertTrue(GOLDEN.get("sources").get(0).get("sha256").textValue().matches("[0-9a-f]{64}"));
    }

    @Test
    void configurationHasExactJsonRoundTripAndOwnsImmutableSchedule() {
        CampaignDeadline.Configuration original = config("main");
        byte[] first = CampaignDeadlineCodec.encodeConfiguration(original);
        CampaignDeadline.Configuration parsed = CampaignDeadlineCodec.decodeConfiguration(first, calendar());
        assertEquals(original, parsed);
        assertArrayEquals(first, CampaignDeadlineCodec.encodeConfiguration(parsed));
        assertThrows(UnsupportedOperationException.class, () -> parsed.boundaryRaws().clear());
        ArrayList<BigInteger> mutable = new ArrayList<>(original.boundaryRaws());
        CampaignDeadline.Configuration owned = new CampaignDeadline.Configuration(original.founding(),
                original.calendarProfile(), original.endpointDateRaw(), mutable);
        mutable.clear();
        assertEquals(original, owned);
    }

    @Test
    void changedConfigurationCannotReplaceTheActualFoundingState() {
        CampaignDeadline.Configuration previous = config("main");
        CampaignDeadline.Founding foreign = new CampaignDeadline.Founding("foreign", previous.founding().startDate(),
                previous.founding().startDateRaw(), previous.founding().months());
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadline.configure(foreign, calendar(), Optional.of(previous)));
        CampaignDeadline.Founding wrongRaw = new CampaignDeadline.Founding(previous.founding().campaignId(),
                previous.founding().startDate(), previous.founding().startDateRaw().add(BigInteger.valueOf(24)), 360);
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadline.configure(wrongRaw, calendar(), Optional.empty()));
    }

    @Test
    void exactMonthlyBoundaryUsesStrictlyLaterCalendarBoundary() {
        CampaignDeadline.Configuration config = config("main");
        BigInteger current = config.boundaryRaws().get(1);
        CampaignDeadline.Cap cap = CampaignDeadline.deadline(Optional.of(config), current,
                current.add(BigInteger.valueOf(45 * 24))).orElseThrow();
        assertEquals(config.boundaryRaws().get(2), cap.boundaryDateRaw());
        assertEquals(CampaignDeadline.Status.ADVANCE, cap.status());
    }

    @Test
    void absentConfigurationDoesNotInspectOrInventSourceFrame() {
        assertTrue(CampaignDeadline.deadline(Optional.empty(), null, null).isEmpty());
    }

    @Test
    void capPreservesIntegersBeyondLongWithoutNumberCoercion() {
        CampaignDeadline.Configuration config = config("main");
        BigInteger current = config.founding().startDateRaw();
        BigInteger huge = current.add(BigInteger.ONE.shiftLeft(100).multiply(BigInteger.valueOf(24)));
        CampaignDeadline.Cap cap = CampaignDeadline.deadline(Optional.of(config), current, huge).orElseThrow();
        assertEquals(huge, cap.requestedTargetDateRaw());
        assertEquals(cap, CampaignDeadlineCodec.decodeCap(CampaignDeadlineCodec.encodeCap(cap)));
    }

    @Test
    void numericBooleanFloatStringAndNullAreRejectedAtTheWireBoundary() {
        ObjectNode founding = (ObjectNode) GOLDEN.at("/configurations/main/founding").deepCopy();
        String original = new String(StrictJson.canonical(founding), StandardCharsets.UTF_8);
        String marker = "\"start_date_raw\":" + founding.get("start_date_raw").bigIntegerValue();
        assertTrue(original.contains(marker));
        for (String json : List.of("true", "53144328.0", "53144328e0", "\"53144328\"", "null")) {
            // Do not parse/write the negative token before the real decoder sees it.
            String malformed = original.replace(marker, "\"start_date_raw\":" + json);
            assertFalse(original.equals(malformed));
            assertTrue(malformed.contains("\"start_date_raw\":" + json));
            assertThrows(IllegalArgumentException.class,
                    () -> CampaignDeadlineCodec.decodeFounding(bytes(malformed)), json);
        }
        founding.remove("months");
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.decodeFounding(StrictJson.canonical(founding)));
        ObjectNode unknown = (ObjectNode) GOLDEN.at("/configurations/main/founding").deepCopy();
        unknown.put("attempt_alias", "not-accepted");
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.decodeFounding(StrictJson.canonical(unknown)));
    }

    @Test
    void duplicateFieldsTrailingValuesAndMissingNullSchedulesAreRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> CampaignDeadlineCodec.decodeFounding(bytes("{\"months\":1,\"months\":2}")));
        assertThrows(IllegalArgumentException.class,
                () -> CampaignDeadlineCodec.decodeFounding(bytes("{} {}")));
        ObjectNode value = (ObjectNode) GOLDEN.at("/configurations/main/configuration").deepCopy();
        value.putNull("boundary_raws");
        assertThrows(IllegalArgumentException.class,
                () -> CampaignDeadlineCodec.decodeConfiguration(StrictJson.canonical(value), calendar()));
        value.remove("boundary_raws");
        assertThrows(IllegalArgumentException.class,
                () -> CampaignDeadlineCodec.decodeConfiguration(StrictJson.canonical(value), calendar()));
    }

    @Test
    void aWellShapedStoredScheduleCannotInventAMonthBoundary() {
        ObjectNode altered = (ObjectNode) GOLDEN.at("/configurations/main/configuration").deepCopy();
        com.fasterxml.jackson.databind.node.ArrayNode boundaries =
                (com.fasterxml.jackson.databind.node.ArrayNode) altered.get("boundary_raws");
        boundaries.set(1, StrictJson.parse(bytes(boundaries.get(1).bigIntegerValue().add(BigInteger.valueOf(24)).toString())));
        assertThrows(IllegalArgumentException.class,
                () -> CampaignDeadlineCodec.decodeConfiguration(StrictJson.canonical(altered), calendar()));
    }

    @Test
    void actualDeadlineConsumerPortRejectsWrongNumericTokensWithoutCoercion() {
        byte[] configuration = CampaignDeadlineCodec.encodeConfiguration(config("main"));
        byte[] validFrame = bytes("{\"date_raw\":53144328,\"unrelated_existing_field\":null}");
        for (String invalid : List.of("true", "53144352.0", "\"53144352\"", "null")) {
            assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.deadlineFromJson(
                    Optional.of(configuration), calendar(), validFrame, bytes(invalid)), invalid);
            assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.deadlineFromJson(
                    Optional.of(configuration), calendar(), bytes("{\"date_raw\":" + invalid + "}"), bytes("53144352")), invalid);
        }
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.deadlineFromJson(
                Optional.of(configuration), calendar(), bytes("{}"), bytes("53144352")));
        assertTrue(CampaignDeadlineCodec.deadlineFromJson(Optional.empty(), calendar(), null, null).isEmpty());
        assertEquals(BigInteger.valueOf(53144352), CampaignDeadlineCodec.deadlineFromJson(
                Optional.of(configuration), calendar(), validFrame, bytes("53144352")).orElseThrow().targetDateRaw());
    }

    @Test
    void unknownOrInconsistentStatusCannotBecomeEndpointAuthority() {
        CampaignDeadline.Cap good = firstEndpointCap();
        ObjectNode value = (ObjectNode) StrictJson.parse(CampaignDeadlineCodec.encodeCap(good));
        for (String status : List.of("UNKNOWN", "advance", "endpoint_due")) {
            ObjectNode bad = value.deepCopy();
            bad.put("status", status);
            assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.decodeCap(StrictJson.canonical(bad)));
        }
        value.put("policy_choices_changed", true);
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.decodeCap(StrictJson.canonical(value)));
    }

    @Test
    void capDecoderRejectsWellTypedSubDayBoundaryAndEndpoint() {
        CampaignDeadline.Configuration config = config("main");
        BigInteger start = config.founding().startDateRaw();
        CampaignDeadline.Cap good = CampaignDeadline.deadline(Optional.of(config), start,
                start.add(BigInteger.valueOf(24))).orElseThrow();
        ObjectNode boundary = (ObjectNode) StrictJson.parse(CampaignDeadlineCodec.encodeCap(good));
        boundary.put("boundary_date_raw", start.add(BigInteger.ONE));
        boundary.put("target_date_raw", start.add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.decodeCap(bytes(boundary.toString())));
        ObjectNode endpoint = (ObjectNode) StrictJson.parse(CampaignDeadlineCodec.encodeCap(good));
        endpoint.put("endpoint_date_raw", good.endpointDateRaw().add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadlineCodec.decodeCap(bytes(endpoint.toString())));
    }

    @Test
    void endpointAlwaysProducesZeroDaysEmptyActionsAndNoCalendarOrBusinessSuccess() {
        CampaignDeadline.Cap cap = firstEndpointCap();
        CampaignDeadline.EndpointFrame frame = new CampaignDeadline.EndpointFrame(cap.startingDateRaw(), false,
                Optional.empty(), Optional.empty());
        CampaignDeadline.EndpointResult result = CampaignDeadline.endpointResult(frame, "life-advance", cap);
        JsonNode wire = StrictJson.parse(CampaignDeadlineCodec.encodeEndpointResult(result));
        assertEquals(wire.get("starting_date_raw"), wire.get("ending_date_raw"));
        assertEquals(0, wire.get("elapsed_days").intValue());
        assertEquals(0, wire.get("requested_horizon_days").intValue());
        assertTrue(wire.get("actions").isArray() && wire.get("actions").isEmpty());
        assertFalse(wire.get("calendar_progress_verified").booleanValue());
        assertFalse(wire.get("business_success_inferred").booleanValue());
        assertFalse(wire.get("paused").booleanValue());
        assertTrue(wire.get("snapshot_id").isNull());
        assertTrue(wire.get("revision").isNull());
        assertNull(wire.get("saved_day_credit"));
    }

    @Test
    void endpointRefusesAdvanceOrDifferentSourceDate() {
        CampaignDeadline.Configuration config = config("main");
        CampaignDeadline.Cap advance = CampaignDeadline.deadline(Optional.of(config), config.founding().startDateRaw(),
                config.founding().startDateRaw().add(BigInteger.valueOf(24))).orElseThrow();
        CampaignDeadline.EndpointFrame start = new CampaignDeadline.EndpointFrame(advance.startingDateRaw(), true,
                Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadline.endpointResult(start, "life-advance", advance));
        CampaignDeadline.Cap reached = firstEndpointCap();
        assertThrows(IllegalArgumentException.class, () -> CampaignDeadline.endpointResult(start, "life-advance", reached));
    }

    private static JsonNode evaluate(JsonNode entry) {
        String operation = entry.get("operation").textValue();
        if (operation.equals("no_configuration")) {
            assertTrue(CampaignDeadline.deadline(Optional.empty(), null, null).isEmpty());
            return StrictJson.parse(bytes("null"));
        }
        CampaignDeadline.Configuration config = config(entry.get("configuration_id").textValue());
        if (operation.startsWith("configure")) {
            JsonNode previousNode = entry.get("prior_configuration");
            Optional<byte[]> previous = previousNode.isNull() ? Optional.empty() : Optional.of(StrictJson.canonical(previousNode));
            return StrictJson.parse(CampaignDeadlineCodec.encodeSummary(CampaignDeadlineCodec.configureFromJson(
                    StrictJson.canonical(entry.get("founding")), calendar(), previous)));
        }
        CampaignDeadline.Cap cap = CampaignDeadlineCodec.deadlineFromJson(
                Optional.of(CampaignDeadlineCodec.encodeConfiguration(config)), calendar(),
                StrictJson.canonical(entry.get("starting")), StrictJson.canonical(entry.get("proposed_target_raw"))).orElseThrow();
        if (operation.equals("endpoint")) {
            CampaignDeadline.EndpointFrame frame = CampaignDeadlineCodec.projectEndpointFrame(StrictJson.canonical(entry.get("starting")));
            return StrictJson.parse(CampaignDeadlineCodec.encodeEndpointResult(
                    CampaignDeadline.endpointResult(frame, entry.get("result_step").textValue(), cap)));
        }
        return StrictJson.parse(CampaignDeadlineCodec.encodeCap(cap));
    }

    private static CampaignDeadline.CalendarPort calendar() {
        return (date, months) -> {
            for (JsonNode value : GOLDEN.get("configurations")) {
                JsonNode config = value.get("configuration");
                if (config.get("start_date").textValue().equals(date) && months <= config.get("months").intValue()) {
                    List<BigInteger> raws = new ArrayList<>();
                    for (JsonNode boundary : config.get("boundary_raws")) { raws.add(boundary.bigIntegerValue()); }
                    // Test-only projection of actual producer boundaries, never a second calendar implementation.
                    return new CampaignDeadline.CalendarSchedule(config.get("calendar_profile").textValue(), date,
                            config.get("start_date_raw").bigIntegerValue(), raws.subList(0, months + 1));
                }
            }
            throw new IllegalArgumentException("calendar fixture does not cover requested schedule");
        };
    }

    private static CampaignDeadline.Configuration config(String id) {
        return CampaignDeadlineCodec.decodeConfiguration(
                StrictJson.canonical(GOLDEN.at("/configurations/" + id + "/configuration")), calendar());
    }

    private static CampaignDeadline.Cap firstEndpointCap() {
        CampaignDeadline.Configuration config = config("main");
        return CampaignDeadline.deadline(Optional.of(config), config.endpointDateRaw(),
                config.endpointDateRaw().add(BigInteger.valueOf(24))).orElseThrow();
    }

    private static JsonNode loadGolden() {
        try (InputStream stream = CampaignDeadlineTest.class.getResourceAsStream("/deadlinecredit/producer-golden.json")) {
            if (stream == null) { throw new IllegalStateException("actual producer golden is missing; tests must not skip"); }
            return StrictJson.parse(stream.readAllBytes());
        } catch (IOException error) {
            throw new IllegalStateException("cannot read tracked actual producer golden", error);
        }
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
