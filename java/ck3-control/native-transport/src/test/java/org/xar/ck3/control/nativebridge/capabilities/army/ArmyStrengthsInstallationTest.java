package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Offline original full service -> one real complete installer -> all native/public consumers.
 * Controlled metadata below is explicitly test data and does not replace Root native read/writer/Game verification. */
final class ArmyStrengthsInstallationTest {
    @TempDir Path temporary;
    @Test void oneCompleteInstallationConsumesActualOriginalServiceAcrossAllFiftyFourStages() throws Exception {
        var installed = ArmyStrengthsInstallation.install(sources());
        assertEquals(68, installed.families().coverage().installed().size());
        assertEquals(54, installed.pipeline().coverage().installed().size());
        assertTrue(installed.families().coverage().missing().isEmpty());
        assertTrue(installed.pipeline().coverage().missing().isEmpty());
        ObjectNode capture = capture();
        for (JsonNode example : capture.withArray("cases")) {
            String name = example.get("name").textValue();
            ObjectNode nativeRow = ArmyJson.object(example.get("input"));
            ObjectNode frozenRow = nativeRow.deepCopy();
            ObjectNode expected = ArmyJson.object(example.get("result"));
            Row row = ArmyStrengthsCodec.row(nativeRow, Mode.EXPLICIT_RICH, installed.families());
            var nullFleet = installed.families().normalize(ArmyStrengthsFamilies.Key.CURRENT_FLEET_SUPPLY_TICK_INPUTS_V1,
                    new NullValue<>(), new RowContext(row.core(), row.regiments()));
            assertTrue(nullFleet.value() instanceof NullValue<?>);
            assertTrue(ArmyStrengthsCodec.parseValue(nullFleet.normalizedJson()).isNull());
            assertTrue(ArmyStrengthsCodec.parseValue(nullFleet.publicV2Json()).isNull());
            var input = input(example, row);
            var projections = installed.pipeline().project(input);
            assertEquals(54, projections.values().size(), name);
            ObjectNode actualRow = projections.rowJson(row);
            ObjectNode publicRow = projections.rowPublicV2Json(row);
            ObjectNode top = projections.topLevelJson(), publicTop = projections.topLevelPublicV2Json();
            for (var stage : ArmyStrengthsPipeline.Stage.values()) {
                JsonNode actual = stage.perRow() ? actualRow.get(stage.wire()) : top.get(stage.wire());
                JsonNode original = stage.perRow() ? expected.get("army_strengths").get(0).get(stage.wire()) : expected.get(stage.wire());
                assertNotNull(original, name + " original service omitted stage " + stage);
                assertEquals(original, actual, name + " complete registered consumer " + stage);
            }
            assertEquals(publicRow, ArmyStrengthsCodec.parseValue(new RawJson(ArmyJson.bytes(publicRow))), name + " public row roundtrip");
            requireSafe(publicRow); requireSafe(publicTop);
            var selection = new ArmyStrengthsContracts.Selection(input.snapshot(), input.query(), input.originalHello().orElseThrow(), new Missing<>());
            var reply = new ArmyStrengthsService.Reply(selection, input.original(), List.of(row), ArmyStrengths.status(List.of(row)), input.original().status(), projections);
            RawJson publicReply = ArmyStrengthsService.encodePublicV2(reply);
            JsonNode publicEnvelope = ArmyStrengthsCodec.parseValue(publicReply);
            assertEquals("xar.army-strengths.public/v2", publicEnvelope.get("schema").textValue());
            assertEquals(publicRow, publicEnvelope.get("army_strengths").get(0));
            assertEquals(publicEnvelope, ArmyStrengthsCodec.parseValue(new RawJson(publicReply.bytes())), name + " complete public service roundtrip");
            requireSafe(publicEnvelope);
            var replayedReply = ArmyStrengthsDriverResult.project(selection, input.original(), installed.pipeline());
            assertEquals(actualRow, replayedReply.projections().rowJson(row), name + " actual pure pipeline history replay");
            RawJson driverReply = ArmyStrengthsDriverResult.encode(replayedReply);
            ObjectNode driverEnvelope = ArmyJson.parse(driverReply.bytes());
            assertEquals(actualRow, driverEnvelope.get("army_strengths").get(0), name + " complete internal Driver row");
            assertTrue(driverEnvelope.get("query_sequence").isIntegralNumber());
            assertEquals(input.original().sequence(), driverEnvelope.get("query_sequence").bigIntegerValue());
            assertEquals(input.snapshot().binding().publicRevision(), driverEnvelope.get("queried_revision").bigIntegerValue());
            assertFalse(driverEnvelope.has("schema"), "public-v2 schema cannot impersonate the legacy internal result");
            assertEquals(driverEnvelope, ArmyJson.parse(new RawJson(driverReply.bytes()).bytes()), name + " full internal result roundtrip");
            RawJson historyPublic = ArmyStrengthsDriverResult.encodeHistoryPublic(replayedReply);
            var internalTree = DriverJson.object(driverReply.bytes(), RawJson.MAXIMUM_BYTES);
            var publicTree = DriverJson.object(historyPublic.bytes(), RawJson.MAXIMUM_BYTES);
            var historyRoles = DriverReadHistoryRichMaterial.PublicNumbers.fromResults(driverReply, historyPublic);
            assertEquals(publicTree, historyRoles.toPublic(internalTree), name + " all54 owning public encoders reach shared history consumer");
            assertEquals(internalTree, historyRoles.fromPublic(publicTree), name + " exact numeric Driver history restored");
            assertEquals(historyRoles, DriverReadHistoryRichMaterial.PublicNumbers.fromJson(historyRoles.toJson()), name + " durable typed role roundtrip");
            requireSafe(ArmyJson.parse(historyPublic.bytes()));
            if (name.equals("scoped-observed_prepared")) {
                ObjectNode privatePacket = ArmyJson.object(example).deepCopy();
                ArmyJson.object(privatePacket.get("native_result")).putNull("observed_army_stage_inputs_12004");
                var privateInput = input(privatePacket, row);
                var privateSelection = new ArmyStrengthsContracts.Selection(privateInput.snapshot(), privateInput.query(), privateInput.originalHello().orElseThrow(), new Missing<>());
                var privateReply = ArmyStrengthsDriverResult.project(privateSelection, privateInput.original(), installed.pipeline());
                assertEquals(54, privateReply.projections().values().size());
                assertFalse(ArmyJson.parse(ArmyStrengthsDriverResult.encode(privateReply).bytes()).has("observed_army_stage_inputs_12004"));
                assertTrue(ArmyJson.parse(privateReply.original().original().original().originalResultToken().orElseThrow().bytes())
                        .get("observed_army_stage_inputs_12004").isNull(), "Java-only Native input stays exactly in its original receipt");
                DriverReadHistoryRichMaterial.PublicNumbers.fromResults(ArmyStrengthsDriverResult.encode(privateReply), ArmyStrengthsDriverResult.encodeHistoryPublic(privateReply));
            }
            var originalRead = input.original();
            var wrongSequence = new Read(originalRead.profile(), originalRead.status(), originalRead.sequence().add(BigInteger.ONE),
                    originalRead.backendId(), originalRead.rows(), originalRead.timing(), originalRead.publishedScopeStatus(), originalRead.original());
            var alteredReply = new ArmyStrengthsService.Reply(selection, wrongSequence, reply.selected(), reply.status(), reply.scopeStatus(), projections);
            assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsDriverResult.encode(alteredReply), name + " no synthetic query identity");
            assertEquals(frozenRow, example.get("input"), name + " actual original query row retained");
        }
        assertEquals(6, capture.withArray("cases").size());
    }
    @Test void exactInstalledCoreProjectionCarriesLongMaxRolesAndPreservesItsOriginalNativePacket() throws Exception {
        ObjectNode nativeResult = ArmyJson.empty().put("step", STEP).put("accepted", true).put("status", "available")
                .put("query_sequence", 1).put("backend_id", "controlled-wide-history")
                .put("army_strengths_profile", "ordinary_core_v1").put("army_observed_phase_coverage", "not_requested");
        ObjectNode row = nativeResult.putArray("army_strengths").addObject().put("status", "available").put("army_id", 0)
                .put("native_carmy_id", 0).put("scope_role", "player").put("regiment_count", 0).put("current_soldiers", 0)
                .put("maximum_soldiers", 0).put("ai_base_power_raw", Long.MAX_VALUE).put("ai_base_power_scale", 100000).putNull("unavailable_reason");
        row.putArray("war_ids");
        var seed = ArmyStrengthsSourceTest.input(nativeResult, ArmyStrengthsSourceTest.projectedHello());
        byte[] originalHello = seed.originalHello().orElseThrow().packet().value();
        var helloBody = org.xar.ck3.control.nativebridge.NativeWire.object(org.xar.ck3.control.nativebridge.NativeWire.parse(
                java.util.Arrays.copyOfRange(originalHello, 4, originalHello.length)));
        helloBody.withArray("capabilities").add(CAPABILITY);
        var hello = (org.xar.ck3.control.nativebridge.NativeWire.Hello) org.xar.ck3.control.nativebridge.NativeWire.decode(
                org.xar.ck3.control.nativebridge.NativeWire.packet(ArmyJson.bytes(helloBody)));
        var query = new Query(Profile.ORDINARY_CORE_V1, Mode.AUTO_CORE, new Missing<>(), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED);
        var selected = new ArmyStrengthsContracts.Selection(seed.snapshot(), query, hello, new Missing<>());
        var normalizers = new ArmyStrengthsFamilies.Registry(); normalizers.freeze();
        var pipeline = new ArmyStrengthsPipeline();
        ExactRef codec = army("ArmyStrengthsCodec");
        var contracts = new ArmyStrengthsContracts(codec, codec, normalizers, pipeline,
                List.of(codec, army("ArmyStrengthsDriverResult"), source("application/src/main/java/org/xar/ck3/control/application/history/DriverReadHistoryRichMaterial.java"),settingsDataRef()),
                java.util.Optional.empty(),settingsDataRef());
        var catalog = new RootReadContractCatalog(List.of(), contracts.families());
        ReadContract<Read> contract = contracts.issue(catalog, selected);
        var base = seed.original().original();
        var receipt = new PlanningReadReceipt(contracts.request(selected), contract.contractId(), base.requestId(), base.before(), base.after(), base.original());
        byte[] originalPacket = receipt.original().originalPacket().clone();
        var projected = contract.projectOriginalHistory(receipt);
        var internal = DriverJson.object(projected.fullResult().bytes(), RawJson.MAXIMUM_BYTES);
        var exposed = projected.publicNumbers().toPublic(internal);
        var publicRow = OpportunityJson.object(OpportunityJson.array(exposed.get("army_strengths"), "original rows").getFirst(), "original row");
        assertEquals(new OpportunityJson.Text(Long.toString(Long.MAX_VALUE)), publicRow.get("ai_base_power_raw"));
        assertEquals(new OpportunityJson.Bool(true), exposed.get("accepted"));
        assertTrue(exposed.get("query_sequence") instanceof OpportunityJson.Text);
        assertEquals(internal, projected.publicNumbers().fromPublic(exposed));
        assertEquals(projected.publicNumbers(), DriverReadHistoryRichMaterial.PublicNumbers.fromJson(projected.publicNumbers().toJson()));
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRichMaterial.PublicNumbers.fromResults(projected.fullResult(), projected.fullResult()),
                "unclaimed original LongMAX must not pass public transport");
        var reversed = new java.util.ArrayList<>(projected.publicNumbers().toJson().items()); java.util.Collections.reverse(reversed);
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRichMaterial.PublicNumbers.fromJson(new OpportunityJson.Arr(reversed)),
                "durable numeric roles require their original canonical order");
        assertArrayEquals(originalPacket, receipt.original().originalPacket());
        assertEquals(BigInteger.valueOf(Long.MAX_VALUE), ArmyJson.parse(receipt.original().originalResultToken().orElseThrow().bytes())
                .withArray("army_strengths").get(0).get("ai_base_power_raw").bigIntegerValue());
    }
    private static ArmyStrengthsPipeline.Input input(JsonNode example, Row row) throws Exception {
        ObjectNode raw = ArmyJson.object(example.get("snapshot")).deepCopy();
        raw.put("map_ready", true).put("episode_run_id", "controlled-full-installation");
        raw.putObject("played_character").put("character_id", 0).put("alive", true);
        ArmyJson.object(raw.get("diagnostics")).put("connection_generation", 5);
        ObjectNode actualResult = ArmyJson.object(example.get("native_result"));
        var seed = ArmyStrengthsSourceTest.input(actualResult, ArmyJson.object(raw.get("diagnostics").get("hello")));
        var old = seed.snapshot().context(); Instant now = Instant.now();
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ZERO, raw.get("native_revision").bigIntegerValue(), raw.get("date_raw").bigIntegerValue()),
                raw.get("snapshot_id").textValue(), raw.get("revision").bigIntegerValue(), "controlled-full-installation");
        var context = new Context(new ProposalLifecycle.ObservationIdentity(old.source().machineId(), seed.snapshot().binding().game(), frame, 1), old.source(), old.sessionId(), now.plusSeconds(60));
        Snapshot snapshot = ArmyStrengthsCodec.snapshot(context, new RawJson(ArmyJson.bytes(raw)));
        var operation = new OperationKey(STEP); var baseReceipt = seed.original().original();
        byte[] priorHello = seed.originalHello().orElseThrow().packet().value();
        ObjectNode helloBody = org.xar.ck3.control.nativebridge.NativeWire.object(org.xar.ck3.control.nativebridge.NativeWire.parse(java.util.Arrays.copyOfRange(priorHello, 4, priorHello.length)));
        helloBody.withArray("capabilities").add(CAPABILITY);
        byte[] actualHelloPacket = org.xar.ck3.control.nativebridge.NativeWire.packet(ArmyJson.bytes(helloBody));
        var actualHello = (org.xar.ck3.control.nativebridge.NativeWire.Hello) org.xar.ck3.control.nativebridge.NativeWire.decode(actualHelloPacket);
        var capability = new ExactRef("controlled-complete-original-hello", actualHelloPacket.length, ActionCodec.sha256(actualHelloPacket));
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(), operation, new OpportunityJson.Obj(Map.of()), context.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(context.before(), context.source(), context.sessionId(), BigInteger.valueOf(5), operation, capability, capability, "controlled", now, context.deadline()), true, true, true, "b".repeat(64));
        var receipt = new PlanningReadReceipt(request, baseReceipt.contractId(), baseReceipt.requestId(), guard, guard, baseReceipt.original());
        var read = new Read(Profile.ORDINARY_CORE_V1, Status.AVAILABLE, actualResult.get("query_sequence").bigIntegerValue(), "pure-memory-fixture", List.of(row), new Missing<>(), new Missing<>(), receipt);
        var query = new Query(Profile.ORDINARY_CORE_V1, Mode.EXPLICIT_RICH, new Present<>(List.of(row.core().army())),
                EntryMode.valueOf(example.get("mode").textValue().toUpperCase(java.util.Locale.ROOT)), EntryMode.valueOf(example.get("mode").textValue().toUpperCase(java.util.Locale.ROOT)));
        return new ArmyStrengthsPipeline.Input(snapshot, read, query, List.of(row), Optional.of(actualHello));
    }
    private static ArmyStrengthsInstallation.Sources sources() throws Exception {
        return new ArmyStrengthsInstallation.Sources(
                new ArmyStrengthsNativeFields.Sources(army("ArmyStrengthsNativeFields"), military("prestore/CurrentMovementCodec"), military("zerostockclock/ArmyUpdateClockCodec")),
                new ArmyStrengthsExistingFamilies.Sources(military("monthlyloss/MonthlyLossCodec"), military("armyqueue/ArmyDailyQueueInputsCodec"),
                        military("countyentry/CountyEntryCodec"), military("updaterwrites/SourceNextFrameCodec"), military("fleetsupply/FleetSupplyCodec"),
                        military("callbackrisk/CurrentSupplyDispatchCodec"), military("supplyschedule/FutureDailySupplyScheduleCodec"), military("combatroles/CombatRolesCodec")),
                army("ArmyStrengthsStages"), army("ArmyStrengthsBaselinePublicRules"), army("ArmyStrengthsRefill"),
                army("ArmyStrengthsAssaultInstaller"), army("ArmyStrengthsPhases"), army("ArmyStrengthsSupply"), army("ArmyStrengthsMonthly"),
                army("ArmyStrengthsMovement"), army("ArmyStrengthsManagers"), army("ArmyStrengthsDetachment"),
                army("ArmyDetachmentDataProjection"), army("ArmyStrengthsLossAllocation"));
    }
    private static ExactRef army(String name) throws Exception { return source("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/" + name + ".java"); }
    private static ExactRef military(String name) throws Exception { return source("wave2-military/src/main/java/org/xar/ck3/control/wave2/military/" + name + ".java"); }
    private static ExactRef source(String target) throws Exception {
        Path module = Path.of(ArmyStrengthsInstallation.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath();
        for (Path cursor = module; cursor != null; cursor = cursor.getParent()) {
            Path selected = cursor.resolve(target);
            if (Files.isRegularFile(selected)) { byte[] body = Files.readAllBytes(selected); return new ExactRef(selected.toRealPath().toString(), body.length, ActionCodec.sha256(body)); }
        }
        throw new IllegalStateException("Actual selected Java source is required: " + target);
    }
    private ObjectNode capture() throws Exception {
        String python = required("xar.python"), repository = required("xar.repository.root");
        Path root = Path.of(repository).toRealPath(), output = temporary.resolve("whole-service.json"), log = temporary.resolve("whole-service.log");
        var process = new ProcessBuilder(python, "-B", "-c", PYTHON, root.toString(), output.toString()).directory(root.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        if (!process.waitFor(180, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IllegalStateException("Original complete strengths service timed out"); }
        assertEquals(0, process.exitValue(), Files.readString(log, StandardCharsets.UTF_8));
        ObjectNode result = ArmyJson.object(ArmyStrengthsCodec.parseValue(new RawJson(Files.readAllBytes(output))));
        assertFalse(result.get("actual_game_observed").booleanValue()); assertEquals("xar.strengths.complete-installation-oracle/v1", result.get("schema").textValue());
        assertFalse(result.get("machine_id").textValue().isBlank()); assertFalse(result.get("observed_at_utc").textValue().isBlank());
        for (JsonNode pin : result.withArray("sources")) {
            Path path = Path.of(pin.get("path").textValue()).toRealPath(); assertTrue(path.startsWith(root));
            byte[] body = Files.readAllBytes(path); assertEquals(pin.get("bytes").longValue(), body.length); assertEquals(pin.get("sha256").textValue(), ActionCodec.sha256(body));
        }
        assertTrue(result.withArray("sources").size() > 15);
        return result;
    }
    private static void requireSafe(JsonNode value) {
        if (value.isIntegralNumber()) assertTrue(value.bigIntegerValue().abs().compareTo(BigInteger.valueOf(9_007_199_254_740_991L)) <= 0, "Undeclared unsafe integer in complete public encoding: " + value);
        else if (value.isContainerNode()) value.forEach(ArmyStrengthsInstallationTest::requireSafe);
    }
    private static String required(String name) { String value = System.getProperty(name); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: required original producer input " + name); return value; }
    private static final String PYTHON = """
import sys,json,hashlib
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2])
sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
import ck3_live_run_id
from test_scoped_ordered_refill_service import row,MemoryRoute
from test_ordered_refill_besieging_assault_service import composed_row
from test_selected_refill_monthly_assembly_service import assembly_packet
class CompleteRoute(MemoryRoute):
    def execute_step(self,*args,**kwargs):
        result=super().execute_step(*args,**kwargs)
        result['query_sequence']=1
        result['source']={'game_version':'1.20.0.4','executable_sha256':'98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'}
        self.native_result=deepcopy(result)
        return result
cases=[]
for label,builder in [('scoped',row),('besieging',composed_row),('monthly',assembly_packet)]:
    for mode in ('observed_prepared','fixed_chunk0_prepare'):
        original=builder(); frozen=deepcopy(original); service=CompleteRoute(original)
        result=service.query_army_strengths([11],expected_revision=42,ordered_refill_entry_mode=mode,ordered_besieging_entry_mode=mode)
        assert original==frozen
        cases.append(dict(name=label+'-'+mode,input=frozen,result=result,snapshot=service.snapshot(),native_result=service.native_result,mode=mode))
sources={}
for module in tuple(sys.modules.values()):
    file=getattr(module,'__file__',None)
    if file:
        path=Path(file).resolve()
        if path.is_file() and path.is_relative_to(repo) and path.suffix=='.py':
            body=path.read_bytes();sources[str(path)]=dict(path=str(path),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
out.write_text(json.dumps(dict(schema='xar.strengths.complete-installation-oracle/v1',machine_id=ck3_live_run_id.current_machine_id(),observed_at_utc=datetime.now(timezone.utc).isoformat(),actual_game_observed=False,sources=list(sources.values()),cases=cases))+chr(10),encoding='utf-8')
""";

    /** Actual typed settings encoder DATA for source-only contract tests; no Bound, Root or storage qualification. */
    private static ExactRef settingsDataRef() {
        byte[] raw=OriginalDriverQueryHistorySettings.encodeRequest(new OriginalDriverQueryHistorySettings.Request(
                "controlled-strengths-settings",java.time.Instant.EPOCH,java.time.Instant.EPOCH.plusSeconds(3600),
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Disabled(),0,
                        OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE)));
        return new ExactRef("controlled-explicit-inline-strengths-settings",raw.length,ActionCodec.sha256(raw));
    }
}
