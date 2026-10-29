package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.contracts.StrictJson;

/** Original held-transport diagnostics DATA. Constructors never grant source/adoption/readiness authority. */
public final class NativeTransportDiagnostics {
    private NativeTransportDiagnostics() { }
    public record SnapshotFields(NativeWire.Field snapshotId,NativeWire.Field revision,NativeWire.Field dateRaw,
            NativeWire.Field speed,NativeWire.Field paused,NativeWire.Field mapReady) {
        public SnapshotFields {Objects.requireNonNull(snapshotId);Objects.requireNonNull(revision);Objects.requireNonNull(dateRaw);Objects.requireNonNull(speed);Objects.requireNonNull(paused);Objects.requireNonNull(mapReady);}
    }
    /** Each ordinal names one actual receive, even when the publisher repeats identical bytes. */
    public record ReceivedSnapshot(TransportSession session,BigInteger ordinal,NativeWire.Bytes originalPacket,Instant observedAt) {
        public ReceivedSnapshot {Objects.requireNonNull(session);positive(ordinal);Objects.requireNonNull(originalPacket);Objects.requireNonNull(observedAt);StrictJson.require(originalPacket.value().length>=5&&originalPacket.value().length<=NativeWire.MAXIMUM_FRAME_BYTES+4,"bounded actual snapshot packet required");}
        public SnapshotFields fields()throws IOException {
            ObjectNode frame=originalObject(originalPacket.value());
            byte[] payload=Arrays.copyOfRange(originalPacket.value(),4,originalPacket.value().length);
            StrictJson.require(frame.path("type").isTextual()&&frame.get("type").textValue().equals("state_snapshot")
                    &&NativeWire.integer(frame.get("protocol_version"),BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE),"actual protocol-v1 state_snapshot required");
            ObjectNode state=frame.get("state") instanceof ObjectNode object?object:NativeWire.object(NativeWire.parse(new byte[]{'{','}'}));
            byte[] statePayload=frame.get("state") instanceof ObjectNode?NativeWire.token(payload,"state"):new byte[]{'{','}'};
            return new SnapshotFields(field(payload,frame,"snapshot_id"),field(payload,frame,"revision"),field(statePayload,state,"date_raw"),field(statePayload,state,"speed"),field(statePayload,state,"paused"),field(statePayload,state,"map_ready"));
        }
    }
    public record RejectedSnapshot(ReceivedSnapshot original,String errorType,String error) {
        public RejectedSnapshot {Objects.requireNonNull(original);StrictJson.text(errorType);Objects.requireNonNull(error);}
    }
    /** The original Python endpoint records only these explicit Driver-adoption refusals. Generic I/O is separate. */
    public enum AdoptionRefusalReason {
        INVALID_DRIVER_JOURNAL("invalid_driver_journal"),ACTIVE_DRIVER_JOURNAL_REQUIRES_CONSOLIDATION("active_driver_journal_requires_consolidation"),
        LEGACY_LIFECYCLE_INCOMPATIBLE("legacy_lifecycle_incompatible"),PERSISTED_LIFECYCLE_MISMATCH("persisted_lifecycle_mismatch");
        private final String wire;AdoptionRefusalReason(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public record AdoptionRefusal(TransportSession session,NativeGameTransport.ReceivedHello originalHello,
            AdoptionRefusalReason reason,String exceptionType,String message) {
        public AdoptionRefusal {
            Objects.requireNonNull(session);Objects.requireNonNull(originalHello);Objects.requireNonNull(reason);StrictJson.text(exceptionType);Objects.requireNonNull(message);
            StrictJson.require(originalHello.original().pid()==session.game().pid()&&originalHello.original().connectionGeneration().equals(session.connectionGeneration()),"adoption refusal crossed actual original HELLO/session");
        }
        public String stage(){return "hello_adoption";}
    }
    public sealed interface AdoptionObservation permits Unobserved,Observed { }
    /** A missing actual adopter hook cannot be exported as a known null refusal. */
    public record Unobserved() implements AdoptionObservation { }
    public record Observed(Optional<AdoptionRefusal> refusal) implements AdoptionObservation {
        public Observed {Objects.requireNonNull(refusal);}
    }
    public record Production(UUID custodyEpoch,Optional<TransportSession> session,BigInteger receivedSnapshotCount,
            BigInteger rejectedSnapshotCount,Optional<RejectedSnapshot> lastRejectedSnapshot,
            BigInteger snapshotPublishDiagnosticCount,Optional<ReceivedSnapshot> lastReceivedSnapshot,AdoptionObservation adoption) {
        public Production {
            Objects.requireNonNull(custodyEpoch);Objects.requireNonNull(session);unsigned(receivedSnapshotCount);unsigned(rejectedSnapshotCount);unsigned(snapshotPublishDiagnosticCount);
            Objects.requireNonNull(lastRejectedSnapshot);Objects.requireNonNull(lastReceivedSnapshot);Objects.requireNonNull(adoption);
            StrictJson.require(rejectedSnapshotCount.compareTo(receivedSnapshotCount)<=0&&(rejectedSnapshotCount.signum()==0)==lastRejectedSnapshot.isEmpty(),"actual rejection count and original last rejection disagree");
            StrictJson.require((receivedSnapshotCount.signum()==0)==lastReceivedSnapshot.isEmpty(),"actual snapshot count and received original disagree");
            lastReceivedSnapshot.ifPresent(value->StrictJson.require(session.filter(value.session()::equals).isPresent()&&value.ordinal().equals(receivedSnapshotCount),"last raw snapshot differs from its actual receive/session"));
            lastRejectedSnapshot.ifPresent(value->StrictJson.require(session.filter(value.original().session()::equals).isPresent()&&value.original().ordinal().compareTo(receivedSnapshotCount)<=0,"rejection crossed actual received lifetime"));
            if(adoption instanceof Observed observed){StrictJson.require(session.isPresent(),"observed adoption requires its actual original HELLO session");observed.refusal().ifPresent(value->StrictJson.require(session.filter(value.session()::equals).isPresent(),"adoption refusal crossed held transport lifetime"));}
        }
    }
    static Optional<ObjectNode> snapshotObject(byte[] original)throws IOException {
        ObjectNode row=originalObject(original);JsonNode type=row.get("type");
        if(type==null||!type.isTextual()||!type.textValue().equals("state_snapshot"))return Optional.empty();
        NativeWire.integer(row.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);return Optional.of(row);
    }
    private static ObjectNode originalObject(byte[] original)throws IOException {
        StrictJson.require(original.length>=5&&original.length<=NativeWire.MAXIMUM_FRAME_BYTES+4,"bounded original diagnostic packet required");
        int length=ByteBuffer.wrap(original,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();StrictJson.require(length>0&&length==original.length-4,"original diagnostic packet length differs");
        return NativeWire.object(NativeWire.parse(Arrays.copyOfRange(original,4,original.length)));
    }
    private static NativeWire.Field field(byte[] original,ObjectNode row,String name)throws IOException {
        if(!row.has(name))return new NativeWire.Field(NativeWire.Presence.ABSENT,Optional.empty());JsonNode value=row.get(name);
        return new NativeWire.Field(value.isNull()?NativeWire.Presence.NULL:NativeWire.Presence.VALUE,Optional.of(new NativeWire.Bytes(NativeWire.token(original,name))));
    }
    private static void positive(BigInteger value){unsigned(value);StrictJson.require(value.signum()>0,"positive actual receive ordinal required");}
    private static void unsigned(BigInteger value){Objects.requireNonNull(value);StrictJson.require(value.signum()>=0&&value.compareTo(NativeWire.UINT64_MAX)<=0,"exact uint64 diagnostic counter required");}
}
