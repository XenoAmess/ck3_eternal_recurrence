package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.node.ArrayNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationIndependentPoststate.*;

/** Invokes only the existing pure original producer in a separate process. Not a Java runtime fallback. */
final class RiteCreationIndependentPoststateOriginalProducerTest {
    private static final String DRIVER_SHA="eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final Map<String,String> SOURCES=Map.of(
        "rite_creation_action_private_v1.py","1712e0de76e2975baa9e8185bf7ee7746c1b8697e2369349f5d807085a2c9f81",
        "player_religion_context_private_transport.py","59d34ed3cd432804495e129097ea86b88353f112a27b7c2cf2483c08ab192c06",
        "ingame_decisions_open_contract.py","86559e259b64c541909e75835f016822a8bb6fd7c4febb5a822f23fa1dad863d",
        "version_identity.py","9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086",
        "nonwar_private_build.py","fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9",
        "driver.py","eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6",
        "title_map_navigation_contract.py","e556fc2347c5fff4acbf4aedd2a09821a9f68a84ad0ac9adf2a1994cea6151d6");
    private static final String SCRIPT="""
        import hashlib,json,pathlib,sys
        driver=pathlib.Path(sys.argv[1]).resolve()
        if hashlib.sha256(driver.read_bytes()).hexdigest()!=sys.argv[2]: raise ValueError('original native driver drift')
        pins=json.loads(sys.argv[3]); before={driver:driver.read_bytes()}
        for name,sha in pins.items():
            path=driver.with_name(name); data=path.read_bytes()
            if hashlib.sha256(data).hexdigest()!=sha: raise ValueError('original helper source drift: '+name)
            before[path]=data
        sys.path.insert(0,str(driver.parents[2]))
        from xar_autoplayer.bridge import rite_creation_action_private_v1 as producer
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        if pathlib.Path(producer.__file__).resolve()!=driver.with_name('rite_creation_action_private_v1.py'): raise ValueError('another original imported')
        # This invokes the original exported pure helper, its original _binding,
        # version checks and actual imported religion normalizer. No driver/server is constructed.
        result=[]
        for case in json.load(sys.stdin):
            try:
                value=producer.evaluate_independent_poststate_v1(**case)
                result.append({'accepted':True,'value':value})
            except (ValueError,KeyError,BridgeUnavailableError):
                result.append({'accepted':False})
        for path,data in before.items():
            if path.read_bytes()!=data: raise ValueError('original producer changed during oracle')
        json.dump(result,sys.stdout,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        """;
    @Test void allOriginalDiagnosticBranchesAndStrictUserIntegerStrengtheningAreCompared()throws Exception{
        var tests=RiteCreationIndependentPoststateTest.cases();var input=empty().putArray("cases");
        for(var c:tests){
            var row=input.addObject().put("expected_outcome_kind",c.expected().wire());
            row.set("before_snapshot",c.before());row.set("after_snapshot",c.after());row.set("before_context",c.first());row.set("after_context",c.last());row.set("quoted_piety_cost_raw",c.quote());
        }
        var actual=oracle(input);assertEquals(tests.size(),actual.size());int accepted=0,rejected=0,strengthened=0;
        for(int i=0;i<tests.size();i++){
            var c=tests.get(i);var row=object(actual.get(i));assertEquals(c.originalAccepted(),bool(get(row,"accepted")),c.name());
            if(c.accepted()){
                assertEquals(object(new RawJson(get(row,"value").toString().getBytes(StandardCharsets.UTF_8))),
                    object(encode(RiteCreationIndependentPoststateTest.run(c))),c.name());accepted++;
            }else{
                assertThrows(IllegalArgumentException.class,()->RiteCreationIndependentPoststateTest.run(c),c.name());rejected++;
                if(c.originalAccepted())strengthened++;
            }
        }
        assertTrue(accepted>=14&&rejected>=25);assertEquals(1,strengthened,"only documented exact-integer wallet scale strengthening");
    }
    private static ArrayNode oracle(ArrayNode input)throws Exception{
        Path python=Path.of(required("xar.native.producer.python")),source=Path.of(required("xar.native.producer.source"));
        assertTrue(python.isAbsolute()&&source.isAbsolute(),"NOT_RUN: absolute original executable/source required");
        assertEquals(DRIVER_SHA,required("xar.native.producer.sha256"));
        assertTrue(Files.isRegularFile(python)&&Files.isRegularFile(source),"NOT_RUN: actual producer environment missing");
        assertEquals(DRIVER_SHA,sha(Files.readAllBytes(source)));var pins=empty();
        for(var e:SOURCES.entrySet()){assertEquals(e.getValue(),sha(Files.readAllBytes(source.resolveSibling(e.getKey()))));pins.put(e.getKey(),e.getValue());}
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-X","utf8","-c",SCRIPT,source.toString(),DRIVER_SHA,pins.toString()).redirectErrorStream(true);
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONIOENCODING","utf-8");
        Process process=builder.start();
        try(var reader=Executors.newSingleThreadExecutor(Thread.ofVirtual().factory())){
            var output=reader.submit(()->process.getInputStream().readNBytes(1048577));
            try{
                try(var stdin=process.getOutputStream()){stdin.write(input.toString().getBytes(StandardCharsets.UTF_8));}
                assertTrue(process.waitFor(30,TimeUnit.SECONDS),"NOT_RUN/FAIL: original helper timed out");
                byte[] bytes=output.get(5,TimeUnit.SECONDS);assertTrue(bytes.length>0&&bytes.length<=1048576);
                assertEquals(0,process.exitValue(),new String(bytes,0,Math.min(bytes.length,4096),StandardCharsets.UTF_8));
                return assertInstanceOf(ArrayNode.class,org.xar.ck3.control.contracts.StrictJson.parse(bytes,1048576));
            }finally{if(process.isAlive()){process.destroyForcibly();assertTrue(process.waitFor(5,TimeUnit.SECONDS),"original cleanup unproved");}}
        }
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"NOT_RUN: required original property "+key);assertFalse(value.isBlank(),"NOT_RUN: required original property "+key);return value;}
    private static String sha(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
}

