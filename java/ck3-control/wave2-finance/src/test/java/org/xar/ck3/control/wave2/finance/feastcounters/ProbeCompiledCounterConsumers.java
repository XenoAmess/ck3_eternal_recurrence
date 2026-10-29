package org.xar.ck3.control.wave2.finance.feastcounters;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ServiceLoader;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;

/** Finite Java SPI regression helper; the former standalone packet executable is retired. */
public final class ProbeCompiledCounterConsumers {
    private static final ObjectMapper JSON = new ObjectMapper();
    private ProbeCompiledCounterConsumers() { }

    public record ValidationSummary(int producerCases, int accepted, int rejected, int consumerCases) { }

    static ValidationSummary verifyRegisteredProjections(JsonNode reference) throws IOException {
        if (reference == null || !reference.isObject()
                || !reference.path("schema").asText().equals("xar.feast-counter-producer-consumer-golden/v1")
                || !reference.path("producer_cases").isArray() || reference.get("producer_cases").size() != 25
                || !reference.path("projection_cases").isArray() || reference.get("projection_cases").size() != 9) {
            throw new IllegalArgumentException("qualified original counter producer/consumer golden required");
        }
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        for (ProjectionOperation operation : new ProjectionOperation[] {
                ProjectionOperation.FEAST_COUNTER_NORMALIZE, ProjectionOperation.FEAST_COUNTER_PROJECT}) {
            var profiles = dispatcher.profiles().stream().filter(profile -> profile.operation() == operation).toList();
            if (profiles.size() != 1 || profiles.getFirst().inputMaximumBytes() != OutcomeCounterCodec.MAX_BYTES
                    || profiles.getFirst().outputMaximumBytes() != OutcomeCounterCodec.MAX_BYTES) {
                throw new IllegalStateException("registered counter operation/profile missing or widened");
            }
        }
        int accepted = 0;
        int rejected = 0;
        for (JsonNode row : reference.get("producer_cases")) {
            byte[] input = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            var identity = new ProjectionCall.Identity("counter-native-" + (accepted + rejected), ProjectionOperation.FEAST_COUNTER_NORMALIZE);
            ProjectionResult result = dispatcher.dispatch(ProjectionWire.encodeCall(new ProjectionCall(identity,
                    ProjectionJson.object(input, OutcomeCounterCodec.MAX_BYTES))));
            if (row.get("accepted").booleanValue()) {
                if (!(result instanceof ProjectionResult.Succeeded success) || !success.identity().equals(identity)
                        || !JSON.readTree(success.result().bytes()).equals(row.get("result"))) {
                    throw new IllegalStateException("registered native counter producer differs from original oracle");
                }
                accepted++;
            } else {
                if (!(result instanceof ProjectionResult.Rejected failure)
                        || failure.error().code() != ProjectionError.Code.INVALID_PAYLOAD
                        || failure.identity().isEmpty() || !failure.identity().orElseThrow().equals(identity)) {
                    throw new IllegalStateException("registered native counter port accepted an original counterexample");
                }
                rejected++;
            }
        }
        int cases = 0;
        for (JsonNode row : reference.get("projection_cases")) {
            byte[] input = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            var identity = new ProjectionCall.Identity("counter-consumer-" + cases, ProjectionOperation.FEAST_COUNTER_PROJECT);
            ProjectionResult result = dispatcher.dispatch(ProjectionWire.encodeCall(new ProjectionCall(identity,
                    ProjectionJson.object(input, OutcomeCounterCodec.MAX_BYTES))));
            if (!(result instanceof ProjectionResult.Succeeded success) || !success.identity().equals(identity)) {
                throw new IllegalStateException("registered counter consumer projection rejected an original case");
            }
            JsonNode receipt = JSON.readTree(success.result().bytes());
            if (!receipt.isObject() || receipt.size() != 2
                    || !receipt.path("pre_outcome_values").equals(row.get("actual_start_seed"))
                    || !receipt.path("value_observation").equals(row.get("expected"))) {
                throw new IllegalStateException("registered counter port changed actual Start seed or lifecycle values");
            }
            cases++;
        }
        return new ValidationSummary(25, accepted, rejected, cases);
    }
}
