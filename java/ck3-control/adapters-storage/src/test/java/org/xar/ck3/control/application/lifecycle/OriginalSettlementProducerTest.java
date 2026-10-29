package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

/** Compatibility-only original Python producer oracle. No new Python production implementation or silent skip. */
public final class OriginalSettlementProducerTest {
    @Test void originalPublishedSettlementProducerMatchesJavaAcrossTypedFailuresAndLargeSignedDelta() throws Exception {
        var source=getClass().getResource("/lifecycle-originals/settlement_contract.py");assertNotNull(source,"actual pinned original producer test resource is required");
        assertEquals("file",source.getProtocol(),"oracle must read the materialized original source file");
        var cases=new ArrayList<com.fasterxml.jackson.databind.JsonNode>();
        cases.add(DeathSettlementTest.ready(true,12,10));var legacy=DeathSettlementTest.ready(false,10,10);legacy.put("ready",1);legacy.put("record_written",0);cases.add(legacy);
        var negative=DeathSettlementTest.ready(false,0,0);var huge=new java.math.BigInteger("18446744073709551616");negative.put("old_record",huge);negative.put("record_delta",huge.negate());cases.add(negative);
        var unready=LifecycleJson.row();unready.put("ready",false);unready.putNull("commit_serial");cases.add(unready);
        var bool=DeathSettlementTest.ready(false,10,10);bool.put("source_character_id",true);cases.add(bool);
        var floating=DeathSettlementTest.ready(false,10,10);floating.put("commit_serial",1.0);cases.add(floating);
        var missing=DeathSettlementTest.ready(false,10,10);missing.remove("final_score");cases.add(missing);
        var raw=DeathSettlementTest.ready(false,10,10);raw.putObject("final_score").put("raw",-1).put("scale",3);cases.add(raw);
        var scalar=DeathSettlementTest.ready(false,10,10);scalar.put("final_score",new java.math.BigInteger("9".repeat(400)));cases.add(scalar);
        var exactRaw=DeathSettlementTest.ready(false,10,10);exactRaw.putObject("final_score").put("raw",new java.math.BigInteger("9".repeat(400))).put("scale",1);cases.add(exactRaw);
        var request=LifecycleJson.row().arrayNode();cases.forEach(request::add);
        String code="""
            import json,runpy,sys
            producer=runpy.run_path(sys.argv[1])['normalize_one_life_settlement']
            result=[]
            for value in json.load(sys.stdin):
                try: result.append({'valid':True,'value':producer(value)})
                except (ValueError,TypeError,OverflowError): result.append({'valid':False})
            print(json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')))
            """;
        String python=System.getenv().getOrDefault("XAR_TEST_PYTHON","python");
        var process=new ProcessBuilder(python,"-B","-X","utf8","-c",code,Path.of(source.toURI()).toString()).redirectErrorStream(true).start();
        try(var input=process.getOutputStream()){input.write(LifecycleJson.bytes(request));}
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();fail("original settlement producer did not exit within its finite test bound");}
        byte[] output=process.getInputStream().readNBytes(1024*1024);assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8));
        var wrapper=LifecycleJson.row();wrapper.set("rows",com.fasterxml.jackson.databind.json.JsonMapper.builder().build().readTree(output));
        var actual=wrapper.get("rows");assertEquals(cases.size(),actual.size());
        for(int i=0;i<cases.size();i++) {
            boolean accepted=true;java.util.Optional<DeathSettlement.Ready> javaValue=java.util.Optional.empty();
            try{javaValue=DeathSettlement.normalize(cases.get(i));}catch(IllegalArgumentException failure){accepted=false;}
            assertEquals(actual.get(i).get("valid").booleanValue(),accepted,"original producer case "+i);
            if(accepted&&javaValue.isPresent())assertTrue(LifecycleJson.same(actual.get(i).get("value"),LifecycleJson.parse(javaValue.orElseThrow().normalized(),65536)),"actual normalized case "+i);
            else if(accepted)assertFalse(actual.get(i).get("value").get("ready").booleanValue());
        }
    }
}
