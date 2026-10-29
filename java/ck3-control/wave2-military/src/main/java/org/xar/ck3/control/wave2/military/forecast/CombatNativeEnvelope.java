package org.xar.ck3.control.wave2.military.forecast;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.Set;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.require;

/** Exact raw Native outer shape. Consumers retain step, status, sequence and payload validation. */
public final class CombatNativeEnvelope {
    public enum Payload {
        COMBAT_INPUTS("combat_simulation_inputs"), PHASE_TRACE("combat_phase_event_trace");
        private final Set<String> fields;
        Payload(String field) { fields = Set.of("step", "accepted", "status", "query_sequence", field); }
    }
    private CombatNativeEnvelope() { }

    /** Does not change the original result or grant any source/frame authority. */
    public static void validate(ObjectNode result, Payload payload) {
        require(result != null && payload != null, "combat native result and payload kind required");
        Set<String> fields = new HashSet<>(); result.fieldNames().forEachRemaining(fields::add);
        if (fields.remove("backend_id")) {
            JsonNode backend = result.get("backend_id");
            require(backend != null && backend.isTextual() && !backend.textValue().isBlank(), "backend_id must be nonblank text when present");
        }
        require(fields.equals(payload.fields), "combat native receipt has missing or extra fields");
    }
}
