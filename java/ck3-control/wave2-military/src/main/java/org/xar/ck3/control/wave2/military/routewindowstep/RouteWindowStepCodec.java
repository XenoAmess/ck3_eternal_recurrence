package org.xar.ck3.control.wave2.military.routewindowstep;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact JSON representation of the existing builder and tuple-returning parser. */
public final class RouteWindowStepCodec {
    private RouteWindowStepCodec() { }

    private sealed interface Input permits Build, Parse { }
    private record Build(RouteWindowStep step) implements Input { }
    private record Parse(String step) implements Input { }

    /** Full builder input validation; parsing malformed text remains a null result. */
    public static void validateRequest(byte[] raw) { decodeInput(raw); }

    private static Input decodeInput(byte[] raw) {
        JsonNode input = StrictJson.parse(raw); String operation = StrictJson.text(input.get("operation"));
        if (operation.equals("build")) {
            StrictJson.object(input, Set.of("operation", "subject_army_id", "target_province_id", "hostile_army_ids", "horizon_days"));
            int subject = (int) StrictJson.integer(input.get("subject_army_id"), 0, Integer.MAX_VALUE);
            int target = (int) StrictJson.integer(input.get("target_province_id"), 1, Integer.MAX_VALUE);
            int days = (int) StrictJson.integer(input.get("horizon_days"), 2, 3);
            JsonNode rows = input.get("hostile_army_ids"); StrictJson.require(rows != null && rows.isArray(), "hostile array required");
            List<Integer> hostiles = new ArrayList<>();
            for (JsonNode row : rows) { hostiles.add((int) StrictJson.integer(row, 0, Integer.MAX_VALUE)); }
            return new Build(new RouteWindowStep(subject, target, hostiles, days));
        } else if (operation.equals("parse")) {
            StrictJson.object(input, Set.of("operation", "step")); JsonNode node = input.get("step");
            return new Parse(node.isTextual() ? node.textValue() : null);
        } else { throw new ContractViolationException("unknown route window step operation"); }
    }

    public static byte[] execute(byte[] raw) {
        Input input = decodeInput(raw); ObjectNode output = StrictJson.object();
        if (input instanceof Build build) { output.put("step", build.step().canonical()); }
        else if (input instanceof Parse parse) {
            Optional<RouteWindowStep> parsed = RouteWindowStep.parse(parse.step());
            if (parsed.isPresent()) {
                RouteWindowStep step = parsed.orElseThrow(); var tuple = output.putArray("parsed");
                tuple.add(step.subjectArmyId()); tuple.add(step.targetProvinceId());
                var hostiles = tuple.addArray(); step.hostileArmyIds().forEach(hostiles::add); tuple.add(step.horizonDays());
            } else { output.putNull("parsed"); }
        }
        return StrictJson.canonical(output);
    }
}
