package org.xar.ck3.control.platform;

import java.math.BigInteger;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** One data contract for both original Steam providers. A receipt never reconstructs a live token. */
public final class SteamOfflineObservation {
    private SteamOfflineObservation() { }
    public enum Status { OFFLINE, ONLINE, UNAVAILABLE }
    public enum Method { NATIVE_CURRENT_USER_BYTE, CEF_APP_GETTERS }
    public enum Reason {
        OBSERVED, UNSUPPORTED_PLATFORM, STEAM_NOT_FOUND, AMBIGUOUS_STEAM, SOURCE_NOT_QUALIFIED,
        CDP_NOT_ENABLED, CDP_NOT_OWNED, CDP_UNAVAILABLE, CONTEXT_UNAVAILABLE, INVALID_OBSERVATION,
        STEAM_INSTANCE_CHANGED, NATIVE_QUERY_FAILED
    }
    public record SteamProcess(long pid, String birthFiletime, String executable, String fileVersion) {
        public SteamProcess {
            if (pid < 1 || pid > 0xffff_ffffL) throw new IllegalArgumentException("DWORD Steam PID required");
            decimal(birthFiletime, 64); absolute(executable); text(fileVersion);
        }
    }
    public record Source(String path, long bytes, String sha256, String fileId, String mtimeNanos) {
        public Source {
            absolute(path); digest(sha256); decimal(fileId, 128); decimal(mtimeNanos, 64);
            if (bytes < 1 || bytes > 9_007_199_254_740_991L) throw new IllegalArgumentException("Exact source bytes required");
        }
    }
    public record Endpoint(long pid, String birthFiletime, int port, String targetId, String targetUrl) {
        public Endpoint {
            if (pid < 1 || pid > 0xffff_ffffL || port < 1 || port > 65535) throw new IllegalArgumentException("Owned CEF endpoint identity required");
            decimal(birthFiletime, 64); text(targetId); text(targetUrl);
        }
    }
    public record Common(String machineId, String observedAtUtc, String nonce, Optional<SteamProcess> steam,
            Optional<Source> source, Optional<Endpoint> endpoint, List<String> diagnostics) {
        public Common {
            text(machineId); timestamp(observedAtUtc); text(nonce); Objects.requireNonNull(steam);
            Objects.requireNonNull(source); Objects.requireNonNull(endpoint); diagnostics = List.copyOf(diagnostics);
            if (diagnostics.size() > 256) throw new IllegalArgumentException("Bounded diagnostics required");
            diagnostics.forEach(SteamOfflineObservation::text);
        }
    }
    public record NativeEvidence(String machineId, String observedAtUtc, String nonce, String moduleBase,
            long moduleSize, String valueRva, String valueAddress, String producerRva, String producerAnchorHex,
            String producerAnchorSha256, List<Integer> rawSamples, SteamProcess steamBefore, SteamProcess steamAfter,
            Source sourceBefore, Source sourceAfter, String trayManagerPointerRva, String trayManagerAddress,
            String trayStateOffset, List<Integer> trayStateSamples) {
        public NativeEvidence {
            text(machineId); timestamp(observedAtUtc); text(nonce);
            BigInteger base = decimal(moduleBase, 64), value = decimal(valueRva, 128),
                    address = decimal(valueAddress, 64), producer = decimal(producerRva, 128),
                    managerRva = decimal(trayManagerPointerRva, 128), manager = decimal(trayManagerAddress, 64);
            decimal(trayStateOffset, 128); digest(producerAnchorSha256);
            rawSamples = List.copyOf(rawSamples); trayStateSamples = List.copyOf(trayStateSamples);
            Objects.requireNonNull(steamBefore); Objects.requireNonNull(steamAfter);
            Objects.requireNonNull(sourceBefore); Objects.requireNonNull(sourceAfter);
            if (moduleSize < 1 || moduleSize > 0xffff_ffffL || base.signum() == 0
                    || value.compareTo(BigInteger.valueOf(moduleSize)) >= 0
                    || producer.compareTo(BigInteger.valueOf(moduleSize)) >= 0
                    || !base.add(value).equals(address) || moduleSize < 8
                    || managerRva.compareTo(BigInteger.valueOf(moduleSize - 8)) > 0 || manager.signum() == 0
                    || !trayStateOffset.equals("340") || !steamBefore.equals(steamAfter)
                    || !sourceBefore.equals(sourceAfter) || !rawSamples.equals(List.of(1, 1))
                    || !trayStateSamples.equals(List.of(4, 4)) || producerAnchorHex == null
                    || !producerAnchorHex.matches("(?:[0-9a-f]{2}){1,256}")
                    || !hash(HexFormat.of().parseHex(producerAnchorHex)).equals(producerAnchorSha256)) {
                throw new IllegalArgumentException("Stable complete positive native evidence required");
            }
        }
    }
    public sealed interface Result permits Offline, Online, Unavailable {
        Common common();
        Status status();
    }
    public record Offline(Common common, Method method, Optional<NativeEvidence> nativeEvidence) implements Result {
        public Offline {
            observed(common); Objects.requireNonNull(method); Objects.requireNonNull(nativeEvidence);
            if (method == Method.NATIVE_CURRENT_USER_BYTE) {
                NativeEvidence nativeValue = nativeEvidence.orElseThrow(() -> new IllegalArgumentException("Native evidence missing"));
                if (common.endpoint().isPresent() || !nativeValue.machineId().equals(common.machineId())
                        || !nativeValue.observedAtUtc().equals(common.observedAtUtc()) || !nativeValue.nonce().equals(common.nonce())
                        || !nativeValue.steamBefore().equals(common.steam().orElseThrow())
                        || !nativeValue.sourceBefore().equals(common.source().orElseThrow())) {
                    throw new IllegalArgumentException("Native observation provenance differs");
                }
            } else if (common.endpoint().isEmpty() || nativeEvidence.isPresent()) {
                throw new IllegalArgumentException("Actual CEF endpoint without native evidence required");
            }
        }
        @Override public Status status() { return Status.OFFLINE; }
    }
    public record Online(Common common) implements Result {
        public Online {
            observed(common);
            if (common.endpoint().isEmpty()) throw new IllegalArgumentException("Only an actual CEF getter can observe online");
        }
        @Override public Status status() { return Status.ONLINE; }
    }
    public record Unavailable(Common common, Reason reason) implements Result {
        public Unavailable {
            Objects.requireNonNull(common); Objects.requireNonNull(reason);
            if (reason == Reason.OBSERVED) throw new IllegalArgumentException("Unavailable is not an observed mode");
        }
        @Override public Status status() { return Status.UNAVAILABLE; }
    }
    static BigInteger decimal(String value, int bits) {
        if (value == null || value.length() > 39 || !value.matches("0|[1-9][0-9]*")) throw new IllegalArgumentException("Canonical decimal identity required");
        BigInteger parsed = new BigInteger(value);
        if (parsed.bitLength() > bits) throw new IllegalArgumentException("Identity exceeds its unsigned domain");
        return parsed;
    }
    static void text(String value) {
        if (value == null || value.isEmpty() || value.length() > 32768 || value.indexOf('\0') >= 0) throw new IllegalArgumentException("Bounded text required");
    }
    static void digest(String value) {
        if (value == null || !value.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("Lowercase SHA256 required");
    }
    static void timestamp(String value) {
        text(value);
        if (!(value.endsWith("Z") || value.endsWith("+00:00"))) throw new IllegalArgumentException("UTC observation time required");
        Instant.parse(value);
    }
    private static void absolute(String value) {
        text(value); Path path = Path.of(value);
        boolean windows = value.matches("[A-Za-z]:[\\\\/].*") || value.startsWith("\\\\");
        if (!(path.isAbsolute() || windows)) throw new IllegalArgumentException("Absolute source path required");
        for (String component : value.split("[\\\\/]")) if (component.equals(".") || component.equals("..")) {
            throw new IllegalArgumentException("Normalized absolute source path required");
        }
    }
    private static void observed(Common value) {
        Objects.requireNonNull(value);
        if (value.steam().isEmpty() || value.source().isEmpty()) throw new IllegalArgumentException("Observed state requires process and source");
    }
    static String hash(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
