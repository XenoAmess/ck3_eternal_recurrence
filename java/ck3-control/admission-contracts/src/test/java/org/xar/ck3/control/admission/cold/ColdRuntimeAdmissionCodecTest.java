package org.xar.ck3.control.admission.cold;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ColdRuntimeAdmissionCodecTest {
    private static ObjectNode golden() throws IOException {
        try (InputStream stream = ColdRuntimeAdmissionCodecTest.class.getResourceAsStream("/cold/preflight-golden.json")) {
            if (stream == null) { throw new IOException("original producer golden required, never skipped"); }
            return (ObjectNode) StrictJson.parse(stream.readAllBytes(), CurrentSavedPreflightCodec.RECEIPT_MAX_BYTES);
        }
    }

    private static ObjectNode fixture() throws IOException {
        return (ObjectNode) golden().get("a17").get("wire").deepCopy();
    }

    private static ColdRuntimeAdmissionCore parse(JsonNode value) {
        return ColdRuntimeAdmissionCodec.parse(value, "portable-admission-fixture", PathFlavor.WINDOWS);
    }

    @Test void existingProducerGoldenKeepsDetachedProjectionAndExactCanonicalBytes() throws IOException {
        ObjectNode a17 = (ObjectNode) golden().get("a17");
        ObjectNode wire = fixture(), before = wire.deepCopy();
        ColdRuntimeAdmissionCore core = parse(wire);
        // JSON integers have one value domain; Jackson BigIntegerNode/IntNode classes are not ABI.
        assertArrayEquals(StrictJson.canonical(a17.get("core")),
                StrictJson.canonical(ColdRuntimeAdmissionCodec.toJson(core)));
        assertEquals(before, wire); assertFalse(ColdRuntimeAdmissionCodec.toJson(core).has("qualification"));
        byte[] encoded = ColdRuntimeAdmissionCodec.encode(core);
        assertArrayEquals(a17.get("canonical_core_json").textValue().getBytes(StandardCharsets.UTF_8), encoded);
        assertEquals(core, ColdRuntimeAdmissionCodec.parse(encoded, core.machineId(), PathFlavor.WINDOWS));
        assertFalse(core.grantsRuntimeExecution()); assertFalse(core.grantsWarmOrRecoveryQualification());
        ((ObjectNode) wire.get("capacity")).put("D_free_floor_bytes", 1);
        assertNotEquals(1, core.capacity().dFreeFloorBytes());
    }

    @Test void requiredCoreFieldsRejectMissingNullAndLegacyAliases() throws IOException {
        ObjectNode original = fixture();
        List<String> fields = new ArrayList<>(); original.fieldNames().forEachRemaining(fields::add);
        fields.remove("qualification");
        for (String field : fields) {
            ObjectNode missing = original.deepCopy(); missing.remove(field);
            assertThrows(ContractViolationException.class, () -> parse(missing), field);
            ObjectNode nullable = original.deepCopy(); nullable.putNull(field);
            assertThrows(ContractViolationException.class, () -> parse(nullable), field);
        }
        ObjectNode legacy = original.deepCopy(); legacy.put("hard_bytes", 1);
        assertThrows(ContractViolationException.class, () -> parse(legacy));
        for (String field : List.of("D_conservative_floor_bytes", "Z_conservative_floor_bytes")) {
            ObjectNode wire = original.deepCopy(); ((ObjectNode) wire.get("capacity")).putNull(field);
            assertThrows(ContractViolationException.class, () -> parse(wire));
        }
    }

    @Test void hardLimitFloorsAndFlagsUseExactJsonTokenTypes() throws IOException {
        for (String field : List.of("runtime_hard_bytes", "D_free_floor_bytes", "Z_free_floor_bytes")) {
            for (String value : List.of("true", "1.0", "\"1\"", "null", "0", "-1", "9007199254740992")) {
                ObjectNode wire = fixture();
                ObjectNode target = field.equals("runtime_hard_bytes") ? wire : (ObjectNode) wire.get("capacity");
                target.set(field, StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
                assertThrows(ContractViolationException.class, () -> parse(wire), field + "=" + value);
            }
        }
        for (String field : List.of("root_direct_execution_release", "canonical_capacity_review_passed")) {
            for (String value : List.of("false", "null", "0", "1", "1.0", "\"true\"")) {
                ObjectNode wire = fixture(); wire.set(field, StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
                assertThrows(ContractViolationException.class, () -> parse(wire));
            }
        }
        ObjectNode max = fixture(); max.put("runtime_hard_bytes", StrictJson.MAX_SAFE_INTEGER);
        assertEquals(StrictJson.MAX_SAFE_INTEGER, parse(max).runtimeHardBytes());
    }

    @Test void exactReferencesRejectWrongShapeSourceDigestAndZeroBytes() throws IOException {
        for (String name : List.of("plan", "quote", "full_storage_ref")) {
            for (String field : List.of("path", "bytes", "sha256")) {
                ObjectNode wire = fixture(); ((ObjectNode) wire.get(name)).remove(field);
                assertThrows(ContractViolationException.class, () -> parse(wire));
            }
            for (String value : List.of("true", "1.0", "\"1\"", "null", "0")) {
                ObjectNode wire = fixture(); ((ObjectNode) wire.get(name)).set("bytes", StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
                assertThrows(ContractViolationException.class, () -> parse(wire));
            }
            ObjectNode wire = fixture(); ((ObjectNode) wire.get(name)).put("old_digest", "a".repeat(64));
            assertThrows(ContractViolationException.class, () -> parse(wire));
            ObjectNode digest = fixture(); ((ObjectNode) digest.get(name)).put("sha256", "A".repeat(64));
            assertThrows(ContractViolationException.class, () -> parse(digest));
            ObjectNode relative = fixture(); ((ObjectNode) relative.get(name)).put("path", "D:relative");
            assertThrows(ContractViolationException.class, () -> parse(relative));
            ObjectNode nul = fixture(); ((ObjectNode) nul.get(name)).put("path", "D:/a\0b");
            assertThrows(ContractViolationException.class, () -> parse(nul));
        }
    }

    @Test void extrasRemainMetadataButMustBeOrdinaryFiniteJson() throws IOException {
        ObjectNode wire = fixture();
        wire.putNull("extra_null"); wire.putArray("extra_empty"); wire.put("finite_float", 1.25);
        ((ObjectNode) wire.get("capacity")).putArray("future_metadata");
        assertEquals(parse(fixture()), parse(wire));
        wire.put("nonfinite", Double.NaN);
        assertThrows(ContractViolationException.class, () -> parse(wire));
        ObjectNode cycle = fixture(); cycle.set("cycle", cycle);
        assertThrows(ContractViolationException.class, () -> parse(cycle));
        String text = new String(ColdRuntimeAdmissionCodec.encode(parse(fixture())), StandardCharsets.UTF_8);
        String overflow = text.substring(0, text.length() - 1) + ",\"metadata\":1e400}";
        assertThrows(ContractViolationException.class, () -> ColdRuntimeAdmissionCodec.parse(overflow.getBytes(StandardCharsets.UTF_8),
                "portable-admission-fixture", PathFlavor.WINDOWS));
    }

    @Test void schemaMachineAndAuthorityRemainExactAndPlatformDoesNotBroadenAbsolutePaths() throws IOException {
        for (String field : List.of("schema", "machine_id", "owner", "status")) {
            ObjectNode wire = fixture(); wire.put(field, wire.get(field).textValue().toLowerCase() + "x");
            assertThrows(ContractViolationException.class, () -> parse(wire));
        }
        assertThrows(ContractViolationException.class, () -> ColdRuntimeAdmissionCodec.parse(fixture(), "", PathFlavor.WINDOWS));
        assertTrue(PathFlavor.WINDOWS.isAbsolute("D:/data/file"));
        assertTrue(PathFlavor.WINDOWS.isAbsolute("\\\\server\\share\\file"));
        assertTrue(PathFlavor.WINDOWS.isAbsolute("\\\\?\\UNC\\server\\share\\file"));
        assertFalse(PathFlavor.WINDOWS.isAbsolute("\\file"));
        assertFalse(PathFlavor.WINDOWS.isAbsolute("/data/file"));
        assertFalse(PathFlavor.WINDOWS.isAbsolute("D:file"));
        assertTrue(PathFlavor.POSIX.isAbsolute("/data/file"));
    }
}
