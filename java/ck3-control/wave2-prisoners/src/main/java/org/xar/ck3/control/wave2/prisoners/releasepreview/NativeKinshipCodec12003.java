package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Exact codec for the actual schema-7 collection kinship consumer. */
public final class NativeKinshipCodec12003 {
    private static final Set<String> UNAVAILABLE = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "unavailable_reason");
    private static final Set<String> AVAILABLE = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "snapshot_id", "native_revision", "proof_epoch",
            "date_raw", "source_ordinal", "jailer_character_id", "prisoner_character_id",
            "is_close_family_of_played_character", "is_close_or_extended_family_of_played_character");

    private NativeKinshipCodec12003() { }

    public static NativeKinship12003 decode(byte[] raw, FrameBinding binding, BigInteger proofEpoch,
                                           int sourceOrdinal, int selectedOrdinal) {
        return fromNode(StrictJson.parse(raw), binding, proofEpoch, sourceOrdinal, selectedOrdinal);
    }

    public static NativeKinship12003 fromNode(JsonNode node, FrameBinding binding, BigInteger proofEpoch,
                                             int sourceOrdinal, int selectedOrdinal) {
        Objects.requireNonNull(binding, "binding");
        ReleasePreviewValues12003.unsigned64(proofEpoch, "kinship collection epoch");
        StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal <= 63
                && selectedOrdinal >= 0 && selectedOrdinal <= 63, "kinship collection ordinal outside 0..63");
        StrictJson.require(node != null && node.isObject(), "native kinship object required");
        StrictJson.trueValue(node.get("private_build"));
        StrictJson.trueValue(node.get("read_only"));
        StrictJson.require(!bool(node.get("advertised")) && !bool(node.get("action_surface_present")),
                "native kinship must remain private and read-only");
        String status = StrictJson.text(node.get("status"));
        if ("unavailable".equals(status)) {
            ObjectNode value = StrictJson.object(node, UNAVAILABLE);
            String reason = StrictJson.text(value.get("unavailable_reason"));
            StrictJson.require("not_evaluated".equals(reason) != (sourceOrdinal == selectedOrdinal),
                    "native kinship evaluated the wrong ordinal");
            return new NativeKinship12003.Unavailable(reason);
        }
        StrictJson.require("available".equals(status) && sourceOrdinal == selectedOrdinal,
                "native kinship available at wrong ordinal or status");
        ObjectNode value = StrictJson.object(node, AVAILABLE);
        StrictJson.require(binding.snapshotId().equals(StrictJson.text(value.get("snapshot_id")))
                && uint64(value.get("native_revision")).equals(binding.nativeRevision())
                && uint64(value.get("proof_epoch")).equals(proofEpoch), "native kinship frame differs");
        StrictJson.integer(value.get("date_raw"), binding.dateRaw(), binding.dateRaw());
        StrictJson.integer(value.get("source_ordinal"), sourceOrdinal, sourceOrdinal);
        StrictJson.integer(value.get("jailer_character_id"), binding.playerCharacterId(), binding.playerCharacterId());
        StrictJson.integer(value.get("prisoner_character_id"), binding.prisonerCharacterId(), binding.prisonerCharacterId());
        return new NativeKinship12003.Available(binding, proofEpoch, sourceOrdinal,
                bool(value.get("is_close_family_of_played_character")),
                bool(value.get("is_close_or_extended_family_of_played_character")));
    }

    public static byte[] encode(NativeKinship12003 kinship) {
        return StrictJson.canonical(toNode(kinship));
    }

    public static ObjectNode toNode(NativeKinship12003 kinship) {
        Objects.requireNonNull(kinship, "kinship");
        StrictJson.require(!(kinship instanceof NativeKinship12003.Missing),
                "missing schema field has no native leaf serialization");
        ObjectNode value = StrictJson.object();
        value.put("private_build", true);
        value.put("read_only", true);
        value.put("advertised", false);
        value.put("action_surface_present", false);
        if (kinship instanceof NativeKinship12003.Unavailable unavailable) {
            value.put("status", "unavailable");
            value.put("unavailable_reason", unavailable.reason());
            return value;
        }
        NativeKinship12003.Available available = (NativeKinship12003.Available) kinship;
        FrameBinding binding = available.binding();
        value.put("status", "available");
        value.put("snapshot_id", binding.snapshotId());
        value.put("native_revision", binding.nativeRevision());
        value.put("proof_epoch", available.proofEpoch());
        value.put("date_raw", binding.dateRaw());
        value.put("source_ordinal", available.sourceOrdinal());
        value.put("jailer_character_id", binding.playerCharacterId());
        value.put("prisoner_character_id", binding.prisonerCharacterId());
        value.put("is_close_family_of_played_character", available.closeFamily());
        value.put("is_close_or_extended_family_of_played_character", available.closeOrExtendedFamily());
        return value;
    }

    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual native kinship boolean required");
        return node.booleanValue();
    }
    private static BigInteger uint64(JsonNode node) {
        return StrictJson.integer(node, BigInteger.ONE, StrictJson.UINT64_MAX);
    }
}
