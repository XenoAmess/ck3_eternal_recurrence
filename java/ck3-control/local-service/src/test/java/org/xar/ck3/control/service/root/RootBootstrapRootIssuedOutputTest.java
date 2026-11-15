package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Real small Native roots. Fixture issuer documents grant no production storage or Game authority. */
final class RootBootstrapRootIssuedOutputTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.now();
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private static final byte[] BODY="{\"software_metadata_only\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
    private record Fixture(Path asset,Path control,CapacityRelease capacity,FileRef capacityRef,Declaration declaration,RootAllocation allocation) {
        FileRef bind()throws IOException {
            return RootProfileBootstrapCommand.bindIssuedCapacity(new RootProfileBootstrapCommand.IssuerBindingRequest(
                    "xar.java-root-bootstrap-issuer-binding-request/v1",capacity.machineId(),NOW.plusSeconds(900).toString(),capacityRef,control.resolve("binding.json").toString()),CLOCK).binding().original();
        }
    }

    @Test void publicBindingSelectsV5AndRealGuardCreatesOnlyTheThreePricedMetadataInputs()throws Exception {
        Fixture fixture=fixture("positive",outputs(),outputs(),fund->{});FileRef bindingRef=fixture.bind();
        Binding binding=decode(Files.readAllBytes(Path.of(bindingRef.path())),Binding.class);
        assertEquals(ROOT_BINDING,binding.schema());assertEquals(ROOT_ISSUER,binding.issuerTask());
        assertEquals(DECLARATION,fixture.declaration().schema());
        assertEquals(fixture.allocation(),decodeRootAllocation(encodeRootAllocation(fixture.allocation())));
        try(var guard=RootBootstrapOutputGuard.readExact(bindingRef,CLOCK)){
            List<Path> targets=outputs().stream().map(output->fixture.asset().resolve(output.fileName())).toList();guard.requireTargets(targets);
            for(Path target:targets){var created=guard.files().createNew(target,BODY);guard.files().verify(created);assertArrayEquals(BODY,guard.files().read(created,65536));}
            assertEquals(3,guard.accounting().completedOutputs());assertEquals(0,guard.accounting().unresolvedPeakBytes());
            assertThrows(IOException.class,()->guard.files().createNew(fixture.asset().resolve("unpriced.json"),BODY));
        }
    }

    @Test void versionedIssuerAndClosedRolesDoNotBroadenLegacyOrFormalAuthority()throws Exception {
        Fixture fixture=fixture("issuer",outputs(),outputs(),fund->{});var mapper=ControlBuild.strictMapper();
        for(String version:List.of(ROOT_CAPACITY,CAPACITY)){
            ObjectNode body=mapper.valueToTree(fixture.capacity());body.put("schema",version);body.put("issuer_task",version.equals(ROOT_CAPACITY)?ISSUER:ROOT_ISSUER);
            assertThrows(IOException.class,()->decode(mapper.writeValueAsBytes(body),CapacityRelease.class));
        }
        var legacy=new CapacityRelease(CAPACITY,PURPOSE,fixture.capacity().machineId(),"/root",ISSUER,fixture.capacity().windowId(),fixture.capacity().observedAtUtc(),fixture.capacity().reviewAtUtc(),
                fixture.capacity().policyRef(),fixture.capacity().declarationRef(),fixture.capacity().censusRef(),fixture.capacity().originalFinancialHeadRef(),fixture.capacity().jointMaximumChargedBytes(),fixture.capacity().volumes(),List.of());
        assertEquals(legacy,decode(encode(legacy),CapacityRelease.class));assertEquals(CAPACITY,legacy.schema());
        assertThrows(IllegalArgumentException.class,()->new Binding(ROOT_BINDING,PURPOSE,fixture.capacity().machineId(),"/root",ISSUER,"wrong-issuer",NOW.toString(),NOW.plusSeconds(3600).toString(),
                fixture.capacity().declarationRef(),fixture.capacity().censusRef(),fixture.capacityRef()));
        Fixture broad=fixture("broad",List.of(output(Kind.MCP_ADMISSION,"admission.json")),outputs(),fund->{});
        assertThrows(IOException.class,broad::bind);
        assertThrows(IllegalArgumentException.class,()->rootOutputPlan(List.of(new Output(Kind.ORIGINAL_DRIVER_RUN_PROFILE,"run-profile.json",65537,"1".repeat(64)))));
        Fixture mixed=fixture("mixed",outputs(),outputs(),fund->{});ObjectNode cap=mapper.valueToTree(mixed.capacity());cap.put("purpose",FORMAL_PURPOSE);
        assertThrows(IOException.class,()->decode(mapper.writeValueAsBytes(cap),CapacityRelease.class));
    }

    @Test void realGuardRejectsWrongNativeAllocatorArithmeticOrMirrorOnlyFunding()throws Exception {
        List<Consumer<ObjectNode>> defects=List.of(fund->fund.put("allocator",ROOT_ISSUER),fund->fund.put("owner","/root"),
                fund->fund.put("raw_after",fund.path("raw_after").longValue()+1),fund->fund.remove("quote"),
                fund->fund.put("same_profile_savedPair_copy",1),fund->fund.put("originalsource_snapshot_6jar_Frozen",false));
        int index=0;for(Consumer<ObjectNode> defect:defects){Fixture fixture=fixture("fund-"+index++,outputs(),outputs(),defect);assertThrows(IOException.class,fixture::bind);}
    }

    @Test void rootSourceMustPriceTheSameTypedPlanAndStayWithinItsFreshHour()throws Exception {
        Fixture mismatch=fixture("plan-mismatch",outputs(),List.of(output(Kind.INITIAL_POLICY,"another-policy.json")),fund->{});
        assertThrows(IOException.class,mismatch::bind);
        Fixture fixture=fixture("finite",outputs(),outputs(),fund->{});var a=fixture.allocation();
        assertThrows(IllegalArgumentException.class,()->new RootAllocation(a.schema(),a.machineId(),a.issuerTask(),a.ownerTask(),a.delegateTask(),a.windowId(),a.observedAtUtc(),NOW.plusSeconds(3601).toString(),
                a.policyRef(),a.declarationRef(),a.censusRef(),a.jointMaximumChargedBytes(),a.volumes(),a.outputs(),a.retainedAllocations(),a.nativeFundRefs()));
        ObjectNode body=ControlBuild.strictMapper().valueToTree(a);body.put("delegate_task","/root");
        assertThrows(IOException.class,()->decodeRootAllocation(ControlBuild.strictMapper().writeValueAsBytes(body)));
    }

    private Fixture fixture(String name,List<Output> plan,List<Output> allocationPlan,Consumer<ObjectNode> fundChange)throws IOException {
        Path base=Files.createDirectory(root.resolve(name)),asset=Files.createDirectory(base.resolve("asset")),control=Files.createDirectory(base.resolve("control"));
        String machine=WindowsJobProcess.currentMachineId(),review=NOW.plusSeconds(3600).toString();
        Declaration declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root",name,NOW.minusSeconds(1).toString(),review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),1536L*1024,512L*1024,1<<20,64,plan,List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        FileRef censusRef=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,CLOCK)));
        ObjectNode policy=StrictJson.object();policy.put("policy_version","1.0.0");ObjectNode rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30).put("safety_ceiling_bytes",20L<<30).put("default_project_quota_ceiling_bytes",100L<<30)
                .put("safety_volume_fraction",new java.math.BigDecimal("0.05")).put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        ObjectNode observation=StrictJson.object().put("scope","actual-volume-upper-not-project-inventory").put("total",total).put("free",free);
        FileRef observationRef=write(control.resolve("volume-observation.json"),StrictJson.canonical(observation));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,total-free,observationRef);
        List<Volume> volumes=List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0));
        ObjectNode fund=StrictJson.object();long metadata=2L<<20,amount=metadata+8192;
        fund.put("atUtc",NOW.minusSeconds(1).toString()).put("allocator","/root/native_continue").put("owner",ROOT_DELEGATE)
                .put("new_distinct_net_upper_once_bytes",amount).put("raw_before",0).put("raw_after",amount).put("normal_unchanged",0).put("cap_unchanged",amount)
                .put("same_profile_savedPair_copy",0).put("originalsource_snapshot_6jar_Frozen",true);
        fund.putObject("quote").put("two_real_READ_wire_cap64MiB_each",4096).put("provider_payload_cap64MiB",4096).put("driver_lifecycle_attachment_logs_NativeAllocation_residual_cap64MiB",metadata);
        fundChange.accept(fund);assertFalse(fund.has("schema"));FileRef fundRef=write(control.resolve("native-fund.json"),StrictJson.canonical(fund));
        RootAllocation allocation=new RootAllocation(ROOT_ALLOCATION,machine,ROOT_ISSUER,"/root",ROOT_DELEGATE,name,NOW.toString(),review,policyRef,declarationRef,censusRef,2L<<20,volumes,allocationPlan,List.of(),List.of(fundRef));
        FileRef source=write(control.resolve("root-allocation.json"),encodeRootAllocation(allocation));
        CapacityRelease capacity=new CapacityRelease(ROOT_CAPACITY,PURPOSE,machine,"/root",ROOT_ISSUER,name,NOW.toString(),review,policyRef,declarationRef,censusRef,source,2L<<20,volumes,List.of());
        FileRef capacityRef=write(control.resolve("capacity.json"),encode(capacity));return new Fixture(asset,control,capacity,capacityRef,declaration,allocation);
    }
    private static List<Output> outputs(){return List.of(output(Kind.PROFILE_ENVIRONMENT,"xar-autoplayer-environment.json"),output(Kind.INITIAL_POLICY,"initial-policy.json"),output(Kind.ORIGINAL_DRIVER_RUN_PROFILE,"original-run-profile.json"));}
    private static Output output(Kind kind,String name){return new Output(kind,name,BODY.length,DriverJson.sha256(BODY));}
    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes);return FileRef.measure(path);}
}
