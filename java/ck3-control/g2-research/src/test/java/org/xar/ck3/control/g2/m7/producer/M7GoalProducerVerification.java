package org.xar.ck3.control.g2.m7.producer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7Research;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** Real original-producer vectors through the same M7 domain used by the host. */
public final class M7GoalProducerVerification {
    private static int checks;
    private M7GoalProducerVerification() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo fresh-golden new-result"); }
        Path.of(arguments[0]).toRealPath();
        Path goldenPath = Path.of(arguments[1]).toRealPath();
        byte[] goldenBytes = Files.readAllBytes(goldenPath);
        JsonNode golden = StrictJson.parse(goldenBytes, StrictJson.EXPLICIT_MAX_BYTES);
        var source = new G2Source(golden.path("machine_id").textValue(),
                Instant.parse(golden.path("observed_at_utc").textValue()).toString(), "1.20.0.2-retained-fixture",
                new ExactRef(goldenPath.toString(), goldenBytes.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(goldenBytes))));
        var domain = new M7Research();
        require(golden.path("source_refs_unchanged").booleanValue(), "original producer sources unchanged");
        require(golden.path("goal_cases").size() == 6, "six complete original goal vectors");
        int sequence = 0;
        for (JsonNode row : golden.path("goal_cases")) {
            String operation = row.path("operation").textValue();
            byte[] rawInput = row.path("raw_input_json").textValue().getBytes(StandardCharsets.UTF_8);
            byte[] actual = domain.evaluate(request(source, ++sequence, operation, rawInput)).result().bytes();
            JsonNode value = StrictJson.parse(actual, StrictJson.EXPLICIT_MAX_BYTES);
            require(value.equals(row.path("expected")), "original goal producer differential " + row.path("name").textValue());
            byte[] restored;
            if (operation.equals("goal_plan")) { restored = GoalCodec.encodePlan(GoalCodec.decodePlan(actual)); }
            else { restored = GoalCodec.encodeGoal(GoalCodec.decodeGoal(actual)); }
            require(Arrays.equals(actual, restored), "goal/plan persisted bytes roundtrip " + operation);
            String normalizedOperation = operation.equals("goal_plan") ? "goal_plan" : "goal_normalize";
            byte[] laterInput = operation.equals("goal_plan") ? rawInput : restored;
            byte[] later = new M7Research().evaluate(request(source, ++sequence, normalizedOperation, laterInput)).result().bytes();
            require(Arrays.equals(restored, later), "fresh domain consumes persisted goal or original goal plan input");
        }
        require(golden.path("goal_rejections").size() == 4, "all complete reconciliation refusal vectors");
        require(golden.path("strict_token_rejections").size() == 9, "all original raw-token vectors");
        for (String collection : List.of("goal_rejections", "strict_token_rejections")) {
            for (JsonNode row : golden.path(collection)) {
                var rejected = request(source, ++sequence, row.path("operation").textValue(),
                        row.path("raw_input_json").textValue().getBytes(StandardCharsets.UTF_8));
                reject(() -> domain.evaluate(rejected), row.path("name").textValue());
            }
        }
        for (JsonNode row : golden.path("government_cases")) {
            byte[] result = domain.evaluate(request(source, ++sequence, "government_context", bytes(row.path("input")))).result().bytes();
            require(StrictJson.parse(result).equals(row.path("expected")), "M7 host government producer delegation");
            byte[] restored = GovernmentContextCodec.encode(GovernmentContextCodec.decodeContext(result));
            require(StrictJson.parse(restored).equals(row.path("expected")), "M7 government typed persistence");
        }
        ObjectNode validGoal = (ObjectNode) golden.path("goal_cases").get(0).path("expected").deepCopy();
        for (String field : List.of("format_version", "goal_key", "campaign_id", "origin_character_id", "current_character_id", "progress")) {
            ObjectNode missing = validGoal.deepCopy(); missing.remove(field);
            var malformed = request(source, ++sequence, "goal_normalize", bytes(missing));
            reject(() -> domain.evaluate(malformed), "missing goal field " + field);
        }
        ObjectNode missingLast = validGoal.deepCopy(); ((ObjectNode) missingLast.get("progress")).remove("last_succession");
        var missingLastRequest = request(source, ++sequence, "goal_normalize", bytes(missingLast));
        reject(() -> domain.evaluate(missingLastRequest), "missing last_succession differs from explicit null");
        ObjectNode extra = validGoal.deepCopy(); extra.put("checkpoint_authorized", true);
        var extraRequest = request(source, ++sequence, "goal_normalize", bytes(extra));
        reject(() -> domain.evaluate(extraRequest), "unknown goal field cannot grant authority");
        ObjectNode actual = StrictJson.object();
        actual.put("schema", "xar.g2-m7-goal-producer-verification/v1"); actual.put("machine_id", source.machineId());
        actual.put("observed_at_utc", Instant.now().toString()); actual.put("status", "PASS"); actual.put("checks", checks);
        actual.put("original_goal_vectors", 6); actual.put("original_complete_reconciliation_refusals", 4);
        actual.put("original_raw_token_refusals", 9); actual.put("fresh_government_domain_vectors", 4);
        actual.put("game_calls", 0); actual.put("true_driver_or_save_body_reads", 0);
        actual.put("qualification_scope", "unchanged original production pure outputs through M7Research and typed persistence; no live/reducer/writer/game qualification");
        Files.write(Path.of(arguments[2]), StrictJson.canonical(actual), StandardOpenOption.CREATE_NEW);
        System.out.println("M7 original goal/government producer domain differential PASS: " + checks);
    }

    private static G2Request request(G2Source source, int sequence, String operation, byte[] rawInput) {
        require(operation != null && operation.matches("[a-z_]+"), "closed test operation token");
        byte[] payload = ("{\"operation\":\"" + operation + "\",\"input\":"
                + new String(rawInput, StandardCharsets.UTF_8) + "}").getBytes(StandardCharsets.UTF_8);
        return new G2Request("m7-producer-" + sequence, Milestone.M7, source, ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
    }
    private static void require(boolean condition, String label) {
        if (!condition) { throw new IllegalStateException(label); } checks++;
    }
    private static void reject(Runnable call, String label) {
        try { call.run(); } catch (IllegalArgumentException expected) { checks++; return; }
        throw new IllegalStateException("expected actual M7 domain rejection: " + label);
    }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
