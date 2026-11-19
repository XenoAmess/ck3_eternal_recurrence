package org.xar.ck3.markets.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Executes the actual capacity/retirement scripts plus the existing real inventory burn.
 * Account selection and zero-wallet creation/history initialization are explicit nonmonetary ports.
 * This bounded script subset is software evidence, not CK3 timing, save/reload, or financial certification.
 */
final class CoinResidentCapacityScriptTest {
    private static final Path SOURCE=Path.of(System.getProperty("xfm.source",".."));
    private static final List<String> INPUTS=List.of(
            "scripted_effects/xfm_registry_capacity.txt","scripted_effects/xfm_registry_history.txt",
            "scripted_effects/xfm_issuer_retirement.txt","scripted_effects/xfm_issuer_closure.txt",
            "scripted_effects/xfm_listing_transitions.txt","scripted_effects/xfm_issuer_daily.txt",
            "scripted_effects/xfm_issuer_subscriptions.txt","scripted_effects/xfm_finance_reserve.txt",
            "scripted_effects/xfm_finance_init.txt","scripted_effects/xfm_finance_assets.txt",
            "scripted_triggers/xfm_registry_capacity_triggers.txt","scripted_triggers/xfm_issuer_triggers.txt",
            "scripted_triggers/xfm_finance_triggers.txt","script_values/xfm_registry_capacity_values.txt",
            "script_values/xfm_finance_values.txt","script_values/xfm_finance_asset_values.txt");

    @Test void legacyBaselineIsConstantWorkAndHistoricalCounterNeverBecomesAnAdmissionLimit()throws IOException{
        Vm v=vm();v.exchange.num("xfm_registered_coin_count",20000).num("xfm_next_coin_id",20000);
        v.run("xfm_registry_capacity_ensure_effect",v.exchange);
        assertEquals(20000,v.exchange.n("xfm_resident_coin_count"));assertEquals(0,v.globalVisits);
        Node clean=v.coin(20000,7);v.hot(clean);v.queueAndFlush(clean);
        assertEquals(19999,v.exchange.n("xfm_resident_coin_count"));assertEquals(20000,v.exchange.n("xfm_registered_coin_count"));assertEquals(20000,v.exchange.n("xfm_next_coin_id"));
        v.exchange.num("xfm_resident_coin_count",16383);v.run("xfm_finance_create_coin_effect",v.actor);
        Node next=v.actor.ref("xfm_result_coin");assertNotNull(next);assertEquals(20001,next.n("xfm_coin_id"));
        assertEquals(20001,v.exchange.n("xfm_registered_coin_count"));assertEquals(16384,v.exchange.n("xfm_resident_coin_count"));
        v.run("xfm_finance_create_coin_effect",v.actor);assertEquals(0,v.actor.n("xfm_result"));assertEquals(20001,v.exchange.n("xfm_next_coin_id"));
    }

    @Test void removalOccursAfterTraversalOnceAndPreservesIdentityReferencesAndHistoricalOracleFields()throws IOException{
        Vm v=vm();Node c=v.coin(4,7);v.hot(c);v.actor.ref("xfm_personal_coin",c);Node receipt=v.node("receipt").ref("xfm_coin",c);c.list("xfm_receipts").add(receipt);
        c.num("xfm_oracle_quality",1).num("xfm_max_leverage",10).num("xfm_oracle_day",12).num("xfm_mark_cents",77);
        v.exchange.num("xfm_registered_coin_count",1);v.run("xfm_registry_capacity_ensure_effect",v.exchange);
        v.exchange.num("xfm_registry_iteration_open",1);v.run("xfm_registry_queue_retire_effect",c);v.run("xfm_registry_flush_retire_effect",v.exchange);
        assertTrue(v.global("xfm_coin_registry").contains(c));assertEquals(1,v.exchange.n("xfm_resident_coin_count"));
        v.exchange.num("xfm_registry_iteration_open",0);v.run("xfm_registry_flush_retire_effect",v.exchange);v.queueAndFlush(c);v.run("xfm_registry_flush_retire_effect",v.exchange);
        assertFalse(v.global("xfm_coin_registry").contains(c));assertEquals(List.of(c),v.global("xfm_archived_coin_registry"));
        assertEquals(0,v.exchange.n("xfm_resident_coin_count"));assertEquals(1,v.exchange.n("xfm_registered_coin_count"));assertSame(c,v.actor.ref("xfm_personal_coin"));assertSame(c,receipt.ref("xfm_coin"));
        assertEquals("xfm_finance_coin",c.type);assertEquals(4,c.n("xfm_coin_id"));assertEquals(0,c.n("xfm_oracle_quality"));assertEquals(0,c.n("xfm_max_leverage"));assertEquals(12,c.n("xfm_oracle_day"));assertEquals(77,c.n("xfm_mark_cents"));assertEquals(0,v.ended);
    }

