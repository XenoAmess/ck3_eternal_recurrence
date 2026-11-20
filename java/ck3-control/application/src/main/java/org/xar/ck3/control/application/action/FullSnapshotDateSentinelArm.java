package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Date-only ARM request DATA. No received Full frame, active lease or Native authority is created here. */
public final class FullSnapshotDateSentinelArm {
    public static final String SCHEMA = "ck3_1210_date_sentinel_arm_v1";
    public static final String PREFIX = "research-arm-tactical-daily-sentinel-v1-";

    private FullSnapshotDateSentinelArm() { }

    public static boolean supports(OperationKey operation) {
        Objects.requireNonNull(operation);
        try { dateSpec(operation.value()); return true; }
        catch (IllegalArgumentException unsupported) { return false; }
    }

    /** The actual transport/provider must independently bind the starting date, speed, world and original lease. */
    public static NativeRequest request(String step, String actualSnapshotId,
            BigInteger actualNativeRevision, Instant originalDeadline) {
        return request(ExactCk3Build.CK3_1210,step,actualSnapshotId,actualNativeRevision,originalDeadline);
    }

    /** Exact selected ARM request DATA. The transport still verifies actual Full, owner, capability and deadline. */
    public static NativeRequest request(ExactCk3Build build,String step,String actualSnapshotId,
            BigInteger actualNativeRevision,Instant originalDeadline) {
        requireProfile(build);
        dateSpec(Objects.requireNonNull(step));
        return new NativeRequest(step, ClockStatusRead.ARM_CAP,
                fields(build,actualSnapshotId,actualNativeRevision,originalDeadline));
    }

    public static RawJson additionalFields(ActionCommand command) {
        Objects.requireNonNull(command);
        String step = command.operation().value();
        StrictJson.require(step.startsWith(PREFIX) && command.arguments().members().isEmpty(),
                "argument-free tactical daily sentinel ARM required");
        // Preserve the registered legacy ARM validation and its original empty native fields.
        AdvancePrimitives.armSpec(step);
        ExactCk3Build build=null;
        for(var candidate:java.util.List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580))
            if(candidate.executableSha256().equalsIgnoreCase(command.source().exactBuild()))build=candidate;
        if(build==null)return new RawJson(new byte[]{'{', '}'});
        return additionalFields(command,build);
    }

    /** Explicit source-selected DATA only; no Full occurrence or active lease is minted. */
    public static RawJson additionalFields(ActionCommand command,ExactCk3Build build) {
        Objects.requireNonNull(command);Objects.requireNonNull(build);requireProfile(build);
        String step=command.operation().value();
        StrictJson.require(step.startsWith(PREFIX)&&command.arguments().members().isEmpty()
                &&build.executableSha256().equalsIgnoreCase(command.source().exactBuild()),
                "explicit Date ARM DATA crossed its original source or arguments");
        var spec = dateSpec(step);
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay,
                "date-only ARM requires the original gameplay command");
        var before = ((CommandOrigin.Gameplay) command.origin()).before().frame();
        StrictJson.require(before.identity().dateRaw().equals(BigInteger.valueOf(spec.startingDateRaw())),
                "date-only ARM starting date differs from the original Full frame");
        return fields(build,before.snapshotId(),before.identity().nativeRevision(),command.deadline());
    }

    private static AdvancePrimitives.ArmSpec dateSpec(String step) {
        var spec = AdvancePrimitives.armSpec(step);
        StrictJson.require(spec.startingDateRaw() > 0 && spec.targetDateRaw() > 0
                && spec.mode().equals("terminal") && spec.armyIds().isEmpty()
                && step.equals(PREFIX + spec.startingDateRaw() + "-to-" + spec.targetDateRaw()
                        + "-speed-" + spec.speed() + "-mode-terminal-a-0"),
                "exact positive int32 whole-day terminal-a-0 ARM required");
        return spec;
    }

    private static void requireProfile(ExactCk3Build build) {
        StrictJson.require(build==ExactCk3Build.CK3_1210||build==ExactCk3Build.CK3_1210_STEAM_26757580
                ||build==ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,
                "explicit exact Florin date-only ARM profile required");
    }

    private static RawJson fields(ExactCk3Build build,String snapshotId,BigInteger revision,Instant originalDeadline) {
        requireProfile(build);
        Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(originalDeadline);
        StrictJson.require(revision.signum() > 0 && revision.bitLength() <= 64
                && snapshotId.equals("native:" + revision), "positive uint64 revision and exact native snapshot ID required");
        final long deadline;
        try { deadline = originalDeadline.toEpochMilli(); }
        catch (ArithmeticException overflow) { throw new IllegalArgumentException("finite original ARM deadline required", overflow); }
        StrictJson.require(deadline > 0, "positive original ARM deadline required");
        var claim = StrictJson.object();
        claim.put("schema", SCHEMA); claim.put("game_version", build.version());
        claim.put("executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT));
        claim.put("adapter_id", build.coreFullAdapterId());
        claim.put("backend", build.coreFullBackend());
        claim.put("snapshot_id", snapshotId); claim.put("native_revision", revision); claim.put("deadline_unix_ms", deadline);
        var fields = StrictJson.object(); fields.set("date_sentinel_arm", claim);
        return new RawJson(StrictJson.canonical(fields));
    }
}
