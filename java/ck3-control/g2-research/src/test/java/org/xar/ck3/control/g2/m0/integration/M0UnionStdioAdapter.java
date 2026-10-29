package org.xar.ck3.control.g2.m0.integration;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m0.M0Research;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;

/** Software-test transport through the existing single M0Research dispatcher, including source producers. */
public final class M0UnionStdioAdapter {
    private M0UnionStdioAdapter() { }
    public static void main(String[] args) throws IOException {
        if (args.length != 1 || !args[0].equals("--stdio")) throw new IllegalArgumentException("finite --stdio test transport required");
        M0FixtureConfig config = M0FixtureConfig.fromEnvironment();
        ObjectNode row = StrictJson.object(StrictJson.parse(Files.readAllBytes(Path.of(config.httpSourceMetadata().path()))),
                Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        G2Source source = new G2Source(StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("observed_at_utc")),
                StrictJson.text(row.get("exact_build")), ExactRef.fromJson(row.get("source_ref")));
        G2ResearchEngine engine = new G2ResearchEngine(List.<G2Domain>of(new M0Research()));
        byte[] raw;
        int calls = 0;
        while ((raw = readLine()) != null) {
            if (++calls > 1024) throw new IllegalArgumentException("finite M0 source-producer call count exceeded");
            G2Request request = new G2Request("m0-union-test-" + UUID.randomUUID(), Milestone.M0, source,
                    ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
            byte[] result;
                G2Request decoded = G2Wire.decodeRequest(G2Wire.encodeRequest(request));
                if (!decoded.requestId().equals(request.requestId()) || decoded.milestone() != request.milestone()
                        || !decoded.source().equals(request.source())
                        || !RaiktorExitObservationCodec.parseWire(raw).equals(RaiktorExitObservationCodec.parseWire(decoded.payload().bytes())))
                    throw new IllegalStateException("M0 request wire identity or JSON type drift");
                G2Response response;
                try { response = engine.evaluate(decoded); }
                catch (IllegalArgumentException failure) {
                    if (failure instanceof G2Exception typed && typed.code() != G2HttpError.Code.DOMAIN_REJECTED) throw failure;
                    result = StrictJson.canonical(StrictJson.object().put("rejected", true).put("message", failure.getMessage()), 8192);
                    System.out.write(result); System.out.write('\n'); System.out.flush();
                    continue;
                }
                G2Response restored = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
                if (!restored.requestId().equals(request.requestId()) || restored.milestone() != request.milestone()
                        || !restored.source().equals(request.source())
                        || !RaiktorExitObservationCodec.parseWire(response.result().bytes()).equals(RaiktorExitObservationCodec.parseWire(restored.result().bytes())))
                    throw new IllegalStateException("M0 response wire identity or JSON type drift");
                result = restored.result().bytes();
            System.out.write(result); System.out.write('\n'); System.out.flush();
        }
        config.verify();
    }
    private static byte[] readLine() throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        for (int value; (value = System.in.read()) != -1;) {
            if (value == '\n') return line.toByteArray();
            if (line.size() >= ProjectionJson.MAX_BYTES) throw new IllegalArgumentException("finite M0 semantic input required");
            line.write(value);
        }
        return line.size() == 0 ? null : line.toByteArray();
    }
}
