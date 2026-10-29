package org.xar.ck3.control.wave3.runtime.processcustody;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.LegacyProcessIdentityCodecV1;
import org.xar.ck3.control.wave3.runtime.processcustody.PublishedSdkPairClaimV1.Role;
import org.xar.ck3.control.wave3.runtime.processcustody.PublishedSdkPairClaimV1.Row;

/** Explicit projection of the extensible original SDK-pair container, with original-byte digest. */
public final class PublishedSdkPairCodecV1 {
    private static final Set<String> IDENTITY_FIELDS = Set.of("role", "pid", "creation_filetime", "executable");

    private PublishedSdkPairCodecV1() { }

    public static PublishedSdkPairClaimV1 decode(byte[] raw) {
        JsonNode root = StrictJson.parse(raw);
        StrictJson.require(root.isObject(), "published SDK pair object required");
        StrictJson.require(root.has("status") && root.get("status").isTextual()
                && root.get("status").textValue().equals("SDK_PAIR_HANDLES_RETAINED"),
                "exact original published SDK pair marker required");
        JsonNode rows = root.get("processes");
        StrictJson.require(rows != null && rows.isArray() && rows.size() == 2,
                "exact two original SDK process rows required");
        List<Row> processes = new ArrayList<>(2);
        for (JsonNode row : rows) {
            StrictJson.require(row.isObject(), "published SDK identity object required");
            ObjectNode selected = StrictJson.object();
            for (String field : IDENTITY_FIELDS) {
                StrictJson.require(row.has(field), "required published SDK identity field: " + field);
                selected.set(field, row.get(field));
            }
            // This integer-only emitter deliberately rejects an original float token
            // before a normalized JSON tree can accidentally re-emit 1.0 as 1.
            var identity = LegacyProcessIdentityCodecV1.decode(StrictJson.canonical(selected));
            processes.add(new Row(Role.fromWire(identity.role()), identity.identity()));
        }
        try {
            return new PublishedSdkPairClaimV1(processes,
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("required SHA-256 unavailable", error);
        }
    }
}
