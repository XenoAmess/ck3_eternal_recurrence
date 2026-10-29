package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Real public-entry preparation/OS-lock regression on owned temporary files. No native child or accepted build is fabricated. */
@org.junit.jupiter.api.parallel.Isolated("temporarily binds exact private JVM temporary properties")
final class NativeBridgeRootPreparationTest {
    @TempDir Path temporary;

    @Test void actualExecuteRootPreparesFreshScratchBeforeRejectingUnqualifiedTools()throws Exception {
        try(var fixture=fixture()){
            assertFalse(Files.exists(fixture.request.scratchRoot()));
            IOException failure=assertThrows(IOException.class,()->NativeBridgeBuild.executeRoot(fixture.requestRef,fixture.limits));
            assertFalse(failure.getMessage()!=null&&failure.getMessage().contains("Plain canonical directory required"));
            assertTrue(Files.isDirectory(fixture.request.scratchRoot()));
            assertTrue(Files.isRegularFile(fixture.request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
            assertFalse(Files.exists(fixture.request.stageRoot()));
            assertFalse(Files.exists(fixture.request.buildRoot()));
            fixture.requestRef.verify();
        }
    }

    @Test void actualOpenUsesTheSameFreshPreparationAndRetainsTheExistingRootLock()throws Exception {
        try(var fixture=fixture()){
            try(var gate=NativeBridgeRootGate.open(fixture.requestRef,fixture.limits)){
                var grant=gate.acquire(fixture.request,fixture.requestRef);
                assertEquals(fixture.requestRef,grant.requestRef());
                gate.revalidate(grant,fixture.request.buildRoot(),fixture.request.scratchRoot());
                assertTrue(Files.isDirectory(fixture.request.scratchRoot()));
                assertThrows(IOException.class,()->NativeBridgeRootGate.open(fixture.requestRef,fixture.limits));
            }
            try(var gate=NativeBridgeRootGate.open(fixture.requestRef,fixture.limits)){
                var grant=gate.acquire(fixture.request,fixture.requestRef);
                assertEquals(fixture.requestRef,grant.requestRef());
                gate.revalidate(grant,fixture.request.buildRoot(),fixture.request.scratchRoot());
                assertFalse(Files.exists(fixture.request.stageRoot()));
            }
        }
    }

    @Test void malformedFinancialEnvelopeStillRefusesBeforeAnyDirectoryOrLockWrite()throws Exception {
        try(var fixture=fixture()){
            var wrong=new NativeBridgeRootGate.Limits("/root",write(temporary.resolve("bad-capacity.json"),"{}"),
                    fixture.limits.deadline(),fixture.limits.memoryLimitBytes(),fixture.limits.outputAllocationLimitBytes(),20);
            assertThrows(IOException.class,()->NativeBridgeBuild.executeRoot(fixture.requestRef,wrong));
            assertFalse(Files.exists(fixture.request.scratchRoot()));
        }
    }

    @Test void unknownExistingStageIsNeverReplayedOrGivenAnotherLock()throws Exception {
        try(var fixture=fixture()){
            Files.createDirectory(fixture.request.scratchRoot());Files.createDirectory(fixture.request.stageRoot());
            var original=write(fixture.request.stageRoot().resolve("INTENT.json"),"unresolved original fixture");
            assertThrows(IOException.class,()->NativeBridgeBuild.executeRoot(fixture.requestRef,fixture.limits));
            original.verify();assertFalse(Files.exists(fixture.request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
        }
    }

    @Test void scratchFileOrMissingParentIsNotRepairedByRecursiveMkdir()throws Exception {
        try(var fixture=fixture()){
            var original=write(fixture.request.scratchRoot(),"regular file cannot become native control directory");
            assertThrows(IOException.class,()->NativeBridgeRootGate.open(fixture.requestRef,fixture.limits));
            original.verify();Files.delete(fixture.request.scratchRoot());
            var old=fixture.request;Path absent=old.scratchRoot().resolve("not-created");
            var changed=new NativeBridgeBuild.Request(old.schema(),old.machineId(),old.stage(),old.canonicalRepository(),old.sourceRoot(),
                    old.completeSources(),old.buildRoot(),absent,old.qualifiedToolsBuild(),old.tools(),old.definitions(),old.parallelJobs(),null,null,null);
            var pin=write(temporary.resolve("missing-parent-request.json"),ControlBuild.strictMapper().writeValueAsString(changed));
            assertThrows(IOException.class,()->NativeBridgeRootGate.open(pin,fixture.limits));
            assertFalse(Files.exists(old.scratchRoot()));
        }
    }

    private Fixture fixture()throws Exception {
        Path source=Files.createDirectory(temporary.resolve("source"));write(source.resolve("CMakeLists.txt"),"option(XAR_CK3_FIXTURE \"fixture\" OFF)\n");
        Path scope=Files.createDirectory(temporary.resolve("output")),tmp=Files.createDirectory(scope.resolve("tmp"));
        var tools=new ArrayList<FileRef>();
        for(String name:List.of("cmd.exe","vcvars64.bat","java.exe","cmake.exe","ninja.exe","cl.exe","link.exe"))tools.add(write(temporary.resolve(name),"software-only never executed"));
        var request=new NativeBridgeBuild.Request(NativeBridgeBuild.REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),NativeBridgeBuild.Stage.ENV,
                temporary,source,NativeBridgeBuild.inventory(source),scope.resolve("production-build"),scope.resolve("native-control"),
                write(temporary.resolve("unqualified-tools.json"),"{}"),new NativeBridgeBuild.Toolchain(tools.get(0),tools.get(1),tools.get(2),tools.get(3),tools.get(4),tools.get(5),tools.get(6)),
                List.of(new NativeBridgeBuild.Definition("XAR_CK3_FIXTURE",NativeBridgeBuild.SwitchValue.OFF)),4,null,null,null);
        var requestRef=write(temporary.resolve("request.json"),ControlBuild.strictMapper().writeValueAsString(request));
        var policy=write(temporary.resolve("policy.json"),"""
                {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                "safety_floor_bytes":1,"safety_ceiling_bytes":1,"safety_volume_fraction":0.00000001,
                "default_project_quota_ceiling_bytes":1000000000000,"default_project_quota_volume_fraction":0.99,
                "quota_override_max_hours":168}}
                """);
        Instant start=Instant.now().minusSeconds(1),deadline=Instant.now().plusSeconds(60);
        var store=Files.getFileStore(scope);var volume=CiBootstrap.calculate(CiBootstrap.readPolicy(Files.readAllBytes(Path.of(policy.path()))),
                store.getTotalSpace(),store.getUsableSpace(),64L<<20,0,1,65536,null,start,deadline);
        // This finite software fixture grants no target launch or build qualification. No child can pass its tools receipt.
        var capacity=new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1",request.machineId(),start.toString(),deadline.toString(),"RELEASED","/root",policy,
                List.of(scope.toString()),tmp.toString(),Map.of("artifacts",64L<<20),Map.of(scope.getRoot().toString(),volume),Map.of(),128L<<20,32L<<20);
        var capacityRef=write(temporary.resolve("capacity.json"),ControlBuild.strictMapper().writeValueAsString(capacity));
        return new Fixture(request,requestRef,new NativeBridgeRootGate.Limits("/root",capacityRef,deadline,64L<<20,64L<<20,20),tmp);
    }
    private static final class Fixture implements AutoCloseable {
        private final NativeBridgeBuild.Request request;private final FileRef requestRef;private final NativeBridgeRootGate.Limits limits;
        private final String oldTmp,oldJna;
        private Fixture(NativeBridgeBuild.Request request,FileRef ref,NativeBridgeRootGate.Limits limits,Path tmp){
            this.request=request;requestRef=ref;this.limits=limits;oldTmp=System.getProperty("java.io.tmpdir");oldJna=System.getProperty("jna.tmpdir");
            System.setProperty("java.io.tmpdir",tmp.toString());System.setProperty("jna.tmpdir",tmp.toString());
        }
        @Override public void close(){restore("java.io.tmpdir",oldTmp);restore("jna.tmpdir",oldJna);}
        private static void restore(String key,String value){if(value==null)System.clearProperty(key);else System.setProperty(key,value);}
    }
    private static FileRef write(Path path,String value)throws IOException {
        Files.writeString(path,value,java.nio.file.StandardOpenOption.CREATE_NEW);return FileRef.measure(path);
    }
}
