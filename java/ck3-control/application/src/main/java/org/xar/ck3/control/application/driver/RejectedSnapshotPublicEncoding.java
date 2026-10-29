package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Shared reversible raw diagnostics representation for rejected snapshots.
 * Operates only on OpportunityJson typed values; no Jackson or private admission.
 */
public final class RejectedSnapshotPublicEncoding {
    public static final String ENCODING_FIELD = "xar_public_rejected_revision_encoding";
    public static final String ENCODING_SCHEMA = "decimal-u64/v1";

    private RejectedSnapshotPublicEncoding() { }

    /**
     * Convert unsafe uint64 IntegerValue revision to canonical decimal Text and add schema marker.
     * Rejects any pre-existing ENCODING_FIELD in the rejected object.
     */
    public static OpportunityJson.Obj toPublic(OpportunityJson.Obj diagnostics) {
        Objects.requireNonNull(diagnostics);
        OpportunityJson.Value lastRejected = diagnostics.get("last_rejected_state_snapshot");
        if (!(lastRejected instanceof OpportunityJson.Obj)) {
            return diagnostics;
        }
        OpportunityJson.Obj rejected = (OpportunityJson.Obj) lastRejected;
        if (rejected.members().containsKey(ENCODING_FIELD)) {
            throw new IllegalArgumentException("pre-existing encoding field in rejected snapshot");
        }
        OpportunityJson.Value revisionValue = rejected.get("revision");
        if (revisionValue instanceof OpportunityJson.IntegerValue) {
            BigInteger revision = ((OpportunityJson.IntegerValue) revisionValue).value();
            if (revision.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) > 0
                    && revision.compareTo(StrictJson.UINT64_MAX) <= 0) {
                OpportunityJson.Obj updated = rejected.with("revision", new OpportunityJson.Text(revision.toString()));
                updated = updated.with(ENCODING_FIELD, new OpportunityJson.Text(ENCODING_SCHEMA));
                return diagnostics.with("last_rejected_state_snapshot", updated);
            }
        }
        return diagnostics;
    }

    /**
     * Restore canonical decimal Text revision to IntegerValue and remove schema marker.
     * Requires exact marker and valid uint64 range if marker is present.
     */
    public static OpportunityJson.Obj fromPublic(OpportunityJson.Obj diagnostics) {
        Objects.requireNonNull(diagnostics);
        OpportunityJson.Value lastRejected = diagnostics.get("last_rejected_state_snapshot");
        if (!(lastRejected instanceof OpportunityJson.Obj)) {
            return diagnostics;
        }
        OpportunityJson.Obj rejected = (OpportunityJson.Obj) lastRejected;
        OpportunityJson.Value marker = rejected.get(ENCODING_FIELD);
        if (!rejected.members().containsKey(ENCODING_FIELD)) {
            return diagnostics;
        }
        if (!(marker instanceof OpportunityJson.Text) || !((OpportunityJson.Text) marker).value().equals(ENCODING_SCHEMA)) {
            throw new IllegalArgumentException("invalid encoding marker");
        }
        OpportunityJson.Value revisionValue = rejected.get("revision");
        if (!(revisionValue instanceof OpportunityJson.Text)) {
            throw new IllegalArgumentException("revision must be text when marker present");
        }
        String revisionText = ((OpportunityJson.Text) revisionValue).value();
        if (!revisionText.matches("[1-9][0-9]{0,19}")) {
            throw new IllegalArgumentException("revision text not canonical decimal uint64");
        }
        BigInteger revision = new BigInteger(revisionText);
        if (revision.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0
                || revision.compareTo(StrictJson.UINT64_MAX) > 0) {
            throw new IllegalArgumentException("revision out of unsafe uint64 range");
        }
        Map<String, OpportunityJson.Value> members = new LinkedHashMap<>(rejected.members());
        members.remove(ENCODING_FIELD);
        members.put("revision", new OpportunityJson.IntegerValue(revision));
        OpportunityJson.Obj updatedRejected = new OpportunityJson.Obj(members);
        return diagnostics.with("last_rejected_state_snapshot", updatedRejected);
    }
}
