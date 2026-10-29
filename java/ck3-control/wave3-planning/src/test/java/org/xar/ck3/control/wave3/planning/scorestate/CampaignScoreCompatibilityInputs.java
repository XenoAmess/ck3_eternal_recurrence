package org.xar.ck3.control.wave3.planning.scorestate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Properties;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One R3 property contract for the preserved mechanical reference cohort; no SDK qualification. */
final class CampaignScoreCompatibilityInputs {
    private static final String SCHEMA = "xar.score-mechanical-reference-inputs/v1";
    private static final String SCOPE = "seven-named-score-consumers-reference-only/v1";
    private CampaignScoreCompatibilityInputs() { }

    enum Role {
        CANDIDATE("xar.score.compat.candidate", "SCORE_COMPATIBILITY_CANDIDATE", 24703,
                "65737d5a2082a83fe5c4ab63b057ce6d49f400a54f20bc8b661361acf6c598bf"),
        REFERENCE_CLIENT("xar.score.reference.client", "SCORE_REFERENCE_CLIENT", 201161,
                "0415281fd865bb7e9bbf68175caca2c6ee25a265f194ff5bb623870bea34c970");
        private final String pathProperty, fixtureName, sha256;
        private final long bytes;
        Role(String pathProperty, String fixtureName, long bytes, String sha256) {
            this.pathProperty = pathProperty; this.fixtureName = fixtureName; this.bytes = bytes; this.sha256 = sha256;
        }
        String pathProperty() { return pathProperty; }
        String bytesProperty() { return "xar.fullParity.fixture." + fixtureName + ".bytes"; }
        String shaProperty() { return pathProperty + ".sha256"; }
        void require(ExactRef ref) {
            Objects.requireNonNull(ref); absolute(ref.path());
            need(ref.bytes() == bytes && ref.sha256().equals(sha256), "Exact preserved reference role required: " + fixtureName);
        }
        ExactRef read(Properties properties) {
            String size = required(properties, bytesProperty());
            need(size.matches("[1-9][0-9]{0,6}"), "Canonical positive R3 byte count required");
            ExactRef result = new ExactRef(required(properties, pathProperty), Long.parseLong(size), required(properties, shaProperty()));
            require(result); return result;
        }
        void write(Properties properties, ExactRef ref) {
            require(ref); properties.setProperty(pathProperty, ref.path()); properties.setProperty(bytesProperty(), Long.toString(ref.bytes()));
            properties.setProperty(shaProperty(), ref.sha256());
        }
    }

