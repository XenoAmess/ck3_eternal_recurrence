package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.DirectoryReadOnlyLease;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.ReadOnlyLease;

/** Real preparation-only source/clone handles. Close before Game CREATE; never carry into SDK SAVE. */
public final class QualifiedCloneCustody implements AutoCloseable {
    public static final int DEFAULT_MAXIMUM_FILE_BYTES=128<<20;
    private enum Phase { ACQUIRING, OPEN, FAILED, CLOSED }
    private final Thread owner=Thread.currentThread();
    private final NativeLaunchPlan plan;
    private final FileWitness original;
    private final Instant deadline;
    private final Clock clock;
    private final Path[] directories;
    private final DirectoryReadOnlyLease[] directoryLeases;
    private final ReadOnlyLease[] fileLeases=new ReadOnlyLease[2];
    private NativeSavedGameClone.Observation observation;
    private Phase phase=Phase.ACQUIRING;
    private Throwable closeFailure;
    private QualifiedCloneCustody(NativeLaunchPlan plan,FileWitness original,int maximumFileBytes,Instant deadline,Clock clock,Path[] directories) {
        this.plan=plan;this.original=original;this.deadline=deadline;this.clock=clock;
        this.directories=directories;this.directoryLeases=new DirectoryReadOnlyLease[directories.length];
    }
    public static QualifiedCloneCustody retain(NativeLaunchPlan plan,FileWitness original,int maximumFileBytes,
            Instant deadline,Clock clock)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(original);Objects.requireNonNull(deadline);Objects.requireNonNull(clock);
        if(maximumFileBytes<=0||maximumFileBytes==Integer.MAX_VALUE||original.reference().bytes()<=0||original.reference().bytes()>maximumFileBytes)
            throw new IOException("original SAVE exceeds finite single-file lease cap");
        if(deadline.equals(Instant.MAX)||deadline.isAfter(plan.deadline())||!clock.instant().isBefore(deadline))
            throw new IOException("finite original-plan bounded clone preparation deadline required");
        Path actual=NativeSavedGameClone.actualPath(plan),source=Path.of(original.reference().path());
        var saved=(NativeLaunchPlan.SavedGame)plan.load();
        if(!new ExactRef(saved.save().path(),saved.save().bytes(),saved.save().sha256()).equals(original.reference()))
            throw new IOException("clone custody source differs from the original plan SAVE");
        if(!source.isAbsolute()||!source.equals(source.normalize())||source.getParent()==null)throw new IOException("exact absolute original SAVE path required");
        var directories=new LinkedHashSet<Path>();directories.add(plan.profileDirectory());directories.add(actual.getParent());directories.add(source.getParent());
        QualifiedCloneCustody result=new QualifiedCloneCustody(plan,original,maximumFileBytes,deadline,clock,directories.toArray(Path[]::new));
        try {
            for(int index=0;index<result.directories.length;index++) {
                result.requireTime();
                result.directoryLeases[index]=IdentityBearingFileAttributes.leaseDirectoryWindows(result.directories[index]);
            }
            result.requireTime();result.fileLeases[0]=IdentityBearingFileAttributes.leaseBoundedWindows(source,maximumFileBytes);
            // Keep real handles/current qualification, retire full SAVE payload before acquiring the next file.
            result.fileLeases[0].releaseOriginalBytes();
            if(!source.equals(actual)) {
                result.requireTime();result.fileLeases[1]=IdentityBearingFileAttributes.leaseBoundedWindows(actual,maximumFileBytes);
                result.fileLeases[1].releaseOriginalBytes();
            }
            result.verifyHandles();result.observation=NativeSavedGameClone.observe(plan,original);
            result.phase=Phase.OPEN;result.requireCurrent(plan,original);return result;
        }catch(IOException|RuntimeException|Error problem) {
            result.phase=Phase.FAILED;
            try{result.close();}catch(IOException|RuntimeException|Error closing){if(problem!=closing)problem.addSuppressed(closing);}
            throw problem;
        }
    }
    /** Quote callers must obtain DATA through this still-held scope, then bind every quote/write callback to requireCurrent. */
    public NativeSavedGameClone.Observation observation()throws IOException {
        requireCurrent(plan,original);return observation;
    }
    public void requireCurrent(NativeLaunchPlan identicalPlan,FileWitness sameOriginal)throws IOException {
        if(Thread.currentThread()!=owner)throw new IOException("clone custody crossed its actual handle owner thread");
        if(phase!=Phase.OPEN)throw new IOException("clone preparation custody is not open");
        try {
            if(identicalPlan!=plan||!original.equals(sameOriginal))throw new IOException("clone custody crossed its original plan/source");
            requireTime();verifyHandles();observation.requireCurrent(plan,original);requireTime();
        }catch(IOException|RuntimeException|Error problem){phase=Phase.FAILED;throw problem;}
    }
    /** Final CREATE callback: verify the held identities, then synchronously release every file/directory handle. */
    public void releaseBeforeCreate(NativeLaunchPlan identicalPlan,FileWitness sameOriginal)throws IOException {
        try{requireCurrent(identicalPlan,sameOriginal);}
        catch(IOException|RuntimeException|Error problem) {
            try{close();}catch(IOException|RuntimeException|Error closing){if(problem!=closing)problem.addSuppressed(closing);}
            throw problem;
        }
        close();
    }
    private void requireTime()throws IOException {
        if(!clock.instant().isBefore(deadline))throw new IOException("original clone preparation deadline expired");
    }
    private void verifyHandles()throws IOException {
        for(DirectoryReadOnlyLease lease:directoryLeases) {
            if(lease==null)throw new IOException("ordinary directory handle acquisition incomplete");lease.verifyCurrent();
        }
        if(fileLeases[0]==null)throw new IOException("original SAVE read handle acquisition incomplete");
        fileLeases[0].verifyCurrent();if(fileLeases[1]!=null)fileLeases[1].verifyCurrent();
    }
    /** A failing close is a failing CREATE handoff. No release/adoption token is manufactured. */
    @Override public void close()throws IOException {
        if(Thread.currentThread()!=owner)throw new IOException("clone custody close crossed its actual handle owner thread");
        if(phase==Phase.CLOSED){
            // A fresh wrapper preserves failure without Java try-with-resources self-suppression.
            if(closeFailure!=null)throw new IOException("clone preparation release previously failed",closeFailure);
            return;
        }
        phase=Phase.CLOSED;Throwable failure=null;
        for(int index=fileLeases.length-1;index>=0;index--) {
            ReadOnlyLease lease=fileLeases[index];fileLeases[index]=null;
            if(lease!=null)try{lease.close();}catch(IOException|RuntimeException|Error closing){if(failure==null)failure=closing;else if(failure!=closing)failure.addSuppressed(closing);}
        }
        for(int index=directoryLeases.length-1;index>=0;index--) {
            DirectoryReadOnlyLease lease=directoryLeases[index];directoryLeases[index]=null;
            if(lease!=null)try{lease.close();}catch(IOException|RuntimeException|Error closing){if(failure==null)failure=closing;else if(failure!=closing)failure.addSuppressed(closing);}
        }
        closeFailure=failure;rethrowCloseFailure();
    }
    private void rethrowCloseFailure()throws IOException {
        if(closeFailure instanceof IOException problem)throw problem;
        if(closeFailure instanceof RuntimeException problem)throw problem;
        if(closeFailure instanceof Error problem)throw problem;
        if(closeFailure!=null)throw new IOException("clone preparation release remains unknown",closeFailure);
    }
}
