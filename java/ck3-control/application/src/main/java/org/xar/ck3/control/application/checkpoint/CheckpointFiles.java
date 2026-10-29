package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;

/** Production file boundary. Probe means actual metadata/content, never an HTTP or launcher ACK. */
public interface CheckpointFiles {
    Optional<FileWitness> observe(Path path) throws IOException;
    byte[] read(FileWitness expected, int maximumBytes) throws IOException;
    FileWitness replace(Path target, byte[] completeBytes) throws IOException;
    /** Publishes a complete immutable file once. An existing target is never opened for writing. */
    FileWitness createNew(Path target, byte[] completeBytes) throws IOException;
    /** Immutable first-episode seed support. Refuses an existing target; caller owns the real storage reservation. */
    FileWitness copyNew(FileWitness source, Path target) throws IOException;
    default void verify(FileWitness expected) throws IOException {
        if (!observe(Path.of(expected.reference().path())).filter(expected::equals).isPresent()) throw new IOException("checkpoint file identity or bytes changed");
    }
    default void verify(CheckpointPair pair) throws IOException { verify(pair.save()); verify(pair.driver()); }
}
