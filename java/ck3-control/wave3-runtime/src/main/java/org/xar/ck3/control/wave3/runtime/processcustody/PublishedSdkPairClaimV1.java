package org.xar.ck3.control.wave3.runtime.processcustody;

import java.util.List;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;

/** Published metadata only; actual handle captures independently validate both generations. */
public record PublishedSdkPairClaimV1(List<Row> processes, String originalSha256) {
    public enum Role {
        SDK_QUEUE("sdk_queue"), SDK_APPLICATION("sdk_application");
        private final String wire;
        Role(String wire) { this.wire = wire; }
        public String wireValue() { return wire; }
        public static Role fromWire(String value) {
            for (Role role : values()) { if (role.wire.equals(value)) { return role; } }
            throw new ContractViolationException("exact published SDK role required");
        }
    }

    public record Row(Role role, ProcessIdentityClaimV1 identity) {
        public Row {
            StrictJson.require(role != null && identity != null, "typed published SDK identity required");
        }
    }

    public PublishedSdkPairClaimV1 {
        StrictJson.require(processes != null && processes.size() == 2, "exact two published SDK identities required");
        processes = List.copyOf(processes);
        StrictJson.require(processes.get(0).role() != processes.get(1).role(),
                "one Queue and one Application row required");
        StrictJson.require(originalSha256 != null && originalSha256.matches("[0-9a-f]{64}"),
                "original metadata SHA-256 required");
    }
}
