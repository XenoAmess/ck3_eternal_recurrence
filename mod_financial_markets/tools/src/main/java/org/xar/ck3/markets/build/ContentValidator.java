package org.xar.ck3.markets.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/** Source/packaging checks only. This does not implement the CK3 parser or prove runtime semantics. */
public final class ContentValidator {
    public record Manifest(String schema, List<String> files) { }
    public record Report(String boundary, int files, int effects, int localizationKeys,
                         List<String> runtimeFiles) { }
    private static final Set<String> ROOTS = Set.of("common", "events", "gui", "localization", "gfx");
    private static final Pattern LOC_KEY = Pattern.compile("^\\s+([A-Za-z0-9_.-]+):[0-9]*\\s+\".*\"\\s*$");
    private static final byte[] BOM = {(byte) 0xef, (byte) 0xbb, (byte) 0xbf};
    private ContentValidator() { }

    public static Report validate(Path source) throws IOException {
        Path root = source.toRealPath();
        Manifest manifest = new ObjectMapper().readValue(root.resolve("runtime-files.json").toFile(), Manifest.class);
        require("xfm.runtime-files.v1".equals(manifest.schema()), "unknown runtime manifest schema");
        require(manifest.files() != null && !manifest.files().isEmpty(), "empty runtime allowlist");
        Set<String> files = new HashSet<>();
        Set<String> effectDefinitions = new HashSet<>();
        Set<String> effectCalls = new HashSet<>();
        Map<String, Set<String>> languages = new LinkedHashMap<>();
        Map<String, Set<String>> definitions = new HashMap<>();
        int effects = 0;
        for (String name : manifest.files()) {
            require(files.add(name), "duplicate allowlist path: " + name);
            Path path = safeFile(root, name);
            String first = Path.of(name).getName(0).toString();
            require(name.equals("descriptor.mod") || ROOTS.contains(first), "non-runtime path in allowlist: " + name);
            if (name.endsWith(".txt") || name.endsWith(".gui") || name.endsWith(".yml") || name.endsWith(".mod")) {
                String text = readBom(path);
                if (name.endsWith(".yml")) {
                    String language = path.getParent().getFileName().toString();
                    Set<String> keys = languages.computeIfAbsent(language, ignored -> new HashSet<>());
                    require(text.lines().anyMatch(line -> line.strip().equals("l_" + language + ":")), "language header: " + name);
                    for (String line : text.lines().toList()) {
                        var match = LOC_KEY.matcher(line);
                        if (match.matches()) require(keys.add(match.group(1)), "duplicate localization: " + match.group(1));
                        else require(line.isBlank() || line.stripLeading().startsWith("#") || line.strip().equals("l_" + language + ":"), "unsupported/malformed localization line: " + name);
                    }
                } else {
                    List<String> tokens = tokenize(text, name);
                    List<String> top = topDefinitions(tokens);
                    if (name.startsWith("common/scripted_effects/")) {
                        require(!top.isEmpty() && top.size() <= 20, "scripted effect file must contain 1..20 effects: " + name);
                        for (String effect : top) require(effectDefinitions.add(effect), "duplicate effect: " + effect);
                        effects += top.size();
                    }
                    if (name.startsWith("common/") && !name.startsWith("common/on_action/")) {
                        String kind = Path.of(name).getName(1).toString();
                        Set<String> names = definitions.computeIfAbsent(kind, ignored -> new HashSet<>());
                        for (String id : top) require(names.add(id), "duplicate definition in " + kind + ": " + id);
                    }
                    if (name.startsWith("events/")) {
                        Set<String> names = definitions.computeIfAbsent("events", ignored -> new HashSet<>());
                        for (String id : top) require(names.add(id), "duplicate event: " + id);
                    }
                    for (int i = 0; i + 1 < tokens.size(); i++) {
                        String token = tokens.get(i);
                        if (token.startsWith("xfm_") && token.endsWith("_effect") && tokens.get(i + 1).equals("=")) effectCalls.add(token);
                    }
                    if (name.equals("descriptor.mod")) require(!tokens.contains("remote_file_id"), "inner descriptor must not contain Workshop ID");
                }
            }
        }
        require(files.contains("descriptor.mod"), "descriptor missing from allowlist");
        for (String runtimeRoot : ROOTS) {
            Path folder = root.resolve(runtimeRoot);
            if (!Files.exists(folder)) continue;
            try (var paths = Files.walk(folder)) {
                for (Path path : paths.toList()) {
                    require(!Files.isSymbolicLink(path), "runtime symlink: " + path);
                    if (Files.isRegularFile(path)) require(files.contains(root.relativize(path).toString().replace('\\', '/')), "unlisted runtime file: " + path);
                }
            }
        }
        require(effectDefinitions.containsAll(effectCalls), "undefined custom effects: " + difference(effectCalls, effectDefinitions));
        require(languages.containsKey("simp_chinese") && languages.containsKey("english"), "Chinese and English required");
        Set<String> chinese = languages.get("simp_chinese");
        require(!chinese.isEmpty(), "no localization keys");
        for (var language : languages.entrySet()) require(language.getValue().equals(chinese), "localization key mismatch: " + language.getKey());
        return new Report("STATIC_ONLY_NOT_ENGINE_OR_BUSINESS_PASS", files.size(), effects, chinese.size(), manifest.files());
    }

