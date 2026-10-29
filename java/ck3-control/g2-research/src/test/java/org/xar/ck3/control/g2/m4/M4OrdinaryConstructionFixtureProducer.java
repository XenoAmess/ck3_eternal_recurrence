package org.xar.ck3.control.g2.m4;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;

/** Exports actual pure-domain request/result bytes for the existing single host's HTTP test. */
public final class M4OrdinaryConstructionFixtureProducer {
    private M4OrdinaryConstructionFixtureProducer() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("exact retained wartime31 corpus and new output directory required");
        Path corpus = Path.of(args[0]), output = Path.of(args[1]);
        byte[] compressed = Files.readAllBytes(corpus); String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed));
        StrictJson.require(compressed.length == 6379 && sha.equals("4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585"), "exact original wartime31 corpus required");
        JsonNode original;
        try (GZIPInputStream input = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
            byte[] expanded = input.readNBytes(524_289); StrictJson.require(expanded.length <= 524_288, "bounded original corpus required");
            original = StrictJson.parse(expanded, 524_288);
        }
        String machine = System.getenv("XAR_MACHINE_ID");
        StrictJson.require(machine != null && machine.equals(original.path("machine_id").textValue()), "current verified machine ID required");
        Files.createDirectory(output);
        G2Source source = new G2Source(machine, Instant.now().toString(), "synthetic-original31-corpus-not-live", new ExactRef(corpus.toAbsolutePath().toString(), compressed.length, sha));
        for (String name : new String[]{"exact_ample_threshold", "market_unavailable"}) {
            JsonNode row = named(original, name); ObjectNode request = StrictJson.object();
            request.put("schema", OrdinaryWartimeConstructionCodec.SCHEMA); request.put("stage", "BEFORE_OPTIONAL_QUERY");
            request.put("original_selected_step", "life-advance"); request.putNull("original_phase"); request.put("opportunity", "ORDINARY_ADVANCE");
            request.set("cash_input", row.get("request")); request.putNull("quoted_outlay"); request.putNull("financing_request");
            byte[] domain = StrictJson.canonical(request, OrdinaryWartimeConstructionCodec.MAX_BYTES);
            G2Request produced = new G2Request("m4-ordinary-http-" + name, Milestone.M4, source, ProjectionJson.object(domain, OrdinaryWartimeConstructionCodec.MAX_BYTES));
            var response = new M4Research().evaluate(produced);
            OrdinaryWartimeConstructionCodec.verifyResponse(domain, response.result().bytes());
            Files.write(output.resolve(name + "-request.json"), G2Wire.encodeRequest(produced), StandardOpenOption.CREATE_NEW);
            Files.write(output.resolve(name + "-response.json"), G2Wire.encodeResponse(response), StandardOpenOption.CREATE_NEW);
        }
        System.out.println("actual M4 ordinary producer exported 2 request/result pairs; 0 Game/native/ledger operations");
    }
    private static JsonNode named(JsonNode corpus, String name) throws IOException {
        for (JsonNode row : corpus.get("cases")) if (name.equals(row.get("name").textValue())) return row;
        throw new IOException("required original vector missing: " + name);
    }
}
