package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Restart DATA codecs only: these documents grant no writer, action or restore admission. */
class RestartStateCodecTest {
    private static final String MACHINE = "codec-test-machine";
    private static final BigInteger ABOVE_JS_SAFE = new BigInteger("9007199254740993");

    @Test void manifestReferenceRoutesEncodedControllerToItsActualDecoder() {
        for (BigInteger revision : List.of(BigInteger.ZERO, ABOVE_JS_SAFE, StrictJson.UINT64_MAX)) {
            Fixture fixture = fixture(revision, true, false);
            CleanBatchRestart manifest = CleanBatchRestart.decode(fixture.manifest().encode());
            byte[] controllerBytes = fixture.originals().get(manifest.controller());
            assertNotNull(controllerBytes);
            assertEquals(manifest.controller(), reference("memory/controller.json", controllerBytes));
            ControllerRestartState restored = ControllerRestartState.decode(controllerBytes);
            assertEquals(fixture.manifest(), manifest);
            assertEquals(fixture.controller(), restored);
            assertTrue(restored.dirty());
            assertTrue(restored.quarantined());
            assertTrue(restored.localUnresolved());
            assertTrue(restored.stopRequested());
            assertEquals(Optional.of(reference("memory/head.json", bytes("head DATA"))), restored.ledgerHead());
        }
    }

    @Test void unsignedRevisionsStayCanonicalDecimalStringsAcrossPersistence() {
        Fixture fixture = fixture(StrictJson.UINT64_MAX, false, false);
        ObjectNode encoded = manifestJson(fixture);
        for (String field : List.of("public_revision", "native_revision")) {
            assertTrue(encoded.get(field).isTextual());
            assertEquals(StrictJson.UINT64_MAX.toString(), encoded.get(field).textValue());
        }
        JsonNode generation = encoded.get("previous_transport").get("connection_generation");
        assertTrue(generation.isTextual());
        assertEquals(ABOVE_JS_SAFE.toString(), generation.textValue());
        assertEquals(fixture.manifest(), CleanBatchRestart.decode(wire(encoded)));
    }

    @Test void revisionsRejectNumbersBooleansNullAndNoncanonicalText() {
        Fixture fixture = fixture(BigInteger.ONE, false, false);
        for (String field : List.of("public_revision", "native_revision", "connection_generation")) {
            for (String invalid : List.of("1", "1.0", "true", "null", "\"\"", "\"01\"", "\"+1\"",
                    "\" 1\"", "\"1e0\"", "\"-1\"", "\"18446744073709551616\"")) {
                ObjectNode document = manifestJson(fixture);
                ObjectNode owner = field.equals("connection_generation")
                        ? (ObjectNode) document.get("previous_transport") : document;
                owner.set(field, value(invalid));
                assertThrows(ContractViolationException.class, () -> CleanBatchRestart.decode(wire(document)), field + "=" + invalid);
            }
        }
    }

