package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared strict JSON domain; native revisions cross JSON as canonical decimal strings. */
public final class ObservationProvenanceCodec {
    private ObservationProvenanceCodec() { }
    public static ObjectNode encode(ObservationProvenance value) {
        Objects.requireNonNull(value); ObjectNode row = StrictJson.object();
        if (value instanceof ObservationProvenance.Query query) {
            row.put("kind", "query"); row.put("request_id", query.requestId());
        } else if (value instanceof ObservationProvenance.FreshSnapshotQuery fresh) {
            row.put("kind", "fresh_snapshot_query"); row.put("request_id", fresh.requestId());
            row.set("read_acknowledgement", fresh.readAcknowledgement().toJson());
            var event = StrictJson.object(); event.put("order", fresh.snapshotReceived().order().toString()); event.put("observed_at_utc", fresh.snapshotReceived().observedAt().toString());
            row.set("snapshot_received", event);
            var basis = StrictJson.object();
            if (fresh.basis() instanceof ObservationProvenance.LiveAfterSetter live) {
                basis.put("kind", "live_after_setter"); basis.set("setter_acknowledgement", live.setterAcknowledgement().toJson());
            } else {
                var watch = (ObservationProvenance.SameGameWatch) fresh.basis();
                basis.put("kind", "same_game_watch"); basis.set("original_parent_receipt", watch.originalParentReceipt().toJson()); basis.set("original_resume_receipt", watch.originalResumeReceipt().toJson());
            }
            row.set("basis", basis);
        } else {
            var push = (ObservationProvenance.Push) value;
            row.put("kind", "push"); row.put("snapshot_id", push.snapshotId());
            row.put("native_revision", push.nativeRevision().toString()); row.set("original_packet", push.originalPacket().toJson());
        }
        return row;
    }
    public static ObservationProvenance decode(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "observation provenance object required");
        String kind = StrictJson.text(value.get("kind"));
        if (kind.equals("query")) {
            var row = StrictJson.object(value, Set.of("kind", "request_id"));
            return new ObservationProvenance.Query(StrictJson.text(row.get("request_id")));
        }
        if (kind.equals("fresh_snapshot_query")) {
            var row = StrictJson.object(value, Set.of("kind", "request_id", "read_acknowledgement", "snapshot_received", "basis"));
            var event = StrictJson.object(row.get("snapshot_received"), Set.of("order", "observed_at_utc"));
            StrictJson.require(row.get("basis") != null && row.get("basis").isObject(), "fresh snapshot basis object required");
            var basis = (ObjectNode) row.get("basis");
            String basisKind = StrictJson.text(basis.get("kind"));
            ObservationProvenance.FreshSnapshotBasis basisValue;
            if (basisKind.equals("live_after_setter")) {
                var live = StrictJson.object(basis, Set.of("kind", "setter_acknowledgement"));
                basisValue = new ObservationProvenance.LiveAfterSetter(ExactRef.fromJson(live.get("setter_acknowledgement")));
            } else {
                StrictJson.require(basisKind.equals("same_game_watch"), "known fresh snapshot basis kind required");
                var watch = StrictJson.object(basis, Set.of("kind", "original_parent_receipt", "original_resume_receipt"));
                basisValue = new ObservationProvenance.SameGameWatch(ExactRef.fromJson(watch.get("original_parent_receipt")), ExactRef.fromJson(watch.get("original_resume_receipt")));
            }
            String order = StrictJson.text(event.get("order"));
            StrictJson.require(order.matches("[1-9][0-9]{0,19}"), "canonical uint64 snapshot event order required");
            return new ObservationProvenance.FreshSnapshotQuery(StrictJson.text(row.get("request_id")), ExactRef.fromJson(row.get("read_acknowledgement")),
                    new NativeRequestChronology.Event(new BigInteger(order), Instant.parse(StrictJson.utc(StrictJson.text(event.get("observed_at_utc"))))), basisValue);
        }
        StrictJson.require(kind.equals("push"), "known observation provenance kind required");
        var row = StrictJson.object(value, Set.of("kind", "snapshot_id", "native_revision", "original_packet"));
        String revision = StrictJson.text(row.get("native_revision"));
        StrictJson.require(revision.matches("0|[1-9][0-9]{0,999}"), "canonical bounded decimal native revision required");
        return new ObservationProvenance.Push(StrictJson.text(row.get("snapshot_id")), new BigInteger(revision), ExactRef.fromJson(row.get("original_packet")));
    }
}
