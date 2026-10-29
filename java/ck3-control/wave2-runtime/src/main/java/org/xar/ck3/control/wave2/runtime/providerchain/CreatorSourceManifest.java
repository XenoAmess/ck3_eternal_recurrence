package org.xar.ck3.control.wave2.runtime.providerchain;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure value projection of _verified_entry_sources followed by _creator_digest. */
public record CreatorSourceManifest(List<CreatorSource> creators, List<ResolvedEntrySource> entries) {
    public enum CreatorTool {
        CANONICAL_CHAIN("canonical_native_provider_chain_v1.py"),
        OWNED_STDIO("mcp_owned_stdio_binding_v1.py"),
        PROCESS_CUSTODY("sdk_process_custody.py");
        private final String filename;
        CreatorTool(String filename) { this.filename = filename; }
        public String filename() { return filename; }
        public static CreatorTool fromFilename(String filename) {
            for (CreatorTool tool : values()) { if (tool.filename.equals(filename)) { return tool; } }
            throw new org.xar.ck3.control.contracts.ContractViolationException("unknown creator source filename");
        }
    }

    public record CreatorSource(CreatorTool tool, SourceSha256 sha256) {
        public CreatorSource {
            StrictJson.require(tool != null && sha256 != null, "complete creator source pin required");
        }
    }

    /** The caller's original reader must still resolve/open/hash this exact file. */
    public record ResolvedEntrySource(String path, SourceSha256 sha256) {
        public ResolvedEntrySource {
            requireAbsoluteWindows(path);
            StrictJson.require(sha256 != null, "entry source SHA-256 required");
        }
    }

    public CreatorSourceManifest {
        StrictJson.require(creators != null && creators.size() == CreatorTool.values().length,
                "all three creator source pins required");
        List<CreatorSource> creatorCopy = new ArrayList<>(creators);
        for (int index = 0; index < creatorCopy.size(); index++) {
            StrictJson.require(creatorCopy.get(index) != null && creatorCopy.get(index).tool() == CreatorTool.values()[index],
                    "original fixed creator source order required");
        }
        creators = List.copyOf(creatorCopy);
        StrictJson.require(entries != null && !entries.isEmpty() && entries.size() <= 8,
                "frozen entry source pins required");
        List<ResolvedEntrySource> selected = new ArrayList<>(entries);
        HashSet<String> paths = new HashSet<>();
        for (ResolvedEntrySource entry : selected) {
            StrictJson.require(entry != null && paths.add(entry.path()), "duplicate entry source");
        }
        selected.sort((left, right) -> pythonTextOrder(left.path(), right.path()));
        entries = List.copyOf(selected);
    }

    /** Python json.dumps((creator tuples, sorted entry tuples), ensure_ascii=True). */
    public byte[] originalManifestBytes() {
        StringBuilder json = new StringBuilder("[[");
        boolean first = true;
        for (CreatorSource source : creators) {
            if (!first) { json.append(','); } first = false;
            pair(source.tool().filename(), source.sha256().value(), json);
        }
        json.append("],["); first = true;
        for (ResolvedEntrySource entry : entries) {
            if (!first) { json.append(','); } first = false;
            pair(entry.path(), entry.sha256().value(), json);
        }
        json.append("]]");
        // Eight bounded paths and three fixed names already bound this projection.
        // Do not inherit a receipt transport cap for Python's ASCII-expanded digest bytes.
        return json.toString().getBytes(StandardCharsets.UTF_8);
    }

    public SourceSha256 creatorDigest() {
        try {
            return new SourceSha256(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(originalManifestBytes())));
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("JDK SHA-256 unavailable", impossible);
        }
    }

    public boolean grantsProviderSourceQualification() { return false; }

    static void requireAbsoluteWindows(String path) {
        StrictJson.text(path);
        String normalized = path.replace('/', '\\');
        boolean drive = normalized.length() >= 3 && normalized.charAt(1) == ':' && normalized.charAt(2) == '\\';
        boolean unc = false;
        if (normalized.startsWith("\\\\")) {
            int begin = normalized.regionMatches(true, 0, "\\\\?\\UNC\\", 0, 8) ? 8 : 2;
            int serverEnd = normalized.indexOf('\\', begin);
            if (serverEnd > begin) {
                int shareEnd = normalized.indexOf('\\', serverEnd + 1);
                unc = (shareEnd < 0 ? normalized.length() : shareEnd) > serverEnd + 1;
            }
        }
        StrictJson.require(drive || unc, "absolute source Windows path required");
    }

    private static int pythonTextOrder(String left, String right) {
        int li = 0, ri = 0;
        while (li < left.length() && ri < right.length()) {
            int lc = left.codePointAt(li), rc = right.codePointAt(ri);
            if (lc != rc) { return Integer.compare(lc, rc); }
            li += Character.charCount(lc); ri += Character.charCount(rc);
        }
        return Integer.compare(left.length() - li, right.length() - ri);
    }

    private static void pair(String first, String second, StringBuilder output) {
        output.append('['); asciiQuote(first, output); output.append(','); asciiQuote(second, output); output.append(']');
    }

    static void asciiQuote(String value, StringBuilder output) {
        output.append('"');
        String hex = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> output.append("\\\"");
                case '\\' -> output.append("\\\\");
                case '\b' -> output.append("\\b");
                case '\f' -> output.append("\\f");
                case '\n' -> output.append("\\n");
                case '\r' -> output.append("\\r");
                case '\t' -> output.append("\\t");
                default -> {
                    if (current < 0x20 || current > 0x7e) {
                        output.append("\\u");
                        output.append(hex.charAt((current >>> 12) & 15)).append(hex.charAt((current >>> 8) & 15))
                                .append(hex.charAt((current >>> 4) & 15)).append(hex.charAt(current & 15));
                    } else { output.append(current); }
                }
            }
        }
        output.append('"');
    }
}
