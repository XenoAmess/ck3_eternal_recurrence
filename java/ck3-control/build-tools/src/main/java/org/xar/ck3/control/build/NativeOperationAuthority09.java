package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.HexFormat;
import java.util.Objects;

/** Read-only continuation preparation. Ordinary launcher09 supplies no native execution authority. */
public final class NativeOperationAuthority09 {
    private static final Path J = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1");
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final List<ControlBuild.FileRef> HISTORY = List.of(
            ref("build/resume56-20261023/native-vendor16/native_fixture09/help05/terminal.json", 6941,
                    "ef2863c72d90d3b83acdeb5a52889fda4d4b08567fe6e5e7c4549eaf35ddc69d"),
            ref("build/resume56-20261023/native-vendor16/case-0-start.json", 607,
                    "f7323461d5bdddb9e53585811e5748f274c56797b8d87c42b4c5948217d79e16"),
            ref("scratch/resume56-20261023/native-lifecycle-next01/VENDOR-HELP05-SPEC.json", 2158,
                    "ae774971848e68f5820cfafd61828bd9a4027035393218972e3de9223503589f"),
            ref("build/resume56-20261023/native-vendor16/native_fixture09/idle-one07/terminal.json", 5760,
                    "a3cf511dbb84084dcee8d6deb797d94f0076d3392a4c29da506143db150b3340"),
            ref("scratch/resume56-20261023/native-lifecycle-next01/VENDOR-IDLEONE07-SPEC.json", 2174,
                    "8e6e290f71603853fb9d7d32a4b3f4bb239adbf6ccb6e1c60b1f5ce38155fb0b"));
    private static final ControlBuild.FileRef HELP_STDOUT = ref(
            "build/resume56-20261023/native-vendor16/native_fixture09/help05/stdout.log", 779,
            "1009bbd252b2ebb0a99e6372aa6c379153ed41d49e74d9c844dfe97019f8340f");
    private static final ControlBuild.FileRef HELP_STDERR = ref(
            "build/resume56-20261023/native-vendor16/native_fixture09/help05/stderr.log", 0,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");

    /** Identical immutable evidence bytes may be transported as CI resources; they grant no native identity. */
    public record OriginalEvidence(ControlBuild.FileRef originalRef, byte[] rawBytes) {
        public OriginalEvidence {
            Objects.requireNonNull(originalRef); Objects.requireNonNull(rawBytes); rawBytes = rawBytes.clone();
            if (rawBytes.length > 65536 || rawBytes.length != originalRef.bytes() || !sha(rawBytes).equals(originalRef.sha256()))
                throw new IllegalArgumentException("exact original evidence bytes required");
        }
        @Override public byte[] rawBytes() { return rawBytes.clone(); }
    }
    public record OriginalHistory(OriginalEvidence helpTerminal, OriginalEvidence seriesStart,
            OriginalEvidence helpRequest, OriginalEvidence caseOneRejection, OriginalEvidence caseOneRequest,
            OriginalEvidence helpStdout, OriginalEvidence helpStderr) {
        public OriginalHistory {
            for (OriginalEvidence value : List.of(helpTerminal, seriesStart, helpRequest, caseOneRejection,
                    caseOneRequest, helpStdout, helpStderr)) Objects.requireNonNull(value);
        }
    }

    public enum PreparationStatus { PREPARED_NOT_AUTHORIZED }
    public enum UnavailableReason { ORDINARY09_HAS_NO_NATIVE_QUALIFICATION }
    public record CaseRequest(int originalIndex, VctipProbeFacts.ProbeCase probeCase,
            ControlBuild.FileRef executableRef, List<String> arguments, long memoryLimitBytes,
            int timeoutSeconds) {
        public CaseRequest {
            Objects.requireNonNull(probeCase); Objects.requireNonNull(executableRef);
            arguments = List.copyOf(arguments);
            if ((originalIndex != 1 && originalIndex != 2)
                    || probeCase != (originalIndex == 1 ? VctipProbeFacts.ProbeCase.IDLE_ONE : VctipProbeFacts.ProbeCase.IDLE_TWO)
                    || !executableRef.equals(VctipProbeFacts.VENDOR)
                    || !arguments.equals(VctipProbeFacts.arguments(probeCase))
                    || memoryLimitBytes != 268435456 || timeoutSeconds != 30) {
                throw new IllegalArgumentException("only original supported finite vendor cases1/2 may be prepared");
            }
        }
    }
    public record PreparedContinuation(String schema, String machineId, PreparationStatus status,
            UnavailableReason executionUnavailableReason, String originalSeriesStartedAtUtc,
            String originalSeriesDeadlineAtUtc, List<ControlBuild.FileRef> historicalRefs,
            List<CaseRequest> cases, int totalTimeoutSeconds, String requiredProviderSeam) {
        public PreparedContinuation { historicalRefs = List.copyOf(historicalRefs); cases = List.copyOf(cases); }
    }

    private NativeOperationAuthority09() { }

    public static List<ControlBuild.FileRef> originalEvidenceRefs() {
        List<ControlBuild.FileRef> refs = new ArrayList<>(HISTORY); refs.add(HELP_STDOUT); refs.add(HELP_STDERR);
        return List.copyOf(refs);
    }

    public static PreparedContinuation prepareOriginalUnexecutedCases() throws IOException {
        return prepareOriginalUnexecutedCases(new OriginalHistory(load(HISTORY.get(0)), load(HISTORY.get(1)),
                load(HISTORY.get(2)), load(HISTORY.get(3)), load(HISTORY.get(4)), load(HELP_STDOUT), load(HELP_STDERR)));
    }

    /** Shared producer boundary for original files and exact portable evidence copies. */
    public static PreparedContinuation prepareOriginalUnexecutedCases(OriginalHistory original) throws IOException {
        List<OriginalEvidence> evidence = List.of(original.helpTerminal(), original.seriesStart(), original.helpRequest(),
                original.caseOneRejection(), original.caseOneRequest(), original.helpStdout(), original.helpStderr());
        List<ControlBuild.FileRef> expected = originalEvidenceRefs();
        for (int index = 0; index < expected.size(); index++)
            require(expected.get(index).equals(evidence.get(index).originalRef()), "original history ref/order changed");
        JsonNode help = read(original.helpTerminal()), start = read(original.seriesStart()), rejected = read(original.caseOneRejection());
        require(MACHINE.equals(text(help, "machine_id")) && MACHINE.equals(text(start, "machine_id"))
                && MACHINE.equals(text(rejected, "machine_id")), "original history machine changed");
        require("RED".equals(text(help, "status")) && help.path("child_started").isBoolean()
                && help.path("child_started").booleanValue(), "original HELP terminal changed");
        var result = ControlBuild.strictMapper().treeToValue(help.get("child"), WindowsJobProcess.CommandResult.class);
        ControlBuild.FileRef stdout = ControlBuild.strictMapper().treeToValue(help.get("stdout_ref"), ControlBuild.FileRef.class);
        ControlBuild.FileRef stderr = ControlBuild.strictMapper().treeToValue(help.get("stderr_ref"), ControlBuild.FileRef.class);
        require(stdout.equals(HELP_STDOUT) && stderr.equals(HELP_STDERR), "original HELP stream refs changed");
        require(VctipProbeFacts.analyze(VctipProbeFacts.ProbeCase.HELP, result,
                original.helpStdout().rawBytes(), original.helpStderr().rawBytes()).observation()
                        == VctipProbeFacts.Observation.HELP_OBSERVED, "original natural HELP usage proof unavailable");
        require("REJECTED".equals(text(rejected, "status")) && rejected.path("child_started").isBoolean()
                && !rejected.path("child_started").booleanValue() && rejected.path("child").isNull()
                && "IOException: vendor series total120s elapsed".equals(text(rejected, "failure")),
                "case1 was not an original prelaunch expiry rejection");
        for (JsonNode terminal : List.of(help, rejected)) for (String key : List.of("input_precheck", "input_postcheck", "runtime_postcheck"))
            require("MATCH".equals(text(terminal, key)), "original terminal input/runtime guard changed");
        String began = text(start, "observed_at_utc");
        require("2026-10-22T21:49:00.208023300Z".equals(began), "original series start may not be rewritten");
        String ended = java.time.Instant.parse(began).plusSeconds(120).toString();
        require(java.time.Instant.parse(text(rejected, "observed_at_utc")).isAfter(java.time.Instant.parse(ended)),
                "original series was not expired before rejected case1");
        List<ControlBuild.FileRef> closure = originalEvidenceRefs();
        List<CaseRequest> cases = List.of(caseRequest(1), caseRequest(2));
        return new PreparedContinuation("xar.native-vendor-continuation-preparation/v1", MACHINE,
                PreparationStatus.PREPARED_NOT_AUTHORIZED, UnavailableReason.ORDINARY09_HAS_NO_NATIVE_QUALIFICATION,
                began, ended, closure, cases, 120,
                "Fresh Root native operation card plus qualified sole shared launcher/native provider integration; "
                        + "synthetic timeout observations do not qualify CMake/compiler reuse or CONFIGURE drain.");
    }

    public static CaseRequest caseRequest(int originalIndex) {
        VctipProbeFacts.ProbeCase probe = switch (originalIndex) {
            case 1 -> VctipProbeFacts.ProbeCase.IDLE_ONE;
            case 2 -> VctipProbeFacts.ProbeCase.IDLE_TWO;
            default -> throw new IllegalArgumentException("HELP is already observed; only original indices1/2 remain");
        };
        return new CaseRequest(originalIndex, probe, VctipProbeFacts.VENDOR,
                VctipProbeFacts.arguments(probe), 268435456, 30);
    }

    private static ControlBuild.FileRef ref(String path, long bytes, String sha256) {
        return new ControlBuild.FileRef(J.resolve(path).toString(), bytes, sha256);
    }
    private static OriginalEvidence load(ControlBuild.FileRef ref) throws IOException {
        require(ref.bytes() <= 65536, "bounded original history required"); ref.verify();
        return new OriginalEvidence(ref, Files.readAllBytes(Path.of(ref.path())));
    }
    private static JsonNode read(OriginalEvidence evidence) throws IOException {
        JsonNode value = ControlBuild.strictMapper().readTree(evidence.rawBytes());
        require(value != null && value.isObject(), "original history object required"); return value;
    }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); }
    }
    private static String text(JsonNode object, String key) throws IOException {
        JsonNode value = object == null ? null : object.get(key);
        require(value != null && value.isTextual(), "original history text required: " + key); return value.textValue();
    }
    private static void require(boolean value, String message) throws IOException { if (!value) throw new IOException(message); }
}
