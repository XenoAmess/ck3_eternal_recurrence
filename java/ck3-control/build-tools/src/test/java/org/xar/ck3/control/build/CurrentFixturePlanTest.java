package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CurrentFixturePlanTest {
    @TempDir Path root;
    private static final String COMMANDER="xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test";
    private static ControlBuild.FileRef pin(Path path) {
        return new ControlBuild.FileRef(path.toString(),1,"0".repeat(64));
    }
    private NativeFixtureBuild.CurrentFixturePlan plan(String schema,String owner,Path build) {
        return plan(schema,owner,build,NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER);
    }
    private NativeFixtureBuild.CurrentFixturePlan plan(String schema,String owner,Path build,NativeFixtureBuild.FixtureTarget target) {
        return new NativeFixtureBuild.CurrentFixturePlan(schema,"xenoamess-full-tower-eb9d2c1186",owner,
                root.resolve("repository"),pin(root.resolve("tools.json")),pin(root.resolve("source.json")),
                pin(root.resolve("binding.json")),pin(root.resolve("env.json")),root.resolve("compile"),build,
                root.resolve("control"),target,
                List.of(new NativeBridgeBuild.Definition("XAR_ENABLE_TEST",NativeBridgeBuild.SwitchValue.ON)),1,512L<<20);
    }
    private String reusableCache(NativeFixtureBuild.CurrentFixturePlan plan, ControlBuild.FileRef compiler,
            ControlBuild.FileRef ninja) {
        return "CMAKE_HOME_DIRECTORY:INTERNAL="+plan.compileSourceRoot()+"\nCMAKE_CACHEFILE_DIR:INTERNAL="+plan.buildRoot()
                +"\nCMAKE_GENERATOR:INTERNAL=Ninja\nCMAKE_BUILD_TYPE:STRING=Release\nBUILD_TESTING:BOOL=OFF"
                +"\nCMAKE_CXX_COMPILER:UNINITIALIZED="+compiler.path()+"\nCMAKE_C_COMPILER:UNINITIALIZED="+compiler.path()
                +"\nCMAKE_MAKE_PROGRAM:UNINITIALIZED="+ninja.path()+"\n";
    }
    private Path cacheFile(NativeFixtureBuild.CurrentFixturePlan plan, String contents) throws Exception {
        Files.createDirectories(plan.compileSourceRoot());Files.createDirectories(plan.buildRoot());
        Path cache=plan.buildRoot().resolve("CMakeCache.txt");Files.writeString(cache,contents);return cache;
    }
    @Test void realCurrentConfigurePreflightPreservesCacheAndObjectsBeforePreparingQueries() throws Exception {
        // Real cache/tool files through the production preflight/query seam; no qualified ENV or process is fabricated.
        var compiler=actualFile(root.resolve("tools/Hostx64/x64/cl.exe"));
        var ninja=actualFile(root.resolve("tools/ninja.exe"));
        for(var target:List.of(NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER,
                NativeFixtureBuild.FixtureTarget.HOLY_ORDER_WAR_ELIGIBILITY)) {
            String schema=target==NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER
                    ?NativeFixtureBuild.CURRENT_PLAN_SCHEMA:NativeFixtureBuild.CURRENT_HOLY_PLAN_SCHEMA;
            var plan=plan(schema,"/root/native_fixtures63",root.resolve(target.name()),target);
            var cache=ControlBuild.FileRef.measure(cacheFile(plan,reusableCache(plan,compiler,ninja)));
            var object=actualFile(plan.buildRoot().resolve("retained.obj"));
            NativeFixtureBuild.prepareCurrentCMakeQuery(plan,List.of(compiler,ninja));
            NativeFixtureBuild.prepareCurrentCMakeQuery(plan,List.of(compiler,ninja));
            cache.verify();object.verify();
            for(String name:List.of("codemodel-v2","cmakeFiles-v1")) {
                Path query=plan.buildRoot().resolve(".cmake/api/v1/query").resolve(name);
                assertTrue(Files.isRegularFile(query));assertEquals(0,Files.size(query));
            }
        }
    }
    @Test void compilerCaseAliasAndForeignNinjaFailBeforeAnyFileApiDirectory() throws Exception {
        var compiler=actualFile(root.resolve("tools/Hostx64/x64/cl.exe"));
        var ninja=actualFile(root.resolve("tools/ninja.exe"));
        String alias=compiler.path().replace("Hostx64","HostX64");
        assertNotEquals(compiler.path(),alias);
        assertTrue(Files.isSameFile(Path.of(alias),Path.of(compiler.path())),
                "Regression uses the same Windows file under the compiler spelling that triggered CMake reset");
        var foreignNinja=actualFile(root.resolve("foreign/ninja.exe"));
        for(boolean compilerAlias:List.of(true,false)) {
            var plan=plan(NativeFixtureBuild.CURRENT_HOLY_PLAN_SCHEMA,"/root/native_fixtures63",
                    root.resolve(compilerAlias?"case-alias":"foreign-ninja"),NativeFixtureBuild.FixtureTarget.HOLY_ORDER_WAR_ELIGIBILITY);
            String values=reusableCache(plan,compiler,ninja);
            values=compilerAlias?values.replace(compiler.path(),alias):values.replace(ninja.path(),foreignNinja.path());
            var cache=ControlBuild.FileRef.measure(cacheFile(plan,values));
            var object=actualFile(plan.buildRoot().resolve("retained.obj"));
            assertThrows(IOException.class,()->NativeFixtureBuild.prepareCurrentCMakeQuery(plan,List.of(compiler,ninja)));
            assertFalse(Files.exists(plan.buildRoot().resolve(".cmake")));
            cache.verify();object.verify();
        }
    }
    @Test void currentConfigureUsesOriginalUniqueToolPinsAndRejectsChangedContentBeforeQueries() throws Exception {
        var compiler=actualFile(root.resolve("tools/Hostx64/x64/cl.exe"));
        var ninja=actualFile(root.resolve("tools/ninja.exe"));
        var plan=plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build"));
        var cache=ControlBuild.FileRef.measure(cacheFile(plan,reusableCache(plan,compiler,ninja)));
        assertThrows(IOException.class,()->NativeFixtureBuild.prepareCurrentCMakeQuery(plan,List.of(ninja)));
        assertThrows(IOException.class,()->NativeFixtureBuild.prepareCurrentCMakeQuery(plan,List.of(compiler,ninja,compiler)));
        Files.writeString(Path.of(compiler.path()),"changed after qualified tool reference");
        assertThrows(IOException.class,()->NativeFixtureBuild.prepareCurrentCMakeQuery(plan,List.of(compiler,ninja)));
        assertFalse(Files.exists(plan.buildRoot().resolve(".cmake")));cache.verify();
    }
    @Test void exactPlanRoundTripAndChangedBytes() throws Exception {
        var expected=plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build"));
        Path file=root.resolve("plan.json");Files.write(file,RootNativePlanJson.mapper().writeValueAsBytes(expected));
        var exact=ControlBuild.FileRef.measure(file);
        assertEquals(expected,NativeFixtureBuild.readCurrentPlan(exact));
        assertEquals(COMMANDER,expected.target().targetName());
        Files.writeString(file," ");
        assertThrows(IOException.class,()->NativeFixtureBuild.readCurrentPlan(exact));
    }
    @Test void rejectOldOwnerSchemaAndOverlap() {
        assertThrows(IllegalArgumentException.class,()->plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixture09",root.resolve("build")));
        assertThrows(IllegalArgumentException.class,()->plan("xar.prisoners-combatroles-shared-native-build-plan.v1","/root/native_fixtures63",root.resolve("build")));
        assertThrows(IllegalArgumentException.class,()->plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("compile/child")));
    }
    @Test void strictPlanTypes() throws Exception {
        var json=RootNativePlanJson.mapper();var tree=json.valueToTree(plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build")));
        var object=(com.fasterxml.jackson.databind.node.ObjectNode)tree;
        object.put("parallel_jobs",true);Path file=root.resolve("bad.json");Files.write(file,json.writeValueAsBytes(tree));
        assertThrows(IOException.class,()->NativeFixtureBuild.readCurrentPlan(ControlBuild.FileRef.measure(file)));
        object.put("parallel_jobs",1);object.put("other_owner","/root/native_fixture09");Files.write(file,json.writeValueAsBytes(tree));
        assertThrows(IOException.class,()->NativeFixtureBuild.readCurrentPlan(ControlBuild.FileRef.measure(file)));
    }
    private NativeFixtureBuild.Target target(String name,List<String> artifacts) {
        return new NativeFixtureBuild.Target(name,"actual-cmake-id",NativeFixtureBuild.TargetType.EXECUTABLE,
                pin(root.resolve("target.json")),List.of(),artifacts,List.of(),List.of(),null,null);
    }
    @Test void artifactScope() throws Exception {
        Path build=root.resolve("build"),exe=build.resolve(COMMANDER+".exe"),pdb=build.resolve(COMMANDER+".pdb");
        assertEquals(exe,NativeFixtureBuild.currentPrimaryArtifact(build,target(COMMANDER,List.of(exe.toString(),pdb.toString()))));
        assertThrows(IOException.class,()->NativeFixtureBuild.currentPrimaryArtifact(build,target(COMMANDER,List.of(root.resolve(COMMANDER+".exe").toString()))));
        assertThrows(IOException.class,()->NativeFixtureBuild.currentPrimaryArtifact(build,target(COMMANDER,List.of(exe.toString(),build.resolve("foreign.exe").toString()))));
        assertThrows(IOException.class,()->NativeFixtureBuild.currentPrimaryArtifact(build,target("other_target",List.of(exe.toString()))));
    }
    @Test void actualCopyPreservesOriginalProofAcrossCacheRewrite() throws Exception {
        String previous=System.getProperty("jna.tmpdir");
        // The harness owns the VM-lifetime native DLL; @TempDir owns only this test's data files.
        assertNotNull(previous,"Harness must supply approved JNA scratch");assertFalse(previous.isBlank());
        try {
            Path original=root.resolve("mutable-generated.json"),copy=root.resolve("retained-generated.json");
            Files.writeString(original,"original configure bytes");
            var row=NativeFixtureBuild.retainFixtureFile(ControlBuild.FileRef.measure(original),copy);
            assertEquals(Files.readString(original),Files.readString(copy));
            assertThrows(IllegalArgumentException.class,()->new NativeFixtureBuild.RetainedFixtureFile(row.original(),row.original()));
            Files.writeString(original,"later legitimate configure");
            assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(row.original()));
            SharedSourceFiles.assertUnchanged(row.retained());
            assertEquals("original configure bytes",Files.readString(copy));
        } finally { if(previous==null)System.clearProperty("jna.tmpdir");else System.setProperty("jna.tmpdir",previous); }
    }
    @Test void currentScanReadsLargeMetadataBeforeBusinessRejection() throws Exception {
        Path large=root.resolve("large-unit-metadata.json");
        Files.writeString(large,"{\"schema\":\"unit-only-wrong-schema\"}"+" ".repeat((2<<20)+1));
        assertTrue(Files.size(large)>(2L<<20) && Files.size(large)<(32L<<20));
        var unused=pin(root.resolve("not-opened-authority"));
        var card=new NativeFixtureBuild.ResourceCard(NativeFixtureBuild.CURRENT_CARD_SCHEMA,
                "xenoamess-full-tower-eb9d2c1186","2026-10-26T00:00:00Z","2026-10-26T00:01:00Z",
                "/root/native_fixtures63",NativeFixtureBuild.ResourceStatus.ADMITTED_SINGLE_STAGE,
                NativeFixtureBuild.Stage.COMBAT,16L<<20,4096,1,unused,unused,unused,unused,unused,unused,
                List.of(ControlBuild.FileRef.measure(large)),List.of(root.toString()));
        var method=NativeFixtureBuild.class.getDeclaredMethod("requireCurrentRegistration",
                NativeFixtureBuild.CurrentFixturePlan.class,NativeFixtureBuild.ResourceCard.class,NativeFixtureBuild.Actual.class);
        method.setAccessible(true);
        var rejection=assertThrows(java.lang.reflect.InvocationTargetException.class,()->method.invoke(null,null,card,null)).getCause();
        assertInstanceOf(IOException.class,rejection);
        assertEquals("One exact completed built-fixture registration required",rejection.getMessage());
    }
    @Test void boundEnvironmentMatchesCompileMapAndHistoricalMatchingDoesNotOpenDev() throws Exception {
        // Real file mapping plus shared public producer and original reader; no Source/ENV qualification.
        String old=System.getProperty("jna.tmpdir");
        assertNotNull(old,"Harness must supply approved JNA scratch");assertFalse(old.isBlank());
        try {
            Path retained=root.resolve("retained"),compile=root.resolve("compile");
            Files.createDirectories(retained);Files.createDirectories(compile);
            Files.writeString(retained.resolve("sample.cpp"),"same source");Files.writeString(compile.resolve("sample.cpp"),"same source");
            var json=RootNativePlanJson.mapper();
            var historicalTools=actualFile(root.resolve("historical-source-tools.json"));
            var tools=actualFile(root.resolve("tools.json"));
            var retainedSources=NativeBridgeBuild.inventory(retained);
            // This software Source candidate deliberately has no qualified receipt and grants no authority.
            var sourceCandidate=new NativeCombinedSourceCut.Actual("xar.native-combined-source-cut-actual/v1",
                    "xenoamess-full-tower-eb9d2c1186","2026-10-26T00:00:00Z",historicalTools,
                    historicalTools,List.of(historicalTools),historicalTools,retained.toString(),retained.toString(),
                    retainedSources,retainedSources,List.of(),retainedSources.stream().mapToLong(ControlBuild.FileRef::bytes).sum(),
                    0,true,"FROZEN_SOURCE_ONLY_NOT_ENV_BUILD_REGISTER_NATIVE_TEST_OR_GAME");
            Path source=root.resolve("unqualified-source-marker");Files.write(source,json.writeValueAsBytes(sourceCandidate));
            var binding=CompileSourceBinding.captureFiles(tools,List.of(tools),"xenoamess-full-tower-eb9d2c1186",
                    ControlBuild.FileRef.measure(source),retained,NativeBridgeBuild.inventory(retained),compile);
            Path bindingFile=root.resolve("binding.json");
            Files.write(bindingFile,json.writeValueAsBytes(binding));var bindingRef=ControlBuild.FileRef.measure(bindingFile);
            var plan=new NativeFixtureBuild.CurrentFixturePlan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,
                    "xenoamess-full-tower-eb9d2c1186","/root/native_fixtures63",root.resolve("repository"),tools,
                    binding.retainedSourceActualRef(),bindingRef,pin(root.resolve("env.json")),compile,root.resolve("build"),
                    root.resolve("control"),NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER,List.of(),1,512L<<20);
            var chain=new NativeBridgeBuild.Toolchain(pin(root.resolve("cmd.exe")),pin(root.resolve("vcvars64.bat")),
                    pin(root.resolve("java.exe")),pin(root.resolve("cmake.exe")),pin(root.resolve("ninja.exe")),
                    pin(root.resolve("cl.exe")),pin(root.resolve("link.exe")));
            var input=new NativeCombinedSourceCut.BoundEnvironmentInput("xar.native-combined-environment-input/v3",bindingRef,
                    plan.canonicalRepository(),tools,chain,List.of(),1,plan.buildRoot(),root.resolve("env-scratch"),
                    null,root,root.resolve("request.json"));
            var request=NativeCombinedSourceCut.composeBoundEnvironmentRequest(input,binding);
            Path requestFile=root.resolve("request.json");Files.write(requestFile,json.writeValueAsBytes(request));
            var decoded=NativeBridgeBuild.readRequest(ControlBuild.FileRef.measure(requestFile));
            var sourceDecoded=json.readValue(Files.readAllBytes(source),NativeCombinedSourceCut.Actual.class);
            assertEquals(sourceCandidate,sourceDecoded);
            assertNotEquals(sourceDecoded.producerToolsBuildRef(),plan.qualifiedToolsBuildRef());
            assertEquals(binding.producerToolsBuildRef(),plan.qualifiedToolsBuildRef());
            assertDoesNotThrow(()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,decoded));
            assertThrows(IOException.class,()->NativeCombinedSourceCut.readAcceptedSource(binding.retainedSourceActualRef()));
            assertThrows(IOException.class,()->CompileSourceBinding.readHistorical(bindingRef));
            var tree=(com.fasterxml.jackson.databind.node.ObjectNode)json.valueToTree(request);
            tree.put("source_root",retained.toString());
            var wrongRoot=json.treeToValue(tree,NativeBridgeBuild.Request.class);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,wrongRoot));
            tree=(com.fasterxml.jackson.databind.node.ObjectNode)json.valueToTree(request);
            tree.withArray("complete_sources").add(json.valueToTree(bindingRef));
            var extraBinding=json.treeToValue(tree,NativeBridgeBuild.Request.class);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,extraBinding));
            tree=(com.fasterxml.jackson.databind.node.ObjectNode)json.valueToTree(request);
            tree.set("compile_source_binding_ref",json.valueToTree(pin(root.resolve("other-binding.json"))));
            var wrongBinding=json.treeToValue(tree,NativeBridgeBuild.Request.class);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,wrongBinding));
            tree=(com.fasterxml.jackson.databind.node.ObjectNode)json.valueToTree(request);
            tree.put("schema",NativeBridgeBuild.REQUEST_SCHEMA);tree.putNull("compile_source_binding_ref");
            var oldSchema=json.treeToValue(tree,NativeBridgeBuild.Request.class);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,oldSchema));
            tree=(com.fasterxml.jackson.databind.node.ObjectNode)json.valueToTree(request);
            tree.set("qualified_tools_build",json.valueToTree(historicalTools));
            var wrongEnvironmentTools=json.treeToValue(tree,NativeBridgeBuild.Request.class);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,wrongEnvironmentTools));
            var bindingTree=(com.fasterxml.jackson.databind.node.ObjectNode)json.valueToTree(binding);
            bindingTree.set("producer_tools_build_ref",json.valueToTree(historicalTools));
            var wrongBindingTools=json.treeToValue(bindingTree,CompileSourceBinding.Binding.class);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,wrongBindingTools,decoded));
            Files.delete(compile.resolve("sample.cpp"));
            assertDoesNotThrow(()->CompileSourceBinding.verifyRetainedFiles(binding));
            assertDoesNotThrow(()->NativeFixtureBuild.requireCurrentEnvironmentBinding(plan,binding,decoded));
        } finally { if(old==null)System.clearProperty("jna.tmpdir");else System.setProperty("jna.tmpdir",old); }
    }
    private record HolyCase(NativeFixtureBuild.FixtureTarget target,String targetName,String ownSource,boolean runtime) { }
    private static List<HolyCase> holyCases() {
        return List.of(
                new HolyCase(NativeFixtureBuild.FixtureTarget.HOLY_ORDER_WAR_ELIGIBILITY,
                        "xar_ck3_12003_holy_order_war_eligibility_test","src/ck3_12003_holy_order_war_eligibility_test.cpp",false),
                new HolyCase(NativeFixtureBuild.FixtureTarget.HOLY_ORDER_SERVICE_LIFECYCLE,
                        "xar_ck3_12003_holy_order_service_lifecycle_test","src/ck3_12003_holy_order_service_lifecycle_test.cpp",false),
                new HolyCase(NativeFixtureBuild.FixtureTarget.HOLY_ORDER_TROOP_ASSOCIATION,
                        "xar_ck3_12003_holy_order_troop_association_test","src/ck3_12003_holy_order_troop_association_test.cpp",false),
                new HolyCase(NativeFixtureBuild.FixtureTarget.HOLY_ORDER_HIRE_COST_CONTEXT,
                        "xar_ck3_12003_holy_order_hire_cost_context_test","src/ck3_12003_holy_order_hire_cost_context_test.cpp",true),
                new HolyCase(NativeFixtureBuild.FixtureTarget.HOLY_ORDER_CURRENT_REINFORCEMENT,
                        "xar_ck3_12003_holy_order_current_reinforcement_test","src/ck3_12003_holy_order_current_reinforcement_test.cpp",true));
    }
    @Test void holyV2PlanRoundTripRejectsCommanderV1AndCombatAuthority() throws Exception {
        for(var item:holyCases()) {
            var expected=plan(NativeFixtureBuild.CURRENT_HOLY_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build"),item.target());
            Path file=root.resolve(item.target().name()+".json");
            Files.write(file,RootNativePlanJson.mapper().writeValueAsBytes(expected));
            assertEquals(expected,NativeFixtureBuild.readCurrentPlan(ControlBuild.FileRef.measure(file)));
            assertEquals(item.targetName(),expected.target().targetName());
            assertEquals(item.runtime(),expected.target().usesRuntime());
            assertEquals(NativeFixtureBuild.ActualStage.HOLY_FIXTURE_TARGET_BUILD,expected.target().buildStage());
            assertEquals("holy-fixture-target-build",expected.target().buildStage().wireId());
            assertThrows(IllegalArgumentException.class,()->plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build"),item.target()));
            assertThrows(IllegalArgumentException.class,()->plan(NativeFixtureBuild.CURRENT_HOLY_PLAN_SCHEMA,"/root/native_fixture09",root.resolve("build"),item.target()));
            assertDoesNotThrow(()->NativeFixtureBuild.requireCurrentStage(expected,NativeFixtureBuild.Stage.BUILD));
            assertDoesNotThrow(()->NativeFixtureBuild.requireCurrentStage(expected,NativeFixtureBuild.Stage.REGISTER));
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentStage(expected,NativeFixtureBuild.Stage.COMBAT));
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentStage(expected,NativeFixtureBuild.Stage.KINSHIP));
        }
        assertThrows(IllegalArgumentException.class,()->plan(NativeFixtureBuild.CURRENT_HOLY_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build")));
        var commander=plan(NativeFixtureBuild.CURRENT_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build"));
        assertEquals("xar.current-native-fixture-build-plan/v1",commander.schema());
        assertEquals(NativeFixtureBuild.ActualStage.COMBATROLES_TARGET_BUILD,commander.target().buildStage());
        assertDoesNotThrow(()->NativeFixtureBuild.requireCurrentStage(commander,NativeFixtureBuild.Stage.COMBAT));
    }
    private ControlBuild.FileRef actualFile(Path path) throws Exception {
        Files.createDirectories(path.getParent());Files.writeString(path,"unit metadata source "+path.getFileName());
        return ControlBuild.FileRef.measure(path);
    }
    private NativeFixtureBuild.Target graphTarget(String name,String id,NativeFixtureBuild.TargetType type,
            List<ControlBuild.FileRef> sources,List<String> dependencies,List<String> definitions) throws Exception {
        var group=new NativeFixtureBuild.CompileGroup("CXX","20",List.of(),definitions,List.of());
        return new NativeFixtureBuild.Target(name,id,type,actualFile(root.resolve("build/"+id+".json")),sources,
                List.of(root.resolve("build/"+name+(type==NativeFixtureBuild.TargetType.EXECUTABLE?".exe":".lib")).toString()),
                dependencies,List.of(group),null,null);
    }
    private NativeFixtureBuild.Graph graph(String schema,List<NativeFixtureBuild.Target> targets,
            ControlBuild.FileRef runtimeSources,int runtimeCount) {
        return new NativeFixtureBuild.Graph(schema,"xenoamess-full-tower-eb9d2c1186","2026-10-27T00:00:00Z",
                NativeFixtureBuild.GraphStatus.CONFIGURED_SOURCE_FROZEN_NOT_BUILT,pin(root.resolve("configure.actual.json")),
                targets,List.of(),List.of(),List.of(),runtimeSources,runtimeCount,List.of("unit-only configured shape; no Native terminal"));
    }
    @Test void actualFileGraphRoundTripUsesProductionClosureMatcherForAllFiveTargets() throws Exception {
        // Finite real files and original graph serialization; these synthetic graphs confer no Source/ENV/BUILD qualification.
        String runtimeName="xar_ck3_12002_runtime";
        var runtimeSource=actualFile(root.resolve("compile/src/unit_runtime.cpp"));
        var runtime=graphTarget(runtimeName,"runtime-id",NativeFixtureBuild.TargetType.STATIC_LIBRARY,List.of(runtimeSource),List.of(),List.of("NOMINMAX"));
        var runtimeList=actualFile(root.resolve("build/ck3_12002_runtime_sources.txt"));
        for(var item:holyCases()) {
            var plan=plan(NativeFixtureBuild.CURRENT_HOLY_PLAN_SCHEMA,"/root/native_fixtures63",root.resolve("build"),item.target());
            var sources=new java.util.ArrayList<ControlBuild.FileRef>();sources.add(actualFile(plan.compileSourceRoot().resolve(item.ownSource())));
            if(!item.runtime())for(String relative:List.of("src/ck3_12003_player_holy_order_context.cpp",
                    "src/ck3_12003_holy_order_current_reinforcement.cpp","src/ck3_12003_player_holy_order_wire.cpp"))
                sources.add(actualFile(plan.compileSourceRoot().resolve(relative)));
            List<String> definitions=!item.runtime()?List.of("NOMINMAX","XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1")
                    : item.target()==NativeFixtureBuild.FixtureTarget.HOLY_ORDER_HIRE_COST_CONTEXT?List.of("NOMINMAX","NDEBUG"):List.of("NOMINMAX");
            var selected=graphTarget(item.targetName(),"selected-id",NativeFixtureBuild.TargetType.EXECUTABLE,sources,
                    item.runtime()?List.of(runtime.id()):List.of(),definitions);
            var targets=item.runtime()?List.of(selected,runtime):List.of(selected);
            var expected=graph("xar.native-configured-selected-graph/v3",targets,item.runtime()?runtimeList:null,item.runtime()?1:0);
            Path file=root.resolve(item.target().name()+"-graph.json");var json=ControlBuild.strictMapper();
            Files.write(file,json.writeValueAsBytes(expected));
            var decoded=json.readValue(Files.readAllBytes(file),NativeFixtureBuild.Graph.class);
            assertEquals(expected,decoded);
            assertDoesNotThrow(()->NativeFixtureBuild.requireCurrentGraphShape(plan,decoded));
            assertEquals(item.runtime()?1:4,selected.translationUnits().size());
            assertEquals(root.resolve("build/"+item.targetName()+".exe"),NativeFixtureBuild.currentPrimaryArtifact(plan.buildRoot(),selected));
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,
                    graph("xar.native-configured-selected-graph/v2",targets,item.runtime()?runtimeList:null,item.runtime()?1:0)));
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,
                    graph(expected.schema(),targets,item.runtime()?null:runtimeList,item.runtime()?0:1)));
            var other=graphTarget("xar_ck3_12003_holy_order_foreign_test","other-id",NativeFixtureBuild.TargetType.EXECUTABLE,sources,List.of(),definitions);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,graph(expected.schema(),List.of(other),null,0)));
            var wrongSources=new java.util.ArrayList<>(sources);wrongSources.set(0,runtimeSource);
            var wrongSource=graphTarget(item.targetName(),"selected-id",NativeFixtureBuild.TargetType.EXECUTABLE,wrongSources,selected.dependencyIds(),definitions);
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,
                    graph(expected.schema(),item.runtime()?List.of(wrongSource,runtime):List.of(wrongSource),item.runtime()?runtimeList:null,item.runtime()?1:0)));
            var wrongDefinitions=graphTarget(item.targetName(),"selected-id",NativeFixtureBuild.TargetType.EXECUTABLE,sources,selected.dependencyIds(),List.of());
            assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,
                    graph(expected.schema(),item.runtime()?List.of(wrongDefinitions,runtime):List.of(wrongDefinitions),item.runtime()?runtimeList:null,item.runtime()?1:0)));
            if(item.runtime()) {
                var extraDependency=graphTarget(runtimeName,"runtime-id",NativeFixtureBuild.TargetType.STATIC_LIBRARY,List.of(runtimeSource),List.of("foreign-id"),List.of("NOMINMAX"));
                assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,graph(expected.schema(),List.of(selected,extraDependency),runtimeList,1)));
                assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,graph(expected.schema(),List.of(selected,runtime),runtimeList,2)));
            } else assertThrows(IOException.class,()->NativeFixtureBuild.requireCurrentGraphShape(plan,graph(expected.schema(),List.of(selected,runtime),runtimeList,1)));
        }
    }
    @Test void versionedStageSidecarsCannotMixCommanderAndHolyBuildRoles() throws Exception {
        for(String schema:List.of("xar.current-fixture-source-terminal/v1","xar.current-fixture-source-terminal/v2")) {
            String stage=schema.endsWith("/v1")?"combatroles-target-build":"holy-fixture-target-build";
            var terminal=new NativeFixtureBuild.CurrentSourceTerminal(schema,stage,null,List.of(),List.of(),null);
            byte[] raw=RootNativePlanJson.mapper().writeValueAsBytes(terminal);
            assertEquals(terminal,RootNativePlanJson.mapper().readValue(raw,NativeFixtureBuild.CurrentSourceTerminal.class));
            assertThrows(IllegalArgumentException.class,()->new NativeFixtureBuild.CurrentSourceTerminal(schema,
                    schema.endsWith("/v1")?"holy-fixture-target-build":"combatroles-target-build",null,List.of(),List.of(),null));
        }
        assertThrows(IllegalArgumentException.class,()->new NativeFixtureBuild.CurrentStageRetention(
                "xar.current-fixture-retained-stage-files/v1","xenoamess-full-tower-eb9d2c1186",pin(root.resolve("p")),"holy-fixture-target-build",List.of()));
        assertThrows(IllegalArgumentException.class,()->new NativeFixtureBuild.CurrentStageRetention(
                "xar.current-fixture-retained-stage-files/v2","xenoamess-full-tower-eb9d2c1186",pin(root.resolve("p")),"combatroles-target-build",List.of()));
    }
    @Test void terminalVersionAndScope() {
        assertThrows(IllegalArgumentException.class,()->new NativeFixtureBuild.CurrentSourceTerminal(
                "xar.current-fixture-source-terminal/v1","combatroles-producer",null,List.of(),List.of(),null));
        assertThrows(IllegalArgumentException.class,()->new NativeFixtureBuild.CurrentSourceTerminal(
                "xar.shared-native-stage-actual/v2","configure-next01",null,List.of(),List.of(),null));
    }
}
