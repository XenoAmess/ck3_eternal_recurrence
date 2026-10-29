package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Original CHECKPOINT producer fields. Decoding never observes a path or replaces its recorded file identity. */
record OpeningCheckpointInput(ExactRef request, SemanticEvidence semantic, CheckpointPair pair,
        ExactRef saveReceipt, SavedCheckpointMaterial.Kind materialKind, CheckpointPair.FileWitness savedMaterial, Optional<ExactRef> restorationBasis) {
    OpeningCheckpointInput {
        Objects.requireNonNull(request); Objects.requireNonNull(semantic); Objects.requireNonNull(pair);
        Objects.requireNonNull(saveReceipt); Objects.requireNonNull(materialKind); Objects.requireNonNull(savedMaterial); Objects.requireNonNull(restorationBasis);
        StrictJson.require(request.bytes() > 0 && saveReceipt.bytes() > 0 && savedMaterial.reference().bytes() > 0,
                "actual opening request, SAVE receipt and original saved material witness required");
        restorationBasis.ifPresent(value -> StrictJson.require(value.bytes() > 0, "actual restoration basis required"));
        var saved = pair.frame(); var current = semantic.frame();
        StrictJson.require(saved.machineId().equals(current.machineId())
                && saved.frame().episodeRunId().equals(current.frame().episodeRunId())
                && saved.frame().identity().player().equals(current.frame().identity().player())
                && saved.frame().identity().dateRaw().compareTo(current.frame().identity().dateRaw()) <= 0,
                "opening CHECKPOINT input crossed its actual machine/episode/actor or moved backwards");
    }

    ObjectNode toJson() {
        var row = StrictJson.object(); row.set("request", request.toJson()); row.set("semantic", semanticToJson(semantic));
        row.set("pair", StrictJson.parse(CheckpointPairCodec.encode(pair))); row.set("save_receipt", saveReceipt.toJson());
        row.put("saved_material_kind",materialKind.name());
        row.set("saved_material", CheckpointPairCodec.fileWitnessToJson(savedMaterial));
        row.set("restoration_basis", restorationBasis.map(ExactRef::toJson).orElse(null)); return row;
    }

    static OpeningCheckpointInput fromJson(JsonNode raw) {
        var row = StrictJson.object(raw, Set.of("request", "semantic", "pair", "save_receipt", "saved_material_kind", "saved_material", "restoration_basis"));
        return new OpeningCheckpointInput(ExactRef.fromJson(row.get("request")), semanticFromJson(row.get("semantic")),
                CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair"))), ExactRef.fromJson(row.get("save_receipt")),
                SavedCheckpointMaterial.Kind.valueOf(StrictJson.text(row.get("saved_material_kind"))),
                CheckpointPairCodec.fileWitnessFromJson(row.get("saved_material")), row.get("restoration_basis").isNull()
                ? Optional.empty() : Optional.of(ExactRef.fromJson(row.get("restoration_basis"))));
    }

    static ObjectNode semanticToJson(SemanticEvidence value) {
        var row = StrictJson.object(); row.set("frame", ProposalLifecycleCodec.observation(value.frame()));
        row.set("semantic", value.semantic().toJson()); row.set("native", value.originalNativePacket().toJson());
        row.set("stamp", value.driverStamp().toJson()); row.set("driver", value.originalDriver().toJson());
        row.put("observed_at", value.observedAt().toString()); return row;
    }

    static SemanticEvidence semanticFromJson(JsonNode raw) {
        var row = StrictJson.object(raw, Set.of("frame", "semantic", "native", "stamp", "driver", "observed_at"));
        return new SemanticEvidence(ProposalLifecycleCodec.decodeObservation(row.get("frame")), ExactRef.fromJson(row.get("semantic")),
                ExactRef.fromJson(row.get("native")), ExactRef.fromJson(row.get("stamp")), ExactRef.fromJson(row.get("driver")),
                Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at")))));
    }
}
