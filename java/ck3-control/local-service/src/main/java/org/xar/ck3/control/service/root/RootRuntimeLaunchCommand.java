package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.JavaRuntimeLaunch;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.contracts.StrictJson;

/** Real post-package command consumer. Only the sole Root launcher may independently admit/start its Job. */
public final class RootRuntimeLaunchCommand {
    private RootRuntimeLaunchCommand(){ }
    public enum Status { COMMAND_PREPARED_NO_JOB_ADMISSION }
    public record CommandData(String schema,String machineId,String observedAtUtc,Status status,
            FileRef packageManifest,FileRef invocation,WindowsJobProcess.CommandSpec command) {
        public CommandData {
            StrictJson.require("xar.java-root-runtime-launch-command/v1".equals(schema),"exact Root command DATA schema required");
            StrictJson.text(machineId);Instant at=Instant.parse(observedAtUtc);
            StrictJson.require(observedAtUtc.equals(at.toString()),"canonical command observation UTC required");
            Objects.requireNonNull(status);Objects.requireNonNull(packageManifest);Objects.requireNonNull(invocation);Objects.requireNonNull(command);
        }
    }
    /** Retains the actual private importer/launch custody for an in-process Root consumer. */
    public static JavaRuntimeLaunch.PreparedLaunch prepare(FileRef actualManifest,FileRef actualInvocation)throws IOException {
        var imported=JavaRuntimePackage.readAccepted(actualManifest,new RootPackageNativeVerifier());
        if(!(imported instanceof JavaRuntimePackage.PackageAvailable available)) {
            var unavailable=(JavaRuntimePackage.Unavailable)imported;
            throw new IOException("actual Root package unavailable at "+unavailable.stage()+": "+unavailable.reason());
        }
        var prepared=JavaRuntimeLaunch.prepareRoot(available.value(),actualInvocation);prepared.verifyCurrent();return prepared;
    }
    private static final class PreparedRoot implements org.xar.ck3.control.build.SharedOwnedCommand.RootPreparer {
        @Override public JavaRuntimeLaunch.PreparedLaunch prepare(
                org.xar.ck3.control.build.SharedOwnedCommand.PreparedRootInputs inputs)throws IOException {
            return RootRuntimeLaunchCommand.prepare(inputs.packageManifest(),inputs.invocation());
        }
    }
    public static org.xar.ck3.control.build.SharedOwnedCommand.Outcome runShared(FileRef exactInvocation)throws Exception {
        var invocation=org.xar.ck3.control.build.SourceGraphCommandSpecProducer.readRootInvocation(exactInvocation);
        var authority=org.xar.ck3.control.build.SourceGraphCommandSpecProducer.readRootAuthorization(invocation);
        org.xar.ck3.control.build.SourceGraphCommandSpecProducer.requireRootProvider(authority,
                org.xar.ck3.control.build.SourceGraphCommandSpecProducer.RootProvider.ROOT_LAUNCHER,RootRuntimeLaunchCommand.class);
        org.xar.ck3.control.build.SourceGraphCommandSpecProducer.requireRootProvider(authority,
                org.xar.ck3.control.build.SourceGraphCommandSpecProducer.RootProvider.NATIVE_VERIFIER,RootPackageNativeVerifier.class);
        return org.xar.ck3.control.build.SharedOwnedCommand.executePreparedRoot(exactInvocation,new PreparedRoot());
    }
    public static org.xar.ck3.control.build.SourceGraphCommandSpecProducer.RootLaunchData publishShared(
            FileRef entrySource,Path bindingDestination,Path specDestination,Path invocationDestination)throws Exception {
        var entry=org.xar.ck3.control.build.SourceGraphCommandSpecProducer.readRootEntryIntent(entrySource);
        var prepared=prepare(entry.preparedRoot().packageManifest(),entry.preparedRoot().invocation());
        var data=org.xar.ck3.control.build.SourceGraphCommandSpecProducer.publishRootInvocation(
                bindingDestination,specDestination,invocationDestination,entry,prepared);
        entrySource.verify();return data;
    }
    public static void main(String... args) {
        try {
            if(args.length==4 && args[0].equals("run-shared")) {
                var outcome=runShared(source(args,1));
                if(outcome.exitCode()!=0)System.exit(outcome.exitCode());
                return;
            }
            if(args.length==7 && args[0].equals("publish-shared")) {
                FileRef entrySource=source(args,1);
                var data=publishShared(entrySource,Path.of(args[4]),Path.of(args[5]),Path.of(args[6]));
                System.out.println(ControlBuild.strictMapper().writeValueAsString(data));return;
            }
            if(args.length!=9)throw new IOException("expected package-manifest exact3, Root-invocation exact3, stdout, stderr and canonical whole-JVM memory bytes");
            FileRef manifest=source(args,0),invocation=source(args,3);
            long memory=Long.parseLong(args[8]);
            if(memory<1||!Long.toString(memory).equals(args[8]))throw new IOException("canonical positive whole-JVM memory byte count required");
            var prepared=prepare(manifest,invocation);
            var command=prepared.command(Path.of(args[6]),Path.of(args[7]),memory);prepared.verifyCurrent();
            var data=new CommandData("xar.java-root-runtime-launch-command/v1",WindowsJobProcess.currentMachineId(),
                    Instant.now().toString(),Status.COMMAND_PREPARED_NO_JOB_ADMISSION,manifest,invocation,command);
            System.out.println(ControlBuild.strictMapper().writeValueAsString(data));
        }catch(Exception unavailable) {
            System.err.println("ROOT_LAUNCH_COMMAND_UNAVAILABLE: "+unavailable.getClass().getSimpleName()+": "+unavailable.getMessage());System.exit(2);
        }
    }
    private static FileRef source(String[] args,int offset)throws IOException {
        long bytes=Long.parseLong(args[offset+1]);
        if(bytes<1||!Long.toString(bytes).equals(args[offset+1]))throw new IOException("canonical positive exact-source byte count required");
        return new FileRef(args[offset],bytes,args[offset+2]);
    }
}
