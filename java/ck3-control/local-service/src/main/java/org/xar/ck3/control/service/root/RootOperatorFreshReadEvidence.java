package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Strict original READ custody. Parsing is DATA only; the canonical private operator source issues the live proof. */
public final class RootOperatorFreshReadEvidence {
    public static final String SCHEMA="xar.java.operator-independent-read-originals/v1";
    private RootOperatorFreshReadEvidence(){ }
    public record Original(NativeObservationPort.ObservedFrame before,
            NativeActionPort.AckReceived afterRead,NativeObservationPort.ObservedFrame after,
            NativeActionPort.AckReceived setter,List<ExactRef> references) {
        public Original {Objects.requireNonNull(before);Objects.requireNonNull(afterRead);Objects.requireNonNull(after);Objects.requireNonNull(setter);references=List.copyOf(references);}
    }
    static ExactRef preserve(ActionCommand command,NativeActionPort.AckReceived setter,
            RootOperatorPhysicalEvidence.Captured before,RootOperatorPhysicalEvidence.Captured after,ActionPorts.OutcomeArchive archive)throws IOException {
        StrictJson.require(before.fresh().isEmpty(),"BEFORE must retain its original accepted packet/revision without another native READ");
        var last=after.fresh().orElseThrow(()->new IOException("AFTER requires its actual independent READ receipt"));
        requireOrder(before.full().actual(),setter,last.acknowledgement());
        archive.preserve(last.acknowledgement());archive.preserve(setter);
        var row=StrictJson.object();row.put("schema",SCHEMA).put("action_id",command.actionId()).put("body_sha256",ActionCodec.bodySha256(command));
        row.set("setter_ack",archive.referenceOf(setter).toJson());row.set("source",command.source().sourceRef().toJson());
        var retained=StrictJson.object();retained.set("native_packet",before.full().originalEvidence().toJson());
        retained.put("observed_at_utc",before.full().actual().observedAt().toString());row.set("before",retained);
        row.set("after",sample(last,archive.referenceOf(last.acknowledgement()),after.full().originalEvidence()));
        var material=new RawJson(StrictJson.canonical(row));var proof=archive.preserveMaterial(material);
        read(proof,command,archive);return proof;
    }
    private static ObjectNode sample(NativeFreshSnapshotPort.Received original,ExactRef ack,ExactRef nativePacket){
        var row=StrictJson.object();row.set("ack",ack.toJson());row.set("native_packet",nativePacket.toJson());
        row.put("snapshot_received_order",original.snapshotReceived().order().toString());row.put("snapshot_received_at_utc",original.snapshotReceived().observedAt().toString());return row;
    }
    /** Uses the transport owner's one original-wire verifier; no synthetic Received or live source permission is returned. */
    public static Original read(ExactRef proof,ActionCommand command,ActionPorts.OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(command);Objects.requireNonNull(archive);
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind,"fresh original proof is finite to the original operator command");
        var raw=archive.loadMaterial(proof);StrictJson.require(proof.bytes()==raw.bytes().length&&proof.sha256().equals(ActionCodec.sha256(raw.bytes())),"operator fresh original material changed");
        var row=StrictJson.object(StrictJson.parse(raw.bytes()),Set.of("schema","action_id","body_sha256","setter_ack","source","before","after"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&command.actionId().equals(StrictJson.text(row.get("action_id")))
                &&ActionCodec.bodySha256(command).equals(StrictJson.text(row.get("body_sha256")))
                &&command.source().sourceRef().equals(ExactRef.fromJson(row.get("source"))),"operator independent READ originals crossed command/body/source");
        var after=sample(StrictJson.object(row.get("after"),sampleFields()),archive);
        ExactRef setterRef=ExactRef.fromJson(row.get("setter_ack"));var dispatch=archive.load(setterRef);
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"operator fresh proof needs the original typed setter ACK metadata");
        var setter=(NativeActionPort.AckReceived)dispatch;
        var retained=StrictJson.object(row.get("before"),Set.of("native_packet","observed_at_utc"));
        ExactRef beforeRef=ExactRef.fromJson(retained.get("native_packet"));byte[] beforePacket=archive.loadNativeFrame(beforeRef);
        var decoded=NativeWire.decode(beforePacket);StrictJson.require(decoded instanceof NativeWire.Snapshot,"actual original BEFORE snapshot packet required");
        var snapshot=(NativeWire.Snapshot)decoded;var custody=setter.custody().orElseThrow(()->new IOException("original setter custody is absent"));
        var before=new NativeObservationPort.ObservedFrame(custody.session(),snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),beforePacket,
                Instant.parse(StrictJson.text(retained.get("observed_at_utc"))));
        requireOrder(before,setter,after.ack());
        StrictJson.require(before.session().equals(after.frame().session())&&before.session().equals(custody.session())
                &&before.session().machineId().equals(command.origin().machineId())&&before.session().game().equals(command.origin().game())
                &&before.session().sessionId().equals(command.sessionId()),"operator original BEFORE and independent AFTER READ crossed actual Game/connection/session");
        OperatorPlayerSwitch.requireAfter(((CommandExpectation.OperatorRebind)command.expectation()).expected().request(),
                org.xar.ck3.control.contracts.FullJsonTree.parse(after.frame().state().bytes(),DriverJson.MAX_NATIVE_BYTES));
        var refs=List.of(proof,beforeRef,setterRef,after.ackRef(),after.nativeRef());
        return new Original(before,after.ack(),after.frame(),setter,refs);
    }
    public static Original require(ExactRef proof,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
        Original original=read(proof,receipt.command(),archive);
        var settled=(ActionState.Settled)receipt.state();StrictJson.require(settled.settlement() instanceof ActionState.OperatorRebound,"actual typed operator receipt required");
        var completion=((ActionState.OperatorRebound)settled.settlement()).observation();var refs=completion.originals();
        StrictJson.require(original.setter().equals(settled.dispatch())&&archive.referenceOf(original.setter()).equals(refs.ack())
                &&ref(original.before().originalPacket(),refs.beforeNative())&&ref(original.after().originalPacket(),refs.afterNative())
                &&refs.beforeNative().equals(settled.attempt().guard().nativeEvidence())
                &&original.before().observedAt().equals(settled.attempt().guard().observedAt())
                &&original.after().session().equals(completion.transport()),"operator Completion substituted its real original BEFORE, independent READ or original setter ACK");
        return original;
    }
    private record Sample(NativeActionPort.AckReceived ack,NativeObservationPort.ObservedFrame frame,ExactRef ackRef,ExactRef nativeRef){ }
    private static Set<String> sampleFields(){return Set.of("ack","native_packet","snapshot_received_order","snapshot_received_at_utc");}
    private static Sample sample(ObjectNode row,ActionPorts.OutcomeArchive archive)throws IOException {
        ExactRef ackRef=ExactRef.fromJson(row.get("ack")),nativeRef=ExactRef.fromJson(row.get("native_packet"));
        var dispatch=archive.load(ackRef);StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"actual READ ACK typed metadata required");
        var ack=(NativeActionPort.AckReceived)dispatch;var custody=ack.custody().orElseThrow(()->new IOException("actual READ custody is absent"));custody.verify(ack);
        byte[] packet=archive.loadNativeFrame(nativeRef);var decoded=NativeWire.decode(packet);
        StrictJson.require(decoded instanceof NativeWire.Snapshot,"independent READ needs its original snapshot packet");var snapshot=(NativeWire.Snapshot)decoded;
        String order=StrictJson.text(row.get("snapshot_received_order"));StrictJson.require(order.matches("[1-9][0-9]*"),"canonical actual receive order required");
        var event=new NativeRequestChronology.Event(new BigInteger(order),Instant.parse(StrictJson.text(row.get("snapshot_received_at_utc"))));
        var frame=new NativeObservationPort.ObservedFrame(custody.session(),snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),packet,event.observedAt());
        NativeFreshSnapshotPort.verifyOriginal(ack,frame,event);return new Sample(ack,frame,ackRef,nativeRef);
    }
    private static void requireOrder(NativeObservationPort.ObservedFrame before,NativeActionPort.AckReceived setter,NativeActionPort.AckReceived after)throws IOException {
        var write=setter.custody().orElseThrow(()->new IOException("actual setter chronology missing"));write.verify(setter);
        var last=after.custody().orElseThrow(()->new IOException("after READ chronology missing"));last.verify(after);
        StrictJson.require(before.session().equals(write.session())&&last.session().equals(write.session())
                &&last.custodyEpoch().equals(write.custodyEpoch())&&write.responseReceived().order().compareTo(last.writeEntered().order())<0
                &&!write.writeEntered().observedAt().isBefore(before.observedAt())
                &&!last.writeEntered().observedAt().isBefore(write.responseReceived().observedAt()),
                "operator source requires retained BEFORE <= actual setter write/ACK < independent AFTER READ write on the identical actual custody epoch");
    }
    private static boolean ref(byte[] bytes,ExactRef reference){return bytes.length==reference.bytes()&&ActionCodec.sha256(bytes).equals(reference.sha256());}
}
