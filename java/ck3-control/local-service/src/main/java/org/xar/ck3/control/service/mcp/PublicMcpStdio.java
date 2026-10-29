package org.xar.ck3.control.service.mcp;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.time.Duration;
import java.util.Arrays;
import java.util.Objects;

/** NDJSON framing over the existing process. No content-length protocol, service launch, or Python fallback. */
public final class PublicMcpStdio {
    public record Exit(int code, long completedCalls, int unresolvedCalls, String reason) { }
    private PublicMcpStdio() { }
    public static Exit run(PublicMcpDirectory directory, InputStream input, OutputStream output, Duration drainLimit) {
        Objects.requireNonNull(input); Objects.requireNonNull(output);
        PublicMcpSession session = new PublicMcpSession(directory, line -> { output.write(line); output.flush(); });
        int code = 0; String reason = "stdio input closed and actual calls drained";
        try {
            ByteArrayOutputStream line = new ByteArrayOutputStream(); byte[] chunk = new byte[8192]; int count;
            while ((count = input.read(chunk)) >= 0) {
                if (count == 0) continue;
                for (int index = 0; index < count; index++) {
                    byte value = chunk[index];
                    if (value == '\n') {
                        byte[] payload = line.toByteArray(); line.reset();
                        if (payload.length > 0 && payload[payload.length - 1] == '\r') payload = Arrays.copyOf(payload, payload.length - 1);
                        session.receive(payload);
                    } else {
                        if (line.size() >= McpJson.INPUT_MAX) throw new IOException("MCP input line exceeds its finite envelope limit");
                        line.write(value);
                    }
                }
                if (session.outputFailure().isPresent()) throw session.outputFailure().orElseThrow();
            }
            if (line.size() != 0) { code = 65; reason = "unterminated MCP frame at EOF; that frame was not dispatched"; }
        } catch (IOException failure) { code = 74; reason = "stdio I/O failed: " + failure.getMessage(); }
        catch (RuntimeException failure) { code = 70; reason = "stdio adapter failed: " + failure.getClass().getName(); }
        try {
            PublicMcpSession.Drain drained = session.closeAndDrain(drainLimit);
            if (!drained.complete()) return new Exit(75, drained.completedCalls(), drained.unresolvedCalls(), "application calls unresolved at shutdown; world outcome unconfirmed; do not resend");
            if (session.outputFailure().isPresent()) return new Exit(74, drained.completedCalls(), 0, "response write failed; client delivery unconfirmed; do not resend world actions");
            return new Exit(code, drained.completedCalls(), 0, reason);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return new Exit(75, 0, -1, "stdio shutdown interrupted; application/world outcome unconfirmed; do not resend");
        }
    }
}