    @Test void queueRevalidatesRightsAppearingAfterPreparationBeforeAnySlotIsReleased()throws IOException{
        Vm v=vm();Node c=v.coin(1,7);v.hot(c);v.exchange.num("xfm_registered_coin_count",1);v.run("xfm_registry_capacity_ensure_effect",v.exchange);
        v.run("xfm_registry_queue_retire_effect",c);c.num("xfm_unpaid_debt_cents",1);v.run("xfm_registry_flush_retire_effect",v.exchange);
        assertTrue(v.global("xfm_coin_registry").contains(c));assertTrue(v.global("xfm_archived_coin_registry").isEmpty());assertEquals(1,v.exchange.n("xfm_resident_coin_count"));assertFalse(c.vars.containsKey("xfm_capacity_slot_released"));
    }

    @Test void actualExistingIssuerTraversalMigratesOnly64ThenContinuesOnTheNextRealDay()throws IOException{
        Vm v=vm();for(int i=1;i<=130;i++)v.hot(v.coin(i,7));v.exchange.num("xfm_registered_coin_count",130);
        v.run("xfm_coin_daily_effect",v.exchange);
        assertEquals(64,v.global("xfm_archived_coin_registry").size());assertEquals(66,v.global("xfm_coin_registry").size());assertEquals(66,v.exchange.n("xfm_resident_coin_count"));assertEquals(130,v.exchange.n("xfm_registered_coin_count"));assertEquals(130,v.globalVisits);
        v.run("xfm_coin_daily_effect",v.exchange);assertEquals(64,v.global("xfm_archived_coin_registry").size(),"same-day duplicate cannot reset the migration budget");
        Collections.reverse(v.global("xfm_coin_registry"));v.exchange.num("xfm_day",2);v.run("xfm_coin_daily_effect",v.exchange);assertEquals(128,v.global("xfm_archived_coin_registry").size());assertEquals(2,v.exchange.n("xfm_resident_coin_count"));
        v.exchange.num("xfm_day",3);v.run("xfm_coin_daily_effect",v.exchange);assertEquals(130,v.global("xfm_archived_coin_registry").size());assertEquals(0,v.exchange.n("xfm_resident_coin_count"));assertEquals(0,v.ended);
        long completedRound=v.exchange.n("xfm_registry_review_round");v.run("xfm_coin_daily_effect",v.exchange);assertEquals(completedRound,v.exchange.n("xfm_registry_review_round"),"an empty same-day reentry cannot advance a second round");
    }

    @Test void protected1920PrefixCannotStarveCleanTailAtDay31OrRestartBeforeTheRoundCompletes()throws IOException{
        Vm v=vm();for(int id=1;id<=1920;id++)v.failedOffer(id).num("xfm_unpaid_debt_cents",1);
        Node clean=v.failedOffer(1921),first=v.global("xfm_coin_registry").getFirst();v.exchange.num("xfm_registered_coin_count",1921);
        for(int day=1;day<=30;day++){
            v.exchange.num("xfm_day",day);v.run("xfm_coin_daily_effect",v.exchange);
            assertEquals(1,v.exchange.n("xfm_registry_review_round"),"round cannot restart before reaching the tail on day "+day);
            assertEquals(1,first.n("xfm_registry_coin_review_round"));assertEquals(15000,clean.n("xfm_supply_units"));assertEquals(6,clean.n("xfm_listing_state"));
            if(day==30){v.run("xfm_coin_daily_effect",v.exchange);assertEquals(0,v.exchange.n("xfm_registry_review_budget"));assertEquals(1,v.exchange.n("xfm_registry_review_round"));}
        }
        v.exchange.num("xfm_day",31);v.run("xfm_coin_daily_effect",v.exchange);
        assertEquals(7,clean.n("xfm_listing_state"));assertEquals(0,clean.n("xfm_supply_units"));assertEquals(List.of(clean),v.global("xfm_archived_coin_registry"));
        assertEquals(1920,v.exchange.n("xfm_resident_coin_count"));assertEquals(1921,v.exchange.n("xfm_registered_coin_count"));assertEquals(2,v.exchange.n("xfm_registry_review_round"));
        assertEquals(1,first.n("xfm_registry_coin_review_round"),"the protected prefix was not re-reviewed before the tail");assertEquals(1,first.n("xfm_unpaid_debt_cents"));assertEquals(15000,first.n("xfm_supply_units"));assertEquals(0,v.cashStock());
    }

    @Test void legacyArchivedRedemptionRightReturnsToResidualServiceAndDoesNotStarveLaterCleanObjects()throws IOException{
        Vm v=vm();Node bad=v.coin(1,7);bad.ref("xfm_redemption_account",v.account().num("xfm_free_cents",10));v.hot(bad);for(int i=2;i<=66;i++)v.hot(v.coin(i,7));v.exchange.num("xfm_registered_coin_count",66);
        v.run("xfm_coin_daily_effect",v.exchange);assertEquals(6,bad.n("xfm_listing_state"));assertEquals(10,bad.ref("xfm_redemption_account").n("xfm_free_cents"));assertTrue(v.global("xfm_coin_registry").contains(bad));
        v.exchange.num("xfm_day",2);v.run("xfm_coin_daily_effect",v.exchange);assertEquals(65,v.global("xfm_archived_coin_registry").size());assertEquals(1,v.exchange.n("xfm_resident_coin_count"));assertEquals(0,v.ended);
    }

