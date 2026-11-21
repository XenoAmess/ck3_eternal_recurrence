package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Real pinned C++ parser/serializer DATA through the production Java request/result contract. No live qualification. */
final class CurrentAubObserverFixtureProducerTest {
    private static ObjectNode result()throws Exception{return NativeWire.object(NativeWire.parse(CurrentAubObserverCppFrames.result("dispatched")));}
    private static CurrentAubObserverFixtureResult decode(ObjectNode n)throws IOException{return CurrentAubObserverFixtureResult.decode(new RawJson(StrictJson.canonical(n)));}
    @Test void genuineCppResultsKeepFiniteDispatchedUnknownAndRefusalMeanings()throws Exception {
        for(String name:new String[]{"dispatched","indeterminate","unavailable","claim-consumed"}) {
            var raw=CurrentAubObserverCppFrames.response(name);var decoded=CurrentAubObserverFixtureResult.decode(new RawJson(raw.result().token().orElseThrow().value()));
            assertEquals(raw.nativeOk(),decoded.dispatched());assertEquals(name.equals("dispatched"),decoded.dispatched());
        }
        var d=decode(result());assertEquals(BigInteger.ONE,d.claimSequence());assertEquals(CurrentAubObserverCppFrames.core().prefix(),d.coreBefore().orElseThrow());
        assertEquals(BigInteger.valueOf(7),d.ownerWitness().orElseThrow().connectionGeneration());assertTrue(d.cleanupKnown());
    }
    @Test void actualCppRequestCoreCreatesOnlyFixedJavaRequestAndEmitsReverseParserInput()throws Exception {
        var request=CurrentAubObserverFixture.request(CurrentAubObserverCppFrames.core());assertEquals(CurrentAubObserverFixture.STEP,request.step());assertEquals(CurrentAubObserverFixture.CAPABILITY,request.requiredCapability().orElseThrow());
        var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));assertEquals(2,fields.size());assertEquals(0,fields.get("arguments").size());
        var claim=NativeWire.object(fields.get("aub_observer_fixture"));assertEquals(13,claim.size());
        assertEquals(CurrentAubObserverFixture.SCHEMA,NativeWire.text(claim.get("schema")));assertEquals(CurrentAubObserverCppFrames.core().prefix().playedCharacterId(),claim.get("played_character_id").intValue());
        fields.put("core_control_deadline_unix_ms",2800000000000L);byte[] packet=NativeWire.execute("fixed-aub-java-qa-1",request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
        var actual=NativeWire.decodeExecuteRequest(packet);assertEquals(BigInteger.ZERO,actual.expectedRevision().orElseThrow());assertEquals(0,NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length))).get("arguments").size());
        String dir=System.getProperty("xar.current267.aub.java.requests");if(dir!=null){var p=Path.of(dir);Files.createDirectories(p);Files.write(p.resolve("fixed-aub-java-request.json"),Arrays.copyOfRange(packet,4,packet.length));}
    }
    @Test void fixtureCannotGrantMarkerBusinessProductionSaveOrCallerAuthority()throws Exception {
        for(String key:new String[]{"observer_markers_confirmed","business_pass_confirmed","production_actions_confirmed","physical_save_confirmed"}) {
            var n=result().put(key,true);assertThrows(IOException.class,()->decode(n),key);
        }
        var path=result().put("path","D:/forged/body.txt");assertThrows(IOException.class,()->decode(path));
        var schema=result().put("schema","ck3_121003_core_checkpoint_save_result_v1");assertThrows(IOException.class,()->decode(schema));
        var tuple=result().put("executable_sha256","0".repeat(64));assertThrows(IOException.class,()->decode(tuple));
    }
    @Test void exactUnsignedWitnessAndExplicitNullRulesRefuseLossyNumbers()throws Exception {
        for(String value:new String[]{"+7","07","-0","-1","18446744073709551616"}) {
            var n=result();((ObjectNode)n.get("owner_witness")).put("connection_generation",value);assertThrows(IOException.class,()->decode(n),value);
        }
        var numeric=result();((ObjectNode)numeric.get("owner_witness")).put("ticket_sequence",13);assertThrows(IOException.class,()->decode(numeric));
        byte[] floating=new String(CurrentAubObserverCppFrames.result("dispatched"),java.nio.charset.StandardCharsets.UTF_8).replace("\"thread_id\":42","\"thread_id\":42.0").getBytes(java.nio.charset.StandardCharsets.UTF_8);assertThrows(IOException.class,()->CurrentAubObserverFixtureResult.decode(new RawJson(floating)));
        var noOwner=result().putNull("owner_witness");assertThrows(IOException.class,()->decode(noOwner));
    }
    @Test void incompleteDispatchedCannotBecomeSuccessfulFixtureExecution()throws Exception {
        for(String key:new String[]{"effect_attempted","native_returned","native_accepted","cleanup_known","file_verified","file_verified_after","addresses_redacted"}) {
            var n=result().put(key,false);assertThrows(IOException.class,()->decode(n),key);
        }
        var hash=result().putNull("inbox_sha256");assertThrows(IOException.class,()->decode(hash));
        var core=result();((ObjectNode)core.get("core_before")).put("paused",false);assertThrows(IOException.class,()->decode(core));
    }
    @Test void requestDataCannotAliasOldFullUnpausedOrNonlivingCore()throws Exception {
        var p=CurrentAubObserverCppFrames.core().prefix();
        assertThrows(IllegalArgumentException.class,()->CurrentAubObserverFixture.request(new CoreFrame.Partial(ExactCk3Build.CK3_12004,p)));
        assertThrows(IllegalArgumentException.class,()->CurrentAubObserverFixture.request(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,p)));
        assertThrows(IllegalArgumentException.class,()->CurrentAubObserverFixture.request(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(p.dateRaw(),p.speed(),false,p.localPlayerId(),true,true,p.playedCharacterId(),true))));
    }
}
