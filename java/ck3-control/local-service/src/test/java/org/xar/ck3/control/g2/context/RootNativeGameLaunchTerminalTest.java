package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Terminal metadata and real file failures only; no process, injector, Native or Game qualification. */
final class RootNativeGameLaunchTerminalTest {
    @TempDir Path temporary;

    @Test void createNewFailureKeepsOriginalExitTimeoutAndWholeJobWithoutRetry() throws Exception {
        Path out=Files.writeString(temporary.resolve("stdout.log"),"fixture output");
        Path err=Files.writeString(temporary.resolve("stderr.log"),"fixture error");
        int index=0;
        for(var terminal:terminals()) {
            Path receipt=Files.writeString(temporary.resolve("terminal-"+(index++)+".json"),"prior evidence");
            var attempt=new RootNativeGameLaunch.LoaderAttempt();attempt.submit();
            assertThrows(IOException.class,()->attempt.complete(terminal,receipt,out,err));
            assertEquals(RootNativeGameLaunch.Submission.UNKNOWN,attempt.current().submission());
            assertSame(terminal,attempt.current().terminal());
            assertEquals("prior evidence",Files.readString(receipt));
            assertNull(attempt.current().stdout());assertNull(attempt.current().stderr());
            assertThrows(IOException.class,attempt::submit);
            assertThrows(IOException.class,()->attempt.complete(terminal,receipt,out,err));
        }
    }

    @Test void missingStderrKeepsTerminalAndAlreadyMeasuredStdout() throws Exception {
        var terminal=terminals().getFirst();
        Path out=Files.writeString(temporary.resolve("stdout.log"),"fixture output");
        Path receipt=temporary.resolve("terminal.json");
        var attempt=new RootNativeGameLaunch.LoaderAttempt();attempt.submit();
        assertThrows(IOException.class,()->attempt.complete(terminal,receipt,out,temporary.resolve("absent.log")));
        assertEquals(RootNativeGameLaunch.Submission.UNKNOWN,attempt.current().submission());
        assertSame(terminal,attempt.current().terminal());
        assertEquals(ControlBuild.FileRef.measure(out),attempt.current().stdout());
        assertNull(attempt.current().stderr());assertRoundtrip(terminal,receipt);
        assertThrows(IOException.class,attempt::submit);
    }

    @Test void unsuccessfulTerminalWithCompleteEvidenceNeverBecomesSuccess() throws Exception {
        var cases=terminals();int index=0;
        for(var terminal:cases.subList(1,cases.size())) {
            Path root=Files.createDirectory(temporary.resolve("case-"+index++));
            Path out=Files.writeString(root.resolve("stdout.log"),"fixture output");
            Path err=Files.writeString(root.resolve("stderr.log"),"fixture error");
            Path receipt=root.resolve("terminal.json");
            var attempt=new RootNativeGameLaunch.LoaderAttempt();attempt.submit();
            assertThrows(IOException.class,()->attempt.complete(terminal,receipt,out,err));
            assertEquals(RootNativeGameLaunch.Submission.UNKNOWN,attempt.current().submission());
            assertSame(terminal,attempt.current().terminal());
            assertNotNull(attempt.current().stdout());assertNotNull(attempt.current().stderr());
            assertRoundtrip(terminal,receipt);assertThrows(IOException.class,attempt::submit);
        }
    }

    @Test void successNeedsBothLogsAndLaterFailureRetainsOriginalTerminal() throws Exception {
        var terminal=terminals().getFirst();
        Path out=Files.writeString(temporary.resolve("stdout.log"),"fixture output");
        Path err=Files.writeString(temporary.resolve("stderr.log"),"fixture error");
        var attempt=new RootNativeGameLaunch.LoaderAttempt();attempt.submit();
        Path receipt=temporary.resolve("terminal.json");attempt.complete(terminal,receipt,out,err);
        assertEquals(RootNativeGameLaunch.Submission.EXIT_ZERO_JOB_EMPTY,attempt.current().submission());
        assertSame(terminal,attempt.current().terminal());assertRoundtrip(terminal,receipt);
        assertEquals(ControlBuild.FileRef.measure(out),attempt.current().stdout());
        assertEquals(ControlBuild.FileRef.measure(err),attempt.current().stderr());
        attempt.unknown();assertEquals(RootNativeGameLaunch.Submission.UNKNOWN,attempt.current().submission());
        assertSame(terminal,attempt.current().terminal());
        assertNotNull(attempt.current().stdout());assertNotNull(attempt.current().stderr());
        assertThrows(IOException.class,attempt::submit);
    }

    @Test void failureBeforeAwaitReturnsDoesNotInventATerminal() throws Exception {
        var attempt=new RootNativeGameLaunch.LoaderAttempt();attempt.submit();attempt.unknown();
        assertEquals(RootNativeGameLaunch.Submission.UNKNOWN,attempt.current().submission());
        assertNull(attempt.current().terminal());assertNull(attempt.current().stdout());assertNull(attempt.current().stderr());
        assertThrows(IOException.class,attempt::submit);
    }
    private void assertRoundtrip(WindowsJobProcess.CommandResult original,Path receipt)throws IOException {
        assertEquals(original,ControlBuild.strictMapper().readValue(Files.readAllBytes(receipt),WindowsJobProcess.CommandResult.class));
    }
    private WindowsJobProcess.CommandResult terminal(int exit,String reason,int active,long peak,int flags) {
        return new WindowsJobProcess.CommandResult(new WindowsJobProcess.ProcessIdentity(23,"132000000000000001",
                temporary.resolve("fixture-injector.exe").toAbsolutePath().toString()),exit,1.25,
                new WindowsJobProcess.Accounting(peak,active,64,flags),reason);
    }
    private List<WindowsJobProcess.CommandResult> terminals() {
        return List.of(terminal(0,null,0,16,WindowsJobProcess.REQUIRED_FLAGS),
                terminal(17,null,0,16,WindowsJobProcess.REQUIRED_FLAGS),
                terminal(0,"command-timeout",0,16,WindowsJobProcess.REQUIRED_FLAGS),
                terminal(0,null,1,16,WindowsJobProcess.REQUIRED_FLAGS),
                terminal(0,null,0,65,WindowsJobProcess.REQUIRED_FLAGS),terminal(0,null,0,16,0));
    }
}
