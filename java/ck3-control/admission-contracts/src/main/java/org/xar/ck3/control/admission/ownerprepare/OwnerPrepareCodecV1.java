package org.xar.ck3.control.admission.ownerprepare;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.io.IOException;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict v1 JSON adapter for the existing five-field pure input contract. */
public final class OwnerPrepareCodecV1 {
    public static final int MAX_WIRE_BYTES = StrictJson.INPUT_MAX_BYTES;
    private static final ObjectMapper WRITER = new ObjectMapper();

    private static final Set<String> FIELDS = Set.of(
            "machine_id", "role", "stage_args", "pythonpath", "enable_driver_state_wal");

    private OwnerPrepareCodecV1() { }

    public static OwnerPrepareInputsV1 decode(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), FIELDS);
        String machineId = string(input.get("machine_id"), "owner machine_id must be a nonempty string");
        OwnerRoleV1 role = OwnerRoleV1.fromWire(string(input.get("role"),
                "exact admitted production role required"));
        JsonNode arguments = input.get("stage_args");
        StrictJson.require(arguments.isArray() && arguments.size() <= OwnerPrepareInputsV1.MAX_STAGE_ARGUMENTS,
                "owner stage_args must be a bounded list or tuple of strings");
        List<String> stageArgs = new ArrayList<>(arguments.size());
        for (JsonNode argument : arguments) {
            stageArgs.add(string(argument, "owner stage_args must contain only strings without NUL"));
        }
        JsonNode path = input.get("pythonpath");
        String pythonpath = path.isNull() ? null
                : string(path, "owner pythonpath must be a string or None");
        JsonNode wal = input.get("enable_driver_state_wal");
        StrictJson.require(wal.isBoolean(), "WAL opt-in requires a boolean and the sdk_owner role");
        return new OwnerPrepareInputsV1(machineId, role, stageArgs, pythonpath, wal.booleanValue());
    }

    public static byte[] encode(OwnerPrepareInputsV1 input) {
        StrictJson.require(input != null, "validated owner preparation inputs required");
        ObjectNode output = StrictJson.object();
        // Fixed lexical field order matches Python's compact sorted-key JSON.
        output.put("enable_driver_state_wal", input.enableDriverStateWal());
        output.put("machine_id", input.machineId());
        if (input.pythonpath() == null) {
            output.putNull("pythonpath");
        } else {
            output.put("pythonpath", input.pythonpath());
        }
        output.put("role", input.role().wireValue());
        ArrayNode arguments = output.putArray("stage_args");
        input.stageArgs().forEach(arguments::add);
        try {
            byte[] raw = WRITER.writeValueAsBytes(output);
            StrictJson.require(raw.length <= MAX_WIRE_BYTES, "owner preparation JSON exceeds wire budget");
            return raw;
        } catch (IOException error) {
            throw new ContractViolationException("owner preparation JSON encoding failed", error);
        }
    }

    private static String string(JsonNode value, String error) {
        StrictJson.require(value != null && value.isTextual(), error);
        return value.textValue();
    }
}
