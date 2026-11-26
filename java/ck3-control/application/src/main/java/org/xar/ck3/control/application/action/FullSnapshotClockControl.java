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

    /** Selected corrected112 artifact DATA only; this predicate grants no Managed, READ, action or SAVE authority. */
    public static boolean isMappedSave112Bridge(org.xar.ck3.control.contracts.ExactRef bridge) {
        return bridge!=null&&((bridge.bytes()==12381696L
                &&"2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6".equalsIgnoreCase(bridge.sha256()))
                // Independent125: original112 Full/clock/SAVE source, published loaded-image admission fix.
                ||(bridge.bytes()==12389376L
                &&"863b4893611d1101e4f5e7f82b43f4fab2c7259bd0db6c0065a59a9a016c12f7".equalsIgnoreCase(bridge.sha256()))
                // Independent131: exact125 source plus separately qualified strict date-sentinel option.
                ||(bridge.bytes()==12389376L
                &&"060a22216f6d7642ce2ee392dc7ffffbd17f1bb8d2029cd79eb17e47599b23f4".equalsIgnoreCase(bridge.sha256()))
                // Independent132/134 control source; empty-Army/War and all live custody gates remain separate.
                ||(bridge.bytes()==12389888L
                &&"50b1b12bae59d5eb70b97978b86aabbb93a675e6e327bbcaa9a37aa5285cdb46".equalsIgnoreCase(bridge.sha256()))
                // Independent142: control source only after the identical transport selects control mode.
                ||(bridge.bytes()==12396032L
                &&"3601748c4d4824509416d61c779f16eda6f97b85cd5608786ecf5645215b733c".equalsIgnoreCase(bridge.sha256()))
                // Full111 ordinary snapshot and original sentinel expiry build from 394b0d2ee5.
                ||(bridge.bytes()==27048960L
                &&"6dc0b448fbe5ab46e0ef59127e00f893b5da71ad2c6e22c51c21f9a80e66602c".equalsIgnoreCase(bridge.sha256()))
                // Full111 with read-only Opening uses the same mapped SAVE implementation.
                ||(bridge.bytes()==21_515_776L
                &&"f33eb6d59068ebd21ba78ef43d933222e15427352d2bb206bb60990152963c52".equalsIgnoreCase(bridge.sha256()))
                // Full111 with foreground event selection retains the same mapped SAVE implementation.
                ||(bridge.bytes()==21_523_968L
                &&"db2a814aaa702b322a53e76512b8c80d71fc3249c71c9d31a674a436effaee86".equalsIgnoreCase(bridge.sha256()))
                // Full111 with stock event button reads retains the same mapped SAVE implementation.
                ||(bridge.bytes()==21_568_000L
                &&"18c9272b94fa1a34d8b72a2be0cf23bae41e2756fd84adf536053a3f33677f03".equalsIgnoreCase(bridge.sha256()))
                // Full111 with single-use stock event selection retains the mapped SAVE implementation.
                ||(bridge.bytes()==21_625_344L
                &&"9f7d32508da373bb6f2783a583641e6d2393a5c8950ce05ee3fefd3877a339c4".equalsIgnoreCase(bridge.sha256())));
    }

    public static NativeRequest requestMappedSave112(org.xar.ck3.control.contracts.ExactRef bridge,
            String snapshotId,BigInteger revision,Instant deadline) {
        StrictJson.require(isMappedSave112Bridge(bridge),"exact corrected112 mapped SAVE source required");
        return new NativeRequest("save-checkpoint","game.command.save-checkpoint",
                fields(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,snapshotId,revision,deadline));
    }

    public static RawJson additionalFieldsMappedSave112(ActionCommand command,org.xar.ck3.control.contracts.ExactRef bridge) {
        Objects.requireNonNull(command);
        StrictJson.require(isMappedSave112Bridge(bridge)&&command.operation().value().equals("save-checkpoint")
                &&command.arguments().members().isEmpty()
                &&ExactCk3Build.CK3_121003_STEAM_26785313_FULL111.executableSha256().equalsIgnoreCase(command.source().exactBuild()),
                "exact corrected112 SAVE command and selected artifact DATA required");
        if(!(command.origin() instanceof CommandOrigin.Gameplay gameplay))
            throw new IllegalArgumentException("mapped112 SAVE requires the original gameplay command");
        var before=gameplay.before().frame();
        return fields(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,before.snapshotId(),before.identity().nativeRevision(),command.deadline());
    }

    /** Exact producer selection DATA, never a live-source or physical SAVE qualification. */
    public static boolean isMappedSave61Bridge(org.xar.ck3.control.contracts.ExactRef bridge) {
        if (bridge == null) return false;
        boolean mapped61 = bridge.bytes()==13451776L
                && "4376f38077794ba100349da7a8cc26f45fcab33d0ad525da9ea1836ca26747d6".equalsIgnoreCase(bridge.sha256());
        // Independent81 exact producer: unchanged mapped SAVE implementation, formally rebuilt Full4 closure.
        boolean diagnostic81 = bridge.bytes()==13752832L
                && "75dc138eecec0719f6b7648a4dca3fa83332138c08a61c07403378ba17b54fd9".equalsIgnoreCase(bridge.sha256());
        // Independent92 exact producer; original SAVE source/objects/flags remain verified.
        boolean observer92 = bridge.bytes()==13761536L
                && "d9cb12a0e634e517ce6f72d9698e4ea9ab72fc3df606e8fcf34d3fee58c6805f".equalsIgnoreCase(bridge.sha256());
        return mapped61 || diagnostic81 || observer92;
    }

    /** Explicit SAVE61 request DATA. The default BB3 clock entry continues to reject SAVE. */
    public static NativeRequest requestMappedSave61(org.xar.ck3.control.contracts.ExactRef bridge,
            String snapshotId,BigInteger revision,Instant deadline) {
        StrictJson.require(isMappedSave61Bridge(bridge),"exact mapped SAVE61 DLL source required");
        return new NativeRequest("save-checkpoint","game.command.save-checkpoint",
                fields(ExactCk3Build.CK3_1210_STEAM_26757580,snapshotId,revision,deadline));
    }

    /** Explicit same-command source selection; no receipt, action or writer authority is created. */
    public static RawJson additionalFieldsMappedSave61(ActionCommand command,
            org.xar.ck3.control.contracts.ExactRef bridge) {
        Objects.requireNonNull(command);
        StrictJson.require(isMappedSave61Bridge(bridge)
                && command.operation().value().equals("save-checkpoint") && command.arguments().members().isEmpty()
                && ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256().equalsIgnoreCase(command.source().exactBuild()),
                "exact BB3 SAVE command and mapped SAVE61 source required");
        if(!(command.origin() instanceof CommandOrigin.Gameplay gameplay))
            throw new IllegalArgumentException("mapped SAVE61 requires the original gameplay command");
        var before=gameplay.before().frame();
        return fields(ExactCk3Build.CK3_1210_STEAM_26757580,before.snapshotId(),
                before.identity().nativeRevision(),command.deadline());
    }

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
        return additionalFields(command,build);
    }

    /** Explicit source-selected DATA. The caller must separately prove its actual Full source and submit authority. */
    public static RawJson additionalFields(ActionCommand command,ExactCk3Build build) {
        Objects.requireNonNull(command);Objects.requireNonNull(build);
        StrictJson.require(supports(command.operation())&&command.arguments().members().isEmpty()
                &&build.executableSha256().equalsIgnoreCase(command.source().exactBuild()),
                "explicit Full clock DATA crossed its command source or fixed argument-free step");
        requireClockProfile(build,command.operation().value());
        if (!(command.origin() instanceof CommandOrigin.Gameplay gameplay))
            throw new IllegalArgumentException("full snapshot clock control requires a gameplay command origin");
        var before = gameplay.before().frame();
        return fields(build,before.snapshotId(), before.identity().nativeRevision(), command.deadline());
    }

    private static void requireClockProfile(ExactCk3Build build,String step) {
        StrictJson.require(build==ExactCk3Build.CK3_1210||build==ExactCk3Build.CK3_1210_STEAM_26757580
                ||build==ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,
                "an explicit exact Florin clock profile is required");
        StrictJson.require((build!=ExactCk3Build.CK3_1210_STEAM_26757580
                &&build!=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111)||!"save-checkpoint".equals(step),
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
        claim.put("backend", build.coreFullBackend());
        claim.put("snapshot_id", snapshotId);
        claim.put("native_revision", revision);
        claim.put("deadline_unix_ms", deadline);
        var fields = StrictJson.object();
        fields.set("full_snapshot_clock_control", claim);
        return new RawJson(StrictJson.canonical(fields));
    }
}
