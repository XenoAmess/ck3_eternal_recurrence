package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/** Exact text transport for existing source patches. It contains no SDK business generator. */
public final class ExactSourcePatch {
    private static final Pattern HEADER = Pattern.compile("@@ -([0-9]+)(?:,([0-9]+))? \\+([0-9]+)(?:,([0-9]+))? @@.*");
    private ExactSourcePatch() { }

    public enum Syntax { UNIFIED_DIFF, CODEX_UPDATE }
    public record Result(byte[] bytes, int selectedFileSections, int hunks) {
        public Result { bytes = bytes.clone(); if (selectedFileSections != 1 || hunks < 1) throw new IllegalArgumentException("one exact patched file required"); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    private record Line(String body, String ending) { }
    private record Token(char operation, String body, boolean noNewline) { }
    private record Hunk(List<Token> tokens, Integer oldCount, Integer newCount) {
        private Hunk { tokens = List.copyOf(tokens); }
    }

    public static Result apply(byte[] original, byte[] patch, Syntax syntax, String patchTarget) throws IOException {
        if (original == null || patch == null || syntax == null || original.length > 8 * 1024 * 1024 || patch.length > 1024 * 1024) {
            throw new IOException("finite source and patch bytes required");
        }
        patchPath(patchTarget);
        List<String> physical = List.of(decode(patch).split("\\r?\\n", -1));
        List<Hunk> hunks = syntax == Syntax.UNIFIED_DIFF ? unified(physical, patchTarget) : codex(physical, patchTarget);
        List<Line> current = lines(decode(original));
        String ending = current.stream().map(Line::ending).filter(value -> !value.isEmpty()).findFirst().orElse("\n");
        int previousEnd = 0;
        for (Hunk hunk : hunks) {
            List<Token> before = hunk.tokens().stream().filter(token -> token.operation() != '+').toList();
            if (before.isEmpty()) throw new IOException("source insertion requires exact nonempty context");
            int found = -1;
            for (int start = previousEnd; start + before.size() <= current.size(); start++) {
                if (!matches(current, start, before)) continue;
                if (found != -1) throw new IOException("ambiguous source hunk; no fuzzy or offset-based choice is allowed");
                found = start;
            }
            if (found < 0) throw new IOException("source hunk exact context no longer matches");
            List<Line> replacement = new ArrayList<>();
            int consumed = 0;
            for (Token token : hunk.tokens()) {
                if (token.operation() == ' ') replacement.add(current.get(found + consumed++));
                else if (token.operation() == '-') consumed++;
                else replacement.add(new Line(token.body(), token.noNewline() ? "" : ending));
            }
            current.subList(found, found + before.size()).clear();
            current.addAll(found, replacement);
            previousEnd = found + replacement.size();
        }
        StringBuilder output = new StringBuilder();
        for (Line line : current) output.append(line.body()).append(line.ending());
        byte[] result = output.toString().getBytes(StandardCharsets.UTF_8);
        if (result.length > 8 * 1024 * 1024) throw new IOException("patched source exceeds limit");
        return new Result(result, 1, hunks.size());
    }

    private static boolean matches(List<Line> source, int start, List<Token> expected) {
        for (int index = 0; index < expected.size(); index++) {
            Token token = expected.get(index); Line line = source.get(start + index);
            if (!line.body().equals(token.body()) || token.noNewline() && !line.ending().isEmpty()) return false;
        }
        return true;
    }

    private static List<Hunk> unified(List<String> lines, String target) throws IOException {
        List<Hunk> result = new ArrayList<>();
        boolean selected = false;
        int sections = 0;
        for (int index = 0; index < lines.size();) {
            String line = lines.get(index);
            if (line.startsWith("--- ")) {
                if (index + 1 >= lines.size() || !lines.get(index + 1).startsWith("+++ ")) throw new IOException("paired source patch headers required");
                selected = headerPath(line.substring(4)).equals(target);
                if (selected && ++sections != 1) throw new IOException("duplicate selected source patch section");
                index += 2;
                continue;
            }
            var header = HEADER.matcher(line);
            if (header.matches()) {
                int oldCount = count(header.group(2)), newCount = count(header.group(4));
                List<Token> tokens = new ArrayList<>();
                index++;
                int oldSeen = 0, newSeen = 0;
                while (index < lines.size()) {
                    String body = lines.get(index);
                    if (body.equals("\\ No newline at end of file")) {
                        markNoNewline(tokens); index++; continue;
                    }
                    if (oldSeen == oldCount && newSeen == newCount) break;
                    if (body.isEmpty() || " +-".indexOf(body.charAt(0)) < 0) throw new IOException("complete unified source hunk required");
                    char operation = body.charAt(0);
                    tokens.add(new Token(operation, body.substring(1), false));
                    if (operation != '+') oldSeen++;
                    if (operation != '-') newSeen++;
                    if (oldSeen > oldCount || newSeen > newCount) throw new IOException("source hunk counts exceeded");
                    index++;
                }
                if (oldSeen != oldCount || newSeen != newCount || tokens.isEmpty()) throw new IOException("source hunk counts differ");
                if (selected) result.add(new Hunk(tokens, oldCount, newCount));
                continue;
            }
            if (selected && line.startsWith("@@")) throw new IOException("malformed unified source hunk header");
            index++;
        }
        if (sections != 1 || result.isEmpty()) throw new IOException("one selected exact source section with hunks required: " + target);
        return List.copyOf(result);
    }

    private static List<Hunk> codex(List<String> lines, String target) throws IOException {
        if (lines.isEmpty() || !lines.getFirst().equals("*** Begin Patch")) throw new IOException("complete source update patch required");
        boolean selected = false, ended = false;
        int sections = 0;
        List<Hunk> result = new ArrayList<>();
        List<Token> tokens = null;
        for (int index = 1; index < lines.size(); index++) {
            String line = lines.get(index);
            if (ended && !line.isEmpty()) throw new IOException("source update has content after End Patch");
            if (line.startsWith("*** Update File: ") || line.equals("*** End Patch")) {
                if (selected && tokens != null) addCodexHunk(result, tokens);
                tokens = null;
                if (line.equals("*** End Patch")) { ended = true; selected = false; continue; }
                selected = line.substring("*** Update File: ".length()).replace('\\', '/').equals(target);
                if (selected && ++sections != 1) throw new IOException("duplicate selected source update");
                continue;
            }
            if (line.startsWith("*** ")) throw new IOException("only exact source Update File patches are supported");
            if (!selected) continue;
            if (line.equals("@@") || line.startsWith("@@ ")) {
                if (tokens != null) addCodexHunk(result, tokens);
                tokens = new ArrayList<>();
            } else if (line.equals("\\ No newline at end of file")) {
                if (tokens == null) throw new IOException("newline marker without hunk");
                markNoNewline(tokens);
            } else if (tokens != null && !line.isEmpty() && " +-".indexOf(line.charAt(0)) >= 0) {
                tokens.add(new Token(line.charAt(0), line.substring(1), false));
            } else if (!line.isEmpty()) throw new IOException("malformed exact source update hunk");
        }
        if (!ended || sections != 1 || result.isEmpty()) throw new IOException("complete selected source update required");
        return List.copyOf(result);
    }
    private static void addCodexHunk(List<Hunk> result, List<Token> tokens) throws IOException {
        if (tokens.isEmpty()) throw new IOException("empty source update hunk");
        result.add(new Hunk(tokens, null, null));
    }
    private static void markNoNewline(List<Token> tokens) throws IOException {
        if (tokens.isEmpty()) throw new IOException("newline marker without source line");
        Token previous = tokens.removeLast();
        if (previous.noNewline()) throw new IOException("repeated no-newline marker");
        tokens.add(new Token(previous.operation(), previous.body(), true));
    }
    private static int count(String value) throws IOException {
        try { int result = value == null ? 1 : Integer.parseInt(value); if (result < 0 || result > 200000) throw new NumberFormatException(); return result; }
        catch (NumberFormatException error) { throw new IOException("finite source hunk count required", error); }
    }
    private static String headerPath(String value) throws IOException {
        String token = value;
        int tab = token.indexOf('\t'); if (tab >= 0) token = token.substring(0, tab);
        if (token.startsWith("\"")) {
            if (!token.endsWith("\"")) throw new IOException("complete quoted Git source path required");
            StringBuilder unquoted = new StringBuilder();
            for (int index = 1; index < token.length() - 1; index++) {
                char ch = token.charAt(index);
                if (ch == '\\') {
                    if (++index >= token.length() - 1) throw new IOException("invalid quoted source path");
                    char escaped = token.charAt(index);
                    if (escaped != '\\' && escaped != '"') throw new IOException("unsupported quoted source-path escape");
                    unquoted.append(escaped);
                } else unquoted.append(ch);
            }
            token = unquoted.toString();
        }
        token = token.replace('\\', '/');
        if (token.startsWith("a/")) token = token.substring(2);
        patchPath(token);
        return token;
    }
    /** Header identity only; the separately validated Source.relativePath controls every write. */
    static String patchPath(String value) {
        if (value != null && (value.startsWith("/") || value.matches("[A-Za-z]:/.*"))) {
            String suffix = value.startsWith("/") ? value.substring(1) : value.substring(3);
            relative(suffix);
            return value;
        }
        return relative(value);
    }
    static String relative(String value) {
        if (value == null || value.isEmpty() || value.startsWith("/") || value.contains("\\") || value.contains(":") || value.indexOf('\0') >= 0) throw new IllegalArgumentException("canonical relative source path required");
        for (String part : value.split("/", -1)) if (part.isEmpty() || part.equals(".") || part.equals("..")) throw new IllegalArgumentException("confined source path required");
        return value;
    }
    private static String decode(byte[] bytes) throws IOException {
        try { return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString(); }
        catch (CharacterCodingException error) { throw new IOException("exact UTF-8 source/patch required", error); }
    }
    private static List<Line> lines(String text) {
        List<Line> result = new ArrayList<>();
        int start = 0;
        for (int index = 0; index < text.length(); index++) {
            if (text.charAt(index) != '\n') continue;
            boolean crlf = index > start && text.charAt(index - 1) == '\r';
            result.add(new Line(text.substring(start, crlf ? index - 1 : index), crlf ? "\r\n" : "\n"));
            start = index + 1;
        }
        if (start < text.length()) result.add(new Line(text.substring(start), ""));
        return result;
    }
}
