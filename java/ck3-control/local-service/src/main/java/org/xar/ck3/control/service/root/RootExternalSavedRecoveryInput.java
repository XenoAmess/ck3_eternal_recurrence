package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** External saved-game request. The physical read and original Writer still decide admission. */
record RootExternalSavedRecoveryInput(ExactRef departedOwner, GameGeneration departed,
        FileWitness namedSave, long dateRaw, NativeCharacterId player, Optional<Remount> remountFrom) {
    static final String MODE = "resume-external-saved";
    private static final String SCHEMA = "xar.root-external-saved-recovery/v1";
    private static final String REMOUNT_SCHEMA = "xar.root-external-saved-recovery/v2";
    record Remount(ExactRef owner, GameGeneration game) { }
    private static final int MAXIMUM_BYTES = 65536;

    RootExternalSavedRecoveryInput {
        Objects.requireNonNull(departedOwner);
        Objects.requireNonNull(departed);
        Objects.requireNonNull(namedSave);
        StrictJson.safe(dateRaw, 0);
        Objects.requireNonNull(player);
        Objects.requireNonNull(remountFrom);
    }

    static RootExternalSavedRecoveryInput read(String[] args) throws IOException {
        if (args.length != 6 || !MODE.equals(args[2]) || !args[4].matches("[1-9][0-9]{0,5}"))
            throw new IOException("external saved recovery requires its exact request path, bytes and SHA-256");
        var reference = new ExactRef(args[3], Long.parseLong(args[4]), args[5]);
        byte[] raw;
        try (var input = Files.newInputStream(Path.of(reference.path()))) {
            raw = input.readNBytes(MAXIMUM_BYTES + 1);
        }
        if (raw.length > MAXIMUM_BYTES || raw.length != reference.bytes() || !ActionCodec.sha256(raw).equals(reference.sha256()))
            throw new IOException("external saved recovery request differs from its exact original");
        var parsed = StrictJson.parse(raw, MAXIMUM_BYTES);
        var schema = StrictJson.text(parsed.get("schema"));
        boolean remount = REMOUNT_SCHEMA.equals(schema);
        StrictJson.require(remount || SCHEMA.equals(schema), "external saved recovery request schema");
        var fields = new java.util.HashSet<>(Set.of("schema", "departed_owner", "departed_game", "named_save", "date_raw", "played_character_id"));
        if (remount) fields.add("remount_from");
        var row = StrictJson.object(parsed, fields);
        Optional<Remount> from = Optional.empty();
        if (remount) {
            var exact = StrictJson.object(row.get("remount_from"), Set.of("owner", "game"));
            from = Optional.of(new Remount(ExactRef.fromJson(exact.get("owner")), GameGeneration.fromJson(exact.get("game"))));
        }
        return new RootExternalSavedRecoveryInput(ExactRef.fromJson(row.get("departed_owner")),
                GameGeneration.fromJson(row.get("departed_game")), CheckpointPairCodec.fileWitnessFromJson(row.get("named_save")),
                StrictJson.integer(row.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER),
                NativeCharacterId.fromJson(row.get("played_character_id")), from);
    }
}
