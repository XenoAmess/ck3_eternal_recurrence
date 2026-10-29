package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionFreshnessModel.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.check;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Strict versioned wrapper over the existing original reconciliation and full-title normalizer. */
public final class SuccessionFreshnessCodec {
    public static final String SCHEMA = "xar.java-succession-freshness-request/v1";
    public static final String RESULT_SCHEMA = "xar.g2.succession-expectation-freshness-observation.v1";
    public static final int MAXIMUM_BYTES = 2 * SuccessionCodec.MAX_BYTES + 4096;
    private static final ObjectMapper JSON = JsonMapper.builder(JsonFactory.builder()
                    .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS,
                    DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private SuccessionFreshnessCodec() { }

    public static byte[] observe(byte[] body) { return encode(SuccessionFreshnessPolicy.observe(decode(body))); }

    public static Input decode(byte[] body) {
        JsonNode request = parse(body, true);
        SuccessionCodec.exact(request, Set.of("schema", "reconciliation", "expectation", "last_living_frame"));
        check(SCHEMA.equals(SuccessionCodec.text(SuccessionCodec.field(request, "schema"))), "freshness request schema changed");
        JsonNode reconciliation = SuccessionCodec.field(request, "reconciliation");
        check(SuccessionModel.RECONCILIATION_SCHEMA.equals(SuccessionCodec.text(SuccessionCodec.field(reconciliation, "schema")))
                        && "available".equals(SuccessionCodec.text(SuccessionCodec.field(reconciliation, "status"))),
                "succession freshness requires the original reconciliation");
        EpisodeBinding source = binding(SuccessionCodec.field(reconciliation, "predecessor_binding"));
        Frame boundary = frame(SuccessionCodec.field(reconciliation, "successor_binding"));
        BigInteger predecessor = NativeCharacterId.fromJson(SuccessionCodec.field(reconciliation, "predecessor_character_id")).asBigInteger();
        JsonNode expectation = SuccessionCodec.field(request, "expectation");
        JsonNode living = SuccessionCodec.field(request, "last_living_frame");
        JsonNode verdict = reconciliation.get("verdict");
        return new Input(source, boundary, predecessor,
                expectation.isNull() ? Optional.empty() : Optional.of(SuccessionCodec.decodeExpectation(bytes(expectation))),
                living.isNull() ? Optional.empty() : Optional.of(binding(living)),
                new VerdictEvidence(bytes(verdict == null ? NullNode.getInstance() : verdict)));
    }

    /** Roundtrip of the consumed input projection; unrelated reconciliation fields are not facts. */
    public static byte[] encodeRequest(Input input) {
        ObjectNode request = JSON.createObjectNode(); request.put("schema", SCHEMA);
        ObjectNode reconciliation = request.putObject("reconciliation");
        reconciliation.put("schema", SuccessionModel.RECONCILIATION_SCHEMA); reconciliation.put("status", "available");
        reconciliation.set("predecessor_binding", bindingNode(input.predecessorBinding()));
        reconciliation.set("successor_binding", frameNode(input.boundaryBinding()));
        reconciliation.put("predecessor_character_id", input.predecessorCharacterId());
        reconciliation.set("verdict", parse(input.verdict().json(), false));
        request.set("expectation", input.expectation().<JsonNode>map(full ->
                parse(SuccessionCodec.encodeExpectation(full), true)).orElseGet(NullNode::getInstance));
        request.set("last_living_frame", input.lastLivingFrame().<JsonNode>map(SuccessionFreshnessCodec::bindingNode)
                .orElseGet(NullNode::getInstance));
        return bytes(request);
    }

    public static byte[] encode(Observation observation) {
        Input input = observation.input(); ObjectNode out = JSON.createObjectNode();
        out.put("schema", RESULT_SCHEMA); out.put("status", "observed");
        out.set("predecessor_binding", bindingNode(input.predecessorBinding()));
        out.set("boundary_binding", frameNode(input.boundaryBinding()));
        out.put("expectation_age_raw_at_boundary", observation.expectationAgeRaw());
        out.put("expectation_age_days_at_boundary", SuccessionFreshnessPolicy.days(observation.expectationAgeRaw()));
        out.set("last_observed_living_binding", input.lastLivingFrame().<JsonNode>map(SuccessionFreshnessCodec::bindingNode)
                .orElseGet(NullNode::getInstance));
        if (observation.lastLivingAgeRaw().isPresent()) {
            out.put("last_observed_living_age_days_at_boundary", SuccessionFreshnessPolicy.days(observation.lastLivingAgeRaw().orElseThrow()));
        } else { out.putNull("last_observed_living_age_days_at_boundary"); }
        if (observation.sameFrame().isPresent()) { out.put("same_frame_as_last_observed_living", observation.sameFrame().orElseThrow()); }
        else { out.putNull("same_frame_as_last_observed_living"); }
        out.put("complete_title_expectation_observed", input.expectation().isPresent());
        if (input.expectation().isPresent()) {
            var titles = out.putArray("complete_title_ids");
            input.expectation().orElseThrow().titleExpectations().forEach(row -> titles.add(row.title().titleId()));
        } else { out.putNull("complete_title_ids"); }
        out.put("all_title_freshness", observation.allTitleFreshness().wire());
        out.put("fresh_immediately_before_death_claimed", false);
        out.set("reconciliation_verdict_transcribed", parse(input.verdict().json(), false));
        out.put("reconciliation_verified_by_this_observer", false); out.put("process_birth_verified_by_this_observer", false);
        out.put("replay_allowed", false); out.put("business_credit", false); out.put("M7_coverage_credit", false);
        return bytes(out);
    }

    private static Frame frame(JsonNode node) {
        return new Frame(SuccessionCodec.text(SuccessionCodec.field(node, "snapshot_id")),
                integer(SuccessionCodec.field(node, "revision"), false),
                integer(SuccessionCodec.field(node, "native_revision"), false),
                integer(SuccessionCodec.field(node, "date_raw"), false));
    }
    private static EpisodeBinding binding(JsonNode node) {
        return new EpisodeBinding(frame(node), SuccessionCodec.text(SuccessionCodec.field(node, "episode_run_id")),
                NativeCharacterId.fromJson(SuccessionCodec.field(node, "episode_character_id")).asBigInteger());
    }
    private static BigInteger integer(JsonNode node, boolean positive) {
        check(node != null && node.isIntegralNumber(), "exact freshness integer required; no bool, float or string");
        BigInteger value = node.bigIntegerValue();
        check(positive ? value.signum() > 0 : value.signum() >= 0, "freshness integer is outside its original domain");
        return value;
    }
    private static ObjectNode frameNode(Frame frame) {
        ObjectNode out = JSON.createObjectNode(); out.put("snapshot_id", frame.snapshotId());
        out.put("revision", frame.revision()); out.put("native_revision", frame.nativeRevision()); out.put("date_raw", frame.dateRaw());
        return out;
    }
    private static ObjectNode bindingNode(EpisodeBinding binding) {
        ObjectNode out = frameNode(binding.frame()); out.put("episode_run_id", binding.episodeRunId());
        out.put("episode_character_id", binding.episodeCharacterId()); return out;
    }
    private static JsonNode parse(byte[] raw, boolean object) {
        byte[] validated = (object ? ProjectionJson.object(raw, MAXIMUM_BYTES) : ProjectionJson.value(raw, MAXIMUM_BYTES)).bytes();
        try { return JSON.readTree(validated); }
        catch (IOException error) { throw new IllegalArgumentException("invalid freshness JSON", error); }
    }
    private static byte[] bytes(JsonNode value) {
        try { return ProjectionJson.value(JSON.writeValueAsBytes(value), MAXIMUM_BYTES).bytes(); }
        catch (IOException error) { throw new IllegalArgumentException("freshness JSON encoding failed", error); }
    }
}
