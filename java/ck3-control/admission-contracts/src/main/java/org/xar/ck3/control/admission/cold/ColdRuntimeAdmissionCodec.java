package org.xar.ck3.control.admission.cold;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Iterator;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.admission.cold.ColdRuntimeAdmissionCore.Capacity;

/** Strict v1 projection boundary. It reads no source files or current capacity. */
public final class ColdRuntimeAdmissionCodec {
    private ColdRuntimeAdmissionCodec() { }

    public static ColdRuntimeAdmissionCore parse(byte[] raw, String expectedMachineId, PathFlavor flavor) {
        return parse(StrictJson.parse(raw), expectedMachineId, flavor);
    }

    public static ColdRuntimeAdmissionCore parse(JsonNode value, String expectedMachineId, PathFlavor flavor) {
        StrictJson.require(expectedMachineId != null && !expectedMachineId.isEmpty(),
                "expected_machine_id must be nonempty text");
        ObjectNode row = finiteObject(value, "runtime admission");
        equalText(row.get("schema"), ColdRuntimeAdmissionCore.Schema.SOURCE29_A17.wire(),
                "current runtime admission schema required");
        equalText(row.get("machine_id"), expectedMachineId, "runtime admission machine differs");
        equalText(row.get("owner"), "Root", "runtime admission requires Root and ADMITTED");
        equalText(row.get("status"), "ADMITTED", "runtime admission requires Root and ADMITTED");
        StrictJson.trueValue(row.get("root_direct_execution_release"));
        StrictJson.trueValue(row.get("canonical_capacity_review_passed"));
        StrictJson.require(!row.has("hard_bytes"), "legacy hard_bytes is not a runtime_hard_bytes alias");
        ObjectNode capacity = finiteObject(row.get("capacity"), "capacity");
        StrictJson.require(!capacity.has("D_conservative_floor_bytes")
                        && !capacity.has("Z_conservative_floor_bytes"),
                "legacy capacity floor fields are not aliases");
        return new ColdRuntimeAdmissionCore(expectedMachineId,
                source(row.get("plan"), "plan", flavor),
                source(row.get("quote"), "quote", flavor),
                source(row.get("full_storage_ref"), "full_storage_ref", flavor),
                positive(row.get("runtime_hard_bytes")),
                new Capacity(positive(capacity.get("D_free_floor_bytes")),
                        positive(capacity.get("Z_free_floor_bytes"))), flavor);
    }

    /** Emits the detached core, deliberately excluding outer metadata. */
    public static byte[] encode(ColdRuntimeAdmissionCore core) {
        return StrictJson.canonical(toJson(core));
    }

    public static ObjectNode toJson(ColdRuntimeAdmissionCore core) {
        StrictJson.require(core != null, "validated runtime admission core required");
        ObjectNode row = StrictJson.object();
        row.put("schema", core.schema().wire());
        row.put("machine_id", core.machineId());
        row.put("owner", core.owner().name());
        row.put("status", core.status().name());
        row.put("root_direct_execution_release", true);
        row.set("plan", core.plan().toJson());
        row.set("quote", core.quote().toJson());
        row.set("full_storage_ref", core.fullStorageRef().toJson());
        row.put("canonical_capacity_review_passed", true);
        row.put("runtime_hard_bytes", core.runtimeHardBytes());
        ObjectNode capacity = StrictJson.object();
        capacity.put("D_free_floor_bytes", core.capacity().dFreeFloorBytes());
        capacity.put("Z_free_floor_bytes", core.capacity().zFreeFloorBytes());
        row.set("capacity", capacity);
        return row;
    }

    private static ExactRef source(JsonNode value, String field, PathFlavor flavor) {
        ExactRef reference = ExactRef.fromJson(value);
        ColdRuntimeAdmissionCore.reference(reference, field, flavor);
        return reference;
    }

    private static long positive(JsonNode value) {
        return StrictJson.integer(value, 1, StrictJson.MAX_SAFE_INTEGER);
    }

    private static void equalText(JsonNode value, String expected, String message) {
        StrictJson.require(value != null && value.isTextual() && value.textValue().equals(expected), message);
    }

    private static ObjectNode finiteObject(JsonNode value, String field) {
        StrictJson.require(value instanceof ObjectNode, field + " must be an ordinary finite JSON object");
        finiteJson(value, Collections.newSetFromMap(new IdentityHashMap<>()));
        return (ObjectNode) value;
    }

    /** Unknown metadata remains valid JSON; no arbitrary Java POJO, NaN or Infinity nodes. */
    private static void finiteJson(JsonNode value, Set<JsonNode> active) {
        StrictJson.require(value != null, "missing JSON value");
        if (value.isContainerNode()) {
            StrictJson.require(active.add(value), "cyclic input is not JSON");
            try {
                Iterator<JsonNode> elements = value.elements();
                while (elements.hasNext()) { finiteJson(elements.next(), active); }
            } finally { active.remove(value); }
        } else if (value.isFloatingPointNumber()) {
            StrictJson.require(Double.isFinite(value.doubleValue()), "finite JSON number required");
        } else {
            StrictJson.require(value.isNull() || value.isBoolean() || value.isIntegralNumber() || value.isTextual(),
                    "ordinary JSON value required");
        }
    }
}
