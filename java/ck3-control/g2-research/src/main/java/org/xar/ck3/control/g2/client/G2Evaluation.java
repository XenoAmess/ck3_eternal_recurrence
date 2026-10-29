package org.xar.ck3.control.g2.client;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;

/** Pure response, original HTTP bytes and actual evidence; no commit, writer or Game permission. */
public record G2Evaluation(G2Response response, G2CallEvidence evidence, byte[] responseBytes) {
    public G2Evaluation {
        Objects.requireNonNull(response, "response");
        Objects.requireNonNull(evidence, "evidence");
        responseBytes = Objects.requireNonNull(responseBytes, "responseBytes").clone();
        if (!evidence.actualHttpInvoked() || !evidence.responseComplete()
                || evidence.httpStatus().orElse(-1) != 200
                || !response.requestId().equals(evidence.requestId())
                || responseBytes.length != evidence.retainedResponseBytes()
                || !sha256(responseBytes).equals(evidence.retainedResponseSha256())) {
            throw new IllegalArgumentException("complete successful actual HTTP bytes and matching evidence required");
        }
        G2Response decoded = G2Wire.decodeResponse(responseBytes);
        if (!response.requestId().equals(decoded.requestId()) || response.milestone() != decoded.milestone()
                || !response.source().equals(decoded.source()) || !Arrays.equals(response.result().bytes(), decoded.result().bytes())) {
            throw new IllegalArgumentException("response must match original complete HTTP body");
        }
    }
    @Override public byte[] responseBytes() { return responseBytes.clone(); }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("required SHA-256 unavailable", error); }
    }
}
