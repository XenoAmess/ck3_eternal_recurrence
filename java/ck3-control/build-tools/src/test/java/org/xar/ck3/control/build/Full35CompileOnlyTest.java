package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class Full35CompileOnlyTest {
    @TempDir Path temporary;

    @Test void rawDiagnosticsDoNotRequireAnEncodingAndErrorRowsRemainFailures() throws Exception {
        var raw = new ByteArrayOutputStream();
        raw.write(new byte[] {(byte) 0xd6, (byte) 0xd0, '\r', '\n'});
        raw.write(("[INFO] Reactor Summary for CK3 Control:\r\n"
                + "[INFO] parent .... SUCCESS [ 0.1 s]\r\n"
                + "[ERROR] broken .... FAILURE [ 0.2 s]\r\n"
                + "[INFO] downstream .... SKIPPED\r\n"
                + "[ERROR] BUILD FAILURE\r\n").getBytes(StandardCharsets.US_ASCII));
        raw.write(new byte[] {(byte) 0xd6, (byte) 0xd0, '\r', '\n'});
        assertEquals(List.of(new Full35CompileOnly.ReactorSummary("parent", "SUCCESS"),
                new Full35CompileOnly.ReactorSummary("broken", "FAILURE"),
                new Full35CompileOnly.ReactorSummary("downstream", "SKIPPED")),
                Full35CompileOnly.reactorSummary(write("raw.stdout.log", raw.toByteArray())));
    }

    @Test void existingAnsiAsciiProtocolIsAcceptedWithoutDecodingOtherBytes() throws Exception {
        String raw = "\u001b[0m[INFO] Reactor Summary for CK3 Control:\r\n"
                + "\u001b[32m[INFO] module .... SUCCESS [ 0.1 s]\u001b[0m\r\n"
                + "\u001b[0m[INFO] BUILD SUCCESS\r\n";
        assertEquals(List.of(new Full35CompileOnly.ReactorSummary("module", "SUCCESS")),
                Full35CompileOnly.reactorSummary(write("ansi.stdout.log",
                        raw.getBytes(StandardCharsets.US_ASCII))));
    }

    @Test void nonAsciiReactorFieldIsRejectedWithItsActualRawPin() throws Exception {
        byte[] raw = ("[INFO] Reactor Summary for CK3 Control:\n"
                + "[ERROR] module .... FAILURE\n[ERROR] BUILD FAILURE\n").getBytes(StandardCharsets.US_ASCII);
        int index = "[INFO] Reactor Summary for CK3 Control:\n[ERROR] ".length();
        raw[index] = (byte) 0xd6; raw[index + 1] = (byte) 0xd0;
        var ref = write("non-ascii.stdout.log", raw);
        IOException rejected = assertThrows(IOException.class, () -> Full35CompileOnly.reactorSummary(ref));
        assertTrue(rejected.getMessage().contains("Non-ASCII reactor protocol"));
        assertTrue(rejected.getMessage().contains(ref.sha256()));
    }

    @Test void duplicateSummariesRemainRejected() throws Exception {
        var ref = write("duplicate.stdout.log", ("[INFO] Reactor Summary:\n[INFO] a .... SUCCESS\n"
                + "[INFO] BUILD SUCCESS\n[INFO] Reactor Summary:\n[INFO] b .... SUCCESS\n"
                + "[INFO] BUILD SUCCESS\n").getBytes(StandardCharsets.US_ASCII));
        assertThrows(IOException.class, () -> Full35CompileOnly.reactorSummary(ref));
    }

    @Test void moreThanThirtyFiveActualRowsRemainRejected() throws Exception {
        var text = new StringBuilder("[INFO] Reactor Summary:\n");
        for (int index = 0; index < 36; index++) text.append("[INFO] module").append(index).append(" .... SUCCESS\n");
        text.append("[INFO] BUILD SUCCESS\n");
        var ref = write("oversized-rows.stdout.log", text.toString().getBytes(StandardCharsets.US_ASCII));
        assertThrows(IOException.class, () -> Full35CompileOnly.reactorSummary(ref));
    }

    @Test void changedRawInputIsRejectedBeforeItsFieldsCanBeAccepted() throws Exception {
        var ref = write("changed.stdout.log", "[INFO] Reactor Summary:\n[INFO] a .... SUCCESS\n"
                .getBytes(StandardCharsets.US_ASCII));
        Files.writeString(Path.of(ref.path()), "[INFO] Reactor Summary:\n[INFO] b .... SUCCESS\n",
                StandardCharsets.US_ASCII);
        assertThrows(IOException.class, () -> Full35CompileOnly.reactorSummary(ref));
    }

    private ControlBuild.FileRef write(String name, byte[] raw) throws IOException {
        Path output = temporary.resolve(name); Files.write(output, raw);
        return ControlBuild.FileRef.measure(output);
    }
}
