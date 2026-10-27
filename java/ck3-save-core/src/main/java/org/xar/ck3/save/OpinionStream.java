package org.xar.ck3.save;

import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.save.OpinionInspection.*;

/** Full grammar walk, one bounded anonymous row at a time; no global opinion table aggregation. */
final class OpinionStream {
    private final Clausewitz.Lexer lexer;
    private final Selection selection;
    private final List<Row> matched = new ArrayList<>();
    private int tables;
    private int matchedBytes;
    private long rows;
    private boolean read;
    private StringBuilder capture;
    private int captureBytes;
    OpinionStream(Reader reader, Selection selection) {
        this.lexer = new Clausewitz.Lexer(reader, Clausewitz.Syntax.SAVE, 2 * 1024 * 1024); this.selection = selection;
    }
    Projection read() throws IOException {
        if (read) throw failure("stream already consumed"); read = true;
        block(List.of(), false);
        if (lexer.peek() != null || capture != null || tables != 1) throw failure("complete stream and exactly one opinion table required");
        List<Finding> findings = new ArrayList<>();
        for (Pair pair : selection.pairs()) {
            List<Row> found = matched.stream().filter(r -> r.owner().equals(pair.owner()) && r.target().equals(pair.target())).toList();
            findings.add(new Finding(pair, found, OpinionInspection.modifiers(selection, found)));
        }
        Projection result = new Projection(lexer.tokens(), rows, findings); OpinionInspection.validate(selection, result); return result;
    }
    private void block(List<String> path, boolean braced) throws IOException {
        if (path.size() > 128) throw failure("stream nesting cap exceeded");
        boolean table = path.equals(selection.tablePath());
        if (table && ++tables != 1) throw failure("duplicate opinion table");
        while (lexer.peek() != null && !lexer.peek().equals("}")) {
            String key = next();
            if (key.equals("=")) throw failure("unexpected assignment");
            if (key.equals("{")) {
                if (table) {
                    capture = new StringBuilder("{ "); captureBytes = 2; block(child(path, "[]"), true); finish();
                } else block(child(path, "[]"), true);
                continue;
            }
            if (table) throw failure("anonymous opinion row blocks required");
            if ("=".equals(lexer.peek())) {
                next(); String value = next();
                if (value == null || value.equals("}") || value.equals("=")) throw failure("missing assigned value");
                List<String> nested = child(path, key);
                if (value.equals("{")) block(nested, true);
                else if (nested.equals(selection.tablePath())) throw failure("opinion table must be a block");
            } else if (path.isEmpty() && !(key.equals("CK3txt") || key.startsWith("SAV"))) throw failure("unassigned root atom");
        }
        if (braced) { if (!"}".equals(next())) throw failure("truncated block"); }
        else if (lexer.peek() != null) throw failure("unexpected root closing brace");
    }
    private void finish() throws IOException {
        Clausewitz.Block ast;
        try { ast = Clausewitz.parse("record = " + capture).block("record"); }
        catch (IllegalArgumentException invalid) { throw new IOException("invalid opinion AST", invalid); }
        rows++;
        Row row = new Row(rows, OpinionInspection.id(ast, "owner"), OpinionInspection.id(ast, "target"), ast);
        if (selection.pairs().stream().anyMatch(p -> p.owner().equals(row.owner()) && p.target().equals(row.target()))) {
            matchedBytes += captureBytes;
            if (matchedBytes > selection.maxMatchedBytes() || matched.size() >= selection.maxMatchedRows()) throw failure("matched-only cap exceeded");
            matched.add(row);
        }
        capture = null;
    }
    private String next() throws IOException {
        String token = lexer.next();
        if (capture != null && token != null) {
            capture.append(token).append(' '); captureBytes += token.getBytes(StandardCharsets.UTF_8).length + 1;
            if (captureBytes > selection.maxRecordBytes()) throw failure("opinion row cap exceeded");
        }
        return token;
    }
    static int tokenBytes(Clausewitz.Block ast) {
        try {
            Clausewitz.Lexer lexer = new Clausewitz.Lexer(new java.io.StringReader(ast.render()), Clausewitz.Syntax.SAVE, 2 * 1024 * 1024);
            int bytes = 0; for (String token; (token = lexer.next()) != null;) bytes += token.getBytes(StandardCharsets.UTF_8).length + 1;
            return bytes;
        } catch (IOException invalid) { throw new IllegalArgumentException("invalid matched row", invalid); }
    }
    private IOException failure(String message) { return new IOException(message + " at token " + lexer.tokens()); }
    private static List<String> child(List<String> path, String key) { List<String> result = new ArrayList<>(path); result.add(key); return List.copyOf(result); }
}
