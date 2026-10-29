package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.service.root.RootFiniteFirstLiveResultReader;
import org.xar.ck3.control.service.root.RootFiniteFirstLiveWork;

/** Software producer/consumer coverage. No child, Game, lease or launch qualification is created. */
final class RootFiniteFirstLiveOutputTest {
    @TempDir Path temporary;

    @Test void originalWorkEncoderAndCommandEncoderPreserveIndependentStartupAndBusinessFailure() throws Exception {
        for (var outcome : List.of(RootFiniteFirstLiveWork.Outcome.NOT_RUN, RootFiniteFirstLiveWork.Outcome.FAILED)) {
            var directory = Files.createDirectory(temporary.resolve(outcome.name()));
            byte[] report = report(outcome);
            var command = command(directory, SharedOwnedCommand.Status.RED, child(1, 0, null),
                    "original Main failed", "Quarkus startup log\n" + text(report) + "\r\nQuarkus stopped\n");
            var result = RootFiniteFirstLiveResultReader.consume(command, 1 << 20);

            assertEquals(1, result.mainExitCode().orElseThrow());
            assertEquals(outcome, result.report().orElseThrow().report().outcome());
            assertEquals(outcome == RootFiniteFirstLiveWork.Outcome.NOT_RUN ? 3 : 26,
                    result.report().orElseThrow().report().exitCode());
            assertEquals(Optional.of("original Main failed"), result.command().failure());
            assertFalse(result.completedSuccessfully());
            // CRLF belongs to stdout; the decoder receives the original line including its trailing CR.
            assertEquals(text(report) + "\r", text(result.report().orElseThrow().originalJson()));
            assertArrayEquals(report, report(outcome));
        }
    }

    @Test void timeoutAndRemainingJobMembersKeepTheOriginalReportAndNeverBecomeSuccess() throws Exception {
        byte[] report = report(RootFiniteFirstLiveWork.Outcome.NOT_RUN);
        var timeout = command(Files.createDirectory(temporary.resolve("timeout")), SharedOwnedCommand.Status.RED,
                child(1, 0, "command deadline expired"), "original child timed out", text(report) + "\n");
        var timed = RootFiniteFirstLiveResultReader.consume(timeout, 1 << 20);
        assertEquals("command deadline expired", timed.command().child().orElseThrow().stopReason());
        assertEquals(RootFiniteFirstLiveWork.Outcome.NOT_RUN, timed.report().orElseThrow().report().outcome());
        assertFalse(timed.completedSuccessfully());

        var stillActive = command(Files.createDirectory(temporary.resolve("remaining-job")), SharedOwnedCommand.Status.RED,
                child(0, 1, "owned Job did not drain"), "original Job remains nonempty", text(report) + "\n");
        var retained = RootFiniteFirstLiveResultReader.consume(stillActive, 1 << 20);
        assertEquals(0, retained.mainExitCode().orElseThrow());
        assertEquals(1, retained.command().child().orElseThrow().accounting().activeProcesses());
        assertTrue(retained.report().isPresent());
        assertFalse(retained.completedSuccessfully());
    }

    @Test void failureBeforeWorkExistsPreservesMissingReportAndActualChildExit() throws Exception {
        var started = command(Files.createDirectory(temporary.resolve("before-work")), SharedOwnedCommand.Status.RED,
                child(1, 0, null), "request read failed before Work construction", "original startup diagnostic\n");
        var result = RootFiniteFirstLiveResultReader.consume(started, 1 << 20);
        assertTrue(result.report().isEmpty());
        assertEquals(1, result.mainExitCode().orElseThrow());
        assertFalse(result.completedSuccessfully());

        var rejected = command(Files.createDirectory(temporary.resolve("not-started")), SharedOwnedCommand.Status.REJECTED,
                null, "launcher rejected before child startup", null);
        var notStarted = RootFiniteFirstLiveResultReader.consume(rejected, 1 << 20);
        assertFalse(notStarted.command().childStarted());
        assertTrue(notStarted.mainExitCode().isEmpty());
        assertTrue(notStarted.report().isEmpty());
        assertFalse(notStarted.completedSuccessfully());
    }

    private WindowsJobProcess.CommandResult child(int exit, int active, String stop) {
        return new WindowsJobProcess.CommandResult(
                new WindowsJobProcess.ProcessIdentity(17, "134374327516050267", temporary.resolve("software-only-java.exe").toString()),
                exit, 0.1, new WindowsJobProcess.Accounting(1024, active, 1 << 20, WindowsJobProcess.REQUIRED_FLAGS), stop);
    }

    private static byte[] report(RootFiniteFirstLiveWork.Outcome outcome) {
        return new RootFiniteFirstLiveWork.Report("software-request", "software-machine", outcome, "original Work detail",
                Optional.empty(), Optional.empty(), 0, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()).toJson();
    }

    private static String text(byte[] value) { return new String(value, StandardCharsets.UTF_8); }

    private static SharedOwnedCommand.Outcome command(Path directory, SharedOwnedCommand.Status status,
            WindowsJobProcess.CommandResult child, String failure, String stdout) throws Exception {
        var input = directory.resolve("software-input.json");
        Files.writeString(input, "{}", StandardOpenOption.CREATE_NEW);
        var inputRef = FileRef.measure(input);
        FileRef stdoutRef = null;
        if (stdout != null) {
            var output = directory.resolve("stdout.log");
            Files.writeString(output, stdout, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
            stdoutRef = FileRef.measure(output);
        }
        var reached = child == null ? SharedOwnedCommand.Check.NOT_REACHED : SharedOwnedCommand.Check.MATCH;
        var terminal = new SharedOwnedCommand.Terminal("xar.shared-owned-command-terminal/v4", "software-machine",
                "2026-10-26T00:00:00Z", status, "software-owner", "software-slot", null,
                inputRef, inputRef, inputRef, List.of(),
                new SharedOwnedCommand.Outer("1", 1 << 20, false, "software fixture; no process was started"),
                child != null, child,
                new WindowsJobProcess.JobDiagnosticOutcome(WindowsJobProcess.DiagnosticWriteState.NOT_REQUESTED, null, null, null),
                reached, reached, reached, failure, List.of(), List.of(), stdoutRef, null, 0, 0, 0, null);
        var file = directory.resolve("terminal.json");
        Files.write(file, SharedOwnedCommand.encodeTerminal(terminal, true), StandardOpenOption.CREATE_NEW);
        return new SharedOwnedCommand.Outcome(status, FileRef.measure(file));
    }
}
