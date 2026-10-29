package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** Native finalizer -> owning material reducer -> persistent original ledger round trip. No Game qualification is claimed. */
final class ConstructionMaterialReducerTest {
    @Test void aFailedPreIntentPublicationNeedsCompleteNativeNegativeProofAndCannotClearUnknown() {
        String digest = "c".repeat(64);
        Obj pending = ConstructionCoordinatorPendingTest.original().with("status", new Text("java_intent_prepared"))
                .with("coordinator_action_id", new Text("actual-pre-intent-failure"))
                .with("coordinator_body_sha256", new Text(digest))
                .with("action_request_id", new Text(org.xar.ck3.control.application.action.RequestIds.forActionBody(digest)));
        Obj original = ledger().with("pending", pending).with("applied", Nil.INSTANCE);
        var body = ConstructionLedgerCodec.decodeLedger(encode(original));
        Obj recovered = ConstructionDomainLifecycle.preparedZeroDispatchBody(body, query(100, 100, false, false)).orElseThrow();
        assertEquals(Nil.INSTANCE, recovered.get("pending"));
        Obj proof = object(recovered.get("last_pre_intent_zero_dispatch"), "actual zero-dispatch proof");
        assertEquals(n(0), proof.get("native_submit_calls")); assertEquals(new Bool(false), proof.get("replay_allowed"));
        assertEquals(pending, proof.get("original_pending"));
        assertTrue(ConstructionDomainLifecycle.preparedZeroDispatchBody(body, query(100, 75, true, false)).isEmpty());
        assertTrue(ConstructionDomainLifecycle.preparedZeroDispatchBody(body, query(100, 99, false, false)).isEmpty());
        assertTrue(ConstructionDomainLifecycle.preparedZeroDispatchBody(body, query(110, 100, false, false)).isEmpty());
        var unknown = ConstructionLedgerCodec.decodeLedger(encode(original.with("pending", pending.with("status", new Text("action_state_unknown")))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionDomainLifecycle.preparedZeroDispatchBody(unknown, query(100, 100, false, false)));
        var dispatched = ConstructionLedgerCodec.decodeLedger(encode(original.with("pending", pending.with("native_ack", json("{}")))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionDomainLifecycle.preparedZeroDispatchBody(dispatched, query(100, 100, false, false)));
    }
    @Test void coldCompletionRetainsTheOriginalActionAndAllowsANewWorkerCounterNamespace() {
        Obj ledger = ledger(); Obj input = input(ledger, query(820, 75, false, true));
        var result = ConstructionMaterialReducer.reduce(encode(input));
        assertEquals(ConstructionMaterialReducer.Disposition.MATERIAL_UPDATED, result.disposition());
        Obj receipt = result.receipt().orElseThrow();
        assertEquals(new Text("completed"), receipt.get("completion_status"));
        assertEquals(n(820), receipt.get("completion_observed_date_raw"));
        assertEquals(n(5), receipt.get("pre_proof_epoch")); assertEquals(n(2), receipt.get("post_proof_epoch"));
        assertEquals(originalReceipt(), receipt.get("start_receipt"));
        assertEquals(object(originalReceipt().get("candidate"), "candidate"), receipt.get("candidate"));
        assertEquals(Nil.INSTANCE, receipt.get("observed_player_monthly_gold_income_raw"));
        assertNull(receipt.get("post_cash_v2"));
        assertEquals(result.originalBody(), ConstructionLedgerCodec.decodeLedger(encode(result.originalBody())).original());
    }
    @Test void earlyColdActiveReadKeepsTheOriginalMonthlyWatchSchedule() {
        var result = ConstructionMaterialReducer.reduce(encode(input(ledger(), query(110, 75, true, false))));
        Obj receipt = result.receipt().orElseThrow();
        assertEquals(n(100), receipt.get("completion_last_check_date_raw"));
        assertEquals(new Text("in_progress"), receipt.get("completion_status"));
        assertEquals(n(7), object(receipt.get("construction_progress_observation"), "progress").get("native_remaining_work_raw"));
        assertEquals(n(80), receipt.get("post_bridge_pid"));
    }
    @Test void missingProjectionRetainsPriorMaterialAndItsNewReadOnlyLeaseWithoutGrantingNewCredit() {
        var result = ConstructionMaterialReducer.reduce(encode(input(ledger(), query(900, 75, false, false))));
        assertEquals(ConstructionMaterialReducer.Disposition.PRIOR_MATERIAL_RETAINED, result.disposition());
        Obj receipt = result.receipt().orElseThrow();
        assertEquals(originalReceipt().get("post_proof_epoch"), receipt.get("post_proof_epoch"));
        assertEquals(originalReceipt().get("post_date_raw"), receipt.get("post_date_raw"));
        Obj observation = object(receipt.get("material_observation_unavailable_v1"), "unavailable read");
        assertEquals(new Bool(false), observation.get("business_submission")); assertEquals(n(0), observation.get("native_submit_calls"));
        assertEquals(n(1620), observation.get("retry_not_before_date_raw"));
        var decoded = ConstructionLedgerCodec.decodeLedger(encode(result.originalBody())).applied().orElseThrow();
        assertEquals(BigInteger.valueOf(900), decoded.observed().dateRaw());
    }
    @Test void anActualPreActionRestoredWorldRemovesOnlyItsVerifiedReceiptAndNeverReplays() {
        var result = ConstructionMaterialReducer.reduce(encode(input(ledger(), query(100, 100, false, false))));
        assertEquals(ConstructionMaterialReducer.Disposition.RESTORED_BEFORE_ACTION, result.disposition());
        assertEquals(Nil.INSTANCE, result.originalBody().get("applied"));
        assertEquals(new Bool(false), result.observation().get("replay_allowed")); assertEquals(n(0), result.observation().get("native_submit_calls"));
    }
    @Test void unresolvedIntentConflictingMaterialAndWrongTypesCannotBecomeCompleted() {
        Obj pending = originalReceipt(); Obj unresolved = ledger().with("pending", pending);
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(encode(input(unresolved, query(820, 75, false, true)))));
        Obj conflicting = query(820, 75, true, true);
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(encode(input(ledger(), conflicting))));
        Obj sameDateWrongWallet = query(100, 99, true, false);
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(encode(input(ledger(), sameDateWrongWallet))));
        Obj wrong = query(820, 75, false, true); Obj envelope = object(wrong.get("native_envelope"), "envelope");
        Obj result = object(envelope.get("result"), "result"), probe = object(result.get("private_probe"), "probe");
        Obj invalid = wrong.with("native_envelope", envelope.with("result", result.with("private_probe", probe.with("proof_epoch", new Bool(true)))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(encode(input(ledger(), invalid))));
    }
    @Test void verifiedStartMergesTheFullOriginalCandidateAndRejectsAnObservedDifferentSelection() {
        var intent = ConstructionLedgerCodec.intent(originalReceipt());
        Obj effect = obj("status", new Text("applied"), "postcondition_verified", new Bool(true), "completion_status", new Text("in_progress"),
                "action_request_id", new Text("original-request"), "episode_run_id", new Text("episode"), "actor_character_id", n(1),
                "post_proof_epoch", n(6), "post_native_revision", n(3), "post_date_raw", n(100), "post_player_gold_raw", n(75), "candidate", tuple(), "native_query_request_id", new Text("actual-start-material-read"));
        Obj snapshot = snapshot(100).with("diagnostics", obj("bridge_pid", n(42), "bridge_creation_date", new Text("old-process")));
        Obj merged = ConstructionMaterialReducer.confirmedStart(intent, effect, snapshot);
        assertEquals(object(originalReceipt().get("candidate"), "candidate"), merged.get("candidate"));
        Obj changed = effect.with("candidate", tuple().with("building_type_id", n(12)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.confirmedStart(intent, changed, snapshot));
    }
    @Test void normalCashKeepsTheFirstSignedIncomeAndOriginalDateShape() {
        Obj completed = completedLedger();
        Obj root = rootIncome(900, 999);
        Obj cash = partialCash(900, Optional.of(BigInteger.valueOf(123)));
        for (long first : new long[]{0, -1, 7}) {
            for (int dateShape = 0; dateShape < 3; dateShape++) {
                Obj receipt = object(completed.get("applied"), "completed receipt")
                        .with("observed_player_monthly_gold_income_raw", n(first));
                receipt = dateShape == 0 ? without(receipt, "income_observed_date_raw")
                        : receipt.with("income_observed_date_raw", dateShape == 1 ? Nil.INSTANCE : n(820));
                Obj original = completed.with("applied", receipt);
                Obj updated = refresh(original, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, Optional.of(root), Optional.of(cash)).receipt().orElseThrow();
                assertEquals(n(first), updated.get("observed_player_monthly_gold_income_raw"));
                assertEquals(receipt.members().containsKey("income_observed_date_raw"), updated.members().containsKey("income_observed_date_raw"));
                assertEquals(receipt.get("income_observed_date_raw"), updated.get("income_observed_date_raw"));
                assertEquals(cash, updated.get("post_cash_v2"));
                assertEquals(new Text("completed"), updated.get("completion_status"));
            }
        }
    }
    @Test void normalCashFillsOnlyMissingIncomeFromTheSameFrameGrossAndAcceptsOtherUnknownRates() {
        Obj original = completedLedger();
        for (long gross : new long[]{0, -1, 123}) {
            Obj cash = partialCash(900, Optional.of(BigInteger.valueOf(gross)));
            Obj updated = refresh(original, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, Optional.empty(), Optional.of(cash)).receipt().orElseThrow();
            assertEquals(n(gross), updated.get("observed_player_monthly_gold_income_raw"));
            assertEquals(n(900), updated.get("income_observed_date_raw"));
            assertEquals(Nil.INSTANCE, object(updated.get("post_cash_v2"), "original partial cash").get("player_monthly_net_income"));
            assertEquals(cash, updated.get("post_cash_v2"));
            assertEquals(updated, ConstructionLedgerCodec.decodeLedger(encode(original.with("applied", updated))).applied().orElseThrow().original());
        }
        Obj noCash = refresh(original, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, Optional.of(rootIncome(900, 999)), Optional.empty()).receipt().orElseThrow();
        assertEquals(n(999), noCash.get("observed_player_monthly_gold_income_raw"));
        assertEquals(n(900), noCash.get("income_observed_date_raw"));
        assertNull(noCash.get("post_cash_v2"));
    }
    @Test void normalCashUnknownGrossKeepsTheOriginalCashWhileColdRetainsItsExistingAttachmentRule() {
        Obj completed = completedLedger();
        Obj oldCash = partialCash(820, Optional.of(BigInteger.valueOf(23)));
        Obj old = object(completed.get("applied"), "completed receipt").with("post_cash_v2", oldCash);
        Obj current = partialCash(900, Optional.empty());
        Obj normal = refresh(completed.with("applied", old), ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                Optional.of(rootIncome(900, 999)), Optional.of(current)).receipt().orElseThrow();
        assertEquals(oldCash, normal.get("post_cash_v2"));
        assertEquals(n(999), normal.get("observed_player_monthly_gold_income_raw"));
        assertEquals(n(900), normal.get("income_observed_date_raw"));
        Obj noOldCash = refresh(completed, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                Optional.empty(), Optional.of(current)).receipt().orElseThrow();
        assertNull(noOldCash.get("post_cash_v2"));
        Obj knownIncome = object(completed.get("applied"), "completed receipt")
                .with("observed_player_monthly_gold_income_raw", n(7)).with("income_observed_date_raw", n(820));
        Obj knownWithoutCash = refresh(completed.with("applied", knownIncome), ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                Optional.empty(), Optional.of(current)).receipt().orElseThrow();
        assertEquals(n(7), knownWithoutCash.get("observed_player_monthly_gold_income_raw"));
        assertNull(knownWithoutCash.get("post_cash_v2"));
        Obj cold = refresh(completed, ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL,
                Optional.of(rootIncome(900, 999)), Optional.of(current)).receipt().orElseThrow();
        assertEquals(n(999), cold.get("observed_player_monthly_gold_income_raw"));
        assertEquals(n(900), cold.get("income_observed_date_raw"));
        assertEquals(current, cold.get("post_cash_v2"));
    }
    @Test void legacyBytesKeepTheirColdAlgorithmAndV2KindsCannotInventCompletionOrZeroDispatch() {
        Obj previous = completedLedger();
        Obj old = object(previous.get("applied"), "completed receipt").with("observed_player_monthly_gold_income_raw", n(7))
                .with("income_observed_date_raw", Nil.INSTANCE);
        previous = previous.with("applied", old);
        Obj legacy = input(previous, query(900, 75, false, true)).with("root", rootIncome(900, -9));
        byte[] archived = encode(legacy);
        var decoded = ConstructionMaterialReducer.decode(archived);
        assertEquals(ConstructionMaterialReducer.InputVersion.LEGACY_V1, decoded.version());
        assertTrue(decoded.refreshKind().isEmpty());
        var fallback = ConstructionMaterialReducer.reduce(encode(input(previous, query(900, 75, false, true)))).receipt().orElseThrow();
        assertEquals(n(7), fallback.get("observed_player_monthly_gold_income_raw"));
        assertEquals(n(820), fallback.get("income_observed_date_raw"));
        var replayed = ConstructionMaterialReducer.reduce(archived);
        var cold = refresh(previous, ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL, Optional.of(rootIncome(900, -9)), Optional.empty());
        assertArrayEquals(encode(replayed.originalBody()), encode(cold.originalBody()));
        assertEquals(n(-9), replayed.receipt().orElseThrow().get("observed_player_monthly_gold_income_raw"));
        assertEquals(n(900), replayed.receipt().orElseThrow().get("income_observed_date_raw"));
        Obj normal = ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                ConstructionLedgerCodec.decodeLedger(encode(ledger())), "original-request", query(900, 75, false, true), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(encode(normal)));
        Obj zero = ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.PREPARED_ZERO_DISPATCH,
                ConstructionLedgerCodec.decodeLedger(encode(completedLedger())), "original-request", query(900, 75, false, true), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(encode(zero)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.decode(encode(legacy.with("refresh_kind", new Text("COLD_MATERIAL")))));
        for (Value invalid : List.<Value>of(Nil.INSTANCE, new Bool(true), n(1), new DecimalValue("1.0"), new Text("UNKNOWN"))) {
            Obj invalidInput = zero.with("refresh_kind", invalid);
            assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.decode(encode(invalidInput)));
        }
        assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.decode(encode(without(zero, "refresh_kind"))));
    }
    @Test void missingCompletedIncomeUsesTheActualRootOnlyAfterTheGrossSourceIsUnavailable() {
        for (long raw : new long[]{0, -1, 17}) {
            for (boolean missingField : new boolean[]{false, true}) {
                Obj original = completedLedger();
                if (missingField) original = original.with("applied", without(object(original.get("applied"), "prior"), "observed_player_monthly_gold_income_raw"));
                for (Optional<Obj> cash : List.of(Optional.<Obj>empty(), Optional.of(partialCash(900, Optional.empty())))) {
                    Obj updated = refresh(original, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, Optional.of(rootIncome(900, raw)), cash).receipt().orElseThrow();
                    assertEquals(n(raw), updated.get("observed_player_monthly_gold_income_raw"));
                    assertEquals(n(900), updated.get("income_observed_date_raw"));
                    assertNull(updated.get("post_cash_v2"));
                    assertEquals(updated, ConstructionLedgerCodec.decodeLedger(encode(original.with("applied", updated))).applied().orElseThrow().original());
                }
            }
        }
        Obj cashFirst = refresh(completedLedger(), ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                Optional.of(rootIncome(900, 999)), Optional.of(partialCash(900, Optional.of(BigInteger.valueOf(-7))))).receipt().orElseThrow();
        assertEquals(n(-7), cashFirst.get("observed_player_monthly_gold_income_raw"));
        for (Obj noIncome : List.of(without(rootIncome(900, 1), "player_monthly_gold_income"), rootIncome(900, 1).with("player_monthly_gold_income", Nil.INSTANCE))) {
            Obj unchanged = refresh(completedLedger(), ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                    Optional.of(noIncome), Optional.empty()).receipt().orElseThrow();
            assertEquals(Nil.INSTANCE, unchanged.get("observed_player_monthly_gold_income_raw"));
            assertNull(unchanged.get("post_cash_v2"));
        }
        Obj root = rootIncome(900, 7);
        for (Obj wrong : List.of(root.with("status", new Text("unavailable")), root.with("player_character_id", n(2)),
                root.with("snapshot_revision", n(4)), root.with("date_raw", n(901)),
                root.with("player_monthly_gold_income", money(7).with("raw", new Bool(true))),
                root.with("player_monthly_gold_income", money(7).with("scale", n(1))))) {
            assertThrows(IllegalArgumentException.class, () -> refresh(completedLedger(), ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                    Optional.of(wrong), Optional.empty()));
        }
    }
    @Test void normalCashStillRejectsCrossedFramesTypesAndNonCurrentPackets() {
        Obj previous = completedLedger();
        Obj valid = partialCash(900, Optional.of(BigInteger.ONE));
        for (Obj wrong : List.of(valid.with("date_raw", n(901)), valid.with("played_character_id", n(2)), valid.with("snapshot_revision", n(4)),
                valid.with("player_monthly_gross_income", money(1).with("raw", new Bool(true))))) {
            assertThrows(IllegalArgumentException.class, () -> refresh(previous, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, Optional.empty(), Optional.of(wrong)));
        }
        Obj notSameFrame = valid.with("readiness", object(valid.get("readiness"), "readiness").with("same_frame_ready", new Bool(false)));
        Obj untouched = refresh(previous, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, Optional.empty(), Optional.of(notSameFrame)).receipt().orElseThrow();
        assertEquals(Nil.INSTANCE, untouched.get("observed_player_monthly_gold_income_raw"));
        assertNull(untouched.get("post_cash_v2"));
        assertThrows(IllegalArgumentException.class, () -> refresh(previous, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                Optional.of(rootIncome(901, 999)), Optional.of(valid)));
        for (BigInteger outside : List.of(BigInteger.ONE.shiftLeft(63), BigInteger.ONE.shiftLeft(63).negate().subtract(BigInteger.ONE))) {
            Obj wrongRoot = rootIncome(900, 999).with("player_monthly_gold_income", money(999).with("raw", new IntegerValue(outside)));
            assertThrows(IllegalArgumentException.class, () -> refresh(previous, ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                    Optional.of(wrongRoot), Optional.of(valid)));
        }
    }
    private static ConstructionMaterialReducer.Reduced refresh(Obj original, ConstructionMaterialReducer.RefreshKind kind,
            Optional<Obj> root, Optional<Obj> cash) {
        Obj input = ConstructionMaterialReducer.input(kind, ConstructionLedgerCodec.decodeLedger(encode(original)), "original-request",
                query(900, 75, false, true), root, cash);
        return ConstructionMaterialReducer.reduce(encode(input));
    }
    private static Obj completedLedger() { return ConstructionMaterialReducer.reduce(encode(input(ledger(), query(820, 75, false, true)))).originalBody(); }
    private static Obj without(Obj original, String field) { var members = new java.util.LinkedHashMap<>(original.members()); members.remove(field); return new Obj(members); }
    private static Obj rootIncome(long date, long raw) {
        return obj("status", new Text("available"), "player_character_id", n(1), "snapshot_revision", n(3), "date_raw", n(date),
                "player_monthly_gold_income", money(raw));
    }
    /** A source-valid software cash producer with observed GROSS and deliberately unavailable EXPENSES/NET. */
    private static Obj partialCash(long date, Optional<BigInteger> gross) {
        Obj readiness = obj("same_frame_ready", new Bool(true), "current_treasury_ready", new Bool(true),
                "monthly_gross_income_ready", new Bool(gross.isPresent()), "monthly_total_expenses_ready", new Bool(false),
                "monthly_net_income_ready", new Bool(false), "current_military_expenses_ready", new Bool(true), "all_raised_military_expenses_ready", new Bool(true));
        return obj("schema", new Text("xar.ck3.war-cash-current-resources.v1"), "read_only", new Bool(true), "advertised", new Bool(false),
                "formal_action_ready", new Bool(false), "status", new Text("partial"), "game_version", new Text("1.20.0.4"),
                "executable_sha256", new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"),
                "played_character_id", n(1), "snapshot_revision", n(3), "date_raw", n(date), "queried_snapshot_id", new Text("native:3"),
                "queried_revision", n(3), "queried_native_revision", n(3), "active_war_ids", new Arr(List.of()), "player_army_ids", new Arr(List.of()),
                "current_treasury", money(75), "player_monthly_gross_income", gross.<Value>map(value -> money(value.longValueExact())).orElse(Nil.INSTANCE),
                "player_monthly_total_expenses", Nil.INSTANCE, "player_monthly_net_income", Nil.INSTANCE,
                "monthly_gross_income_unavailable_reason", gross.isPresent() ? Nil.INSTANCE : new Text("fixture_gross_unavailable"),
                "monthly_total_expenses_unavailable_reason", new Text("fixture_expenses_unavailable"),
                "monthly_net_income_unavailable_reason", new Text("fixture_net_unavailable"),
                "monthly_income_semantics", obj("version", new Text("ck3-1.20.0.4-native-income-minus-total-expenses-v2"),
                        "time_basis", new Text("month"), "source_scope", new Text("played_character_personal_gold"),
                        "income_source", new Text("native_character_monthly_gold_income"), "expense_source", new Text("native_character_monthly_total_gold_expenses"),
                        "military_expenses_included", new Bool(true)),
                "readiness", readiness, "military_expenses", obj("current", military(), "all_raised", military()));
    }
    private static Obj military() {
        var vector = new java.util.ArrayList<Value>(); for (int i = 0; i < 10; i++) vector.add(n(0));
        return obj("status", new Text("available"), "owner_character_id", n(1), "resource_id", new Text("1"), "war_ids", new Arr(List.of()),
                "raw_scale", n(100000), "time_basis", new Text("month"), "source_scope", new Text("actor_owned_military_once_across_all_wars"),
                "future_war_cost_upper_ready", new Bool(false), "resource_raw_native", new Arr(vector), "gold_raw", n(0), "treasury_raw", n(0));
    }
    private static Obj money(long raw) { return obj("raw", n(raw), "scale", n(100000)); }
    private static Obj input(Obj ledger, Obj observation) {
        // Retain the original archived six-field producer input for all historical branch regressions.
        return obj("schema", new Text("xar.construction-material-reducer-input/v1"), "ledger", ledger,
                "action_request_id", new Text("original-request"), "query_observation", observation, "root", Nil.INSTANCE, "cash", Nil.INSTANCE);
    }
    private static Obj ledger() { return obj("schema", new Text(ConstructionLedgerCodec.SCHEMA), "pending", Nil.INSTANCE, "applied", originalReceipt(), "applied_prior", new Arr(List.of())); }
    private static Obj originalReceipt() {
        return json("{\"action_request_id\":\"original-request\",\"episode_run_id\":\"episode\",\"actor_character_id\":1,\"pre_native_revision\":2,\"pre_date_raw\":100,\"pre_proof_epoch\":5,\"source_bridge_pid\":42,\"source_bridge_creation_date\":\"old-process\",\"status\":\"applied\",\"postcondition_verified\":true,\"completion_status\":\"in_progress\",\"post_native_revision\":3,\"post_date_raw\":100,\"post_proof_epoch\":6,\"post_bridge_pid\":42,\"post_bridge_creation_date\":\"old-process\",\"completion_last_check_date_raw\":100,\"candidate\":{\"barony_title_id\":2,\"province_id\":3,\"building_type_id\":11,\"slot_index\":0,\"gold_before_raw\":100,\"stock_gold_cost_raw\":25}}");
    }
    private static Obj tuple() { return obj("barony_title_id", n(2), "province_id", n(3), "building_type_id", n(11), "slot_index", n(0)); }
    private static Obj snapshot(long date) {
        return obj("snapshot_id", new Text("native:3"), "revision", n(3), "native_revision", n(3), "date_raw", n(date), "episode_run_id", new Text("episode"),
                "paused", new Bool(true), "map_ready", new Bool(true), "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "played_character", obj("character_id", n(1), "alive", new Bool(true)), "active_wars", new Arr(List.of()), "player_armies", new Arr(List.of()),
                "diagnostics", obj("bridge_pid", n(80), "bridge_creation_date", new Text("new-process"), "hello", obj("expected_ck3_version", new Text("1.20.0.4"),
                        "expected_ck3_sha256", new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"))));
    }
    private static Obj query(long date, long gold, boolean active, boolean complete) {
        Obj idle = obj("barony_title_id", n(2), "province_id", n(3), "active", new Bool(false),
                "native_province_monthly_income_observed", new Bool(false), "native_province_monthly_income_raw", Nil.INSTANCE);
        Obj activeRow = tuple().with("active", new Bool(true)).with("initiator_character_id", n(1)).with("native_remaining_work_raw", n(7))
                .with("native_progress_divisor_raw", n(2)).with("native_province_monthly_income_observed", new Bool(false)).with("native_province_monthly_income_raw", Nil.INSTANCE);
        Obj world = obj("status", new Text("source_available"), "snapshot_revision", n(3), "date_raw", n(date), "player_character_id", n(1),
                "native_final_legality_evaluated", new Bool(true), "native_cost_evaluated", new Bool(false), "player_gold_raw", n(gold),
                "active_constructions", new Arr(List.of(active ? activeRow : idle)), "completed_buildings_observed", new Bool(true),
                "completed_buildings", new Arr(complete ? List.of(tuple()) : List.of()), "positive_income_coverage_complete", new Bool(true), "legal_samples", new Arr(List.of()));
        Obj probe = obj("advertised", new Bool(false), "snapshot_revision", n(3), "date_raw", n(date), "proof_epoch", n(2), "player_world_building_sources", world);
        Obj envelope = obj("type", new Text("command_result"), "protocol_version", n(1), "request_id", new Text("current-material-read"), "ok", new Bool(true),
                "result", obj("step", new Text("g2_player_construction_view_probe_v1"), "accepted", new Bool(true), "private_probe", probe));
        return obj("schema", new Text("xar.construction-query-observation-input.v1"), "starting_snapshot", snapshot(date), "ending_snapshot", snapshot(date),
                "native_envelope", envelope, "expected_revision", n(3), "native_query_request_id", new Text("current-material-read"), "material_receipt", new Bool(true), "wartime_observation", new Bool(false));
    }
    private static IntegerValue n(long number) { return new IntegerValue(BigInteger.valueOf(number)); }
    private static Obj json(String value) { return object(parse(value.getBytes(StandardCharsets.UTF_8)), "fixture object"); }
}
