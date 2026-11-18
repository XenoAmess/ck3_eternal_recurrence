package org.xar.ck3.markets.issuance;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Offline script-subset contract checks. This interpreter is test-only and is NOT CK3.
 * Unknown effects/operators fail. Fixture snapshots are authored graph round trips, not game saves.
 */
final class AiAttentionScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final List<String> INPUTS = List.of(
        "scripted_effects/xfm_finance_attention.txt", "scripted_effects/xfm_finance_schedule.txt",
        "scripted_effects/xfm_issuer_ai_funding.txt", "scripted_effects/xfm_issuer_daily.txt",
        "scripted_effects/xfm_issuer_influence.txt", "script_values/xfm_finance_attention_values.txt",
        "script_values/xfm_issuer_ai_values.txt", "script_values/xfm_config_values.txt",
        "script_values/xfm_issuer_values.txt", "scripted_triggers/xfm_issuer_triggers.txt");

    @Test void quotasAndCapacityReadActualPresetValues() throws IOException {
        Vm v = vm();
        for (String tier : List.of("xfm_ai_light", "default", "xfm_ai_dense")) {
            v.rule = tier;
            int b = (int) v.number("xfm_config_ai_budget_value", v.exchange, null);
            int q = (int) v.number("xfm_finance_attention_quota_value", v.exchange, null);
            int cap = (int) v.number("xfm_finance_attention_capacity_value", v.exchange, null);
            assertEquals(Math.min(b / 4, 64), q);
            assertEquals(Math.min(1024, 20 * q), cap);
            assertTrue((cap + q - 1) / q <= 20);
        }
    }

    @Test void fullRingsShareBudgetPreserveOrdinaryAndDoNotDoubleDecide() throws IOException {
        for (String tier : List.of("xfm_ai_light", "default", "xfm_ai_dense")) {
            Vm v = vm(); v.rule = tier;
            List<Node> actors = population(v, 2000);
            int cap = (int) v.number("xfm_finance_attention_capacity_value", v.exchange, null);
            for (int i = 0; i < cap; i++) attention(v, actors.get(i), 31);
            v.run("xfm_finance_run_ai_budget_effect", v.exchange);
            int b = (int) v.number("xfm_config_ai_budget_value", v.exchange, null);
            int q = (int) v.number("xfm_finance_attention_quota_value", v.exchange, null);
            assertEquals(b, v.num(v.exchange, "xfm_ai_work_today"));
            assertEquals(q, v.num(v.exchange, "xfm_attention_work_today"));
            assertTrue(b - q >= 3 * b / 4);
            assertEquals(b - q, v.ordinaryPops);
            assertEquals(2000, v.num(v.exchange, "xfm_ai_count"));
            assertTrue(v.calls.values().stream().allMatch(c -> c == 1));
            assertEquals(v.calls.size(), v.num(v.exchange, "xfm_ai_decisions_today"));
        }
    }

    @Test void smallPriorityReturnsUnusedSlotsAndSmallRingsVisitOnce() throws IOException {
        Vm v = vm(); population(v, 1000); attention(v, v.nodes.get("a0"), 31);
        v.run("xfm_finance_run_ai_budget_effect", v.exchange);
        assertEquals(1, v.num(v.exchange, "xfm_attention_work_today"));
        assertEquals(511, v.ordinaryPops);
        assertEquals(1, v.calls.get("a0"));
        Vm tiny = vm(); population(tiny, 1); attention(tiny, tiny.nodes.get("a0"), 31);
        tiny.run("xfm_finance_run_ai_budget_effect", tiny.exchange);
        assertEquals(2, tiny.num(tiny.exchange, "xfm_ai_work_today"));
        assertEquals(1, tiny.calls.get("a0"));
    }

    @Test void paidPriorityAdmissionIsBoundedAndNeverMutatesOrdinaryLinks() throws IOException {
        Vm v = vm(); v.rule = "xfm_ai_light"; List<Node> actors = population(v, 700);
        for (Node a : actors) attention(v, a, 31);
        assertEquals(640, v.num(v.exchange, "xfm_attention_count"));
        assertFalse(actors.get(640).vars.containsKey("xfm_attention_queued"));
        assertEquals(700, v.num(v.exchange, "xfm_ai_count"));
        assertSame(actors.get(641), actors.get(640).vars.get("xfm_ai_next"));
        attention(v, actors.get(0), 35); // renewal keeps position, no duplicate node
        assertEquals(640, v.num(v.exchange, "xfm_attention_count"));
        assertSame(actors.get(1), actors.get(0).vars.get("xfm_attention_next"));
    }

    @Test void deadlinesDeathsPlayersAndChildrenDropWithoutLosingNormalMembership() throws IOException {
        Vm v = vm(); List<Node> a = population(v, 8);
        attention(v, a.get(0), 2); attention(v, a.get(1), 31);
        a.get(1).alive = false;
        a.get(2).ai = false; a.get(3).adult = false;
        attention(v, a.get(2), 31); attention(v, a.get(3), 31);
        assertFalse(a.get(2).vars.containsKey("xfm_attention_queued"));
        assertFalse(a.get(3).vars.containsKey("xfm_attention_queued"));
        v.exchange.vars.put("xfm_day", 2d);
        v.run("xfm_finance_run_ai_budget_effect", v.exchange);
        assertEquals(0, v.num(v.exchange, "xfm_attention_count"));
        assertEquals(7, v.num(v.exchange, "xfm_ai_count"));
        assertFalse(v.calls.containsKey("a1"));
        assertTrue(a.get(0).vars.containsKey("xfm_ai_queued"));
        assertFalse(a.get(0).vars.containsKey("xfm_attention_until_day"));
    }

    @Test void nestedAdvertisingUsesIndependentAliasesAndFailedBusinessStaysQueued() throws IOException {
        Vm v = vm(); List<Node> a = population(v, 10);
        attention(v, a.get(0), 31);
        v.coinCallback = actor -> { if (actor == a.get(0)) { attention(v, a.get(1), 31); attention(v, actor, 31); } };
        v.run("xfm_finance_run_ai_budget_effect", v.exchange);
        assertEquals(2, v.num(v.exchange, "xfm_attention_count"));
        assertEquals(10, v.num(v.exchange, "xfm_ai_count"));
        assertTrue(a.get(0).vars.containsKey("xfm_ai_queued"));
        assertEquals(1, v.calls.get("a0"));
        assertFalse(v.scopes.containsKey("xfm_attention_active_actor"));
        assertFalse(v.scopes.containsKey("xfm_attention_enqueue_actor"));
        // Consumers' false business result does not gate normal requeue.
        assertEquals(0, v.num(a.get(0), "xfm_issuer_result"));
    }

    @Test void authoredSnapshotReloadRetainsPointersDeadlineAndSameDayGuard() throws IOException {
        Vm v = vm(); List<Node> a = population(v, 20); attention(v, a.get(8), 31);
        v.run("xfm_finance_run_ai_budget_effect", v.exchange);
        Vm restored = Vm.read(v.program, v.write());
        assertSame(restored.nodes.get("a8"), restored.exchange.vars.get("xfm_attention_head"));
        assertEquals(31, restored.num(restored.nodes.get("a8"), "xfm_attention_until_day"));
        restored.run("xfm_finance_run_ai_budget_effect", restored.exchange);
        assertTrue(restored.calls.isEmpty()); // same financial day, including both rings
        restored.exchange.vars.put("xfm_day", 2d);
        restored.run("xfm_finance_run_ai_budget_effect", restored.exchange);
        assertEquals(20, restored.calls.size());
        assertTrue(restored.calls.values().stream().allMatch(c -> c == 1));
    }

    @Test void actualMoneyFormulasAnd171BoundaryExcludeOtherPeoplesOrReservedCash() throws IOException {
        Vm v = vm(); Node a = v.node("owner"); a.gold = 171;
        Node account = v.node("private"); account.vars.put("xfm_holder", a); account.vars.put("xfm_free_cents", 0d);
        account.vars.put("xfm_system_account", 0d); a.vars.put("xfm_account", account);
        Block standard = findLimit(v.program.get("xfm_coin_ai_effect"), "xfm_issuer_ai_liquid_cents_value", ">=", "17100");
        assertTrue(v.test(standard, a, null));
        a.gold = 170.99; assertFalse(v.test(standard, a, null));
        a.gold = 100; account.vars.put("xfm_free_cents", 7100d); account.vars.put("xfm_reserved_cents", 900000d);
        assertTrue(v.test(standard, a, null));
        account.vars.put("xfm_free_cents", 7099d); assertFalse(v.test(standard, a, null));
        account.vars.put("xfm_free_cents", 7100d); account.vars.put("xfm_system_account", 1d);
        assertFalse(v.test(standard, a, null));
        account.vars.put("xfm_system_account", 0d); account.vars.put("xfm_holder", v.node("other"));
        assertFalse(v.test(standard, a, null));
        account.vars.put("xfm_holder", a); account.usable = false; assertFalse(v.test(standard, a, null));
        // A separate inherited account reference never contributes to the primary cash calculation.
        a.vars.remove("xfm_account"); a.vars.put("xfm_active_account", account); assertFalse(v.test(standard, a, null));
    }

    @Test void actualSubscriptionHelpersCapAndReserveRealAssetsAndStillUseOrdinaryPayment() throws IOException {
        Vm v = vm(); Node a = v.node("owner"); a.gold = 166;
        Node coin = v.node("coin"); coin.vars.put("xfm_controller", a); coin.vars.put("xfm_minimum_raised_cents", 20000d);
        a.vars.put("xfm_pending_offer", coin); a.vars.put("xfm_selected_coin", coin);
        v.run("xfm_issuer_ai_self_subscribe_effect", a);
        assertEquals(160, v.num(a, "xfm_subscription_gold"));
        assertEquals(1, v.subscriptionAttempts);
        a.gold = 8; v.run("xfm_issuer_ai_self_subscribe_effect", a);
        assertEquals(2, v.num(a, "xfm_subscription_gold"));
        a.gold = 5; v.run("xfm_issuer_ai_self_subscribe_effect", a);
        assertEquals(0, v.num(a, "xfm_subscription_gold"));
        coin.vars.put("xfm_controller", v.node("issuer"));
        a.vars.put("xfm_promoted_coin", coin); a.vars.put("xfm_promotion_end_day", 31d); a.gold = 200;
        v.run("xfm_issuer_ai_ad_subscribe_effect", a);
        assertEquals(20, v.num(a, "xfm_subscription_gold"));
        coin.vars.put("xfm_minimum_raised_cents", 2000d);
        v.run("xfm_issuer_ai_ad_subscribe_effect", a); assertEquals(2, v.num(a, "xfm_subscription_gold"));
        a.gold = 5.25; v.run("xfm_issuer_ai_ad_subscribe_effect", a);
        assertEquals(0.25, v.num(a, "xfm_subscription_gold"), 0.00001);
        coin.vars.put("xfm_controller", a); int before = v.subscriptionAttempts;
        v.run("xfm_issuer_ai_ad_subscribe_effect", a); assertEquals(before, v.subscriptionAttempts);
    }

    @Test void paidPromotionAdmissionOccursOnlyAfterSuccessfulRealFeeAndKeepsIssuerReachable() throws IOException {
        Vm v = vm(); Node promoter = v.node("promoter"); Node coin = v.node("coin");
        Node account = v.node("account"); account.vars.put("xfm_holder", promoter); account.vars.put("xfm_system_account", 0d);
        account.vars.put("xfm_free_cents", 0d); promoter.vars.put("xfm_account", account); promoter.vars.put("xfm_selected_coin", coin);
        v.run("xfm_issuer_promote_effect", promoter);
        assertFalse(promoter.vars.containsKey("xfm_attention_queued"));
        promoter.gold = 1;
        v.run("xfm_issuer_promote_effect", promoter);
        assertEquals(0, promoter.gold);
        assertEquals(100, v.fees);
        assertEquals(31, v.num(promoter, "xfm_attention_until_day"));
        assertTrue(promoter.vars.containsKey("xfm_attention_queued"));
        assertFalse(promoter.vars.containsKey("xfm_promoted_coin"));
        Node invited = v.node("invited"); v.scopes.put("xfm_offer_promoter", promoter);
        v.run("xfm_issuer_receive_ad_effect", invited);
        assertSame(coin, invited.vars.get("xfm_promoted_coin"));
        assertTrue(invited.vars.containsKey("xfm_attention_queued"));
        assertEquals(2, v.num(v.exchange, "xfm_attention_count"));
    }

    @Test void existingSubscriptionLotAndCostFormulasRoundDownWithinCashAndFounderCaps() throws IOException {
        Vm v=vm(); Node a=v.node("buyer"); Node coin=v.node("coin"); a.vars.put("xfm_selected_coin",coin);
        coin.vars.put("xfm_minimum_raised_cents",20000d); coin.vars.put("xfm_ipo_price_cents",200d); coin.vars.put("xfm_offer_units_remaining",10000d);
        for(double gold:List.of(5.25,7d,20d,166d,10000d)) {
            a.gold=gold; double subscription=v.number("xfm_issuer_ai_self_gold_value",a,null);
            a.vars.put("xfm_subscription_gold",subscription);
            a.vars.put("xfm_offer_request_cents",v.number("xfm_issuer_subscription_cents_value",a,null));
            a.vars.put("xfm_offer_request_lots",v.number("xfm_issuer_subscription_lots_value",a,null));
            double cost=v.number("xfm_issuer_subscription_cost_value",a,null);
            double units=v.number("xfm_issuer_subscription_units_value",a,null);
            assertTrue(cost<=16000 && cost<=Math.max(0,gold*100-600));
            assertEquals(0,cost%200); assertEquals(0,units%100); assertTrue(units<=8000);
            a.vars.put("xfm_subscription_gold",v.number("xfm_issuer_ai_ad_gold_value",a,null));
            a.vars.put("xfm_offer_request_cents",v.number("xfm_issuer_subscription_cents_value",a,null));
            a.vars.put("xfm_offer_request_lots",v.number("xfm_issuer_subscription_lots_value",a,null));
            double adCost=v.number("xfm_issuer_subscription_cost_value",a,null);
            assertTrue(adCost<=2000 && adCost<=Math.max(0,gold*100-500));
        }
        a.gold=1000; coin.vars.put("xfm_offer_units_remaining",100d);
        a.vars.put("xfm_subscription_gold",v.number("xfm_issuer_ai_self_gold_value",a,null));
        a.vars.put("xfm_offer_request_cents",v.number("xfm_issuer_subscription_cents_value",a,null));
        a.vars.put("xfm_offer_request_lots",v.number("xfm_issuer_subscription_lots_value",a,null));
        assertEquals(1,v.num(a,"xfm_offer_request_lots"));
        assertEquals(200,v.number("xfm_issuer_subscription_cost_value",a,null));
    }

    @Test void sourceCompositionRetainsChanceNormalFundingAndNoSecondGlobalScan() throws IOException {
        Vm v = vm();
        Block purchase = findBlockWith(v.program.get("xfm_coin_ai_effect"), "xfm_issuer_ai_ad_subscribe_effect");
        assertTrue(purchase.entries().contains(new Entry("chance", "=", new Text("25"))));
        Block registration = findBlockWith(v.program.get("xfm_coin_ai_effect"), "xfm_issuer_ai_self_subscribe_effect");
        assertTrue(index(registration, "xfm_issuer_ai_self_subscribe_effect") < index(registration, "xfm_issuer_promote_effect"));
        assertEquals(1, count(v.program.get("xfm_finance_daily_effect"), "xfm_finance_run_ai_budget_effect"));
        assertEquals(1, count(v.program.get("xfm_finance_pop_ai_effect"), "xfm_finance_ai_decision_effect"));
        for (String name : List.of("xfm_finance_run_ai_budget_effect", "xfm_finance_enqueue_attention_effect", "xfm_finance_pop_attention_effect")) {
            assertEquals(0, count(v.program.get(name), "every_living_character"));
            assertEquals(0, count(v.program.get(name), "random_in_global_list"));
        }
        // Original production subscriber still calls real funding and reserve; never a direct balance addition.
        String subscriber = Files.readString(dependency("scripted_effects/xfm_issuer_subscriptions.txt"));
        assertTrue(subscriber.contains("xfm_finance_ensure_funds_effect = yes"));
        assertTrue(subscriber.contains("xfm_finance_reserve_effect = yes"));
        assertTrue(subscriber.contains("var:xfm_controller != scope:xfm_offer_buyer"));
        assertThrows(IllegalArgumentException.class, () -> v.execute(parse("unknown_operation = yes"), v.exchange, null));
        assertThrows(IllegalArgumentException.class, () -> v.value(parse("value = 1 mysterious = 8"), v.exchange, null));
    }

    @Test void actualPendingTickClosesDay29FundingOnDay30BeforeRefundAndRestoresSelection() throws IOException {
        Vm v = vm(); Node a = v.node("issuer"); Node coin = offering(v,a); Node previous = v.node("previous"); a.vars.put("xfm_selected_coin",previous);
        Block tick = without(findBlockWith(v.program.get("xfm_coin_daily_effect"),"xfm_issuer_revisit_offer_effect"),"limit");
        coin.vars.put("xfm_offer_age",15d); coin.vars.put("xfm_actual_raised_cents",16000d);
        v.exchange.vars.put("xfm_day",16d); v.execute(tick,coin,v.exchange);
        assertEquals(0,v.completions); assertEquals(0,v.refunds);
        coin.vars.put("xfm_offer_age",28d); v.exchange.vars.put("xfm_day",29d); v.execute(tick,coin,v.exchange);
        // Ordinary subscriber pays after D29 housekeeping; controller next ring visit would be D32.
        coin.vars.put("xfm_actual_raised_cents",20000d); coin.vars.put("xfm_external_raised_cents",4000d);
        v.exchange.vars.put("xfm_day",30d); v.execute(tick,coin,v.exchange);
        assertEquals(1,v.completions); assertEquals(0,v.refunds); assertEquals(1,v.num(coin,"xfm_listing_state"));
        assertSame(previous,a.vars.get("xfm_selected_coin"));
        assertFalse(v.scopes.containsKey("xfm_offer_retry_coin"));
        assertFalse(v.scopes.containsKey("xfm_offer_retry_previous_coin"));
    }

    @Test void fundedPlayersRemainManualButPriorClosingRetriesAndNativeCapacityStillApply() throws IOException {
        Vm v = vm(); Node a=v.node("player"); a.ai=false; Node coin=offering(v,a);
        coin.vars.put("xfm_actual_raised_cents",20000d); coin.vars.put("xfm_external_raised_cents",4000d);
        v.run("xfm_issuer_revisit_offer_effect",coin); assertEquals(0,v.completions);
        coin.vars.put("xfm_offer_closing_started",1d); v.run("xfm_issuer_revisit_offer_effect",coin);
        assertEquals(1,v.completions); assertFalse(a.vars.containsKey("xfm_selected_coin"));
        Vm blocked=vm(); Node ai=blocked.node("issuer"); Node pending=offering(blocked,ai);
        pending.vars.put("xfm_actual_raised_cents",20000d); pending.vars.put("xfm_external_raised_cents",4000d);
        blocked.exchange.vars.put("xfm_new_listings_today",8d);
        blocked.run("xfm_issuer_revisit_offer_effect",pending); assertEquals(0,blocked.completions);
        blocked.exchange.vars.put("xfm_new_listings_today",0d); ai.alive=false;
        blocked.run("xfm_issuer_revisit_offer_effect",pending); assertEquals(0,blocked.completions);
    }

    @Test void completingInheritedOfferPreservesOnlyDifferentLiveStillOwnedPendingOffer() throws IOException {
        for(boolean stillOwned:List.of(false,true)) {
            Vm v=vm(); Node a=v.node("issuer"); Node inherited=offering(v,a);
            inherited.vars.put("xfm_actual_raised_cents",20000d); inherited.vars.put("xfm_external_raised_cents",4000d);
            Node own=v.node("separate-offer"); own.storyType="xfm_finance_coin"; own.vars.put("xfm_listing_state",0d);
            own.vars.put("xfm_controller",stillOwned?a:v.node("new-controller"));
            a.vars.put("xfm_pending_offer",own);
            v.run("xfm_issuer_revisit_offer_effect",inherited);
            assertEquals(1,v.completions);
            if(stillOwned) assertSame(own,a.vars.get("xfm_pending_offer"));
            else assertFalse(a.vars.containsKey("xfm_pending_offer"));
            assertFalse(v.scopes.containsKey("xfm_offer_retry_previous_pending"));
        }
        Vm same=vm(); Node a=same.node("issuer"); Node own=offering(same,a);
        own.vars.put("xfm_actual_raised_cents",20000d); own.vars.put("xfm_external_raised_cents",4000d);
        a.vars.put("xfm_pending_offer",own); same.run("xfm_issuer_revisit_offer_effect",own);
        assertEquals(1,same.completions); assertFalse(a.vars.containsKey("xfm_pending_offer"));
    }

    private static Node offering(Vm v,Node a) { Node coin=v.node("offering"); coin.vars.put("xfm_controller",a); coin.vars.put("xfm_listing_state",0d); coin.vars.put("xfm_minimum_raised_cents",20000d); coin.vars.put("xfm_actual_raised_cents",0d); coin.vars.put("xfm_external_raised_cents",0d); coin.vars.put("xfm_offer_units_remaining",2000d); return coin; }

    private static int index(Block b, String key) { for (int i = 0; i < b.entries().size(); i++) if (b.entries().get(i).key().equals(key)) return i; return -1; }
    private static int count(Block b, String key) { int n = 0; for (Entry e : b.entries()) { if (e.key().equals(key)) n++; if (e.term() instanceof Block child) n += count(child, key); } return n; }
    private static Block findBlockWith(Block b, String key) { if (index(b, key) >= 0) return b; for (Entry e : b.entries()) if (e.term() instanceof Block child) { Block found = findBlockOrNull(child, key); if (found != null) return found; } throw new AssertionError(key); }
    private static Block findBlockOrNull(Block b, String key) { if (index(b, key) >= 0) return b; for (Entry e : b.entries()) if (e.term() instanceof Block child) { Block found = findBlockOrNull(child, key); if (found != null) return found; } return null; }
    private static Block findLimit(Block b, String key, String op, String text) { for (Entry e : b.entries()) if (e.term() instanceof Block child) { if (e.key().equals("limit") && child.entries().contains(new Entry(key, op, new Text(text)))) return child; try { return findLimit(child,key,op,text); } catch (IllegalArgumentException ignored) { /* continue another branch */ } } throw new IllegalArgumentException("missing actual limit: " + key); }
    private static Path dependency(String rel) { Path direct = SOURCE.resolve("common").resolve(rel); return Files.exists(direct) ? direct : SOURCE.resolve("../baseline/mod_financial_markets/common").normalize().resolve(rel); }
    private static Vm vm() throws IOException {
        Map<String, Block> defs = new LinkedHashMap<>();
        for (String rel : INPUTS) for (Entry e : parse(Files.readString(dependency(rel), StandardCharsets.UTF_8)).entries()) {
            Block definition;
            if (e.term() instanceof Block block) definition = block;
            else { Double.parseDouble(((Text)e.term()).text()); definition = new Block(List.of(new Entry("value","=",e.term()))); }
            if (defs.put(e.key(),definition) != null) throw new IllegalArgumentException("duplicate definition: " + e.key());
        }
        return new Vm(defs);
    }
    private static List<Node> population(Vm v, int n) { List<Node> a = new ArrayList<>(); for (int i = 0; i < n; i++) { Node node = v.node("a" + i); a.add(node); v.run("xfm_finance_enqueue_ai_effect", node); } return a; }
    private static void attention(Vm v, Node n, int until) { n.vars.put("xfm_attention_until_day", (double) until); v.run("xfm_finance_enqueue_attention_effect", n); }

    private sealed interface Term permits Text, Block {}
    private record Text(String text) implements Term {}
    private record Block(List<Entry> entries) implements Term { Block { entries = List.copyOf(entries); } }
    private record Entry(String key, String op, Term term) {}
    private static Block parse(String source) {
        List<String> tokens = new ArrayList<>(); var matcher = Pattern.compile("#[^\\r\\n]*|[\\s\\uFEFF]+|>=|<=|!=|[{}=<>]|[^\\s{}=<>!#\\uFEFF]+").matcher(source);
        while (matcher.find()) { String s = matcher.group(); if (!s.isBlank() && !s.startsWith("#") && !s.equals("\uFEFF")) tokens.add(s); }
        int[] at = {0}; Block result = block(tokens, at, false); if (at[0] != tokens.size()) throw new IllegalArgumentException("trailing tokens"); return result;
    }
    private static Block block(List<String> tokens, int[] at, boolean nested) {
        List<Entry> result = new ArrayList<>();
        while (at[0] < tokens.size()) {
            String key = tokens.get(at[0]++); if (key.equals("}")) { if (!nested) throw new IllegalArgumentException("unexpected }"); return new Block(result); }
            String op = tokens.get(at[0]++); if (!List.of("=", "<", ">", "<=", ">=", "!=").contains(op)) throw new IllegalArgumentException("operator " + op);
            String text = tokens.get(at[0]++); Term term = text.equals("{") ? block(tokens, at, true) : new Text(text); result.add(new Entry(key, op, term));
        }
        if (nested) throw new IllegalArgumentException("missing }"); return new Block(result);
    }

    private static final class Node {
        final String id; final Map<String,Object> vars = new LinkedHashMap<>(); boolean alive = true, adult = true, ai = true, usable = true; double gold; String storyType="";
        Node(String id) { this.id = id; }
    }
    private static final class Vm {
        final Map<String,Block> program; final Map<String,Node> nodes = new LinkedHashMap<>(); final Map<String,Node> scopes = new HashMap<>();
        final Map<String,Integer> calls = new LinkedHashMap<>(); final Node exchange; String rule = "default"; int ordinaryPops, subscriptionAttempts; double fees;
        int completions,refunds;
        Consumer<Node> coinCallback = actor -> {};
        Vm(Map<String,Block> program) { this.program = program; exchange = node("exchange"); exchange.vars.put("xfm_day", 1d); exchange.vars.put("xfm_ai_count", 0d); exchange.vars.put("xfm_new_listings_today",0d); exchange.vars.put("xfm_active_coin_count",0d); }
        Node node(String id) { return nodes.computeIfAbsent(id, Node::new); }
        double num(Node node, String key) { Object v = node.vars.get(key); return v == null ? 0 : (Double) v; }
        Object resolve(String text, Node here, Node prev) {
            if (text.equals("this")) return here; if (text.equals("prev")) return prev;
            if (text.equals("global_var:xfm_exchange")) return exchange;
            if (text.startsWith("global_var:xfm_exchange.")) return resolve(text.substring(24), exchange, here);
            int dot = text.indexOf('.');
            if (dot > 0) { Object base = resolve(text.substring(0,dot),here,prev); return base instanceof Node n ? resolve(text.substring(dot+1),n,here) : null; }
            if (text.startsWith("scope:")) return scopes.get(text.substring(6));
            if (text.startsWith("var:")) return here.vars.get(text.substring(4));
            if (text.equals("gold")) return here.gold;
            if (program.containsKey(text)) return value(program.get(text),here,prev);
            try { return Double.valueOf(text); } catch (NumberFormatException ignored) { return text; }
        }
        double number(String text, Node here, Node prev) { Object value = resolve(text,here,prev); if (!(value instanceof Double n)) throw new IllegalArgumentException("not number: " + text); return n; }
        private String text(Term term) { if (!(term instanceof Text t)) throw new IllegalArgumentException("not atom"); return t.text(); }
        private Object term(Term term, Node here, Node prev) { return term instanceof Block b ? value(b,here,prev) : resolve(text(term),here,prev); }
        double value(Block b, Node here, Node prev) { return value(b, here, prev, 0); }
        double value(Block b, Node here, Node prev, double initial) {
            double n = initial; boolean chain = false;
            for (Entry e : b.entries()) {
                String key = e.key();
                if (key.equals("if") || key.equals("else_if")) { Block child = (Block)e.term(); boolean applies = (!key.equals("else_if") || !chain) && test(child(child,"limit"),here,prev); if (key.equals("if")) chain = false; if (applies) { n = value(without(child,"limit"),here,prev,n); chain = true; } continue; }
                if (key.equals("floor")) { n = Math.floor(n); continue; }
                if (key.equals("ceiling")) { n = Math.ceil(n); continue; }
                double operand = (Double)term(e.term(),here,prev);
                n = switch(key) { case "value" -> operand; case "add" -> n + operand; case "subtract" -> n - operand; case "multiply" -> n * operand; case "divide" -> n / operand; case "max" -> Math.min(n,operand); case "min" -> Math.max(n,operand); default -> throw new IllegalArgumentException("value op " + key); };
            } return n;
        }
        boolean test(Block b, Node here, Node prev) { for (Entry e : b.entries()) if (!check(e,here,prev)) return false; return true; }
        boolean check(Entry e, Node here, Node prev) {
            String key = e.key();
            if (key.equals("OR")) return ((Block)e.term()).entries().stream().anyMatch(x -> check(x,here,prev));
            if (key.equals("AND")) return test((Block)e.term(),here,prev);
            if (key.equals("NOT")) return ((Block)e.term()).entries().stream().noneMatch(x -> check(x,here,prev));
            if (key.equals("has_variable")) return here.vars.containsKey(text(e.term()));
            if (key.equals("exists")) return resolve(text(e.term()),here,prev) != null;
            if (key.equals("has_game_rule")) return rule.equals(text(e.term()));
            if (key.equals("story_type")) return here.storyType.equals(text(e.term()));
            if (key.equals("is_alive")) return here.alive; if (key.equals("is_adult")) return here.adult; if (key.equals("is_ai")) return here.ai;
            if (key.equals("xfm_finance_account_usable_trigger")) return here.usable;
            if (key.equals("xfm_issuer_controls_selected_trigger")) return here.alive && here.adult && here.vars.get("xfm_selected_coin") instanceof Node c && c.vars.get("xfm_controller") == here;
            if (key.equals("xfm_issuer_actor_trigger")) return here.alive && here.adult;
            if(key.equals("xfm_issuer_can_complete_trigger")) return test(program.get(key),here,prev);
            if(key.endsWith("_trigger")) throw new IllegalArgumentException("unknown test trigger " + key);
            if (e.term() instanceof Block child) { Object resolved = resolve(key,here,prev); return resolved instanceof Node n && test(child,n,here); }
            Object l = resolve(key,here,prev), r = term(e.term(),here,prev);
            if (e.op().equals("=")) return java.util.Objects.equals(l,r);
            if (e.op().equals("!=")) return !java.util.Objects.equals(l,r);
            if (!(l instanceof Double x) || !(r instanceof Double y)) return false;
            return switch(e.op()) { case ">" -> x > y; case "<" -> x < y; case ">=" -> x >= y; case "<=" -> x <= y; default -> throw new IllegalArgumentException("test op " + e.op()); };
        }
        void run(String name, Node here) {
            if (name.equals("xfm_finance_pop_ai_effect")) ordinaryPops++;
            Block effect = program.get(name); if (effect == null) throw new IllegalArgumentException("unknown effect " + name); execute(effect,here,null);
        }
        void execute(Block b, Node here, Node prev) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                String key = e.key();
                if (key.equals("if") || key.equals("else_if")) { Block child = (Block)e.term(); boolean applies = (!key.equals("else_if") || !chain) && test(child(child,"limit"),here,prev); if (key.equals("if")) chain = false; if (applies) { execute(without(child,"limit"),here,prev); chain = true; } continue; }
                if (key.equals("else")) { if (!chain) execute((Block)e.term(),here,prev); chain = false; continue; }
                if (key.equals("while")) { Block child = (Block)e.term(); int loops = 0; while (test(child(child,"limit"),here,prev)) { if (++loops > 10000) throw new IllegalArgumentException("unbounded loop"); execute(without(child,"limit"),here,prev); } continue; }
                if (key.equals("save_scope_as")) { scopes.put(text(e.term()),here); continue; }
                if (key.equals("clear_saved_scope")) { scopes.remove(text(e.term())); continue; }
                if (key.equals("remove_variable")) { here.vars.remove(text(e.term())); continue; }
                if (key.equals("set_variable") || key.equals("change_variable")) { Block fields = (Block)e.term(); String name = text(field(fields,"name"));
                    if (key.equals("set_variable")) { Term t = optional(fields,"value"); if (t == null) t = field(fields,"days"); here.vars.put(name,term(t,here,prev)); }
                    else if (optional(fields,"add") != null) here.vars.put(name,num(here,name)+(Double)term(field(fields,"add"),here,prev));
                    else here.vars.put(name,num(here,name)-(Double)term(field(fields,"subtract"),here,prev)); continue;
                }
                if (key.equals("xfm_coin_ai_effect")) { calls.merge(here.id,1,Integer::sum); here.vars.put("xfm_issuer_result",0d); coinCallback.accept(here); continue; }
                if (List.of("xfm_spot_ai_effect","xfm_futures_ai_effect","xfm_spot_watch_coin_effect").contains(key)) continue; // explicitly authored no-op consumer ports
                if (key.equals("xfm_issuer_subscribe_effect")) { subscriptionAttempts++; continue; } // records attempted normal funding, never grants money
                if(key.equals("xfm_issuer_complete_offer_effect")) { if(check(new Entry("xfm_issuer_can_complete_trigger","=",new Text("yes")),here,prev)) { ((Node)here.vars.get("xfm_selected_coin")).vars.put("xfm_listing_state",1d); here.vars.remove("xfm_pending_offer"); completions++; } continue; } // actual public success also unconditionally removes pending; engine allocation is outside this subset
                if(key.equals("xfm_issuer_refund_effect")) { here.vars.put("xfm_listing_state",6d); refunds++; continue; } // explicit refund port, no cash manufactured
                if (key.equals("xfm_finance_ensure_account_effect")) continue; // fixture requires pre-existing explicit account
                if (key.equals("xfm_finance_ensure_funds_effect")) { double need = num(here,"xfm_request_cents") - num(here,"xfm_free_cents"); Node holder = (Node)here.vars.get("xfm_holder"); if (need > 0 && holder.gold*100 >= need) { holder.gold -= need/100; here.vars.put("xfm_free_cents",num(here,"xfm_free_cents")+need); } continue; }
                if (key.equals("xfm_finance_fee_effect")) { double cost = num(here,"xfm_request_cents"); boolean paid = num(here,"xfm_free_cents") >= cost; here.vars.put("xfm_result",paid?1d:0d); if (paid) { here.vars.put("xfm_free_cents",num(here,"xfm_free_cents")-cost); fees += cost; } continue; }
                if (key.equals("every_close_family_member") || key.equals("every_courtier_or_guest")) continue; // authored empty family/court; receive_ad tested separately
                if (e.term() instanceof Block child) { Object resolved = resolve(key,here,prev); if (!(resolved instanceof Node n)) throw new IllegalArgumentException("missing scope " + key); execute(child,n,here); continue; }
                run(key,here);
            }
        }
        byte[] write() throws IOException { var bytes = new ByteArrayOutputStream(); try (var out = new DataOutputStream(bytes)) { out.writeUTF(rule); out.writeInt(nodes.size()); for (Node n : nodes.values()) { out.writeUTF(n.id); out.writeBoolean(n.alive); out.writeBoolean(n.adult); out.writeBoolean(n.ai); out.writeBoolean(n.usable); out.writeDouble(n.gold); out.writeInt(n.vars.size()); for (var e : n.vars.entrySet()) { out.writeUTF(e.getKey()); out.writeBoolean(e.getValue() instanceof Node); if (e.getValue() instanceof Node ref) out.writeUTF(ref.id); else out.writeDouble((Double)e.getValue()); } } } return bytes.toByteArray(); }
        static Vm read(Map<String,Block> p, byte[] bytes) throws IOException { Vm v = new Vm(p); Map<Node,Map<String,String>> refs = new HashMap<>(); try (var in = new DataInputStream(new ByteArrayInputStream(bytes))) { v.rule=in.readUTF(); int size=in.readInt(); for(int i=0;i<size;i++) { Node n=v.node(in.readUTF()); n.vars.clear(); n.alive=in.readBoolean(); n.adult=in.readBoolean(); n.ai=in.readBoolean(); n.usable=in.readBoolean(); n.gold=in.readDouble(); int fields=in.readInt(); for(int j=0;j<fields;j++) { String key=in.readUTF(); if(in.readBoolean()) refs.computeIfAbsent(n,k->new HashMap<>()).put(key,in.readUTF()); else n.vars.put(key,in.readDouble()); } } } refs.forEach((n,map)->map.forEach((key,id)->n.vars.put(key,v.nodes.get(id)))); return v; }
    }
    private static Term optional(Block b,String key) { for(Entry e:b.entries()) if(e.key().equals(key)) return e.term(); return null; }
    private static Term field(Block b,String key) { Term t=optional(b,key); if(t==null) throw new IllegalArgumentException("missing field " + key); return t; }
    private static Block child(Block b,String key) { return (Block)field(b,key); }
    private static Block without(Block b,String key) { return new Block(b.entries().stream().filter(e->!e.key().equals(key)).toList()); }
}
