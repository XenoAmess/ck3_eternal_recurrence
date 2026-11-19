package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Full-observation command DATA only. Neither a source SHA nor this claim grants a live frame or submit authority. */
public final class FullSnapshotClockControl {
    public static final String SCHEMA = "ck3_1210_full_clock_control_v1";
    private static final Set<String> STEPS = Set.of("pause-map", "resume-map", "set-speed-1", "set-speed-2",
            "set-speed-3", "set-speed-4", "set-speed-5", "save-checkpoint");

    private FullSnapshotClockControl() { }

    public static boolean supports(OperationKey operation) {
        return STEPS.contains(Objects.requireNonNull(operation).value());
    }

    /**
     * Exact Florin request DATA, without a Driver, received frame or permission.
     * The transport must independently retain and verify its actual Full READ,
     * connection, original deadline and one-use submit authority.
     */
    public static NativeRequest request(String step, String actualSnapshotId,
            BigInteger actualNativeRevision, Instant originalDeadline) {
        StrictJson.require(STEPS.contains(Objects.requireNonNull(step)),
                "fixed full snapshot clock control step required");
        return request(ExactCk3Build.CK3_1210,step,actualSnapshotId,actualNativeRevision,originalDeadline);
    }

    /** Exact selected clock profile DATA; all actual received-frame and capability guards remain in the transport. */
    public static NativeRequest request(ExactCk3Build build,String step,String actualSnapshotId,
            BigInteger actualNativeRevision,Instant originalDeadline) {
        requireClockProfile(build,step);
        StrictJson.require(STEPS.contains(Objects.requireNonNull(step)),"fixed full snapshot clock control step required");
        return new NativeRequest(step,"game.command."+step,fields(build,actualSnapshotId,actualNativeRevision,originalDeadline));
    }

    /** Keeps legacy/unknown source spellings unchanged. Only the exact current raw executable SHA selects new DATA. */
    public static RawJson additionalFields(ActionCommand command) {
        Objects.requireNonNull(command);
        StrictJson.require(supports(command.operation()) && command.arguments().members().isEmpty(),
                "fixed argument-free full snapshot clock control required");
        ExactCk3Build build=null;
        for(var candidate:java.util.List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580))
            if(candidate.executableSha256().equalsIgnoreCase(command.source().exactBuild()))build=candidate;
        if(build==null)return new RawJson(new byte[] {'{', '}'});
        requireClockProfile(build,command.operation().value());
        if (!(command.origin() instanceof CommandOrigin.Gameplay gameplay))
            throw new IllegalArgumentException("full snapshot clock control requires a gameplay command origin");
        var before = gameplay.before().frame();
        return fields(build,before.snapshotId(), before.identity().nativeRevision(), command.deadline());
    }

    private static void requireClockProfile(ExactCk3Build build,String step) {
        StrictJson.require(build==ExactCk3Build.CK3_1210||build==ExactCk3Build.CK3_1210_STEAM_26757580,
                "an explicit exact Florin clock profile is required");
        StrictJson.require(build!=ExactCk3Build.CK3_1210_STEAM_26757580||!"save-checkpoint".equals(step),
                "this hotfix Full clock profile does not qualify SAVE");
    }
    private static RawJson fields(ExactCk3Build build,String snapshotId, BigInteger revision, Instant originalDeadline) {
        Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(originalDeadline);
        StrictJson.require(revision.signum() > 0 && revision.bitLength() <= 64
                && snapshotId.equals("native:" + revision),
                "full snapshot clock control requires a positive exact native revision and matching native snapshot ID");
        final long deadline;
        try { deadline = originalDeadline.toEpochMilli(); }
        catch (ArithmeticException overflow) {
            throw new IllegalArgumentException("full snapshot clock control requires a finite epoch-millisecond deadline", overflow);
        }
        StrictJson.require(deadline > 0, "full snapshot clock control requires the original positive command deadline");
        var claim = StrictJson.object();
        claim.put("schema", SCHEMA);
        claim.put("game_version", build.version());
        claim.put("executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT));
        claim.put("adapter_id", build.coreFullAdapterId());
        claim.put("backend", "ck3-" + build.version() + "-native-headless-main-thread");
        claim.put("snapshot_id", snapshotId);
        claim.put("native_revision", revision);
        claim.put("deadline_unix_ms", deadline);
        var fields = StrictJson.object();
        fields.set("full_snapshot_clock_control", claim);
        return new RawJson(StrictJson.canonical(fields));
    }
}
