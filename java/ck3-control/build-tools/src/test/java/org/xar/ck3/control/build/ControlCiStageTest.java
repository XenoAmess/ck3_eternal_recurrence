package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.build.CiBootstrap.JavaUtf8Invocation;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ControlCiStageTest {
    @TempDir Path root;
    private CiBootstrap.Plan utf8Plan(String name) throws IOException {
        Path work=root.resolve(name),repo=root.resolve("仓库-é-🙂");
        Files.createDirectories(work.resolve("scratch"));Files.createDirectories(work.resolve("logs"));Files.createDirectories(repo);
        var source=pin(name+"-source.raw");var file=new CiBootstrap.FilePin(source.path(),source.bytes(),source.sha256());
        return new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA,WindowsJobProcess.currentMachineId(),Instant.now().toString(),
                Instant.now().plusSeconds(300).toString(),repo.toString(),work.toString(),root.toString(),"mvn",
                root.resolve("python.exe").toString(),"metadata-utf8-test",file,java.util.Map.of(),java.util.Map.of(),
                java.util.Map.of(),List.of(file),List.of(file),false,false);
    }
    private ControlCi.QualifiedJavaLaunch utf8Launch(CiBootstrap.Plan plan,ControlBuild.FileRef request,
            JavaUtf8Invocation.OutputGuard guard)throws Exception {
        Path origin=Path.of(ControlCi.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        return ControlCi.qualifiedJavaLaunch(plan,Path.of(pin("计划-𝄞.json").path()),Path.of(pin("资格-汉字.json").path()),
                origin,null,request,java.util.Map.of("TEMP","Z:/remote/scratch","TMP","Z:/remote/scratch",
                        "XAR_EXACT_UNICODE","输入-🙂"),ControlCi.currentJavaCarrier(),guard);
    }
    @Test void utf8QualifiedProducerRestoresTheActualControlCiConsumerAndCommandSpec()throws Exception {
        var plan=utf8Plan("utf8-work");var request=pin("原件-🙂.json");
        var prepared=utf8Launch(plan,request,pending->assertTrue(pending>4096));
        assertEquals(prepared.launch().physicalArguments(),prepared.command().arguments());
        assertTrue(prepared.command().arguments().stream().allMatch(value->value.codePoints().allMatch(code->code>=32&&code<=126)));
        assertEquals(Path.of(plan.repoRoot()),prepared.command().cwd());assertEquals(2L<<30,prepared.command().memoryLimitBytes());
        assertEquals("Z:/remote/scratch",prepared.command().environment().get("TMP"));
        assertEquals("输入-🙂",prepared.command().environment().get("XAR_EXACT_UNICODE"));
        assertEquals(List.of("-Xms32m","-Xmx128m","-XX:MaxMetaspaceSize=96m","-XX:ReservedCodeCacheSize=48m",
                "-XX:MaxDirectMemorySize=32m","-Djava.io.tmpdir="+Path.of(plan.workRoot()).resolve("scratch"),
                "-Djna.tmpdir="+Path.of(plan.workRoot()).resolve("scratch")),prepared.startupOptions());
        var deadline=CiBootstrap.pipelineTiming(plan).workDeadline();
        var evidence=new ControlCi.QualifiedJavaEvidence(ControlCi.QUALIFIED_JAVA_SCHEMA,plan.machineId(),
                deadline.toString(),prepared.command().arguments());
        byte[] wire=ControlBuild.strictMapper().writeValueAsBytes(evidence);
        Path recorded=root.resolve("qualified-evidence.json");Files.write(recorded,wire);
        var cold=ControlCi.readQualifiedJavaEvidence(ControlBuild.FileRef.measure(recorded));assertEquals(evidence,cold);
        var restored=ControlCi.requireQualifiedJava(cold,prepared.carrier(),prepared.startupOptions(),plan.machineId(),deadline,
                prepared.launch().logicalRequest());
        assertEquals(request,restored.fixtureProductionRequestRef());assertNull(restored.fixtureRequestRef());
        assertEquals(ControlCi.invocation(prepared.launch().logicalRequest().arguments().toArray(String[]::new)),restored);
        assertEquals(List.of("--bootstrap-plan",restored.planPath().toString(),"--qualified-tools-receipt",
                restored.toolsReceiptPath().toString(),"--fixture-production-request",request.path(),
                Long.toString(request.bytes()),request.sha256()),prepared.launch().logicalRequest().arguments());
        assertThrows(IOException.class,()->ControlCi.requireQualifiedJava(cold,prepared.carrier(),prepared.startupOptions(),
                "another-machine",deadline,prepared.launch().logicalRequest()));
        assertThrows(IOException.class,()->ControlCi.requireQualifiedJava(cold,prepared.carrier(),prepared.startupOptions(),
                plan.machineId(),deadline.plusSeconds(1),prepared.launch().logicalRequest()));
        var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)ControlBuild.strictMapper().readTree(wire);
        wrong.set("physical_arguments",ControlBuild.strictMapper().createArrayNode().add(17));
        Files.write(recorded,ControlBuild.strictMapper().writeValueAsBytes(wrong));
        assertThrows(IOException.class,()->ControlCi.readQualifiedJavaEvidence(ControlBuild.FileRef.measure(recorded)));
        wrong.putNull("physical_arguments");Files.write(recorded,ControlBuild.strictMapper().writeValueAsBytes(wrong));
        assertThrows(IOException.class,()->ControlCi.readQualifiedJavaEvidence(ControlBuild.FileRef.measure(recorded)));
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)ControlBuild.strictMapper().readTree(wire);
        missing.remove("physical_arguments");Files.write(recorded,ControlBuild.strictMapper().writeValueAsBytes(missing));
        assertThrows(IOException.class,()->ControlCi.readQualifiedJavaEvidence(ControlBuild.FileRef.measure(recorded)));
        var scalar=(com.fasterxml.jackson.databind.node.ObjectNode)ControlBuild.strictMapper().readTree(wire);
        scalar.put("machine_id",17);Files.write(recorded,ControlBuild.strictMapper().writeValueAsBytes(scalar));
        assertThrows(IOException.class,()->ControlCi.readQualifiedJavaEvidence(ControlBuild.FileRef.measure(recorded)));
    }
    @Test void sharedUtf8CodecRetainsAnEmptyTokenForTheOriginalCliToReject()throws Exception {
        var plan=utf8Plan("empty-work");var prepared=utf8Launch(plan,null,pending->{});
        var original=prepared.launch().logicalRequest();var args=new ArrayList<>(original.arguments());args.add("");
        var request=new JavaUtf8Invocation.Request(original.target(),original.properties(),args,original.evidenceRoot());
        var publication=JavaUtf8Invocation.publish(request,original.evidenceRoot(),"empty-token.bin",pending->{});
        var launch=JavaUtf8Invocation.launch(publication,prepared.carrier(),prepared.startupOptions());
        var restored=JavaUtf8Invocation.inspect(launch.physicalArguments(),prepared.carrier(),prepared.startupOptions());
        assertEquals(args,restored.arguments());assertEquals("",restored.arguments().getLast());
        assertThrows(IllegalArgumentException.class,()->ControlCi.invocation(restored.arguments().toArray(String[]::new)));
        assertThrows(IllegalArgumentException.class,()->new JavaUtf8Invocation.Property("java.io.tmpdir","不能改启动选项"));
    }
    @Test void quotaOrOriginalDriftFailsBeforeAnyQualifiedChildCanBeProduced()throws Exception {
        var plan=utf8Plan("quota-work");var request=pin("immutable-原件.json");
        assertThrows(IOException.class,()->utf8Launch(plan,request,pending->{throw new IOException("actual quota refusal");}));
        assertFalse(Files.exists(Path.of(plan.workRoot()).resolve("scratch/qualified-utf8.bin")));
        var second=utf8Plan("source-drift-work");var prepared=utf8Launch(second,request,pending->{});
        assertFalse(Files.exists(JavaUtf8Invocation.preparationPath(prepared.launch().logicalRequest())));
        assertThrows(IOException.class,()->ControlCi.requireQualifiedPreparation(prepared));
        Files.writeString(Path.of(request.path()),"changed original");
        var deadline=CiBootstrap.pipelineTiming(second).workDeadline();
        var evidence=new ControlCi.QualifiedJavaEvidence(ControlCi.QUALIFIED_JAVA_SCHEMA,second.machineId(),
                deadline.toString(),prepared.command().arguments());
        assertThrows(IOException.class,()->ControlCi.requireQualifiedJava(evidence,prepared.carrier(),prepared.startupOptions(),
                second.machineId(),deadline,prepared.launch().logicalRequest()));
        String raw=ControlBuild.strictMapper().writeValueAsString(evidence);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(raw.replace("physical_arguments","unknown_arguments"),
                ControlCi.QualifiedJavaEvidence.class));
    }
    private ControlCi.QualifiedJavaLaunch ownedUtf8Fixture(String name,boolean fail)throws Exception {
        var plan=utf8Plan(name);
        Path origin=Path.of(ControlCiUtf8JobFixture.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        var pin=JavaUtf8Invocation.captureClasspath(origin);
        var target=new JavaUtf8Invocation.ClassTarget(ControlCiUtf8JobFixture.class.getName(),pin,List.of(pin));
        var request=new JavaUtf8Invocation.Request(target,List.of(),
                List.of(fail?"FAIL42":"PASS",Path.of(plan.workRoot()).resolve("原件输出-🙂.txt").toString(),"输入-𝄞-中文"),
                JavaUtf8Invocation.captureOutputRoot(Path.of(plan.workRoot()).resolve("scratch")));
        var publication=JavaUtf8Invocation.publish(request,request.evidenceRoot(),"owned-fixture.bin",pending->{});
        var carrier=ControlCi.currentJavaCarrier();var options=List.of("-Xms16m","-Xmx64m","-XX:MaxMetaspaceSize=64m",
                "-XX:ReservedCodeCacheSize=32m","-Djava.io.tmpdir="+Path.of(plan.workRoot()).resolve("scratch"),
                "-Djna.tmpdir="+Path.of(plan.workRoot()).resolve("scratch"));
        var launch=JavaUtf8Invocation.launch(publication,carrier,options);
        var environment=new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());
        for(String key:List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS"))environment.remove(key);
        var command=new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),
                launch.physicalArguments(),Path.of(plan.repoRoot()),environment,
                Path.of(plan.workRoot()).resolve("logs/stdout.log"),Path.of(plan.workRoot()).resolve("logs/stderr.log"),384L<<20);
        return new ControlCi.QualifiedJavaLaunch(command,launch,carrier,options);
    }
    @Test void actualOwnedUtf8ChildPersistsItsOriginalTerminalNativeEvidenceAndPreparation()throws Exception {
        var prepared=ownedUtf8Fixture("owned-success",false);Path logs=prepared.command().stdout().getParent();
        var pending=new ArrayList<Long>();Path terminal=logs.resolve("terminal.json"),nativePath=logs.resolve("native.json");
        var ref=ControlCi.runQualifiedChild(prepared,java.time.Duration.ofSeconds(50),Instant.now().plusSeconds(55),
                terminal,nativePath,pending::add);
        var result=ControlBuild.strictMapper().readValue(Files.readAllBytes(terminal),WindowsJobProcess.CommandResult.class);
        String stderr=Files.readString(prepared.command().stderr());
        assertTrue(result.passed(),()->result+" stderr="+stderr);
        var cold=ControlCi.readQualifiedNativeEvidence(ref,prepared);
        assertEquals(result,cold.terminal());assertEquals(result.identity(),cold.identity());
        assertEquals(WindowsJobProcess.currentMachineId(),cold.machineId());assertEquals(0,result.accounting().activeProcesses());
        assertTrue(pending.getFirst()>8192);assertTrue(pending.getLast()>4096);
        assertEquals("输入-𝄞-中文",Files.readString(Path.of(prepared.launch().logicalRequest().arguments().get(1))));
        var actualPreparation=ControlCi.requireQualifiedPreparation(prepared);
        assertEquals(ControlCiUtf8JobFixture.class.getName(),actualPreparation.mainClass());
        assertEquals(prepared.launch().publication().envelope(),actualPreparation.envelope());
        var mapper=ControlBuild.strictMapper();var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(Files.readAllBytes(nativePath));
        wrong.put("machine_id","another-machine");Path other=logs.resolve("foreign.json");Files.write(other,mapper.writeValueAsBytes(wrong));
        assertThrows(IOException.class,()->ControlCi.readQualifiedNativeEvidence(ControlBuild.FileRef.measure(other),prepared));
        wrong.remove("machine_id");Files.write(other,mapper.writeValueAsBytes(wrong));
        assertThrows(IOException.class,()->ControlCi.readQualifiedNativeEvidence(ControlBuild.FileRef.measure(other),prepared));
        wrong.put("machine_id",17);Files.write(other,mapper.writeValueAsBytes(wrong));
        assertThrows(IOException.class,()->ControlCi.readQualifiedNativeEvidence(ControlBuild.FileRef.measure(other),prepared));
        var evidence=new ControlCi.QualifiedJavaEvidence(ControlCi.QUALIFIED_JAVA_SCHEMA,WindowsJobProcess.currentMachineId(),
                Instant.now().plusSeconds(55).toString(),prepared.command().arguments());
        String legacy=mapper.writeValueAsString(evidence).replace(ControlCi.QUALIFIED_JAVA_SCHEMA,"xar.control-ci-qualified-java/v1");
        Path legacyPath=logs.resolve("legacy.json");Files.writeString(legacyPath,legacy);
        assertThrows(IOException.class,()->ControlCi.readQualifiedJavaEvidence(ControlBuild.FileRef.measure(legacyPath)));
        Files.writeString(Path.of(prepared.launch().publication().envelope().path()),"drift after actual custody ended");
        assertThrows(IOException.class,()->ControlCi.readQualifiedNativeEvidence(ref,prepared));
    }
    @Test void unsuccessfulOriginalJobStaysPrimaryAndRetainsItsTerminalBeforeCustodyPublicationFailure()throws Exception {
        var prepared=ownedUtf8Fixture("owned-failure",true);Path logs=prepared.command().stdout().getParent();
        Path terminal=logs.resolve("terminal.json"),occupied=logs.resolve("occupied-native.json");Files.writeString(occupied,"original occupied evidence");
        var failure=assertThrows(IOException.class,()->ControlCi.runQualifiedChild(prepared,java.time.Duration.ofSeconds(50),
                Instant.now().plusSeconds(55),terminal,occupied,pending->{}));
        assertTrue(failure.getMessage().startsWith("Qualified Java pipeline did not exit cleanly:"));
        assertTrue(failure.getSuppressed().length>0);assertEquals("original occupied evidence",Files.readString(occupied));
        var result=ControlBuild.strictMapper().readValue(Files.readAllBytes(terminal),WindowsJobProcess.CommandResult.class);
        assertEquals(42,result.exitCode());assertNull(result.stopReason());assertEquals(0,result.accounting().activeProcesses());
        assertFalse(result.passed());
        assertEquals(ControlCiUtf8JobFixture.class.getName(),ControlCi.requireQualifiedPreparation(prepared).mainClass());
    }
    @Test void actualNativeCustodyAndQuotaRefusalPreventTheChildBeforeAnyTerminalExists()throws Exception {
        var prepared=ownedUtf8Fixture("owned-refusal",false);Path logs=prepared.command().stdout().getParent();
        try(var held=JavaUtf8NativeCustody.acquire(prepared.launch(),prepared.carrier())){
            held.requireCurrent();
            assertThrows(IOException.class,()->Files.writeString(Path.of(prepared.launch().publication().envelope().path()),"tamper"));
            var calls=new java.util.concurrent.atomic.AtomicInteger();
            held.guard(calls::incrementAndGet).run();assertEquals(1,calls.get());
        }
        var refusal=assertThrows(IOException.class,()->ControlCi.runQualifiedChild(prepared,java.time.Duration.ofSeconds(50),
                Instant.now().plusSeconds(55),logs.resolve("terminal.json"),logs.resolve("native.json"),
                pending->{throw new IOException("original quota refused before child");}));
        assertEquals("original quota refused before child",refusal.getMessage());
        assertFalse(Files.exists(logs.resolve("terminal.json")));assertFalse(Files.exists(logs.resolve("native.json")));
        assertFalse(Files.exists(JavaUtf8Invocation.preparationPath(prepared.launch().logicalRequest())));
    }
    private ControlBuild.FileRef pin(String name) throws IOException {
        Path path = root.resolve(name); Files.writeString(path, "synthetic immutable source pin"); return ControlBuild.FileRef.measure(path);
    }
    @Test void pinnedRequestHasOneStrictSchemaAndRequiresBothConfigs() throws Exception {
        var request = new ControlCi.FixtureRequest(ControlCi.FIXTURE_REQUEST_SCHEMA, "fixture-machine", Instant.now().plusSeconds(60).toString(), pin("fresh.json"), pin("canonical.json"));
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(request);
        assertEquals(request, mapper.readValue(raw, ControlCi.FixtureRequest.class));
        for (String wrong : List.of(raw.replace(ControlCi.FIXTURE_REQUEST_SCHEMA, "old-request/v0"),
                raw.replace("\"canonical_config_ref\"", "\"unknown_config_ref\""),
                raw.replace("\"bytes\":" + request.freshSdkConfigRef().bytes(), "\"bytes\":true"))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, ControlCi.FixtureRequest.class));
        }
    }
    @Test void cliForwardsExactPinsAndRejectsMissingDuplicateAndChangedRequests() throws Exception {
        Path plan = Path.of(pin("plan.json").path()); var request = pin("request.json");
        String[] valid = {"--bootstrap-plan", plan.toString(), "--fixture-stage-request", request.path(), Long.toString(request.bytes()), request.sha256()};
        var parsed = ControlCi.invocation(valid); assertEquals(request, parsed.fixtureRequestRef()); assertNull(parsed.toolsReceiptPath());
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(new String[] {"--bootstrap-plan", plan.toString(), "--fixture-stage-request", request.path()}));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(new String[] {"--bootstrap-plan", plan.toString(), "--unknown"}));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(new String[] {"--bootstrap-plan", plan.toString(), "--qualified-tools-receipt", plan.toString(), "--qualified-tools-receipt", plan.toString()}));
        Files.writeString(Path.of(request.path()), "changed request"); assertThrows(IOException.class, () -> ControlCi.invocation(valid));
    }
    private void report(String suite, String attributes, String cases) throws IOException {
        Files.writeString(root.resolve("TEST-" + suite + ".xml"), "<testsuite name=\"" + suite + "\" " + attributes + ">" + cases + "</testsuite>");
    }
    @Test void lateSelectedSuiteCannotDisappearFromActualToolReports() throws Exception {
        report("FirstTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"actual\"/>");
        ControlCi.requireJUnit(root, Set.of("FirstTest"));
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("FirstTest", "LateAddedTest")));
        report("LateAddedTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"late_actual\"/>");
        ControlCi.requireJUnit(root, Set.of("FirstTest", "LateAddedTest"));
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("FirstTest")));
    }
    @Test void greenSurefireSummaryCannotHideSkippedOrMissingActualCaseChildren() throws Exception {
        report("SelectedTest", "tests=\"2\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"only_one\"/>");
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("SelectedTest")));
        report("SelectedTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"hidden_skip\"><skipped/></testcase>");
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("SelectedTest")));
        report("SelectedTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"hidden_failure\"><failure/></testcase>");
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("SelectedTest")));
    }
    @Test void redReceiptPreservesFailedStageAndEveryUnstartedSuccessorAcrossJson() throws Exception {
        var stages = ControlCi.initialStages(); var evidence = pin("actual-stage.json");
        stages.set(ControlCi.Stage.EXPECTED_MAVEN_RED.ordinal(), new ControlCi.StageActual(ControlCi.Stage.EXPECTED_MAVEN_RED, ControlCi.StageState.PASS, evidence, null));
        stages.set(ControlCi.Stage.REACTOR.ordinal(), new ControlCi.StageActual(ControlCi.Stage.REACTOR, ControlCi.StageState.RED, evidence, "actual reactor failure"));
        var receipt = new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "2026-10-22T00:00:00Z", "2026-10-22T00:00:01Z", ControlCi.PipelineState.RED, "actual reactor failure",
                evidence, evidence, evidence, null, evidence, null, List.of(), null, null, null, null, ControlCi.ExecutionPurpose.HOSTED_CI, null, stages);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(receipt);
        assertEquals(receipt, mapper.readValue(raw, ControlCi.Receipt.class));
        assertEquals(ControlCi.StageState.NOT_RUN, receipt.stages().get(ControlCi.Stage.CANONICAL_THIRTY.ordinal()).state());
        assertThrows(IOException.class, () -> mapper.readValue(raw.replace(ControlCi.ACTUAL_SCHEMA, "xar.java-control-CI-actual/v3"), ControlCi.Receipt.class));
        var incomplete = new ArrayList<>(stages); incomplete.removeLast();
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.RED, "incomplete", null, null, null, null, null, null, List.of(), null, null, null, null, ControlCi.ExecutionPurpose.HOSTED_CI, null, incomplete));
    }
    @Test void bootstrapAndQualifiedChildForwardTheSameProductionPinAndRejectDrift() throws Exception {
        var production = pin("production-input.json"); var plan = pin("forwarded-plan.json");
        String[] args = {"--repo-root", root.toString(), "--work-root", root.resolve("work").toString(),
                "--python-executable", root.resolve("python.exe").toString(), "--system-growth-reserve-bytes", "1",
                "--max-project-bytes", "8589934592", "--fixture-production-request", production.path(),
                "--fixture-production-request-bytes", Long.toString(production.bytes()), "--fixture-production-request-sha256", production.sha256()};
        var values = CiBootstrap.arguments(args); var pinned = CiBootstrap.fixtureProductionPin(values);
        var bootstrap = new ArrayList<>(List.of("--bootstrap-plan", plan.path()));
        CiBootstrap.appendFixtureProduction(bootstrap, pinned);
        var first = ControlCi.invocation(bootstrap.toArray(String[]::new));
        assertEquals(production, first.fixtureProductionRequestRef()); assertNull(first.fixtureRequestRef());
        var qualified = new ArrayList<>(List.of("--bootstrap-plan", plan.path()));
        ControlCi.forwardFixtureRequests(qualified, null, first.fixtureProductionRequestRef());
        assertEquals(first, ControlCi.invocation(qualified.toArray(String[]::new)));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.arguments(java.util.Arrays.copyOf(args, 14)));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), production, production));
        var both = new ArrayList<>(qualified); both.addAll(List.of("--fixture-stage-request", production.path(), Long.toString(production.bytes()), production.sha256()));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(both.toArray(String[]::new)));
        Files.writeString(Path.of(production.path()), "changed actual production input");
        assertThrows(IOException.class, () -> CiBootstrap.appendFixtureProduction(new ArrayList<>(), pinned));
        assertThrows(IOException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), null, production));
    }
    @Test void requestedProductionCannotDisappearIntoAnOptionalBasePass() throws Exception {
        var evidence=pin("requested-production.json");
        var stages=new ArrayList<ControlCi.StageActual>();
        for(var stage:ControlCi.Stage.values()) {
            if(stage==ControlCi.Stage.PERSON10_ACTUAL||stage==ControlCi.Stage.ROOT_INVOCATION_ACTUAL)continue;
            stages.add(new ControlCi.StageActual(stage,
                    stage==ControlCi.Stage.FRESH_SDK||stage==ControlCi.Stage.CANONICAL_THIRTY?ControlCi.StageState.NOT_RUN:ControlCi.StageState.PASS,
                    stage==ControlCi.Stage.FRESH_SDK||stage==ControlCi.Stage.CANONICAL_THIRTY?null:evidence,null));
        }
        var unexecuted=List.of(new ControlCi.StageActual(ControlCi.Stage.PERSON10_ACTUAL,ControlCi.StageState.NOT_RUN,null,null),
                new ControlCi.StageActual(ControlCi.Stage.ROOT_INVOCATION_ACTUAL,ControlCi.StageState.NOT_RUN,null,null));
        assertThrows(IllegalArgumentException.class,()->new ControlCi.SoftwareReceipt(
                ControlCi.QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED,ControlCi.SOFTWARE_SCHEMA,"fixture-machine","a","b",
                ControlCi.PipelineState.PASS,null,evidence,evidence,evidence,null,evidence,evidence,List.of(),evidence,evidence,null,evidence,
                ControlCi.ExecutionPurpose.HOSTED_CI,null,stages,unexecuted,evidence));
        var red=new ControlCi.SoftwareReceipt(ControlCi.QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED,
                ControlCi.SOFTWARE_SCHEMA,"fixture-machine","a","b",ControlCi.PipelineState.RED,"actual host fixture unavailable",
                evidence,evidence,evidence,null,evidence,evidence,List.of(),evidence,evidence,null,evidence,
                ControlCi.ExecutionPurpose.HOSTED_CI,null,stages,unexecuted);
        assertEquals(red,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(red),ControlCi.SoftwareReceipt.class));
        assertEquals(ControlCi.StageState.NOT_RUN,red.postqualificationStages().getFirst().state());
    }
    @Test void productionInputHasItsOwnStrictContractWithoutInventingAnOriginOrStageConfig() throws Exception {
        var request = pin("original-request.raw"); var payload = pin("original-payload.raw");
        var host = new RootSoftwareFixtureHandoff.Request(List.of(request, payload), List.of(request), request, payload);
        var input = new ControlCi.FixtureProductionRequest(ControlCi.FIXTURE_PRODUCTION_SCHEMA, "fixture-machine",
                Instant.now().plusSeconds(60).toString(), pin("sdk-inputs.json"), host);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(input);
        assertEquals(input, mapper.readValue(raw, ControlCi.FixtureProductionRequest.class));
        assertFalse(raw.contains("origin_ref")); assertFalse(raw.contains("fresh_sdk_config_ref"));
        assertThrows(IOException.class, () -> mapper.readValue(raw.replace("sdk_production_inputs_ref", "unknown_inputs_ref"), ControlCi.FixtureProductionRequest.class));
        assertThrows(IOException.class, () -> mapper.readValue(raw.replace(ControlCi.FIXTURE_PRODUCTION_SCHEMA, "old-production/v0"), ControlCi.FixtureProductionRequest.class));
    }
    private record ProducerInputs(CiBootstrap.Plan plan, FreshSdkFixtureStage.Config fresh, CanonicalColdWarmStage.Config canonical) { }
    private ProducerInputs producerInputs() throws IOException {
        Path repo = root.resolve("repository"), work = root.resolve("work"), oracle = root.resolve("oracle-repository");
        Files.createDirectories(oracle.resolve(".github/workflows"));
        Files.writeString(oracle.resolve(".github/workflows/static-ci.yml"), "# isolated metadata contract fixture");
        Path tools = repo.resolve("java/ck3-control/build-tools"); Files.createDirectories(tools);
        Files.writeString(tools.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><groupId>fixture</groupId><artifactId>metadata</artifactId><version>1</version></project>");
        Files.createDirectories(work.resolve("artifacts"));
        Path git = root.resolve("git.exe"); Files.writeString(git, "metadata fixture, never executable");
        var ref = pin("metadata.pin"); var golden = goldenPlan();
        Path goldenPath = root.resolve("golden-plan.json"); Files.write(goldenPath, ControlBuild.strictMapper().writeValueAsBytes(golden));
        String machine = WindowsJobProcess.currentMachineId(), review = Instant.now().plusSeconds(300).toString();
        var sourcePins = ControlBuild.sourceManifest(tools).stream().map(value -> new CiBootstrap.FilePin(value.path(), value.bytes(), value.sha256())).toList();
        var plan = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, machine, Instant.now().toString(), review,
                repo.toString(), work.toString(), root.toString(), "mvn", ref.path(), "metadata-fixture",
                sourcePins.getFirst(), java.util.Map.of(), java.util.Map.of(), java.util.Map.of(), sourcePins, sourcePins, false, false);
        String fixtureReview = CiBootstrap.pipelineTiming(plan).workDeadline().toString();
        var clientRef = ControlBuild.FileRef.measure(root.resolve("client.py"));
        var bootstrap = new RootSoftwareChildBootstrap.Configuration(RootSoftwareChildBootstrap.SCHEMA, RootSoftwareChildBootstrap.SCOPE,
                machine, "metadata-only-no-host-qualification", new RootSoftwareChildBootstrap.ServiceProof(ref, ref, clientRef),
                new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32, ref, null),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.java_map_admission_client_v1", clientRef),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.current_saved_continuity_v1", ref),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", ref),
                ref, ref, ref, List.of(ref), List.of());
        var bootstrapRef = RootSoftwareChildBootstrap.writeConfiguration(bootstrap, root.resolve("bootstrap.json"));
        var fresh = new FreshSdkFixtureStage.Config(FreshSdkFixtureStage.SCHEMA, machine, fixtureReview,
                oracle.toString(), work.resolve("artifacts/fresh").toString(), ref, ref, ref, ref, ref, ref, List.of(ref),
                List.of(root.resolve("dependencies").toString()), List.of(ref), ref, List.of(), bootstrapRef,
                ControlBuild.FileRef.measure(goldenPath), 64L << 20, 60, 59);
        var canonical = new CanonicalColdWarmStage.Config(CanonicalColdWarmStage.SCHEMA, machine, fixtureReview,
                oracle.toString(), work.resolve("artifacts/canonical").toString(), ref, ControlBuild.FileRef.measure(git), ref, ref,
                List.of(ref), List.of(root.resolve("dependencies").toString()), List.of(ref), ref,
                CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE, bootstrapRef, 64L << 20, 60);
        return new ProducerInputs(plan, fresh, canonical);
    }
    @Test void actualTypedProducerRoundTripsThroughTheSharedReaderWithOneNestedGoldenPlan() throws Exception {
        var input = producerInputs(); Path output = Path.of(input.plan().workRoot()).resolve("artifacts/request");
        var requestRef = ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output);
        var request = ControlCi.readFixtureRequest(requestRef, input.plan()); var mapper = ControlBuild.strictMapper();
        assertEquals(input.fresh(), mapper.readValue(Files.readAllBytes(Path.of(request.freshSdkConfigRef().path())), FreshSdkFixtureStage.Config.class));
        assertEquals(input.canonical(), mapper.readValue(Files.readAllBytes(Path.of(request.canonicalConfigRef().path())), CanonicalColdWarmStage.Config.class));
        assertFalse(Files.readString(Path.of(requestRef.path())).contains("producer_golden_plan_ref"));
        assertNotEquals(Path.of(input.plan().repoRoot()), Path.of(input.fresh().canonicalRepository()));
        var oracle = CanonicalOracleEnvironment.bind(Path.of(input.fresh().canonicalRepository()),
                Path.of(input.plan().pythonExecutable()), java.util.Map.of("EXACT_INHERITED", "retained"));
        var forwarded = ControlCi.bindOracleEnvironment(input.plan(), oracle);
        assertEquals(input.fresh().canonicalRepository(), forwarded.get("XAR_ORACLE_REPO"));
        assertEquals(input.fresh().canonicalRepository(), forwarded.get("XAR_REPO_ROOT"));
        assertEquals("retained", forwarded.get("EXACT_INHERITED"));
        var missingOracle = new java.util.TreeMap<String, String>(forwarded); missingOracle.remove("XAR_ORACLE_REPO");
        assertThrows(IOException.class, () -> ControlCi.bindOracleEnvironment(input.plan(), missingOracle));
        var crossed = new java.util.TreeMap<String, String>(forwarded);
        crossed.put("XAR_ORACLE_PYTHON", input.canonical().gitExecutable().path());
        assertThrows(IOException.class, () -> ControlCi.bindOracleEnvironment(input.plan(), crossed));
        var crossedConfig = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.valueToTree(input.canonical());
        crossedConfig.put("repository", input.plan().repoRoot());
        Path crossedPath = root.resolve("crossed-canonical.json"); Files.write(crossedPath, mapper.writeValueAsBytes(crossedConfig));
        var crossedRequest = new ControlCi.FixtureRequest(ControlCi.FIXTURE_REQUEST_SCHEMA, input.plan().machineId(),
                request.reviewAtUtc(), request.freshSdkConfigRef(), ControlBuild.FileRef.measure(crossedPath));
        Path crossedRequestPath = root.resolve("crossed-request.json"); Files.write(crossedRequestPath, mapper.writeValueAsBytes(crossedRequest));
        assertThrows(IOException.class, () -> ControlCi.readFixtureRequest(ControlBuild.FileRef.measure(crossedRequestPath), input.plan()));
        Path planPath = root.resolve("cli-plan.json"); Files.write(planPath, mapper.writeValueAsBytes(input.plan()));
        Path cliOutput = output.resolveSibling("cli-request"); var freshRef = request.freshSdkConfigRef(); var canonicalRef = request.canonicalConfigRef();
        ControlCi.main(new String[] {"--write-fixture-stage-request", planPath.toString(), "--fresh-sdk-config", freshRef.path(), Long.toString(freshRef.bytes()), freshRef.sha256(),
                "--canonical-config", canonicalRef.path(), Long.toString(canonicalRef.bytes()), canonicalRef.sha256(), "--output-root", cliOutput.toString()});
        var cliRequest = ControlCi.readFixtureRequest(ControlBuild.FileRef.measure(cliOutput.resolve("fixture-stage-request.json")), input.plan());
        assertEquals(freshRef.sha256(), cliRequest.freshSdkConfigRef().sha256());
        assertEquals(canonicalRef.sha256(), cliRequest.canonicalConfigRef().sha256());
        assertThrows(IOException.class, () -> ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output));
        requestRef.verify();
        Files.writeString(Path.of(FreshSdkFixtureStage.readProducerGoldenPlan(input.fresh().producerGoldenPlanRef()).contextInput().path()), "changed actual source");
        assertThrows(IOException.class, () -> ControlCi.readFixtureRequest(requestRef, input.plan()));
        assertThrows(IOException.class, () -> ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output.resolveSibling("changed")));
        assertFalse(Files.exists(output.resolveSibling("changed")));
    }
    @Test void portableCheckoutSourceDataTravelsThroughTheOriginalFixtureRequestProducerAndReader() throws Exception {
        var input = producerInputs(); var mapper = ControlBuild.strictMapper();
        Path checkout = RootSoftwareFixtureInputsProducerTest.checkoutFixture(root.resolve("portable-checkout"));
        Path context = Files.createDirectories(checkout.resolve("local-service/src/test/resources/g2-context"));
        for (String name : List.of("context-input.json", "context-result.json", "evaluate-request.json"))
            Files.writeString(context.resolve(name), "{\"fixture\":\"" + name + "\"}");
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values())
            Files.writeString(checkout.resolve("g2-research/src/test/resources/g2-http/" + milestone.name() + ".expected-result.json"),
                    "{\"fixture\":\"" + milestone.name() + "\"}");
        var original = FreshSdkFixtureStage.writeCheckoutProducerGoldenSources(checkout, root.resolve("portable-original-sources.json"));
        byte[] originalMetadata = Files.readAllBytes(Path.of(original.path()));
        var foreign = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.readTree(originalMetadata));
        String foreignMachine = foreign.get("machine_id").textValue() + "-portable-foreign-source";
        foreign.put("machine_id", foreignMachine);
        Path foreignPath = root.resolve("portable-foreign-sources.json"); Files.write(foreignPath, mapper.writeValueAsBytes(foreign));
        var foreignRef = ControlBuild.FileRef.measure(foreignPath);
        var freshNode = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(input.fresh()));
        freshNode.set("producer_golden_plan_ref", mapper.valueToTree(foreignRef));
        var fresh = mapper.treeToValue(freshNode, FreshSdkFixtureStage.Config.class);
        Path output = Path.of(input.plan().workRoot()).resolve("artifacts/portable-request");
        var requestRef = ControlCi.writeFixtureRequest(input.plan(), fresh, input.canonical(), output);
        var request = ControlCi.readFixtureRequest(requestRef, input.plan());
        var persisted = mapper.readValue(Files.readAllBytes(Path.of(request.freshSdkConfigRef().path())), FreshSdkFixtureStage.Config.class);
        assertEquals(fresh, persisted); assertEquals(foreignRef, persisted.producerGoldenPlanRef());
        var sources = assertInstanceOf(FreshSdkFixtureStage.CheckoutProducerGoldenSources.class,
                FreshSdkFixtureStage.readProducerGoldenSources(persisted.producerGoldenPlanRef()));
        assertEquals(foreignMachine, sources.machineId());
        assertFalse(mapper.readTree(Files.readAllBytes(foreignPath)).has("original_install_map_ref"));
        assertArrayEquals(originalMetadata, Files.readAllBytes(Path.of(original.path()))); original.verify(); requestRef.verify();

        var bootstrapNode = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                mapper.valueToTree(RootSoftwareChildBootstrap.readConfiguration(fresh.rootBootstrapRef())));
        bootstrapNode.put("machine_id", foreignMachine);
        var foreignBootstrap = RootSoftwareChildBootstrap.writeConfiguration(
                mapper.treeToValue(bootstrapNode, RootSoftwareChildBootstrap.Configuration.class), root.resolve("foreign-runtime-bootstrap.json"));
        var foreignFreshNode = freshNode.deepCopy(); foreignFreshNode.set("root_bootstrap_ref", mapper.valueToTree(foreignBootstrap));
        var foreignCanonicalNode = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(input.canonical()));
        foreignCanonicalNode.set("root_bootstrap_ref", mapper.valueToTree(foreignBootstrap));
        var foreignFresh = mapper.treeToValue(foreignFreshNode, FreshSdkFixtureStage.Config.class);
        var foreignCanonical = mapper.treeToValue(foreignCanonicalNode, CanonicalColdWarmStage.Config.class);
        Path wrongRuntime = output.resolveSibling("foreign-runtime-request");
        var rejected = assertThrows(IOException.class, () -> ControlCi.writeFixtureRequest(input.plan(), foreignFresh, foreignCanonical, wrongRuntime));
        assertEquals("Root bootstrap machine differs from the actual pipeline", rejected.getMessage());
        assertFalse(Files.exists(wrongRuntime));

        Files.writeString(Path.of(sources.contextResult().path()), "{\"changed\":true}");
        assertThrows(IOException.class, () -> ControlCi.readFixtureRequest(requestRef, input.plan()));
        Path changed = output.resolveSibling("changed-portable-request");
        assertThrows(IOException.class, () -> ControlCi.writeFixtureRequest(input.plan(), fresh, input.canonical(), changed));
        assertFalse(Files.exists(changed));
    }

    @Test void producerFailureRetainsAlreadyWrittenConfigWithoutPublishingARequest() throws Exception {
        var input = producerInputs(); Path output = root.resolve("partial"); var calls = new java.util.concurrent.atomic.AtomicInteger();
        assertThrows(IOException.class, () -> ControlCi.writeFixtureDocuments(output, input.plan().machineId(), input.fresh().reviewAtUtc(),
                input.fresh(), input.canonical(), () -> { if (calls.incrementAndGet() == 3) throw new IOException("actual resource guard rejection"); }));
        assertTrue(Files.isRegularFile(output.resolve("fresh-sdk-config.json")));
        assertFalse(Files.exists(output.resolve("canonical-config.json"))); assertFalse(Files.exists(output.resolve("fixture-stage-request.json")));
        assertEquals(input.fresh(), ControlBuild.strictMapper().readValue(Files.readAllBytes(output.resolve("fresh-sdk-config.json")), FreshSdkFixtureStage.Config.class));
    }
    @Test void typedProducerCliPinsBothInputsAndRejectsIncompleteOrChangedArguments() throws Exception {
        var plan = pin("producer-plan.json"); var fresh = pin("producer-fresh.json"); var canonical = pin("producer-canonical.json");
        String[] args = {"--write-fixture-stage-request", plan.path(), "--fresh-sdk-config", fresh.path(), Long.toString(fresh.bytes()), fresh.sha256(),
                "--canonical-config", canonical.path(), Long.toString(canonical.bytes()), canonical.sha256(), "--output-root", root.resolve("new-output").toString()};
        var invocation = ControlCi.fixtureWriterInvocation(args); assertEquals(fresh, invocation.freshConfigRef()); assertEquals(canonical, invocation.canonicalConfigRef());
        assertThrows(IllegalArgumentException.class, () -> ControlCi.fixtureWriterInvocation(java.util.Arrays.copyOf(args, 11)));
        var wrong = args.clone(); wrong[4] = "true"; assertThrows(IllegalArgumentException.class, () -> ControlCi.fixtureWriterInvocation(wrong));
        Files.writeString(Path.of(fresh.path()), "changed input"); assertThrows(IOException.class, () -> ControlCi.fixtureWriterInvocation(args));
    }
    @Test void readerRejectsRemovedGoldenPlanAndARequestBeyondTheSharedWorkDeadline() throws Exception {
        var input = producerInputs(); Path output = Path.of(input.plan().workRoot()).resolve("artifacts/request");
        var requestRef = ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output);
        var request = ControlCi.readFixtureRequest(requestRef, input.plan()); var mapper = ControlBuild.strictMapper();
        var missing = mapper.readTree(Files.readAllBytes(Path.of(request.freshSdkConfigRef().path())));
        assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, missing).remove("producer_golden_plan_ref");
        assertThrows(IOException.class, () -> mapper.treeToValue(missing, FreshSdkFixtureStage.Config.class));
        var late = new ControlCi.FixtureRequest(ControlCi.FIXTURE_REQUEST_SCHEMA, input.plan().machineId(), input.plan().reviewAtUtc(), request.freshSdkConfigRef(), request.canonicalConfigRef());
        Path latePath = root.resolve("late.json"); Files.write(latePath, mapper.writeValueAsBytes(late));
        assertThrows(IOException.class, () -> ControlCi.readFixtureRequest(ControlBuild.FileRef.measure(latePath), input.plan()));
    }
    private ControlCi.RootSoftwareExecutionCard localCard(CiBootstrap.Plan plan, ControlBuild.FileRef ref) {
        return new ControlCi.RootSoftwareExecutionCard(ControlCi.ROOT_CARD_SCHEMA, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,
                plan.machineId(), plan.observedAtUtc(), plan.reviewAtUtc(), plan.ownerTask(), "software-slot", ref, ref, ref, ref, ref,
                ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023);
    }
    @Test void rootLocalCardAndPlanKeepStrictPurposeAndNormalProfileAcrossJson() throws Exception {
        var input = producerInputs(); var ref = pin("local-card-input.json"); var card = localCard(input.plan(), ref);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(card);
        assertEquals(card, mapper.readValue(raw, ControlCi.RootSoftwareExecutionCard.class));
        for (String wrong : List.of(raw.replace("ROOT_LOCAL_FULL_SOFTWARE", "HOSTED_CI"),
                raw.replace("G2_STABILIZATION_20261023", "STANDARD_8_MIB"),
                raw.replace("\"slot_id\":\"software-slot\"", "\"slot_id\":true"),
                raw.replace("\"owner_task\":\"" + card.ownerTask() + "\"", "\"owner_task\":\"github-actions-java-ci\""),
                raw.replace(card.reviewAtUtc(), card.observedAtUtc()))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, ControlCi.RootSoftwareExecutionCard.class));
        }
        var plan = new ControlCi.RootLocalPlan(ControlCi.ROOT_PLAN_SCHEMA, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, ref);
        assertEquals(plan, mapper.readValue(mapper.writeValueAsBytes(plan), ControlCi.RootLocalPlan.class));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.RootLocalPlan(ControlCi.ROOT_PLAN_SCHEMA, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, null));
    }
    @Test void wholeSoftwareDeadlineCannotBorrowTheOrdinary180SecondSlot() throws Exception {
        var input = producerInputs(); var ref = pin("slot-card.json"); var card = localCard(input.plan(), ref);
        var standing = ControlBuild.strictMapper().createObjectNode(); var slot = standing.putArray("slots").addObject();
        slot.put("slot_id", card.slotId()); slot.put("coordinator", card.ownerTask()); slot.put("timeout_seconds", 180); slot.put("output_root", root.toString());
        assertThrows(IOException.class, () -> ControlCi.requireRootSlot(input.plan(), card, standing));
        slot.put("timeout_seconds", 2700); ControlCi.requireRootSlot(input.plan(), card, standing);
        slot.put("coordinator", "wrong-owner");
        assertThrows(IOException.class, () -> ControlCi.requireRootSlot(input.plan(), card, standing));
        slot.put("coordinator", card.ownerTask());
        slot.put("output_root", root.resolve("another-scope").toString());
        assertThrows(IOException.class, () -> ControlCi.requireRootSlot(input.plan(), card, standing));
    }
    @Test void localActualRequiresFullSdkAndCannotClaimHostedMavenExecution() throws Exception {
        var ref = pin("local-actual.json"); var stages = ControlCi.initialStages();
        for (var stage : ControlCi.Stage.values()) if (stage != ControlCi.Stage.EXPECTED_MAVEN_RED) {
            stages.set(stage.ordinal(), new ControlCi.StageActual(stage, ControlCi.StageState.PASS, ref, null));
        }
        var actual = new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.PASS,
                null, ref, ref, ref, null, ref, ref, List.of(), ref, ref, ref, ref, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, ref, stages, ref);
        assertEquals(actual, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(actual), ControlCi.Receipt.class));
        stages.set(ControlCi.Stage.CANONICAL_THIRTY.ordinal(), new ControlCi.StageActual(ControlCi.Stage.CANONICAL_THIRTY, ControlCi.StageState.NOT_RUN, null, null));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.PASS,
                null, ref, ref, ref, null, ref, ref, List.of(), ref, ref, ref, ref, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, ref, stages, ref));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.RED,
                "incomplete", ref, ref, ref, null, ref, ref, List.of(), ref, ref, null, null, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, ref, stages, ref));
    }

    private FreshSdkFixtureStage.ProducerGoldenPlan goldenPlan() throws IOException {
        var mapper = ControlBuild.strictMapper(); var refs = new java.util.ArrayList<ControlBuild.FileRef>();
        for (int index = 0; index < 19; index++) {
            Path file = root.resolve("golden-" + index + ".raw"); Files.writeString(file, "original producer bytes " + index); refs.add(ControlBuild.FileRef.measure(file));
        }
        Path client = root.resolve("client.py"), test = root.resolve("client-test.py"); Files.writeString(client, "exact client"); Files.writeString(test, "exact test");
        var clientRef = ControlBuild.FileRef.measure(client); var testRef = ControlBuild.FileRef.measure(test);
        var origin = mapper.createObjectNode();
        for (String field : List.of("observed_at_utc", "status", "existing_setup_spec_ref", "setup_source_field", "framework", "golden_install", "actual_config_seam", "authority")) origin.put(field, "synthetic original handoff");
        origin.put("schema", "xar.existing-python-producer-golden-install-map/v1"); origin.put("machine_id", WindowsJobProcess.currentMachineId());
        origin.put("observed_at_utc", Instant.now().toString()); origin.set("existing_setup_spec_ref", mapper.valueToTree(clientRef));
        origin.put("status", "EXACT_EXISTING_SETUP_HANDOFF_NO_NEW_RUNNER");
        origin.put("logical_module", "tools.g2_saved_campaign.test_java_projection_client_v1"); origin.set("test_module_ref", mapper.valueToTree(testRef));
        var classes = origin.putObject("classes"); classes.put("ProjectionClientContractTests", 49); classes.put("ProjectionClientG2ProducerGoldenTests", 4); classes.put("ProjectionClientActualJavaTests", 2);
        var rows = origin.putArray("roles"); var roles = new java.util.ArrayList<>(List.of("context_input", "context_result", "evaluate_request"));
        var vectors = new java.util.ArrayList<FreshSdkFixtureStage.ProducerGoldenVector>();
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values()) {
            roles.add("G2-" + milestone.name() + ".request"); roles.add("G2-" + milestone.name() + ".result");
            int index = milestone.ordinal() * 2 + 3; vectors.add(new FreshSdkFixtureStage.ProducerGoldenVector(milestone, refs.get(index), refs.get(index + 1)));
        }
        for (int index = 0; index < roles.size(); index++) { var row = rows.addObject(); row.put("role", roles.get(index)); row.set("ref", mapper.valueToTree(refs.get(index))); }
        Path originPath = root.resolve("original-install-map.json"); Files.write(originPath, mapper.writeValueAsBytes(origin));
        return new FreshSdkFixtureStage.ProducerGoldenPlan("xar.sdk-producer-golden-plan/v1", WindowsJobProcess.currentMachineId(), ControlBuild.FileRef.measure(originPath),
                new SdkSourceAssembly.Digest(clientRef.bytes(), clientRef.sha256()), new SdkSourceAssembly.Digest(testRef.bytes(), testRef.sha256()), refs.get(0), refs.get(1), refs.get(2), vectors);
    }
    @Test void actualHostedReactorConfigProducesR6AndToolsKeepsItsIndependentProfile() throws Exception {
        var plan = utf8Plan("hosted-r6");
        var producer = ControlCi.class.getDeclaredMethod("config", CiBootstrap.Plan.class, Path.class, Path.class,
                String.class, ControlBuild.TargetKind.class);
        producer.setAccessible(true);
        Path reactor = Path.of(plan.repoRoot()).resolve("java/ck3-control");
        Path release = root.resolve("config-data-only-release.json");
        var actual = (ControlBuild.Config) producer.invoke(null, plan, reactor, release, "hosted-r6-fixture",
                ControlBuild.TargetKind.SERVICE_FAST_JAR);
        assertEquals(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R6, actual.sourceLimitProfile());
        var mapper = ControlBuild.strictMapper();
        assertEquals(actual, mapper.readValue(mapper.writeValueAsBytes(actual), ControlBuild.Config.class));
        var tools = (ControlBuild.Config) producer.invoke(null, plan, reactor.resolve("build-tools"), release,
                "tools-fixture", ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME);
        assertEquals(ControlBuild.SourceLimitProfile.STANDARD_8_MIB, tools.sourceLimitProfile());
        assertEquals(3600,tools.timeoutSeconds());assertEquals(3600,actual.timeoutSeconds());
        var bounded = ControlCi.class.getDeclaredMethod("config", CiBootstrap.Plan.class, Path.class, Path.class,
                String.class, ControlBuild.TargetKind.class, int.class);
        bounded.setAccessible(true);
        for (var target : ControlBuild.TargetKind.values()) {
            Path selectedSource = target == ControlBuild.TargetKind.SERVICE_FAST_JAR ? reactor : reactor.resolve("build-tools");
            var selected = (ControlBuild.Config) bounded.invoke(null, plan, selectedSource, release,
                    "bounded-stage", target, 900);
            assertEquals(900, selected.timeoutSeconds());
            assertEquals(selected, mapper.readValue(mapper.writeValueAsBytes(selected), ControlBuild.Config.class));
            for (int rejected : new int[] {0, ControlBuild.maximumBuildTimeoutSeconds(target) + 1}) {
                var failure = assertThrows(java.lang.reflect.InvocationTargetException.class,
                        () -> bounded.invoke(null, plan, selectedSource, release, "rejected-stage", target, rejected));
                assertInstanceOf(IllegalArgumentException.class, failure.getCause());
            }
        }
        // The actual configuration producer is exercised; no build/receipt qualification is constructed.
    }

    @Test void plannedFixtureTravelsThroughTheActualQualifiedUtf8ProducerAndOriginalReader() throws Exception {
        var plan = utf8Plan("planned-utf8");
        var planned = pin("planned-source.json"); var current = pin("current-source.json");
        Path origin = Path.of(ControlCi.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        var environment = new java.util.TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        environment.put("TEMP", Path.of(plan.workRoot()).resolve("scratch").toString());
        environment.put("TMP", environment.get("TEMP"));
        ControlCi.bindCurrentOracleEnvironment(environment, current);
        var prepared = ControlCi.qualifiedJavaLaunch(plan, Path.of(pin("planned-resource-plan.json").path()),
                Path.of(pin("planned-tools-data.json").path()), origin, null, null, planned,
                environment, ControlCi.currentJavaCarrier(), pending -> assertTrue(pending > 4096));
        var deadline = CiBootstrap.pipelineTiming(plan).workDeadline();
        var evidence = new ControlCi.QualifiedJavaEvidence(ControlCi.QUALIFIED_JAVA_SCHEMA, plan.machineId(),
                deadline.toString(), prepared.command().arguments());
        byte[] wire = ControlBuild.strictMapper().writeValueAsBytes(evidence);
        var cold = ControlBuild.strictMapper().readValue(wire, ControlCi.QualifiedJavaEvidence.class);
        var selected = ControlCi.requireQualifiedJava(cold, prepared.carrier(), prepared.startupOptions(),
                plan.machineId(), deadline, prepared.launch().logicalRequest());
        assertEquals(planned, selected.plannedFixtureProductionRequestRef());
        assertNull(selected.fixtureRequestRef()); assertNull(selected.fixtureProductionRequestRef());
        assertEquals(current.path(), prepared.command().environment().get("XAR_FULL_PARITY_CURRENT_INPUTS"));
        assertEquals(current.sha256(), prepared.command().environment().get("XAR_FULL_PARITY_CURRENT_INPUTS_SHA256"));
        assertTrue(prepared.command().arguments().stream().allMatch(value ->
                value.codePoints().allMatch(code -> code >= 32 && code <= 126)));
        assertEquals(prepared.launch().logicalRequest(), JavaUtf8Invocation.read(prepared.launch().publication()));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.forwardFixtureRequests(
                new ArrayList<>(), planned, null, planned));
        Files.writeString(Path.of(planned.path()), "changed original");
        assertThrows(IOException.class, () -> ControlCi.requireQualifiedJava(cold, prepared.carrier(),
                prepared.startupOptions(), plan.machineId(), deadline, prepared.launch().logicalRequest()));
        // The binary request, carrier and CLI reader are real; these DATA pins do not qualify a tools bundle.
    }

    @Test void typedSoftwareReceiptCannotClaimCompleteActualQualificationAcrossSerde()throws Exception {
        var ref=pin("software-metadata-not-an-actual.json");var stages=new ArrayList<ControlCi.StageActual>();
        var actuals=new ArrayList<ControlCi.StageActual>();
        for(var stage:ControlCi.Stage.values()) {
            boolean actual=stage==ControlCi.Stage.PERSON10_ACTUAL||stage==ControlCi.Stage.ROOT_INVOCATION_ACTUAL;
            boolean fixture=stage==ControlCi.Stage.FRESH_SDK||stage==ControlCi.Stage.CANONICAL_THIRTY;
            var value=new ControlCi.StageActual(stage,actual||fixture?ControlCi.StageState.NOT_RUN:ControlCi.StageState.PASS,
                    actual||fixture?null:ref,null);
            if(actual)actuals.add(value);else stages.add(value);
        }
        var metadata=new ControlCi.SoftwareReceipt(ControlCi.QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED,
                ControlCi.SOFTWARE_SCHEMA,"fixture-machine","a","b",ControlCi.PipelineState.PASS,null,
                ref,ref,ref,null,ref,ref,List.of(),ref,ref,null,null,ControlCi.ExecutionPurpose.HOSTED_CI,null,stages,actuals,ref);
        var mapper=ControlBuild.strictMapper();byte[] wire=mapper.writeValueAsBytes(metadata);
        assertEquals(metadata,mapper.readValue(wire,ControlCi.SoftwareReceipt.class));
        assertThrows(IOException.class,()->mapper.readValue(wire,ControlCi.Receipt.class));
        assertEquals(9,metadata.stages().size());assertEquals(11,ControlCi.initialStages().size());
        var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);
        wrong.put("qualification_scope","ROOT_MANAGED_COMPLETE");
        assertThrows(IOException.class,()->mapper.treeToValue(wrong,ControlCi.SoftwareReceipt.class));
        actuals.set(0,new ControlCi.StageActual(ControlCi.Stage.PERSON10_ACTUAL,ControlCi.StageState.PASS,ref,null));
        assertThrows(IllegalArgumentException.class,()->new ControlCi.SoftwareReceipt(
                ControlCi.QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED,ControlCi.SOFTWARE_SCHEMA,"fixture-machine","a","b",
                ControlCi.PipelineState.PASS,null,ref,ref,ref,null,ref,ref,List.of(),ref,ref,null,null,
                ControlCi.ExecutionPurpose.HOSTED_CI,null,stages,actuals,ref));
    }

    @Test void managedPlanAndCompleteReceiptRequireBothActualStagesAndOriginalPinnedPlan()throws Exception {
        var ref=pin("typed-data-boundary-only.json");var mapper=ControlBuild.strictMapper();
        var plan=new ControlCi.RootManagedPlan(ControlCi.MANAGED_ROOT_PLAN_SCHEMA,ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,ref,ref,ref);
        byte[] wire=mapper.writeValueAsBytes(plan);assertEquals(plan,mapper.readValue(wire,ControlCi.RootManagedPlan.class));
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);missing.remove("postqualification_plan_ref");
        assertThrows(IOException.class,()->mapper.treeToValue(missing,ControlCi.RootManagedPlan.class));
        for(var omitted:List.of(ControlCi.Stage.PERSON10_ACTUAL,ControlCi.Stage.ROOT_INVOCATION_ACTUAL)) {
            var stages=ControlCi.initialStages();
            for(var stage:ControlCi.Stage.values())if(stage!=ControlCi.Stage.EXPECTED_MAVEN_RED&&stage!=omitted)
                stages.set(stage.ordinal(),new ControlCi.StageActual(stage,ControlCi.StageState.PASS,ref,null));
            assertThrows(IllegalArgumentException.class,()->new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA,"fixture-machine","a","b",
                    ControlCi.PipelineState.PASS,null,ref,ref,ref,null,ref,ref,List.of(),ref,ref,ref,ref,
                    ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,ref,ref,stages,ref));
        }
        Path output=root.resolve("must-not-exist-managed-plan.json");
        assertThrows(IOException.class,()->ControlCi.main(new String[]{"--write-root-local-complete-plan",ref.path(),Long.toString(ref.bytes()),ref.sha256(),
                "--fixture-production-request",ref.path(),Long.toString(ref.bytes()),ref.sha256(),"--postqualification-plan",ref.path(),
                Long.toString(ref.bytes()),ref.sha256(),"--output",output.toString()}));
        assertFalse(Files.exists(output));
    }


}

