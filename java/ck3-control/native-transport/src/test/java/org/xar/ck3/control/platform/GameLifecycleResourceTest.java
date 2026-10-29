package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsPreloadCustody;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Meaningful original resource regressions. No Steam/Game/injector/Native endpoint is launched. */
final class GameLifecycleResourceTest {
    @TempDir Path temporary;
    private WindowsJobProcess child(String mode)throws IOException{
        Path root=Files.createTempDirectory(temporary,"child-");
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());env.remove("JAVA_TOOL_OPTIONS");
        return child(mode,root,env,List.of());
    }
    private WindowsJobProcess child(String mode,Path root,Map<String,String> environment,List<String> facts)throws IOException{
        return child(mode,root,environment,facts,null);
    }
    private WindowsJobProcess child(String mode,Path root,Map<String,String> environment,List<String> facts,WindowsJobProcess.PreResumeHook hook)throws IOException{
        String cp=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        var args=new ArrayList<>(List.of("-Xms8m","-Xmx16m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=1","-XX:MaxMetaspaceSize=32m","-XX:ReservedCodeCacheSize=16m","-Xss256k","-Djava.io.tmpdir="+System.getProperty("java.io.tmpdir"),"-Djna.tmpdir="+System.getProperty("jna.tmpdir",System.getProperty("java.io.tmpdir")),"-cp",cp,LifecycleSoftwarePeer.class.getName(),mode));
        args.addAll(facts);
        var command=new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),args,root,environment,root.resolve("stdout.raw"),root.resolve("stderr.raw"),128L<<20);
        return hook==null?WindowsJobProcess.start(command):WindowsJobProcess.start(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,hook);
    }
    @Test void actualGameEnvironmentProducerReachesOriginalChildWithInheritanceAndCaseInsensitiveOverrides()throws Exception{
        Path root=Files.createTempDirectory(temporary,"environment-").toAbsolutePath();
        Path scratch=Files.createDirectory(root.resolve("isolated-temp"));
        String pipe="\\\\.\\pipe\\game-environment-software";
        Map<String,String> overrides=Map.of("tEmP",scratch.toString(),"tMp",scratch.toString(),
                "xar_ck3_bridge_mode","native-headless","xar_ck3_bridge_pipe",pipe,
                "JAVA_TOOL_OPTIONS","","_JAVA_OPTIONS","","JDK_JAVA_OPTIONS","");
        Map<String,String> environment=JavaGameLifecycle.gameEnvironment(overrides,pipe);
        try(var process=child("environment",root,environment,List.of(scratch.toString(),pipe))){
            var actual=process.await(Duration.ofSeconds(5),Instant.now().plusSeconds(6),()->{});
            assertEquals(0,actual.exitCode());assertEquals(0,actual.accounting().activeProcesses());assertTrue(actual.passed());
            assertEquals("ENVIRONMENT_OK",Files.readString(root.resolve("stdout.raw")).strip());
        }
        for(String key:List.of("SystemRoot","WINDIR","Path","USERPROFILE","APPDATA","LOCALAPPDATA")){
            assertTrue(System.getenv(key)!=null&&!System.getenv(key).isBlank(),"parent missing "+key);
            assertTrue(java.util.Objects.equals(System.getenv(key),environment.get(key)),"inheritance differs: "+key);
        }
        for(String key:List.of("TEMP","TMP","XAR_CK3_BRIDGE_MODE","XAR_CK3_BRIDGE_PIPE"))
            assertEquals(1L,environment.keySet().stream().filter(name->name.equalsIgnoreCase(key)).count(),"duplicate "+key);
        assertTrue(scratch.toString().equals(environment.get("TEMP")),"override differs: TEMP");
        assertTrue(scratch.toString().equals(environment.get("TMP")),"override differs: TMP");
        assertTrue(scratch.getRoot().equals(Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().getRoot()),"temporary volume differs: TMP");
        assertThrows(UnsupportedOperationException.class,()->environment.put("TEMP","changed"));
    }
    @Test void actualExit259FlowsThroughNewNaturalExitConsumer()throws Exception{
        try(var process=child("exit259")){
            var actual=process.await(Duration.ofSeconds(5),Instant.now().plusSeconds(6),()->{});
            assertEquals(259,actual.exitCode());assertEquals(0,actual.accounting().activeProcesses());assertNull(actual.stopReason());assertFalse(actual.passed());
            var consumed=ManagedGameSession.consumeSignalledRoot(process,Instant.now().plusSeconds(2));
            assertEquals(259,consumed.exitCode());assertNull(consumed.stopReason());assertEquals(0,consumed.accounting().activeProcesses());
        }
    }
    @Test void actualLiveOriginalCannotBeMisreportedAsNaturalTerminal()throws Exception{
        try(var process=child("wait")){
            assertTrue(process.isRunning());
            assertThrows(IOException.class,()->ManagedGameSession.consumeSignalledRoot(process,Instant.now().plusSeconds(1)));
            assertTrue(process.isRunning());process.terminate(125);
            var actual=process.await(Duration.ofSeconds(3),Instant.now().plusSeconds(4),()->{});
            assertEquals(125,actual.exitCode());assertEquals(0,actual.accounting().activeProcesses());assertFalse(actual.passed());
        }
    }

    private WindowsJobProcess heldChild(AtomicReference<WindowsPreloadCustody.Lease> held,AtomicReference<Instant> startup)throws IOException{
        Path root=Files.createTempDirectory(temporary,"runtime-owner-");
        Path file=root.resolve("held-software-resource.dll");Files.writeString(file,"ordinary held software resource");
        var environment=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());environment.remove("JAVA_TOOL_OPTIONS");
        return child("wait",root,environment,List.of(),target->{
            Instant until=Instant.now().plusSeconds(1);startup.set(until);
            var lease=WindowsPreloadCustody.prepare(target,new WindowsPreloadCustody.DllRef(ControlBuild.FileRef.measure(file),until,
                    ()->{throw new IOException("software resource has no source-authority callback");}));
            held.set(lease);return lease;
        });
    }
    private static void crossStartupDeadline(Instant startup)throws InterruptedException{
        long remaining=Duration.between(Instant.now(),startup.plusMillis(150)).toMillis();
        if(remaining>0)Thread.sleep(remaining);
        assertFalse(Instant.now().isBefore(startup));
    }
    @Test void activatedHeldRuntimeSurvivesStartupDeadlineAndExplicitCloseRevokesOnlyItsLease()throws Exception{
        var held=new AtomicReference<WindowsPreloadCustody.Lease>();var startup=new AtomicReference<Instant>();
        try(var process=heldChild(held,startup)){
            held.get().activateRuntime();crossStartupDeadline(startup.get());
            held.get().verify();assertTrue(process.isRunning());
            assertThrows(IOException.class,()->held.get().activateRuntime());
            held.get().close();assertThrows(IOException.class,()->held.get().verify());
            assertTrue(process.isRunning(),"closing a borrowed resource is not an invented Game exit");
            process.terminate(125);
            var actual=process.await(Duration.ofSeconds(2),Instant.now().plusSeconds(3),()->{});
            assertEquals(125,actual.exitCode());assertEquals(0,actual.accounting().activeProcesses());
            assertTrue(ManagedGameSession.cleanupProven(process,actual));assertFalse(actual.passed());
        }
    }
    @Test void expiredStartupCannotBePromotedToRuntime()throws Exception{
        var held=new AtomicReference<WindowsPreloadCustody.Lease>();var startup=new AtomicReference<Instant>();
        try(var process=heldChild(held,startup)){
            crossStartupDeadline(startup.get());
            assertThrows(IOException.class,()->held.get().verify());
            assertThrows(IOException.class,()->held.get().activateRuntime());
            assertTrue(process.isRunning());
            process.terminate(125);
            var actual=process.await(Duration.ofSeconds(2),Instant.now().plusSeconds(3),()->{});
            assertEquals(125,actual.exitCode());assertTrue(ManagedGameSession.cleanupProven(process,actual));
        }
    }
    @Test void activatedRuntimeStillHonorsEachOperationTimeoutAndKeepsFailureTerminal()throws Exception{
        var held=new AtomicReference<WindowsPreloadCustody.Lease>();var startup=new AtomicReference<Instant>();
        try(var process=heldChild(held,startup)){
            held.get().activateRuntime();crossStartupDeadline(startup.get());
            var actual=process.await(Duration.ofMillis(150),Instant.now().plusSeconds(2),()->{
                try{held.get().verify();}catch(IOException unavailable){throw new IllegalStateException(unavailable);}
            });
            assertEquals(124,actual.exitCode());assertEquals("timeout_or_release_expired",actual.stopReason());
            assertEquals(0,actual.accounting().activeProcesses());assertFalse(actual.passed());
            assertTrue(ManagedGameSession.cleanupProven(process,actual));
        }
    }
    @Test void runtimeWatchdogUsesHeldResourceStateAfterStartupDeadlineAndConsumesActualExit()throws Exception{
        var held=new AtomicReference<WindowsPreloadCustody.Lease>();var startup=new AtomicReference<Instant>();
        var stopped=new CountDownLatch(1);var checks=new AtomicInteger();
        var reason=new AtomicReference<GameLifecycle.TerminalKind>();
        var terminal=new AtomicReference<WindowsJobProcess.CommandResult>();
        try(var process=heldChild(held,startup)){
            held.get().activateRuntime();
            var watchdog=new GameWatchdog(new GameWatchdog.Target(){
                @Override public String sessionId(){return "actual-software-runtime";}
                @Override public GameLifecycle.TerminalKind inspect()throws IOException{
                    if(!process.isRunning())return GameLifecycle.TerminalKind.NATURAL_EXIT;
                    held.get().verify();checks.incrementAndGet();return null;
                }
                @Override public void stop(GameLifecycle.TerminalKind actualReason)throws InterruptedException{
                    reason.set(actualReason);
                    terminal.set(process.await(Duration.ofSeconds(2),Instant.now().plusSeconds(3),()->{}));
                    stopped.countDown();
                }
            });
            try{
                crossStartupDeadline(startup.get());assertTrue(process.isRunning());
                assertTrue(checks.get()>0);assertEquals(1,stopped.getCount());
                process.terminate(125);assertTrue(stopped.await(3,TimeUnit.SECONDS));
                assertEquals(GameLifecycle.TerminalKind.NATURAL_EXIT,reason.get());
                assertEquals(125,terminal.get().exitCode());assertFalse(terminal.get().passed());
                assertTrue(ManagedGameSession.cleanupProven(process,terminal.get()));
            }finally{watchdog.cancel();}
        }
    }

    @Test void failedBusinessWorkerAndObservationDoNotStopIndependentGameOwner()throws Exception{
        try(var process=child("wait");var retained=WindowsJobProcess.retainReadOnlyProcess(process.identity().pid())){
            var original=retained.identity();assertEquals(process.identity(),original);
            WindowsJobProcess.CommandResult failed;
            try(var worker=child("unsupported-worker-constructor")){
                failed=worker.await(Duration.ofSeconds(5),Instant.now().plusSeconds(6),()->{});
                assertNotEquals(0,failed.exitCode());assertFalse(failed.passed());
                assertEquals(0,failed.accounting().activeProcesses());assertFalse(worker.isRunning());
            }
            var observedFailure=new AtomicReference<IOException>(new IOException("actual failed software worker: "+failed));
            var polls=new CountDownLatch(2);var stopped=new CountDownLatch(1);var stops=new AtomicInteger();
            var reason=new AtomicReference<GameLifecycle.TerminalKind>();
            var terminal=new AtomicReference<WindowsJobProcess.CommandResult>();
            var watchdog=new GameWatchdog(new GameWatchdog.Target(){
                @Override public String sessionId(){return "independent-owner-after-worker-failure";}
                @Override public GameLifecycle.TerminalKind inspect()throws IOException{
                    polls.countDown();
                    if(!process.isRunning())return GameLifecycle.TerminalKind.NATURAL_EXIT;
                    IOException failure=observedFailure.get();if(failure!=null)throw failure;
                    return null;
                }
                @Override public void stop(GameLifecycle.TerminalKind actualReason)throws InterruptedException{
                    stops.incrementAndGet();reason.set(actualReason);
                    if(process.isRunning())process.terminate(125);
                    terminal.set(process.await(Duration.ofSeconds(2),Instant.now().plusSeconds(3),()->{}));
                    stopped.countDown();
                }
            });
            try{
                boolean continued=polls.await(4,TimeUnit.SECONDS);
                assertTrue(continued,"failed business observation must leave owner polling alive; stops="+stops.get()+"; held_wait="+retained.waitZero());
                assertEquals(0,stops.get());assertEquals(258,retained.waitZero());assertEquals(original,retained.identity());
                observedFailure.set(null);
                try(var replacement=child("exit0")){
                    var actual=replacement.await(Duration.ofSeconds(5),Instant.now().plusSeconds(6),()->{});
                    assertTrue(actual.passed());assertEquals(0,actual.accounting().activeProcesses());
                }
                assertEquals(0,stops.get());assertEquals(258,retained.waitZero());assertEquals(original,retained.identity());
                process.terminate(125);assertTrue(stopped.await(3,TimeUnit.SECONDS));
                assertEquals(1,stops.get());assertEquals(GameLifecycle.TerminalKind.NATURAL_EXIT,reason.get());
                assertEquals(125,terminal.get().exitCode());assertFalse(terminal.get().passed());
                assertTrue(ManagedGameSession.cleanupProven(process,terminal.get()));assertEquals(0,retained.waitZero());
            }finally{watchdog.cancel();}
        }
    }
    @Test void actualTimeoutPreservesInnerReasonAndWholeJobCleanup()throws Exception{
        try(var process=child("wait")){
            var actual=process.await(Duration.ofMillis(200),Instant.now().plusSeconds(3),()->{});
            assertEquals(124,actual.exitCode());assertEquals("timeout_or_release_expired",actual.stopReason());assertEquals(0,actual.accounting().activeProcesses());assertFalse(actual.passed());
        }
    }
    @Test void actualSourceMutationRevokesHeldProcessGuardAndRetainsFailure()throws Exception{
        Path source=temporary.resolve("source.txt");Files.writeString(source,"original");var witness=SharedSourceFiles.observe(source);
        try(var process=child("wait")){
            Files.writeString(source,"changed!");
            var actual=process.await(Duration.ofSeconds(3),Instant.now().plusSeconds(4),()->{
                try{SharedSourceFiles.assertUnchanged(witness);}catch(IOException drift){throw new IllegalStateException("actual-source-drift",drift);}
            });
            assertEquals(124,actual.exitCode());assertEquals("periodic_guard: actual-source-drift",actual.stopReason());assertEquals(0,actual.accounting().activeProcesses());
        }
    }
}
