package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.NaturalClockOriginals.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverPendingEpisodeProjection;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Actual sole domain encoder -> decoder -> immutable typed child consumer. DATA fixtures grant no Root custody. */
final class PendingClockOriginalsCodecTest {
    private static final Instant AT=Instant.parse("2026-10-24T06:30:00Z");
    private static final BigInteger HIGH=new BigInteger("18446744073709551615");
    private static ExactRef ref(String name){return new ExactRef("pure-pending-codec/"+name,17,"a".repeat(64));}
    private static Capture capture(){var source=new G2Source("pure-pending-codec",AT.toString(),"1.20.0.4",ref("source"));return new Capture("old-clock","b".repeat(64),ref("parent"),"resume","c".repeat(64),ref("resume"),source.machineId(),"session",42,HIGH.toString(),HIGH.toString(),"old-run",source,new Frame("old",HIGH,HIGH,100,73,1),ref("exe"),"340282366920938463463374607431768211455","1770000000000000000",ref("root-read"),ref("root-result"),ref("native"),ref("sem"),ref("stamp"),ref("driver"),ref("hello"),ref("qualified"),"d".repeat(64),17,Optional.empty());}
    private static Document document(){
        var child=new DriverPendingEpisodeProjection(2,3,"a".repeat(64),3,4,new GameGeneration(42,new PythonOnlyUInt64(HIGH)),"pure-pending-codec",AT,"old-run",BigInteger.valueOf(73),"new-run",BigInteger.valueOf(74),ref("before"),ref("after"),ref("aux"),ref("obligation"),ref("cause"));
        var exact=new ExactRef("pure-pending-codec/projection",child.encode().length,DriverJson.sha256(child.encode()));
        var read=new ReadArtifact(ref("timeline"),ref("frame"),"query",new Frame("current",HIGH,HIGH,100,74,1),ref("semantic"));
        var ready=new Ready("continue","e".repeat(64),ref("continue"),ref("dead"),read,Optional.empty(),List.of(),ref("final-native"),ref("final-sem"),ref("final-driver"),ref("final-source"));
        var intent=new DateIntent("life","f".repeat(64),new ExactRef("pure-pending-codec/life",19,"f".repeat(64)),ref("close"),ref("clearance"),AT);
        return new Document(capture(),Optional.of(ready),Optional.of(new PendingProjection(child,exact,Optional.empty(),Optional.of(intent))),AT);
    }
    @Test void realDomainEncoderRetainsMachineTimeExactPendingChildAndOnceDateOriginals(){
        var actual=document();var bytes=encode(actual);assertEquals(actual,decode(bytes));
        var wire=StrictJson.parse(bytes);assertEquals("pure-pending-codec",wire.get("machine_id").textValue());assertEquals(AT.toString(),wire.get("observed_at_utc").textValue());
        var decoded=decode(bytes).pendingProjection().orElseThrow();assertEquals(actual.pendingProjection().orElseThrow().dateIntent(),decoded.dateIntent());
        assertTrue(decoded.artifacts().contains(decoded.dateIntent().orElseThrow().command()));assertEquals(HIGH,decode(bytes).capture().predecessorFrame().nativeRevision());
    }
    @Test void missingNullBooleanAndOldSchemaCannotAliasCurrentPendingOriginals(){
        var root=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(document()));
        var missing=root.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("pending_projection")).remove("date_intent");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(missing)));
        var noDate=root.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)noDate.get("pending_projection")).putNull("date_intent");assertTrue(decode(StrictJson.canonical(noDate)).pendingProjection().orElseThrow().dateIntent().isEmpty());
        var wrong=root.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("pending_projection").get("date_intent")).put("body_sha256",true);assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(wrong)));
        var old=root.deepCopy();old.put("schema","xar.java.natural-clock-originals/v1");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(old)));
        var machine=root.deepCopy();machine.put("machine_id","another-machine");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(machine)));
    }
    @Test void projectionAndDateIntentKeepTheirOwnExactOriginalDigest(){
        var actual=document().pendingProjection().orElseThrow();assertThrows(IllegalArgumentException.class,()->new PendingProjection(actual.value(),ref("wrong"),Optional.empty(),actual.dateIntent()));
        assertThrows(IllegalArgumentException.class,()->new DateIntent("life","b".repeat(64),ref("command"),ref("close"),ref("clearance"),AT));
    }
    @Test void actualEventChildCodecRetainsItsOnceCommandReadSourceAndOriginalUnknownChain(){
        var command=new ExactRef("pure-pending-codec/event-command",23,"c".repeat(64));
        var event=new EventIntent("pure-pending-codec",2,"event-once","c".repeat(64),command,ref("original-window"),19,false,List.of(ref("stock-source"),ref("context")),Optional.of(ref("previous-event")),Optional.of(ref("original-unknown")),Optional.of(ref("actual-confirmed")),AT);
        assertEquals(event,decodeEventIntent(encodeEventIntent(event)));
        var old=document();var projection=old.pendingProjection().orElseThrow();var document=new Document(old.capture(),old.ready(),Optional.of(new PendingProjection(projection.value(),projection.original(),projection.latestMutation(),projection.dateIntent(),Optional.of(event),Optional.of(ref("original-diagnosis")))),AT);
        assertEquals(document,decode(encode(document)));assertTrue(document.artifacts().contains(ref("actual-confirmed")));assertTrue(document.artifacts().contains(ref("original-unknown")));assertTrue(document.artifacts().contains(ref("original-diagnosis")));
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(document));((com.fasterxml.jackson.databind.node.ObjectNode)row.get("pending_projection")).remove("event_diagnosis");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(row)));
    }
    @Test void laterDateMustRetainBothActualPriorDocumentAndSettledReceipt(){
        var old=document();var projection=old.pendingProjection().orElseThrow();var prior=projection.dateIntent().orElseThrow();
        var next=new DateIntent("new-life",prior.bodySha256(),prior.command(),prior.closeReceipt(),prior.materialClearance(),AT,Optional.of(ref("prior-canonical-domain")),Optional.of(ref("prior-zero-day-receipt")));
        var actual=new Document(old.capture(),old.ready(),Optional.of(new PendingProjection(projection.value(),projection.original(),projection.latestMutation(),Optional.of(next))),AT);assertEquals(actual,decode(encode(actual)));
        assertThrows(IllegalArgumentException.class,()->new DateIntent("new-life",prior.bodySha256(),prior.command(),prior.closeReceipt(),prior.materialClearance(),AT,Optional.of(ref("prior-canonical-domain")),Optional.empty()));
    }
}
