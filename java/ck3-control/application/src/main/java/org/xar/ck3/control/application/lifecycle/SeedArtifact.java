package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Minted only by the real seed reader/freezer. Current checkpoint files are never accepted as seeds. */
public final class SeedArtifact {
    public static final String NAME = "xar_episode_seed.ck3";
    private final FileWitness save, metadata;
    private final BigInteger dateRaw, characterId;
    private final String sourceRunId;
    SeedArtifact(FileWitness save, FileWitness metadata, BigInteger dateRaw, BigInteger characterId, String sourceRunId) {
        this.save = Objects.requireNonNull(save); this.metadata = Objects.requireNonNull(metadata);
        this.dateRaw = Objects.requireNonNull(dateRaw); this.characterId = Objects.requireNonNull(characterId);
        NativeCharacterId.of(characterId);
        StrictJson.require(save.reference().bytes() > 0 && dateRaw.signum() >= 0, "actual nonempty seed and identity required");
        StrictJson.text(sourceRunId); this.sourceRunId = sourceRunId;
    }
    public FileWitness save() { return save; }
    public FileWitness metadata() { return metadata; }
    public BigInteger dateRaw() { return dateRaw; }
    public BigInteger characterId() { return characterId; }
    public String sourceRunId() { return sourceRunId; }
    public void requireCurrent(CheckpointFiles files) throws IOException {
        files.verify(save); files.verify(metadata);
        SeedArtifact current = SeedStore.decode(files, save, metadata);
        if (!dateRaw.equals(current.dateRaw) || !characterId.equals(current.characterId) || !sourceRunId.equals(current.sourceRunId))
            throw new IOException("immutable seed metadata changed");
    }
}
