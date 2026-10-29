package org.xar.ck3.control.vanilla.schemesway;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.*;

/** Raw-token HTTP boundary for the actual Java ordinary staging consumer. No disk/native reads. */
public final class OrdinarySwayServiceWire {
    public static final String REQUEST_SCHEMA = "xar.java-ordinary-sway-stage-request/v1";
    public static final String RESPONSE_SCHEMA = "xar.java-ordinary-sway-stage-response/v1";
    private OrdinarySwayServiceWire() { }

    public static byte[] stage(byte[] input) {
        ObjectNode row = StrictJson.object(StrictJson.parse(input), Set.of("schema", "wrapper_snapshot_id",
                "wrapper_revision", "formal_query_enabled", "formal_action_enabled", "lifecycle_reader_enabled", "request"));
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(row.get("schema"))), "unsupported stage schema");
        var request = SwayScheduleWire.decode(StrictJson.canonical(row.get("request")));
        Wrapper wrapper = new Wrapper(StrictJson.text(row.get("wrapper_snapshot_id")),
                StrictJson.integer(row.get("wrapper_revision"), BigInteger.ONE, BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)));
        Captured captured = new Captured(request.source(), wrapper, request.selectedStep(), request.frame(), request.root(),
                new Capabilities(flag(row, "formal_query_enabled"), flag(row, "formal_action_enabled"), flag(row, "lifecycle_reader_enabled")));
        StrictJson.require(!request.activeObservationOnly(), "ordinary staging requires the normal selected plan");
        StageResult result = new OrdinarySwayService().stage(captured,
                () -> Optional.of(new Inputs(request.ledger(), request.state())));
        ObjectNode output = StrictJson.object(); output.put("schema", RESPONSE_SCHEMA);
        output.put("status", result.staged().isPresent() ? "staged" : "preserved");
        output.put("reason", result.reason().name().toLowerCase(Locale.ROOT));
        output.put("selected_step", result.staged().isPresent() ? STEP
                : StrictJson.text(row.get("request").get("selected_step")));
        if (result.decision().isPresent()) {
            output.set("decision", StrictJson.parse(SwayScheduleWire.encode(result.decision().orElseThrow())));
        } else { output.putNull("decision"); }
        result.error().ifPresent(value -> output.put("error", value));
        output.put("submit_allowed", false); output.put("game_outcome_claimed", false);
        return StrictJson.canonical(output);
    }

    private static boolean flag(ObjectNode row, String key) {
        var value = row.get(key); StrictJson.require(value != null && value.isBoolean(), "actual boolean required: " + key);
        return value.booleanValue();
    }
}
