package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameLifecycle;

final class ReleasedLaunchFailureTest {
    @TempDir Path temporary;
    private static final String ID="failed-launch-data",MACHINE="machine-data",SESSION="session-data",NONCE="nonce-data";
    private record Fixture(ReleasedLaunchFailure.Request request,Path control,byte[] claim,byte[] marker) { }
    private Fixture fixture(WindowsJobProcess.CommandResult terminal)throws Exception {
        Path state=temporary.resolve("state");Path control=Files.createDirectories(state.resolve("control"));
        var claim=ControlBuild.strictMapper().createObjectNode().put("schema","xar.java-game-launch-claim/v1").put("machine_id",MACHINE)
                .put("request_id",ID).put("session_id",SESSION).put("nonce",NONCE).put("state","UNKNOWN").put("observed_at_utc",Instant.now().toString());
        claim.set("game",ControlBuild.strictMapper().valueToTree(terminal.identity()));
        Path c=control.resolve("request-"+ID+".json");Files.write(c,ControlBuild.strictMapper().writeValueAsBytes(claim));
        var marker=claim.deepCopy().put("schema","xar.java-game-unsafe/v1").put("state","CREATE_ENTERED");
        Path m=control.resolve("unsafe-cleanup.json");Files.write(m,ControlBuild.strictMapper().writeValueAsBytes(marker));
        Path e=temporary.resolve("event-stopped.json");
        Files.write(e,ControlBuild.strictMapper().writeValueAsBytes(new LifecycleEvidence.Row("xar.java-game-lifecycle-event/v1",MACHINE,
                Instant.now().toString(),ID,SESSION,LifecycleEvidence.Event.STOPPED,terminal.identity(),terminal.accounting(),terminal,
                GameLifecycle.TerminalKind.UNKNOWN,"NoGame original failed-child terminal DATA")));
        var request=new ReleasedLaunchFailure.Request("xar.java-game-released-failure-request/v1",MACHINE,ID,SESSION,NONCE,
                terminal.identity(),state.toString(),ControlBuild.FileRef.measure(c),ControlBuild.FileRef.measure(m),ControlBuild.FileRef.measure(e),
                "operator-decision-data",Instant.now().plusSeconds(30).toString());
        return new Fixture(request,control,Files.readAllBytes(c),Files.readAllBytes(m));
    }
    private static WindowsJobProcess.CommandResult data(int active) {
        return new WindowsJobProcess.CommandResult(new WindowsJobProcess.ProcessIdentity(42,"1234",Path.of(System.getProperty("java.home"),"bin/java.exe").toString()),
                125,1,new WindowsJobProcess.Accounting(1234,active,128L<<20,8704),null);
    }
    private static Win32Host.ProcessInventory empty(ReleasedLaunchFailure.Request r){return new Win32Host.ProcessInventory(Path.of(r.game().executable()).getFileName().toString(),Instant.now().toString(),List.of());}
    @Test void actualOwnedChildCleanupThroughCodecAndRetirementKeepsUnknownAndOnlyAllowsFreshId()throws Exception {
        String cp=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        var argv=List.of("-Xms8m","-Xmx16m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=1","-cp",cp,LifecycleSoftwarePeer.class.getName(),"wait");
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
        var spec=new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),argv,temporary,env,temporary.resolve("out"),temporary.resolve("err"),128L<<20);
        try(var child=WindowsJobProcess.start(spec)) {
            var terminal=JavaGameLifecycle.consumeUnknownCleanup(child,Instant.now().plusSeconds(10));assertEquals(0,terminal.accounting().activeProcesses());assertEquals(125,terminal.exitCode());
            var f=fixture(terminal);Path request=temporary.resolve("retirement-request.json");Files.write(request,ControlBuild.strictMapper().writeValueAsBytes(f.request()));
            var decoded=ReleasedLaunchFailure.readRequest(request);assertEquals(f.request(),decoded);
            assertThrows(IOException.class,()->ReleasedLaunchFailure.requireFresh(f.control(),"new-launch-data"));
            var receipt=ReleasedLaunchFailure.publish(decoded,empty(decoded));assertTrue(Files.isRegularFile(Path.of(receipt.path())));
            assertArrayEquals(f.claim(),Files.readAllBytes(Path.of(decoded.claim().path())));assertArrayEquals(f.marker(),Files.readAllBytes(Path.of(decoded.unsafeMarker().path())));
            ReleasedLaunchFailure.requireFresh(f.control(),"new-launch-data");
            assertThrows(IOException.class,()->ReleasedLaunchFailure.requireFresh(f.control(),ID));
            assertThrows(IOException.class,()->ReleasedLaunchFailure.publish(decoded,empty(decoded)));
            assertFalse(terminal.passed());
        }
    }
    @Test void activeJobTerminalCannotBuyRetirement()throws Exception {
        var f=fixture(data(1));assertThrows(IOException.class,()->ReleasedLaunchFailure.publish(f.request(),empty(f.request())));
        assertFalse(Files.exists(f.control().resolve("retirement-"+ID+".json")));
    }
    @Test void wrongNonceAndWrongControlRootCannotRetireAnotherLaunch()throws Exception {
        var f=fixture(data(0));var r=f.request();
        var wrong=new ReleasedLaunchFailure.Request(r.schema(),r.machineId(),r.requestId(),r.sessionId(),"other-nonce",r.game(),r.stateDirectory(),r.claim(),r.unsafeMarker(),r.terminalEvidence(),r.operatorDecisionId(),r.deadlineUtc());
        assertThrows(IOException.class,()->ReleasedLaunchFailure.publish(wrong,empty(wrong)));
        var wrongRoot=new ReleasedLaunchFailure.Request(r.schema(),r.machineId(),r.requestId(),r.sessionId(),r.nonce(),r.game(),temporary.toString(),r.claim(),r.unsafeMarker(),r.terminalEvidence(),r.operatorDecisionId(),r.deadlineUtc());
        assertThrows(IOException.class,()->ReleasedLaunchFailure.publish(wrongRoot,empty(wrongRoot)));
    }
    @Test void alteredOriginalPinsInvalidatePublishedRetirement()throws Exception {
        var f=fixture(data(0));ReleasedLaunchFailure.publish(f.request(),empty(f.request()));
        Files.writeString(Path.of(f.request().terminalEvidence().path()),"{}");
        assertThrows(IOException.class,()->ReleasedLaunchFailure.requireFresh(f.control(),"new-launch-data"));
    }
    @Test void staleInventoryAndMissingFieldsAreRejectedBeforePublication()throws Exception {
        var f=fixture(data(0));var stale=new Win32Host.ProcessInventory("java.exe",Instant.now().minusSeconds(60).toString(),List.of());
        assertThrows(IOException.class,()->ReleasedLaunchFailure.publish(f.request(),stale));
        var row=ControlBuild.strictMapper().valueToTree(f.request());assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,row).remove("nonce");
        Path request=temporary.resolve("bad-request.json");Files.write(request,ControlBuild.strictMapper().writeValueAsBytes(row));
        assertThrows(IOException.class,()->ReleasedLaunchFailure.readRequest(request));
    }
}
