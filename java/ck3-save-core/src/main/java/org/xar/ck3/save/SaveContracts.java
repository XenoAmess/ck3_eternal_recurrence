package org.xar.ck3.save;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Product-independent selection. Every table/projection path is supplied, never inferred. */
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
            if (path == null || !Path.of(path).isAbsolute() || bytes < 0) throw new IllegalArgumentException("absolute file pin required");
            digest(sha256);
        }
    }
    public enum ScopeKind { METADATA, ACTOR, RITE, FAITH, RELIGION, DYNASTY, HOUSE, COAT_OF_ARMS, TITLE }
    public enum Coverage { FULL_RECORD, DIRECT_SCALARS }
    public enum Availability { UNKNOWN_LAYOUT, TABLE_NOT_FOUND, OBSERVED }
    public enum RecordStatus { UNKNOWN_TABLE, NOT_FOUND, FULL_RECORD }
    public enum ProjectionKind { GLOBAL_VARIABLES, SCHEDULED_EVENTS, OTHER }
    public record TableSelection(ScopeKind kind, List<String> path, List<NativeId> ids, boolean required) {
        public TableSelection {
            if (kind == null || kind == ScopeKind.METADATA) throw new IllegalArgumentException("native table kind required");
            path = checkedPath(path); ids = List.copyOf(ids);
            if (ids.size() > 128 || new HashSet<>(ids).size() != ids.size()) throw new IllegalArgumentException("unique bounded selected IDs required");
        }
    }
    public record ProjectionSelection(String name, ProjectionKind kind, List<String> path, int maxMatches, int maxBytes, boolean required) {
        public ProjectionSelection {
            if (name == null || !name.matches("[a-z][a-z0-9_-]{0,63}") || kind == null || maxMatches < 1 || maxMatches > 1024 || maxBytes < 1 || maxBytes > 512 * 1024) throw new IllegalArgumentException("bounded named projection required");
            path = checkedPath(path);
        }
    }
    public record Selection(List<TableSelection> tables, List<ProjectionSelection> projections, boolean metadataRequired,
                            boolean structureCensus, List<List<String>> structureRoots) {
        public Selection {
            tables = List.copyOf(tables); projections = List.copyOf(projections);
            structureRoots = structureRoots.stream().map(SaveContracts::checkedPath).toList();
            Set<ScopeKind> kinds = new HashSet<>(); Set<List<String>> paths = new HashSet<>(); Set<String> names = new HashSet<>();
            if (tables.size() > 8 || projections.size() > 64) throw new IllegalArgumentException("selection cap exceeded");
            if (structureCensus == structureRoots.isEmpty() || structureRoots.size() > 64 || new HashSet<>(structureRoots).size() != structureRoots.size()) throw new IllegalArgumentException("explicit unique bounded census roots required when enabled; empty roots required when disabled");
            for (TableSelection table : tables) if (!kinds.add(table.kind()) || !paths.add(table.path())) throw new IllegalArgumentException("duplicate table kind/path");
            for (ProjectionSelection projection : projections) if (!names.add(projection.name())) throw new IllegalArgumentException("duplicate projection name");
        }
    }
    public record Scope(ScopeKind kind, Coverage coverage, List<String> path, String canonicalTokenSha256, Clausewitz.Block ast) {
        public Scope { Objects.requireNonNull(kind); Objects.requireNonNull(coverage); path = List.copyOf(path); digest(canonicalTokenSha256); Objects.requireNonNull(ast); }
    }
    /** IDs of full block records only; recognized native `none` slots are not records or members. */
    public record Inventory(ScopeKind kind, List<String> path, Availability availability, List<NativeId> ids) {
        public Inventory { Objects.requireNonNull(kind); path = List.copyOf(path); Objects.requireNonNull(availability); ids = List.copyOf(ids); }
    }
    public record RecordObservation(ScopeKind kind, NativeId id, List<String> path, RecordStatus status) {
        public RecordObservation { Objects.requireNonNull(kind); Objects.requireNonNull(id); path = List.copyOf(path); Objects.requireNonNull(status); }
    }
    public record ProjectionScope(String name, ProjectionKind kind, List<String> path, int occurrence, String canonicalTokenSha256, Clausewitz.Block ast) {
        public ProjectionScope { Objects.requireNonNull(name); Objects.requireNonNull(kind); path = List.copyOf(path); if (occurrence < 0) throw new IllegalArgumentException("negative occurrence"); digest(canonicalTokenSha256); Objects.requireNonNull(ast); }
    }
    public record ProjectionObservation(String name, int matches) { public ProjectionObservation { Objects.requireNonNull(name); if (matches < 0) throw new IllegalArgumentException("negative matches"); } }
    /** Structural facts only: numeric children are counted, not assumed to be a HouseDB. */
    public record Structure(List<String> path, int occurrence, List<String> namedBlockChildren, long numericBlockChildren, List<String> scalarKeys) {
        public Structure { path = List.copyOf(path); namedBlockChildren = List.copyOf(namedBlockChildren); scalarKeys = List.copyOf(scalarKeys); }
    }
    public record StructureCoverage(boolean enabled, List<List<String>> roots, int maxRelativeNamedDepth,
                                    int maxNodes, int maxKeys, boolean excludesNumericRecordPaths) {
        public StructureCoverage {
            roots = roots.stream().map(SaveContracts::checkedPath).toList();
            if (enabled == roots.isEmpty() || roots.size() > 64 || new HashSet<>(roots).size() != roots.size()
                    || maxRelativeNamedDepth != 4 || maxNodes != 1024 || maxKeys != 4096 || !excludesNumericRecordPaths) throw new IllegalArgumentException("explicit census root coverage and unchanged bounds required");
        }
    }
    public record Projection(List<Inventory> inventories, List<Scope> scopes, List<RecordObservation> records,
                             List<ProjectionScope> projections, List<ProjectionObservation> projectionObservations,
                             List<Structure> structures, StructureCoverage structureCoverage, List<String> rootKeys, List<Clausewitz.Entry> rootScalars,
                             long tokens, int selectedTokenBytes) {
        public Projection {
            inventories = List.copyOf(inventories); scopes = List.copyOf(scopes); records = List.copyOf(records);
            projections = List.copyOf(projections); projectionObservations = List.copyOf(projectionObservations);
            structures = List.copyOf(structures); rootKeys = List.copyOf(rootKeys); rootScalars = List.copyOf(rootScalars);
            Objects.requireNonNull(structureCoverage);
        }
    }
    public record DecoderLimits(long maxStreamBytes, int maxStderrBytes, Duration timeout) {
        public DecoderLimits {
            if (maxStreamBytes < 1 || maxStreamBytes > 512L * 1024 * 1024 || maxStderrBytes < 1 || maxStderrBytes > 65536 || timeout == null || timeout.isZero() || timeout.isNegative() || timeout.compareTo(Duration.ofSeconds(120)) > 0) throw new IllegalArgumentException("bounded decoder limits required");
        }
        public static DecoderLimits standard() { return new DecoderLimits(512L * 1024 * 1024, 65536, Duration.ofSeconds(120)); }
    }
    public record Decoded(Pin save, Pin decoder, int exitCode, String stderr, String streamSha256, String streamBytes, Projection projection, boolean saveUnchanged) {
        public Decoded { Objects.requireNonNull(save); Objects.requireNonNull(decoder); Objects.requireNonNull(stderr); digest(streamSha256); Objects.requireNonNull(projection); if (exitCode != 0 || !saveUnchanged) throw new IllegalArgumentException("successful offline decode required"); }
    }
    public static List<String> checkedPath(List<String> path) {
        List<String> result = List.copyOf(path);
        if (result.isEmpty() || result.size() > 16 || result.stream().anyMatch(p -> !p.matches("[A-Za-z_][A-Za-z0-9_]*"))) throw new IllegalArgumentException("explicit named table/projection path required");
        return result;
    }
    public static void digest(String value) { if (value == null || !value.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("lowercase SHA-256 required"); }
}
