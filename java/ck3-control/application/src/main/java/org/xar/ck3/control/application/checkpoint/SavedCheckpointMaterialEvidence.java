package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Original capture DATA. Only a qualified canonical SAVE admission may publish this field.
 * Parsing or constructing this record grants no capture, restore, or current Game authority. */
public record SavedCheckpointMaterialEvidence(CheckpointPair pair, SessionIdentity source,
        CheckpointPair.FileWitness material, long originalHeadSequence, String originalHeadDigest,
        String checkpointDigest) {
    public static final String SCHEMA = "xar.java-saved-checkpoint-material-evidence/v1";
    public static final String FIELD = "java_ordinary_saved_material";
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> FIELDS = Set.of("schema", "pair", "source", "material_witness",
            "original_head_sequence", "original_head_digest", "checkpoint_digest");

    public SavedCheckpointMaterialEvidence {
        Objects.requireNonNull(pair); Objects.requireNonNull(source); Objects.requireNonNull(material);
        StrictJson.safe(originalHeadSequence, 0);
        WriterContracts.requireDigest(originalHeadDigest); WriterContracts.requireDigest(checkpointDigest);
        StrictJson.require(source.machineId().equals(pair.frame().machineId())
                && source.game().equals(pair.frame().game()), "saved material DATA crossed source machine or Game");
        StrictJson.require(material.reference().bytes() > 0 && Path.of(material.reference().path()).isAbsolute(),
                "saved material DATA requires an explicit original nonempty absolute manifest witness");
    }

    /** Extracts DATA from the actual store-issued material; no file is observed or qualified here. */
    public static SavedCheckpointMaterialEvidence fromMaterial(SavedAttachmentSourceStore.SavedMaterial actual) {
        Objects.requireNonNull(actual);
        return new SavedCheckpointMaterialEvidence(actual.pair(), actual.session(), actual.witness(),
                actual.originalHeadSequence(), actual.originalHeadDigest(), actual.checkpointDigest());
    }

    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.set("pair", StrictJson.parse(CheckpointPairCodec.encode(pair)));
        row.set("source", OrdinaryCycleTransitions.sessionToJson(source));
        row.set("material_witness", CheckpointPairCodec.fileWitnessToJson(material));
        row.put("original_head_sequence", originalHeadSequence); row.put("original_head_digest", originalHeadDigest);
        row.put("checkpoint_digest", checkpointDigest);
        ContinuityJson.canonical(row, MAX_BYTES); return row;
    }
    public byte[] encode() { return ContinuityJson.canonical(toJson(), MAX_BYTES); }
    public static SavedCheckpointMaterialEvidence decode(byte[] raw) {
        return decode(ContinuityJson.parseObject(raw, MAX_BYTES));
    }
    public static SavedCheckpointMaterialEvidence decode(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FIELDS, FIELDS);
        ContinuityJson.canonical(row, MAX_BYTES);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "saved material evidence schema");
        return new SavedCheckpointMaterialEvidence(
                CheckpointPairCodec.decode(ContinuityJson.canonical(row.get("pair"))),
                OrdinaryCycleTransitions.sessionFromJson(row.get("source")),
                CheckpointPairCodec.fileWitnessFromJson(row.get("material_witness")),
                StrictJson.integer(row.get("original_head_sequence"), 0, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(row.get("original_head_digest")), StrictJson.text(row.get("checkpoint_digest")));
    }
    /** Compares source DATA only; the caller must separately verify original files and canonical ancestry. */
    public void requireMaterial(SavedAttachmentSourceStore.SavedMaterial actual) {
        StrictJson.require(equals(fromMaterial(actual)), "canonical saved material evidence differs from original material");
    }
    public void requireSavedBranch(CheckpointPair exactPair, SessionIdentity exactSource) {
        StrictJson.require(pair.equals(exactPair) && source.equals(exactSource),
                "canonical saved material evidence crossed its exact saved pair or source");
    }
}