    record SourcePin(String relativePath, long bytes, String sha256) {
        SourcePin {
            Objects.requireNonNull(relativePath); need(!Path.of(relativePath).isAbsolute() && !relativePath.contains(".."), "Relative original source required");
            need(bytes > 0 && bytes <= 1_048_576 && sha256 != null && sha256.matches("[a-f0-9]{64}"), "Finite original source pin required");
        }
        ExactRef at(Path repository) { return new ExactRef(repository.resolve(relativePath).toString(), bytes, sha256); }
    }
    private static final List<SourcePin> SOURCES = List.of(
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py", 22816, "ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d"),
            new SourcePin("ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py", 24758, "0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2"),
            new SourcePin("ck3_autonomous_player/tools/score_ck3_campaign.py", 17396, "ba6493478872ee6c100360b689d1eed4c8aca6aee40463b44a7bf1b3f849b212"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py", 49118, "ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e"),
            new SourcePin("tools/g2_saved_campaign/current_saved_basis_v1.py", 216548, "6fd69c6bbe958bde489ffe7f391aae690716c26c8ddbe48f82010a5a88261a1e"),
            new SourcePin("tools/g2_saved_campaign/file_stat_identity_v1.py", 2642, "b5c267b11d2b2b7933eec7a62092e29ec2e0d80a8342cab0c7818009385653d0"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/ck3_live_run_identity_v1.py", 2248, "b81c2a1f1e7c562981a1cc001ef65d454a52f4993b2783d3a5a468db84ced43b"));

    /** Pure recorded values. Historical decoding never opens or remeasures current files. */
    record Selected(Path python, Path repository, ExactRef candidate, ExactRef referenceClient) {
        Selected {
            Objects.requireNonNull(python); Objects.requireNonNull(repository);
            python = absolute(python.toString()); repository = absolute(repository.toString());
            Role.CANDIDATE.require(candidate); Role.REFERENCE_CLIENT.require(referenceClient);
            need(!Path.of(candidate.path()).equals(Path.of(referenceClient.path())), "Distinct candidate/reference roles required");
        }
        List<ExactRef> originalSources() { return SOURCES.stream().map(pin -> pin.at(repository)).toList(); }
        ObjectNode json() {
            ObjectNode n = StrictJson.object(); n.put("schema", SCHEMA).put("scope", SCOPE).put("python", python.toString()).put("repository_root", repository.toString());
            n.set("candidate", candidate.toJson()); n.set("reference_client", referenceClient.toJson());
            var originals = n.putArray("original_sources"); originalSources().forEach(ref -> originals.add(ref.toJson())); return n;
        }
        byte[] encode() { return StrictJson.canonical(json()); }
        Properties properties() {
            Properties result = new Properties(); result.setProperty("xar.python", python.toString()); result.setProperty("xar.repository.root", repository.toString());
            Role.CANDIDATE.write(result, candidate); Role.REFERENCE_CLIENT.write(result, referenceClient); return result;
        }
        void verifyActual() throws IOException {
            plain(python, 64L << 20); need(Files.isDirectory(repository, LinkOption.NOFOLLOW_LINKS) && repository.toRealPath().equals(repository), "Plain original repository required");
            verifyFile(candidate); verifyFile(referenceClient);
            for (ExactRef ref : originalSources()) verifyFile(ref);
        }
    }
    static Selected fromProperties(Properties properties) {
        Objects.requireNonNull(properties);
        return new Selected(absolute(required(properties, "xar.python")), absolute(required(properties, "xar.repository.root")), Role.CANDIDATE.read(properties), Role.REFERENCE_CLIENT.read(properties));
    }
    static Selected decode(byte[] raw) {
        need(raw.length > 0 && raw.length <= 16384, "Bounded mechanical-reference input required");
        ObjectNode n = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "scope", "python", "repository_root", "candidate", "reference_client", "original_sources"));
        need(SCHEMA.equals(StrictJson.text(n.get("schema"))) && SCOPE.equals(StrictJson.text(n.get("scope"))), "Exact reference-only schema/scope required");
        Selected result = new Selected(absolute(StrictJson.text(n.get("python"))), absolute(StrictJson.text(n.get("repository_root"))), file(n.get("candidate")), file(n.get("reference_client")));
        JsonNode originals = n.get("original_sources"); need(originals.isArray() && originals.size() == SOURCES.size(), "Complete ordered original source cohort required");
        for (int i = 0; i < SOURCES.size(); i++) need(file(originals.get(i)).equals(result.originalSources().get(i)), "Original source role differs");
        return result;
    }
    static byte[] verifyFile(ExactRef ref) throws IOException {
        Path path = absolute(ref.path()); plain(path, 1_048_576); need(Files.size(path) == ref.bytes(), "Exact reference byte count changed: " + path);
        byte[] raw = Files.readAllBytes(path); need(raw.length == ref.bytes() && digest(raw).equals(ref.sha256()), "Exact original source content changed: " + path);
        return raw;
    }
    private static void plain(Path path, long maximum) throws IOException {
        for (Path cursor = path; cursor != null; cursor = cursor.getParent()) need(!Files.isSymbolicLink(cursor), "Source link is not an exact plain input");
        need(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path) && Files.size(path) > 0 && Files.size(path) <= maximum, "Actual finite plain source required: " + path);
    }
    private static ExactRef file(JsonNode value) {
        ExactRef result = ExactRef.fromJson(value); absolute(result.path());
        need(result.bytes() > 0 && result.bytes() <= 1_048_576, "Finite original source reference required"); return result;
    }
    private static String digest(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static Path absolute(String value) {
        need(value != null && !value.isBlank() && value.length() <= 4096 && value.chars().noneMatch(c -> c < 32 || c == 127), "Bounded plain absolute source path required");
        Path path = Path.of(value); need(path.isAbsolute() && path.equals(path.normalize()), "Canonical absolute source path required"); return path;
    }
    private static String required(Properties properties, String name) {
        String value = properties.getProperty(name); need(value != null && !value.isBlank(), "NOT EXECUTED: mandatory typed R3 score property missing: " + name); return value;
    }
    private static void need(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}