    @Test void controllerCountersRejectBooleanAndFloatingPointEquality() {
        Fixture fixture = fixture(BigInteger.ONE, false, false);
        for (String field : List.of("next_batch_sequence", "eligible_since_save", "total_committed_days")) {
            for (String invalid : List.of("true", "1.0", "\"1\"", "null", "-1", "9007199254740992")) {
                ObjectNode document = controllerJson(fixture);
                document.set(field, value(invalid));
                assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(document)), field + "=" + invalid);
            }
        }
        ObjectNode boundary = controllerJson(fixture);
        boundary.put("next_batch_sequence", StrictJson.MAX_SAFE_INTEGER);
        boundary.put("total_committed_days", StrictJson.MAX_SAFE_INTEGER);
        boundary.put("eligible_since_save", Integer.MAX_VALUE);
        ControllerRestartState restored = ControllerRestartState.decode(wire(boundary));
        assertEquals(StrictJson.MAX_SAFE_INTEGER, restored.nextBatchSequence());
        assertEquals(StrictJson.MAX_SAFE_INTEGER, restored.totalCommittedDays());
        assertEquals(Integer.MAX_VALUE, restored.eligibleSinceSave());
    }

    @Test void manifestNumericFieldsAndReferenceSizesRejectBooleanAndFloat() {
        Fixture fixture = fixture(BigInteger.ONE, true, false);
        for (String field : List.of("observation_version", "date_raw")) {
            for (String invalid : List.of("true", "3.0", "\"3\"", "null")) {
                ObjectNode document = manifestJson(fixture);
                document.set(field, value(invalid));
                assertThrows(ContractViolationException.class, () -> CleanBatchRestart.decode(wire(document)), field + "=" + invalid);
            }
        }
        for (String field : List.of("controller", "driver_facts", "full_driver")) {
            for (String invalid : List.of("true", "1.0")) {
                ObjectNode document = manifestJson(fixture);
                ((ObjectNode) document.get(field)).set("bytes", value(invalid));
                assertThrows(ContractViolationException.class, () -> CleanBatchRestart.decode(wire(document)), field + ".bytes=" + invalid);
            }
        }
        ObjectNode controller = controllerJson(fixture);
        ((ObjectNode) controller.get("ledger_head")).put("bytes", true);
        assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(controller)));
        ((ObjectNode) controller.get("ledger_head")).put("bytes", 1.0);
        assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(controller)));
    }

    @Test void optionalValuesRequireExplicitNullAndRejectMissingOrEmptyContainers() {
        Fixture fixture = fixture(BigInteger.ONE, false, false);
        ObjectNode encoded = controllerJson(fixture);
        assertTrue(encoded.get("saved_pair").isNull());
        assertTrue(encoded.get("ledger_head").isNull());
        ControllerRestartState restored = ControllerRestartState.decode(wire(encoded));
        assertTrue(restored.savedPair().isEmpty());
        assertTrue(restored.ledgerHead().isEmpty());
        for (String field : List.of("saved_pair", "ledger_head")) {
            ObjectNode missing = controllerJson(fixture);
            missing.remove(field);
            assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(missing)), field + " missing");
            for (String invalid : List.of("{}", "[]")) {
                ObjectNode document = controllerJson(fixture);
                document.set(field, value(invalid));
                assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(document)), field + "=" + invalid);
            }
        }
    }

    @Test void emptySetsSurviveButMissingNullDuplicatesAndWrongEntryTypesFail() {
        Fixture empty = fixture(BigInteger.ONE, false, true);
        assertEquals(empty.controller(), ControllerRestartState.decode(empty.controller().encode()));
        for (String field : List.of("used_batches", "unsaved_gameplay_actions", "completed_analysis_ids")) {
            ObjectNode missing = controllerJson(empty);
            missing.remove(field);
            assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(missing)), field + " missing");
            for (String invalid : List.of("null", "{}", "[\"same\",\"same\"]", "[true]", "[1]", "[1.0]", "[\"\"]")) {
                ObjectNode document = controllerJson(empty);
                document.set(field, value(invalid));
                assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(document)), field + "=" + invalid);
            }
        }
    }

    @Test void controllerFlagsRequireActualJsonBooleans() {
        Fixture fixture = fixture(BigInteger.ONE, false, false);
        for (String field : List.of("dirty", "quarantined", "local_unresolved", "stop_requested")) {
            for (String invalid : List.of("1", "1.0", "\"true\"", "null")) {
                ObjectNode document = controllerJson(fixture);
                document.set(field, value(invalid));
                assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(document)), field + "=" + invalid);
            }
        }
    }

    @Test void bothDurableDocumentsRequireTheirExactFieldContracts() {
        Fixture fixture = fixture(BigInteger.ONE, false, false);
        ObjectNode controller = controllerJson(fixture);
        for (String field : fieldNames(controller)) {
            ObjectNode missing = controller.deepCopy();
            missing.remove(field);
            assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(missing)), field + " missing");
        }
        controller.put("extra", true);
        assertThrows(ContractViolationException.class, () -> ControllerRestartState.decode(wire(controller)));
        ObjectNode manifest = manifestJson(fixture);
        for (String field : fieldNames(manifest)) {
            ObjectNode missing = manifest.deepCopy();
            missing.remove(field);
            assertThrows(ContractViolationException.class, () -> CleanBatchRestart.decode(wire(missing)), field + " missing");
        }
        manifest.put("extra", true);
        assertThrows(ContractViolationException.class, () -> CleanBatchRestart.decode(wire(manifest)));
    }

    private static Fixture fixture(BigInteger revision, boolean hasHead, boolean emptySets) {
        GameGeneration game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var owner = new SessionPorts.SessionIdentity(MACHINE, game, "codec-session");
        var head = reference("memory/head.json", bytes("head DATA"));
        var controller = new ControllerRestartState(owner, "batch", 1,
                emptySets ? Set.of() : Set.of("batch-2", "batch-1"), emptySets ? Set.of() : Set.of("unknown-action"),
                Optional.empty(), hasHead ? Optional.of(head) : Optional.empty(), 1, true, true, true, 1,
                emptySets ? Set.of() : Set.of("analysis-1"), true);
        byte[] controllerBytes = controller.encode();
        ExactRef controllerRef = reference("memory/controller.json", controllerBytes);
        byte[] facts = bytes("driver facts DATA");
        byte[] full = bytes("full driver DATA");
        var source = new G2Source(MACHINE, "2026-10-29T00:00:00Z", "codec-build",
                reference("memory/source.json", bytes("caller DATA")));
        var manifest = new CleanBatchRestart(controllerRef, reference("memory/facts.json", facts),
                reference("memory/full.json", full), new TransportSession(MACHINE, game, ABOVE_JS_SAFE, "codec-session"),
                revision, revision, 4, 1, source);
        return new Fixture(controller, manifest, Map.of(controllerRef, controllerBytes));
    }

    private record Fixture(ControllerRestartState controller, CleanBatchRestart manifest, Map<ExactRef, byte[]> originals) { }

    private static ObjectNode controllerJson(Fixture fixture) {
        return ContinuityJson.parseObject(fixture.controller().encode(), ContinuityJson.DOCUMENT_MAX_BYTES);
    }

    private static ObjectNode manifestJson(Fixture fixture) {
        return ContinuityJson.parseObject(fixture.manifest().encode(), ContinuityJson.DOCUMENT_MAX_BYTES);
    }

    private static List<String> fieldNames(ObjectNode document) {
        var names = new java.util.ArrayList<String>();
        document.fieldNames().forEachRemaining(names::add);
        return List.copyOf(names);
    }

    private static JsonNode value(String json) {
        // Keep the deliberately floating token when serializing the malformed input.
        // The strict parser's DecimalNode may normalize 1.0 to an integer spelling.
        if (json.equals("1.0") || json.equals("3.0")) {
            return com.fasterxml.jackson.databind.node.DoubleNode.valueOf(Double.parseDouble(json));
        }
        return StrictJson.parse(bytes(json), 1024);
    }

    private static byte[] wire(ObjectNode document) {
        return bytes(document.toString());
    }

    private static byte[] bytes(String value) {
        return value.getBytes(StandardCharsets.UTF_8);
    }

    private static ExactRef reference(String path, byte[] body) {
        try {
            return new ExactRef(path, body.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
        } catch (NoSuchAlgorithmException unavailable) {
            throw new AssertionError(unavailable);
        }
    }
}
