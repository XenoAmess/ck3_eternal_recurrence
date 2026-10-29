package org.xar.ck3.control.g2.m6;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Pure producer export for the unique host assembler; this program does not claim an HTTP call. */
public final class M6ServiceCapture {
    private M6ServiceCapture() { }
    public static void main(String[] args) throws Exception {
        StrictJson.require(args.length == 1, "new output directory required"); Path output = Path.of(args[0]); Files.createDirectory(output);
        byte[] ledger = M6TerminalSourceCompositionTest.resource("closed-ledger-original.json");
        byte[] auto = M6TerminalSourceCompositionTest.resource("ordinary-start-auto48-original.json");
        byte[] packet = M6SourceProducer.encodeEvidencePacket(ledger, M6TerminalSourceCompositionTest.ref("fixture:original-closed-ledger", ledger),
                auto, M6TerminalSourceCompositionTest.ref("fixture:original-AUTO48", auto),
                new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
        var evidence = M6SourceProducer.fromEvidencePacket(packet, M6TerminalSourceCompositionTest.source("fixture:ordinary-packet", packet));
        var sources = evidence.episodes().stream().map(episode -> new M6ServiceIntegration.EpisodeSources(episode.identity().actionId(),
                M6TerminalSourceCompositionTest.inputs(M6TerminalSourceCompositionTest.completion(episode), null, null, null))).toList();
        byte[] payload = M6ServiceIntegration.encode(packet, M6TerminalSourceCompositionTest.ref("fixture:ordinary-packet", packet), sources);
        G2Request request = request("m6-service-original-two", payload); var response = new M6Research().evaluate(request);
        write(output, "M6-service.request.json", G2Wire.encodeRequest(request));
        write(output, "M6-service.expected-result.json", response.result().bytes());
        write(output, "M6-service.expected-response.json", G2Wire.encodeResponse(response));
        var episode = evidence.episodes().getFirst(); ObjectNode termination = M6TerminalSourceCompositionTest.journal(episode, false);
        termination.put("scheme_instance_generation", true);
        var badInputs = new M6TerminalSourceComposition.Inputs(Optional.empty(), Optional.empty(),
                Optional.of(ProjectionJson.object(StrictJson.canonical(termination), M6SourceProducer.MAX_BYTES)), Optional.empty());
        byte[] bad = M6ServiceIntegration.encode(packet, M6TerminalSourceCompositionTest.ref("fixture:ordinary-packet", packet),
                List.of(new M6ServiceIntegration.EpisodeSources(episode.identity().actionId(), badInputs)));
        write(output, "M6-service-invalid.request.json", G2Wire.encodeRequest(request("m6-service-bool-generation", bad)));
        boolean refused = false;
        try { new M6Research().evaluate(request("m6-service-bool-generation", bad)); }
        catch (IllegalArgumentException expected) { refused = true; }
        StrictJson.require(refused, "malformed actual producer fixture must be refused");
        ObjectNode actual = StrictJson.object(); actual.put("schema", "xar.g2.m6.service-fixture-export/v1");
        actual.put("machine_id", "xenoamess-full-tower-eb9d2c1186"); actual.put("observed_at_utc", Instant.now().toString());
        actual.put("scope", "Actual Java producer exports over retained historical inputs; direct domain evaluation, not HTTP or live native qualification");
        actual.put("malformed_generation_refused", refused); actual.put("original_episodes", evidence.episodes().size());
        actual.put("http_invoked", false); actual.put("game_rpc_calls", 0); actual.put("game_days", 0); actual.put("natural_live_terminal", "UNKNOWN");
        var refs = actual.putArray("outputs");
        for (String name : List.of("M6-service.request.json", "M6-service.expected-result.json", "M6-service.expected-response.json", "M6-service-invalid.request.json")) {
            byte[] bytes = Files.readAllBytes(output.resolve(name)); refs.add(M6TerminalSourceCompositionTest.ref(output.resolve(name).toString(), bytes).toJson());
        }
        write(output, "M6-SERVICE-CAPTURE-ACTUAL01.json", StrictJson.canonical(actual));
    }
    private static G2Request request(String id, byte[] payload) throws Exception {
        return new G2Request(id, Milestone.M6, M6TerminalSourceCompositionTest.source("fixture:" + id, payload), ProjectionJson.object(payload, M6SourceProducer.MAX_BYTES));
    }
    private static void write(Path output, String name, byte[] bytes) throws Exception { Files.write(output.resolve(name), bytes, StandardOpenOption.CREATE_NEW); }
}
