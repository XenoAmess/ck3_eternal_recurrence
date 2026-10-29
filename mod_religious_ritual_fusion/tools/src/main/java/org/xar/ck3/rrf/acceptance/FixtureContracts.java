package org.xar.ck3.rrf.acceptance;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigDecimal;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.rrf.Contracts;
import org.xar.ck3.rrf.ExpectedSelection;
import org.xar.ck3.rrf.ExpectedSelection.TenetKey;

/** Private acceptance inputs and the exact public prebuilt-fixture import contract. */
public final class FixtureContracts {
    private FixtureContracts() { }
    public static final String REQUEST_FILE = "_rrfa_request.json";
    public static final List<TenetKey> SOURCE_A = List.of(new TenetKey("tenet_esotericism"), new TenetKey("tenet_legalism"), new TenetKey("tenet_astrology"));
    public static final List<TenetKey> SOURCE_B = List.of(new TenetKey("tenet_esotericism"), new TenetKey("tenet_legalism"), new TenetKey("tenet_communal_identity"));
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
    @JsonSubTypes({@JsonSubTypes.Type(value = FreshSetup.class, name = "fresh"), @JsonSubTypes.Type(value = SavedSetup.class, name = "saved"),
            @JsonSubTypes.Type(value = SavedSnapshotSetup.class, name = "saved_snapshot"),
            @JsonSubTypes.Type(value = CompletedSnapshotSetup.class, name = "completed_snapshot")})
    public sealed interface Setup permits FreshSetup, SavedSetup, SavedSnapshotSetup, CompletedSnapshotSetup { }
    public record FreshSetup(int piety) implements Setup {
        public FreshSetup { if (piety < 0 || piety > 10000) throw new IllegalArgumentException("fixture piety must be 0..10000"); }
    }
    public record SavedSetup() implements Setup { }
    /** Canonical signed fixed-point wallet amount; JSON numbers and script fragments are never accepted. */
    public record PietyAmount(String value) {
        public PietyAmount {
            if (value == null || !value.matches("-?(?:0|[1-9][0-9]{0,6})(?:\\.[0-9]{0,4}[1-9])?") || value.equals("-0")
                    || new BigDecimal(value).abs().compareTo(BigDecimal.valueOf(1_000_000)) > 0)
                throw new IllegalArgumentException("canonical signed piety string with magnitude up to 1000000 required");
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING) public static PietyAmount fromJson(JsonNode node) {
            if (node == null || !node.isTextual()) throw new IllegalArgumentException("piety amount must be a canonical string");
            return new PietyAmount(node.textValue());
        }
        @JsonValue public String value() { return value; }
        public BigDecimal amount() { return new BigDecimal(value); }
    }
    public record CreationWalletHistory(PietyAmount before, PietyAmount after, int chargedCost,
                                        FilePin beforeInspection, FilePin afterInspection) {
        public CreationWalletHistory {
            Objects.requireNonNull(before); Objects.requireNonNull(after);
            Objects.requireNonNull(beforeInspection); Objects.requireNonNull(afterInspection);
            if (before.amount().signum() < 0 || after.amount().signum() < 0 || chargedCost <= 0
                    || before.amount().subtract(after.amount()).compareTo(BigDecimal.valueOf(chargedCost)) != 0)
                throw new IllegalArgumentException("creation before/after must prove the declared single charge");
        }
    }
    public interface SnapshotEvidence {
        org.xar.ck3.save.SaveContracts.NativeId actorId();
        FilePin sourceSave();
        FilePin sourceInspection();
        PietyAmount expectedCurrentPiety();
        CreationWalletHistory creationHistory();
    }
    /** Version 4 only: independently observed cold wallet, distinct from creation history. */
    public record SavedSnapshotSetup(org.xar.ck3.save.SaveContracts.NativeId actorId, FilePin sourceSave,
                                     FilePin sourceInspection, PietyAmount expectedCurrentPiety,
                                     CreationWalletHistory creationHistory) implements Setup, SnapshotEvidence {
        public SavedSnapshotSetup {
            Objects.requireNonNull(actorId); Objects.requireNonNull(sourceSave); Objects.requireNonNull(sourceInspection);
            Objects.requireNonNull(expectedCurrentPiety); Objects.requireNonNull(creationHistory);
        }
    }
    /** Version 5 explicitly observes both the completed Rite and its creation origin. */
    public record CompletedSnapshotSetup(org.xar.ck3.save.SaveContracts.NativeId actorId, FilePin sourceSave,
                                         FilePin sourceInspection, PietyAmount expectedCurrentPiety,
                                         CreationWalletHistory creationHistory) implements Setup, SnapshotEvidence {
        public CompletedSnapshotSetup {
            Objects.requireNonNull(actorId); Objects.requireNonNull(sourceSave); Objects.requireNonNull(sourceInspection);
            Objects.requireNonNull(expectedCurrentPiety); Objects.requireNonNull(creationHistory);
        }
    }
    public enum DivorceRule {
        ALLOWED("doctrine_divorce_allowed"), DISALLOWED("doctrine_divorce_disallowed");
        private final String doctrine;
        DivorceRule(String doctrine) { this.doctrine = doctrine; }
        public String doctrine() { return doctrine; }
        public DivorceRule opposite() { return this == ALLOWED ? DISALLOWED : ALLOWED; }
    }
    public record DivorceRules(DivorceRule result, DivorceRule origin) {
        public DivorceRules { Objects.requireNonNull(result); Objects.requireNonNull(origin); }
    }
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
    public record Request(int schemaVersion, CaseKind kind, Mode mode, ActorHistoryId actorHistoryId, Setup setup, ExpectedSelection expectedSelection) {
        public Request {
            if (schemaVersion != 3 && schemaVersion != 4 && schemaVersion != 5) throw new IllegalArgumentException("fixture request schemaVersion 3, 4 or 5 required");
            if (kind == null || mode == null || actorHistoryId == null || setup == null || expectedSelection == null) throw new IllegalArgumentException("fixture kind/mode/actorHistoryId/setup/expectedSelection required");
            expectedSelection.requireSources(SOURCE_A, SOURCE_B);
            if ((schemaVersion == 4) != (setup instanceof SavedSnapshotSetup)
                    || (schemaVersion == 5) != (setup instanceof CompletedSnapshotSetup))
                throw new IllegalArgumentException("version 4 requires saved_snapshot; version 5 requires completed_snapshot; version 3 retains its original setup contract");
            if ((kind == CaseKind.COLD_RELOAD) != (setup instanceof SavedSetup || setup instanceof SnapshotEvidence)) throw new IllegalArgumentException("cold_reload requires saved setup; fresh cases require fresh setup");
            if (setup instanceof SnapshotEvidence snapshot && snapshot.creationHistory().chargedCost() != mode.cost())
                throw new IllegalArgumentException("creation history charge differs from the selected mode");
            if (kind == CaseKind.CORE && setup instanceof FreshSetup fresh && fresh.piety() < mode.cost()) throw new IllegalArgumentException("positive core fixture must be able to pay its mode cost");
        }
    }
    public record FilePin(String path, long bytes, String sha256) {
        public FilePin { if (path == null || !Path.of(path).isAbsolute() || bytes < 0) throw new IllegalArgumentException("absolute file pin required"); Contracts.digest(sha256); }
    }
    public record FileContent(long bytes, String sha256) {
        public FileContent { if (bytes < 0) throw new IllegalArgumentException("negative file size"); Contracts.digest(sha256); }
    }
    public record PrebuiltInputs(String schema, FilePin manifest, FilePin request,
                                 @JsonProperty("input_pins") List<FilePin> inputPins) {
        public PrebuiltInputs {
            if (!"rrf-prebuilt-fixture-inputs-v1".equals(schema) || manifest == null || request == null)
                throw new IllegalArgumentException("strict prebuilt input receipt required");
            inputPins = List.copyOf(inputPins);
            if (inputPins.isEmpty() || inputPins.size() > 4) throw new IllegalArgumentException("bounded snapshot input pins required");
            Contracts.unique(inputPins.stream().map(FilePin::path).toList());
        }
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
