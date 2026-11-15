package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Real ordinary Windows process and original supervisor producer; no CK3/Steam/Native or Saved launch. */
final class ExitedGameSourceTest {
    @TempDir Path temporary;
    private record Subject(WindowsJobProcess process,NativeLaunchPlan plan,Path owner,ExactRef terminalEvent,
            WindowsJobProcess.CommandResult terminal,byte[] terminalBytes) implements AutoCloseable {
        @Override public void close(){process.close();}
    }
    private ControlBuild.FileRef file(String name,String content)throws IOException {
        Path path=temporary.resolve(name);Files.createDirectories(path.getParent());Files.writeString(path,content);
        return ControlBuild.FileRef.measure(path);
    }
    private Subject exited()throws Exception {
        Path peer=temporary.resolve("exited-peer-"+UUID.randomUUID()+".exe");
        Files.copy(Path.of(System.getenv("SystemRoot"),"System32","ping.exe"),peer);
        var environment=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());
        for(String name:List.of("JAVA_TOOL_OPTIONS","_JAVA_OPTIONS","JDK_JAVA_OPTIONS"))environment.remove(name);
        var process=WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(peer,List.of("127.0.0.1","-n","30"),
                temporary,environment,temporary.resolve("peer.stdout"),temporary.resolve("peer.stderr"),128L<<20));
        try {
            exitOwnPeer259(process.identity());
            var terminal=process.await(Duration.ofSeconds(5),Instant.now().plusSeconds(7),()->{});
            assertEquals(259,terminal.exitCode(),()->"software peer stderr: "+readPeerError());assertEquals(0,terminal.accounting().activeProcesses());
            String machine=WindowsJobProcess.currentMachineId();Instant deadline=Instant.now().plusSeconds(40);
            var dll=file("software.dll","no Native library is loaded");var injector=file("software-injector.exe","no injector is run");
            var inputs=new NativeLaunchEvidence.Inputs(file("environment.json","environment DATA"),file("build.json","build DATA"),file("registration.json","registration DATA"));
            var review=new LaunchSourceBinding.Review(machine,deadline,ControlBuild.FileRef.measure(peer),dll,injector,
                    inputs,temporary,List.of(file("source.txt","software source")));
            Path profile=Files.createDirectory(temporary.resolve("profile"));Files.createDirectories(profile.resolve("save games"));
            Path saved=profile.resolve("save games/checkpoint.ck3");Files.writeString(saved,"software checkpoint; never loaded");
            Path state=Files.createDirectory(temporary.resolve("state")),events=Files.createDirectory(temporary.resolve("events"));
            String pipe="\\\\.\\pipe\\exited-software-"+UUID.randomUUID();
            var plan=new NativeLaunchPlan("software-launch","software-session",LaunchSourceBinding.accept(review),profile,state,events,
                    pipe,"software-bridge","software-adapter",new NativeLaunchPlan.SavedGame("checkpoint",ControlBuild.FileRef.measure(saved)),
                    false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),128L<<20,32L<<20,deadline,
                    Duration.ofSeconds(2),Duration.ofSeconds(3),new SteamOfflineProbe.Plan(machine,file("steam.exe","not a Steam runtime"),deadline),
                    NativeLaunchPlan.PreparedProfile.vanilla(),64);
            var evidence=new LifecycleEvidence(plan);
            ExactRef launch=evidence.write(LifecycleEvidence.Event.HELLO,terminal.identity(),terminal.accounting(),null,null,
                    "offline protocol fixture: no Native handshake is claimed");
            ExactRef exit=evidence.write(LifecycleEvidence.Event.STOPPED,terminal.identity(),terminal.accounting(),terminal,
                    GameLifecycle.TerminalKind.NATURAL_EXIT,"actual ordinary child root signal and Job0");
            Path hello=temporary.resolve("software-hello.packet");Files.writeString(hello,"offline protocol fixture, not Native evidence");
            ExactRef helloRef=LifecycleEvidence.exact(ControlBuild.FileRef.measure(hello));
            Path ownerDirectory=Files.createDirectory(temporary.resolve("owner"));Path owner=ownerDirectory.resolve("owner.json");
            WindowsJobProcess.ProcessIdentity supervisor;
            try(var handle=WindowsJobProcess.retainReadOnlyProcess(ProcessHandle.current().pid())){supervisor=handle.identity();}
            var descriptor=new GameSupervisorControl.Descriptor(machine,plan.sessionId(),supervisor,terminal.identity(),
                    NativeLaunchPlanCodec.describe(plan),helloRef,launch,ownerDirectory.resolve("stop-request.json"),ownerDirectory.resolve("terminal.json"));
            GameSupervisorControl.writeDescriptor(owner,descriptor);
            byte[] encoded=GameSupervisor.encodeTerminal(machine,plan.sessionId(),terminal.identity(),
                    new GameSupervisor.Completed("",new GameSupervisor.Terminal(terminal,true,GameLifecycle.TerminalKind.NATURAL_EXIT,Optional.of(exit))));
            GameSupervisorControl.publish(ownerDirectory.resolve("terminal.json"),encoded,false);
            return new Subject(process,plan,owner,exit,terminal,encoded);
        }catch(Exception failure){process.close();throw failure;}
    }
    /** Real OS exit of this exact owned test child; never an old Game or another process sharing its PID. */
    private static void exitOwnPeer259(WindowsJobProcess.ProcessIdentity own)throws IOException {
        var api=com.sun.jna.platform.win32.Kernel32.INSTANCE;
        var handle=api.OpenProcess(0x00101001,false,(int)own.pid()); // QUERY_LIMITED_INFORMATION | SYNCHRONIZE | TERMINATE
        if(handle==null)throw new IOException("own software peer open failed: "+com.sun.jna.Native.getLastError());
        try {
            var birth=new com.sun.jna.platform.win32.WinBase.FILETIME();var exit=new com.sun.jna.platform.win32.WinBase.FILETIME();
            if(!api.GetProcessTimes(handle,birth,exit,new com.sun.jna.platform.win32.WinBase.FILETIME(),new com.sun.jna.platform.win32.WinBase.FILETIME()))
                throw new IOException("own software peer time failed: "+com.sun.jna.Native.getLastError());
            String actual=BigInteger.valueOf(Integer.toUnsignedLong(birth.dwHighDateTime)).shiftLeft(32)
                    .add(BigInteger.valueOf(Integer.toUnsignedLong(birth.dwLowDateTime))).toString();
            if(!actual.equals(own.creationFiletimeDecimal())||api.WaitForSingleObject(handle,0)!=258)
                throw new IOException("own software peer birth/running identity changed");
            if(!api.TerminateProcess(handle,259))throw new IOException("own software peer exit259 failed: "+com.sun.jna.Native.getLastError());
        }finally{if(!api.CloseHandle(handle))throw new IOException("own software peer handle close failed");}
    }
    private String readPeerError(){try{byte[] raw=Files.readAllBytes(temporary.resolve("peer.stderr"));return "raw="+java.util.HexFormat.of().formatHex(raw)+" decoded="+new String(raw,java.nio.charset.Charset.forName("GB18030"));}catch(IOException unavailable){return unavailable.toString();}}
    @Test void realSupervisorTerminalAndKernelExitIssueAnOpaqueRoleWithoutCurrentManagedSession()throws Exception {
        try(var subject=exited()) {
            var lifecycle=new JavaGameLifecycle(List.of());assertTrue(lifecycle.currentSession().isEmpty());
            var original=subject.terminal().identity();var generation=ManagedGameSession.generation(original);
            var role=lifecycle.qualifyExitedOwner(subject.owner(),generation,subject.plan(),subject.plan().deadline());
            assertEquals(generation,role.generation());assertEquals(subject.plan().sessionId(),role.sourceSessionId());
            assertEquals(WindowsJobProcess.currentMachineId(),role.machineId());assertEquals(subject.plan().deadline(),role.deadline());
            assertEquals(NativeLaunchPlanCodec.describe(subject.plan()),role.originalConfiguration());
            role.requireOwner(lifecycle,subject.plan().deadline());role.requireHistoricalOwner(lifecycle);
            assertTrue(lifecycle.currentSession().isEmpty(),"source qualification must not launch or adopt a Game");
            var proof=StrictJson.parse(Files.readAllBytes(Path.of(role.evidence().path())),262144);
            assertEquals("xar.java-exited-game-source-observation/v1",proof.path("schema").textValue());
            assertEquals(0,proof.path("kernel").path("original_pid").path("wait_after").intValue());
            assertEquals(259,proof.path("kernel").path("original_pid").path("exit_code").intValue());
            assertThrows(IOException.class,()->role.requireOwner(new JavaGameLifecycle(List.of()),subject.plan().deadline()));
            assertThrows(IOException.class,()->role.requireOwner(lifecycle,subject.plan().deadline().plusSeconds(1)));
            assertThrows(IOException.class,()->role.requireMembership(new JavaGameLifecycle(List.of()),subject.plan().deadline()));
            assertThrows(IOException.class,()->role.requireMembership(lifecycle,subject.plan().deadline().plusSeconds(1)));
        }
    }
    @Test void wrongBirthMissingCleanupAndChangedOriginalEventNeverIssueOrReuseTheRole()throws Exception {
        try(var subject=exited()) {
            var lifecycle=new JavaGameLifecycle(List.of());var generation=ManagedGameSession.generation(subject.terminal().identity());
            var wrong=new GameGeneration(generation.pid(),new PythonOnlyUInt64(generation.creationFiletime().value().add(BigInteger.ONE)));
            assertThrows(IOException.class,()->lifecycle.qualifyExitedOwner(subject.owner(),wrong,subject.plan(),subject.plan().deadline()));
            var parsed=StrictJson.parse(subject.terminalBytes(),262144);
            var noCleanup=((com.fasterxml.jackson.databind.node.ObjectNode)parsed).deepCopy();noCleanup.put("cleanup_proven",false);
            assertThrows(IOException.class,()->ExitedGameSource.readTerminal(StrictJson.canonical(noCleanup,262144)));
            var active=((com.fasterxml.jackson.databind.node.ObjectNode)parsed).deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode)active.path("actual_terminal").path("accounting")).put("active_processes",1);
            assertThrows(IOException.class,()->ExitedGameSource.readTerminal(StrictJson.canonical(active,262144)));
            var role=lifecycle.qualifyExitedOwner(subject.owner(),generation,subject.plan(),subject.plan().deadline());
            Files.writeString(Path.of(subject.terminalEvent().path()),"changed original terminal");
            role.requireMembership(lifecycle,subject.plan().deadline()); // An archive read checks custody, not fresh source/OS proof.
            assertThrows(IOException.class,()->role.requireOwner(lifecycle,subject.plan().deadline()));
            assertTrue(lifecycle.currentSession().isEmpty());
        }
    }
    @Test void originalTerminalProducerPreservesNonzeroExitAndRejectsTypedIdentityCoercion()throws Exception {
        try(var subject=exited()) {
            var terminal=ExitedGameSource.readTerminal(subject.terminalBytes());
            assertEquals(259,terminal.exitCode());assertEquals(subject.terminal().identity(),terminal.game());
            assertEquals(subject.terminalEvent(),terminal.originalEvidence());
            var raw=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(subject.terminalBytes(),262144);
            var changed=raw.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("game")).put("pid",42.0);
            assertThrows(IOException.class,()->ExitedGameSource.readTerminal(ControlBuild.strictMapper().writeValueAsBytes(changed)));
            var unknown=raw.deepCopy();unknown.put("terminal_kind","UNKNOWN");
            assertThrows(IOException.class,()->ExitedGameSource.readTerminal(StrictJson.canonical(unknown,262144)));
        }
    }
    @Test void persistentOldGenerationClaimRefusesANewWorkerAndDifferentRequestWithoutLaunching()throws Exception {
        try(var subject=exited()) {
            var lifecycle=new JavaGameLifecycle(List.of());var generation=ManagedGameSession.generation(subject.terminal().identity());
            var role=lifecycle.qualifyExitedOwner(subject.owner(),generation,subject.plan(),subject.plan().deadline());
            String originalKey=role.machineId()+":"+generation.pid()+":"+generation.creationFiletime().value();
            Path claim=subject.plan().stateDirectory().resolve("control/exited-generation-"+JavaGameLifecycle.replacementRequestId(originalKey)+".json");
            Files.writeString(claim,"original replacement entered; unavailable terminal remains UNKNOWN");
            var saved=(NativeLaunchPlan.SavedGame)subject.plan().load();
            var plan=subject.plan().savedReplacement("different-worker-request",saved.save(),subject.plan().deadline());
            var request=new JavaGameLifecycle.ReplacementRequest("different-worker-request",generation,plan,false);
            var result=lifecycle.replaceExitedSavedOnce(request,role);
            assertInstanceOf(JavaGameLifecycle.ReplacementUnknown.class,result);
            assertTrue(result.toString().contains("persistent exited-generation"));
            assertTrue(lifecycle.currentSession().isEmpty());
            assertFalse(Files.exists(plan.evidenceRoot()),"refused replay must not enter a new Saved launch");
            assertEquals("original replacement entered; unavailable terminal remains UNKNOWN",Files.readString(claim));
        }
    }
}
