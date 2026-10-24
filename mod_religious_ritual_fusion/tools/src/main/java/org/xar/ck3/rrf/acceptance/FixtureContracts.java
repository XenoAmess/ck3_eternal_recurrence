package org.xar.ck3.rrf.acceptance;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.xar.ck3.rrf.Contracts;

/** Private acceptance inputs and the exact public prebuilt-fixture import contract. */
public final class FixtureContracts {
    private FixtureContracts() { }
    public enum CaseKind {
        CORE("core"), UI_REJECTION("ui_rejection"), COLD_RELOAD("cold_reload");
        private final String wire;
        CaseKind(String wire) { this.wire = wire; }
        @JsonValue public String wire() { return wire; }
    }
    public enum Mode {
        RITE("rite", 500), FAITH("faith", 1000);
        private final String wire; private final int cost;
        Mode(String wire, int cost) { this.wire = wire; this.cost = cost; }
        @JsonValue public String wire() { return wire; }
        public int cost() { return cost; }
    }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = FreshSetup.class, name = "fresh"), @JsonSubTypes.Type(value = SavedSetup.class, name = "saved")})
    public sealed interface Setup permits FreshSetup, SavedSetup { }
    public record FreshSetup(int piety) implements Setup {
        public FreshSetup { if (piety < 0 || piety > 10000) throw new IllegalArgumentException("fixture piety must be 0..10000"); }
    }
    public record SavedSetup() implements Setup { }
    /** A CK3 character: script link uses a history definition key, not a native runtime handle. */
    public record ActorHistoryId(String value) {
        public ActorHistoryId {
            if (!"1128".equals(value)) throw new IllegalArgumentException("fixture requires Robert's history definition key 1128");
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ActorHistoryId fromJson(JsonNode input) {
            if (input == null || !input.isTextual()) throw new IllegalArgumentException("actorHistoryId must be a canonical history-key string");
            return new ActorHistoryId(input.textValue());
        }
        @JsonValue public String value() { return value; }
    }
    public record Request(int schemaVersion, CaseKind kind, Mode mode, ActorHistoryId actorHistoryId, Setup setup) {
        public Request {
            if (schemaVersion != 2) throw new IllegalArgumentException("fixture request schemaVersion 2 required");
            if (kind == null || mode == null || actorHistoryId == null || setup == null) throw new IllegalArgumentException("fixture kind/mode/actorHistoryId/setup required");
            if ((kind == CaseKind.COLD_RELOAD) != (setup instanceof SavedSetup)) throw new IllegalArgumentException("cold_reload requires saved setup; fresh cases require fresh setup");
            if (kind == CaseKind.CORE && setup instanceof FreshSetup fresh && fresh.piety() < mode.cost()) throw new IllegalArgumentException("positive core fixture must be able to pay its mode cost");
        }
    }
    public record FilePin(String path, long bytes, String sha256) {
        public FilePin { if (path == null || !Path.of(path).isAbsolute() || bytes < 0) throw new IllegalArgumentException("absolute file pin required"); Contracts.digest(sha256); }
    }
    public record FileContent(long bytes, String sha256) {
        public FileContent { if (bytes < 0) throw new IllegalArgumentException("negative file size"); Contracts.digest(sha256); }
    }
    public record Receipt(@JsonProperty("required_markers") List<String> requiredMarkers,
                          @JsonProperty("required_product_markers_minimum") Map<String, Integer> minimumMarkers,
                          @JsonProperty("fixture_contains_business_effects") boolean containsBusinessEffects) {
        public Receipt {
            requiredMarkers = List.copyOf(requiredMarkers); Contracts.unique(requiredMarkers); minimumMarkers = Map.copyOf(minimumMarkers);
            if (requiredMarkers.isEmpty() || requiredMarkers.stream().anyMatch(String::isBlank) || minimumMarkers.values().stream().anyMatch(v -> v <= 0)) throw new IllegalArgumentException("invalid fixture marker receipt");
        }
    }
    public record Manifest(String schema, String product, @JsonProperty("case_id") String caseId,
                           @JsonProperty("machine_id") String machineId, @JsonProperty("observed_at_utc") String observedAtUtc,
                           @JsonProperty("fixture_root") String fixtureRoot, @JsonProperty("producer_source_pins") List<FilePin> producerSourcePins,
                           Map<String, FileContent> files, Receipt receipt) {
        public Manifest {
            if (!schema.equals("ck3-mod-acceptance-prebuilt-fixture-v1") || !product.equals("religious-ritual-fusion")) throw new IllegalArgumentException("fixture schema/product mismatch");
            if (java.util.Arrays.stream(CaseKind.values()).noneMatch(k -> k.wire().equals(caseId))) throw new IllegalArgumentException("unknown fixture case");
            machine(machineId); Instant.parse(observedAtUtc);
            if (!Path.of(fixtureRoot).isAbsolute()) throw new IllegalArgumentException("absolute fixture root required");
            producerSourcePins = List.copyOf(producerSourcePins); files = java.util.Collections.unmodifiableMap(new java.util.LinkedHashMap<>(files));
            Contracts.unique(producerSourcePins.stream().map(FilePin::path).toList());
            if (producerSourcePins.isEmpty() || producerSourcePins.size() > 64 || files.isEmpty() || !files.containsKey("descriptor.mod") || receipt == null) throw new IllegalArgumentException("incomplete fixture closure");
            files.keySet().forEach(Contracts::safePath);
        }
    }
    public static void machine(String id) { if (id == null || !id.matches("[a-z0-9][a-z0-9-]{2,95}")) throw new IllegalArgumentException("observed stable machine ID required"); }
}
