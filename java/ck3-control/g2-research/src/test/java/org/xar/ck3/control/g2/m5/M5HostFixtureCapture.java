package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycleFixtures;

/** Captures host vectors by executing the actual G2 wire and M5 domain, never by inventing its result. */
public final class M5HostFixtureCapture {
    private static final String CORPUS_SHA = "7dd54e752495c5a1f7cacd19e7651758689e3052120d335e273b36650268177c";
    private M5HostFixtureCapture() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("original corpus, new output directory, actual machine ID, lifecycle fixture source required");
        Path corpus = Path.of(args[0]).toRealPath(), destination = Path.of(args[1]).toAbsolutePath();
        byte[] original = Files.readAllBytes(corpus);
        String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original));
        require(CORPUS_SHA.equals(hash), "the original producer corpus changed");
        Obj data;
        try (var gzip = new GZIPInputStream(Files.newInputStream(corpus))) {
            data = M5PayloadCodec.parseObject(gzip.readAllBytes(), "original producer corpus");
        }
        Obj intake = array(data.get("cases"), "original producer cases").stream()
                .map(value -> object(value, "original case"))
                .filter(value -> new Text("five-family-proposals-original-rank").equals(value.get("name")))
                .map(value -> object(value.get("input"), "original intake request")).findFirst().orElseThrow();
        M5PayloadCodec.Request context = new M5PayloadCodec.Request(intake, new M5Research.MissingPlan());
        G2Source source = new G2Source(args[2], Instant.now().toString(), "synthetic-original-producer-corpus-no-native-qualification",
                new ExactRef(corpus.toString(), original.length, hash));
        G2Request request = new G2Request("m5-original-producer-family-host01", Milestone.M5, source,
                ProjectionJson.object(M5PayloadCodec.encodeContextOperation(context), M5PayloadCodec.MAXIMUM_BYTES));
        byte[] requestBytes = G2Wire.encodeRequest(request);
        G2Response response = new M5Research().evaluate(G2Wire.decodeRequest(requestBytes));
        byte[] responseBytes = G2Wire.encodeResponse(response);
        G2Response readback = G2Wire.decodeResponse(responseBytes);
        M5Research.Result result = M5PayloadCodec.decodeResult(readback.result().bytes());
        require(array(result.intakeAnalysis().get("collected_candidate_ids"), "original candidates").size() == 5,
                "original fixed-five candidates were not consumed");
        require(!M5DecisionConsumer.consume(result).actionAuthorized(), "analytic capture acquired action authority");
        Obj badOperation = new Obj(Map.of("schema", new Text(M5PayloadCodec.OPERATION_SCHEMA),
                "operation", new Text("unsupported_submit"), "request", new Obj(Map.of())));
        G2Request rejected = new G2Request("m5-unknown-operation-host01", Milestone.M5, source,
                ProjectionJson.object(encode(badOperation), M5PayloadCodec.MAXIMUM_BYTES));
        boolean rejectedActually = false;
        try { new M5Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(rejected))); }
        catch (IllegalArgumentException expected) { rejectedActually = true; }
        require(rejectedActually, "unknown operation was not actually rejected");
        Files.createDirectories(destination);
        Files.write(destination.resolve("M5.request.json"), requestBytes, StandardOpenOption.CREATE_NEW);
        Files.write(destination.resolve("M5.expected-result.json"), response.result().bytes(), StandardOpenOption.CREATE_NEW);
        Files.write(destination.resolve("M5.actual-response.json"), responseBytes, StandardOpenOption.CREATE_NEW);
        Files.write(destination.resolve("M5.rejected-request.json"), G2Wire.encodeRequest(rejected), StandardOpenOption.CREATE_NEW);
        Path lifecycleFixture = Path.of(args[3]).toRealPath(); byte[] lifecycleSource = Files.readAllBytes(lifecycleFixture);
        G2Source lifecycle = new G2Source(args[2], Instant.now().toString(), "synthetic-lifecycle-fixture-no-native-qualification",
                new ExactRef(lifecycleFixture.toString(), lifecycleSource.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(lifecycleSource))));
        ObjectNode lifecycleInput = ProposalLifecycleFixtures.request();
        Obj proposed = lifecycle("M5.lifecycle-proposed", lifecycleInput, lifecycle, destination, "PROPOSED");
        String action = text(object(object(proposed.get("proposal"), "proposal").get("body"), "body").get("action_id"), "action id");
        String bodySha = text(object(proposed.get("proposal"), "proposal").get("body_sha256"), "body digest");
        ObjectNode unknown = lifecycleInput.deepCopy();
        ObjectNode fact = ProposalLifecycleFixtures.fact(action, bodySha, "UNKNOWN", "DOMAIN", "war", 7);
        fact.set("origin", ProposalLifecycleCodec.observation(ProposalLifecycleCodec.decode(
                ProposalLifecycleCodec.encodePayload(lifecycleInput), lifecycle).observed()));
        fact.set("original_evidence_ref", lifecycle.sourceRef().toJson());
        ((ArrayNode) unknown.get("external_facts")).add(fact);
        Obj unknownResult = lifecycle("M5.lifecycle-unknown", unknown, lifecycle, destination, "DEFERRED");
        require(new Text("EXISTING_UNKNOWN").equals(unknownResult.get("deferred_reason")), "UNKNOWN was not retained");
        ObjectNode conflicting = unknown.deepCopy();
        ((ObjectNode) conflicting.get("intents").get(0).get("expected").get("values").get(0)).put("value", false);
        lifecycle("M5.lifecycle-conflict", conflicting, lifecycle, destination, "BODY_CONFLICT");
        for (String name : List.of("M5.request.json", "M5.expected-result.json", "M5.actual-response.json", "M5.rejected-request.json")) {
            byte[] bytes = Files.readAllBytes(destination.resolve(name));
            System.out.println(name + " bytes=" + bytes.length + " sha256="
                    + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        }
        System.out.println("ACTUAL_G2_M5_WIRE_PRODUCER_CONSUMER_AND_SAVE_ROUNDTRIP_PASS; native_credit=0; game_calls=0");
    }

    private static Obj lifecycle(String name, ObjectNode inner, G2Source source, Path destination, String expectedStatus) throws Exception {
        Obj operation = new Obj(Map.of("schema", new Text(M5PayloadCodec.OPERATION_SCHEMA), "operation", new Text("proposal_lifecycle"),
                "request", M5PayloadCodec.parseObject(ProposalLifecycleCodec.encodePayload(inner), "lifecycle input")));
        G2Request request = new G2Request(name, Milestone.M5, source, ProjectionJson.object(encode(operation), M5PayloadCodec.MAXIMUM_BYTES));
        byte[] requestBytes = G2Wire.encodeRequest(request);
        G2Response response = new M5Research().evaluate(G2Wire.decodeRequest(requestBytes));
        G2Response saved = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        Obj result = M5PayloadCodec.parseObject(saved.result().bytes(), "actual lifecycle result");
        require(new Text(expectedStatus).equals(result.get("status")), "actual lifecycle status mismatch: " + name);
        require(new Bool(false).equals(result.get("formal_action_ready"))
                && new Bool(false).equals(result.get("resource_reservation_performed")), "lifecycle capture acquired action authority");
        Files.write(destination.resolve(name + ".request.json"), requestBytes, StandardOpenOption.CREATE_NEW);
        Files.write(destination.resolve(name + ".expected-result.json"), saved.result().bytes(), StandardOpenOption.CREATE_NEW);
        System.out.println(name + " ACTUAL_STATUS=" + expectedStatus + " request_bytes=" + requestBytes.length + " result_bytes=" + saved.result().size());
        return result;
    }
}
