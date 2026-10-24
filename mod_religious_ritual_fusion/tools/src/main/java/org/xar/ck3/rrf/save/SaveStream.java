package org.xar.ck3.rrf.save;

import java.io.BufferedReader;
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
import org.xar.ck3.rrf.Clausewitz;
import org.xar.ck3.rrf.ReleaseBuilder;
import org.xar.ck3.rrf.save.SaveContracts.Block;
import org.xar.ck3.rrf.save.SaveContracts.Inventory;
import org.xar.ck3.rrf.save.SaveContracts.NativeId;
import org.xar.ck3.rrf.save.SaveContracts.Request;
import org.xar.ck3.rrf.save.SaveContracts.Scope;
import org.xar.ck3.rrf.save.SaveContracts.ScopeKind;

/** Full stream validation, table identity census, and bounded selected records; no world AST. */
public final class SaveStream {
    private static final int MAX_TOKEN = 2 * 1024 * 1024;
    private static final int MAX_RECORD = 512 * 1024;
    private static final int MAX_SELECTED = 4 * 1024 * 1024;
    private final Reader reader;
    private final Request request;
    private final Map<ScopeKind, List<String>> tables = new LinkedHashMap<>();
    private final Map<ScopeKind, Set<String>> census = new LinkedHashMap<>();
    private final Map<ScopeKind, Set<String>> wanted = new LinkedHashMap<>();
    private final List<Scope> scopes = new ArrayList<>();
    private final List<String> rootKeys = new ArrayList<>();
    private final List<SaveContracts.Entry> rootScalars = new ArrayList<>();
    private final Set<ScopeKind> tableSeen = new LinkedHashSet<>();
    private final Set<String> tableChildren = new LinkedHashSet<>();
    private final Set<String> selectedSeen = new LinkedHashSet<>();
    private int character = -2;
    private String lookahead;
    private long tokens;
    private int selectedBytes;
    private StringBuilder capture;
    private int captureDepth;
    private ScopeKind captureKind;
    private List<String> capturePath;

