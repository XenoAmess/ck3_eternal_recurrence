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

/** Normal production memory admission only: real records, storage envelope and OS lock; no child is launched. */
@org.junit.jupiter.api.parallel.Isolated("temporarily binds exact private JVM temporary properties")
final class NativeBridgeMemoryAdmissionTest {
    @TempDir Path temporary;
    private static final long FOUR_GIB = 4L << 30;
    private static final long EIGHT_GIB = 8L << 30;

    @Test void explicitEightGiBTraversesNormalRootGateAndExactGrantRoundTrip() throws Exception {
        try (var fixture=fixture(EIGHT_GIB,EIGHT_GIB,false);
                var gate=NativeBridgeRootGate.open(fixture.requestRef,fixture.limits)) {
            var grant=gate.acquire(fixture.request,fixture.requestRef);
            assertEquals(EIGHT_GIB,grant.memoryLimitBytes());
            assertEquals(fixture.limits.memoryLimitBytes(),grant.memoryLimitBytes());
            gate.revalidate(grant,fixture.request.buildRoot(),fixture.request.scratchRoot());
            var mapper=RootNativePlanJson.mapper();
            assertEquals(grant,mapper.readValue(mapper.writeValueAsBytes(grant),NativeBridgeBuild.Grant.class));
            assertEquals(fixture.limits,mapper.readValue(mapper.writeValueAsBytes(fixture.limits),NativeBridgeRootGate.Limits.class));
            assertFalse(Files.exists(fixture.request.stageRoot()));
            assertFalse(Files.exists(fixture.request.buildRoot()));
        }
    }

    @Test void explicitEightGiBGrantConstructsAndRoundTripsTheExistingRecordDirectly() throws Exception {
        var pin=write(temporary.resolve("grant-pin.json"),"{}");
        var grant=new NativeBridgeBuild.Grant("software-only","/root",NativeBridgeBuild.Stage.BUILD,
                pin,pin,Instant.now().plusSeconds(120),EIGHT_GIB,64L<<20,20);
        var mapper=RootNativePlanJson.mapper();
        assertEquals(EIGHT_GIB,grant.memoryLimitBytes());
        assertEquals(grant,mapper.readValue(mapper.writeValueAsBytes(grant),NativeBridgeBuild.Grant.class));
    }

    @Test void existingFourGiBReleaseAndGrantRemainExactWithoutImplicitUpgrade() throws Exception {
        try (var fixture=fixture(FOUR_GIB,FOUR_GIB,false);
                var gate=NativeBridgeRootGate.open(fixture.requestRef,fixture.limits)) {
            var grant=gate.acquire(fixture.request,fixture.requestRef);
            assertEquals(FOUR_GIB,grant.memoryLimitBytes());
            gate.revalidate(grant,fixture.request.buildRoot(),fixture.request.scratchRoot());
            var mapper=RootNativePlanJson.mapper();
            byte[] wire=mapper.writeValueAsBytes(grant);
            assertArrayEquals(wire,mapper.writeValueAsBytes(mapper.readValue(wire,NativeBridgeBuild.Grant.class)));
        }
    }

    @Test void explicitEightGiBCannotConsumeAnOldFourGiBCapacityRelease() throws Exception {
        try (var fixture=fixture(EIGHT_GIB,FOUR_GIB,false)) {
            assertThrows(IOException.class,()->NativeBridgeRootGate.open(fixture.requestRef,fixture.limits));
            assertFalse(Files.exists(fixture.request.scratchRoot()));
        }
    }

    @Test void aboveEightGiBIsRejectedByBothNormalTypedEntryPoints() throws Exception {
        var pin=write(temporary.resolve("pin.json"),"{}");
        Instant deadline=Instant.now().plusSeconds(120);
        assertThrows(IllegalArgumentException.class,()->new NativeBridgeRootGate.Limits("/root",pin,deadline,EIGHT_GIB+1,64L<<20,20));
        assertThrows(IllegalArgumentException.class,()->new NativeBridgeBuild.Grant("software-only","/root",NativeBridgeBuild.Stage.ENV,pin,pin,deadline,EIGHT_GIB+1,64L<<20,20));
    }

