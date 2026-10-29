package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeStorageGeometry;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Native metadata and original Guard path. The independent capacity card below is an explicit
 * software fixture, never production financial authority, a live producer qualification or Game admission. */
final class RootBootstrapIssuerCommandTest {
    @TempDir Path root;
    private record Scene(Path asset,Path control,Clock clock,String machine,String review,byte[] body,
            RootJavaBootstrapInputs.Request quoteRequest,
            RootProfileBootstrapCommand.IssuerPublication declaration,
            RootProfileBootstrapCommand.IssuerPublication census) {
        private Scene { body=body.clone(); }
        @Override public byte[] body(){return body.clone();}
    }

    @Test void actualQuoteNativeDeclarationCensusAndIndependentReleaseReachTheOriginalGuard()throws Exception {
        Scene scene=prepare();
        FileRef release=softwareRelease(scene);
        var request=new RootProfileBootstrapCommand.IssuerBindingRequest(
                "xar.java-root-bootstrap-issuer-binding-request/v1",scene.machine(),scene.review(),release,
                scene.control().resolve("binding.json").toString());
        var published=RootProfileBootstrapCommand.bindIssuedCapacity(request,scene.clock());
        assertEquals(RootBootstrapOutputGuard.Status.ADMITTED,published.actualAccounting().status());
        assertEquals(0,published.actualAccounting().completedOutputs());
        var original=scene.quoteRequest();
        var actualRequest=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,scene.machine(),scene.review(),
                RootJavaBootstrapInputs.Mode.CREATE_NEW,published.binding().original(),original.inputs());
        // Execute the original immutable publisher and its complete-plan/Native-readback checks, not a direct guard write.
        var created=RootJavaBootstrapInputs.prepare(actualRequest,scene.clock()).createNew(scene.clock());
        assertEquals(1,created.size());assertEquals(Kind.LIFE_SETTINGS,created.getFirst().kind());
        assertArrayEquals(scene.body(),Files.readAllBytes(Path.of(created.getFirst().original().path())));
        assertEquals(SharedSourceFiles.nativeFile(Path.of(created.getFirst().original().path())),created.getFirst().nativeFile());
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.bindIssuedCapacity(request,scene.clock()),
                "the helper must not overwrite or repeat an already completed immutable binding write");
    }

    @Test void changedActualCensusCannotGainBindingAdmissionAndTheFailedWriteIsRetained()throws Exception {
        Scene scene=prepare();FileRef release=softwareRelease(scene);
        write(scene.asset().resolve("unpriced.json"),new byte[]{'{','}'});
        Path target=scene.control().resolve("binding.json");
        var request=new RootProfileBootstrapCommand.IssuerBindingRequest(
                "xar.java-root-bootstrap-issuer-binding-request/v1",scene.machine(),scene.review(),release,target.toString());
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.bindIssuedCapacity(request,scene.clock()));
        assertTrue(Files.exists(target),"a real failed binding write remains evidence, without an admission result");
        var original=SharedSourceFiles.observe(target);
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.bindIssuedCapacity(request,scene.clock()));
        SharedSourceFiles.assertUnchanged(original);
    }

    private Scene prepare()throws Exception {
        Path asset=Files.createDirectory(root.resolve("asset")),control=Files.createDirectory(root.resolve("control"));
        Instant observed=Instant.now();Clock clock=Clock.fixed(observed,ZoneOffset.UTC);
        String machine=WindowsJobProcess.currentMachineId(),review=observed.plusSeconds(600).toString();
        byte[] body=RootAdvanceRuntimeFacts.Settings.encode(true,true,true).bytes();
        FileRef source=write(root.resolve("original-life-settings.json"),body);
        var request=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,machine,review,
                RootJavaBootstrapInputs.Mode.QUOTE,null,
                List.of(new RootJavaBootstrapInputs.Item(Kind.LIFE_SETTINGS,source,asset.resolve("life-settings.json").toString())));
        var outputs=RootJavaBootstrapInputs.prepare(request,clock).quote();
        assertEquals(1,outputs.size());assertEquals(Kind.LIFE_SETTINGS,outputs.getFirst().kind());
        // The exact plan comes from the original typed producer. This software scene does not qualify a live profile.
        var quote=new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","LIFE_SETTINGS",
                machine,review,asset.toString(),outputs,List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
        byte[] canonical=RootBootstrapProtocol.encode(quote,65536),line=Arrays.copyOf(canonical,canonical.length+1);line[line.length-1]='\n';
        FileRef quoteRef=write(root.resolve("actual-phase-quote.jsonl"),line);
        var declaration=RootProfileBootstrapCommand.declareOutput(new RootProfileBootstrapCommand.IssuerDeclarationRequest(
                "xar.java-root-bootstrap-issuer-declaration-request/v1",machine,review,"issuer-command-fixture",quoteRef,
                control.toString(),control.resolve("declaration.json").toString(),1536L*1024,512L*1024,1<<20,64),clock);
        assertEquals(NativeStorageGeometry.read(asset),declaration.assetGeometry());
        assertEquals(NativeStorageGeometry.read(control),declaration.controlGeometry());
        var typed=RootBootstrapOutputContract.decode(Files.readAllBytes(Path.of(declaration.declaration().original().path())),Declaration.class);
        assertEquals(SharedSourceFiles.nativeDirectory(asset),typed.assetDirectory());
        assertEquals(SharedSourceFiles.nativeDirectory(control),typed.controlDirectory());assertEquals(outputs,typed.outputs());
        var census=RootProfileBootstrapCommand.observeOutputCensus(new RootProfileBootstrapCommand.IssuerCensusRequest(
                "xar.java-root-bootstrap-issuer-census-request/v1",machine,review,declaration.declaration().original(),
                control.resolve("census.json").toString()),clock);
        var original=RootBootstrapOutputContract.decode(Files.readAllBytes(Path.of(census.original().path())),AssetCensus.class);
        assertTrue(original.entries().isEmpty());assertEquals(typed.assetDirectory(),original.assetDirectory());
        return new Scene(asset,control,clock,machine,review,body,request,declaration.declaration(),census);
    }

    private static FileRef softwareRelease(Scene scene)throws Exception {
        var policy=StrictJson.object().put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);
        rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));
        rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(scene.control().resolve("policy-fixture.json"),org.xar.ck3.control.build.ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=scene.asset().getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","software-fixture-actual-volume-observation")
                .put("machine_id",scene.machine()).put("total_bytes",total).put("usable_bytes",free)
                .put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(scene.control().resolve("financial-fixture.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,scene.machine(),"/root",ISSUER,"issuer-command-fixture",
                scene.clock().instant().toString(),scene.review(),policyRef,scene.declaration().original(),scene.census().original(),head,
                2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,scene.review(),usage,List.of(),0)),List.of());
        return write(scene.control().resolve("capacity-fixture.json"),RootBootstrapOutputContract.encode(release));
    }
    private static FileRef write(Path target,byte[] bytes)throws IOException {
        var files=new NativeCheckpointFiles();var actual=files.createNew(target,bytes);files.verify(actual);
        var ref=actual.reference();return new FileRef(ref.path(),ref.bytes(),ref.sha256());
    }
}
