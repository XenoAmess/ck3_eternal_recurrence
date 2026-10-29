package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.NativeFeastEffects;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure production projection over explicit synthetic native originals; no live qualification. */
final class NativeFeastMaterialTest {
    private static RawJson raw(Obj value) { return new RawJson(encode(value)); }
    private static Obj balances(long gold) {
        Obj zero = new Obj(java.util.Map.of()).with("available", new Bool(true)) .with("raw", n(0));
        return new Obj(java.util.Map.of()).with("gold", new Obj(java.util.Map.of()).with("available", new Bool(true)) .with("raw", n(gold)))
                .with("treasury", zero) .with("piety", zero) .with("barter_goods", zero);
    }
    private static Obj hosted(int revision, long gold, List<Value> rows) {
        return new Obj(java.util.Map.of()).with("schema", new Text("activity-feast-hosted-post-private-read-v1")) .with("snapshot_revision", n(revision))
                .with("date_raw", n(100)) .with("actor_character_id", n(29829)) .with("balances", balances(gold))
                .with("hosted_activities", new Arr(rows)) .with("read_only", new Bool(true)) .with("advertised", new Bool(false));
    }
    private static Obj instance(long id, long actor, String type) {
        return new Obj(java.util.Map.of()).with("activity_id", n(id)) .with("host_character_id", n(actor)) .with("activity_type_key", new Text(type));
    }
    private static Obj diagnostic(int revision, int stage) {
        return OrdinaryGovernanceFactoriesTest.diagnostic(request(revision, false, List.of()))
                .with("planner_status", new Text("observed")).with("planner_present", new Bool(true))
                .with("widget_attached", new Bool(true)).with("widget_visible", new Bool(true))
                .with("planning_stage", n(stage)).with("host_view_activity_key", new Text("activity_feast"));
    }
    private static Obj envelope(OperationKey operation, String key, Obj payload, boolean readOnly, String status) {
        return new Obj(java.util.Map.of()).with("step", new Text(operation.value())) .with("accepted", new Bool(true)) .with("status", new Text(status))
                .with("private_build", new Bool(true)) .with("read_only", new Bool(readOnly)) .with("advertised", new Bool(false))
                .with(key, payload) .with("backend_id", new Text("native-headless"));
    }
    private static RawJson diagnosticRead(int stage) { return raw(envelope(NativeFeastEffects.Query.DIAGNOSTIC.operation(), "activity_planner_diag", diagnostic(10, stage), true, "available")); }
    private static RawJson hostedRead(Obj payload) { return raw(envelope(NativeFeastEffects.Query.HOSTED.operation(), "activity_feast_hosted_post", payload, true, "available")); }
    private static Obj inputs() {
        Obj zero = new Obj(java.util.Map.of()).with("resource_index", n(1)) .with("configured_cost_raw", n(0));
        return hosted(9, 1000, List.of()).with("schema", new Text("activity-feast-stage5-start-inputs-private-v1"))
                .with("final_can_start", new Bool(true)).with("native_guest_route_qualified", new Bool(true))
                .with("resources", new Obj(java.util.Map.of()).with("gold", new Obj(java.util.Map.of()).with("resource_index", n(0)) .with("configured_cost_raw", n(100)))
                        .with("treasury", zero) .with("piety", zero) .with("barter_goods", zero));
    }
    private static RawJson startAck() {
        return startAck(inputs());
    }
    private static RawJson startAck(Obj source) {
        return raw(envelope(OrdinaryFeastPolicy.START, "activity_feast_stage5_start",
                new Obj(java.util.Map.of()).with("schema", new Text("activity-feast-stage5-start-private-action-v1")) .with("submitted", new Bool(true))
                        .with("native_status", new Text("submitted_pending")) .with("failure", new Text("")) .with("precondition", source), false, "pending"));
    }
    private static Obj startArguments() { return new Obj(java.util.Map.of()).with("inputs", inputs()) .with("new_attempt", new Bool(true)); }
    @Test void pendingAckAloneCannotProveStartAndFreshHostedInstanceRequiresActualDebit() {
        Obj post = hosted(10, 900, List.of(instance(18, 29829, "activity_feast")));
        var actual = NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(), identity(9), identity(10), startAck(), diagnosticRead(5), hostedRead(post));
        assertTrue(actual.contains(new ExpectedBoolean(new FieldKey("feast.new_hosted_instance"), true)));
        assertTrue(actual.contains(new ExpectedInteger(new FieldKey("feast.activity_id"),BigInteger.valueOf(18))));
        assertTrue(actual.contains(new ExpectedInteger(new FieldKey("feast.host_character_id"),BigInteger.valueOf(29829))));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(),
                identity(9), identity(10), startAck(), diagnosticRead(5), hostedRead(hosted(10, 1000, List.of()))));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(),
                identity(9), identity(10), startAck(), diagnosticRead(5), hostedRead(post.with("balances", balances(999)))));
    }
    @Test void anotherHostExtraActivityOrRemovedPreexistingInstanceCannotBecomeTheSavedStart() {
        for (List<Value> rows : List.of(List.<Value>of(instance(18, 29830, "activity_feast")),
                List.<Value>of(instance(18, 29829, "activity_feast"), instance(19, 29829, "activity_feast"))))
            assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(),
                    identity(9), identity(10), startAck(), diagnosticRead(5), hostedRead(hosted(10, 900, rows))));
        Obj pre = inputs().with("hosted_activities", new Arr(List.of(instance(10, 29829, "activity_hunt"))));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START,
                startArguments().with("inputs", pre), identity(9), identity(10), startAck(pre), diagnosticRead(5),
                hostedRead(hosted(10, 900, List.of(instance(18, 29829, "activity_feast"))))));
    }
    @Test void zeroCostUnknownWalletSemanticsMatchTheOriginalConsumerWithoutGuessingItsBalance() {
        Obj unknown = new Obj(java.util.Map.of()).with("available", new Bool(false)) .with("raw", Nil.INSTANCE);
        Obj pre = inputs().with("balances", balances(1000).with("treasury", unknown));
        Obj post = hosted(10, 900, List.of(instance(18, 29829, "activity_feast"))).with("balances", balances(900).with("treasury", unknown));
        assertDoesNotThrow(() -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments().with("inputs", pre),
                identity(9), identity(10), startAck(pre), diagnosticRead(5), hostedRead(post)));
        var invalid = unknown.with("raw", new Bool(false));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments().with("inputs", pre),
                identity(9), identity(10), startAck(pre), diagnosticRead(5), hostedRead(post.with("balances", balances(900).with("treasury", invalid)))));
    }
    private static RawJson confirmAck() {
        Obj receipt = new Obj(java.util.Map.of()).with("schema", new Text("activity-stage1-confirm-private-v1")) .with("snapshot_revision", n(9)) .with("date_raw", n(100)) .with("actor_character_id", n(29829))
                .with("status", new Text("stage_two_verified")) .with("submitted", new Bool(true)) .with("stage_two_visible", new Bool(true))
                .with("selected_option_retained", new Bool(true)) .with("selected_option_key", new Text("feast_type_generic"))
                .with("activity_start_state", new Text("not_started_immediate")) .with("planning_stage_after", n(2)) .with("gold_before_raw", n(1000)) .with("gold_after_raw", n(1000));
        receipt = receipt.with("activity_key", new Text("activity_feast")).with("expected_option_key", new Text("feast_type_generic"))
                .with("precondition_status", new Text("observed")).with("selected_option_shown", new Bool(true)).with("selected_option_valid", new Bool(true))
                .with("can_progress_stage1", new Bool(true)).with("generic_feast_confirm_ready", new Bool(true)).with("snapshot_unchanged", new Bool(true))
                .with("next_turn_verified", new Bool(false)).with("raw_pointer_fields_persisted", new Bool(false)).with("advertised", new Bool(false));
        return raw(envelope(OrdinaryFeastPolicy.CONFIRM, "activity_stage1_confirm", receipt, false, "available"));
    }
    @Test void confirmRequiresAnIndependentStageTwoAndUnchangedWalletWithNoNewActivity() {
        Obj args = new Obj(java.util.Map.of()).with("hosted_observation", hosted(9, 1000, List.of())); Obj post = hosted(10, 1000, List.of());
        assertDoesNotThrow(() -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIRM, args, identity(9), identity(10), confirmAck(), diagnosticRead(2), hostedRead(post)));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIRM, args, identity(9), identity(10), confirmAck(), diagnosticRead(1), hostedRead(post)));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIRM, args, identity(9), identity(10), confirmAck(), diagnosticRead(2), hostedRead(post.with("balances", balances(999)))));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIRM, args, identity(9), identity(10), confirmAck(), diagnosticRead(2), hostedRead(hosted(10, 1000, List.of(instance(18, 29829, "activity_feast"))))));
    }
    @Test void sameFrameWrongActorOrBooleanResourceCannotBeAcceptedAsNativeMaterial() {
        Obj post = hosted(10, 900, List.of(instance(18, 29829, "activity_feast")));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(), identity(9), identity(9), startAck(), diagnosticRead(5), hostedRead(post)));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(), identity(9), identity(10), startAck(), diagnosticRead(5), hostedRead(post.with("actor_character_id", n(29830)))));
        Obj broken = post.with("balances", balances(900).with("gold", new Obj(java.util.Map.of()).with("available", new Bool(true)) .with("raw", new Bool(true))));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.START, startArguments(), identity(9), identity(10), startAck(), diagnosticRead(5), hostedRead(broken)));
    }
    @Test void destinationRequiresBothOriginalFilledRowsAndFreshIndependentStageFive() {
        Obj receipt = new Obj(java.util.Map.of()).with("schema", new Text("activity-stage2-destination-private-action-v1")) .with("snapshot_revision", n(9))
                .with("date_raw", n(100)) .with("actor_character_id", n(29829)) .with("activity_key", new Text("activity_feast"))
                .with("selected_option_key", new Text("feast_type_generic")) .with("selected_province_id", n(123)) .with("status", new Text("verified_stage_five"))
                .with("submitted", new Bool(true)) .with("needs_recovery", new Bool(false)) .with("stage_five_visible", new Bool(true)) .with("rows_filled", new Bool(true))
                .with("selected_option_retained", new Bool(true)) .with("gold_unchanged", new Bool(true)) .with("frame_unchanged", new Bool(true))
                .with("no_activity_started", new Bool(true)) .with("planning_stage_before", n(2)) .with("planning_stage_after", n(5))
                .with("configuration_province_ids_before", new Arr(List.of(n(0), n(0)))) .with("configuration_province_ids_after", new Arr(List.of(n(123), n(123))))
                .with("player_gold_before_raw", n(1000)) .with("player_gold_after_raw", n(1000)) .with("read_only", new Bool(false)) .with("advertised", new Bool(false));
        Obj args = new Obj(java.util.Map.of()).with("native_arguments", new Obj(java.util.Map.of()).with("province_id", n(123))) .with("hosted_observation", hosted(9, 1000, List.of()));
        RawJson ack = raw(envelope(OrdinaryFeastPolicy.DESTINATION, "activity_stage2_destination_select", receipt, false, "available"));
        RawJson post = hostedRead(hosted(10, 1000, List.of()));
        assertDoesNotThrow(() -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.DESTINATION, args, identity(9), identity(10), ack, diagnosticRead(5), post));
        RawJson broken = raw(envelope(OrdinaryFeastPolicy.DESTINATION, "activity_stage2_destination_select",
                receipt.with("configuration_province_ids_after", new Arr(List.of(n(123), n(124)))), false, "available"));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.DESTINATION, args, identity(9), identity(10), broken, diagnosticRead(5), post));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.DESTINATION, args, identity(9), identity(10), ack, diagnosticRead(2), post));
    }
    @Test void openNeverClaimsConfigurationCompleteAndAcceptsTheGenuineNativeStageOneOrTwo() {
        Obj receipt = new Obj(java.util.Map.of()).with("schema", new Text("activity-feast-planner-open-private-v1")) .with("snapshot_revision", n(9)) .with("date_raw", n(100)) .with("actor_character_id", n(29829))
                .with("open_status", new Text("opened")) .with("native_dispatch_invoked", new Bool(true)) .with("selected_feast_verified", new Bool(true))
                .with("widget_attached", new Bool(true)) .with("widget_visible", new Bool(true)) .with("planning_stage", n(1))
                .with("configured_cost_state", new Text("unknown")) .with("final_can_start_state", new Text("unknown")) .with("raw_pointer_fields_persisted", new Bool(false));
        RawJson ack = raw(envelope(OrdinaryFeastPolicy.CONFIGURE, "activity_feast_planner_open", receipt, false, "available"));
        Obj args = new Obj(java.util.Map.of()).with("hosted_observation", hosted(9, 1000, List.of())); RawJson post = hostedRead(hosted(10, 1000, List.of()));
        var actual = NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIGURE, args, identity(9), identity(10), ack, diagnosticRead(1), post);
        assertFalse(actual.stream().anyMatch(value -> value.field().equals(new FieldKey("feast.planning_stage"))));
        RawJson stageTwoAck = raw(envelope(OrdinaryFeastPolicy.CONFIGURE, "activity_feast_planner_open", receipt.with("planning_stage", n(2)), false, "available"));
        assertDoesNotThrow(() -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIGURE, args, identity(9), identity(10), stageTwoAck, diagnosticRead(2), post));
        assertThrows(IllegalArgumentException.class, () -> NativeFeastEffects.materialValues(OrdinaryFeastPolicy.CONFIGURE, args, identity(9), identity(10), ack, diagnosticRead(5), post));
    }
}
