package org.xar.ck3.control.wave3.governance.educationoptions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.*;
import static org.junit.jupiter.api.Assertions.*;

class EducationOptionsTest {
    @Test void originalBothHelpersGoldenAndSerializationRoundTrip() throws Exception {
        JsonNode golden;
        try (var stream = getClass().getResourceAsStream("/educationoptions/legacy-golden-v1.json")) {
            assertNotNull(stream, "actual unchanged producer capture must be present"); golden = StrictJson.parse(stream.readAllBytes(), 196_608);
        }
        assertTrue(golden.path("cases").size() >= 25);
        int retained = 0;
        for (JsonNode sample : golden.path("cases")) {
            byte[] raw = sample.path("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            if (sample.path("name").textValue().startsWith("retained-")) {
                assertTrue(sample.path("accepted").booleanValue(), "each retained P43 default/requested context must execute both original validators successfully: " + sample.path("name").textValue());
                retained++;
            }
            if (!sample.path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode(raw), sample.path("name").textValue()); continue;
            }
            Input input = EducationOptionsCodec.decode(raw);
            assertEquals(sample.path("projection"), StrictJson.parse(EducationOptionsCodec.encodeProjection(input)));
            assertEquals(input, EducationOptionsCodec.decode(EducationOptionsCodec.encodeInput(input)));
            assertEquals(input, EducationOptionsCodec.projectParsedInput(StrictJson.parse(raw)));
        }
        assertEquals(6, retained, "all original P43 default and requested contexts");
    }
    @Test void duplicateFlagsPreserveLegacyGetterAndPerOrdinalByteMeanings() {
        Input input = decode(base()); List<Row> rows = input.rows().orElseThrow().rows();
        assertEquals(List.of(1, 0, 255), rows.stream().map(Row::bankValueU8).toList());
        assertEquals(List.of(true, true, false), rows.stream().map(Row::selected).toList());
        assertEquals(List.of(true, false, false), rows.stream().map(Row::ordinalSelected).toList());
        assertNull(rows.get(2).canonicalFlagKey()); assertEquals(4_294_967_295L, rows.get(2).flagFullU32());
        ObjectNode bad = base(); ((ObjectNode) bad.at("/context/education_option_rows/rows/1")).put("selected", false);
        assertThrows(IllegalArgumentException.class, () -> decode(bad));
    }
    @Test void requestedNullEmptyAndDuplicateKeysRemainDifferentFacts() {
        ObjectNode unspecified = base(); ObjectNode leaf = (ObjectNode) unspecified.at("/context/education_request_materialization");
        leaf.putNull("requested_option_keys"); leaf.putNull("option_keys_match");
        Input first = decode(unspecified); Input empty = decode(base());
        assertTrue(first.materialization().orElseThrow().requestedOptionKeys().isEmpty());
        assertEquals(List.of(), empty.materialization().orElseThrow().requestedOptionKeys().orElseThrow());
        ObjectNode duplicates = base(); ((ArrayNode) duplicates.at("/context/education_request_materialization/requested_option_keys")).add("x").add("x").add("y");
        assertEquals(List.of("x", "x", "y"), decode(duplicates).materialization().orElseThrow().requestedOptionKeys().orElseThrow());
        assertNotEquals(first, empty);
    }
    @Test void unavailableObservationsDoNotRequireMatchOrAvailableContext() {
        ObjectNode root = base(); ObjectNode context = (ObjectNode) root.get("context"); context.put("status", "unavailable");
        ObjectNode rows = (ObjectNode) context.get("education_option_rows"); rows.put("status", "unavailable"); rows.putArray("rows"); rows.put("unavailable_reason", "bank_unavailable");
        ObjectNode request = (ObjectNode) context.get("education_request_materialization"); request.put("status", "unavailable"); request.put("pair_matches", false);
        request.putNull("option_keys_match"); request.put("unavailable_reason", "native_materialization_unavailable");
        Input input = decode(root); assertEquals(Availability.UNAVAILABLE, input.materialization().orElseThrow().status());
        assertEquals(false, input.materialization().orElseThrow().pairMatches()); assertTrue(input.finalRoles().isEmpty());
    }
    @Test void exactRawIntegerAndBooleanTokensMissingFieldsAndBoundsAreRejected() {
        for (String token : List.of("true", "1.0", "\"1\"", "null", "-1", "4294967296")) {
            assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode(rawToken(base(), "/context/education_option_rows/rows/0", "flag_full_u32", token)), token);
        }
        for (String token : List.of("1", "1.0", "\"true\"", "null")) {
            assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode(rawToken(base(), "/context/education_option_rows/rows/0", "selected", token)), token);
        }
        for (String token : List.of("true", "10.0", "\"10\"", "0", "4294967295")) {
            assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode(rawToken(base(), "/context/education_request_materialization", "child_full_id", token)), token);
        }
        ObjectNode missing = base(); ((ObjectNode) missing.at("/context/education_option_rows/rows/0")).remove("ordinal_selected");
        assertThrows(IllegalArgumentException.class, () -> decode(missing));
        ObjectNode wrongOrdinal = base(); ((ObjectNode) wrongOrdinal.at("/context/education_option_rows/rows/1")).put("declared_ordinal", 0);
        assertThrows(IllegalArgumentException.class, () -> decode(wrongOrdinal));
        ObjectNode byteOverflow = base(); ((ObjectNode) byteOverflow.at("/context/education_option_rows/rows/2")).put("bank_value_u8", 256);
        assertThrows(IllegalArgumentException.class, () -> decode(byteOverflow));
    }
    @Test void pairRolesAndOwnedRowsAreRequiredOnlyForAvailableMaterialization() {
        for (String key : List.of("secondary_recipient_id", "secondary_actor_id")) {
            ObjectNode bad = base(); ((ObjectNode) bad.at("/context/effective_roles")).put(key, 12);
            assertThrows(IllegalArgumentException.class, () -> decode(bad));
        }
        ObjectNode halfPair = base(); ((ObjectNode) halfPair.at("/context/education_request_materialization")).putNull("guardian_full_id");
        assertThrows(IllegalArgumentException.class, () -> decode(halfPair));
        ObjectNode absentRows = base(); ((ObjectNode) absentRows.get("context")).remove("education_option_rows");
        assertThrows(IllegalArgumentException.class, () -> decode(absentRows));
        ObjectNode absentBoth = base(); ((ObjectNode) absentBoth.get("context")).remove(List.of("education_option_rows", "education_request_materialization"));
        Input absent = decode(absentBoth); assertTrue(absent.rows().isEmpty()); assertTrue(absent.materialization().isEmpty());
        ObjectNode explicitNull = absentBoth.deepCopy(); ((ObjectNode) explicitNull.get("context")).putNull("education_option_rows");
        assertThrows(IllegalArgumentException.class, () -> decode(explicitNull));
    }
    @Test void maximum4096RowsAndUnicodeReasonUseOriginalBoundsAndImmutableLists() {
        List<Row> rows = new ArrayList<>(); for (int index = 0; index < 4096; index++) { rows.add(new Row(index, 4_294_967_295L, "_".repeat(128), false, 255, false)); }
        Input input = new Input("1.20.0.4", "educate_child_interaction", Availability.AVAILABLE,
                Optional.of(new Rows(Availability.AVAILABLE, rows, null)), Optional.empty(), Optional.empty());
        byte[] encoded = EducationOptionsCodec.encodeInput(input); assertEquals(1_092_761, encoded.length);
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(encoded, 1_048_576), "shared ceiling remains unchanged");
        assertEquals(input, EducationOptionsCodec.decode(encoded)); rows.clear(); assertEquals(4096, input.rows().orElseThrow().rows().size());
        List<Row> overflow = new ArrayList<>(input.rows().orElseThrow().rows()); overflow.add(new Row(4096, 4096, "x", false, 2, false));
        assertThrows(IllegalArgumentException.class, () -> new Rows(Availability.AVAILABLE, overflow, null));
        assertDoesNotThrow(() -> new Rows(Availability.UNAVAILABLE, List.of(), "\uD83D\uDE00".repeat(512)));
        assertThrows(IllegalArgumentException.class, () -> new Rows(Availability.UNAVAILABLE, List.of(), "\uD83D\uDE00".repeat(513)));
        assertThrows(UnsupportedOperationException.class, () -> input.rows().orElseThrow().rows().clear());
        Materialization manyKeys = new Materialization(Availability.AVAILABLE, Optional.empty(), Optional.of(java.util.Collections.nCopies(20_000, "_".repeat(128))), null, true, null);
        Input large = new Input("1.20.0.4", "educate_child_interaction", Availability.AVAILABLE,
                Optional.of(new Rows(Availability.AVAILABLE, List.of(), null)), Optional.of(manyKeys), Optional.empty());
        assertEquals(20_000, large.materialization().orElseThrow().requestedOptionKeys().orElseThrow().size(), "original domain list has no invented count limit");
        assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.encodeInput(large), "finite byte transport rejects explicitly");
    }
    @Test void closedLeavesDuplicateFieldsUtf8AndByteBudgetAreStrict() {
        ObjectNode unknown = base(); ((ObjectNode) unknown.at("/context/education_option_rows")).put("extra", true);
        assertThrows(IllegalArgumentException.class, () -> decode(unknown));
        assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode(new byte[]{(byte) 0xff}));
        assertThrows(IllegalArgumentException.class, () -> EducationOptionsCodec.decode(new byte[EducationOptionsCodec.BYTE_BUDGET + 1]));
        ObjectNode counts = base(); ObjectNode context = (ObjectNode) counts.get("context"); context.put("declared_option_count", 0); context.put("selected_option_count", 0);
        assertEquals(decode(base()), decode(counts), "earlier legacy count samples must not be joined to the later native bank");
    }
    private static Input decode(JsonNode node) { return EducationOptionsCodec.decode(StrictJson.canonical(node)); }
    private static byte[] rawToken(ObjectNode input, String pointer, String key, String token) {
        String sentinel = "987654321098765432109876543210"; ObjectNode parent = (ObjectNode) input.at(pointer); parent.put(key, new BigInteger(sentinel));
        String wire = input.toString(); String site = "\"" + key + "\":" + sentinel;
        assertEquals(1, wire.split(java.util.regex.Pattern.quote(site), -1).length - 1);
        wire = wire.replace(site, "\"" + key + "\":" + token); assertFalse(wire.contains(sentinel));
        assertTrue(wire.contains("\"" + key + "\":" + token), "outgoing negative token must not normalize 1.0 into 1");
        return wire.getBytes(StandardCharsets.UTF_8);
    }
    private static ObjectNode base() {
        return (ObjectNode) StrictJson.parse(("{\"schema\":\"" + EducationOptionsCodec.INPUT_SCHEMA + "\",\"context\":{\"exact_build\":\"1.20.0.4\",\"interaction_key\":\"educate_child_interaction\",\"status\":\"available\","
                + "\"effective_roles\":{\"secondary_recipient_id\":10,\"secondary_actor_id\":11},\"education_option_rows\":{\"status\":\"available\",\"rows\":["
                + "{\"declared_ordinal\":0,\"flag_full_u32\":9,\"canonical_flag_key\":\"x\",\"selected\":true,\"bank_value_u8\":1,\"ordinal_selected\":true},"
                + "{\"declared_ordinal\":1,\"flag_full_u32\":9,\"canonical_flag_key\":\"x\",\"selected\":true,\"bank_value_u8\":0,\"ordinal_selected\":false},"
                + "{\"declared_ordinal\":2,\"flag_full_u32\":4294967295,\"canonical_flag_key\":null,\"selected\":false,\"bank_value_u8\":255,\"ordinal_selected\":false}],\"unavailable_reason\":null},"
                + "\"education_request_materialization\":{\"status\":\"available\",\"child_full_id\":10,\"guardian_full_id\":11,\"requested_option_keys\":[],\"pair_matches\":true,\"option_keys_match\":true,\"unavailable_reason\":null}}}").getBytes(StandardCharsets.UTF_8));
    }
}
