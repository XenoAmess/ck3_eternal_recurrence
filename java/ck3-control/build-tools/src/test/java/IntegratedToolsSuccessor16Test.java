import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

/** Constructor and durable wire bounds only; no source materialization authority is minted here. */
final class IntegratedToolsSuccessor16Test {
    @TempDir Path temporary;

    private IntegratedToolsSuccessor16.Request request(String schema, long cap) {
        var pin = new ControlBuild.FileRef(temporary.resolve("fixture-only").toString(), 0, "0".repeat(64));
        var roster = new IntegratedToolsSuccessor16.SourceRoster(188, 41);
        var overlay = new IntegratedToolsSuccessor16.Overlay(IntegratedToolsGraph01.Group.TOOLS,
                "pom.xml", pin, pin, pin, "Typed constructor fixture; never submitted for copying");
        return new IntegratedToolsSuccessor16.Request(schema, "fixture-machine", 
                new IntegratedToolsSuccessor16.TaskOwner("/root/tools_c15"), "2026-10-24T04:30:00Z",
                pin, pin, pin, pin, pin, temporary.resolve("not-created").toString(), cap,
                roster, roster, List.of(overlay), List.of());
    }

    @Test void explicitV5EightMiBContractRetainsFiniteRosterAndStrictWireTypes() throws Exception {
        var mapper = ControlBuild.strictMapper();
        var accepted = request("xar.integrated-tools-firstcut-successor/v5", 8L << 20);
        assertEquals(accepted, IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(accepted)));
        assertThrows(IllegalArgumentException.class,
                () -> request("xar.integrated-tools-firstcut-successor/v4", 8L << 20));
        assertThrows(IllegalArgumentException.class,
                () -> request("xar.integrated-tools-firstcut-successor/v5", (8L << 20) + 1));
        assertThrows(IllegalArgumentException.class,
                () -> request("xar.integrated-tools-firstcut-successor/v5", 0));
        var extended = new IntegratedToolsSuccessor16.SourceRoster(217, 41);
        assertEquals(258, extended.total());
        assertThrows(IllegalArgumentException.class, () -> new IntegratedToolsSuccessor16.Request(accepted.schema(), accepted.machineId(),
                accepted.taskOwner(), accepted.reviewAtUtc(), accepted.sourceAuthorityRef(), accepted.scopeClarificationRef(),
                accepted.qualificationEvidenceRef(), accepted.baseMapRef(), accepted.inputManifestRef(), accepted.outputRoot(),
                accepted.conservativeNewRootCapBytes(), accepted.baseRoster(), extended, accepted.overlays(), accepted.additions()));
        for (var bad : List.of(mapper.getNodeFactory().booleanNode(true),
                mapper.getNodeFactory().numberNode(8388608.0), mapper.getNodeFactory().textNode("8388608"))) {
            var wire = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                    mapper.valueToTree(accepted));
            wire.set("conservative_new_root_cap_bytes", bad);
            assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(wire)));
        }
        var missing = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                mapper.valueToTree(accepted));
        missing.remove("conservative_new_root_cap_bytes");
        assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(missing)));
        var unknown = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                mapper.valueToTree(accepted));
        unknown.put("unapproved_source_cap", 8L << 20);
        assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(unknown)));
        assertFalse(java.nio.file.Files.exists(temporary.resolve("not-created")));
    }
    @Test void explicitV6SupportsNewExactIssuerRosterWhileHistoricalV5CannotExecute() throws Exception {
        var legacy = request("xar.integrated-tools-firstcut-successor/v5", 8L << 20);
        var current = new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/v6", legacy.machineId(),
                legacy.taskOwner(), legacy.reviewAtUtc(), legacy.sourceAuthorityRef(), legacy.scopeClarificationRef(),
                legacy.qualificationEvidenceRef(), legacy.baseMapRef(), legacy.inputManifestRef(), legacy.outputRoot(),
                legacy.conservativeNewRootCapBytes(), new IntegratedToolsSuccessor16.SourceRoster(215, 41),
                new IntegratedToolsSuccessor16.SourceRoster(217, 41), legacy.overlays(), legacy.additions());
        var mapper = ControlBuild.strictMapper();
        assertEquals(current, IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(current)));
        assertThrows(IllegalArgumentException.class, () -> new IntegratedToolsSuccessor16.SourceRoster(472, 41));
        assertThrows(IllegalArgumentException.class, () -> new IntegratedToolsSuccessor16.SourceRoster(Integer.MAX_VALUE, 41));
        Path originalLegacyRequest = temporary.resolve("historical-v5-request.json");
        java.nio.file.Files.write(originalLegacyRequest, mapper.writeValueAsBytes(legacy), java.nio.file.StandardOpenOption.CREATE_NEW);
        var rejected = assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.main(new String[] { originalLegacyRequest.toString() }));
        assertEquals("Historical v5 source requests are readable but cannot authorize new materialization", rejected.getMessage());
        assertFalse(java.nio.file.Files.exists(temporary.resolve("not-created")));
    }
    @Test void genuineCapturedReceiptSourceExceedsMetadataCeilingButIsCopiedOnlyAfterExactFiniteRead() throws Exception {
        byte[] original;
        try (var resource = getClass().getResourceAsStream("/build-receipts/full-g2-capture01-red.json")) {
            assertNotNull(resource); original = resource.readAllBytes();
        }
        assertEquals(1201708, original.length);
        var digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original));
        assertEquals("c2423f9f849244232fe4a592113c01a3fbb45af77436952c5a7157da5fa93c42", digest);
        Path source = temporary.resolve("genuine-capture-source.json");
        java.nio.file.Files.write(source, original);
        var exact = ControlBuild.FileRef.measure(source);
        assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.readExact(exact));
        assertArrayEquals(original, IntegratedToolsSuccessor16.readSource(exact, 8L << 20));
        Path largerThanFourMiB = temporary.resolve("legal-source-under-issued-eightMiB");
        java.nio.file.Files.write(largerThanFourMiB, new byte[(4 << 20) + 1]);
        assertEquals((4 << 20) + 1, IntegratedToolsSuccessor16.readSource(ControlBuild.FileRef.measure(largerThanFourMiB), 8L << 20).length);
        java.nio.file.Files.delete(largerThanFourMiB);
        Path oversized = temporary.resolve("oversized-source");
        java.nio.file.Files.write(oversized, new byte[(8 << 20) + 1]);
        var tooLarge = ControlBuild.FileRef.measure(oversized);
        assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.readSource(tooLarge, 8L << 20));
        assertFalse(java.nio.file.Files.exists(temporary.resolve("not-created")));
    }
    @Test void actualMainRejectsMissingWinnerBeforeCopyAndFinalPackageMatchesCompleteSelection() throws Exception {
        var mapper = ControlBuild.strictMapper();
        String machine = org.xar.ck3.control.build.WindowsJobProcess.currentMachineId();
        String opened = java.time.Instant.now().toString(), review = java.time.Instant.now().plusSeconds(120).toString();
        var group = IntegratedToolsGraph01.Group.TOOLS;
        var host = IntegratedToolsGraph01.Group.HOST;
        var absent = new IntegratedToolsGraph01.Preimage(IntegratedToolsGraph01.PreimageKind.ABSENT, null);
        Path oldA = temporary.resolve("old-a.java"), oldMcp = temporary.resolve("old-mcp.java"), hostFile = temporary.resolve("host.java");
        Path newA = temporary.resolve("new-a.java"), newMcp = temporary.resolve("new-mcp.java");
        java.nio.file.Files.writeString(oldA, "old-a"); java.nio.file.Files.writeString(oldMcp, "old-mcp");
        java.nio.file.Files.writeString(hostFile, "host"); java.nio.file.Files.writeString(newA, "new-a");
        java.nio.file.Files.writeString(newMcp, "old-mcp" + "x".repeat(65)); // Actual omission kept old MCP winner by exactly 65 bytes.
        var oldARef = ControlBuild.FileRef.measure(oldA); var oldMcpRef = ControlBuild.FileRef.measure(oldMcp);
        var hostRef = ControlBuild.FileRef.measure(hostFile); var newARef = ControlBuild.FileRef.measure(newA);
        var newMcpRef = ControlBuild.FileRef.measure(newMcp);
        var baseRows = List.of(new IntegratedToolsGraph01.Selection(group, "A.java", absent, absent, null, oldARef, "fixture", oldARef),
                new IntegratedToolsGraph01.Selection(group, "OriginalMcpCapture.java", absent, absent, null, oldMcpRef, "fixture", oldMcpRef),
                new IntegratedToolsGraph01.Selection(host, "Host.java", absent, absent, null, hostRef, "fixture", hostRef));
        var base = new IntegratedToolsGraph01.Actual("xar.integrated-host-tools-source-map/v1", machine, opened, "SOFTWARE_ONLY", oldARef,
                oldARef, oldARef, oldARef, "No runtime qualification", 2, 1, 16, 4096, List.of(oldARef), baseRows);
        var baseRef = json(temporary.resolve("base.json"), base);
        Path output = temporary.resolve("complete-output");
        var selected = List.of(new IntegratedToolsSuccessor16.SelectedFile(group, "build-tools/A.java", newARef),
                new IntegratedToolsSuccessor16.SelectedFile(group, "build-tools/OriginalMcpCapture.java", newMcpRef),
                new IntegratedToolsSuccessor16.SelectedFile(host, "Host.java", hostRef));
        var selection = new IntegratedToolsSuccessor16.EffectiveSelection("xar.java-source-effective-selection/v2", machine, "/root/tools_c15", opened,
                "FROZEN_COMPLETE_WINNERS_SOURCE_ONLY", baseRef, selected, List.of(), new IntegratedToolsSuccessor16.SelectionCounts(3, 2, 1, 2),
                newARef.bytes() + newMcpRef.bytes() + hostRef.bytes(), 4096, 1, output.toString(), "SOURCE_ONLY", "NOT_QUALIFIED", "none",
                oldARef, oldARef, "software only", oldARef, "actual 65-byte omitted MCP overlay regression");
        var selectionRef = json(temporary.resolve("complete-selection.json"), selection);
        var scope = mapper.createObjectNode().put("schema", "xar.java-phase1.source-task-scope-clarification/v1").put("machine_id", machine)
                .put("actual_task_owner", "/root/tools_c15").put("review_at_utc", review).put("tools_source_files", 2).put("host_source_files", 1)
                .put("physical_source_files", 3).put("new_external_native_upper_bytes", 8L << 20);
        scope.putArray("exact_roots").add(output.toString()); scope.set("exact_selected_files_ref", mapper.valueToTree(selectionRef));
        var scopeRef = json(temporary.resolve("scope.json"), scope);
        var first = new IntegratedToolsSuccessor16.Overlay(group, "A.java", oldARef, newARef, selectionRef, "first selected repair");
        var mcp = new IntegratedToolsSuccessor16.Overlay(group, "OriginalMcpCapture.java", oldMcpRef, newMcpRef, selectionRef, "complete MCP repair");
        var omitted = current(temporary.resolve("omitted-manifest.json"), List.of(first), List.of(selectionRef, oldARef, oldMcpRef, hostRef, newARef),
                machine, opened, review, scopeRef, baseRef, output, selectionRef);
        Path omittedPath = Path.of(json(temporary.resolve("omitted-request.json"), omitted).path());
        var rejected = assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.main(new String[] { omittedPath.toString() }));
        assertTrue(rejected.getMessage().contains("Resolved final winner differs before CREATE_NEW"));
        assertFalse(java.nio.file.Files.exists(output), "same-count omitted winner must fail before ANY destination creation");
        var complete = current(temporary.resolve("complete-manifest.json"), List.of(first, mcp), List.of(selectionRef, oldARef, oldMcpRef, hostRef, newARef, newMcpRef),
                machine, opened, review, scopeRef, baseRef, output, selectionRef);
        var wire = mapper.writeValueAsBytes(complete);
        assertEquals(complete, IntegratedToolsSuccessor16.decodeRequest(wire));
        for (String mutation : List.of("missing", "null", "unknown")) {
            var node = mapper.valueToTree(complete).deepCopy(); var object = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, node);
            if (mutation.equals("missing")) object.remove("final_selection_ref");
            else if (mutation.equals("null")) object.putNull("final_selection_ref"); else object.put("unbound_final_selection", true);
            assertThrows(java.io.IOException.class, () -> IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(object)));
        }
        Path completePath = Path.of(json(temporary.resolve("complete-request.json"), complete).path());
        IntegratedToolsSuccessor16.main(new String[] { completePath.toString() });
        assertArrayEquals(java.nio.file.Files.readAllBytes(newMcp), java.nio.file.Files.readAllBytes(output.resolve("tools/OriginalMcpCapture.java")));
        var finalMap = mapper.readValue(java.nio.file.Files.readAllBytes(output.resolve("SOURCE-MAP01.json")), IntegratedToolsGraph01.Actual.class);
        assertEquals(3, finalMap.sources().size());
        for (var row : finalMap.sources()) {
            var wanted = selected.stream().filter(value -> value.group() == row.group() && value.key().equals(row.group().name() + ":" + row.targetRelative())).findFirst().orElseThrow();
            assertEquals(wanted.sourceRef().bytes(), row.materializedRef().bytes()); assertEquals(wanted.sourceRef().sha256(), row.materializedRef().sha256()); row.materializedRef().verify();
        }
        var guard = mapper.readValue(java.nio.file.Files.readAllBytes(output.resolve("SOURCE-INPUT-GUARD01.json")), org.xar.ck3.control.build.BoundedSourceInputGuard.Receipt.class);
        assertEquals("MATCH", guard.postcheck()); assertEquals(6, guard.files());
        assertTrue(guard.observations().stream().anyMatch(value -> Path.of(value.source().path()).equals(Path.of(selectionRef.path()))));
    }
    private IntegratedToolsSuccessor16.Request current(Path manifest, List<IntegratedToolsSuccessor16.Overlay> overlays, List<ControlBuild.FileRef> inputs,
            String machine, String opened, String review, ControlBuild.FileRef scope, ControlBuild.FileRef base, Path output, ControlBuild.FileRef selection) throws Exception {
        var body = new org.xar.ck3.control.build.BoundedSourceInputGuard.Manifest("xar.bounded-source-input-manifest/v1", machine, "/root/tools_c15", opened, review, inputs);
        var inputRef = json(manifest, body); var roster = new IntegratedToolsSuccessor16.SourceRoster(2, 1);
        return new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/v7", machine, new IntegratedToolsSuccessor16.TaskOwner("/root/tools_c15"), review,
                scope, scope, scope, base, inputRef, output.toString(), 8L << 20, roster, roster, overlays, List.of(), selection);
    }
    private static ControlBuild.FileRef json(Path path, Object value) throws Exception {
        java.nio.file.Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value), java.nio.file.StandardOpenOption.CREATE_NEW);
        return ControlBuild.FileRef.measure(path);
    }

