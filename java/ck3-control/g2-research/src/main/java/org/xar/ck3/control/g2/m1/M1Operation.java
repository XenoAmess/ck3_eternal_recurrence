package org.xar.ck3.control.g2.m1;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** The single public contract for the eight M1 application operations. */
public enum M1Operation {
    SAVED_MEMBERSHIP("saved-membership"), REALM_FEEDBACK("realm-feedback"),
    MONTHLY_OBSERVATION("monthly-observation"), NATIVE_DIFFERENCE("native-difference"),
    NATIVE_CACHE("native-cache"), MONTHLY_CACHE("monthly-cache"),
    SAVED_DIFFERENCE("saved-difference"), DATED_SUMMARY("dated-summary");

    private final String wire;
    M1Operation(String wire) { this.wire = wire; }
    public String wire() { return wire; }

    public static M1Operation parse(String wire) {
        for (M1Operation operation : values()) {
            if (operation.wire.equals(wire)) { return operation; }
        }
        throw new ContractViolationException("unknown M1 operation");
    }

    /** Preserve the original input token bytes, including decimal and uint64 tokens. */
    public ProjectionJson payload(byte[] originalInputJson) {
        Objects.requireNonNull(originalInputJson, "original M1 input bytes");
        ProjectionJson.object(originalInputJson, M1Research.MAX_BYTES);
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        output.writeBytes(("{\"operation\":\"" + wire + "\",\"input\":").getBytes(StandardCharsets.UTF_8));
        output.writeBytes(originalInputJson);
        output.write('}');
        return ProjectionJson.object(output.toByteArray(), M1Research.MAX_BYTES);
    }
}
