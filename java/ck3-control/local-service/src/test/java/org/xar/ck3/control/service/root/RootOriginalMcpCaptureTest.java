package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.OriginalMcpCapture;
import org.xar.ck3.control.build.OriginalMcpCapture.Role;
import org.xar.ck3.control.service.mcp.McpCoverage;
import static org.junit.jupiter.api.Assertions.*;

/** Actual once-captured original API output is consumed read-only. Missing source is FAIL/NOT_RUN, never skip. */
final class RootOriginalMcpCaptureTest {
    private static final com.fasterxml.jackson.databind.ObjectMapper JSON=ControlBuild.strictMapper();
    @Test void targetsUseOneTypedClosedContractAndRejectMissingUnknownNullAndWrongType()throws Exception{
        Path root=Path.of(".").toAbsolutePath().normalize();var targets=new RootOriginalMcpCapture.Targets(RootOriginalMcpCapture.TARGETS_SCHEMA,
            root.resolve("catalog.json").toString(),root.resolve("tools.json").toString(),root.resolve("resources.json").toString(),root.resolve("facts.json").toString(),root.resolve("inventory.json").toString());
        assertEquals(targets,RootOriginalMcpCapture.decodeTargets(RootOriginalMcpCapture.encodeTargets(targets)));
        ObjectNode original=(ObjectNode)JSON.readTree(RootOriginalMcpCapture.encodeTargets(targets));
        for(String field:List.of("schema","catalog","tools","resources","registration_facts","inventory_proof")){
            assertTrue(original.has(field),"required field must exist in the actual Targets wire: "+field);
            ObjectNode absent=original.deepCopy();absent.remove(field);assertThrows(java.io.IOException.class,()->RootOriginalMcpCapture.decodeTargets(JSON.writeValueAsBytes(absent)));
        }
        var extra=original.deepCopy();extra.put("javaAdmission",true);assertThrows(java.io.IOException.class,()->RootOriginalMcpCapture.decodeTargets(JSON.writeValueAsBytes(extra)));
        var wrong=original.deepCopy();wrong.put("tools",true);assertThrows(java.io.IOException.class,()->RootOriginalMcpCapture.decodeTargets(JSON.writeValueAsBytes(wrong)));
        var missing=original.deepCopy();missing.putNull("catalog");assertThrows(java.io.IOException.class,()->RootOriginalMcpCapture.decodeTargets(JSON.writeValueAsBytes(missing)));
        assertThrows(IllegalArgumentException.class,()->new RootOriginalMcpCapture.Targets(RootOriginalMcpCapture.TARGETS_SCHEMA,targets.catalog(),targets.catalog(),targets.resources(),targets.registrationFacts(),targets.inventoryProof()));
    }
    @Test void actualOriginalSdkCaptureFeedsSharedFullCatalogEveryDescriptorAndStableDataSerde()throws Exception{
        FileRef receipt=propertyRef("xar.original.mcp.capture.receipt");var actual=RootOriginalMcpCapture.readActual(receipt);
        var retained=RootOriginalMcpCapture.readRetained(receipt);retained.requireUnchanged();assertEquals(actual,retained.actual());
        for(var module:OriginalMcpCapture.OriginalModule.values()){
            var source=retained.sourceSet().get(module);assertEquals(source,retained.sourceSet().requireOriginal(source.original()));
        }
        var mcpSource=retained.sourceSet().mcpServer().original();var invented=new FileRef(Path.of(mcpSource.path()).resolveSibling("not-the-captured-original.py").toString(),mcpSource.bytes(),mcpSource.sha256());
        assertTrue(retained.sourceSet().lookup(invented).isEmpty(),"neighbor path is not an explicit original Python source");
        assertThrows(java.io.IOException.class,()->retained.sourceSet().requireOriginal(invented));
        var sourceSet=retained.sourceSet();var first=sourceSet.mcpServer();var second=sourceSet.riteCreationActionMcpV1();
        var substituted=new OriginalMcpCapture.OriginalMcpSourceSet(
            new OriginalMcpCapture.OriginalSource(first.module(),second.original(),second.nativeFile()),
            new OriginalMcpCapture.OriginalSource(second.module(),first.original(),first.nativeFile()),sourceSet.armyObserverResearchSamplingControl(),sourceSet.privateAutoScalarAbControlV1());
        var actualPlan=OriginalMcpCapture.decodePlan(Files.readAllBytes(Path.of(actual.capturePlanRef().path())));
        assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.verifySourceSet(substituted,actualPlan.originalRequestRef(),raw(actual.documents().catalog().original()).bytes()),
            "four real unchanged files with the wrong module attribution must fail the original request/catalog join");
        assertEquals("PASS_ORIGINAL_REGISTRATION_ONLY_NOT_JAVA_OR_GAME",actual.status());assertEquals("NOT_PRODUCED",actual.javaAdmission());assertEquals("NOT_RUN",actual.gameQualification());
        assertTrue(actual.captureProcess().result().passed());assertTrue(actual.actualTransport().listenerClosed());
        assertEquals(actual,RootOriginalMcpCapture.decodeActual(RootOriginalMcpCapture.encodeActual(actual)));
        var measured=OriginalMcpCapture.readMeasured(actual.measuredReceiptRef());
        // This exact source inventory is 323; the actual same-configuration subset is not inferred from that number.
        assertEquals(323,measured.summary().counts().declarations());
        var catalog=McpCoverage.readCatalog(raw(actual.documents().catalog().original()));
        var tools=RootPublicCatalogCodec.decodeTools(raw(actual.documents().tools().original()));
        assertEquals(measured.summary().counts().declarations(),catalog.declarations().size());
        assertEquals(measured.summary().counts().registeredTools(),tools.size());
        FileRef actualSharedTools=propertyRef("xar.public.mcp.tools");
        assertEquals(Path.of(actual.documents().tools().original().path()),Path.of(actualSharedTools.path()),"SDK/public tests must use the one captured tools original");
        assertEquals(actual.documents().tools().original().bytes(),actualSharedTools.bytes());assertEquals(actual.documents().tools().original().sha256(),actualSharedTools.sha256());
        var originalWrapper=PublicDataJson.object(raw(actualSharedTools));var originalRows=originalWrapper.get("tools");
        assertTrue(originalRows.isArray());assertEquals(tools.size(),originalRows.size());
        var allNames=new HashSet<String>();
        for(int i=0;i<tools.size();i++){
            var tool=tools.get(i);assertTrue(allNames.add(tool.name()));assertEquals(originalRows.get(i).get("name").textValue(),tool.name());
            // Every SDK metadata/inputSchema field, opaque values and nullable choices stay with the same shared decoder.
            assertEquals(originalRows.get(i),PublicDataJson.object(tool.original()));
        }
        for(Role role:Role.values()){
            var file=actual.documents().get(role);var extent=measured.summary().documents().get(role);
            assertEquals(extent.bytes(),file.original().bytes());assertEquals(extent.sha256(),file.original().sha256());
            JsonNode value=PublicDataJson.object(raw(file.original()));assertEquals(role.schema(),value.get("schema").textValue());
        }
        var source=PublicDataJson.object(raw(actual.documents().registrationFacts().original()));
        assertEquals("ORIGINAL_REGISTRATION_FACTS_ONLY_NO_JAVA_ADMISSION",source.get("semantic_scope").textValue());
        assertEquals("ROOT_TYPED_PRODUCER_REQUIRED_NOT_GRANTED_BY_THIS_CAPTURE",source.get("selected_configuration_qualification").textValue());
        assertEquals(6,source.get("sdk_wrong_type_missing_field_rejections").intValue());
        var transport=source.get("transport_override");assertFalse(transport.get("native_peer_observed").booleanValue());
        var forged=(ObjectNode)JSON.readTree(RootOriginalMcpCapture.encodeActual(actual));forged.put("java_admission","ADMITTED");
        assertThrows(java.io.IOException.class,()->RootOriginalMcpCapture.decodeActual(JSON.writeValueAsBytes(forged)));
    }
    private static RawJson raw(FileRef actual)throws Exception{actual.verify();return new RawJson(Files.readAllBytes(Path.of(actual.path())));}
    private static FileRef propertyRef(String prefix){
        String path=required(prefix+".path"),count=required(prefix+".bytes"),sha=required(prefix+".sha256");
        long bytes=Long.parseLong(count);assertEquals(Long.toString(bytes),count,"canonical exact fixture bytes required");
        assertTrue(Path.of(path).isAbsolute(),"NOT_RUN: actual absolute once-capture original required");return new FileRef(path,bytes,sha);
    }
    private static String required(String key){String value=System.getProperty(key);assertNotNull(value,"FAIL/NOT_RUN: actual original capture fixture missing "+key);assertFalse(value.isBlank(),"FAIL/NOT_RUN: actual original capture fixture missing "+key);return value;}
}

