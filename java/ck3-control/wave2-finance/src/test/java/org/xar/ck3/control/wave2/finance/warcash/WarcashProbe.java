package org.xar.ck3.control.wave2.finance.warcash;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Offline test pipe only; neither a native RPC nor a new service. */
public final class WarcashProbe {
    private WarcashProbe() { }
    public static void main(String[] arguments) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream(); int next;
        while ((next = System.in.read()) != -1) {
            if (next != '\n') { if (line.size() >= StrictJson.INPUT_MAX_BYTES) { throw new IOException("request too large"); } line.write(next); continue; }
            try { System.out.write(WarcashCodec.evaluate(line.toByteArray())); }
            catch (ContractViolationException error) { System.out.write("{\"test_transport_status\":\"invalid_contract\"}".getBytes(StandardCharsets.UTF_8)); }
            System.out.write('\n'); System.out.flush(); line.reset();
        }
        if (line.size() != 0) { throw new IOException("incomplete request line"); }
    }
}
