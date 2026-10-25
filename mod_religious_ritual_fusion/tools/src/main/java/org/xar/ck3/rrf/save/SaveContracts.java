package org.xar.ck3.rrf.save;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.xar.ck3.rrf.Contracts;
import org.xar.ck3.rrf.ExpectedSelection;

/** Versioned offline evidence. Native identities and resource lexemes never pass through floating point. */
public final class SaveContracts {
    private SaveContracts() { }
    public record NativeId(String value) {
        public NativeId {
            if (value == null || !value.matches("0|[1-9][0-9]{0,19}") || new BigInteger(value).bitLength() > 64) throw new IllegalArgumentException("canonical unsigned native ID string required");
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING) public static NativeId fromJson(JsonNode node) {
            if (node == null || !node.isTextual()) throw new IllegalArgumentException("native ID must be a string");
            return new NativeId(node.textValue());
        }
        @JsonValue public String value() { return value; }
    }
    public record Pin(String path, long bytes, String sha256) {
        public Pin {
            if (path == null || !Path.of(path).isAbsolute() || bytes < 0) throw new IllegalArgumentException("absolute input pin required");
            Contracts.digest(sha256);
        }
    }
    public record Layout(List<String> actorTable, List<String> riteTable, List<String> faithTable, List<String> religionTable) {
        public Layout {
            actorTable = checkedPath(actorTable); riteTable = checkedPath(riteTable); faithTable = checkedPath(faithTable); religionTable = checkedPath(religionTable);
            Contracts.unique(List.of(String.join("/", actorTable), String.join("/", riteTable), String.join("/", faithTable), String.join("/", religionTable)));
        }
    }
    public record Selection(NativeId actorId, List<NativeId> riteIds, List<NativeId> faithIds, List<NativeId> religionIds) {
        public Selection {
            if (actorId == null || actorId.value().equals("0")) throw new IllegalArgumentException("nonzero runtime actor ID required");
            riteIds = checkedIds(riteIds); faithIds = checkedIds(faithIds); religionIds = checkedIds(religionIds);
        }
    }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = InspectOnly.class, name = "inspect_only"), @JsonSubTypes.Type(value = FusionSelection.class, name = "fusion_selection")})
    public sealed interface Expectation permits InspectOnly, FusionSelection { }
    public record InspectOnly() implements Expectation { }
    public record FusionSelection(Pin fixtureManifest, Pin preparedProfileInventory, NativeId resultRiteId) implements Expectation {
        public FusionSelection { if (fixtureManifest == null || preparedProfileInventory == null || resultRiteId == null) throw new IllegalArgumentException("pinned fixture, public prepared inventory and actual result Rite required"); }
    }
    public record Request(int schemaVersion, String machineId, String repository, Pin save, Pin decoder, Layout layout, Selection selection, Expectation expectation) {
        public Request {
            if (schemaVersion != 2) throw new IllegalArgumentException("save inspection request schemaVersion 2 required");
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}") || repository == null || !Path.of(repository).isAbsolute() || save == null || decoder == null || layout == null || selection == null || expectation == null) throw new IllegalArgumentException("complete pinned save inspection request and explicit expectation required");
            if (expectation instanceof FusionSelection fusion && !selection.riteIds().contains(fusion.resultRiteId())) throw new IllegalArgumentException("actual fusion result Rite must be selected for complete AST inspection");
        }
    }
    public enum ScopeKind { METADATA, ACTOR, RITE, FAITH, RELIGION }
    public enum Coverage { FULL_RECORD, DIRECT_SCALARS }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = Atom.class, name = "atom"), @JsonSubTypes.Type(value = Block.class, name = "block")})
    public sealed interface Value permits Atom, Block { }
    public record Atom(String raw) implements Value {
        public Atom { if (raw == null || raw.isEmpty()) throw new IllegalArgumentException("empty saved atom"); }
    }
    public record Entry(String key, String operator, Value value) {
        public Entry { if (key == null || operator == null || value == null) throw new IllegalArgumentException("incomplete AST entry"); }
    }
    public record Block(List<Entry> entries) implements Value { public Block { entries = List.copyOf(entries); } }
    public record Scope(ScopeKind kind, Coverage coverage, List<String> path, String canonicalTokenSha256, Block ast) {
        public Scope { path = List.copyOf(path); Contracts.digest(canonicalTokenSha256); if (kind == null || coverage == null || ast == null) throw new IllegalArgumentException("complete saved scope required"); }
    }
    public record Inventory(ScopeKind kind, List<String> path, List<NativeId> ids) {
        public Inventory { path = List.copyOf(path); ids = List.copyOf(ids); Contracts.unique(ids.stream().map(NativeId::value).toList()); }
    }
    public record StreamEvidence(String sha256, String bytes, String tokens, String selectedTokenBytes, List<String> rootKeys, List<Entry> rootScalars) {
        public StreamEvidence { Contracts.digest(sha256); rootKeys = List.copyOf(rootKeys); rootScalars = List.copyOf(rootScalars); }
    }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = NotAssessed.class, name = "not_assessed"), @JsonSubTypes.Type(value = SelectionVerified.class, name = "fixture_bound_selection_verified")})
    public sealed interface Assessment permits NotAssessed, SelectionVerified { }
    public record NotAssessed() implements Assessment { }
    /** Only saved exact core/origin selection and both source contributions; no GUI, charge or reload claim. */
    public record SelectionVerified(Pin fixtureManifest, Pin fixtureRequest, Pin preparedProfileInventory,
                                    Pin preparedFixtureRequest, Pin preparedCaseContract, ExpectedSelection expectedSelection,
                                    NativeId resultRiteId, NativeId sourceARiteId, NativeId sourceBRiteId) implements Assessment {
        public SelectionVerified {
            if (fixtureManifest == null || fixtureRequest == null || preparedProfileInventory == null || preparedFixtureRequest == null || preparedCaseContract == null || expectedSelection == null || resultRiteId == null || sourceARiteId == null || sourceBRiteId == null) throw new IllegalArgumentException("complete fixture-bound selection evidence required");
        }
    }
    public record Report(String schema, String machineId, String observedAtUtc, Request request, int decoderExitCode,
                         String decoderStderr, StreamEvidence stream, List<Inventory> inventories, List<Scope> scopes,
                         List<Pin> producerSources, boolean saveUnchanged, boolean gameStarted, Assessment assessment) {
        public Report {
            if (!"rrf-save-inspection-v2".equals(schema) || decoderExitCode != 0 || !saveUnchanged || gameStarted || assessment == null) throw new IllegalArgumentException("incomplete offline evidence");
            if ((request.expectation() instanceof FusionSelection) != (assessment instanceof SelectionVerified)) throw new IllegalArgumentException("saved selection expectation/assessment branch mismatch");
            if (request.expectation() instanceof FusionSelection expected && assessment instanceof SelectionVerified verified
                    && (!expected.fixtureManifest().equals(verified.fixtureManifest()) || !expected.preparedProfileInventory().equals(verified.preparedProfileInventory()) || !expected.resultRiteId().equals(verified.resultRiteId()))) throw new IllegalArgumentException("saved selection expectation/assessment identity mismatch");
            Instant.parse(observedAtUtc); inventories = List.copyOf(inventories); scopes = List.copyOf(scopes); producerSources = List.copyOf(producerSources);
        }
    }
    private static List<String> checkedPath(List<String> path) {
        List<String> result = List.copyOf(path);
        if (result.isEmpty() || result.size() > 4 || result.stream().anyMatch(p -> !p.matches("[A-Za-z_][A-Za-z0-9_]*"))) throw new IllegalArgumentException("explicit save table path required");
        return result;
    }
    private static List<NativeId> checkedIds(List<NativeId> ids) {
        List<NativeId> result = List.copyOf(ids); if (result.size() > 128) throw new IllegalArgumentException("selected ID cap exceeded");
        Contracts.unique(result.stream().map(NativeId::value).toList()); return result;
    }
}
