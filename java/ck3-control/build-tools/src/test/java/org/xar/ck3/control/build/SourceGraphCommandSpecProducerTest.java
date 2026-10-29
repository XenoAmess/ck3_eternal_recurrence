package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SourceGraphCommandSpecProducer.Intent;
import org.xar.ck3.control.build.SourceGraphCommandSpecProducer.Slot;

final class SourceGraphCommandSpecProducerTest {
    @TempDir Path root;
    @Test void explicitUnicodePublicationFlowsThroughActualSpecParserAndEvidenceReaderWithoutLaunching() throws Exception {
        Path classes=Files.createDirectory(root.resolve("class-metadata"));Files.write(classes.resolve("Example.class"),new byte[]{1,2,3});
        var cp=CiBootstrap.JavaUtf8Invocation.captureClasspath(classes);
        Path evidence=Files.createDirectory(root.resolve("utf8-evidence"));
        var logical=new CiBootstrap.JavaUtf8Invocation.Request(new CiBootstrap.JavaUtf8Invocation.ClassTarget("example.Main",cp,List.of(cp)),
                List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.fixture","编译输入λ")),List.of("中文路径/🛡"),
                CiBootstrap.JavaUtf8Invocation.captureOutputRoot(evidence));
        var publication=CiBootstrap.JavaUtf8Invocation.publish(logical,logical.evidenceRoot(),"invocation.bin",pending->{
            if(pending>8L<<20) throw new IOException("Finite software metadata fixture output exceeded");
        });
        var descriptor=new SharedOwnedCommand.JavaInvocation(SharedSourceFiles.observe(Path.of(publication.envelope().path())),List.of("-Xmx128m"));
        Intent base=intent("compile");
        Intent child=new Intent(base.machineId(),base.owner(),base.coordinator(),base.slotId(),null,base.runId(),base.standingRef(),
                base.launcherSourceRef(),base.executable(),List.of(),base.cwd(),base.environment(),List.of(descriptor.fileRef()),
                base.timeoutSeconds(),base.memoryLimitBytes(),base.rootExitDrainPolicy());
        byte[] wire=SourceGraphCommandSpecProducer.produceJava(new Slot(child.slotId(),root.resolve("commands")),child,descriptor);
        ObjectNode parsed=(ObjectNode)ControlBuild.strictMapper().readTree(wire);
        var request=SharedOwnedCommand.parseRequest(parsed);
        assertEquals("xar.shared-owned-command-spec/v4",request.schema());assertTrue(request.arguments().isEmpty());
        assertEquals(logical,CiBootstrap.JavaUtf8Invocation.read(request.javaInvocation().publication()));
        var runtime=new java.util.ArrayList<FileRef>();for(int i=0;i<6;i++) runtime.add(plain(root,"carrier-"+i+".bin"));
        var carrier=SharedOwnedCommand.javaCarrier(runtime);var launch=CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,descriptor.asciiVmOptions());
        assertTrue(launch.physicalArguments().stream().allMatch(argument->argument.chars().allMatch(c->c>=32 && c<=126)));
        var snapshot=new SharedOwnedCommand.JavaInvocationEvidence("xar.shared-owned-command-java-evidence/v2",descriptor,runtime,
                launch.physicalArguments(),descriptor.asciiVmOptions(),SharedOwnedCommand.JavaPreparationState.PRE_LAUNCH,null,null);
        Path snapshotPath=root.resolve("evidence.json");Files.write(snapshotPath,ControlBuild.strictMapper().writeValueAsBytes(snapshot));
        String external=Files.readString(snapshotPath);assertTrue(external.contains("native_file"));assertFalse(external.contains("provider_file_key"));
        assertEquals(logical,SharedOwnedCommand.verifyJavaEvidence(FileRef.measure(snapshotPath)));
        ObjectNode changed=(ObjectNode)ControlBuild.strictMapper().readTree(Files.readAllBytes(snapshotPath));
        ((com.fasterxml.jackson.databind.node.ArrayNode)changed.get("physical_arguments")).add("different");
        FileRef changedRef=json(root.resolve("wrong-logical.json"),changed);
        assertThrows(IOException.class,()->SharedOwnedCommand.verifyJavaEvidence(changedRef));
        ObjectNode missing=parsed.deepCopy();missing.putArray("inputs");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(missing));
        ObjectNode dual=parsed.deepCopy();dual.putArray("arguments").add("example.Other");
        assertThrows(IOException.class,()->SharedOwnedCommand.parseRequest(dual));
        assertFalse(Files.exists(root.resolve("commands")),"Only codec metadata is produced, no bytecode or child qualification claimed");
    }

    @Test void nativeEnvelopeWitnessSurvivesJsonAndHeldInputsRejectWritesWithoutMintingAJob() throws Exception {
        Path classes=Files.createDirectory(root.resolve("metadata-only-classes"));Files.write(classes.resolve("Example.class"),new byte[]{1,2,3});
        var cp=CiBootstrap.JavaUtf8Invocation.captureClasspath(classes);Path evidence=Files.createDirectory(root.resolve("native-metadata-evidence"));
        var logical=new CiBootstrap.JavaUtf8Invocation.Request(new CiBootstrap.JavaUtf8Invocation.ClassTarget("example.Main",cp,List.of(cp)),
                List.of(),List.of("native metadata only"),CiBootstrap.JavaUtf8Invocation.captureOutputRoot(evidence));
        var published=CiBootstrap.JavaUtf8Invocation.publish(logical,logical.evidenceRoot(),"invocation.bin",pending->{
            if(pending>8L<<20) throw new IOException("Finite metadata fixture output exceeded");
        });
        var original=SharedSourceFiles.observe(Path.of(published.envelope().path()));
        var descriptor=new SharedOwnedCommand.JavaInvocation(original,List.of("-Xmx128m"));
        var decoded=ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(descriptor),SharedOwnedCommand.JavaInvocation.class);
        assertEquals(original,decoded.envelope());assertEquals(logical,CiBootstrap.JavaUtf8Invocation.read(decoded.publication()));
        var runtime=new java.util.ArrayList<FileRef>();for(int i=0;i<6;i++) runtime.add(plain(root,"metadata-carrier-"+i+".bin"));
        var carrier=SharedOwnedCommand.javaCarrier(runtime);var launch=CiBootstrap.JavaUtf8Invocation.launch(decoded.publication(),carrier,decoded.asciiVmOptions());
        try(var held=JavaUtf8NativeCustody.acquire(launch,carrier)) {
            assertTrue(held.maximumEvidenceBytes(Path.of(ProcessHandle.current().info().command().orElseThrow()))>0);
            assertThrows(IOException.class,()->Files.write(Path.of(original.source().path()),new byte[]{9}));
            held.requireCurrent();
        }
        Path replacement=root.resolve("replacement-envelope.bin");Files.write(replacement,Files.readAllBytes(Path.of(original.source().path())));
        Files.move(replacement,Path.of(original.source().path()),java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        decoded.fileRef().verify();
        assertThrows(IOException.class,decoded::publication);
        assertFalse(Files.exists(root.resolve("commands")),"No process, Job0 observation or execution authority is fabricated");
    }

    @Test void typedJavaEntryActuallyPublishesOneEnvelopeAndClosedWholeEntryWithOriginalStandingGuards() throws Exception {
        EntryFixture fixture=entryFixture(false);Path directory=fixture.directory();var original=fixture.entry();
        ObjectNode standing=(ObjectNode)ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(original.binding().standingRef().path())));
        ((ObjectNode)standing.path("slots").get(0)).put("output_cap_bytes",8L<<20);
        FileRef larger=json(directory.resolve("fixture-only-eight-metadata.json"),standing);
        var binding=new SourceGraphCommandSpecProducer.BindingIntent(original.binding().machineId(),original.binding().launcherSourceRef(),larger,
                original.binding().deliveryRef(),original.binding().standingExpectation(),original.binding().deliveryExpectation());
        FileRef primary=plain(directory,"class-origin.bin");var inputs=new java.util.ArrayList<>(original.inputs());inputs.add(primary);
        var entry=new SourceGraphCommandSpecProducer.EntryIntent(binding,original.owner(),original.coordinator(),original.slotId(),null,
                original.runId(),original.executable(),List.of(),original.cwd(),original.environment(),inputs,original.timeoutSeconds(),
                original.memoryLimitBytes(),original.rootExitDrainPolicy());
        Path evidence=SharedOwnedCommand.javaEvidenceRoot(directory.resolve("commands"),entry.owner(),entry.runId(),false);
        Files.createDirectories(evidence);
        var declared=new SourceGraphCommandSpecProducer.JavaIntent(SourceGraphCommandSpecProducer.JavaTargetKind.CLASS,primary,"example.Main",
                List.of(primary),List.of(new CiBootstrap.JavaUtf8Invocation.Property("xar.fixture","存档λ")),List.of("真实输入/🛡"),
                List.of("-Xmx128m"),null,0);
        var result=SourceGraphCommandSpecProducer.publishJavaInvocation(directory.resolve("binding.json"),directory.resolve("spec.json"),
                directory.resolve("invocation.json"),entry,declared,false);
        var child=SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(result.specRef().path()))));
        assertEquals("xar.shared-owned-command-spec/v4",child.schema());
        var logical=CiBootstrap.JavaUtf8Invocation.read(child.javaInvocation().publication());assertEquals(declared.arguments(),logical.arguments());
        assertEquals(declared.properties(),logical.properties());assertEquals(evidence,Path.of(logical.evidenceRoot().path()));
        assertEquals(1,child.inputs().stream().filter(input->input.equals(child.javaInvocation().fileRef())).count());
        assertEquals("xar.shared-owned-command-invocation/v2",SourceGraphCommandSpecProducer.readInvocation(result.invocationRef()).schema());
        assertFalse(Files.exists(child.outputRoot()));
        assertThrows(FileAlreadyExistsException.class,()->SourceGraphCommandSpecProducer.publishJavaInvocation(directory.resolve("binding.json"),
                directory.resolve("spec.json"),directory.resolve("invocation.json"),entry,declared,false));
    }

    @Test void legacyJavaArgvCannotSilentlyGainUnicodeAndNewWireCannotBeRelabeledHistorical() throws Exception {
        Intent base=intent("plan");
        Intent unicode=new Intent(base.machineId(),base.owner(),base.coordinator(),base.slotId(),null,base.runId(),base.standingRef(),
                base.launcherSourceRef(),base.executable(),List.of("example.Main","中文"),base.cwd(),base.environment(),base.inputs(),
                base.timeoutSeconds(),base.memoryLimitBytes(),base.rootExitDrainPolicy());
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.produce(new Slot(base.slotId(),root.resolve("commands")),unicode));
        assertThrows(IllegalArgumentException.class,()->new SourceGraphCommandSpecProducer.Invocation("xar.shared-owned-command-invocation/v4",
                base.machineId(),base.executable(),List.of(),base.cwd(),Map.of(),List.of(),ref("binding.json"),ref("spec.json")));
        assertFalse(Files.exists(root.resolve("commands")));
    }
    @Test void actuallyDecodedBodyMustMatchPinEvenWhenSameFileHasReturnedToOriginalBytes() throws IOException {
        Path file=root.resolve("a-b-a.json");
        byte[] original="{\"value\":\"A\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] transientBody="{\"value\":\"B\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(file,original); FileRef pinned=FileRef.measure(file);
        Files.write(file,transientBody); byte[] observed=Files.readAllBytes(file); Files.write(file,original);
        pinned.verify();
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.decodeExact(pinned,observed));
        assertEquals("A",SourceGraphCommandSpecProducer.decodeExact(pinned,original).path("value").textValue());
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.decodeExact(pinned,new byte[original.length+1]));
    }

    private record EntryFixture(SourceGraphCommandSpecProducer.EntryIntent entry, Path directory, Path nativeTmp) { }
    private FileRef json(Path file, ObjectNode value) throws IOException {
        Files.write(file,ControlBuild.strictMapper().writeValueAsBytes(value)); return FileRef.measure(file);
    }
    private FileRef plain(Path directory,String name) throws IOException {
        Path file=directory.resolve(name); Files.writeString(file,name); return FileRef.measure(file);
    }
    /** Declaration fixture only. It cannot pass the executor's real completed-build/archive qualification. */
    private EntryFixture entryFixture(boolean annotatedCapacity) throws IOException {
        Path directory=Files.createTempDirectory(root,"whole-entry-"),nativeTmp=Files.createDirectory(directory.resolve("fresh-jna"));
        var mapper=ControlBuild.strictMapper(); FileRef java=plain(directory,"java.exe"),launcher=plain(directory,"SharedOwnedCommand.java");
        var runtime=new java.util.ArrayList<FileRef>();
        for(int index=0;index<6;index++) runtime.add(plain(directory,"runtime-"+index+".jar"));
        ObjectNode delivery=mapper.createObjectNode(); delivery.put("schema","fixture.delivery/v1");
        delivery.put("machine_id","fixture-machine-123"); delivery.put("status","DECLARED_FIXTURE_METADATA_ONLY");
        delivery.set("complete_runtime",mapper.valueToTree(runtime)); FileRef deliveryRef=json(directory.resolve("delivery.json"),delivery);
        FileRef source=plain(directory,"source-grant.json"),capacity=plain(directory,"capacity.json");
        ObjectNode standing=mapper.createObjectNode();standing.put("schema","fixture.standing/v1");
        standing.put("machine_id","fixture-machine-123");standing.put("status","ISSUED_FIXTURE_METADATA_ONLY");
        standing.put("review_at_utc","2099-01-01T00:00:00Z");standing.put("native_tmp_root",nativeTmp.toString());
        standing.put("private_temporary_aggregate_root",directory.resolve("private-temporary").toString());
        standing.set("source_grant_ref",mapper.valueToTree(source));
        ObjectNode capacityRef=mapper.valueToTree(capacity);
        if(annotatedCapacity) capacityRef.put("annotation","Real rejected shape: FileRef permits exactly three fields");
        standing.set("capacity_release_ref",capacityRef);
        standing.set("qualified_tools_ref",mapper.valueToTree(plain(directory,"whole-build.json")));
        standing.set("qualified_own_readback_ref",mapper.valueToTree(plain(directory,"own-readback.json")));
        standing.set("runtime_closure",mapper.valueToTree(runtime)); standing.set("allowed_executables",mapper.valueToTree(List.of(java)));
        ObjectNode slot=standing.putArray("slots").addObject();slot.put("slot_id","fixture-slot");
        slot.put("output_root",directory.resolve("commands").toString());slot.put("output_cap_bytes",1L<<20);
        slot.put("worker_memory_limit_bytes",512L<<20);slot.put("outer_memory_budget_bytes",256L<<20);
        slot.put("timeout_seconds",180);slot.put("serial",true);
        FileRef standingRef=json(directory.resolve("standing.json"),standing);
        var binding=new SourceGraphCommandSpecProducer.BindingIntent("fixture-machine-123",launcher,standingRef,deliveryRef,
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture.standing/v1","ISSUED_FIXTURE_METADATA_ONLY"),
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture.delivery/v1","DECLARED_FIXTURE_METADATA_ONLY"));
        var entry=new SourceGraphCommandSpecProducer.EntryIntent(binding,"/root/source_graph","/root","fixture-slot",null,"fixture-run",
                java,List.of("-Xmx128m","example.Child"),directory.toString(),Map.of(),List.of(plain(directory,"actual-input.json")),
                120,256L<<20,WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
        return new EntryFixture(entry,directory,nativeTmp);
    }

    @Test void wholeEntryDerivesFreshTmpAndBothJvmFlagsFromStandingBeforeAnyChild() throws Exception {
        EntryFixture fixture=entryFixture(false);Path directory=fixture.directory();
        var published=SourceGraphCommandSpecProducer.publishInvocation(directory.resolve("binding.json"),directory.resolve("spec.json"),
                directory.resolve("invocation.json"),fixture.entry());
        var invocation=SourceGraphCommandSpecProducer.readInvocation(published.invocationRef());
        var binding=SharedOwnedCommandBinding.read(published.bindingRef());
        assertEquals(fixture.nativeTmp(),binding.nativeTemporaryRoot()); assertNotEquals(directory,binding.nativeTemporaryRoot());
        assertTrue(invocation.arguments().contains("-Xmx128m"));
        assertEquals(List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS"),invocation.unsetEnvironment());
        assertTrue(invocation.arguments().contains("-Djava.io.tmpdir="+fixture.nativeTmp()));
        assertTrue(invocation.arguments().contains("-Djna.tmpdir="+fixture.nativeTmp()));
        assertEquals(Map.of("TMP",fixture.nativeTmp().toString(),"TEMP",fixture.nativeTmp().toString()),invocation.environment());
        var actual=SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(published.specRef().path()))));
        assertEquals(directory.resolve("commands/source_graph/fixture-run"),actual.outputRoot());
        assertFalse(Files.exists(directory.resolve("commands")),"Metadata production starts no child and creates no output root");
        assertThrows(FileAlreadyExistsException.class,()->SourceGraphCommandSpecProducer.publishInvocation(directory.resolve("binding.json"),
                directory.resolve("spec.json"),directory.resolve("invocation.json"),fixture.entry()));
        published.invocationRef().verify();
    }

    @Test void annotatedCapacityRefIsRejectedByActualSharedStandingParserBeforePublication() throws Exception {
        EntryFixture fixture=entryFixture(true);Path directory=fixture.directory();
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.publishInvocation(directory.resolve("binding.json"),
                directory.resolve("spec.json"),directory.resolve("invocation.json"),fixture.entry()));
        for(String file:List.of("binding.json","spec.json","invocation.json","commands")) assertFalse(Files.exists(directory.resolve(file)));
    }

    @Test void wholeEntryReaderRejectsActualMissingJnaFlagAndHistoricalTmpBinding() throws Exception {
        EntryFixture fixture=entryFixture(false);Path directory=fixture.directory();
        var published=SourceGraphCommandSpecProducer.publishInvocation(directory.resolve("binding.json"),directory.resolve("spec.json"),
                directory.resolve("invocation.json"),fixture.entry());
        var mapper=ControlBuild.strictMapper();ObjectNode wire=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(published.invocationRef().path())));
        var arguments=mapper.createArrayNode();
        for(var argument:wire.path("arguments")) if(!argument.textValue().startsWith("-Djna.tmpdir=")) arguments.add(argument);
        wire.set("arguments",arguments);FileRef missingJna=json(directory.resolve("failed-missing-jna.json"),wire);
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.readInvocation(missingJna));
        ObjectNode binding=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(published.bindingRef().path())));
        binding.put("native_temporary_root",directory.toString());FileRef staleBinding=json(directory.resolve("failed-stale-tmp-binding.json"),binding);
        ObjectNode staleWire=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(published.invocationRef().path())));
        staleWire.set("binding_ref",mapper.valueToTree(staleBinding));FileRef stale=json(directory.resolve("failed-stale-tmp-invocation.json"),staleWire);
        assertThrows(IOException.class,()->SourceGraphCommandSpecProducer.readInvocation(stale));
        assertFalse(Files.exists(directory.resolve("commands"))); published.invocationRef().verify();
    }
    private FileRef ref(String name) { return new FileRef(root.resolve(name).toString(), 1, "0".repeat(64)); }
    private Intent intent(String phase) {
        return new Intent("fixture-machine-123", "/root/source03_audit", "/root",
                "full35-input09-" + phase, null, "full35-" + phase + "09",
                ref("standing.json"), ref("SharedOwnedCommand.java"), ref("java.exe"),
                List.of("-Xmx256m", "org.xar.ck3.control.build.Source08Assembly", "an argument with spaces"),
                root.toString(), Map.of("FIXTURE", "typed"), List.of(ref("actual-input.json")),
                180, 536870912L, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
    }

    @Test void allFiveRealPhaseIntentsProduceStrictSpecsAcceptedByTheActualOutputGuard() throws IOException {
        for (String phase : List.of("assembly", "plan", "materialize", "independent-audit", "compile")) {
            Intent intent = intent(phase);
            Path slotRoot = root.resolve("commands/" + phase);
            byte[] bytes = SourceGraphCommandSpecProducer.produce(new Slot(intent.slotId(), slotRoot), intent);
            ObjectNode wire = (ObjectNode) ControlBuild.strictMapper().readTree(bytes);
            assertEquals(20, wire.size());
            SharedOwnedCommand.Request actual = SharedOwnedCommand.parseRequest(wire);
            SharedOwnedCommand.requireCommandOutputRoot(actual.outputRoot(), slotRoot, actual.owner(), actual.runId());
            assertEquals(slotRoot.resolve("source03_audit/full35-" + phase + "09"), actual.outputRoot());
            assertNotEquals(slotRoot, actual.outputRoot());
            assertEquals(intent.arguments(), actual.arguments());
            assertEquals(intent.inputs(), actual.inputs());
            assertNull(actual.borrowedSlotId()); assertNull(actual.operationCardRef());
            assertEquals(SharedOwnedCommand.TemporaryPolicy.SLOT_PRIVATE, actual.temporaryPolicy());
            assertFalse(Files.exists(slotRoot), "Source production never precreates command output or starts a child");
        }
    }

    @Test void actualAssembly09RejectedSlotRootRemainsARealConsumerNegative() throws IOException {
        Intent intent = intent("assembly"); Path slotRoot = root.resolve("commands/assembly");
        byte[] valid = SourceGraphCommandSpecProducer.produce(new Slot(intent.slotId(), slotRoot), intent);
        ObjectNode oldFailedWire = (ObjectNode) ControlBuild.strictMapper().readTree(valid);
        oldFailedWire.put("output_root", slotRoot.toString());
        SharedOwnedCommand.Request parsedOld = SharedOwnedCommand.parseRequest(oldFailedWire);
        IOException rejected = assertThrows(IOException.class, () ->
                SharedOwnedCommand.requireCommandOutputRoot(parsedOld.outputRoot(), slotRoot, parsedOld.owner(), parsedOld.runId()));
        assertEquals("output outside exact slot build root", rejected.getMessage());
        SharedOwnedCommand.Request corrected = SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(valid));
        SharedOwnedCommand.requireCommandOutputRoot(corrected.outputRoot(), slotRoot, corrected.owner(), corrected.runId());
        assertFalse(Files.exists(slotRoot));
    }

    @Test void wrongOwnerRunAndExtraPathDepthCannotBorrowTheCorrectSlotPrefix() throws IOException {
        Intent intent = intent("plan"); Path slot = root.resolve("commands/plan");
        for (Path wrong : List.of(slot.resolve("another_owner/full35-plan09"),
                slot.resolve("source03_audit/another-run"), slot.resolve("source03_audit/full35-plan09/extra"))) {
            assertThrows(IOException.class, () ->
                    SharedOwnedCommand.requireCommandOutputRoot(wrong, slot, intent.owner(), intent.runId()));
        }
        assertThrows(IOException.class, () -> SharedOwnedCommand.commandOutputRoot(slot, "/root/../outside", intent.runId()));
        assertThrows(IOException.class, () -> SharedOwnedCommand.commandOutputRoot(slot, intent.owner(), "../outside"));
        assertThrows(IOException.class, () -> SourceGraphCommandSpecProducer.produce(new Slot("different-slot", slot), intent));
    }

    @Test void actualPublishedSpecRoundtripsAndCannotOverwritePreservedInputs() throws IOException {
        Intent intent = intent("assembly"); Slot slot = new Slot(intent.slotId(), root.resolve("commands/assembly"));
        Path destination = root.resolve("immutable-spec.json");
        FileRef published = SourceGraphCommandSpecProducer.publish(destination, slot, intent);
        published.verify();
        byte[] preserved = Files.readAllBytes(destination);
        var readBack = SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(preserved));
        SharedOwnedCommand.requireCommandOutputRoot(readBack.outputRoot(), slot.outputRoot(), readBack.owner(), readBack.runId());
        assertThrows(FileAlreadyExistsException.class, () -> SourceGraphCommandSpecProducer.publish(destination, slot, intent));
        assertArrayEquals(preserved, Files.readAllBytes(destination));
        assertThrows(IOException.class, () ->
                SourceGraphCommandSpecProducer.publish(root.resolve("missing-parent/spec.json"), slot, intent));
        assertFalse(Files.exists(slot.outputRoot()));
    }

    private record RejectedSourceFixture(String schema, FileRef originalSpecRef, FileRef originalTerminalRef,
            int actualInputCount, int actualConflictingInputIndex, FileRef executable, List<FileRef> conflictingInputs) { }

    @Test void actualRejected501InputSpecFixtureExercisesTheProductionReservedExecutorGuard() throws IOException {
        RejectedSourceFixture fixture;
        try (var stream = getClass().getResourceAsStream("/sourcegraph/source23-duplicate-executable.json")) {
            assertNotNull(stream, "Original C23 rejected-spec fixture is mandatory");
            fixture = ControlBuild.strictMapper().readValue(stream, RejectedSourceFixture.class);
        }
        assertThrows(IllegalArgumentException.class, () ->
                SourceGraphCommandSpecProducer.validateInputs(fixture.executable(), fixture.conflictingInputs()));
        assertEquals(501, fixture.actualInputCount());
        assertEquals(12, fixture.actualConflictingInputIndex());
        assertFalse(Files.exists(root.resolve("commands")));
    }

    @Test void duplicateInputPathsRejectSameAndConflictingPinsInsteadOfSilentlyDeduplicating() {
        FileRef executable = ref("java.exe"), input = ref("actual-input.json");
        FileRef caseAlias = new FileRef(input.path().toUpperCase(java.util.Locale.ROOT), input.bytes(), input.sha256());
        FileRef conflicting = new FileRef(input.path(), input.bytes() + 1, "1".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> SourceGraphCommandSpecProducer.validateInputs(executable, List.of(executable)));
        assertThrows(IllegalArgumentException.class, () -> SourceGraphCommandSpecProducer.validateInputs(executable, List.of(input, input)));
        assertThrows(IllegalArgumentException.class, () -> SourceGraphCommandSpecProducer.validateInputs(executable, List.of(input, caseAlias)));
        assertThrows(IllegalArgumentException.class, () -> SourceGraphCommandSpecProducer.validateInputs(executable, List.of(input, conflicting)));
        Intent base = intent("plan");
        assertThrows(IllegalArgumentException.class, () -> new Intent(base.machineId(), base.owner(), base.coordinator(),
                base.slotId(), base.borrowedSlotId(), base.runId(), base.standingRef(), base.launcherSourceRef(),
                executable, base.arguments(), base.cwd(), base.environment(), List.of(executable),
                base.timeoutSeconds(), base.memoryLimitBytes(), base.rootExitDrainPolicy()));
        SourceGraphCommandSpecProducer.validateInputs(executable, List.of(input));
    }
}
