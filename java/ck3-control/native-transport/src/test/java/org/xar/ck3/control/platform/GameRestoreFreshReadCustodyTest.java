package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.semantic.NativePlayerEventTraitMembership;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePacketPort;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeTransportReplayTestFactory;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Real sole transport receiver feeds the production restore READ state through a software packet boundary. */
final class GameRestoreFreshReadCustodyTest {
    private static final String SHA=NativePlayerEventTraitMembership.EXECUTABLE_SHA256;
    private static final String ADAPTER="ck3-1.20.0.4-msvc-x64";
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static final class Packets implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes,reads;long revision=6;String requestId;boolean respond=true,omitSnapshot,reject;
        Packets(boolean capability)throws IOException {
            var hello=StrictJson.object();hello.put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
                    .put("bridge_version","restore-read-test").put("expected_ck3_sha256",SHA).put("expected_ck3_version",NativePlayerEventTraitMembership.GAME_VERSION)
                    .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot");if(capability)((com.fasterxml.jackson.databind.node.ArrayNode)hello.get("capabilities")).add(NativeFreshSnapshotPort.CAPABILITY);
            add(hello);snapshot("cached",null);
        }
        void add(ObjectNode value)throws IOException {packets.add(NativeWire.packet(StrictJson.canonical(value)));}
        void snapshot(String id,String read)throws IOException {
            var row=StrictJson.object();row.put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",id).put("revision",revision);
            var state=row.putObject("state");state.put("date_raw",53144328).put("speed",3).put("paused",true).put("map_ready",true);
            state.putObject("played_character").put("character_id",73).put("alive",true);
            var membership=state.withObject("/played_character").putObject("event_trait_membership");
            membership.put("schema",NativePlayerEventTraitMembership.SCHEMA).put("game_version",NativePlayerEventTraitMembership.GAME_VERSION)
                    .put("executable_sha256",NativePlayerEventTraitMembership.EXECUTABLE_SHA256).put("status","available")
                    .put("snapshot_revision",revision).put("date_raw",53144328).put("played_character_id",73).putNull("unavailable_reason");
            membership.putObject("traits").put("lifestyle_poet",false).put("journaller",false);
            state.putNull("active_event");state.putNull("pending_character_interaction");state.putNull("one_life_terminal_reason");state.putNull("one_life_settlement");
            for(var resource:NativePlayedResources.Resource.values())
                state.set(resource.wire(),NativePlayedResources.encode(new NativePlayedResources.Amount(0)));
            state.putArray("history");state.putArray("active_wars");state.putArray("player_armies");state.putObject("diagnostics");
            if(read!=null)row.put("read_request_id",read);add(row);
        }
        void finishOriginal()throws IOException {
            if(!reject)revision++; // Actual fresh producer creates a new publication even for an unchanged state DTO.
            String id="read:"+requestId;if(!omitSnapshot&&!reject)snapshot(id,requestId);
            var ack=StrictJson.object();ack.put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",!reject);
            if(reject)ack.put("error","original explicit native refusal");
            else ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",requestId).put("snapshot_id",id).put("revision",revision);add(ack);
        }
        public void verify(){}public void awaitConnection(Instant until){}public void close(){}
        public byte[] readPacket(Instant until)throws IOException {reads++;if(packets.isEmpty())throw new IOException("software read unavailable");return packets.remove();}
        public void writePacket(byte[] bytes,Instant until)throws IOException {
            writes++;var row=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(bytes,4,bytes.length)));
            assertEquals(NativeFreshSnapshotPort.STEP,row.get("step").textValue());requestId=row.get("request_id").textValue();if(respond)finishOriginal();
        }
    }
    private static NativeGameTransport transport(Packets packets)throws IOException {
        String slash=Character.toString(92);var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"restore-fresh-source-test",
                "source-test-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"actual-held-session","restore-read-test",SHA,ADAPTER);
        return NativeTransportReplayTestFactory.create(packets,config,16,64);
    }
    @Test void productionReadStateKeepsOriginalUntilArchiveAndRequiresTwoActualRequests()throws Exception {
        var packets=new Packets(true);try(var port=transport(packets)) {
            var cached=port.observe(deadline());var state=new GameRestoreNativeAdapter.FreshReadCustody();
            var first=state.read(port,deadline(),unavailable->{throw new AssertionError(unavailable.reason());});
            assertNotEquals(cached.snapshotId(),first.originalFrame().snapshotId());assertNotEquals(cached.state(),first.originalFrame().state());
            assertTrue(RestoreCheckpointService.sameStableReadState(cached,first.originalFrame()));
            // Simulate failed archive after Received: production must return this identical original without another write.
            assertSame(first,state.read(port,deadline(),unavailable->{throw new AssertionError();}));assertEquals(1,packets.writes);
            state.archived(first);var second=state.read(port,deadline(),unavailable->{throw new AssertionError();});
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);assertNotEquals(first.acknowledgement().requestId(),second.acknowledgement().requestId());
            assertEquals(BigInteger.valueOf(7),first.originalFrame().nativeRevision());assertEquals(BigInteger.valueOf(8),second.originalFrame().nativeRevision());
            RestoreCheckpointService.requireStableReadProgression(first.originalFrame(),second.originalFrame());
            assertEquals(2,packets.writes);assertThrows(IOException.class,()->state.archived(first));
            state.archived(second);
        }
    }
    @Test void actualIncreasingReadPublicationsStillRejectCachedReversedAndChangedRawState()throws Exception {
        var packets=new Packets(true);try(var port=transport(packets)) {
            port.observe(deadline());var state=new GameRestoreNativeAdapter.FreshReadCustody();
            var first=state.read(port,deadline(),unavailable->{throw new AssertionError();});state.archived(first);
            var second=state.read(port,deadline(),unavailable->{throw new AssertionError();});state.archived(second);
            var left=first.originalFrame();var right=second.originalFrame();
            RestoreCheckpointService.requireStableReadProgression(left,right);
            assertThrows(IllegalArgumentException.class,()->RestoreCheckpointService.requireStableReadProgression(left,left));
            assertThrows(IllegalArgumentException.class,()->RestoreCheckpointService.requireStableReadProgression(right,left));
            var changed=(ObjectNode)StrictJson.parse(right.state().bytes());changed.put("date_raw",53144352);
            var later=new NativeObservationPort.ObservedFrame(right.session(),right.snapshotId(),right.nativeRevision(),
                    new RawJson(StrictJson.canonical(changed)),right.originalPacket(),right.observedAt());
            assertThrows(IllegalArgumentException.class,()->RestoreCheckpointService.requireStableReadProgression(left,later));
            var bad=(ObjectNode)FullJsonTree.parse(right.state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            ((ObjectNode)bad.path("played_character").path("event_trait_membership")).put("snapshot_revision",left.nativeRevision());
            var wrongNested=copyState(right,bad);
            assertThrows(IllegalArgumentException.class,()->RestoreCheckpointService.requireStableReadProgression(left,wrongNested));
            var badType=bad.deepCopy();((ObjectNode)badType.path("played_character").path("event_trait_membership")).put("snapshot_revision",true);
            assertThrows(IllegalArgumentException.class,()->RestoreCheckpointService.sameStableReadState(left,copyState(right,badType)));
            var missing=bad.deepCopy();((ObjectNode)missing.path("played_character").path("event_trait_membership")).remove("date_raw");
            assertThrows(IllegalArgumentException.class,()->RestoreCheckpointService.sameStableReadState(left,copyState(right,missing)));
            var changedTrait=(ObjectNode)FullJsonTree.parse(right.state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            ((ObjectNode)changedTrait.path("played_character").path("event_trait_membership").path("traits")).put("journaller",true);
            assertFalse(RestoreCheckpointService.sameStableReadState(left,copyState(right,changedTrait)));
            var decimalLeft=(ObjectNode)FullJsonTree.parse(left.state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            var decimalRight=(ObjectNode)FullJsonTree.parse(right.state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            decimalLeft.set("original_decimal",new DecimalTokenNode("1.0"));decimalRight.set("original_decimal",new DecimalTokenNode("1.00"));
            assertFalse(RestoreCheckpointService.sameStableReadState(copyState(left,decimalLeft),copyState(right,decimalRight)));
            assertEquals(2,packets.writes);
        }
    }
    private static NativeObservationPort.ObservedFrame copyState(NativeObservationPort.ObservedFrame original,ObjectNode state) {
        return new NativeObservationPort.ObservedFrame(original.session(),original.snapshotId(),original.nativeRevision(),
                new RawJson(FullJsonTree.encode(state,org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES)),original.originalPacket(),original.observedAt());
    }
    @Test void unknownCollectsOnlyOriginalRequestEvenIfEvidenceRetentionInitiallyFails()throws Exception {
        var packets=new Packets(true);packets.respond=false;try(var port=transport(packets)) {
            port.observe(deadline());var state=new GameRestoreNativeAdapter.FreshReadCustody();var originals=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            assertThrows(IOException.class,()->state.read(port,deadline(),unavailable->{originals.add(unavailable);throw new IOException("original evidence write unavailable");}));
            String id=packets.requestId;assertInstanceOf(NativeActionPort.Unknown.class,originals.getFirst().dispatch());
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));assertEquals(1,packets.writes);assertEquals(id,packets.requestId);
            packets.finishOriginal();var received=state.read(port,deadline(),originals::add);
            assertEquals(id,received.acknowledgement().requestId());assertEquals(1,packets.writes);state.archived(received);
            packets.respond=true;var later=state.read(port,deadline(),originals::add);NativeFreshSnapshotPort.verifyAfter(received.acknowledgement(),later);assertEquals(2,packets.writes);
        }
    }
    @Test void missingFreshCapabilityKeepsZeroDispatchAndNeverFallsBackToCachedObservation()throws Exception {
        var packets=new Packets(false);try(var port=transport(packets)) {
            port.observe(deadline());var state=new GameRestoreNativeAdapter.FreshReadCustody();var originals=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));
            assertEquals(2,originals.size());assertSame(originals.getFirst(),originals.getLast());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,originals.getFirst().dispatch());assertEquals(0,packets.writes);
        }
    }
    @Test void positiveAckWithoutItsEarlierMatchingSnapshotRemainsOriginalUnavailability()throws Exception {
        var packets=new Packets(true);packets.omitSnapshot=true;try(var port=transport(packets)) {
            var cached=port.observe(deadline());var state=new GameRestoreNativeAdapter.FreshReadCustody();var originals=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,originals.getFirst().dispatch());assertTrue(ack.nativeOk());assertTrue(originals.getFirst().originalFrame().isEmpty());
            int reads=packets.reads;packets.snapshot("read:"+packets.requestId,packets.requestId);
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));
            assertSame(ack,originals.getLast().dispatch());assertEquals(1,packets.writes);assertEquals(reads,packets.reads);assertEquals(1,packets.packets.size());
            assertArrayEquals(cached.originalPacket(),port.currentSnapshot(deadline()).originalPacket());
        }
    }
    @Test void negativeAckIsRetainedAsTerminalAndNeverBecomesAnotherReadRequest()throws Exception {
        var packets=new Packets(true);packets.reject=true;try(var port=transport(packets)) {
            port.observe(deadline());var state=new GameRestoreNativeAdapter.FreshReadCustody();var originals=new ArrayList<NativeFreshSnapshotPort.Unavailable>();
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,originals.getFirst().dispatch());assertFalse(ack.nativeOk());int reads=packets.reads;
            assertThrows(IOException.class,()->state.read(port,deadline(),originals::add));
            assertSame(originals.getFirst(),originals.getLast());assertEquals(1,packets.writes);assertEquals(reads,packets.reads);
        }
    }
}