    @Test void missingOrMalformedCapacityStillRefusesBeforeOutputPreparation() throws Exception {
        try (var fixture=fixture(EIGHT_GIB,EIGHT_GIB,false)) {
            var missing=new FileRef(temporary.resolve("absent-capacity.json").toString(),0,"0".repeat(64));
            var noCapacity=new NativeBridgeRootGate.Limits("/root",missing,fixture.limits.deadline(),EIGHT_GIB,64L<<20,20);
            assertThrows(IOException.class,()->NativeBridgeRootGate.open(fixture.requestRef,noCapacity));
            var malformed=new NativeBridgeRootGate.Limits("/root",write(temporary.resolve("malformed-capacity.json"),"{}"),fixture.limits.deadline(),EIGHT_GIB,64L<<20,20);
            assertThrows(IOException.class,()->NativeBridgeRootGate.open(fixture.requestRef,malformed));
            assertFalse(Files.exists(fixture.request.scratchRoot()));
        }
    }

    @Test void expiredEightGiBCapacityDoesNotRenewOrPrepareOutput() throws Exception {
        try (var fixture=fixture(EIGHT_GIB,EIGHT_GIB,true)) {
            assertThrows(IOException.class,()->NativeBridgeRootGate.open(fixture.requestRef,fixture.limits));
            assertFalse(Files.exists(fixture.request.scratchRoot()));
        }
    }

    @Test void memoryWireRejectsMissingBooleanFractionalAndStringValues() throws Exception {
        try (var fixture=fixture(EIGHT_GIB,EIGHT_GIB,false)) {
            var mapper=RootNativePlanJson.mapper();
            var grant=new NativeBridgeBuild.Grant(fixture.request.machineId(),"/root",NativeBridgeBuild.Stage.ENV,
                    fixture.requestRef,fixture.limits.capacityEvidence(),fixture.limits.deadline(),EIGHT_GIB,64L<<20,20);
            for (String invalid:List.of("true","8589934592.0","\"8589934592\"","null")) {
                var grantTree=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(grant);
                grantTree.set("memory_limit_bytes",mapper.readTree(invalid));
                assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(grantTree),NativeBridgeBuild.Grant.class));
                var limitTree=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(fixture.limits);
                limitTree.set("memory_limit_bytes",mapper.readTree(invalid));
                assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(limitTree),NativeBridgeRootGate.Limits.class));
            }
            var missing=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(grant);
            missing.remove("memory_limit_bytes");
            assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(missing),NativeBridgeBuild.Grant.class));
        }
    }

    private Fixture fixture(long requestedMemory, long capacityMemory, boolean expired)throws Exception {
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
        Instant start=Instant.now().minusSeconds(120),deadline=Instant.now().plusSeconds(expired ? -1 : 120);
        var store=Files.getFileStore(scope);var volume=CiBootstrap.calculate(CiBootstrap.readPolicy(Files.readAllBytes(Path.of(policy.path()))),
                store.getTotalSpace(),store.getUsableSpace(),64L<<20,0,1,65536,null,start,deadline);
        // This finite software fixture grants no target launch or build qualification. No child can pass its tools receipt.
        var capacity=new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1",request.machineId(),start.toString(),deadline.toString(),"RELEASED","/root",policy,
                List.of(scope.toString()),tmp.toString(),Map.of("artifacts",64L<<20),Map.of(scope.getRoot().toString(),volume),Map.of(),capacityMemory,32L<<20);
        var capacityRef=write(temporary.resolve("capacity.json"),ControlBuild.strictMapper().writeValueAsString(capacity));
        return new Fixture(request,requestRef,new NativeBridgeRootGate.Limits("/root",capacityRef,deadline,requestedMemory,64L<<20,20),tmp);
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
