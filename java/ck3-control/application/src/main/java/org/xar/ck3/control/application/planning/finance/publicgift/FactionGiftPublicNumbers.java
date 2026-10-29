package org.xar.ck3.control.application.planning.finance.publicgift;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;

/** Explicit Gift paths only. Original native/archive bytes remain unchanged; unknown wide fields fail public output. */
public final class FactionGiftPublicNumbers {
    private enum Role { U64, SIGNED64, INTEGER }
    private FactionGiftPublicNumbers() { }
    public static RawJson businessPublic(Method method, RawJson original) {
        var result = business(method, object(original), true); safe(result, "$");
        return PublicDataJson.encodeTyped(result);
    }
    public static RawJson businessNative(Method method, RawJson supplied) {
        return PublicDataJson.encodeTyped(business(method, object(supplied), false));
    }
    public static RawJson candidateNative(RawJson supplied) { return PublicDataJson.encodeTyped(candidate(object(supplied), false)); }
    public static RawJson pendingNative(RawJson supplied) { return PublicDataJson.encodeTyped(pending(object(supplied), false)); }
    public static RawJson rootNative(RawJson supplied) { return PublicDataJson.encodeTyped(common(object(supplied), false)); }
    public static RawJson checkpointNative(RawJson supplied) {
        // The original checkpoint uses sha256/date_raw/episode_run_id. Do not invent FileID or birth fields.
        return PublicDataJson.encodeTyped(object(supplied));
    }
    private static OpportunityJson.Obj business(Method method, OpportunityJson.Obj value, boolean out) {
        return switch (method) {
            case CANDIDATE -> candidate(value, out);
            case SEND, RECEIPT, COLD_RECOVERY -> route(value, out);
            case RESOLVED -> outcome(value, out);
        };
    }
    private static OpportunityJson.Obj common(OpportunityJson.Obj value, boolean out) {
        return fields(value, List.of("query_sequence", "observation_revision", "snapshot_revision", "native_snapshot_revision",
                "revision", "native_revision", "queried_revision", "queried_native_revision", "expected_revision",
                "pre_snapshot_revision", "pre_native_snapshot_revision", "post_snapshot_revision", "post_native_snapshot_revision"), Role.U64, out);
    }
    private static OpportunityJson.Obj money(OpportunityJson.Obj value, boolean out) {
        return fields(value, List.of("gold_cost_raw", "player_gold_raw", "pre_player_gold_raw", "post_player_gold_raw",
                "source_faction_power_raw", "source_faction_discontent_raw", "pre_source_faction_power_raw",
                "pre_source_faction_discontent_raw"), Role.SIGNED64, out);
    }
    private static OpportunityJson.Obj choice(OpportunityJson.Obj value, boolean out) {
        value = money(common(value, out), out);
        value = number(value, "definition_stable_hash", Role.U64, out);
        return number(value, "minimum_gold_reserve_raw", Role.INTEGER, out);
    }
    private static OpportunityJson.Obj observation(OpportunityJson.Obj value, boolean out) {
        value = money(common(value, out), out);
        return child(value, "gift_preview", out, (preview, direction) ->
                number(money(preview, direction), "definition_stable_hash", Role.U64, direction));
    }
    private static OpportunityJson.Obj candidate(OpportunityJson.Obj value, boolean out) {
        value = common(value, out);
        value = child(value, "choice", out, FactionGiftPublicNumbers::choice);
        return child(value, "observation", out, FactionGiftPublicNumbers::observation);
    }
    private static OpportunityJson.Obj pending(OpportunityJson.Obj value, boolean out) {
        value = number(money(common(value, out), out), "minimum_gold_reserve_raw", Role.INTEGER, out);
        return child(value, "ack", out, (ack, direction) ->
                number(money(common(ack, direction), direction), "definition_stable_hash", Role.U64, direction));
    }
    private static OpportunityJson.Obj receipt(OpportunityJson.Obj value, boolean out) {
        return number(money(common(value, out), out), "definition_stable_hash", Role.U64, out);
    }
    private static OpportunityJson.Obj route(OpportunityJson.Obj value, boolean out) {
        value = common(value, out);
        value = child(value, "source_frame", out, FactionGiftPublicNumbers::common);
        value = child(value, "receipt", out, FactionGiftPublicNumbers::receipt);
        value = child(value, "pending_ledger", out,
                (ledger, direction) -> child(ledger, "pending", direction, FactionGiftPublicNumbers::pending));
        value = child(value, "native", out, (nativeRow, direction) -> {
            var changed = common(nativeRow, direction);
            changed = child(changed, "observation", direction, FactionGiftPublicNumbers::observation);
            return child(changed, "ack", direction, FactionGiftPublicNumbers::receipt);
        });
        value = child(value, "cold_recovery", out,
                (cold, direction) -> child(common(cold, direction), "post_observation", direction, FactionGiftPublicNumbers::observation));
        return value;
    }
    private static OpportunityJson.Obj outcome(OpportunityJson.Obj value, boolean out) {
        value = common(value, out);
        value = child(value, "original", out, (original, direction) ->
                child(money(common(original, direction), direction), "receipt", direction, FactionGiftPublicNumbers::receipt));
        value = child(value, "current_observation", out, FactionGiftPublicNumbers::observation);
        return child(value, "current_alert", out, (alert, direction) ->
                child(alert, "row", direction, (row, toPublic) -> money(common(row, toPublic), toPublic)));
    }
    @FunctionalInterface private interface Transform {
        OpportunityJson.Obj apply(OpportunityJson.Obj value, boolean out);
    }
    private static OpportunityJson.Obj child(OpportunityJson.Obj value, String key, boolean out, Transform transform) {
        var child = value.get(key);
        if (child == null || child == OpportunityJson.Nil.INSTANCE) return value;
        StrictJson.require(child instanceof OpportunityJson.Obj, "declared Gift object path requires an object: " + key);
        return value.with(key, transform.apply((OpportunityJson.Obj) child, out));
    }
    private static OpportunityJson.Obj fields(OpportunityJson.Obj value, List<String> keys, Role role, boolean out) {
        for (String key : keys) value = number(value, key, role, out);
        return value;
    }
    private static OpportunityJson.Obj number(OpportunityJson.Obj value, String key, Role role, boolean out) {
        var token = value.get(key);
        if (token == null || token == OpportunityJson.Nil.INSTANCE) return value;
        BigInteger integer;
        if (token instanceof OpportunityJson.IntegerValue nativeInteger) {
            integer = nativeInteger.value();
            StrictJson.require(out || integer.abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER) <= 0,
                    "unsafe public numeric Gift field requires decimal text: " + key);
        } else {
            StrictJson.require(token instanceof OpportunityJson.Text, "declared wide Gift field requires exact integer token or decimal text: " + key);
            String text = ((OpportunityJson.Text) token).value();
            StrictJson.require(text.matches("0|-?[1-9][0-9]*"), "canonical Gift decimal required: " + key);
            integer = new BigInteger(text);
        }
        if (role == Role.U64) PublicUnsigned64.canonical(integer, PublicUnsigned64.Minimum.ZERO);
        if (role == Role.SIGNED64) StrictJson.require(integer.compareTo(BigInteger.ONE.shiftLeft(63).negate()) >= 0
                && integer.compareTo(BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE)) <= 0, "Gift signed64 range: " + key);
        return value.with(key, out ? new OpportunityJson.Text(integer.toString()) : new OpportunityJson.IntegerValue(integer));
    }
    private static OpportunityJson.Obj object(RawJson original) {
        return DriverJson.object(original.bytes(), RawJson.MAXIMUM_BYTES);
    }
    private static void safe(OpportunityJson.Value value, String path) {
        if (value instanceof OpportunityJson.IntegerValue integer)
            StrictJson.require(integer.value().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER) <= 0,
                    "undeclared unsafe public Gift integer at " + path);
        else if (value instanceof OpportunityJson.Obj object)
            object.members().forEach((key, child) -> safe(child, path + "/" + key));
        else if (value instanceof OpportunityJson.Arr array)
            for (int i = 0; i < array.items().size(); i++) safe(array.items().get(i), path + "/" + i);
        // Opaque decimal tokens are retained exactly by DriverJson/PublicDataJson, including -0.0.
    }
}
