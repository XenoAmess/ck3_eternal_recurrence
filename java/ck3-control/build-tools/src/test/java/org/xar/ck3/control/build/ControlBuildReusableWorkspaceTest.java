package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** NoGame DATA/physical workspace tests; these do not mint a qualified runtime receipt. */
final class ControlBuildReusableWorkspaceTest {
    @TempDir Path temporary;

    private ControlBuild.Config config() throws IOException {
        Path source=Files.createDirectories(temporary.resolve("dev"));
        Files.writeString(source.resolve("pom.xml"),"<project><modelVersion>4.0.0</modelVersion><groupId>org.xar.ck3.control</groupId><artifactId>ck3-control-build-tools</artifactId><version>0.1.0-SNAPSHOT</version></project>");
        Path java=Files.createDirectories(source.resolve("src/main/java/example"));
        Files.writeString(java.resolve("Example.java"),"package example; final class Example {}\n");
        Path work=Files.createDirectories(temporary.resolve("control"));
        Files.createDirectories(work.resolve("scratch"));
        Path build=Files.createDirectories(temporary.resolve("target"));
        Path m2=Files.createDirectories(temporary.resolve("m2"));
        Path settings=temporary.resolve("settings.xml");Files.writeString(settings,"<settings/>");
        Path release=temporary.resolve("release.json");
        var json=ControlBuild.strictMapper();
        ObjectNode allowed=json.createObjectNode().put("schema","xar.java-phase1.manual-capacity-release/v1");
        allowed.putArray("approved_output_roots").add(temporary.toString());
        Files.write(release,json.writeValueAsBytes(allowed));
        return new ControlBuild.Config(source,work,release,"reusable-test","/NoGame/DATA",null,
                Path.of(System.getProperty("java.home")),"3.10.0",900,ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,
                ControlBuild.SourceLimitProfile.TOOLS_20261116_12_MIB,
                new ControlBuild.ReusableWorkspace(build.toString(),m2.toString(),ControlBuild.FileRef.measure(settings),2));
    }

    @Test void realSourceProducerCodecAndCommandKeepExistingPhysicalWorkspace() throws Exception {
        var config=config();var json=ControlBuild.strictMapper();
        var produced=json.writeValueAsBytes(config);
        var consumed=json.readValue(produced,ControlBuild.Config.class);
        assertEquals(config,consumed);
        Path build=Path.of(consumed.reusableWorkspace().buildRoot());
        Path retained=build.resolve("retained.obj");Files.writeString(retained,"existing cached bytes");
        var before=ControlBuild.sourceManifest(consumed.sourceRoot(),consumed.sourceLimitProfile());
        var stamp=Files.getLastModifiedTime(retained);
        for(int attempt=0;attempt<2;attempt++) {
            try(var locks=ControlBuild.lockReusable(consumed)) {
                locks.requireHeld();
                var argv=ControlBuild.reactorVerifyArguments(consumed,Path.of(consumed.reusableWorkspace().settingsRef().path()),
                        consumed.sourceRoot(),build,Map.of("XAR_ORACLE_PYTHON",temporary.resolve("NoGame-python-input.exe").toString()));
                assertTrue(argv.contains("-T2"));assertTrue(argv.contains("verify"));assertFalse(argv.contains("-U"));
                assertTrue(argv.contains("-Dmaven.repo.local="+consumed.reusableWorkspace().mavenRepository()));
                assertTrue(argv.contains("-Dck3.build.root="+build));
                assertTrue(argv.contains("-Dck3.tools.bootstrap.directory="+ControlBuild.reusableDeployment(consumed)));
                assertEquals(before,ControlBuild.sourceManifest(consumed.sourceRoot(),consumed.sourceLimitProfile()));
            }
        }
        assertEquals("existing cached bytes",Files.readString(retained));assertEquals(stamp,Files.getLastModifiedTime(retained));
        assertFalse(Files.exists(consumed.workRoot().resolve("scratch/source-reusable-test")));
    }

    @Test void realWriterLocksRejectConcurrentReuseAndReleaseWithoutRebuilding() throws Exception {
        var config=config();
        try(var first=ControlBuild.lockReusable(config)) {
            first.requireHeld();
            assertThrows(OverlappingFileLockException.class,()->ControlBuild.lockReusable(config));
        }
        try(var next=ControlBuild.lockReusable(config)){next.requireHeld();}
    }

