package org.xar.ck3.save;

import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.save.SaveContracts.*;

/** Validates the entire stream; retains only bounded selected records and explicit projections. */
public final class SaveStream {
    private static final int MAX_RECORD_CHARS = 512 * 1024;
    private static final int MAX_SELECTED_BYTES = 4 * 1024 * 1024;
    private final Clausewitz.Lexer lexer;
    private final Selection selection;
    private final Map<ScopeKind, Set<String>> census = new LinkedHashMap<>();
    private final Map<ScopeKind, Set<String>> emptySlots = new LinkedHashMap<>();
    private final Set<ScopeKind> seen = new LinkedHashSet<>();
    private final List<Scope> scopes = new ArrayList<>();
    private final List<ProjectionScope> projections = new ArrayList<>();
    private final Map<String, Integer> matches = new LinkedHashMap<>();
    private final List<String> rootKeys = new ArrayList<>();
    private final List<Clausewitz.Entry> rootScalars = new ArrayList<>();
    private final Set<String> tableChildren = new LinkedHashSet<>();
    private final List<Capture> active = new ArrayList<>();
    private final List<StructureBuilder> structures = new ArrayList<>();
    private final Map<List<String>, Integer> structureOccurrences = new LinkedHashMap<>();
    private int selectedBytes;
    private int structureKeys;
    private int diagnosticBytes;
    private boolean metadataSeen;
    private boolean read;

