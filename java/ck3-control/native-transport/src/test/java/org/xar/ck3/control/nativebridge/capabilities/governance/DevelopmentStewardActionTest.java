package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Native/Python contract data tests, with no native mutation permission or Game credit. */
final class DevelopmentStewardActionTest {
    static DevelopmentStewardAction.Request request() {
        return new DevelopmentStewardAction.Request("steward-dev-fixture-1", 32910, 1048577, BigInteger.valueOf(7), true);
    }
    static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value)); }
    static ObjectNode ack(boolean submitted) {
        ObjectNode value = StrictJson.object().put("schema_version", 1).put("contract_stage", DevelopmentStewardAction.STAGE)
                .put("status", submitted ? "submitted_verification_pending" : "rejected_before_submit")
                .put("verification_pending", submitted).put("request_id", request().requestId())
                .put("pre_snapshot_revision", submitted ? 7 : 0).put("pre_native_snapshot_revision", submitted ? 31 : 0)
                .put("councillor_character_id", 32910).put("task_key", DevelopmentStewardAction.TASK)
                .put("target_county_title_id", 1048577).put("submitted_target_province_id", submitted ? 2586 : -1)
                .put("replaced_existing_task", submitted).put("failure_class", submitted ? "none" : "native_command_dispatch");
        if (submitted) value.putNull("rejection_reason"); else value.put("rejection_reason", "native_command_abi_not_certified");
        value.putNull("native_reason_key");
        value.set("exact_build", StrictJson.object().put("game_version", DevelopmentStewardAction.VERSION)
                .put("executable_sha256", DevelopmentStewardAction.SHA).put("backend_id", DevelopmentStewardAction.BACKEND));
        return value;
    }
    static ObjectNode receipt(boolean applied, boolean rejected) {
        ObjectNode value = StrictJson.object().put("schema_version", 1)
                .put("status", rejected ? "rejected" : applied ? "applied" : "postcondition_failed")
                .put("request_id", request().requestId()).put("post_snapshot_revision", rejected ? 0 : applied ? 8 : 7)
                .put("post_native_snapshot_revision", rejected ? 0 : applied ? 32 : 31)
                .put("post_observed_date_raw", rejected ? 0 : 53182016).put("councillor_character_id", rejected ? -1 : 32910)
                .put("active_task_key", rejected ? "" : DevelopmentStewardAction.TASK)
                .put("progress_kind", rejected ? "" : "value").put("postcondition_verified", applied);
        if (applied) value.putNull("reason");
        else value.put("reason", rejected ? "native_command_abi_not_certified" : "no_new_paused_observation");
        if (rejected) {
            for (String field : List.of("target_county_title_id", "target_province_id", "progress_current_raw", "progress_max_raw", "progress_frozen")) value.putNull(field);
        } else {
            value.put("target_county_title_id", 1048577).put("target_province_id", 2586)
                    .put("progress_current_raw", 0).put("progress_max_raw", 100000).put("progress_frozen", false);
        }
        return value;
    }

    @Test void fixedRequestCannotInjectProvinceTaskOrCoercedIdentity() {
        var expected = request();
        assertEquals(expected, DevelopmentStewardAction.decodeRequest(DevelopmentStewardAction.encodeRequest(expected)));
        ObjectNode source = assertInstanceOf(ObjectNode.class, StrictJson.parse(DevelopmentStewardAction.encodeRequest(expected).bytes()));
        for (String field : List.of("councillor_character_id", "target_county_title_id", "expected_revision")) {
            ObjectNode changed = source.deepCopy(); changed.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeRequest(raw(changed)));
            ObjectNode floating = source.deepCopy(); floating.put(field, 7.0);
            assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeRequest(rawFloating(floating)));
        }
        ObjectNode task = source.deepCopy().put("task_key", "task_collect_taxes");
        assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeRequest(raw(task)));
        ObjectNode injected = source.deepCopy().put("target_province_id", 2586);
        assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeRequest(raw(injected)));
    }

    @Test void submittedAckAndUnverifiedPostReceiptRemainPendingAndNeverReplay() {
        var actual = DevelopmentStewardAction.decodeAck(raw(ack(true)), request());
        assertArrayEquals(raw(ack(true)).bytes(), DevelopmentStewardAction.encodeAck(actual).bytes());
        var missing = assertInstanceOf(DevelopmentStewardResults.Pending.class,
                DevelopmentStewardResults.reduce(actual, Optional.empty()));
        assertFalse(missing.replayAllowed());
        var unverified = DevelopmentStewardAction.decodeReceipt(raw(receipt(false, false)), actual);
        var retained = assertInstanceOf(DevelopmentStewardResults.Pending.class,
                DevelopmentStewardResults.reduce(actual, Optional.of(unverified)));
        assertEquals(unverified, retained.originalUnverifiedReceipt().orElseThrow());
        assertFalse(retained.replayAllowed());
        assertFalse(new DevelopmentStewardResults.UnknownSubmission(request(), Optional.empty()).replayAllowed());
    }

    @Test void onlyIndependentLaterExactReceiptIsAppliedAndInt64RawValuesRoundTrip() {
        var originalAck = DevelopmentStewardAction.decodeAck(raw(ack(true)), request());
        ObjectNode original = receipt(true, false).put("progress_current_raw", Long.MIN_VALUE).put("progress_max_raw", Long.MAX_VALUE);
        var decoded = DevelopmentStewardAction.decodeReceipt(raw(original), originalAck);
        assertArrayEquals(raw(original).bytes(), DevelopmentStewardAction.encodeReceipt(decoded).bytes());
        assertInstanceOf(DevelopmentStewardResults.AppliedObserved.class,
                DevelopmentStewardResults.reduce(originalAck, Optional.of(decoded)));
        for (String field : List.of("post_snapshot_revision", "post_native_snapshot_revision", "councillor_character_id", "target_county_title_id", "target_province_id")) {
            ObjectNode changed = original.deepCopy();
            changed.put(field, field.equals("post_snapshot_revision") ? 7 : field.equals("post_native_snapshot_revision") ? 31 : 1);
            assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeReceipt(raw(changed), originalAck), field);
        }
        ObjectNode missing = original.deepCopy(); missing.remove("progress_frozen");
        assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeReceipt(raw(missing), originalAck));
        ObjectNode bad = original.deepCopy().put("progress_current_raw", true);
        assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeReceipt(raw(bad), originalAck));
    }

    @Test void rejectionIsDistinctAndEveryEchoedIntegerIsStrict() {
        var rejected = DevelopmentStewardAction.decodeAck(raw(ack(false)), request());
        var actualReceipt = DevelopmentStewardAction.decodeReceipt(raw(receipt(false, true)), rejected);
        assertInstanceOf(DevelopmentStewardResults.RejectedObserved.class,
                DevelopmentStewardResults.reduce(rejected, Optional.of(actualReceipt)));
        for (String field : List.of("schema_version", "pre_snapshot_revision", "pre_native_snapshot_revision", "councillor_character_id", "target_county_title_id", "submitted_target_province_id")) {
            ObjectNode invalid = ack(true).put(field, true);
            assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeAck(raw(invalid), request()), field);
        }
        ObjectNode wrongBuild = ack(true);
        assertInstanceOf(ObjectNode.class, wrongBuild.get("exact_build")).put("game_version", "1.20.0.4");
        assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardAction.decodeAck(raw(wrongBuild), request()));
    }

    private static RawJson rawFloating(ObjectNode value) {
        // Preserve the actual floating JSON token for boundary tests. Shared
        // canonical intentionally refuses noninteger numbers before encoding.
        try { return new RawJson(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(value)); }
        catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
    }
}
