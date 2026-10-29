package org.xar.ck3.control.service.root;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** The exact original try-body is executed as a DATA oracle, without importing a backend or creating a Game. */
final class RootArmyEntryFailureOriginalOracleTest {
    @Test void originalCurrentFailureRecordsFalseNoResultOnceWithoutAnotherSnapshot()throws Exception {
        Path repository=Path.of(required("xar.repository.root"));
        Path original=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        byte[] bytes=Files.readAllBytes(original);
        assertEquals(1658471,bytes.length);
        assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        Path outputRoot=Path.of(required("xar.test.output.root"));
        assertTrue(outputRoot.isAbsolute(),"an explicitly granted test output root is required");
        Path run=Files.createTempDirectory(outputRoot,"army-entry-original-");
        Path stdout=run.resolve("stdout.json"),stderr=run.resolve("stderr.txt");
        String script="""
                import ast,json,sys
                tree=ast.parse(open(sys.argv[1],encoding='utf-8').read())
                nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='query_army_strengths' and n.lineno==14515]
                assert len(nodes)==1
                function=nodes[0]
                function.decorator_list=[]
                module=ast.Module(body=[function],type_ignores=[])
                scope={'ORDINARY_CORE_PROFILE':'ordinary_core_v1','require_army_strengths_profile':lambda value:value,
                    'start_army_timing':lambda *a,**k:None,'finish_army_timing':lambda *a,**k:None,
                    'QUERY_ARMY_STRENGTHS_STEP':'query-army-strengths-v1'}
                exec(compile(ast.fix_missing_locations(module),sys.argv[1],'exec'),scope)
                error=RuntimeError('actual entry failure')
                class OriginalBoundary:
                    def __init__(self):self.attempts=0;self.rows=[]
                    def take_internal_semantic_snapshot(self):
                        self.attempts+=1
                        raise error
                    def _record_command(self,command,**fields):self.rows.append({'command':command,**fields})
                boundary=OriginalBoundary()
                try:scope['query_army_strengths'](boundary)
                except RuntimeError as actual:same=actual is error
                else:raise AssertionError('the original source failure was lost')
                print(json.dumps({'attempts':boundary.attempts,'rows':boundary.rows,'same_error':same},sort_keys=True))
                """;
        Process process=new ProcessBuilder(required("xar.python"),"-X","utf8","-c",script,original.toString())
                .redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();fail("original Army oracle exceeded its finite deadline");}
        assertEquals(0,process.exitValue(),Files.readString(stderr,StandardCharsets.UTF_8));
        var result=StrictJson.parse(Files.readAllBytes(stdout));
        assertEquals(1,result.path("attempts").intValue());assertTrue(result.path("same_error").booleanValue());
        var rows=result.path("rows");assertEquals(1,rows.size());var row=rows.get(0);
        assertEquals("query-army-strengths-v1",row.path("command").textValue());
        assertFalse(row.path("ok").booleanValue());assertTrue(row.get("result").isNull());
        assertEquals("RuntimeError: actual entry failure",row.path("error").textValue());
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"missing "+key);assertFalse(value.isBlank(),"blank "+key);return value;}
}
