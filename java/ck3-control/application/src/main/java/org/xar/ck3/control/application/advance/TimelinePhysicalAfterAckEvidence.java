package org.xar.ck3.control.application.advance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.NativeRequestChronologyCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict DATA codec for the physical after-ACK occurrence. No native transport authority is granted. */
public final class TimelinePhysicalAfterAckEvidence {
    public static final String SCHEMA = "xar.java.timeline-physical-after-ack-occurrence/v1";
    private static final Set<String> FIELDS = Set.of("schema", "setter_chronology", "snapshot_id", "native_revision", "public_revision",
            "snapshot_received", "original_packet_identity", "native_packet", "setter_acknowledgement", "setter_receipt", "running_parent_receipt");

    public record Recorded(NativeRequestChronology setterChronology, String snapshotId, BigInteger nativeRevision, BigInteger publicRevision,
            NativeRequestChronology.Event snapshotReceived, NativeRequestChronology.PacketIdentity originalPacketIdentity,
            ExactRef nativePacket, ExactRef setterAcknowledgement, ExactRef setterReceipt, ExactRef runningParentReceipt) {
        public Recorded {
            Objects.requireNonNull(setterChronology); StrictJson.text(snapshotId);
            StrictJson.require(nativeRevision != null && nativeRevision.signum() >= 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "bounded uint64 native revision required");
            StrictJson.require(publicRevision != null && publicRevision.signum() >= 0 && publicRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "bounded uint64 public revision required");
            Objects.requireNonNull(snapshotReceived); Objects.requireNonNull(originalPacketIdentity);
            Objects.requireNonNull(nativePacket); Objects.requireNonNull(setterAcknowledgement); Objects.requireNonNull(setterReceipt); Objects.requireNonNull(runningParentReceipt);
            StrictJson.require(nativePacket.bytes() > 0 && setterAcknowledgement.bytes() > 0 && setterReceipt.bytes() > 0 && runningParentReceipt.bytes() > 0, "positive original evidence references required");
            StrictJson.require(snapshotReceived.order().compareTo(setterChronology.responseReceived().order()) > 0, "physical snapshot receive must follow setter ACK response");
            StrictJson.require(!snapshotReceived.observedAt().isBefore(setterChronology.responseReceived().observedAt()), "physical snapshot UTC must not regress");
            StrictJson.require(nativePacket.bytes() == originalPacketIdentity.bytes() && nativePacket.sha256().equals(originalPacketIdentity.sha256()), "native packet reference crossed original packet identity");
        }
    }

    public static RawJson encode(Recorded value) {
        Objects.requireNonNull(value);
        ObjectNode row = StrictJson.object();
        row.put("schema", SCHEMA);
        row.set("setter_chronology", NativeRequestChronologyCodec.encode(value.setterChronology()));
        row.put("snapshot_id", value.snapshotId());
        row.put("native_revision", value.nativeRevision().toString());
        row.put("public_revision", value.publicRevision().toString());
        var received = StrictJson.object();
        received.put("order", value.snapshotReceived().order().toString());
        received.put("observed_at", value.snapshotReceived().observedAt().toString());
        row.set("snapshot_received", received);
        var packet = StrictJson.object();
        packet.put("bytes", value.originalPacketIdentity().bytes());
        packet.put("sha256", value.originalPacketIdentity().sha256());
        row.set("original_packet_identity", packet);
        row.set("native_packet", value.nativePacket().toJson());
        row.set("setter_acknowledgement", value.setterAcknowledgement().toJson());
        row.set("setter_receipt", value.setterReceipt().toJson());
        row.set("running_parent_receipt", value.runningParentReceipt().toJson());
        return RawJson.fullMaterial(StrictJson.canonical(row));
    }

    public static Recorded decode(RawJson original) {
        Objects.requireNonNull(original);
        JsonNode value = StrictJson.parse(original.bytes());
        ObjectNode row = StrictJson.object(value, FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "timeline physical after-ack schema mismatch");
        var chronology = NativeRequestChronologyCodec.decode(row.get("setter_chronology"));
        var receivedNode = StrictJson.object(row.get("snapshot_received"), Set.of("order", "observed_at"));
        var order = StrictJson.text(receivedNode.get("order"));
        StrictJson.require(order.matches("[1-9][0-9]{0,19}"), "canonical uint64 snapshot event order required");
        var received = new NativeRequestChronology.Event(new BigInteger(order), Instant.parse(StrictJson.utc(StrictJson.text(receivedNode.get("observed_at")))));
        var packetNode = StrictJson.object(row.get("original_packet_identity"), Set.of("bytes", "sha256"));
        var packet = new NativeRequestChronology.PacketIdentity(StrictJson.integer(packetNode.get("bytes"), 1, RawJson.MAXIMUM_BYTES + 4L), StrictJson.text(packetNode.get("sha256")));
        return new Recorded(chronology, StrictJson.text(row.get("snapshot_id")),
                boundedDecimal(row.get("native_revision")), boundedDecimal(row.get("public_revision")),
                received, packet, ExactRef.fromJson(row.get("native_packet")),
                ExactRef.fromJson(row.get("setter_acknowledgement")), ExactRef.fromJson(row.get("setter_receipt")),
                ExactRef.fromJson(row.get("running_parent_receipt")));
    }

    public static ExactRef preserve(Recorded value, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(value); Objects.requireNonNull(archive);
        RawJson body = encode(value);
        ExactRef reference = archive.preserveMaterial(body);
        StrictJson.require(reference.bytes() == body.bytes().length && reference.sha256().equals(ActionCodec.sha256(body.bytes())),
                "actual timeline physical after-ack reference differs from preserved bytes");
        StrictJson.require(body.equals(archive.loadMaterial(reference)), "actual timeline physical after-ack archive changed");
        return reference;
    }

    private static BigInteger boundedDecimal(JsonNode value) {
        String encoded = StrictJson.text(value);
        StrictJson.require(encoded.matches("0|[1-9][0-9]{0,19}"), "canonical bounded uint64 decimal string required");
        BigInteger result = new BigInteger(encoded);
        StrictJson.require(result.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 decimal out of range");
        return result;
    }
}
