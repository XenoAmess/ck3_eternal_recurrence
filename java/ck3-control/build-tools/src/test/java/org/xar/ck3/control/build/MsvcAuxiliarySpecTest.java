package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class MsvcAuxiliarySpecTest {
    @TempDir Path root;
    private static ControlBuild.FileRef ref(String name) {
        return new ControlBuild.FileRef(Path.of("D:/msvc-test",name).toAbsolutePath().toString(),1024,"a".repeat(64));
    }
    private static SourceGraphCommandSpecProducer.Intent intent(WindowsJobProcess.RootExitDrainPolicy drain) {
        return new SourceGraphCommandSpecProducer.Intent("machine-test","/root/lifecycle","/root/lifecycle","slot1",null,
                "msvc-fixture",ref("standing.json"),ref("SharedOwnedCommand.java"),ref("cl.exe"),List.of("/nologo","/c","fixture.c"),
                Path.of("D:/msvc-test").toAbsolutePath().toString(),Map.of(),List.of(),30,256L<<20,drain);
    }
    private static SourceGraphCommandSpecProducer.Slot slot() {
        return new SourceGraphCommandSpecProducer.Slot("slot1",Path.of("D:/admitted-msvc-slot").toAbsolutePath());
    }
    private static SourceGraphCommandSpecProducer.Intent otherRoot(String name,List<ControlBuild.FileRef> inputs) {
        var command=intent(WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS);
        return new SourceGraphCommandSpecProducer.Intent(command.machineId(),command.owner(),command.coordinator(),
                command.slotId(),command.borrowedSlotId(),command.runId(),command.standingRef(),command.launcherSourceRef(),
                ref(name),command.arguments(),command.cwd(),command.environment(),inputs,command.timeoutSeconds(),
                command.memoryLimitBytes(),command.rootExitDrainPolicy());
    }
    @Test void actualV3ProducerParserAndBindingCodecRoundTripWhileV2KeepsOriginalShape() throws Exception {
        var mapper=ControlBuild.strictMapper();var entry=intent(WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS);
        byte[] old=SourceGraphCommandSpecProducer.produce(slot(),entry);
        assertEquals("xar.shared-owned-command-spec/v2",mapper.readTree(old).path("schema").textValue());
        assertFalse(mapper.readTree(old).has("msvc_auxiliary_binding"));
        assertNull(SharedOwnedCommand.parseRequest(mapper.readTree(old)).msvcAuxiliaryBinding());
        byte[] bytes=SourceGraphCommandSpecProducer.produceMsvc(slot(),entry,MsvcAuxiliaryPolicyTest.execution());
        var request=SharedOwnedCommand.parseRequest(mapper.readTree(bytes));
        assertEquals("xar.shared-owned-command-spec/v3",request.schema());
        assertEquals(MsvcAuxiliaryPolicyTest.execution(),request.msvcAuxiliaryBinding());
        assertEquals(request.executable().path(),request.msvcAuxiliaryBinding().rootExecutable().path());
        for(String name:List.of("cmake.exe","ninja.exe","python.exe","dumpbin.exe","lib.exe","fixture.exe")) {
            var binding=new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1",
                    MsvcAuxiliaryPolicyTest.binding(),ref(name));
            byte[] explicit=SourceGraphCommandSpecProducer.produceMsvc(slot(),otherRoot(name,List.of(ref("cl.exe"))),binding);
            assertEquals(binding,SharedOwnedCommand.parseRequest(mapper.readTree(explicit)).msvcAuxiliaryBinding());
            byte[] unchanged=SourceGraphCommandSpecProducer.produce(slot(),otherRoot(name,List.of(ref("cl.exe"))));
            assertNull(SharedOwnedCommand.parseRequest(mapper.readTree(unchanged)).msvcAuxiliaryBinding());
            assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.produceMsvc(slot(),otherRoot(name,List.of()),binding));
        }
    }
    @Test void missingNullWrongTypeAndCrossSchemaBindingCannotOptIn() throws Exception {
        var mapper=ControlBuild.strictMapper();byte[] bytes=SourceGraphCommandSpecProducer.produceMsvc(slot(),
                intent(WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS),MsvcAuxiliaryPolicyTest.execution());
        ObjectNode valid=(ObjectNode)mapper.readTree(bytes);
        ObjectNode missing=valid.deepCopy();missing.remove("msvc_auxiliary_binding");
        ObjectNode nul=valid.deepCopy();nul.putNull("msvc_auxiliary_binding");
        ObjectNode wrong=valid.deepCopy();wrong.put("msvc_auxiliary_binding",true);
        ObjectNode legacy=valid.deepCopy();legacy.put("schema","xar.shared-owned-command-spec/v2");
        for(ObjectNode bad:List.of(missing,nul,wrong,legacy))assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(bad));
    }
    @Test void compilerMismatchAndCombinationWithUntilDeadlineAreRejectedBeforeExecution() throws Exception {
        var mapper=ControlBuild.strictMapper();
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.produceMsvc(slot(),
                intent(WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE),MsvcAuxiliaryPolicyTest.execution()));
        ObjectNode wire=(ObjectNode)mapper.readTree(SourceGraphCommandSpecProducer.produceMsvc(slot(),
                intent(WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS),MsvcAuxiliaryPolicyTest.execution()));
        ((ObjectNode)wire.path("executable")).put("sha256","b".repeat(64));
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(wire));
    }

    @Test void msvcAndUtf8ChildGenerationsCannotCaptureEachOthersFields() throws Exception {
        var mapper=ControlBuild.strictMapper();
        ObjectNode wire=(ObjectNode)mapper.readTree(SourceGraphCommandSpecProducer.produceMsvc(slot(),
                intent(WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS),MsvcAuxiliaryPolicyTest.execution()));
        ObjectNode extra=wire.deepCopy();extra.putNull("java_invocation");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(extra));
        ObjectNode relabeled=wire.deepCopy();relabeled.put("schema","xar.shared-owned-command-spec/v4");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(relabeled));
        ObjectNode unknown=wire.deepCopy();unknown.put("schema","xar.shared-owned-command-spec/v5");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(unknown));
    }

    private ControlBuild.FileRef plain(String name) throws IOException {
        Path file=root.resolve(name);Files.writeString(file,"software declaration fixture, never executed: "+name);
        return ControlBuild.FileRef.measure(file);
    }
    private ControlBuild.FileRef json(String name,ObjectNode value) throws IOException {
        Path file=root.resolve(name);Files.write(file,ControlBuild.strictMapper().writeValueAsBytes(value));
        return ControlBuild.FileRef.measure(file);
    }
    /** Original production readers run here; declared fixture evidence cannot qualify an executor or native image. */
    private SourceGraphCommandSpecProducer.MsvcEntryIntent wholeEntry() throws IOException {
        var mapper=ControlBuild.strictMapper();var compiler=plain("cl.exe");plain("vctip.exe");plain("mspdbsrv.exe");
        var count=new java.util.concurrent.atomic.AtomicInteger();
        var tools=MsvcAuxiliaryPolicy.bind(Path.of(compiler.path()),Instant.now().plusSeconds(60),count::incrementAndGet);
        assertTrue(count.get()>0);
        var java=plain("java.exe");var launcher=plain("SharedOwnedCommand.java");
        var runtime=new java.util.ArrayList<ControlBuild.FileRef>();
        for(int index=0;index<6;index++)runtime.add(plain("runtime-"+index+".jar"));
        ObjectNode delivery=mapper.createObjectNode();delivery.put("schema","fixture.delivery/v1");
        delivery.put("machine_id","fixture-machine-123");delivery.put("status","DECLARED_FIXTURE_METADATA_ONLY");
        delivery.set("complete_runtime",mapper.valueToTree(runtime));var deliveryRef=json("delivery.json",delivery);
        ObjectNode standing=mapper.createObjectNode();standing.put("schema","fixture.standing/v1");
        standing.put("machine_id","fixture-machine-123");standing.put("status","ISSUED_FIXTURE_METADATA_ONLY");
        standing.put("review_at_utc",Instant.now().plusSeconds(120).toString());
        standing.put("native_tmp_root",Files.createDirectory(root.resolve("native-tmp")).toString());
        standing.put("private_temporary_aggregate_root",root.resolve("private-temporary").toString());
        standing.set("source_grant_ref",mapper.valueToTree(plain("grant.json")));
        standing.set("capacity_release_ref",mapper.valueToTree(plain("capacity.json")));
        standing.set("qualified_tools_ref",mapper.valueToTree(plain("whole-build.json")));
        standing.set("qualified_own_readback_ref",mapper.valueToTree(plain("own-readback.json")));
        standing.set("runtime_closure",mapper.valueToTree(runtime));standing.set("allowed_executables",mapper.valueToTree(List.of(java,compiler)));
        ObjectNode slot=standing.putArray("slots").addObject();slot.put("slot_id","fixture-slot");slot.put("output_root",root.resolve("commands").toString());
        slot.put("output_cap_bytes",1L<<20);slot.put("worker_memory_limit_bytes",512L<<20);slot.put("outer_memory_budget_bytes",256L<<20);
        slot.put("timeout_seconds",180);slot.put("serial",true);
        var binding=new SourceGraphCommandSpecProducer.BindingIntent("fixture-machine-123",launcher,json("standing.json",standing),deliveryRef,
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture.standing/v1","ISSUED_FIXTURE_METADATA_ONLY"),
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture.delivery/v1","DECLARED_FIXTURE_METADATA_ONLY"));
        var entry=new SourceGraphCommandSpecProducer.EntryIntent(binding,"/root/parity_ci","/root","fixture-slot",null,"msvc-test",
                compiler,List.of("/nologo","/c","fixture.c"),root.toString(),Map.of(),List.of(),60,256L<<20,
                WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS);
        return new SourceGraphCommandSpecProducer.MsvcEntryIntent(entry,
                new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1",tools,compiler));
    }

    @Test void actualWholeEntryCliAndReadbackKeepExplicitBindingWhileStartingNoChild() throws Exception {
        var original=wholeEntry();var mapper=ControlBuild.strictMapper();ObjectNode wire=mapper.valueToTree(original);
        assertEquals(original,SourceGraphCommandSpecProducer.decodeMsvcEntryIntent(wire));
        var input=json("entry.json",wire);
        SourceGraphCommandSpecProducer.main(new String[]{"msvc",input.path(),Long.toString(input.bytes()),input.sha256(),
                root.resolve("binding.json").toString(),root.resolve("spec.json").toString(),root.resolve("invocation.json").toString()});
        var spec=SharedOwnedCommand.parseRequest(mapper.readTree(Files.readAllBytes(root.resolve("spec.json"))));
        assertEquals(original.msvcAuxiliaryBinding(),spec.msvcAuxiliaryBinding());assertNull(spec.javaInvocation());
        assertEquals("xar.shared-owned-command-spec/v3",spec.schema());
        var invocation=SourceGraphCommandSpecProducer.readInvocation(ControlBuild.FileRef.measure(root.resolve("invocation.json")));
        assertNull(invocation.javaInvocation());assertEquals("xar.shared-owned-command-invocation/v2",invocation.schema());
        assertFalse(Files.exists(root.resolve("commands")));input.verify();
        ObjectNode mixed=wire.deepCopy();((ObjectNode)mixed.get("command")).putNull("java_invocation");
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.decodeMsvcEntryIntent(mixed));
    }
}
