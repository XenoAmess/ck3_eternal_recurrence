package org.xar.ck3.dynastic.acceptance;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Emits an external CK3 fixture; the shared acceptance entry imports its frozen manifest. */
public final class FixtureEmitter {
    private static final String PRODUCT = "dynastic-esotericism";
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final List<String> ASSETS = List.of(
            "descriptor.mod",
            "common/on_action/des_acceptance_on_actions.txt",
            "common/decisions/des_acceptance_decisions.txt",
            "common/scripted_effects/des_acceptance_effects.txt",
            "events/des_acceptance_events.txt",
            "localization/english/des_acceptance_l_english.yml",
            "localization/simp_chinese/des_acceptance_l_simp_chinese.yml",
            "common/scripted_effects/des_acceptance_extended_effects.txt",
            "common/decisions/des_acceptance_extended_decisions.txt",
            "common/on_action/des_acceptance_extended_on_actions.txt",
            "events/des_acceptance_extended_events.txt",
            "localization/english/des_acceptance_extended_l_english.yml",
            "localization/simp_chinese/des_acceptance_extended_l_simp_chinese.yml");
    private static final String SEED_START = "common/on_action/des_acceptance_pre_product_seed.txt";
    private static final List<String> MARKERS = List.of(
            "DESAF: TEST PASS fixture_ready",
            "DESAF: TEST PASS binding_and_members",
            "DESAF: TEST PASS same_faith_apostasy",
            "DESAF: TEST PASS prisoner_control_ready",
            "DESAF: TEST PASS cross_faith_apostasy",
            "DESAF: TEST PASS repentance",
            "DESAF: TEST PASS closed_binding",
            "DESAF: TEST PASS reopened_binding",
            "DESAF: TEST PASS unchanged_unconverted_descendant",
            "DESAF: TEST PASS generated_next_day",
            "DESAF: TEST PASS cadet_and_house_correction",
            "DESAF: TEST PASS second_rite_binding",
            "DESAF: TEST PASS cross_rite_negative_pairs",
            "DESAF: TEST PASS cross_dynasty_migration",
            "DESAF: TEST PASS independent_crime_and_apostasy",
            "DESAF: TEST PASS independent_crime_retained",
            "DESAF: TEST PASS pardon_candidate",
            "DESAF: TEST PASS pardon_consumed",
            "DESAF: TEST PASS pardon_not_refreshed_31_days",
            "DESAF: TEST PASS join_after_founder_death",
            "DESAF: TEST PASS founder_death_and_head_change",
            "DESAF: TEST PASS two_periodic_callbacks",
            "DESAF: TEST PASS actual_birth_next_day",
            "DESAF: TEST PASS actual_primary_heir_successor");

    private FixtureEmitter() { }

    public enum CaseKind {
        CORE("core"), COLD_RELOAD("cold_reload"), OLD_SAVE_BOOTSTRAP("old_save_bootstrap"), PRE_PRODUCT_SEED("pre_product_seed");
        private final String value;
        CaseKind(String value) { this.value = value; }
        @JsonValue public String wireValue() { return value; }
        static CaseKind parse(String value) {
            for (CaseKind kind : values()) if (kind.value.equals(value)) return kind;
            throw new IllegalArgumentException("unknown fixture case");
        }
    }

    public record FilePin(String path, long bytes, String sha256) { }
    public record FileContent(long bytes, String sha256) { }
    public record FixtureReceipt(
            @JsonProperty("required_markers") List<String> requiredMarkers,
            @JsonProperty("required_product_markers_minimum") Map<String, Integer> minimumMarkers,
            @JsonProperty("fixture_contains_business_effects") boolean containsBusinessEffects) {
        public FixtureReceipt {
            requiredMarkers = List.copyOf(requiredMarkers);
            minimumMarkers = Map.copyOf(minimumMarkers);
        }
    }
    public record FixtureManifest(String schema, String product,
            @JsonProperty("case_id") String caseId,
            @JsonProperty("machine_id") String machineId,
            @JsonProperty("observed_at_utc") String observedAtUtc,
            @JsonProperty("fixture_root") String fixtureRoot,
            @JsonProperty("producer_source_pins") List<FilePin> producerSourcePins,
            Map<String, FileContent> files, FixtureReceipt receipt) {
        public FixtureManifest {
            producerSourcePins = List.copyOf(producerSourcePins);
            files = Map.copyOf(files);
        }
    }
    public record Emission(Path fixture, Path manifest, FixtureManifest payload) { }

    public static int run(String[] args) {
        try {
            Map<String, String> options = parse(args);
            Emission result = emit(Path.of(options.get("--repo-root")), Path.of(options.get("--output")),
                    options.get("--machine-id"), CaseKind.parse(options.getOrDefault("--case", "core")));
            System.out.println(JSON.writerWithDefaultPrettyPrinter().writeValueAsString(
                    new EmissionReport(result.fixture().toString(), pin(result.manifest()),
                            result.payload().files().size(), false, BusinessAcceptance.NOT_RUN)));
            return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("DES fixture emission failed: " + error.getMessage());
            return 1;
        }
    }

    public enum BusinessAcceptance { NOT_RUN }

