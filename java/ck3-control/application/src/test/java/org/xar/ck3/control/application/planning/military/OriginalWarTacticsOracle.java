package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Executes unchanged actual Python functions as the compatibility oracle; no Python production module is created. */
final class OriginalWarTacticsOracle {
    private OriginalWarTacticsOracle() { }
    private static final String SCRIPT = """
            import ast, json, pathlib, sys, __future__
            strategy, war, units, window = map(pathlib.Path, sys.argv[1:5])
            namespace = {}
            flags = __future__.annotations.compiler_flag
            exec(compile(units.read_text(encoding='utf-8'), str(units), 'exec'), namespace)
            wt = ast.parse(window.read_text(encoding='utf-8'))
            wn = [node for node in wt.body if isinstance(node, (ast.FunctionDef, ast.Assign))]
            exec(compile(ast.fix_missing_locations(ast.Module(body=wn,type_ignores=[])),str(window),'exec',flags=flags),namespace)
            functions = {'is_life_advance_step','parse_battle_decision_epoch_advance_step',
              'parse_committed_route_sentinel_advance_step','_parse_committed_route_sentinel_advance_step',
              'parse_war_objective_hold_sentinel_advance_step','_parse_war_objective_hold_sentinel_advance_step',
              '_parse_war_sentinel_date_and_speed','parse_advance_route_contact_horizon_step',
              'parse_query_route_contact_horizon_step'}
            constants = {'ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX','BATTLE_DECISION_EPOCH_ADVANCE_STEP',
              'BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX','COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP',
              'COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX','WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP',
              'WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX','BATTLE_TERMINAL_CRUISE_STEP',
              'BATTLE_SENTINEL_ADVANCE_STEPS','MAX_ROUTE_CONTACT_HOSTILE_IDS'}
            def selected(path, names, values):
              tree=ast.parse(path.read_text(encoding='utf-8'))
              body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names
                or isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in values for target in node.targets)]
              assert {node.name for node in body if isinstance(node,ast.FunctionDef)} == names
              assert {target.id for node in body if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name)} == values
              exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(path),'exec',flags=flags),namespace)
            selected(war,functions,constants)
            selected(strategy,{'_recent_war_tactics','_native_int','_public_cunit_int','_army_tactical_state',
              '_progress_slice','_progress_army','_progress_siege_objectives','_history_after_latest_restore','_effective_command'},
              {'_NATIVE_CONTACT_STALE_GAME_DAYS','_NATIVE_CONTACT_MAX_PROBES','_NATIVE_COLLISION_COOLDOWN_GAME_DAYS','_NATIVE_DEFEAT_SCORE_DROP'})
            request=json.load(sys.stdin)
            if request['operation']=='classify':
              value=[namespace['is_life_advance_step'](step) for step in request['steps']]
            elif request['operation']=='recent':
              value=namespace['_recent_war_tactics'](request['history'],request['snapshot'],army_id=request['army_id'],war_id=request['war_id'])
            else: raise ValueError('unknown compatibility operation')
            print(json.dumps({'value':value},ensure_ascii=False,separators=(',',':')))
            """;
    static Value call(Obj request) throws IOException, InterruptedException {
        Path repository = Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path root = repository.resolve("ck3_autonomous_player/src/xar_autoplayer");
        Path strategy = checked(root.resolve("strategy.py"), "52b4381758ee712dc8555ac3a31186e13adbe10c3c18dc93b23bca5147934111");
        Path war = checked(root.resolve("bridge/war_contract.py"), "b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937");
        Path units = checked(root.resolve("bridge/public_unit_contract.py"), "0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e");
        Path window = checked(root.resolve("bridge/route_contact_window_contract.py"), "b517fc1eb1efe3b21842109904387f6a2e953c6b46d7b3dec6656710b161b455");
        var builder = new ProcessBuilder(List.of(required("xar.native.producer.python"), "-I", "-B", "-c", SCRIPT,
                strategy.toString(), war.toString(), units.toString(), window.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process child = builder.start();
        try {
            try (var input = child.getOutputStream()) { input.write(OpportunityJson.encode(request)); }
            if (!child.waitFor(30, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new AssertionError("original tactics oracle exceeded finite timeout"); }
            byte[] output = child.getInputStream().readAllBytes(), error = child.getErrorStream().readAllBytes();
            assertEquals(0, child.exitValue(), () -> "actual original tactics producer failed: " + new String(error, StandardCharsets.UTF_8));
            assertTrue(output.length > 0 && output.length <= 1_048_576, "bounded complete original tactics output required");
            return DriverJson.object(output, 1_048_576).get("value");
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static Path checked(Path source, String digest) throws IOException {
        assertEquals(digest, DriverJson.sha256(Files.readAllBytes(source)), "actual original tactics source drifted: " + source); return source;
    }
    private static String required(String property) {
        String value = System.getProperty(property); assertTrue(value != null && !value.isBlank(), "NOT EXECUTED: original tactics oracle requires " + property); return value;
    }
}
