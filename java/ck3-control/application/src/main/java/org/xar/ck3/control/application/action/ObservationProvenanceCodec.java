package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
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
        StrictJson.require(kind.equals("push"), "known observation provenance kind required");
        var row = StrictJson.object(value, Set.of("kind", "snapshot_id", "native_revision", "original_packet"));
        String revision = StrictJson.text(row.get("native_revision"));
        StrictJson.require(revision.matches("0|[1-9][0-9]{0,999}"), "canonical bounded decimal native revision required");
        return new ObservationProvenance.Push(StrictJson.text(row.get("snapshot_id")), new BigInteger(revision), ExactRef.fromJson(row.get("original_packet")));
    }
}
