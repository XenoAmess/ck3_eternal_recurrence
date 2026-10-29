package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;

/** Adapter for the already real once-bound runtime guard; it never constructs another writer or storage authority. */
public final class RootRuntimeBootstrapInputFiles implements RootBootstrapInputFiles {
    private final RootRuntimeStorageGuard storage;
    private final CheckpointFiles identical;
    private final CheckpointFiles immutable=new ImmutableFiles();
    public RootRuntimeBootstrapInputFiles(RootRuntimeStorageGuard actual,CheckpointFiles sameGuardedFiles)throws IOException {
        storage=Objects.requireNonNull(actual);identical=Objects.requireNonNull(sameGuardedFiles);storage.requireFilePort(identical);
    }
    @Override public void requireTargets(List<Path> actualTargets)throws IOException {
        Objects.requireNonNull(actualTargets);storage.requireFilePort(identical);
        if(actualTargets.isEmpty()||actualTargets.size()>256||actualTargets.stream().distinct().count()!=actualTargets.size())
            throw new IOException("bounded distinct immutable input targets required");
        for(Path target:actualTargets)if(!target.isAbsolute()||!target.normalize().equals(target))throw new IOException("absolute normalized input target required");
        storage.requireManagedRoots(actualTargets.stream().map(Path::getParent).distinct().toList());
    }
    @Override public CheckpointFiles files(){return immutable;}
    private final class ImmutableFiles implements CheckpointFiles {
        @Override public Optional<FileWitness> observe(Path path)throws IOException{return identical.observe(path);}
        @Override public byte[] read(FileWitness original,int maximum)throws IOException{return identical.read(original,maximum);}
        @Override public FileWitness createNew(Path target,byte[] original)throws IOException {
            requireTargets(List.of(target));return identical.createNew(target,original);
        }
        @Override public FileWitness replace(Path target,byte[] original)throws IOException{throw new IOException("immutable bootstrap input cannot replace an original");}
        @Override public FileWitness copyNew(FileWitness original,Path target)throws IOException{
            requireTargets(List.of(target));return identical.copyNew(original,target);
        }
    }
}