    @Test void completedRoundCannotReviewSingleProtectedCandidateAgainOnTheSameDayButNextDayCan()throws IOException{
        Vm v=vm();Node c=v.failedOffer().num("xfm_unpaid_debt_cents",1);v.exchange.num("xfm_registered_coin_count",1);
        v.run("xfm_coin_daily_effect",v.exchange);
        assertEquals(1,c.n("xfm_registry_coin_review_round"));assertEquals(2,v.exchange.n("xfm_registry_review_round"));assertEquals(63,v.exchange.n("xfm_registry_review_budget"));assertEquals(1,v.exchange.n("xfm_registry_round_completed_day"));
        v.run("xfm_coin_daily_effect",v.exchange);
        assertEquals(1,c.n("xfm_registry_coin_review_round"));assertEquals(2,v.exchange.n("xfm_registry_review_round"));assertEquals(63,v.exchange.n("xfm_registry_review_budget"));
        v.exchange.num("xfm_day",2);v.run("xfm_coin_daily_effect",v.exchange);
        assertEquals(2,c.n("xfm_registry_coin_review_round"));assertEquals(3,v.exchange.n("xfm_registry_review_round"));assertEquals(63,v.exchange.n("xfm_registry_review_budget"));assertEquals(2,v.exchange.n("xfm_registry_round_completed_day"));
        assertEquals(15000,c.n("xfm_supply_units"));assertEquals(1,c.n("xfm_unpaid_debt_cents"));assertEquals(1,v.exchange.n("xfm_resident_coin_count"));assertTrue(v.global("xfm_archived_coin_registry").isEmpty());
    }

    @Test void allIndependentResidualRightsPreventRetirementWithoutEditingMoneyOrSupply()throws IOException{
        for(String kind:List.of("supply","holder","reserved-units","issuer-cash","founder-cash","maker-cash","frozen","inheritance","claim","claim-counter","debt","promise","arrears","settlement","spot","futures-position","futures-order","pending-journal","subscription","maintenance","bond","maker-reserve","redemption-cash","redemption-window")){
            Vm v=vm();Node c=v.coin(1,7);v.hot(c);v.exchange.num("xfm_registered_coin_count",1);v.run("xfm_registry_capacity_ensure_effect",v.exchange);
            switch(kind){
                case "supply"->c.num("xfm_supply_units",1);
                case "holder"->c.list("xfm_holders").add(v.node("xfm_finance_position").num("xfm_quantity_units",1));
                case "reserved-units"->c.list("xfm_holders").add(v.node("xfm_finance_position").num("xfm_reserved_units",1));
                case "issuer-cash"->c.ref("xfm_issuer_account").num("xfm_free_cents",1);
                case "founder-cash"->c.ref("xfm_founder_account").num("xfm_reserved_cents",1);
                case "maker-cash"->c.ref("xfm_market_maker_account",v.account().num("xfm_free_cents",1));
                case "frozen"->c.ref("xfm_issuer_account").num("xfm_account_frozen",1);
                case "inheritance"->c.ref("xfm_founder_account").num("xfm_inheritance_state",2);
                case "claim"->c.list("xfm_claims").add(v.node("claim").num("xfm_outstanding_cents",1));
                case "claim-counter"->c.num("xfm_unresolved_claim_count",1);
                case "debt"->c.num("xfm_unpaid_debt_cents",1);
                case "promise"->c.num("xfm_promises_due_cents",1);
                case "arrears"->c.num("xfm_maintenance_arrears_cents",1);
                case "settlement"->c.num("xfm_settlement_price_pending",1);
                case "spot"->c.list("xfm_spot_orders").add(v.node("order").num("xfm_status",1));
                case "futures-position"->{Node contract=v.node("contract");c.list("xfm_futures_contracts").add(contract);contract.list("xfm_positions").add(v.node("position").num("xfm_status",0).num("xfm_lots",1));}
                case "futures-order"->{Node contract=v.node("contract");c.list("xfm_futures_contracts").add(contract);contract.list("xfm_orders").add(v.node("order").num("xfm_status",1).num("xfm_remaining_lots",1));}
                case "pending-journal"->{Node contract=v.node("contract");c.list("xfm_futures_contracts").add(contract);contract.list("xfm_positions").add(v.node("position").num("xfm_status",2).num("xfm_pending_payment",1));}
                case "subscription"->c.list("xfm_subscriptions").add(v.node("xfm_finance_reservation").num("xfm_subscription_state",1).num("xfm_remaining_cents",0));
                case "maintenance"->c.ref("xfm_maintenance_reservation",v.node("xfm_finance_reservation").num("xfm_remaining_cents",1));
                case "bond"->c.ref("xfm_bond_reservation",v.node("xfm_finance_reservation").num("xfm_remaining_cents",1));
                case "maker-reserve"->c.ref("xfm_maker_reservation",v.node("xfm_finance_reservation").num("xfm_remaining_cents",1));
                case "redemption-cash"->c.ref("xfm_redemption_account",v.account().num("xfm_free_cents",1));
                case "redemption-window"->c.ref("xfm_redemption_window",v.node("window").num("xfm_remaining_cents",0).num("xfm_status",1).num("xfm_expiry_day",90));
                default->throw new AssertionError(kind);
            }
            Map<Node,Map<String,Datum>> before=v.copyVars();v.queueAndFlush(c);
            assertEquals(before,v.copyVars(),kind);assertEquals(1,v.exchange.n("xfm_resident_coin_count"),kind);assertTrue(v.global("xfm_archived_coin_registry").isEmpty(),kind);
        }
    }

