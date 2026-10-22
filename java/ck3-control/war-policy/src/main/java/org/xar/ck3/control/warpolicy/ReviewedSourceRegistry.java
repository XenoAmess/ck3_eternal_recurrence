package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable source knowledge. It never establishes loaded-game effects. */
public final class ReviewedSourceRegistry {
    public static final String SHA256 = "d4e4369d587fc9257100f8c366aa1f284a7d0e9f7333992843184fc76ef60930";
    public static final int MAX_BYTES = 16_384;
    private static final String RESOURCE = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_source_v1.json";
    private final String gameVersion;
    private final String executableSha256;
    private final String reviewedMachineId;
    private final String reviewedAtUtc;
    private final List<Source> sources;
    private final List<Profile> profiles;

    public enum Exposure {
        CONDITIONAL_TITLE_AND_VASSAL_CHANGE("conditional_title_and_vassal_change"),
        CONDITIONAL_IMPRISONMENT("conditional_imprisonment"),
        LIEGE_REVOKE_IMPRISON_BANISH_EXECUTE_REASONS("liege_revoke_imprison_banish_execute_reasons");
        private final String wire;
        Exposure(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Exposure fromJson(JsonNode value) {
            for (Exposure exposure : values()) {
                if (WarJson.textEquals(value, exposure.wire)) { return exposure; }
            }
            throw new ContractViolationException("unreviewed exposure label");
        }
    }

    public record Source(String path, String sha256, String definition, int lineStart, int lineEnd) {
        public Source {
            StrictJson.text(path); StrictJson.text(definition);
            require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "canonical source SHA-256 required");
            require(path.startsWith("common/") && !path.contains("\\")
                && !List.of(path.split("/", -1)).contains("..") && lineStart > 0 && lineEnd >= lineStart,
                "source path/range differs");
        }
    }
    public record Profile(String profileId, String canonicalKey, WarSide side,
            boolean requireObservedDefenderLiege, List<Exposure> exposures, List<String> sourcePaths) {
        public Profile {
            StrictJson.text(profileId); StrictJson.text(canonicalKey); Objects.requireNonNull(side, "profile side");
            exposures = List.copyOf(exposures); sourcePaths = List.copyOf(sourcePaths);
            require(!exposures.isEmpty() && !sourcePaths.isEmpty()
                && new HashSet<>(sourcePaths).size() == sourcePaths.size(), "profile sources/exposures incomplete");
        }
    }

    private ReviewedSourceRegistry(String gameVersion, String executableSha256,
            String reviewedMachineId, String reviewedAtUtc, List<Source> sources, List<Profile> profiles) {
        this.sources = List.copyOf(sources); this.profiles = List.copyOf(profiles);
        require(WarJson.GAME_VERSION.equals(gameVersion)
            && WarJson.EXECUTABLE_SHA256.toLowerCase(Locale.ROOT).equals(executableSha256), "reviewed registry build differs");
        StrictJson.text(reviewedMachineId); StrictJson.text(reviewedAtUtc);
        Set<String> sourcePaths = new HashSet<>();
        for (Source source : sources) { require(sourcePaths.add(source.path()), "duplicate source path"); }
        Set<String> profileKeys = new HashSet<>();
        for (Profile profile : profiles) {
            require(profileKeys.add(profile.canonicalKey() + "\n" + profile.side().wire())
                && sourcePaths.containsAll(profile.sourcePaths()), "duplicate or unbound profile");
        }
        require(!sources.isEmpty() && !profiles.isEmpty(), "nonempty registry required");
        this.gameVersion = gameVersion;
        this.executableSha256 = executableSha256;
        this.reviewedMachineId = reviewedMachineId;
        this.reviewedAtUtc = reviewedAtUtc;
    }

    public String gameVersion() { return gameVersion; }
    public String executableSha256() { return executableSha256; }
    public String reviewedMachineId() { return reviewedMachineId; }
    public String reviewedAtUtc() { return reviewedAtUtc; }
    public List<Source> sources() { return sources; }
    public List<Profile> profiles() { return profiles; }

