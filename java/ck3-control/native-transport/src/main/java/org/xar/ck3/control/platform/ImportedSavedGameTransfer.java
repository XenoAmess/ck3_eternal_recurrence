package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ImportedSaveTransfer;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** The v5 exited restore's distinct source and in-profile CK3 load. */
public final class ImportedSavedGameTransfer {
    private static final String SCHEMA = "xar.java-imported-saved-transfer/v1";
    private static final int MAXIMUM_PROOF_BYTES = 32 * 1024;
    private static final Set<String> CLONE_FIELDS = Set.of("schema", "request_id", "session_id", "profile_directory",
            "profile_identity", "save_directory_identity", "original_save", "actual_save",
            "original_native_identity", "actual_native_identity", "in_place");

    private ImportedSavedGameTransfer() { }

    /** A per-parent slot distinct from the ordinary checkpoint output. */
    public static Path stagedPath(NativeLaunchPlan template, String parent) {
        String child = JavaGameLifecycle.replacementRequestId(parent);
        return template.profileDirectory().resolve("save games").resolve("xar_restore_" + child.substring("replacement-".length()) + ".ck3");
    }

    static Prepared prepare(NativeLaunchPlan template, String parent, GameGeneration departed, FileWitness original,
            CheckpointFiles files, Instant deadline, Clock clock) throws IOException {
        Path stagedPath = stagedPath(template, parent);
        Path futureSave = template.profileDirectory().resolve("save games/xar_checkpoint.ck3");
        if (stagedPath.equals(Path.of(original.reference().path())) || stagedPath.equals(futureSave))
            throw new IOException("Imported load must use its own per-parent load slot");
        var source = original.reference();
        var declared = new ControlBuild.FileRef(stagedPath.toString(), source.bytes(), source.sha256());
        var child = template.savedReplacement(parent, declared, deadline);
        var proofPath = stagedPath.resolveSibling(stagedPath.getFileName() + ".transfer.json");
        var prior = files.observe(proofPath);
        if (prior.isPresent()) {
            var witness = prior.orElseThrow();
            var existing = decodeOriginal(files.read(witness, MAXIMUM_PROOF_BYTES),witness.reference(),parent,departed,child);
            if (!original.equals(existing.original()))
                throw new IOException("Retained imported transfer belongs to another original SAVE");
            files.verify(existing.staged());
        }
        var observed = NativeSavedGamePreparation.prepareImported(child, original, files, clock);
        var staged = observed.actualSave();
        if (Files.exists(futureSave, LinkOption.NOFOLLOW_LINKS) && Files.isSameFile(futureSave,stagedPath))
            throw new IOException("Imported load aliases the ordinary checkpoint output");
        ObjectNode row = StrictJson.object().put("schema", SCHEMA).put("parent_request_id", parent)
                .put("machine_id", child.sources().review().machineId());
        row.set("departed_game", departed.toJson());
        row.set("clone", observed.toJson());
        byte[] bytes = StrictJson.canonical(row, MAXIMUM_PROOF_BYTES);
        var witness = prior.isPresent() ? prior.orElseThrow() : files.createNew(proofPath, bytes);
        if (!Arrays.equals(files.read(witness, MAXIMUM_PROOF_BYTES), bytes))
            throw new IOException("Original imported transfer proof changed or conflicts with this source/stage");
        var transfer = new ImportedSaveTransfer(original, staged, witness.reference());
        verifyOriginal(bytes, parent, departed, original, staged, child);

        var custody = QualifiedCloneCustody.retainImported(child, original, clock);
        boolean retained = false;
        try {
            if (!custody.observation().toJson().equals(observed.toJson()))
                throw new IOException("Prepared imported load changed before acquiring its CREATE handoff");
            var prepared = new Prepared(parent, departed, child, transfer, custody, files, witness);
            prepared.requireCurrent(parent, departed, child);
            retained = true;
            return prepared;
        } finally {
            if (!retained) custody.close();
        }
    }

    /** Replays immutable DATA. No current file, process, load or submission authority is inferred. */
    public static ImportedSaveTransfer decodeOriginal(byte[] bytes, ExactRef proof, String parent, GameGeneration departed,
            NativeLaunchPlan child) throws IOException {
        var clone = StrictJson.parse(bytes, MAXIMUM_PROOF_BYTES).get("clone");
        if (clone == null || !clone.isObject()) throw new IOException("Imported load clone original absent");
        var original = CheckpointPairCodec.fileWitnessFromJson(clone.get("original_save"));
        var staged = CheckpointPairCodec.fileWitnessFromJson(clone.get("actual_save"));
        if (bytes.length != proof.bytes() || !org.xar.ck3.control.application.action.ActionCodec.sha256(bytes).equals(proof.sha256()))
            throw new IOException("Imported load transfer differs from its exact archived proof");
        verifyOriginal(bytes, parent, departed, original, staged, child);
        return new ImportedSaveTransfer(original, staged, proof);
    }

