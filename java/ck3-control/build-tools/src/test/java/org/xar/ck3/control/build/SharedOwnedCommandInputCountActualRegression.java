package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Mandatory after general Tools verify and Own; a class-directory JVM cannot qualify this launcher. */
public final class SharedOwnedCommandInputCountActualRegression {
    @TempDir Path temporary;
    private static final String PREFIX="xar.sharedOwned.largeInputs.";

    private static FileRef propertyRef(String kind)throws IOException {
        String path=System.getProperty(PREFIX+kind+".path"),count=System.getProperty(PREFIX+kind+".bytes"),
                sha=System.getProperty(PREFIX+kind+".sha256");
        if(path==null||count==null||sha==null)throw new IOException("Actual qualified binding and controlled large-input Spec are mandatory; no skip");
        FileRef ref=SharedOwnedCommand.cliRef(path,count,sha);ref.verify();return ref;
    }
    private ObjectNode shape(int count) {
        var json=ControlBuild.strictMapper();var value=json.createObjectNode();
        value.put("schema","xar.shared-owned-command-spec/v2");value.put("machine_id","parser-boundary-only");
        value.put("owner","/root/input_count");value.put("coordinator","/root/input_count");value.put("slot_id","test");
        value.putNull("borrowed_slot_id");value.put("run_id","count01");
        for(String name:List.of("standing_ref","launcher_source_ref","executable"))value.set(name,reference(name));
        value.putArray("arguments");value.put("cwd",temporary.toString());value.putObject("environment");
        var inputs=value.putArray("inputs");for(int i=0;i<count;i++)inputs.add(reference("input-"+i));
        value.put("output_root",temporary.resolve("output").toString());value.put("timeout_seconds",30);
        value.put("memory_limit_bytes",268435456);value.put("root_exit_drain_policy","UNTIL_COMMAND_DEADLINE");
        value.putNull("operation_card_ref");value.put("temporary_policy","SLOT_PRIVATE");return value;
    }
    private ObjectNode reference(String name) {
        return ControlBuild.strictMapper().createObjectNode().put("path",temporary.resolve(name).toString())
                .put("bytes",0).put("sha256","0".repeat(64));
    }
    @Test void exact2048BoundaryRetainsStrictV2FieldsAndTypes()throws Exception {
        var accepted=shape(2048);
        assertEquals(2048,SharedOwnedCommand.parseRequest(accepted).inputs().size());
        assertTrue(ControlBuild.strictMapper().writeValueAsBytes(accepted).length<1048576);
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(shape(2049)));
        var unknown=shape(513);unknown.put("input_manifest_alias","not-a-native-witness");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(unknown));
        var wrong=shape(513);((ObjectNode)wrong.get("inputs").get(0)).put("bytes",true);
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(wrong));
    }
    @Test void realLauncherWitnessesEveryInputRejectsOversizeAndCannotReplayUnknownOutput()throws Exception {
        var binding=propertyRef("binding");var spec=propertyRef("spec");
        if(spec.bytes()>1048576)throw new IOException("Existing1MiB Spec limit is unchanged");
        var json=ControlBuild.strictMapper();var wire=(ObjectNode)json.readTree(Files.readAllBytes(Path.of(spec.path())));
        var request=SharedOwnedCommand.parseRequest(wire);
        assertTrue(request.inputs().size()>512&&request.inputs().size()<=2048);
        assertEquals("xar.shared-owned-command-spec/v2",request.schema());
        assertEquals(FileRef.measure(Path.of(System.getenv("SystemRoot")).resolve("System32/hostname.exe")),request.executable());
        assertTrue(request.arguments().isEmpty());
        assertTrue(request.timeoutSeconds()<=120&&request.memoryLimitBytes()<=512L<<20);
        assertFalse(Files.exists(request.outputRoot()));
        var oversized=wire.deepCopy();var tooMany=oversized.putArray("inputs");
        for(int i=0;i<2049;i++)tooMany.add(wire.get("inputs").get(i%request.inputs().size()).deepCopy());
        Path overflow=temporary.resolve("over-limit-spec.json");Files.write(overflow,json.writeValueAsBytes(oversized));
        var rejected=assertThrows(IOException.class,()->SharedOwnedCommand.execute(binding,FileRef.measure(overflow)));
        assertTrue(rejected.getMessage().contains("2048"));assertFalse(Files.exists(request.outputRoot()));
        var unknown=wire.deepCopy();unknown.put("manifest_alias","not-individual-identities");
        Path unknownPath=temporary.resolve("unknown-spec.json");Files.write(unknownPath,json.writeValueAsBytes(unknown));
        assertThrows(IOException.class,()->SharedOwnedCommand.execute(binding,FileRef.measure(unknownPath)));
        assertFalse(Files.exists(request.outputRoot()));
        var outcome=SharedOwnedCommand.execute(binding,spec);
        assertEquals(SharedOwnedCommand.Status.PASS,outcome.status());assertEquals(0,outcome.exitCode());
        var terminalRef=outcome.terminalRef();terminalRef.verify();assertTrue(terminalRef.bytes()<=6L<<20);
        var terminal=json.readTree(Files.readAllBytes(Path.of(terminalRef.path())));
        assertTrue(terminal.get("child_started").booleanValue());assertEquals("PASS",terminal.get("status").textValue());
        for(String field:List.of("input_precheck","input_postcheck","runtime_postcheck"))assertEquals("MATCH",terminal.get(field).textValue());
        var child=json.treeToValue(terminal.get("child"),WindowsJobProcess.CommandResult.class);
        assertTrue(child.passed());assertEquals(0,child.exitCode());assertEquals(0,child.accounting().activeProcesses());
        var witnesses=json.treeToValue(terminal.get("input_before"),SharedSourceFiles.Witness[].class);
        assertEquals(request.inputs().size()+2,witnesses.length);
        for(int i=0;i<witnesses.length;i++) {
            SharedSourceFiles.assertUnchanged(witnesses[i]);
            if(i>=2)assertEquals(request.inputs().get(i-2),witnesses[i].source());
        }
        var retained=SharedSourceFiles.observe(Path.of(terminalRef.path()));
        assertThrows(IOException.class,()->SharedOwnedCommand.execute(binding,spec));
        SharedSourceFiles.assertUnchanged(retained);spec.verify();binding.verify();
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("No alternate actual selection");
        var request=org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(SharedOwnedCommandInputCountActualRegression.class))
                .configurationParameter("junit.jupiter.execution.parallel.enabled","false").build();
        var listener=new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        org.junit.platform.launcher.core.LauncherFactory.create().execute(request,listener);
        var summary=listener.getSummary();summary.printTo(new java.io.PrintWriter(System.out,true));
        summary.printFailuresTo(new java.io.PrintWriter(System.err,true));
        if(summary.getTestsFoundCount()!=2||summary.getTestsStartedCount()!=2||summary.getTestsSucceededCount()!=2
                ||summary.getTestsFailedCount()!=0||summary.getTestsSkippedCount()!=0||summary.getTestsAbortedCount()!=0
                ||summary.getContainersFailedCount()!=0||summary.getTotalFailureCount()!=0)
            throw new IllegalStateException("Mandatory post-P actual launcher regression requires2 successes and0 failures/skips/aborts");
        System.out.println("PASS_SHARED_OWNED_INPUTS_2048_ACTUAL_JUNIT_2");
    }
}
