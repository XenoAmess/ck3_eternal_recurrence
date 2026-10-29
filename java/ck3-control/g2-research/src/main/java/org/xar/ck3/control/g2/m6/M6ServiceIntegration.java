package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;

/** Single-host copied-reader composition. The original ledger is assessed and preserved, never committed. */
public final class M6ServiceIntegration {
    public static final String PACKET_SCHEMA = "xar.g2.m6.service-copied-sources/v1";
    public static final String RESULT_SCHEMA = "xar.g2.m6.service-source-result/v1";
    private static final int MAX = M6SourceProducer.MAX_BYTES;
    private M6ServiceIntegration() { }
    public record EpisodeSources(String actionId, M6TerminalSourceComposition.Inputs inputs) {
        public EpisodeSources { StrictJson.text(actionId); Objects.requireNonNull(inputs); }
    }
    public record Result(G2M6Contracts.CampaignEvidence evidence, List<M6TerminalSourceComposition.Result> compositions,
            G2M6Contracts.CampaignAssessment assessment) {
        public Result { Objects.requireNonNull(evidence); compositions = List.copyOf(compositions); Objects.requireNonNull(assessment); }
        public boolean actionAuthorized() { return false; }
        public boolean requestRetried() { return false; }
        public boolean ledgerCommitted() { return false; }
    }

    /** Independent copied-observation reducer; the existing HTTP result and writer remain unchanged. */
    public static M6ObservationReducer.Report observeCampaign(G2M6Contracts.CampaignEvidence evidence,
            List<M6ObservationReducer.Input> sources) {
        return M6ObservationReducer.observe(evidence, sources);
    }

    public static Result compose(G2M6Contracts.CampaignEvidence evidence, List<EpisodeSources> sources, M6Research research) {
        Objects.requireNonNull(evidence); Objects.requireNonNull(research); sources = List.copyOf(sources);
        Set<String> seen = new HashSet<>(); List<M6TerminalSourceComposition.Result> results = new ArrayList<>();
        for (EpisodeSources source : sources) {
            require(seen.add(source.actionId()), "M6 episode source action duplicated");
            G2M6Contracts.Episode episode = evidence.episodes().stream().filter(row -> row.identity().actionId().equals(source.actionId()))
                    .findFirst().orElseThrow(() -> new IllegalArgumentException("M6 source has no admitted original episode"));
            results.add(M6TerminalSourceComposition.compose(episode, source.inputs()));
        }
        return new Result(evidence, results, research.evaluateCampaign(evidence));
    }

    public static G2Response evaluate(G2Request request, M6Research research) {
        Objects.requireNonNull(request); require(request.milestone() == Milestone.M6, "M6 service milestone differs");
        require(request.source().sourceRef().bytes() == request.payload().size()
                && request.source().sourceRef().sha256().equals(sha(request.payload().bytes())), "M6 outer service source pin differs");
        JsonNode packet = StrictJson.object(StrictJson.parse(request.payload().bytes(), MAX), Set.of("schema", "evidence_packet", "episode_sources"));
        M6TerminalSourceComposition.textEquals(packet, "schema", PACKET_SCHEMA);
        JsonNode nested = StrictJson.object(packet.get("evidence_packet"), Set.of("source_ref", "original_bytes_base64"));
        ExactRef ref = ExactRef.fromJson(nested.get("source_ref"));
        byte[] bytes = decode(nested.get("original_bytes_base64"), ref);
        G2Source source = new G2Source(request.source().machineId(), request.source().observedAtUtc(), request.source().exactBuild(), ref);
        var evidence = M6SourceProducer.fromEvidencePacket(bytes, source);
        JsonNode rows = packet.get("episode_sources"); M6TerminalSourceComposition.array(rows);
        List<EpisodeSources> sources = new ArrayList<>();
        for (JsonNode row : rows) {
            StrictJson.object(row, Set.of("action_id", "completion_read", "execution_frame", "termination_frame", "opinion_read"));
            sources.add(new EpisodeSources(StrictJson.text(row.get("action_id")), new M6TerminalSourceComposition.Inputs(
                    optional(row.get("completion_read")), optional(row.get("execution_frame")), optional(row.get("termination_frame")), optional(row.get("opinion_read")))));
        }
        Result result = compose(evidence, sources, research);
        ObjectNode output = StrictJson.object(); output.put("schema", RESULT_SCHEMA); output.put("milestone_status", "in_progress");
        output.set("assessment", StrictJson.parse(research.toJson(result.assessment()).bytes(), MAX));
        var compositions = output.putArray("compositions");
        for (var composition : result.compositions()) compositions.add(StrictJson.parse(composition.wire().bytes(), MAX));
        output.put("grants_submission_authority", false); output.put("request_retried", false); output.put("ledger_committed", false);
        output.put("game_day_credit", 0); output.put("whole_m6_complete", false);
        return new G2Response(request.requestId(), Milestone.M6, request.source(), ProjectionJson.object(StrictJson.canonical(output, MAX), MAX));
    }

    /** Producer of the exact same packet parsed by the resident M6 route. */
    public static byte[] encode(byte[] evidencePacket, ExactRef ref, List<EpisodeSources> sources) {
        Objects.requireNonNull(evidencePacket); Objects.requireNonNull(ref); sources = List.copyOf(sources);
        require(ref.bytes() == evidencePacket.length && ref.sha256().equals(sha(evidencePacket)), "M6 evidence packet source pin differs");
        ObjectNode output = StrictJson.object(); output.put("schema", PACKET_SCHEMA);
        ObjectNode nested = output.putObject("evidence_packet"); nested.set("source_ref", ref.toJson()); nested.put("original_bytes_base64", Base64.getEncoder().encodeToString(evidencePacket));
        var rows = output.putArray("episode_sources");
        for (EpisodeSources source : sources) {
            ObjectNode row = rows.addObject(); row.put("action_id", source.actionId());
            put(row, "completion_read", source.inputs().completion()); put(row, "execution_frame", source.inputs().execution());
            put(row, "termination_frame", source.inputs().termination()); put(row, "opinion_read", source.inputs().opinion());
        }
        // The base64 original is a role-bounded transport value, not a small business string.
        return ProjectionJson.object(output.toString().getBytes(StandardCharsets.UTF_8), MAX).bytes();
    }
    private static void put(ObjectNode output, String key, Optional<ProjectionJson> value) {
        if (value.isEmpty()) output.putNull(key); else output.set(key, StrictJson.parse(value.orElseThrow().bytes(), MAX));
    }
    private static Optional<ProjectionJson> optional(JsonNode value) {
        require(value != null, "required nullable M6 copied plane missing");
        if (value.isNull()) return Optional.empty(); M6TerminalSourceComposition.object(value); return Optional.of(M6TerminalSourceComposition.json(value));
    }
    private static byte[] decode(JsonNode value, ExactRef ref) {
        require(value != null && value.isTextual() && value.textValue().length() <= MAX, "finite canonical M6 packet base64 required");
        byte[] decoded = Base64.getDecoder().decode(value.textValue());
        require(Base64.getEncoder().encodeToString(decoded).equals(value.textValue()) && ref.bytes() == decoded.length
                && ref.sha256().equals(sha(decoded)), "M6 nested exact original packet differs"); return decoded;
    }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException(failure); }
    }
}
