package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Retained real original Native endpoint fixture -> the production five-field boundary.
 * This narrow regression is not the current .4 fullPower or Root read/history qualification. */
final class WarEntryNativeEnvelopeOriginalTest {
    @Test void retainedNativeEndpointHasFiveKeysBeforeTheDriverAddsItsBackendIdentity()throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"actual original repository required");assertNotNull(python,"actual original oracle executable required");
        Path root=Path.of(repository).toRealPath(),fixture=root.resolve("ck3_autonomous_player/tests/unit/test_war_entry_assessments_bridge.py").toRealPath();
        assertTrue(fixture.startsWith(root));String before=sha(Files.readAllBytes(fixture));
        assertEquals("f7b743b252d85607f0009195c5002b2caf0ccfd15c451d15d88caea0769cd1de",before,"original native endpoint fixture source drift");
        var builder=new ProcessBuilder(python,"-B","-X","utf8","-c","import json,runpy,sys,pathlib; r=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(r/'ck3_autonomous_player/src')); m=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_war_entry_assessments_bridge.py')); print(json.dumps(m['_result'](),allow_nan=False))",repository).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");var process=builder.start();
        byte[] original;
        try(var readers=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            var out=readers.submit(()->process.getInputStream().readNBytes(1048577));var err=readers.submit(()->process.getErrorStream().readNBytes(1048577));
            try{process.getOutputStream().close();assertTrue(process.waitFor(45,java.util.concurrent.TimeUnit.SECONDS),"original Native fixture timed out");original=out.get(5,java.util.concurrent.TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(err.get(5,java.util.concurrent.TimeUnit.SECONDS),StandardCharsets.UTF_8));assertTrue(original.length<=1048576);}
            finally{if(process.isAlive())process.destroyForcibly();}
        }
        assertEquals(before,sha(Files.readAllBytes(fixture)),"original fixture changed during production read");
        var result=StrictJson.object(StrictJson.parse(original,1048576),java.util.Set.of("step","accepted","status","query_sequence","war_entry_assessments"));
        ArmyForecastReads.warEntryEnvelope(result);
        assertFalse(result.has("backend_id"));
        var wrapped=result.deepCopy().put("backend_id","later-original-driver-backend");
        assertThrows(IllegalArgumentException.class,()->ArmyForecastReads.warEntryEnvelope(wrapped),"Driver wrapping must not be accepted as original native data");
        for(String field:List.of("step","accepted","status","query_sequence","war_entry_assessments")) {
            var missing=result.deepCopy();missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->ArmyForecastReads.warEntryEnvelope(missing),field);
        }
        assertThrows(IllegalArgumentException.class,()->ArmyForecastReads.warEntryEnvelope(result.deepCopy().put("query_sequence",true)));
        assertThrows(IllegalArgumentException.class,()->ArmyForecastReads.warEntryEnvelope(result.deepCopy().put("query_sequence",1.0)));
    }
    private static String sha(byte[] original)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original));}
}