    @Test void actuallyRefundedFailedAiOfferUsesExistingControllerAndBurnsRealInventoryBeforeSlotRelease()throws IOException{
        Vm v=vm();Node c=v.failedOffer();Node other=v.coin(2,1);v.actor.ref("xfm_selected_coin",other);v.actor.ref("xfm_personal_coin",c);v.exchange.num("xfm_registered_coin_count",1);
        v.run("xfm_coin_daily_effect",v.exchange);
        assertEquals(0,c.n("xfm_supply_units"));for(Node p:c.list("xfm_holders"))assertEquals(0,p.n("xfm_quantity_units"));
        assertEquals(0,c.n("xfm_founder_locked_units"));assertEquals(7,c.n("xfm_listing_state"));assertEquals(0,v.exchange.n("xfm_resident_coin_count"));assertEquals(1,v.exchange.n("xfm_registered_coin_count"));
        assertSame(other,v.actor.ref("xfm_selected_coin"));assertSame(c,v.actor.ref("xfm_personal_coin"));assertEquals(0,v.ended);assertEquals(0,v.cashStock());
        assertEquals(List.of(c),v.global("xfm_archived_coin_registry"));
    }

    @Test void realRefundReleasesOnlyRealReservedCashThenAllowsLaterAiRetirement()throws IOException{
        Vm v=vm();Node c=v.failedOffer().num("xfm_listing_state",0).num("xfm_offer_counted",1),sub=c.list("xfm_subscriptions").getFirst();
        sub.num("xfm_subscription_state",0).num("xfm_status",1).num("xfm_remaining_cents",1600).ref("xfm_account",v.wallet);
        v.wallet.num("xfm_reserved_cents",1600);v.actor.ref("xfm_pending_offer",c);v.exchange.num("xfm_registered_coin_count",1).num("xfm_pending_coin_count",1);
        long before=v.cashStock();v.run("xfm_issuer_refund_effect",c);
        assertEquals(3,sub.n("xfm_subscription_state"));assertEquals(0,sub.n("xfm_remaining_cents"));assertEquals(1600,v.wallet.n("xfm_free_cents"));assertEquals(0,v.wallet.n("xfm_reserved_cents"));assertEquals(0,v.exchange.n("xfm_pending_coin_count"));
        assertEquals(6,c.n("xfm_listing_state"));assertFalse(v.actor.vars.containsKey("xfm_pending_offer"));assertEquals(15000,c.n("xfm_supply_units"));
        v.run("xfm_coin_daily_effect",v.exchange);assertEquals(7,c.n("xfm_listing_state"));assertEquals(0,c.n("xfm_supply_units"));assertEquals(0,v.exchange.n("xfm_resident_coin_count"));assertEquals(before,v.cashStock());
    }

    @Test void actualReleaseFailureKeepsSubscriptionPendingAndNeverBurnsOrReleasesCapacity()throws IOException{
        Vm v=vm();Node c=v.failedOffer().num("xfm_listing_state",0).num("xfm_offer_counted",1),sub=c.list("xfm_subscriptions").getFirst();
        sub.num("xfm_subscription_state",0).num("xfm_status",1).num("xfm_remaining_cents",1600).ref("xfm_account",v.wallet);
        v.exchange.num("xfm_registered_coin_count",1).num("xfm_pending_coin_count",1);v.actor.ref("xfm_pending_offer",c);
        v.run("xfm_issuer_refund_effect",c);assertEquals(0,sub.n("xfm_result"));assertEquals(0,sub.n("xfm_subscription_state"));assertEquals(1600,sub.n("xfm_remaining_cents"));assertEquals(0,c.n("xfm_listing_state"));
        v.run("xfm_coin_daily_effect",v.exchange);assertEquals(15000,c.n("xfm_supply_units"));assertEquals(1,v.exchange.n("xfm_resident_coin_count"));assertEquals(1,v.exchange.n("xfm_pending_coin_count"));assertEquals(0,v.cashStock());assertSame(c,v.actor.ref("xfm_pending_offer"));assertTrue(v.global("xfm_archived_coin_registry").isEmpty());
    }

