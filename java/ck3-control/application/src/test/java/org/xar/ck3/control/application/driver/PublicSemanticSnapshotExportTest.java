package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleOriginFactory;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual framed Native + Driver import + manifest encoder/decoder + assembler, then the sole public semantic lane.
 * These software originals confer no Root, loaded native provider, writer, restore or Game qualification. */
final class PublicSemanticSnapshotExportTest {
    private static final BigInteger MAX64=new BigInteger("18446744073709551615");
    private static final List<String> PRIVATE=List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures");
    private static final int LIMIT=8*1024*1024;
    private record Original(DriverObservationAssembler.Complete actual,RawJson driver,RawJson manifest,RawJson nativeState){ }
    private static Original actual(String extension,boolean unsafePrivateHistory){
        String state=DriverObservationAssemblerTest.STATE.replace("\"original\":\"retained\"",
                "\"original\":\"retained\",\"connection_generation\":"+MAX64+",\"hello\":{\"connection_generation\":"+MAX64+"},\"last_heartbeat\":{\"sequence\":"+MAX64+",\"monotonic_ms\":"+MAX64+"}")
                .replace("\"active_wars\":[]","\"active_wars\":[],\"open_extension\":"+extension);
        String wire=DriverStateAssemblerTest.WIRE;
        if(unsafePrivateHistory)wire=wire.replace("\"armies\":[]","\"armies\":[],\"unqualified_revision\":"+MAX64)
                .replace("\"reason\":\"original advisory\"","\"reason\":\"original advisory\",\"unqualified_identity\":"+MAX64);
        byte[] driverWire=bytes(wire);var driver=new RawJson(driverWire);
        var known=DriverFactsRepository.imported(ref("original-driver.json",driverWire),driverWire,3,7,DriverStateAssemblerTest.game(),new Obj(java.util.Map.of()));
        byte[] stateBytes=bytes(state),envelope=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"semantic-only-full64\",\"revision\":"+MAX64+",\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(envelope.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(envelope.length).put(envelope).array();
        var session=new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),MAX64,"held-session");
        var nativeFrame=new NativeObservationPort.ObservedFrame(session,"semantic-only-full64",MAX64,new RawJson(stateBytes),packet,Instant.parse("2026-10-24T04:00:00Z"));
        // Import keeps the exact original wire; the manifest separately binds the actual complete Driver encoder bytes.
        var completeDriver=new RawJson(known.driver().encode());
        var manifest=DriverObservationEvidenceReader.encode(known,nativeFrame,MAX64,2,DriverStateAssemblerTest.source(),new Obj(java.util.Map.of()),ref("complete-driver.json",completeDriver.bytes()));
        var facts=DriverObservationEvidenceReader.decode(ref("facts.json",manifest.bytes()),manifest,completeDriver,nativeFrame);
        var actual=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,facts,ref("native.bin",packet)));
        return new Original(actual,driver,manifest,new RawJson(stateBytes));
    }
    @Test void actualCompleteToSemanticWireExcludesAllThreeHistoryRootsWithoutOmissionPlaceholders(){
        var original=actual("{\"numeric_text\":\"9007199254740993\",\"optional\":null,\"safe_revision\":73}",false);
        Obj full=original.actual().semantic();byte[] before=DriverJson.encode(full);RawJson exported=PublicSnapshotCodec.exportSemanticOnly(original.actual());
        Obj publicTree=DriverJson.object(exported.bytes(),RawJson.MAXIMUM_BYTES);
        for(String key:PRIVATE){assertTrue(full.members().containsKey(key));assertFalse(publicTree.members().containsKey(key));}
        assertFalse(publicTree.members().containsKey("native_command_history_export"));
        assertEquals(new Text(MAX64.toString()),publicTree.get("revision"));assertEquals(new Text(MAX64.toString()),publicTree.get("native_revision"));
        Obj diagnostics=object(publicTree.get("diagnostics"),"diagnostics");
        assertEquals(new Text(MAX64.toString()),diagnostics.get("connection_generation"));
        assertEquals(new Text(MAX64.toString()),object(diagnostics.get("last_heartbeat"),"heartbeat").get("sequence"));
        var expected=new LinkedHashMap<String,Value>(full.members());PRIVATE.forEach(expected::remove);
        assertEquals(new Obj(expected),PublicSnapshotCodec.decodeSemanticOnly(exported));assertArrayEquals(before,DriverJson.encode(original.actual().semantic()));
        Obj omitted=PublicSnapshotCodec.export(original.actual(),false).semantic();
        for(String key:PRIVATE)assertTrue(omitted.members().containsKey(key),"old ordinary omitted-history contract remains distinct");
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(exported));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodeSemanticOnly(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(original.actual(),false))));
    }
    @Test void originalFloatingDomainsAndDecimalTokensRemainExactWhilePrivateUnknownHistoryIsAbsent(){
        var original=actual("{\"one\":1.0,\"negative_zero\":-0.0,\"scaled\":1.2500,\"decimal_text\":\"1.0\"}",true);
        byte[] driverBefore=original.driver().bytes(),manifestBefore=original.manifest().bytes(),nativeBefore=original.nativeState().bytes();
        var result=PublicSnapshotCodec.exportSemanticOnly(original.actual());var decoded=PublicSnapshotCodec.decodeSemanticOnly(result);
        Obj extension=object(decoded.get("open_extension"),"open extension");
        assertEquals(new DecimalValue("1.0"),extension.get("one"));assertEquals(new DecimalValue("-0.0"),extension.get("negative_zero"));
        assertEquals(new DecimalValue("1.2500"),extension.get("scaled"));assertEquals(new Text("1.0"),extension.get("decimal_text"));
        assertArrayEquals(driverBefore,original.driver().bytes());assertArrayEquals(manifestBefore,original.manifest().bytes());assertArrayEquals(nativeBefore,original.nativeState().bytes());
        assertTrue(new String(original.driver().bytes(),StandardCharsets.UTF_8).contains("unqualified_identity"));
        for(String key:PRIVATE)assertFalse(decoded.members().containsKey(key));
    }
    @Test void unqualifiedUnsafeNumbersAndNonfinitePublicFloatsStillRejectRatherThanGuessingRoles(){
        var unsafe=actual("{\"revision\":"+MAX64+"}",false);
        var failure=assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportSemanticOnly(unsafe.actual()));
        assertTrue(failure.getMessage().contains("/open_extension/revision"));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportSemanticOnly(actual("{\"float\":1e9999}",false).actual()));
        var valid=PublicSnapshotCodec.exportSemanticOnly(actual("null",false).actual());
        String text=new String(valid.bytes(),StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodeSemanticOnly(new RawJson(bytes(text.replace("\"revision\":\""+MAX64+"\"","\"revision\":true")))));
    }
    @Test void exactEightMiBUtf8BoundaryAndMultibyteOverflowAreCheckedAfterPublicRoleEncoding(){
        int base=PublicSnapshotCodec.exportSemanticOnly(actual("{\"padding\":\"\"}",false).actual()).bytes().length;
        int count=LIMIT-base-32;
        var under=PublicSnapshotCodec.exportSemanticOnly(actual("{\"padding\":\""+"x".repeat(count)+"\"}",false).actual());
        count+=LIMIT-under.bytes().length;
        var exact=PublicSnapshotCodec.exportSemanticOnly(actual("{\"padding\":\""+"x".repeat(count)+"\"}",false).actual());
        assertEquals(LIMIT,exact.bytes().length);
        int overflowCount=count+1;
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportSemanticOnly(actual("{\"padding\":\""+"x".repeat(overflowCount)+"\"}",false).actual()));
        // UTF-8 byte length, not Java character count: these characters alone exceed the wire bound.
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportSemanticOnly(actual("{\"padding\":\""+"中".repeat(LIMIT/3+1)+"\"}",false).actual()));
    }
    private record Terminal(DriverObservationAssembler.FullSnapshot full,LifecycleIdentity identity) { }
    private static Terminal terminal() {
        String state=DriverObservationAssemblerTest.STATE.replace("\"character_id\":73,\"alive\":true","\"character_id\":73,\"alive\":false");
        var actual=DriverObservationAssemblerTest.actual(state);var known=DriverStateAssemblerTest.known();
        var driver=new RawJson(known.driver().encode());var driverRef=ref("terminal-driver.json",driver.bytes());
        var manifest=DriverObservationEvidenceReader.encode(known,actual,MAX64,2,DriverStateAssemblerTest.source(),new Obj(java.util.Map.of()),driverRef);
        var facts=DriverObservationEvidenceReader.decode(ref("terminal-facts.json",manifest.bytes()),manifest,driver,actual);
        var full=new DriverObservationAssembler().projectFull(actual,facts,ref("terminal-native.bin",actual.originalPacket()));
        var source=assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.project(full,
                ref("hello.bin",bytes("software original hello")),driverRef,ref("qualification.json",bytes("software source proof"))));
        return new Terminal(full,source.identity());
    }
    @Test void actualTerminalManifestUsesFullSnapshotSemanticLaneWithoutConstructingLivingComplete() {
        var original=terminal();var full=original.full();byte[] before=DriverJson.encode(full.semantic());
        // Terminal export consumes the actual FullSnapshot and its terminal origin; a data join grants no living Root authority.
        assertEquals(LifecycleIdentity.TerminalReason.DEAD,original.identity().terminalReason());
        RawJson wire=PublicSnapshotCodec.exportSemanticOnly(full,original.identity());Obj semantic=PublicSnapshotCodec.decodeSemanticOnly(wire);
        var expected=new LinkedHashMap<String,Value>(full.semantic().members());PRIVATE.forEach(expected::remove);
        assertEquals(new Obj(expected),semantic);for(String key:PRIVATE)assertFalse(semantic.members().containsKey(key));
        assertFalse(semantic.members().containsKey("native_command_history_export"));
        assertEquals(new Text(MAX64.toString()),DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES).get("revision"));
        assertFalse(bool(object(semantic.get("played_character"),"terminal player").get("alive"),"alive"));
        assertEquals(full.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encodeTerminal(full,original.identity(),true)));
        assertArrayEquals(before,DriverJson.encode(full.semantic()));assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(wire));
        var id=original.identity();var wrong=new LifecycleIdentity(id.machineId(),id.game(),"different-held-session",id.connectionGeneration(),id.subject(),id.frame(),id.currentPlayer(),id.terminalReason(),id.evidence(),id.observedAt());
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportSemanticOnly(full,wrong));
        var forged=new DriverObservationAssembler.FullSnapshot(full.actual(),full.facts(),full.semantic().with("revision",new IntegerValue(BigInteger.ONE)),full.originalEvidence(),full.fullBindingSha256());
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.exportSemanticOnly(forged,original.identity()));
    }
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(String name,byte[] bytes){return new ExactRef(Path.of(System.getProperty("java.io.tmpdir"),"xar-semantic-only-data",name).toAbsolutePath().toString(),bytes.length,DriverJson.sha256(bytes));}
}
