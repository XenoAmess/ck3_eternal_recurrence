package org.xar.ck3.rrf.acceptance;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.rrf.Clausewitz;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Kind;
import org.xar.ck3.rrf.ExpectedSelection;
import org.xar.ck3.rrf.ExpectedSelection.TenetKey;
import org.xar.ck3.rrf.Contracts.Definition;
import org.xar.ck3.rrf.Contracts.Group;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.ReleaseBuilder;
import org.xar.ck3.rrf.acceptance.FixtureContracts.CaseKind;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FileContent;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FilePin;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FreshSetup;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Manifest;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Receipt;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Request;

/** Emits inputs and read-only assertions; never submits an RRF action or launches the game. */
public final class FixtureEmitter {
    private static final String MAIN = "mod_religious_ritual_fusion/tools/src/main/";
    private static final List<String> COMMON = List.of("descriptor.mod", "common/scripted_triggers/rrfa_observation_triggers.txt", "common/script_values/rrfa_observation_values.txt", "events/rrfa_observation_events.txt");
    private static final List<String> FRESH = List.of("common/on_action/rrfa_fresh_startup.txt", "common/scripted_effects/rrfa_seed_effects.txt", "events/rrfa_seed_events.txt",
            "common/decisions/rrfa_observation_decisions.txt", "localization/english/rrfa_observation_l_english.yml", "localization/simp_chinese/rrfa_observation_l_simp_chinese.yml");
    private static final List<String> COLD = List.of("common/decisions/rrfa_cold_observation_decisions.txt",
            "localization/english/rrfa_observation_l_english.yml", "localization/simp_chinese/rrfa_observation_l_simp_chinese.yml");
    private static final List<TenetKey> TENETS = java.util.stream.Stream.concat(FixtureContracts.SOURCE_A.stream(), FixtureContracts.SOURCE_B.stream()).distinct().toList();
    private FixtureEmitter() { }
    public enum BusinessAcceptance { NOT_RUN }
    public record Emission(Path fixture, Path manifest, Path requestSnapshot, Manifest payload) { }
    public record Report(String fixture, FilePin manifest, FilePin request,
                         @com.fasterxml.jackson.annotation.JsonProperty("game_started") boolean gameStarted,
                         @com.fasterxml.jackson.annotation.JsonProperty("business_acceptance") BusinessAcceptance businessAcceptance) { }
    public static int run(String[] args) {
        try {
            Map<String, String> options = options(args);
            Request request = Json.read(Files.readAllBytes(Path.of(options.get("--inputs"))), Request.class);
            Emission emission = emit(Path.of(options.get("--repo-root")), Path.of(options.get("--output")), options.get("--machine-id"), request);
            System.out.println(new String(Json.write(new Report(emission.fixture().toString(), pin(emission.manifest()), pin(emission.requestSnapshot()), false, BusinessAcceptance.NOT_RUN)), StandardCharsets.UTF_8));
            return 0;
        } catch (IOException | IllegalArgumentException error) { System.err.println("RRF FIXTURE FAILED: " + error.getMessage()); return 1; }
    }
    public static Emission emit(Path repository, Path output, String machineId, Request request) throws IOException {
        FixtureContracts.machine(machineId);
        Path repo = repository.toRealPath(); Path destination = output.toAbsolutePath().normalize();
        FixtureContracts.DivorceRules divorce = ColdSnapshotReader.verifiedDivorceRules(request, machineId, repo);
        Path manifest = Path.of(destination + ".fixture.json"); Path snapshot = Path.of(destination + ".request.json");
        Path inputs = Path.of(destination + ".inputs.json");
        for (Path target : List.of(destination, manifest, snapshot, inputs)) if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) throw new IllegalArgumentException("unused fixture output required: " + target);
        Path producer = repo.resolve(MAIN);
        if (producer.startsWith(destination) || destination.startsWith(producer)) throw new IllegalArgumentException("fixture output overlaps producer sources");
        List<FilePin> pins = new ArrayList<>();
        for (String java : List.of("org/xar/ck3/rrf/acceptance/FixtureEmitter.java", "org/xar/ck3/rrf/acceptance/CompatibilityModEmitter.java", "org/xar/ck3/rrf/acceptance/FrozenFixtureReader.java", "org/xar/ck3/rrf/acceptance/FixtureContracts.java", "org/xar/ck3/rrf/acceptance/ColdSnapshotReader.java", "org/xar/ck3/rrf/ExpectedSelection.java", "org/xar/ck3/rrf/Json.java", "org/xar/ck3/rrf/Contracts.java", "org/xar/ck3/rrf/Clausewitz.java", "org/xar/ck3/rrf/ReleaseBuilder.java")) {
            Path path = producer.resolve("java").resolve(java); checkedResource(path, "/producer-source/" + java); pins.add(pin(path));
        }
        Path catalogPath = repo.resolve("mod_religious_ritual_fusion/catalog/generated-catalog.json");
        Catalog catalog = Json.read(Files.readAllBytes(catalogPath), Catalog.class);
        validateCatalog(catalog); request.expectedSelection().requireCatalog(catalog); pins.add(pin(catalogPath));
        for (org.xar.ck3.save.SaveContracts.Pin source : org.xar.ck3.save.ProducerSources.verify(repo).repositorySources()) {
            pins.add(new FilePin(source.path(), source.bytes(), source.sha256()));
        }
        Path evidence = producer.resolve("resources/acceptance/native-source-evidence.json"); checkedResource(evidence, "/acceptance/native-source-evidence.json"); pins.add(pin(evidence));
        List<String> assets = new ArrayList<>(COMMON);
        assets.addAll(request.kind() == CaseKind.COLD_RELOAD ? COLD : FRESH);
        if (request.kind() == CaseKind.UI_REJECTION) assets.add("common/scripted_effects/rrfa_family_preview_seed_effects.txt");
        if (request.setup() instanceof FixtureContracts.DesCompatibilitySetup) assets.add("common/on_action/rrfa_des_compatibility_observers.txt");
        Map<String, byte[]> payloads = new LinkedHashMap<>();
        for (String relative : assets) {
            Path template = producer.resolve("resources/acceptance").resolve(relative);
            byte[] original = checkedResource(template, "/acceptance/" + relative); pins.add(pin(template));
            String rendered = renderAsset(relative, original, request, divorce);
            payloads.put(relative, (relative.equals("descriptor.mod") ? rendered : "\ufeff" + rendered).getBytes(StandardCharsets.UTF_8));
        }
        payloads.put(FixtureContracts.REQUEST_FILE, Json.write(request));
        List<String> markers = switch (request.kind()) {
            case CORE -> List.of("RRFAT: TEST PASS fixture_ready", "RRFAT: TEST PASS " + request.mode().wire() + "_success_readback");
            case UI_REJECTION -> List.of("RRFAT: TEST PASS fixture_ready", "RRFAT: TEST PASS no_product_change_readback", "RRFAT: TEST PASS family_preview_input_ready_32");
            case COLD_RELOAD -> List.of("RRFAT: TEST PASS " + request.mode().wire() + "_persisted_readback");
        };
        if (request.setup() instanceof FixtureContracts.DesCompatibilitySetup) {
            markers = new ArrayList<>(markers);
            markers.add("RRFDES: OBSERVED PRE_DYNASTIC_BEFORE_ADOPTION");
            markers.add("RRFDES: OBSERVED POST_NONE_BEFORE_ADOPTION");
        }
        Files.createDirectories(destination);
        Map<String, FileContent> files = new LinkedHashMap<>();
        for (Map.Entry<String, byte[]> payload : payloads.entrySet()) {
            Path target = destination.resolve(payload.getKey()); Files.createDirectories(target.getParent()); Files.write(target, payload.getValue(), StandardOpenOption.CREATE_NEW);
            files.put(payload.getKey(), new FileContent(payload.getValue().length, ReleaseBuilder.sha256(payload.getValue())));
        }
        Manifest result = new Manifest("ck3-mod-acceptance-prebuilt-fixture-v1", "religious-ritual-fusion", request.kind().wire(), machineId, Instant.now().toString(), destination.toString(), pins, files, new Receipt(markers, Map.of(), request.kind() != CaseKind.COLD_RELOAD));
        Files.write(manifest, Json.write(result), StandardOpenOption.CREATE_NEW); Files.write(snapshot, Json.write(request), StandardOpenOption.CREATE_NEW);
        if (request.schemaVersion() >= 4) Files.write(inputs, Json.write(new FixtureContracts.PrebuiltInputs(
                "rrf-prebuilt-fixture-inputs-v1", pin(manifest), pin(destination.resolve(FixtureContracts.REQUEST_FILE)),
                ColdSnapshotReader.inputPins(request))), StandardOpenOption.CREATE_NEW);
        return new Emission(destination, manifest, snapshot, result);
    }
    private static String renderAsset(String relative, byte[] original, Request request, FixtureContracts.DivorceRules divorce) {
        String rendered = new String(original, StandardCharsets.UTF_8).replace("${CASE}", request.kind().wire()).replace("${MODE}", request.mode().wire()).replace("${COST}", Integer.toString(request.mode().cost()))
                .replace("${ACTOR_HISTORY_ID}", request.actorHistoryId().value())
                .replace("${SOURCE_A_CORE}", corePredicate(FixtureContracts.SOURCE_A))
                .replace("${SOURCE_B_CORE}", corePredicate(FixtureContracts.SOURCE_B))
                .replace("${EXPECTED_RESULT_CORE}", corePredicate(request.expectedSelection().coreTenets()))
                .replace("${EXPECTED_ORIGIN_CORE}", originPredicate(request.expectedSelection()))
                .replace("${PIETY_READBACK}", ColdSnapshotReader.walletPredicate(request))
                .replace("${EXPECTED_RESULT_DIVORCE}", "rite_has_doctrine = " + divorce.result().doctrine()
                        + "\n        NOT = { rite_has_doctrine = " + divorce.result().opposite().doctrine() + " }")
                .replace("${EXPECTED_ORIGIN_DIVORCE}", "is_target_in_variable_list = { name = rrf_origin_doctrines target = doctrine:" + divorce.origin().doctrine() + " }"
                        + "\n        NOT = { is_target_in_variable_list = { name = rrf_origin_doctrines target = doctrine:" + divorce.origin().opposite().doctrine() + " } }")
                .replace("${SOURCE_SHARED_ONE}", FixtureContracts.SOURCE_A.get(0).value())
                .replace("${SOURCE_SHARED_TWO}", FixtureContracts.SOURCE_A.get(1).value())
                .replace("${SOURCE_A_EXCLUSIVE}", FixtureContracts.SOURCE_A.get(2).value())
                .replace("${SOURCE_B_EXCLUSIVE}", FixtureContracts.SOURCE_B.get(2).value())
                .replace("${PIETY}", request.setup() instanceof FreshSetup fresh ? Integer.toString(fresh.piety()) : request.setup() instanceof FixtureContracts.DesCompatibilitySetup compatibility ? Integer.toString(compatibility.piety()) : "0")
                .replace("${EXPECTED_B}", request.mode() == FixtureContracts.Mode.RITE ? "rrfa_source_b_rite" : "rrfa_source_b_faith_rite")
                .replace("${UI_FAMILY_PREVIEW_SEED}", request.kind() == CaseKind.UI_REJECTION ? "rrfa_seed_family_preview_effect = yes" : "")
                .replace("${OBSERVATION_DECISION}", request.kind() == CaseKind.COLD_RELOAD ? "rrfa_observe_cold_decision" : "rrfa_observe_" + request.kind().wire() + "_decision")
                .replace("${OBSERVATION_EVENT}", request.kind() == CaseKind.COLD_RELOAD ? "rrfa.22" : request.kind() == CaseKind.UI_REJECTION ? "rrfa.30" : request.mode() == FixtureContracts.Mode.RITE ? "rrfa.20" : "rrfa.21");
        if (request.setup() instanceof FixtureContracts.DesCompatibilitySetup
                && relative.equals("common/scripted_effects/rrfa_seed_effects.txt")) {
            int[] created = {0};
            rendered = desSourcePrecondition(Clausewitz.parse(rendered), created).body() + "\n";
            if (created[0] != 3) throw new IllegalArgumentException("DES precondition requires exactly three isolated source factories");
        }
        if (request.kind() == CaseKind.UI_REJECTION && relative.startsWith("localization/")) {
            String label = relative.contains("/simp_chinese/") ? "验收家属 " : "Fixture family child ";
            StringBuilder names = new StringBuilder(rendered).append('\n');
            for (int index = 1; index <= 32; index++) {
                names.append(" rrfa_fixture_family_").append(String.format(java.util.Locale.ROOT, "%02d", index))
                        .append(":0 \"").append(label).append(index).append("\"\n");
            }
            rendered = names.toString();
        }
        if (rendered.contains("${")) throw new IllegalArgumentException("unresolved fixture template token");
        if (relative.endsWith(".txt")) validateCharacterPlacement(rendered);
        return rendered;
    }
    private static Clausewitz.Block desSourcePrecondition(Clausewitz.Block ast, int[] created) {
        List<Clausewitz.Entry> entries = new ArrayList<>();
        for (Clausewitz.Entry entry : ast.entries()) {
            if (!(entry.value() instanceof Clausewitz.Block body)) { entries.add(entry); continue; }
            Clausewitz.Block next = desSourcePrecondition(body, created);
            if (entry.key().equals("create_dynamic_rite")) {
                if (!List.of("rrfa_a", "rrfa_b", "rrfa_b_faith_rite").contains(body.atom("save_scope_as", ""))
                        || !body.atom("convert", "").equals("no") || !body.named("doctrine_override_entry").isEmpty())
                    throw new IllegalArgumentException("DES fixture may only prepare the three isolated stock source factories");
                List<Clausewitz.Entry> fields = new ArrayList<>(next.entries());
                fields.add(new Clausewitz.Entry("doctrine_override_entry", "=", new Clausewitz.Atom("doctrine:des_doctrine_dynastic")));
                next = new Clausewitz.Block(fields); created[0]++;
            }
            entries.add(new Clausewitz.Entry(entry.key(), entry.operator(), next));
        }
        return new Clausewitz.Block(entries);
    }
    /** Validate the exact declared provider projection through the existing shared byte consumer. */
    public static CompatibilityModEmitter.CompatibilityMod verifyDesProvider(FixtureContracts.DesCompatibilitySetup setup) throws IOException {
        var provider = CompatibilityModEmitter.verifySource(setup.provider());
        var header = Json.read(Files.readAllBytes(Path.of(provider.sourceManifest().path())), com.fasterxml.jackson.databind.JsonNode.class);
        if (!header.path("product_id").asText().equals("mod_dynastic_esotericism")
                || !header.path("workshop_item_id").asText().equals("3826991345"))
            throw new IOException("DES compatibility fixture requires the canonical DES projection");
        Path root = Path.of(provider.directory());
        Clausewitz.Block actions = Clausewitz.parse(Files.readString(root.resolve("common/on_action/des_on_actions.txt")));
        Clausewitz.Block parent = actions.block("xar_rite_creation_apply_optional_defaults_v2");
        boolean bridge = parent.block("on_actions").entries().stream().anyMatch(e -> e.value() instanceof Clausewitz.Atom atom
                && atom.token().equals("des_apply_registered_rite_creation_defaults_v2"));
        Clausewitz.Block child = actions.block("des_apply_registered_rite_creation_defaults_v2");
        Clausewitz.Block doctrines = Clausewitz.parse(Files.readString(root.resolve("common/religion/doctrine_types/des_doctrines.txt")));
        if (!bridge || !child.block("effect").atom("des_apply_registered_rite_creation_defaults_v2_effect", "").equals("yes")
                || doctrines.block("des_doctrine_none").entries().isEmpty() || doctrines.block("des_doctrine_dynastic").entries().isEmpty())
            throw new IOException("DES projection lacks the real v2 application bridge or required doctrines");
        return provider;
    }
    /** Re-render the two v6-specific assets from the actual embedded producer; rehash tampering is rejected. */
    static void validateDesPayload(Path repository, Path fixture, Request request, String machineId) throws IOException {
        if (!(request.setup() instanceof FixtureContracts.DesCompatibilitySetup)) return;
        var rules = ColdSnapshotReader.verifiedDivorceRules(request, machineId, repository);
        for (String relative : List.of("common/scripted_effects/rrfa_seed_effects.txt", "common/on_action/rrfa_des_compatibility_observers.txt")) {
            Path source = repository.resolve(MAIN).resolve("resources/acceptance").resolve(relative);
            byte[] original = checkedResource(source, "/acceptance/" + relative);
            byte[] expected = ("\ufeff" + renderAsset(relative, original, request, rules)).getBytes(StandardCharsets.UTF_8);
            if (!Arrays.equals(expected, Files.readAllBytes(fixture.resolve(relative))))
                throw new IOException("DES fixture differs from its actual producer: " + relative);
        }
    }
    public static void validateCatalog(Catalog catalog) {
        for (TenetKey key : TENETS) {
            String id = key.value();
            Definition definition = catalog.definitions().stream().filter(d -> d.id().equals(id)).findFirst().orElseThrow(() -> new IllegalArgumentException("fixture native tenet missing: " + id));
            if (definition.kind() != Kind.TENET || !definition.visible() || !definition.shown().isEmpty() || !(definition.canPick().isEmpty() || definition.canPick().equals("always = yes")) || !definition.requiresDlc().isEmpty() || !definition.blockedReasons().isEmpty()) throw new IllegalArgumentException("fixture simple-tenet assumption changed: " + id);
        }
        Group divorce = catalog.groups().stream().filter(g -> g.id().equals("doctrine_divorce")).findFirst().orElseThrow();
        if (!divorce.lock().equals("none") || !divorce.availableOnCreate().isEmpty()) throw new IllegalArgumentException("fixture divorce group changed");
        for (String id : List.of("doctrine_divorce_disallowed", "doctrine_divorce_allowed")) {
            Definition d = catalog.definitions().stream().filter(row -> row.id().equals(id)).findFirst().orElseThrow();
            if (!d.group().equals(divorce.id()) || !d.shown().isEmpty() || !d.canPick().isEmpty() || !d.requiresDlc().isEmpty() || !d.blockedReasons().isEmpty()) throw new IllegalArgumentException("fixture divorce doctrine changed: " + id);
        }
    }
    /** Membership and cardinality are both checked; duplicates cannot satisfy the observer. */
    public static String corePredicate(List<TenetKey> keys) {
        ExpectedSelection.unique(keys, "rendered core predicate");
        StringBuilder result = new StringBuilder("any_rite_tenet = { count = " + keys.size() + " }\n");
        for (TenetKey key : keys) result.append("    any_rite_tenet = { this = tenet:").append(key.value()).append(" }\n");
        result.append("    NOT = { any_rite_tenet = { NOR = { ");
        for (TenetKey key : keys) result.append("this = tenet:").append(key.value()).append(' ');
        return result.append("} } }").toString();
    }
    public static String originPredicate(ExpectedSelection selection) {
        StringBuilder result = new StringBuilder("variable_list_size = { name = rrf_origin_core_tenets value = " + selection.coreTenets().size() + " }\n");
        for (TenetKey key : selection.coreTenets()) result.append("        is_target_in_variable_list = { name = rrf_origin_core_tenets target = tenet:").append(key.value()).append(" }\n");
        result.append("        NOT = { any_in_list = { variable = rrf_origin_core_tenets NOR = { ");
        for (TenetKey key : selection.coreTenets()) result.append("this = tenet:").append(key.value()).append(' ');
        return result.append("} } }").toString();
    }
    /** CK3 creation placement accepts an employer or a location, never both. */
    public static void validateCharacterPlacement(String source) {
        validateCharacterPlacement(org.xar.ck3.rrf.Clausewitz.parse(source));
    }
    private static void validateCharacterPlacement(org.xar.ck3.rrf.Clausewitz.Block block) {
        for (org.xar.ck3.rrf.Clausewitz.Entry entry : block.entries()) {
            if (!(entry.value() instanceof org.xar.ck3.rrf.Clausewitz.Block child)) continue;
            if (entry.key().equals("create_character") && !child.named("location").isEmpty()
                    && !child.named("employer").isEmpty()) {
                throw new IllegalArgumentException("create_character cannot specify both location and employer");
            }
            validateCharacterPlacement(child);
        }
    }
    private static byte[] checkedResource(Path source, String resource) throws IOException {
        byte[] bytes = Files.readAllBytes(source);
        try (InputStream stream = FixtureEmitter.class.getResourceAsStream(resource)) { if (stream == null || !Arrays.equals(bytes, stream.readAllBytes())) throw new IOException("packaged producer/resource differs from current source: " + source); }
        return bytes;
    }
    private static FilePin pin(Path source) throws IOException { Path actual = source.toRealPath(); byte[] bytes = Files.readAllBytes(actual); return new FilePin(actual.toString(), bytes.length, ReleaseBuilder.sha256(bytes)); }
    private static Map<String, String> options(String[] args) {
        if (args.length != 8) throw new IllegalArgumentException("fixture requires --repo-root, --output, --machine-id, --inputs");
        Set<String> allowed = Set.of("--repo-root", "--output", "--machine-id", "--inputs"); Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < args.length; index += 2) if (!allowed.contains(args[index]) || args[index + 1].isBlank() || result.putIfAbsent(args[index], args[index + 1]) != null) throw new IllegalArgumentException("unknown/duplicate/empty fixture option");
        return Map.copyOf(result);
    }
}
