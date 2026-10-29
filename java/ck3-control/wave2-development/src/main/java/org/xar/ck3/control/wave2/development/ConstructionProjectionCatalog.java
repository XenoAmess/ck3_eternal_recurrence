package org.xar.ck3.control.wave2.development;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.development.ConstructionProjectionDispatcher.Operation;

/** In-process seven-leaf registration for the sole shared Quarkus projection endpoint. */
public final class ConstructionProjectionCatalog implements ProjectionPortCatalog {
    public ConstructionProjectionCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        return Arrays.stream(Operation.values()).map(Port::new).map(RegisteredProjection::of).toList();
    }

    /** An opaque, schema-bound transport payload; each existing leaf still performs its full field validation. */
    private record Input(Operation operation, ProjectionJson payload) {
        private Input {
            Objects.requireNonNull(operation); Objects.requireNonNull(payload);
            StrictJson.require(payload.isObject() && payload.size() <= operation.maximumRequestBytes(),
                    "construction input role budget required");
            JsonNode object = StrictJson.parse(payload.bytes(), operation.maximumRequestBytes());
            StrictJson.require(operation.requestSchema().equals(StrictJson.text(object.get("schema"))),
                    "construction input schema differs from registered operation");
        }
    }

    private record Output(Operation operation, ProjectionJson payload) {
        private Output {
            Objects.requireNonNull(operation); Objects.requireNonNull(payload);
            StrictJson.require(payload.size() <= operation.maximumResponseBytes(), "construction output role budget required");
        }
    }

    private static final class Port implements ProjectionPort<Input, Output> {
        private final Operation selected;
        private Port(Operation selected) { this.selected = Objects.requireNonNull(selected); }
        @Override public ProjectionOperation operation() {
            return switch (selected) {
                case INTENT -> ProjectionOperation.CONSTRUCTION_INTENT;
                case READBACK -> ProjectionOperation.CONSTRUCTION_READBACK;
                case INCOME -> ProjectionOperation.CONSTRUCTION_INCOME;
                case PROVINCE_INCOME -> ProjectionOperation.CONSTRUCTION_PROVINCE_INCOME;
                case SCENE -> ProjectionOperation.CONSTRUCTION_SCENE;
                case CLAN_CASH -> ProjectionOperation.CONSTRUCTION_CLAN_CASH;
                case VALUE_LOOKUP -> ProjectionOperation.CONSTRUCTION_VALUE_LOOKUP;
                case VALUE_SELECT -> ProjectionOperation.CONSTRUCTION_VALUE_SELECT;
                case VALUE_CONSUME -> ProjectionOperation.CONSTRUCTION_VALUE_CONSUME;
                case MODE3 -> ProjectionOperation.CONSTRUCTION_MODE3;
                case ECONOMY_OUTCOME -> ProjectionOperation.CONSTRUCTION_ECONOMY_OUTCOME;
                case ECONOMY_BUDGET -> ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET;
                case ECONOMY_PREPARE -> ProjectionOperation.CONSTRUCTION_ECONOMY_PREPARE;
                case ECONOMY_COMPLETED -> ProjectionOperation.CONSTRUCTION_ECONOMY_COMPLETED;
                case ECONOMY_QUOTE -> ProjectionOperation.CONSTRUCTION_ECONOMY_QUOTE;
                case ECONOMY_QUERY_OUTCOME -> ProjectionOperation.CONSTRUCTION_ECONOMY_QUERY_OUTCOME;
                case ECONOMY_ENRICH -> ProjectionOperation.CONSTRUCTION_ECONOMY_ENRICH;
            };
        }
        @Override public int inputMaximumBytes() { return selected.maximumRequestBytes(); }
        @Override public int outputMaximumBytes() { return selected.maximumResponseBytes(); }
        @Override public Input decode(byte[] rawPayload) {
            return new Input(selected, ProjectionJson.object(rawPayload, inputMaximumBytes()));
        }
        @Override public Output project(Input input) {
            StrictJson.require(input.operation() == selected, "construction decoded operation drift");
            // Forward original bytes; serializing the parsed payload here can turn 1.0 into integer 1.
            byte[] result = ConstructionProjectionDispatcher.project(selected, input.payload().bytes());
            return new Output(selected, ProjectionJson.value(result, outputMaximumBytes()));
        }
        @Override public byte[] encode(Output result) {
            StrictJson.require(result.operation() == selected, "construction encoded operation drift");
            return result.payload().bytes();
        }
    }
}
