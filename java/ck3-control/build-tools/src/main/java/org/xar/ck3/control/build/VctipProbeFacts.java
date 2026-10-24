package org.xar.ck3.control.build;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Domain interpretation only. Process execution belongs to the admitted shared owned-command launcher. */
public final class VctipProbeFacts {
    private VctipProbeFacts() { }
    public static final ControlBuild.FileRef VENDOR = new ControlBuild.FileRef(
            "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/vctip.exe",
            514528, "7775ba4e0e0b03de15caefc1b92e63acc0a3dd9e388648f5489c777dfdbaadc8");
    public enum ProbeCase { HELP, IDLE_ONE, IDLE_TWO }
    public enum Observation { HELP_OBSERVED, NATURAL_ZERO_EXIT_OBSERVED, RED }
    public enum Qualification { NONE }
    public record Analysis(ProbeCase probeCase, Observation observation, Qualification qualification,
            double elapsedSeconds, boolean mayRequestNextSyntheticCase, String boundary) { }
    public static List<String> arguments(ProbeCase probeCase) {
        return switch (probeCase) {
            case HELP -> List.of("-?");
            case IDLE_ONE -> List.of("-timeout:1");
            case IDLE_TWO -> List.of("-timeout:2");
        };
    }
    public static Analysis analyze(ProbeCase probeCase, WindowsJobProcess.CommandResult result,
            byte[] stdout, byte[] stderr) {
        if (probeCase == null || result == null || stdout == null || stderr == null
                || stdout.length > 65536 || stderr.length > 65536) throw new IllegalArgumentException("bounded exact probe facts required");
        boolean settled = result.stopReason() == null && result.accounting().activeProcesses() == 0
                && Path.of(result.identity().executable()).toAbsolutePath().normalize()
                        .equals(Path.of(VENDOR.path()).toAbsolutePath().normalize())
                && result.accounting().memoryLimitBytes() == 268435456
                && result.accounting().peakJobMemoryBytes() <= result.accounting().memoryLimitBytes()
                && result.accounting().limitFlags() == 8704;
        Observation observation = Observation.RED;
        if (probeCase == ProbeCase.HELP && settled && (result.exitCode() == 0 || result.exitCode() == 1)
                && (helpContract(stdout) || helpContract(stderr))) observation = Observation.HELP_OBSERVED;
        else if (probeCase != ProbeCase.HELP && settled && result.passed()
                && idleTimeoutObserved(probeCase, result.elapsedSeconds(), stdout, stderr)) {
            observation = Observation.NATURAL_ZERO_EXIT_OBSERVED;
        }
        return new Analysis(probeCase, observation, Qualification.NONE, result.elapsedSeconds(),
                observation != Observation.RED && probeCase != ProbeCase.IDLE_TWO,
                "Synthetic terminal observation only; compiler reuse and production cohort remain unqualified.");
    }
    private static boolean helpContract(byte[] bytes) {
        return helpContract(bytes, StandardCharsets.US_ASCII) || helpContract(bytes, StandardCharsets.UTF_16LE);
    }
    private static boolean helpContract(byte[] bytes, java.nio.charset.Charset charset) {
        return contains(bytes, "Usage: VCTIP [options]".getBytes(charset))
                && contains(bytes, "-timeout:<seconds>".getBytes(charset))
                && contains(bytes, "Specify server timeout in seconds (0 = disable timeout)".getBytes(charset));
    }
    private static boolean idleTimeoutObserved(ProbeCase probeCase, double elapsed, byte[] stdout, byte[] stderr) {
        int seconds = switch (probeCase) { case IDLE_ONE -> 1; case IDLE_TWO -> 2; case HELP -> throw new IllegalArgumentException("idle case required"); };
        String marker = "Telemetry service timeout: " + seconds + "s";
        return elapsed >= seconds && elapsed < 30
                && (contains(stdout, marker.getBytes(StandardCharsets.US_ASCII))
                    || contains(stderr, marker.getBytes(StandardCharsets.US_ASCII)))
                && (contains(stdout, "Starting telemetry reporting service".getBytes(StandardCharsets.US_ASCII))
                    || contains(stderr, "Starting telemetry reporting service".getBytes(StandardCharsets.US_ASCII)));
    }
    private static boolean contains(byte[] bytes, byte[] marker) {
        for (int offset = 0; offset <= bytes.length - marker.length; offset++) {
            int index = 0; while (index < marker.length && bytes[offset + index] == marker[index]) index++;
            if (index == marker.length) return true;
        }
        return false;
    }
    /** Synthetic value objects only; no native library call, process, compiler or vendor launch. */
    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("pure domain self-check accepts no runtime inputs");
        var identity = new WindowsJobProcess.ProcessIdentity(17, "1", VENDOR.path());
        var empty = new WindowsJobProcess.Accounting(1024, 0, 268435456, 8704);
        var live = new WindowsJobProcess.Accounting(1024, 1, 268435456, 8704);
        byte[] help = "Usage: VCTIP [options]\n-timeout:<seconds> Specify server timeout in seconds (0 = disable timeout)".getBytes(StandardCharsets.US_ASCII), none = new byte[0];
        check(analyze(ProbeCase.HELP, new WindowsJobProcess.CommandResult(identity, 1, .1, empty, null), help, none).observation() == Observation.HELP_OBSERVED);
        check(analyze(ProbeCase.HELP, new WindowsJobProcess.CommandResult(identity, 0, .1, empty, null), none, none).observation() == Observation.RED);
        check(analyze(ProbeCase.HELP, new WindowsJobProcess.CommandResult(identity, 0, 30, empty, "timeout_or_release_expired"), help, none).observation() == Observation.RED);
        check(analyze(ProbeCase.HELP, new WindowsJobProcess.CommandResult(identity, 0, .1, live, null), help, none).observation() == Observation.RED);
        byte[] idle = "Telemetry service timeout: 1s\nStarting telemetry reporting service...".getBytes(StandardCharsets.US_ASCII);
        Analysis natural = analyze(ProbeCase.IDLE_ONE, new WindowsJobProcess.CommandResult(identity, 0, 1.1, empty, null), idle, none);
        check(natural.observation() == Observation.NATURAL_ZERO_EXIT_OBSERVED && natural.qualification() == Qualification.NONE);
        check(analyze(ProbeCase.IDLE_TWO, new WindowsJobProcess.CommandResult(identity, 1, .1, empty, null), help, none).observation() == Observation.RED);
        check(analyze(ProbeCase.IDLE_ONE, new WindowsJobProcess.CommandResult(identity, 0, .1, empty, null), idle, none).observation() == Observation.RED);
        var unrelated = new WindowsJobProcess.ProcessIdentity(18, "2", "D:/synthetic/other.exe");
        check(analyze(ProbeCase.IDLE_ONE, new WindowsJobProcess.CommandResult(unrelated, 0, 1.1, empty, null), idle, none).observation() == Observation.RED);
        System.out.println("synthetic_domain_checks=8 PASS vendor_launches=0 production_qualification=NONE");
    }
    private static void check(boolean condition) { if (!condition) throw new AssertionError("synthetic probe interpretation failed"); }
}
