package org.xar.ck3.control.g2.m0.integration;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m0.M0Research;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;
import org.xar.ck3.control.g2.m0.RaiktorRecommendationInputCodec;

/** One source-bound original M0 oracle vector through the actual common wire and domain route.
 * Output files are HTTP test inputs, never native observations or action authorizations.
 */
public final class M0CommonRoundTrip {
    private M0CommonRoundTrip() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 5) throw new IllegalArgumentException("original-input, original-expected, source-metadata, fresh-output-directory, request-id required");
        byte[] payload = read(Path.of(args[0]), ProjectionJson.MAX_BYTES);
        byte[] expected = read(Path.of(args[1]), ProjectionJson.MAX_BYTES);
        ObjectNode sourceJson = StrictJson.object(StrictJson.parse(read(Path.of(args[2]), 8192)),
                Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        G2Source source = new G2Source(StrictJson.text(sourceJson.get("machine_id")),
                StrictJson.text(sourceJson.get("observed_at_utc")), StrictJson.text(sourceJson.get("exact_build")),
                ExactRef.fromJson(sourceJson.get("source_ref")));
        G2Request original = new G2Request(args[4], Milestone.M0, source, ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
        byte[] requestBytes = G2Wire.encodeRequest(original);
        G2Request decoded = G2Wire.decodeRequest(requestBytes);
        requireEcho(original, decoded);
        G2ResearchEngine engine = new G2ResearchEngine(List.<G2Domain>of(new M0Research()));
        DecisionMetricRecorder.SystemClock clock = new DecisionMetricRecorder.SystemClock();
        DecisionMetricRecorder recorder = new DecisionMetricRecorder(new DecisionMetrics.Context(
                source.machineId(), "g2-m0-original-oracle", "software-common-wire", decoded.requestId(), clock.domainId()), clock);
        G2Response response = engine.evaluate(decoded, recorder);
        DecisionMetrics.Snapshot metrics = recorder.snapshot();
        byte[] metricsBytes = DecisionMetrics.encode(metrics);
        if (!DecisionMetrics.decode(metricsBytes).equals(metrics) || metrics.spans().size() != 1
                || metrics.spans().getFirst().stage() != DecisionMetrics.Stage.DOMAIN_EVALUATION
                || metrics.spans().getFirst().terminal() != DecisionMetrics.Terminal.RETURNED
                || metrics.acknowledgements().isPresent() || metrics.nativeObservation().isPresent() || metrics.savedWindow().isPresent()
                || metrics.speedupClaimAllowed()) throw new IllegalStateException("pure M0 metrics acquired invalid game or speed credit");
        if (!response.requestId().equals(original.requestId()) || response.milestone() != Milestone.M0
                || !response.source().equals(source)) throw new IllegalStateException("common M0 response source echo drifted");
        sameJson(expected, response.result().bytes());
        byte[] responseBytes = G2Wire.encodeResponse(response);
        G2Response restored = G2Wire.decodeResponse(responseBytes);
        if (!restored.requestId().equals(original.requestId()) || !restored.source().equals(source)
                || restored.milestone() != Milestone.M0) throw new IllegalStateException("common response persisted identity drifted");
        sameJson(expected, restored.result().bytes());

        String raw = new String(requestBytes, StandardCharsets.UTF_8);
        String altered = raw.replace("\"schema_version\":1", "\"schema_version\":true");
        if (altered.equals(raw)) throw new IllegalStateException("outer raw version mutation did not change input");
        boolean outerRejected = false;
        try { G2Wire.decodeRequest(altered.getBytes(StandardCharsets.UTF_8)); }
        catch (G2Exception expectedRejection) { outerRejected = true; }
        if (!outerRejected) throw new IllegalStateException("raw bool version became an integer");

        ObjectNode wrongPayload = (ObjectNode) RaiktorExitObservationCodec.parseWire(payload);
        ObjectNode frame = (ObjectNode) wrongPayload.path("terminal_control").path("frame");
        if (!frame.has("date_raw")) throw new IllegalArgumentException("real source terminal frame required");
        frame.put("date_raw", frame.get("date_raw").bigIntegerValue().add(java.math.BigInteger.ONE));
        G2Request wrongFrame = new G2Request(original.requestId() + "-wrong-frame", Milestone.M0, source,
                ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(wrongPayload), ProjectionJson.MAX_BYTES));
        boolean frameRejected = false;
        try { engine.evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(wrongFrame))); }
        catch (G2Exception expectedRejection) { frameRejected = true; }
        catch (RaiktorRecommendationInputCodec.InputRejected expectedRejection) { frameRejected = true; }
        if (!frameRejected) throw new IllegalStateException("M0 domain accepted a crossed terminal frame");

        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(output) || !Files.isDirectory(output.getParent())) throw new IllegalArgumentException("fresh admitted output directory required");
        Files.createDirectory(output);
        write(output.resolve("M0.request.json"), requestBytes);
        write(output.resolve("M0.expected-result.json"), expected);
        write(output.resolve("M0.response.json"), responseBytes);
        write(output.resolve("M0.decision-metrics.json"), metricsBytes);
        write(output.resolve("M0.raw-version-bool.request.json"), altered.getBytes(StandardCharsets.UTF_8));
        write(output.resolve("M0.wrong-frame.request.json"), G2Wire.encodeRequest(wrongFrame));
        ObjectNode receipt = StrictJson.object();
        receipt.put("schema", "xar.g2-m0-common-roundtrip/v1"); receipt.put("status", "PASS");
        receipt.set("source", sourceJson); receipt.put("request_id", original.requestId());
        receipt.put("source_echo_roundtrip", true); receipt.put("original_expected_result_match", true);
        receipt.put("outer_raw_bool_rejected", true); receipt.put("domain_cross_frame_rejected", true);
        receipt.put("actual_http", false); receipt.put("game_calls", 0); receipt.put("actual_driver_state_reads", 0);
        receipt.put("actual_save_state_reads", 0); receipt.put("action_submitted", false); receipt.put("postcondition_verified", false);
        write(output.resolve("M0.common-roundtrip.json"), StrictJson.canonical(receipt, 8192));
    }

    private static void requireEcho(G2Request original, G2Request decoded) {
        if (!original.requestId().equals(decoded.requestId()) || original.milestone() != decoded.milestone()
                || !original.source().equals(decoded.source()))
            throw new IllegalStateException("common request persisted source or raw payload drifted");
        sameJson(original.payload().bytes(), decoded.payload().bytes());
    }
    private static void sameJson(byte[] expected, byte[] actual) {
        JsonNode expectedJson = RaiktorExitObservationCodec.parseWire(expected);
        JsonNode actualJson = RaiktorExitObservationCodec.parseWire(actual);
        if (!expectedJson.equals(actualJson))
            throw new IllegalStateException("common M0 result differs from retained original producer oracle");
    }
    private static byte[] read(Path path, int maximum) throws IOException {
        try (var stream = Files.newInputStream(path)) {
            byte[] raw = stream.readNBytes(maximum + 1);
            if (raw.length == 0 || raw.length > maximum) throw new IllegalArgumentException("bounded actual input required");
            return raw;
        }
    }
    private static void write(Path path, byte[] raw) throws IOException { Files.write(path, raw, StandardOpenOption.CREATE_NEW); }
}
