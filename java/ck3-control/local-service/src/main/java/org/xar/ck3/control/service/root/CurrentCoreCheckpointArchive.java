package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.build.SharedSourceFiles;

/** Physical-file material only. Copying or observing a file does not mint a Native SAVE/business receipt. */
final class CurrentCoreCheckpointArchive {
    private CurrentCoreCheckpointArchive() { }
    record Material(FileWitness source,FileWitness archive) { }
    static Optional<FileWitness> preflight(CheckpointFiles files,Path checkpoint,Path archive,long maximumBytes,
            Optional<FileWitness> previousSource,Optional<FileWitness> previousArchive)throws IOException {
        Objects.requireNonNull(files);Objects.requireNonNull(previousSource);Objects.requireNonNull(previousArchive);
        if(!checkpoint.isAbsolute()||!archive.isAbsolute()||checkpoint.normalize().equals(archive.normalize())||maximumBytes<1)
            throw new IOException("Independent absolute checkpoint/archive and finite byte bound required");
        SharedSourceFiles.plainAncestors(checkpoint);SharedSourceFiles.plainAncestors(archive);
        if(Files.exists(archive,LinkOption.NOFOLLOW_LINKS))throw new IOException("New immutable checkpoint archive already exists");
        bounded(checkpoint,maximumBytes);Optional<FileWitness> baseline=files.observe(checkpoint);
        if(previousSource.isPresent()!=previousArchive.isPresent())throw new IOException("Previous source and immutable archive must be paired");
        if(previousSource.isEmpty()) {
            if(baseline.isPresent())throw new IOException("Existing fixed checkpoint cannot be overwritten without its original archived witness");
        } else {
            FileWitness source=previousSource.orElseThrow(),retained=previousArchive.orElseThrow();
            if(!Path.of(source.reference().path()).equals(checkpoint)||!baseline.filter(source::equals).isPresent()
                    ||source.reference().bytes()!=retained.reference().bytes()||!source.reference().sha256().equals(retained.reference().sha256())
                    ||source.identity().fileId().equals(retained.identity().fileId()))
                throw new IOException("Previous exact source and independent immutable archive required before another SAVE");
            files.verify(source);files.verify(retained);
        }
        return baseline;
    }
    static Material observeAndCopyChanged(CheckpointFiles files,Path checkpoint,Optional<FileWitness> baseline,Path archive,
            Instant deadline,long maximumBytes,int maximumObservations,long pollMillis)throws IOException,InterruptedException {
        if(maximumObservations<1||maximumObservations>64||pollMillis<100||pollMillis>5000)throw new IOException("Finite physical observation bounds required");
        IOException last=null;
        for(int count=0;count<maximumObservations;count++) {
            if(!Instant.now().isBefore(deadline))throw new IOException("Original physical checkpoint observation deadline expired",last);
            bounded(checkpoint,maximumBytes);
            Optional<FileWitness> current;
            try {current=files.observe(checkpoint);if(current.isPresent())files.verify(current.orElseThrow());}
            catch(IOException transientRead){last=transientRead;current=Optional.empty();}
            if(current.isPresent()&&current.orElseThrow().reference().bytes()>0
                    &&current.orElseThrow().reference().bytes()<=maximumBytes&&!baseline.filter(current.orElseThrow()::equals).isPresent()) {
                if(!Instant.now().isBefore(deadline))throw new IOException("Original archive deadline expired before copying");
                // Publication failure is never retried: a target may already have appeared and remains an original.
                FileWitness copy=files.copyNew(current.orElseThrow(),archive);files.verify(copy);files.verify(current.orElseThrow());
                return new Material(current.orElseThrow(),copy);
            }
            long remaining=java.time.Duration.between(Instant.now(),deadline).toMillis();
            if(remaining<=0)break;Thread.sleep(Math.min(pollMillis,remaining));
        }
        throw new IOException("No complete new/changed physical checkpoint observed; submitted is not SAVE confirmation",last);
    }
    private static void bounded(Path checkpoint,long maximumBytes)throws IOException {
        SharedSourceFiles.plainAncestors(checkpoint);
        if(Files.exists(checkpoint,LinkOption.NOFOLLOW_LINKS)
                &&(!Files.isRegularFile(checkpoint,LinkOption.NOFOLLOW_LINKS)||Files.size(checkpoint)>maximumBytes))
            throw new IOException("Checkpoint is not a bounded regular source file");
    }
}
