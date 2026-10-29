package org.xar.ck3.control.wave2.finance.holyloan;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/** Offline test stream; no native query, service, pending intent, or wallet write. */
public final class HolyLoanProbe {
    private HolyLoanProbe() { }
    public static void main(String[] args) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream(); int next;
        while ((next = System.in.read()) != -1) {
            if (next != '\n') { if (line.size() >= 65536) { throw new IOException("bounded request required"); } line.write(next); continue; }
            try { System.out.write(HolyLoanHarness.evaluate(line.toByteArray())); }
            catch (IllegalArgumentException error) { System.out.write("{\"test_transport_status\":\"invalid_contract\"}".getBytes(StandardCharsets.UTF_8)); }
            System.out.write('\n'); System.out.flush(); line.reset();
        }
        if (line.size() != 0) { throw new IOException("incomplete test request"); }
    }
}
