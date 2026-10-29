package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/** Exact existing source-index definition projection. Unindexed events retain the original unique-file scan. */
public final class OfflineEventSourceIndex {
    private static final String RESOURCE = "/sourcecatalog/offline-source-definitions-12004-v1.json";
    private static final String RESOURCE_SHA = "e234984c0195d47482d967fb82b57418e024b1697792fa540c17c0470785df6b";
    private record Definition(String relative, String sha256) { }
    public record Loaded(Path path, String relative, byte[] bytes) {
        public Loaded { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    private final Map<String, Definition> definitions;
    private OfflineEventSourceIndex(Map<String, Definition> definitions) { this.definitions = Map.copyOf(definitions); }
    public static OfflineEventSourceIndex currentBuild() throws IOException {
        byte[] raw;
        try (var stream = OfflineEventSourceIndex.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) throw new IOException("mandatory exact offline source-index resource missing");
            raw = stream.readNBytes(65_537);
        }
        require(raw.length <= 65_536 && sha(raw).equals(RESOURCE_SHA), "offline source-index projection source pin differs");
        ObjectValue root = RetainedJson.object(RetainedJson.parse(raw));
        require(eq(root, "schema", s("xar.events-offline-source-definitions/v1")) && eq(root, "build", s("1.20.0.4")), "offline source-index build differs");
        Map<String, Definition> definitions = new LinkedHashMap<>();
        for (ObjectValue row : objects(root, "definitions")) {
            require(row.fields().keySet().equals(Set.of("event_key", "relative_path", "sha256")), "exact offline definition row required");
            String key = text(row, "event_key"), relative = text(row, "relative_path"), digest = text(row, "sha256");
            require(key != null && key.matches("[A-Za-z0-9_]+\\.[0-9]+") && relative != null && relative.startsWith("events/")
                    && !relative.contains("\\") && !relative.contains(":") && !java.util.Arrays.asList(relative.split("/", -1)).contains("..")
                    && digest != null && digest.matches("[0-9a-f]{64}"), "valid fixed event source definition required");
            require(definitions.put(key, new Definition(relative, digest)) == null, "duplicate offline source definition");
        }
        require(definitions.size() == 196, "complete existing .3 definitions and three existing .4 additions required");
        return new OfflineEventSourceIndex(definitions);
    }

    public Loaded load(TrustedEventSourceContext trusted, ObjectValue before) throws IOException {
        SourceReviewedEventConsumer.NativeBinding binding = SourceReviewedEventConsumer.nativeBinding(before);
        trusted.requireBuild(binding.build()); Definition indexed = definitions.get(binding.eventKey());
        if (indexed != null) {
            Path path = trusted.stockGameDirectory().resolve(indexed.relative());
            byte[] raw = trusted.read(path, 2_097_152, TrustedEventSourceContext.FileRole.SOURCE);
            require(sha(raw).equals(indexed.sha256()), "exact vanilla source file bound/hash differs");
            return new Loaded(path, indexed.relative(), raw);
        }
        Pattern definition = Pattern.compile("^\\s*" + Pattern.quote(binding.eventKey()) + "\\s*=\\s*\\{",
                Pattern.MULTILINE | Pattern.UNIX_LINES | Pattern.UNICODE_CHARACTER_CLASS);
        List<Path> scanned;
        try (var walk = Files.walk(trusted.stockGameDirectory().resolve("events"))) { scanned = walk.limit(65_537).toList(); }
        require(scanned.size() <= 65_536, "bounded vanilla event source scan exceeded");
        Loaded found = null;
        for (Path path : scanned) {
            if (!path.getFileName().toString().endsWith(".txt") || !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) continue;
            byte[] raw = trusted.read(path, 2_097_152, TrustedEventSourceContext.FileRole.SOURCE);
            // This is only lexical candidate discovery, like rg. The actual selected source is decoded strictly by the analyzer.
            if (!definition.matcher(new String(raw, StandardCharsets.UTF_8)).find()) continue;
            require(found == null, "vanilla event definition missing or ambiguous");
            found = new Loaded(path, trusted.stockGameDirectory().relativize(path).toString().replace('\\', '/'), raw);
        }
        require(found != null, "vanilla event definition missing or ambiguous"); return found;
    }
}
