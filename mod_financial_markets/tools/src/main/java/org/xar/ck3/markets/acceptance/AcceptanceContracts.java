package org.xar.ck3.markets.acceptance;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/** Data only: the common acceptance entry owns runtime, allocation and Game. */
public final class AcceptanceContracts {
    private AcceptanceContracts() { }
    public record Request(int schemaVersion, String actorHistoryId) {
        public Request {
            require(schemaVersion == 1, "fixture schemaVersion must be 1");
            require(actorHistoryId != null && actorHistoryId.matches("[1-9][0-9]{0,9}"), "numeric history key string required");
        }
    }
    public record Pin(String path, long bytes, String sha256) {
        public Pin {
            require(path != null && Path.of(path).isAbsolute(), "absolute file pin required");
            require(bytes > 0 && sha256 != null && sha256.matches("[0-9a-f]{64}"), "nonempty exact file pin required");
        }
    }
    public record Content(long bytes, String sha256) { }
    public record Receipt(@JsonProperty("required_markers") List<String> requiredMarkers,
                          @JsonProperty("required_product_markers_minimum") Map<String, Integer> productMinima,
                          @JsonProperty("fixture_contains_business_effects") boolean containsBusinessEffects) {
        public Receipt { requiredMarkers = List.copyOf(requiredMarkers); productMinima = Map.copyOf(productMinima); }
    }
    public record Manifest(String schema, String product, @JsonProperty("case_id") String caseId,
                           @JsonProperty("machine_id") String machineId,
                           @JsonProperty("observed_at_utc") String observedAtUtc,
                           @JsonProperty("fixture_root") String fixtureRoot,
                           @JsonProperty("producer_source_pins") List<Pin> producerSources,
                           Map<String, Content> files, Receipt receipt) {
        public Manifest { producerSources = List.copyOf(producerSources); files = Map.copyOf(files); }
    }
    public record Emission(String fixture, Pin manifest, @JsonProperty("game_started") boolean gameStarted,
                           @JsonProperty("business_acceptance") String businessAcceptance) { }
    static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
