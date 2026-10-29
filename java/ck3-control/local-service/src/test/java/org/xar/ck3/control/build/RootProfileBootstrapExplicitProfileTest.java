package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.NativeRunProfileManifest.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootBootstrapOutputGuard;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs;

/** Same physical production derivation and admitted writer, using owned software DATA; no qualified runtime or Game is minted. */
final class RootProfileBootstrapExplicitProfileTest {
    @TempDir Path root;
    private record Fixture(ExplicitRequest request,FileRef requestOriginal,List<FileRef> runtime,Path outputRoot) { }
    @Test void savedAndFixturePhysicalProducerReachOneEnvWriteAndTheSoleEnvironmentCodec()throws Exception {
        for(boolean fixtureDomain:List.of(false,true)){
            var fixture=fixture(fixtureDomain);Clock clock=Clock.fixed(Instant.now(),ZoneOffset.UTC);
            var actual=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
            Path target=fixture.outputRoot().resolve(NativeRunProfileProducer.ENVIRONMENT_NAME);
            var prepared=RootProfileBootstrapInputs.explicitEnvironment(actual,fixture.requestOriginal(),target,clock);
            var expected=NativeRunProfileProducer.finishExplicit(actual,clock);
            byte[] bytes=encodeEnvironment(expected);
            assertEquals(1,prepared.quote().size());assertEquals(Kind.PROFILE_ENVIRONMENT,prepared.quote().getFirst().kind());
            assertEquals(bytes.length,prepared.quote().getFirst().bytes());
            assertEquals(org.xar.ck3.control.application.driver.DriverJson.sha256(bytes),prepared.quote().getFirst().sha256());
            assertTrue(prepared.retainedInputs().isEmpty());assertTrue(prepared.outputDirectories().isEmpty());
            assertNotEquals(actual.request().profile(),prepared.assetRoot());
            try(var authority=authority(prepared,clock)){
                var created=prepared.createNew(authority).getFirst();
                assertEquals(target.toString(),created.original().path());assertArrayEquals(bytes,Files.readAllBytes(target));
                assertEquals(expected,readEnvironmentOriginal(created.original()));assertEquals(expected,decodeEnvironment(bytes));
                assertEquals(1,authority.accounting().completedOutputs());
                assertThrows(IOException.class,()->prepared.createNew(authority));
                // This software fixture never qualifies the public completed-build boundary.
                assertThrows(IOException.class,()->NativeRunProfileProducer.readEnvironmentVerified(created.original()));
            }
            actual.verifyOriginals();assertFalse(Files.exists(actual.request().profile().resolve(NativeRunProfileProducer.ENVIRONMENT_NAME)));
            assertEquals(fixtureDomain?ProfileKind.FRESH_FRONTEND_FIXTURE:ProfileKind.SAVED_VANILLA,expected.kind());
            assertEquals(List.of("dlc_second","dlc_first"),expected.profile().loadProfile().declaredDlc().disabledDlcs());
        }
    }
    @Test void sameBytesProducerRequestReplacementAndActualProductDriftFailBeforeTheOriginalWriter()throws Exception {
        for(boolean replaceRequest:List.of(false,true)){
            var fixture=fixture(true);Clock clock=Clock.fixed(Instant.now(),ZoneOffset.UTC);
            var actual=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
            var prepared=RootProfileBootstrapInputs.explicitEnvironment(actual,fixture.requestOriginal(),
                    fixture.outputRoot().resolve(NativeRunProfileProducer.ENVIRONMENT_NAME),clock);
            try(var authority=authority(prepared,clock)){
                if(replaceRequest){
                    Path source=Path.of(fixture.requestOriginal().path());byte[] original=Files.readAllBytes(source);
                    Files.move(source,source.resolveSibling("preserved-explicit-request.json"));write(source,original);
                }else Files.writeString(Path.of(actual.productionRoots().getFirst()).resolve("script.txt"),"changed actual source");
                assertThrows(IOException.class,()->prepared.createNew(authority));
                assertFalse(Files.exists(fixture.outputRoot().resolve(NativeRunProfileProducer.ENVIRONMENT_NAME)));
                assertEquals(0,authority.accounting().completedOutputs());
            }
        }
    }
    @Test void profileOrProductOutputOverlapIsRejectedWithoutWritingOrManufacturingPreparedInputs()throws Exception {
        var fixture=fixture(true);var actual=NativeRunProfileProducer.deriveExplicit(fixture.request(),fixture.runtime());
        for(Path output:List.of(actual.request().profile(),actual.request().profile().getParent(),Path.of(actual.productionRoots().getFirst())))
            assertThrows(IOException.class,()->RootProfileBootstrapInputs.explicitEnvironment(actual,fixture.requestOriginal(),
                    output.resolve(NativeRunProfileProducer.ENVIRONMENT_NAME),Clock.systemUTC()));
        assertThrows(IOException.class,()->NativeRunProfileProducer.prepareFixture(fixture.request(),Clock.systemUTC()));
        assertFalse(Files.exists(fixture.outputRoot().resolve(NativeRunProfileProducer.ENVIRONMENT_NAME)));
    }
    private Fixture fixture(boolean fixtureDomain)throws Exception {
        Path base=Files.createTempDirectory(root,"profile-"),state=Files.createDirectory(base.resolve("state"));
        Path profile=Files.createDirectory(state.resolve("profile")),game=Files.createDirectory(base.resolve("game"));
        Files.createDirectories(game.resolve("game/dlc"));Files.createDirectories(game.resolve("binaries"));
        Path launcher=Files.createDirectory(game.resolve("launcher"));
        var executable=write(game.resolve("binaries/ck3.exe"),"software DATA never executed".getBytes(StandardCharsets.UTF_8));
        var rules=write(game.resolve("rules.txt"),"software rule DATA".getBytes(StandardCharsets.UTF_8));
        var settings=write(launcher.resolve("launcher-settings.json"),
                "{\"rawVersion\":\"software\",\"version\":\"software\",\"distPlatform\":\"steam\"}".getBytes(StandardCharsets.UTF_8));
        var unqualified=write(base.resolve("unqualified-build.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var runtime=new ArrayList<FileRef>();for(int index=0;index<6;index++)
            runtime.add(write(base.resolve("runtime"+index+".jar"),("software runtime "+index).getBytes(StandardCharsets.UTF_8)));
        var load=StrictJson.object();var enabled=load.putArray("enabled_mods");
        load.putArray("disabled_dlcs").add("dlc_second").add("dlc_first");
        var mounted=new ArrayList<FileRef>();
        if(fixtureDomain){
            Path product=Files.createDirectories(profile.resolve("mod-content/fixture")),descriptor=profile.resolve("mod/fixture.mod");
            Files.createDirectories(descriptor.getParent());enabled.add("mod/fixture.mod");
            mounted.add(write(descriptor,("name=\"actual fixture\"\npath=\""+product.toString().replace('\\','/')+"\"\n").getBytes(StandardCharsets.UTF_8)));
            mounted.add(write(product.resolve("descriptor.mod"),"name=\"actual fixture\"\n".getBytes(StandardCharsets.UTF_8)));
            mounted.add(write(product.resolve("script.txt"),"on_game_start_after_lobby = { }".getBytes(StandardCharsets.UTF_8)));
        }
        FileRef loadSource=write(profile.resolve("dlc_load.json"),StrictJson.canonical(load));
        ExplicitSource source;
        if(fixtureDomain){
            var policy=write(state.resolve("fixture-policy.json"),"{\"software_source_only\":true}".getBytes(StandardCharsets.UTF_8));
            var closure=new ArrayList<FileRef>();closure.add(policy);closure.add(loadSource);closure.addAll(mounted);
            source=new FixtureSource(policy,closure,mounted.stream().map(row->profile.relativize(Path.of(row.path())).toString().replace('\\','/')).sorted().toList());
        }else{
            var inventory=StrictJson.object().put("schema","ck3-saved-campaign-vanilla-profile-v1").put("profile_path",profile.toString());
            inventory.putArray("enabled_mods");inventory.putArray("product_files");
            source=new SavedSource(SavedKind.VANILLA,write(state.resolve("inventory.json"),StrictJson.canonical(inventory)));
        }
        var request=new ExplicitRequest(EXPLICIT_REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(600).toString(),
                state.toString(),base.toString(),unqualified,executable,rules,settings,false,source);
        return new Fixture(request,write(base.resolve("explicit-request.json"),encodeExplicitRequest(request)),
                List.copyOf(runtime),Files.createDirectory(base.resolve("env-output")));
    }
    private RootBootstrapOutputGuard authority(RootProfileBootstrapInputs.Prepared prepared,Clock clock)throws Exception {
        Instant now=clock.instant();String machine=WindowsJobProcess.currentMachineId(),observed=now.minusSeconds(1).toString(),review=now.plusSeconds(300).toString();
        Path control=Files.createTempDirectory(root,"authority-"),asset=prepared.assetRoot();String window=control.getFileName().toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root",window,observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,prepared.quote(),prepared.outputDirectories(),prepared.retainedInputs());
        var declared=write(control.resolve("declaration.json"),encode(declaration));
        var census=RootBootstrapOutputGuard.observeAssetRoot(declared,clock);var censusRef=write(control.resolve("census.json"),encode(census));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var capacity=policy.putObject("capacity");
        capacity.put("safety_floor_bytes",2L<<30);capacity.put("safety_ceiling_bytes",20L<<30);capacity.put("default_project_quota_ceiling_bytes",100L<<30);
        capacity.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));capacity.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));
        FileRef financial=write(control.resolve("financial.json"),StrictJson.canonical(StrictJson.object().put("scope","actual-software-volume-upper").put("machine_id",machine)));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var usage=new org.xar.ck3.control.service.root.RootRuntimeStorageContract.ExistingUsage(
                org.xar.ck3.control.service.root.RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,total-free,financial);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,window,now.toString(),review,
                policyRef,declared,censusRef,financial,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        var released=write(control.resolve("capacity.json"),encode(release));
        return RootBootstrapOutputGuard.readExact(write(control.resolve("binding.json"),encode(
                new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,window,now.toString(),review,declared,censusRef,released))),clock);
    }
    private static FileRef write(Path path,byte[] body)throws IOException {
        Files.write(path,body,StandardOpenOption.CREATE_NEW);return FileRef.measure(path);
    }
}

