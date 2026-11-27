package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** The new process's first observation and the unchanged predecessor of a manually preserved campaign. */
public record ExternalSaveOrigin(long predecessorSequence, String predecessorDigest, SessionIdentity departed,
        SessionIdentity successor, CheckpointPair savedPair, CheckpointPair.FileWitness loadedFile,
        ExactRef retiredActionHead, NativeOpening opening, Optional<ExactRef> previousOrigin, Optional<String> deferredBatch) {
    static final String SCHEMA = "xar.java-ordinary-external-save-origin/v1";
    static final String REMOUNT_SCHEMA = "xar.java-ordinary-external-save-origin/v2";
    static final String REMOUNT_SOURCE = "java-external-save-observation/v2";
    static final String REMOUNT_TRANSITION = "external_save_observation_remount";

    public ExternalSaveOrigin(long predecessorSequence, String predecessorDigest, SessionIdentity departed,
            SessionIdentity successor, CheckpointPair savedPair, CheckpointPair.FileWitness loadedFile,
            ExactRef retiredActionHead, NativeOpening opening) {
        this(predecessorSequence, predecessorDigest, departed, successor, savedPair, loadedFile, retiredActionHead,
                opening, Optional.empty(), Optional.empty());
    }
    static final String SOURCE = "java-external-save-observation/v1";
    static final String TRANSITION = "external_save_observation_rebind";

    public ExternalSaveOrigin {
        StrictJson.safe(predecessorSequence, 1);
        WriterContracts.requireDigest(predecessorDigest);
        Objects.requireNonNull(departed);
        Objects.requireNonNull(successor);
        Objects.requireNonNull(savedPair);
        Objects.requireNonNull(loadedFile);
        Objects.requireNonNull(retiredActionHead);
        Objects.requireNonNull(opening);
        Objects.requireNonNull(previousOrigin);
        Objects.requireNonNull(deferredBatch);
        deferredBatch.ifPresent(StrictJson::text);
        StrictJson.require(deferredBatch.isEmpty() || previousOrigin.isPresent(), "only a named remount may defer an open batch");
        StrictJson.require(!successor.game().equals(departed.game())
                && !successor.game().equals(savedPair.frame().game())
                && successor.machineId().equals(departed.machineId())
                && successor.machineId().equals(savedPair.frame().machineId())
                && successor.machineId().equals(opening.session().machineId()) && successor.game().equals(opening.session().game())
                && successor.sessionId().equals(opening.session().sessionId()),
                "external save observation must belong to the replacement process on the original machine");
        StrictJson.require(loadedFile.reference().bytes() > 0 && !loadedFile.equals(savedPair.save())
                && !loadedFile.reference().sha256().equals(savedPair.save().reference().sha256())
                && opening.actor().value() == savedPair.frame().frame().identity().player().longValueExact()
                && opening.dateRaw() > savedPair.frame().frame().identity().dateRaw().longValueExact(),
                "external save observation requires the independently preserved later save of the same actor and episode");
    }

    /** Exact first available current Native frame, prior to Driver publication. */
    public record NativeOpening(TransportSession session, NativeCharacterId actor, long dateRaw,
            String snapshotId, BigInteger nativeRevision) {
        public NativeOpening {
            Objects.requireNonNull(session);
            Objects.requireNonNull(actor);
            StrictJson.safe(dateRaw, 0);
            StrictJson.text(snapshotId);
            StrictJson.require(nativeRevision != null && nativeRevision.signum() >= 0
                    && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "external save native revision range");
        }

        private ObjectNode toJson() {
            var row = StrictJson.object().put("machine_id", session.machineId()).put("session_id", session.sessionId())
                    .put("connection_generation", session.connectionGeneration().toString()).put("actor", actor.value())
                    .put("date_raw", dateRaw).put("snapshot_id", snapshotId).put("native_revision", nativeRevision.toString());
            row.set("game", session.game().toJson());
            return row;
        }

        private static NativeOpening fromJson(JsonNode value) {
            var row = StrictJson.object(value, Set.of("machine_id", "session_id", "connection_generation", "actor",
                    "date_raw", "snapshot_id", "native_revision", "game"));
            var session = new TransportSession(StrictJson.text(row.get("machine_id")), GameGeneration.fromJson(row.get("game")),
                    decimal(row.get("connection_generation")),
                    StrictJson.text(row.get("session_id")));
            return new NativeOpening(session, NativeCharacterId.fromJson(row.get("actor")),
                    StrictJson.integer(row.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(row.get("snapshot_id")),
                    decimal(row.get("native_revision")));
        }

        private static BigInteger decimal(JsonNode value) {
            return new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(value)).decimal());
        }
    }

    void requireSemantic(ObservationIdentity actual) {
        var identity = actual.frame().identity();
        StrictJson.require(successor.machineId().equals(actual.machineId()) && successor.game().equals(actual.game())
                && actual.frame().episodeRunId().equals(savedPair.frame().frame().episodeRunId())
                && identity.player().longValueExact() == opening.actor().value()
                && identity.dateRaw().longValueExact() == opening.dateRaw()
                && (identity.nativeRevision().compareTo(opening.nativeRevision()) > 0
                        || identity.nativeRevision().equals(opening.nativeRevision()) && actual.frame().snapshotId().equals(opening.snapshotId())),
                "external save Driver SEM changed the actual loaded actor, date, episode or native observation");
    }

    ObjectNode toJson() {
        var row = StrictJson.object().put("schema", previousOrigin.isPresent() ? REMOUNT_SCHEMA : SCHEMA).put("predecessor_sequence", predecessorSequence)
                .put("predecessor_digest", predecessorDigest);
        row.set("departed", OrdinaryCycleTransitions.sessionToJson(departed));
        row.set("successor", OrdinaryCycleTransitions.sessionToJson(successor));
        row.set("saved_pair", StrictJson.parse(CheckpointPairCodec.encode(savedPair)));
        row.set("loaded_file", CheckpointPairCodec.fileWitnessToJson(loadedFile));
        row.set("retired_action_head", retiredActionHead.toJson());
        row.set("opening", opening.toJson());
        previousOrigin.ifPresent(ref -> {
            row.set("previous_origin", ref.toJson());
            if (deferredBatch.isPresent()) row.put("deferred_batch", deferredBatch.orElseThrow());
            else row.putNull("deferred_batch");
        });
        return row;
    }

    public static ExternalSaveOrigin fromJson(JsonNode value) {
        var schema = StrictJson.text(value.get("schema"));
        boolean remount = REMOUNT_SCHEMA.equals(schema);
        StrictJson.require(remount || SCHEMA.equals(schema), "external save origin schema differs");
        var fields = new java.util.HashSet<>(Set.of("schema", "predecessor_sequence", "predecessor_digest", "departed",
                "successor", "saved_pair", "loaded_file", "retired_action_head", "opening"));
        if (remount) fields.addAll(Set.of("previous_origin", "deferred_batch"));
        var row = StrictJson.object(value, fields);
        return new ExternalSaveOrigin(StrictJson.integer(row.get("predecessor_sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(row.get("predecessor_digest")), OrdinaryCycleTransitions.sessionFromJson(row.get("departed")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("successor")),
                CheckpointPairCodec.decode(ContinuityJson.canonical(row.get("saved_pair"))),
                CheckpointPairCodec.fileWitnessFromJson(row.get("loaded_file")), ExactRef.fromJson(row.get("retired_action_head")),
                NativeOpening.fromJson(row.get("opening")),
                remount ? Optional.of(ExactRef.fromJson(row.get("previous_origin"))) : Optional.empty(),
                remount && !row.get("deferred_batch").isNull() ? Optional.of(StrictJson.text(row.get("deferred_batch"))) : Optional.empty());
    }

    /** The holder verifies the actual former ledger state. The observation grants no SAVE or dispatch authority. */
    public ContinuityState requireOriginal(ContinuityStorePort.Session same) throws IOException {
        var original = same.requireHistoricalState(predecessorSequence, predecessorDigest);
        requireOriginal(original);
        return original;
    }

    void requireOriginal(ContinuityState original) {
        var before = original.toJson();
        var imported = before.path(SavedContinuityBootstrap.FIELD);
        StrictJson.require(original.sequence() == predecessorSequence
                && ContinuityJson.digest(before).equals(predecessorDigest)
                && original.machineId().equals(departed.machineId())
                && original.status() == (previousOrigin.isPresent() ? ContinuityState.Status.RUNNING : ContinuityState.Status.REPAIR_REQUIRED)
                && ContinuityJson.same(before.get("game_binding"), departed.game().toJson())
                && ContinuityActionJournal.recordHead(original).filter(retiredActionHead::equals).isPresent()
                && imported.hasNonNull("checkpoint_pair")
                && ContinuityJson.same(imported.get("checkpoint_pair"), StrictJson.parse(CheckpointPairCodec.encode(savedPair)))
                && original.settledDateRaw() == savedPair.frame().frame().identity().dateRaw().longValueExact(),
                "external save origin changed the original retired owner or physical saved frontier");
        if (previousOrigin.isPresent()) {
            var binding = before.path("latest_binding");
            var boundary = before.path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
            boolean open = "BATCH_STARTED".equals(boundary.path("boundary").asText());
            StrictJson.require(ExactRef.fromJson(before.get(WriterContracts.ORDINARY_EXTERNAL_SAVE_ORIGIN_FIELD))
                    .equals(previousOrigin.orElseThrow()) && open == deferredBatch.isPresent()
                    && deferredBatch.map(batch -> batch.equals(boundary.path("batch_id").asText())
                            && departed.equals(OrdinaryCycleTransitions.sessionFromJson(boundary.get("session")))).orElse(true)
                    && binding.path("date_raw").longValue() == opening.dateRaw()
                    && NativeCharacterId.fromJson(binding.get("actor_character_id")).equals(opening.actor())
                    && binding.path("episode_run_id").asText().equals(savedPair.frame().frame().episodeRunId()),
                    "named remount must retain the actual previous named observation, owner and zero-action open batch");
        }
    }

    public void requirePreviousOrigin(ExternalSaveOrigin previous) {
        StrictJson.require(previousOrigin.isPresent() && previous.predecessorSequence() < predecessorSequence
                && previous.successor().equals(departed) && previous.savedPair().equals(savedPair)
                && previous.retiredActionHead().equals(retiredActionHead)
                && previous.loadedFile().reference().sha256().equals(loadedFile.reference().sha256())
                && previous.loadedFile().reference().bytes() == loadedFile.reference().bytes()
                && previous.opening().actor().equals(opening.actor()) && previous.opening().dateRaw() == opening.dateRaw(),
                "named remount must retain the same file bytes, date, actor, SAVE and original action frontier");
    }
}
