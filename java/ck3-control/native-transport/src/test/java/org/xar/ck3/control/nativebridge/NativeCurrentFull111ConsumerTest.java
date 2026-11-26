package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.FullSnapshotDateSentinelArm;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePlayedCharacter;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Synthetic DATA and software endpoint regressions only. No C++111 producer, actual DLL,
 * live Game, complete Driver, physical SAVE, effect or source qualification is asserted. */
final class NativeCurrentFull111ConsumerTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final ExactCk3Build CORE=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final BigInteger REVISION=new BigInteger("18446744073709551615");
    private static final CoreFrame.Prefix PREFIX=new CoreFrame.Prefix(53179368,3,true,-2147483647,true,true,-2147483647,true);
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final Instant DATA_DEADLINE=Instant.parse("2030-01-02T03:04:05.123456789Z");
    private static final String ARM="research-arm-tactical-daily-sentinel-v1-53179368-to-53179392-speed-3-mode-terminal-a-0";

    @Test void full111RequiresItsIndependentTupleWithoutExpandingLegacySelection() {
        assertTrue(FULL.matches(CORE.version(),CORE.executableSha256()));
        assertNotEquals(FULL,CORE);
        assertNotEquals(FULL.coreFullAdapterId(),CORE.coreFrameAdapterId());
        assertTrue(ExactCk3Build.florinCoreFullBuild(FULL.version(),FULL.executableSha256()).isEmpty());
        assertEquals(Optional.of(CORE),ExactCk3Build.florinCoreFrameBuild(CORE.version(),CORE.executableSha256()));
        assertEquals(Optional.of(FULL),ExactCk3Build.florinCoreFullBuild(FULL.version(),FULL.executableSha256(),FULL.coreFullAdapterId()));
        assertTrue(ExactCk3Build.florinCoreFullBuild(CORE.version(),CORE.executableSha256(),CORE.coreFrameAdapterId()).isEmpty());
        assertTrue(ExactCk3Build.florinCoreFullBuild("1.21.0",FULL.executableSha256(),FULL.coreFullAdapterId()).isEmpty());
        assertTrue(ExactCk3Build.florinCoreFullBuild(FULL.version(),ExactCk3Build.CK3_1210.executableSha256(),FULL.coreFullAdapterId()).isEmpty());
        assertTrue(ExactCk3Build.florinCoreFullBuild(FULL.version(),FULL.executableSha256(),FULL.coreFullAdapterId()+"-unknown").isEmpty());
        assertThrows(IllegalStateException.class,CORE::coreFullAdapterId);
        assertThrows(IllegalStateException.class,CORE::coreFullBackend);
        assertEquals(Optional.of(ExactCk3Build.CK3_1210),ExactCk3Build.florinCoreFullBuild("1.21.0",ExactCk3Build.CK3_1210.executableSha256()));
    }

    @Test void bothCoreProfilesNormalizeWithoutChangingAdapterOrCompleteness() throws Exception {
        for(var build:List.of(CORE,FULL,ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            for(CoreFrame data:List.of(new CoreFrame.Partial(build,PREFIX),new CoreFrame.Unavailable(build,false,"software not loaded"))) {
                RawJson encoded=CoreFramePublicCodec.encode(data);
                assertEquals(data,CoreFrame.decode(encoded));
                var tree=object(encoded);
                assertEquals(build.coreFrameAdapterId(),tree.path("adapter_id").textValue());
                assertEquals("ck3-"+build.version()+"-native-headless-main-thread",tree.path("backend").textValue());
                assertFalse(tree.path("complete_snapshot").booleanValue());
                assertEquals(CoreFrame.EXCLUDED.size(),tree.path("excluded_snapshot_families").size());
            }
        }
    }

    @Test void coreRejectsUnknownTupleAndAnyCompleteClaim() throws Exception {
        var base=object(CoreFramePublicCodec.encode(new CoreFrame.Partial(FULL,PREFIX)));
        var complete=base.deepCopy().put("complete_snapshot",true);
        assertThrows(IllegalArgumentException.class,()->CoreFrame.decodeObject(complete));
        for(String field:List.of("adapter_id","backend","game_version","executable_sha256")) {
            var changed=base.deepCopy().put(field,"unqualified-software-data");
            assertThrows(IllegalArgumentException.class,()->CoreFrame.decodeObject(changed));
        }
        var coreOnly=base.deepCopy().put("adapter_id",CORE.coreFrameAdapterId());
        assertEquals(CORE,CoreFrame.decodeObject(coreOnly).build());
        assertFalse(object(CoreFramePublicCodec.encode(CoreFrame.decodeObject(coreOnly))).path("complete_snapshot").booleanValue());
    }

    @Test void explicitFullClockAndDateClaimsUse111AndPreserveRevisionDeadline() throws Exception {
        for(String step:List.of("pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5")) {
            var request=FullSnapshotClockControl.request(FULL,step,"native:"+REVISION,REVISION,DATA_DEADLINE);
            assertEquals(step,request.step());assertEquals(Optional.of("game.command."+step),request.requiredCapability());
            var fields=object(request.additionalFields());assertEquals(1,fields.size());
            var claim=(ObjectNode)fields.get("full_snapshot_clock_control");assertEquals(8,claim.size());
            tuple(claim,FullSnapshotClockControl.SCHEMA);
            assertEquals("native:"+REVISION,claim.path("snapshot_id").textValue());
            assertTrue(claim.path("native_revision").isIntegralNumber());assertEquals(REVISION,claim.path("native_revision").bigIntegerValue());
            assertEquals(DATA_DEADLINE.toEpochMilli(),claim.path("deadline_unix_ms").longValue());
        }
        var arm=FullSnapshotDateSentinelArm.request(FULL,ARM,"native:"+REVISION,REVISION,DATA_DEADLINE);
        var claim=(ObjectNode)object(arm.additionalFields()).get("date_sentinel_arm");
        assertEquals(8,claim.size());tuple(claim,FullSnapshotDateSentinelArm.SCHEMA);
        assertEquals(DATA_DEADLINE.toEpochMilli(),claim.path("deadline_unix_ms").longValue());
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(FULL,"pause-map","native:1",REVISION,DATA_DEADLINE));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(FULL,"pause-map","native:0",BigInteger.ZERO,DATA_DEADLINE));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(FULL,"pause-map","native:1",BigInteger.ONE,Instant.EPOCH));
    }

    @Test void sourceOnlyAndCoreOnlyCannotPrepareSaveOrPartialClock() {
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(FULL,"save-checkpoint","native:1",BigInteger.ONE,DATA_DEADLINE));
        for(var build:List.of(CORE,FULL)) {
            var partial=new CoreFrame.Partial(build,PREFIX);
            for(var step:CoreClockControl.Step.values())
                assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(step,partial));
        }
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(CORE,"pause-map","native:1",BigInteger.ONE,DATA_DEADLINE));
        assertThrows(IllegalArgumentException.class,()->FullSnapshotDateSentinelArm.request(CORE,ARM,"native:1",BigInteger.ONE,DATA_DEADLINE));
        assertFalse(FullSnapshotClockControl.isMappedSave61Bridge(null));
        assertEquals("save-checkpoint",FullSnapshotClockControl.request(ExactCk3Build.CK3_1210,"save-checkpoint","native:1",BigInteger.ONE,DATA_DEADLINE).step());
    }

    @Test void fullActorAndRootKeepTupleAndEmptyDomainRequirements() {
        var actor=identity(NativePlayedCharacter.FLORIN_SCHEMA).put("character_id",-2147483647).put("alive",true);
        var normalized=NativePlayedCharacter.normalizeFlorin(actor,BigInteger.ONE,com.fasterxml.jackson.databind.node.IntNode.valueOf(PREFIX.dateRaw()));
        assertEquals(-2147483647,normalized.path("character_id").intValue());
        assertEquals(FULL.coreFullAdapterId(),normalized.path("adapter_id").textValue());
        assertEquals(FULL.coreFullBackend(),normalized.path("backend").textValue());
        var root=identity(NativeSemanticNormalizer.FLORIN_SCHEMA).put("date_raw",PREFIX.dateRaw());
        root.set("played_character",actor);root.putNull("active_event");root.putArray("active_wars");root.putArray("player_armies");
        assertEquals(FULL.coreFullAdapterId(),NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(root),"native:1",BigInteger.ONE)
                .semantic().path("played_character").path("adapter_id").textValue());
        for(String field:List.of("active_wars","player_armies")) {
            var changed=root.deepCopy();changed.withArray(field).addObject().put("unqualified",true);
            assertThrows(IllegalArgumentException.class,()->NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(changed),"native:1",BigInteger.ONE));
        }
        var event=root.deepCopy();event.putObject("active_event").put("unqualified",true);
        assertThrows(IllegalArgumentException.class,()->NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(event),"native:1",BigInteger.ONE));
        var absent=root.deepCopy();absent.remove("active_wars");
        assertThrows(IllegalArgumentException.class,()->NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(absent),"native:1",BigInteger.ONE));
        var mismatch=root.deepCopy();((ObjectNode)mismatch.path("played_character")).put("adapter_id",CORE.coreFrameAdapterId());
        assertThrows(IllegalArgumentException.class,()->NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(mismatch),"native:1",BigInteger.ONE));
        var oldBackend=actor.deepCopy().put("backend",NativePlayedCharacter.FLORIN_BACKEND);
        assertThrows(IllegalArgumentException.class,()->NativePlayedCharacter.normalizeFlorin(oldBackend,BigInteger.ONE,root.path("date_raw")));
    }

    @Test void sourceOnlyFull111ReceiverRefusesFullBeforeAnyQueryOrToken() throws Exception {
        for(var build:List.of(FULL,CORE))try(var fixture=new Fixture(build)) {
            var fresh=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,fixture.actual.readFreshFullState(fixture.deadline));
            zero(fresh.dispatch());
            var full=assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,fixture.actual.readFullClockFrameReceived(fixture.deadline));
            zero(assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,full.original()).dispatch());
            if(build==FULL)assertTrue(full.reason().contains("corrected112 independent actual Managed source is not bound or current"),full::reason);
            assertTrue(fixture.actual.latestAcceptedSnapshotRevision().isEmpty());assertEquals(0,fixture.source.writes);
        }
    }

    @Test void actualSoftwareCoreReceiptRetains111IdentityButCannotMintClockOrFull() throws Exception {
        try(var fixture=new Fixture(FULL)) {
            var received=assertInstanceOf(NativeGameTransport.CoreReceived.class,fixture.actual.readCoreFrameReceived(fixture.deadline));
            assertEquals(FULL,received.frame().build());received.requireOriginal(fixture.actual,fixture.deadline);
            assertEquals(FULL.coreFullAdapterId(),object(CoreFramePublicCodec.encode(received.frame())).path("adapter_id").textValue());
            Object role=received;assertFalse(role instanceof NativeGameTransport.FullClockReceived);
            zero(fixture.actual.submitCoreClockControl(received,CoreClockControl.Step.SET_SPEED_3,fixture.deadline));
            zero(fixture.actual.submitFullClockControl(null,
                    FullSnapshotClockControl.request(FULL,"pause-map","native:1",BigInteger.ONE,fixture.deadline),fixture.deadline));
            assertEquals(1,fixture.source.writes);assertTrue(fixture.actual.latestAcceptedSnapshotRevision().isEmpty());
        }
    }

    @Test void heldStatusReadsAfterItsExactCoreWithoutFullOrArm() throws Exception {
        try(var fixture=new Fixture(FULL,true);var other=new Fixture(FULL,true)) {
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,fixture.actual.readCoreFrameReceived(fixture.deadline));
            zero(other.actual.readHeldDateSentinelStatus(core,other.deadline));
            assertEquals(0,other.source.writes);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,fixture.actual.readHeldDateSentinelStatus(core,fixture.deadline));
            var status=ClockStatusRead.decode(ack);
            assertEquals("2",status.generation().decimal());
            assertEquals("FAILED",status.state().name());
            assertEquals(53180088,status.targetDateRaw());
            var before=core.original().custody().orElseThrow();
            var after=ack.custody().orElseThrow();
            assertEquals(before.session(),after.session());
            assertEquals(before.custodyEpoch(),after.custodyEpoch());
            assertTrue(after.writeEntered().order().compareTo(before.responseReceived().order())>0);
            assertEquals(2,fixture.source.writes);
            assertTrue(fixture.actual.latestAcceptedSnapshotRevision().isEmpty());
        }
    }

    @Test void heldStatusKeepsRejectionAndRequiresTheAdvertisedExactBuild() throws Exception {
        try(var fixture=new Fixture(FULL,true)) {
            fixture.source.statusNativeOk=false;
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,fixture.actual.readCoreFrameReceived(fixture.deadline));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,fixture.actual.readHeldDateSentinelStatus(core,fixture.deadline));
            assertFalse(ack.nativeOk());
            assertTrue(ack.custody().isPresent());
            assertEquals(2,fixture.source.writes);
        }
        try(var missing=new Fixture(FULL);var coreOnly=new Fixture(CORE,true)) {
            for(var fixture:List.of(missing,coreOnly)) {
                var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,fixture.actual.readCoreFrameReceived(fixture.deadline));
                zero(fixture.actual.readHeldDateSentinelStatus(core,fixture.deadline));
                assertEquals(1,fixture.source.writes);
            }
        }
    }

    private static ObjectNode identity(String schema) {
        return StrictJson.object().put("schema",schema).put("game_version",FULL.version()).put("executable_sha256",FULL.executableSha256())
                .put("adapter_id",FULL.coreFullAdapterId()).put("backend",FULL.coreFullBackend());
    }
    private static void tuple(ObjectNode claim,String schema) {
        assertEquals(schema,claim.path("schema").textValue());assertEquals(FULL.version(),claim.path("game_version").textValue());
        assertEquals(FULL.executableSha256().toUpperCase(java.util.Locale.ROOT),claim.path("executable_sha256").textValue());
        assertEquals(FULL.coreFullAdapterId(),claim.path("adapter_id").textValue());assertEquals(FULL.coreFullBackend(),claim.path("backend").textValue());
    }
    private static ObjectNode object(RawJson raw)throws IOException{return NativeWire.object(NativeWire.parse(raw.bytes()));}
    private static void zero(NativeActionPort.DispatchOutcome outcome) {
        var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,outcome);
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());assertEquals(0,rejected.proof().requestBytesWritten());
    }
    private static final class Fixture implements AutoCloseable {
        final Instant deadline=Instant.now().plusSeconds(120);final Replay source;final NativeGameTransport actual;
        Fixture(ExactCk3Build build)throws Exception {this(build,false);}
        Fixture(ExactCk3Build build,boolean statusAdvertised)throws Exception {
            source=new Replay(build,statusAdvertised);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"current111-software","current111-software",GAME,
                    "current111-software-session","current111-software",build.executableSha256(),build.coreFrameAdapterId());
            actual=new NativeGameTransport(source,config,16,16,List.of(),Clock.systemUTC());
        }
        @Override public void close()throws IOException{actual.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final ExactCk3Build build;int writes;boolean closed;
        final boolean statusAdvertised;
        boolean statusNativeOk=true;
        Replay(ExactCk3Build build,boolean statusAdvertised)throws IOException {
            this.build=build;
            this.statusAdvertised=statusAdvertised;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                    .put("bridge_version","current111-software").put("expected_ck3_version",build.version()).put("expected_ck3_sha256",build.executableSha256())
                    .put("game_adapter_id",build.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(CoreFrame.CAPABILITY).add(NativeFreshSnapshotPort.CAPABILITY).add("game.state.snapshot")
                    .add("game.command.set-speed-3").add("game.command.pause-map").add("game.command.save-checkpoint");
            if(statusAdvertised)hello.withArray("capabilities").add(ClockStatusRead.STATUS_CAP).add("game.guard.date-only-postday.v1");
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify()throws IOException{if(closed)throw new IOException("software endpoint closed");}
        @Override public void awaitConnection(Instant deadline)throws IOException{verify();}
        @Override public byte[] readPacket(Instant deadline)throws IOException{verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();}
        @Override public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);writes++;
            assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
            assertTrue(NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).isEmpty());
            var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId());
            if(request.step().equals(ClockStatusRead.STEP)) {
                assertTrue(statusAdvertised);
                ack.put("ok",statusNativeOk);
                var result=ack.putObject("result").put("step",ClockStatusRead.STEP).put("accepted",statusNativeOk);
                if(statusNativeOk) {
                    result.put("status","available");
                    var status=result.putObject("tactical_daily_sentinel").put("state","failed").put("generation",2)
                            .put("starting_date_raw",53179368).put("target_date_raw",53180088).put("last_observed_date_raw",53179944)
                            .put("trigger_date_raw",53179944).put("speed",5).put("mode","terminal_or_sentinel")
                            .put("army_count",0).put("combat_count",0).put("completed_daily_ticks",24).put("intermediate_pause_count",0)
                            .put("trigger_flags",32768).put("signed_date_delta_from_target_raw",-144).put("overshoot_days",-1)
                            .put("pause_wrapper_called",true).put("pause_observed",true).put("terminal_observed",false).put("abnormal",true);
                    status.putArray("trigger_reasons").add("evaluation_failure");
                } else result.put("error","date-only sentinel unavailable");
            } else {
                assertEquals(CoreFrame.STEP,request.step(),"unqualified Full111 must not enter a full-state or control write");
                ack.put("ok",true).set("result",object(CoreFramePublicCodec.encode(new CoreFrame.Partial(build,PREFIX))));
            }
            packets.add(NativeWire.packet(StrictJson.canonical(ack)));
        }
        @Override public void close(){closed=true;}
    }
}
