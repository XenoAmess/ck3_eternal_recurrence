package org.xar.ck3.control.governance.crownauthority;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.ServiceLoader;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;

/** Shared regression assertions, also executable by the finite uniform javac runner. */
public final class CrownAuthorityProjectionChecks {
    private CrownAuthorityProjectionChecks() { }

    public static int golden(JsonNode fixture) {
        int count = 0;
        var dispatcher = ProjectionDispatcher.fromCatalogs(List.of(new CrownAuthorityProjectionCatalog()));
        require(fixture.get("cases").size() == 20, "all twenty original producer cases required");
        for (JsonNode vector : fixture.get("cases")) {
            byte[] payload = StrictJson.canonical(vector.get("input"));
            ProjectionResult result = dispatcher.dispatch(envelope(payload, "crown-golden-" + count));
            require(result instanceof ProjectionResult.Succeeded, "producer vector rejected: " + vector.get("name"));
            var succeeded = (ProjectionResult.Succeeded) result;
            require(Arrays.equals(StrictJson.canonical(vector.get("expected")), succeeded.result().bytes()),
                    "complete original producer JSON differs: " + vector.get("name"));
            ProjectionResult roundtrip = ProjectionWire.decodeResult(ProjectionWire.encodeResult(result));
            require(roundtrip instanceof ProjectionResult.Succeeded &&
                    Arrays.equals(((ProjectionResult.Succeeded) roundtrip).result().bytes(), succeeded.result().bytes()),
                    "raw result changed across common transport roundtrip");
            count++;
        }
        return count;
    }

    public static int rawBoundaries(JsonNode fixture) {
        var dispatcher = ProjectionDispatcher.fromCatalogs(List.of(new CrownAuthorityProjectionCatalog()));
        String input = new String(StrictJson.canonical(fixture.get("cases").get(0).get("input")), StandardCharsets.UTF_8);
        int count = 0;
        for (String field : List.of("snapshot_revision", "native_snapshot_revision", "proof_epoch",
                "date_raw", "player_character_id", "queried_revision", "queried_native_revision")) {
            JsonNode original = fixture.get("cases").get(0).get("input").get("readback").get(field);
            String needle = "\"" + field + "\":" + original.bigIntegerValue();
            require(input.indexOf(needle) == input.lastIndexOf(needle) && input.contains(needle), "unique original integer site required");
            for (String token : List.of("true", "40.0", "\"40\"")) {
                String replacement = "\"" + field + "\":" + token;
                byte[] raw = input.replace(needle, replacement).getBytes(StandardCharsets.UTF_8);
                require(new String(raw, StandardCharsets.UTF_8).contains(replacement), "raw negative token was normalized before entry");
                rejected(dispatcher, raw, ProjectionError.Code.INVALID_PAYLOAD, "wrong-integer-" + count++);
            }
        }
        for (String payload : List.of(
                "{}",
                input.replace("\"reserves_raw\":{}", "\"reserves_raw\":null"),
                input.replace("\"reserves_raw\":{}", "\"reserves_raw\":{},\"reserves_raw\":{}"),
                input.replace("\"reserves_raw\":{}", "\"renamed_reserves\":{}"))) {
            require(!payload.equals(input), "negative field mutation must change exact request bytes");
            ProjectionError.Code expected = payload.contains("\"reserves_raw\":{},\"reserves_raw\":{}")
                    ? ProjectionError.Code.INVALID_ENVELOPE : ProjectionError.Code.INVALID_PAYLOAD;
            rejected(dispatcher, payload.getBytes(StandardCharsets.UTF_8), expected, "wrong-field-" + count++);
        }
        return count;
    }

    public static int discovery() {
        long matches = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type().equals(CrownAuthorityProjectionCatalog.class)).count();
        require(matches == 1, "the packaged governance provider must be discovered exactly once");
        var ports = new CrownAuthorityProjectionCatalog().registrations();
        require(ports.size() == 1 && ports.get(0).operation() == ProjectionOperation.GOVERNANCE_CROWN_CHOOSE,
                "Crown catalog registers exactly its declared one operation");
        require(ports.get(0).inputMaximumBytes() == 65_536 && ports.get(0).outputMaximumBytes() == 65_536,
                "Crown role profile changed");
        return 3;
    }

    private static byte[] envelope(byte[] payload, String requestId) {
        String prefix = "{\"schema\":\"" + ProjectionCall.SCHEMA
                + "\",\"schema_version\":1,\"request_id\":\"" + requestId
                + "\",\"operation\":\"governance-crown-choose\",\"payload\":";
        byte[] first = prefix.getBytes(StandardCharsets.UTF_8);
        byte[] result = Arrays.copyOf(first, first.length + payload.length + 1);
        System.arraycopy(payload, 0, result, first.length, payload.length);
        result[result.length - 1] = '}';
        return result;
    }

    private static void rejected(ProjectionDispatcher dispatcher, byte[] payload, ProjectionError.Code code, String id) {
        ProjectionResult result = dispatcher.dispatch(envelope(payload, id));
        require(result instanceof ProjectionResult.Rejected, "wrong-token input unexpectedly succeeded");
        require(((ProjectionResult.Rejected) result).error().code() == code, "wrong rejection boundary: " + result);
    }

    private static void require(boolean condition, String reason) {
        if (!condition) throw new IllegalStateException(reason);
    }

    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 1) throw new IllegalArgumentException("one exact retained producer golden path required");
        JsonNode fixture = StrictJson.parse(Files.readAllBytes(Path.of(arguments[0])));
        int vectors = golden(fixture), boundaries = rawBoundaries(fixture), discovery = discovery();
        System.out.println("{\"schema\":\"xar.crown-projection-checks/v1\",\"golden_vectors\":" + vectors
                + ",\"raw_boundary_cases\":" + boundaries + ",\"discovery_checks\":" + discovery
                + ",\"passed\":true,\"skipped\":0}");
    }
}
