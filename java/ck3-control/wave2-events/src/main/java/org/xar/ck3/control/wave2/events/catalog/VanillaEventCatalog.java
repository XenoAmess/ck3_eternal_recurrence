package org.xar.ck3.control.wave2.events.catalog;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Collections;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.StringValue;

/** Complete immutable original knowledge and actual discovery catalogs, loaded directly by Java. */
public final class VanillaEventCatalog {
    /** Maps and every nested RetainedJson value are immutable. Missing metadata keys remain missing. */
    public record Catalog(String ck3Build, Map<String, ObjectValue> contracts, Map<String, ObjectValue> analysis,
            Map<String, ObjectValue> observations) {
        public Catalog {
            Objects.requireNonNull(ck3Build);
            contracts = VanillaEventCatalogCodec.immutable(contracts);
            analysis = VanillaEventCatalogCodec.immutable(analysis);
            observations = VanillaEventCatalogCodec.immutable(observations);
        }
    }

    public record MigrationReference(int contracts, int analysis, int observations, String discoveryDatasetSha256) {
        public MigrationReference {
            StrictJson.require(contracts >= 0 && analysis >= 0 && observations >= 0, "actual producer counts are nonnegative");
            StrictJson.require(discoveryDatasetSha256 != null && discoveryDatasetSha256.matches("[A-F0-9]{64}"),
                    "actual original discovery digest required");
        }
    }

    /** Exact tables from the captured producer's Unicode version, independent of the host JDK's Unicode version. */
    public record TextRules(String unicodeVersion, Map<Integer, String> casefold, Set<Integer> whitespace) {
        public TextRules {
            StrictJson.require(unicodeVersion != null && unicodeVersion.matches("[0-9]+\\.[0-9]+\\.[0-9]+"),
                    "original producer Unicode version required");
            Objects.requireNonNull(casefold); Map<Integer, String> mappings = new LinkedHashMap<>();
            casefold.forEach((point, value) -> {
                scalar(Objects.requireNonNull(point)); new StringValue(value);
                StrictJson.require(!new String(Character.toChars(point)).equals(value), "nonidentity casefold mapping required");
                mappings.put(point, value);
            });
            casefold = Collections.unmodifiableMap(mappings);
            Objects.requireNonNull(whitespace); Set<Integer> spaces = new LinkedHashSet<>();
            whitespace.forEach(point -> { scalar(Objects.requireNonNull(point)); spaces.add(point); });
            whitespace = Collections.unmodifiableSet(spaces);
        }
        public String strip(String value) {
            new StringValue(value);
            int first = 0, last = value.length();
            while (first < last && whitespace.contains(value.codePointAt(first))) first += Character.charCount(value.codePointAt(first));
            while (last > first && whitespace.contains(value.codePointBefore(last))) last -= Character.charCount(value.codePointBefore(last));
            return value.substring(first, last);
        }
        public String fold(String value) {
            new StringValue(value); StringBuilder result = new StringBuilder();
            for (int at = 0; at < value.length();) {
                int point = value.codePointAt(at); String mapped = casefold.get(point);
                if (mapped == null) result.appendCodePoint(point); else result.append(mapped);
                at += Character.charCount(point);
            }
            return result.toString();
        }
        private static void scalar(int point) {
            StrictJson.require(Character.isValidCodePoint(point) && !(point >= 0xD800 && point <= 0xDFFF),
                    "actual Unicode scalar required");
        }
    }

    /** Frozen file facts are generated only from Root's actual one-time producer capture/readback. */
    record SourceFacts(String resource, int gzipBytes, String gzipSha256, int expandedBytes, String expandedSha256) {
        SourceFacts {
            StrictJson.require(resource != null && resource.startsWith("/") && !resource.contains("..")
                    && !resource.contains("\\"), "fixed relative classpath resource required");
            StrictJson.require(gzipBytes > 0 && expandedBytes > 0 && gzipBytes < (64 << 20) && expandedBytes < (64 << 20),
                    "bounded actual resource byte counts required");
            StrictJson.require(gzipSha256 != null && gzipSha256.matches("[a-f0-9]{64}")
                    && expandedSha256 != null && expandedSha256.matches("[a-f0-9]{64}"), "actual resource SHA256 facts required");
        }
    }

    private static final SourceFacts SOURCE = VanillaEventCatalogSourceFacts.SOURCE;
    private final VanillaEventCatalogCodec.Document document;
    private VanillaEventCatalog(VanillaEventCatalogCodec.Document document) { this.document = Objects.requireNonNull(document); }

    /** Resource absence, byte drift, malformed JSON or incomplete tables cannot create an empty usable provider. */
    public static VanillaEventCatalog load() throws IOException {
        try (InputStream input = VanillaEventCatalog.class.getResourceAsStream(SOURCE.resource())) {
            if (input == null) throw new IOException("complete vanilla event catalog resource is absent");
            byte[] compressed = input.readNBytes(SOURCE.gzipBytes() + 1);
            StrictJson.require(compressed.length == SOURCE.gzipBytes() && input.read() == -1,
                    "complete bounded original catalog resource required");
            return decode(compressed);
        }
    }

    /** Both immutable source hashes are checked before the complete internal model is constructed. */
    public static VanillaEventCatalog decode(byte[] compressed) throws IOException {
        Objects.requireNonNull(compressed);
        StrictJson.require(compressed.length == SOURCE.gzipBytes() && sha(compressed).equals(SOURCE.gzipSha256()),
                "complete original catalog gzip bytes drift");
        byte[] expanded;
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            expanded = gzip.readNBytes(SOURCE.expandedBytes() + 1);
            StrictJson.require(expanded.length == SOURCE.expandedBytes() && gzip.read() == -1,
                    "complete bounded original expanded catalog required");
        }
        StrictJson.require(sha(expanded).equals(SOURCE.expandedSha256()), "complete original expanded catalog bytes drift");
        return new VanillaEventCatalog(VanillaEventCatalogCodec.parse(expanded));
    }

    public String defaultBuild() { return document.defaultBuild(); }
    public String currentBuild() { return document.currentBuild(); }
    public Set<String> supportedBuilds() { return document.builds().keySet(); }
    public TextRules textRules() { return document.textRules(); }
    public Catalog catalog(String build) { return requireBuild(build).catalog(); }
    /** Complete query universe, including original unavailable/source-only rows; this is not the discovery keyset. */
    public Set<String> queryKeys(String build) { return requireBuild(build).knowledge().keySet(); }
    public MigrationReference migrationReference(String build) { return requireBuild(build).reference(); }

    /** The original complete ten-field response is retained, including unavailable rows with analyzed source data. */
    public ObjectValue fullQuery(String build, String key) {
        if (build == null || !document.builds().containsKey(build))
            return VanillaEventCatalogCodec.unavailable(build, null, key, "unsupported_ck3_build");
        VanillaEventCatalogCodec.BuildData actual = document.builds().get(build);
        if (key == null || document.textRules().strip(key).isEmpty())
            return VanillaEventCatalogCodec.unavailable(build, actual.executableSha256(), key, "invalid_event_definition_key");
        VanillaEventCatalogCodec.KnowledgeRow row = actual.knowledge().get(key);
        return row == null ? actual.unregisteredQuery().with("event_definition_key", new StringValue(key)) : row.original();
    }

    static SourceFacts sourceFacts() { return SOURCE; }
    private VanillaEventCatalogCodec.BuildData requireBuild(String build) {
        StrictJson.require(build != null && document.builds().containsKey(build), "unsupported exact vanilla event catalog build");
        return document.builds().get(build);
    }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
}