    public SaveStream(Reader reader, Request request) {
        this.reader = new BufferedReader(reader, 65536); this.request = request;
        tables.put(ScopeKind.ACTOR, request.layout().actorTable()); tables.put(ScopeKind.RITE, request.layout().riteTable());
        tables.put(ScopeKind.FAITH, request.layout().faithTable()); tables.put(ScopeKind.RELIGION, request.layout().religionTable());
        for (ScopeKind kind : tables.keySet()) census.put(kind, new LinkedHashSet<>());
        wanted.put(ScopeKind.ACTOR, Set.of(request.selection().actorId().value()));
        wanted.put(ScopeKind.RITE, ids(request.selection().riteIds())); wanted.put(ScopeKind.FAITH, ids(request.selection().faithIds())); wanted.put(ScopeKind.RELIGION, ids(request.selection().religionIds()));
    }
    public record Projection(List<Inventory> inventories, List<Scope> scopes, List<String> rootKeys, List<SaveContracts.Entry> rootScalars, long tokens, int selectedTokenBytes) { }
    public Projection read() throws IOException {
        block(List.of(), false);
        if (peek() != null || capture != null) throw failure("incomplete stream");
        for (ScopeKind kind : tables.keySet()) {
            if (!tableSeen.contains(kind)) throw failure("required table absent: " + tables.get(kind) + "; observed table children=" + tableChildren + "; roots=" + rootKeys);
            if (!census.get(kind).containsAll(wanted.get(kind))) throw failure("selected " + kind + " records absent; available=" + census.get(kind));
        }
        if (scopes.stream().noneMatch(s -> s.kind() == ScopeKind.METADATA)) throw failure("meta_data absent");
        Comparator<NativeId> order = Comparator.comparingInt((NativeId id) -> id.value().length()).thenComparing(NativeId::value);
        List<Inventory> inventories = tables.entrySet().stream().filter(e -> e.getKey() != ScopeKind.ACTOR)
                .map(e -> new Inventory(e.getKey(), e.getValue(), census.get(e.getKey()).stream().map(NativeId::new).sorted(order).toList())).toList();
        return new Projection(inventories, List.copyOf(scopes), List.copyOf(rootKeys), List.copyOf(rootScalars), tokens, selectedBytes);
    }
    private void block(List<String> path, boolean braced) throws IOException {
        if (path.size() > 128) throw failure("nesting cap exceeded");
        while (peek() != null && !peek().equals("}")) {
            String key = next();
            if (key.equals("=")) throw failure("unexpected assignment");
            if (key.equals("{")) { block(child(path, "[]"), true); continue; }
            if ("=".equals(peek())) {
                next(); String value = next();
                if (value == null || value.equals("}") || value.equals("=")) throw failure("missing assigned value");
                // Current saves also place deceased numeric character records at root.
                // Census only named containers here; those unrelated records are still fully validated.
                if (path.isEmpty() && !key.matches("[0-9]+") && !rootKeys.contains(key)) { rootKeys.add(key); if (rootKeys.size() > 512) throw failure("root-key cap exceeded"); }
                if (value.equals("{")) {
                    List<String> nested = child(path, key); enter(nested); block(nested, true);
                } else if (path.isEmpty()) rootScalars.add(new SaveContracts.Entry(key, "=", new SaveContracts.Atom(value)));
            } else if (path.isEmpty() && !(rootKeys.isEmpty() && (key.startsWith("SAV") || key.equals("CK3txt")))) throw failure("unassigned root atom: " + key);
        }
        if (braced) {
            if (!"}".equals(next())) throw failure("truncated block");
            if (capture != null && path.size() == captureDepth) finishCapture();
        } else if (peek() != null) throw failure("unexpected root closing brace");
    }
    private void enter(List<String> path) throws IOException {
        if (path.size() == 2 && !path.getLast().matches("[0-9]+") && tables.values().stream().anyMatch(table -> table.getFirst().equals(path.getFirst()))) {
            tableChildren.add(String.join("/", path)); if (tableChildren.size() > 1024) throw failure("table-child diagnostic cap exceeded");
        }
        if (path.equals(List.of("meta_data"))) startCapture(ScopeKind.METADATA, path);
        for (Map.Entry<ScopeKind, List<String>> table : tables.entrySet()) {
            if (path.equals(table.getValue()) && !tableSeen.add(table.getKey())) throw failure("duplicate selected table: " + path);
            if (path.size() != table.getValue().size() + 1 || !path.subList(0, path.size() - 1).equals(table.getValue())) continue;
            String id = path.getLast();
            try { new NativeId(id); } catch (IllegalArgumentException invalid) { throw failure("invalid native table identity at " + path); }
            Set<String> ids = census.get(table.getKey());
            if (!ids.add(id)) throw failure("duplicate native ID in table: " + path);
            if (ids.size() > 200000) throw failure("table identity cap exceeded");
            if (wanted.get(table.getKey()).contains(id)) startCapture(table.getKey(), path);
        }
    }
    private void startCapture(ScopeKind kind, List<String> path) throws IOException {
        if (capture != null || !selectedSeen.add(String.join("/", path))) throw failure("overlapping/duplicate selected record");
        capture = new StringBuilder("record = { "); captureDepth = path.size(); captureKind = kind; capturePath = path;
    }
    private void finishCapture() throws IOException {
        byte[] bytes = capture.toString().getBytes(StandardCharsets.UTF_8); selectedBytes += bytes.length;
        if (selectedBytes > MAX_SELECTED) throw failure("total selected record cap exceeded");
        Clausewitz.Block ast = Clausewitz.parse(capture.toString()).block("record");
        SaveContracts.Coverage coverage = captureKind == ScopeKind.METADATA ? SaveContracts.Coverage.DIRECT_SCALARS : SaveContracts.Coverage.FULL_RECORD;
        // Portraits and nested campaign metadata are unrelated to the requested oracle.
        // The full metadata token digest is retained; metadata AST coverage is explicit.
        if (coverage == SaveContracts.Coverage.DIRECT_SCALARS) ast = new Clausewitz.Block(ast.entries().stream().filter(e -> e.value() instanceof Clausewitz.Atom).toList());
        scopes.add(new Scope(captureKind, coverage, capturePath, ReleaseBuilder.sha256(bytes), convert(ast))); capture = null;
    }
    private static Block convert(Clausewitz.Block block) {
        return new Block(block.entries().stream().map(e -> new SaveContracts.Entry(e.key(), e.operator(), e.value() instanceof Clausewitz.Block child ? convert(child) : new SaveContracts.Atom(((Clausewitz.Atom) e.value()).token()))).toList());
    }
    private String peek() throws IOException { if (lookahead == null) lookahead = token(); return lookahead; }
    private String next() throws IOException {
        String value = peek(); lookahead = null;
        if (value != null) {
            tokens++;
            if (capture != null) { capture.append(value).append(' '); if (capture.length() > MAX_RECORD) throw failure("selected record cap exceeded"); }
        }
        return value;
    }
    private int current() throws IOException { if (character == -2) character = reader.read(); return character; }
    private int take() throws IOException { int value = current(); character = -2; return value; }
    private String token() throws IOException {
        while (current() != -1) {
            if (Character.isWhitespace(current()) || current() == '\ufeff') { take(); continue; }
            if (current() == '#') { while (current() != -1 && take() != '\n') { } continue; }
            break;
        }
        if (current() == -1) return null;
        StringBuilder token = new StringBuilder(); int first = take(); token.append((char) first);
        if (first == '{' || first == '}' || first == '=') return token.toString();
        if (first == '"') {
            boolean escaped = false;
            while (current() != -1) {
                int c = take(); token.append((char) c);
                if (token.length() > MAX_TOKEN) throw failure("token cap exceeded");
                if (c == '"' && !escaped) return token.toString();
                escaped = c == '\\' && !escaped;
            }
            throw failure("truncated quoted atom");
        }
        while (current() != -1 && !Character.isWhitespace(current()) && "{}=#".indexOf(current()) < 0) {
            token.append((char) take()); if (token.length() > MAX_TOKEN) throw failure("token cap exceeded");
        }
        return token.toString();
    }
    private IOException failure(String message) { return new IOException(message + " at token " + tokens); }
    private static List<String> child(List<String> path, String key) { List<String> result = new ArrayList<>(path); result.add(key); return List.copyOf(result); }
    private static Set<String> ids(List<NativeId> ids) { return Set.copyOf(ids.stream().map(NativeId::value).toList()); }
}