    @Test void physicalSourceMutationAndSettingsDriftAreNotAcceptedAsCachedQualification() throws Exception {
        var config=config();var before=ControlBuild.sourceManifest(config.sourceRoot(),config.sourceLimitProfile());
        try(var locks=ControlBuild.lockReusable(config)) {
            locks.requireHeld();Files.writeString(config.sourceRoot().resolve("src/main/java/example/Example.java"),"package example; final class Changed {}\n");
            assertEquals(ControlBuild.SourceState.MISMATCH,ControlBuild.postcheckSource(config.sourceRoot(),before,config.sourceLimitProfile()).state());
        }
        Files.writeString(Path.of(config.reusableWorkspace().settingsRef().path()),"<changed/>");
        assertThrows(IOException.class,()->ControlBuild.lockReusable(config));
    }

    @Test void typedWorkspaceRejectsMissingNullWrongNumericOrUnknownFields() throws Exception {
        var config=config();var json=ControlBuild.strictMapper();
        for(String fault:List.of("missing","null","bool","float","zero","three","extra")) {
            ObjectNode node=json.valueToTree(config);ObjectNode workspace=(ObjectNode)node.get("reusable_workspace");
            switch(fault) {
                case "missing"->workspace.remove("parallelism");case "null"->workspace.putNull("parallelism");
                case "bool"->workspace.put("parallelism",true);case "float"->workspace.put("parallelism",1.5);
                case "zero"->workspace.put("parallelism",0);case "three"->workspace.put("parallelism",3);
                case "extra"->workspace.put("skip_tests",true);default->throw new AssertionError(fault);
            }
            assertThrows(IOException.class,()->json.treeToValue(node,ControlBuild.Config.class),fault);
        }
        ObjectNode historical=json.valueToTree(config);historical.remove("reusable_workspace");
        assertNull(json.treeToValue(historical,ControlBuild.Config.class).reusableWorkspace());
    }

    @Test void explicitCliRequiresAllReusableOptionsAndKeepsDefaultMaven() throws Exception {
        var config=config();
        List<String> args=new ArrayList<>(List.of("--source-root",config.sourceRoot().toString(),"--work-root",config.workRoot().toString(),
                "--capacity-release",config.capacityRelease().toString(),"--attempt",config.attempt(),"--owner-task",config.ownerTask(),
                "--java-home",config.javaHome().toString(),"--target-kind","BUILD_TOOLS_RUNTIME","--source-limit-profile","TOOLS_20261116_12_MIB"));
        String previous=System.getProperty("jna.tmpdir");
        try {
            System.setProperty("jna.tmpdir",config.workRoot().resolve("scratch").toString());
            List<String> partial=new ArrayList<>(args);partial.addAll(List.of("--reuse-build-root",config.reusableWorkspace().buildRoot()));
            assertThrows(IOException.class,()->ControlBuild.parseArguments(partial.toArray(String[]::new)));
            args.addAll(List.of("--reuse-build-root",config.reusableWorkspace().buildRoot(),"--reuse-maven-repository",config.reusableWorkspace().mavenRepository(),
                    "--reuse-settings",config.reusableWorkspace().settingsRef().path(),"--reuse-parallelism","2"));
            var actual=ControlBuild.parseArguments(args.toArray(String[]::new));
            assertEquals(config.reusableWorkspace(),actual.reusableWorkspace());assertNull(actual.mavenCommand());
        } finally {if(previous==null)System.clearProperty("jna.tmpdir");else System.setProperty("jna.tmpdir",previous);}
    }

    @Test void originalManualProducerUsesTheExplicitReusableRootsAndInvocationCodecKeepsPins() throws Exception {
        var config=config();var now=Instant.now();var ref=config.reusableWorkspace().settingsRef();
        var request=new ManualBuildCapacityReleaseProducer.Request(config,"software-data-machine",now,now.plusSeconds(60),
                new ManualBuildCapacityReleaseProducer.IssuerDomain("DATA-owner","DATA-issuer",ref,"SYNTHETIC NoGame authorization DATA","codec only"),
                ref,List.of(temporary),new ManualBuildCapacityReleaseProducer.Parts(1,1,1,1,1,1),
                List.of(new ManualBuildCapacityReleaseProducer.Volume(temporary.getRoot(),1000,900,100,10,0,1,1,1000)),
                new ManualBuildCapacityReleaseProducer.Memory(1000,100));
        var json=ControlBuild.strictMapper();
        var original=json.readTree(ManualBuildCapacityReleaseProducer.encode(request));
        assertEquals(config.reusableWorkspace().mavenRepository(),original.path("Maven_repository").textValue());
        assertEquals(config.reusableWorkspace().buildRoot(),original.path("build_root").textValue());
        var invocation=new ControlBuild.ReusableInvocation("xar.java-control-reusable-invocation/v1",config,List.of(),null,null,null,null,List.of(),List.of(),null);
        assertEquals(invocation,json.readValue(json.writeValueAsBytes(invocation),ControlBuild.ReusableInvocation.class));
    }

