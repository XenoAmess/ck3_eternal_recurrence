package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Metadata boundaries only; no fixture here is a real Own, package or native qualification. */
final class ToolsInputPostqualificationTest {
    @TempDir Path root;
    private FileRef ref(String name) { return new FileRef(root.resolve(name).toString(),1,"0".repeat(64)); }
    private ToolsInputPostqualification.Input input() {
        var source=new FileRef(root.resolve("ToolsIntegratedAcceptedReadback24c.java").toString(),38867L,
                "d0551d847cfacb31b1181ea50b384950bb693497967f6d3f57429e33f5311cf3");
        assertEquals(38867L, ToolsInputPostqualification.OWN_SOURCE_BYTES);
        assertEquals(source.sha256(), ToolsInputPostqualification.OWN_SOURCE_SHA256);
        var own=new ToolsInputPostqualification.FullOwnInputs(source,ref("map"),ref("history"),ref("capture"),
                ref("lease"),ref("rejection"),ref("source-map"),ref("manifest"));
        var inputs=new ArrayList<FileRef>();for(int i=0;i<513;i++)inputs.add(ref("original-"+i));
        return new ToolsInputPostqualification.Input(ToolsInputPostqualification.INPUT_SCHEMA,"metadata-machine",
                "2026-10-25T10:00:00Z","2026-10-25T11:00:00Z",ref("plan"),ref("capacity"),ref("tools"),
                own,List.of(ref("junit.jar")),inputs);
    }
    @Test void originalProducerToStrictConsumerRoundTripKeepsEveryDependencyAndInput()throws Exception {
        var mapper=ControlBuild.strictMapper();var original=input();byte[] wire=mapper.writeValueAsBytes(original);
        var decoded=mapper.readValue(wire,ToolsInputPostqualification.Input.class);
        assertEquals(original,decoded);assertEquals(513,decoded.largeInputs().size());
        assertEquals(7,decoded.fullOwn().arguments(decoded.toolsReceiptRef()).size());
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);missing.remove("full_own");
        assertThrows(IOException.class,()->mapper.treeToValue(missing,ToolsInputPostqualification.Input.class));
        var unknown=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);unknown.put("own_alias","easier-own");
        assertThrows(IOException.class,()->mapper.treeToValue(unknown,ToolsInputPostqualification.Input.class));
        var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);
        ((com.fasterxml.jackson.databind.node.ObjectNode)wrong.required("tools_receipt_ref")).put("bytes",true);
        assertThrows(IOException.class,()->mapper.treeToValue(wrong,ToolsInputPostqualification.Input.class));
        var partial=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);
        ((com.fasterxml.jackson.databind.node.ObjectNode)partial.required("full_own")).remove("historical_completed_receipt_ref");
        assertThrows(IOException.class,()->mapper.treeToValue(partial,ToolsInputPostqualification.Input.class));
        var changed=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);changed.put("schema","xar.control-ci-tools-postqualification-input/v99");
        assertThrows(IOException.class,()->mapper.treeToValue(changed,ToolsInputPostqualification.Input.class));
    }
    @Test void countDuplicateAndOriginalOwnGuardsCannotBeReplacedWithMetadataAliases() {
        var a=input();
        var original=a.fullOwn();
        var previousSource=new FileRef(original.producerSourceRef().path(),38044L,
                "ea924ce3d82ebfcc288b2e6f3e48ae96a4238d4d5631daa29fc4cf1ac3ad6e9f");
        assertThrows(IllegalArgumentException.class,()->new ToolsInputPostqualification.FullOwnInputs(previousSource,
                original.materializedMapRef(),original.historicalCompletedReceiptRef(),original.genuineHistoricalCaptureRef(),
                original.originalQuotaLeaseRef(),original.originalQuotaRejectionRef(),original.originalQuotaSourceMapRef(),
                original.boundedInputManifestRef()));
        var legacySource=new FileRef(original.producerSourceRef().path(),36601,
                "5b84673947edfcdefd524c875b8a123fcfcd8fafba744b12f67319da7c86e40d");
        assertThrows(IllegalArgumentException.class,()->new ToolsInputPostqualification.FullOwnInputs(legacySource,
                original.materializedMapRef(),original.historicalCompletedReceiptRef(),original.genuineHistoricalCaptureRef(),
                original.originalQuotaLeaseRef(),original.originalQuotaRejectionRef(),original.originalQuotaSourceMapRef(),
                original.boundedInputManifestRef()));
        assertThrows(IllegalArgumentException.class,()->new ToolsInputPostqualification.Input(a.schema(),a.machineId(),a.observedAtUtc(),a.reviewAtUtc(),
                a.resourcePlanRef(),a.capacityReleaseRef(),a.toolsReceiptRef(),a.fullOwn(),a.junitRuntime(),a.largeInputs().subList(0,512)));
        var repeated=new ArrayList<>(a.largeInputs());repeated.set(1,repeated.getFirst());
        assertThrows(IllegalArgumentException.class,()->new ToolsInputPostqualification.Input(a.schema(),a.machineId(),a.observedAtUtc(),a.reviewAtUtc(),
                a.resourcePlanRef(),a.capacityReleaseRef(),a.toolsReceiptRef(),a.fullOwn(),a.junitRuntime(),repeated));
        assertThrows(IllegalArgumentException.class,()->new ToolsInputPostqualification.FullOwnInputs(ref("easier.java"),ref("map"),ref("history"),
                ref("capture"),ref("lease"),ref("rejection"),ref("source-map"),ref("manifest")));
    }
    @Test void actualMainReceivesExactlySixPropertiesAndMissingActualNeverPasses()throws Exception {
        var props=ToolsInputPostqualification.properties(ref("binding"),ref("spec"));assertEquals(6,props.size());
        assertEquals(List.of("xar.sharedOwned.largeInputs.binding.path","xar.sharedOwned.largeInputs.binding.bytes",
                "xar.sharedOwned.largeInputs.binding.sha256","xar.sharedOwned.largeInputs.spec.path",
                "xar.sharedOwned.largeInputs.spec.bytes","xar.sharedOwned.largeInputs.spec.sha256"),props.stream().map(CiBootstrap.JavaUtf8Invocation.Property::name).toList());
        Path fake=root.resolve("not-an-actual.json");Files.writeString(fake,"{}");
        assertThrows(IOException.class,()->ControlCi.requireToolsPostqualification(FileRef.measure(fake),ref("tools")));
        assertFalse(Files.exists(root.resolve("artifacts")));
        assertThrows(IllegalArgumentException.class,()->ControlCi.main(new String[]{"--postqualify-tools"}));
    }
    @Test void hostedPolicyRequiresExplicitV4AndCliAndDoesNotGrantFullWindow()throws Exception {
        String current="{\"schema\":\"xar.java-control-CI-profile/v4\",\"max_project_bytes\":8589934592,\"review_minutes\":300,"
                +"\"task\":\"github-actions-java-ci\",\"qualification_scope\":\"SOFTWARE_ONLY_NOT_POSTQUALIFIED\","
                +"\"tools_postqualification_policy\":\""+ToolsInputPostqualification.POLICY+"\"}";
        byte[] raw=current.getBytes(StandardCharsets.UTF_8);
        CiBootstrap.requireToolsPostqualificationPolicy(raw,ToolsInputPostqualification.POLICY);
        assertThrows(IOException.class,()->CiBootstrap.requireToolsPostqualificationPolicy(raw,null));
        assertThrows(IOException.class,()->CiBootstrap.requireToolsPostqualificationPolicy(current.replace("/v4","/v3").getBytes(StandardCharsets.UTF_8),ToolsInputPostqualification.POLICY));
        assertThrows(IOException.class,()->CiBootstrap.hostedReviewDuration(current.replace(ToolsInputPostqualification.POLICY,"SKIP").getBytes(StandardCharsets.UTF_8),8L<<30,CiBootstrap.PipelineProfile.HOSTED_SOFTWARE));
        assertThrows(IOException.class,()->CiBootstrap.hostedReviewDuration(raw,8L<<30,CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE));
        assertEquals(9,ControlCi.Stage.values().length-2);assertEquals(11,ControlCi.Stage.values().length);
        var missing=CiBootstrap.missingToolsPostqualification();
        assertFalse(missing.toolsAdopted());assertFalse(missing.actualJunitExecuted());
        assertEquals(missing,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(missing),
                CiBootstrap.ToolsPostqualificationAvailability.class));
    }
}
