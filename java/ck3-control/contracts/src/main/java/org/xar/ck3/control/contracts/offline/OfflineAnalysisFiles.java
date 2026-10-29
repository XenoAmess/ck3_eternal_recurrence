package org.xar.ck3.control.contracts.offline;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;

/** Thread-confined storage routing for the existing offline producers, never a Game/action authority.
 * The worker binds the real Root storage/file producer for the whole original analysis transaction.
 * Unscoped legacy callers retain their existing writer; no child thread inherits this scope. */
public final class OfflineAnalysisFiles {
    private OfflineAnalysisFiles() { }
    public interface Port {
        void directories(Path actualDirectory) throws IOException;
        ExactRef createNew(Path target, byte[] completeBytes) throws IOException;
        ExactRef replace(Path target, byte[] completeBytes) throws IOException;
        void beforeLock(Path actualLock) throws IOException;
        void beforeLink(Path target, long originalBytes) throws IOException;
    }
    @FunctionalInterface public interface Work<T> { T run() throws IOException; }
    private static final ThreadLocal<Port> CURRENT = new ThreadLocal<>();
    public static Optional<Port> current() { return Optional.ofNullable(CURRENT.get()); }
    public static <T> T with(Port actual, Work<T> work) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(work);
        if (CURRENT.get() != null) throw new IOException("offline file scope cannot nest or replace its real storage owner");
        CURRENT.set(actual);
        try { return work.run(); } finally { CURRENT.remove(); }
    }
}
