package org.xar.ck3.dynastic.release;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** File-format and exact-inventory checks; does not claim engine or gameplay validation. */
public final class StaticValidation {
    private static final byte[] BOM = {(byte) 0xef, (byte) 0xbb, (byte) 0xbf};
    private static final Pattern VERSION = Pattern.compile("(?m)^[ \\t]*version[ \\t]*=[ \\t]*\"([^\"\\r\\n]+)\"[ \\t]*(?:#[^\\r\\n]*)?$");
    private static final Pattern LOCALIZATION_KEY = Pattern.compile("(?m)^[ \\t]+([A-Za-z0-9_.-]+):[0-9]*[ \\t]+\"");

    private StaticValidation() { }

    public record ValidationReport(int fileCount, long totalBytes, String modVersion) { }

    public static ValidationReport validate(ReleaseProduct product, Path repository) throws IOException {
        Map<String, Path> files = inventory(product.source(), true);
        if (!files.keySet().equals(Set.copyOf(product.runtimeFiles()))) {
            Set<String> missing = new HashSet<>(product.runtimeFiles());
            missing.removeAll(files.keySet());
            Set<String> extra = new HashSet<>(files.keySet());
            extra.removeAll(product.runtimeFiles());
            throw new IllegalArgumentException("source inventory mismatch; missing=" + missing + ", extra=" + extra);
        }
        long bytes = 0;
        Set<String> english = Set.of();
        Set<String> chinese = Set.of();
        for (Map.Entry<String, Path> entry : files.entrySet()) {
            byte[] data = Files.readAllBytes(entry.getValue());
            bytes = Math.addExact(bytes, data.length);
            validateBytes(entry.getKey(), data);
            if (entry.getKey().equals("localization/english/des_l_english.yml")) english = localizationKeys(text(data), "l_english:");
            if (entry.getKey().equals("localization/simp_chinese/des_l_simp_chinese.yml")) chinese = localizationKeys(text(data), "l_simp_chinese:");
        }
        if (!english.equals(chinese)) throw new IllegalArgumentException("English and Chinese localization keys differ");
        String descriptor = Files.readString(product.source().resolve("descriptor.mod"), StandardCharsets.UTF_8);
        CompatibilityTags.label(descriptor, repository);
        return new ValidationReport(files.size(), bytes, descriptorVersion(descriptor));
    }

    public static Map<String, Path> inventory(Path root, boolean allowSourceOnly) throws IOException {
        if (!Files.isDirectory(root)) throw new IllegalArgumentException("tree root is not a directory: " + root);
        Map<String, Path> files = new TreeMap<>();
        Files.walkFileTree(root, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult preVisitDirectory(Path directory, BasicFileAttributes attributes) {
                String relative = relative(root, directory);
                return allowSourceOnly && ReleaseProduct.sourceOnly(relative) ? FileVisitResult.SKIP_SUBTREE : FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attributes) {
                String relative = relative(root, file);
                if (allowSourceOnly && ReleaseProduct.sourceOnly(relative)) return FileVisitResult.CONTINUE;
                if (!attributes.isRegularFile()) throw new IllegalArgumentException("runtime entry is not a regular file: " + relative);
                files.put(relative, file);
                return FileVisitResult.CONTINUE;
            }
        });
        return files;
    }

    public static void validateBytes(String relative, byte[] data) throws CharacterCodingException {
        if (relative.endsWith(".dds")) {
            if (data.length < 128 || data[0] != 'D' || data[1] != 'D' || data[2] != 'S' || data[3] != ' ') {
                throw new IllegalArgumentException("invalid DDS header: " + relative);
            }
            return;
        }
        if (relative.endsWith(".png")) {
            byte[] signature = {(byte) 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a};
            if (data.length < signature.length) throw new IllegalArgumentException("invalid PNG: " + relative);
            for (int index = 0; index < signature.length; index++) {
                if (data[index] != signature[index]) throw new IllegalArgumentException("invalid PNG: " + relative);
            }
            return;
        }
        if (!(relative.endsWith(".txt") || relative.endsWith(".gui") || relative.endsWith(".yml") || relative.endsWith(".mod"))) return;
        boolean bom = data.length >= 3 && data[0] == BOM[0] && data[1] == BOM[1] && data[2] == BOM[2];
        if (relative.equals("descriptor.mod") ? bom : !bom) {
            throw new IllegalArgumentException("invalid UTF-8 BOM policy: " + relative);
        }
        String value = text(data);
        if (value.contains("remote_file_id")) throw new IllegalArgumentException("internal runtime contains remote_file_id: " + relative);
        if (relative.endsWith(".txt") || relative.endsWith(".gui") || relative.endsWith(".mod")) balanced(value, relative);
    }

    public static String descriptorVersion(String descriptor) {
        Matcher matcher = VERSION.matcher(descriptor);
        if (!matcher.find()) throw new IllegalArgumentException("descriptor requires a numeric version");
        String result = matcher.group(1);
        if (matcher.find() || !ReleaseProduct.VERSION.matcher(result).matches()) throw new IllegalArgumentException("invalid or duplicate descriptor version");
        return result;
    }

    public static String text(byte[] data) throws CharacterCodingException {
        String result = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(data)).toString();
        return result.startsWith("\ufeff") ? result.substring(1) : result;
    }

    private static String relative(Path root, Path path) {
        return root.relativize(path).toString().replace('\\', '/');
    }

    private static Set<String> localizationKeys(String text, String header) {
        if (!text.startsWith(header + "\n") && !text.startsWith(header + "\r\n")) {
            throw new IllegalArgumentException("invalid localization header: " + header);
        }
        List<String> keys = new ArrayList<>();
        LOCALIZATION_KEY.matcher(text).results().forEach(result -> keys.add(result.group(1)));
        Set<String> unique = Set.copyOf(keys);
        if (unique.isEmpty() || unique.size() != keys.size()) throw new IllegalArgumentException("empty or duplicate localization keys: " + header);
        return unique;
    }

    private static void balanced(String text, String relative) {
        int depth = 0;
        boolean quoted = false;
        boolean comment = false;
        boolean escaped = false;
        for (int index = 0; index < text.length(); index++) {
            char value = text.charAt(index);
            if (comment) {
                if (value == '\n' || value == '\r') comment = false;
                continue;
            }
            if (quoted) {
                if (escaped) escaped = false;
                else if (value == '\\') escaped = true;
                else if (value == '"') quoted = false;
                continue;
            }
            if (value == '#') comment = true;
            else if (value == '"') quoted = true;
            else if (value == '{') depth++;
            else if (value == '}' && --depth < 0) throw new IllegalArgumentException("unmatched closing brace: " + relative);
        }
        if (quoted || depth != 0) throw new IllegalArgumentException("unclosed string or brace: " + relative);
    }
}
