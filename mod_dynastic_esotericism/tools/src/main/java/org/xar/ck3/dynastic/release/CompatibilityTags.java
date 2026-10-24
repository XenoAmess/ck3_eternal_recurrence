package org.xar.ck3.dynastic.release;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Reads the single publication registry; this Java builder owns no second version table. */
public final class CompatibilityTags {
    private static final String REGISTRY_PATH = "ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py";
    private static final Pattern REGISTRY = Pattern.compile("(?m)^CK3_WORKSHOP_VERSION_TAGS\\s*=\\s*\\{([^{}]*)}");
    private static final Pattern ENTRY = Pattern.compile("\"([0-9]+\\.[0-9]+)\"\\s*:\\s*(\"(?:[^\"\\\\]|\\\\.)*\")");
    private static final Pattern SUPPORTED = Pattern.compile("(?m)^\\s*supported_version\\s*=\\s*\"([^\"\\r\\n]+)\"\\s*(?:#[^\\r\\n]*)?$");
    private static final Pattern VERSION_ASSIGNMENT = Pattern.compile("(?m)^[ \\t]*supported_version[ \\t]*=");
    private static final Pattern VERSION = Pattern.compile("([0-9]+)\\.([0-9]+)(?:\\.(?:[0-9]+|\\*)){0,2}");
    private static final Pattern TAG_BLOCK = Pattern.compile("\\btags\\s*=\\s*\\{([^{}]*)}", Pattern.DOTALL);
    private static final Pattern STRING_OR_COMMENT = Pattern.compile("#[^\\r\\n]*|\"(?:[^\"\\\\]|\\\\.)*\"");
    private static final Pattern VERSION_TAG = Pattern.compile("[0-9]+\\.[0-9]+(?: '[^'\\r\\n]+')?");
    private static final ObjectMapper JSON = new ObjectMapper();

    private CompatibilityTags() { }

    public static byte[] render(byte[] descriptor, Path repository) throws IOException {
        String text = new String(descriptor, StandardCharsets.UTF_8);
        String label = label(text, repository);
        if (label == null) return descriptor.clone();
        Matcher block = TAG_BLOCK.matcher(text);
        if (!block.find()) throw new IllegalArgumentException("descriptor requires one tags block");
        int start = block.start(1);
        int end = block.end(1);
        String body = block.group(1);
        if (block.find()) throw new IllegalArgumentException("descriptor has duplicate tags blocks");
        List<String> tags = new ArrayList<>();
        Matcher tokens = STRING_OR_COMMENT.matcher(body);
        while (tokens.find()) {
            if (tokens.group().startsWith("\"")) {
                String tag = JSON.readValue(tokens.group(), String.class);
                if (tag.isEmpty()) throw new IllegalArgumentException("empty Workshop tag");
                if (!VERSION_TAG.matcher(tag).matches()) tags.add(tag);
            }
        }
        tags.add(label);
        StringBuilder rendered = new StringBuilder("\n");
        for (String tag : tags) rendered.append('\t').append(JSON.writeValueAsString(tag)).append('\n');
        return (text.substring(0, start) + rendered + text.substring(end)).getBytes(StandardCharsets.UTF_8);
    }

    /** Returns null only for versions older than 1.20, following the canonical registry policy. */
    public static String label(String descriptor, Path repository) throws IOException {
        Matcher supported = SUPPORTED.matcher(descriptor);
        if (!supported.find()) throw new IllegalArgumentException("descriptor requires one supported_version");
        String raw = supported.group(1);
        if (supported.find() || VERSION_ASSIGNMENT.matcher(descriptor).results().count() != 1) {
            throw new IllegalArgumentException("descriptor has duplicate supported_version");
        }
        Matcher version = VERSION.matcher(raw);
        if (!version.matches()) throw new IllegalArgumentException("invalid supported_version: " + raw);
        int major = Integer.parseInt(version.group(1));
        int minor = Integer.parseInt(version.group(2));
        if (major < 1 || (major == 1 && minor < 20)) return null;
        String key = major + "." + minor;
        String result = readRegistry(repository).get(key);
        if (result == null) throw new IllegalArgumentException("no confirmed Workshop compatibility tag for " + key);
        return result;
    }

    private static Map<String, String> readRegistry(Path repository) throws IOException {
        String text = Files.readString(repository.resolve(REGISTRY_PATH), StandardCharsets.UTF_8);
        Matcher registry = REGISTRY.matcher(text);
        if (!registry.find()) throw new IllegalArgumentException("canonical compatibility registry is not a literal table");
        String body = registry.group(1);
        if (registry.find()) throw new IllegalArgumentException("duplicate compatibility registry");
        Map<String, String> result = new LinkedHashMap<>();
        Matcher entry = ENTRY.matcher(body);
        int end = 0;
        while (entry.find()) {
            if (!body.substring(end, entry.start()).matches("[\\s,]*")) throw new IllegalArgumentException("unsupported registry expression");
            String value = JSON.readValue(entry.group(2), String.class);
            if (value.isEmpty() || result.putIfAbsent(entry.group(1), value) != null) {
                throw new IllegalArgumentException("invalid or duplicate compatibility registry entry");
            }
            end = entry.end();
        }
        if (result.isEmpty() || !body.substring(end).matches("[\\s,]*")) throw new IllegalArgumentException("unsupported compatibility registry table");
        return Map.copyOf(result);
    }
}
