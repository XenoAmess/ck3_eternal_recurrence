package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Validated event envelope; constructing/validating it grants no commit or replay. */
public record ContinuityEvent(long sequence, String atUtc, String kind, byte[] details,
                              String identity, String previousSha256, ContinuityState after) {
    public ContinuityEvent {
        StrictJson.safe(sequence, 1); StrictJson.utc(atUtc); StrictJson.text(kind);
        details = ContinuityJson.canonical(ContinuityJson.parseObject(details, ContinuityJson.DOCUMENT_MAX_BYTES));
        org.xar.ck3.control.contracts.StrictJson.require(identity.matches("[0-9a-f]{64}")
                && previousSha256.matches("[0-9a-f]{64}"), "canonical continuity digests");
        java.util.Objects.requireNonNull(after);
    }
    @Override public byte[] details() { return details.clone(); }
    public static ContinuityEvent fromJson(ObjectNode value, ContinuityState previous) {
        ObjectNode row = StrictJson.object(value, Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        long sequence = ContinuityState.number(row, "sequence", 1);
        String kind = StrictJson.text(row.get("kind"));
        ObjectNode details = ContinuityJson.object(row.get("details"));
        StrictJson.text(details.get("evidence_id"));
        com.fasterxml.jackson.databind.JsonNode source = details.get("source");
        StrictJson.require(source != null && !source.isNull() && (!source.isContainerNode() || !source.isEmpty())
                && (!source.isTextual() || !source.textValue().isEmpty())
                && (!source.isBoolean() || source.booleanValue())
                && (!source.isNumber() || source.doubleValue() != 0), "event exact source");
        ObjectNode identityValue = StrictJson.object(); identityValue.put("kind", kind); identityValue.set("details", details);
        String identity = StrictJson.text(row.get("identity"));
        ContinuityState after = ContinuityState.fromJson(row.get("after"), previous.machineId());
        String predecessor = StrictJson.text(row.get("previous_sha256"));
        StrictJson.require(sequence == previous.sequence() + 1 && after.sequence() == sequence
                && predecessor.equals(ContinuityJson.digest(previous.toJson())), "continuity event gap or predecessor digest");
        StrictJson.require(identity.equals(ContinuityJson.digest(identityValue))
                && identity.equals(StrictJson.text(after.toJson().get("last_event_identity"))), "event changed identity/sequence");
        if(EpisodeWindow.isTransition(kind)) {
            EpisodeWindow.requireReduction(previous,after,new org.xar.ck3.control.continuity.writer.WriterContracts.Request(kind,ContinuityJson.canonical(details),java.util.List.of()),true);
        }else if(OriginalLegacyResume.KIND.equals(kind)) {
            // The full evidence closure is derived from this same strict typed descriptor.
            // Historical decoding grants no physical OriginalLoad/queue/adoption authority.
            OriginalLegacyResume.requireReduction(previous,after,OriginalLegacyResume.decode(details).request(),true);
        }else if(ObservedGameplayEntry.KIND.equals(kind)) {
            ObservedGameplayEntry.requireReduction(previous,after,
                    new org.xar.ck3.control.continuity.writer.WriterContracts.Request(kind,ContinuityJson.canonical(details),java.util.List.of()),true);
        }else if(org.xar.ck3.control.continuity.writer.WriterContracts.GAMEPLAY_ENTRY_KIND.equals(kind)) {
            org.xar.ck3.control.continuity.writer.WriterContracts.requireGameplayEntryReduction(previous,after,
                    new org.xar.ck3.control.continuity.writer.WriterContracts.Request(kind,ContinuityJson.canonical(details),java.util.List.of()),true);
        }else if(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_ACTION_HISTORY_KIND.equals(kind)) {
            org.xar.ck3.control.continuity.writer.WriterContracts.requireDriverActionHistoryReduction(previous,after,
                    new org.xar.ck3.control.continuity.writer.WriterContracts.Request(kind,ContinuityJson.canonical(details),java.util.List.of()),true);
        }else {
            StrictJson.require(java.util.Objects.equals(after.toJson().get(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_ACTION_HISTORY_FIELD),
                    previous.toJson().get(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_ACTION_HISTORY_FIELD)),
                    "unrelated event changed Driver action-history publication");
            StrictJson.require(java.util.Objects.equals(after.toJson().get(OriginalLegacyResume.STATE_FIELD),
                    previous.toJson().get(OriginalLegacyResume.STATE_FIELD)),"unrelated event changed original legacy resume");
            StrictJson.require(after.initializedOrigin().equals(previous.initializedOrigin())
                    && java.util.Objects.equals(after.toJson().get("schema"),previous.toJson().get("schema"))
                    && java.util.Objects.equals(after.toJson().get(EpisodeWindow.FIELD),previous.toJson().get(EpisodeWindow.FIELD))
                    && java.util.Objects.equals(after.toJson().get(FreshContinuityGenesis.FIELD),previous.toJson().get(FreshContinuityGenesis.FIELD)),
                    "only exact versioned BEGIN/BASELINE may change episode window/schema/origin");
        }
        return new ContinuityEvent(sequence, StrictJson.text(row.get("at_utc")), kind,
                ContinuityJson.canonical(details), identity, predecessor, after);
    }
    public String sourceKey() {
        ObjectNode value = StrictJson.object(); value.put("kind", kind);
        value.set("evidence_id", ContinuityJson.parseObject(details, ContinuityJson.DOCUMENT_MAX_BYTES).get("evidence_id"));
        return ContinuityJson.digest(value);
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object(); row.put("sequence", sequence); row.put("at_utc", atUtc);
        row.put("kind", kind); row.set("details", ContinuityJson.parseObject(details, ContinuityJson.DOCUMENT_MAX_BYTES));
        row.put("identity", identity); row.put("previous_sha256", previousSha256); row.set("after", after.toJson());
        return row;
    }
}