@Test void v8HasExplicit64AdditionTwelveMiBBoundsAndKeepsHistoricalVersionsStrict()throws Exception{
var old=request("xar.integrated-tools-firstcut-successor/v6",8L<<20);var pin=old.baseMapRef();
var additions=new java.util.ArrayList<IntegratedToolsSuccessor16.Addition>();
for(int i=0;i<65;i++)additions.add(new IntegratedToolsSuccessor16.Addition(IntegratedToolsGraph01.Group.TOOLS,"new"+i+".java",pin,pin,"typed finite boundary"));
var roster=new IntegratedToolsSuccessor16.SourceRoster(252,41);
var actual=new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/v8",old.machineId(),old.taskOwner(),old.reviewAtUtc(),
pin,pin,pin,pin,pin,old.outputRoot(),12L<<20,old.baseRoster(),roster,old.overlays(),additions.subList(0,64),pin);
var mapper=ControlBuild.strictMapper();
assertEquals(actual,IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(actual)));
assertThrows(IllegalArgumentException.class,()->new IntegratedToolsSuccessor16.Request(actual.schema(),old.machineId(),old.taskOwner(),old.reviewAtUtc(),
pin,pin,pin,pin,pin,old.outputRoot(),12L<<20,old.baseRoster(),roster,old.overlays(),additions,pin));
assertThrows(IllegalArgumentException.class,()->new IntegratedToolsSuccessor16.Request(actual.schema(),old.machineId(),old.taskOwner(),old.reviewAtUtc(),
pin,pin,pin,pin,pin,old.outputRoot(),(12L<<20)+1,old.baseRoster(),roster,old.overlays(),List.of(),pin));
for(String schema:List.of("v5","v6","v7")){
ControlBuild.FileRef selection=schema.equals("v7")?pin:null;
assertThrows(IllegalArgumentException.class,()->new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/"+schema,
old.machineId(),old.taskOwner(),old.reviewAtUtc(),pin,pin,pin,pin,pin,old.outputRoot(),8L<<20,
old.baseRoster(),old.baseRoster(),old.overlays(),additions.subList(0,33),selection));
assertThrows(IllegalArgumentException.class,()->new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/"+schema,
old.machineId(),old.taskOwner(),old.reviewAtUtc(),pin,pin,pin,pin,pin,old.outputRoot(),(8L<<20)+1,
old.baseRoster(),old.baseRoster(),old.overlays(),List.of(),selection));
}
for(String field:List.of("schema","final_selection_ref","conservative_new_root_cap_bytes")){
var wire=mapper.valueToTree(actual);var object=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,wire);
object.remove(field);assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.decodeRequest(mapper.writeValueAsBytes(wire)));
}
assertFalse(java.nio.file.Files.exists(Path.of(old.outputRoot())));
}
@Test void v8ActualMainCopiesAll282ToolsAnd46HostFilesWith48AdditionsAndExactFinalWinners()throws Exception{
var mapper=ControlBuild.strictMapper();String machine=org.xar.ck3.control.build.WindowsJobProcess.currentMachineId();
String opened=java.time.Instant.now().toString(),review=java.time.Instant.now().plusSeconds(120).toString();
var tools=IntegratedToolsGraph01.Group.TOOLS;var host=IntegratedToolsGraph01.Group.HOST;
var absent=new IntegratedToolsGraph01.Preimage(IntegratedToolsGraph01.PreimageKind.ABSENT,null);
var baseRows=new java.util.ArrayList<IntegratedToolsGraph01.Selection>();
var selected=new java.util.ArrayList<IntegratedToolsSuccessor16.SelectedFile>();
var inputs=new java.util.LinkedHashMap<String,ControlBuild.FileRef>();
for(int i=0;i<280;i++){
var group=i<234?tools:host;String target=(i<234?"src/main/java/Base":"Host")+i+".java";
var source=fixtureBytes("old"+i,"physical source DATA "+i);inputs.put(source.path(),source);
baseRows.add(new IntegratedToolsGraph01.Selection(group,target,absent,absent,null,source,"owned physical DATA",source));
selected.add(new IntegratedToolsSuccessor16.SelectedFile(group,(group==tools?"build-tools/":"")+target,source));
}
var first=baseRows.getFirst().materializedRef();var base=new IntegratedToolsGraph01.Actual("xar.integrated-host-tools-source-map/v1",machine,opened,
"SOFTWARE_ONLY",first,first,first,first,"No runtime qualification",234,46,1,4096,List.of(first),baseRows);
var baseRef=json(temporary.resolve("v8-base.json"),base);Path output=temporary.resolve("v8-output");
var replacement=fixtureBytes("replacement","different actual first winner");inputs.put(replacement.path(),replacement);
selected.set(0,new IntegratedToolsSuccessor16.SelectedFile(tools,"build-tools/"+baseRows.getFirst().targetRelative(),replacement));
var additions=new java.util.ArrayList<IntegratedToolsSuccessor16.Addition>();
for(int i=0;i<48;i++){
var source=fixtureBytes("addition"+i,"actual additional DATA "+i);inputs.put(source.path(),source);
String target="src/test/java/Additional"+i+".java";
selected.add(new IntegratedToolsSuccessor16.SelectedFile(tools,"build-tools/"+target,source));
additions.add(new IntegratedToolsSuccessor16.Addition(tools,target,source,baseRef,"actual current-cut addition"));
}
long logical=selected.stream().mapToLong(row->row.sourceRef().bytes()).sum();
var selection=new IntegratedToolsSuccessor16.EffectiveSelection("xar.java-source-effective-selection/v2",machine,"/root/tools_c15",opened,
"FROZEN_COMPLETE_WINNERS_SOURCE_ONLY",baseRef,selected,List.of(),new IntegratedToolsSuccessor16.SelectionCounts(328,282,46,234),
logical,1L<<20,1,output.toString(),"SOURCE_ONLY","NOT_QUALIFIED","none",first,first,"software only",first,"actual 48-addition full-roster regression");
var selectionRef=json(temporary.resolve("v8-selection.json"),selection);inputs.put(selectionRef.path(),selectionRef);
var scope=mapper.createObjectNode().put("schema","xar.java-phase1.source-task-scope-clarification/v1").put("machine_id",machine)
.put("actual_task_owner","/root/tools_c15").put("review_at_utc",review).put("tools_source_files",282).put("host_source_files",46)
.put("physical_source_files",328).put("new_external_native_upper_bytes",12L<<20);
scope.putArray("exact_roots").add(output.toString());scope.set("exact_selected_files_ref",mapper.valueToTree(selectionRef));
var scopeRef=json(temporary.resolve("v8-scope.json"),scope);
var manifest=new org.xar.ck3.control.build.BoundedSourceInputGuard.Manifest("xar.bounded-source-input-manifest/v1",machine,"/root/tools_c15",opened,review,List.copyOf(inputs.values()));
var manifestRef=json(temporary.resolve("v8-input-manifest.json"),manifest);
var overlay=new IntegratedToolsSuccessor16.Overlay(tools,baseRows.getFirst().targetRelative(),first,replacement,selectionRef,"replace actual first winner");
var request=new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/v8",machine,new IntegratedToolsSuccessor16.TaskOwner("/root/tools_c15"),review,
scopeRef,scopeRef,scopeRef,baseRef,manifestRef,output.toString(),12L<<20,new IntegratedToolsSuccessor16.SourceRoster(234,46),
new IntegratedToolsSuccessor16.SourceRoster(282,46),List.of(overlay),additions,selectionRef);
var requestRef=json(temporary.resolve("v8-request.json"),request);
IntegratedToolsSuccessor16.main(new String[]{requestRef.path()});
var result=mapper.readValue(java.nio.file.Files.readAllBytes(output.resolve("SOURCE-MAP01.json")),IntegratedToolsGraph01.Actual.class);
assertEquals(282,result.toolsSources());assertEquals(46,result.hostOverlaySources());assertEquals(328,result.sources().size());
for(var row:result.sources()){
var wanted=selected.stream().filter(x->x.key().equals(row.group().name()+":"+row.targetRelative())).findFirst().orElseThrow();
assertEquals(wanted.sourceRef().bytes(),row.materializedRef().bytes());assertEquals(wanted.sourceRef().sha256(),row.materializedRef().sha256());row.materializedRef().verify();
}
var guard=mapper.readValue(java.nio.file.Files.readAllBytes(output.resolve("SOURCE-INPUT-GUARD01.json")),org.xar.ck3.control.build.BoundedSourceInputGuard.Receipt.class);
assertEquals("MATCH",guard.postcheck());assertEquals(330,guard.files());
assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.main(new String[]{requestRef.path()}));
}

    @Test void v9RetiresExactExternalTestOnlyAfterSharedAuthorityAndCompleteWinnerValidation()throws Exception{
        var m=ControlBuild.strictMapper();String machine=org.xar.ck3.control.build.WindowsJobProcess.currentMachineId();
        String now=java.time.Instant.now().toString(),until=java.time.Instant.now().plusSeconds(120).toString();
        var tools=IntegratedToolsGraph01.Group.TOOLS;var host=IntegratedToolsGraph01.Group.HOST;
        var old=fixtureBytes("retired-old","genuine old source DATA");var logical=fixtureBytes("retired-logical","genuine old source DATA");var keep=fixtureBytes("retired-keep","kept source DATA");var next=fixtureBytes("retired-next","actual new owner DATA");
        String from="build-tools/src/test/java/sample/OldTest.java",to="local-service/src/test/java/sample/ActualRegression.java";
        var a=m.createObjectNode().put("schema","original-owner").put("machine_id",machine).put("owner","/root/parity_ci");
        a.putArray("selected_files").addObject().put("target_relative",to).set("source_ref",m.valueToTree(logical));
        var move=a.putArray("relocations").addObject().put("old_target_relative",from).put("new_target_relative",to);move.set("source_ref",m.valueToTree(logical));
        var original=json(temporary.resolve("retired-original.json"),a);
        var owner=m.createObjectNode().put("schema","current-owner").put("machine_id",machine).put("owner","/root/parity_ci");
        owner.putArray("selected_files").addObject().put("target_relative",to).set("source_ref",m.valueToTree(next));
        var current=json(temporary.resolve("retired-current.json"),owner);
        var relocation=new org.xar.ck3.control.build.CompleteSourceGraph.Relocation(from,to,logical,original,next,current,to);
        var authority=json(temporary.resolve("retired-authority.json"),new IntegratedToolsSuccessor16.Retirements("xar.source08.explicit-test-relocations/v1",machine,"/root/parity_ci",List.of(relocation),List.of(new org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile(to,next))));
        var absent=new IntegratedToolsGraph01.Preimage(IntegratedToolsGraph01.PreimageKind.ABSENT,null);
        var rows=List.of(new IntegratedToolsGraph01.Selection(tools,from.substring(12),absent,absent,null,logical,"fixture",old),new IntegratedToolsGraph01.Selection(tools,"Keep.java",absent,absent,null,keep,"fixture",keep),new IntegratedToolsGraph01.Selection(host,"Host.java",absent,absent,null,keep,"fixture",keep));
        var base=json(temporary.resolve("retired-base.json"),new IntegratedToolsGraph01.Actual("xar.integrated-host-tools-source-map/v1",machine,now,"SOURCE_ONLY",old,old,old,old,"unqualified",2,1,1,4096,List.of(old),rows));
        Path out=temporary.resolve("retired-output");var selected=List.of(new IntegratedToolsSuccessor16.SelectedFile(tools,"build-tools/Keep.java",keep),new IntegratedToolsSuccessor16.SelectedFile(host,"Host.java",keep));
        var selection=json(temporary.resolve("retired-selected.json"),new IntegratedToolsSuccessor16.EffectiveSelection("xar.java-source-effective-selection/v2",machine,"/root/tools_c15",now,"FROZEN_COMPLETE_WINNERS_SOURCE_ONLY",base,selected,List.of(),new IntegratedToolsSuccessor16.SelectionCounts(2,1,1,1),keep.bytes()*2,4096,1,out.toString(),"SOURCE_ONLY","NOT_QUALIFIED","none",old,old,"software only",old,"external test transfer"));
        var scope=m.createObjectNode().put("schema","xar.java-phase1.source-task-scope-clarification/v1").put("machine_id",machine).put("actual_task_owner","/root/tools_c15").put("review_at_utc",until).put("tools_source_files",1).put("host_source_files",1).put("physical_source_files",2).put("new_external_native_upper_bytes",12L<<20);
        scope.putArray("exact_roots").add(out.toString());scope.set("exact_selected_files_ref",m.valueToTree(selection));var scopeRef=json(temporary.resolve("retired-scope.json"),scope);
        var manifest=json(temporary.resolve("retired-inputs.json"),new org.xar.ck3.control.build.BoundedSourceInputGuard.Manifest("xar.bounded-source-input-manifest/v1",machine,"/root/tools_c15",now,until,List.of(old,logical,keep,next,original,current,authority,selection)));
        var overlay=new IntegratedToolsSuccessor16.Overlay(tools,"Keep.java",keep,keep,selection,"retained exact winner");
        var request=new IntegratedToolsSuccessor16.Request("xar.integrated-tools-firstcut-successor/v9",machine,new IntegratedToolsSuccessor16.TaskOwner("/root/tools_c15"),until,scopeRef,scopeRef,scopeRef,base,manifest,out.toString(),12L<<20,new IntegratedToolsSuccessor16.SourceRoster(2,1),new IntegratedToolsSuccessor16.SourceRoster(1,1),List.of(overlay),List.of(),selection,authority);
        var wire=m.valueToTree(request);var object=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,wire);
        object.remove("retirement_authority_ref");assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.decodeRequest(m.writeValueAsBytes(object)));
        object.set("retirement_authority_ref",m.valueToTree(authority));object.put("schema","xar.integrated-tools-firstcut-successor/v8");assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.decodeRequest(m.writeValueAsBytes(object)));
        var bad=a.deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)bad.withArray("relocations").get(0)).put("new_target_relative","local-service/src/test/java/sample/WrongRegression.java");
        var badOriginal=json(temporary.resolve("retired-bad-original.json"),bad);
        var badMove=new org.xar.ck3.control.build.CompleteSourceGraph.Relocation(from,to,logical,badOriginal,next,current,to);
        var badAuthority=json(temporary.resolve("retired-bad-authority.json"),new IntegratedToolsSuccessor16.Retirements("xar.source08.explicit-test-relocations/v1",machine,"/root/parity_ci",List.of(badMove),List.of(new org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile(to,next))));
        var badManifest=json(temporary.resolve("retired-bad-inputs.json"),new org.xar.ck3.control.build.BoundedSourceInputGuard.Manifest("xar.bounded-source-input-manifest/v1",machine,"/root/tools_c15",now,until,List.of(old,logical,keep,next,badOriginal,current,badAuthority,selection)));
        var badRequest=new IntegratedToolsSuccessor16.Request(request.schema(),machine,request.taskOwner(),until,scopeRef,scopeRef,scopeRef,base,badManifest,out.toString(),12L<<20,request.baseRoster(),request.finalRoster(),request.overlays(),List.of(),selection,badAuthority);
        var badRequestRef=json(temporary.resolve("retired-bad-request.json"),badRequest);
        var rejected=assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.main(new String[]{badRequestRef.path()}));assertTrue(rejected.getMessage().contains("relocation authority exact row differs"));assertFalse(java.nio.file.Files.exists(out));
        var requestRef=json(temporary.resolve("retired-request.json"),request);java.nio.file.Files.writeString(Path.of(next.path()),"wrong current source");
        assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.main(new String[]{requestRef.path()}));assertFalse(java.nio.file.Files.exists(out));
        java.nio.file.Files.writeString(Path.of(next.path()),"actual new owner DATA");IntegratedToolsSuccessor16.main(new String[]{requestRef.path()});
        assertFalse(java.nio.file.Files.exists(out.resolve("tools").resolve(from.substring(12))));assertFalse(java.nio.file.Files.exists(out.resolve("host-overlay").resolve(to)));
        old.verify();logical.verify();next.verify();var result=m.readValue(java.nio.file.Files.readAllBytes(out.resolve("SOURCE-MAP01.json")),IntegratedToolsGraph01.Actual.class);
        assertEquals(2,result.sources().size());assertTrue(result.provenanceRefs().containsAll(List.of(authority,original,current,logical,next)));assertTrue(result.originalQualificationBoundary().contains("source-only"));
    }
