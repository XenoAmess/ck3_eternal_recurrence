package org.xar.ck3.control.wave2.runtime.creationtime;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.ContractViolationException;

/** Explicit test pipe for local original-consumer differential, not a service or native transport. */
public final class CreationTimeProbe {
    private CreationTimeProbe() { }
    public static void main(String[] args) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream(); int value;
        while ((value = System.in.read()) != -1) {
            if (value != '\n') { if (line.size() >= 65536) { throw new IOException("creation time test line cap"); } line.write(value); continue; }
            byte[] output;
            try { output = CreationTimeCodec.evaluate(line.toByteArray()); }
            catch (ContractViolationException error) { output = "{\"test_transport_status\":\"invalid_contract\"}".getBytes(StandardCharsets.UTF_8); }
            System.out.write(output); System.out.write('\n'); System.out.flush(); line.reset();
        }
        if (line.size() != 0) { throw new IOException("unterminated test line"); }
    }
}
