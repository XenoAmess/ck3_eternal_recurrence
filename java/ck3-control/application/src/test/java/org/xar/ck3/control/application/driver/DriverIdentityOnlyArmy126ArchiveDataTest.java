package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
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
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies;
import org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies.ObservationMode;
import org.xar.ck3.control.contracts.semantic.NativePlayedCharacter;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * NOT_NATIVE_OBSERVATION / NOT_LIVE. Explicit software packets exercise the real Driver repository,
 * evidence encoder, strict framed-byte reader and archive replay. No DLL is opened or loaded;
 * source path/bytes/SHA are DATA references, not loaded-module, Game, owner, receipt or permission proof.
 */
final class DriverIdentityOnlyArmy126ArchiveDataTest {
    private static final JsonNodeFactory JSON=JsonNodeFactory.instance;
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final String SOURCE_SHA="30c21218df7b9ca567b30f5a02fe31731c790db1397e0ecc45b89aa502e617ea";
    private static final String ACTUAL_SOURCE_PATH="D:/ck3-state/ck3-migration-20261118-native/identity-build01/cmake-focused01/current-owned-army126/build-01/xar_ck3_bridge_current126.dll";
    private static final Instant NOW=Instant.parse("2026-11-21T00:00:00Z");
    private static final String WIRE= """
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
    private static ExactRef ref(String name,byte[] value){return new ExactRef("pure-data/"+name,value.length,DriverJson.sha256(value));}
    private static ExactRef sourceRef(){
        // Portable CI does not require this path to exist. This test never treats a path declaration as a file witness.
        return new ExactRef(System.getProperty("xar.army126.dll",ACTUAL_SOURCE_PATH),12_395_520L,SOURCE_SHA);
    }
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));}
    private static G2Source source(){return new G2Source("software-machine",NOW.toString(),BUILD.version()+"@"+BUILD.executableSha256(),ref("source",bytes("software source, no Native authority")));}
    private static DriverSnapshotFacts.Known known(){
        return DriverFactsRepository.imported(ref("driver-input",bytes(WIRE)),bytes(WIRE),3,7,game(),new OpportunityJson.Obj(Map.of()));
    }
    private static ObjectNode identity(ObjectNode row,String schema){
        row.put("schema",schema).put("game_version",BUILD.version()).put("executable_sha256",BUILD.executableSha256())
                .put("adapter_id",BUILD.coreFullAdapterId()).put("backend",BUILD.coreFullBackend());
        return row;
    }
    private static ObjectNode row(int unit,int owner){
        return JSON.objectNode().put("army_id",unit).put("owner_character_id",owner).put("controllable",true);
    }
    private static ObjectNode root(int actor,int... units){
        var root=identity(JSON.objectNode(),NativeSemanticNormalizer.FLORIN_SCHEMA);
        root.put("paused",true).put("map_ready",true).put("speed",3).put("date_raw",53179368);
        root.set("played_character",identity(JSON.objectNode().put("character_id",actor).put("alive",true),NativePlayedCharacter.FLORIN_SCHEMA));
        root.putNull("active_event");root.putArray("active_wars");root.putNull("pending_character_interaction");
        root.putNull("one_life_terminal_reason");
        root.putObject("diagnostics"); // Explicit empty software metadata, never a Native observation claim.
        var armies=root.putArray("player_armies");for(int unit:units)armies.add(row(unit,actor));
        return root;
    }
    private static NativeObservationPort.ObservedFrame frame(ObjectNode root){
        byte[] state=DriverJson.encode(DriverJson.fromNode(root));
        byte[] prefix=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"native:9\",\"revision\":9,\"state\":");
        byte[] packet=ByteBuffer.allocate(prefix.length+state.length+1).put(prefix).put(state).put((byte)'}').array();
        byte[] framed=ByteBuffer.allocate(packet.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(packet.length).put(packet).array();
        var session=new NativeObservationPort.TransportSession("software-machine",game(),BigInteger.valueOf(5),"software-only-session");
        return new NativeObservationPort.ObservedFrame(session,"native:9",BigInteger.valueOf(9),new RawJson(state),framed,NOW);
    }
    private record Bundle(DriverSnapshotFacts.Known known,NativeObservationPort.ObservedFrame actual,
            RawJson driver,RawJson manifest,ExactRef manifestRef,ExactRef nativeRef) { }
    private static Bundle bundle(){
        var actual=frame(root(73,Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE));
        var known=known();byte[] driver=known.driver().encode();
        var manifest=DriverObservationEvidenceReader.encodeIdentityOnly126(known,actual,BigInteger.valueOf(2),3,source(),
                new OpportunityJson.Obj(Map.of()),ref("driver",driver),sourceRef());
        return new Bundle(known,actual,new RawJson(driver),manifest,ref("manifest",manifest.bytes()),ref("native",actual.originalPacket()));
    }
    private static DriverObservationAssembler.Result replay(Bundle value,RawJson manifest,ExactRef expected){
        return DriverObservationEvidenceReader.replayIdentityOnly126Originals(ref("manifest",manifest.bytes()),manifest,
                value.driver(),value.actual().originalPacket(),value.nativeRef(),expected);
    }
    private static RawJson manifest(OpportunityJson.Obj row){return RawJson.fullMaterial(DriverJson.encode(row));}

    @Test void explicitIdentityModePreservesSignedIdsAndOnlyObservedFields(){
        var raw=root(Integer.MIN_VALUE,Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE);
        var normalized=FlorinPlayerArmies.normalize(raw,ObservationMode.IDENTITY_ONLY126);
        assertEquals(4,normalized.size());
        int[] ids={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE};
        for(int i=0;i<ids.length;i++){
            var observed=normalized.get(i);assertEquals(ids[i],observed.get("army_id").intValue());
            assertEquals(Integer.MIN_VALUE,observed.get("owner_character_id").intValue());
            assertTrue(observed.get("controllable").booleanValue());
            var names=new java.util.HashSet<String>();observed.fieldNames().forEachRemaining(names::add);
            assertEquals(java.util.Set.of("army_id","owner_character_id","controllable"),names);
        }
        var projected=DriverObservationAssembler.canonicalNativeState(frame(raw),ObservationMode.IDENTITY_ONLY126).semantic();
        assertEquals(DriverJson.fromNode(normalized),projected.get("player_armies"));
        assertFalse(normalized.get(0).has("soldiers"));assertFalse(normalized.get(0).has("route_province_ids"));
        assertFalse(normalized.get(0).has("in_combat"));assertFalse(normalized.get(0).has("army_state"));
    }

    @Test void richDefaultsCannotDowngradeAndEmptyRichKeepsItsExistingContract(){
        var raw=root(73,-2);
        assertThrows(IllegalArgumentException.class,()->FlorinPlayerArmies.normalize(raw));
        assertThrows(IllegalArgumentException.class,()->NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(raw),"native:9",BigInteger.valueOf(9)));
        assertThrows(IllegalArgumentException.class,()->DriverObservationAssembler.canonicalNativeState(frame(raw)));
        var empty=root(73);
        assertTrue(FlorinPlayerArmies.normalize(empty).isEmpty());
        assertDoesNotThrow(()->DriverObservationAssembler.canonicalNativeState(frame(empty)));
        var rich=NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(empty),"native:9",BigInteger.valueOf(9)).semantic();
        assertTrue(rich.get("player_armies").isEmpty());
        empty.set("active_event",JSON.objectNode().put("unobserved",true));
        assertThrows(IllegalArgumentException.class,()->DriverObservationAssembler.canonicalNativeState(frame(empty),ObservationMode.IDENTITY_ONLY126));
    }

    @Test void strictRowsRejectSentinelsAliasesWrongOwnerDuplicatesAndUnknownData(){
        for(JsonNode invalid:List.of(JSON.numberNode(-1),JSON.numberNode(new BigInteger("2147483648")),
                JSON.numberNode(new java.math.BigDecimal("1.0")),JSON.textNode("0"),JSON.booleanNode(true),JSON.nullNode())){
            var raw=root(73,0);((ObjectNode)raw.get("player_armies").get(0)).set("army_id",invalid);
            assertThrows(IllegalArgumentException.class,()->FlorinPlayerArmies.normalize(raw,ObservationMode.IDENTITY_ONLY126));
        }
        var duplicate=root(73,0,0);
        assertThrows(IllegalArgumentException.class,()->FlorinPlayerArmies.normalize(duplicate,ObservationMode.IDENTITY_ONLY126));
        for(String bad:List.of("owner","uncontrolled","extra","missing","null","absent","missing-actor","mixed-actor")){
            var raw=root(73,0);var first=(ObjectNode)raw.get("player_armies").get(0);
            switch(bad){
                case "owner"->first.put("owner_character_id",74);
                case "uncontrolled"->first.put("controllable",false);
                case "extra"->first.put("soldiers",0);
                case "missing"->first.remove("controllable");
                case "null"->raw.putNull("player_armies");
                case "absent"->raw.remove("player_armies");
                case "missing-actor"->raw.putNull("played_character");
                case "mixed-actor"->{
                    var actor=(ObjectNode)raw.get("played_character");var oldBuild=ExactCk3Build.CK3_1210;
                    actor.put("game_version",oldBuild.version()).put("executable_sha256",oldBuild.executableSha256())
                            .put("adapter_id",oldBuild.coreFullAdapterId()).put("backend",oldBuild.coreFullBackend());
                }
                default->throw new AssertionError();
            }
            assertThrows(IllegalArgumentException.class,()->FlorinPlayerArmies.normalize(raw,ObservationMode.IDENTITY_ONLY126),bad);
        }
    }

    @Test void realVersion2EncoderAndArchiveReplayPreserveTheSameDataAndMode(){
        var value=bundle();byte[] original=value.actual().originalPacket();
        var facts=DriverObservationEvidenceReader.decodeIdentityOnly126(value.manifestRef(),value.manifest(),value.driver(),value.actual(),sourceRef());
        assertEquals(ObservationMode.IDENTITY_ONLY126,facts.armyObservationMode());
        assertEquals(Optional.of(sourceRef()),facts.identityOnly126Source());
        var directResult=new DriverObservationAssembler().assemble(value.actual(),facts,value.nativeRef());
        var direct=assertInstanceOf(DriverObservationAssembler.Complete.class,directResult,directResult::toString);
        var replayResult=replay(value,value.manifest(),sourceRef());
        var restored=assertInstanceOf(DriverObservationAssembler.Complete.class,replayResult,replayResult::toString);
        assertEquals(direct,restored);
        assertEquals(value.nativeRef(),restored.originalEvidence());
        assertArrayEquals(original,value.actual().originalPacket());
        var armies=(OpportunityJson.Arr)restored.semantic().get("player_armies");
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE)),
                ((OpportunityJson.Obj)armies.items().getFirst()).get("army_id"));
        assertEquals(ref("driver",value.driver().bytes()),
                DriverObservationEvidenceReader.identityOnly126DriverReference(value.manifestRef(),value.manifest(),sourceRef()));
        assertEquals(sourceRef(),DriverObservationEvidenceReader.reference(
                DriverJson.object(value.manifest().bytes(),DriverJson.MAX_NATIVE_BYTES).get("identity_only126_source")));
        assertTrue(FlorinPlayerArmies.identityOnly126SourceMatches(sourceRef()));
    }

    @Test void archiveRejectsWrongExpectedSourceModePacketAndActualFrame(){
        var value=bundle();
        var wrong=new ExactRef(sourceRef().path()+".different",sourceRef().bytes(),sourceRef().sha256());
        assertThrows(IllegalArgumentException.class,()->replay(value,value.manifest(),wrong));
        assertThrows(IllegalArgumentException.class,()->replay(value,value.manifest(),new ExactRef(sourceRef().path(),1,SOURCE_SHA)));
        var row=DriverJson.object(value.manifest().bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertThrows(IllegalArgumentException.class,()->replay(value,manifest(row.with("army_observation_mode",new OpportunityJson.Text("RICH"))),sourceRef()));
        var missing=new java.util.LinkedHashMap<>(row.members());missing.remove("army_observation_mode");
        assertThrows(IllegalArgumentException.class,()->replay(value,manifest(new OpportunityJson.Obj(missing)),sourceRef()));
        byte[] changed=value.actual().originalPacket();changed[changed.length-2]^=1;
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.replayIdentityOnly126Originals(
                value.manifestRef(),value.manifest(),value.driver(),changed,value.nativeRef(),sourceRef()));
        var otherSession=new NativeObservationPort.TransportSession("software-machine",game(),BigInteger.valueOf(5),"other-session");
        var foreign=new NativeObservationPort.ObservedFrame(otherSession,value.actual().snapshotId(),value.actual().nativeRevision(),
                value.actual().state(),value.actual().originalPacket(),NOW);
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.decodeIdentityOnly126(
                value.manifestRef(),value.manifest(),value.driver(),foreign,sourceRef()));
    }

    @Test void version1AndHistoricalFactsNeverAcquireIdentityOnlyMode(){
        var value=bundle();
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.replayOriginals(
                value.manifestRef(),value.manifest(),value.driver(),value.actual().originalPacket(),value.nativeRef()));
        var old=DriverObservationEvidenceReader.encode(value.known(),value.actual(),BigInteger.valueOf(2),3,source(),
                new OpportunityJson.Obj(Map.of()),ref("driver",value.driver().bytes()));
        assertInstanceOf(DriverObservationAssembler.Incomplete.class,DriverObservationEvidenceReader.replayOriginals(
                ref("v1",old.bytes()),old,value.driver(),value.actual().originalPacket(),value.nativeRef()));
        var legacy=new DriverObservationFacts(value.known().driver(),3,7,value.actual().session(),value.actual().snapshotId(),
                value.actual().nativeRevision(),DriverJson.sha256(value.actual().state().bytes()),BigInteger.valueOf(2),3,source(),
                new OpportunityJson.Obj(Map.of()),value.manifestRef());
        assertEquals(ObservationMode.RICH,legacy.armyObservationMode());assertTrue(legacy.identityOnly126Source().isEmpty());
        assertThrows(IllegalArgumentException.class,()->new DriverObservationFacts(value.known().driver(),3,7,value.actual().session(),
                value.actual().snapshotId(),value.actual().nativeRevision(),DriverJson.sha256(value.actual().state().bytes()),
                BigInteger.valueOf(2),1,source(),new OpportunityJson.Obj(Map.of()),value.manifestRef(),
                ObservationMode.IDENTITY_ONLY126,Optional.of(sourceRef())));
    }
}