    public record EmissionReport(String fixture, FilePin manifest, int files,
            @JsonProperty("game_started") boolean gameStarted,
            @JsonProperty("business_acceptance") BusinessAcceptance businessAcceptance) { }

    public static Emission emit(Path repository, Path output, String machineId) throws IOException {
        return emit(repository, output, machineId, CaseKind.CORE);
    }

    public static Emission emit(Path repository, Path output, String machineId, CaseKind kind) throws IOException {
        if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")) {
            throw new IllegalArgumentException("an observed stable machine ID is required");
        }
        Path repo = repository.toRealPath();
        Path destination = output.toAbsolutePath().normalize();
        Path manifest = Path.of(destination + ".fixture.json");
        if (Files.exists(destination, LinkOption.NOFOLLOW_LINKS) || Files.exists(manifest, LinkOption.NOFOLLOW_LINKS)) {
            throw new IllegalArgumentException("new fixture and manifest paths are required");
        }
        Path source = repo.resolve("mod_dynastic_esotericism/tools/src/main");
        List<FilePin> sources = new ArrayList<>();
        sources.add(pin(source.resolve("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java")));
        Map<String, byte[]> payloads = new LinkedHashMap<>();
        List<String> assets = kind == CaseKind.PRE_PRODUCT_SEED ? List.of("descriptor.mod", SEED_START)
                : kind == CaseKind.CORE ? ASSETS : ASSETS.stream()
                        .filter(name -> !name.equals("common/on_action/des_acceptance_on_actions.txt")).toList();
        for (String relative : assets) {
            Path template = source.resolve("resources/acceptance-fixture").resolve(relative);
            byte[] bytes = Files.readAllBytes(template);
            sources.add(pin(template));
            try (InputStream stream = FixtureEmitter.class.getResourceAsStream("/acceptance-fixture/" + relative)) {
                if (stream == null || !Arrays.equals(bytes, stream.readAllBytes())) {
                    throw new IOException("packaged fixture resource differs from current source: " + relative);
                }
            }
            payloads.put(relative, relative.equals("descriptor.mod") ? bytes.clone() : withBom(bytes));
        }
        Files.createDirectories(destination);
        Map<String, FileContent> files = new LinkedHashMap<>();
        for (Map.Entry<String, byte[]> entry : payloads.entrySet()) {
            Path target = destination.resolve(entry.getKey());
            Files.createDirectories(target.getParent());
            Files.write(target, entry.getValue(), StandardOpenOption.CREATE_NEW);
            files.put(entry.getKey(), new FileContent(entry.getValue().length, sha256(entry.getValue())));
        }
        List<String> markers = switch (kind) {
            case CORE -> MARKERS;
            case COLD_RELOAD -> List.of("DESAF: TEST PASS persisted_state_readback");
            case OLD_SAVE_BOOTSTRAP -> List.of("DESAF: TEST PASS legacy_uninitialized_observed", "DESAF: TEST PASS legacy_bootstrap");
            case PRE_PRODUCT_SEED -> List.of("DESAF: TEST PASS legacy_seed_ready");
        };
        FixtureManifest payload = new FixtureManifest("ck3-mod-acceptance-prebuilt-fixture-v1", PRODUCT, kind.wireValue(),
                machineId, Instant.now().toString(), destination.toString(), sources, files,
                new FixtureReceipt(markers, Map.of(), kind != CaseKind.PRE_PRODUCT_SEED));
        Files.writeString(manifest, JSON.writerWithDefaultPrettyPrinter().writeValueAsString(payload) + "\n",
                StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        return new Emission(destination, manifest, payload);
    }

    private static byte[] withBom(byte[] source) {
        if (source.length >= 3 && source[0] == (byte) 0xef && source[1] == (byte) 0xbb && source[2] == (byte) 0xbf) {
            return source.clone();
        }
        byte[] result = new byte[source.length + 3];
        result[0] = (byte) 0xef;
        result[1] = (byte) 0xbb;
        result[2] = (byte) 0xbf;
        System.arraycopy(source, 0, result, 3, source.length);
        return result;
    }

    private static FilePin pin(Path path) throws IOException {
        Path actual = path.toRealPath();
        byte[] bytes = Files.readAllBytes(actual);
        return new FilePin(actual.toString(), bytes.length, sha256(bytes));
    }

    private static String sha256(byte[] bytes) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("required SHA-256 provider is absent", error);
        }
    }

    private static Map<String, String> parse(String[] args) {
        if (args.length != 6 && args.length != 8) throw new IllegalArgumentException("expected --output, --repo-root, --machine-id and optional --case");
        Set<String> names = Set.of("--output", "--repo-root", "--machine-id", "--case");
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < args.length; index += 2) {
            if (!names.contains(args[index]) || args[index + 1].isBlank()
                    || result.putIfAbsent(args[index], args[index + 1]) != null) {
                throw new IllegalArgumentException("unknown, duplicate or empty fixture option");
            }
        }
        if (!result.keySet().containsAll(Set.of("--output", "--repo-root", "--machine-id"))) throw new IllegalArgumentException("missing fixture option");
        return Map.copyOf(result);
    }
}
