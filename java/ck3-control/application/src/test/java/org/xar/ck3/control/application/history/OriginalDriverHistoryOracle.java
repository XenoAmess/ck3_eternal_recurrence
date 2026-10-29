package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Assertions;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Executes the unchanged original producer AST. Only unrelated file persistence is replaced by a no-write test double. */
final class OriginalDriverHistoryOracle {
    private OriginalDriverHistoryOracle() { }
    private static final String DRIVER_SHA = "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String IDENTITY_SHA = "80409033090bbbf437c304db7bc7c83e19524dff0f5f8390e000815eb47ac938";
    private static final String SCRIPT = """
            import ast, copy, json, pathlib, sys, threading, types, __future__
            driver_path, identity_path = map(pathlib.Path, sys.argv[1:3])
            namespace = {'copy':copy, '_RESTORE_CHECKPOINT_STEP':'restore-checkpoint',
              '_CHECKPOINT_ANCHOR_STEPS':frozenset({'save-checkpoint','restore-phase2-span-source-checkpoint-v1'}),
              '_COLD_RESTORE_SOURCE':'native-session-cold-start'}
            exec(compile(identity_path.read_text(encoding='utf-8'), str(identity_path), 'exec'), namespace)
            tree=ast.parse(driver_path.read_text(encoding='utf-8'))
            wanted={'_checkpoint_history_index','_proven_restore_lineage_row','_checkpoint_history_with_restore_lineage',
                    '_same_restore_process_replacement','_effective_native_history_entry','_native_history_after_latest_restore','_positive_native_id'}
            selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
            assert {node.name for node in selected} == wanted
            method=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='_record_command']
            assert len(method)==1
            selected.extend(method)
            exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])), str(driver_path), 'exec',
                 flags=__future__.annotations.compiler_flag), namespace)
            request=json.load(sys.stdin)
            if request['operation']=='retain':
              value=namespace['_checkpoint_history_with_restore_lineage'](request['checkpoint'],request['history'])
            elif request['operation']=='effective':
              value=namespace['_effective_native_history_entry'](request['row'])
            elif request['operation']=='after':
              value=namespace['_native_history_after_latest_restore'](request['history'])
            elif request['operation']=='record':
              namespace['_is_deferred_read_only_history_step']=lambda step:False
              namespace['is_life_advance_step']=lambda step:False
              namespace['CONTINUE_AS_RECONCILED_SUCCESSOR_STEP']='continue-as-reconciled-successor'
              owner=types.SimpleNamespace(_history_lock=threading.RLock(),_last_checkpoint=request['checkpoint'],
                  _command_history=copy.deepcopy(request['history']),_managed_restore_transaction=None,
                  _pending_cold_candidate=None,state_dir=None,_driver_state_dirty=False,
                  _persist_driver_state=lambda **kw:None,_route_horizon_wal_eligible_v1=lambda *args:False)
              completed=request['completed']
              namespace['_record_command'](owner,'restore-checkpoint',ok=True,result=completed['result'])
              value=owner._command_history
            else: raise ValueError('unknown operation')
            print(json.dumps({'value':value},ensure_ascii=False,separators=(',',':')))
            """;
    static Value call(Obj request) throws IOException, InterruptedException {
        Assertions.assertEquals(DRIVER_SHA, required("xar.native.producer.sha256"), "selected original Driver producer differs from this migrated contract");
        Path driver = checkedSource(Path.of(required("xar.native.producer.source")), DRIVER_SHA);
        Path repository = Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path identity = checkedSource(repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/restore_checkpoint_type_contract_v1.py"), IDENTITY_SHA);
        String python = required("xar.native.producer.python");
        ProcessBuilder command = new ProcessBuilder(List.of(python, "-I", "-B", "-c", SCRIPT, driver.toString(), identity.toString()));
        command.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process child = command.start();
        try {
            try (var input = child.getOutputStream()) { input.write(OpportunityJson.encode(request)); }
            boolean finished = child.waitFor(Duration.ofSeconds(30).toMillis(), TimeUnit.MILLISECONDS);
            if (!finished) { child.destroyForcibly(); throw new AssertionError("original producer differential exceeded its finite timeout"); }
            byte[] output = child.getInputStream().readAllBytes(), error = child.getErrorStream().readAllBytes();
            Assertions.assertEquals(0, child.exitValue(), () -> "original Python producer failed: " + new String(error, java.nio.charset.StandardCharsets.UTF_8));
            Assertions.assertTrue(output.length > 0 && output.length <= 1024 * 1024, "bounded complete original producer output required");
            return DriverJson.object(output, 1024 * 1024).get("value");
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static Path checkedSource(Path source, String sha256) throws IOException {
        Path path = source.toAbsolutePath().normalize();
        Assertions.assertEquals(sha256, DriverJson.sha256(Files.readAllBytes(path)), "actual unchanged original producer SHA drifted: " + path);
        return path;
    }
    private static String required(String name) {
        String value = System.getProperty(name);
        Assertions.assertTrue(value != null && !value.isBlank(), "original producer differential NOT RUN: required property missing: " + name);
        return value;
    }
}
