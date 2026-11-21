package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies;
import org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.ObservationMode;
import org.xar.ck3.control.contracts.semantic.NativePlayedCharacter;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** NOT_NATIVE_OBSERVATION / NOT_LIVE: original production DATA encoder/Driver/archive reader only.
 * Declared source references do not witness any file or loaded DLL, create Managed custody, or qualify restore/control. */
final class DriverIdentityOnlyArmy142ArchiveDataTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Instant NOW=Instant.parse("2026-11-21T00:00:00Z");
    private static final String SOURCE_SHA="3601748c4d4824509416d61c779f16eda6f97b85cd5608786ecf5645215b733c";
    private static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(String name,byte[] value){return new ExactRef("software-data/"+name,value.length,DriverJson.sha256(value));}
    private static ExactRef expectedSource(){return new ExactRef(System.getProperty("xar.current142.dll","D:/software-data/not-loaded-current142.dll"),12396032L,SOURCE_SHA);}
    private static ExactRef prior126(){return new ExactRef("D:/software-data/not-loaded-current126.dll",12395520L,"30c21218df7b9ca567b30f5a02fe31731c790db1397e0ecc45b89aa502e617ea");}
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));}
    private static G2Source source(){return new G2Source("software-machine",NOW.toString(),BUILD.version()+"@"+BUILD.executableSha256(),ref("source",bytes("DATA source, no Native authority")));}
    private static DriverSnapshotFacts.Known known(){return DriverFactsRepository.imported(ref("driver-input",bytes(WIRE)),bytes(WIRE),3,7,game(),new OpportunityJson.Obj(Map.of()));}
    private static ObjectNode identity(String schema){return StrictJson.object().put("schema",schema).put("game_version",BUILD.version())
            .put("executable_sha256",BUILD.executableSha256()).put("adapter_id",BUILD.coreFullAdapterId()).put("backend",BUILD.coreFullBackend());}
    private static NativeObservationPort.ObservedFrame frame(){
        var root=identity(NativeSemanticNormalizer.FLORIN_SCHEMA).put("paused",true).put("map_ready",true).put("speed",3).put("date_raw",53179368);
        root.set("played_character",identity(NativePlayedCharacter.FLORIN_SCHEMA).put("character_id",73).put("alive",true));
        root.putNull("active_event");root.putNull("pending_character_interaction");root.putNull("one_life_terminal_reason");root.putArray("active_wars");root.putObject("diagnostics");
        var armies=root.putArray("player_armies");for(int unit:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE})
            armies.addObject().put("army_id",unit).put("owner_character_id",73).put("controllable",true);
        byte[] state=DriverJson.encode(DriverJson.fromNode(root));
        byte[] prefix=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"native:9\",\"revision\":9,\"state\":");
        byte[] raw=ByteBuffer.allocate(prefix.length+state.length+1).put(prefix).put(state).put((byte)'}').array();
        byte[] framed=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
        var session=new NativeObservationPort.TransportSession("software-machine",game(),BigInteger.valueOf(5),"software-only-session");
        return new NativeObservationPort.ObservedFrame(session,"native:9",BigInteger.valueOf(9),new RawJson(state),framed,NOW);
    }
    private record Bundle(DriverSnapshotFacts.Known known,NativeObservationPort.ObservedFrame actual,RawJson driver,RawJson manifest,ExactRef manifestRef,ExactRef nativeRef){}
    private static Bundle bundle(ExactRef declared){
        var actual=frame();var known=known();var driver=new RawJson(known.driver().encode());
        var manifest=DriverObservationEvidenceReader.encodeIdentityOnly126(known,actual,BigInteger.valueOf(2),3,source(),new OpportunityJson.Obj(Map.of()),ref("driver",driver.bytes()),declared);
        return new Bundle(known,actual,driver,manifest,ref("manifest",manifest.bytes()),ref("native",actual.originalPacket()));
    }
    private static DriverObservationAssembler.Result replay(Bundle b,RawJson manifest,ExactRef expected){return DriverObservationEvidenceReader.replayIdentityOnly126Originals(
            ref("manifest",manifest.bytes()),manifest,b.driver(),b.actual().originalPacket(),b.nativeRef(),expected);}
    @Test void exact142SupportsBothExplicitDataContractsWithoutGrantingEitherRuntimeMode(){
        var selected=expectedSource();assertTrue(FlorinPlayerArmies.identityOnly126SourceMatches(selected));
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(selected));
        assertTrue(FlorinPlayerArmies.identityOnly126SourceMatches(prior126()));assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(prior126()));
        for(var wrong:List.of(new ExactRef(selected.path(),selected.bytes()-1,selected.sha256()),new ExactRef(selected.path(),selected.bytes(),"0".repeat(64)))){
            assertFalse(FlorinPlayerArmies.identityOnly126SourceMatches(wrong));assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(wrong));
            assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(wrong,"native:9",BigInteger.valueOf(9),NOW.plusSeconds(30)));
        }
        var revision=new BigInteger("9007199254740993");var until=Instant.parse("2030-01-02T03:04:05.123456789Z");
        var data=FullSnapshotClockControl.requestMappedSave112(selected,"native:"+revision,revision,until);
        assertEquals("save-checkpoint",data.step());assertEquals(Optional.of("game.command.save-checkpoint"),data.requiredCapability());
        var fields=StrictJson.parse(data.additionalFields().bytes()).path("full_snapshot_clock_control");
        assertEquals(BUILD.version(),fields.path("game_version").textValue());assertEquals(BUILD.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(revision,fields.path("native_revision").bigIntegerValue());assertEquals(until.toEpochMilli(),fields.path("deadline_unix_ms").longValue());
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(BUILD,"save-checkpoint","native:"+revision,revision,until));
    }
    @Test void theProductionVersion2EncoderAndArchiveReaderPreserve142SourceAndAllDriverOriginals(){
        var value=bundle(expectedSource());byte[] nativeBefore=value.actual().originalPacket(),driverBefore=value.driver().bytes();
        var independentlyExpected=expectedSource();
        var facts=DriverObservationEvidenceReader.decodeIdentityOnly126(value.manifestRef(),value.manifest(),value.driver(),value.actual(),independentlyExpected);
        assertEquals(ObservationMode.IDENTITY_ONLY126,facts.armyObservationMode());assertEquals(Optional.of(independentlyExpected),facts.identityOnly126Source());
        var direct=new DriverObservationAssembler().assemble(value.actual(),facts,value.nativeRef());
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,direct,direct::toString);
        var restored=replay(value,value.manifest(),independentlyExpected);assertEquals(complete,assertInstanceOf(DriverObservationAssembler.Complete.class,restored,restored::toString));
        assertArrayEquals(nativeBefore,value.actual().originalPacket());assertArrayEquals(driverBefore,value.driver().bytes());
        assertEquals(value.nativeRef(),complete.originalEvidence());
        assertEquals(ref("driver",driverBefore),DriverObservationEvidenceReader.identityOnly126DriverReference(value.manifestRef(),value.manifest(),independentlyExpected));
        var rows=(OpportunityJson.Arr)complete.semantic().get("player_armies");assertEquals(4,rows.items().size());
        int[] ids={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE};
        for(int i=0;i<ids.length;i++){
            var row=(OpportunityJson.Obj)rows.items().get(i);assertEquals(3,row.members().size());
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(ids[i])),row.get("army_id"));
        }
    }
    @Test void independentExpectedSourcePacketAndVersion1NeverAcquireIdentityRestoreSemantics(){
        var value=bundle(expectedSource());
        for(var wrong:List.of(new ExactRef(expectedSource().path()+".other",expectedSource().bytes(),SOURCE_SHA),
                new ExactRef(expectedSource().path(),expectedSource().bytes()-1,SOURCE_SHA),prior126()))
            assertThrows(IllegalArgumentException.class,()->replay(value,value.manifest(),wrong));
        var prior=bundle(prior126());assertThrows(IllegalArgumentException.class,()->replay(prior,prior.manifest(),expectedSource()));
        var row=DriverJson.object(value.manifest().bytes(),DriverJson.MAX_NATIVE_BYTES);
        for(var changed:List.of(row.with("identity_only126_source",DriverObservationEvidenceReader.reference(prior126())),
                row.with("army_observation_mode",new OpportunityJson.Text("RICH")))){
            var manifest=RawJson.fullMaterial(DriverJson.encode(changed));assertThrows(IllegalArgumentException.class,()->replay(value,manifest,expectedSource()));
        }
        byte[] corrupt=value.actual().originalPacket();corrupt[corrupt.length-2]^=1;
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.replayIdentityOnly126Originals(value.manifestRef(),value.manifest(),value.driver(),corrupt,value.nativeRef(),expectedSource()));
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.replayOriginals(value.manifestRef(),value.manifest(),value.driver(),value.actual().originalPacket(),value.nativeRef()));
        var v1=DriverObservationEvidenceReader.encode(value.known(),value.actual(),BigInteger.valueOf(2),3,source(),new OpportunityJson.Obj(Map.of()),ref("driver",value.driver().bytes()));
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,DriverObservationEvidenceReader.replayOriginals(ref("v1",v1.bytes()),v1,value.driver(),value.actual().originalPacket(),value.nativeRef()));
        var oldFacts=new DriverObservationFacts(value.known().driver(),3,7,value.actual().session(),value.actual().snapshotId(),value.actual().nativeRevision(),
                DriverJson.sha256(value.actual().state().bytes()),BigInteger.valueOf(2),3,source(),new OpportunityJson.Obj(Map.of()),value.manifestRef());
        assertEquals(ObservationMode.RICH,oldFacts.armyObservationMode());assertTrue(oldFacts.identityOnly126Source().isEmpty());
    }
}
