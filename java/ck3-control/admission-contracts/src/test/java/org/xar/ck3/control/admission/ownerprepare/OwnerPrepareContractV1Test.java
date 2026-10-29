package org.xar.ck3.control.admission.ownerprepare;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Producer capture is committed data: normal JUnit needs no Python or host OS. */
final class OwnerPrepareContractV1Test {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String BASE = "{\"machine_id\":\"synthetic-test-only\","
            + "\"role\":\"sdk_owner\",\"stage_args\":[],\"pythonpath\":null,"
            + "\"enable_driver_state_wal\":false}";

    @TestFactory
    Stream<DynamicTest> originalProducerGoldenParity() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.owner-prepare-producer-golden/v1", golden.path("schema").textValue());
        assertEquals("3d19624797c122960e52266a8bd5c89c6786cf3dfbdcdf0521e77228bcbb6c92",
                golden.path("producer").path("sha256").textValue());
        assertEquals(2615, golden.path("producer").path("bytes").intValue());
        assertEquals(51, golden.path("cases").size());
        return StreamSupport.stream(golden.path("cases").spliterator(), false)
                .map(sample -> DynamicTest.dynamicTest(sample.path("id").textValue(), () -> {
                    // The rejection corpus deliberately includes floating point
                    // tokens, outside the shared integer-only canonical emitter.
                    byte[] input = JSON.writeValueAsBytes(sample.path("input"));
                    if (sample.path("accepted").booleanValue()) {
                        OwnerPrepareInputsV1 value = OwnerPrepareCodecV1.decode(input);
                        byte[] encoded = OwnerPrepareCodecV1.encode(value);
                        assertEquals(sample.path("output"), StrictJson.parse(encoded));
                        assertEquals(value, OwnerPrepareCodecV1.decode(encoded));
                        assertArrayEquals(encoded, OwnerPrepareCodecV1.encode(OwnerPrepareCodecV1.decode(encoded)));
                    } else {
                        ContractViolationException error = assertThrows(ContractViolationException.class,
                                () -> OwnerPrepareCodecV1.decode(input));
                        assertEquals(sample.path("error_message").textValue(), error.getMessage());
                    }
                }));
    }

    @Test
    void exactFieldsRejectMissingUnknownAndDuplicates() {
        ObjectNode base = (ObjectNode) StrictJson.parse(bytes(BASE));
        for (String field : List.of("machine_id", "role", "stage_args", "pythonpath", "enable_driver_state_wal")) {
            ObjectNode missing = base.deepCopy();
            missing.remove(field);
            assertThrows(ContractViolationException.class,
                    () -> OwnerPrepareCodecV1.decode(StrictJson.canonical(missing)), field);
        }
        ObjectNode renamed = base.deepCopy();
        renamed.set("stage_arguments", renamed.remove("stage_args"));
        assertThrows(ContractViolationException.class,
                () -> OwnerPrepareCodecV1.decode(StrictJson.canonical(renamed)));
        ObjectNode unknown = base.deepCopy();
        unknown.put("registered", false);
        assertThrows(ContractViolationException.class,
                () -> OwnerPrepareCodecV1.decode(StrictJson.canonical(unknown)));
        assertThrows(ContractViolationException.class,
                () -> OwnerPrepareCodecV1.decode(bytes(BASE.replace("\"machine_id\":",
                        "\"machine_id\":\"first\",\"machine_id\":"))));
        assertThrows(ContractViolationException.class,
                () -> OwnerPrepareCodecV1.decode(bytes(BASE + " null")));
    }

    @Test
    void nullableAndEmptyValuesHaveDistinctMeaning() {
        OwnerPrepareInputsV1 nullPath = OwnerPrepareCodecV1.decode(bytes(BASE));
        OwnerPrepareInputsV1 emptyPath = OwnerPrepareCodecV1.decode(bytes(BASE.replace(
                "\"pythonpath\":null", "\"pythonpath\":\"\"")));
        assertEquals(null, nullPath.pythonpath());
        assertEquals("", emptyPath.pythonpath());
        assertNotEquals(nullPath, emptyPath);
        assertEquals(List.of(), nullPath.stageArgs());
        assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.decode(bytes(
                BASE.replace("\"stage_args\":[]", "\"stage_args\":null"))));
        assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.decode(bytes(
                BASE.replace("\"enable_driver_state_wal\":false", "\"enable_driver_state_wal\":null"))));
        for (String wrongBoolean : List.of("0", "1", "1.0", "\"false\"")) {
            assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.decode(bytes(
                    BASE.replace("\"enable_driver_state_wal\":false",
                            "\"enable_driver_state_wal\":" + wrongBoolean))));
        }
        for (String wrongArgument : List.of("1", "1.0", "true", "null")) {
            assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.decode(bytes(
                    BASE.replace("\"stage_args\":[]", "\"stage_args\":[" + wrongArgument + "]"))));
        }
    }

    @Test
    void immutableModelPreservesBoundariesAndRejectsInvalidDirectConstruction() {
        List<String> mutable = new ArrayList<>(List.of("", "value with spaces", "--qualify"));
        OwnerPrepareInputsV1 value = new OwnerPrepareInputsV1(" machine ", OwnerRoleV1.SDK_OWNER,
                mutable, "", true);
        mutable.set(1, "mutated");
        assertEquals(List.of("", "value with spaces", "--qualify"), value.stageArgs());
        assertEquals(" machine ", value.machineId());
        assertThrows(UnsupportedOperationException.class, () -> value.stageArgs().add("new"));
        assertThrows(ContractViolationException.class,
                () -> new OwnerPrepareInputsV1("node", null, List.of(), null, false));
        assertThrows(ContractViolationException.class,
                () -> new OwnerPrepareInputsV1("node", OwnerRoleV1.SDK_OWNER,
                        Arrays.asList("valid", null), null, false));
        for (OwnerRoleV1 role : OwnerRoleV1.values()) {
            if (role != OwnerRoleV1.SDK_OWNER) {
                assertThrows(ContractViolationException.class,
                        () -> new OwnerPrepareInputsV1("node", role, List.of(), null, true));
            }
        }
    }

    @Test
    void exactPythonBlanknessAndArgumentLimitArePreserved() {
        int[] whitespace = {0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x1c, 0x1d, 0x1e, 0x1f, 0x20,
                0x85, 0xa0, 0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006,
                0x2007, 0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000};
        for (int codePoint : whitespace) {
            String blank = new String(Character.toChars(codePoint));
            assertThrows(ContractViolationException.class,
                    () -> new OwnerPrepareInputsV1(blank, OwnerRoleV1.SDK_OWNER, List.of(), null, false));
        }
        for (String nonBlank : List.of("\u180e", "\u200b", "\ufeff")) {
            assertEquals(nonBlank, new OwnerPrepareInputsV1(nonBlank, OwnerRoleV1.SDK_OWNER,
                    List.of(), null, false).machineId());
        }
        List<String> maximum = new ArrayList<>();
        for (int index = 0; index < 128; index++) {
            maximum.add("");
        }
        OwnerPrepareInputsV1 accepted = new OwnerPrepareInputsV1("node", OwnerRoleV1.SDK_OWNER,
                maximum, null, false);
        assertEquals(128, accepted.stageArgs().size());
        maximum.add("");
        assertThrows(ContractViolationException.class,
                () -> new OwnerPrepareInputsV1("node", OwnerRoleV1.SDK_OWNER, maximum, null, false));
    }

    @Test
    void wireBudgetDoesNotInventAnIndividualStringLimit() {
        OwnerPrepareInputsV1 largeText = new OwnerPrepareInputsV1("n".repeat(40_000),
                OwnerRoleV1.SDK_OWNER, List.of(""), null, false);
        byte[] raw = OwnerPrepareCodecV1.encode(largeText);
        assertTrue(raw.length < OwnerPrepareCodecV1.MAX_WIRE_BYTES);
        assertEquals(largeText, OwnerPrepareCodecV1.decode(raw));
        OwnerPrepareInputsV1 tooLarge = new OwnerPrepareInputsV1("n".repeat(65_536),
                OwnerRoleV1.SDK_OWNER, List.of(), null, false);
        assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.encode(tooLarge));
        assertThrows(ContractViolationException.class,
                () -> OwnerPrepareCodecV1.decode(new byte[OwnerPrepareCodecV1.MAX_WIRE_BYTES + 1]));
        assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.decode(new byte[0]));
        assertThrows(ContractViolationException.class,
                () -> OwnerPrepareCodecV1.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(ContractViolationException.class, () -> OwnerPrepareCodecV1.decode(bytes(
                BASE.replace("synthetic-test-only", "\\ud800"))));
    }

    private static byte[] bytes(String value) {
        return value.getBytes(StandardCharsets.UTF_8);
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = OwnerPrepareContractV1Test.class.getResourceAsStream(
                "/ownerprepare/producer-golden-v1.json")) {
            if (stream == null) {
                throw new IOException("required original producer golden was not packaged");
            }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
}
