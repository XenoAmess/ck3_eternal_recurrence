package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Existing run-profile codec -> actual Bootstrap Guard/write -> both startup roles -> original reader.
 * Configuration and issuer records below are software DATA; no Game, plan or InitialEpisodePolicy is minted.
 */
final class RootExplicitFreshPactBindingTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-25T20:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);

    private static FileRef write(Path path,byte[] bytes)throws IOException {
        Files.write(path,bytes);return FileRef.measure(path);
    }
    private RootFrozenRunProfile.Request runProfile(boolean ordinary)throws IOException {
        FileRef environment=write(root.resolve("environment.json"),"{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        return new RootFrozenRunProfile.Request(WindowsJobProcess.currentMachineId(),NOW,NOW.plusSeconds(3600),
                "fresh-run","fresh-session",new ExactRef(environment.path(),environment.bytes(),environment.sha256()),
                ordinary?RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION:RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                ordinary,new RootFrozenRunProfile.DisabledFreshRobert());
    }
    private RootJavaBootstrapInputs.Request request(FileRef original,Path target,
            RootJavaBootstrapInputs.Mode mode,FileRef binding) {
        return new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.plusSeconds(3600).toString(),mode,binding,
                List.of(new RootJavaBootstrapInputs.Item(Kind.ORIGINAL_DRIVER_RUN_PROFILE,original,target.toString())));
    }
    /** Reuses the original Bootstrap Guard's Declaration/Census/Capacity/Binding fixture contract. */
    private FileRef authority(Path asset,List<Output> outputs)throws IOException {
        Path control=Files.createDirectory(root.resolve("control"));String machine=WindowsJobProcess.currentMachineId();
        String observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","pact-bootstrap-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,outputs,List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,CLOCK)));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","software-fixture-actual-volume-observation").put("machine_id",machine)
                .put("total_bytes",total).put("usable_bytes",free).put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"pact-bootstrap-fixture",NOW.toString(),review,
                policyRef,declarationRef,census,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,
                "pact-bootstrap-fixture",NOW.toString(),review,declarationRef,census,capacity)));
    }
    @Test void actualSingleProfilePublicationSuppliesBothRequiredRolesAndConsumesTheExplicitBoolean()throws Exception {
        RootFrozenRunProfile.Request explicit=runProfile(true);
        FileRef original=write(root.resolve("original-profile.json"),RootFrozenRunProfile.encode(explicit));
        Path asset=Files.createDirectory(root.resolve("asset")),target=asset.resolve("run-profile.json");
        var quote=RootJavaBootstrapInputs.prepare(request(original,target,RootJavaBootstrapInputs.Mode.QUOTE,null),CLOCK);
        assertEquals(1,quote.quote().size());
        var publish=request(original,target,RootJavaBootstrapInputs.Mode.CREATE_NEW,authority(asset,quote.quote()));
        assertEquals(publish,RootJavaBootstrapInputs.decodeRequest(RootJavaBootstrapInputs.encodeRequest(publish)));
        var written=RootJavaBootstrapInputs.prepare(publish,CLOCK).createNew(CLOCK);
        assertEquals(1,written.size());
        var pins=written.getFirst().originalDriverRunProfileData();
        assertEquals(List.of(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,DataRole.EXPLICIT_FRESH_PACT),pins.stream().map(DataPin::role).toList());
        assertEquals(written.getFirst().original(),pins.get(0).originalRef());
        assertEquals(pins.get(0).originalRef(),pins.get(1).originalRef());
        FileRef consumed=RootRuntimeDefinitionModel.explicitFreshPactProfile(pins);
        assertNotEquals(original,consumed);
        assertEquals(explicit,RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(pins.get(1))));
        assertTrue(RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(pins.get(0))).ordinaryCampaignNoPact());
        byte[] wire=ControlBuild.strictMapper().writeValueAsBytes(pins);
        List<DataPin> reopened=Arrays.asList(ControlBuild.strictMapper().readValue(wire,DataPin[].class));
        assertEquals(pins,reopened);
        assertEquals(consumed,RootRuntimeDefinitionModel.explicitFreshPactProfile(reopened));
        try(var files=Files.list(asset)){assertEquals(1,files.count());}
    }
    @Test void missingOrSeparatePactOriginalCannotReplaceTheProfileThatActualStartupConsumes()throws Exception {
        byte[] body=RootFrozenRunProfile.encode(runProfile(false));
        FileRef profile=write(root.resolve("profile.json"),body);
        FileRef separate=write(root.resolve("separate-identical-profile.json"),body);
        var pair=List.of(new DataPin(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,profile),new DataPin(DataRole.EXPLICIT_FRESH_PACT,profile));
        assertEquals(profile,RootRuntimeDefinitionModel.explicitFreshPactProfile(pair));
        assertFalse(RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(pair.get(1))).ordinaryCampaignNoPact());
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionModel.explicitFreshPactProfile(List.of(pair.getFirst())));
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionModel.explicitFreshPactProfile(
                List.of(pair.getFirst(),new DataPin(DataRole.EXPLICIT_FRESH_PACT,separate))));
        var duplicate=new ArrayList<>(pair);duplicate.add(pair.get(1));
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitionModel.explicitFreshPactProfile(duplicate));
    }
    @Test void bootstrapUsesTheSoleProfileCodecAndNeverDefaultsMissingNullOrWrongTypedPact()throws Exception {
        byte[] original=RootFrozenRunProfile.encode(runProfile(true));
        Path asset=Files.createDirectory(root.resolve("asset"));
        for(int kind=0;kind<5;kind++) {
            ObjectNode value=(ObjectNode)StrictJson.parse(original);
            switch(kind) {
                case 0->value.remove("ordinary_campaign_no_pact");
                case 1->value.putNull("ordinary_campaign_no_pact");
                case 2->value.put("ordinary_campaign_no_pact",1);
                case 3->value.put("ordinary_campaign_no_pact","true");
                case 4->{value.remove("ordinary_campaign_no_pact");value.put("fresh", "ORDINARY_NO_PACT");}
                default->throw new AssertionError();
            }
            FileRef invalid=write(root.resolve("invalid-"+kind+".json"),StrictJson.canonical(value,65536));
            var input=request(invalid,asset.resolve("invalid-"+kind+".json"),RootJavaBootstrapInputs.Mode.QUOTE,null);
            assertThrows(IllegalArgumentException.class,()->RootJavaBootstrapInputs.prepare(input,CLOCK));
        }
        assertEquals(RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES,maximumDataBytes(DataRole.EXPLICIT_FRESH_PACT));
        try(var files=Files.list(asset)){assertEquals(0,files.count());}
    }
}
