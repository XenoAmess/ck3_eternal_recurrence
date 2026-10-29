package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Real temporary immutable writer -> startup reader -> original finite-input consumer.
 * Temporary test capacity records do not authorize production storage or Game execution. */
public final class RootStartupConfigurationProducerTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-26T00:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private static FileRef write(Path path,byte[] bytes)throws IOException {
        Files.write(path,bytes);return SharedSourceFiles.observe(path).source();
    }
    private RootStartupConfiguration startup()throws IOException {
        String machine=WindowsJobProcess.currentMachineId();
        var source=write(temporary.resolve("source.txt"),new byte[]{1});
        return new RootStartupConfiguration(machine,NOW.plusSeconds(600),write(temporary.resolve("application.json"),new byte[]{'{','}'}),
                write(temporary.resolve("runtime.json"),new byte[]{'{','}'}),"software-startup-input",
                new G2Source(machine,NOW.toString(),"software-input-fixture",new ExactRef(source.path(),source.bytes(),source.sha256())),
                new RootStartupConfiguration.FreshRobert("fresh-robert"),new RootStartupConfiguration.CheckpointPaths(
                        temporary.resolve("driver.json"),temporary.resolve("checkpoint"),temporary.resolve("attachments"),"lineage",temporary.resolve("robert.ck3")),
                new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ofMillis(25),true),Duration.ofSeconds(30),
                List.of(new BatchLimits("batch-first",5,Duration.ofMinutes(2),Duration.ofSeconds(20),Duration.ofMillis(100),1)),temporary.resolve("receipts"));
    }
    @Test public void firstStartupPublishesThroughTheActualGuardAndFeedsTheOriginalFiniteConsumer()throws Exception {
        Path assets=Files.createDirectory(temporary.resolve("assets")),control=Files.createDirectory(temporary.resolve("control"));
        var startup=startup();Path target=assets.resolve("startup.json");
        var quote=new RootStartupConfigurationProducer.Request(RootJavaBootstrapInputs.Mode.QUOTE,null,target,startup);
        var quoted=RootStartupConfigurationProducer.prepare(RootStartupConfigurationProducer.decode(RootStartupConfigurationProducer.encode(quote)),CLOCK);
        assertFalse(Files.exists(target));
        FileRef binding=binding(assets,control,quoted.quote());
        var prepared=RootStartupConfigurationProducer.prepare(new RootStartupConfigurationProducer.Request(
                RootJavaBootstrapInputs.Mode.CREATE_NEW,binding,target,startup),CLOCK);
        var published=prepared.createNew();
        assertEquals(prepared.expected(),published.original());assertEquals(startup,published.readExact(CLOCK));
        assertEquals(startup,RootStartupConfiguration.readExact(published.original()));
        var originalInputs=new RootStartupInputsProducer.Request(published.original(),Duration.ofSeconds(1));
        var finite=new RootFiniteFirstLiveRequest("startup-consumer-test",startup.machineId(),NOW,NOW.plusSeconds(300),originalInputs,1,Duration.ofSeconds(30));
        var finiteQuote=RootFiniteFirstLiveRequestProducer.prepare(new RootFiniteFirstLiveRequestProducer.Request(
                RootJavaBootstrapInputs.Mode.QUOTE,null,assets.resolve("finite-request.json"),finite),CLOCK);
        assertEquals(RootFiniteFirstLiveRequestProducer.decode(RootFiniteFirstLiveRequestProducer.encode(
                new RootFiniteFirstLiveRequestProducer.Request(RootJavaBootstrapInputs.Mode.QUOTE,null,assets.resolve("finite-request.json"),finite))).finite(),finite);
        assertEquals(finite.encode().length,finiteQuote.expected().bytes());assertFalse(Files.exists(assets.resolve("finite-request.json")));
        assertFalse(Files.exists(startup.checkpoints().save()));assertFalse(Files.exists(startup.checkpoints().driverCheckpoint()));
        assertThrows(IOException.class,prepared::createNew);
    }
    private FileRef binding(Path assets,Path control,Output output)throws IOException {
        String machine=WindowsJobProcess.currentMachineId(),review=NOW.plusSeconds(600).toString(),window="startup-software-fixture";
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root",window,NOW.minusSeconds(1).toString(),review,
                assets.toString(),SharedSourceFiles.nativeDirectory(assets),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,List.of(output),List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,CLOCK)));
        var policy=StrictJson.object().put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30).put("safety_ceiling_bytes",20L<<30).put("default_project_quota_ceiling_bytes",100L<<30)
                .put("safety_volume_fraction",new java.math.BigDecimal("0.05")).put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));
        Path volume=assets.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","temporary-software-actual-volume-only").put("machine_id",machine)
                .put("total_bytes",total).put("usable_bytes",free).put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var capacity=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,window,NOW.toString(),review,
                policyRef,declarationRef,census,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef release=write(control.resolve("capacity.json"),encode(capacity));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,window,NOW.toString(),review,declarationRef,census,release)));
    }
}
