package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Executes the failed-launch cleanup consumer with an ordinary owned Java child, never CK3. */
final class LifecycleFailureCleanupTest {
    @TempDir Path temporary;
    @Test void cleanupConsumesOriginalRootExitAndJobZeroWithoutGrantingLaunchSuccess()throws Exception{
        String cp=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        List<String> argv=List.of("-Xms8m","-Xmx16m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=32m","-XX:ReservedCodeCacheSize=16m","-Xss256k",
                "-Djava.io.tmpdir="+System.getProperty("java.io.tmpdir"),"-Djna.tmpdir="+System.getProperty("jna.tmpdir",System.getProperty("java.io.tmpdir")),
                "-cp",cp,LifecycleSoftwarePeer.class.getName(),"wait");
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());env.remove("JAVA_TOOL_OPTIONS");
        var spec=new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),argv,temporary,env,
                temporary.resolve("stdout.raw"),temporary.resolve("stderr.raw"),128L<<20);
        try(var process=WindowsJobProcess.start(spec)){
            assertTrue(process.isRunning());var identity=process.identity();
            var actual=JavaGameLifecycle.consumeUnknownCleanup(process,Instant.now().plusSeconds(5));
            assertEquals(identity,actual.identity());assertEquals(125,actual.exitCode());
            assertEquals(0,actual.accounting().activeProcesses());assertNull(actual.stopReason());
            assertFalse(process.isRunning());assertFalse(actual.passed());
        }
    }
    @Test void actualJobMemoryRejectionStillProvesCleanupAndRetainsTheFailedTerminal()throws Exception{
        String cp=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        List<String> argv=List.of("-Xms8m","-Xmx16m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=32m","-XX:ReservedCodeCacheSize=16m","-Xss256k",
                "-Djava.io.tmpdir="+System.getProperty("java.io.tmpdir"),"-Djna.tmpdir="+System.getProperty("jna.tmpdir",System.getProperty("java.io.tmpdir")),
                "-cp",cp,LifecycleSoftwarePeer.class.getName(),"job-memory-overflow");
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
        for(String key:List.of("JAVA_TOOL_OPTIONS","_JAVA_OPTIONS","JDK_JAVA_OPTIONS"))env.remove(key);
        Path output=temporary.resolve("memory-stdout.raw");
        var spec=new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),argv,temporary,env,
                output,temporary.resolve("memory-stderr.raw"),64L<<20);
        try(var process=WindowsJobProcess.start(spec)){
            var identity=process.identity();
            var actual=process.await(Duration.ofSeconds(12),Instant.now().plusSeconds(15),()->{
                try{
                    if(Files.exists(output)&&Files.readString(output).contains("JOB_MEMORY_ALLOCATION_REJECTED"))
                        throw new IllegalStateException("actual_native_allocation_rejected_under_job_memory_limit");
                }catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
            assertTrue(Files.readString(output).contains("JOB_MEMORY_ALLOCATION_REJECTED"));
            assertEquals(identity,actual.identity());assertEquals(124,actual.exitCode());
            assertEquals("periodic_guard: actual_native_allocation_rejected_under_job_memory_limit",actual.stopReason());
            assertEquals(64L<<20,actual.accounting().memoryLimitBytes());assertEquals(0,actual.accounting().activeProcesses());
            assertFalse(process.isRunning());assertFalse(actual.passed());
            assertTrue(ManagedGameSession.cleanupProven(process,actual),"a failed resource budget must not leave already-cleaned tracking stuck");
        }
    }
}
