package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure Java DATA, not C++ originals or an actual open/close, snapshot, callback or action lease. */
final class NativeCurrentZg361ScoreboardDataTest {
    private static final BigInteger MAX=NativeWire.UINT64_MAX;
    private static final BigInteger ZERO=BigInteger.ZERO;
    private static CoreFrame.Partial core(int actor) {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(0,3,true,0,true,true,actor,true));
    }
    private static CurrentZg361Ae2Source source(CurrentZg361Ae2Source.Scoreboard value) {
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.SCOREBOARD,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(value));
    }
    private static CurrentZg361Ae2Source closed(String entry) {
        return source(new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,false,false,false,
                3,0,Optional.of(entry),true,false));
    }
    private static CurrentLetterResult.OwnerWitness owner() {
        return new CurrentLetterResult.OwnerWitness(MAX,BigInteger.ONE,BigInteger.TWO,0xffff_ffffL);
    }

    @Test void threeAppendedFactoriesUseProductionStrictPacketAndExactCapabilities() throws Exception {
        var actions=List.of(CurrentZg361Ae2.Action.QUERY_SCOREBOARD,
                CurrentZg361Ae2.Action.OPEN_SCOREBOARD,CurrentZg361Ae2.Action.CLOSE_SCOREBOARD);
        for (int i=0;i<actions.size();i++) {
            var action=actions.get(i);assertEquals(10+i,action.ordinal());
            assertEquals(CurrentZg361Ae2Source.Kind.SCOREBOARD,action.sourceKind());
            assertEquals(i==0,action.queryOnly());
            for (int actor:new int[]{0,-2}) {
                var value=action.queryOnly()?ZERO:MAX;
                var request=CurrentZg361Ae2.request(core(actor),action,value,value);
                assertEquals(action.queryOnly()?CurrentZg361Ae2.SCOREBOARD_QUERY_CAPABILITY:
                        CurrentZg361Ae2.SCOREBOARD_COMMAND_CAPABILITY,request.requiredCapability().orElseThrow());
                byte[] packet=NativeGameTransport.currentZg361Ae2Packet("java-data-scoreboard-"+i,request,MAX);
                assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
                var envelope=StrictJson.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)),Set.of(
                        "type","protocol_version","request_id","step","actor","target","arguments","deadline_unix_ms"));
                assertEquals(MAX,envelope.get("deadline_unix_ms").bigIntegerValue());
                assertEquals(1,StrictJson.object(envelope.get("arguments"),Set.of("zg361_ae2")).size());
                var claim=StrictJson.object(envelope.get("arguments").get("zg361_ae2"),Set.of("schema","game_version",
                        "executable_sha256","adapter_id","backend","action","expected_core","provider_generation","query_sequence"));
                assertEquals(action.wire(),claim.get("action").textValue());
                assertTrue(claim.get("provider_generation").isTextual());
                assertEquals(value.toString(),claim.get("provider_generation").textValue());
                assertEquals(value.toString(),claim.get("query_sequence").textValue());
                assertEquals(actor,claim.get("expected_core").get("played_character_id").intValue());
                var decoded=NativeWire.decodeExecuteRequest(packet);
                assertTrue(decoded.expectedRevision().isEmpty());assertTrue(decoded.expectedSnapshotRevision().isEmpty());
            }
            assertThrows(IllegalArgumentException.class,()->CurrentZg361Ae2.request(core(0),action,
                    action.queryOnly()?BigInteger.ONE:ZERO,action.queryOnly()?BigInteger.ONE:ZERO));
        }
        assertThrows(IllegalArgumentException.class,()->CurrentZg361Ae2.request(core(-1),actions.get(0),ZERO,ZERO));
        assertThrows(IllegalArgumentException.class,()->CurrentZg361Ae2.request(core(0),actions.get(1),MAX.add(BigInteger.ONE),MAX));
    }

    @Test void physicalSnapshotsKeepNullableEntriesAndFalseDataWithoutInventingAdmissibility() throws Exception {
        var absent=source(new CurrentZg361Ae2Source.Scoreboard(true,false,false,false,false,false,false,
                0,0,Optional.empty(),false,false));
        assertTrue(absent.actionAdmissible(CurrentZg361Ae2.Action.QUERY_SCOREBOARD));
        assertFalse(absent.actionAdmissible(CurrentZg361Ae2.Action.OPEN_SCOREBOARD));
        assertTrue(absent.scoreboard().orElseThrow().openEntry().isEmpty());
        assertEquals(absent,CurrentZg361Ae2Source.decode(absent.encode()));
        for (String entry:List.of("zg361_scoreboard_entry_managed","zg361_scoreboard_entry_received","zg361_scoreboard_entry_system")) {
            var snapshot=closed(entry);
            assertEquals(snapshot,CurrentZg361Ae2Source.decode(snapshot.encode()));
            assertEquals(3,StrictJson.object(snapshot.encode(),Set.of("schema","kind","scoreboard")).size());
            assertEquals(12,snapshot.encode().get("scoreboard").size());
            assertTrue(snapshot.actionAdmissible(CurrentZg361Ae2.Action.OPEN_SCOREBOARD));
            assertFalse(snapshot.actionAdmissible(CurrentZg361Ae2.Action.CLOSE_SCOREBOARD));
        }
        // Physical guards need not imply a public true permission bit or a modal child count>0.
        var noPermission=source(new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,true,true,true,
                4096,0,Optional.empty(),false,false));
        assertFalse(noPermission.actionAdmissible(CurrentZg361Ae2.Action.CLOSE_SCOREBOARD));
        assertEquals(noPermission,CurrentZg361Ae2Source.decode(noPermission.encode()));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Scoreboard(false,false,false,false,false,false,false,0,0,Optional.empty(),false,false));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Scoreboard(true,true,false,false,false,false,false,0,0,Optional.empty(),false,false));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,false,false,false,4097,0,Optional.empty(),false,false));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,false,false,false,1,1,Optional.empty(),false,false));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,false,false,false,1,0,Optional.empty(),true,false));
        assertThrows(IllegalArgumentException.class,()->closed("zg361_scoreboard_entry_other"));
        var wrongCount=closed("zg361_scoreboard_entry_managed").encode();
        ((com.fasterxml.jackson.databind.node.ObjectNode)wrongCount.get("scoreboard")).put("window_nodes",1.5);
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.decode(wrongCount));
    }

    @Test void originalConstructorOverloadsAndExactUnionsRemainSeparate() throws Exception {
        var controls=new CurrentZg361Ae2Source.Controls(false,false,false,false,false,false,false,Optional.empty(),List.of());
        var oldThree=new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(controls),Optional.empty());
        assertTrue(oldThree.scoreboard().isEmpty());assertEquals(4,oldThree.encode().size());
        assertEquals(oldThree,CurrentZg361Ae2Source.decode(oldThree.encode()));
        var review=new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,false,false,false,false,false,false,
                false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty());
        var oldFour=new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.REVIEW,Optional.empty(),Optional.empty(),Optional.of(review));
        assertTrue(oldFour.scoreboard().isEmpty());assertEquals(3,oldFour.encode().size());
        assertEquals(oldFour,CurrentZg361Ae2Source.decode(oldFour.encode()));
        var originalExtra=oldThree.encode();originalExtra.putNull("scoreboard");
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.decode(originalExtra));
        var scoreExtra=closed("zg361_scoreboard_entry_system").encode();scoreExtra.putNull("review");
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.decode(scoreExtra));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.SCOREBOARD,
                Optional.of(controls),Optional.empty(),Optional.empty(),closed("zg361_scoreboard_entry_system").scoreboard()));
        assertFalse(oldFour.actionAdmissible(CurrentZg361Ae2.Action.OPEN_SCOREBOARD));
    }

    @Test void navigationRetainsBeforeSnapshotAndUnknownKeepsRawFlagsSourceNull() throws Exception {
        var before=closed("zg361_scoreboard_entry_managed");
        var dispatch=new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.OPEN_SCOREBOARD,CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,
                true,true,true,MAX,MAX,MAX,Optional.of(core(-2).prefix()),Optional.of(owner()),Optional.of(before),Optional.empty());
        assertEquals(dispatch,CurrentZg361Ae2Result.decode(dispatch.encode()));
        assertFalse(dispatch.source().orElseThrow().scoreboard().orElseThrow().modalVisible());
        assertFalse(dispatch.nativeHandled());assertEquals(20,NativeWire.parse(dispatch.encode().bytes()).size());
        var opened=source(new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,true,true,true,2,0,Optional.empty(),false,true));
        var close=new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.CLOSE_SCOREBOARD,CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,
                true,true,true,MAX,MAX,MAX,Optional.of(core(0).prefix()),Optional.of(owner()),Optional.of(opened),Optional.empty());
        assertTrue(close.source().orElseThrow().scoreboard().orElseThrow().modalVisible());
        assertEquals(close,CurrentZg361Ae2Result.decode(close.encode()));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.CLOSE_SCOREBOARD,
                CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,true,true,true,MAX,MAX,MAX,
                Optional.of(core(0).prefix()),Optional.of(owner()),Optional.of(before),Optional.empty()));
        var unknown=new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_SCOREBOARD,CurrentZg361Ae2Result.Status.INDETERMINATE,
                false,true,false,MAX,MAX,MAX,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("original diagnostic"));
        var round=CurrentZg361Ae2Result.decode(unknown.encode());
        assertEquals(unknown,round);assertTrue(round.nativeReturned());assertFalse(round.effectAttempted());
        assertFalse(round.cleanupKnown());assertTrue(round.source().isEmpty());assertEquals(MAX,round.claimSequence());
    }
}