    @Test void failedRefundExternalUnitsPlayerControlAndClosingNeverAuthorizeAutomaticConfiscation()throws IOException{
        for(String kind:List.of("unrefunded","failed-release","outside-holder","reserved-founder","player","closing","listed-before","frozen","wrong-political-head")){
            Vm v=vm();Node c=v.failedOffer();v.exchange.num("xfm_registered_coin_count",1);
            switch(kind){
                case "unrefunded"->c.list("xfm_subscriptions").getFirst().num("xfm_subscription_state",0).num("xfm_remaining_cents",1);
                case "failed-release"->c.list("xfm_subscriptions").getFirst().num("xfm_subscription_state",0).num("xfm_remaining_cents",0);
                case "outside-holder"->{Node p=v.node("xfm_finance_position").ref("xfm_account",v.account()).num("xfm_quantity_units",1).num("xfm_reserved_units",0);c.list("xfm_holders").add(p);c.num("xfm_supply_units",15001);}
                case "reserved-founder"->c.list("xfm_holders").getLast().num("xfm_reserved_units",1);
                case "player"->v.actor.ai=false;
                case "closing"->c.num("xfm_offer_closing_started",1);
                case "listed-before"->c.num("xfm_listed_day",0);
                case "frozen"->c.ref("xfm_issuer_account").num("xfm_account_frozen",1);
                case "wrong-political-head"->c.num("xfm_entity_type",4).ref("xfm_bound_entity",v.node("title").ref("holder",v.node("character")));
                default->throw new AssertionError(kind);
            }
            long cash=v.cashStock();v.run("xfm_coin_daily_effect",v.exchange);
            assertTrue(c.n("xfm_supply_units")>=15000,kind);assertEquals(6,c.n("xfm_listing_state"),kind);assertEquals(1,v.exchange.n("xfm_resident_coin_count"),kind);assertEquals(cash,v.cashStock(),kind);assertTrue(v.global("xfm_archived_coin_registry").isEmpty(),kind);
        }
    }

    @Test void currentHouseDynastyTitleAndFaithHeadsRetireOnlyTheirOwnFullyRefundedProjects()throws IOException{
        for(int type:List.of(2,3,4,5)){
            Vm v=vm();Node c=v.failedOffer().num("xfm_entity_type",type);String scope=switch(type){case 2->"house_head";case 3->"dynast";case 4->"holder";case 5->"religious_head";default->throw new AssertionError();};
            c.ref("xfm_bound_entity",v.node("entity").ref(scope,v.actor));v.exchange.num("xfm_registered_coin_count",1);
            v.run("xfm_coin_daily_effect",v.exchange);assertEquals(7,c.n("xfm_listing_state"),"entity type "+type);assertEquals(0,c.n("xfm_supply_units"));assertEquals(0,v.exchange.n("xfm_resident_coin_count"));
        }
    }

    @Test void zeroResidualSuccessfullyListedCoinCanRetireDespiteItsHistoricalClosingMarker()throws IOException{
        Vm v=vm();Node c=v.coin(1,6).num("xfm_offer_closing_started",1).num("xfm_listed_day",0);v.hot(c);v.exchange.num("xfm_registered_coin_count",1);v.run("xfm_registry_capacity_ensure_effect",v.exchange);
        v.run("xfm_listing_archive_effect",c);assertEquals(7,c.n("xfm_listing_state"));assertEquals(0,v.exchange.n("xfm_resident_coin_count"));assertEquals(1,c.n("xfm_offer_closing_started"));assertEquals(0,v.ended);
    }

    @Test void explicitHistoricalIdLookupIsReachableButDefaultMarketRefreshDoesNotWalkColdHistory()throws IOException{
        Vm v=vm();Node c=v.coin(77,7).num("xfm_capacity_slot_released",1);v.global("xfm_archived_coin_registry").add(c);v.actor.ai=false;v.actor.num("xfm_ui_id_filter",0).num("xfm_ui_offset",0).num("xfm_ui_holdings_only",0).num("xfm_ui_type_filter",0);
        v.run("xfm_registry_lookup_history_effect",v.actor);assertEquals(0,v.globalVisits);assertTrue(v.actor.list("xfm_ui_coin_page").isEmpty());
        v.actor.num("xfm_ui_id_filter",77);v.run("xfm_registry_lookup_history_effect",v.actor);assertEquals(List.of(c),v.actor.list("xfm_ui_coin_page"));
        v.run("xfm_registry_lookup_history_effect",v.actor);assertEquals(1,v.actor.list("xfm_ui_coin_page").size());assertEquals(0,c.n("xfm_trading_open"));assertEquals(7,c.n("xfm_listing_state"));
        String nav=Files.readString(SOURCE.resolve("common/scripted_guis/xfm_market_navigation.txt"));assertTrue(nav.contains("xfm_registry_lookup_history_effect = yes"));assertTrue(nav.contains("name = xfm_archived_coin_registry target = scope:xfm_ui_item"));
    }

    @Test void invalidOrMissingHistoricalCounterCannotSilentlyCreateFreeCapacity()throws IOException{
        for(String failure:List.of("missing","negative","fractional")){
            Vm v=vm();if(failure.equals("missing"))v.exchange.vars.remove("xfm_registered_coin_count");else v.exchange.num("xfm_registered_coin_count",failure.equals("negative")?-1:1.5);
            v.run("xfm_finance_create_coin_effect",v.actor);assertEquals(0,v.actor.n("xfm_result"),failure);assertFalse(v.exchange.vars.containsKey("xfm_resident_coin_count"),failure);assertTrue(v.global("xfm_coin_registry").isEmpty(),failure);
        }
    }

