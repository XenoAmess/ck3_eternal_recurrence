package org.xar.ck3.control.g2.m1;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.EnumSet;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;

/** Finite eight-operation fixture exporter; production and every typed consumer run before publication. */
public final class M1HttpFixtureExporter {
    private M1HttpFixtureExporter() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 2) { throw new IllegalArgumentException("output-directory actual-machine-id required"); }
        export(Path.of(args[0]), args[1]);
    }

    public static Path export(Path outputDirectory, String executionMachineId) throws IOException {
        StrictJson.require(executionMachineId != null && executionMachineId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"),
                "explicit actual execution machine required");
        Path output = outputDirectory.toAbsolutePath().normalize();
        Files.createDirectories(output);
        List<M1FixtureCases.Fixture> fixtures = M1FixtureCases.all();
        EnumSet<M1Operation> exported = EnumSet.noneOf(M1Operation.class);
        ObjectNode index = StrictJson.object();
        index.put("schema", "xar.g2-m1.http-fixture-export/v2");
        index.put("execution_machine_id", executionMachineId); index.put("observed_at_utc", Instant.now().toString());
        index.put("actual_http_executed", false); index.put("native_game_rpc_count", 0);
        index.put("status", "EIGHT_PRODUCER_CONSUMER_FIXTURES_EXPORTED_NOT_HTTP_QUALIFIED");
        index.put("source_boundary", "original producer synthetic DTO captures; pure producer pins grant no current Native/EXE authority");
        var operations = index.putArray("operations");
        for (M1FixtureCases.Fixture fixture : fixtures) {
            StrictJson.require(exported.add(fixture.operation()), "duplicate M1 operation export");
            G2Request request = fixture.request(); byte[] wire = G2Wire.encodeRequest(request);
            G2Response response = new M1Research().evaluate(G2Wire.decodeRequest(wire));
            byte[] result = response.result().bytes();
            StrictJson.require(StrictJson.parse(result, M1ResultConsumers.MAX_BYTES)
                    .equals(StrictJson.parse(fixture.expected().bytes(), M1ResultConsumers.MAX_BYTES)),
                    "actual M1 producer output differs from original case: " + fixture.operation().wire());
            M1FixtureCases.consume(fixture.operation(), result);
            G2Response restored = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
            StrictJson.require(java.util.Arrays.equals(result, restored.result().bytes())
                    && request.source().equals(restored.source()) && request.requestId().equals(restored.requestId()),
                    "M1 persisted wire identity changed");
            String prefix = "M1." + fixture.operation().wire();
            Path requestPath = write(output, prefix + ".request.json", wire);
            Path expectedPath = write(output, prefix + ".expected-result.json", result);
            ObjectNode row = operations.addObject(); row.put("operation", fixture.operation().wire());
            row.set("request", reference(requestPath)); row.set("expected_result", reference(expectedPath));
            if (fixture.operation() == M1Operation.REALM_FEEDBACK) {
                // Existing all-milestone host test selects one representative M1 fixture.
                index.set("request", reference(write(output, "M1.request.json", wire)));
                index.set("expected_result", reference(write(output, "M1.expected-result.json", result)));
                G2Request rejected = new G2Request("m1-fixture-rejected", request.milestone(), request.source(),
                        ProjectionJson.object("{\"operation\":\"unsupported-operation\",\"input\":{}}".getBytes(java.nio.charset.StandardCharsets.UTF_8), M1Research.MAX_BYTES));
                try {
                    new M1Research().evaluate(rejected);
                    throw new IOException("unsupported M1 operation unexpectedly accepted");
                } catch (IllegalArgumentException expected) {
                    index.put("rejected_exception_type", expected.getClass().getName());
                }
                index.set("rejected_request", reference(write(output, "M1.rejected-request.json", G2Wire.encodeRequest(rejected))));
                G2HttpError error = new G2HttpError(G2HttpError.SCHEMA, G2HttpError.Code.DOMAIN_REJECTED,
                        "domain input does not satisfy the selected milestone contract");
                index.put("expected_rejection_http_status", error.code().httpStatus());
                index.set("expected_http_error", reference(write(output, "M1.expected-http-error.json", G2Wire.encodeError(error))));
            }
        }
        StrictJson.require(exported.equals(EnumSet.allOf(M1Operation.class)), "all eight M1 operation adapters required");
        return write(output, "M1.fixture-index.json", StrictJson.canonical(index, M1ResultConsumers.MAX_BYTES));
    }
    private static Path write(Path output, String name, byte[] raw) throws IOException {
        Path path = output.resolve(name); Files.write(path, raw, StandardOpenOption.CREATE_NEW); return path;
    }
    private static ObjectNode reference(Path path) throws IOException {
        byte[] raw = Files.readAllBytes(path); ObjectNode ref = StrictJson.object();
        ref.put("path", path.toString()); ref.put("bytes", raw.length); ref.put("sha256", M1FixtureCases.sha256(raw)); return ref;
    }
}
