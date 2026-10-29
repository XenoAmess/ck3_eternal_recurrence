package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReadValue;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleControlExtensionCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponseCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.NativeArmiesCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/**
 * The original driver's single BattleControl cache slot. The sole Driver writer
 * supplies its archived contract replay after checking the actual receipt's
 * frame, source, episode, and connection; this projection issues no read or ACK.
 */
public final class BattleControlSemanticProjection {
    private BattleControlSemanticProjection() { }
    private static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Set<String> FIELDS = Set.of(
            "battle_control_snapshot_v1", "active_combat_resume_inputs_v1",
            "battle_control_snapshot_v1_status", "battle_control_snapshot_v1_query_sequence",
            "battle_control_snapshot_v1_query_attempts", "battle_control_snapshot_v1_diagnostic_reason",
            "battle_control_snapshot_v1_native_query_status", "battle_control_snapshot_v1_subject_army_id",
            "battle_control_snapshot_v1_queried_snapshot_id", "battle_control_snapshot_v1_queried_revision",
            "battle_control_snapshot_v1_queried_native_revision");

    public static boolean supports(Object value) {
        return value instanceof ArmyBattleReadValue battle && battle.kind() == ArmyBattleReadValue.Kind.CONTROL;
    }
    /** Compare the entire replayed result, including the optional same-query resume sidecar. */
    public static boolean same(ArmyBattleReadValue left, ArmyBattleReadValue right) {
        return left != null && right != null && left.kind() == right.kind()
                && left.sequence().equals(right.sequence()) && left.normalized().equals(right.normalized())
                && left.extensions().equals(right.extensions());
    }
    public static Set<String> fields() { return FIELDS; }
    /** Missing/unavailable cache remains explicit null in every original Python slot. */
    public static Obj unavailable() {
        var fields = new LinkedHashMap<String, Value>();
        for (String key : FIELDS) fields.put(key, Nil.INSTANCE);
        return new Obj(fields);
    }
    /**
     * Receives a strict replay of the existing battle-domain decoder. Finalized
     * and done frames remain observations for the ordinary cleanup gate; they
     * never become an inferred winner or a new permission to advance.
     */
    public static Obj project(ArmyBattleReadValue replayed, Obj currentSnapshot) {
        Objects.requireNonNull(replayed); Objects.requireNonNull(currentSnapshot);
        StrictJson.require(supports(replayed), "BattleControl cache requires its actual CONTROL read");
        BigInteger sequence = Objects.requireNonNull(replayed.sequence());
        StrictJson.require(sequence.signum() > 0 && sequence.compareTo(U64_MAX) <= 0,
                "BattleControl query_sequence must be positive unsigned64");
        StrictJson.require(OpportunityJson.bool(currentSnapshot.get("paused"), "paused"),
                "BattleControl cache requires the actual paused snapshot");
        int subject = OpportunityJson.integer(replayed.normalized().get("subject_public_cunit_id"),
                "subject_public_cunit_id").intValueExact();
        StrictJson.require(subject >= 0, "BattleControl cache requires a canonical public CUnitID");
        BigInteger nativeRevision = OpportunityJson.integer(currentSnapshot.get("native_revision"), "native_revision");
        Obj frame = BattleResponseCodec.normalizeControl(replayed.normalized(), subject, nativeRevision,
                OpportunityJson.integer(currentSnapshot.get("date_raw"), "date_raw").longValueExact());
        StrictJson.require(frame.equals(replayed.normalized()), "BattleControl typed read differs from strict normalization");
        requireActiveSubject(currentSnapshot, subject);
        Obj extensions = Objects.requireNonNull(replayed.extensions());
        StrictJson.require(Set.of("active_combat_resume_inputs_v1").containsAll(extensions.members().keySet()),
                "BattleControl cache cannot drop an unhandled original extension");
        Value resume = Nil.INSTANCE;
        if (extensions.members().containsKey("active_combat_resume_inputs_v1")) {
            Obj original = OpportunityJson.object(extensions.get("active_combat_resume_inputs_v1"), "active_combat_resume_inputs_v1");
            ObjectNode normalized = BattleControlExtensionCodec.normalizeResume(
                    (ObjectNode) OpportunityJson.toNode(original), (ObjectNode) OpportunityJson.toNode(frame));
            Obj checked = DriverJson.object(StrictJson.canonical(normalized), DriverJson.MAX_NATIVE_BYTES);
            StrictJson.require(original.equals(checked), "BattleControl resume sidecar differs from strict same-frame normalization");
            resume = checked;
        }
        BigInteger revision = OpportunityJson.integer(currentSnapshot.get("revision"), "revision");
        StrictJson.require(revision.signum() >= 0 && nativeRevision.signum() > 0,
                "BattleControl cache requires actual public/native revisions");
        String snapshotId = OpportunityJson.text(currentSnapshot.get("snapshot_id"), "snapshot_id");
        StrictJson.text(snapshotId);
        var fields = new LinkedHashMap<>(unavailable().members());
        fields.put("battle_control_snapshot_v1", frame);
        fields.put("active_combat_resume_inputs_v1", resume);
        fields.put("battle_control_snapshot_v1_status", new Text("available"));
        fields.put("battle_control_snapshot_v1_query_sequence", new IntegerValue(sequence));
        fields.put("battle_control_snapshot_v1_subject_army_id", new IntegerValue(BigInteger.valueOf(subject)));
        fields.put("battle_control_snapshot_v1_queried_snapshot_id", new Text(snapshotId));
        fields.put("battle_control_snapshot_v1_queried_revision", new IntegerValue(revision));
        fields.put("battle_control_snapshot_v1_queried_native_revision", new IntegerValue(nativeRevision));
        return new Obj(fields);
    }
    private static void requireActiveSubject(Obj snapshot, int subject) {
        int matches = 0;
        for (Value value : OpportunityJson.array(snapshot.get("player_armies"), "player_armies")) {
            Obj army = OpportunityJson.object(value, "player army");
            if (!OpportunityJson.integer(army.get("army_id"), "army_id").equals(BigInteger.valueOf(subject))) continue;
            NativeArmiesCodec.Army observed = NativeArmiesCodec.normalizeArmy(
                    OpportunityJson.toNode(army), "BattleControl current subject");
            // The original ordinary producer accepts each independently observed
            // tactical representation. Missing/null flags cannot erase state/code.
            boolean active = observed.inCombat().orElse(false)
                    || observed.armyState().map("combat"::equalsIgnoreCase).orElse(false)
                    || observed.armyStateCode().filter(BigInteger.TWO::equals).isPresent();
            StrictJson.require(observed.controllable() && active,
                    "BattleControl cache subject is no longer a controllable active combat");
            matches++;
        }
        StrictJson.require(matches == 1, "BattleControl cache requires one actual current subject");
    }
}
