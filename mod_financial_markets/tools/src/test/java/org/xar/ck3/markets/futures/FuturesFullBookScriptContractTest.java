package org.xar.ck3.markets.futures;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.Clausewitz.Value;

/** Actual production futures submit/match/reservation/allocation/archive/reduce scripts.
 * No matching or financial transfer port. Authored source fixtures are not a Game or physical SAVE. */
final class FuturesFullBookScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final List<String> INPUTS = List.of(
        "scripted_effects/xfm_futures_orders.txt", "scripted_effects/xfm_futures_match.txt",
        "scripted_effects/xfm_futures_fill_receipts.txt",
        "scripted_effects/xfm_futures_archive.txt", "scripted_effects/xfm_futures_reduce.txt",
        "scripted_effects/xfm_futures_liquidation.txt", "scripted_effects/xfm_futures_book_daily.txt",
        "scripted_effects/xfm_futures_identity.txt", "scripted_effects/xfm_futures_margin.txt",
        "scripted_effects/xfm_futures_daily_index.txt", "scripted_effects/xfm_futures_settlement.txt",
        "scripted_effects/xfm_futures_ai_funding.txt",
        "scripted_effects/xfm_futures_cancel_receipts.txt",
        "scripted_triggers/xfm_futures_cancel_triggers.txt", "script_values/xfm_futures_cancel_values.txt",
        "scripted_effects/xfm_finance_init.txt", "scripted_effects/xfm_finance_cash.txt",
        "scripted_effects/xfm_finance_reserve.txt", "scripted_effects/xfm_finance_split.txt",
        "scripted_effects/xfm_finance_policy.txt", "scripted_effects/xfm_issuer_governance.txt",
        "scripted_triggers/xfm_finance_triggers.txt", "scripted_triggers/xfm_futures_triggers.txt",
        "scripted_triggers/xfm_futures_ai_triggers.txt", "script_values/xfm_finance_values.txt",
        "script_values/xfm_futures_values.txt", "script_values/xfm_futures_ai_values.txt",
        "script_values/xfm_numeric_comparison_values.txt", "script_values/xfm_config_values.txt");

    @Test void firstUnmatchedOrderRestsAndEnrolsOnlyAfterTheTransientEntryFinishes() throws IOException {
        Vm v = vm(); Node c = series(v, "series"), a = actor(v, "actor", 121);
        Node o = submit(v, a, c, 1, 1, 100);
        assertEquals(1, a.integer("xfm_futures_result")); assertNotNull(o);
        assertEquals(List.of(o), c.list("xfm_orders")); assertEquals(1, o.integer("xfm_indexed"));
        assertEquals(121, a.ref("xfm_account").integer("xfm_reserved_cents"));
        assertEquals(1, c.integer("xfm_futures_daily_queued")); assertEquals(1, v.exchange.integer("xfm_futures_daily_count"));
        assertEquals(1, v.exchange.integer("xfm_active_orders_count")); assertTrue(c.list("xfm_positions").isEmpty());
        assertBalanced(v);
    }
    @Test void fullOpeningBookFormsARealPairWithoutAnExtraRestingSlot() throws IOException {
        Vm v = vm(); Node c = series(v, "series"); List<Node> bids = fullBook(v, c, 1, 100);
        Node a = actor(v, "seller", 121); BigDecimal cash = v.cashStock();
        Node o = submit(v, a, c, 2, 1, 100);
        assertEquals(1, a.integer("xfm_futures_result")); assertEquals(2, o.integer("xfm_status"));
        assertEquals(0, o.integer("xfm_indexed")); assertEquals(63, c.list("xfm_orders").size());
        assertEquals(63, c.integer("xfm_open_orders_count")); assertEquals(63, v.exchange.integer("xfm_active_orders_count"));
        Node p = c.list("xfm_positions").getFirst();
        assertEquals(1, p.integer("xfm_lots")); assertEquals(1, p.integer("xfm_position_id"));
        assertSame(bids.getFirst().ref("xfm_account"), p.ref("xfm_long_account")); assertSame(a.ref("xfm_account"), p.ref("xfm_short_account"));
        assertEquals(100, p.ref("xfm_long_reservation").integer("xfm_remaining_cents"));
        assertEquals(100, p.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
        assertEquals(2, v.exchange.integer("xfm_fee_cents")); assertEquals(64, v.maxFuturesBookEntries);
        assertEquals(cash, v.cashStock()); assertBalanced(v);
    }
    @Test void originalThirtyTwoFillAndPositionCapsRemainBindingAfterFullBookAdmission() throws IOException {
        Vm v = vm(); Node c = series(v, "series"); List<Node> bids = fullBook(v, c, 1, 100);
        Node a = actor(v, "seller", 8546); BigDecimal cash = v.cashStock();
        Node o = submit(v, a, c, 2, 71, 100);
        assertEquals(32, c.list("xfm_positions").size()); assertEquals(32, a.ref("xfm_account").integer("xfm_open_positions_count"));
        assertEquals(39, o.integer("xfm_remaining_lots")); assertEquals(1, o.integer("xfm_indexed"));
        assertEquals(33, c.list("xfm_orders").size()); assertEquals(32, v.maxFuturesMatchIterations);
        assertEquals(bids.subList(0,32).stream().map(b -> b.ref("xfm_account")).toList(),
            c.list("xfm_positions").stream().map(p -> p.ref("xfm_long_account")).toList());
        assertEquals(10, o.integer("xfm_fee_paid_cents")); assertEquals(4694, o.ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(7894, a.ref("xfm_account").integer("xfm_reserved_cents")); assertEquals(642, a.ref("xfm_account").integer("xfm_free_cents"));
        assertEquals(cash, v.cashStock()); assertBalanced(v);
    }
    @Test void fullAccountSettlesFillsButCancelsAndReturnsOnlyItsUnplaceableRemainder() throws IOException {
        Vm v = vm(); Node c = series(v, "series"), other = series(v, "other"); Node a = actor(v, "seller", 12418);
        for (int i=0;i<32;i++) assertNotNull(submit(v,a,other,1,1,100));
        fullBook(v,c,1,100); BigDecimal cash=v.cashStock();
        Node o=submit(v,a,c,2,71,100);
        assertEquals(32,c.list("xfm_positions").size()); assertEquals(3,o.integer("xfm_status"));
        assertCancelReceipt(o,16,1,4694,1);
        assertEquals(39,o.integer("xfm_capacity_cancelled_lots")); assertEquals(0,o.ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(32,a.ref("xfm_account").integer("xfm_open_orders_count")); assertEquals(32,other.list("xfm_orders").size());
        assertEquals(32,c.list("xfm_orders").size()); assertEquals(7072,a.ref("xfm_account").integer("xfm_reserved_cents"));
        assertEquals(5336,a.ref("xfm_account").integer("xfm_free_cents")); assertEquals(cash,v.cashStock()); assertBalanced(v);
    }
    @Test void noCrossRelatedCrossOrUnderfundedBookCannotFreezeMoneyAtCapacity() throws IOException {
        for (String defect:List.of("no-cross","related","underfunded","fee-only")) {
            Vm v=vm();Node c=series(v,"series");List<Node> bids=fullBook(v,c,1,100);Node a=actor(v,"seller",121);
            if(defect.equals("related")) bids.getLast().ref("xfm_account").put("xfm_holder",a);
            if(defect.equals("underfunded") || defect.equals("fee-only")) for(Node b:bids) {
                b.ref("xfm_reservation").put("xfm_request_cents",defect.equals("fee-only")?1:120);v.run("xfm_finance_release_effect",b.ref("xfm_reservation"));
            }
            BigDecimal cash=v.cashStock();int allocations=v.created("xfm_futures_order");
            assertNull(submit(v,a,c,2,1,defect.equals("no-cross")?101:100),defect);
            assertEquals(0,a.integer("xfm_futures_result"));assertEquals(121,a.ref("xfm_account").integer("xfm_free_cents"));
            assertEquals(0,a.ref("xfm_account").integer("xfm_reserved_cents"));assertEquals(allocations,v.created("xfm_futures_order"));
            assertEquals(bids,c.list("xfm_orders"));assertTrue(c.list("xfm_positions").isEmpty());assertEquals(cash,v.cashStock());assertBalanced(v);
        }
        // Actual four-lot position -> actual reducing order. Its remaining fee is two cents,
        // even before the first fill has ever populated remaining_notional.
        Vm v=vm();Node c=series(v,"reduce-fee"), la=actor(v,"long",2000), sa=actor(v,"short",2000);
        submit(v,la,c,1,4,100);submit(v,sa,c,2,4,100);Node p=c.list("xfm_positions").getFirst();
        la.put("xfm_futures_selected_position",p);la.put("xfm_futures_reduce_lots",4);la.put("xfm_futures_limit_cents",100);
        v.run("xfm_futures_reduce_effect",la);assertEquals(1,la.integer("xfm_futures_result"));
        Node close=c.list("xfm_orders").getFirst();assertTrue(close.vars.containsKey("xfm_reduce_order"));
        assertFalse(close.vars.containsKey("xfm_remaining_notional"));
        assertEquals(2,v.integerValue("xfm_futures_order_required_reserve_value",close));
        Node reservation=close.ref("xfm_reservation");assertEquals(2,reservation.integer("xfm_remaining_cents"));
        BigDecimal cash=v.cashStock();reservation.put("xfm_request_cents",1);v.run("xfm_finance_release_effect",reservation);
        assertEquals(1,reservation.integer("xfm_remaining_cents"));
        assertTrue(v.test(v.definition("xfm_finance_reservation_usable_trigger"),new Frame(reservation,null,reservation)));
        assertFalse(v.test(v.definition("xfm_futures_order_collateralized_trigger"),new Frame(close,null,close)));
        assertEquals(4,p.integer("xfm_lots"));assertEquals(cash,v.cashStock());assertBalanced(v);
    }
    @Test void insufficientCashPositionLimitAndStaleOracleRefuseBeforeReservation() throws IOException {
        for(String defect:List.of("cash","position-cap","global-cap","oracle")) {
            Vm v=vm();Node c=series(v,"series");fullBook(v,c,1,100);Node a=actor(v,"seller",defect.equals("cash")?120:121);
            if(defect.equals("position-cap"))a.ref("xfm_account").put("xfm_open_positions_count",32);
            if(defect.equals("global-cap"))v.exchange.put("xfm_futures_open_positions_count",4096);
            if(defect.equals("oracle"))c.ref("xfm_coin").put("xfm_oracle_day",0);
            BigDecimal cash=v.cashStock();int allocations=v.created("xfm_futures_order");
            assertNull(submit(v,a,c,2,1,100),defect);assertEquals(0,a.integer("xfm_futures_result"));
            assertEquals(0,a.ref("xfm_account").integer("xfm_reserved_cents"));assertEquals(allocations,v.created("xfm_futures_order"));
            assertEquals(64,c.list("xfm_orders").size());assertEquals(cash,v.cashStock());
        }
    }
    @Test void allocationFailureDoesNotInventAPositionOrChargeFeesAndReturnsTransientCollateral() throws IOException {
        Vm v=vm();Node c=series(v,"series");fullBook(v,c,1,100);Node a=actor(v,"seller",121);
        v.failType="xfm_futures_position";BigDecimal cash=v.cashStock();Node o=submit(v,a,c,2,1,100);
        assertNotNull(o);assertEquals(3,o.integer("xfm_status"));assertEquals(1,o.integer("xfm_capacity_cancelled_lots"));
        assertTrue(c.list("xfm_positions").isEmpty());assertEquals(0,v.exchange.integer("xfm_fee_cents"));
        assertEquals(121,a.ref("xfm_account").integer("xfm_free_cents"));assertEquals(0,a.ref("xfm_account").integer("xfm_reserved_cents"));
        assertEquals(64,c.list("xfm_orders").size());assertEquals(cash,v.cashStock());assertBalanced(v);
    }
    @Test void aRealElevenLotPairSupportsAnActualPartialThreeLotNovation() throws IOException {
        Vm v=vm();Node c=series(v,"series"), longActor=actor(v,"long",26980), shortActor=actor(v,"short",1324);
        // Exact output from the actual bounded AI size producer flows unchanged into the actual submitter.
        longActor.ai=true;longActor.put("xfm_selected_coin",c.ref("xfm_coin"));longActor.put("xfm_futures_contract",c);
        longActor.put("xfm_futures_leverage",1);longActor.put("xfm_futures_side",1);longActor.put("xfm_futures_limit_cents",100);
        v.run("xfm_futures_ai_size_order_effect",longActor);
        assertEquals(1,longActor.integer("xfm_futures_ai_size_result"));assertEquals(11,longActor.integer("xfm_futures_lots"));
        assertEquals(1324,longActor.integer("xfm_futures_reserve_cents"));
        v.run("xfm_futures_submit_effect",longActor);assertEquals(1,longActor.integer("xfm_futures_result"));
        submit(v,shortActor,c,2,11,100);
        assertEquals(1,c.list("xfm_positions").size());Node original=c.list("xfm_positions").getFirst();
        assertEquals(11,original.integer("xfm_lots"));long id=original.integer("xfm_position_id");
        Node replacement=actor(v,"replacement",362);submit(v,replacement,c,1,3,100);
        longActor.put("xfm_futures_selected_position",original);longActor.put("xfm_futures_reduce_lots",3);longActor.put("xfm_futures_limit_cents",100);
        BigDecimal cash=v.cashStock();v.run("xfm_futures_reduce_effect",longActor);
        assertEquals(1,longActor.integer("xfm_futures_result"));assertEquals(8,original.integer("xfm_lots"));assertEquals(id,original.integer("xfm_position_id"));
        assertEquals(2,c.list("xfm_positions").size());Node novated=c.list("xfm_positions").getLast();
        assertEquals(3,novated.integer("xfm_lots"));assertSame(replacement.ref("xfm_account"),novated.ref("xfm_long_account"));
        assertSame(shortActor.ref("xfm_account"),novated.ref("xfm_short_account"));assertNotEquals(id,novated.integer("xfm_position_id"));
        assertEquals(800,original.ref("xfm_long_reservation").integer("xfm_remaining_cents"));assertEquals(800,original.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
        assertEquals(300,novated.ref("xfm_long_reservation").integer("xfm_remaining_cents"));assertEquals(300,novated.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
        assertEquals(26175,longActor.ref("xfm_account").integer("xfm_free_cents"));assertEquals(10,v.exchange.integer("xfm_fee_cents"));
        assertEquals(cash,v.cashStock());assertBalanced(v);
    }
    @Test void forcedExitAgainstASameSideFullBookNeverEntersA65thSlotOrErasesThePosition() throws IOException {
        Vm v=vm();Node c=series(v,"series"), la=actor(v,"long",1324), sa=actor(v,"short",1324);
        submit(v,la,c,1,11,100);submit(v,sa,c,2,11,100);Node p=c.list("xfm_positions").getFirst();
        fullBook(v,c,2,100);BigDecimal cash=v.cashStock();
        v.execute(substitute(v.definition("xfm_futures_post_exit_effect"),Clausewitz.parse("SIDE = long ORDER_SIDE = 2 LONG_EXIT = yes")),new Frame(p,null,p));
        assertEquals(64,c.list("xfm_orders").size());assertEquals(64,c.integer("xfm_open_orders_count"));
        assertEquals(64,v.exchange.integer("xfm_active_orders_count"));assertEquals(11,p.integer("xfm_lots"));assertEquals(0,p.integer("xfm_status"));
        assertEquals(1100,p.ref("xfm_long_reservation").integer("xfm_remaining_cents"));assertEquals(220,la.ref("xfm_account").integer("xfm_free_cents"));
        assertEquals(64,v.maxFuturesBookEntries);assertEquals(cash,v.cashStock());assertBalanced(v);
    }
    @Test void legacyIndexedOrdersWithoutTheNewMarkerArchiveExactlyOnce() throws IOException {
        Vm v=vm();Node c=series(v,"series"), a=actor(v,"actor",121);Node o=submit(v,a,c,1,1,100);
        o.vars.remove("xfm_indexed");v.run("xfm_futures_cancel_order_effect",o);v.run("xfm_futures_cancel_order_effect",o);
        assertTrue(c.list("xfm_orders").isEmpty());assertEquals(0,c.integer("xfm_open_orders_count"));
        assertEquals(0,a.ref("xfm_account").integer("xfm_open_orders_count"));assertEquals(0,v.exchange.integer("xfm_active_orders_count"));
        assertEquals(121,a.ref("xfm_account").integer("xfm_free_cents"));assertEquals(1,a.ref("xfm_account").list("xfm_futures_order_history").size());assertBalanced(v);
    }

    @Test void capacityRulesReachActualFuturesSubmitAndRealCancellationRecoversOneSlot() throws IOException {
        for (String rule : List.of("xfm_capacity_conservative", "xfm_capacity_standard", "xfm_capacity_extended")) {
            Vm v = vm(); v.rules.add(rule); Node c = series(v, "depth-series");
            int depth = rule.equals("xfm_capacity_conservative") ? 32 : rule.equals("xfm_capacity_extended") ? 128 : 64;
            List<Node> orders = fullDepth(v, c, depth); Node a = actor(v, "extra", 121);
            BigDecimal cash = v.cashStock(); int created = v.created("xfm_futures_order");
            assertNull(submit(v, a, c, 1, 1, 100)); assertEquals(0, a.integer("xfm_futures_result"));
            assertEquals(created, v.created("xfm_futures_order")); assertEquals(0, a.ref("xfm_account").integer("xfm_reserved_cents"));
            assertEquals(orders, c.list("xfm_orders")); assertEquals(cash, v.cashStock());
            Node removed = orders.getLast(); v.run("xfm_futures_cancel_order_effect", removed);
            assertEquals(3, removed.integer("xfm_status")); assertEquals(0, removed.ref("xfm_reservation").integer("xfm_remaining_cents"));
            assertNotNull(submit(v, a, c, 1, 1, 100)); assertEquals(1, a.integer("xfm_futures_result"));
            assertEquals(depth, c.integer("xfm_open_orders_count")); assertEquals(depth, c.list("xfm_orders").size());
            assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
    }
    @Test void lowerFuturesDepthKeepsOldOrdersAndThirtyTwoFillsButRefundsOnlyNewRemainder() throws IOException {
        Vm v = vm(); v.rules.add("xfm_capacity_extended"); Node c = series(v, "depth-series");
        List<Node> orders = fullDepth(v, c, 128); Node seller = actor(v, "seller", 8546); BigDecimal cash = v.cashStock();
        v.rules.clear(); v.rules.add("xfm_capacity_conservative"); assertEquals(orders, c.list("xfm_orders"));
        Node o = submit(v, seller, c, 2, 71, 100); assertNotNull(o); assertEquals(1, seller.integer("xfm_futures_result"));
        assertEquals(32, c.list("xfm_positions").size()); assertEquals(32, v.maxFuturesMatchIterations);
        assertEquals(3, o.integer("xfm_status")); assertEquals(39, o.integer("xfm_capacity_cancelled_lots"));
        assertEquals(0, o.ref("xfm_reservation").integer("xfm_remaining_cents")); assertEquals(0, o.integer("xfm_indexed"));
        assertEquals(orders.subList(32, 128), c.list("xfm_orders")); assertEquals(96, c.integer("xfm_open_orders_count"));
        assertEquals(cash, v.cashStock()); assertBalanced(v);
        Node tail = orders.getLast(); v.run("xfm_futures_cancel_order_effect", tail);
        assertEquals(3, tail.integer("xfm_status")); assertEquals(95, c.list("xfm_orders").size());
        assertEquals(0, tail.ref("xfm_reservation").integer("xfm_remaining_cents")); assertEquals(cash, v.cashStock()); assertBalanced(v);
    }
    @Test void lowerDepthDoesNotBlockActualReductionAgainstPreviouslyAdmittedOrders() throws IOException {
        Vm v = vm(); v.rules.add("xfm_capacity_extended"); Node c = series(v, "reduce-series");
        Node longActor = actor(v, "long", 2000), shortActor = actor(v, "short", 2000);
        submit(v, longActor, c, 1, 4, 100); submit(v, shortActor, c, 2, 4, 100);
        Node position = c.list("xfm_positions").getFirst(); assertEquals(4, position.integer("xfm_lots"));
        fullDepth(v, c, 128); v.rules.clear(); v.rules.add("xfm_capacity_conservative");
        longActor.put("xfm_futures_selected_position", position); longActor.put("xfm_futures_reduce_lots", 4);
        longActor.put("xfm_futures_limit_cents", 100); BigDecimal cash = v.cashStock();
        v.run("xfm_futures_reduce_effect", longActor); assertEquals(1, longActor.integer("xfm_futures_result"));
        Node close = (Node) v.scopes.get("xfm_fut_incoming"); assertNotNull(close); assertEquals(2, close.integer("xfm_status"));
        assertEquals(0, close.integer("xfm_remaining_lots")); assertEquals(0, position.integer("xfm_lots"));
        assertEquals(2, position.integer("xfm_status")); assertEquals(124, c.list("xfm_orders").size());
        assertEquals(cash, v.cashStock()); assertBalanced(v);
    }
    private static List<Node> fullDepth(Vm v, Node c, int depth) {
        List<Node> result = new ArrayList<>();
        for (int i = 0; i < depth; i++) {
            Node a = actor(v, "depth-actor-" + i, 121); Node o = submit(v, a, c, 1, 1, 100);
            assertNotNull(o); assertEquals(1, a.integer("xfm_futures_result")); result.add(o);
        }
        assertEquals(depth, c.list("xfm_orders").size()); return result;
    }

    @Test void exhaustedAndLegacySealedOpeningBudgetStillAllowsRealReductionAndForcedCloseAtArchivePressure() throws IOException {
        for (boolean forced : List.of(false, true)) {
            Vm v = vm(); Node c = series(v, "pressure-close");
            Node la = actor(v, "long", 2000), sa = actor(v, "short", 2000), replacement = actor(v, "replacement", 2000);
            submit(v, la, c, 1, 4, 100); submit(v, sa, c, 2, 4, 100);
            Node original = c.list("xfm_positions").getFirst(); long originalId = original.integer("xfm_position_id");
            Node longMargin = original.ref("xfm_long_reservation"), shortMargin = original.ref("xfm_short_reservation");
            long longMarginId = longMargin.integer("xfm_reservation_id"), shortMarginId = shortMargin.integer("xfm_reservation_id");
            assertNotNull(submit(v, replacement, c, 1, 4, 100));
            List<Node> initialArchive = fillArchiveTo(v, c, la.ref("xfm_account"), 4096);
            Node blocked = actor(v, "blocked", 121); BigDecimal cash = v.cashStock();
            if (forced) {
                for (String key : List.of("xfm_futures_opening_budget_v1", "xfm_futures_opening_budget_day", "xfm_futures_opening_allocated_today")) v.exchange.vars.remove(key);
            } else v.exchange.put("xfm_futures_opening_allocated_today", 512);
            int created = v.created("xfm_futures_order"); assertNull(submit(v, blocked, c, 1, 1, 100));
            assertEquals(8, blocked.integer("xfm_futures_reason")); assertEquals(created, v.created("xfm_futures_order"));
            assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today"));
            assertEquals(1, v.exchange.integer("xfm_futures_opening_budget_day"));
            assertEquals(4096, v.exchange.integer("xfm_futures_archive_count"));
            long priorOrderId = v.exchange.integer("xfm_next_futures_order_id"), priorPositionId = v.exchange.integer("xfm_next_futures_position_id");
            if (forced) {
                v.execute(substitute(v.definition("xfm_futures_post_exit_effect"), Clausewitz.parse("SIDE = long ORDER_SIDE = 2 LONG_EXIT = yes")), new Frame(original, null, original));
            } else {
                la.put("xfm_futures_selected_position", original); la.put("xfm_futures_reduce_lots", 4); la.put("xfm_futures_limit_cents", 100);
                v.run("xfm_futures_reduce_effect", la); assertEquals(1, la.integer("xfm_futures_result"));
            }
            Node close = (Node)v.scopes.get("xfm_fut_incoming"); assertNotNull(close);
            assertEquals(priorOrderId + 1, close.integer("xfm_order_id")); assertEquals(2, close.integer("xfm_status"));
            assertEquals(0, close.integer("xfm_remaining_lots")); assertEquals(0, close.ref("xfm_reservation").integer("xfm_remaining_cents"));
            assertEquals(originalId, original.integer("xfm_position_id")); assertEquals(0, original.integer("xfm_lots")); assertEquals(2, original.integer("xfm_status"));
            assertSame(longMargin, original.ref("xfm_long_reservation")); assertSame(shortMargin, original.ref("xfm_short_reservation"));
            assertEquals(longMarginId, longMargin.integer("xfm_reservation_id")); assertEquals(shortMarginId, shortMargin.integer("xfm_reservation_id"));
            assertEquals(0, longMargin.integer("xfm_remaining_cents")); assertEquals(0, shortMargin.integer("xfm_remaining_cents"));
            assertFalse(original.ended); assertFalse(longMargin.ended); assertFalse(shortMargin.ended);
            assertEquals(1, c.list("xfm_positions").size()); Node novated = c.list("xfm_positions").getFirst();
            assertEquals(priorPositionId + 2, novated.integer("xfm_position_id")); assertNotEquals(originalId, novated.integer("xfm_position_id"));
            assertSame(replacement.ref("xfm_account"), novated.ref("xfm_long_account")); assertSame(sa.ref("xfm_account"), novated.ref("xfm_short_account"));
            assertEquals(4, novated.integer("xfm_lots")); assertEquals(400, novated.ref("xfm_long_reservation").integer("xfm_remaining_cents"));
            assertEquals(400, novated.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
            assertEquals(1996, la.ref("xfm_account").integer("xfm_free_cents")); assertEquals(0, la.ref("xfm_account").integer("xfm_reserved_cents"));
            assertEquals(1598, sa.ref("xfm_account").integer("xfm_free_cents")); assertEquals(1598, replacement.ref("xfm_account").integer("xfm_free_cents"));
            assertEquals(8, v.exchange.integer("xfm_fee_cents")); assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today"));
            assertTrue(v.exchange.integer("xfm_futures_archive_count") >= 4096); assertTrue(initialArchive.stream().noneMatch(n -> n.ended));
            assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
    }

    @Test void actualAiGoldAndPlayerWalletShareTheLastOpeningAllocationWithoutRefundingWork() throws IOException {
        for (boolean aiFirst : List.of(false, true)) {
            Vm v = vm(); Node c = series(v, "shared-budget");
            Node ai = actor(v, "ai", 0); ai.ai = true; ai.gold = new BigDecimal("50.00");
            Node player = actor(v, "player", 121); Node first = aiFirst ? ai : player, second = aiFirst ? player : ai;
            v.exchange.put("xfm_futures_opening_allocated_today", 511); BigDecimal cash = v.cashStock();
            Node accepted = submit(v, first, c, 1, 1, 100); assertNotNull(accepted); assertEquals(1, first.integer("xfm_futures_result"));
            assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(121, first.ref("xfm_account").integer("xfm_reserved_cents"));
            BigDecimal secondGold = second.gold; long secondFree = second.ref("xfm_account").integer("xfm_free_cents");
            int orders = v.created("xfm_futures_order"), reservations = v.created("xfm_finance_reservation");
            assertNull(submit(v, second, c, 1, 1, 100)); assertEquals(8, second.integer("xfm_futures_reason"));
            assertEquals(orders, v.created("xfm_futures_order")); assertEquals(reservations, v.created("xfm_finance_reservation"));
            assertEquals(secondGold, second.gold); assertEquals(secondFree, second.ref("xfm_account").integer("xfm_free_cents"));
            v.run("xfm_futures_cancel_order_effect", accepted);
            assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(121, first.ref("xfm_account").integer("xfm_free_cents"));
            assertNull(submit(v, second, c, 1, 1, 100)); assertEquals(orders, v.created("xfm_futures_order"));
            assertEquals(secondGold, second.gold); assertEquals(secondFree, second.ref("xfm_account").integer("xfm_free_cents"));
            v.exchange.put("xfm_day", 2); c.ref("xfm_coin").put("xfm_oracle_day", 2);
            assertNotNull(submit(v, second, c, 1, 1, 100)); assertEquals(1, second.integer("xfm_futures_result"));
            assertEquals(1, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(2, v.exchange.integer("xfm_futures_opening_budget_day"));
            assertEquals(121, second.ref("xfm_account").integer("xfm_reserved_cents")); assertEquals(0, second.ref("xfm_account").integer("xfm_free_cents"));
            assertEquals(new BigDecimal("48.79"), ai.gold); assertEquals(BigDecimal.ZERO, player.gold);
            assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
    }

    @Test void repeatedUnmatchedReductionAndCancelIsExemptButOnlyAgedUnprotectedHistoryIsPruned() throws IOException {
        Vm v = vm(); Node c = series(v, "optional-close"); Node la = actor(v, "long", 2000), sa = actor(v, "short", 2000);
        submit(v, la, c, 1, 4, 100); submit(v, sa, c, 2, 4, 100); Node original = c.list("xfm_positions").getFirst();
        long id = original.integer("xfm_position_id"); List<Node> initialArchive = fillArchiveTo(v, c, la.ref("xfm_account"), 4096);
        v.exchange.put("xfm_futures_opening_allocated_today", 512); BigDecimal cash = v.cashStock();
        la.put("xfm_futures_selected_position", original); la.put("xfm_futures_reduce_lots", 1); la.put("xfm_futures_limit_cents", 100);
        int orders = v.created("xfm_futures_order"), reservations = v.created("xfm_finance_reservation");
        List<Node> closes = new ArrayList<>(); long lastId = v.exchange.integer("xfm_next_futures_order_id");
        for (int i = 0; i < 3; i++) {
            v.run("xfm_futures_reduce_effect", la); assertEquals(1, la.integer("xfm_futures_result"));
            Node close = (Node)v.scopes.get("xfm_fut_incoming"); closes.add(close); assertEquals(++lastId, close.integer("xfm_order_id"));
            assertEquals(1, close.integer("xfm_remaining_lots")); assertEquals(1, close.ref("xfm_reservation").integer("xfm_remaining_cents"));
            v.run("xfm_futures_cancel_order_effect", close); assertEquals(0, close.ref("xfm_reservation").integer("xfm_remaining_cents"));
            assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
        assertEquals(orders + 3, v.created("xfm_futures_order")); assertEquals(reservations + 3, v.created("xfm_finance_reservation"));
        assertEquals(4099, v.exchange.integer("xfm_futures_archive_count")); assertTrue(closes.stream().noneMatch(n -> n.ended));
        assertTrue(initialArchive.stream().noneMatch(n -> n.ended)); assertEquals(id, original.integer("xfm_position_id")); assertEquals(4, original.integer("xfm_lots"));
        assertEquals(0, original.integer("xfm_status")); assertEquals(400, original.ref("xfm_long_reservation").integer("xfm_remaining_cents"));
        long endedOrders = v.nodes.values().stream().filter(n -> n.type.equals("xfm_futures_order") && n.ended).count();
        v.exchange.put("xfm_day", 2); c.ref("xfm_coin").put("xfm_oracle_day", 2); v.run("xfm_futures_archive_prune_effect", v.exchange);
        assertEquals(4035, v.exchange.integer("xfm_futures_archive_count"));
        assertEquals(endedOrders + 64, v.nodes.values().stream().filter(n -> n.type.equals("xfm_futures_order") && n.ended).count());
        assertFalse(original.ended); assertEquals(4, original.integer("xfm_lots")); assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today"));
        assertEquals(cash, v.cashStock()); assertBalanced(v); // Queue count is not a resident counter; no global512 Story assertion.
    }

    @Test void deferredCoverageIsHistoricalWhileOriginalPricedPendingPaymentStillReallyPays() throws IOException {
        Vm v = vm(); Node c = series(v, "deferred-existing"), la = actor(v, "deferred-long", 2000), sa = actor(v, "deferred-short", 2000);
        submit(v, la, c, 1, 1, 100); submit(v, sa, c, 2, 1, 100); Node p = c.list("xfm_positions").getFirst();
        // Explicit software input: a genuine earlier priced payment journal, using
        // the exact fields written by begin_settlement. No missing history is priced.
        p.put("xfm_pending_payment", 1); p.put("xfm_pending_day", 1); p.put("xfm_pending_kind", 1);
        p.put("xfm_pending_new_mark", 110); p.put("xfm_pending_amount", 10); p.put("xfm_pending_paid", 0); p.put("xfm_pending_loser", 2);
        p.put("xfm_pending_debtor", sa.ref("xfm_account")); p.put("xfm_pending_creditor", la.ref("xfm_account"));
        v.exchange.put("xfm_day", 2); v.exchange.put("xfm_calendar_recovery", 1); v.exchange.put("xfm_calendar_observed_date", 389472);
        c.put("xfm_perpetual", 0); c.put("xfm_expiry_day", 2); c.ref("xfm_coin").put("xfm_oracle_quality", 0);
        long before = la.ref("xfm_account").integer("xfm_free_cents"); BigDecimal total = v.cashStock();
        v.run("xfm_futures_position_daily_effect", p);
        assertEquals(before + 10, la.ref("xfm_account").integer("xfm_free_cents"));
        assertFalse(p.vars.containsKey("xfm_pending_payment")); assertEquals(1, p.integer("xfm_last_settled_day"));
        assertEquals(2, p.integer("xfm_deferred_unpriced_from_day")); assertEquals(2, p.integer("xfm_deferred_unpriced_through_day"));
        assertEquals(1, p.integer("xfm_deferred_expiry_observed")); assertEquals(0, p.integer("xfm_status"));
        assertFalse(p.ended); assertFalse(p.vars.containsKey("xfm_last_funding_day")); assertEquals(total, v.cashStock()); assertBalanced(v);
    }
    @Test void deferredDuePeriodStillCancelsTheActualOpeningOrderAndReturnsItsReservation() throws IOException {
        Vm v = vm(); Node c = series(v, "deferred-expiry"), actor = actor(v, "deferred-order-owner", 2000);
        Node o = submit(v, actor, c, 1, 1, 100); assertNotNull(o);
        v.exchange.put("xfm_day", 2); v.exchange.put("xfm_calendar_recovery", 1); c.put("xfm_perpetual", 0); c.put("xfm_expiry_day", 2);
        c.ref("xfm_coin").put("xfm_oracle_quality", 0); BigDecimal total = v.cashStock();
        int allocations = v.created("xfm_futures_order"); v.run("xfm_futures_maintain_orders_effect", c);
        assertEquals(3, o.integer("xfm_status")); assertEquals(0, o.ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(2000, actor.ref("xfm_account").integer("xfm_free_cents")); assertEquals(0, actor.ref("xfm_account").integer("xfm_reserved_cents"));
        assertEquals(allocations, v.created("xfm_futures_order")); assertEquals(total, v.cashStock()); assertBalanced(v);
    }

    @Test void manualCancellationReceiptsMeasureActualCashAndRemainImmutableOnRetry() throws IOException {
        Vm v=vm();Node c=series(v,"cancel-owner"),a=actor(v,"owner",500),o=submit(v,a,c,1,2,100);
        Node r=o.ref("xfm_reservation"),wallet=a.ref("xfm_account");long refund=r.integer("xfm_remaining_cents");
        long before=wallet.integer("xfm_free_cents");BigDecimal cash=v.cashStock();a.put("xfm_futures_selected_order",o);
        v.run("xfm_futures_cancel_effect",a);
        assertCancelReceipt(o,2,1,refund,1);assertEquals(before+refund,wallet.integer("xfm_free_cents"));
        assertEquals(2,v.integerValue("xfm_futures_cancel_display_reason_value",o));
        assertEquals(2,v.integerValue("xfm_futures_cancel_display_refund_mode_value",o));
        assertEquals(1,v.integerValue("xfm_futures_cancel_display_day_value",o));
        assertEquals(0,r.integer("xfm_remaining_cents"));assertEquals(3,o.integer("xfm_status"));
        Map<String,Datum> first=Map.copyOf(o.vars);v.exchange.put("xfm_day",7);
        v.execute(substitute(v.definition("xfm_futures_cancel_with_reason_effect"),Clausewitz.parse("REASON=15")),new Frame(o,null,o));
        v.run("xfm_futures_cancel_effect",a);assertEquals(first,o.vars);assertEquals(cash,v.cashStock());
        assertEquals(1,wallet.list("xfm_futures_order_history").size());assertBalanced(v);
        // Authored historical cancellation: no future call may fabricate its unknown cause/refund.
        Node legacy=v.node("old-cancelled-205","xfm_futures_order");legacy.put("xfm_status",3);legacy.put("xfm_remaining_lots",1);
        v.run("xfm_futures_cancel_order_effect",legacy);assertFalse(legacy.vars.containsKey("xfm_cancel_receipt_version"));
        assertEquals(0,v.integerValue("xfm_futures_cancel_display_reason_value",legacy));
        assertEquals(1,v.integerValue("xfm_futures_cancel_display_refund_mode_value",legacy));
    }
    @Test void allEightExistingRiskBranchesKeepTheirOrderAndRefundActualReservation() throws IOException {
        for(int cause=3;cause<=10;cause++) {
            Vm v=vm();Node c=series(v,"risk-"+cause),a=actor(v,"risk-owner",500),o=submit(v,a,c,1,1,100),asset=c.ref("xfm_coin");
            switch(cause) {
                case 3 -> v.open=false;
                case 4 -> a.ref("xfm_account").put("xfm_account_frozen",1);
                case 5 -> {asset.put("xfm_oracle_quality",0);asset.put("xfm_max_leverage",0);v.exchange.put("xfm_calendar_recovery",1);}
                case 6 -> asset.put("xfm_derivatives_reduce_only",1);
                case 7 -> asset.put("xfm_max_leverage",0);
                case 8 -> asset.put("xfm_mark_cents",200);
                case 9 -> asset.put("xfm_mark_cents",50);
                case 10 -> {c.put("xfm_perpetual",0);c.put("xfm_expiry_day",1);}
                default -> throw new AssertionError(cause);
            }
            BigDecimal cash=v.cashStock();long refund=o.ref("xfm_reservation").integer("xfm_remaining_cents");
            v.run("xfm_futures_maintain_orders_effect",c);assertCancelReceipt(o,cause,1,refund,1);
            assertEquals(500,a.ref("xfm_account").integer("xfm_free_cents"));assertEquals(cash,v.cashStock());assertBalanced(v);
            if(cause==5)assertEquals(1,o.integer("xfm_cancel_recovery"));
        }
    }
    @Test void invalidCloseVenueAndSourceClosureUseTheirActualCancellationCallsites() throws IOException {
        Vm v=vm();Node c=series(v,"invalid-close"),a=actor(v,"a",500),o=submit(v,a,c,1,1,100);
        o.put("xfm_reduce_order",1);BigDecimal cash=v.cashStock();v.run("xfm_futures_maintain_orders_effect",c);
        assertCancelReceipt(o,11,1,121,1);assertEquals(cash,v.cashStock());assertBalanced(v);
        Vm venue=vm();Node vc=series(venue,"venue"),va=actor(venue,"a",500),vo=submit(venue,va,vc,1,1,100);
        vc.ref("xfm_coin").list("xfm_futures_contracts").add(vc);cash=venue.cashStock();
        venue.run("xfm_futures_reduce_only_effect",vc.ref("xfm_coin"));assertCancelReceipt(vo,15,1,121,1);
        assertEquals(cash,venue.cashStock());assertBalanced(venue);
        Vm closed=vm();Node cc=series(closed,"closed-source"),la=actor(closed,"long",2000),sa=actor(closed,"short",2000);
        submit(closed,la,cc,1,4,100);submit(closed,sa,cc,2,4,100);Node p=cc.list("xfm_positions").getFirst();
        la.put("xfm_futures_selected_position",p);la.put("xfm_futures_reduce_lots",4);la.put("xfm_futures_limit_cents",100);
        closed.run("xfm_futures_reduce_effect",la);Node close=cc.list("xfm_orders").getFirst();
        long refund=close.ref("xfm_reservation").integer("xfm_remaining_cents");cash=closed.cashStock();
        closed.run("xfm_futures_close_position_effect",p);assertCancelReceipt(close,12,1,refund,1);
        assertEquals(2,p.integer("xfm_status"));assertEquals(cash,closed.cashStock());assertBalanced(closed);
    }
    @Test void forcedReplacementAndDefensiveIocCallsitesRecordTheirOwnCause() throws IOException {
        Vm v=vm();Node c=series(v,"forced-replace"),la=actor(v,"long",2000),sa=actor(v,"short",2000);
        submit(v,la,c,1,4,100);submit(v,sa,c,2,4,100);Node p=c.list("xfm_positions").getFirst();
        la.put("xfm_futures_selected_position",p);la.put("xfm_futures_reduce_lots",4);la.put("xfm_futures_limit_cents",100);
        v.run("xfm_futures_reduce_effect",la);Node old=c.list("xfm_orders").getFirst();long refund=old.ref("xfm_reservation").integer("xfm_remaining_cents");
        BigDecimal cash=v.cashStock();v.execute(substitute(v.definition("xfm_futures_post_exit_effect"),Clausewitz.parse("SIDE=long ORDER_SIDE=2 LONG_EXIT=yes")),new Frame(p,null,p));
        assertCancelReceipt(old,13,1,refund,1);
        Node forced=(Node)v.scopes.get("xfm_fut_exit_order");assertNotNull(forced);assertEquals(1,forced.integer("xfm_forced_exit"));
        assertCancelReceipt(forced,14,1,forced.integer("xfm_cancel_before_remaining_cents"),1);
        assertEquals(cash,v.cashStock());assertBalanced(v);
        // Defensive post-matcher callsite normally sees an already cancelled IOC. Execute its
        // exact production conditional on a genuine funded order; no money/matcher port is used.
        Vm defensive=vm();Node dc=series(defensive,"defensive"),da=actor(defensive,"a",121),d=submit(defensive,da,dc,1,1,100);
        List<Block> blocks=new ArrayList<>();collectCancellationBlocks(defensive.definition("xfm_futures_post_exit_effect"),blocks);
        assertEquals(1,blocks.size());cash=defensive.cashStock();defensive.execute(blocks.getFirst(),new Frame(d,null,d));
        assertCancelReceipt(d,14,1,121,1);assertEquals(cash,defensive.cashStock());assertBalanced(defensive);
    }
    @Test void zeroUncalledRejectedAndInconsistentReleaseNeverBorrowAStaleSuccessResult() throws IOException {
        Vm zero=vm();Node zc=series(zero,"zero"),za=actor(zero,"a",121),z=submit(zero,za,zc,1,1,100),zr=z.ref("xfm_reservation");
        zr.put("xfm_request_cents",121);zero.run("xfm_finance_release_effect",zr);assertEquals(1,zr.integer("xfm_result"));
        zero.run("xfm_futures_cancel_order_effect",z);assertCancelReceipt(z,1,0,0,1);assertFalse(z.vars.containsKey("xfm_cancel_release_result"));assertBalanced(zero);
        Vm rejected=vm();Node rc=series(rejected,"rejected"),ra=actor(rejected,"a",121),r=submit(rejected,ra,rc,1,1,100);
        r.ref("xfm_reservation").put("xfm_status",2);r.ref("xfm_reservation").put("xfm_result",1);BigDecimal cash=rejected.cashStock();
        rejected.run("xfm_futures_cancel_order_effect",r);assertEquals(3,r.integer("xfm_status"));assertEquals(1,r.integer("xfm_cancel_release_api_called"));
        assertEquals(0,r.integer("xfm_cancel_release_result"));assertEquals(0,r.integer("xfm_cancel_release_verified"));
        assertFalse(r.vars.containsKey("xfm_cancel_released_cents"));assertEquals(cash,rejected.cashStock());assertBalanced(rejected);
        // Fault injection: if a future financial producer reports success but fails conservation,
        // the receipt must stay unverified. This is not credit for the real release producer.
        Vm broken=vm();Node bc=series(broken,"broken"),ba=actor(broken,"a",121),b=submit(broken,ba,bc,1,1,100);
        broken.program.put("xfm_finance_release_effect",Clausewitz.parse("set_variable={name=xfm_result value=1} set_variable={name=xfm_remaining_cents value=0}"));
        broken.run("xfm_futures_cancel_order_effect",b);assertEquals(1,b.integer("xfm_cancel_release_result"));assertEquals(0,b.integer("xfm_cancel_release_verified"));
        assertFalse(b.vars.containsKey("xfm_cancel_released_cents"));
        // Missing after snapshot remains unknown even though the original cancellation still runs.
        Vm missing=vm();Node mc=series(missing,"missing"),ma=actor(missing,"a",121),m=submit(missing,ma,mc,1,1,100);
        m.ref("xfm_account").vars.remove("xfm_free_cents");missing.run("xfm_futures_cancel_order_effect",m);
        assertEquals(1,m.integer("xfm_cancel_receipt_version"));assertEquals(0,m.integer("xfm_cancel_release_verified"));
        assertFalse(m.vars.containsKey("xfm_cancel_released_cents"));
        assertEquals(1,missing.integerValue("xfm_futures_cancel_display_refund_mode_value",m));
        Node live=missing.node("not-cancelled","xfm_futures_order");live.put("xfm_status",2);
        assertEquals(-1,missing.integerValue("xfm_futures_cancel_display_reason_value",live));
        assertEquals(0,missing.integerValue("xfm_futures_cancel_display_refund_mode_value",live));
    }
    private static void assertCancelReceipt(Node order,long cause,long api,long released,long day) {
        assertEquals(1,order.integer("xfm_cancel_receipt_version"));assertEquals(cause,order.integer("xfm_cancel_reason"));
        assertEquals(day,order.integer("xfm_cancel_day"));assertEquals(day,order.integer("xfm_archived_day"));
        assertEquals(api,order.integer("xfm_cancel_release_api_called"));assertEquals(1,order.integer("xfm_cancel_release_verified"));
        assertTrue(order.vars.containsKey("xfm_cancel_released_cents"));assertEquals(released,order.integer("xfm_cancel_released_cents"));
        assertEquals(order.integer("xfm_cancel_before_free_cents")+released,order.integer("xfm_cancel_after_free_cents"));
        assertEquals(order.integer("xfm_cancel_before_reserved_cents")-released,order.integer("xfm_cancel_after_reserved_cents"));
        assertEquals(order.integer("xfm_cancel_before_remaining_cents")-released,order.integer("xfm_cancel_after_remaining_cents"));
        assertFalse(order.vars.containsKey("xfm_cancel_receipt_pending"));assertFalse(order.vars.containsKey("xfm_cancel_capture_ready"));
    }
    private static void collectCancellationBlocks(Block block,List<Block> out) {
        for(Entry e:block.entries())if(e.value() instanceof Block b) {
            if(e.key().equals("if")&&b.entries().stream().anyMatch(x->x.key().equals("xfm_futures_cancel_with_reason_effect")))out.add(new Block(List.of(e)));
            else collectCancellationBlocks(b,out);
        }
    }

    // Authored closed-history input: append to the genuine queue already made by real fills.
    // It carries no cash, reservation or position; all queue traversal/pruning is production AST.
    private static List<Node> fillArchiveTo(Vm v, Node c, Node account, int count) {
        List<Node> added = new ArrayList<>(); Node tail = v.exchange.ref("xfm_futures_archive_tail");
        long start = v.exchange.integer("xfm_futures_archive_count"), nextId = Math.max(10_000, v.exchange.integer("xfm_next_futures_order_id"));
        for (long i = start; i < count; i++) {
            Node n = v.node("authored-history-" + i, "xfm_futures_order"); n.owner = v.custodian;
            n.put("xfm_order_id", ++nextId); n.put("xfm_contract", c); n.put("xfm_account", account);
            n.put("xfm_status", 3); n.put("xfm_remaining_lots", 0); n.put("xfm_indexed", 0);
            n.put("xfm_archived_day", v.exchange.integer("xfm_day")); n.put("xfm_futures_archive_queued", 1);
            if (tail == null) v.exchange.put("xfm_futures_archive_head", n); else tail.put("xfm_futures_archive_next", n);
            tail = n; account.list("xfm_futures_order_history").add(n); added.add(n);
        }
        assertNotNull(tail); v.exchange.put("xfm_futures_archive_tail", tail); v.exchange.put("xfm_futures_archive_count", count);
        v.exchange.put("xfm_next_futures_order_id", nextId); return added;
    }


    @Test void missingSavedScopeDoesNotPassIdentityInequalityInTheActualFiniteInterpreter() throws IOException {
        Vm v = vm(); Node present = v.node("present", "xfm_futures_position"), other = v.node("other", "xfm_futures_position");
        v.scopes.put("present", present); v.scopes.put("other", other); Frame frame = new Frame(present, null, present);
        assertFalse(v.test(Clausewitz.parse("scope:present != scope:missing"), frame));
        assertFalse(v.test(Clausewitz.parse("scope:missing != scope:present"), frame));
        assertFalse(v.test(Clausewitz.parse("scope:missing = scope:missing"), frame));
        assertTrue(v.test(Clausewitz.parse("scope:present != scope:other"), frame));
        assertTrue(v.test(Clausewitz.parse("NOT = { exists = scope:missing }"), frame));
    }

    @Test void realPendingShortThenSingleLongCloseAllocatesAndArchivesSliceBeforeNovation() throws IOException {
        Vm v = vm(); Node c = series(v, "consecutive"), player = actor(v, "player", 2000), oldShort = actor(v, "old-short", 2000);
        submit(v, player, c, 1, 1, 100); submit(v, oldShort, c, 2, 1, 100);
        Node source = c.list("xfm_positions").getFirst(); long sourceId = source.integer("xfm_position_id");
        Node shortOrder = submit(v, player, c, 2, 1, 100);
        player.put("xfm_futures_selected_position", source); player.put("xfm_futures_reduce_lots", 1); player.put("xfm_futures_limit_cents", 100);
        v.run("xfm_futures_reduce_effect", player); assertEquals(1, player.integer("xfm_futures_result"));
        Node closeOrder = (Node) v.scopes.get("xfm_fut_incoming");
        assertEquals(2, c.list("xfm_orders").size()); assertEquals(1, source.integer("xfm_lots"));
        Node buyer = actor(v, "independent-buyer", 2000); BigDecimal cash = v.cashStock(); Node incoming = submit(v, buyer, c, 1, 2, 100);
        assertEquals(0, shortOrder.integer("xfm_remaining_lots")); assertEquals(0, closeOrder.integer("xfm_remaining_lots"));
        assertEquals(2, shortOrder.integer("xfm_status")); assertEquals(2, closeOrder.integer("xfm_status"));
        assertEquals(100, shortOrder.integer("xfm_filled_gross_cents")); assertEquals(100, closeOrder.integer("xfm_filled_gross_cents"));
        assertEquals(1, shortOrder.integer("xfm_fee_paid_cents")); assertEquals(1, closeOrder.integer("xfm_fee_paid_cents"));
        assertEquals(0, source.integer("xfm_lots")); assertEquals(2, source.integer("xfm_status"));
        assertEquals(sourceId, source.integer("xfm_position_id")); assertEquals(0, source.ref("xfm_long_reservation").integer("xfm_remaining_cents"));
        assertEquals(0, source.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
        assertEquals(2, c.list("xfm_positions").size()); Node novated = c.list("xfm_positions").getLast();
        Node slice = (Node) v.scopes.get("xfm_fut_sell_slice");
        assertFalse(v.scopes.containsKey("xfm_fut_buy_slice")); assertEquals(sourceId + 2, slice.integer("xfm_position_id"));
        assertEquals(sourceId + 3, novated.integer("xfm_position_id")); assertSame(source, slice.ref("xfm_source_position"));
        assertEquals(2, slice.integer("xfm_status")); assertTrue(slice.vars.containsKey("xfm_archived_day")); assertFalse(slice.ended);
        assertSame(buyer.ref("xfm_account"), novated.ref("xfm_long_account")); assertSame(oldShort.ref("xfm_account"), novated.ref("xfm_short_account"));
        assertSame(slice.ref("xfm_short_reservation"), novated.ref("xfm_short_reservation"));
        assertSame(oldShort.ref("xfm_account"), novated.ref("xfm_short_reservation").ref("xfm_account"));
        assertEquals(100, novated.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
        assertEquals(1, incoming.integer("xfm_fee_paid_cents")); assertEquals(5, v.exchange.integer("xfm_fee_cents"));
        assertActiveMarginsResolve(v); assertEquals(cash, v.cashStock()); assertBalanced(v);
    }

    @Test void singleShortCloseStillAllocatesBuySliceAndKeepsBothRealMarginsInTheNewPosition() throws IOException {
        Vm v = vm(); Node c = series(v, "short-close"), oldLong = actor(v, "old-long", 2000), oldShort = actor(v, "old-short", 2000);
        submit(v, oldLong, c, 1, 1, 100); submit(v, oldShort, c, 2, 1, 100); Node source = c.list("xfm_positions").getFirst();
        Node seller = actor(v, "new-short", 2000); submit(v, seller, c, 2, 1, 100);
        BigDecimal cash = v.cashStock(); oldShort.put("xfm_futures_selected_position", source); oldShort.put("xfm_futures_reduce_lots", 1); oldShort.put("xfm_futures_limit_cents", 100);
        v.run("xfm_futures_reduce_effect", oldShort); assertEquals(1, oldShort.integer("xfm_futures_result"));
        assertEquals(0, source.integer("xfm_lots")); assertEquals(2, source.integer("xfm_status"));
        Node next = c.list("xfm_positions").getFirst(); assertSame(oldLong.ref("xfm_account"), next.ref("xfm_long_account"));
        assertSame(seller.ref("xfm_account"), next.ref("xfm_short_account"));
        assertEquals(3, next.integer("xfm_position_id")); assertActiveMarginsResolve(v); assertEquals(cash, v.cashStock()); assertBalanced(v);
    }

    @Test void opposingClosesOfSameSourceAllocateAndArchiveOnlyOneSharedSlice() throws IOException {
        Vm v = vm(); Node c = series(v, "both-close"), la = actor(v, "long", 2000), sa = actor(v, "short", 2000);
        submit(v, la, c, 1, 1, 100); submit(v, sa, c, 2, 1, 100); Node source = c.list("xfm_positions").getFirst();
        la.put("xfm_futures_selected_position", source); la.put("xfm_futures_reduce_lots", 1); la.put("xfm_futures_limit_cents", 100); v.run("xfm_futures_reduce_effect", la);
        BigDecimal cash = v.cashStock(); sa.put("xfm_futures_selected_position", source); sa.put("xfm_futures_reduce_lots", 1); sa.put("xfm_futures_limit_cents", 100); v.run("xfm_futures_reduce_effect", sa);
        assertEquals(0, source.integer("xfm_lots")); assertEquals(2, source.integer("xfm_status")); assertTrue(c.list("xfm_positions").isEmpty());
        Node slice = (Node) v.scopes.get("xfm_fut_buy_slice"); assertSame(slice, v.scopes.get("xfm_fut_sell_slice"));
        assertEquals(2, slice.integer("xfm_position_id")); assertEquals(2, v.exchange.integer("xfm_next_futures_position_id"));
        assertEquals(2, slice.integer("xfm_status")); assertTrue(slice.vars.containsKey("xfm_archived_day"));
        assertEquals(0, la.ref("xfm_account").integer("xfm_reserved_cents")); assertEquals(0, sa.ref("xfm_account").integer("xfm_reserved_cents"));
        assertEquals(cash, v.cashStock()); assertBalanced(v);
    }

    @Test void productionPerpetualFundingPaysTheCorrectRealMarginOnceForBothPremiumSigns() throws IOException {
        for (int index : List.of(100, 120)) {
            Vm v = vm(); Node c = series(v, "funding-sign-" + index);
            Node la = receiptActor(v, "long", 30000), sa = receiptActor(v, "short", 30000);
            submit(v, la, c, 1, 100, 110); submit(v, sa, c, 2, 100, 110);
            assertEquals(1, c.list("xfm_positions").size()); Node p = c.list("xfm_positions").getFirst();
            assertEquals(11000, c.integer("xfm_execution_volume_cents")); assertEquals(100, c.integer("xfm_execution_lots"));
            assertEquals(1, c.integer("xfm_execution_day")); assertEquals(110, c.integer("xfm_last_execution_cents"));
            Node longWallet = la.ref("xfm_account"), shortWallet = sa.ref("xfm_account");
            Node longMargin = p.ref("xfm_long_reservation"), shortMargin = p.ref("xfm_short_reservation");
            long longFree = longWallet.integer("xfm_free_cents"), shortFree = shortWallet.integer("xfm_free_cents");
            assertEquals(11000, longMargin.integer("xfm_remaining_cents")); assertEquals(11000, shortMargin.integer("xfm_remaining_cents"));
            BigDecimal cash = v.cashStock(); long fees = v.exchange.integer("xfm_fee_cents");
            v.exchange.put("xfm_day", 2); Node asset = c.ref("xfm_coin");
            asset.put("xfm_index_cents", index); asset.put("xfm_mark_cents", index); asset.put("xfm_oracle_day", 2);
            v.run("xfm_futures_position_daily_effect", p);
            assertEquals(2, p.integer("xfm_last_settled_day")); assertEquals(2, p.integer("xfm_last_funding_day"));
            assertEquals(2, p.integer("xfm_pending_kind")); assertFalse(p.vars.containsKey("xfm_pending_payment"));
            assertFalse(p.vars.containsKey("xfm_pending_amount")); assertFalse(p.vars.containsKey("xfm_pending_paid"));
            if (index == 100) {
                assertEquals(9990, longMargin.integer("xfm_remaining_cents")); assertEquals(11000, shortMargin.integer("xfm_remaining_cents"));
                assertEquals(longFree, longWallet.integer("xfm_free_cents")); assertEquals(shortFree + 1010, shortWallet.integer("xfm_free_cents"));
                assertEquals(10, p.integer("xfm_pay_now")); // MTM 1000, then LONG pays funding 10.
            } else {
                assertEquals(11000, longMargin.integer("xfm_remaining_cents")); assertEquals(9988, shortMargin.integer("xfm_remaining_cents"));
                assertEquals(longFree + 1012, longWallet.integer("xfm_free_cents")); assertEquals(shortFree, shortWallet.integer("xfm_free_cents"));
                assertEquals(12, p.integer("xfm_pay_now")); // MTM 1000, then SHORT pays funding 12.
            }
            Map<String, Datum> settled = Map.copyOf(p.vars);
            long longReserved = longWallet.integer("xfm_reserved_cents"), shortReserved = shortWallet.integer("xfm_reserved_cents");
            long longPaidFree = longWallet.integer("xfm_free_cents"), shortPaidFree = shortWallet.integer("xfm_free_cents");
            v.run("xfm_futures_position_daily_effect", p);
            assertEquals(settled, p.vars, "A same-day retry must not open another funding journal");
            assertEquals(longReserved, longWallet.integer("xfm_reserved_cents")); assertEquals(shortReserved, shortWallet.integer("xfm_reserved_cents"));
            assertEquals(longPaidFree, longWallet.integer("xfm_free_cents")); assertEquals(shortPaidFree, shortWallet.integer("xfm_free_cents"));
            v.exchange.put("xfm_day", 3); asset.put("xfm_oracle_day", 3);
            v.run("xfm_futures_position_daily_effect", p);
            assertEquals(2, p.integer("xfm_last_funding_day"), "The real day-1 print is stale on day 3");
            assertEquals(longReserved, longWallet.integer("xfm_reserved_cents")); assertEquals(shortReserved, shortWallet.integer("xfm_reserved_cents"));
            assertEquals(longPaidFree, longWallet.integer("xfm_free_cents")); assertEquals(shortPaidFree, shortWallet.integer("xfm_free_cents"));
            assertEquals(fees, v.exchange.integer("xfm_fee_cents")); assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
    }

    @Test void productionFundingKeepsTheAbsoluteRealVolumeGateAtTheCentBoundary() throws IOException {
        for (int lots : List.of(90, 91)) {
            Vm v = vm(); Node c = series(v, "volume-" + lots);
            Node la = receiptActor(v, "long", 30000), sa = receiptActor(v, "short", 30000);
            submit(v, la, c, 1, lots, 110); submit(v, sa, c, 2, lots, 110);
            Node p = c.list("xfm_positions").getFirst(); Node lm = p.ref("xfm_long_reservation");
            long shortFree = sa.ref("xfm_account").integer("xfm_free_cents"); BigDecimal cash = v.cashStock();
            assertEquals(lots * 110L, c.integer("xfm_execution_volume_cents")); assertEquals(lots, c.integer("xfm_execution_lots"));
            v.exchange.put("xfm_day", 2); c.ref("xfm_coin").put("xfm_oracle_day", 2);
            v.run("xfm_futures_position_daily_effect", p);
            assertEquals(2, p.integer("xfm_last_settled_day"));
            if (lots == 90) {
                assertFalse(p.vars.containsKey("xfm_last_funding_day"), "9900 actual cents do not satisfy 10000");
                assertEquals(9000, lm.integer("xfm_remaining_cents")); assertEquals(shortFree + 900, sa.ref("xfm_account").integer("xfm_free_cents"));
            } else {
                assertEquals(2, p.integer("xfm_last_funding_day")); assertEquals(9091, lm.integer("xfm_remaining_cents"));
                assertEquals(shortFree + 919, sa.ref("xfm_account").integer("xfm_free_cents")); assertEquals(9, p.integer("xfm_pay_now"));
            }
            assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
    }

    @Test void productionEligibleOneLotFundingRoundsToZeroWithoutInventingADeferredCent() throws IOException {
        Vm v = vm(); Node c = series(v, "funding-small");
        Node la = receiptActor(v, "large-long", 30000), sa = receiptActor(v, "large-short", 30000);
        submit(v, la, c, 1, 100, 110); submit(v, sa, c, 2, 100, 110);
        Node large = c.list("xfm_positions").getFirst();
        Node smallLong = receiptActor(v, "small-long", 1000), smallShort = receiptActor(v, "small-short", 1000);
        submit(v, smallLong, c, 1, 1, 110); submit(v, smallShort, c, 2, 1, 110);
        assertEquals(2, c.list("xfm_positions").size()); Node small = c.list("xfm_positions").getLast();
        assertEquals(11110, c.integer("xfm_execution_volume_cents")); assertEquals(101, c.integer("xfm_execution_lots"));
        long shortFree = smallShort.ref("xfm_account").integer("xfm_free_cents"); BigDecimal cash = v.cashStock();
        v.exchange.put("xfm_day", 2); c.ref("xfm_coin").put("xfm_oracle_day", 2);
        v.run("xfm_futures_position_daily_effect", small); v.run("xfm_futures_position_daily_effect", large);
        assertEquals(2, small.integer("xfm_last_funding_day")); assertEquals(0, small.integer("xfm_pay_now"));
        assertEquals(100, small.ref("xfm_long_reservation").integer("xfm_remaining_cents"));
        assertEquals(110, small.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
        assertEquals(shortFree + 10, smallShort.ref("xfm_account").integer("xfm_free_cents"), "Only the real 10-cent MTM is paid");
        assertEquals(10, large.integer("xfm_pay_now"), "A separate 100-lot position pays its own funding");
        assertFalse(small.vars.containsKey("xfm_pending_payment")); assertFalse(small.vars.containsKey("xfm_pending_amount"));
        assertEquals(cash, v.cashStock()); assertBalanced(v);
    }

    @Test void controlledFixtureMinimumUsesEmittedGuardQuotesAndOriginalFundingPayments() throws IOException {
        var generated = org.xar.ck3.markets.acceptance.FollowupObservationScripts.renderControlledFunding(
            new org.xar.ck3.markets.acceptance.FollowupContracts.ControlledFundingRequest(3, "perpetual-funding-engine-fixture", true));
        // Expected integer boundaries; the actual predicate and quote arithmetic below come from the emitter.
        long[][] boundaries = {{87,78,9984,0},{88,79,10112,0},{89,80,10240,0},
            {90,81,10368,1},{96,86,11008,1},{500,450,57600,1},{501,450,57600,0}};
        for (long[] row : boundaries) {
            Vm v = vm(); Node c = series(v, "emitted-minimum-" + row[0]), asset = c.ref("xfm_coin");
            for (String path : List.of("common/scripted_triggers/xfmf_guards.txt", "common/script_values/xfmf_values.txt")) {
                byte[] bytes = generated.get(path); assertNotNull(bytes, path);
                for (Entry entry : Clausewitz.parse(new String(bytes, java.nio.charset.StandardCharsets.UTF_8)).entries()) {
                    assertInstanceOf(Block.class, entry.value(), entry.key());
                    assertNull(v.program.putIfAbsent(entry.key(), (Block) entry.value()), entry.key());
                }
            }
            asset.put("xfm_index_id", 1); asset.put("xfm_index_cents", row[0]); asset.put("xfm_mark_cents", row[0]);
            v.custodian.put("xfmf_p_asset", asset); v.custodian.put("xfmf_n_asset", asset);
            Frame frame = new Frame(asset, null, asset); Block predicate = v.definition("xfmf_asset_trigger");
            assertEquals(row[3] == 1, v.test(predicate, frame), "Actual emitted asset guard at " + row[0]);
            long negativeQuote = v.integerValue("xfmf_negative_quote_value", v.custodian);
            assertEquals(row[1], negativeQuote); assertEquals(row[2], negativeQuote * 128);
            assertEquals(row[0] >= 88, negativeQuote * 128 >= 10000,
                "88 is the mathematical volume boundary, while 90 is the conservative fixture policy");

            if (row[0] == 96) {
                for (String field : List.of("xfm_index_id", "xfm_index_cents", "xfm_mark_cents", "xfm_oracle_day",
                        "xfm_oracle_quality", "xfm_max_leverage", "xfm_derivatives_reduce_only")) {
                    Datum original = asset.vars.remove(field); assertNotNull(original, field);
                    assertFalse(v.test(predicate, frame), "Missing is never a qualified zero: " + field);
                    asset.vars.put(field, original); assertTrue(v.test(predicate, frame));
                }
                for (String field : List.of("xfm_mark_cents", "xfm_oracle_quality", "xfm_max_leverage")) {
                    Datum original = asset.vars.get(field); asset.put(field, 0);
                    assertFalse(v.test(predicate, frame), "Original positive gate: " + field); asset.vars.put(field, original);
                }
                asset.put("xfm_oracle_day", 0); assertFalse(v.test(predicate, frame)); asset.put("xfm_oracle_day", 1);
                asset.put("xfm_derivatives_reduce_only", 1); assertFalse(v.test(predicate, frame)); asset.put("xfm_derivatives_reduce_only", 0);
                asset.list("xfm_futures_contracts").add(c); assertFalse(v.test(predicate, frame)); asset.list("xfm_futures_contracts").clear();
                assertTrue(v.test(predicate, frame));
                assertThrows(IllegalArgumentException.class, () -> v.test(Clausewitz.parse("trigger_else = { always = yes }"), frame));
                assertThrows(IllegalArgumentException.class, () -> v.test(Clausewitz.parse("trigger_else_if = { limit = { always = yes } always = yes }"), frame));
            }
            if (row[0] != 90 && row[0] != 96) continue;
            // Existing authored account/oracle inputs; actual submit/match/reserve/MTM/funding do every transfer.
            Node la = receiptActor(v, "negative-long", 100000), sa = receiptActor(v, "negative-short", 100000);
            Node buy = submit(v, la, c, 1, 128, Math.toIntExact(negativeQuote));
            Node sell = submit(v, sa, c, 2, 128, Math.toIntExact(negativeQuote));
            assertNotNull(buy); assertNotNull(sell); assertEquals(1, c.list("xfm_positions").size());
            assertEquals(row[2], c.integer("xfm_execution_volume_cents")); assertEquals(128, c.integer("xfm_execution_lots"));
            Node p = c.list("xfm_positions").getFirst(), lm = p.ref("xfm_long_reservation"), sm = p.ref("xfm_short_reservation");
            assertFillReceipt(p, buy, sell, 128, Math.toIntExact(negativeQuote));
            assertEquals(row[2], lm.integer("xfm_remaining_cents")); assertEquals(row[2], sm.integer("xfm_remaining_cents"));
            long longFree = la.ref("xfm_account").integer("xfm_free_cents"), shortFree = sa.ref("xfm_account").integer("xfm_free_cents");
            BigDecimal cash = v.cashStock(); long fees = v.exchange.integer("xfm_fee_cents");
            long funding = row[0] == 90 ? 11 : 12, mtm = row[0] == 90 ? 1152 : 1280;
            v.exchange.put("xfm_day", 2); asset.put("xfm_oracle_day", 2);
            v.run("xfm_futures_position_daily_effect", p);
            assertEquals(2, p.integer("xfm_last_settled_day")); assertEquals(2, p.integer("xfm_last_funding_day"));
            assertEquals(new BigDecimal("-0.001"), ((NumberDatum) p.vars.get("xfm_funding_rate")).value().stripTrailingZeros());
            assertEquals(funding, p.integer("xfm_pay_now")); assertEquals(2, p.integer("xfm_pending_kind"));
            assertFalse(p.vars.containsKey("xfm_pending_payment")); assertFalse(p.vars.containsKey("xfm_pending_amount"));
            assertEquals(row[2], lm.integer("xfm_remaining_cents")); assertEquals(row[2] - mtm - funding, sm.integer("xfm_remaining_cents"));
            assertEquals(longFree + mtm + funding, la.ref("xfm_account").integer("xfm_free_cents"));
            assertEquals(shortFree, sa.ref("xfm_account").integer("xfm_free_cents"));
            Map<String, Datum> paid = Map.copyOf(p.vars); v.run("xfm_futures_position_daily_effect", p);
            assertEquals(paid, p.vars); assertEquals(fees, v.exchange.integer("xfm_fee_cents")); assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
    }

    private static void assertActiveMarginsResolve(Vm v) {
        for (Node position : v.nodes.values()) if (position.type.equals("xfm_futures_position") && !position.ended
                && position.vars.containsKey("xfm_kind") && position.integer("xfm_status") == 0 && position.integer("xfm_lots") > 0) {
            for (String side : List.of("long", "short")) {
                Node reserve = position.ref("xfm_" + side + "_reservation"); assertNotNull(reserve, position.id + side);
                assertFalse(reserve.ended, position.id + side + " must not inherit a subsequently discarded reservation");
                assertSame(position.ref("xfm_" + side + "_account"), reserve.ref("xfm_account"));
                assertSame(position, reserve.ref("xfm_futures_position"));
            }
        }
    }

    @Test void primitiveReceiptPreservesDistinctOrderPairsAcrossMultipleActualPositiveFills() throws IOException {
        Vm v = vm(); Node c = series(v, "receipt-many"), seller = receiptActor(v, "seller", 2000); List<Node> bids = new ArrayList<>();
        for (int i = 0; i < 3; i++) bids.add(submit(v, receiptActor(v, "maker-" + i, 2000), c, 1, 1, 100));
        BigDecimal cash = v.cashStock(); Node incoming = submit(v, seller, c, 2, 3, 100);
        assertEquals(3, c.list("xfm_positions").size());
        for (int i = 0; i < 3; i++) {
            Node position = c.list("xfm_positions").get(i); assertFillReceipt(position, bids.get(i), incoming, 1, 100);
            assertEquals(0, position.integer("xfm_fill_buy_intent")); assertEquals(0, position.integer("xfm_fill_sell_intent"));
            assertFalse(position.vars.containsKey("xfm_fill_buy_close_source_id")); assertFalse(position.vars.containsKey("xfm_fill_sell_close_source_id"));
            assertFalse(position.vars.containsKey("xfm_fill_slice_source_position_id"));
        }
        assertEquals(4, v.exchange.integer("xfm_fee_cents")); assertEquals(1, incoming.integer("xfm_fee_paid_cents"));
        assertEquals(cash, v.cashStock()); assertActiveMarginsResolve(v); assertBalanced(v);
    }

    @Test void correctedSingleSellCloseWritesSamePrimitiveFillKeyOnAllocatedSliceAndNovatedPosition() throws IOException {
        Vm v = vm(); Node c = series(v, "receipt-close"), player = receiptActor(v, "player", 2000), oldShort = receiptActor(v, "old-short", 2000);
        Node originalBuy = submit(v, player, c, 1, 1, 100), originalSell = submit(v, oldShort, c, 2, 1, 100);
        Node source = c.list("xfm_positions").getFirst(); assertFillReceipt(source, originalBuy, originalSell, 1, 100);
        Map<String, Datum> oldReceipt = primitiveReceipt(source);
        Node newShort = submit(v, player, c, 2, 1, 100);
        player.put("xfm_futures_selected_position", source); player.put("xfm_futures_reduce_lots", 1); player.put("xfm_futures_limit_cents", 100);
        v.run("xfm_futures_reduce_effect", player); Node close = (Node) v.scopes.get("xfm_fut_incoming");
        Node replacement = receiptActor(v, "replacement", 2000); BigDecimal cash = v.cashStock(); Node buy = submit(v, replacement, c, 1, 2, 100);
        Node opened = c.list("xfm_positions").getFirst(), novated = c.list("xfm_positions").getLast(), slice = (Node) v.scopes.get("xfm_fut_sell_slice");
        assertFillReceipt(opened, buy, newShort, 1, 100); assertFillReceipt(novated, buy, close, 1, 100); assertFillReceipt(slice, buy, close, 1, 100);
        assertEquals(1, novated.integer("xfm_fill_sell_intent")); assertEquals(1, slice.integer("xfm_fill_sell_intent"));
        assertEquals(source.integer("xfm_position_id"), novated.integer("xfm_fill_sell_close_source_id"));
        assertEquals(source.integer("xfm_position_id"), slice.integer("xfm_fill_slice_source_position_id"));
        assertFalse(novated.vars.containsKey("xfm_fill_slice_source_position_id"));
        assertEquals(0, source.integer("xfm_lots")); assertEquals(oldReceipt, primitiveReceipt(source), "Never backfill/rewrite the old source receipt");
        assertNotEquals(opened.integer("xfm_fill_sell_order_id"), novated.integer("xfm_fill_sell_order_id"));
        assertEquals(cash, v.cashStock()); assertActiveMarginsResolve(v); assertBalanced(v);
    }

    @Test void sharedCloseSliceCommitsOnceAndForcedExitIntentIsDistinctFromAnOrdinaryClose() throws IOException {
        for (boolean forced : List.of(false, true)) {
            Vm v = vm(); Node c = series(v, "intent"), la = receiptActor(v, "long", 2000), sa = receiptActor(v, "short", 2000);
            submit(v, la, c, 1, 1, 100); submit(v, sa, c, 2, 1, 100); Node source = c.list("xfm_positions").getFirst();
            Node replacement = forced ? receiptActor(v, "replacement", 2000) : null;
            BigDecimal cash = v.cashStock(); Node slice;
            if (forced) {
                Node buy = submit(v, replacement, c, 1, 1, 100);
                v.execute(substitute(v.definition("xfm_futures_post_exit_effect"), Clausewitz.parse("SIDE = long ORDER_SIDE = 2 LONG_EXIT = yes")), new Frame(source, null, source));
                Node close = (Node) v.scopes.get("xfm_fut_exit_order"); slice = (Node) v.scopes.get("xfm_fut_sell_slice");
                assertFillReceipt(slice, buy, close, 1, 100); assertEquals(2, slice.integer("xfm_fill_sell_intent"));
            } else {
                la.put("xfm_futures_selected_position", source); la.put("xfm_futures_reduce_lots", 1); la.put("xfm_futures_limit_cents", 100); v.run("xfm_futures_reduce_effect", la);
                Node sell = (Node) v.scopes.get("xfm_fut_incoming");
                sa.put("xfm_futures_selected_position", source); sa.put("xfm_futures_reduce_lots", 1); sa.put("xfm_futures_limit_cents", 100); v.run("xfm_futures_reduce_effect", sa);
                Node buy = (Node) v.scopes.get("xfm_fut_incoming"); slice = (Node) v.scopes.get("xfm_fut_buy_slice");
                assertSame(slice, v.scopes.get("xfm_fut_sell_slice")); assertFillReceipt(slice, buy, sell, 1, 100);
                assertEquals(1, slice.integer("xfm_fill_buy_intent")); assertEquals(1, slice.integer("xfm_fill_sell_intent"));
                assertEquals(source.integer("xfm_position_id"), slice.integer("xfm_fill_buy_close_source_id"));
                assertTrue(c.list("xfm_positions").isEmpty());
            }
            Map<String, Datum> before = primitiveReceipt(slice); v.exchange.put("xfm_day", 2); v.run("xfm_futures_fill_receipt_effect", slice);
            assertEquals(before, primitiveReceipt(slice)); assertFalse(slice.vars.containsKey("xfm_fr_ready"));
            assertEquals(cash, v.cashStock()); assertActiveMarginsResolve(v); assertBalanced(v);
        }
    }

    @Test void noPositiveFillOrMissingPermanentAccountIdentityLeavesReceiptUnknownWithoutChangingCash() throws IOException {
        for (String defect : List.of("no-cross", "allocation", "missing-id", "fractional-id")) {
            Vm v = vm(); Node c = series(v, defect), la = receiptActor(v, "long", 2000), sa = receiptActor(v, "short", 2000);
            submit(v, la, c, 1, 1, 100);
            if (defect.equals("allocation")) v.failType = "xfm_futures_position";
            if (defect.equals("missing-id")) la.ref("xfm_account").vars.remove("xfm_account_id");
            if (defect.equals("fractional-id")) la.ref("xfm_account").vars.put("xfm_account_id", new NumberDatum(new BigDecimal("1.5")));
            BigDecimal cash = v.cashStock(); submit(v, sa, c, 2, 1, defect.equals("no-cross") ? 101 : 100);
            if (defect.endsWith("id")) assertEquals(1, c.list("xfm_positions").size(), "Missing receipt evidence must not modify real matching behavior");
            assertTrue(c.list("xfm_positions").stream().noneMatch(p -> p.vars.containsKey("xfm_fill_receipt_version")));
            assertTrue(v.nodes.values().stream().noneMatch(p -> p.vars.containsKey("xfm_fr_ready")));
            assertEquals(cash, v.cashStock()); assertBalanced(v);
        }
        Vm v = vm(); Node old = v.node("old-position", "xfm_futures_position"); old.put("xfm_lots", 1);
        v.run("xfm_futures_fill_receipt_effect", old); assertTrue(primitiveReceipt(old).isEmpty());
    }

    private static Node receiptActor(Vm v, String name, long free) {
        Node actor = actor(v, name, free); actor.ref("xfm_account").put("xfm_account_id", v.nodes.size());
        return actor; // Existing finite fixture's explicit account-allocation identity port; no new money/match port.
    }
    private static boolean fillReceiptName(String key) { return key.startsWith("xfm_fill_") && !key.equals("xfm_fill_gross"); }
    private static Map<String, Datum> primitiveReceipt(Node node) {
        Map<String, Datum> result = new LinkedHashMap<>(); node.vars.forEach((key, value) -> { if (fillReceiptName(key)) result.put(key, value); }); return Map.copyOf(result);
    }
    private static void assertFillReceipt(Node target, Node buy, Node sell, int lots, int price) {
        assertEquals(1, target.integer("xfm_fill_receipt_version")); assertEquals(1, target.integer("xfm_fill_day"));
        assertEquals(buy.integer("xfm_order_id"), target.integer("xfm_fill_buy_order_id"));
        assertEquals(sell.integer("xfm_order_id"), target.integer("xfm_fill_sell_order_id"));
        assertEquals(buy.ref("xfm_account").integer("xfm_account_id"), target.integer("xfm_fill_buy_account_id"));
        assertEquals(sell.ref("xfm_account").integer("xfm_account_id"), target.integer("xfm_fill_sell_account_id"));
        assertEquals(lots, target.integer("xfm_fill_lots")); assertEquals(price, target.integer("xfm_fill_mark_cents"));
        assertTrue(primitiveReceipt(target).values().stream().allMatch(value -> value instanceof NumberDatum), "No weak order/account/story references");
        assertFalse(target.vars.containsKey("xfm_fr_ready"));
    }


    @Test void controlledDebtFixtureRunsOriginalCoverCashConsentAndSameOperationWithoutMinting() throws IOException {
        Vm v=debtFixtureVm();Node player=v.nodes.get("debt-player");BigDecimal cash=v.cashStock();
        assertTrue(v.validGui("xfmd_setup_gui",player));v.runGui("xfmd_setup_gui",player);
        Node a=player.ref("xfmd_a_claim"),b=player.ref("xfmd_b_claim");
        assertNotNull(a);assertNotNull(b);assertEquals(2,v.created("xfmd_claim_source"));assertEquals(2,v.created("xfm_debt_claim"));
        assertEquals(2000,a.integer("xfm_original_cents"));assertEquals(1000,b.integer("xfm_original_cents"));
        assertEquals(0,a.integer("xfm_fund_paid_cents"));assertEquals(0,b.integer("xfm_fund_paid_cents"));
        assertEquals(cash,v.cashStock());assertEquals(List.of(1L,1L),v.debtNewsKinds);
        Node creditor=a.ref("xfm_creditor_account");long creditorBefore=creditor.integer("xfm_free_cents");
        // Original .106 ultimately calls this exact original selected-payment effect.
        player.put("xfm_selected_debt",a);player.put("xfm_ui_debt_pay_cents",1000);
        v.run("xfm_debt_pay_selected_effect",player);
        assertEquals(2000,player.ref("xfm_account").integer("xfm_free_cents"));
        assertEquals(creditorBefore+1000,creditor.integer("xfm_free_cents"));
        assertEquals(1000,a.integer("xfm_outstanding_cents"));assertEquals(1000,a.integer("xfm_repaid_cents"));
        assertEquals(31,a.ref("xfm_debtor_account").integer("xfm_crisis_relief_until"));
        player.put("xfm_selected_debt",b);v.run("xfm_debt_restructure_selected_effect",player);
        assertEquals(900,b.integer("xfm_outstanding_cents"));assertEquals(100,b.integer("xfm_written_off_cents"));
        assertEquals(31,b.integer("xfm_due_day"));assertEquals(1900,a.ref("xfm_debtor_account").integer("xfm_total_debt_cents"));
        assertEquals(List.of(1L,1L,2L,3L),v.debtNewsKinds);
        assertTrue(v.validGui("xfmd_review_gui",player));v.runGui("xfmd_review_gui",player);
        assertEquals(0,a.integer("xfmd_retry_result"));assertEquals(1,player.integer("xfmd_review_recorded"));
        assertEquals(1000,a.integer("xfm_payment_actual_cents"),"Old retained value is not a second payment; current result is0");
        assertEquals(a.integer("xfmd_help_payer_free"),a.integer("xfmd_retry_payer_free"));
        assertEquals(b.integer("xfmd_consent_outstanding"),b.integer("xfmd_consent_retry_outstanding"));
        assertEquals(b.integer("xfmd_consent_written_off"),b.integer("xfmd_consent_retry_written_off"));
        assertEquals(2000,player.ref("xfm_account").integer("xfm_free_cents"));
        assertSame(b,player.ref("xfm_selected_debt"));assertEquals(List.of(1L,1L,2L,3L),v.debtNewsKinds);
        assertEquals(2,v.debtRelationshipCalls);assertEquals(cash,v.cashStock());assertBalanced(v);
        v.run("xfmd_review_effect",player);v.run("xfmd_setup_effect",player);
        assertEquals(2,v.created("xfm_debt_claim"));assertEquals(cash,v.cashStock());assertEquals(2,v.debtRelationshipCalls);
        // A truly new valid operation is a new real payment, never rejected as the previous retry.
        long oldOperation=player.ref("xfm_account").integer("xfm_last_debt_payment_operation");
        player.put("xfm_selected_debt",a);player.put("xfm_ui_debt_pay_cents",1000);
        v.run("xfm_debt_pay_selected_effect",player);
        assertEquals(oldOperation+1,player.ref("xfm_account").integer("xfm_last_debt_payment_operation"));
        assertEquals(1,a.integer("xfm_result"));assertEquals(0,a.integer("xfm_outstanding_cents"));assertEquals(2000,a.integer("xfm_repaid_cents"));
        assertEquals(1000,player.ref("xfm_account").integer("xfm_free_cents"));
        assertEquals(creditorBefore+2000,creditor.integer("xfm_free_cents"));
        assertEquals(List.of(1L,1L,2L,3L,2L),v.debtNewsKinds);assertEquals(cash,v.cashStock());assertBalanced(v);
    }
    @Test void controlledDebtFixtureRefusesMissingIllegalAndNonControlledSourcesBeforeAnyStory() throws IOException {
        for(String defect:List.of("no-origin","not-closed","child-owner","AI-owner","frozen-player","first-payment-only","missing-cash", "missing-account-id","AI-child","AI-dead","AI-not-primary","wrong-id","same-beneficiary")) {
            Vm v=debtFixtureVm();Node p=v.nodes.get("debt-player"),d=v.nodes.get("debt-debtor");BigDecimal cash=v.cashStock();
            if(defect.equals("no-origin"))v.globalVars.remove("xfmf_fixture_owner");
            if(defect.equals("not-closed"))p.vars.remove("xfmf_close_recorded");
            if(defect.equals("child-owner"))p.adult=false;
            if(defect.equals("AI-owner"))p.ai=true;
            if(defect.equals("frozen-player"))p.ref("xfm_account").put("xfm_account_frozen",1);
            if(defect.equals("first-payment-only")){p.ref("xfm_account").put("xfm_free_cents",1999);cash=v.cashStock();}
            if(defect.equals("missing-cash"))d.ref("xfm_account").vars.remove("xfm_free_cents");
            if(defect.equals("missing-account-id"))d.ref("xfm_account").vars.remove("xfm_account_id");
            if(defect.equals("AI-child"))d.adult=false;
            if(defect.equals("AI-dead"))d.alive=false;
            if(defect.equals("AI-not-primary"))d.vars.remove("xfm_account");
            if(defect.equals("wrong-id"))d.ref("xfm_account").put("xfm_account_id",44);
            if(defect.equals("same-beneficiary"))d.ref("xfm_account").put("xfm_beneficial_owner",p);
            assertFalse(v.validGui("xfmd_setup_gui",p),defect);v.run("xfmd_setup_effect",p);
            assertEquals(0,v.created("xfmd_claim_source"),defect);assertEquals(0,v.created("xfm_debt_claim"),defect);
            assertFalse(p.vars.containsKey("xfmd_setup_attempted"));assertTrue(v.debtNewsKinds.isEmpty());
            if(!defect.equals("missing-cash"))assertEquals(cash,v.cashStock());
        }
    }
    @Test void controlledDebtFixtureConsumesPartialFailureAndRefusesUnauthorizedOrInsufficientHelp() throws IOException {
        Vm failed=debtFixtureVm();Node fp=failed.nodes.get("debt-player");failed.failType="xfm_debt_claim";
        BigDecimal before=failed.cashStock();failed.runGui("xfmd_setup_gui",fp);
        assertEquals(1,fp.integer("xfmd_setup_attempted"));assertFalse(fp.vars.containsKey("xfmd_seeded"));
        assertEquals(2,failed.created("xfmd_claim_source"));assertEquals(0,failed.created("xfm_debt_claim"));
        failed.failType="";failed.run("xfmd_setup_effect",fp);assertEquals(0,failed.created("xfm_debt_claim"));assertEquals(before,failed.cashStock());
        Vm v=debtFixtureVm();Node player=v.nodes.get("debt-player");v.runGui("xfmd_setup_gui",player);
        Node a=player.ref("xfmd_a_claim"),b=player.ref("xfmd_b_claim"),stranger=actor(v,"wrong-creditor",3000);
        BigDecimal cash=v.cashStock();stranger.put("xfm_selected_debt",b);v.run("xfm_debt_restructure_selected_effect",stranger);
        assertFalse(b.vars.containsKey("xfm_creditor_haircut_done"));assertEquals(1000,b.integer("xfm_outstanding_cents"));
        a.put("xfm_request_payer",player.ref("xfm_account"));a.put("xfm_request_operation",1);a.put("xfm_request_cents",4000);
        player.ref("xfm_account").put("xfm_account_frozen",1);v.run("xfm_debt_repay_effect",a);
        assertEquals(0,a.integer("xfm_result"));assertEquals(2000,a.integer("xfm_outstanding_cents"));assertEquals(cash,v.cashStock());
        player.ref("xfm_account").put("xfm_account_frozen",0);a.put("xfm_request_cents",1000);
        player.ref("xfm_account").put("xfm_free_cents",999);BigDecimal insufficient=v.cashStock();v.run("xfm_debt_repay_effect",a);
        assertEquals(0,a.integer("xfm_result"));assertEquals(2000,a.integer("xfm_outstanding_cents"));assertEquals(insufficient,v.cashStock());
        assertFalse(v.validGui("xfmd_review_gui",player));assertEquals(List.of(1L,1L),v.debtNewsKinds);
    }
    @Test void controlledDebtFixtureReviewRejectsAnotherClaimWrongDayOrMissingProofAndKeepsOtherSelection() throws IOException {
        for(String defect:List.of("other-source","next-day","missing-operation","wrong-payer","not-credited")) {
            Vm v=debtFixtureVm();Node p=v.nodes.get("debt-player");v.runGui("xfmd_setup_gui",p);
            Node a=p.ref("xfmd_a_claim"),b=p.ref("xfmd_b_claim");
            p.put("xfm_selected_debt",a);p.put("xfm_ui_debt_pay_cents",1000);v.run("xfm_debt_pay_selected_effect",p);
            p.put("xfm_selected_debt",b);v.run("xfm_debt_restructure_selected_effect",p);
            if(defect.equals("other-source"))a.put("xfm_source",p.ref("xfmd_b_source"));
            if(defect.equals("next-day"))v.exchange.put("xfm_day",2);
            if(defect.equals("missing-operation"))a.vars.remove("xfm_request_operation");
            if(defect.equals("wrong-payer"))a.put("xfm_request_payer",a.ref("xfm_debtor_account"));
            if(defect.equals("not-credited"))b.put("xfm_written_off_cents",0);
            BigDecimal cash=v.cashStock();assertFalse(v.validGui("xfmd_review_gui",p),defect);v.run("xfmd_review_effect",p);
            assertFalse(p.vars.containsKey("xfmd_review_attempted"));assertEquals(cash,v.cashStock());assertEquals(List.of(1L,1L,2L,3L),v.debtNewsKinds);
        }
        Vm v=debtFixtureVm();Node p=v.nodes.get("debt-player");v.runGui("xfmd_setup_gui",p);
        p.put("xfm_selected_debt",p.ref("xfmd_a_claim"));p.put("xfm_ui_debt_pay_cents",1000);v.run("xfm_debt_pay_selected_effect",p);
        p.put("xfm_selected_debt",p.ref("xfmd_b_claim"));v.run("xfm_debt_restructure_selected_effect",p);
        p.vars.remove("xfm_selected_debt");v.runGui("xfmd_review_gui",p);assertFalse(p.vars.containsKey("xfm_selected_debt"));
    }
    /** Same existing VM. Only lifecycle-review/opinion/news boundaries are ports, never cash/cover/repay/consent. */
    private static Vm debtFixtureVm() throws IOException {
        Vm v=vm();v.debtBoundaryPorts=true;
        for(String input:List.of("scripted_effects/xfm_debt_cover.txt","scripted_effects/xfm_debt_repayment.txt",
            "scripted_effects/xfm_debt_closure.txt","scripted_triggers/xfm_debt_triggers.txt","script_values/xfm_debt_values.txt"))
            addDebtDefinitions(v,Clausewitz.parse(Files.readString(SOURCE.resolve("common").resolve(input))));
        var input=new org.xar.ck3.markets.acceptance.FollowupContracts.ControlledDebtAidNewsRequest(3,"debt-aid-news-engine-fixture",true,
            new org.xar.ck3.markets.acceptance.FollowupContracts.ControlledDebtParticipants("1","2","3"));
        org.xar.ck3.markets.acceptance.FollowupObservationScripts.renderControlledDebtAidNews(input).forEach((path,bytes)->{
            if(path.startsWith("common/scripted_effects/")||path.startsWith("common/scripted_triggers/")||path.startsWith("common/scripted_guis/"))
                addDebtDefinitions(v,Clausewitz.parse(new String(bytes,java.nio.charset.StandardCharsets.UTF_8)));
        });
        Node p=actor(v,"debt-player",3000),d=actor(v,"debt-debtor",5000),c=actor(v,"debt-creditor",4000);
        p.ref("xfm_account").put("xfm_account_id",3);d.ref("xfm_account").put("xfm_account_id",1);c.ref("xfm_account").put("xfm_account_id",2);
        p.put("xfmf_seeded",1);p.put("xfmf_close_recorded",1);p.put("xfmf_p_long",d);p.put("xfmf_p_short",c);
        for(Node a:List.of(d,c)){a.ai=true;a.put("xfmf_seed_version",1);a.put("xfmf_fixture_actor",1);a.put("xfmf_owner",p);}
        v.globalVars.put("xfmf_fixture_owner",p);return v;
    }
    private static void addDebtDefinitions(Vm v,Block source) {
        for(Entry e:source.entries())if(v.program.putIfAbsent(e.key(),(Block)e.value())!=null)throw new IllegalArgumentException("duplicate debt subset definition "+e.key());
    }

    @Test void syntheticGenesisAndTwoBoundedBatchesExecuteProductionCashMintReserveAndNormalSpotBodies() throws IOException {
        Vm v=loadVm();Node owner=loadOwner(v);BigDecimal before=v.cashStock();v.runGui("xfmcl_setup_gui",owner);
        assertEquals(1,owner.integer("xfmcl_seeded"));assertEquals(5200000,owner.integer("xfmcl_genesis_deposited_cents"));
        assertEquals(before.add(BigDecimal.valueOf(16000000)).stripTrailingZeros(),v.cashStock());
        for(String role:List.of("buyer1","buyer2","buyer3","buyer4","seller1","seller2","seller3","seller4")){
            Node actor=owner.ref("xfmcl_"+role);assertNotNull(actor);assertTrue(actor.ai);assertNotSame(owner,actor);
            assertEquals(20000,actor.integer("xfmcl_genesis_gold_added"));assertEquals(1,actor.integer("xfmcl_role_ready"));
            assertEquals(actor,actor.ref("xfm_account").ref("xfm_holder"));
            assertEquals(actor.ref("xfm_account"),owner.ref("xfmcl_"+role+"_primary"));
            assertEquals(actor.vars.get("xfmcl_genesis_gold_before"),owner.vars.get("xfmcl_"+role+"_gold_before"));
            assertEquals(actor.vars.get("xfmcl_gold_after_deposit"),owner.vars.get("xfmcl_"+role+"_gold_after_deposit"));
        }
        v.runGui("xfmcl_batch_gui",owner);assertEquals(32,owner.integer("xfmcl_count"),
            () -> v.loadFirstFailure+"; final="+loadDiagnostic(v,owner));
        assertEquals(1,owner.integer("xfmcl_batch_attempts"));assertEquals(32,owner.integer("xfmcl_hot_books"));
        v.runGui("xfmcl_batch_gui",owner);assertEquals(64,owner.integer("xfmcl_count"));
        assertEquals(64,owner.integer("xfmcl_hot_books"));assertEquals(64,v.exchange.integer("xfm_registered_coin_count"));
        assertEquals(64,v.exchange.integer("xfm_resident_coin_count"));assertEquals(64,v.exchange.integer("xfm_active_coin_count"));
        assertEquals(0,v.exchange.integer("xfm_pending_coin_count"));
        assertEquals(64,v.globalLists.get("xfm_coin_registry").size());assertEquals(64,v.created("xfm_finance_coin"));
        for(Node order:v.nodes.values())if(order.type.equals("xfm_spot_order")){
            assertTrue(order.vars.containsKey("xfm_is_maker_quote"),"Production initializes the typed maker bit even for ordinary orders");
            assertTrue(Set.of(0L,1L).contains(order.integer("xfm_is_maker_quote")));
        }
        assertEquals(128,v.nodes.values().stream().filter(n->n.type.equals("xfm_spot_order")&&n.integer("xfm_is_maker_quote")==0).count());
        assertEquals(0,v.created("xfm_futures_order"));assertEquals(0,v.created("xfm_finance_debt"));
        for(Node coin:owner.list("xfmcl_coins")){
            assertEquals(15000,coin.integer("xfm_supply_units"));assertEquals(0,coin.integer("xfm_registration_paid_cents"));
            assertFalse(coin.vars.containsKey("xfm_issue_receipt_version"));
            assertEquals(15000,coin.list("xfm_holders").stream().mapToLong(n->n.integer("xfm_quantity_units")).sum());
            Node issuerPosition=coin.list("xfm_holders").stream().filter(n->n.ref("xfm_account")==coin.ref("xfm_issuer_account")).findFirst().orElseThrow();
            assertEquals(9900,issuerPosition.integer("xfm_quantity_units"),"Real12500 mint minus100 user transfer minus2500 maker transfer");
            assertEquals(9900,v.integerValue("xfm_finance_position_available_value",issuerPosition),"Actual asset-value definition, not an unknown scalar");
            Node makerPosition=coin.list("xfm_holders").stream().filter(n->n.ref("xfm_account")==coin.ref("xfm_market_maker_account")).findFirst().orElseThrow();
            assertEquals(2500,makerPosition.integer("xfm_quantity_units"));assertEquals(100,makerPosition.integer("xfm_reserved_units"));
            Node sellerPosition=coin.list("xfm_holders").stream().filter(n->n.ref("xfm_account").integer("xfm_system_account")==0).findFirst().orElseThrow();
            assertEquals(100,sellerPosition.integer("xfm_quantity_units"));assertEquals(100,sellerPosition.integer("xfm_reserved_units"));
            assertNotSame(sellerPosition.ref("xfm_account").ref("xfm_holder"),owner);
            assertEquals(60,coin.ref("xfm_maintenance_reservation").integer("xfm_remaining_cents"));
            assertEquals(100,coin.ref("xfm_bond_reservation").integer("xfm_remaining_cents"));
            assertEquals(0,coin.ref("xfm_maker_reservation").integer("xfm_remaining_cents"),"Original maker consumes its real seed");
            assertTrue(coin.list("xfm_spot_orders").size()<=4);assertEquals(0,coin.integer("xfm_actual_trades"));
            for(Node order:coin.list("xfm_spot_orders")){assertEquals(1,order.integer("xfm_remaining_lots"));assertEquals(0,order.integer("xfm_filled_lots"));}
        }
        assertEquals(before.add(BigDecimal.valueOf(16000000)).stripTrailingZeros(),v.cashStock());assertBalanced(v);
        long coins=v.created("xfm_finance_coin");v.run("xfmcl_setup_effect",owner);assertEquals(coins,v.created("xfm_finance_coin"));
        assertEquals(before.add(BigDecimal.valueOf(16000000)).stripTrailingZeros(),v.cashStock());
    }
    @Test void syntheticPartialRealReservationFailureRetainsRightsAndStopsWithoutRetryOrUnbackedCash() throws IOException {
        Vm v=loadVm();Node owner=loadOwner(v);v.runGui("xfmcl_setup_gui",owner);BigDecimal cash=v.cashStock();
        v.failType="xfm_finance_reservation";v.runGui("xfmcl_batch_gui",owner);
        assertEquals(1,owner.integer("xfmcl_failed"));assertEquals(0,owner.integer("xfmcl_count"));
        assertEquals(1,v.created("xfm_finance_coin"));assertEquals(1,v.exchange.integer("xfm_pending_coin_count"));
        assertEquals(15000,v.globalLists.get("xfm_coin_registry").getFirst().integer("xfm_supply_units"));
        assertFalse(v.validGui("xfmcl_batch_gui",owner));assertFalse(v.validGui("xfmcl_setup_gui",owner));
        long created=v.nodes.size();v.run("xfmcl_batch_effect",owner);assertEquals(created,v.nodes.size());
        assertEquals(1,owner.integer("xfmcl_batch_attempts"));assertEquals(cash,v.cashStock());assertBalanced(v);
    }
    @Test void syntheticWrongRulesNonemptyWorldAndForeignActorRejectBeforeAnyGenesis() throws IOException {
        for(String rule:List.of("xfm_capacity_standard","xfm_ai_standard","xfm_ai_issuance_disabled","xfm_futures_disabled","xfm_spot_enabled")){
            Vm v=loadVm();Node owner=loadOwner(v);v.rules.remove(rule);int n=v.nodes.size();
            assertFalse(v.validGui("xfmcl_setup_gui",owner));v.run("xfmcl_setup_effect",owner);assertEquals(n,v.nodes.size());
            assertFalse(v.globalVars.containsKey("xfmcl_fixture_owner"));assertEquals(0,v.cashStock().signum());
        }
        Vm occupied=loadVm();Node owner=loadOwner(occupied);occupied.exchange.put("xfm_registered_coin_count",1);
        assertFalse(occupied.validGui("xfmcl_setup_gui",owner));
        Vm bound=loadVm();Node actual=loadOwner(bound);bound.runGui("xfmcl_setup_gui",actual);
        Node foreign=actor(bound,"foreign-human",0);assertFalse(bound.validGui("xfmcl_batch_gui",foreign));
        assertFalse(bound.validGui("xfmcl_grow_gui",foreign));
    }
    @Test void syntheticActualObservationBodyIsDayIdempotentPreservesMissingFieldsAndNeverAdvancesFinance() throws IOException {
        Vm v=loadVm();Node owner=loadOwner(v);v.runGui("xfmcl_setup_gui",owner);loadObservationStage(v,owner,2048);
        for(int day=1;day<=8;day++){
            v.scriptDate=1000+day;v.exchange.put("xfm_day",day);v.run("xfmcl_after_finance_effect",owner);
            assertEquals(day,owner.integer("xfmcl_samples1"));assertEquals(day,v.exchange.integer("xfm_day"));
            v.run("xfmcl_after_finance_effect",owner);assertEquals(day,owner.integer("xfmcl_samples1"));
            assertEquals(0,owner.integer("xfmcl_s1_d"+day+"_daily_raw_attempt_count_present"));
            assertFalse(owner.vars.containsKey("xfmcl_s1_d"+day+"_daily_raw_attempt_count"));
        }
        assertEquals(1,owner.integer("xfmcl_window1_ready"));assertTrue(v.validGui("xfmcl_grow_gui",owner));
        v.runGui("xfmcl_grow_gui",owner);assertEquals(4096,owner.integer("xfmcl_target"));
        assertFalse(v.validGui("xfmcl_grow_gui",owner));assertEquals(1,owner.integer("xfmcl_grow_attempted"));
        loadObservationStage(v,owner,4096);
        for(int day=1;day<=8;day++){v.scriptDate=1008+day;v.exchange.put("xfm_day",8+day);v.run("xfmcl_after_finance_effect",owner);}
        assertEquals(8,owner.integer("xfmcl_samples2"));assertEquals(1,owner.integer("xfmcl_window2_ready"));
        assertFalse(owner.vars.containsKey("xfmcl_gap"));
        assertEquals(1,v.loadLogs.stream().filter(x->x.contains("synthetic_load_2048_window_recorded")).count());
        assertEquals(1,v.loadLogs.stream().filter(x->x.contains("synthetic_load_4096_window_recorded")).count());
    }
    @Test void syntheticMissedCalendarOrMissingFinancialDayCannotFabricateCoverageOrEnableGrowth() throws IOException {
        for(boolean missing:List.of(false,true)){
            Vm v=loadVm();Node owner=loadOwner(v);v.runGui("xfmcl_setup_gui",owner);loadObservationStage(v,owner,2048);
            v.scriptDate=missing?1001:1002;v.exchange.put("xfm_day",missing?1:2);
            if(missing)v.exchange.vars.remove("xfm_day");v.run("xfmcl_after_finance_effect",owner);
            assertEquals(1,owner.integer("xfmcl_gap"));assertEquals(0,owner.integer("xfmcl_samples1"));
            assertFalse(owner.vars.containsKey("xfmcl_window1_ready"));assertFalse(v.validGui("xfmcl_grow_gui",owner));
            assertTrue(v.loadLogs.isEmpty());assertFalse(owner.vars.containsKey("xfmcl_s1_d1_recorded"));
        }
    }
    private static String loadDiagnostic(Vm v,Node owner){
        Map<String,Object> state=new LinkedHashMap<>();state.put("trace",List.copyOf(v.trace));state.put("logs",List.copyOf(v.loadLogs));
        for(Node n:v.nodes.values()){
            Map<String,String> fields=new LinkedHashMap<>();
            n.vars.forEach((key,value)->fields.put(key,value instanceof Node ref?ref.id+":"+ref.type:value.toString()));
            state.put(n.id+":"+n.type,fields);
        }
        return state.toString();
    }
    private static Vm loadVm() throws IOException {
        Vm v=vm();v.loadBoundaryPorts=true;v.scriptDate=1000;
        for(String input:List.of("scripted_effects/xfm_finance_assets.txt","script_values/xfm_finance_asset_values.txt",
                "scripted_effects/xfm_registry_capacity.txt",
                "scripted_triggers/xfm_registry_capacity_triggers.txt","script_values/xfm_registry_capacity_values.txt",
                "scripted_effects/xfm_issuer_registration.txt","script_values/xfm_issuer_values.txt",
                "scripted_effects/xfm_oracle_samples.txt","scripted_effects/xfm_spot_history.txt",
                "scripted_effects/xfm_spot_submit.txt","scripted_effects/xfm_spot_orders.txt",
                "scripted_effects/xfm_spot_match.txt","scripted_effects/xfm_spot_maker.txt","scripted_effects/xfm_spot_trades.txt",
                "scripted_effects/xfm_spot_archive.txt","script_values/xfm_spot_values.txt","scripted_triggers/xfm_spot_triggers.txt")){
            for(Entry entry:Clausewitz.parse(Files.readString(SOURCE.resolve("common").resolve(input))).entries()){
                Block block=entry.value() instanceof Block b?b:new Block(List.of(new Entry("value","=",entry.value())));
                assertNull(v.program.putIfAbsent(entry.key(),block),entry.key());
            }
        }
        org.xar.ck3.markets.acceptance.FollowupObservationScripts.renderControlledLoad(
            new org.xar.ck3.markets.acceptance.FollowupContracts.ControlledLoadRequest(3,"synthetic-controlled-load",true,List.of(2048,4096))).forEach((path,bytes)->{
            if(path.startsWith("common/scripted_"))for(Entry entry:Clausewitz.parse(new String(bytes,java.nio.charset.StandardCharsets.UTF_8)).entries())
                assertNull(v.program.putIfAbsent(entry.key(),(Block)entry.value()),entry.key());
        });
        v.rules.addAll(List.of("xfm_capacity_standard","xfm_ai_standard","xfm_ai_issuance_disabled","xfm_futures_disabled","xfm_spot_enabled"));
        for(String field:List.of("xfm_day","xfm_coin_count","xfm_registered_coin_count","xfm_resident_coin_count","xfm_pending_coin_count","xfm_active_coin_count","xfm_next_coin_id","xfm_next_order_id","xfm_fee_cents"))v.exchange.put(field,0);
        v.exchange.put("xfm_registry_capacity_version",1);return v;
    }
    private static Node loadOwner(Vm v){Node owner=v.custodian;owner.ai=false;
        owner.links.put("capital_province",v.node("load-capital","province"));owner.links.put("culture",v.node("load-culture","culture"));
        owner.links.put("faith",v.node("load-faith","faith"));return owner;}
    private static void loadObservationStage(Vm v,Node owner,int count){
        // Observation-only fixture: no claim that these scalar metadata values construct a real 2048/4096 graph.
        int stage=count==2048?1:2;owner.put("xfmcl_count",count);owner.put("xfmcl_hot_books",64);
        owner.put("xfmcl_complete"+count,1);owner.put("xfmcl_start"+stage,v.scriptDate);owner.put("xfmcl_samples"+stage,0);
        owner.put("xfmcl_last_financial",v.exchange.integer("xfm_day"));
        v.exchange.put("xfm_active_coin_count",count);v.exchange.put("xfm_resident_coin_count",count);v.exchange.put("xfm_pending_coin_count",0);
    }

    @Test void originalCountyInputsProduceTheActualTwentyPercentMarkWithoutAQuoteSetter() throws IOException {
        for(int wars=0;wars<=4;wars++) {
            Vm v=riskVm(wars);Node owner=v.custodian;
            long before=v.nodes.get("risk-county-0").integer("xfmr_test_control");
            assertEquals(43,before);v.run("xfmr_prepare_world_inputs_effect",owner);
            Node asset=(Node)v.globalVars.get("xfm_trade_index");
            assertEquals(150,asset.integer("xfm_mark_cents"));assertEquals(150,asset.integer("xfm_index_cents"));
            assertEquals(8,owner.integer("xfmr_prepared_county_count"));
            assertEquals(wars*1250,owner.integer("xfmr_prepared_xfm_oracle_war_bps"));
            for(int i=1;i<=8;i++) {
                assertSame(v.nodes.get("risk-county-"+(i-1)),owner.ref("xfmr_prepared_county"+i));
                assertEquals(100,owner.integer("xfmr_prepared_control"+i));
                assertEquals(owner.integer("xfmr_target_prosperity"),owner.integer("xfmr_prepared_prosperity"+i));
                assertEquals(i<=wars?1:0,owner.integer("xfmr_prepared_war"+i));
            }
            riskWorldAction(v,"xfmr_first_world_shock_effect");
            assertEquals(120,asset.integer("xfm_mark_cents"));assertEquals(30,150-asset.integer("xfm_mark_cents"));
            riskWorldAction(v,"xfmr_second_world_shock_effect");assertEquals(100,asset.integer("xfm_mark_cents"));
            // Same owner cannot re-prepare the world after consuming its original one-shot input.
            v.run("xfmr_prepare_world_inputs_effect",owner);assertEquals(100,asset.integer("xfm_mark_cents"));
        }
        Vm tooMuchWar=riskVm(5);tooMuchWar.run("xfmr_prepare_world_inputs_effect",tooMuchWar.custodian);
        assertFalse(tooMuchWar.custodian.vars.containsKey("xfmr_world_prepare_attempted"));
        Vm changed=riskVm(0);changed.run("xfmr_prepare_world_inputs_effect",changed.custodian);
        changed.nodes.get("risk-county-holder-0").atWar=true;
        riskWorldAction(changed,"xfmr_first_world_shock_effect");
        Node actual=(Node)changed.globalVars.get("xfm_trade_index");assertNotEquals(120,actual.integer("xfm_mark_cents"));
        assertFalse(changed.test(Clausewitz.parse("xfmr_mark_trigger = { MARK = 120 }"),new Frame(changed.custodian,null,changed.custodian)));
        assertThrows(IllegalArgumentException.class,()->changed.execute(Clausewitz.parse("change_unknown_risk_input = 1"),new Frame(changed.custodian,null,changed.custodian)));
    }

    @Test void openingEquityBelowLiveMaintenanceCannotExportItsInitialBasisLossAfterFreeWithdrawal() throws IOException {
        for(int price:List.of(120,139,167,180)) {
            Vm v=riskVm(0);v.run("xfmr_prepare_world_inputs_effect",v.custodian);Node asset=(Node)v.globalVars.get("xfm_trade_index");
            Node c=riskContract(v,"basis-"+price,asset,30),la=receiptActor(v,"basis-long",10000),sa=receiptActor(v,"basis-short",10000);
            Node donor=receiptActor(v,"basis-donor",1000);riskDonate(v,donor,100);BigDecimal stock=v.cashStock();
            Node buy=riskSubmit(v,la,c,1,1,5,price),sell=riskSubmit(v,sa,c,2,1,5,price);
            List<Node> actual=List.copyOf(c.list("xfm_positions"));
            if(!actual.isEmpty()) {
                // This branch is an intentional pre-fix regression witness. It runs the original complete
                // withdrawal/MTM/fund/claim path before failing the new-opening invariant below.
                Node position=actual.getFirst();assertFillReceipt(position,buy,sell,1,price);
                assertEquals(2,v.exchange.integer("xfm_fee_cents"));
                for(Node actor:List.of(la,sa)) {
                    long free=actor.ref("xfm_account").integer("xfm_free_cents");actor.put("xfm_request_cents",free);
                    v.run("xfm_finance_withdraw_effect",actor);assertEquals(1,actor.integer("xfm_result"));
                    assertEquals(0,actor.ref("xfm_account").integer("xfm_free_cents"));
                }
                v.exchange.put("xfm_day",2);v.run("xfm_oracle_index_daily_effect",v.exchange);
                v.run("xfm_futures_position_daily_effect",position);
                assertEquals(stock,v.cashStock());assertBalanced(v);
                if(price==120) {
                    Node claim=position.ref("xfm_debt_receipt_1");assertNotNull(claim);
                    assertEquals(6,claim.integer("xfm_original_cents"));assertEquals(6,claim.integer("xfm_fund_paid_cents"));
                    assertEquals(0,claim.integer("xfm_winner_unpaid_cents"));assertEquals(6,claim.integer("xfm_fund_recourse_cents"));
                    assertSame(sa.ref("xfm_account"),claim.ref("xfm_debtor_account"));
                    assertSame(la.ref("xfm_account"),claim.ref("xfm_creditor_account"));
                    assertEquals(94,v.exchange.ref("xfm_default_fund_account").integer("xfm_free_cents"));
                }
            }
            assertTrue(actual.isEmpty(),"Unsafe new fill at "+price+" existed before actual free withdrawal / next-mark waterfall");
            assertEquals(0,buy.integer("xfm_filled_gross_cents"));assertEquals(0,sell.integer("xfm_filled_gross_cents"));
            assertEquals(0,v.exchange.integer("xfm_fee_cents"));assertEquals(0,v.created("xfm_debt_claim"));
            assertEquals(100,v.exchange.ref("xfm_default_fund_account").integer("xfm_free_cents"));
            assertEquals(0,v.exchange.integer("xfm_next_futures_position_id"));
            for(Node actor:List.of(la,sa)) {
                assertEquals(37,actor.ref("xfm_account").integer("xfm_reserved_cents"));
                actor.put("xfm_request_cents",actor.ref("xfm_account").integer("xfm_free_cents"));
                v.run("xfm_finance_withdraw_effect",actor);assertEquals(1,actor.integer("xfm_result"));
            }
            assertEquals(stock,v.cashStock());assertBalanced(v);
        }
    }

    @Test void exactMaintenanceBoundaryAndOrdinaryAtMarkFillsStillUseOriginalMarginFeesAndReceipts() throws IOException {
        for(int price:List.of(140,150,166)) {
            Vm v=riskVm(0);v.run("xfmr_prepare_world_inputs_effect",v.custodian);
            Node c=riskContract(v,"safe-"+price,(Node)v.globalVars.get("xfm_trade_index"),30);
            Node la=receiptActor(v,"safe-long",10000),sa=receiptActor(v,"safe-short",10000);BigDecimal stock=v.cashStock();
            Node buy=riskSubmit(v,la,c,1,1,5,price),sell=riskSubmit(v,sa,c,2,1,5,price);
            assertEquals(1,c.list("xfm_positions").size());Node p=c.list("xfm_positions").getFirst();
            assertFillReceipt(p,buy,sell,1,price);assertEquals((price+4)/5,p.ref("xfm_long_reservation").integer("xfm_remaining_cents"));
            assertEquals((price+4)/5,p.ref("xfm_short_reservation").integer("xfm_remaining_cents"));
            assertEquals(2,v.exchange.integer("xfm_fee_cents"));assertEquals(stock,v.cashStock());assertBalanced(v);
        }
    }

    @Test void actualCountyShockRunsStopAt110LiquidationAt120AndAnUnfilledGapWithoutFictitiousPayment() throws IOException {
        Vm v=riskVm(0);v.run("xfmr_prepare_world_inputs_effect",v.custodian);Node asset=(Node)v.globalVars.get("xfm_trade_index");
        Node la=receiptActor(v,"risk-long",100000),sa=receiptActor(v,"risk-short",100000),maker=receiptActor(v,"risk-maker",100000);
        riskDonate(v,maker,100);BigDecimal stock=v.cashStock();
        Node stop=riskOpenPair(v,asset,la,sa,"stop",30,1,1),liquidate=riskOpenPair(v,asset,la,sa,"liquidate",31,1,5),gap=riskOpenPair(v,asset,la,sa,"gap",32,100,5);
        la.put("xfm_futures_selected_position",stop);la.put("xfm_futures_stop_cents",135);la.put("xfm_futures_take_profit_cents",0);
        v.run("xfm_futures_set_stops_effect",la);assertEquals(1,la.integer("xfm_futures_result"));
        riskWorldAction(v,"xfmr_first_world_shock_effect");assertEquals(120,asset.integer("xfm_mark_cents"));
        Node stopBid=riskSubmit(v,maker,stop.ref("xfm_contract"),1,1,1,110),liqBid=riskSubmit(v,maker,liquidate.ref("xfm_contract"),1,1,1,120);
        assertEquals(0,stopBid.integer("xfm_filled_gross_cents"));assertEquals(0,liqBid.integer("xfm_filled_gross_cents"));
        v.exchange.put("xfm_day",2);v.run("xfm_oracle_index_daily_effect",v.exchange);
        v.run("xfm_finance_capitalize_default_fund_effect",v.exchange);
        for(Node p:List.of(stop,liquidate,gap))v.run("xfm_futures_position_daily_effect",p);
        assertEquals(2,stop.integer("xfm_status"));assertEquals(2,liquidate.integer("xfm_status"));
        assertEquals(110,stopBid.integer("xfm_filled_gross_cents"));assertEquals(120,liqBid.integer("xfm_filled_gross_cents"));
        Node stopSlice=riskSlice(v,stop),liqSlice=riskSlice(v,liquidate);
        assertEquals(110,stopSlice.integer("xfm_fill_mark_cents"));assertEquals(120,liqSlice.integer("xfm_fill_mark_cents"));
        assertEquals(2,stopSlice.integer("xfm_fill_sell_intent"));assertEquals(2,liqSlice.integer("xfm_fill_sell_intent"));
        assertEquals(stop.integer("xfm_position_id"),stopSlice.integer("xfm_fill_sell_close_source_id"));
        assertEquals(liquidate.integer("xfm_position_id"),liqSlice.integer("xfm_fill_slice_source_position_id"));
        assertEquals(maker.ref("xfm_account").integer("xfm_account_id"),stopSlice.integer("xfm_fill_buy_account_id"));
        assertEquals(0,gap.integer("xfm_status"));assertEquals(120,gap.integer("xfm_mark_cents"));
        assertEquals(0,gap.ref("xfm_long_reservation").integer("xfm_remaining_cents"));assertEquals(1,gap.integer("xfm_long_exit_requested"));
        assertFalse(gap.vars.containsKey("xfm_defaulted"));assertEquals(0,v.created("xfm_debt_claim"));
        assertEquals(98,v.exchange.integer("xfm_fee_cents")+v.exchange.integer("xfm_default_fund_allocated_cents"));assertEquals(stock,v.cashStock());assertBalanced(v);assertActiveMarginsResolve(v);
        Map<String,Datum> oldStop=primitiveReceipt(stop),oldLiq=primitiveReceipt(liquidate);
        long earned=v.exchange.integer("xfm_default_fund_allocated_cents"),fund=v.exchange.ref("xfm_default_fund_account").integer("xfm_free_cents");
        assertEquals(9,earned);assertEquals(100+earned,fund);
        riskWorldAction(v,"xfmr_second_world_shock_effect");assertEquals(100,asset.integer("xfm_mark_cents"));
        v.exchange.put("xfm_day",3);v.run("xfm_oracle_index_daily_effect",v.exchange);
        v.run("xfm_finance_capitalize_default_fund_effect",v.exchange);
        for(Node p:List.copyOf(v.nodes.values()))if(p.type.equals("xfm_futures_position")&&p.integer("xfm_status")==0&&p.integer("xfm_lots")>0)
            v.run("xfm_futures_position_daily_effect",p);
        Node claim=gap.ref("xfm_debt_receipt_1");assertNotNull(claim);assertEquals(3,gap.integer("xfm_status"));
        assertEquals(2000,claim.integer("xfm_original_cents"));assertEquals(fund,claim.integer("xfm_fund_paid_cents"));
        assertEquals(2000-fund,claim.integer("xfm_winner_unpaid_cents"));assertEquals(fund,claim.integer("xfm_fund_recourse_cents"));
        assertEquals(2000,claim.integer("xfm_outstanding_cents"));assertEquals(0,v.exchange.ref("xfm_default_fund_account").integer("xfm_free_cents"));
        assertSame(gap,claim.ref("xfm_source"));assertSame(la.ref("xfm_account"),claim.ref("xfm_debtor_account"));
        assertSame(sa.ref("xfm_account"),claim.ref("xfm_creditor_account"));
        assertEquals(oldStop,primitiveReceipt(stop));assertEquals(oldLiq,primitiveReceipt(liquidate));assertEquals(stock,v.cashStock());assertBalanced(v);
        // The real day chain next services an AI debtor, at most500c/day. Do not confuse the
        // initial fund clearing with the after-finance snapshot or freeze its original unpaid amount.
        la.ai=true;v.run("xfm_debt_auto_service_effect",claim);
        assertEquals(500,claim.integer("xfm_repaid_cents"));assertEquals(1500,claim.integer("xfm_outstanding_cents"));
        assertEquals(1500-fund,claim.integer("xfm_winner_unpaid_cents"));assertEquals(fund,claim.integer("xfm_fund_recourse_cents"));
        assertEquals(0,la.ref("xfm_account").integer("xfm_debt_service_budget_cents"));assertEquals(stock,v.cashStock());
        Map<String,Datum> before=Map.copyOf(claim.vars);Map<String,Datum> position=Map.copyOf(gap.vars);
        long fee=v.exchange.integer("xfm_fee_cents"),claims=v.created("xfm_debt_claim");
        for(Node p:List.of(stop,liquidate,gap))v.run("xfm_futures_position_daily_effect",p);
        v.run("xfm_debt_cover_shortfall_effect",gap);assertEquals(1,gap.integer("xfm_result"));
        v.run("xfm_debt_auto_service_effect",claim);
        assertEquals(before,claim.vars);assertEquals(position,gap.vars);assertEquals(claims,v.created("xfm_debt_claim"));
        assertEquals(fee,v.exchange.integer("xfm_fee_cents"));assertEquals(stock,v.cashStock());assertBalanced(v);
    }

    private static Vm riskVm(int wars) throws IOException {
        Vm v=vm();v.riskWorldBoundaryPorts=true;v.debtBoundaryPorts=true;v.custodian.ai=false;
        for(String input:List.of("scripted_effects/xfm_oracle_indexes.txt","script_values/xfm_oracle_index_values.txt",
            "scripted_effects/xfm_debt_cover.txt","scripted_effects/xfm_debt_fund.txt","scripted_effects/xfm_debt_closure.txt",
            "scripted_effects/xfm_debt_service.txt","scripted_effects/xfm_debt_repayment.txt",
            "scripted_triggers/xfm_debt_triggers.txt","script_values/xfm_debt_values.txt"))
            addDebtDefinitions(v,Clausewitz.parse(Files.readString(SOURCE.resolve("common").resolve(input))));
        var generated=org.xar.ck3.markets.acceptance.ControlledFuturesRiskFixture.render(
            new org.xar.ck3.markets.acceptance.ControlledFuturesRiskFixture.Request(3,"futures-risk-engine-fixture",true));
        for(String path:List.of("common/script_values/xfmr_values.txt","common/scripted_triggers/xfmr_guards.txt",
            "common/scripted_effects/xfmr_world.txt","common/scripted_effects/xfmr_book.txt","common/scripted_effects/xfmr_observe.txt"))
            addDebtDefinitions(v,Clausewitz.parse(new String(generated.get(path),java.nio.charset.StandardCharsets.UTF_8)));
        v.globalVars.put("xfmr_fixture_owner",v.custodian);
        for(int i=0;i<8;i++) {
            Node county=v.node("risk-county-"+i,"county"),holder=v.node("risk-county-holder-"+i,"");holder.atWar=i<wars;
            county.links.put("holder",holder);county.countyControl=BigDecimal.valueOf(43);county.prosperity=BigDecimal.valueOf(17);
            county.put("xfmr_test_control",43);v.exchange.list("xfm_oracle_counties").add(county);
        }
        for(String id:List.of("grain","military","trade")) {
            Node a=v.asset("risk-"+id);a.put("xfm_index_id",id.equals("grain")?1:id.equals("military")?2:3);a.put("xfm_model_quote_divisor",100);
            v.globalVars.put("xfm_"+id+"_index",a);v.globalLists.computeIfAbsent("xfm_index_registry",ignored->new ArrayList<>()).add(a);
        }
        Node fund=v.account("risk-fund",v.custodian,0);fund.put("xfm_system_account",1);v.exchange.put("xfm_default_fund_account",fund);
        v.run("xfm_oracle_index_daily_effect",v.exchange);return v;
    }
    private static Node riskContract(Vm v,String name,Node asset,int expiry) {
        Node c=v.contract(name,asset,0,expiry);c.put("xfm_contract_id",v.nodes.size());c.put("xfm_execution_day",-1);
        c.put("xfm_execution_volume_cents",0);c.put("xfm_execution_lots",0);return c;
    }
    private static Node riskSubmit(Vm v,Node actor,Node contract,int side,int lots,int leverage,int price) {
        actor.put("xfm_selected_coin",contract.ref("xfm_coin"));actor.put("xfm_futures_contract",contract);
        actor.put("xfm_futures_side",side);actor.put("xfm_futures_lots",lots);actor.put("xfm_futures_leverage",leverage);
        actor.put("xfm_futures_limit_cents",price);v.run("xfm_futures_submit_effect",actor);
        assertEquals(1,actor.integer("xfm_futures_result"));Node order=(Node)v.scopes.get("xfm_fut_incoming");assertNotNull(order);return order;
    }
    private static Node riskOpenPair(Vm v,Node asset,Node la,Node sa,String name,int expiry,int lots,int leverage) {
        Node c=riskContract(v,name,asset,expiry),buy=riskSubmit(v,la,c,1,lots,leverage,150),sell=riskSubmit(v,sa,c,2,lots,leverage,150);
        assertEquals(1,c.list("xfm_positions").size());Node p=c.list("xfm_positions").getFirst();assertFillReceipt(p,buy,sell,lots,150);return p;
    }
    private static void riskDonate(Vm v,Node donor,int cents) {
        donor.put("xfm_ui_fund_donation_cents",cents);v.run("xfm_debt_donate_fund_effect",donor);
        assertEquals(1,donor.integer("xfm_result"));assertEquals(cents,donor.integer("xfm_last_fund_donation_cents"));
    }
    /** Execute the actual rendered county-input block; no authored financial quote/mark mutation. */
    private static void riskWorldAction(Vm v,String effect) {
        Block guarded=(Block)v.definition(effect).named("if").getFirst().value();
        Entry action=guarded.named("global_var:xfm_exchange").getFirst();
        v.execute(new Block(List.of(action)),new Frame(v.custodian,null,v.custodian));
    }
    private static Node riskSlice(Vm v,Node source) {
        List<Node> slices=v.nodes.values().stream().filter(n->n.type.equals("xfm_futures_position")&&!n.ended
            &&n.ref("xfm_source_position")==source&&n.integer("xfm_fill_receipt_version")==1).toList();
        assertEquals(1,slices.size());return slices.getFirst();
    }

    private static Vm vm() throws IOException {
        Map<String,Block> program=new LinkedHashMap<>();
        for(String input:INPUTS)for(Entry e:Clausewitz.parse(Files.readString(SOURCE.resolve("common").resolve(input))).entries()) {
            Block b=e.value() instanceof Block block?block:new Block(List.of(new Entry("value","=",e.value())));
            if(program.putIfAbsent(e.key(),b)!=null)throw new IllegalArgumentException("duplicate "+e.key());
        }
        return new Vm(program);
    }
    private static Node series(Vm v,String id) {
        Node asset=v.asset(id+"-asset"), c=v.contract(id,asset,1,0);
        c.put("xfm_contract_id",v.nodes.size());c.put("xfm_execution_day",-1);c.put("xfm_execution_volume_cents",0);c.put("xfm_execution_lots",0);return c;
    }
    private static Node actor(Vm v,String id,long free) {
        Node a=v.node(id,"");a.ai=false;Node wallet=v.account(id+"-wallet",a,free);
        a.put("xfm_account",wallet);a.put("xfm_active_account",wallet);return a;
    }
    private static Node submit(Vm v,Node a,Node c,int side,int lots,int price) {
        a.put("xfm_selected_coin",c.ref("xfm_coin"));a.put("xfm_futures_contract",c);
        a.put("xfm_futures_side",side);a.put("xfm_futures_lots",lots);a.put("xfm_futures_limit_cents",price);a.put("xfm_futures_leverage",1);
        v.run("xfm_futures_submit_effect",a);return (Node)v.scopes.get("xfm_fut_incoming");
    }
    private static List<Node> fullBook(Vm v,Node c,int side,int price) {
        List<Node> out=new ArrayList<>();
        for(int i=0;i<64;i++){Node a=actor(v,c.id+"-"+side+"-actor-"+i,121);Node o=submit(v,a,c,side,1,price);assertNotNull(o);out.add(o);}
        assertEquals(64,c.list("xfm_orders").size());return out;
    }
    private static void assertBalanced(Vm v) {
        for(Node a:v.nodes.values())if(a.type.equals("xfm_finance_account")){
            assertTrue(a.integer("xfm_free_cents")>=0,a.id);assertTrue(a.integer("xfm_reserved_cents")>=0,a.id);
            long claims=a.list("xfm_reservations").stream().filter(r->!r.ended).mapToLong(r->r.integer("xfm_remaining_cents")).sum();
            assertEquals(a.integer("xfm_reserved_cents"),claims,a.id);
            assertEquals(a.integer("xfm_open_orders_count"),a.list("xfm_orders").stream().filter(o->o.integer("xfm_status")<2&&o.integer("xfm_remaining_lots")>0).count(),a.id);
        }
        for(Node c:v.nodes.values())if(c.type.equals("xfm_futures_contract")) {
            assertTrue(c.list("xfm_orders").size()<=128,c.id);assertEquals(c.integer("xfm_open_orders_count"),c.list("xfm_orders").size(),c.id);
        }
    }

    private sealed interface Datum permits NumberDatum, TextDatum, Node { }
    private record NumberDatum(BigDecimal value) implements Datum { }
    private record TextDatum(String text) implements Datum { }
    private static final class Node implements Datum {
        final String id, type;
        final Map<String, Datum> vars = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new HashMap<>();
        final Set<String> traits = new HashSet<>(); final Map<String, Node> links = new HashMap<>();
        BigDecimal gold = BigDecimal.ZERO; Node owner; boolean ai = true, alive = true, adult = true, ended;
        // Explicit engine county boundary for controlled world-input tests, never a financial primitive.
        BigDecimal countyControl=BigDecimal.ZERO,prosperity=BigDecimal.ZERO;boolean atWar;
        Node(String id, String type) { this.id = id; this.type = type; }
        void put(String name, long value) { vars.put(name, new NumberDatum(BigDecimal.valueOf(value))); }
        void put(String name, Node value) { vars.put(name, value); }
        long integer(String name) { Datum d = vars.get(name); return d == null ? 0 : ((NumberDatum) d).value().longValueExact(); }
        Node ref(String name) { return (Node) vars.get(name); }
        List<Node> list(String name) { return lists.computeIfAbsent(name, ignored -> new ArrayList<>()); }
    }
    private record Frame(Node here, Node previous, Node root) { Frame enter(Node node) { return new Frame(node, here, root); } }
    private static final class Vm {
        final Map<String, Block> program; final Map<String, Node> nodes = new LinkedHashMap<>();
        final Map<String, Datum> scopes = new HashMap<>();
        final Set<String> rules = new HashSet<>(); // Engine rule selection; all capacity arithmetic is production AST.
        final Map<String, List<Node>> globalLists = new HashMap<>();
        final Map<String, Datum> globalVars = new HashMap<>();
        final List<Long> debtNewsKinds = new ArrayList<>();
        boolean debtBoundaryPorts; int debtRelationshipCalls; boolean riskWorldBoundaryPorts;
        boolean loadBoundaryPorts; long scriptDate; final List<String> loadLogs=new ArrayList<>(); String loadFirstFailure="";
        final Node exchange, custodian;
        final List<String> trace = new ArrayList<>(); String failType = ""; boolean open = true, randomEnabled = true; int sequence, matchCalls, historyVisits, maxDiscoveryEntries;
        final List<Long> spotExecutionOrderIds = new ArrayList<>(); int maxSpotBookEntries, maxSpotMatchIterations;
        int maxFuturesBookEntries, maxFuturesMatchIterations;
        Vm(Map<String, Block> program) {
            this.program = program; custodian = node("technical-owner", ""); exchange = node("exchange", "xfm_finance_exchange"); exchange.owner = custodian;
            exchange.put("xfm_day", 1); exchange.put("xfm_ai_seeded", 1); exchange.put("xfm_next_account_id", 0); exchange.put("xfm_next_reservation_id", 0);
            exchange.put("xfm_next_futures_contract_id", 0); exchange.put("xfm_next_futures_position_id", 0);
            exchange.put("xfm_active_orders_count", 0); exchange.put("xfm_futures_open_positions_count", 0);
            exchange.put("xfm_futures_archive_count", 0); exchange.put("xfm_futures_opening_budget_v1", 1);
            exchange.put("xfm_futures_opening_budget_day", 1); exchange.put("xfm_futures_opening_allocated_today", 0); // Fresh bootstrap, advanced to fixture day1.
            exchange.put("xfm_order_stories_count", 0); // Actual finance bootstrap initializes the physical spot-story admission counter.
        }
        Node node(String id, String type) {
            Node n = new Node(id, type); if (nodes.putIfAbsent(id, n) != null) throw new IllegalArgumentException("duplicate node " + id); return n;
        }
        Node asset(String id) {
            Node a = node(id, "xfm_oracle_index"); a.put("xfm_mark_cents", 100); a.put("xfm_index_cents", 100);
            a.put("xfm_oracle_quality", 3); a.put("xfm_oracle_day", exchange.integer("xfm_day")); a.put("xfm_max_leverage", 5);
            a.put("xfm_derivatives_reduce_only", 0); return a;
        }
        Node account(String id, Node holder, long free) {
            Node a = node(id, "xfm_finance_account"); a.owner = custodian; a.put("xfm_holder", holder); a.put("xfm_beneficial_owner", holder);
            a.put("xfm_free_cents", free); a.put("xfm_reserved_cents", 0); a.put("xfm_account_frozen", 0);
            a.put("xfm_system_account", 0); a.put("xfm_inheritance_state", 0); a.put("xfm_open_orders_count", 0); a.put("xfm_open_positions_count", 0); return a;
        }
        Node contract(String id, Node asset, long perpetual, long expiry) {
            Node c = node(id, "xfm_futures_contract"); c.owner = custodian; c.put("xfm_coin", asset); c.put("xfm_status", 0);
            c.put("xfm_perpetual", perpetual); c.put("xfm_expiry_day", expiry); c.put("xfm_open_orders_count", 0); return c;
        }
        void order(String id, Node contract, Node account, int side, int price) {
            Node r = node(id + "-reservation", "xfm_finance_reservation"); r.put("xfm_account", account); r.put("xfm_status", 1); r.put("xfm_remaining_cents", 121);
            account.put("xfm_reserved_cents", account.integer("xfm_reserved_cents") + 121);
            Node o = node(id, "xfm_futures_order"); o.put("xfm_contract", contract); o.put("xfm_account", account); o.put("xfm_reservation", r);
            o.put("xfm_status", 0); o.put("xfm_remaining_lots", 1); o.put("xfm_side", side); o.put("xfm_limit_cents", price);
            contract.list("xfm_orders").add(o); contract.put("xfm_open_orders_count", contract.integer("xfm_open_orders_count") + 1);
        }
        int created(String type) { return (int) nodes.values().stream().filter(n -> n.id.startsWith("created-") && n.type.equals(type)).count(); }
        BigDecimal cashStock() {
            BigDecimal sum = BigDecimal.ZERO;
            for (Node n : nodes.values()) {
                sum = sum.add(n.gold.multiply(BigDecimal.valueOf(100)));
                if (n.type.equals("xfm_finance_account")) sum = sum.add(number(n.vars.get("xfm_free_cents"))).add(number(n.vars.get("xfm_reserved_cents")));
            }
            return sum.add(BigDecimal.valueOf(exchange.integer("xfm_fee_cents"))).stripTrailingZeros();
        }
        long integerValue(String value, Node node) { return value(program.get(value), new Frame(node, null, node), BigDecimal.ZERO).longValueExact(); }
        boolean validGui(String name, Node node) { return test(definition(name).block("is_valid"), new Frame(node, null, node)); }
        void runGui(String name, Node node) { if (!validGui(name, node)) throw new IllegalArgumentException("invalid GUI action"); execute(definition(name).block("effect"), new Frame(node, null, node)); }
        void run(String name, Node node) { trace.clear(); execute(definition(name), new Frame(node, null, node)); if (Boolean.getBoolean("xfm.subset.trace") && name.equals("xfm_futures_submit_effect") && node.integer("xfm_futures_result") == 0) System.out.println("REJECT reason=" + node.integer("xfm_futures_reason") + " " + trace); }
        Block definition(String name) { Block b = program.get(name); if (b == null) throw new IllegalArgumentException("unknown definition " + name); return b; }
        Datum resolve(String text, Frame f) {
            try { return new NumberDatum(new BigDecimal(text)); } catch (NumberFormatException ignored) { /* scope/value token */ }
            int dot = text.indexOf('.');
            if (dot > 0) { Datum base = resolve(text.substring(0, dot), f); return base instanceof Node n ? resolve(text.substring(dot + 1), f.enter(n)) : null; }
            if (text.equals("this")) return f.here(); if (text.equals("prev")) return f.previous(); if (text.equals("root")) return f.root();
            if (text.equals("global_var:xfm_exchange")) return exchange;
            if (text.startsWith("global_var:")) return globalVars.get(text.substring(11));
            if (text.equals("story_owner")) return f.here().owner;
            if (text.startsWith("scope:")) return scopes.get(text.substring(6));
            if (text.startsWith("var:")) return f.here().vars.get(text.substring(4));
            if (text.equals("gold")) return new NumberDatum(f.here().gold);
            if (text.equals("current_date")) return new NumberDatum(BigDecimal.valueOf(scriptDate));
            if(riskWorldBoundaryPorts&&text.equals("county_control")&&f.here().type.equals("county"))return new NumberDatum(f.here().countyControl);
            if(riskWorldBoundaryPorts&&text.equals("prosperity_level")&&f.here().type.equals("county"))return new NumberDatum(f.here().prosperity);
            if (f.here().links.containsKey(text)) return f.here().links.get(text);
            if (program.containsKey(text)) return new NumberDatum(value(definition(text), f, BigDecimal.ZERO));
            if (Set.of("xfm_config_player_order_capacity_value", "xfm_config_coin_order_capacity_value", "xfm_config_global_order_capacity_value", "xfm_config_futures_position_capacity_value").contains(text)) return new NumberDatum(BigDecimal.valueOf(4096));
            try { return new NumberDatum(new BigDecimal(text)); } catch (NumberFormatException ignored) { return new TextDatum(text); }
        }
        Datum evaluate(Value v, Frame f) { return v instanceof Block b ? new NumberDatum(value(b, f, BigDecimal.ZERO)) : resolve(atom(v), f); }
        BigDecimal number(Datum d) { if (d == null) return BigDecimal.ZERO; if (d instanceof NumberDatum n) return n.value(); throw new IllegalArgumentException("number required " + d); }
        BigDecimal value(Block b, Frame f, BigDecimal initial) {
            BigDecimal n = initial; boolean chain = false;
            for (Entry e : b.entries()) {
                if (e.key().equals("if") || e.key().equals("else_if")) {
                    Block child = (Block)e.value(); boolean yes = (!e.key().equals("else_if") || !chain) && test(child.block("limit"), f);
                    if (e.key().equals("if")) chain = false;
                    if (yes) { n = value(without(child, "limit"), f, n); chain = true; } continue;
                }
                if (e.key().equals("else")) { if (!chain) n = value((Block)e.value(), f, n); chain = false; continue; }
                if (e.key().equals("floor")) { n = n.setScale(0, RoundingMode.FLOOR); continue; }
                if (e.key().equals("ceiling")) { n = n.setScale(0, RoundingMode.CEILING); continue; }
                BigDecimal x = number(evaluate(e.value(), f));
                n = switch (e.key()) {
                    case "value" -> x; case "add" -> n.add(x); case "subtract" -> n.subtract(x); case "multiply" -> n.multiply(x);
                    case "divide" -> n.divide(x, 18, RoundingMode.HALF_EVEN); case "max" -> n.min(x); case "min" -> n.max(x);
                    default -> throw new IllegalArgumentException("unknown value operation " + e.key());
                };
            }
            return n;
        }
        boolean test(Block b, Frame f) {
            boolean conditionalOpen = false, matched = false;
            for (Entry e : b.entries()) {
                if (e.key().equals("trigger_if")) {
                    Block branch = (Block) e.value(); matched = test(branch.block("limit"), f); conditionalOpen = true;
                    if (matched && !test(without(branch, "limit"), f)) return false;
                    continue;
                }
                if (e.key().equals("trigger_else")) {
                    if (!conditionalOpen) throw new IllegalArgumentException("orphan trigger_else");
                    if (!matched && !test((Block) e.value(), f)) return false;
                    conditionalOpen = false; continue;
                }
                if (e.key().startsWith("trigger_")) throw new IllegalArgumentException("unsupported conditional trigger " + e.key());
                conditionalOpen = false;
                if (!check(e, f)) {
                    if (trace.size() > 40) trace.removeFirst();
                    trace.add(f.here().id + ":" + e.key() + e.operator() + (e.value() instanceof Atom a ? a.token() : "{...}"));
                    return false;
                }
            }
            return true;
        }
        boolean check(Entry e, Frame f) {
            String k = e.key();
            if (k.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, f));
            if (k.equals("NOR")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, f));
            if (k.equals("AND")) return test((Block)e.value(), f);
            if (k.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, f));
            if (k.equals("exists")) return resolve(atom(e.value()), f) != null;
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("has_variable_list")) return f.here().lists.containsKey(atom(e.value()));
            if (k.equals("has_global_variable")) return globalVars.containsKey(atom(e.value()));
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if(riskWorldBoundaryPorts&&k.equals("is_at_war"))return f.here().atWar==atom(e.value()).equals("yes");
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("has_trait")) return f.here().traits.contains(atom(e.value()));
            if (k.equals("has_game_rule")) return rules.contains(atom(e.value())); // Engine rule selection only.
            if (k.equals("always")) return atom(e.value()).equals("yes");
            if (k.equals("xfm_config_futures_open_trigger")) return open;
            if (k.equals("xfm_config_spot_open_trigger")) return open;
            if (k.equals("any_in_list")) {
                Block b = (Block)e.value(); for (Node n : list(f.here(), atom(field(b, "variable")))) if (test(without(b, "variable"), f.enter(n))) return true; return false;
            }
            if (k.endsWith("_trigger") && program.containsKey(k)) return test(e.value() instanceof Block args ? substitute(definition(k), args) : definition(k), f);
            if (e.value() instanceof Block child && !(resolve(k, f) instanceof NumberDatum)) {
                Datum scope = resolve(k, f); return scope instanceof Node n && test(child, f.enter(n));
            }
            Datum left = resolve(k, f), right = evaluate(e.value(), f);
            // An unresolved saved-scope comparison is not true (including !=). exists must guard it.
            if ((left == null || right == null) && e.value() instanceof Atom operand
                    && (k.startsWith("scope:") || operand.token().startsWith("scope:"))) return false;
            if (left instanceof NumberDatum x && right instanceof NumberDatum y) {
                int cmp = x.value().compareTo(y.value()); return switch (e.operator()) { case "=" -> cmp == 0; case "!=" -> cmp != 0; case ">" -> cmp > 0; case "<" -> cmp < 0; case ">=" -> cmp >= 0; case "<=" -> cmp <= 0; default -> throw new IllegalArgumentException(e.operator()); };
            }
            if (e.operator().equals("=")) return java.util.Objects.equals(left, right);
            if (e.operator().equals("!=")) return !java.util.Objects.equals(left, right);
            return false;
        }
        List<Node> list(Node owner, String name) {
            List<Node> result = List.copyOf(owner.list(name));
            if (name.equals("xfm_futures_discovery_contracts")) { maxDiscoveryEntries = Math.max(maxDiscoveryEntries, result.size()); if (result.size() > 8) throw new IllegalArgumentException("discovery capacity exceeded"); }
            if (name.equals("xfm_futures_contracts")) historyVisits += result.size();
            return result;
        }
        void execute(Block b, Frame f) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                String k = e.key();
                if (k.equals("if") || k.equals("else_if")) {
                    Block child = (Block)e.value(); boolean yes = (!k.equals("else_if") || !chain) && test(child.block("limit"), f);
                    if (k.equals("if")) chain = false; if (yes) { execute(without(child, "limit"), f); chain = true; } continue;
                }
                if (k.equals("else")) { if (!chain) execute((Block)e.value(), f); chain = false; continue; }
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if(riskWorldBoundaryPorts&&Set.of("change_county_control","change_prosperity_level").contains(k)) {
                    if(!f.here().type.equals("county"))throw new IllegalArgumentException("county scope required");
                    BigDecimal delta=number(evaluate(e.value(),f));
                    BigDecimal old=k.equals("change_county_control")?f.here().countyControl:f.here().prosperity;
                    BigDecimal next=old.add(delta);
                    // This narrow port certifies only in-range stock county inputs used by this fixture.
                    if(next.signum()<0||next.compareTo(BigDecimal.valueOf(100))>0)throw new IllegalArgumentException("unsupported out-of-range county input");
                    if(k.equals("change_county_control"))f.here().countyControl=next;else f.here().prosperity=next;
                    continue;
                }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("remove_variable")) { f.here().vars.remove(atom(e.value())); continue; }
                if (k.equals("clear_variable_list")) { f.here().list(atom(e.value())).clear(); continue; }
                if (k.equals("while")) {
                    Block a = (Block)e.value(); int bound = 0;
                    if (!a.named("count").isEmpty()) {
                        int count = number(evaluate(field(a, "count"), f)).intValueExact();
                        if (f.here().type.equals("xfm_spot_order")) { if (count > 64) throw new IllegalArgumentException("spot work cap exceeded"); maxSpotMatchIterations = Math.max(maxSpotMatchIterations, count); }
                        for (int i = 0; i < count; i++) execute(without(a, "count"), f);
                        continue;
                    }
                    while (test(a.block("limit"), f)) { if (++bound > 64) throw new IllegalArgumentException("bounded production loop exceeded 64"); if (f.here().type.equals("xfm_futures_order")) { if (bound > 32) throw new IllegalArgumentException("original futures match work exceeded 32"); maxFuturesMatchIterations = Math.max(maxFuturesMatchIterations, bound); } execute(without(a, "limit"), f); }
                    continue;
                }
                if (k.equals("ordered_in_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> ordered = new ArrayList<>();
                    for (Node n : list(f.here(), name)) if (test(a.block("limit"), f.enter(n))) ordered.add(n);
                    ordered.sort((left, right) -> number(evaluate(field(a, "order_by"), f.enter(right))).compareTo(number(evaluate(field(a, "order_by"), f.enter(left)))));
                    int start = a.named("position").isEmpty() ? 0 : number(evaluate(field(a, "position"), f)).intValueExact();
                    int count = a.named("max").isEmpty() ? 1 : number(evaluate(field(a, "max"), f)).intValueExact();
                    Block effect = without(without(without(without(without(without(a, "variable"), "limit"), "order_by"), "max"), "position"), "check_range_bounds");
                    for (int i = start; i < Math.min(ordered.size(), start + count); i++) execute(effect, f.enter(ordered.get(i)));
                    continue;
                }
                if (k.equals("set_global_variable")) {
                    Block a=(Block)e.value();globalVars.put(atom(field(a,"name")),evaluate(field(a,"value"),f));continue;
                }
                if (k.equals("set_variable") || k.equals("change_variable")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name"));
                    if (k.equals("set_variable")) f.here().vars.put(name, evaluate(field(a, "value"), f));
                    else {
                        boolean add = !a.named("add").isEmpty(); BigDecimal amount = number(evaluate(field(a, add ? "add" : "subtract"), f));
                        BigDecimal old = number(f.here().vars.get(name)); f.here().vars.put(name, new NumberDatum(add ? old.add(amount) : old.subtract(amount)));
                    }
                    continue;
                }
                if (k.equals("save_scope_value_as")) { Block a = (Block)e.value(); scopes.put(atom(field(a, "name")), evaluate(field(a, "value"), f)); continue; }
                if (k.equals("remove_short_term_gold")) { f.here().gold = f.here().gold.subtract(number(evaluate(e.value(), f))).setScale(2); continue; }
                if (k.equals("add_gold")) { f.here().gold = f.here().gold.add(number(evaluate(e.value(), f))).setScale(2); continue; }
                // Engine object-creation boundary only; financial primitives below execute their actual bodies.
                if (loadBoundaryPorts && k.equals("create_character")) {
                    Block a=(Block)e.value();
                    if(!failType.equals("character")){
                        Node created=node("created-character-"+(++sequence),"");
                        created.links.put("culture",(Node)evaluate(field(a,"culture"),f));
                        created.links.put("faith",(Node)evaluate(field(a,"faith"),f));
                        created.links.put("capital_province",(Node)evaluate(field(a,"location"),f));
                        scopes.put(atom(field(a,"save_scope_as")),created);
                    }
                    continue;
                }
                if(loadBoundaryPorts && k.equals("debug_log")){
                    String message=atom(e.value());loadLogs.add(message);
                    if(message.contains("TEST FAIL")&&loadFirstFailure.isEmpty())loadFirstFailure=loadDiagnostic(this,f.root());
                    continue;
                }
                if (k.equals("create_story")) {
                    Block a = (Block)e.value(); String type = atom(field(a, "type"));
                    if (!type.equals(failType)) { Node created = node("created-" + ++sequence, type); created.owner = f.here(); scopes.put(atom(field(a, "save_scope_as")), created); }
                    continue;
                }
                if (k.equals("end_story")) { f.here().ended = true; continue; }
                if (k.equals("add_to_variable_list") || k.equals("remove_list_variable") || k.equals("add_to_global_variable_list") || k.equals("remove_list_global_variable")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name")); Node target = (Node)evaluate(field(a, "target"), f);
                    List<Node> list = k.equals("add_to_global_variable_list") || k.equals("remove_list_global_variable") ? globalLists.computeIfAbsent(name, ignored -> new ArrayList<>()) : f.here().list(name);
                    if (k.equals("remove_list_variable") || k.equals("remove_list_global_variable")) list.remove(target); else list.add(target);
                    if (name.equals("xfm_spot_orders")) { maxSpotBookEntries = Math.max(maxSpotBookEntries, list.size()); if (list.size() > 64) throw new IllegalArgumentException("65th resting order"); }
                    if (name.equals("xfm_orders") && f.here().type.equals("xfm_futures_contract")) { maxFuturesBookEntries = Math.max(maxFuturesBookEntries, list.size()); if (list.size() > 128) throw new IllegalArgumentException("futures book exceeds every supported preset"); }
                    continue;
                }
                if (k.equals("every_in_list") || k.equals("every_in_global_list") || k.equals("random_in_list") || k.equals("random_in_global_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> list = k.equals("random_in_global_list") || k.equals("every_in_global_list") ? List.copyOf(globalLists.getOrDefault(name, List.of())) : list(f.here(), name);
                    for (Node n : list) if (test(a.block("limit"), f.enter(n))) {
                        execute(without(without(a, "variable"), "limit"), f.enter(n)); if (!k.equals("every_in_list") && !k.equals("every_in_global_list")) break;
                    }
                    continue;
                }
                if (k.equals("random")) { Block a = (Block)e.value(); if (randomEnabled && number(evaluate(field(a, "chance"), f)).signum() > 0) execute(without(a, "chance"), f); continue; }
                // Explicit observation/lifecycle boundaries for the controlled-debt tests only.
                // These ports grant no dispatch, relationship-amount, asset-review or Game credit.
                if (debtBoundaryPorts && k.equals("xfm_news_record_effect")) { debtNewsKinds.add(f.here().integer("xfm_news_kind")); continue; }
                if (debtBoundaryPorts && k.equals("xfm_debt_account_review_effect")) continue;
                if (debtBoundaryPorts && Set.of("xfm_debt_aid_relation_effect","xfm_debt_restructure_relation_effect").contains(k)) { debtRelationshipCalls++; continue; }
                if (debtBoundaryPorts && k.equals("debug_log")) continue;
                if (k.equals("xfm_oracle_record_trade_effect")) continue; // independent oracle sampler, outside cash/coin settlement subset
                if (k.equals("xfm_spot_record_trade_effect")) spotExecutionOrderIds.add(((Node)scopes.get("xfm_spot_resting")).integer("xfm_order_id"));
                if (e.value() instanceof Block child) { if (program.containsKey(k)) { execute(substitute(definition(k), child), f); continue; } Datum scope = resolve(k, f); if (!(scope instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(child, f.enter(n)); continue; }
                execute(definition(k), f);
            }
        }
    }
    private static String atom(Value value) { if (!(value instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Block substitute(Block block, Block arguments) {
        Map<String, String> replacements = new LinkedHashMap<>();
        for (Entry arg : arguments.entries()) replacements.put("$" + arg.key() + "$", atom(arg.value()));
        return substitute(block, replacements);
    }
    private static Block substitute(Block block, Map<String, String> replacements) {
        return new Block(block.entries().stream().map(entry -> new Entry(replace(entry.key(), replacements), entry.operator(),
                entry.value() instanceof Block child ? substitute(child, replacements)
                        : new Atom(replace(atom(entry.value()), replacements)))).toList());
    }
    private static String replace(String text, Map<String, String> replacements) {
        String result = text; for (var e : replacements.entrySet()) result = result.replace(e.getKey(), e.getValue()); return result;
    }
    private static Value field(Block block, String name) { List<Entry> found = block.named(name); if (found.size() != 1) throw new IllegalArgumentException("one field required " + name); return found.getFirst().value(); }
    private static Block without(Block block, String name) { return new Block(block.entries().stream().filter(e -> !e.key().equals(name)).toList()); }
}
