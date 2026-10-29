package org.xar.ck3.control.wave3.runtime.timelineowner;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/** Test-only bounded pipe to the actual Java codec; owns no native or action capability. */
public final class TimelineOwnerProbe {
    static final int MAX_REQUEST_BYTES = 32 * 1024;
    private static final byte[] INVALID = "{\"test_transport_status\":\"invalid_contract\"}".getBytes(StandardCharsets.US_ASCII);

    private TimelineOwnerProbe() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 0) { throw new IllegalArgumentException("timeline owner probe has no arguments"); }
        run(System.in, System.out);
    }

    static void run(InputStream input, OutputStream output) throws IOException {
        byte[] request;
        while ((request = request(input)) != null) {
            byte[] response;
            try { response = TimelineOwnerCodec.encode(TimelineOwnerCodec.assess(request)); }
            catch (IllegalArgumentException error) { response = INVALID; }
            output.write(response); output.write('\n'); output.flush();
        }
    }

    private static byte[] request(InputStream input) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        int value;
        while ((value = input.read()) != -1) {
            if (value == '\n') { return line.toByteArray(); }
            if (line.size() == MAX_REQUEST_BYTES) { throw new IOException("timeline owner probe request exceeds32KiB"); }
            line.write(value);
        }
        if (line.size() != 0) { throw new IOException("timeline owner probe request lacks final LF"); }
        return null;
    }
}