    private static Vm vm()throws IOException{
        Map<String,Block>defs=new LinkedHashMap<>();for(String rel:INPUTS)for(Entry e:parse(Files.readString(SOURCE.resolve("common").resolve(rel))).entries())defs.put(e.key(),e.value() instanceof Block b?b:new Block(List.of(new Entry("value","=",e.value()))));return new Vm(defs);
    }
    private sealed interface Expr permits Atom,Block{}
    private record Atom(String text)implements Expr{}
    private record Entry(String key,String op,Expr value){}
    private record Block(List<Entry>entries)implements Expr{Block{entries=List.copyOf(entries);}Block block(String key){return (Block)field(this,key);}}
    private sealed interface Datum permits Num,Node,Text{}
    private record Num(BigDecimal value)implements Datum{}
    private record Text(String value)implements Datum{}
    private static final class Node implements Datum{
        final String type;final Map<String,Datum>vars=new HashMap<>();final Map<String,List<Node>>lists=new HashMap<>();Node owner;boolean ai=true;
        Node(String type){this.type=type;}Node num(String k,double n){vars.put(k,new Num(BigDecimal.valueOf(n)));return this;}Node ref(String k,Node n){vars.put(k,n);return this;}Node ref(String k){return vars.get(k) instanceof Node n?n:null;}
        long n(String k){return vars.get(k) instanceof Num x?x.value().longValueExact():0;}List<Node>list(String k){return lists.computeIfAbsent(k,ignored->new ArrayList<>());}
    }
    private record Frame(Node here,Node previous,Node root){Frame enter(Node n){return new Frame(n,here,root);}}
    private static final class Vm{
        final Map<String,Block>defs;final Map<String,Datum>scopes=new HashMap<>();final Map<String,List<Node>>globals=new HashMap<>();final List<Node>nodes=new ArrayList<>();
        final Node actor,exchange,wallet;int globalVisits,ended,globalDepth;
        Vm(Map<String,Block>d){defs=d;actor=node("character");exchange=node("xfm_finance_exchange");exchange.owner=actor;exchange.num("xfm_day",1).num("xfm_next_coin_id",0).num("xfm_coin_count",0).num("xfm_registered_coin_count",0).num("xfm_pending_coin_count",0);wallet=account();actor.ref("xfm_account",wallet).ref("xfm_active_account",wallet);}
        Node node(String t){Node n=new Node(t);n.owner=actor;nodes.add(n);return n;}
        Node account(){return node("xfm_finance_account").ref("xfm_holder",actor).num("xfm_free_cents",0).num("xfm_reserved_cents",0).num("xfm_account_frozen",0).num("xfm_inheritance_state",0).num("xfm_holdings_count",0);}
        Node coin(int id,int state){return node("xfm_finance_coin").num("xfm_coin_id",id).num("xfm_listing_state",state).num("xfm_trading_open",0).num("xfm_supply_units",0).num("xfm_entity_type",1).num("xfm_unpaid_debt_cents",0).num("xfm_promises_due_cents",0).num("xfm_maintenance_arrears_cents",0).num("xfm_settlement_price_pending",0).num("xfm_unresolved_claim_count",0).num("xfm_asset_age",0).num("xfm_founder_locked_units",0).ref("xfm_controller",actor).ref("xfm_issuer_account",account()).ref("xfm_founder_account",account());}
        Node failedOffer(){return failedOffer(1);}
        Node failedOffer(int id){Node c=coin(id,6).num("xfm_supply_units",15000).num("xfm_founder_locked_units",2500);for(int i=0;i<2;i++){Node a=c.ref(i==0?"xfm_issuer_account":"xfm_founder_account"),p=node("xfm_finance_position").ref("xfm_account",a).ref("xfm_coin",c).num("xfm_quantity_units",i==0?12500:2500).num("xfm_reserved_units",0).num("xfm_counted",1);a.num("xfm_holdings_count",1).list("xfm_positions").add(p);c.list("xfm_holders").add(p);}c.list("xfm_subscriptions").add(node("xfm_finance_reservation").num("xfm_subscription_state",3).num("xfm_remaining_cents",0));hot(c);return c;}
        List<Node>global(String name){return globals.computeIfAbsent(name,k->new ArrayList<>());}void hot(Node c){global("xfm_coin_registry").add(c);}
        void queueAndFlush(Node c){run("xfm_registry_queue_retire_effect",c);run("xfm_registry_flush_retire_effect",exchange);}
        Map<Node,Map<String,Datum>>copyVars(){Map<Node,Map<String,Datum>>result=new HashMap<>();for(Node n:nodes)result.put(n,Map.copyOf(n.vars));return result;}
        long cashStock(){return nodes.stream().filter(n->n.type.equals("xfm_finance_account")).mapToLong(n->n.n("xfm_free_cents")+n.n("xfm_reserved_cents")).sum();}
        void run(String name,Node n){exec(defs.get(name),new Frame(n,null,n));}
        Datum resolve(String token,Frame f){try{return new Num(new BigDecimal(token));}catch(NumberFormatException ignored){}int dot=token.indexOf('.');if(dot>0){Datum base=resolve(token.substring(0,dot),f);return base instanceof Node n?resolve(token.substring(dot+1),f.enter(n)):null;}if(token.equals("this"))return f.here();if(token.equals("prev"))return f.previous();if(token.equals("root"))return f.root();if(token.equals("story_owner"))return f.here().owner;if(Set.of("holder","house_head","dynast","religious_head").contains(token))return f.here().vars.get(token);if(token.equals("global_var:xfm_exchange"))return exchange;if(token.startsWith("scope:"))return scopes.get(token.substring(6));if(token.startsWith("var:"))return f.here().vars.get(token.substring(4));if(token.equals("xfm_config_registration_capacity_value"))return new Num(BigDecimal.valueOf(16384));if(token.equals("xfm_config_pending_capacity_value"))return new Num(BigDecimal.valueOf(240));if(defs.containsKey(token))return new Num(value(defs.get(token),f,BigDecimal.ZERO));return new Text(token);}
        BigDecimal number(Datum x){if(x==null)return BigDecimal.ZERO;if(x instanceof Num n)return n.value();throw new IllegalArgumentException("not a number "+x);}
        Datum eval(Expr x,Frame f){return x instanceof Block b?new Num(value(b,f,BigDecimal.ZERO)):resolve(atom(x),f);}
        BigDecimal value(Block b,Frame f,BigDecimal start){BigDecimal n=start;boolean chain=false;for(Entry e:b.entries()){String k=e.key();if(k.equals("if")||k.equals("else_if")){Block child=(Block)e.value();boolean yes=(!k.equals("else_if")||!chain)&&test(child.block("limit"),f);if(k.equals("if"))chain=false;if(yes){n=value(without(child,"limit"),f,n);chain=true;}continue;}if(k.equals("else")){if(!chain)n=value((Block)e.value(),f,n);chain=false;continue;}if(k.equals("every_in_list")){Block a=(Block)e.value();for(Node child:List.copyOf(f.here().list(atom(field(a,"variable")))))if(test(optionalLimit(a),f.enter(child)))n=value(without(a,"variable","limit"),f.enter(child),n);continue;}if(k.equals("floor")){n=n.setScale(0,RoundingMode.FLOOR);continue;}if(k.equals("ceiling")){n=n.setScale(0,RoundingMode.CEILING);continue;}BigDecimal x=number(eval(e.value(),f));n=switch(k){case "value"->x;case "add"->n.add(x);case "subtract"->n.subtract(x);case "multiply"->n.multiply(x);case "divide"->n.divide(x,18,RoundingMode.HALF_EVEN);case "min"->n.max(x);case "max"->n.min(x);default->throw new IllegalArgumentException("value "+k);};}return n;}
        boolean test(Block b,Frame f){return b.entries().stream().allMatch(e->check(e,f));}
        boolean check(Entry e,Frame f){String k=e.key();if(k.equals("AND"))return test((Block)e.value(),f);if(k.equals("OR"))return ((Block)e.value()).entries().stream().anyMatch(x->check(x,f));if(k.equals("NOT"))return ((Block)e.value()).entries().stream().noneMatch(x->check(x,f));if(k.equals("exists"))return resolve(atom(e.value()),f)!=null;if(k.equals("has_variable"))return f.here().vars.containsKey(atom(e.value()));if(k.equals("story_type"))return f.here().type.equals(atom(e.value()));if(k.equals("is_ai"))return f.here().ai==atom(e.value()).equals("yes");if(k.equals("is_alive")||k.equals("is_adult"))return atom(e.value()).equals("yes");if(k.equals("trigger_if")){Block a=(Block)e.value();return !test(a.block("limit"),f)||test(without(a,"limit"),f);}if(k.equals("any_in_list")){Block a=(Block)e.value();return List.copyOf(f.here().list(atom(field(a,"variable")))).stream().anyMatch(n->test(without(a,"variable"),f.enter(n)));}if(k.equals("is_target_in_variable_list")||k.equals("is_target_in_global_variable_list")){Block a=(Block)e.value();List<Node>list=k.equals("is_target_in_global_variable_list")?global(atom(field(a,"name"))):f.here().list(atom(field(a,"name")));return list.contains(eval(field(a,"target"),f));}if(k.endsWith("_trigger")&&defs.containsKey(k))return test(defs.get(k),f);Datum left=resolve(k,f);if(e.value() instanceof Block b&&left instanceof Node n)return test(b,f.enter(n));Datum right=eval(e.value(),f);if(left instanceof Num a&&right instanceof Num b){int c=a.value().compareTo(b.value());return switch(e.op()){case "="->c==0;case "!="->c!=0;case ">"->c>0;case "<"->c<0;case ">="->c>=0;case "<="->c<=0;default->throw new IllegalArgumentException(e.op());};}return e.op().equals("=")?Objects.equals(left,right):e.op().equals("!=")&&!Objects.equals(left,right);}
        void exec(Block b,Frame f){if(b==null)throw new IllegalArgumentException("missing definition");boolean chain=false;for(Entry e:b.entries()){String k=e.key();if(k.equals("if")||k.equals("else_if")){Block a=(Block)e.value();boolean yes=(!k.equals("else_if")||!chain)&&test(a.block("limit"),f);if(k.equals("if"))chain=false;if(yes){exec(without(a,"limit"),f);chain=true;}continue;}if(k.equals("else")){if(!chain)exec((Block)e.value(),f);chain=false;continue;}if(k.equals("save_scope_as")){scopes.put(atom(e.value()),f.here());continue;}if(k.equals("clear_saved_scope")){scopes.remove(atom(e.value()));continue;}if(k.equals("remove_variable")){f.here().vars.remove(atom(e.value()));continue;}if(k.equals("set_variable")||k.equals("change_variable")){Block a=(Block)e.value();String name=atom(field(a,"name"));if(k.equals("set_variable"))f.here().vars.put(name,eval(field(a,"value"),f));else{boolean add=a.entries().stream().anyMatch(x->x.key().equals("add"));BigDecimal amount=number(eval(field(a,add?"add":"subtract"),f)),old=number(f.here().vars.get(name));f.here().vars.put(name,new Num(add?old.add(amount):old.subtract(amount)));}continue;}if(k.equals("clear_variable_list")){f.here().list(atom(e.value())).clear();continue;}if(Set.of("add_to_variable_list","add_to_global_variable_list","remove_list_global_variable").contains(k)){Block a=(Block)e.value();String name=atom(field(a,"name"));Node target=(Node)eval(field(a,"target"),f);List<Node>list=k.equals("add_to_variable_list")?f.here().list(name):global(name);if(k.equals("remove_list_global_variable")){if(globalDepth>0)throw new IllegalStateException("mutated live list inside traversal");list.remove(target);}else list.add(target);continue;}if(Set.of("every_in_list","every_in_global_list","random_in_list","random_in_global_list").contains(k)){Block a=(Block)e.value();boolean global=k.contains("global");List<Node>list=List.copyOf(global?global(atom(field(a,"variable"))):f.here().list(atom(field(a,"variable"))));if(global)globalDepth++;for(Node n:list){if(global)globalVisits++;if(test(optionalLimit(a),f.enter(n))){exec(without(a,"variable","limit"),f.enter(n));if(k.startsWith("random"))break;}}if(global)globalDepth--;continue;}if(k.equals("create_story")){Block a=(Block)e.value();Node n=node(atom(field(a,"type")));n.owner=f.here();scopes.put(atom(field(a,"save_scope_as")),n);continue;}if(k.equals("end_story")){ended++;throw new IllegalStateException("permanent identity was ended");}
            if(k.equals("xfm_finance_select_account_effect")){scopes.put("xfm_account",wallet);continue;} // explicit account-selection port; no balance mutations
            if(Set.of("xfm_oracle_init_coin_effect","xfm_spot_init_history_effect","xfm_issuer_adopt_legacy_defaults_effect","xfm_issuer_refresh_controller_effect","xfm_issuer_unlock_founder_effect","xfm_issuer_investigate_effect","xfm_issuer_revisit_offer_effect","xfm_news_record_effect").contains(k))continue; // unrelated existing modules, no fake price/cash/units
            if(e.value() instanceof Block a){Datum scope=resolve(k,f);if(!(scope instanceof Node n))throw new IllegalArgumentException("missing scope "+k);exec(a,f.enter(n));continue;}exec(defs.get(k),f);
        }}
    }
    private static String atom(Expr e){return ((Atom)e).text();}
    private static Expr field(Block b,String key){List<Entry>list=b.entries().stream().filter(e->e.key().equals(key)).toList();if(list.size()!=1)throw new IllegalArgumentException("one field "+key);return list.getFirst().value();}
    private static Block optionalLimit(Block b){return b.entries().stream().anyMatch(e->e.key().equals("limit"))?b.block("limit"):new Block(List.of());}
    private static Block without(Block b,String...keys){Set<String>skip=Set.of(keys);return new Block(b.entries().stream().filter(e->!skip.contains(e.key())).toList());}
    private static Block parse(String raw){var m=Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|!=|>=|<=|[{}=<>]|[^\\s{}=<>]+").matcher(raw.replace("\ufeff","").replaceAll("(?m)#.*$",""));List<String>tokens=new ArrayList<>();while(m.find())tokens.add(m.group());int[]i={0};Block b=block(tokens,i,false);assertEquals(tokens.size(),i[0]);return b;}
    private static Block block(List<String>t,int[]i,boolean nested){List<Entry>entries=new ArrayList<>();while(i[0]<t.size()){String k=t.get(i[0]++);if(k.equals("}")){assertTrue(nested);return new Block(entries);}String op=t.get(i[0]++),v=t.get(i[0]++);assertTrue(Set.of("=","!=",">=","<=",">","<").contains(op));entries.add(new Entry(k,op,v.equals("{")?block(t,i,true):new Atom(v.startsWith("\"")?v.substring(1,v.length()-1):v)));}assertFalse(nested);return new Block(entries);}
}
