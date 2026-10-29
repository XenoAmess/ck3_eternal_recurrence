package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.battleretreat.BattleRetreatCodec;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponseCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Full native-normalizer -> actual current-model -> existing retreat-policy producer differential. */
final class CurrentBattleRetreatModelTest {
    private static final String PROGRAM = """
            import hashlib,json,sys
            from pathlib import Path
            root=Path(sys.argv[1]);sys.dont_write_bytecode=True
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            pins={
              'src/xar_autoplayer/simulation/combat_core.py':'15a9efce451e1830def6a7d93c87d0d00b7bb4e852fd75895780d289108a11b6',
              'src/xar_autoplayer/simulation/active_counter_current_basis.py':'aefb80f5fe4771063d9b0da2d0caf75470903488212d30b45ff0f300a41eedd1',
              'src/xar_autoplayer/simulation/battle_current_adapter.py':'7860986a1e435b6e992b840e50072ae8106ed7f05c1787de99a5c57c80751155',
              'src/xar_autoplayer/simulation/battle_current_runner.py':'07c23795802ebb891a18c679432caf05064929c3a25d99227fe5348dbbe53e55',
              'src/xar_autoplayer/simulation/battle_current_retreat_policy.py':'76fbc9a96754044395cf3904e8ec7e97ba4e5c86c68f65851183973f4ac5ad53',
              'src/xar_autoplayer/bridge/battle_control_contract.py':'2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de',
              'tests/unit/test_battle_current_condition.py':'18ba3867161b66632c72c370347fced9030e0d87091f0c0f1ea0b626dceece03',
              'tests/unit/test_battle_current_retreat_policy.py':'36ca975108d8496319ee7af361a40c71eadcfa3184955c086fe42ca0f596d9b9'}
            def verify():
                for name,pin in pins.items():assert hashlib.sha256((root/'ck3_autonomous_player'/name).read_bytes()).hexdigest()==pin,name
            verify()
            from test_battle_current_retreat_policy import _preview,_normalized_frame,_raw_frame,DATE,SUBJECT
            from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
            from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
            from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick
            from xar_autoplayer.simulation.battle_current_retreat_policy import assess_current_battle_retreat
            from xar_autoplayer.simulation.combat_core import DrawState
            cases=[]
            for name,budget,with_preview in (('over-budget',100000,True),('boundary',125000,False),('preview-needed',100000,False),('missing-loss',100000,False)):
                raw=_raw_frame(1)
                if name=='missing-loss':raw.pop('current_loss_inputs_v1')
                frame=normalize_battle_control_snapshot_v1(raw,expected_subject_public_cunit_id=SUBJECT,expected_observed_date_raw=DATE,expected_snapshot_revision=5)
                preview=_preview(frame) if with_preview else None
                tick=run_frozen_main_tick(adapt_current_battle_condition(frame),draw_state=DrawState(0,0))
                decision=assess_current_battle_retreat(frame,frozen_main_tick=tick,maximum_next_tick_hard_loss_raw=budget,retreat_preview=preview)
                cases.append({'name':name,'raw_frame':raw,'frame':frame,'preview':preview,'budget':budget,'expected':decision})
            verify();print(json.dumps({'producer':'actual-current-model-to-ordinary-retreat','cases':cases},separators=(',',':')))
            """;
    private static JsonNode original() throws Exception {
        String configuredRoot = System.getProperty("xar.repository.root"), configuredPython = System.getProperty("xar.python");
        assertNotNull(configuredRoot, "actual repository required; missing environment fails"); assertNotNull(configuredPython, "actual compatible interpreter required; missing environment fails");
        Path root = Path.of(configuredRoot), python = Path.of(configuredPython); assertTrue(root.isAbsolute() && Files.isDirectory(root)); assertTrue(python.isAbsolute() && Files.isRegularFile(python));
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-X", "utf8", "-c", PROGRAM, root.toString()).directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start(); FutureTask<byte[]> out = new FutureTask<>(() -> process.getInputStream().readNBytes(1024 * 1024 + 1)), err = new FutureTask<>(() -> process.getErrorStream().readNBytes(8193)); Thread.ofVirtual().start(out); Thread.ofVirtual().start(err);
        try {
            process.getOutputStream().close(); assertTrue(process.waitFor(45, TimeUnit.SECONDS), "original current-retreat producer timed out"); byte[] stdout = out.get(5, TimeUnit.SECONDS), stderr = err.get(5, TimeUnit.SECONDS); assertEquals(0, process.exitValue(), new String(stderr, StandardCharsets.UTF_8)); assertTrue(stdout.length <= 1024 * 1024 && stderr.length <= 8192, "bounded actual producer output required"); return StrictJson.parse(stdout, 1024 * 1024);
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); } }
    }
    @Test void completeActualNativeControlProducerToModelAndPolicyMatchesOriginal() throws Exception {
        JsonNode corpus = original(); assertEquals("actual-current-model-to-ordinary-retreat", corpus.path("producer").textValue()); assertEquals(4, corpus.path("cases").size());
        for (JsonNode row : corpus.get("cases")) {
            Obj raw = OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row.get("raw_frame"))), "actual raw control");
            Obj normalized = BattleResponseCodec.normalizeControl(raw, row.path("frame").path("subject_public_cunit_id").intValue(), row.path("frame").path("snapshot_revision").bigIntegerValue(), row.path("frame").path("observed_date_raw").longValue());
            assertArrayEquals(StrictJson.canonical(row.get("frame")), StrictJson.canonical(OpportunityJson.toNode(normalized)));
            Optional<Obj> preview = row.get("preview").isNull() ? Optional.empty() : Optional.of(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row.get("preview"))), "actual normalized preview"));
            BattleRetreatPolicy.Request request = new CurrentBattleRetreatModel().inputs(normalized, row.get("budget").bigIntegerValue(), preview);
            assertEquals(request, BattleRetreatCodec.decode(BattleRetreatCodec.encodeRequest(request)), "actual produced request must survive persistence");
            JsonNode actual = StrictJson.parse(BattleRetreatCodec.encodeDecision(BattleRetreatPolicy.assess(request)));
            assertArrayEquals(StrictJson.canonical(row.get("expected")), StrictJson.canonical(actual), row.path("name").textValue());
            assertFalse(actual.path("complete_transition").booleanValue()); assertTrue(actual.path("win_probability").isNull());
        }
    }
    @Test void emptyOptionalModelInputsRemainHonestMissingInputs() {
        assertThrows(IllegalArgumentException.class, () -> new CurrentBattleRetreatModel().inputs(new Obj(java.util.Map.of()), BigInteger.ONE, Optional.empty()));
    }
}
