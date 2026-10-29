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
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.FormalReleaseTestFixture;
import org.xar.ck3.control.service.root.RootBootstrapOutputGuard;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs;
import org.xar.ck3.control.service.root.RootRuntimeStorageContract;

/** Actual managed-Git release -> sole Guard -> ordinary profile producer -> inventory/assets/ENV -> cold codec.
 * Same-package derive uses the original DATA production core; the public qualified-tools boundary stays rejected.
 */
final class RootFormalProfileImportChainTest {
    @Test void isolatedImportKeepsSidecarOutsideRetainedParentAndReachesOrdinaryProfileColdCodec()throws Exception {
        try(var fixture=FormalReleaseTestFixture.create(FormalReleaseProducer.Mode.PUBLISH_RELEASE,0,0,
                FormalReleaseProducer.Layout.ISOLATED_PROFILE_IMPORT)){
            var release=fixture.actual();var releaseStage=RootProfileBootstrapInputs.formalRelease(release);Clock clock=Clock.systemUTC();
            assertEquals(FormalReleaseProducer.Layout.ISOLATED_PROFILE_IMPORT,releaseStage.formalLayout());
            Path state=release.outputRoot(),production=state.resolve("profile/mod-content/xar-production");
            assertEquals(production,release.request().productionRoot());
            assertEquals(state.resolve("xar-production.manifest.json"),release.request().manifestTarget());
            try(var authority=authority(releaseStage,fixture.root(),clock)){releaseStage.createNew(authority);}
            release.verifyCreatedPayload();
            try(var children=Files.list(production.getParent())){assertEquals(List.of(production),children.toList());}

            Path input=Files.createDirectory(fixture.root().resolve("ordinary-profile-inputs"));
            Path game=Files.createDirectory(input.resolve("game"));Files.createDirectories(game.resolve("game/dlc"));
            Path binaries=Files.createDirectory(game.resolve("binaries")),launcher=Files.createDirectory(game.resolve("launcher"));
            FileRef executable=write(binaries.resolve("ck3.exe"),"owned software DATA never executed".getBytes(StandardCharsets.UTF_8));
            FileRef rules=write(game.resolve("rules.txt"),defaults());
            FileRef settings=write(launcher.resolve("launcher-settings.json"),
                    "{\"rawVersion\":\"fixture\",\"version\":\"fixture\",\"distPlatform\":\"steam\"}".getBytes(StandardCharsets.UTF_8));
            FileRef unqualified=write(input.resolve("unqualified-tools-build.json"),"{}".getBytes(StandardCharsets.UTF_8));
            var runtime=new ArrayList<FileRef>();for(int index=0;index<6;index++)runtime.add(write(input.resolve("runtime"+index+".jar"),
                    ("actual owned software runtime DATA "+index).getBytes(StandardCharsets.UTF_8)));
            FileRef manifest=FileRef.measure(release.request().manifestTarget());
            var request=new NativeRunProfileProducer.Request(NativeRunProfileProducer.REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),
                    Instant.now().plusSeconds(300).toString(),state.toString(),production.toString(),unqualified,executable,rules,settings,manifest,
                    NativeRunProfileRules.XarMode.XAR_OFF,Display.FULLSCREEN);
            // This is the exact private production core already used by ordinary PROFILE, not a copied producer.
            var profile=NativeRunProfileProducer.derive(request,List.copyOf(runtime));
            assertEquals(release.manifest().files().size(),profile.productionTree().files().size());
            Path inventoryRoot=Files.createDirectory(fixture.root().resolve("profile-production-custody"));
            var inventoryStage=RootProfileBootstrapInputs.productionInventory(profile,inventoryRoot.resolve("production-tree.json"));
            RootProfileBootstrapInputs.Created inventory;
            try(var authority=authority(inventoryStage,fixture.root(),clock)){inventory=inventoryStage.createNew(authority).getFirst();}
            assertEquals(profile.productionTree(),NativeRunProfileProducer.readProductionTree(inventory.original()));

            var assets=RootProfileBootstrapInputs.assets(profile,inventory.original());
            try(var authority=authority(assets,fixture.root(),clock)){
                var actual=assets.createNew(authority);assertEquals(5,actual.size());
                assertEquals(profile.productionTree().retainedAllocatedUpperBytes()+directoryQuote(assets.assetRoot()),
                        authority.accounting().retainedAllocatedUpperBytes());
            }
            var environmentStage=RootProfileBootstrapInputs.environment(profile,inventory.original(),clock);
            RootProfileBootstrapInputs.Created environment;
            try(var authority=authority(environmentStage,fixture.root(),clock)){environment=environmentStage.createNew(authority).getFirst();}
            byte[] bytes=Files.readAllBytes(Path.of(environment.original().path()));
            Manifest cold=readOriginal(environment.original());assertEquals(cold,decode(bytes));
            assertEquals(production.toString(),cold.mod().productionPath());assertEquals(manifest.path(),cold.mod().productionManifest());
            assertEquals(release.manifest().files().size(),cold.mod().productionFileCount());
            assertThrows(IOException.class,()->NativeRunProfileProducer.prepare(request,clock));
            assertThrows(IOException.class,()->NativeRunProfileProducer.readVerified(environment.original()));

            // Reproduce the original sibling-manifest pollution as negative fixture data. The unchanged strict
            // retained-parent consumer must reject it even though the production tree itself is still exact.
            Path polluted=production.getParent().resolve("xar-production.manifest.json");Files.copy(release.request().manifestTarget(),polluted);
            var sameAssets=RootProfileBootstrapInputs.assets(profile,inventory.original());
            assertThrows(IOException.class,()->{try(var ignored=authority(sameAssets,fixture.root(),clock)){fail("unpriced retained-parent sibling admitted");}});
        }
    }
    private static RootBootstrapOutputGuard authority(RootProfileBootstrapInputs.Prepared prepared,Path fixtureRoot,Clock clock)throws Exception {
        boolean formal=prepared.branch()==Branch.FORMAL_RELEASE;Path control=Files.createTempDirectory(fixtureRoot,"ls-authority-");
        Path asset=prepared.assetRoot();String machine=WindowsJobProcess.currentMachineId(),window=control.getFileName().toString();
        Instant now=clock.instant();String observed=now.minusSeconds(1).toString(),review=now.plusSeconds(240).toString();
        long assetCap=formal?FORMAL_MAXIMUM_ASSET_BYTES:1536L*1024,controlCap=512L*1024,joint=Math.addExact(assetCap,controlCap);
        var declaration=new Declaration(formal?FORMAL_DECLARATION:DECLARATION,formal?FORMAL_PURPOSE:PURPOSE,machine,"/root",window,observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),assetCap,controlCap,
                formal?FORMAL_MAXIMUM_SINGLE_BYTES:1<<20,formal?prepared.quote().size()+prepared.outputDirectories().size():64,
                prepared.quote(),prepared.outputDirectories(),prepared.retainedInputs());
        FileRef declared=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declared,clock)));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","actual-software-volume-upper").put("machine_id",machine).put("total_bytes",total).put("usable_bytes",free);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,total-free,head);
        var retained=new ArrayList<RetainedAllocation>();
        for(RetainedInput input:prepared.retainedInputs()){
            var tree=NativeRunProfileProducer.readProductionTree(input.productionInventory());
            retained.add(new RetainedAllocation(input.productionInventory(),tree.retainedAllocatedUpperBytes()+directoryQuote(asset),head,
                    RetentionPurpose.ACTIVE_PROFILE_PRODUCTION_INPUT,review,input.productionInventory()));
        }
        var release=new CapacityRelease(formal?FORMAL_CAPACITY:CAPACITY,formal?FORMAL_PURPOSE:PURPOSE,machine,"/root",ISSUER,window,now.toString(),review,
                policyRef,declared,census,head,joint,List.of(new Volume(volume.toString(),joint,0,0,total,review,usage,List.of(),0)),retained);
        FileRef released=write(control.resolve("capacity.json"),encode(release));
        return RootBootstrapOutputGuard.readExact(write(control.resolve("binding.json"),encode(new Binding(formal?FORMAL_BINDING:BINDING,
                formal?FORMAL_PURPOSE:PURPOSE,machine,"/root",ISSUER,window,now.toString(),review,declared,census,released))),clock);
    }
    private static long directoryQuote(Path root)throws IOException{return Math.max(4096,NativeStorageGeometry.read(root).clusterBytes());}
    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes,StandardOpenOption.CREATE_NEW);return FileRef.measure(path);}
    private static byte[] defaults(){var text=new StringBuilder();for(int index=0;index<70;index++)text.append("r").append(index).append("={\n default=s").append(index).append("\n}\n");return text.toString().getBytes(StandardCharsets.UTF_8);}
}
