package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Local-service seam into the existing Shared caller's read-only scope checks. This is not a financial issuer.
 * The original Shared process keeps its slot lock, hard Job, financial guard and deadline over this child. */
public final class RootBootstrapSessionScope implements WindowsJobProcess.StdioGuard {
    private final SharedOwnedCommandBinding binding;
    private final SharedOwnedCommand.Request request;
    private final SharedOwnedCommand.StandingPreflight standing;
    private final List<SharedSourceFiles.Witness> originals;
    private final Instant deadline;
    private RootBootstrapSessionScope(SharedOwnedCommandBinding binding,SharedOwnedCommand.Request request,
            SharedOwnedCommand.StandingPreflight standing,List<SharedSourceFiles.Witness> originals,Instant deadline){
        this.binding=binding;this.request=request;this.standing=standing;this.originals=List.copyOf(originals);this.deadline=deadline;
    }
    public static RootBootstrapSessionScope open(FileRef session,FileRef bindingRef,Path mechanicalSpec,
            Path controlRoot,Instant deadline,List<FileRef> requiredInputs,List<String> exactArguments,FileRef serviceBuild)throws Exception {
        var held=new ArrayList<SharedSourceFiles.Witness>();retain(bindingRef,held);
        SharedOwnedCommandBinding binding=SharedOwnedCommandBinding.read(bindingRef);
        FileRef spec=FileRef.measure(mechanicalSpec);retain(spec,held);
        var request=SharedOwnedCommand.parseRequest(read(spec,1<<20));
        retain(binding.standingRef(),held);retain(binding.deliveryRef(),held);retain(binding.launcherSourceRef(),held);
        var standingJson=read(binding.standingRef(),4<<20);
        var standing=SharedOwnedCommand.validateStanding(request,binding,standingJson);
        SharedOwnedCommandBinding.verifyAuthority(read(binding.deliveryRef(),4<<20),binding.deliveryExpectation(),binding.machineId());
        if(!binding.machineId().equals(WindowsJobProcess.currentMachineId())||!controlRoot.equals(request.outputRoot().resolve("session"))
                ||deadline.isAfter(standing.deadline())||!Instant.now().isBefore(deadline)
                ||java.time.Duration.between(Instant.now(),deadline).toSeconds()>request.timeoutSeconds()
                ||request.memoryLimitBytes()<(2L<<30)||request.javaInvocation()==null)
            throw new IOException("session requires the original finite 2GiB Shared child scope and its exact output subtree");
        var logical=CiBootstrap.JavaUtf8Invocation.read(request.javaInvocation().publication());
        if(!(logical.target() instanceof CiBootstrap.JavaUtf8Invocation.ClassTarget target)
                ||!target.mainClass().equals("org.xar.ck3.control.service.root.RootProfileBootstrapSession")
                ||!logical.arguments().equals(exactArguments))throw new IOException("original Shared envelope does not select this exact Session CLI");
        var service=ControlBuild.verifiedCompletedReceipt(serviceBuild);
        if(service.targetKind()!=ControlBuild.TargetKind.SERVICE_FAST_JAR)throw new IOException("qualified parent SERVICE required");
        var actualClasspath=new ArrayList<FileRef>();
        for(var entry:target.classpath()){
            if(!(entry instanceof CiBootstrap.JavaUtf8Invocation.JarClasspath jar))throw new IOException("parent must use exact qualified SERVICE archives, no raw classes");
            actualClasspath.add(new FileRef(jar.jar().path(),jar.jar().bytes(),jar.jar().sha256()));
        }
        var expectedClasspath=service.completeDeployment().stream().filter(r->r.path().endsWith(".jar")).toList();
        if(actualClasspath.size()!=expectedClasspath.size()||!java.util.Set.copyOf(actualClasspath).equals(java.util.Set.copyOf(expectedClasspath)))
            throw new IOException("parent envelope must retain all exact SERVICE archives in one defining class loader");
        // These are original Shared authority data, not an inferred ControlBuild closure in the SERVICE loader.
        for(String field:List.of("qualified_tools_ref","qualified_own_readback_ref","source_grant_ref","capacity_release_ref")){
            FileRef ref=ControlBuild.strictMapper().treeToValue(standingJson.get(field),FileRef.class);retain(ref,held);
        }
        var delivered=read(binding.deliveryRef(),4<<20);var runtime=new ArrayList<FileRef>();var deliveryRuntime=new ArrayList<FileRef>();
        for(var node:standingJson.path("runtime_closure")){FileRef ref=ControlBuild.strictMapper().treeToValue(node,FileRef.class);retain(ref,held);runtime.add(ref);}
        for(var node:delivered.path("complete_runtime"))deliveryRuntime.add(ControlBuild.strictMapper().treeToValue(node,FileRef.class));
        var toolsRef=ControlBuild.strictMapper().treeToValue(standingJson.get("qualified_tools_ref"),FileRef.class);
        var tools=ControlBuild.verifiedCompletedReceipt(toolsRef);
        if(runtime.size()!=6||!java.util.Set.copyOf(runtime).equals(java.util.Set.copyOf(deliveryRuntime))
                ||!java.util.Set.copyOf(runtime).equals(java.util.Set.copyOf(tools.completeDeployment()))
                ||!tools.sourcePins().contains(binding.launcherSourceRef()))throw new IOException("original Shared qualified Tools/source/delivery closure differs");
        var needed=new ArrayList<>(requiredInputs);needed.add(session);needed.add(bindingRef);
        for(FileRef ref:needed){if(!request.inputs().contains(ref))throw new IOException("Session input absent from actual Shared inputs: "+ref.path());retain(ref,held);}
        if(!Files.isDirectory(request.outputRoot()))throw new IOException("original Shared output must already exist before Session entry");
        SharedSourceFiles.plainAncestors(controlRoot);
        var result=new RootBootstrapSessionScope(binding,request,standing,held,deadline);result.verify();return result;
    }
    @Override public void verify()throws IOException {
        if(!Instant.now().isBefore(deadline))throw new IOException("original Session deadline expired");
        for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        long allocated=Math.addExact(SharedOwnedCommand.allocated(standing.primary().outputRoot()),
                SharedOwnedCommand.allocated(binding.privateTemporaryAggregateRoot().resolve(request.slotId().replace('/','_'))));
        if(allocated>standing.primary().outputCapBytes()-65536)throw new IOException("original Shared slot/native output cap exceeded");
    }
    /** Same mutable-output native accounting as the original Shared guard; never freeze growing stdio as an input. */
    public static long allocated(Path sessionRoot,Path target)throws IOException {
        sessionRoot=sessionRoot.toAbsolutePath().normalize();target=target.toAbsolutePath().normalize();
        if(!target.startsWith(sessionRoot))throw new IOException("mutable measurement outside exact Session subtree");
        return SharedOwnedCommand.allocated(target);
    }
    public record ChildCompletion(FileRef envelope,FileRef preparation,FileRef nativeEvidence,WindowsJobProcess.RetirementObservation retirement) {
        public ChildCompletion {java.util.Objects.requireNonNull(envelope);java.util.Objects.requireNonNull(preparation);java.util.Objects.requireNonNull(nativeEvidence);java.util.Objects.requireNonNull(retirement);}
    }
    /** Uses the existing sole Java envelope/loader and native source holds. It does not create a process or writer. */
    public static final class ChildLaunch implements AutoCloseable {
        private final CiBootstrap.JavaUtf8Invocation.Launch launch;
        private final JavaUtf8NativeCustody.Held sources;
        private final List<FileRef> inputs;
        private final Path sessionRoot;
        private final WindowsJobProcess.StdioGuard guard;
        private final long controlCap;
        private ChildLaunch(CiBootstrap.JavaUtf8Invocation.Launch launch,JavaUtf8NativeCustody.Held sources,List<FileRef> inputs,
                Path sessionRoot,WindowsJobProcess.StdioGuard guard,long controlCap){
            this.launch=launch;this.sources=sources;this.inputs=List.copyOf(inputs);this.sessionRoot=sessionRoot;this.guard=guard;this.controlCap=controlCap;
        }
        public List<String> arguments(){return launch.physicalArguments();}
        public List<FileRef> inputs(){return inputs;}
        public void requireCurrent()throws IOException {sources.requireCurrent();}
        public void attach(WindowsJobProcess.OwnedStdio original)throws IOException {sources.attach(original);}
        /** Native holds are composed with the original OwnedStdio retirement capability, not a data-shaped replacement. */
        public ChildCompletion completed(WindowsJobProcess.OwnedStdio original,WindowsJobProcess.AwaitResult terminal)throws IOException {
            if(!terminal.commandResult().identity().equals(original.identity()))throw new IOException("actual original child terminal required");
            try(var retired=original.observeRetiredCustody()){
                retired.requireCurrent();sources.requireCurrent();var observation=retired.observation();
                if(!observation.identity().equals(terminal.commandResult().identity())
                        ||!observation.sessionNonce().equals(original.sessionNonce()))throw new IOException("original retirement differs from actual pipe owner");
                var pin=CiBootstrap.JavaUtf8Invocation.captureFile(CiBootstrap.JavaUtf8Invocation.preparationPath(launch.logicalRequest()));
                CiBootstrap.JavaUtf8Invocation.inspectPreparation(pin,launch.publication());sources.requireCurrent();retired.requireCurrent();
                var nativeSources=sources.verifyTerminal(retired,terminal.commandResult());
                byte[] nativeBytes=JavaUtf8NativeCustody.encodeEvidence(nativeSources.evidence());guard.verify();
                if(Math.addExact(allocated(sessionRoot,sessionRoot),Math.addExact(nativeBytes.length+8192L,65536))>controlCap)
                    throw new IOException("actual native source evidence would consume the Session terminal reserve");
                Path evidence=Path.of(launch.logicalRequest().evidenceRoot().path()).resolve("native-sources.json");
                SharedSourceFiles.plainAncestors(evidence);Files.write(evidence,nativeBytes,java.nio.file.StandardOpenOption.CREATE_NEW);guard.verify();
                var envelope=launch.publication().envelope();
                return new ChildCompletion(new FileRef(envelope.path(),envelope.bytes(),envelope.sha256()),new FileRef(pin.path(),pin.bytes(),pin.sha256()),FileRef.measure(evidence),observation);
            }
        }
        @Override public void close()throws IOException {sources.close();}
    }
    public static ChildLaunch prepareChild(CiBootstrap.JavaUtf8Invocation.ClassTarget target,
            CiBootstrap.JavaUtf8Invocation.ClassCarrier carrier,List<String> startupOptions,List<String> arguments,
            Path sessionRoot,Path actualExecutable,WindowsJobProcess.StdioGuard guard,long controlCap)throws IOException {
        guard.verify();Path evidence=sessionRoot.resolve("child-engine");
        if(Math.addExact(allocated(sessionRoot,sessionRoot),69632)>controlCap)throw new IOException("child engine directory would consume the terminal reserve");
        SharedSourceFiles.plainAncestors(evidence);Files.createDirectory(evidence);
        var directory=CiBootstrap.JavaUtf8Invocation.captureOutputRoot(evidence);
        var request=new CiBootstrap.JavaUtf8Invocation.Request(target,List.of(),arguments,directory);
        var publication=CiBootstrap.JavaUtf8Invocation.publish(request,directory,"child-invocation.bin",pending->{
            guard.verify();if(Math.addExact(allocated(sessionRoot,sessionRoot),Math.addExact(pending,65536))>controlCap)throw new IOException("sole Java engine would consume the Session terminal reserve");
        });
        var launch=CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,startupOptions);
        var snapshot=CiBootstrap.JavaUtf8Invocation.inputSnapshot(launch,carrier);var inputs=new ArrayList<FileRef>();
        for(var file:snapshot.files())inputs.add(new FileRef(file.path(),file.bytes(),file.sha256()));
        var held=JavaUtf8NativeCustody.acquire(launch,carrier);
        try{
            guard.verify();held.requireCurrent();
            long additional=Math.addExact(held.maximumEvidenceBytes(actualExecutable),Math.addExact(CiBootstrap.JavaUtf8Invocation.maximumOutputBytes(request),81920));
            if(Math.addExact(allocated(sessionRoot,sessionRoot),additional)>controlCap)throw new IOException("complete Java preparation and native source evidence exceed Session control quote before launch");
            return new ChildLaunch(launch,held,inputs,sessionRoot,guard,controlCap);
        }
        catch(IOException|RuntimeException failure){try{held.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    public static JavaUtf8NativeCustody.Evidence verifyChildCompletion(ChildCompletion completion,CiBootstrap.JavaUtf8Invocation.ClassCarrier carrier)throws IOException {
        completion.envelope().verify();completion.preparation().verify();completion.nativeEvidence().verify();
        var publication=new CiBootstrap.JavaUtf8Invocation.Publication(CiBootstrap.JavaUtf8Invocation.captureFile(Path.of(completion.envelope().path())));
        CiBootstrap.JavaUtf8Invocation.inspectPreparation(CiBootstrap.JavaUtf8Invocation.captureFile(Path.of(completion.preparation().path())),publication);
        if(completion.nativeEvidence().bytes()>JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES)throw new IOException("bounded actual native evidence required");
        var nativeEvidence=JavaUtf8NativeCustody.decodeEvidence(Files.readAllBytes(Path.of(completion.nativeEvidence().path())));
        JavaUtf8NativeCustody.requireCurrent(nativeEvidence,CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,List.of()),carrier);
        if(!nativeEvidence.identity().equals(completion.retirement().identity())
                ||Integer.toUnsignedLong(nativeEvidence.terminal().exitCode())!=completion.retirement().exitCode()
                ||!nativeEvidence.terminal().accounting().equals(completion.retirement().accounting()))throw new IOException("native evidence differs from original duplex retirement");
        completion.nativeEvidence().verify();return nativeEvidence;
    }
    private static void retain(FileRef ref,List<SharedSourceFiles.Witness> held)throws IOException {
        var witness=SharedSourceFiles.observe(Path.of(ref.path()));if(!witness.source().equals(ref))throw new IOException("original Shared input drift");held.add(witness);
    }
    private static com.fasterxml.jackson.databind.JsonNode read(FileRef ref,int maximum)throws IOException {
        if(ref.bytes()<1||ref.bytes()>maximum)throw new IOException("bounded Shared original required");ref.verify();
        return ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(ref.path())));
    }
}
