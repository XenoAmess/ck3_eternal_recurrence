package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;

/** Explicit persistent actual-MSVC CI phase. Missing exact installed inputs or no forced case is NOT_EXECUTED/RED, never skipped. */
final class MsvcAuxiliaryActualRegression {
    private record ActualTrace(String schema,String machineId,String phase,ControlBuild.FileRef originalSpec,
            MsvcAuxiliaryPolicy.ExecutionBinding binding,WindowsJobProcess.AuxiliaryAwaitResult actualResult,
            String failureType,String failureMessage) { }
    private static String required(String property) throws IOException {
        String value=System.getProperty(property);
        if(value==null || value.isBlank())throw new IOException("NOT_EXECUTED exact actual-MSVC regression input required: "+property);
        return value;
    }
    @Test void actualClRootZeroOwnedVctipIsCleanedBySharedFiniteBackendAndNotCalledNaturalExit() throws Exception {
        var mapper=ControlBuild.strictMapper();
        Path temporary=Path.of(required("xar.msvcAuxiliary.evidenceRoot"));
        if(!temporary.isAbsolute())throw new IOException("Absolute persistent actual evidence root required");
        temporary=temporary.toAbsolutePath().normalize();SharedSourceFiles.plainAncestors(temporary.getParent());
        if(!Files.isDirectory(temporary.getParent(),LinkOption.NOFOLLOW_LINKS))throw new IOException("Owned run output parent must already exist");
        Files.createDirectory(temporary);
        String machine=WindowsJobProcess.currentMachineId(),phase="VERIFY_ORIGINAL";
        ControlBuild.FileRef originalSpec=null;MsvcAuxiliaryPolicy.ExecutionBinding binding=null;
        WindowsJobProcess.AuxiliaryAwaitResult result=null;Throwable failure=null;
        try {
        originalSpec=new ControlBuild.FileRef(required("xar.msvcAuxiliary.originalSpec"),
                Long.parseLong(required("xar.msvcAuxiliary.originalSpecBytes")),required("xar.msvcAuxiliary.originalSpecSha256"));
        originalSpec.verify();JsonNode spec=mapper.readTree(Files.readAllBytes(Path.of(originalSpec.path())));originalSpec.verify();
        var original=SharedOwnedCommand.parseRequest(spec);
        assertEquals(machine,original.machineId(),"Original failed producer must belong to this actual machine");
        original.executable().verify();
        Path compiler=Path.of(original.executable().path());Instant now=Instant.now();
        Instant leaseDeadline=Instant.parse(required("xar.msvcAuxiliary.leaseDeadline"));
        if(!now.isBefore(leaseDeadline))throw new IOException("Original actual lease expired before binding");
        Instant deadline=now.plusSeconds(20);if(leaseDeadline.isBefore(deadline))deadline=leaseDeadline;
        phase="BIND_EXACT_ROOT_AND_AUXILIARIES";
        var tools=MsvcAuxiliaryPolicy.bind(compiler,deadline,()->{});tools.requireCompiler(original.executable());
        binding=new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1",tools,original.executable());
        Path source=temporary.resolve("actual-cl-auxiliary-fixture.c"),object=temporary.resolve("actual-cl-auxiliary-fixture.obj");
        Files.writeString(source,"int ck3_auxiliary_regression(void) { return 74; }\n");
        Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());environment.putAll(original.environment());
        environment.put("TEMP",temporary.toString());environment.put("TMP",temporary.toString());
        var command=new WindowsJobProcess.CommandSpec(compiler,List.of("/nologo","/c","/Od","/Fo"+object,source.toString()),
                temporary.toAbsolutePath(),environment,temporary.resolve("actual-cl.stdout"),temporary.resolve("actual-cl.stderr"),256L<<20);
        phase="CREATE_AND_AWAIT_ORIGINAL_OWNED_COMPILER";
        try(var images=MsvcAuxiliaryPolicy.retain(binding,deadline,()->{});var owner=WindowsJobProcess.start(command)) {
            result=owner.awaitWithMsvcAuxiliaries(Duration.ofSeconds(15),deadline,()->{},temporary.resolve("before-cleanup.json"),images);
            Files.write(temporary.resolve("actual-msvc-auxiliary.json"),mapper.writeValueAsBytes(result));
            phase="VERIFY_ACTUAL_FORCED_CLEANUP";
            assertEquals(0,result.original().commandResult().exitCode());
            assertEquals(0,result.original().commandResult().accounting().activeProcesses());
            assertNull(result.original().commandResult().stopReason());assertTrue(result.passed());
            assertEquals(MsvcAuxiliaryPolicy.State.FORCED_AUXILIARY_CLEANUP,result.auxiliaryCleanup().state(),
                    "NOT_EXECUTED actual live auxiliary failure shape was not reproduced on this compiler/environment; natural drain cannot qualify forced cleanup");
            assertFalse(result.auxiliaryCleanup().failureJobTerminationRequested());
            assertFalse(result.auxiliaryCleanup().forcedCleanup().isEmpty());
            for(var member:result.auxiliaryCleanup().forcedCleanup()) {
                assertEquals(0L,member.actualWaitZero().longValue());assertEquals(74L,member.actualExitCode().longValue());
            }
        }
        assertTrue(Files.size(object)>0);assertEquals(result,mapper.readValue(mapper.writeValueAsBytes(result),WindowsJobProcess.AuxiliaryAwaitResult.class));
        phase="VERIFIED_ACTUAL_FORCED_CLEANUP";
        }catch(Exception|AssertionError error){failure=error;throw error;}
        finally {
            var trace=new ActualTrace("xar.actual-msvc-auxiliary-persistent-trace/v1",machine,phase,originalSpec,binding,result,
                    failure==null?null:failure.getClass().getName(),failure==null?null:failure.getMessage());
            try{Files.write(temporary.resolve("actual-regression-trace.json"),mapper.writeValueAsBytes(trace));}
            catch(IOException traceFailure){if(failure!=null)failure.addSuppressed(traceFailure);else throw traceFailure;}
        }
    }
}
