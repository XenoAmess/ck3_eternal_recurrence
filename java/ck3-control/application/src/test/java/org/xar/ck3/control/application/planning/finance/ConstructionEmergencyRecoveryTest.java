package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;

/** Real persistent mercenary decoder -> construction recovery consumer -> the sole source-bound finance producer. */
final class ConstructionEmergencyRecoveryTest {
    @Test void peacefulConstructionStillDefersAfterEmergencySpendingUntilTheObservedBufferReturns() {
        Obj snapshot = snapshot(19_999_999), root = root();
        var original = body(claim(), true);
        Obj recovery = OrdinaryConstructionPolicy.emergencyRecovery(snapshot, original, Optional.of(root)).orElseThrow();
        assertEquals(new Text("recovering_emergency_cash_buffer"), recovery.get("status"));
        assertEquals(new Bool(true), recovery.get("defer_new_economic_construction"));
        assertEquals(new Bool(true), recovery.get("unknown_pending_preserved"));
        assertEquals(n(20_000_000), recovery.get("normal_reserve_target_raw"));
        assertEquals(n(0), recovery.get("future_income_credited_raw"));
        assertEquals(new Arr(List.of()), snapshot.get("active_wars"));
        Obj restored = OrdinaryConstructionPolicy.emergencyRecovery(snapshot(20_000_000), original, Optional.of(root)).orElseThrow();
        assertEquals(new Text("normal_buffer_restored"), restored.get("status"));
        assertEquals(new Bool(false), restored.get("defer_new_economic_construction"));
        assertEquals(new Bool(true), restored.get("unknown_pending_preserved"));
        assertTrue(MercenaryProcurement.decode(original.document().bytes()).pending().isPresent());
        assertEquals(original.original(), MercenaryProcurement.decode(original.document().bytes()).original());
        // A large income observation never funds current optional spending.
        Obj highIncome = root.with("player_monthly_gold_income", obj("raw", n(900_000_000), "scale", n(100_000)));
        assertEquals(new Bool(true), OrdinaryConstructionPolicy.emergencyRecovery(snapshot, original, Optional.of(highIncome))
                .orElseThrow().get("defer_new_economic_construction"));
    }
    @Test void sourceDriftUnavailableRootAndTypedBodyMismatchCannotGrantRecoveryCredit() {
        var original = body(claim(), true);
        Obj stale = root().with("snapshot_revision", n(10));
        Obj unknown = OrdinaryConstructionPolicy.emergencyRecovery(snapshot(50_000_000), original, Optional.of(stale)).orElseThrow();
        assertEquals(new Bool(false), unknown.get("finance_observed"));
        assertEquals(new Bool(true), unknown.get("defer_new_economic_construction"));
        assertEquals(new Bool(true), OrdinaryConstructionPolicy.emergencyRecovery(snapshot(50_000_000), original, Optional.empty())
                .orElseThrow().get("defer_new_economic_construction"));
        var mismatched = new FinanceStatePort.Ledger(original.document(), original.original().with("pending", Nil.INSTANCE), FinanceStatePort.Pending.CLEAR);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionPolicy.emergencyRecovery(snapshot(50_000_000), mismatched, Optional.of(root())));
        var wrongDomain = new FinanceStatePort.Document(FinanceStatePort.Domain.CONSTRUCTION, original.document().original(), original.document().bytes());
        assertThrows(IllegalArgumentException.class, () -> OrdinaryConstructionPolicy.emergencyRecovery(snapshot(50_000_000),
                new FinanceStatePort.Ledger(wrongDomain, original.original(), original.pending()), Optional.of(root())));
    }
    @Test void rejectedAndOtherEpisodeEmergencyClaimsDoNotOpenARecoveryEpoch() {
        Obj rejected = claim().with("status", new Text("native_rejected"));
        assertTrue(OrdinaryConstructionPolicy.emergencyRecovery(snapshot(1), body(rejected, false), Optional.of(root())).isEmpty());
        assertTrue(OrdinaryConstructionPolicy.emergencyRecovery(snapshot(1).with("episode_run_id", new Text("other-episode")),
                body(claim(), true), Optional.of(root())).isEmpty());
    }
    private static FinanceStatePort.Ledger body(Obj claim, boolean pending) {
        Obj original = obj("schema", new Text(MercenaryProcurement.SCHEMA), "pending", pending ? claim : Nil.INSTANCE,
                "observed", new Arr(pending ? List.of() : List.of(claim)));
        byte[] bytes = encode(original);
        var ref = new ExactRef("C:/actual-source-test/original-mercenary.json", bytes.length, ActionCodec.sha256(bytes));
        var document = new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY, ref, bytes);
        var decoded = MercenaryProcurement.decode(document.bytes());
        return new FinanceStatePort.Ledger(document, decoded.original(), decoded.pending().isPresent() ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR);
    }
    private static Obj claim() {
        Obj source = obj("played_character_id", n(1), "native_revision", n(10), "date_raw", n(100),
                "snapshot_id", new Text("native-10"), "revision", n(10), "episode_run_id", new Text("actual-episode"));
        Obj emergency = obj("source_frame", source, "level", n(1), "epoch_id", new Text("actual-emergency"),
                "anchor_treasury_raw", n(50_000_000), "total_package_limit_raw", n(30_000_000), "ordinary_reserve_target_raw", n(20_000_000));
        return obj("action_request_id", new Text("actual-original-native"), "company_id", n(0), "status", new Text("submission_unresolved"),
                "pre_capture_epoch", n(10), "pre_player_army_ids", new Arr(List.of()), "source_frame", source,
                "decision", obj("selected_candidate", obj("emergency_budget_revision_v1", emergency)));
    }
    private static Obj snapshot(long gold) {
        return obj("played_character", obj("character_id", n(1), "alive", new Bool(true)),
                "native_revision", n(11), "date_raw", n(100), "snapshot_id", new Text("native-11"), "revision", n(11),
                "episode_run_id", new Text("actual-episode"), "paused", new Bool(true), "map_ready", new Bool(true),
                "active_wars", new Arr(List.of()), "player_armies", new Arr(List.of()),
                "played_character_gold", obj("raw", n(gold), "scale", n(100_000)));
    }
    private static Obj root() {
        return obj("status", new Text("available"), "player_character_id", n(1), "snapshot_revision", n(11), "date_raw", n(100),
                "player_monthly_gold_income", obj("raw", n(100_000), "scale", n(100_000)),
                "player_max_monthly_gold_maintenance_v1", obj("status", new Text("available"), "value", obj("raw", n(1_000_000), "scale", n(100_000))));
    }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
