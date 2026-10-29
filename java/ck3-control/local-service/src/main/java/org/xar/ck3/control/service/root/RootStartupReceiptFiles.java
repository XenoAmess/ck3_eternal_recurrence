package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Immutable Main receipts use the same original writer and finite runtime allocation authority as SAVE.
 * Retained startup configuration is read-only DATA; real output IO keeps its writer and storage checks. */
public final class RootStartupReceiptFiles {
    public static final int MAXIMUM_RECEIPT_BYTES=1<<20;
    private final RootApplicationConfiguration application;
    private final FileRef applicationRef;
    private final FileRef runtimeDefinitionsRef;
    private final RootCoreBoundPorts ports;
    private final RootRuntimeStorageGuard storage;
    private final CheckpointFiles files;
    private FileRef original;
    private RootStartupConfiguration startup;

    public RootStartupReceiptFiles(RootRuntimeDefinitions.Inputs inputs,RootCoreBoundPorts ports,
            RootRuntimeStorageGuard storage,CheckpointFiles files,Clock clock)throws IOException {
        this(Objects.requireNonNull(inputs).application(),inputs.configuration().applicationRef(),inputs.originalRef(),
                ports,storage,files,clock);
    }
    /** Both entry paths retain only the configuration values this receipt consumer actually uses. */
    RootStartupReceiptFiles(RootApplicationConfiguration application,FileRef applicationRef,FileRef runtimeDefinitionsRef,
            RootCoreBoundPorts ports,RootRuntimeStorageGuard storage,CheckpointFiles files,Clock clock)throws IOException {
        this.application=Objects.requireNonNull(application);this.applicationRef=Objects.requireNonNull(applicationRef);
        this.runtimeDefinitionsRef=Objects.requireNonNull(runtimeDefinitionsRef);this.ports=Objects.requireNonNull(ports);
        this.storage=Objects.requireNonNull(storage);this.files=Objects.requireNonNull(files);Objects.requireNonNull(clock);
        storage.requireFilePort(files);
    }
    public synchronized void bindStartup(FileRef actual)throws IOException {
        Objects.requireNonNull(actual);
        if(original!=null){
            if(!same(original,actual))throw new IOException("the exact CLI startup original cannot be replaced");
            requireCurrent();return;
        }
        var decoded=RootStartupConfiguration.readExact(actual);
        if(!decoded.machineId().equals(application.machineId())
                ||!same(decoded.application(),applicationRef)
                ||!same(decoded.runtimeDefinitions(),runtimeDefinitionsRef))
            throw new IOException("CLI startup does not bind these actual application/definitions/machine inputs");
        original=actual;startup=decoded;
    }
    public synchronized RootStartupConfiguration requireCurrent()throws IOException {
        if(original==null||startup==null)throw new IOException("the exact validated CLI startup original is not bound");
        storage.requireFilePort(files);return startup;
    }
    public void requireStartup(RootStartupConfiguration actual)throws IOException {
        if(!requireCurrent().equals(Objects.requireNonNull(actual)))
            throw new IOException("runtime finish attempted a different startup than the retained exact CLI input");
    }
    public void writeRuntimeReceipt(Path target,byte[] body)throws IOException {
        Objects.requireNonNull(target);Objects.requireNonNull(body);byte[] originalBody=body.clone();
        var actual=requireCurrent();
        if(!target.isAbsolute()||!target.normalize().equals(target)||!Objects.equals(target.getParent(),actual.receiptDirectory()))
            throw new IOException("Main receipt must be a direct immutable child of the exact startup receipt directory");
        var core=ports.requireCore();
        if(!core.configuration().equals(application)||core.archive().writer()!=core.writer())
            throw new IOException("Main receipt belongs to another original Core/writer/archive");
        core.writer().locked(same->{
            core.writer().requireSession(same);requireCurrent();
            writeExact(storage,files,same,target,originalBody);
            requireCurrent();core.writer().requireSession(same);return null;
        });
    }
    /** The production physical path is also exercised with a real temporary guarded root and writer in CI.
     * This narrow method grants neither startup identity nor any gameplay admission. */
    static FileWitness writeExact(RootRuntimeStorageGuard storage,CheckpointFiles files,
            ContinuityStorePort.Session same,Path target,byte[] body)throws IOException {
        Objects.requireNonNull(target);Objects.requireNonNull(body);
        if(body.length==0||body.length>MAXIMUM_RECEIPT_BYTES||!target.isAbsolute()||!target.normalize().equals(target))
            throw new IOException("finite immutable runtime receipt target/body required");
        storage.requireReadScope(same,files);storage.createManagedDirectories(target.getParent());
        storage.requireManagedRoots(java.util.List.of(target.getParent()));
        FileWitness actual=files.createNew(target,body);files.verify(actual);
        byte[] readback=files.read(actual,MAXIMUM_RECEIPT_BYTES);
        if(!Arrays.equals(body,readback)||!Path.of(actual.reference().path()).equals(target)
                ||actual.reference().bytes()!=body.length)
            throw new IOException("actual immutable Main receipt differs on physical readback");
        var nativeWitness=SharedSourceFiles.observe(target);
        if(!nativeWitness.source().path().equals(actual.reference().path())
                ||nativeWitness.source().bytes()!=actual.reference().bytes()
                ||!nativeWitness.source().sha256().equals(actual.reference().sha256()))
            throw new IOException("Main receipt native identity and bounded exact file witness disagree");
        SharedSourceFiles.assertUnchanged(nativeWitness);storage.requireReadScope(same,files);return actual;
    }
    private static boolean same(FileRef left,FileRef right){return Path.of(left.path()).equals(Path.of(right.path()))
            &&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
}
