package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Software protocol rejection only; no native process, accepted build or launch is fabricated. */
final class NativeBridgeBuildTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef pin(String name, String body) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, body); return ControlBuild.FileRef.measure(path);
    }
    private NativeBridgeBuild.Request request(NativeBridgeBuild.Stage stage,
            ControlBuild.FileRef environment, ControlBuild.FileRef build) throws IOException {
        Path source = temporary.resolve("source"); Files.createDirectories(source);
        if (!Files.exists(source.resolve("CMakeLists.txt"))) Files.writeString(source.resolve("CMakeLists.txt"), "option(XAR_CK3_EXAMPLE \"fixture\" OFF)\n");
        var toolPins = new ArrayList<ControlBuild.FileRef>();
        for (String name : List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe")) {
            Path file = temporary.resolve(name); if (!Files.exists(file)) Files.writeString(file, name); toolPins.add(ControlBuild.FileRef.measure(file));
        }
        Path helper = temporary.resolve("helper.py"), python = temporary.resolve("python.exe");
        if (!Files.exists(helper)) Files.writeString(helper, "helper fixture"); if (!Files.exists(python)) Files.writeString(python, "python fixture");
        var helperRuntime = new NativeBridgeDefender.HelperRuntime(temporary.resolve("python-base"), temporary.resolve("venv"),
                ControlBuild.FileRef.measure(python), ControlBuild.FileRef.measure(helper), List.of(ControlBuild.FileRef.measure(python)), List.of(ControlBuild.FileRef.measure(helper)));
        Path metadata = temporary.resolve("tools.json"); if (!Files.exists(metadata)) Files.writeString(metadata, "{}");
        return new NativeBridgeBuild.Request(NativeBridgeBuild.REQUEST_SCHEMA, "software-machine", stage, temporary, source,
                NativeBridgeBuild.inventory(source), temporary.resolve("build"), temporary.resolve("scratch"), ControlBuild.FileRef.measure(metadata),
                new NativeBridgeBuild.Toolchain(toolPins.get(0), toolPins.get(1), toolPins.get(2), toolPins.get(3), toolPins.get(4), toolPins.get(5), toolPins.get(6)),
                List.of(new NativeBridgeBuild.Definition("XAR_CK3_EXAMPLE", NativeBridgeBuild.SwitchValue.ON)), 2, environment, build, stage == NativeBridgeBuild.Stage.REGISTER ? helperRuntime : null);
    }
    @Test void buildCommandHasOnlyTheRealDllAndInjectorTargets() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null);
        assertEquals(List.of("xar_ck3_bridge", "xar_ck3_bridge_injector"), NativeBridgeBuild.TARGETS);
        var command = NativeBridgeBuild.buildCommand(request);
        assertEquals(List.of("--target", "xar_ck3_bridge", "xar_ck3_bridge_injector"), command.subList(command.size() - 3, command.size()));
        assertFalse(command.stream().anyMatch(word -> word.contains("kinship") || word.contains("combat_roles")));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Definition("CMAKE_PROJECT_INCLUDE", NativeBridgeBuild.SwitchValue.ON));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Definition("XAR_CK3_EXAMPLE;EXECUTE", NativeBridgeBuild.SwitchValue.ON));
    }
    @Test void onlySourceDeclaredBooleanOptionsAndCompleteSourceTreeAreAccepted() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null); NativeBridgeBuild.validateSources(request);
        Files.writeString(request.sourceRoot().resolve("unlisted-resource.txt"), "new native input");
        assertThrows(IOException.class, () -> NativeBridgeBuild.validateSources(request));
    }
    @Test void causalStageFieldsAndOldFixtureProtocolCannotGrantBridgeQualification() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> request(NativeBridgeBuild.Stage.BUILD, null, null));
        var old = pin("research-actual.json", "{\"schema\":\"xar.shared-native-stage-actual/v2\",\"status\":\"PASS\",\"stage_id\":\"two-target-build\"}");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(old, NativeBridgeBuild.Stage.BUILD));
    }
    @Test void strictRequestRoundTripRejectsBooleanOrFractionalSequenceAndMissingFields() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null); var mapper = ControlBuild.strictMapper();
        assertEquals(request, mapper.readValue(mapper.writeValueAsBytes(request), NativeBridgeBuild.Request.class));
        for (String invalid : List.of("true", "2.0", "\"2\"")) {
            var tree = mapper.valueToTree(request); ((com.fasterxml.jackson.databind.node.ObjectNode) tree).set("parallel_jobs", mapper.readTree(invalid));
            assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(tree), NativeBridgeBuild.Request.class));
        }
        var missing = mapper.valueToTree(request); ((com.fasterxml.jackson.databind.node.ObjectNode) missing).remove("complete_sources");
        assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(missing), NativeBridgeBuild.Request.class));
    }
    @Test void unknownCommandOwnerAndNonzeroJobCannotPassCommandAdmission() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null); var actualPin = pin("request-pin.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, actualPin, actualPin,
                Instant.now().plusSeconds(20), 64L << 20, 4096, 10);
        var command = new NativeBridgeBuild.Command(NativeBridgeBuild.CommandKind.ENV_CAPTURE, List.of(request.tools().cmd().path()),
                request.stageRoot().toString(), null, null, null, null);
        var actual = new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA, "software-machine", NativeBridgeBuild.Stage.ENV, NativeBridgeBuild.Status.UNKNOWN,
                Instant.now().toString(), Instant.now().toString(), actualPin, grant, List.of(command), List.of(), List.of(), List.of(),
                null, null, null, List.of(), List.of(), List.of(), false, "child terminal unavailable");
        assertThrows(IOException.class, () -> NativeBridgeBuild.validateCommands(request, actual));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA, "software-machine", NativeBridgeBuild.Stage.ENV,
                NativeBridgeBuild.Status.PASS, Instant.now().toString(), Instant.now().toString(), actualPin, grant, List.of(), List.of(), List.of(), List.of(),
                null, null, null, List.of(), List.of(), List.of(), true, null));
    }

    @Test void rootLimitsRejectUnscopedOwnerAndMissingTerminalReserve() throws Exception {
        var metadata = pin("capacity-shape.json", "{}");
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeRootGate.Limits("owner", metadata,
                Instant.now().plusSeconds(30), 64L << 20, 32L << 20, 20));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeRootGate.Limits("/root", metadata,
                Instant.now().plusSeconds(30), 64L << 20, 4096, 20));
    }

    @Test void actualRootGateRejectsMalformedCapacityBeforeCreatingLockOrStage() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null);
        var requestPin = pin("root-negative-request.json", ControlBuild.strictMapper().writeValueAsString(request));
        var capacity = pin("root-malformed-capacity.json", "{}");
        var limits = new NativeBridgeRootGate.Limits("/root", capacity, Instant.now().plusSeconds(30),
                64L << 20, 32L << 20, 20);
        assertThrows(IOException.class, () -> NativeBridgeRootGate.open(requestPin, limits));
        assertFalse(Files.exists(request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
        assertFalse(Files.exists(request.stageRoot()));
    }

    @Test void historicalGrantCannotBorrowAnotherOwnersPinnedCapacity() throws Exception {
        var request = request(NativeBridgeBuild.Stage.ENV, null, null);
        var requestPin = pin("historical-negative-request.json", ControlBuild.strictMapper().writeValueAsString(request));
        var policy = pin("historical-policy-shape.json", "{}");
        Instant opened = Instant.now().minusSeconds(10), until = Instant.now().plusSeconds(60), at = Instant.now();
        var release = new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1", request.machineId(),
                opened.toString(), until.toString(), "RELEASED", "/root/other_owner", policy,
                List.of(request.buildRoot().toString(), request.scratchRoot().toString()), request.scratchRoot().toString(),
                java.util.Map.of("artifacts", 64L << 20),
                java.util.Map.of(request.buildRoot().getRoot().toString(), new CiBootstrap.VolumeBudget(1000, 900, 100, 0, 1, 1, 1, 1000, 102)),
                java.util.Map.of(), 128L << 20, 32L << 20);
        var capacity = pin("historical-capacity.json", ControlBuild.strictMapper().writeValueAsString(release));
        var grant = new NativeBridgeBuild.Grant(request.machineId(), "/root", request.stage(), requestPin, capacity,
                until.minusSeconds(1), 64L << 20, 32L << 20, 20);
        IOException rejected = assertThrows(IOException.class,
                () -> NativeBridgeRootGate.verifyHistorical(request, grant, at, at));
        assertTrue(rejected.getMessage().contains("owner/machine/stage/window/memory/allocation"));
        assertFalse(Files.exists(request.stageRoot()));
    }

    @Test void missingOwnerAndLegacyActualCannotEnterTheNewStrictProtocol() throws Exception {
        var ref = pin("negative-grant-ref.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                Instant.now().plusSeconds(30), 64L << 20, 32L << 20, 20);
        var mapper = ControlBuild.strictMapper();
        var intent = NativeBridgeBuild.writeNew(temporary.resolve("owner-negative-intent.json"), grant);
        var missing = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(intent.path())));
        missing.remove("owner_task");
        var missingPin = pin("owner-missing-intent.json", mapper.writeValueAsString(missing));
        assertThrows(IOException.class, () -> NativeBridgeBuild.readGrantEnvelope(missingPin));
        var old = pin("old-native-v1-actual.json", "{\"schema\":\"xar.native-bridge-build-actual/v1\",\"status\":\"PASS\"}");
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(old, NativeBridgeBuild.Stage.ENV));
    }

    @Test void productionIntentWriterAndReaderRoundTripExactUtcNanoseconds() throws Exception {
        // This is the actual execute -> INTENT writer and readAccepted -> INTENT reader.
        // The grant is codec input only; no Root gate, stage or successful native evidence is fabricated.
        var ref = pin("intent-codec-input.json", "{}");
        Instant deadline = Instant.parse("2030-01-02T03:04:05.123456789Z");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                deadline, 64L << 20, 32L << 20, 20);
        Path output = temporary.resolve("codec-INTENT.json");
        var written = NativeBridgeBuild.writeNew(output, grant);
        var tree = ControlBuild.strictMapper().readTree(Files.readAllBytes(output));
        assertTrue(tree.get("deadline").isTextual()); assertEquals(deadline.toString(), tree.get("deadline").textValue());
        assertEquals(grant, NativeBridgeBuild.readGrantEnvelope(written));
        assertEquals(written, ControlBuild.FileRef.measure(output));
        assertThrows(IOException.class, () -> NativeBridgeBuild.writeNew(output, grant));
        assertEquals(written, ControlBuild.FileRef.measure(output));
    }

    @Test void productionActualWriterAndReaderRoundTripNestedDeadlineWithoutGrantingAcceptance() throws Exception {
        var ref = pin("actual-codec-input.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                Instant.parse("2030-01-02T03:04:05.000000007Z"), 64L << 20, 32L << 20, 20);
        var red = new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA, "software-machine", NativeBridgeBuild.Stage.ENV,
                NativeBridgeBuild.Status.RED, "2026-10-23T00:00:00Z", "2026-10-23T00:00:01Z", ref, grant,
                List.of(), List.of(), List.of(), List.of(), null, null, null, List.of(), List.of(), List.of(), false,
                "Codec boundary only: no native command or successful stage exists");
        var written = NativeBridgeBuild.writeNew(temporary.resolve("codec-ACTUAL.json"), red);
        assertEquals(red, NativeBridgeBuild.readActualEnvelope(written));
        var tree = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(written.path())));
        assertTrue(tree.path("grant").get("deadline").isTextual());
        assertEquals(grant.deadline().toString(), tree.path("grant").get("deadline").textValue());
        assertThrows(IOException.class, () -> NativeBridgeBuild.readAccepted(written, NativeBridgeBuild.Stage.ENV));
    }

    @Test void productionGrantReaderRejectsWrongTemporalTypesOffsetsAndInvalidDates() throws Exception {
        var ref = pin("temporal-negative-input.json", "{}");
        var grant = new NativeBridgeBuild.Grant("software-machine", "/root", NativeBridgeBuild.Stage.ENV, ref, ref,
                Instant.parse("2030-01-02T03:04:05Z"), 64L << 20, 32L << 20, 20);
        var original = NativeBridgeBuild.writeNew(temporary.resolve("temporal-original.json"), grant);
        var mapper = ControlBuild.strictMapper();
        var tree = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(original.path())));
        int index = 0;
        for (String invalid : List.of("true", "1", "1.5", "null", "\"2030-01-02T03:04:05+00:00\"",
                "\"2030-02-30T03:04:05Z\"", "\"123456789\"")) {
            var changed = tree.deepCopy(); changed.set("deadline", mapper.readTree(invalid));
            var malformed = pin("temporal-invalid-" + index++ + ".json", mapper.writeValueAsString(changed));
            assertThrows(IOException.class, () -> NativeBridgeBuild.readGrantEnvelope(malformed));
        }
        assertEquals(grant, NativeBridgeBuild.readGrantEnvelope(original));
    }

    @Test void compilerHelpProductionArgvAndPersistedCommandConsumerKeepTheObservedHelpContract()throws Exception{
        var fixture=helpCommands();
        assertEquals("/HELP",NativeBridgeBuild.compilerHelpCommand(fixture.request()).getLast());
        NativeBridgeBuild.validateCommands(fixture.request(),fixture.actual());
        Path recorded=temporary.resolve("help-command-codec-data.json");
        var pin=NativeBridgeBuild.writeNew(recorded,fixture.actual());
        var decoded=NativeBridgeBuild.readActualEnvelope(pin);
        assertEquals(fixture.actual(),decoded);NativeBridgeBuild.validateCommands(fixture.request(),decoded);
        var commands=new ArrayList<>(decoded.commands());var last=commands.getLast();
        commands.set(commands.size()-1,new NativeBridgeBuild.Command(last.kind(),
                List.of(fixture.request().tools().compiler().path(),"/?"),last.cwd(),last.owner(),last.terminal(),last.stdout(),last.stderr()));
        assertThrows(IOException.class,()->NativeBridgeBuild.validateCommands(fixture.request(),commandData(fixture,commands)));
        // Even complete well-typed software command DATA is not an accepted actual ENV.
        assertThrows(IOException.class,()->NativeBridgeBuild.readAccepted(pin,NativeBridgeBuild.Stage.ENV));
    }
    @Test void correctedCompilerHelpNeverHidesD8004ExitUnknownOwnerTimeoutOrLiveJob()throws Exception{
        var fixture=helpCommands();var original=fixture.actual().commands().getLast();var identity=original.owner();
        for(var result:List.of(
                new WindowsJobProcess.CommandResult(identity,2,0.2,new WindowsJobProcess.Accounting(4096,0,64L<<20,8704),null),
                new WindowsJobProcess.CommandResult(identity,0,0.2,new WindowsJobProcess.Accounting(4096,1,64L<<20,8704),null),
                new WindowsJobProcess.CommandResult(identity,0,0.2,new WindowsJobProcess.Accounting(4096,0,64L<<20,8704),"timeout_or_release_expired"),
                new WindowsJobProcess.CommandResult(identity,0,0.2,new WindowsJobProcess.Accounting(4096,0,128L<<20,8704),null))){
            var commands=new ArrayList<>(fixture.actual().commands());commands.set(commands.size()-1,
                    new NativeBridgeBuild.Command(original.kind(),original.argv(),original.cwd(),identity,result,original.stdout(),original.stderr()));
            assertThrows(IOException.class,()->NativeBridgeBuild.validateCommands(fixture.request(),commandData(fixture,commands)));
        }
        for(var command:List.of(
                new NativeBridgeBuild.Command(original.kind(),original.argv(),original.cwd(),null,original.terminal(),original.stdout(),original.stderr()),
                new NativeBridgeBuild.Command(original.kind(),original.argv(),original.cwd(),identity,null,original.stdout(),original.stderr()),
                new NativeBridgeBuild.Command(original.kind(),original.argv(),temporary.toString(),identity,original.terminal(),original.stdout(),original.stderr()))){
            var commands=new ArrayList<>(fixture.actual().commands());commands.set(commands.size()-1,command);
            assertThrows(IOException.class,()->NativeBridgeBuild.validateCommands(fixture.request(),commandData(fixture,commands)));
        }
        var missing=new ArrayList<>(fixture.actual().commands());missing.remove(0);
        assertThrows(IOException.class,()->NativeBridgeBuild.validateCommands(fixture.request(),commandData(fixture,missing)));
        Files.writeString(Path.of(original.stdout().path()),"changed original compiler output");
        assertThrows(IOException.class,()->NativeBridgeBuild.validateCommands(fixture.request(),fixture.actual()));
    }
    @Test void actualSharedReducerOutcomeRoundTripsIntoTheNativeCommandAndEnvConsumers() throws Exception {
        var fixture=helpCommands();var command=fixture.actual().commands().getLast();
        var compiler=fixture.request().tools().compiler();
        var binding=new MsvcAuxiliaryPolicy.Binding(MsvcAuxiliaryPolicy.SCHEMA,
                image(compiler,11),image(pin("vctip.exe","software VCTIP image"),12),
                image(pin("mspdbsrv.exe","software PDB image"),13));
        var execution=new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1",binding,compiler);
        var backend=new MsvcAuxiliaryPolicy.Backend(){
            @Override public MsvcAuxiliaryPolicy.Root root(){return new MsvcAuxiliaryPolicy.Root(command.owner(),0,0);}
            @Override public int active(){return 0;}
            @Override public List<Long> members(){return List.of();}
            @Override public MsvcAuxiliaryPolicy.Member retain(long pid){throw new AssertionError("Natural-drain software fixture has no member");}
        };
        var outcome=MsvcAuxiliaryPolicy.finish(backend,execution,new MsvcAuxiliaryPolicy.Budget(
                System.nanoTime()+2_000_000_000L,Instant.now().plusSeconds(20)),()->{});
        assertTrue(outcome.completed());
        var actual=currentActual(fixture,List.of(new NativeBridgeBuild.AuxiliaryCommand(command.kind(),outcome)));
        var mapper=RootNativePlanJson.mapper();var encoded=pin("current-msvc-actual.json",mapper.writeValueAsString(actual));
        var decoded=NativeBridgeBuild.readActualEnvelope(encoded);
        assertEquals(actual,decoded);NativeBridgeBuild.validateCommands(fixture.request(),decoded);
        assertEquals(binding,NativeBridgeBuild.environmentCompilerBinding(decoded));
        assertThrows(IOException.class,()->NativeBridgeBuild.readAccepted(encoded,NativeBridgeBuild.Stage.ENV),
                "Software reducer/codec coverage grants no real Root, ENV, compiler execution or production BUILD");
    }
    @Test void newActualCannotLoseItsAuxiliaryFieldAndHistoricalEnvCannotQualifyNewBuild() throws Exception {
        var fixture=helpCommands();var mapper=RootNativePlanJson.mapper();
        var current=currentActual(fixture,List.of());
        assertThrows(IOException.class,()->NativeBridgeBuild.validateCommands(fixture.request(),current));
        var tree=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(current);
        tree.remove("auxiliary_commands");var missing=pin("current-missing-aux.json",mapper.writeValueAsString(tree));
        assertThrows(IOException.class,()->NativeBridgeBuild.readActualEnvelope(missing));
        var historical=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(fixture.actual());
        historical.remove("auxiliary_commands");
        var old=NativeBridgeBuild.readActualEnvelope(pin("historical-v2.json",mapper.writeValueAsString(historical)));
        assertEquals(NativeBridgeBuild.LEGACY_ACTUAL_SCHEMA,old.schema());
        NativeBridgeBuild.validateCommands(fixture.request(),old);
        assertThrows(IOException.class,()->NativeBridgeBuild.environmentCompilerBinding(old));
    }
    @Test void sameSourceCompilerCacheKeepsExistingObjectsAndReconfigureStillSelectsProductionTargets() throws Exception {
        var request=request(NativeBridgeBuild.Stage.ENV,null,null);Files.createDirectory(request.buildRoot());
        Path object=request.buildRoot().resolve("retained.obj");Files.writeString(object,"existing compiler output");
        var objectBefore=ControlBuild.FileRef.measure(object);
        Path cache=request.buildRoot().resolve("CMakeCache.txt");
        String values=reusableCache(request);
        Files.writeString(cache,values);var cacheBefore=ControlBuild.FileRef.measure(cache);
        NativeBridgeBuild.prepareBuildRoot(request);
        assertEquals(objectBefore,ControlBuild.FileRef.measure(object));assertEquals(cacheBefore,ControlBuild.FileRef.measure(cache));
        assertTrue(NativeBridgeBuild.configureCommand(request).contains("-DBUILD_TESTING=OFF"));
        var configure=NativeBridgeBuild.configureCommand(request);
        assertEquals("XAR_*",configure.get(configure.indexOf("-U")+1));
        assertTrue(configure.indexOf("-U")<configure.indexOf("-DXAR_CK3_EXAMPLE=ON"),
                "Old optional project flags reset to source defaults before exact Request definitions are reapplied");
        assertEquals(List.of("xar_ck3_bridge","xar_ck3_bridge_injector"),NativeBridgeBuild.buildCommand(request).subList(6,8));
        Files.writeString(cache,values.replace(request.sourceRoot().toString(),temporary.resolve("other-source").toString()));
        assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));objectBefore.verify();
    }
    private static String reusableCache(NativeBridgeBuild.Request request) {
        return "CMAKE_HOME_DIRECTORY:INTERNAL="+request.sourceRoot()+"\nCMAKE_CACHEFILE_DIR:INTERNAL="+request.buildRoot()
                +"\nCMAKE_GENERATOR:INTERNAL=Ninja\nCMAKE_CXX_COMPILER:UNINITIALIZED="+request.tools().compiler().path()
                +"\nCMAKE_C_COMPILER:UNINITIALIZED="+request.tools().compiler().path()
                +"\nCMAKE_MAKE_PROGRAM:FILEPATH="+request.tools().ninja().path()
                +"\nCMAKE_BUILD_TYPE:STRING=Release\nBUILD_TESTING:BOOL=ON\n";
    }
    @Test void samePhysicalCompilerWithDifferentCaseIsRejectedBeforeWarmCacheMutation() throws Exception {
        var request=request(NativeBridgeBuild.Stage.ENV,null,null);Files.createDirectory(request.buildRoot());
        Path object=request.buildRoot().resolve("retained.obj");Files.writeString(object,"retained compiler output");
        var objectBefore=SharedSourceFiles.observe(object);
        Path compiler=Path.of(request.tools().compiler().path()), alias=compiler.resolveSibling("CL.EXE");
        assertEquals(SharedSourceFiles.observe(compiler).nativeFile().identityKey(),
                SharedSourceFiles.observe(alias).nativeFile().identityKey(),"Actual Windows case alias is the same physical file");
        Path cache=request.buildRoot().resolve("CMakeCache.txt");
        String values=reusableCache(request).replace(request.tools().compiler().path(),alias.toString());
        Files.writeString(cache,values);var cacheBefore=SharedSourceFiles.observe(cache);
        IOException failure=assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));
        assertTrue(failure.getMessage().contains("spelling would reset CMake"));
        SharedSourceFiles.assertUnchanged(objectBefore);SharedSourceFiles.assertUnchanged(cacheBefore);
        // An explicit input bound to the original cache spelling is legal; no command or Native qualification is fabricated.
        NativeBridgeBuild.requireReusableCMakeCache(request.sourceRoot(),request.buildRoot(),
                ControlBuild.FileRef.measure(alias),request.tools().ninja());
        SharedSourceFiles.assertUnchanged(objectBefore);SharedSourceFiles.assertUnchanged(cacheBefore);
    }
    @Test void sameBytesDifferentToolImageAndCygwinStyleNinjaCannotEnterWarmConfigure() throws Exception {
        var request=request(NativeBridgeBuild.Stage.ENV,null,null);Files.createDirectory(request.buildRoot());
        Path object=request.buildRoot().resolve("retained.obj");Files.writeString(object,"retained output");
        var before=SharedSourceFiles.observe(object);Path cache=request.buildRoot().resolve("CMakeCache.txt");
        for (var tool:List.of(request.tools().compiler(),request.tools().ninja())) {
            Path copy=temporary.resolve("copy-"+Path.of(tool.path()).getFileName());Files.copy(Path.of(tool.path()),copy);
            assertEquals(tool.sha256(),ControlBuild.FileRef.measure(copy).sha256());
            assertNotEquals(SharedSourceFiles.observe(Path.of(tool.path())).nativeFile().identityKey(),
                    SharedSourceFiles.observe(copy).nativeFile().identityKey());
            Files.writeString(cache,reusableCache(request).replace(tool.path(),copy.toString()));
            IOException failure=assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));
            assertTrue(failure.getMessage().contains("qualified physical image"));SharedSourceFiles.assertUnchanged(before);
        }
        Files.writeString(cache,reusableCache(request).replace("CMAKE_GENERATOR:INTERNAL=Ninja","CMAKE_GENERATOR:INTERNAL=Unix Makefiles"));
        assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));SharedSourceFiles.assertUnchanged(before);
        Files.writeString(cache,reusableCache(request).replace("CMAKE_BUILD_TYPE:STRING=Release","CMAKE_BUILD_TYPE:STRING=Debug"));
        assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));SharedSourceFiles.assertUnchanged(before);
        Files.writeString(cache,reusableCache(request)+"CMAKE_CXX_COMPILER:FILEPATH="+request.tools().compiler().path()+"\n");
        assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));SharedSourceFiles.assertUnchanged(before);
        Files.writeString(cache,reusableCache(request).replace("CMAKE_C_COMPILER:UNINITIALIZED="+request.tools().compiler().path()+"\n",""));
        assertThrows(IOException.class,()->NativeBridgeBuild.prepareBuildRoot(request));SharedSourceFiles.assertUnchanged(before);
    }
    @Test void existingFileApiQueriesAreReusedWithoutOverwritingTheirBodies() throws Exception {
        Path query=temporary.resolve("codemodel-v2");NativeBridgeBuild.prepareQuery(query);
        var original=ControlBuild.FileRef.measure(query);NativeBridgeBuild.prepareQuery(query);original.verify();
        Files.writeString(query,"existing nonempty query");var nonempty=ControlBuild.FileRef.measure(query);
        assertThrows(IOException.class,()->NativeBridgeBuild.prepareQuery(query));nonempty.verify();
    }
    private static MsvcAuxiliaryPolicy.Image image(ControlBuild.FileRef pin,long id){
        return new MsvcAuxiliaryPolicy.Image(pin.path(),"1",Long.toString(id),pin.bytes(),pin.sha256());
    }
    private static NativeBridgeBuild.Actual currentActual(HelpCommands fixture,List<NativeBridgeBuild.AuxiliaryCommand> auxiliary){
        var a=fixture.actual();return new NativeBridgeBuild.Actual(NativeBridgeBuild.ACTUAL_SCHEMA,a.machineId(),a.stage(),a.status(),
                a.startedAtUtc(),a.observedAtUtc(),a.requestRef(),a.grant(),a.commands(),a.sourceWitnesses(),a.toolRefs(),a.runtimeRefs(),
                a.snapshotRef(),a.manifestRef(),a.helperReceiptRef(),a.graphRefs(),a.dependencyRefs(),a.outputRefs(),a.sourceUnchanged(),a.error(),auxiliary);
    }
    private record HelpCommands(NativeBridgeBuild.Request request,NativeBridgeBuild.Actual actual){ }
    private HelpCommands helpCommands()throws Exception{
        var request=request(NativeBridgeBuild.Stage.ENV,null,null);Files.createDirectories(request.stageRoot());
        var input=pin("help-software-command-input.json","not native stage authority");
        var grant=new NativeBridgeBuild.Grant(request.machineId(),"/root",request.stage(),input,input,
                Instant.now().plusSeconds(60),64L<<20,32L<<20,20);
        var commands=new ArrayList<NativeBridgeBuild.Command>();int index=0;
        for(var kind:List.of(NativeBridgeBuild.CommandKind.ENV_CAPTURE,NativeBridgeBuild.CommandKind.CMAKE_VERSION,
                NativeBridgeBuild.CommandKind.NINJA_VERSION,NativeBridgeBuild.CommandKind.COMPILER_HELP)){
            List<String> argv=switch(kind){
                case ENV_CAPTURE->List.of(request.tools().cmd().path(),"/d","/c",request.stageRoot().resolve("capture.cmd").toString());
                case CMAKE_VERSION->List.of(request.tools().cmake().path(),"--version");
                case NINJA_VERSION->List.of(request.tools().ninja().path(),"--version");
                case COMPILER_HELP->NativeBridgeBuild.compilerHelpCommand(request);
                default->throw new AssertionError(kind);
            };
            var identity=new WindowsJobProcess.ProcessIdentity(100+index++,"1",argv.getFirst());
            var result=new WindowsJobProcess.CommandResult(identity,0,0.2,new WindowsJobProcess.Accounting(4096,0,64L<<20,8704),null);
            Path stdout=request.stageRoot().resolve(kind.name().toLowerCase(java.util.Locale.ROOT)+".stdout.log");
            Path stderr=request.stageRoot().resolve(kind.name().toLowerCase(java.util.Locale.ROOT)+".stderr.log");
            Files.writeString(stdout,"owned software command codec data");Files.writeString(stderr,"");
            commands.add(new NativeBridgeBuild.Command(kind,argv,request.stageRoot().toString(),identity,result,
                    ControlBuild.FileRef.measure(stdout),ControlBuild.FileRef.measure(stderr)));
        }
        var actual=new NativeBridgeBuild.Actual(NativeBridgeBuild.LEGACY_ACTUAL_SCHEMA,request.machineId(),request.stage(),NativeBridgeBuild.Status.RED,
                Instant.now().toString(),Instant.now().toString(),input,grant,commands,List.of(),List.of(),List.of(),null,null,null,
                List.of(),List.of(),List.of(),false,"Software command validation DATA; no native stage was executed or qualified");
        return new HelpCommands(request,actual);
    }
    private static NativeBridgeBuild.Actual commandData(HelpCommands fixture,List<NativeBridgeBuild.Command> commands){
        var a=fixture.actual();return new NativeBridgeBuild.Actual(a.schema(),a.machineId(),a.stage(),a.status(),a.startedAtUtc(),a.observedAtUtc(),a.requestRef(),a.grant(),
                commands,a.sourceWitnesses(),a.toolRefs(),a.runtimeRefs(),a.snapshotRef(),a.manifestRef(),a.helperReceiptRef(),a.graphRefs(),a.dependencyRefs(),a.outputRefs(),a.sourceUnchanged(),a.error());
    }
}