private ControlBuild.FileRef fixtureBytes(String name,String value)throws Exception{
Path path=temporary.resolve(name);java.nio.file.Files.writeString(path,value,java.nio.file.StandardOpenOption.CREATE_NEW);return ControlBuild.FileRef.measure(path);
}

    @Test void actualNativeProjectionRetainsCanonicalPathsAndFullConsumerManifest() throws Exception {
        var m=ControlBuild.strictMapper();String machine=org.xar.ck3.control.build.WindowsJobProcess.currentMachineId();
        String now=java.time.Instant.now().toString();
        Path root=temporary.resolve("canonical");java.nio.file.Files.createDirectory(root);
        var resolved=new java.util.ArrayList<org.xar.ck3.control.build.CompleteSourceGraph.ResolvedFile>();
        var copies=new java.util.ArrayList<org.xar.ck3.control.build.CompleteSourceGraphMaterializer.CopyRow>();
        var inventory=new java.util.ArrayList<ControlBuild.FileRef>();
        var selected=new java.util.ArrayList<IntegratedToolsSuccessor16.SelectedFile>();
        var host=IntegratedToolsGraph01.Group.HOST;var tools=IntegratedToolsGraph01.Group.TOOLS;
        int index=0;
        for(String target:List.of("build-tools/pom.xml","build-tools/src/main/java/Actual.java","contracts/pom.xml","other/pom.xml")) {
            var original=fixtureBytes("projection-original-"+index++,target.endsWith("pom.xml")?"<project xmlns=\"http://maven.apache.org/POM/4.0.0\"><modelVersion>4.0.0</modelVersion><artifactId>fixture</artifactId></project>":"class Actual { /* immutable "+index+" */ }");
            Path destination=root.resolve(target);java.nio.file.Files.createDirectories(destination.getParent());
            java.nio.file.Files.copy(Path.of(original.path()),destination);
            var before=org.xar.ck3.control.build.SharedSourceFiles.observe(Path.of(original.path()));
            var copied=org.xar.ck3.control.build.SharedSourceFiles.observe(destination);
            resolved.add(new org.xar.ck3.control.build.CompleteSourceGraph.ResolvedFile(target,original));
            copies.add(new org.xar.ck3.control.build.CompleteSourceGraphMaterializer.CopyRow(target,before,before,copied));
            inventory.add(copied.source());
            if(!target.startsWith("other/"))selected.add(new IntegratedToolsSuccessor16.SelectedFile(target.startsWith("build-tools/")?tools:host,target,original));
        }
        var baseline=List.of(copies.get(0).originalBefore());
        var proof=new org.xar.ck3.control.build.CompleteSourceGraphMaterializer.NativeProof("xar.complete-source-native-copy-proof/v1",machine,now,baseline,baseline,copies);
        var snapshot=new org.xar.ck3.control.build.CompleteSourceGraphAudit.NativeSnapshot("xar.complete-source-independent-native-snapshot/v1",machine,now,baseline,copies.stream().map(org.xar.ck3.control.build.CompleteSourceGraphMaterializer.CopyRow::destination).toList());
        var selection=new IntegratedToolsSuccessor16.ProjectionSelection("xar.integrated-tools-existing-projection-selection/v1",machine,selected);
        var absent=new IntegratedToolsGraph01.Preimage(IntegratedToolsGraph01.PreimageKind.ABSENT,null);
        var oldHost=new IntegratedToolsGraph01.Selection(host,"contracts/pom.xml",absent,absent,null,resolved.get(2).sourceRef(),"real historical source-only provenance",resolved.get(2).sourceRef());
        var oldTool=new IntegratedToolsGraph01.Selection(tools,"pom.xml",absent,absent,null,resolved.get(0).sourceRef(),"real historical source-only provenance",resolved.get(0).sourceRef());
        var pin=resolved.get(0).sourceRef();
        var base=new IntegratedToolsGraph01.Actual("xar.integrated-host-tools-source-map/v1",machine,now,"SOURCE_ONLY",pin,pin,pin,pin,"unqualified",1,1,pin.bytes()+oldHost.materializedRef().bytes(),0,List.of(pin),List.of(oldTool,oldHost));
        var graph=new org.xar.ck3.control.build.CompleteSourceGraph.SelectionProof(org.xar.ck3.control.build.CompleteSourceGraph.SELECTION_SCHEMA,org.xar.ck3.control.build.CompleteSourceGraph.SelectionStatus.SOURCE_SELECTION_ONLY,org.xar.ck3.control.build.CompleteSourceGraph.Profile.G2_FULL_PARITY_20261025_R7,resolved,List.of(),resolved.stream().mapToLong(row->row.sourceRef().bytes()).sum());
        var rows=IntegratedToolsSuccessor16.projectRows(machine,root,graph,proof,snapshot,inventory,base,selection);
        var scope=new IntegratedToolsSuccessor16.ProjectionScope("xar.integrated-tools-existing-projection-scope/v1",machine,"/root",new IntegratedToolsSuccessor16.TaskOwner("/root/tools_current"),java.time.Instant.now().plusSeconds(60).toString(),pin,pin,pin,pin,root.toString(),temporary.resolve("projection-metadata").toString(),4L<<20);
        var actual=IntegratedToolsSuccessor16.projectedMap(pin,scope,base,rows);
        Path output=temporary.resolve("projection-map.json");
        IntegratedToolsSuccessor16.writeProjection(output,m.writeValueAsBytes(actual));
        var read=m.readValue(java.nio.file.Files.readAllBytes(output),IntegratedToolsGraph01.Actual.class);
        assertEquals(actual,read);assertEquals(2,read.toolsSources());assertEquals(1,read.hostOverlaySources());
        assertEquals(0,read.conservativeSourceChargeBytes());assertTrue(read.status().contains("SOURCE_ONLY"));
        assertEquals(ControlBuild.sourceManifest(root.resolve("build-tools")),read.sources().stream().filter(row->row.group()==tools).map(IntegratedToolsGraph01.Selection::materializedRef).sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList());
        assertEquals(oldHost.originalPreimage(),read.sources().stream().filter(row->row.group()==host).findFirst().orElseThrow().originalPreimage());
        assertThrows(java.nio.file.FileAlreadyExistsException.class,()->IntegratedToolsSuccessor16.writeProjection(output,new byte[]{1}));
        var missing=new IntegratedToolsSuccessor16.ProjectionSelection(selection.schema(),machine,selected.subList(1,3));
        assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.projectRows(machine,root,graph,proof,snapshot,inventory,base,missing));
        assertThrows(IllegalArgumentException.class,()->new IntegratedToolsSuccessor16.ProjectionSelection(selection.schema(),machine,List.of(selected.get(0),selected.get(0),selected.get(2))));
        var incomplete=new org.xar.ck3.control.build.CompleteSourceGraphMaterializer.NativeProof(proof.schema(),machine,now,baseline,baseline,copies.subList(0,3));
        assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.projectRows(machine,root,graph,incomplete,snapshot,inventory,base,selection));
        var altered=new java.util.ArrayList<>(copies);var row=copies.get(0);
        altered.set(0,new org.xar.ck3.control.build.CompleteSourceGraphMaterializer.CopyRow(row.targetRelative(),row.originalBefore(),row.originalAfter(),row.originalBefore()));
        var alias=new org.xar.ck3.control.build.CompleteSourceGraphMaterializer.NativeProof(proof.schema(),machine,now,baseline,baseline,altered);
        assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.projectRows(machine,root,graph,alias,snapshot,inventory,base,selection));
        java.nio.file.Files.writeString(root.resolve("contracts/pom.xml"),"actual mutation");
        assertThrows(java.io.IOException.class,()->IntegratedToolsSuccessor16.projectRows(machine,root,graph,proof,snapshot,inventory,base,selection));
        for(var original:resolved)original.sourceRef().verify();
        var wire=m.valueToTree(scope);var object=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,wire);
        object.put("metadata_cap_bytes",true);assertThrows(java.io.IOException.class,()->m.treeToValue(object,IntegratedToolsSuccessor16.ProjectionScope.class));
        object.put("metadata_cap_bytes",4096);object.put("unknown_scope",1);
        assertThrows(java.io.IOException.class,()->m.treeToValue(object,IntegratedToolsSuccessor16.ProjectionScope.class));
        assertFalse(java.nio.file.Files.exists(Path.of(scope.outputRoot())));
    }


    /** Test-only entry for the exact complete producer suite before using the source-only operator. */
    public static void main(String[] args) throws Exception {
        if(args.length!=0)throw new IllegalArgumentException("Exact complete C16 producer suite; no selector arguments");
        var config=org.junit.platform.launcher.core.LauncherConfig.builder()
                .enableTestEngineAutoRegistration(false).enableLauncherSessionListenerAutoRegistration(false)
                .enableLauncherDiscoveryListenerAutoRegistration(false).enableTestExecutionListenerAutoRegistration(false)
                .enablePostDiscoveryFilterAutoRegistration(false).addTestEngines(new org.junit.jupiter.engine.JupiterTestEngine()).build();
        var request=org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(IntegratedToolsSuccessor16Test.class))
                .configurationParameter("junit.jupiter.execution.parallel.enabled","false")
                .configurationParameter("junit.jupiter.extensions.autodetection.enabled","false").build();
        var launcher=org.junit.platform.launcher.core.LauncherFactory.create(config);
        var plan=launcher.discover(request);var expected=new java.util.TreeSet<String>();var actual=new java.util.TreeSet<String>();
        for(var method:IntegratedToolsSuccessor16Test.class.getDeclaredMethods())
            if(method.isAnnotationPresent(Test.class))expected.add(method.getName());
        for(var root:plan.getRoots())for(var test:plan.getDescendants(root))if(test.isTest()) {
            var source=test.getSource().orElseThrow();
            if(!(source instanceof org.junit.platform.engine.support.descriptor.MethodSource method)
                    ||!method.getClassName().equals(IntegratedToolsSuccessor16Test.class.getName())||!actual.add(method.getMethodName()))
                throw new java.io.IOException("Foreign or duplicate producer test");
        }
        if(expected.isEmpty()||!actual.equals(expected))throw new java.io.IOException("Complete producer test discovery differs");
        var listener=new org.junit.platform.launcher.listeners.SummaryGeneratingListener();launcher.execute(plan,listener);
        var summary=listener.getSummary();summary.printTo(new java.io.PrintWriter(System.out,true));
        summary.printFailuresTo(new java.io.PrintWriter(System.err,true));
        if(summary.getTestsFoundCount()!=expected.size()||summary.getTestsStartedCount()!=expected.size()
                ||summary.getTestsSucceededCount()!=expected.size()||summary.getTestsFailedCount()!=0
                ||summary.getTestsSkippedCount()!=0||summary.getTestsAbortedCount()!=0
                ||summary.getContainersFailedCount()!=0||summary.getContainersSkippedCount()!=0||summary.getContainersAbortedCount()!=0)
            throw new java.io.IOException("Complete actual C16 producer suite failed");
    }

}
