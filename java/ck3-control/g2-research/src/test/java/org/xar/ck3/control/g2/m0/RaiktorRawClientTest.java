package org.xar.ck3.control.g2.m0;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpServer;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.*;
import org.xar.ck3.control.g2.m0.RaiktorRawClient.*;
import org.xar.ck3.control.g2.m0.RaiktorRawOperations.Operation;

/** Actual raw producer -> M0 dispatcher -> common wire -> existing SDK -> strict consumer.
 * Loopback is a protocol fixture, not Quarkus/native/Game qualification. */
final class RaiktorRawClientTest {
    private static final G2Source SOURCE = new G2Source("fixture-machine", "2026-10-23T17:50:00Z", "synthetic-sdk-raw-only",
            new ExactRef("D:/synthetic-not-opened/raw-source.json", 1, "a".repeat(64)));
    private static final int OPPONENT = Integer.MIN_VALUE + 1;
    private static final Sha256 SHA = new Sha256("A".repeat(64));
    @TempDir Path directory;

    @Test void allThirteenTypedRequestsReachActualDispatcherAndExistingHttpSdkExactlyOnce() throws Exception {
        var configuration = configuration();
        var engine = new G2ResearchEngine(List.of(new M0Research()));
        var campaign = campaign();
        var local = new RaiktorRawClient(engine::evaluate);
        var certificate = ((DocumentResult)local.evaluate("seed-power", SOURCE, campaign)).document().value().get("campaign_dominance_certificate");
        var requests = requests(configuration, certificate);
        assertEquals(EnumSet.allOf(Operation.class), EnumSet.copyOf(requests.stream().map(Request::operation).toList()));
        AtomicInteger calls = new AtomicInteger();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext(G2Wire.HTTP_PATH, exchange -> {
            try {
                calls.incrementAndGet(); var input = G2Wire.decodeRequest(exchange.getRequestBody().readNBytes(G2Wire.MAX_REQUEST_BYTES + 1));
                byte[] output = G2Wire.encodeResponse(engine.evaluate(input)); headers(exchange);
                exchange.sendResponseHeaders(200, output.length); exchange.getResponseBody().write(output);
            } finally { exchange.close(); }
        });
        server.start();
        try (var sdk = new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + server.getAddress().getPort()), Duration.ofSeconds(5), G2Wire.MAX_RESPONSE_BYTES))) {
            var client = new RaiktorRawClient(sdk);
            for (Request request : requests) {
                int before = calls.get(); Result result = client.evaluate("raw-" + request.operation().name(), SOURCE, request);
                assertEquals(before + 1, calls.get()); assertEquals(request.operation(), result.operation());
                if (result instanceof AggregateResult aggregate) assertTrue(aggregate.aggregate().isEmpty());
                if (result instanceof ConfigurationResult loaded) {
                    assertEquals("available", loaded.budgetProvider().value().get("status").textValue());
                    assertEquals("available", loaded.modelProvider().value().get("status").textValue());
                }
                if (result instanceof RecommendationUnavailable unavailable)
                    assertEquals(List.of(RaiktorActualRecommendationFactory.Blocker.CURRENT_SNAPSHOT_UNAVAILABLE), unavailable.blockers());
                if (result instanceof AttachmentResult attached) {
                    assertEquals(attached.request().termsQuery().value().get("original_extra"), attached.document().value().get("original_extra"));
                    var forged = (ObjectNode)attached.document().value(); forged.put("unbacked_extra", "forged");
                    assertThrows(IllegalArgumentException.class, () -> RaiktorRawClient.consume(attached.request(), forged));
                    assertThrows(IllegalArgumentException.class, () -> RaiktorRawClient.consume(Operation.ATTACH, attached.document().value()));
                }
            }
            assertEquals(13, calls.get());
        } finally { server.stop(0); }
    }

    @Test void genericExistingSdkRejectsForgedRawResultBeforeReturningSuccessAndNeverRetries() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext(G2Wire.HTTP_PATH, exchange -> {
            try {
                calls.incrementAndGet(); var input = G2Wire.decodeRequest(exchange.getRequestBody().readNBytes(G2Wire.MAX_REQUEST_BYTES + 1));
                // A common valid G2 envelope still cannot turn {} into an aggregate or unavailable into available.
                var returned = new G2Response(input.requestId(), input.milestone(), input.source(), ProjectionJson.value("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8), ProjectionJson.MAX_BYTES));
                byte[] raw = G2Wire.encodeResponse(returned); headers(exchange); exchange.sendResponseHeaders(200, raw.length); exchange.getResponseBody().write(raw);
            } finally { exchange.close(); }
        });
        server.start();
        try (var sdk = new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + server.getAddress().getPort()), Duration.ofSeconds(5), G2Wire.MAX_RESPONSE_BYTES))) {
            var input = new G2Request("forged-aggregate", Milestone.M0, SOURCE,
                    ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(new ProjectSurrender(nil(), nil(), nil(), nil()).payload()), ProjectionJson.MAX_BYTES));
            var error = assertThrows(G2ClientException.class, () -> sdk.evaluateWithEvidence(input));
            assertEquals(G2ClientException.Reason.RESPONSE_UNVERIFIED, error.reason()); assertEquals(1, calls.get());
        } finally { server.stop(0); }
    }

    @Test void rawContractWrongTypesFieldsAndPersistedResultMutationStayRejected() throws Exception {
        var configuration = configuration(); var engine = new G2ResearchEngine(List.of(new M0Research()));
        var client = new RaiktorRawClient(engine::evaluate);
        var certificate = ((DocumentResult)client.evaluate("original", SOURCE, campaign())).document().value().get("campaign_dominance_certificate");
        assertInstanceOf(DocumentResult.class, client.evaluate("normalized", SOURCE, new NormalizePower(Operand.of(certificate))));
        for (JsonNode wrong : List.of(StrictJson.object(), StrictJson.object().put("unexpected", true), NullNode.instance))
            assertThrows(IllegalArgumentException.class, () -> RaiktorRawClient.consume(Operation.CAMPAIGN, wrong));
        ObjectNode tampered = ((ObjectNode) certificate).deepCopy(); ((ObjectNode)tampered.get("power")).put("actor_power_total_raw", true);
        assertThrows(IllegalArgumentException.class, () -> client.evaluate("tampered", SOURCE, new NormalizePower(Operand.of(tampered))));
        var request = new LoadConfiguration(configuration).payload(); ((ObjectNode)request.at("/configuration_sources/default_budget")).put("bytes", true);
        assertThrows(IllegalArgumentException.class, () -> engine.evaluate(new G2Request("wrong-ref", Milestone.M0, SOURCE,
                ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(request), ProjectionJson.MAX_BYTES))));
        var alias = StrictJson.object().put("x", 1); var retained = Operand.of(alias); alias.put("x", 2);
        assertEquals(1, retained.value().get("x").intValue()); ((ObjectNode)retained.value()).put("x", 3); assertEquals(1, retained.value().get("x").intValue());
        assertThrows(NullPointerException.class, () -> Operand.of(null));
        assertThrows(IllegalArgumentException.class, () -> new FullId(-1));
        assertThrows(IllegalArgumentException.class, () -> new Sha256("short"));
        assertThrows(IllegalArgumentException.class, () -> new Sha256("a".repeat(64)));
        ObjectNode unavailable = StrictJson.object().put("schema", "xar.ck3.raiktor-actual-recommendation-result/v1").put("status", "unavailable").put("action_authority", true);
        unavailable.putNull("recommendation"); unavailable.putArray("blockers").add("CURRENT_SNAPSHOT_UNAVAILABLE"); unavailable.putArray("diagnostics");
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawClient.consume(Operation.ACTUAL, unavailable));
        String duplicate = "{\"operation\":\"project-surrender-six-domain\",\"operation\":\"project-surrender-six-domain\"}";
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(duplicate.getBytes(java.nio.charset.StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES));
        var wrongEcho = new RaiktorRawClient(input -> new G2Response("wrong", input.milestone(), input.source(), ProjectionJson.value("null".getBytes(java.nio.charset.StandardCharsets.UTF_8), ProjectionJson.MAX_BYTES)));
        assertThrows(IllegalArgumentException.class, () -> wrongEcho.evaluate("right", SOURCE, new ProjectSurrender(nil(), nil(), nil(), nil())));
        var wrongSource = new RaiktorRawClient(input -> {
            var changed = campaign().payload(); changed.put("source_artifact_sha256", "B".repeat(64));
            return engine.evaluate(new G2Request(input.requestId(), input.milestone(), input.source(),
                    ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(changed), ProjectionJson.MAX_BYTES)));
        });
        assertThrows(IllegalArgumentException.class, () -> wrongSource.evaluate("same-envelope-other-source", SOURCE, campaign()));
    }

    private List<Request> requests(RaiktorActualRecommendationFactory.ConfigurationSources sources, JsonNode certificate) throws Exception {
        var target = ((ObjectNode)certificate.get("frame")).deepCopy(); target.put("ck3_pid", 124);
        JsonNode budget = StrictJson.parse(Files.readAllBytes(sources.defaultBudget().path()), StrictJson.EXPLICIT_MAX_BYTES);
        JsonNode model = StrictJson.parse(Files.readAllBytes(sources.defaultModel().path()), StrictJson.EXPLICIT_MAX_BYTES);
        var actual = new RaiktorActualRecommendationFactory.Inputs(NullNode.instance, NullNode.instance, NullNode.instance,
                NullNode.instance, NullNode.instance, NullNode.instance, NullNode.instance, NullNode.instance, 17, 99, false);
        var query = StrictJson.object().put("accepted", true).put("status", "available"); query.set("war_termination_terms", unsupported());
        query.putObject("original_extra").put("file_id", "18446744073709551615").putNull("optional");
        return List.of(campaign(), new NormalizePower(Operand.of(certificate)),
                new ReplayPower(Operand.of(certificate), Operand.of(target), SHA, SHA, new Sha256("B".repeat(64)), new Sha256("B".repeat(64))),
                new WhitePeace(nil(), nil(), nil(), false), new ProjectSurrender(nil(), nil(), nil(), nil()), new BindSurrender(nil(), nil(), nil()),
                new AttachSurrender(nil(), Operand.of(query), nil()),
                new RenderBudget(Operand.of(budget), new Sha256(sources.defaultBudget().sha256().toUpperCase(java.util.Locale.ROOT)), Operand.of(budget)),
                new RenderModel(Operand.of(model), new Sha256(sources.defaultModel().sha256().toUpperCase(java.util.Locale.ROOT))),
                new ProvideBudget(sources.defaultBudget(), Optional.empty()), new ProvideModel(sources.defaultBudget(), sources.defaultModel(), Optional.empty()),
                new LoadConfiguration(sources), new ActualRecommendation(actual, sources));
    }
    private static Operand nil() { return Operand.of(NullNode.instance); }
    private static Campaign campaign() {
        return new Campaign(Operand.of(snapshot()), Operand.of(query(40)), Operand.of(snapshot()), Operand.of(query(41)), Operand.of(snapshot()),
                new FullId(17), new FullId(OPPONENT), SHA);
    }
    private static ObjectNode snapshot() {
        var n = StrictJson.object().put("snapshot_id", "p900").put("revision", 900).put("native_revision", 51).put("date_raw", 53144520)
                .put("paused", true).put("map_ready", true).put("episode_run_id", "fixture-episode");
        n.putObject("diagnostics").put("connection_generation", 7).put("bridge_pid", 123); n.putObject("played_character").put("character_id", Integer.MIN_VALUE);
        n.putArray("active_wars").addObject().put("war_id", 17).put("player_side", "attacker").put("player_is_primary_war_leader", true).put("primary_opponent_character_id", OPPONENT); return n;
    }
    private static ObjectNode query(int sequence) {
        var q = StrictJson.object().put("query_sequence", sequence).put("accepted", true).put("status", "available").put("queried_snapshot_id", "p900")
                .put("queried_revision", 900).put("queried_native_revision", 51);
        q.putArray("target_scopes").addObject().put("target_character_id", OPPONENT).putArray("sources").add("active_war_primary_opponent");
        var n = q.putObject("war_entry_assessments").put("status", "available").put("snapshot_revision", 51).put("date_raw", 53144520).put("actor_character_id", Integer.MIN_VALUE);
        n.putArray("requested_target_character_ids").add(OPPONENT); n.putObject("readiness").put("ready", true).put("actual_power_ratio_ready", true);
        n.putObject("provenance").put("fixed_point_scale", 100000);
        n.putArray("assessments").addObject().put("target_character_id", OPPONENT).put("effective_target_character_id", OPPONENT)
                .put("actor_power_base_raw", 1000000).put("actor_network_contribution_raw", 1000000).put("actor_power_total_raw", 2000000)
                .put("target_power_base_raw", 2000000).put("target_network_contribution_raw", 1000000).put("target_pre_adjustment_total_raw", 3000000)
                .put("target_adjustment_delta_raw", 0).put("target_power_total_raw", 3000000).put("actual_power_ratio_raw", 150000); return q;
    }
    private static ObjectNode unsupported() {
        var n = StrictJson.object().put("schema_version", 1).put("status", "unsupported").put("war_id", 17).put("supported_slice", "claim_cb_claim_disposition").put("reason", "casus_belli_not_claim_cb");
        n.putObject("casus_belli").put("database_index", 91).put("canonical_key", "raiktor_claim_cb"); n.putObject("readiness").put("ready", false);
        n.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                .put("native_reader", "CWar+0x270/+0x290;0x2B9ECB0").put("present_claim_lifecycle", "present_only_vtable_slot_0_delete_flags_0")
                .put("claim_script_sha256", "887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4"); return n;
    }
    private RaiktorActualRecommendationFactory.ConfigurationSources configuration() throws Exception {
        return new RaiktorActualRecommendationFactory.ConfigurationSources(resource("raiktor_exit_budget_v1.json"), resource("raiktor_exit_utility_v1.json"), Optional.empty(), Optional.empty());
    }
    private RaiktorActualRecommendationFactory.FileRef resource(String name) throws Exception {
        byte[] raw;
        try (InputStream stream = getClass().getResourceAsStream("/g2/m0/raw-producers/" + name)) {
            assertNotNull(stream, "required original configuration source absent"); raw = stream.readNBytes(65537);
        }
        assertTrue(raw.length > 0 && raw.length <= 65536); Path target = directory.resolve(name); Files.write(target, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        return new RaiktorActualRecommendationFactory.FileRef(target, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
    private static void headers(com.sun.net.httpserver.HttpExchange exchange) {
        var h = exchange.getResponseHeaders(); h.set("Content-Type", "application/json; charset=utf-8"); h.set("X-Xar-Producer", G2Wire.PRODUCER);
        h.set("X-Xar-Producer-Version", G2Wire.PRODUCER_VERSION); h.set("X-Xar-Contract-Revision", G2Wire.REQUEST_SCHEMA);
    }
}
