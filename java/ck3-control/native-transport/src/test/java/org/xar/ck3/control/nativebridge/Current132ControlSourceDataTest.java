package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeFull111OrdinaryEvent;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Portable DATA/software-port regression. No Native call, Managed owner, private Full receipt,
 * source binding, physical SAVE or control success is fabricated. The one local artifact test
 * is explicit opt-in and only hashes/observes a file; it never loads it or inspects a process.
 */
final class Current132ControlSourceDataTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final ExactRef SOURCE132=new ExactRef("pure-data/current132-not-a-loaded-module",12389888L,
            "50b1b12bae59d5eb70b97978b86aabbb93a675e6e327bbcaa9a37aa5285cdb46");
    private static final ExactRef SOURCE131=new ExactRef("pure-data/current131",12389376L,
            "060a22216f6d7642ce2ee392dc7ffffbd17f1bb8d2029cd79eb17e47599b23f4");
    private static final ExactRef SOURCE125=new ExactRef("pure-data/current125",12389376L,
            "863b4893611d1101e4f5e7f82b43f4fab2c7259bd0db6c0065a59a9a016c12f7");
    private static final ExactRef SOURCE112=new ExactRef("pure-data/corrected112",12381696L,
            "2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6");
    private static final ExactRef SOURCE126=new ExactRef("pure-data/readonly126",12395520L,
            "30c21218df7b9ca567b30f5a02fe31731c790db1397e0ecc45b89aa502e617ea");
    private static final String SESSION="current132-software-session";
    private static final String MACHINE="current132-software-machine";
    private static GameGeneration game(){return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));}

    @Test void exact132AndOldControlPairsStayIndependentFromReadonlyAndWithdrawnSources(){
        for(var source:List.of(SOURCE132,SOURCE131,SOURCE125,SOURCE112))
            assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(source),source::toString);
        for(var bad:List.of(
                new ExactRef("wrong-size",SOURCE132.bytes()-1,SOURCE132.sha256()),
                new ExactRef("wrong-sha",SOURCE132.bytes(),"0".repeat(64)),
                new ExactRef("crossed132size131sha",SOURCE132.bytes(),SOURCE131.sha256()),
                new ExactRef("crossed131size132sha",SOURCE131.bytes(),SOURCE132.sha256()),
                SOURCE126,
                new ExactRef("withdrawn111",13792256L,"803da0130362c58bf8ba98c9e8bd41c3046c7dba4b12a0fa2fbbb29c6073eaa0"),
                new ExactRef("independent114-not-mapped112",12382720L,"42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a")))
            assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(bad),bad::toString);
        assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(null));
    }

    @Test void mapped132SaveBindsOriginalTuplePositiveRevisionAndFiniteCallerDeadline(){
        var revision=new BigInteger("9007199254740993");
        var deadline=Instant.parse("2030-01-02T03:04:05.123456789Z");
        var snapshot="native:"+revision;
        var prepared=FullSnapshotClockControl.requestMappedSave112(SOURCE132,snapshot,revision,deadline);
        var fields=StrictJson.parse(prepared.additionalFields().bytes(),1<<20).path("full_snapshot_clock_control");
        assertEquals("save-checkpoint",prepared.step());
        assertEquals("game.command.save-checkpoint",prepared.requiredCapability().orElseThrow());
        assertEquals(FULL.version(),fields.path("game_version").textValue());
        assertEquals(FULL.executableSha256().toUpperCase(java.util.Locale.ROOT),fields.path("executable_sha256").textValue());
        assertEquals(FULL.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(FULL.coreFullBackend(),fields.path("backend").textValue());
        assertEquals(snapshot,fields.path("snapshot_id").textValue());
        assertEquals(revision,fields.path("native_revision").bigIntegerValue());
        assertEquals(deadline.toEpochMilli(),fields.path("deadline_unix_ms").longValue());
        var command=command(revision,deadline,FULL.executableSha256());
        assertArrayEquals(prepared.additionalFields().bytes(),
                FullSnapshotClockControl.additionalFieldsMappedSave112(command,SOURCE132).bytes());
        assertEquals(deadline,command.deadline(),"DATA encoding never refreshes or rounds the caller's original Instant");
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(FULL,"save-checkpoint",snapshot,revision,deadline));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(SOURCE126,snapshot,revision,deadline));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.additionalFieldsMappedSave112(
                command(revision,deadline,ExactCk3Build.CK3_1210.executableSha256()),SOURCE132));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(SOURCE132,"native:0",BigInteger.ZERO,deadline));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(SOURCE132,"native:9",revision,deadline));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(SOURCE132,"native:1",BigInteger.ONE,Instant.EPOCH));
    }

    @Test void exactHelloAndSourceDataCannotReplaceActualManagedCustody()throws Exception{
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE132));
        var source=new Replay(null);
        try(var actual=transport(source)){
            assertThrows(NullPointerException.class,()->actual.bindFull112Source(null));
            var read=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    actual.readFreshFullState(Instant.now().plusSeconds(30)));
            var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,read.dispatch());
            assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());
            assertEquals(0,rejected.proof().requestBytesWritten());
            assertTrue(read.reason().contains("actual Managed source is not bound"),read::reason);
            assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,
                    actual.readFullClockFrameReceived(Instant.now().plusSeconds(30)));
            var failure=assertThrows(IOException.class,()->actual.fullClockProfileForPreparation(
                    command(BigInteger.ONE,Instant.now().plusSeconds(30),FULL.executableSha256())));
            assertTrue(failure.getMessage().contains("actual Managed source is not bound"),failure::toString);
            assertEquals(0,source.writes);
            assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());
            // Positive owner/session/module-Witness binding is NOT_RUN: it requires an actual opaque Managed owner.
        }
    }

    @Test void actualReceivePathPreservesCurrentEmptyArmyWarAndExactEventGates()throws Exception{
        for(String field:List.of("active_event","active_wars","player_armies")){
            var state=emptyFull();
            final String expected;
            if(field.equals("active_event")){
                state.putObject(field).put("software_unqualified_event",true);
                expected="exact JSON fields required";
            }else{
                var row=state.putArray(field).addObject();
                if(field.equals("player_armies"))row.put("army_id",0).put("owner_character_id",73).put("controllable",true);
                else row.put("software_unqualified_war",true);
                expected="Full111 initial Full requires an explicit empty "+field;
            }
            byte[] original=snapshot(state);
            var source=new Replay(original);
            try(var actual=transport(source)){
                assertThrows(UncheckedIOException.class,()->actual.observe(Instant.now().plusSeconds(30)));
                assertTrue(actual.diagnostics().toString().contains(expected),()->field+": "+actual.diagnostics());
                assertArrayEquals(original,actual.diagnostics().lastOriginalPacket().value());
                assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());
                assertEquals(0,source.writes,"unsolicited software packet inspection cannot query or act");
            }
        }
    }

    @Test void fullOrdinaryEventSummaryRequiresBothAdvertisedCapabilityAndBoundSource()throws Exception{
        var state=emptyFull();
        state.putObject("active_event").put("schema",NativeFull111OrdinaryEvent.SCHEMA)
                .put("instance_id",42).put("authored_option_count",3);
        byte[] original=snapshot(state);
        for(boolean advertised:List.of(false,true)){
            var source=new Replay(original,advertised);
            try(var actual=transport(source)){
                assertThrows(UncheckedIOException.class,()->actual.observe(Instant.now().plusSeconds(30)));
                String expected=advertised?"actual Managed source is not bound":"requires its advertised Full capability";
                assertTrue(actual.diagnostics().toString().contains(expected),actual.diagnostics()::toString);
                assertArrayEquals(original,actual.diagnostics().lastOriginalPacket().value());
                assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());
                assertEquals(0,source.writes);
            }
        }
    }

    @Test void sameSpeedAdmissionNeverQualifiesChangedOrUnknownSpeedData()throws Exception{
        var before=new RawJson(StrictJson.canonical(StrictJson.object().put("speed",3)));
        assertDoesNotThrow(()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",before));
        assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-4",before));
        for(String bad:List.of("{\"speed\":0}","{\"speed\":6}","{\"speed\":3.0}","{\"speed\":\"3\"}","{\"speed\":null}","{}")){
            var invalid=new RawJson(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",invalid),bad);
        }
    }

    @Test @EnabledIfSystemProperty(named="xar.current132.dll",matches=".+")
    void optInActual132FileWitnessIsExactAndStableWithoutLoading()throws Exception{
        var path=Path.of(System.getProperty("xar.current132.dll"));
        assertTrue(path.isAbsolute(),"explicit local source path must be absolute");
        var measured=ControlBuild.FileRef.measure(path);
        var source=new ExactRef(measured.path(),measured.bytes(),measured.sha256());
        assertEquals(SOURCE132.bytes(),source.bytes());assertEquals(SOURCE132.sha256(),source.sha256());
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(source));
        var witness=SharedSourceFiles.observe(path);
        assertEquals(source.bytes(),witness.source().bytes());assertEquals(source.sha256(),witness.source().sha256());
        SharedSourceFiles.assertUnchanged(witness);
        // File identity and full-byte SHA are measured. Loaded module, actual Managed, Game and action authority remain unproved.
    }

    private static ActionCommand command(BigInteger revision,Instant deadline,String executableSha){
        var before=new ObservationIdentity(MACHINE,game(),
                new ProposalFrame(new Frame(BigInteger.valueOf(73),revision,BigInteger.valueOf(53179344)),
                        "native:"+revision,BigInteger.ONE,"software132-episode"),1);
        var source=new G2Source(MACHINE,"2030-01-02T03:00:00Z",executableSha,SOURCE132);
        return new ActionCommand("software132-save",before,source,SESSION,new OperationKey("save-checkpoint"),
                new OpportunityJson.Obj(Map.of()),
                new ExpectedPostcondition(1,before,source,"software132-no-observer-authority",
                        List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode emptyFull(){
        var root=tuple(StrictJson.object(),"ck3_1210_full_state_v1");
        root.put("paused",true).put("map_ready",true).put("speed",3).put("date_raw",53179344);
        tuple(root.putObject("played_character"),"ck3_1210_played_character_v1").put("character_id",73).put("alive",true);
        root.putNull("active_event");root.putArray("active_wars");root.putArray("player_armies");
        return root;
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode tuple(com.fasterxml.jackson.databind.node.ObjectNode row,String schema){
        return row.put("schema",schema).put("game_version",FULL.version()).put("executable_sha256",FULL.executableSha256())
                .put("adapter_id",FULL.coreFullAdapterId()).put("backend",FULL.coreFullBackend());
    }
    private static byte[] snapshot(com.fasterxml.jackson.databind.node.ObjectNode state)throws IOException{
        var envelope=StrictJson.object().put("protocol_version",1).put("type","state_snapshot").put("snapshot_id","native:1").put("revision",1);
        envelope.set("state",state);return NativeWire.packet(StrictJson.canonical(envelope));
    }
    private static NativeGameTransport transport(Replay source)throws IOException{
        String slash=Character.toString(92);
        var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"current132-software",MACHINE,game(),SESSION,
                "current132-software",FULL.executableSha256(),FULL.coreFullAdapterId());
        return new NativeGameTransport(source,config,16,16,List.of(),Clock.systemUTC());
    }
    private static final class Replay implements NativePacketPort{
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes;boolean closed;
        Replay(byte[] candidate)throws IOException{
            this(candidate,false);
        }
        Replay(byte[] candidate,boolean ordinaryEventFull)throws IOException{
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42)
                    .put("connection_generation",1).put("bridge_version","current132-software")
                    .put("expected_ck3_version",FULL.version()).put("expected_ck3_sha256",FULL.executableSha256())
                    .put("game_adapter_id",FULL.coreFullAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(NativeFreshSnapshotPort.CAPABILITY).add("game.state.snapshot")
                    .add("game.command.save-checkpoint").add("game.command.set-speed-3");
            if(ordinaryEventFull)hello.withArray("capabilities").add(NativeFull111OrdinaryEvent.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));if(candidate!=null)packets.add(candidate);
        }
        @Override public void verify()throws IOException{if(closed)throw new IOException("software endpoint closed");}
        @Override public void awaitConnection(Instant until)throws IOException{verify();}
        @Override public byte[] readPacket(Instant until)throws IOException{
            verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] packet,Instant until)throws IOException{
            writes++;throw new IOException("unbound software DATA must not write a query or command");
        }
        @Override public void close(){closed=true;}
    }
}
