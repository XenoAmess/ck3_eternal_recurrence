package org.xar.ck3.control.wave2.finance.feastterminal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.ServiceLoader;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;

/** Pure Java catalog regression helper. Former standalone executable and wire-packet path are retired. */
public final class ProbeCompiledTerminalConsumers {
    static final int CASE_COUNT = 48;
    private static final ObjectMapper JSON = new ObjectMapper();
    private ProbeCompiledTerminalConsumers() { }

    public record ValidationSummary(int cases, int accepted, int rejected) { }

    /** Real ServiceLoader catalog to registered typed port and actual codec/policy; no process launch. */
    static ValidationSummary verifyRegisteredProjection(JsonNode reference) throws IOException {
        if (reference == null || !reference.isObject()
                || !reference.path("schema").asText().equals("xar.feast-terminal-producer-golden/v1")
                || !reference.path("cases").isArray() || reference.get("cases").size() != CASE_COUNT) {
            throw new IllegalArgumentException("qualified original terminal golden required");
        }
        Set<String> names = new HashSet<>();
        for (JsonNode row : reference.get("cases")) {
            if (!row.path("name").isTextual() || row.get("name").textValue().isEmpty()
                    || !names.add(row.get("name").textValue()) || !row.path("input_json").isTextual()
                    || !row.path("accepted").isBoolean()) {
                throw new IllegalArgumentException("invalid or duplicate original terminal case");
            }
        }
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        var profiles = dispatcher.profiles().stream()
                .filter(profile -> profile.operation() == ProjectionOperation.FEAST_TERMINAL_NORMALIZE).toList();
        if (profiles.size() != 1 || profiles.getFirst().inputMaximumBytes() != FeastTerminalCodec.MAX_INPUT_BYTES
                || profiles.getFirst().outputMaximumBytes() != FeastTerminalCodec.MAX_OUTPUT_BYTES) {
            throw new IllegalStateException("actual terminal catalog/profile missing or widened");
        }
        int accepted = 0;
        int rejected = 0;
        for (JsonNode row : reference.get("cases")) {
            byte[] input = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            var identity = new ProjectionCall.Identity("terminal-catalog-" + (accepted + rejected),
                    ProjectionOperation.FEAST_TERMINAL_NORMALIZE);
            byte[] envelope = ProjectionWire.encodeCall(new ProjectionCall(identity,
                    ProjectionJson.object(input, FeastTerminalCodec.MAX_INPUT_BYTES)));
            ProjectionResult result = dispatcher.dispatch(envelope);
            if (row.get("accepted").booleanValue()) {
                if (!(result instanceof ProjectionResult.Succeeded succeeded)
                        || !succeeded.identity().equals(identity)
                        || !JSON.readTree(succeeded.result().bytes()).equals(row.get("result"))) {
                    throw new IllegalStateException("registered terminal port differs from actual original producer");
                }
                accepted++;
            } else {
                if (!(result instanceof ProjectionResult.Rejected invalid)
                        || invalid.error().code() != ProjectionError.Code.INVALID_PAYLOAD
                        || invalid.identity().isEmpty() || !invalid.identity().orElseThrow().equals(identity)) {
                    throw new IllegalStateException("registered terminal codec did not reject the actual original counterexample");
                }
                rejected++;
            }
        }
        return new ValidationSummary(CASE_COUNT, accepted, rejected);
    }
}