    public SaveStream(Reader reader, Selection selection) {
        this.lexer = new Clausewitz.Lexer(reader, Clausewitz.Syntax.SAVE, 2 * 1024 * 1024);
        this.selection = java.util.Objects.requireNonNull(selection);
        for (TableSelection table : selection.tables()) {
            census.put(table.kind(), new LinkedHashSet<>()); emptySlots.put(table.kind(), new LinkedHashSet<>());
        }
        for (ProjectionSelection projection : selection.projections()) matches.put(projection.name(), 0);
    }
    public Projection read() throws IOException {
        if (read) throw failure("stream already consumed");
        read = true;
        block(List.of(), false);
        if (lexer.peek() != null || !active.isEmpty()) throw failure("incomplete stream");
        for (TableSelection table : selection.tables()) {
            if (table.required() && !seen.contains(table.kind())) throw failure("required table absent: " + table.path() + "; observed table children=" + tableChildren + "; roots=" + rootKeys);
            if (table.required() && !census.get(table.kind()).containsAll(table.ids().stream().map(NativeId::value).toList())) throw failure("selected " + table.kind() + " records absent; available=" + census.get(table.kind()));
        }
        if (selection.metadataRequired() && !metadataSeen) throw failure("meta_data absent");
        for (ProjectionSelection projection : selection.projections()) if (projection.required() && matches.get(projection.name()) == 0) throw failure("required projection absent: " + projection.name());
        Comparator<NativeId> order = Comparator.comparingInt((NativeId id) -> id.value().length()).thenComparing(NativeId::value);
        List<Inventory> inventories = new ArrayList<>();
        List<RecordObservation> records = new ArrayList<>();
        for (ScopeKind kind : ScopeKind.values()) {
            if (kind == ScopeKind.METADATA) continue;
            TableSelection table = selection.tables().stream().filter(t -> t.kind() == kind).findFirst().orElse(null);
            if (table == null) {
                inventories.add(new Inventory(kind, List.of(), Availability.UNKNOWN_LAYOUT, List.of()));
                continue;
            }
            boolean observed = seen.contains(kind);
            inventories.add(new Inventory(kind, table.path(), observed ? Availability.OBSERVED : Availability.TABLE_NOT_FOUND,
                    census.get(kind).stream().map(NativeId::new).sorted(order).toList()));
            for (NativeId id : table.ids()) records.add(new RecordObservation(kind, id, child(table.path(), id.value()),
                    !observed ? RecordStatus.UNKNOWN_TABLE : census.get(kind).contains(id.value()) ? RecordStatus.FULL_RECORD : RecordStatus.NOT_FOUND));
        }
        return new Projection(inventories, scopes, records, projections,
                matches.entrySet().stream().map(e -> new ProjectionObservation(e.getKey(), e.getValue())).toList(),
                structures.stream().map(StructureBuilder::freeze).toList(),
                new StructureCoverage(selection.structureCensus(), selection.structureRoots(), 4, 1024, 4096, true), rootKeys, rootScalars, lexer.tokens(), selectedBytes);
    }
    private void block(List<String> path, boolean braced) throws IOException {
        if (path.size() > 128) throw failure("nesting cap exceeded");
        StructureBuilder structure = structure(path);
        while (lexer.peek() != null && !lexer.peek().equals("}")) {
            String key = next();
            if (key.equals("=")) throw failure("unexpected assignment");
            if (key.equals("{")) { block(child(path, "[]"), true); continue; }
            if ("=".equals(lexer.peek())) {
                next(); String value = next();
                if (value == null || value.equals("}") || value.equals("=")) throw failure("missing assigned value");
                if (path.isEmpty() && !key.matches("[0-9]+") && !rootKeys.contains(key)) {
                    diagnostic(key); rootKeys.add(key); if (rootKeys.size() > 512) throw failure("root-key cap exceeded");
                }
                if (structure != null) structure.observe(key, value.equals("{"));
                if (value.equals("{")) {
                    List<String> nested = child(path, key); enter(nested); block(nested, true);
                } else {
                    observeScalar(path, key, value);
                    if (path.isEmpty()) {
                        diagnostic(key); diagnostic(value);
                        rootScalars.add(new Clausewitz.Entry(key, "=", new Clausewitz.Atom(value)));
                        if (rootScalars.size() > 512) throw failure("root-scalar cap exceeded");
                    }
                }
            } else if (selection.tables().stream().anyMatch(table -> table.path().equals(path))) throw failure("unassigned native table atom: " + key);
            else if (path.isEmpty() && !(rootKeys.isEmpty() && (key.startsWith("SAV") || key.equals("CK3txt")))) throw failure("unassigned root atom: " + key);
        }
        if (braced) {
            if (!"}".equals(next())) throw failure("truncated block");
            for (int i = active.size() - 1; i >= 0; i--) if (active.get(i).path.equals(path)) finish(active.remove(i));
        } else if (lexer.peek() != null) throw failure("unexpected root closing brace");
    }
    private void enter(List<String> path) throws IOException {
        if (path.size() == 2 && !path.getLast().matches("[0-9]+") && selection.tables().stream().anyMatch(table -> table.path().getFirst().equals(path.getFirst()))) {
            tableChildren.add(String.join("/", path)); if (tableChildren.size() > 1024) throw failure("table-child diagnostic cap exceeded");
        }
        if (path.equals(List.of("meta_data"))) {
            if (metadataSeen) throw failure("duplicate meta_data");
            metadataSeen = true;
            start(new Capture(ScopeKind.METADATA, path, null, 0));
        }
        for (TableSelection table : selection.tables()) {
            if (path.equals(table.path()) && !seen.add(table.kind())) throw failure("duplicate selected table: " + path);
            if (path.size() != table.path().size() + 1 || !path.subList(0, path.size() - 1).equals(table.path())) continue;
            String id = path.getLast();
            try { new NativeId(id); } catch (IllegalArgumentException invalid) { throw failure("invalid native table identity at " + path); }
            Set<String> ids = census.get(table.kind());
            if (!ids.add(id) || emptySlots.get(table.kind()).contains(id)) throw failure("duplicate native ID in table: " + path);
            if (ids.size() + emptySlots.get(table.kind()).size() > 200000) throw failure("table identity cap exceeded");
            if (table.ids().contains(new NativeId(id))) start(new Capture(table.kind(), path, null, 0));
        }
        for (ProjectionSelection projection : selection.projections()) if (projection.path().equals(path)) {
            int occurrence = matches.get(projection.name());
            if (occurrence >= projection.maxMatches()) throw failure("projection match cap exceeded: " + projection.name());
            matches.put(projection.name(), occurrence + 1);
            start(new Capture(null, path, projection, occurrence));
        }
    }
    /** Native empty cells are not full records; unknown scalar layouts never become silent omissions. */
    private void observeScalar(List<String> path, String key, String value) throws IOException {
        for (TableSelection table : selection.tables()) {
            if (child(path, key).equals(table.path())) throw failure("native table must be a block: " + table.path());
            if (!path.equals(table.path())) continue;
            try { new NativeId(key); } catch (IllegalArgumentException invalid) { throw failure("invalid native empty-slot identity: " + key); }
            Set<String> slots = emptySlots.get(table.kind());
            if (!value.equals("none")) throw failure("unknown native table scalar: " + child(path, key));
            if (!slots.add(key) || census.get(table.kind()).contains(key)) throw failure("duplicate native ID in table: " + child(path, key));
            if (slots.size() + census.get(table.kind()).size() > 200000) throw failure("table identity cap exceeded");
        }
    }
    private void start(Capture capture) throws IOException {
        selectedBytes += capture.bytes;
        if (selectedBytes > MAX_SELECTED_BYTES) throw failure("total selected record cap exceeded");
        active.add(capture);
    }
    private void finish(Capture capture) throws IOException {
        byte[] bytes = capture.text.toString().getBytes(StandardCharsets.UTF_8);
        Clausewitz.Block ast;
        try { ast = Clausewitz.parse(capture.text.toString()).block("record"); }
        catch (IllegalArgumentException invalid) { throw new IOException("invalid selected AST", invalid); }
        String hash = FilePins.sha256(bytes);
        if (capture.projection != null) {
            projections.add(new ProjectionScope(capture.projection.name(), capture.projection.kind(), capture.path, capture.occurrence, hash, ast));
        } else {
            Coverage coverage = capture.kind == ScopeKind.METADATA ? Coverage.DIRECT_SCALARS : Coverage.FULL_RECORD;
            if (coverage == Coverage.DIRECT_SCALARS) ast = new Clausewitz.Block(ast.entries().stream().filter(e -> e.value() instanceof Clausewitz.Atom).toList());
            scopes.add(new Scope(capture.kind, coverage, capture.path, hash, ast));
        }
    }
    private String next() throws IOException {
        String value = lexer.next();
        if (value != null && !active.isEmpty()) {
            int bytes = value.getBytes(StandardCharsets.UTF_8).length + 1;
            for (Capture capture : active) {
                capture.text.append(value).append(' '); capture.bytes += bytes; selectedBytes += bytes;
                if (capture.text.length() > MAX_RECORD_CHARS) throw failure("selected record cap exceeded");
                if (capture.projection != null && capture.bytes > capture.projection.maxBytes()) throw failure("projection byte cap exceeded: " + capture.projection.name());
            }
            if (selectedBytes > MAX_SELECTED_BYTES) throw failure("total selected record cap exceeded");
        }
        return value;
    }
    private StructureBuilder structure(List<String> path) throws IOException {
        if (!selection.structureCensus() || path.stream().anyMatch(p -> !p.matches("[A-Za-z_][A-Za-z0-9_]*"))) return null;
        // Ancestors are traversed by block(), but only explicitly selected roots and
        // their bounded named descendants get census records. Unrelated containers
        // are still fully parsed without accumulating their keys.
        boolean selected = selection.structureRoots().stream().anyMatch(root ->
                path.size() >= root.size() && path.size() - root.size() <= 4 && path.subList(0, root.size()).equals(root));
        if (!selected) return null;
        if (structures.size() >= 1024) throw failure("structure census cap exceeded");
        int occurrence = structureOccurrences.getOrDefault(path, 0);
        structureOccurrences.put(path, occurrence + 1);
        StructureBuilder result = new StructureBuilder(path, occurrence); structures.add(result); return result;
    }
    private final class StructureBuilder {
        private final List<String> path;
        private final int occurrence;
        private final Set<String> blocks = new LinkedHashSet<>();
        private final Set<String> scalars = new LinkedHashSet<>();
        private long numeric;
        private StructureBuilder(List<String> path, int occurrence) { this.path = path; this.occurrence = occurrence; }
        private void observe(String key, boolean block) throws IOException {
            if (key.matches("[0-9]+")) { if (block) numeric++; return; }
            if ((block ? blocks : scalars).add(key)) {
                diagnostic(key);
                if (++structureKeys > 4096) throw failure("structure key cap exceeded");
            }
        }
        private Structure freeze() { return new Structure(path, occurrence, List.copyOf(blocks), numeric, List.copyOf(scalars)); }
    }
    private static final class Capture {
        private final ScopeKind kind;
        private final List<String> path;
        private final ProjectionSelection projection;
        private final int occurrence;
        private final StringBuilder text = new StringBuilder("record = { ");
        private int bytes = 11;
        private Capture(ScopeKind kind, List<String> path, ProjectionSelection projection, int occurrence) {
            this.kind = kind; this.path = path; this.projection = projection; this.occurrence = occurrence;
        }
    }
    private IOException failure(String message) { return new IOException(message + " at token " + lexer.tokens()); }
    private void diagnostic(String value) throws IOException {
        diagnosticBytes += value.getBytes(StandardCharsets.UTF_8).length;
        if (diagnosticBytes > 1024 * 1024) throw failure("root/census diagnostic byte cap exceeded");
    }
    private static List<String> child(List<String> path, String key) { List<String> result = new ArrayList<>(path); result.add(key); return List.copyOf(result); }
}
