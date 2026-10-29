package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;

/** Shared full Driver producer. The state supplier owns the complete history; no test runner is imported. */
public final class DriverCheckpointStore {
    public static final int MAX_DRIVER_BYTES = 268_435_456;
    /** Must freeze the complete consolidated state under the same action/history authority. WAL fragments are not a snapshot. */
    public interface SnapshotSupplier {
        <T> T withFrozen(SnapshotWork<T> work) throws IOException;
    }
    @FunctionalInterface public interface SnapshotWork<T> { T run(DriverStateSnapshot frozen, CheckpointPublisher publisher) throws IOException; }
    /** Called before the same frozen state lease is released. No default empty implementation. */
    @FunctionalInterface public interface CheckpointPublisher { void publish(DriverStateSnapshot.Complete expected, DriverStateSnapshot.Complete published) throws IOException; }
    public record Anchor(FileWitness driver, long historyIndex) { }
    private final CheckpointFiles files; private final Path target; private final String pipeName; private final SnapshotSupplier snapshots;
    public DriverCheckpointStore(CheckpointFiles files, Path target, String pipeName, SnapshotSupplier snapshots) {
        this.files = Objects.requireNonNull(files); this.target = Objects.requireNonNull(target); StrictJson.text(pipeName); this.pipeName = pipeName; this.snapshots = Objects.requireNonNull(snapshots);
        StrictJson.require(target.isAbsolute(), "actual configured Driver path required");
    }
    public synchronized Anchor persist(String actionId, FileWitness save, ObservationIdentity frame, String lineageId) throws IOException {
        return snapshots.withFrozen((snapshot,publisher) -> persistFrozen(actionId,save,frame,lineageId,snapshot,publisher));
    }
    private Anchor persistFrozen(String actionId, FileWitness save, ObservationIdentity frame, String lineageId, DriverStateSnapshot snapshot, CheckpointPublisher publisher) throws IOException {
        if (!(snapshot instanceof DriverStateSnapshot.Complete complete)) throw new IOException("complete consolidated Driver snapshot unavailable: " + snapshot);
        ObjectNode document = parse(complete.encode()); validateIdentity(document, frame);
        ArrayNode history = history(document);
        // A retry may only re-read the already produced pair. It may never append the SAVE twice.
        ObjectNode last = document.get("last_checkpoint") instanceof ObjectNode value ? value : null;
        if (last != null && actionId.equals(textOrNull(last, "java_action_id"))) {
            long index = StrictJson.integer(last.get("history_index"), 1, StrictJson.MAX_SAFE_INTEGER);
            validateAnchor(document, save, frame, lineageId, actionId, index);
            FileWitness existing = files.observe(target).orElseThrow(() -> new IOException("published Driver missing"));
            validateAnchor(parse(files.read(existing, MAX_DRIVER_BYTES)), save, frame, lineageId, actionId, index);
            return new Anchor(existing, index);
        }
        long index = history.size() + 1L;
        ObjectNode checkpoint = StrictJson.object(); checkpoint.put("status", "saved"); checkpoint.put("name", "xar_checkpoint.ck3");
        checkpoint.put("path", save.reference().path()); checkpoint.put("size", save.reference().bytes()); checkpoint.put("sha256", save.reference().sha256());
        checkpoint.put("date_raw", frame.frame().identity().dateRaw()); checkpoint.put("history_index", index);
        checkpoint.put("episode_character_id", frame.frame().identity().player()); checkpoint.put("episode_run_id", frame.frame().episodeRunId());
        checkpoint.put("strategy", "native-autosave-command-v1"); checkpoint.put("java_action_id", actionId); checkpoint.put("save_lineage_id", lineageId);
        checkpoint.set("java_game_generation", frame.game().toJson());
        // Native campaign null is meaningful. A one-life binding is retained byte-semantically from the complete state.
        if (document.has("succession_lifecycle")) checkpoint.set("succession_lifecycle", document.get("succession_lifecycle").deepCopy());
        ObjectNode row = history.addObject(); row.put("index", index); row.put("command", "save-checkpoint"); row.put("ok", true);
        row.putObject("result").set("checkpoint", checkpoint.deepCopy()); document.set("last_checkpoint", checkpoint);
        // The original SAVE producer starts a new rollback scope at each new physical anchor.
        document.putNull("rollback_war_failure"); document.putArray("rollback_war_failures");
        validateAnchor(document, save, frame, lineageId, actionId, index); files.verify(save);
        byte[] encoded = FullJsonTree.encode(document,MAX_DRIVER_BYTES); if (encoded.length > MAX_DRIVER_BYTES) throw new IOException("complete Driver exceeds explicit limit");
        FileWitness witness = files.replace(target, encoded); files.verify(save);
        validateAnchor(parse(files.read(witness, MAX_DRIVER_BYTES)), save, frame, lineageId, actionId, index);
        publisher.publish(complete, DriverStateSnapshot.decodeComplete(encoded));
        return new Anchor(witness, index);
    }
    public void verify(CheckpointPair pair) throws IOException {
        files.verify(pair);
        StrictJson.require(files.observe(Path.of(pair.nativeAckRef().path())).map(FileWitness::reference).filter(pair.nativeAckRef()::equals).isPresent(), "original Native ACK evidence remains exact and available");
        validateAnchor(parse(files.read(pair.driver(), MAX_DRIVER_BYTES)), pair.save(), pair.frame(), pair.lineageId(), pair.saveActionId(), pair.historyIndex()); files.verify(pair);
    }
    /** The physical saved Driver is reread in full; an in-memory WAL tail cannot stand in for this source. */
    public DriverStateSnapshot.Complete readVerified(CheckpointPair pair) throws IOException {
        verify(pair);
        DriverStateSnapshot.Complete complete = DriverStateSnapshot.decodeComplete(files.read(pair.driver(), MAX_DRIVER_BYTES));
        verify(pair); return complete;
    }
    /** Consumer borrows the source's verified complete Driver session, including an earlier physical Game's pipe. */
    public DriverStateSnapshot.Complete readVerifiedOriginal(CheckpointPair pair,DriverStateSnapshot.Session expected)throws IOException {
        Objects.requireNonNull(expected);files.verify(pair);
        var ack=files.observe(Path.of(pair.nativeAckRef().path())).orElseThrow(()->new IOException("original SAVE ACK source unavailable"));
        StrictJson.require(ack.reference().equals(pair.nativeAckRef()),"original SAVE ACK differs");
        byte[] raw=files.read(pair.driver(),MAX_DRIVER_BYTES);var complete=DriverStateSnapshot.decodeComplete(raw);
        StrictJson.require(complete.session().equals(expected),"physical saved Driver differs from its actual verified source session");
        validateAnchor(parse(raw),pair.save(),pair.frame(),pair.lineageId(),pair.saveActionId(),pair.historyIndex(),expected.pipeName());
        files.verify(pair);return complete;
    }
    public void verifyOriginal(CheckpointPair pair,DriverStateSnapshot.Session expected)throws IOException {readVerifiedOriginal(pair,expected);}
    /** Original archived bytes and typed anchor only; this grants no present physical SAVE/reload qualification. */
    public DriverStateSnapshot.Complete readArchivedSnapshot(CheckpointPair pair,byte[] raw) throws IOException {
        Objects.requireNonNull(pair);Objects.requireNonNull(raw);
        StrictJson.require(raw.length==pair.driver().reference().bytes()
                &&sha256(raw).equals(pair.driver().reference().sha256()),"archived complete saved Driver differs from the original physical pair");
        var complete=DriverStateSnapshot.decodeComplete(raw);
        validateAnchor(parse(raw),pair.save(),pair.frame(),pair.lineageId(),pair.saveActionId(),pair.historyIndex(),complete.session().pipeName());
        return complete;
    }
    private void validateIdentity(ObjectNode document, ObservationIdentity frame) {validateIdentity(document,frame,pipeName);}
    private static void validateIdentity(ObjectNode document,ObservationIdentity frame,String expectedPipe) {
        StrictJson.require(StrictJson.integer(document.get("format_version"), 2, 2) == 2 && expectedPipe.equals(StrictJson.text(document.get("pipe_name"))), "complete v2 Driver for this pipe required");
        StrictJson.require(NativeCharacterId.fromJson(document.get("episode_character_id")).asBigInteger().equals(frame.frame().identity().player())
                && frame.frame().episodeRunId().equals(StrictJson.text(document.get("episode_run_id")))
                && StrictJson.integer(document.get("bridge_pid"), 1, 0xffff_ffffL) == frame.game().pid(), "current Driver episode and actual Game process identity");
        StrictJson.require(!document.hasNonNull("managed_restore_transaction"), "pending managed restore must be reconciled before SAVE");
        history(document);
    }
    private void validateAnchor(ObjectNode document, FileWitness save, ObservationIdentity frame, String lineage, String action, long index) {
        validateAnchor(document,save,frame,lineage,action,index,pipeName);
    }
    private static void validateAnchor(ObjectNode document,FileWitness save,ObservationIdentity frame,String lineage,String action,long index,String expectedPipe) {
        validateIdentity(document,frame,expectedPipe); ArrayNode history = history(document);
        StrictJson.require(index <= history.size(), "full original history includes SAVE anchor");
        ObjectNode checkpoint = object(document.get("last_checkpoint")); ObjectNode row = object(history.get(Math.toIntExact(index - 1)));
        ObjectNode saved = object(object(row.get("result")).get("checkpoint"));
        StrictJson.require(checkpoint.equals(saved) && "save-checkpoint".equals(StrictJson.text(row.get("command"))) && row.get("ok") != null && row.get("ok").isBoolean() && row.get("ok").booleanValue(), "real SAVE history row binds exact checkpoint");
        StrictJson.require(StrictJson.integer(checkpoint.get("history_index"), 1, StrictJson.MAX_SAFE_INTEGER) == index
                && StrictJson.integer(checkpoint.get("size"), 1, StrictJson.MAX_SAFE_INTEGER) == save.reference().bytes()
                && save.reference().sha256().equals(StrictJson.text(checkpoint.get("sha256")))
                && save.reference().path().equals(StrictJson.text(checkpoint.get("path")))
                && StrictJson.integer(checkpoint.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER) == frame.frame().identity().dateRaw().longValueExact()
                && NativeCharacterId.fromJson(checkpoint.get("episode_character_id")).asBigInteger().equals(frame.frame().identity().player())
                && frame.frame().episodeRunId().equals(StrictJson.text(checkpoint.get("episode_run_id")))
                && lineage.equals(StrictJson.text(checkpoint.get("save_lineage_id"))) && action.equals(StrictJson.text(checkpoint.get("java_action_id"))), "physical SAVE, Driver, date, actor, episode, lineage, action and history agree");
        StrictJson.require(document.has("succession_lifecycle") == checkpoint.has("succession_lifecycle")
                && Objects.equals(document.get("succession_lifecycle"), checkpoint.get("succession_lifecycle")), "missing/null lifecycle preserved and paired");
        StrictJson.require(org.xar.ck3.control.contracts.GameGeneration.fromJson(checkpoint.get("java_game_generation")).equals(frame.game()),
                "exact shared Game birth identity remains a decimal string");
    }
    private static ArrayNode history(ObjectNode root) {
        StrictJson.require(root.get("command_history") instanceof ArrayNode, "complete history array required"); ArrayNode rows = (ArrayNode) root.get("command_history");
        for (int i = 0; i < rows.size(); i++) StrictJson.require(StrictJson.integer(object(rows.get(i)).get("index"), 1, StrictJson.MAX_SAFE_INTEGER) == i + 1L, "complete ordered history, no gaps or boolean indices");
        return rows;
    }
    private static ObjectNode parse(byte[] raw) throws IOException {
        if (raw == null || raw.length == 0 || raw.length > MAX_DRIVER_BYTES) throw new IOException("bounded full Driver required");
        return object(FullJsonTree.parse(raw,MAX_DRIVER_BYTES));
    }
    private static ObjectNode object(JsonNode value) { StrictJson.require(value instanceof ObjectNode, "required Driver object, missing/null are distinct"); return (ObjectNode) value; }
    private static String textOrNull(ObjectNode value, String key) { return value.get(key) != null && value.get(key).isTextual() ? value.get(key).textValue() : null; }
    static String sha256(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
}
