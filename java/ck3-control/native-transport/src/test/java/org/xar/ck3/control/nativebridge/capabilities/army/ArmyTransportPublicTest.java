package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTransportPublicCodec.*;

/** Production request/wire/normalizer/public consumer boundary; original Python oracle is read-only, never a backend. */
final class ArmyTransportPublicTest {
    @Test void allPublicRevisionBoundariesAndMissingNullScopeRemainDistinct(){
        for(String value:List.of("1","9007199254740991","\"9007199254740992\"","\"18446744073709551615\""))assertNotNull(revision(raw("{\"expected_revision\":"+value+"}")));
        for(String value:List.of("true","false","1.0","0","-1","9007199254740992","null","\"01\"","\"+1\"","\"18446744073709551616\"","\"1\n\""))assertThrows(IllegalArgumentException.class,()->revision(raw("{\"expected_revision\":"+value+"}")));
        assertThrows(IllegalArgumentException.class,()->revision(raw("{}")));assertThrows(IllegalArgumentException.class,()->empty(raw("{\"extra\":null}")));
        var missing=samplingSet(raw("{\"enabled\":true,\"observer_family\":\"regular_core\",\"expected_revision\":1}"));
        var nil=samplingSet(raw("{\"enabled\":true,\"observer_family\":\"regular_core\",\"expected_revision\":1,\"regular_core_full_carmy_ids\":null}"));
        assertEquals(Presence.MISSING,missing.subjects().presence());assertEquals(Presence.NULL,nil.subjects().presence());assertEquals(missing.selection(),nil.selection());assertEquals(missing,samplingSet(encode(missing)));assertEquals(nil,samplingSet(encode(nil)));
        for(String value:List.of("[]","[-1]","[1,1]","[true]","[1.0]","[2147483648]"))assertThrows(IllegalArgumentException.class,()->samplingSet(raw("{\"enabled\":true,\"observer_family\":\"regular_core\",\"expected_revision\":1,\"regular_core_full_carmy_ids\":"+value+"}")));
        var actual=samplingSet(raw("{\"enabled\":true,\"observer_family\":\"regular_core\",\"expected_revision\":\"18446744073709551615\",\"regular_core_full_carmy_ids\":[-2147483648,2147483647]}"));
        assertEquals(List.of(Integer.MIN_VALUE,Integer.MAX_VALUE),actual.selection().subjects().orElseThrow());assertEquals(actual,samplingSet(encode(actual)));assertEquals(actual.selection(),ArmyObserverSampling.selection(ArmyJson.parse(ArmyObserverSampling.request(ArmyObserverSampling.ENABLE,actual.selection()).additionalFields().bytes())));
        assertThrows(IllegalArgumentException.class,()->samplingSet(raw("{\"enabled\":\"true\",\"observer_family\":\"all\",\"expected_revision\":1}")));
        for(String mode:List.of("OFF","bogus","use "))assertThrows(IllegalArgumentException.class,()->scalarSet(raw("{\"mode\":\""+mode+"\",\"expected_revision\":1}")));
    }
    @Test void actualWirePacketTypedRowsAndPublicCounterRolesRoundTrip()throws Exception {
        var selected=new ArmyObserverSampling.Selection(ArmyObserverSampling.Family.REGULAR_CORE,Optional.empty());var nativeResult=result(true,true);
        var envelope=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id","original-query").put("ok",true);envelope.set("result",nativeResult);
        var wire=(NativeWire.CommandResult)NativeWire.decode(NativeWire.packet(ArmyJson.bytes(envelope)));
        var result=ArmyObserverSampling.decode(new RawJson(wire.result().token().orElseThrow().value()),ArmyObserverSampling.QUERY,selected);
        assertEquals(new BigInteger("18446744073709551615"),result.rows().getFirst().epoch());
        var seed=ArmyStrengthsSourceTest.input(ArmyJson.empty(),ArmyStrengthsSourceTest.projectedHello());var publicResult=ArmyObserverSampling.publicResult(result,seed.snapshot().context().before(),new BigInteger("18446744073709551615"));
        var internal=ArmyObserverSampling.driverResult(result,seed.snapshot().context().before(),new BigInteger("18446744073709551615"));
        assertTrue(ArmyJson.parse(internal.bytes()).at("/army_observer_research_sampling_v1/regular_core/epoch").isIntegralNumber());
        var parsed=ArmyJson.parse(publicResult.bytes());assertEquals("18446744073709551615",parsed.at("/army_observer_research_sampling_v1/regular_core/epoch").textValue());
        assertEquals("18446744073709551615",parsed.get("queried_connection_generation").textValue());assertTrue(parsed.get("queried_player_character_id").isIntegralNumber());assertEquals(parsed,ArmyJson.parse(new RawJson(publicResult.bytes()).bytes()));
        var roles=DriverReadHistoryRichMaterial.PublicNumbers.fromResults(internal,publicResult);
        var originalTree=DriverJson.object(internal.bytes(),RawJson.MAXIMUM_BYTES);var exposedTree=DriverJson.object(publicResult.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(exposedTree,roles.toPublic(originalTree));assertEquals(originalTree,roles.fromPublic(exposedTree));
        assertEquals(roles,DriverReadHistoryRichMaterial.PublicNumbers.fromJson(roles.toJson()));
        assertThrows(IllegalArgumentException.class,()->new DriverReadHistoryRichMaterial.PublicNumbers(List.of()).toPublic(originalTree));
        var changed=parsed.deepCopy();changed.put("queried_revision","01");
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRichMaterial.PublicNumbers.fromResults(internal,new RawJson(ArmyJson.bytes(changed))));
        var wrongType=parsed.deepCopy();ArmyJson.object(wrongType.at("/army_observer_research_sampling_v1/regular_core")).put("installed","true");
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRichMaterial.PublicNumbers.fromResults(internal,new RawJson(ArmyJson.bytes(wrongType))));
        for(String key:List.of("epoch","active_captures","retained_records","qualified_records"))for(String token:List.of("true","1.0","\"1\"","-1","18446744073709551616")){
            var bad=nativeResult.deepCopy();ArmyJson.object(bad.at("/army_observer_research_sampling_v1/regular_core")).set(key,ArmyJson.parseValue(token.getBytes(StandardCharsets.UTF_8),100));
            assertThrows(IllegalArgumentException.class,()->ArmyObserverSampling.decode(new RawJson(ArmyJson.bytes(bad)),ArmyObserverSampling.QUERY,selected));
        }
        var wrong=nativeResult.deepCopy();ArmyJson.object(wrong.at("/army_observer_research_sampling_v1/regular_core")).put("busy",true);
        assertThrows(IllegalArgumentException.class,()->ArmyObserverSampling.decode(new RawJson(ArmyJson.bytes(wrong)),ArmyObserverSampling.QUERY,selected));
        assertThrows(IllegalArgumentException.class,()->bounded(raw("{\"native_command_history\":[]}")));
    }
    static ObjectNode result(boolean enabled,boolean available){var root=ArmyJson.empty().put("step",ArmyObserverSampling.QUERY).put("accepted",true).put("status","completed");root.putObject("army_observer_research_sampling_v1").putObject("regular_core").put("installed",true).put("available",available).put("capture_enabled",enabled).put("busy",false).put("clear_completed",!enabled).put("epoch",new BigInteger("18446744073709551615")).put("active_captures",0).put("retained_records",0).put("qualified_records",0).put("status",!available?"unavailable":enabled?"enabled":"disabled").put("readiness",!available?"unavailable":enabled?"awaiting_sample":"off");return root;}
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    @Test void originalPythonNineFamilyNormalizerIsTheIndependentReadonlyOracle()throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"set xar.repository.root for the original Python parity fixture");
        Path source=Path.of(repository,"ck3_autonomous_player/src/xar_autoplayer/bridge/army_observer_research_sampling_control.py");byte[] original=Files.readAllBytes(source);
        assertEquals("927fdbb94ae5c07a14f4039595c865af3b28eac0ecdb0fb629ead9b38016b5ae",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        String script="import json,runpy,sys\nm=runpy.run_path(sys.argv[1])\np=json.load(sys.stdin)\np['backend_id']='native-headless'\nprint(json.dumps(m['normalize_result'](p,expected_step=m['QUERY_STEP'],observer_family='regular_core'),ensure_ascii=False,allow_nan=False))";
        for(var nativeResult:List.of(result(true,true),result(false,true),result(true,false))){
            var process=new ProcessBuilder(System.getProperty("xar.python.command","python"),"-c",script,source.toString()).redirectErrorStream(true).start();
            process.getOutputStream().write(ArmyJson.bytes(nativeResult));process.getOutputStream().close();
            byte[] output=process.getInputStream().readAllBytes();assertTrue(process.waitFor(15,TimeUnit.SECONDS));assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8));
            var oracle=ArmyJson.parse(output);var selection=new ArmyObserverSampling.Selection(ArmyObserverSampling.Family.REGULAR_CORE,Optional.empty());
            var decoded=ArmyObserverSampling.decode(new RawJson(ArmyJson.bytes(nativeResult)),ArmyObserverSampling.QUERY,selection);
            assertEquals(oracle.get("accepted").booleanValue(),decoded.accepted());var row=oracle.at("/army_observer_research_sampling_v1/regular_core");var actual=decoded.rows().getFirst();
            assertEquals(row.get("epoch").bigIntegerValue(),actual.epoch());assertEquals(row.get("status").textValue(),actual.status().wire());assertEquals(row.get("readiness").textValue(),actual.readiness().wire());
            assertEquals(row.get("capture_enabled").booleanValue(),actual.enabled());assertEquals(row.get("available").booleanValue(),actual.available());
        }
    }
}