    /** Reads only this module's reviewed bundled configuration, once at host setup. */
    public static ReviewedSourceRegistry bundled() {
        try (InputStream input = ReviewedSourceRegistry.class.getResourceAsStream(RESOURCE)) {
            if (input == null) { throw new IllegalStateException("reviewed war source resource is absent"); }
            return fromBytes(input.readNBytes(MAX_BYTES + 1));
        } catch (IOException error) {
            throw new IllegalStateException("reviewed war source resource cannot be read", error);
        }
    }

    public static ReviewedSourceRegistry fromBytes(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded source-registry bytes required");
        try {
            require(SHA256.equals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))),
                "source registry differs from reviewed exact bytes");
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "game_version",
            "executable_sha256", "review", "sources", "profiles", "source_tree_mermaid", "boundaries"));
        require(WarJson.textEquals(row.get("schema"), "g2.war-outcome-stakes-source/v1"), "source registry schema differs");
        StrictJson.text(row.get("source_tree_mermaid"));
        WarJson.array(row.get("boundaries"), "boundaries").elements().forEachRemaining(StrictJson::text);
        String version = StrictJson.text(row.get("game_version"));
        String executable = WarJson.sha(row.get("executable_sha256"));
        require(version.equals(WarJson.GAME_VERSION)
            && executable.equals(WarJson.EXECUTABLE_SHA256.toLowerCase(Locale.ROOT)), "source registry exact build differs");
        ObjectNode review = StrictJson.object(row.get("review"), Set.of("machine_id", "observed_at_utc", "source", "scope"));
        String machine = StrictJson.text(review.get("machine_id"));
        String observed = StrictJson.text(review.get("observed_at_utc"));
        require(observed.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"), "registry UTC spelling differs");
        List<Source> sources = new ArrayList<>();
        Set<String> paths = new HashSet<>();
        for (JsonNode source : WarJson.array(row.get("sources"), "sources")) {
            ObjectNode entry = StrictJson.object(source, Set.of("path", "sha256", "definition", "line_start", "line_end"));
            String path = StrictJson.text(entry.get("path"));
            int start = WarJson.positive32(entry.get("line_start"));
            int end = WarJson.positive32(entry.get("line_end"));
            require(path.startsWith("common/") && !path.contains("\\")
                && !List.of(path.split("/", -1)).contains("..") && end >= start, "source path/range differs");
            require(paths.add(path), "duplicate source path");
            sources.add(new Source(path, WarJson.sha(entry.get("sha256")), StrictJson.text(entry.get("definition")), start, end));
        }
        require(!sources.isEmpty(), "source set must be nonempty");
        List<Profile> profiles = new ArrayList<>();
        Set<String> identities = new HashSet<>();
        for (JsonNode profile : WarJson.array(row.get("profiles"), "profiles")) {
            ObjectNode entry = StrictJson.object(profile, Set.of("profile_id", "canonical_key", "player_side",
                "require_observed_defender_liege", "exposures", "source_paths"));
            List<String> references = new ArrayList<>();
            for (JsonNode path : WarJson.array(entry.get("source_paths"), "source_paths")) { references.add(StrictJson.text(path)); }
            List<Exposure> exposures = new ArrayList<>();
            for (JsonNode exposure : WarJson.array(entry.get("exposures"), "exposures")) { exposures.add(Exposure.fromJson(exposure)); }
            require(!references.isEmpty() && new HashSet<>(references).size() == references.size()
                && paths.containsAll(references) && !exposures.isEmpty(), "profile sources/exposures incomplete");
            String key = StrictJson.text(entry.get("canonical_key"));
            WarSide side = WarSide.fromJson(entry.get("player_side"));
            require(identities.add(key + "\n" + side.wire()), "duplicate CB/side profile");
            profiles.add(new Profile(StrictJson.text(entry.get("profile_id")), key, side,
                WarJson.bool(entry.get("require_observed_defender_liege")), exposures, references));
        }
        require(!profiles.isEmpty(), "profile set must be nonempty");
        return new ReviewedSourceRegistry(version, executable, machine, observed, sources, profiles);
    }
}
