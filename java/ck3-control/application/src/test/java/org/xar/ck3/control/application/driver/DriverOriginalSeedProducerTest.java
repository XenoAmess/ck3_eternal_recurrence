package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Executes the pinned original full Driver producer, then the actual Java decoder/repository/assembler. */
final class DriverOriginalSeedProducerTest {
    @TempDir Path temporary;
    private int sequence;
    private static final String ORIGINAL_PAYLOAD="""
        import ast,base64,copy,hashlib,json,sys,types
        from pathlib import Path
        source=Path(sys.argv[1]).read_bytes()
        if hashlib.sha256(source).hexdigest()!=sys.argv[2]: raise RuntimeError('original Driver source drift')
        tree=ast.parse(source.decode('utf-8-sig'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeHeadlessGameplayDriver')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_driver_state_payload_locked')
        scope={'copy':copy,'_NATIVE_DRIVER_STATE_VERSION':2}
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        module=ast.fix_missing_locations(ast.Module(body=[future,method],type_ignores=[]))
        exec(compile(module,str(Path(sys.argv[1])),'exec'),scope)
        row=json.loads(base64.b64decode(sys.argv[3]))
        owner=types.SimpleNamespace(pipe_name=row['pipe_name'],_session_bridge_pid=row['bridge_pid'],
          _episode_character_id=row['episode_character_id'],_episode_run_id=row['episode_run_id'],
          _last_checkpoint=row['last_checkpoint'],_command_history=row['command_history'],
          _rollback_war_failures=row['rollback_war_failures'],_managed_restore_transaction=row['managed_restore_transaction'],
          _succession_expectation=row['succession_expectation'],_succession_lifecycle=row['succession_lifecycle'],
          _campaign_goal=row['campaign_goal'],_rollback_war_failures_migration_required=sys.argv[4]=='migration')
        original=scope['_driver_state_payload_locked'](owner)
        sys.stdout.buffer.write(json.dumps(original,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void originalProducerFullHistoryFlowsThroughCanonicalBoundAssemblerAndJsonRoundTrip() throws Exception {
        byte[] original=produce(DriverStateAssemblerTest.WIRE,false);
        var parsed=DriverJson.object(original,65536);
        var known=DriverFactsRepository.imported(DriverStateAssemblerTest.ref(original),original,3,7,
                DriverStateAssemblerTest.game(),new OpportunityJson.Obj(java.util.Map.of()));
        var complete=assertInstanceOf(DriverStateSnapshot.Complete.class,DriverStateAssembler.project(known,
                DriverStateAssemblerTest.snapshot(known,List.of()),Optional.empty()));
        assertEquals(parsed,DriverJson.object(complete.encode(),65536));
        assertEquals(2,complete.commandHistory().size());
        assertFalse(OpportunityJson.bool(DriverJson.object(complete.commandHistory().get(1).originalRow().json(),65536).get("ok"),"ok"));
        assertInstanceOf(DriverStateSnapshot.Value.class,complete.managedRestoreTransaction());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,complete.successionExpectation());
    }
    @Test void originalMigrationProducerKeepsAbsentPluralDistinctFromExplicitNullAndEmpty() throws Exception {
        byte[] original=produce(DriverStateAssemblerTest.WIRE,true);
        var complete=DriverStateSnapshot.decodeComplete(original);
        assertInstanceOf(DriverStateSnapshot.Missing.class,complete.rollbackWarFailures());
        assertFalse(DriverJson.object(complete.encode(),65536).members().containsKey("rollback_war_failures"));
        assertEquals(2,complete.commandHistory().size());
        assertInstanceOf(DriverStateSnapshot.Value.class,complete.rollbackWarFailure());
    }
    @Test void actualProducerWrongIntegerTokensAreRejectedAtJavaBoundary() throws Exception {
        for(String input:List.of(DriverStateAssemblerTest.WIRE.replace("\"bridge_pid\":42","\"bridge_pid\":true"),
                DriverStateAssemblerTest.WIRE.replace("\"episode_character_id\":73","\"episode_character_id\":73.0"))) {
            byte[] actual=produce(input,false);
            assertThrows(IllegalArgumentException.class,() -> DriverStateSnapshot.decodeComplete(actual));
        }
    }
    private byte[] produce(String input,boolean migration) throws Exception {
        String python=required("xar.native.producer.python"),source=required("xar.native.producer.source"),sha=required("xar.native.producer.sha256");
        if(!Path.of(python).isAbsolute() || !Path.of(source).isAbsolute() || !sha.matches("[a-f0-9]{64}"))
            throw new IllegalStateException("NOT EXECUTED: pinned original native producer fixture required");
        Path output=temporary.resolve("driver-original-"+(++sequence)+".json"),error=temporary.resolve("driver-original-"+sequence+".stderr");
        var process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL_PAYLOAD,source,sha,
                Base64.getEncoder().encodeToString(input.getBytes(StandardCharsets.UTF_8)),migration?"migration":"complete")
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)) { process.destroyForcibly();throw new IOException("original Driver producer timeout"); }
        if(process.exitValue()!=0)throw new IOException("original Driver producer failed: "+Files.readString(error,StandardCharsets.UTF_8));
        return Files.readAllBytes(output);
    }
    private static String required(String key) {
        String value=System.getProperty(key);
        if(value==null || value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original producer binding absent: "+key);
        return value;
    }
}
