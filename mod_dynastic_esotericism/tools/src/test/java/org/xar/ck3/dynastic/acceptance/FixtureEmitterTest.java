package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class FixtureEmitterTest {
    @TempDir Path temporary;

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    @Test
    void realProducerWritesExactManifestAndSeparateFixture() throws IOException, NoSuchAlgorithmException {
        FixtureEmitter.Emission result = FixtureEmitter.emit(repository(), temporary.resolve("fixture"), "authored-machine");
        JsonNode decoded = new ObjectMapper().readTree(result.manifest().toFile());
        assertEquals("ck3-mod-acceptance-prebuilt-fixture-v1", decoded.path("schema").textValue());
        assertEquals("dynastic-esotericism", decoded.path("product").textValue());
        assertEquals("core", decoded.path("case_id").textValue());
        assertEquals("authored-machine", decoded.path("machine_id").textValue());
        assertEquals(13, decoded.path("files").size());
        assertEquals(14, decoded.path("producer_source_pins").size());
        assertEquals(22, decoded.path("receipt").path("required_markers").size());
        assertTrue(decoded.path("receipt").path("fixture_contains_business_effects").booleanValue());
        for (var entry : result.payload().files().entrySet()) {
            byte[] bytes = Files.readAllBytes(result.fixture().resolve(entry.getKey()));
            assertEquals(bytes.length, entry.getValue().bytes());
            assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),
                    entry.getValue().sha256());
            if (entry.getKey().equals("descriptor.mod")) {
                assertEquals('n', bytes[0]);
            } else {
                assertArrayEquals(new byte[]{(byte) 0xef, (byte) 0xbb, (byte) 0xbf},
                        new byte[]{bytes[0], bytes[1], bytes[2]});
            }
        }
        assertFalse(Files.exists(result.fixture().resolve("_case_contract.json")));
        String events = Files.readString(result.fixture().resolve("events/des_acceptance_events.txt"), StandardCharsets.UTF_8);
        assertTrue(events.contains("rite_has_doctrine = des_doctrine_none"));
        assertTrue(events.contains("des_has_active_binding_trigger = yes"));
        String decisions = Files.readString(result.fixture().resolve("common/decisions/des_acceptance_decisions.txt"), StandardCharsets.UTF_8);
        assertTrue(decisions.contains("set_character_rite = rite:byzantine_rite"));
        assertFalse(events.contains("add_trait = des_apostate"));
        assertFalse(events.contains("des_sync_character_effect = yes"));
        assertThrows(IllegalArgumentException.class,
                () -> FixtureEmitter.emit(repository(), result.fixture(), "authored-machine"));
    }

    @Test
    void passiveColdAndBootstrapKeepNoColdRegistrarAndSeedHasNoProductState() throws IOException {
        for (FixtureEmitter.CaseKind kind : new FixtureEmitter.CaseKind[]{
                FixtureEmitter.CaseKind.COLD_RELOAD, FixtureEmitter.CaseKind.OLD_SAVE_BOOTSTRAP}) {
            FixtureEmitter.Emission result = FixtureEmitter.emit(repository(), temporary.resolve(kind.wireValue()), "authored-machine", kind);
            assertEquals(kind.wireValue(), result.payload().caseId());
            assertEquals(12, result.payload().files().size());
            for (String name : result.payload().files().keySet()) {
                if (name.endsWith(".txt")) {
                    assertFalse(Files.readString(result.fixture().resolve(name)).contains("on_game_start_after_lobby"));
                }
            }
        }
        FixtureEmitter.Emission seed = FixtureEmitter.emit(repository(), temporary.resolve("seed"), "authored-machine", FixtureEmitter.CaseKind.PRE_PRODUCT_SEED);
        assertEquals(2, seed.payload().files().size());
        assertFalse(seed.payload().receipt().containsBusinessEffects());
        String input = Files.readString(seed.fixture().resolve("common/on_action/des_acceptance_pre_product_seed.txt"));
        assertFalse(input.contains("set_variable"));
        assertFalse(input.contains("des_initialized"));
    }

    @Test
    void rejectsChangedFixtureSourcesBeforeEmittingFromPackagedResources() throws IOException {
        List<String> changedResources = List.of(
                "common/scripted_effects/des_acceptance_effects.txt",
                "common/scripted_effects/des_acceptance_extended_effects.txt",
                "events/des_acceptance_events.txt",
                "events/des_acceptance_extended_events.txt");
        for (int index = 0; index < changedResources.size(); index++) {
            String relative = changedResources.get(index);
            Path copiedRepository = temporary.resolve("changed-source-" + index);
            copyFixtureInputs(copiedRepository);
            Path changed = copiedRepository.resolve("mod_dynastic_esotericism/tools/src/main/resources/acceptance-fixture")
                    .resolve(relative);
            Files.writeString(changed, "\n", StandardCharsets.UTF_8, StandardOpenOption.APPEND);
            Path output = temporary.resolve("rejected-fixture-" + index);

            IOException failure = assertThrows(IOException.class,
                    () -> FixtureEmitter.emit(copiedRepository, output, "authored-machine"));

            assertEquals("packaged fixture resource differs from current source: " + relative, failure.getMessage());
            assertFalse(Files.exists(output));
            assertFalse(Files.exists(Path.of(output + ".fixture.json")));
        }
    }

    @Test
    void realFixtureDefinesLiteralMarkersAndRetainsTheActualR0004Guards()
            throws IOException, InterruptedException, NoSuchAlgorithmException {
        FixtureEmitter.Emission current = FixtureEmitter.emit(repository(), temporary.resolve("literal-markers"), "authored-machine");
        Path baseline = temporary.resolve("r0004-guard-baseline.json");
        copyTestResource("guard-baseline.json", baseline);
        ProbeResult accepted = probeFixture(current, baseline);
        assertEquals(0, accepted.exitCode(), accepted.output());
        JsonNode observation = new ObjectMapper().readTree(accepted.output());
        assertEquals(current.payload().receipt().requiredMarkers().size(), observation.path("required_marker_count").intValue());
        assertEquals(2, observation.path("unchanged_guard_count").intValue());
        assertTrue(observation.path("original_rite_readback_only_observes").booleanValue());

        FixtureEmitter.Emission failedR0004 = FixtureEmitter.emit(repository(), temporary.resolve("original-r0004"), "authored-machine");
        JsonNode sources = new ObjectMapper().readTree(baseline.toFile()).path("original_fixture_sources");
        for (JsonNode source : sources) {
            String relative = source.path("path").textValue();
            Path restored = failedR0004.fixture().resolve(relative);
            copyTestResource("original/" + relative, restored);
            byte[] raw = Files.readAllBytes(restored);
            assertEquals(source.path("bytes").longValue(), raw.length);
            assertEquals(source.path("sha256").textValue(),
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        }
        ProbeResult rejected = probeFixture(failedR0004, baseline);
        assertNotEquals(0, rejected.exitCode(), rejected.output());
        JsonNode failure = new ObjectMapper().readTree(rejected.output());
        assertEquals("NON_LITERAL_DEBUG_LOG", failure.path("reason").textValue());
        assertEquals(4, failure.path("non_literal_count").intValue());
    }

    private static void copyTestResource(String relative, Path destination) throws IOException {
        try (InputStream source = FixtureEmitterTest.class.getResourceAsStream("/acceptance-r0004/" + relative)) {
            if (source == null) throw new IOException("missing actual R0004 regression resource: " + relative);
            Files.copy(source, destination, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static ProbeResult probeFixture(FixtureEmitter.Emission fixture, Path baseline)
            throws IOException, InterruptedException {
        String program = """
                import io,json,sys
                from pathlib import Path
                repository,fixture,manifest,baseline=map(Path,sys.argv[1:])
                sys.path.insert(0,str(repository/'ck3_autonomous_player/src'))
                from xar_autoplayer.campaign_score_save_reader import melt_tokens
                sys.path.insert(0,str(repository/'tools/lyd_i3b_checkpoint_readback/reader/dependencies'))
                from bounded_save_parser import parse_block,one
                def reject(reason,**details):
                    print(json.dumps({'status':'REJECTED','reason':reason,**details}))
                    sys.exit(1)
                def script(path):
                    raw=path.read_text(encoding='utf-8-sig').encode('utf-8')
                    return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(raw)))+' }')
                literals=[]
                non_literal=[]
                def logs(entries,source):
                    for row in entries:
                        value=row['value']
                        if row['key']=='debug_log':
                            if not isinstance(value,str) or not value.startswith(chr(34)) or not value.endswith(chr(34)):
                                non_literal.append({'source':source,'value':value})
                            else:
                                literals.append(json.loads(value))
                        if isinstance(value,list):
                            logs(value,source)
                parsed={}
                for path in sorted(fixture.rglob('*.txt')):
                    relative=path.relative_to(fixture).as_posix()
                    parsed[relative]=script(path)
                    logs(parsed[relative],relative)
                if non_literal:
                    reject('NON_LITERAL_DEBUG_LOG',non_literal_count=len(non_literal),arguments=non_literal)
                events=parsed['events/des_acceptance_events.txt']
                prepare_key='des_acceptance_prepare_original_rite_input_effect'
                def calls(entries):
                    found=[]
                    for row in entries:
                        if row['key']==prepare_key and row['value']=='yes':
                            found.append(row)
                        if isinstance(row['value'],list):
                            found.extend(calls(row['value']))
                    return found
                setup=one(one(events,'des_acceptance.1',required=True),'immediate',required=True)
                setup_calls=[row for row in setup if row['key']==prepare_key and row['value']=='yes']
                if len(setup_calls)!=1 or sum(len(calls(entries)) for entries in parsed.values())!=1:
                    reject('ORIGINAL_RELATION_PREPARATION_OUTSIDE_FRESH_SETUP')
                effects=parsed['common/scripted_effects/des_acceptance_effects.txt']
                decisions=parsed['common/decisions/des_acceptance_decisions.txt']
                readback=one(effects,'des_acceptance_read_original_rite_input_effect',required=True)
                def readback_effects(entries):
                    for row in entries:
                        key,value=row['key'],row['value']
                        if key in ('if','else'):
                            readback_effects([entry for entry in value if entry['key']!='limit'])
                        elif key in ('add_character_flag','remove_character_flag'):
                            if value!='des_test_original_rite_input_ready':
                                reject('READBACK_WRITES_NON_FIXTURE_FLAG',key=key,value=value)
                        elif key not in ('save_scope_as','debug_log'):
                            reject('READBACK_HAS_MUTATING_EFFECT',key=key)
                readback_effects(readback)
                decision=one(decisions,'des_acceptance_original_rite_input_readback_decision',required=True)
                invoked=one(one(decision,'effect',required=True),'hidden_effect',required=True)
                if invoked != [{'key':'des_acceptance_read_original_rite_input_effect','value':'yes'}]:
                    reject('INDEPENDENT_READBACK_HAS_OTHER_EFFECTS')
                required=json.loads(manifest.read_bytes())['receipt']['required_markers']
                missing=sorted(set(required)-set(literals))
                if missing:
                    reject('MISSING_LITERAL_REQUIRED_MARKER',markers=missing)
                expected=json.loads(baseline.read_bytes())['events']
                for event,guard in expected.items():
                    immediate=one(one(events,event,required=True),'immediate',required=True)
                    branch=one(immediate,'if',required=True)
                    if one(branch,'limit',required=True)!=guard['limit'] or one(immediate,'else',required=True)!=guard['else']:
                        reject('CHANGED_OBSERVER_OR_OUTSIDER_GUARD',event=event)
                    observer=json.loads(one(branch,'debug_log',required=True))
                    outsider=json.loads(one(one(branch,'scope:des_test_outsider',required=True),'debug_log',required=True))
                    if [observer,outsider]!=guard['success_logs']:
                        reject('CHANGED_SCOPED_SUCCESS_MARKERS',event=event)
                print(json.dumps({'status':'ACCEPTED','required_marker_count':len(required),'unchanged_guard_count':len(expected),'original_rite_readback_only_observes':True}))
                """;
        Process process = new ProcessBuilder("python", "-B", "-X", "utf8", "-c", program,
                repository().toString(), fixture.fixture().toString(), fixture.manifest().toString(), baseline.toString())
                .redirectErrorStream(true).start();
        assertTrue(process.waitFor(30, TimeUnit.SECONDS), "existing lexer/AST fixture probe timed out");
        return new ProbeResult(process.exitValue(), new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
    }

    private record ProbeResult(int exitCode, String output) { }

    private static void copyFixtureInputs(Path destinationRepository) throws IOException {
        Path sourceMain = repository().resolve("mod_dynastic_esotericism/tools/src/main");
        Path destinationMain = destinationRepository.resolve("mod_dynastic_esotericism/tools/src/main");
        Path emitter = Path.of("java/org/xar/ck3/dynastic/acceptance/FixtureEmitter.java");
        Files.createDirectories(destinationMain.resolve(emitter).getParent());
        Files.copy(sourceMain.resolve(emitter), destinationMain.resolve(emitter));
        Path resources = sourceMain.resolve("resources/acceptance-fixture");
        try (Stream<Path> sources = Files.walk(resources)) {
            for (Path source : sources.filter(Files::isRegularFile).toList()) {
                Path target = destinationMain.resolve("resources/acceptance-fixture").resolve(resources.relativize(source));
                Files.createDirectories(target.getParent());
                Files.copy(source, target);
            }
        }
    }

    @Test
    void rejectsMissingSourcesInvalidMachineAndIncompleteOptions() {
        assertThrows(IOException.class,
                () -> FixtureEmitter.emit(temporary, temporary.resolve("missing-sources"), "authored-machine"));
        assertThrows(IllegalArgumentException.class,
                () -> FixtureEmitter.emit(repository(), temporary.resolve("invalid-machine"), ""));
        assertEquals(1, FixtureEmitter.run(new String[]{"--output", temporary.resolve("no-output").toString()}));
        assertFalse(Files.exists(temporary.resolve("no-output")));
    }
}