    @Test void staleCompilerInputStateIsArchivedWhileClassesAndOtherCachesRemain() throws Exception {
        Path module=Files.createDirectories(temporary.resolve("selected-module"));
        Path classes=Files.createDirectories(module.resolve("classes"));
        Path originalClass=classes.resolve("Same.class");Files.writeString(originalClass,"previous compiled bytes");
        var classPin=ControlBuild.FileRef.measure(originalClass);var classTime=Files.getLastModifiedTime(originalClass);
        Path other=Files.createDirectories(temporary.resolve("other-module"));Files.writeString(other.resolve("retained.obj"),"untouched");
        for(String phase:List.of("compile","testCompile")) {
            Path file=module.resolve("maven-status/maven-compiler-plugin/"+phase+"/default-"+phase+"/inputFiles.lst");
            Files.createDirectories(file.getParent());Files.writeString(file,"original "+phase+" inputs");
        }
        Path archive=Files.createDirectory(temporary.resolve("archive"));
        var originals=ControlBuild.invalidateCompilerInputs(module,archive,"actual-data");
        assertEquals(2,originals.size());for(var ref:originals)ref.verify();
        assertEquals("original compile inputs",Files.readString(archive.resolve("actual-data-previous-compile-inputFiles.lst")));
        assertFalse(Files.exists(module.resolve("maven-status/maven-compiler-plugin/compile/default-compile/inputFiles.lst")));
        classPin.verify();assertEquals(classTime,Files.getLastModifiedTime(originalClass));
        assertEquals("untouched",Files.readString(other.resolve("retained.obj")));
    }

    @Test void cachedSourceMetadataCannotLoseRequiredPinsOrHideUnknownFields() throws Exception {
        var config=config();var json=ControlBuild.strictMapper();
        var state=new ControlBuild.ReusableCacheState("xar.java-control-reusable-cache/v1",config.sourceRoot().toString(),"a".repeat(64),config.reusableWorkspace().settingsRef());
        assertEquals(state,json.readValue(json.writeValueAsBytes(state),ControlBuild.ReusableCacheState.class));
        for(String fault:List.of("missing","null","wrong-digest","extra")) {
            ObjectNode bad=json.valueToTree(state);
            switch(fault) {
                case "missing"->bad.remove("completed_receipt_ref");case "null"->bad.putNull("source_digest");
                case "wrong-digest"->bad.put("source_digest","not-a-digest");case "extra"->bad.put("skip_compile",true);
                default->throw new AssertionError(fault);
            }
            assertThrows(IOException.class,()->json.treeToValue(bad,ControlBuild.ReusableCacheState.class),fault);
        }
    }

    @Test void reusableArgumentPreparationValidatesWithoutWritingSourceOrRelaxingPropertyRules() throws Exception {
        var config=config();Path source=config.sourceRoot();
        var before=ControlBuild.sourceManifest(source,config.sourceLimitProfile());
        MavenArgumentFile.prepareReusable(source,null,List.of("-B","-Dactual=value","verify"));
        assertEquals(before,ControlBuild.sourceManifest(source,config.sourceLimitProfile()));
        assertFalse(Files.exists(source.resolve(MavenArgumentFile.CONFIG)));
        assertThrows(IOException.class,()->MavenArgumentFile.prepareReusable(source,null,List.of("-Dactual=one","-Dactual=two","verify")));
        assertThrows(IOException.class,()->MavenArgumentFile.prepareReusable(source,null,List.of("-Dlarge="+"x".repeat(9000),"verify")));
        Path inherited=source.resolve(MavenArgumentFile.CONFIG);Files.createDirectories(inherited.getParent());Files.writeString(inherited,"-Dactual=original\n");
        var original=ControlBuild.FileRef.measure(inherited);
        assertThrows(IOException.class,()->MavenArgumentFile.prepareReusable(source,null,List.of("-Dactual=replacement","verify")));
        original.verify();Files.writeString(source.resolve(MavenArgumentFile.MANIFEST),"{}");
        assertThrows(IOException.class,()->MavenArgumentFile.prepareReusable(source,null,List.of("verify")));
    }
}
