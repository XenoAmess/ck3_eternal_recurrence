package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class SharedOwnedCommandTest {
    @TempDir Path root;
    private static final String HASH="0".repeat(64);

    private ObjectNode reference(String name) {
        ObjectNode ref=ControlBuild.strictMapper().createObjectNode();
        ref.put("path",root.resolve(name).toString());ref.put("bytes",0);ref.put("sha256",HASH);return ref;
    }
    private ObjectNode binding() {
        ObjectNode value=ControlBuild.strictMapper().createObjectNode();
        value.put("schema",SharedOwnedCommandBinding.SCHEMA);value.put("machine_id","fixture-machine-123");
        value.set("launcher_source_ref",reference("SharedOwnedCommand.java"));
        value.set("standing_ref",reference("runtime01.json"));value.set("delivery_ref",reference("delivery01.json"));
        value.put("native_temporary_root",root.resolve("native-tmp").toString());
        value.put("private_temporary_aggregate_root",root.resolve("private-tmp").toString());
        value.putObject("standing_expectation").put("schema","standing/v1").put("status","ADMITTED01");
        value.putObject("delivery_expectation").put("schema","delivery/v1").put("status","ACCEPTED01");return value;
    }
    private ObjectNode request() {
        ObjectNode value=ControlBuild.strictMapper().createObjectNode();
        value.put("schema","xar.shared-owned-command-spec/v2");value.put("machine_id","fixture-machine-123");
        value.put("owner","/root/test_owner");value.put("coordinator","/root/g2_java_delivery");value.put("slot_id","common-0");
        value.putNull("borrowed_slot_id");value.put("run_id","finite01");value.set("standing_ref",reference("runtime01.json"));
        value.set("launcher_source_ref",reference("SharedOwnedCommand.java"));value.set("executable",reference("java.exe"));
        value.putArray("arguments").add("-version");value.put("cwd",root.toString());value.putObject("environment");
        value.putArray("inputs");value.put("output_root",root.resolve("output/test_owner/finite01").toString());
        value.put("timeout_seconds",1);value.put("memory_limit_bytes",268435456);
        value.put("root_exit_drain_policy","UNTIL_COMMAND_DEADLINE");value.putNull("operation_card_ref");
        value.put("temporary_policy","SLOT_PRIVATE");return value;
    }

    @Test void exactBindingRoundTripRetainsAllTypedFields() throws Exception {
        SharedOwnedCommandBinding first=SharedOwnedCommandBinding.parse(binding());
        JsonNode encoded=first.toJson();
        SharedOwnedCommandBinding second=SharedOwnedCommandBinding.parse(encoded);
        assertEquals(first,second);assertEquals(root.resolve("private-tmp"),second.privateTemporaryAggregateRoot());
        assertEquals("fixture-machine-123",second.machineId());
    }
    @Test void newWindowUsesNewDataWithSamePackagedSource() throws Exception {
        ObjectNode first=binding(), next=first.deepCopy();
        next.set("standing_ref",reference("runtime02.json"));next.set("delivery_ref",reference("delivery02.json"));
        ((ObjectNode)next.get("standing_expectation")).put("status","ADMITTED02");
        ((ObjectNode)next.get("delivery_expectation")).put("status","ACCEPTED02");
        SharedOwnedCommandBinding a=SharedOwnedCommandBinding.parse(first),b=SharedOwnedCommandBinding.parse(next);
        assertEquals(a.launcherSourceRef(),b.launcherSourceRef());assertNotEquals(a.standingRef(),b.standingRef());
        ObjectNode actual=ControlBuild.strictMapper().createObjectNode().put("schema","standing/v1").put("machine_id",b.machineId()).put("status","ADMITTED02");
        SharedOwnedCommandBinding.verifyAuthority(actual,b.standingExpectation(),b.machineId());
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.verifyAuthority(actual,a.standingExpectation(),a.machineId()));
    }
    @Test void missingUnknownAndNullBindingFieldsAreRejected() {
        ObjectNode missing=binding();missing.remove("standing_ref");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(missing));
        ObjectNode extra=binding();extra.put("legacy_runtime_alias","old");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(extra));
        ObjectNode nullable=binding();nullable.putNull("delivery_ref");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(nullable));
    }
    @Test void referenceBytesRejectBooleanFractionAndOutOfLongRange() throws Exception {
        for(String bad:List.of("true","1.0","9223372036854775808")) {
            ObjectNode value=binding();
            ((ObjectNode)value.get("standing_ref")).set("bytes",ControlBuild.strictMapper().readTree(bad));
            assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(value),bad);
        }
    }
    @Test void nestedUnknownFieldsAndRelativeRootsAreRejected() {
        ObjectNode extra=binding();((ObjectNode)extra.get("standing_expectation")).put("expiry_alias","old");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(extra));
        ObjectNode relative=binding();relative.put("native_temporary_root","relative-tmp");
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.parse(relative));
    }
    @Test void exactBindingReaderRejectsChangedFileAndOversize() throws Exception {
        Path path=root.resolve("binding.json");Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(binding()));
        FileRef pin=FileRef.measure(path);assertEquals("fixture-machine-123",SharedOwnedCommandBinding.read(pin).machineId());
        Files.writeString(path,"{}");assertThrows(IOException.class,()->SharedOwnedCommandBinding.read(pin));
        FileRef large=new FileRef(path.toString(),65537,HASH);
        assertThrows(IOException.class,()->SharedOwnedCommandBinding.read(large));
    }
    @Test void requestV2PreservesExplicitNullAndStructuredArguments() throws Exception {
        ObjectNode value=request();SharedOwnedCommand.Request parsed=SharedOwnedCommand.parseRequest(value);
        assertNull(parsed.borrowedSlotId());assertNull(parsed.operationCardRef());assertEquals(List.of("-version"),parsed.arguments());
        assertEquals(SharedOwnedCommand.TemporaryPolicy.SLOT_PRIVATE,parsed.temporaryPolicy());
        value.remove("operation_card_ref");assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(value));
    }
    @Test void requestV2RejectsWrongScalarTypesAndUnknownKeys() throws Exception {
        for(String key:List.of("timeout_seconds","memory_limit_bytes")) {
            ObjectNode booleanValue=request();booleanValue.put(key,true);assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(booleanValue));
            ObjectNode fractionValue=request();fractionValue.put(key,1.0);assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(fractionValue));
        }
        ObjectNode extra=request();extra.put("compatibility_alias","old");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(extra));
        ObjectNode environment=request();((ObjectNode)environment.get("environment")).put("VALUE",1);
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(environment));
    }
    private ObjectNode rootRequest() {
        var value=request();value.put("schema","xar.shared-owned-command-spec/v5");
        value.putArray("arguments");var input=value.putObject("prepared_root");
        for(String key:List.of("package_manifest","invocation","root_runtime_authorization_ref")) {
            var pin=reference(key+".json");pin.put("bytes",1);input.set(key,pin);((com.fasterxml.jackson.databind.node.ArrayNode)value.get("inputs")).add(pin.deepCopy());
        }
        return value;
    }
    @Test void rootV5StrictProducerConsumerRoundTripKeepsOnePreparedInputAndNoSecondEngine()throws Exception {
        var wire=rootRequest();var request=SharedOwnedCommand.parseRequest(wire);
        assertNotNull(request.preparedRoot());assertNull(request.javaInvocation());assertNull(request.msvcAuxiliaryBinding());
        assertEquals(request.preparedRoot(),SharedOwnedCommand.decodePreparedRoot(ControlBuild.strictMapper().valueToTree(request.preparedRoot())));
        for(String alternate:List.of("java_invocation","msvc_auxiliary_binding","raw_argv")) {
            var changed=wire.deepCopy();changed.putNull(alternate);
            assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(changed),alternate);
        }
        var argv=wire.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)argv.get("arguments")).add("-version");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(argv));
        var environment=wire.deepCopy();((ObjectNode)environment.get("environment")).put("TMP",root.toString());
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(environment));
        var missing=wire.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)missing.get("inputs")).remove(0);
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(missing));
        var duplicate=wire.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)duplicate.get("inputs")).add(duplicate.path("inputs").get(0).deepCopy());
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(duplicate));
    }
    @Test void rootPreparedOriginalsRejectWrongTypesAliasesMissingFieldsAndZeroByteInputs()throws Exception {
        var original=(ObjectNode)rootRequest().get("prepared_root");
        for(String key:List.of("package_manifest","invocation","root_runtime_authorization_ref")) {
            var missing=original.deepCopy();missing.remove(key);assertThrows(IOException.class,()->SharedOwnedCommand.decodePreparedRoot(missing));
            var nullable=original.deepCopy();nullable.putNull(key);assertThrows(IOException.class,()->SharedOwnedCommand.decodePreparedRoot(nullable));
            for(String bad:List.of("true","1.0","0","9223372036854775808")) {
                var changed=original.deepCopy();((ObjectNode)changed.get(key)).set("bytes",ControlBuild.strictMapper().readTree(bad));
                assertThrows(IOException.class,()->SharedOwnedCommand.decodePreparedRoot(changed),key+bad);
            }
        }
        var alias=original.deepCopy();alias.set("invocation",alias.get("package_manifest").deepCopy());
        assertThrows(IOException.class,()->SharedOwnedCommand.decodePreparedRoot(alias));
        var unknown=original.deepCopy();unknown.put("legacy_invocation","elsewhere");
        assertThrows(IOException.class,()->SharedOwnedCommand.decodePreparedRoot(unknown));
    }
    @Test void preparedRootCommandIsRejectedOnEveryAdmittedFieldDriftInsteadOfRebuilt()throws Exception {
        var request=SharedOwnedCommand.parseRequest(rootRequest());Path out=request.outputRoot(),tmp=root.resolve("tmp"),jna=root.resolve("jna");
        var paths=new org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.ManagedCommandPaths(out.resolve("stdout.log"),out.resolve("stderr.log"),tmp,jna,request.memoryLimitBytes());
        var prepared=java.util.Map.of("TEMP",tmp.toString(),"TMP",tmp.toString());
        var environment=java.util.Map.of("TEMP",tmp.toString(),"TMP",tmp.toString(),"PYTHONDONTWRITEBYTECODE","1");
        var arguments=List.of("-Djava.io.tmpdir="+tmp,"-Djna.tmpdir="+jna,"-jar","actual.jar","input","1",HASH);
        var actual=new WindowsJobProcess.CommandSpec(Path.of(request.executable().path()),arguments,request.cwd(),environment,paths.stdout(),paths.stderr(),request.memoryLimitBytes());
        SharedOwnedCommand.requirePreparedRootCommand(request,actual,paths,prepared);
        for(var changed:List.of(
                new WindowsJobProcess.CommandSpec(root.resolve("other.exe"),arguments,actual.cwd(),environment,actual.stdout(),actual.stderr(),actual.memoryLimitBytes()),
                new WindowsJobProcess.CommandSpec(actual.executable(),arguments,root.resolve("other-cwd"),environment,actual.stdout(),actual.stderr(),actual.memoryLimitBytes()),
                new WindowsJobProcess.CommandSpec(actual.executable(),arguments,actual.cwd(),java.util.Map.of("TMP",tmp.toString()),actual.stdout(),actual.stderr(),actual.memoryLimitBytes()),
                new WindowsJobProcess.CommandSpec(actual.executable(),arguments,actual.cwd(),environment,out.resolve("other-out"),actual.stderr(),actual.memoryLimitBytes()),
                new WindowsJobProcess.CommandSpec(actual.executable(),arguments,actual.cwd(),environment,actual.stdout(),out.resolve("other-err"),actual.memoryLimitBytes()),
                new WindowsJobProcess.CommandSpec(actual.executable(),arguments,actual.cwd(),environment,actual.stdout(),actual.stderr(),actual.memoryLimitBytes()+1),
                new WindowsJobProcess.CommandSpec(actual.executable(),List.of("-Djava.io.tmpdir="+jna,"-Djna.tmpdir="+tmp),actual.cwd(),environment,actual.stdout(),actual.stderr(),actual.memoryLimitBytes()))) {
            assertThrows(IOException.class,()->SharedOwnedCommand.requirePreparedRootCommand(request,changed,paths,prepared));
        }
    }
    @Test void alternateRootPreparerCannotReadInputsOrReachAChild() {
        var missing=new FileRef(root.resolve("must-not-read.json").toString(),1,HASH);
        IOException rejected=assertThrows(IOException.class,()->SharedOwnedCommand.executePreparedRoot(missing,inputs->{
            fail("Unqualified preparer was entered");throw new IOException("not reached");
        }));
        assertTrue(rejected.getMessage().contains("fixed named private LS"));
    }
    @Test void rootInvocationPureDecoderRejectsScalarCoercionDuplicateUnknownAndTrailingJson()throws Exception {
        var prepared=SharedOwnedCommand.parseRequest(rootRequest()).preparedRoot();
        var original=new SourceGraphCommandSpecProducer.RootInvocation("xar.shared-owned-root-invocation/v1","fixture-machine-123",
                new FileRef(root.resolve("binding.json").toString(),1,HASH),new FileRef(root.resolve("spec.json").toString(),1,HASH),prepared);
        var mapper=ControlBuild.strictMapper();var wire=(ObjectNode)mapper.valueToTree(original);
        assertEquals(original,SourceGraphCommandSpecProducer.decodeRootInvocation(wire));
        var bad=wire.deepCopy();((ObjectNode)bad.get("spec_ref")).put("bytes",1.0);
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.decodeRootInvocation(bad));
        var unknown=wire.deepCopy();unknown.put("argv","not admitted");
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.decodeRootInvocation(unknown));
        String json=mapper.writeValueAsString(wire);
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.decodeRootInvocation(mapper.readTree(json+" {}")));
        assertThrows(IOException.class,()->mapper.readTree("{\"schema\":\"duplicate\","+json.substring(1)));
    }
    @Test void rootV5CannotBeReadAsLegacyWholeEntryOrUtf8Output()throws Exception {
        Path rootWire=root.resolve("root-wire.json");
        var prepared=SharedOwnedCommand.parseRequest(rootRequest()).preparedRoot();
        Files.write(rootWire,ControlBuild.strictMapper().writeValueAsBytes(new SourceGraphCommandSpecProducer.RootInvocation(
                "xar.shared-owned-root-invocation/v1","fixture-machine-123",new FileRef(root.resolve("binding.json").toString(),1,HASH),
                new FileRef(root.resolve("spec.json").toString(),1,HASH),prepared)));
        assertThrows(Exception.class,()->SourceGraphCommandSpecProducer.readInvocation(FileRef.measure(rootWire)));
        var incomplete=ControlBuild.strictMapper().createObjectNode().put("schema","xar.shared-owned-command-terminal/v5");
        Path terminal=root.resolve("incomplete-v5.json");Files.write(terminal,ControlBuild.strictMapper().writeValueAsBytes(incomplete));
        assertThrows(IOException.class,()->SharedCommandOutputReader.read(FileRef.measure(terminal),1024));
    }
    @Test void rootReaderConsumesOriginalV5RejectionAfterWindowExpiryAndRejectsInventedPassOrCoercedEvidence()throws Exception {
        var mapper=ControlBuild.strictMapper();var jars=new java.util.ArrayList<FileRef>();
        for(int index=0;index<6;index++) {
            Path jar=root.resolve("runtime-"+index+".jar");var manifest=new java.util.jar.Manifest();
            manifest.getMainAttributes().putValue("Manifest-Version","1.0");
            try(var output=new java.util.jar.JarOutputStream(Files.newOutputStream(jar),manifest)) {
                output.putNextEntry(new java.util.jar.JarEntry("fixture.txt"));output.write(index);output.closeEntry();
            }
            jars.add(FileRef.measure(jar));
        }
        Path packageFile=root.resolve("package.json"),finiteFile=root.resolve("finite.json");
        Files.writeString(packageFile,"{}");Files.writeString(finiteFile,"{}");
        FileRef packageRef=FileRef.measure(packageFile),finiteRef=FileRef.measure(finiteFile);
        Path standingFile=root.resolve("standing.json"),deliveryFile=root.resolve("delivery.json"),launcherFile=root.resolve("SharedOwnedCommand.java");
        Files.writeString(launcherFile,"fixture source");
        var standingWire=mapper.createObjectNode().put("schema","standing/v1").put("status","ADMITTED01").put("machine_id","fixture-machine-123");
        standingWire.set("runtime_closure",mapper.valueToTree(jars));Files.write(standingFile,mapper.writeValueAsBytes(standingWire));
        var deliveryWire=mapper.createObjectNode().put("schema","delivery/v1").put("status","ACCEPTED01").put("machine_id","fixture-machine-123");
        deliveryWire.set("complete_runtime",mapper.valueToTree(jars));Files.write(deliveryFile,mapper.writeValueAsBytes(deliveryWire));
        FileRef standing=FileRef.measure(standingFile),delivery=FileRef.measure(deliveryFile),launcher=FileRef.measure(launcherFile);
        var requestWire=rootRequest();requestWire.set("standing_ref",mapper.valueToTree(standing));requestWire.set("launcher_source_ref",mapper.valueToTree(launcher));
        Path javaFile=root.resolve("java.exe");Files.writeString(javaFile,"not executed");FileRef javaRef=FileRef.measure(javaFile);
        requestWire.set("executable",mapper.valueToTree(javaRef));
        var bound=new SharedOwnedCommandBinding(SharedOwnedCommandBinding.SCHEMA,"fixture-machine-123",launcher,standing,delivery,
                root.resolve("native-tmp"),root.resolve("private-tmp"),new SharedOwnedCommandBinding.AuthorityExpectation("standing/v1","ADMITTED01"),
                new SharedOwnedCommandBinding.AuthorityExpectation("delivery/v1","ACCEPTED01"));
        Path bindingFile=root.resolve("root-binding.json");Files.write(bindingFile,mapper.writeValueAsBytes(bound.toJson()));
        var authority=new SourceGraphCommandSpecProducer.RootRuntimeAuthorization(
                "xar.root-prepared-launch-runtime-authorization/v1","ROOT_FINITE_SHARED_RUNTIME_AUTHORIZED","fixture-machine-123",
                "/root/test_owner","2000-01-01T00:00:00Z",standing,delivery,
                packageRef,finiteRef,List.of(),new SourceGraphCommandSpecProducer.RootClasspath(jars,jars),
                java.util.Arrays.stream(SourceGraphCommandSpecProducer.RootProvider.values()).map(role->
                        new SourceGraphCommandSpecProducer.RootProviderBinding(role,jars.getFirst())).toList());
        Path authorityFile=root.resolve("authority.json");Files.write(authorityFile,mapper.writeValueAsBytes(authority));
        var prepared=new SharedOwnedCommand.PreparedRootInputs(packageRef,finiteRef,FileRef.measure(authorityFile));
        requestWire.set("prepared_root",mapper.valueToTree(prepared));var inputs=requestWire.putArray("inputs");
        for(FileRef ref:List.of(packageRef,finiteRef,prepared.rootRuntimeAuthorizationRef()))inputs.add(mapper.valueToTree(ref));
        Path spec=root.resolve("v5-spec.json");Files.write(spec,mapper.writeValueAsBytes(requestWire));FileRef specRef=FileRef.measure(spec);
        var invocation=new SourceGraphCommandSpecProducer.RootInvocation("xar.shared-owned-root-invocation/v1","fixture-machine-123",
                FileRef.measure(bindingFile),specRef,prepared);
        Path invocationFile=root.resolve("v5-invocation.json");Files.write(invocationFile,mapper.writeValueAsBytes(invocation));
        var outerSources=new java.util.ArrayList<SharedSourceFiles.Witness>();
        for(FileRef jar:jars)outerSources.add(SharedSourceFiles.observe(Path.of(jar.path())));
        outerSources.add(SharedSourceFiles.observe(invocationFile));outerSources.add(SharedSourceFiles.observe(authorityFile));
        var evidence=new SharedOwnedCommand.RootInvocationEvidence("xar.shared-owned-command-root-evidence/v1",FileRef.measure(invocationFile),
                prepared,authority,null,List.of(SharedSourceFiles.observe(packageFile),SharedSourceFiles.observe(finiteFile)),outerSources,
                SharedOwnedCommand.Check.NOT_REACHED,SharedOwnedCommand.Check.FAILED,SharedOwnedCommand.Check.MATCH,SharedOwnedCommand.Check.MATCH);
        Path evidenceFile=root.resolve("root-evidence.json");Files.write(evidenceFile,mapper.writeValueAsBytes(evidence));
        var terminal=new SharedOwnedCommand.Terminal("xar.shared-owned-command-terminal/v5","fixture-machine-123",
                "2000-01-01T00:00:00Z",SharedOwnedCommand.Status.REJECTED,"/root/test_owner","common-0",null,
                specRef,standing,launcher,jars,new SharedOwnedCommand.Outer("1",268435456,false,"fixture"),false,null,null,
                SharedOwnedCommand.Check.MATCH,SharedOwnedCommand.Check.MATCH,SharedOwnedCommand.Check.MATCH,"Original package rejected",
                List.of(SharedSourceFiles.observe(bindingFile),SharedSourceFiles.observe(javaFile),SharedSourceFiles.observe(packageFile),
                        SharedSourceFiles.observe(finiteFile),SharedSourceFiles.observe(authorityFile)),List.of(),null,null,0,0,0,null,null,FileRef.measure(evidenceFile));
        Path terminalFile=root.resolve("v5-terminal.json");Files.write(terminalFile,SharedOwnedCommand.encodeTerminal(terminal,false));
        assertEquals(SharedOwnedCommand.Status.REJECTED,SharedCommandOutputReader.read(FileRef.measure(terminalFile),1024).status());
        assertEquals(evidence,SharedCommandOutputReader.readRootEvidence(terminal));
        // Compact and drifted failed outcomes remain diagnostic readbacks, never source qualification.
        var compact=(ObjectNode)mapper.readTree(Files.readAllBytes(terminalFile));compact.putArray("input_before");compact.putArray("effective_arguments");
        Path compactFile=root.resolve("compact-rejection.json");Files.write(compactFile,mapper.writeValueAsBytes(compact));
        assertEquals(SharedOwnedCommand.Status.REJECTED,SharedCommandOutputReader.read(FileRef.measure(compactFile),1024).status());
        var invented=(ObjectNode)mapper.readTree(Files.readAllBytes(terminalFile));invented.put("status","PASS");invented.putNull("failure");
        Path bad=root.resolve("invented-pass.json");Files.write(bad,mapper.writeValueAsBytes(invented));
        assertThrows(IOException.class,()->SharedCommandOutputReader.read(FileRef.measure(bad),1024));
        Files.writeString(packageFile,"source drift after real rejection");
        assertEquals(SharedOwnedCommand.Status.REJECTED,SharedCommandOutputReader.read(FileRef.measure(terminalFile),1024).status());
        assertThrows(IOException.class,()->SharedCommandOutputReader.readRootEvidence(terminal));
        var coerced=(ObjectNode)mapper.readTree(Files.readAllBytes(evidenceFile));
        ((ObjectNode)coerced.get("root_invocation_ref")).put("bytes",true);Files.write(evidenceFile,mapper.writeValueAsBytes(coerced));
        var coercedTerminal=(ObjectNode)mapper.readTree(Files.readAllBytes(terminalFile));
        coercedTerminal.set("root_invocation_evidence_ref",mapper.valueToTree(FileRef.measure(evidenceFile)));
        Path coercedFile=root.resolve("coerced-terminal.json");Files.write(coercedFile,mapper.writeValueAsBytes(coercedTerminal));
        assertEquals(SharedOwnedCommand.Status.REJECTED,SharedCommandOutputReader.read(FileRef.measure(coercedFile),1024).status());
        coercedTerminal.putNull("java_invocation_evidence_ref");coercedTerminal.putNull("auxiliary_cleanup");
        var strictCoerced=mapper.treeToValue(coercedTerminal,SharedOwnedCommand.Terminal.class);
        assertThrows(IOException.class,()->SharedCommandOutputReader.readRootEvidence(strictCoerced));
    }
    @Test void rootSourceRosterRejectsOmissionUnrelatedWitnessDuplicateAndSameHashWrongPhysicalPath()throws Exception {
        Path first=root.resolve("original.jar"),second=root.resolve("second.jar"),sameHashCopy=root.resolve("copy.jar"),unrelated=root.resolve("unrelated.jar");
        Files.writeString(first,"original");Files.writeString(second,"second");Files.copy(first,sameHashCopy);Files.writeString(unrelated,"other");
        var a=SharedSourceFiles.observe(first);var b=SharedSourceFiles.observe(second);var copy=SharedSourceFiles.observe(sameHashCopy);var other=SharedSourceFiles.observe(unrelated);
        var expected=List.of(a.source(),b.source());
        SharedCommandOutputReader.requireExactRootSources(List.of(a,b),expected,List.of(a,b));
        assertEquals(a.source().sha256(),copy.source().sha256());assertNotEquals(a.source().path(),copy.source().path());
        for(var malformed:List.of(List.of(a),List.of(a,other),List.of(copy,b),List.of(a,b,a)))
            assertThrows(IOException.class,()->SharedCommandOutputReader.requireExactRootSources(malformed,expected,List.of(a,b)));
    }
    @Test void v5RejectedTerminalWithoutEvidenceRetainsFailureAndCanBeReadWithoutClaimingCustody()throws Exception {
        var pin=new FileRef(root.resolve("unused").toString(),0,HASH);
        var terminal=new SharedOwnedCommand.Terminal("xar.shared-owned-command-terminal/v5","fixture-machine-123",
                java.time.Instant.now().toString(),SharedOwnedCommand.Status.REJECTED,"/root/test_owner","common-0",null,
                pin,pin,pin,List.of(),new SharedOwnedCommand.Outer("1",268435456,false,"fixture"),false,null,null,
                SharedOwnedCommand.Check.MATCH,SharedOwnedCommand.Check.MATCH,SharedOwnedCommand.Check.MATCH,
                "root_evidence: admitted output exhausted",List.of(),List.of(),null,null,0,0,0,null,null,null);
        Path file=root.resolve("v5-no-evidence.json");Files.write(file,SharedOwnedCommand.encodeTerminal(terminal,false));
        var actual=SharedCommandOutputReader.read(FileRef.measure(file),1024);
        assertEquals(SharedOwnedCommand.Status.REJECTED,actual.status());assertFalse(actual.childStarted());
        assertEquals("root_evidence: admitted output exhausted",actual.failure().orElseThrow());
    }
    @Test void legacyV4OutputKeepsItsOriginalWireWithoutANewRootEvidenceField()throws Exception {
        var pin=new FileRef(root.resolve("unused").toString(),0,HASH);
        var terminal=new SharedOwnedCommand.Terminal("xar.shared-owned-command-terminal/v4","fixture-machine-123",
                java.time.Instant.now().toString(),SharedOwnedCommand.Status.REJECTED,"/root/test_owner","common-0",null,
                pin,pin,pin,List.of(),new SharedOwnedCommand.Outer("1",268435456,false,"fixture"),false,null,null,
                SharedOwnedCommand.Check.NOT_REACHED,SharedOwnedCommand.Check.NOT_REACHED,SharedOwnedCommand.Check.NOT_REACHED,
                "Fixture rejection",List.of(),List.of(),null,null,0,0,0);
        byte[] bytes=SharedOwnedCommand.encodeTerminal(terminal,false);
        assertFalse(ControlBuild.strictMapper().readTree(bytes).has("root_invocation_evidence_ref"));
        Path file=root.resolve("legacy-v4.json");Files.write(file,bytes);
        assertEquals(SharedOwnedCommand.Status.REJECTED,SharedCommandOutputReader.read(FileRef.measure(file),1024).status());
    }
    @Test void canonicalCliCountsRejectWhitespaceSignsAndLeadingZeros() throws Exception {
        assertEquals(0,SharedOwnedCommand.cliRef(root.resolve("empty").toString(),"0",HASH).bytes());
        for(String bad:List.of("+1","01"," 1","1.0","-0"))
            assertThrows(IOException.class,()->SharedOwnedCommand.cliRef(root.resolve("file").toString(),bad,HASH));
    }
    @Test void authorityMachineSchemaAndStatusMustMatchIndividually() throws Exception {
        SharedOwnedCommandBinding parsed=SharedOwnedCommandBinding.parse(binding());
        ObjectNode actual=ControlBuild.strictMapper().createObjectNode().put("schema","standing/v1").put("status","ADMITTED01").put("machine_id",parsed.machineId());
        SharedOwnedCommandBinding.verifyAuthority(actual,parsed.standingExpectation(),parsed.machineId());
        for(String field:List.of("schema","status","machine_id")) {
            ObjectNode bad=actual.deepCopy();bad.put(field,"changed");
            assertThrows(IOException.class,()->SharedOwnedCommandBinding.verifyAuthority(bad,parsed.standingExpectation(),parsed.machineId()));
        }
    }
}