    public static void verifyOriginal(byte[] bytes, String parent, GameGeneration departed, FileWitness original,
            FileWitness staged, NativeLaunchPlan child) throws IOException {
        try {
            var row = StrictJson.object(StrictJson.parse(bytes, MAXIMUM_PROOF_BYTES),
                    Set.of("schema", "parent_request_id", "machine_id", "departed_game", "clone"));
            var clone = StrictJson.object(row.get("clone"), CLONE_FIELDS);
            var sourceNative = nativeIdentity(clone.get("original_native_identity"));
            var targetNative = nativeIdentity(clone.get("actual_native_identity"));
            nativeIdentity(clone.get("profile_identity"));
            nativeIdentity(clone.get("save_directory_identity"));
            if (!SCHEMA.equals(StrictJson.text(row.get("schema")))
                    || !parent.equals(StrictJson.text(row.get("parent_request_id")))
                    || !child.sources().review().machineId().equals(StrictJson.text(row.get("machine_id")))
                    || !departed.equals(GameGeneration.fromJson(row.get("departed_game")))
                    || !NativeSavedGameClone.SCHEMA.equals(StrictJson.text(clone.get("schema")))
                    || !child.requestId().equals(JavaGameLifecycle.replacementRequestId(parent))
                    || !child.requestId().equals(StrictJson.text(clone.get("request_id")))
                    || !child.sessionId().equals(StrictJson.text(clone.get("session_id")))
                    || !child.profileDirectory().toString().equals(StrictJson.text(clone.get("profile_directory")))
                    || !clone.get("in_place").isBoolean() || clone.get("in_place").booleanValue()
                    || !original.equals(CheckpointPairCodec.fileWitnessFromJson(clone.get("original_save")))
                    || !staged.equals(CheckpointPairCodec.fileWitnessFromJson(clone.get("actual_save")))
                    || !stagedPath(child, parent).equals(Path.of(staged.reference().path()))
                    || !NativeSavedGameClone.actualPath(child).equals(Path.of(staged.reference().path()))
                    || !staged.reference().equals(LifecycleEvidence.exact(((NativeLaunchPlan.SavedGame)child.load()).save()))
                    || original.reference().path().equals(staged.reference().path())
                    || original.reference().bytes() != staged.reference().bytes()
                    || !original.reference().sha256().equals(staged.reference().sha256())
                    || !sourceNative.get("file_id_decimal").asText().equals(original.identity().fileId())
                    || !targetNative.get("file_id_decimal").asText().equals(staged.identity().fileId())
                    || sourceNative.get("volume_serial_decimal").equals(targetNative.get("volume_serial_decimal"))
                        && sourceNative.get("file_id_decimal").equals(targetNative.get("file_id_decimal")))
                throw new IOException("Imported transfer crossed its original file, stage, departed Game or exact child plan");
        } catch (IllegalArgumentException failure) {
            throw new IOException("Invalid original imported load transfer", failure);
        }
    }

    private static ObjectNode nativeIdentity(com.fasterxml.jackson.databind.JsonNode raw) {
        var row = StrictJson.object(raw, Set.of("volume_serial_decimal", "file_id_decimal", "creation_filetime_decimal"));
        for (var field : row.properties())
            StrictJson.require(StrictJson.text(field.getValue()).matches("0|[1-9][0-9]{0,19}"), "exact native decimal file identity");
        return row;
    }

    static final class Prepared implements AutoCloseable {
        private final String parent;
        private final GameGeneration departed;
        private final NativeLaunchPlan child;
        private final ImportedSaveTransfer transfer;
        private final QualifiedCloneCustody custody;
        private final CheckpointFiles files;
        private final FileWitness proof;
        private Prepared(String parent, GameGeneration departed, NativeLaunchPlan child, ImportedSaveTransfer transfer,
                QualifiedCloneCustody custody, CheckpointFiles files, FileWitness proof) {
            this.parent = parent;
            this.departed = departed;
            this.child = child;
            this.transfer = transfer;
            this.custody = custody;
            this.files = files;
            this.proof = proof;
        }
        NativeLaunchPlan child() { return child; }
        ImportedSaveTransfer transfer() { return transfer; }
        void requireCurrent(String actualParent, GameGeneration actualDeparted, NativeLaunchPlan actualChild) throws IOException {
            if (!parent.equals(actualParent) || !departed.equals(actualDeparted) || child != actualChild)
                throw new IOException("Imported load preparation belongs to another exited child");
            custody.requireCurrent(child, transfer.original());
            if (!custody.observation().actualSave().equals(transfer.staged()))
                throw new IOException("Imported load file identity changed before CREATE");
            files.verify(proof);
        }
        void releaseBeforeCreate() throws IOException {
            requireCurrent(parent, departed, child);
            custody.releaseBeforeCreate(child, transfer.original());
        }
        void requireLoadedFile() throws IOException {
            files.verify(transfer.staged());
        }
        @Override public void close() throws IOException { custody.close(); }
    }
}
