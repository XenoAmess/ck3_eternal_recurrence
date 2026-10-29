package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeRequestChronology;

/** One fixed read-only original full-state sample; no actor setter, gameplay permit or source authority. */
public interface NativeFreshSnapshotPort {
    String STEP="query-fresh-full-state-v1";
    String CAPABILITY="game.query.fresh-full-state.v1";
    String RESULT_SCHEMA="xar.native.fresh-full-state-read/v1";
    sealed interface Result permits Received,Unavailable { NativeActionPort.DispatchOutcome dispatch(); }
    /** Constructed only by the actual held receiver after both original packets and actual ordering are checked. */
    final class Received implements Result {
        private final NativeActionPort.AckReceived acknowledgement;
        private final ObservedFrame originalFrame;
        private final NativeRequestChronology.Event snapshotReceived;
        Received(NativeActionPort.AckReceived actualAck,ObservedFrame actualFrame,NativeRequestChronology.Event actualReceived)throws IOException {
            acknowledgement=Objects.requireNonNull(actualAck);originalFrame=Objects.requireNonNull(actualFrame);snapshotReceived=Objects.requireNonNull(actualReceived);
            var custody=actualAck.custody().orElseThrow(()->new IOException("actual fresh-read request chronology unavailable"));custody.verify(actualAck);
            if(!actualAck.nativeOk()||!custody.session().equals(actualFrame.session())
                    ||snapshotReceived.order().compareTo(custody.writeCompleted().order())<=0
                    ||snapshotReceived.order().compareTo(custody.responseReceived().order())>=0
                    ||snapshotReceived.observedAt().isBefore(custody.writeCompleted().observedAt())
                    ||snapshotReceived.observedAt().isAfter(custody.responseReceived().observedAt())
                    ||!snapshotReceived.observedAt().equals(actualFrame.observedAt()))throw new IOException("fresh state was not actually received between this read write and ACK");
            var outbound=actualAck.outbound().orElseThrow(()->new IOException("fresh-read original outbound unavailable"));
            ObjectNode request=payload(outbound.originalPacket());keys(request,Set.of("type","protocol_version","request_id","step","expected_revision"));
            if(!"execute_step".equals(NativeWire.text(request.get("type")))||!BigInteger.ONE.equals(NativeWire.integer(request.get("protocol_version"),BigInteger.ONE,BigInteger.ONE))
                    ||!STEP.equals(NativeWire.text(request.get("step")))||!actualAck.requestId().equals(NativeWire.text(request.get("request_id")))
                    ||!BigInteger.ZERO.equals(NativeWire.integer(request.get("expected_revision"),BigInteger.ZERO,BigInteger.ZERO)))throw new IOException("fresh-read original request differs from its sole fixed contract");
            ObjectNode rawSnapshot=payload(actualFrame.originalPacket());keys(rawSnapshot,Set.of("type","protocol_version","snapshot_id","revision","state","read_request_id"));
            var decoded=NativeWire.decode(actualFrame.originalPacket());
            if(!(decoded instanceof NativeWire.Snapshot frame)||!frame.snapshotId().equals(actualFrame.snapshotId())||!frame.revision().equals(actualFrame.nativeRevision())
                    ||!Arrays.equals(frame.state().value(),actualFrame.state().bytes())
                    ||!actualAck.requestId().equals(NativeWire.text(payload(actualFrame.originalPacket()).get("read_request_id"))))throw new IOException("fresh state packet is not this actual request's independently received original");
            keys(payload(actualAck.originalPacket()),Set.of("type","protocol_version","request_id","ok","result"));
            var decodedAck=NativeWire.decode(actualAck.originalPacket());
            if(!(decodedAck instanceof NativeWire.CommandResult ack)||!ack.nativeOk()||!ack.requestId().equals(actualAck.requestId())
                    ||!Arrays.equals(ack.payload().value(),actualAck.originalFrame().bytes())
                    ||ack.result().token().isEmpty()||actualAck.originalResultToken().isEmpty()
                    ||!Arrays.equals(ack.result().token().orElseThrow().value(),actualAck.originalResultToken().orElseThrow().bytes()))throw new IOException("fresh ACK differs from its actual framed original");
            ObjectNode result=NativeWire.object(NativeWire.parse(ack.result().token().orElseThrow().value()));keys(result,Set.of("schema","request_id","snapshot_id","revision"));
            if(!RESULT_SCHEMA.equals(NativeWire.text(result.get("schema")))||!actualAck.requestId().equals(NativeWire.text(result.get("request_id")))
                    ||!actualFrame.snapshotId().equals(NativeWire.text(result.get("snapshot_id")))
                    ||!actualFrame.nativeRevision().equals(NativeWire.integer(result.get("revision"),BigInteger.ONE,NativeWire.UINT64_MAX)))throw new IOException("fresh ACK does not bind the independent original state packet");
        }
        @Override public NativeActionPort.AckReceived dispatch(){return acknowledgement;}
        public NativeActionPort.AckReceived acknowledgement(){return acknowledgement;}
        public ObservedFrame originalFrame(){return originalFrame;}
        public NativeRequestChronology.Event snapshotReceived(){return snapshotReceived;}
    }
    record Unavailable(NativeActionPort.DispatchOutcome dispatch,String reason,Optional<ObservedFrame> originalFrame,
            Optional<NativeRequestChronology.Event> snapshotReceived) implements Result {
        public Unavailable {Objects.requireNonNull(dispatch);Objects.requireNonNull(originalFrame);Objects.requireNonNull(snapshotReceived);
            if(reason==null||reason.isBlank()||originalFrame.isPresent()!=snapshotReceived.isPresent())throw new IllegalArgumentException("actual unavailability reason and paired retained frame/event required");}
        public Unavailable(NativeActionPort.DispatchOutcome dispatch,String reason){this(dispatch,reason,Optional.empty(),Optional.empty());}
    }
    /** Pure archived original DATA validation. This returns no Received or live/source authority. */
    static void verifyOriginal(NativeActionPort.AckReceived originalAck,ObservedFrame originalFrame,
            NativeRequestChronology.Event originalReceived)throws IOException {
        new Received(originalAck,originalFrame,originalReceived);
    }
    /**
     * Verifies an independent full-state READ after an original command acknowledgement.
     * The caller still verifies the command's business result and projects this identical frame.
     * A fresh read can have the same native revision and state as its before image.
     */
    static void verifyAfter(NativeActionPort.AckReceived originalSetterAck,Received actualRead)throws IOException {
        Objects.requireNonNull(originalSetterAck);Objects.requireNonNull(actualRead);
        verifyAfterOriginal(originalSetterAck,actualRead.acknowledgement(),actualRead.originalFrame(),actualRead.snapshotReceived());
    }
    /** Archived DATA validation only; creates no live Received, completion, writer or source authority. */
    static void verifyAfterOriginal(NativeActionPort.AckReceived originalSetterAck,
            NativeActionPort.AckReceived originalReadAck,ObservedFrame originalReadFrame,
            NativeRequestChronology.Event originalReadReceived)throws IOException {
        Objects.requireNonNull(originalSetterAck);
        verifyOriginal(originalReadAck,originalReadFrame,originalReadReceived);
        if(!originalSetterAck.nativeOk())throw new IOException("fresh after requires the original successful command ACK");
        var setter=originalSetterAck.custody().orElseThrow(()->new IOException("original command has no actual request chronology"));
        setter.verify(originalSetterAck);
        var read=originalReadAck.custody().orElseThrow(()->new IOException("independent READ has no actual request chronology"));
        if(setter.requestId().equals(read.requestId())||!setter.session().equals(read.session())
                ||!setter.custodyEpoch().equals(read.custodyEpoch()))
            throw new IOException("fresh after must use a different original request in the same actual held connection");
        if(read.writeEntered().order().compareTo(setter.responseReceived().order())<=0
                ||read.writeEntered().observedAt().isBefore(setter.responseReceived().observedAt()))
            throw new IOException("independent READ was not actually written after the original command ACK");
        var decoded=NativeWire.decode(originalSetterAck.originalPacket());
        if(!(decoded instanceof NativeWire.CommandResult command)||!command.nativeOk()
                ||!command.requestId().equals(originalSetterAck.requestId())
                ||!Arrays.equals(command.payload().value(),originalSetterAck.originalFrame().bytes())
                ||command.result().token().isPresent()!=originalSetterAck.originalResultToken().isPresent()
                ||command.result().token().isPresent()&&!Arrays.equals(command.result().token().orElseThrow().value(),
                        originalSetterAck.originalResultToken().orElseThrow().bytes()))
            throw new IOException("original command ACK fields differ from its actual framed packet");
    }
    Result readFreshFullState(Instant deadline)throws InterruptedException;
    /** Collects only the same original attempt; never creates another request or write. */
    Result collectFreshFullState(String originalRequestId,Instant deadline)throws IOException,InterruptedException;
    private static ObjectNode payload(byte[] packet)throws IOException{return NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)));}
    private static void keys(ObjectNode value,Set<String> expected)throws IOException {
        var keys=new HashSet<String>();for(var entry:value.properties())keys.add(entry.getKey());
        if(!keys.equals(expected))throw new IOException("fresh-read closed wire fields differ");
    }
}
