package org.xar.ck3.dynastic.release;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayDeque;
import java.util.Deque;
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
    // Same raw-entry and protected-token contract as tools/translate_localization_minimax.py.
    private static final Pattern RELEASE_ENTRY = Pattern.compile("^ ([^:\\s]+):0 \"((?:[^\"\\\\]|\\\\.)*)\"$");
    private static final Pattern ICU_PREFIX = Pattern.compile("^\\{[^{},]+,\\s*(?:plural|selectordinal|select)\\s*,");
    private static final Pattern PROTECTED = Pattern.compile(
            "https?://[^\\s<>\"'\\\\]+|<[^<>\\r\\n]+>|\\[[^\\[\\]\\r\\n]+\\]"
            + "|\\$\\{[^{}\\r\\n]+\\}|\\{\\{[^{}\\r\\n]+\\}\\}|\\{[^{}\\r\\n]+\\}|\\$[^$\\r\\n]+\\$"
            + "|@[A-Za-z0-9_.:/-]+!|#[A-Za-z0-9_]+|#!|\u00a7."
            + "|%(?:\\d+\\$)?[-+0#]*\\d*(?:\\.\\d+)?[hlLzjt]*[diuoxXfFeEgGaAcspn%]|\\\\.|\u2212100");
    private static final Set<String> RELEASE_KEYS = Set.of(
            "des_dynastic_membership_name", "des_dynastic_membership_desc", "des_doctrine_none_name", "des_doctrine_none_desc",
            "des_doctrine_dynastic_name", "des_doctrine_dynastic_desc", "doctrine_parameter_des_dynastic_membership",
            "trait_des_apostate", "trait_des_apostate_desc", "des_apostasy_opinion", "des_initialize_decision",
            "des_initialize_decision_desc", "des_initialize_decision_tooltip", "des_initialize_decision_confirm", "des_initialize_decision_effect");

    private enum LocalizationFamily {
        PRODUCT, SECTS, IDENTITY;
        private Set<String> keys() {
            return switch (this) {
                case PRODUCT -> RELEASE_KEYS;
                case SECTS -> SectPreset.localizationKeys();
                case IDENTITY -> Set.of("des_rite_dynasty_name");
            };
        }
        private String relative(ReleaseProduct.Language language) {
            return switch (this) {
                case PRODUCT -> language.relativePath();
                case SECTS -> language.sectRelativePath();
                case IDENTITY -> language.identityRelativePath();
            };
        }
    }

    private StaticValidation() { }

    public record ValidationReport(int fileCount, long totalBytes, String modVersion) { }

    public static ValidationReport validate(ReleaseProduct product, Path repository) throws IOException {
        Map<String, Path> files = inventory(product.source(), true);
        if (product.localizationMode() == ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION) {
            validateLocalization(product, product.source());
        } else if (product.productId().equals(ReleaseProduct.PRODUCT_ID)) {
            files.keySet().removeAll(ReleaseProduct.additionalLocalizationFiles());
        }
        if (!files.keySet().equals(Set.copyOf(product.runtimeFiles()))) {
            Set<String> missing = new HashSet<>(product.runtimeFiles());
            missing.removeAll(files.keySet());
            Set<String> extra = new HashSet<>(files.keySet());
            extra.removeAll(product.runtimeFiles());
            throw new IllegalArgumentException("source inventory mismatch; missing=" + missing + ", extra=" + extra);
        }
        long bytes = 0;
        for (Map.Entry<String, Path> entry : files.entrySet()) {
            byte[] data = Files.readAllBytes(entry.getValue());
            bytes = Math.addExact(bytes, data.length);
            validateBytes(entry.getKey(), data);
        }
        if (product.localizationMode() == ReleaseProduct.LocalizationMode.DEVELOPMENT) validateLocalization(product, product.source());
        SectPresetValidation.validate(product, product.source());
        String descriptor = Files.readString(product.source().resolve("descriptor.mod"), StandardCharsets.UTF_8);
        CompatibilityTags.label(descriptor, repository);
        return new ValidationReport(files.size(), bytes, descriptorVersion(descriptor));
    }

    /** Product-local format certification only; no non-Chinese semantic or game qualification. */
    public static void validateLocalization(ReleaseProduct product, Path root) throws IOException {
        if (!product.productId().equals(ReleaseProduct.PRODUCT_ID)) return;
        for (LocalizationFamily family : LocalizationFamily.values()) validateLocalizationFamily(product, root, family);
    }

    private static void validateLocalizationFamily(ReleaseProduct product, Path root, LocalizationFamily family) throws IOException {
        Set<String> keys = family.keys();
        Map<String, String> english = releaseEntries(root, ReleaseProduct.Language.ENGLISH, family);
        List<ReleaseProduct.Language> languages = product.localizationMode() == ReleaseProduct.LocalizationMode.DEVELOPMENT
                ? List.of(ReleaseProduct.Language.ENGLISH, ReleaseProduct.Language.SIMP_CHINESE) : List.of(ReleaseProduct.Language.values());
        for (ReleaseProduct.Language language : languages) {
            Map<String, String> entries = language == ReleaseProduct.Language.ENGLISH ? english : releaseEntries(root, language, family);
            if (family == LocalizationFamily.SECTS) SectPresetValidation.validateLocalizationAliases(entries);
            if (family == LocalizationFamily.IDENTITY && !"[des_identity_rite.GetNameNoTooltip]".equals(entries.get("des_rite_dynasty_name"))) {
                throw new IllegalArgumentException("identity localization must use the bound Rite's native name: " + language);
            }
            for (String key : keys) {
                if (language == ReleaseProduct.Language.SIMP_CHINESE && entries.get(key).isBlank()) {
                    throw new IllegalArgumentException("visible Chinese localization must not be empty: " + key);
                }
                if (!protectedTokens(english.get(key)).equals(protectedTokens(entries.get(key)))) {
                    throw new IllegalArgumentException("protected localization tokens differ: " + language + "/" + key);
                }
            }
        }
    }

    private static Map<String, String> releaseEntries(Path root, ReleaseProduct.Language language, LocalizationFamily family) throws IOException {
        String relative = family.relative(language);
        byte[] raw = Files.readAllBytes(root.resolve(relative));
        validateBytes(relative, raw);
        Map<String, String> result = new TreeMap<>();
        boolean header = false;
        for (String line : text(raw).split("\\R", -1)) {
            if (line.isEmpty() || line.stripLeading().startsWith("#")) continue;
            if (!header) {
                if (!line.equals(language.header())) throw new IllegalArgumentException("invalid release localization header: " + language);
                header = true;
                continue;
            }
            Matcher entry = RELEASE_ENTRY.matcher(line);
            if (!entry.matches()) throw new IllegalArgumentException("release localization requires :0 and a quoted single-line entry: " + language);
            if (result.putIfAbsent(entry.group(1), entry.group(2)) != null) {
                throw new IllegalArgumentException("duplicate release localization key: " + language + "/" + entry.group(1));
            }
        }
        if (!header || !result.keySet().equals(family.keys())) {
            throw new IllegalArgumentException("release localization requires the exact " + family.keys().size() + "-key " + family + " contract: " + language);
        }
        return Map.copyOf(result);
    }

    private static Map<String, Integer> protectedTokens(String value) {
        Map<String, Integer> counts = new TreeMap<>();
        PROTECTED.matcher(value).results().forEach(token -> counts.merge(token.group(), 1, Integer::sum));
        Deque<Integer> starts = new ArrayDeque<>();
        for (int index = 0; index < value.length(); index++) {
            if (value.charAt(index) == '{') starts.push(index);
            else if (value.charAt(index) == '}' && !starts.isEmpty()) {
                int start = starts.pop();
                if (starts.isEmpty()) {
                    String block = value.substring(start, index + 1);
                    if (ICU_PREFIX.matcher(block).find()) counts.merge(block, 1, Integer::sum);
                }
            }
        }
        return counts;
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
            validateDds(relative, data);
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

    private static void validateDds(String relative, byte[] data) {
        if (data.length < 128 || data[0] != 'D' || data[1] != 'D' || data[2] != 'S' || data[3] != ' ') throw new IllegalArgumentException("invalid DDS header: " + relative);
        ByteBuffer header = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        int flags = header.getInt(8);
        int height = header.getInt(12);
        int width = header.getInt(16);
        int mipmaps = Math.max(1, header.getInt(28));
        int pixelFlags = header.getInt(80);
        int fourcc = header.getInt(84);
        int bits = header.getInt(88);
        if (header.getInt(4) != 124 || header.getInt(76) != 32 || (flags & 0x1007) != 0x1007
                || width <= 0 || height <= 0 || width > 16384 || height > 16384 || (header.getInt(108) & 0x1000) == 0
                || header.getInt(112) != 0 || header.getInt(24) > 1 || header.getInt(28) < 0
                || mipmaps > 1 + (31 - Integer.numberOfLeadingZeros(Math.max(width, height)))) {
            throw new IllegalArgumentException("invalid DDS dimensions, flags or mipmaps: " + relative);
        }
        int blockBytes = 0;
        if ((pixelFlags & 4) != 0) {
            blockBytes = switch (fourcc) {
                case 0x31545844 -> 8; // DXT1
                case 0x33545844, 0x35545844 -> 16; // DXT3, DXT5
                default -> throw new IllegalArgumentException("unsupported DDS compression: " + relative);
            };
        } else if ((pixelFlags & 0x40) == 0 || bits != 32 || header.getInt(92) == 0 || header.getInt(96) == 0 || header.getInt(100) == 0) {
            throw new IllegalArgumentException("unsupported DDS pixel layout: " + relative);
        }
        long payload = 0;
        for (int level = 0; level < mipmaps; level++) {
            payload = Math.addExact(payload, blockBytes == 0 ? (long) width * height * 4 : (long) ((width + 3) / 4) * ((height + 3) / 4) * blockBytes);
            width = Math.max(1, width / 2);
            height = Math.max(1, height / 2);
        }
        if (data.length != 128 + payload) throw new IllegalArgumentException("DDS pixel payload length differs from its header: " + relative);
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