    static Path safeFile(Path root, String name) throws IOException {
        require(name != null && !name.isBlank() && !name.contains("\\") && !name.contains(":"), "invalid manifest path");
        Path relative = Path.of(name);
        require(!relative.isAbsolute() && !relative.normalize().startsWith("..") && relative.normalize().toString().replace('\\', '/').equals(name), "path traversal: " + name);
        Path path = root.resolve(relative);
        Path cursor = path;
        while (!cursor.equals(root)) {
            require(!Files.isSymbolicLink(cursor), "symlink in runtime path: " + name);
            cursor = cursor.getParent();
        }
        require(Files.isRegularFile(path) && path.toRealPath().startsWith(root), "missing/escaped runtime file: " + name);
        return path;
    }

    private static String readBom(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        require(bytes.length >= 3 && bytes[0] == BOM[0] && bytes[1] == BOM[1] && bytes[2] == BOM[2], "UTF-8 BOM missing: " + path);
        try {
            return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes, 3, bytes.length - 3)).toString();
        } catch (CharacterCodingException error) {
            throw new IOException("invalid UTF-8: " + path, error);
        }
    }

    private static List<String> tokenize(String text, String name) throws IOException {
        List<String> tokens = new ArrayList<>();
        int depth = 0;
        for (int i = 0; i < text.length();) {
            char c = text.charAt(i);
            if (Character.isWhitespace(c)) { i++; continue; }
            if (c == '#') { while (i < text.length() && text.charAt(i) != '\n') i++; continue; }
            if (c == '"') {
                i++;
                boolean closed = false;
                while (i < text.length()) {
                    char q = text.charAt(i++);
                    if (q == '\\') { if (i < text.length()) i++; }
                    else if (q == '"') { closed = true; break; }
                }
                require(closed, "unterminated quoted string: " + name);
                tokens.add("<quoted>");
            } else if (c == '{' || c == '}') {
                depth += c == '{' ? 1 : -1;
                require(depth >= 0, "unmatched close brace: " + name);
                tokens.add(String.valueOf(c)); i++;
            } else if (c == '=' || c == '<' || c == '>' || c == '!' || c == '?') {
                int begin = i++;
                if (i < text.length() && text.charAt(i) == '=') i++;
                tokens.add(text.substring(begin, i));
            } else {
                int begin = i++;
                while (i < text.length() && !Character.isWhitespace(text.charAt(i)) && "{}=<>!?\"#".indexOf(text.charAt(i)) < 0) i++;
                tokens.add(text.substring(begin, i));
            }
        }
        require(depth == 0, "unclosed brace: " + name);
        return tokens;
    }

    private static List<String> topDefinitions(List<String> tokens) {
        List<String> result = new ArrayList<>();
        int depth = 0;
        for (int i = 0; i < tokens.size(); i++) {
            String token = tokens.get(i);
            if (depth == 0 && i + 2 < tokens.size() && tokens.get(i + 1).equals("=") && tokens.get(i + 2).equals("{")) result.add(token);
            if (token.equals("{")) depth++;
            else if (token.equals("}")) depth--;
        }
        return result;
    }

    private static Set<String> difference(Set<String> left, Set<String> right) {
        Set<String> result = new HashSet<>(left); result.removeAll(right); return result;
    }
    static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}
