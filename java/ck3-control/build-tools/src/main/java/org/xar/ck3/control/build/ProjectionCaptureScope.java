package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Explicit request-bound capture scope; source qualification grants neither production nor Game authority. */
public final class ProjectionCaptureScope {
    public enum Qualification { FULL_SOFTWARE, TEST_COMPILED_CAPTURE_ONLY }
    public static final String SCHEMA = "xar.java-projection-capture-scope/v1";
    public static final int MAX_SCOPE_BYTES = 1 << 20;
    private ProjectionCaptureScope() {}

    public record Request(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
            List<ControlBuild.FileRef> requestRefs, List<String> operations) {
        public Request {
            requestRefs = List.copyOf(requestRefs); operations = List.copyOf(operations);
            Instant observed = Instant.parse(observedAtUtc), review = Instant.parse(reviewAtUtc);
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")
                    || !review.isAfter(observed)
                    || requestRefs.isEmpty() || requestRefs.size() > 256 || operations.isEmpty() || operations.size() > 256
                    || requestRefs.stream().map(ControlBuild.FileRef::path).distinct().count() != requestRefs.size()
                    || operations.stream().distinct().count() != operations.size()
                    || operations.stream().anyMatch(wire -> wire == null || wire.length() > 128 || !wire.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)*"))) {
                throw new IllegalArgumentException("Exact finite actual capture requests and operation wires required");
            }
        }
    }

    public record Bound(ControlBuild.FileRef scopeRef, Request request) {
        public Bound {
            Objects.requireNonNull(scopeRef); Objects.requireNonNull(request);
            if (scopeRef.bytes() < 1 || scopeRef.bytes() > MAX_SCOPE_BYTES) throw new IllegalArgumentException("Bounded capture scope reference required");
        }
        public void verify() throws IOException {
            byte[] raw = readBounded(Path.of(scopeRef.path()));
            if (raw.length != scopeRef.bytes() || !sha256(raw).equals(scopeRef.sha256())
                    || !ControlBuild.strictMapper().readValue(raw, Request.class).equals(request)) {
                throw new IOException("Capture scope raw bytes, reference and typed request must agree");
            }
            scopeRef.verify();
            for (ControlBuild.FileRef actualRequest : request.requestRefs()) actualRequest.verify();
            Instant now = Instant.now();
            if (Instant.parse(request.observedAtUtc()).isAfter(now.plusSeconds(5))
                    || !now.isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("Capture request scope not current");
        }
        public void requireCatalog(ProjectionDeploymentProof.Attestation actual) throws IOException {
            Set<String> advertised = new HashSet<>(actual.identity().operations().stream().map(ProjectionDeploymentProof.OperationProfile::operation).toList());
            if (!advertised.containsAll(request.operations())) throw new IOException("Capture operation absent from actual qualified host");
        }
    }

    public static Bound read(Path path, String machine) throws IOException {
        byte[] raw = readBounded(path);
        ControlBuild.FileRef ref = new ControlBuild.FileRef(path.toAbsolutePath().normalize().toString(), raw.length, sha256(raw));
        Request request = ControlBuild.strictMapper().readValue(raw, Request.class);
        Instant now = Instant.now();
        if (!machine.equals(request.machineId()) || Instant.parse(request.observedAtUtc()).isAfter(now.plusSeconds(5))
                || !now.isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("Current same-machine finite capture scope required");
        Bound result = new Bound(ref, request); result.verify(); return result;
    }
    private static byte[] readBounded(Path path) throws IOException {
        byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(MAX_SCOPE_BYTES + 1); }
        if (raw.length < 1 || raw.length > MAX_SCOPE_BYTES) throw new IOException("Bounded actual capture scope required");
        return raw;
    }

    private static String sha256(byte[] raw) {
        try { return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
