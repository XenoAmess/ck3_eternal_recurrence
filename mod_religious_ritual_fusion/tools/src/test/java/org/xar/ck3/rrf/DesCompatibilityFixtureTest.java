package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.acceptance.CompatibilityModEmitter;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FixtureContracts.*;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader;

/** Real DES CLI -> complete provider -> opt-in producer -> public prepare -> frozen reader.
 * Only installation identity, plain configuration and dispatch timing are authored; no CK3 runs here. */
final class DesCompatibilityFixtureTest {
    @TempDir Path temporary;
    private static Path repository() { return Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent(); }
    private static Path configured(String name, Path fallback) { return Path.of(System.getenv().getOrDefault(name, fallback.toString())).toAbsolutePath().normalize(); }
    private static FilePin pin(Path file) throws IOException { Path p = file.toRealPath(); byte[] b = Files.readAllBytes(p); return new FilePin(p.toString(), b.length, ReleaseBuilder.sha256(b)); }
    private static ExpectedSelection selection() { return new ExpectedSelection(List.of(new ExpectedSelection.TenetKey("tenet_esotericism"), new ExpectedSelection.TenetKey("tenet_astrology"), new ExpectedSelection.TenetKey("tenet_communal_identity"))); }
    private static Request request(CompatibilityModEmitter.Source source) { return new Request(6, CaseKind.CORE, Mode.RITE, new ActorHistoryId("1128"), new DesCompatibilitySetup(1000, source), selection()); }
    private void command(List<String> arguments, String name) throws IOException, InterruptedException {
        Path log = temporary.resolve(name + ".log");
        Process process = new ProcessBuilder(arguments).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); fail("actual consumer timed out: " + name); }
        assertEquals(0, process.exitValue(), () -> { try { return Files.readString(log); } catch (IOException ex) { return ex.toString(); } });
    }
    @Test void explicitProviderCrossesActualPackagedProducerAndAllPublicConsumers() throws Exception {
        Path repo = repository();
        Path desJar = configured("DES_FIXTURE_CLI_JAR", repo.resolve("mod_dynastic_esotericism/tools/target/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar"));
        assertTrue(Files.isRegularFile(desJar), "The actual built DES CLI is required; absence is not a skip/pass");
        Path desSource = configured("DES_FIXTURE_SOURCE", repo.resolve("mod_dynastic_esotericism"));
        Path desGit = configured("DES_SOURCE_GIT_ROOT", repo);
        Path java = Path.of(System.getProperty("java.home"), "bin", "java");
        Path providerOutput = temporary.resolve("des-provider");
        command(List.of(java.toString(), "-Xmx256m", "-Djava.io.tmpdir=" + temporary, "-jar", desJar.toString(), "build", "--release-localization",
                "--source", desSource.toString(), "--repo-root", desGit.toString(), "--output", providerOutput.toString(), "--workshop-item-id", "3826991345"), "des-cli");
        var built = Json.read(Files.readAllBytes(temporary.resolve("des-cli.log")), com.fasterxml.jackson.databind.JsonNode.class);
        var source = new CompatibilityModEmitter.Source("dynastic_esotericism", Path.of(built.path("staging").asText()).toRealPath().toString(), pin(Path.of(built.path("manifest").asText())));
        Request request = request(source);
        assertEquals(request, Json.read(Json.write(request), Request.class));
        var provider = FixtureEmitter.verifyDesProvider((DesCompatibilitySetup) request.setup());
        var providerHeader = Json.read(Files.readAllBytes(Path.of(source.sourceManifest().path())), com.fasterxml.jackson.databind.JsonNode.class);
        assertTrue(providerHeader.path("files").isArray());
        assertTrue(built.path("fileCount").isIntegralNumber());
        assertEquals(providerHeader.path("files").size(), built.path("fileCount").intValue());
        var expectedProviderFiles = new LinkedHashMap<String, FilePin>();
        for (var entry : providerHeader.path("files")) {
            assertTrue(entry.path("path").isTextual());
            assertTrue(entry.path("size").isIntegralNumber());
            assertTrue(entry.path("sha256").isTextual());
            String relative = entry.path("path").textValue();
            FilePin actual = pin(Path.of(source.directory()).resolve(relative));
            assertEquals(entry.path("size").longValue(), actual.bytes(), relative);
            assertEquals(entry.path("sha256").textValue(), actual.sha256(), relative);
            assertNull(expectedProviderFiles.put(relative, actual), "duplicate provider path: " + relative);
        }
        assertEquals(expectedProviderFiles, provider.files());
        Path providerManifest = Path.of(source.sourceManifest().path());
        Path providerActions = Path.of(source.directory()).resolve("common/on_action/des_on_actions.txt");
        byte[] originalManifest = Files.readAllBytes(providerManifest), originalActions = Files.readAllBytes(providerActions);
        try {
            // Authored v1-only corruption of a real complete projection, with correct full-manifest hashes.
            var actions = Clausewitz.parse(new String(originalActions, StandardCharsets.UTF_8));
            Files.writeString(providerActions, new Clausewitz.Block(actions.entries().stream().filter(e -> !e.key().equals("xar_rite_creation_apply_optional_defaults_v2")).toList()).body());
            var header = Json.read(originalManifest, com.fasterxml.jackson.databind.JsonNode.class);
            for (var entry : header.path("files")) if (entry.path("path").asText().equals("common/on_action/des_on_actions.txt")) {
                var object = (com.fasterxml.jackson.databind.node.ObjectNode) entry;
                var changed = pin(providerActions); object.put(object.has("bytes") ? "bytes" : "size", changed.bytes()); object.put("sha256", changed.sha256());
            }
            Files.write(providerManifest, Json.write(header));
            var oldProvider = new CompatibilityModEmitter.Source(source.key(), source.directory(), pin(providerManifest));
            Path refused = temporary.resolve("v1-only-refused");
            assertThrows(IOException.class, () -> FixtureEmitter.emit(repo, refused, "authored-machine", request(oldProvider)));
            assertFalse(Files.exists(refused));
        } finally { Files.write(providerActions, originalActions); Files.write(providerManifest, originalManifest); }
        var release = new ReleaseBuilder().build(repo.resolve("mod_religious_ritual_fusion"), temporary.resolve("rrf-product"),
                new Contracts.ReleaseIdentity("3826756673", "authored-des-compatibility", "0".repeat(40)),
                new Contracts.Provenance(Contracts.ProvenanceKind.SYNTHETIC_FIXTURE, "authored-machine", "2026-11-20T00:00:00Z"));
        assertEquals(96, release.files());
        var compatibility = CompatibilityModEmitter.emit(new CompatibilityModEmitter.Request(1, "authored-machine", List.of(source)), temporary.resolve("compatibility"));
        assertFalse(compatibility.gameStarted());
        var emitted = FixtureEmitter.emit(repo, temporary.resolve("fixture"), "authored-machine", request);
        var binding = FrozenFixtureReader.read(pin(emitted.manifest()), "authored-machine", repo);
        assertEquals(12, emitted.payload().files().size());
        assertEquals(4, emitted.payload().receipt().requiredMarkers().size());
        String seed = Files.readString(emitted.fixture().resolve("common/scripted_effects/rrfa_seed_effects.txt"));
        assertEquals(3, factories(Clausewitz.parse(seed)).size());
        for (Clausewitz.Block factory : factories(Clausewitz.parse(seed))) {
            assertEquals("no", factory.atom("convert", ""));
            assertEquals("doctrine:des_doctrine_dynastic", factory.atom("doctrine_override_entry", ""));
        }
        observeActualPredicates(emitted.fixture());
        Path imported = temporary.resolve("public");
        String program = """
                from pathlib import Path
                import copy,json,sys
                from unittest.mock import patch
                repo,manifest,compat,product,output=map(Path,sys.argv[1:])
                sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
                import ck3_mod_acceptance_prepare as prepare
                from ck3_mod_acceptance_cases import generic_product_adapter as adapter
                output.mkdir()
                runtime=output/'authored-runtime.json';runtime.write_text(json.dumps({'machine_id':'authored-machine'}),encoding='utf-8')
                plain={}
                for i,name in enumerate(prepare.CONFIG_NAMES):
                    p=output/('plain-'+str(i));p.write_text('authored configuration',encoding='utf-8');plain[name]=prepare.pin(p)
                mods=json.loads(compat.read_bytes())['case_inputs']['compatibility_mods']
                inputs={'product_dir':str(product),'plain_configuration':plain,'compatibility_mods':mods,
                    'prebuilt_fixture_manifest':prepare.pin(manifest),'prebuilt_fixture_inputs':prepare.pin(Path(str(manifest).replace('.fixture.json','.inputs.json')))}
                checked=prepare.prebuilt_fixture_inputs(inputs)
                assert checked is not None
                for change in ('missing-provider','wrong-provider'):
                    bad=copy.deepcopy(inputs)
                    if change=='missing-provider':bad.pop('compatibility_mods')
                    else:bad['compatibility_mods'][0]['key']='other_provider'
                    try:prepare.prebuilt_fixture_inputs(bad)
                    except (ValueError,KeyError):pass
                    else:raise AssertionError('accepted '+change)
                config=json.loads((repo/'tools/ck3_mod_acceptance_cases/religious_ritual_fusion_core.json').read_bytes())
                context={'product':'religious-ritual-fusion','case':'core','repo_root':str(repo),'runtime_manifest':prepare.pin(runtime),
                    'state_dir':str(output/'state'),'output':str(output/'prepared'),'case_contract':config,'case_inputs':inputs}
                (output/'prepared').mkdir()
                with patch.object(prepare,'_engine',return_value=(None,{'game_version':'authored-no-game','exe_sha256':'0'*64})):
                    result=adapter.prepare_case(context)
                assert result['runtime_status']=='NOT_RUN' and result['business_pass'] is False and result['product_release_pass'] is False
                profile=Path(result['profile_preparation']['profile'])
                provider=next(row for row in mods if row['key']=='dynastic_esotericism')
                provider_root=profile/'mod-content/compat_dynastic_esotericism'
                actual_provider={p.relative_to(provider_root).as_posix():p.read_bytes()
                                 for p in provider_root.rglob('*') if p.is_file()}
                expected_provider={name:Path(row['path']).read_bytes() for name,row in provider['files'].items()}
                assert actual_provider==expected_provider
                assert json.loads((profile/'dlc_load.json').read_bytes())['enabled_mods']==['mod/compat_dynastic_esotericism.mod','mod/product.mod','mod/fixture.mod']
                compiled=json.loads((profile/'mod-content/fixture/_case_contract.json').read_bytes())
                assert len(compiled['required_markers'])==4 and len(compiled['compatibility_mods'])==1
                print('PASS; engine_semantics_verified=false')
                """;
        command(List.of(System.getProperty("dynastic.python", "python"), "-B", "-X", "utf8", "-c", program,
                repo.toString(), emitted.manifest().toString(), temporary.resolve("compatibility/compatibility-mods.json").toString(), release.staging(), imported.toString()), "public-prepare");
        Path prepared = imported.resolve("prepared/profile-preparation.json");
        assertNotNull(FrozenFixtureReader.readPrepared(pin(prepared), binding));
        var inventory = Json.read(Files.readAllBytes(prepared), com.fasterxml.jackson.databind.JsonNode.class);
        Path mounted = Path.of(inventory.path("profile_dir").asText()).resolve("mod-content/compat_dynastic_esotericism/common/on_action/des_on_actions.txt");
        Files.writeString(mounted, "# correctly located but wrong provider bytes\n");
        assertThrows(IOException.class, () -> FrozenFixtureReader.readPrepared(pin(prepared), binding));
        for (String asset : List.of("common/on_action/rrfa_des_compatibility_observers.txt", "common/scripted_effects/rrfa_seed_effects.txt")) {
            byte[] original = Files.readAllBytes(emitted.fixture().resolve(asset));
            String bad = asset.contains("on_action") ? new String(original, StandardCharsets.UTF_8).replace("var:rrf_state = flag:committing", "always = yes")
                    : new String(original, StandardCharsets.UTF_8).replace("doctrine:des_doctrine_dynastic", "doctrine:des_doctrine_none");
            assertFalse(bad.equals(new String(original, StandardCharsets.UTF_8)));
            Files.writeString(emitted.fixture().resolve(asset), bad);
            rehash(emitted, request);
            assertThrows(IOException.class, () -> FrozenFixtureReader.read(pin(emitted.manifest()), "authored-machine", repo), "Rehashing cannot bless a fake observer/precondition");
            Files.write(emitted.fixture().resolve(asset), original); rehash(emitted, request);
        }
        assertEquals(request, FrozenFixtureReader.read(pin(emitted.manifest()), "authored-machine", repo).request());
    }
    private static List<Clausewitz.Block> factories(Clausewitz.Block block) {
        List<Clausewitz.Block> result = new ArrayList<>();
        for (Clausewitz.Entry entry : block.entries()) if (entry.value() instanceof Clausewitz.Block child) {
            if (entry.key().equals("create_dynamic_rite")) result.add(child);
            result.addAll(factories(child));
        }
        return result;
    }
    private static void rehash(FixtureEmitter.Emission emitted, Request request) throws IOException {
        var old = emitted.payload(); var files = new LinkedHashMap<String, FileContent>();
        for (String name : old.files().keySet()) { FilePin p = pin(emitted.fixture().resolve(name)); files.put(name, new FileContent(p.bytes(), p.sha256())); }
        Files.write(emitted.manifest(), Json.write(new Manifest(old.schema(), old.product(), old.caseId(), old.machineId(), old.observedAtUtc(), old.fixtureRoot(), old.producerSourcePins(), files, old.receipt())));
        Files.write(Path.of(emitted.fixture() + ".inputs.json"), Json.write(new PrebuiltInputs("rrf-prebuilt-fixture-inputs-v1", pin(emitted.manifest()), pin(emitted.fixture().resolve(FixtureContracts.REQUEST_FILE)), List.of(((DesCompatibilitySetup) request.setup()).provider().sourceManifest()))));
    }
    private static void observeActualPredicates(Path fixture) throws IOException {
        var model = NativeSetupLifecycleTest.model(true);
        model.load(fixture.resolve("common/on_action/rrfa_des_compatibility_observers.txt"), NativeSetupLifecycleTest.SourceKind.ON_ACTIONS);
        model.state(model.actor).variables.put("rrf_state", new NativeSetupLifecycleTest.Token("flag:committing"));
        model.state(model.actor).variables.put("rrfa_source_a", new NativeSetupLifecycleTest.Reference(model.sourceA));
        model.state(model.actor).variables.put("rrfa_expected_b", new NativeSetupLifecycleTest.Reference(model.sourceB));
        model.state(model.actor).links.put("rite", model.sourceA);
        var dynastic = NativeSetupLifecycleTest.node(NativeSetupLifecycleTest.Kind.DOCTRINE, "des_doctrine_dynastic");
        var none = NativeSetupLifecycleTest.node(NativeSetupLifecycleTest.Kind.DOCTRINE, "des_doctrine_none");
        for (var rite : List.of(model.sourceA, model.sourceB, model.result)) { model.state(rite).doctrines.remove(none); model.state(rite).doctrines.add(dynastic); }
        model.effect("rrf_apply_creation_options_effect", model.actor);
        assertEquals(List.of("RRFDES: OBSERVED PRE_DYNASTIC_BEFORE_ADOPTION", "RRFDES: OBSERVED POST_NONE_BEFORE_ADOPTION"), model.diagnostics);
        assertTrue(model.state(model.result).doctrines.contains(none)); assertFalse(model.state(model.result).doctrines.contains(dynastic));
        assertTrue(model.state(model.sourceA).doctrines.contains(dynastic)); assertTrue(model.state(model.sourceB).doctrines.contains(dynastic));
        assertEquals(model.sourceA, model.state(model.actor).links.get("rite"));
        model.diagnostics.clear();
        // An observer scheduled before its provider or after adoption does not manufacture PASS.
        model.state(model.result).doctrines.remove(none); model.state(model.result).doctrines.add(dynastic);
        model.onAction("rrfa_des_observe_post", model.actor);
        model.state(model.actor).links.put("rite", model.result);
        model.onAction("rrfa_des_observe_pre", model.actor);
        model.onAction("rrfa_des_observe_post", model.actor);
        assertEquals(List.of("RRFDES: UNOBSERVED POST", "RRFDES: UNOBSERVED PRE", "RRFDES: UNOBSERVED POST"), model.diagnostics);
        // This model dispatch is authored and synchronous; it cannot qualify native scheduling or adoption.
    }
    @Test void versionSixCannotBeEnabledImplicitlyOrWithoutItsFundedCoreRite() {
        var source = new CompatibilityModEmitter.Source("dynastic_esotericism", temporary.toAbsolutePath().toString(), new FilePin(temporary.resolve("authored-unread-manifest").toAbsolutePath().toString(), 0, "0".repeat(64)));
        for (int version : List.of(3, 4, 5)) assertThrows(IllegalArgumentException.class, () -> new Request(version, CaseKind.CORE, Mode.RITE, new ActorHistoryId("1128"), new DesCompatibilitySetup(1000, source), selection()));
        assertThrows(IllegalArgumentException.class, () -> new Request(6, CaseKind.CORE, Mode.RITE, new ActorHistoryId("1128"), new FreshSetup(1000), selection()));
        assertThrows(IllegalArgumentException.class, () -> new Request(6, CaseKind.CORE, Mode.FAITH, new ActorHistoryId("1128"), new DesCompatibilitySetup(1000, source), selection()));
        assertThrows(IllegalArgumentException.class, () -> new Request(6, CaseKind.CORE, Mode.RITE, new ActorHistoryId("1128"), new DesCompatibilitySetup(499, source), selection()));
    }
}
