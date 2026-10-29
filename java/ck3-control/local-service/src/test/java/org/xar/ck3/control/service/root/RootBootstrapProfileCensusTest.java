package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Real temporary native directory/file census. Software issuer fixtures grant no runtime, Native or Game authority. */
class RootBootstrapProfileCensusTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-24T05:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private record Fixture(Path asset,Path source,FileRef binding,Output output,long retained){ }
    private Fixture fixture()throws IOException {
        Path asset=Files.createDirectory(root.resolve("profile")),control=Files.createDirectory(root.resolve("control"));
        Path parent=Files.createDirectory(asset.resolve("mod-content")),production=Files.createDirectory(parent.resolve("xar-production"));
        Path source=production.resolve("actual-source.txt");Files.writeString(source,"actual retained immutable source");var witness=SharedSourceFiles.observe(source);
        long guard=RootBootstrapAssetTree.directoryQuote(asset),allocated=witness.nativeFile().allocatedBytes();
        var tree=new NativeRunProfileManifest.ProductionTree(production.toString(),
                List.of(new NativeRunProfileManifest.TreeDirectory(production.toString(),SharedSourceFiles.nativeDirectory(production))),
                List.of(witness),allocated,guard,Math.addExact(allocated,guard));
        FileRef inventory=write(control.resolve("production-inventory.json"),NativeRunProfileProducer.encodeProductionTree(tree));
        var retained=new RetainedInput("mod-content",SharedSourceFiles.nativeDirectory(parent),inventory,SharedSourceFiles.nativeFile(Path.of(inventory.path())));
        String machine=WindowsJobProcess.currentMachineId(),observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        byte[] body="actual generated presets".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var output=new Output(Kind.PROFILE_PRESETS,"player/game_rules/presets.txt",body.length,DriverJson.sha256(body));
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","profile-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,List.of(output),List.of("mod","player","player/game_rules"),List.of(retained));
        FileRef declared=write(control.resolve("declaration.json"),encode(declaration));var census=RootBootstrapOutputGuard.observeAssetRoot(declared,CLOCK);
        assertEquals(Math.addExact(tree.retainedAllocatedUpperBytes(),guard),census.retainedAllocatedUpperBytes());
        assertEquals(guard,census.chargedUpperBytes());FileRef censusRef=write(control.resolve("census.json"),encode(census));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));Path volume=asset.getRoot();
        long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object();financial.put("scope","actual-software-fixture-volume-upper");financial.put("machine_id",machine);
        FileRef financialRef=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,total-free,financialRef);
        var custody=StrictJson.object().put("purpose","ACTIVE_PROFILE_PRODUCTION_INPUT").put("review_at_utc",review).put("fixture_only",true);
        custody.set("inventory",org.xar.ck3.control.build.ControlBuild.strictMapper().valueToTree(inventory));
        FileRef held=write(control.resolve("retention.json"),StrictJson.canonical(custody));
        var capacity=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"profile-fixture",NOW.toString(),review,
                policyRef,declared,censusRef,financialRef,2L<<20,
                List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),
                List.of(new RetainedAllocation(inventory,census.retainedAllocatedUpperBytes(),financialRef,RetentionPurpose.ACTIVE_PROFILE_PRODUCTION_INPUT,review,held)));
        FileRef capacityRef=write(control.resolve("capacity.json"),encode(capacity));
        var binding=new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,"profile-fixture",NOW.toString(),review,declared,censusRef,capacityRef);
        return new Fixture(asset,source,write(control.resolve("binding.json"),encode(binding)),output,census.retainedAllocatedUpperBytes());
    }
    @Test void completeRetainedTreeAndClosedGeneratedDirectoriesAreIndependentlyChargedAndActuallyWritten()throws IOException {
        var fixture=fixture();try(var guard=RootBootstrapOutputGuard.readExact(fixture.binding(),CLOCK)){
            Path target=fixture.asset().resolve(fixture.output().fileName());assertThrows(IOException.class,()->guard.requireTargets(List.of(target)));
            guard.createOutputDirectories();guard.requireTargets(List.of(target));
            byte[] body="actual generated presets".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            var actual=guard.files().createNew(target,body);guard.files().verify(actual);assertArrayEquals(body,guard.files().read(actual,1024));
            assertEquals(1,guard.accounting().completedOutputs());assertEquals(0,guard.accounting().unresolvedPeakBytes());
            assertEquals(fixture.retained(),guard.accounting().retainedAllocatedUpperBytes());
            assertEquals(Math.addExact(guard.accounting().assetChargedUpperBytes(),fixture.retained()),guard.accounting().completeAssetAllocatedUpperBytes());
            assertTrue(guard.accounting().assetChargedUpperBytes()<1536L*1024);assertTrue(Files.isRegularFile(fixture.source()));
            guard.createOutputDirectories();assertThrows(IOException.class,()->guard.files().createNew(target,body));
        }
    }
    @Test void retainedFileSameBytesReplacementAndExtraParentInputCannotBeExcludedFromTheCompleteCensus()throws IOException {
        var fixture=fixture();try(var guard=RootBootstrapOutputGuard.readExact(fixture.binding(),CLOCK)){
            Path backup=root.resolve("preserved-original.txt"),replacement=root.resolve("same-content.txt");
            Files.copy(fixture.source(),replacement);Files.move(fixture.source(),backup);Files.move(replacement,fixture.source());
            assertThrows(IOException.class,guard::createOutputDirectories);assertFalse(Files.exists(fixture.asset().resolve("player")));
        }
    }
    @Test void unknownRetainedParentEntryIsRejectedBeforeAnyGeneratedOutput()throws IOException {
        var fixture=fixture();Files.writeString(fixture.source().getParent().getParent().resolve("unaccounted.txt"),"unknown retained sibling");
        assertThrows(IOException.class,()->RootBootstrapOutputGuard.readExact(fixture.binding(),CLOCK));assertFalse(Files.exists(fixture.asset().resolve("player")));
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes);return FileRef.measure(path);}
}
