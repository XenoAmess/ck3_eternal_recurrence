package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Pure boundary/cache regression. These controlled frames are neither real writer evidence nor Game acceptance. */
final class ArmyStrengthsCodecTest {
    private static final String CORE = "{\"status\":\"available\",\"army_id\":0,\"native_carmy_id\":0,\"scope_role\":\"player\",\"war_ids\":[],\"regiment_count\":0,\"current_soldiers\":0,\"maximum_soldiers\":0,\"ai_base_power_raw\":0,\"ai_base_power_scale\":100000,\"unavailable_reason\":null}";
    private static final String PYTHON_ORACLE = """
            import base64,hashlib,json,sys
            from pathlib import Path
            m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
            for r in m['original_sources']:
                b=Path(r['path']).read_bytes()
                if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']: raise RuntimeError('original Army source drift')
            sys.path.insert(0,m['python_source_root'])
            from xar_autoplayer.bridge.war_contract import army_strength_scope,_ARMY_STRENGTH_ROW_KEYS,_ARMY_STRENGTH_SUPPLY_ROW_KEYS,_ARMY_STRENGTH_SUPPLY_FIELD_PAIRS,_ARMY_STRENGTH_GATHERING_DAYS_KEYS
            from xar_autoplayer.bridge.auto_army_core_validation_v1 import normalize_auto_army_core_v1
            from xar_autoplayer.bridge.army_strengths_manager_shared_wire import expand_army_strengths_manager_inputs
            from xar_autoplayer.bridge.army_strengths_profile_contract import validate_army_strengths_profile_coverage
            p=json.loads(base64.b64decode(sys.argv[2])); scope=army_strength_scope(p['snapshot'])
            expanded=expand_army_strengths_manager_inputs(p['result'],detached=False)
            validate_army_strengths_profile_coverage(expanded,expected_profile='ordinary_core_v1')
            families=sorted(_ARMY_STRENGTH_SUPPLY_ROW_KEYS-_ARMY_STRENGTH_ROW_KEYS-_ARMY_STRENGTH_GATHERING_DAYS_KEYS-{f for pair in _ARMY_STRENGTH_SUPPLY_FIELD_PAIRS for f in pair})
            print(json.dumps({'scope':scope,'rows':normalize_auto_army_core_v1(expanded['army_strengths'],expected_scope=scope),'family_keys':families},separators=(',',':')))
            """;
    @Test void actualOriginalScopeSharedWireAndAutoCoreProducerAgreeWithJava() throws Exception {
        ObjectNode snapshot = ArmyJson.parse("{\"player_armies\":[{\"army_id\":0},{\"army_id\":2}],\"active_wars\":[{\"war_id\":7,\"allied_armies\":[{\"army_id\":1},{\"army_id\":2}],\"enemy_armies\":[{\"army_id\":3}]},{\"war_id\":8,\"allied_armies\":[],\"enemy_armies\":[{\"army_id\":1},{\"army_id\":0}]}]}".getBytes(StandardCharsets.UTF_8));
        List<ScopeArmy> expected = ArmyStrengthsCodec.scope(snapshot); ObjectNode input = ArmyJson.empty(); input.set("snapshot", snapshot);
        ObjectNode result = input.putObject("result").put("army_strengths_profile", "ordinary_core_v1").put("army_observed_phase_coverage", "not_requested"); var rows = result.putArray("army_strengths");
        for (ScopeArmy member : expected) { ObjectNode row = core(); row.put("army_id", member.army().value()).put("scope_role", ArmyStrengthsCodec.wire(member.role())); var ids = row.putArray("war_ids"); member.wars().forEach(id -> ids.add(id.value())); rows.add(row); }
        var bundle = result.putObject("army_manager_inputs_shared_v1").put("schema_version", 1); var ids = bundle.putArray("army_ids"); expected.forEach(row -> ids.add(row.army().value())); bundle.putObject("fields").putNull("current_army_flag31_inputs_v1");
        JsonNode oracle = oracle(input); var actualScope = ArmyJson.empty().arrayNode(); expected.forEach(row -> { var n = actualScope.addObject().put("army_id", row.army().value()).put("scope_role", ArmyStrengthsCodec.wire(row.role())); var wars = n.putArray("war_ids"); row.wars().forEach(id -> wars.add(id.value())); });
        assertEquals(oracle.get("scope"), actualScope);
        var javaRows = ArmyJson.empty().arrayNode(); ArmyStrengthsFamilies.Registry empty = new ArmyStrengthsFamilies.Registry(); empty.freeze();
        for (ObjectNode row : ArmyStrengthsCodec.expandShared(result)) javaRows.add(ArmyStrengthsCodec.rowJson(ArmyStrengthsCodec.row(row, Mode.AUTO_CORE, empty)));
        assertEquals(oracle.get("rows"), javaRows);
        Set<String> actualKeys = ArmyStrengthsFamilies.allowedFieldNames(); var originalKeys = new java.util.HashSet<String>(); oracle.get("family_keys").forEach(value -> originalKeys.add(value.textValue())); assertEquals(originalKeys, actualKeys);
    }
    @Test void zeroAndSignedFullIdsArePreservedButInvalidSentinelAndWrongTokenTypesAreRejected() {
        assertEquals(new Present<>(new FullId(0)), ArmyStrengthsCodec.core(core()).nativeArmy());
        ObjectNode signed = core().put("native_carmy_id", Integer.MIN_VALUE); assertEquals(new Present<>(new FullId(Integer.MIN_VALUE)), ArmyStrengthsCodec.core(signed).nativeArmy());
        for (String field : List.of("army_id", "native_carmy_id", "regiment_count", "current_soldiers", "maximum_soldiers", "ai_base_power_raw", "ai_base_power_scale"))
            for (String token : List.of("true", "0.0", "\"0\"")) { ObjectNode bad = core(); bad.set(field, ArmyJson.parse(("{\"value\":" + token + "}").getBytes(StandardCharsets.UTF_8)).get("value")); assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.core(bad), field + token); }
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.core(core().put("native_carmy_id", -1)));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.core(core().putNull("native_carmy_id")));
    }
    @Test void atomicUnavailableAggregatesSupplyPairsAndUnknownFieldsRemainStrictInAutoCore() {
        ObjectNode unavailable = core().put("status", "unavailable").put("unavailable_reason", "native identity unavailable");
        for (String name : List.of("regiment_count", "current_soldiers", "maximum_soldiers", "ai_base_power_raw")) unavailable.putNull(name);
        assertEquals(Status.UNAVAILABLE, ArmyStrengthsCodec.core(unavailable).status());
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.core(unavailable.deepCopy().put("current_soldiers", 0)));
        ArmyStrengthsFamilies.Registry registry = new ArmyStrengthsFamilies.Registry(); registry.freeze();
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.row(core().put("current_supply_raw", 0), Mode.AUTO_CORE, registry));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.row(unavailable.deepCopy().put("current_supply_raw", 0).put("current_supply_scale", 100000), Mode.AUTO_CORE, registry));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.row(core().put("unregistered_extension", true), Mode.AUTO_CORE, registry));
    }
    @Test void missingRichMigrationRemainsExplicitAndCannotRegisterThePublicRoute() {
        ArmyStrengthsFamilies.Registry registry = new ArmyStrengthsFamilies.Registry(); registry.freeze();
        var failure = assertThrows(ArmyStrengthsFamilies.MissingMigration.class, registry::requireCompleteRich);
        assertTrue(failure.missing().contains(ArmyStrengthsFamilies.Key.CURRENT_DAILY_ASSAULT_TABLE_V1));
        ArmyStrengthsPipeline pipeline = new ArmyStrengthsPipeline(); pipeline.freeze(); assertFalse(pipeline.coverage().complete()); assertThrows(IllegalArgumentException.class, pipeline::requireComplete);
    }
    @Test void subsetAndEveryBindingProfileScopeChangeInvalidateTheExactFrameCache() {
        Snapshot snapshot = snapshot(); Row row = ArmyStrengthsCodec.row(core(), Mode.AUTO_CORE, new ArmyStrengthsFamilies.Registry());
        Read read = new Read(Profile.ORDINARY_CORE_V1, Status.AVAILABLE, BigInteger.ONE, "controlled", List.of(row), new Missing<>(), new Missing<>(), receipt(snapshot));
        ArmyStrengthsCache cache = new ArmyStrengthsCache(); cache.publish(snapshot, read, false);
        assertEquals(1, cache.forSnapshot(snapshot, Profile.ORDINARY_CORE_V1).orElseThrow().rows().size());
        assertThrows(UnsupportedOperationException.class, () -> cache.forSnapshot(snapshot, Profile.ORDINARY_CORE_V1).orElseThrow().rows().clear());
        assertTrue(cache.forSnapshot(snapshot, Profile.OBSERVED_HISTORY_FULL_V1).isEmpty());
        cache.publish(snapshot, read, true); assertTrue(cache.forSnapshot(snapshot, Profile.ORDINARY_CORE_V1).isEmpty());
        cache.publish(snapshot, read, false); Binding b = snapshot.binding(); Snapshot changed = new Snapshot(snapshot.context(), new Binding(b.machineId(), b.game(), b.sessionId(), b.connectionGeneration().add(BigInteger.ONE), b.snapshotId(), b.publicRevision(), b.nativeRevision(), b.dateRaw(), b.episodeRunId(), b.actorCharacterId()), snapshot.scope(), snapshot.original());
        assertTrue(cache.forSnapshot(changed, Profile.ORDINARY_CORE_V1).isEmpty()); assertTrue(cache.forSnapshot(snapshot, Profile.ORDINARY_CORE_V1).isEmpty());
        cache.publish(snapshot, read, false); Snapshot scopeDrift = new Snapshot(snapshot.context(), snapshot.binding(), List.of(new ScopeArmy(new PublicUnitId(1), Role.PLAYER, List.of())), snapshot.original());
        assertTrue(cache.forSnapshot(scopeDrift, Profile.ORDINARY_CORE_V1).isEmpty()); cache.invalidate();
    }
    @Test void requestLimitsAreExactlySixtyFourAndNeverSilentlyDeduplicate() {
        List<PublicUnitId> sixtyFour = java.util.stream.IntStream.range(0, 64).mapToObj(PublicUnitId::new).toList();
        assertDoesNotThrow(() -> new Query(Profile.ORDINARY_CORE_V1, Mode.EXPLICIT_RICH, new Present<>(sixtyFour), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED));
        List<PublicUnitId> tooMany = new ArrayList<>(sixtyFour); tooMany.add(new PublicUnitId(64));
        assertThrows(IllegalArgumentException.class, () -> new Query(Profile.ORDINARY_CORE_V1, Mode.EXPLICIT_RICH, new Present<>(tooMany), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED));
        assertThrows(IllegalArgumentException.class, () -> new Query(Profile.ORDINARY_CORE_V1, Mode.EXPLICIT_RICH, new Present<>(List.of(new PublicUnitId(0), new PublicUnitId(0))), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED));
    }
    @Test void completeRegimentCompositionAndEligibilitySurviveSerializationAndRejectWrongGroups() {
        ObjectNode raw = ArmyJson.parse("{\"army_regiment_id\":0,\"current_soldiers\":100,\"maximum_soldiers\":120,\"scale\":1,\"maa_type_status\":\"available\",\"maa_type_key\":\"archers\",\"siege_tier_observable\":false,\"siege_tier\":null,\"composition_unavailable_reason\":null,\"native_supply_loss_eligible\":null,\"supply_loss_eligibility_unavailable_reason\":\"not captured\"}".getBytes(StandardCharsets.UTF_8));
        Regiment value = ArmyStrengthsCodec.regiment(raw);
        ObjectNode core = core().put("regiment_count", 1).put("current_soldiers", 100).put("maximum_soldiers", 120);
        Row row = new Row(ArmyStrengthsCodec.core(core), List.of(), new Missing<>(), new Present<>(List.of(value)), List.of());
        ObjectNode encoded = ArmyStrengthsCodec.rowJson(row); assertEquals(value, ArmyStrengthsCodec.regiment(encoded.get("regiment_strengths").get(0)));
        ObjectNode missing = raw.deepCopy(); missing.remove("maa_type_key"); assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.regiment(missing));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.regiment(raw.deepCopy().put("siege_tier_observable", true)));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.regiment(raw.deepCopy().put("native_supply_loss_eligible", true)));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsCodec.regiment(raw.deepCopy().put("current_soldiers", 2147483648L)));
        ArmyJson.object(encoded.get("regiment_strengths").get(0)).put("maa_type_key", "changed external copy");
        assertEquals("archers", ArmyStrengthsCodec.rowJson(row).get("regiment_strengths").get(0).get("maa_type_key").textValue());
    }
    private static ObjectNode core() { return ArmyJson.parse(CORE.getBytes(StandardCharsets.UTF_8)); }
    private static Snapshot snapshot() {
        Instant now = Instant.now(); ExactRef ref = new ExactRef("controlled-unit-fixture", 1, "a".repeat(64)); G2Source source = new G2Source("fixture-machine", now.toString(), "controlled", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ZERO, BigInteger.valueOf(11), BigInteger.valueOf(53238336)), "native:11", BigInteger.valueOf(7), "fixture-episode");
        Context context = new Context(new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "fixture-session", now.plusSeconds(60));
        ObjectNode raw = ArmyJson.empty().put("snapshot_id", "native:11").put("revision", 7).put("native_revision", 11).put("date_raw", 53238336).put("episode_run_id", "fixture-episode").put("paused", true).put("map_ready", true);
        raw.putObject("played_character").put("character_id", 0).put("alive", true); raw.putObject("diagnostics").put("connection_generation", 5); raw.putArray("player_armies").addObject().put("army_id", 0); raw.putArray("active_wars");
        return ArmyStrengthsCodec.snapshot(context, new RawJson(ArmyJson.bytes(raw)));
    }
    private static PlanningReadReceipt receipt(Snapshot snapshot) {
        Context c = snapshot.context(); OperationKey operation = new OperationKey(STEP); var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), operation, new OpportunityJson.Obj(java.util.Map.of()), c.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(c.before(), c.source(), c.sessionId(), snapshot.binding().connectionGeneration(), operation, c.source().sourceRef(), c.source().sourceRef(), "controlled", Instant.now(), c.deadline()), true, true, true, "b".repeat(64));
        byte[] body = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"controlled-read\",\"ok\":true,\"result\":{}}".getBytes(StandardCharsets.UTF_8);
        try { return new PlanningReadReceipt(request, "controlled-read", "controlled-read", guard, guard, new NativeActionPort.AckReceived("controlled-read", true, Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))), new RawJson(body), org.xar.ck3.control.nativebridge.NativeWire.packet(body))); }
        catch (java.io.IOException invalid) { throw new IllegalArgumentException(invalid); }
    }
    private static JsonNode oracle(ObjectNode input) throws Exception {
        String executable = required("xar.python"), manifest = required("xar.army.strengths.oracle.manifest");
        assertTrue(Files.isRegularFile(Path.of(manifest)), "original source manifest must actually exist");
        String expectedDigest = required("xar.army.strengths.oracle.manifest.sha256");
        assertTrue(expectedDigest.matches("[a-f0-9]{64}"), "original source manifest requires a canonical SHA256");
        assertEquals(expectedDigest, java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256")
                .digest(Files.readAllBytes(Path.of(manifest)))), "original source manifest drift");
        Process process = new ProcessBuilder(executable, "-I", "-c", PYTHON_ORACLE, manifest, Base64.getEncoder().encodeToString(ArmyJson.bytes(input))).redirectErrorStream(true).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IllegalStateException("original Army producer oracle timed out"); }
        byte[] result = process.getInputStream().readAllBytes(); assertEquals(0, process.exitValue(), new String(result, StandardCharsets.UTF_8)); return org.xar.ck3.control.contracts.StrictJson.parse(result, RawJson.MAXIMUM_BYTES);
    }
    private static String required(String name) { String value = System.getProperty(name); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: original Army producer property missing: " + name); return value; }
}
