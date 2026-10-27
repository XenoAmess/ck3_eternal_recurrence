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
import java.util.Optional;
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
    private static final List<String> SECT_ASSETS = List.of(
            "descriptor.mod",
            "common/on_action/des_preset_acceptance_on_actions.txt",
            "common/decisions/des_preset_acceptance_decisions.txt",
            "localization/english/des_preset_acceptance_l_english.yml",
            "localization/simp_chinese/des_preset_acceptance_l_simp_chinese.yml");
    private static final List<String> SECT_MARKERS = List.of(
            "DESPAF: FIXTURE_ARMED sect_presets",
            "DESPAF: INPUT APPLIED procreation_adopt",
            "DESPAF: INPUT APPLIED procreation_leave",
            "DESPAF: INPUT APPLIED procreation_return",
            "DESPAF: INPUT APPLIED vivhite_adopt",
            "DESPAF: INPUT APPLIED old_procreation_reason",
            "DESPAF: INPUT APPLIED vivhite_join");
    private static final List<String> INITIAL_REFORM_ASSETS = List.of(
            "descriptor.mod",
            "common/on_action/des_initial_reform_acceptance_on_actions.txt",
            "common/scripted_effects/des_initial_reform_acceptance_effects.txt");
    private static final List<String> INITIAL_REFORM_MARKERS = List.of(
            "DESIRF: FIXTURE_ARMED initial_reform",
            "DESIRF: QUALIFICATION_INPUT_APPLIED initial_reform");
    private static final List<String> NATIVE_BINDING_TRANSFER_ASSETS = java.util.stream.Stream.concat(
            SECT_ASSETS.stream(), java.util.stream.Stream.of(
                    "common/scripted_effects/des_initial_reform_acceptance_effects.txt",
                    "common/decisions/des_transfer_acceptance_decisions.txt",
                    "localization/english/des_transfer_acceptance_l_english.yml",
                    "localization/simp_chinese/des_transfer_acceptance_l_simp_chinese.yml")).toList();
    private static final List<String> NATIVE_BINDING_TRANSFER_MARKERS = List.of(
            "DESPAF: FIXTURE_ARMED sect_presets",
            "DESPAF: INPUT APPLIED procreation_adopt",
            "DESPAF: INPUT APPLIED procreation_leave",
            "DESTRF: INPUT APPLIED qualification_and_stock_crime");
    private static final List<String> EMPIRE_HEAD_ASSETS = List.of(
            "descriptor.mod",
            "common/on_action/des_empire_heads_acceptance_on_actions.txt",
            "common/decisions/des_empire_heads_acceptance_decisions.txt",
            "events/des_empire_heads_acceptance_events.txt",
            "common/bookmarks/bookmarks/des_empire_1066_byzantium.txt",
            "localization/english/des_empire_heads_acceptance_l_english.yml",
            "localization/simp_chinese/des_empire_heads_acceptance_l_simp_chinese.yml");
    private static final List<String> EMPIRE_HEAD_PASSIVE_ASSETS = List.of(
            "descriptor.mod",
            "common/decisions/des_empire_heads_readback_decisions.txt",
            "localization/english/des_empire_heads_acceptance_l_english.yml",
            "localization/simp_chinese/des_empire_heads_acceptance_l_simp_chinese.yml");
    private static final List<String> EMPIRE_HEAD_INPUT_MARKERS = List.of(
            "DES_EHF: INPUT APPLIED adopted",
            "DES_EHF: INPUT APPLIED claim_preparation",
            "DES_EHF: INPUT APPLIED heir_preparation",
            "DES_EHF: OBSERVATION heir_ready",
            "DES_EHF: INPUT APPLIED death_staged",
            "DES_EHF: INPUT APPLIED predecessor_death",
            "DES_EHF: OBSERVATION successor_current");

    public enum EmpireHeadPreset {
        PROCREATION("des_procreation_faith", "des_procreation_rite", "e_des_procreation_papacy"),
        VIVHITE("des_vivhite_faith", "des_vivhite_rite", "e_des_vivhite_papacy");
        private final String faith;
        private final String rite;
        private final String title;
        EmpireHeadPreset(String faith, String rite, String title) {
            this.faith = faith;
            this.rite = rite;
            this.title = title;
        }
        public String faith() { return faith; }
        public String rite() { return rite; }
        public String title() { return title; }
    }

    private static final List<String> MARKERS = List.of(
            "DESAF: TEST PASS fixture_ready",
            "DESAF: TEST PASS binding_and_members",
            "DESAF: TEST PASS requested_head_cells",
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
        CORE("core"), COLD_RELOAD("cold_reload"), OLD_SAVE_BOOTSTRAP("old_save_bootstrap"),
        PRE_PRODUCT_SEED("pre_product_seed"), SECT_PRESETS("sect_presets"), INITIAL_REFORM("initial_reform"),
        EMPIRE_HEADS_PROCREATION("empire_heads_procreation"),
        EMPIRE_HEADS_VIVHITE("empire_heads_vivhite"),
        EMPIRE_HEADS_PROCREATION_COLD("empire_heads_procreation_cold"),
        EMPIRE_HEADS_VIVHITE_COLD("empire_heads_vivhite_cold"),
        EMPIRE_HEADS_PROCREATION_RESTORE("empire_heads_procreation_restore"),
        EMPIRE_HEADS_VIVHITE_RESTORE("empire_heads_vivhite_restore"),
        NATIVE_BINDING_TRANSFER("native_binding_transfer");
        private final String value;
        CaseKind(String value) { this.value = value; }
        @JsonValue public String wireValue() { return value; }
        public Optional<EmpireHeadPreset> empireHeadPreset() {
            return switch (this) {
                case EMPIRE_HEADS_PROCREATION, EMPIRE_HEADS_PROCREATION_COLD, EMPIRE_HEADS_PROCREATION_RESTORE ->
                        Optional.of(EmpireHeadPreset.PROCREATION);
                case EMPIRE_HEADS_VIVHITE, EMPIRE_HEADS_VIVHITE_COLD, EMPIRE_HEADS_VIVHITE_RESTORE ->
                        Optional.of(EmpireHeadPreset.VIVHITE);
                default -> Optional.empty();
            };
        }
        public boolean empireHeadFresh() {
            return this == EMPIRE_HEADS_PROCREATION || this == EMPIRE_HEADS_VIVHITE;
        }
        public boolean empireHeadRestore() {
            return this == EMPIRE_HEADS_PROCREATION_RESTORE || this == EMPIRE_HEADS_VIVHITE_RESTORE;
        }
        static CaseKind parse(String value) {
            for (CaseKind kind : values()) if (kind.value.equals(value)) return kind;
            throw new IllegalArgumentException("unknown fixture case");
        }
    }

    public record FrontendTarget(
            @JsonProperty("bookmark_key") String bookmarkKey,
            @JsonProperty("character_name_key") String characterNameKey,
            @JsonProperty("government_keys") List<String> governmentKeys,
            @JsonProperty("start_date_raw") int startDateRaw,
            @JsonProperty("bookmark_group_key") String bookmarkGroupKey,
            @JsonProperty("stock_history_id") int stockHistoryId) {
        public FrontendTarget { governmentKeys = List.copyOf(governmentKeys); }
    }
    public record StartupEventAdmission(String mode) { }
    public record FrontendScenario(
            @JsonProperty("profile_id") String profileId,
            @JsonProperty("frontend_target") FrontendTarget frontendTarget,
            @JsonProperty("startup_event_admission") StartupEventAdmission startupEventAdmission) { }
    public record EmpirePostStart(
            @JsonProperty("government_keys") List<String> governmentKeys,
            @JsonProperty("primary_title_tier_key") String primaryTitleTierKey,
            boolean independent) {
        public EmpirePostStart { governmentKeys = List.copyOf(governmentKeys); }
    }
    public static FrontendScenario empireFrontendScenario() {
        return new FrontendScenario("dynastic-esotericism-empire-byzantium-1066",
                new FrontendTarget("bm_des_empire_1066_byzantium",
                        "bookmark_des_empire_1066_konstantinos",
                        List.of("administrative_government", "feudal_government"),
                        0x032AEB08, "bm_group_1066", 1732),
                new StartupEventAdmission("none"));
    }
    public static EmpirePostStart empirePostStart() {
        return new EmpirePostStart(List.of("administrative_government", "feudal_government"), "empire", true);
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
                : kind == CaseKind.SECT_PRESETS ? SECT_ASSETS
                : kind == CaseKind.INITIAL_REFORM ? INITIAL_REFORM_ASSETS
                : kind == CaseKind.NATIVE_BINDING_TRANSFER ? NATIVE_BINDING_TRANSFER_ASSETS
                : kind.empireHeadPreset().isPresent() ? (kind.empireHeadFresh() ? EMPIRE_HEAD_ASSETS : EMPIRE_HEAD_PASSIVE_ASSETS)
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
            byte[] payload = renderEmpireHeadAsset(bytes, kind);
            payloads.put(relative, relative.equals("descriptor.mod") ? payload : withBom(payload));
        }
        if (kind == CaseKind.INITIAL_REFORM || kind == CaseKind.NATIVE_BINDING_TRANSFER) {
            // Exact provenance for the four copied qualification definitions and
            // the disclosed stock resource inputs. These references are not mounted.
            sources.add(pin(source.resolve("resources/acceptance-fixture/common/scripted_effects/des_acceptance_effects.txt")));
            sources.add(pin(source.resolve("resources/acceptance-fixture/events/des_acceptance_events.txt")));
        }
        if (kind.empireHeadFresh()) {
            Path caseSource = repo.resolve("tools/ck3_mod_acceptance_cases/dynastic_esotericism_"
                    + kind.wireValue() + ".json");
            var contract = JSON.readTree(Files.readAllBytes(caseSource));
            if (!JSON.valueToTree(empireFrontendScenario()).equals(contract.get("frontend_scenario"))
                    || !JSON.valueToTree(empirePostStart()).equals(contract.get("post_start"))) {
                throw new IllegalArgumentException("fresh Empire case differs from its closed Java frontend contract");
            }
            sources.add(pin(caseSource));
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
            case SECT_PRESETS -> SECT_MARKERS;
            case INITIAL_REFORM -> INITIAL_REFORM_MARKERS;
            case NATIVE_BINDING_TRANSFER -> NATIVE_BINDING_TRANSFER_MARKERS;
            case EMPIRE_HEADS_PROCREATION, EMPIRE_HEADS_VIVHITE,
                    EMPIRE_HEADS_PROCREATION_COLD, EMPIRE_HEADS_VIVHITE_COLD,
                    EMPIRE_HEADS_PROCREATION_RESTORE, EMPIRE_HEADS_VIVHITE_RESTORE -> empireHeadMarkers(kind);
            case COLD_RELOAD -> List.of("DESAF: TEST PASS persisted_state_readback");
            case OLD_SAVE_BOOTSTRAP -> List.of("DESAF: TEST PASS legacy_uninitialized_observed", "DESAF: TEST PASS legacy_bootstrap");
            case PRE_PRODUCT_SEED -> List.of("DESAF: TEST PASS legacy_seed_ready");
        };
        FixtureManifest payload = new FixtureManifest("ck3-mod-acceptance-prebuilt-fixture-v1", PRODUCT, kind.wireValue(),
                machineId, Instant.now().toString(), destination.toString(), sources, files,
                new FixtureReceipt(markers, Map.of(), kind != CaseKind.PRE_PRODUCT_SEED
                        && (kind.empireHeadPreset().isEmpty() || kind.empireHeadFresh())));
        Files.writeString(manifest, JSON.writerWithDefaultPrettyPrinter().writeValueAsString(payload) + "\n",
                StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        return new Emission(destination, manifest, payload);
    }

    private static byte[] renderEmpireHeadAsset(byte[] source, CaseKind kind) {
        Optional<EmpireHeadPreset> selected = kind.empireHeadPreset();
        if (selected.isEmpty()) return source.clone();
        EmpireHeadPreset preset = selected.orElseThrow();
        String rendered = new String(source, StandardCharsets.UTF_8)
                .replace("@DES_EHF_FAITH@", preset.faith())
                .replace("@DES_EHF_RITE@", preset.rite())
                .replace("@DES_EHF_TITLE@", preset.title())
                .replace("@DES_EHF_CASE@", kind.wireValue());
        if (rendered.contains("@DES_EHF_")) {
            throw new IllegalArgumentException("unresolved empire head fixture token");
        }
        return rendered.getBytes(StandardCharsets.UTF_8);
    }

    private static List<String> empireHeadMarkers(CaseKind kind) {
        if (kind.empireHeadFresh()) {
            return java.util.stream.Stream.concat(
                    java.util.stream.Stream.of("DES_EHF: FIXTURE_ARMED " + kind.wireValue()),
                    EMPIRE_HEAD_INPUT_MARKERS.stream()).toList();
        }
        return kind.empireHeadRestore()
                ? List.of("DES_EHF: OBSERVATION holderless_qualification", "DES_EHF: OBSERVATION current_head")
                : List.of("DES_EHF: OBSERVATION current_head");
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
