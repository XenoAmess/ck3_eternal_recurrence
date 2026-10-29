package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.OptionalLong;

/**
 * Required allocation authority for the original writer and immutable archive.
 * Implementations admit real finite cards/native roots before the first physical mutation,
 * account actual native allocation themselves, and retain unresolved writes after failure.
 * This contract grants no Game, action, restoration or continuity-session authority.
 */
public interface StorageWriteGuard extends AutoCloseable {
    /** Sole allocation owner closes the real held storage scope, including constructor failure paths. */
    @Override void close()throws IOException;
    /** Allocation-only bootstrap admission; it must work before ContinuityWriter exists. */
    void requireInitialization(Path originalLock,List<Path> exactManagedRoots)throws IOException;
    /**
     * Maximum aggregate charged bytes enforced by this original-lock guard over managedDirectory.
     * Empty leaves the caller's own budget check unchanged. A present bound covers this directory
     * and every physical mutation must still use write(), including UNKNOWN retention.
     * This reports a configured enforced limit, not current usage or an external-writer inventory.
     */
    default OptionalLong enforcedAggregateMaximumBytes(Path originalLock,Path managedDirectory)throws IOException {
        return OptionalLong.empty();
    }
    /**
     * The complete physical plan is reserved before actualIO runs. Successful return includes
     * actual target/source/native-identity/accounting verification by the guard. Failure after
     * possible mutation retains UNKNOWN allocation; a callback result is not a settlement flag.
     * Nested calls from the same guard must use the retained parent reservation, not reserve twice.
     */
    <T> T write(WritePlan plan,PhysicalWrite<T> actualIO)throws IOException;
    @FunctionalInterface interface PhysicalWrite<T> { T run()throws IOException; }
    sealed interface Mutation permits FileCreate,FileFillExistingEmpty,FileRename,DirectoryCreate {
        Path target();
    }
    /** CREATE_NEW followed by bounded writes/force, including a deliberately empty metadata file. */
    record FileCreate(Path target,long maxLogicalBytes) implements Mutation {
        public FileCreate {target=absolute(target);bounded(maxLogicalBytes);}
    }
    /** The existing file must really be empty and retain its same original native FileID. */
    record FileFillExistingEmpty(Path target,long maxLogicalBytes) implements Mutation {
        public FileFillExistingEmpty {target=absolute(target);bounded(maxLogicalBytes);}
    }
    /**
     * Same-volume rename. No payload is free: the guard measures the actual source and carries
     * its native identity/allocation to the target; replace releases an old target only after
     * successful native accounting. Source and target must be distinct ordinary paths.
     */
    record FileRename(Path source,Path target,boolean replace) implements Mutation {
        public FileRename {
            source=absolute(source);target=absolute(target);
            if(source.equals(target)||!source.getParent().equals(target.getParent()))
                throw new IllegalArgumentException("same-parent distinct storage rename required");
        }
    }
    /** One ordinary directory; the guard applies its actual finite directory-allocation quote. */
    record DirectoryCreate(Path target) implements Mutation {
        public DirectoryCreate {target=absolute(target);}
    }
    record WritePlan(Path originalLock,List<Mutation> mutations) {
        public WritePlan {
            originalLock=absolute(originalLock);mutations=List.copyOf(mutations);
            if(mutations.isEmpty()||mutations.size()>2048)
                throw new IllegalArgumentException("complete bounded physical storage plan required");
            mutations.forEach(Objects::requireNonNull);
        }
    }
    private static Path absolute(Path path) {
        Objects.requireNonNull(path);
        if(!path.isAbsolute()||!path.normalize().equals(path)||path.getParent()==null)
            throw new IllegalArgumentException("absolute normalized ordinary storage path required");
        return path;
    }
    private static void bounded(long bytes) {
        if(bytes<0||bytes>WriterContracts.MAX_PIN_BYTES)
            throw new IllegalArgumentException("finite complete file logical-byte quote required");
    }
}
