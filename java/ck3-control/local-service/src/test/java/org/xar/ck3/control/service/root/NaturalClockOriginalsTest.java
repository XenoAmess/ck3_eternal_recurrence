package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;
import static org.xar.ck3.control.service.root.NaturalClockOriginals.*;

/** Strict durable producer body -> decode -> immutable typed consumer; fixtures do not grant Root authority. */
final class NaturalClockOriginalsTest {
    private static ExactRef ref(String key) {return new ExactRef("D:/natural-original-fixture/"+key,17,"1".repeat(64));}
    private static Capture capture() {
        var source=new G2Source("natural-original-fixture","2026-10-24T00:00:00Z","1.20.0.4",ref("native-source"));
        return new Capture("clock-parent","a".repeat(64),ref("parent-command"),"clock-child","b".repeat(64),ref("clock-command"),
                source.machineId(),"session",123,"133700000000000001","18446744073709551615","old-episode",source,
                new Frame("native:1",BigInteger.valueOf(9),new BigInteger("18446744073709551615"),100,29829,1),
                ref("ck3.exe"),"340282366920938463463374607431768211455","1770000000000000000",ref("root-read"),ref("root-result"),ref("packet"),ref("semantic"),ref("stamp"),ref("driver"),ref("hello"),ref("source-proof"),"c".repeat(64),7,Optional.empty());
    }
    private static ReadArtifact read(int ordinal) {return new ReadArtifact(ref("read-"+ordinal),ref("frame-"+ordinal),"read-"+ordinal,new Frame("native:"+ordinal,BigInteger.valueOf(10+ordinal),BigInteger.valueOf(20+ordinal),101,30000,1),ref("semantic-"+ordinal));}
    private static Ready ready(Optional<ExactRef> close,List<ReadArtifact> subsequent) {return new Ready("natural-parent","d".repeat(64),ref("natural-command"),ref("retained-death"),read(1),close,subsequent,ref("final-native"),ref("final-semantic"),ref("final-driver"),ref("final-source"));}
    @Test void originalDecimalIdentitiesAndUnsignedNativeRevisionSurviveDurableRoundTrip() {
        var original=new Document(capture(),Optional.empty());byte[] bytes=encode(original);assertEquals(original,decode(bytes));
        var row=StrictJson.parse(bytes);assertTrue(row.get("capture").get("game_birth_filetime").isTextual());assertTrue(row.get("capture").get("executable_file_id").isTextual());
        assertEquals("18446744073709551615",decode(bytes).capture().connectionGeneration());assertEquals(new BigInteger("18446744073709551615"),decode(bytes).capture().predecessorFrame().nativeRevision());
    }
    @Test void missingNullWrongTypeAndAliasAreNotInterchangeable() {
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(new Document(capture(),Optional.empty())));
        var missing=wire.deepCopy();missing.remove("ready");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(missing)));
        var bool=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)bool.get("capture")).put("game_pid",true);assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(bool)));
        var floating=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)floating.get("capture")).put("ledger_sequence_before_capture",7.0);assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(floating)));
        var number=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)number.get("capture")).put("game_birth_filetime",new BigInteger("133700000000000001"));assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(number)));
        var alias=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)alias.get("capture")).put("before_heir_ack",true);assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(alias)));
    }
    @Test void exactOwnFramesAndOneToEightPostqueriesRemainBoundToOneClose() {
        var document=new Document(capture(),Optional.of(ready(Optional.of(ref("close-receipt")),List.of(read(2),read(3)))));
        assertEquals(document,decode(encode(document)));assertNotEquals(document.ready().orElseThrow().initialTimeline().actualFrame(),document.ready().orElseThrow().subsequentTimeline().getFirst().actualFrame());
        assertThrows(IllegalArgumentException.class,()->ready(Optional.of(ref("close")),List.of()));
        assertThrows(IllegalArgumentException.class,()->ready(Optional.empty(),List.of(read(2))));
        assertThrows(IllegalArgumentException.class,()->ready(Optional.of(ref("close")),java.util.stream.IntStream.rangeClosed(2,10).mapToObj(NaturalClockOriginalsTest::read).toList()));
    }
    @Test void sourceMachineAndIdentityStringsCannotBeReboundByEditingTheCapture() {
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(new Document(capture(),Optional.empty())));
        var machine=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)machine.get("capture")).put("machine_id","another-machine");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(machine)));
        var padded=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)padded.get("capture")).put("connection_generation","01");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(padded)));
        var overflow=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)overflow.get("capture")).put("executable_file_id","340282366920938463463374607431768211456");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(overflow)));
    }
    @Test void originalFrameComparisonUsesActualPacketBytesAcrossIndependentArchiveDecodes() {
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));var transport=new NativeObservationPort.TransportSession("natural-original-fixture",game,BigInteger.ONE,"session");
        byte[] bytes="{\"original\":true}".getBytes(StandardCharsets.UTF_8);var first=new NativeObservationPort.ObservedFrame(transport,"native:1",BigInteger.ONE,new RawJson("{}".getBytes(StandardCharsets.UTF_8)),bytes,Instant.parse("2026-10-24T00:00:00Z"));
        var decoded=new NativeObservationPort.ObservedFrame(transport,first.snapshotId(),first.nativeRevision(),first.state(),first.originalPacket(),first.observedAt());assertTrue(RootNaturalSuccessionOriginals.sameNativeFrame(first,decoded));
        byte[] changed=first.originalPacket();changed[0]='[';var drift=new NativeObservationPort.ObservedFrame(transport,first.snapshotId(),first.nativeRevision(),first.state(),changed,first.observedAt());assertFalse(RootNaturalSuccessionOriginals.sameNativeFrame(first,drift));
    }
    @Test void rootSoftwareEpochMustStayExactWhileIndependentProofObservationTimeMayAdvance() {
        var first=StrictJson.object().put("schema","xar.java-root-native-source-proof/v2").put("machine_id","natural-original-fixture").put("session_id","session").put("mode","MANAGED").put("observed_at_utc","2026-10-24T00:00:00Z").put("owner_source_epoch","a".repeat(64));
        first.set("source_epoch_manifest",new ExactRef("D:/natural-original-fixture/epoch",20,"a".repeat(64)).toJson());for(String field:List.of("host_configuration","source","game_executable"))first.set(field,ref(field).toJson());
        var after=first.deepCopy();after.put("observed_at_utc","2026-10-24T00:00:01Z");assertDoesNotThrow(()->requireSameSourceEpoch(StrictJson.canonical(first),StrictJson.canonical(after)));
        var changed=after.deepCopy();changed.put("owner_source_epoch","b".repeat(64));changed.set("source_epoch_manifest",new ExactRef("D:/natural-original-fixture/epoch2",20,"b".repeat(64)).toJson());assertThrows(IllegalArgumentException.class,()->requireSameSourceEpoch(StrictJson.canonical(first),StrictJson.canonical(changed)));
        var old=after.deepCopy();old.put("schema","xar.java-root-native-source-proof/v1");assertThrows(IllegalArgumentException.class,()->requireSameSourceEpoch(StrictJson.canonical(first),StrictJson.canonical(old)));
    }
}
