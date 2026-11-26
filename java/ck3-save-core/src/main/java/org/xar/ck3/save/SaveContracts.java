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
    public enum ScopeKind { METADATA, ACTOR, RITE, FAITH, RELIGION, DYNASTY, HOUSE, COAT_OF_ARMS }
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
            // Only an exact observed Story record has a numeric projection path.
            // Table/census and all other projections retain checkedPath unchanged.
            if (path != null && path.size() == 3 && path.get(0).equals("stories") && path.get(1).equals("active")
                    && path.get(2) != null && path.get(2).matches("0|[1-9][0-9]{0,9}")) {
                BigInteger id = new BigInteger(path.get(2));
                if (kind != ProjectionKind.OTHER || maxMatches != 1 || id.compareTo(BigInteger.valueOf(0xFFFFFFFFL)) >= 0)
                    throw new IllegalArgumentException("exact valid uint32 Story projection required");
                path = List.copyOf(path);
            } else path = checkedPath(path);
        }
        /** Explicit identity request, distinct from the legacy generic named-path constructor. */
        public static ProjectionSelection exactStory(String name, String canonicalStoryId, int maxBytes, boolean required) {
            if (canonicalStoryId == null || !canonicalStoryId.matches("0|[1-9][0-9]{0,9}")
                    || new BigInteger(canonicalStoryId).compareTo(BigInteger.valueOf(0xFFFFFFFFL)) >= 0)
                throw new IllegalArgumentException("canonical valid uint32 exact Story ID required: " + canonicalStoryId);
            return new ProjectionSelection(name, ProjectionKind.OTHER, List.of("stories", "active", canonicalStoryId), 1, maxBytes, required);
        }
    }
    /** Provisional streaming callbacks; callers publish only after full read/physical-pin validation succeeds. */
    public interface StreamingTableSink {
        void discriminator(NativeId id, String value) throws java.io.IOException;
        void record(StreamedRecord record) throws java.io.IOException;
        /** A canonical native slot tombstone has no record AST/discriminator or financial rights. */
        default void tombstone(NativeTombstone slot) throws java.io.IOException { }
        /** Explicit opt-in callback is provisional until complete EOF and physical-pin validation. */
        default void missingDiscriminator(UntypedRecord record) throws java.io.IOException {
            throw new java.io.IOException("untyped streaming record has no accepting sink: " + record.id().value());
        }
    }
    public enum MissingDiscriminatorPolicy { REJECT, CAPTURE_MISSING_BOUNDED }
    public record UntypedRecord(NativeId id, String canonicalTokenSha256, int canonicalTokenBytes, Clausewitz.Block ast) {
        public UntypedRecord {
            Objects.requireNonNull(id); digest(canonicalTokenSha256); Objects.requireNonNull(ast);
            if (canonicalTokenBytes < 11 || canonicalTokenBytes > 512 * 1024) throw new IllegalArgumentException("bounded untyped record required");
        }
    }
    /** Separate streamed-work budget; existing retained-record/projection limits are unchanged. */
    public record StreamingTable(List<String> path, String discriminatorField, List<NativeId> selectedIds,
                                 int maxTableRecords, int maxRecordBytes, long maxStreamedBytes, boolean required,
                                 MissingDiscriminatorPolicy missingDiscriminatorPolicy) {
        /** Existing seven-argument callers retain strict missing-discriminator rejection. */
        public StreamingTable(List<String> path, String discriminatorField, List<NativeId> selectedIds,
                              int maxTableRecords, int maxRecordBytes, long maxStreamedBytes, boolean required) {
            this(path, discriminatorField, selectedIds, maxTableRecords, maxRecordBytes, maxStreamedBytes, required, MissingDiscriminatorPolicy.REJECT);
        }
        public StreamingTable {
            Objects.requireNonNull(missingDiscriminatorPolicy);
            path = checkedPath(path); selectedIds = List.copyOf(selectedIds);
            if (discriminatorField == null || !discriminatorField.matches("[A-Za-z_][A-Za-z0-9_]{0,127}")
                    || maxTableRecords < 1 || maxTableRecords > 200000 || selectedIds.size() > maxTableRecords
                    || new HashSet<>(selectedIds).size() != selectedIds.size()
                    || maxRecordBytes < 11 || maxRecordBytes > 512 * 1024
                    || maxStreamedBytes < 11 || maxStreamedBytes > 64L * 1024 * 1024)
                throw new IllegalArgumentException("explicit bounded streaming table required");
        }
    }
    public record StreamedRecord(NativeId id, String discriminator, String canonicalTokenSha256,
                                 int canonicalTokenBytes, Clausewitz.Block ast) {
        public StreamedRecord {
            Objects.requireNonNull(id); Objects.requireNonNull(discriminator); digest(canonicalTokenSha256);
            Objects.requireNonNull(ast); if (canonicalTokenBytes < 11 || canonicalTokenBytes > 512 * 1024) throw new IllegalArgumentException("bounded record bytes required");
        }
    }
    /** The exact unquoted <canonical-native-id> = none storage form; never a financial record. */
    public record NativeTombstone(NativeId id, String canonicalTokenSha256, int canonicalTokenBytes, long valueToken) {
        public NativeTombstone {
            Objects.requireNonNull(id); digest(canonicalTokenSha256);
            byte[] canonical = (id.value() + " = none").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            if (canonicalTokenBytes != canonical.length || valueToken < 3
                    || !canonicalTokenSha256.equals(FilePins.sha256(canonical)))
                throw new IllegalArgumentException("exact canonical native tombstone evidence required");
        }
    }
    public record StreamingObservation(boolean tableSeen, int records, int selectedRecords, long streamedTokenBytes,
                                       List<NativeTombstone> tombstones) {
        public StreamingObservation(boolean tableSeen, int records, int selectedRecords, long streamedTokenBytes) {
            this(tableSeen, records, selectedRecords, streamedTokenBytes, List.of());
        }
        public int observedSlots() { return records + tombstones.size(); }
        public StreamingObservation {
            tombstones = List.copyOf(tombstones);
            if (tombstones.stream().map(NativeTombstone::id).distinct().count() != tombstones.size()
                    || (long) records + tombstones.size() > 200000) throw new IllegalArgumentException("unique bounded observed native slots required");
            if (records < 0 || records > 200000 || selectedRecords < 0 || selectedRecords > records
                    || streamedTokenBytes < 0 || streamedTokenBytes > 64L * 1024 * 1024
                    || !tableSeen && (records != 0 || selectedRecords != 0 || streamedTokenBytes != 0 || !tombstones.isEmpty()))
                throw new IllegalArgumentException("bounded streaming observation required");
        }
    }
    public record Selection(List<TableSelection> tables, List<ProjectionSelection> projections, boolean metadataRequired,
                            boolean structureCensus, List<List<String>> structureRoots) {
        public Selection {
            tables = List.copyOf(tables); projections = List.copyOf(projections);
            structureRoots = structureRoots.stream().map(SaveContracts::checkedPath).toList();
            Set<ScopeKind> kinds = new HashSet<>(); Set<List<String>> paths = new HashSet<>(); Set<String> names = new HashSet<>();
            if (tables.size() > 7 || projections.size() > 64) throw new IllegalArgumentException("selection cap exceeded");
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
