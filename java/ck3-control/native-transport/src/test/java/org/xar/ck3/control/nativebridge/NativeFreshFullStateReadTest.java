package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequestChronologyCodec;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual sole Java receiver with a software packet boundary. These packets are DATA, not a C++/Game oracle.
 * The independently owned native producer regression and actual Root private-source chain remain mandatory. */
final class NativeFreshFullStateReadTest {
    private static final String SHA="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ADAPTER="ck3-1.19.0.6-msvc-x64";
    private static final String STATE="""
        {"date_raw":53144328,"speed":3,"paused":true,"map_ready":true,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,"one_life_settlement":null,
        "played_character_gold":0,"played_character_prestige":0,"played_character_piety":0,"history":[],
        "active_wars":[],"player_armies":[],"diagnostics":{}}
        """;
    @FunctionalInterface private interface Producer {void write(Replay actual,ObjectNode originalRequest)throws IOException;}
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();Producer producer;int reads,writes;ObjectNode request;
        byte[] snapshotPacket,ackPacket;boolean failWrite;
        Replay(Producer producer)throws IOException {this.producer=producer;add(hello());add(snapshot("old",5,null));}
        void add(ObjectNode row)throws IOException{packets.add(NativeWire.packet(StrictJson.canonical(row)));}
        @Override public void verify(){}
        @Override public void awaitConnection(Instant deadline){}
        @Override public byte[] readPacket(Instant deadline)throws IOException {reads++;if(packets.isEmpty())throw new IOException("software original read deadline/error");return packets.remove();}
        @Override public void writePacket(byte[] packet,Instant deadline)throws IOException {
            writes++;request=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(packet,4,packet.length)));
            var keys=new java.util.HashSet<String>();for(var field:request.properties())keys.add(field.getKey());
            assertEquals(Set.of("type","protocol_version","request_id","step","expected_revision"),keys);
            assertEquals("execute_step",request.get("type").textValue());assertEquals(NativeFreshSnapshotPort.STEP,request.get("step").textValue());
            assertEquals(BigInteger.ZERO,request.get("expected_revision").bigIntegerValue());
            if(failWrite)throw new IOException("actual write entered but return unavailable");producer.write(this,request);
        }
        @Override public void close(){}
        String id(){return request.get("request_id").textValue();}
        void fresh(ObjectNode frame,ObjectNode ack)throws IOException {
            snapshotPacket=NativeWire.packet(StrictJson.canonical(frame));ackPacket=NativeWire.packet(StrictJson.canonical(ack));
            packets.add(snapshotPacket);packets.add(ackPacket);
        }
    }
    private static ObjectNode object(String json)throws IOException{return NativeWire.object(NativeWire.parse(json.getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode hello()throws IOException {
        var row=object("{}");row.put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
            .put("bridge_version","source-test").put("expected_ck3_sha256",SHA).put("expected_ck3_version","1.19.0.6")
            .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);return row;
    }
    private static ObjectNode snapshot(String id,int revision,String requestId)throws IOException {
        var row=object("{}");row.put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",id).put("revision",revision).set("state",NativeWire.parse(STATE.getBytes(StandardCharsets.UTF_8)));
        if(requestId!=null)row.put("read_request_id",requestId);return row;
    }
    private static ObjectNode ack(String id,boolean ok)throws IOException {
        var row=object("{}");row.put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",ok);
        if(ok)row.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",id).put("snapshot_id","native:6").put("revision",6);
        else row.put("error","actual explicit native refusal");return row;
    }
    private static NativeGameTransport transport(Replay replay)throws IOException {
        return transport(replay,SHA,ADAPTER);
    }
    private static NativeGameTransport transport(Replay replay,String sha,String adapter)throws IOException {
        String slash=Character.toString(92);var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"fresh-full-state-source-test",
                "source-test-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"actual-held-session","source-test",sha,adapter);
        return new NativeGameTransport(replay,config,16,64);
    }
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static Replay valid()throws IOException{return new Replay((actual,request)->actual.fresh(snapshot("native:6",6,actual.id()),ack(actual.id(),true)));}
    @Test void exactFourUsesTheSameOriginalPacketPortAndKeepsIndependentReadAndUnknownCustody()throws Exception {
        String fourSha="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",fourAdapter="ck3-1.20.0.4-msvc-x64";
        var replay=valid();replay.packets.clear();
        replay.add(hello().put("expected_ck3_version","1.20.0.4").put("expected_ck3_sha256",fourSha).put("game_adapter_id",fourAdapter));
        replay.add(snapshot("old-four",5,null));
        try(var actual=transport(replay,fourSha,fourAdapter)) {
            var before=actual.observe(deadline());
            var first=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            var second=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            assertEquals(before.state(),first.originalFrame().state());
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            NativeFreshSnapshotPort.verifyAfterOriginal(first.acknowledgement(),second.acknowledgement(),second.originalFrame(),second.snapshotReceived());
            assertEquals(2,replay.writes);
            replay.producer=(ignored,request)->{};
            var unknown=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            assertInstanceOf(NativeActionPort.Unknown.class,unknown.dispatch());int writes=replay.writes;
            var held=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            assertSame(unknown.dispatch(),held.dispatch());assertEquals(writes,replay.writes);
        }
    }
    @Test void exactFourStillRequiresBothCapabilitiesAndTheCompleteBuildTuple()throws Exception {
        String fourSha="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",fourAdapter="ck3-1.20.0.4-msvc-x64";
        for(String wrong:List.of("fresh-capability","snapshot-capability","version","adapter","hash")){
            var replay=valid();replay.packets.clear();var advertised=hello().put("expected_ck3_version","1.20.0.4").put("expected_ck3_sha256",fourSha).put("game_adapter_id",fourAdapter);
            switch(wrong){
                case "fresh-capability"->advertised.putArray("capabilities").add("game.state.snapshot");
                case "snapshot-capability"->advertised.putArray("capabilities").add(NativeFreshSnapshotPort.CAPABILITY);
                case "version"->advertised.put("expected_ck3_version","1.19.0.6");
                case "adapter"->advertised.put("game_adapter_id",ADAPTER);
                case "hash"->advertised.put("expected_ck3_sha256",SHA);
                default->throw new AssertionError(wrong);
            }
            replay.add(advertised);
            try(var actual=transport(replay,fourSha,fourAdapter)){
                var failure=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()),wrong);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,failure.dispatch());assertEquals(0,replay.writes,wrong);
            }
        }
    }
    @Test void independentReadKeepsBothActualPacketsChronologyAndUnchangedStateInsteadOfTheCachedFrame()throws Exception {
        var replay=valid();try(var actual=transport(replay)) {
            var before=actual.observe(deadline());var received=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            assertEquals(before.state(),received.originalFrame().state());assertNotEquals(before.snapshotId(),received.originalFrame().snapshotId());
            assertArrayEquals(replay.snapshotPacket,received.originalFrame().originalPacket());assertArrayEquals(replay.ackPacket,received.acknowledgement().originalPacket());
            assertEquals("native:6",received.originalFrame().snapshotId());assertEquals(BigInteger.valueOf(6),received.originalFrame().nativeRevision());
            assertEquals(before.session(),received.originalFrame().session());assertEquals(1,replay.writes);
            var custody=received.acknowledgement().custody().orElseThrow();custody.verify(received.acknowledgement());
            assertEquals(custody,NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(custody)));
            assertTrue(custody.writeCompleted().order().compareTo(received.snapshotReceived().order())<0);
            assertTrue(received.snapshotReceived().order().compareTo(custody.responseReceived().order())<0);
            assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(received.originalFrame().originalPacket()));
            assertEquals(received.originalFrame().observedAt(),actual.currentSnapshot(deadline()).observedAt());
            assertEquals(received.originalFrame().observedAt(),actual.diagnostics().production().orElseThrow().lastReceivedSnapshot().orElseThrow().observedAt());
            assertEquals(BigInteger.valueOf(2),actual.diagnostics().production().orElseThrow().receivedSnapshotCount());
        }
    }
    @Test void afterRequiresAnIndependentActualReadButNotAnAdvancedNativeRevision()throws Exception {
        var replay=valid();try(var actual=transport(replay)) {
            actual.observe(deadline());
            var first=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            var second=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            assertEquals(first.originalFrame().nativeRevision(),second.originalFrame().nativeRevision());
            assertEquals(first.originalFrame().state(),second.originalFrame().state());
            NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
            var original=second.acknowledgement();
            var archived=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),
                    original.originalFrame(),original.originalPacket(),original.outbound(),
                    java.util.Optional.of(NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(original.custody().orElseThrow()))));
            NativeFreshSnapshotPort.verifyAfterOriginal(first.acknowledgement(),archived,second.originalFrame(),second.snapshotReceived());
            assertThrows(IOException.class,()->NativeFreshSnapshotPort.verifyAfter(second.acknowledgement(),first));
            assertThrows(IOException.class,()->NativeFreshSnapshotPort.verifyAfter(second.acknowledgement(),second));
            assertEquals(2,replay.writes);
        }
    }
    @Test void escapedNativeResultIdentityAndMaximumUint64RemainExactThroughTheActualReceiver()throws Exception {
        String identity="native:\"\\\n雪\uD83D\uDE00";
        var replay=new Replay((actual,request)->{
            var frame=snapshot(identity,6,actual.id());frame.put("revision",NativeWire.UINT64_MAX);
            var response=ack(actual.id(),true);var result=(ObjectNode)response.get("result");
            result.put("snapshot_id",identity).put("revision",NativeWire.UINT64_MAX);
            actual.fresh(frame,response);
        });try(var actual=transport(replay)) {
            actual.observe(deadline());
            var received=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            assertEquals(identity,received.originalFrame().snapshotId());
            assertEquals(NativeWire.UINT64_MAX,received.originalFrame().nativeRevision());
            var original=received.acknowledgement();
            var result=NativeWire.parse(original.originalResultToken().orElseThrow().bytes());
            assertEquals(identity,result.get("snapshot_id").textValue());
            assertEquals(NativeWire.UINT64_MAX,result.get("revision").bigIntegerValue());
            assertArrayEquals(replay.snapshotPacket,received.originalFrame().originalPacket());
            assertArrayEquals(replay.ackPacket,original.originalPacket());
            var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(original.originalPacket()));
            assertArrayEquals(decoded.result().token().orElseThrow().value(),original.originalResultToken().orElseThrow().bytes());
            NativeFreshSnapshotPort.verifyOriginal(original,received.originalFrame(),received.snapshotReceived());
            assertEquals(1,replay.writes);
        }
    }
    @Test void afterRejectsOtherHeldCustodyMissingChronologyAndChangedOriginalAckFields()throws Exception {
        var left=valid();var right=valid();try(var actual=transport(left);var other=transport(right)) {
            actual.observe(deadline());other.observe(deadline());
            var first=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            var second=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.readFreshFullState(deadline()));
            var alien=assertInstanceOf(NativeFreshSnapshotPort.Received.class,other.readFreshFullState(deadline()));
            assertEquals(first.originalFrame().session(),alien.originalFrame().session());
            assertThrows(IOException.class,()->NativeFreshSnapshotPort.verifyAfter(alien.acknowledgement(),second));
            var original=first.acknowledgement();
            var noChronology=new NativeActionPort.AckReceived(original.requestId(),true,original.originalResultToken(),
                    original.originalFrame(),original.originalPacket(),original.outbound());
            assertThrows(IOException.class,()->NativeFreshSnapshotPort.verifyAfter(noChronology,second));
            var refused=new NativeActionPort.AckReceived(original.requestId(),false,original.originalResultToken(),
                    original.originalFrame(),original.originalPacket(),original.outbound(),original.custody());
            assertThrows(IOException.class,()->NativeFreshSnapshotPort.verifyAfter(refused,second));
            var changedToken=new NativeActionPort.AckReceived(original.requestId(),true,java.util.Optional.empty(),
                    original.originalFrame(),original.originalPacket(),original.outbound(),original.custody());
            assertThrows(IOException.class,()->NativeFreshSnapshotPort.verifyAfter(changedToken,second));
            assertEquals(2,left.writes);assertEquals(1,right.writes);
        }
    }
    @Test void positiveAckWithNoNewMatchingPacketCannotUseOldCachedStateAndCannotRetryAutomatically()throws Exception {
        var replay=new Replay((actual,request)->actual.add(ack(actual.id(),true)));try(var actual=transport(replay)) {
            var old=actual.observe(deadline());var missing=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            assertInstanceOf(NativeActionPort.AckReceived.class,missing.dispatch());assertTrue(missing.originalFrame().isEmpty());
            assertArrayEquals(old.originalPacket(),actual.currentSnapshot(deadline()).originalPacket());int reads=replay.reads;
            assertSame(missing.dispatch(),assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline())).dispatch());
            assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.collectFreshFullState(missing.dispatch().requestId(),deadline()));
            assertEquals(1,replay.writes);assertEquals(reads,replay.reads);
        }
    }
    @Test void allMarkerAndAckClosedFieldFailuresKeepRealAckButNeverBecomeFreshProof()throws Exception {
        for(String failure:List.of("marker-missing","marker-bool","marker-other","snapshot-extra","semantic-rejected","ack-outer-extra","ack-schema","ack-other-id","ack-snapshot","ack-revision-bool","ack-revision-float","ack-revision-text","ack-revision-mismatch","ack-revision-null","ack-extra")) {
            var replay=new Replay((actual,request)->{
                var frame=snapshot("native:6",6,actual.id());var response=ack(actual.id(),true);var result=(ObjectNode)response.get("result");
                switch(failure) {
                    case "marker-missing"->frame.remove("read_request_id");case "marker-bool"->frame.put("read_request_id",true);case "marker-other"->frame.put("read_request_id","different-original");
                    case "snapshot-extra"->frame.put("extra",true);case "semantic-rejected"->((ObjectNode)frame.get("state")).put("active_wars",true);case "ack-outer-extra"->response.putNull("error");
                    case "ack-schema"->result.put("schema","other");case "ack-other-id"->result.put("request_id","different-original");case "ack-snapshot"->result.put("snapshot_id","old");
                    case "ack-revision-bool"->result.put("revision",true);case "ack-revision-float"->result.put("revision",6.0);case "ack-revision-text"->result.put("revision","6");
                    case "ack-revision-mismatch"->result.put("revision",7);case "ack-revision-null"->result.putNull("revision");case "ack-extra"->result.put("extra",true);
                    default->throw new AssertionError(failure);
                }
                actual.fresh(frame,response);
            });try(var actual=transport(replay)) {
                actual.observe(deadline());var failed=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()),failure);
                assertInstanceOf(NativeActionPort.AckReceived.class,failed.dispatch());assertEquals(1,replay.writes);
                assertArrayEquals(replay.ackPacket,((NativeActionPort.AckReceived)failed.dispatch()).originalPacket());
            }
        }
    }
    @Test void multipleClaimedPacketsAndAckBeforeSnapshotCannotBecomeIndependentProof()throws Exception {
        for(boolean duplicate:List.of(false,true)) {
            var replay=new Replay((actual,request)->{
                if(duplicate){actual.add(snapshot("native:6",6,actual.id()));actual.add(snapshot("native:6",6,actual.id()));actual.add(ack(actual.id(),true));}
                else {actual.add(ack(actual.id(),true));actual.add(snapshot("native:6",6,actual.id()));}
            });try(var actual=transport(replay)) {
                actual.observe(deadline());var failed=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
                assertInstanceOf(NativeActionPort.AckReceived.class,failed.dispatch());assertEquals(1,replay.writes);
                assertEquals(duplicate,failed.originalFrame().isPresent());
            }
        }
    }
    @Test void unknownThenConcurrentCallsAndLateCollectionNeverResubmitOrInventTheFirstFrame()throws Exception {
        var replay=new Replay((actual,request)->actual.add(snapshot("native:6",6,actual.id())));
        try(var actual=transport(replay)) {
            actual.observe(deadline());var missing=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            var original=assertInstanceOf(NativeActionPort.Unknown.class,missing.dispatch());assertTrue(missing.originalFrame().isPresent());
            int reads=replay.reads;
            try(var workers=Executors.newFixedThreadPool(4)) {
                var futures=new ArrayList<java.util.concurrent.Future<NativeFreshSnapshotPort.Result>>();
                for(int i=0;i<12;i++)futures.add(workers.submit(()->actual.readFreshFullState(deadline())));
                for(var future:futures)assertSame(original,assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,future.get(5,TimeUnit.SECONDS)).dispatch());
            }
            assertEquals(1,replay.writes);assertEquals(reads,replay.reads);
            assertThrows(IOException.class,()->actual.collectFreshFullState("different-original",deadline()));
            replay.add(ack(original.requestId(),true));
            var received=assertInstanceOf(NativeFreshSnapshotPort.Received.class,actual.collectFreshFullState(original.requestId(),deadline()));
            assertArrayEquals(missing.originalFrame().orElseThrow().originalPacket(),received.originalFrame().originalPacket());
            assertEquals(original.requestId(),received.acknowledgement().requestId());assertEquals(1,replay.writes);
            assertTrue(actual.pollOriginalOutcome(original.requestId()).isEmpty());
        }
    }
    @Test void exactHelloCapabilityAndVersionAreNecessaryBeforeAnyRequestWrite()throws Exception {
        for(String wrong:List.of("capability","version","adapter","hash")) {
            var replay=valid();replay.packets.clear();var hello=hello();
            switch(wrong) {
                case "capability"->hello.putArray("capabilities").add("game.state.snapshot");
                case "version"->hello.put("expected_ck3_version","1.20.0.4");
                case "adapter"->hello.put("game_adapter_id","ck3-1.20.0.4-msvc-x64");
                case "hash"->hello.put("expected_ck3_sha256","0".repeat(64));
                default->throw new AssertionError(wrong);
            }
            replay.add(hello);try(var actual=transport(replay)) {
                var failure=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()),wrong);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,failure.dispatch());assertEquals(0,replay.writes);
            }
        }
    }
    @Test void enteredWriteErrorPreservesActualUnknownAndExplicitNativeFailureStaysItsRealAck()throws Exception {
        var replay=valid();replay.failWrite=true;try(var actual=transport(replay)) {
            actual.observe(deadline());var first=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            assertInstanceOf(NativeActionPort.Unknown.class,first.dispatch());assertTrue(first.originalFrame().isEmpty());
            assertSame(first.dispatch(),assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline())).dispatch());assertEquals(1,replay.writes);
        }
        var rejected=new Replay((actual,request)->actual.add(ack(actual.id(),false)));try(var actual=transport(rejected)) {
            actual.observe(deadline());var result=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,actual.readFreshFullState(deadline()));
            assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,result.dispatch()).nativeOk());assertTrue(result.originalFrame().isEmpty());
            assertEquals(1,rejected.writes);
        }
    }
}
