package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.markets.acceptance.FollowupFixtureTest.parse;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.acceptance.FollowupContracts.*;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Atom;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Block;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Entry;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Expr;

/** Executes the actual emitted read-only effects. Explicit synthetic inputs grant no CK3/business credit. */
final class MarketEvolutionScriptContractTest {
    private static Request request(String contract, String position) {
        return new Request(2, Profile.MARKET_EVOLUTION, 1, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", contract, position, null, null), null, null);
    }

    @Test void newObservationProfileNeedsNoDebtAndNeverRelaxesLifecycleOrCapacity() {
        assertDoesNotThrow(() -> request(null, null));
        var actor = new ActorBinding(ActorMode.CURRENT_PLAYER, null);
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.LIFECYCLE, 1, actor,
                new Targets("2", "1", null, null, null, null), null, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.MARKET_EVOLUTION, 1, actor,
                new Targets("2", "1", null, null, "9", null), null, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.MARKET_EVOLUTION, 1, actor,
                new Targets("2", "1", null, null, null, null), null, ScaleTier.SMOKE));
        assertEquals(128, ScaleTier.SMOKE.coins());
        assertFalse(request(null, null).markers().stream().anyMatch(m -> m.contains("issuance_readback") || m.contains("claim_accounting")));
    }

    @Test void baselineAndRepeatedSameDayReadsDoNotInventCoinsFeesOrDailySamples() {
        Vm v = new Vm(request(null, null)); v.arm(); Node o = v.observer();
        String product = v.productState();
        v.observe(); v.observe();
        assertEquals(1, o.n("xfma_evolution_day_records"));
        assertEquals(0, o.n("xfma_daily_samples"));
        assertEquals(1, o.n("xfma_evolution_coin_records"));
        assertEquals(0, o.n("xfma_new_ai_issues_observed"));
        assertEquals(0, o.n("xfma_new_listings_observed"));
        assertEquals(0, o.n("xfma_expiry_available"));
        assertEquals(product, v.productState());
        assertEquals(1, v.logs.stream().filter(s -> s.endsWith("baseline_inventory_captured")).count());
        Node first = o.nodes("xfma_evolution_days").getFirst();
        v.exchange.put("xfm_fee_cents", 17); v.observe();
        assertEquals(0, first.n("xfma_first_fee_cents"));
        assertEquals(17, first.n("xfma_fee_cents"));
        assertEquals(1, o.n("xfma_evolution_day_records"));
    }

    @Test void unrelatedOrSystemAccountAndPerpetualTargetCannotBeArmedAsADatedPrivateBaseline() {
        Vm system = new Vm(request(null, null)); system.privateAccount.put("xfm_system_account", 1); system.arm();
        assertFalse(system.observer().vars.containsKey("xfma_ready"));
        assertTrue(system.logs.stream().anyMatch(s -> s.contains("followup_target_missing")));
        Vm foreign = new Vm(request(null, null)); foreign.privateAccount.ref("xfm_holder", foreign.character("other-holder", true)); foreign.arm();
        assertFalse(foreign.observer().vars.containsKey("xfma_ready"));
        Vm perpetual = new Vm(request("3", null));
        perpetual.exchange.nodes("xfm_futures_contracts").add(perpetual.node("perpetual", "xfm_futures_contract", true)
                .put("xfm_contract_id", 3).put("xfm_perpetual", 1).put("xfm_expiry_day", 0));
        perpetual.arm(); assertFalse(perpetual.observer().vars.containsKey("xfma_ready"));
    }

    @Test void newLandlessAiIssueAndRealListedStateUsePermanentIdentityAndFirstObservedRank() {
        Vm v = new Vm(request(null, null)); v.arm();
        Node ai = v.character("landless-ai", true); ai.gold = 5;
        Node privateAccount = v.account("private-ai", 33, ai, 0); privateAccount.put("xfm_system_account", 0); ai.ref("xfm_account", privateAccount);
        Node coin = v.coin("new-ai-coin", 2, ai, 0); coin.put("xfm_actual_raised_cents", 1600).put("xfm_external_raised_cents", 200);
        v.global("xfm_coin_registry").add(coin);
        v.exchange.put("xfm_next_coin_id", 2).put("xfm_registered_coin_count", 2).put("xfm_pending_coin_count", 1);
        v.day(7); String before = v.productState(); v.observe();
        Node sample = v.coinRecord(2);
        assertEquals(1, v.observer().n("xfma_new_ai_issues_observed"));
        assertEquals(1, v.observer().n("xfma_new_landless_ai_issues_observed"));
        assertEquals(0, sample.n("xfma_first_issuer_rank"));
        assertSame(ai, sample.node("xfma_first_original_issuer"));
        assertSame(privateAccount, sample.node("xfma_first_issuer_private_account"));
        assertEquals(100, sample.n("xfma_first_registration_paid_cents"));
        assertEquals(0, sample.n("xfma_actual_registration_transfer_verified"));
        assertEquals(before, v.productState());
        coin.put("xfm_listing_state", 1).put("xfm_listed_day", 8).put("xfm_trading_open", 1)
                .put("xfm_actual_raised_cents", 2000).put("xfm_external_raised_cents", 400);
        v.exchange.put("xfm_active_coin_count", 2).put("xfm_pending_coin_count", 0);
        ai.landed = true; ai.tier = 4;
        v.day(8); v.observe();
        assertEquals(1, v.observer().n("xfma_new_listings_observed"));
        assertEquals(0, sample.n("xfma_first_issuer_rank"), "first observation cannot become an invented issuance-time rank");
        assertEquals(1, sample.n("xfma_latest_listing_state"));
        assertEquals(2, sample.n("xfma_latest_coin_id"));
    }

    @Test void refundWitnessNeedsActualOriginalReservationStateAndMissingAmountsStayUnavailable() {
        Vm v = new Vm(request(null, null)); v.arm();
        Node ai = v.character("issuer", true), buyer = v.character("external", true);
        Node wallet = v.account("external-private", 40, buyer, 0);
        Node coin = v.coin("pending", 2, ai, 0);
        Node subscription = v.node("reservation", "xfm_finance_reservation", true)
                .put("xfm_reservation_id", 90).put("xfm_subscription_state", 0)
                .put("xfm_subscription_paid_cents", 400).put("xfm_remaining_cents", 400).ref("xfm_account", wallet);
        coin.nodes("xfm_subscriptions").add(subscription); v.global("xfm_coin_registry").add(coin);
        v.exchange.put("xfm_next_coin_id", 2).put("xfm_registered_coin_count", 2); v.day(7); v.observe();
        Node record = v.coinRecord(2);
        assertSame(subscription, record.nodes("xfma_subscription_sources").getFirst());
        coin.put("xfm_listing_state", 6).put("xfm_refund_news_recorded", 1);
        subscription.put("xfm_subscription_state", 3); subscription.vars.remove("xfm_remaining_cents");
        v.day(8); v.observe();
        assertEquals(0, record.n("xfma_subscriptions_available"));
        assertEquals(0, record.n("xfma_refund_readback_occurred"));
        assertEquals(1, record.n("xfma_fundraise_failed_occurred"), "failed fundraising does not invent a successful money refund");
        coin.vars.remove("xfm_registration_paid_cents"); v.observe();
        assertEquals(0, record.n("xfma_latest_registration_paid_cents_available"));
        assertFalse(record.vars.containsKey("xfma_latest_registration_paid_cents"), "missing financial value must not become zero");
        subscription.put("xfm_remaining_cents", 0); wallet.put("xfm_free_cents", 400);
        v.observe();
        assertEquals(1, record.n("xfma_subscriptions_available"));
        assertEquals(1, record.n("xfma_refund_readback_occurred"));
        assertEquals(1, v.observer().n("xfma_offer_refunds_observed"));
        assertEquals(0, record.n("xfma_actual_registration_transfer_verified"));
    }

    @Test void exactlyThirtyFiveConsecutiveDaysCompleteObservationWithoutRequiringRandomFeatures() {
        Vm v = new Vm(request(null, null)); v.arm();
        for (int day = 7; day <= 41; day++) { v.day(day); v.observe(); v.observe(); }
        Node o = v.observer();
        assertEquals(36, o.n("xfma_evolution_day_records"));
        assertEquals(35, o.n("xfma_daily_samples"));
        assertEquals(0, o.n("xfma_new_ai_issues_observed"));
        assertEquals(0, o.n("xfma_offer_refunds_observed"));
        assertEquals(0, o.n("xfma_expiry_available"));
        assertEquals(1, v.logs.stream().filter(s -> s.endsWith("35_daily_samples_observed")).count());
        assertFalse(v.logs.stream().anyMatch(s -> s.contains("ai_paid_issuance") || s.contains("surviving_claim")));
        v.day(42); v.observe();
        assertEquals(36, o.n("xfma_evolution_day_records"), "never append beyond the declared observation bound");
    }

    @Test void skippedFinancialDayOrAllocationFailureNeverCompletesAnObservationWindow() {
        Vm gap = new Vm(request(null, null)); gap.arm(); gap.day(8); gap.observe();
        for (int day = 9; day <= 41; day++) { gap.day(day); gap.observe(); }
        assertEquals(1, gap.observer().n("xfma_sample_gap"));
        assertFalse(gap.logs.stream().anyMatch(s -> s.endsWith("35_daily_samples_observed")));
        Vm failed = new Vm(request(null, null)); failed.failRecordCreation = true; failed.arm();
        assertEquals(1, failed.observer().n("xfma_record_allocation_failed"));
        assertTrue(failed.logs.stream().anyMatch(s -> s.contains("TEST FAIL evolution_day_record")));
        assertFalse(failed.logs.stream().anyMatch(s -> s.endsWith("baseline_inventory_captured")));
    }

    @Test void expiryDateReachedIsDistinctFromPendingOrActualTerminalReadback() {
        Vm v = new Vm(request("3", null));
        Node index = v.node("index", "xfm_oracle_index", true).put("xfm_index_id", 3);
        Node contract = v.node("dated", "xfm_futures_contract", true).put("xfm_contract_id", 3)
                .put("xfm_perpetual", 0).put("xfm_expiry_day", 30).put("xfm_status", 0).ref("xfm_coin", index);
        v.exchange.nodes("xfm_futures_contracts").add(contract);
        Node shortAccount = v.account("short-private", 44, v.character("short", true), 5);
        Node longReserve = v.node("long-reserve", "xfm_finance_reservation", true).put("xfm_remaining_cents", 20);
        Node shortReserve = v.node("short-reserve", "xfm_finance_reservation", true).put("xfm_remaining_cents", 20);
        Node position = v.node("paired-position", "xfm_futures_position", true).put("xfm_position_id", 12)
                .put("xfm_status", 0).put("xfm_last_settled_day", 6).ref("xfm_contract", contract)
                .ref("xfm_long_account", v.privateAccount).ref("xfm_short_account", shortAccount)
                .ref("xfm_long_reservation", longReserve).ref("xfm_short_reservation", shortReserve);
        contract.nodes("xfm_positions").add(position); v.arm();
        assertEquals(1, v.observer().n("xfma_expiry_available"));
        assertEquals(1, v.observer().n("xfma_expiry_contract_available"));
        assertEquals(1, v.observer().n("xfma_expiry_positions_available"));
        assertEquals(0, v.observer().n("xfma_expiry_due_occurred"));
        v.day(30); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_due_occurred"));
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
        position.put("xfm_pending_payment", 1).put("xfm_pending_kind", 4); v.observe();
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
        position.vars.remove("xfm_pending_payment"); position.put("xfm_status", 2).put("xfm_last_settled_day", 30);
        contract.nodes("xfm_positions").clear(); longReserve.put("xfm_remaining_cents", 0); shortReserve.put("xfm_remaining_cents", 0);
        String product = v.productState(); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_closed_readback_occurred"));
        assertEquals(12, v.observer().n("xfma_expiry_closed_position_id"));
        assertSame(position, v.observer().node("xfma_expiry_closed_position"));
        assertEquals(product, v.productState());
        assertEquals(30, contract.n("xfm_expiry_day"));
    }

    @Test void readableContractDatesDoNotInventReadablePositionsOrMissingContractStatus() {
        Vm v = new Vm(request("3", null));
        Node contract = v.node("empty-dated", "xfm_futures_contract", true).put("xfm_contract_id", 3)
                .put("xfm_perpetual", 0).put("xfm_expiry_day", 30).put("xfm_status", 0);
        v.exchange.nodes("xfm_futures_contracts").add(contract); v.arm();
        assertEquals(1, v.observer().n("xfma_expiry_contract_available"));
        assertEquals(0, v.observer().n("xfma_expiry_positions_available"));
        assertEquals(0, v.observer().n("xfma_expiry_available"));
        v.day(30); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_due_occurred"));
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
        Node position = v.node("date-only-position", "xfm_futures_position", true).put("xfm_position_id", 22)
                .put("xfm_status", 0).put("xfm_last_settled_day", 30).ref("xfm_contract", contract);
        contract.nodes("xfm_positions").add(position); contract.vars.remove("xfm_status"); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_contract_available"));
        assertEquals(1, v.observer().n("xfma_expiry_positions_sampled"));
        assertEquals(0, v.observer().n("xfma_watched_status_available"));
        assertEquals(0, v.observer().n("xfma_expiry_positions_available"));
        assertEquals(0, v.observer().n("xfma_expiry_available"));
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
    }

    @Test void finiteCoinCapacityIsRecheckedInsideTheIteratorAndTruncationIsExplicit() {
        Vm v = new Vm(request(null, null));
        for (int id = 2; id <= 63; id++) v.global("xfm_coin_registry").add(v.coin("old-" + id, id, v.player, 1));
        v.exchange.put("xfm_next_coin_id", 63).put("xfm_registered_coin_count", 63).put("xfm_active_coin_count", 63);
        v.arm(); assertEquals(63, v.observer().n("xfma_evolution_coin_records"));
        for (int id = 64; id <= 127; id++) v.global("xfm_coin_registry").add(v.coin("new-" + id, id, v.player, 0));
        v.exchange.put("xfm_next_coin_id", 127).put("xfm_registered_coin_count", 127); v.day(7); v.observe();
        assertEquals(64, v.observer().n("xfma_evolution_coin_records"));
        assertEquals(64, v.observer().n("xfma_evolution_coin_cursor"));
        assertEquals(0, v.observer().n("xfma_coin_coverage_complete"));
        assertEquals(0, v.observer().n("xfma_new_ai_issues_observed"));
        v.observe(); assertEquals(64, v.observer().n("xfma_evolution_coin_records"));
    }

    @Test void publicRegistryAddsOnlyTheNewCaseAndKeepsExistingFiniteWindowsAndStrictClaims() throws IOException {
        String shared = System.getProperty("xfm.shared.source");
        Path root = shared == null ? Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent()
                : Path.of(shared).toAbsolutePath().normalize();
        var products = FixtureEmitter.JSON.readTree(Files.readAllBytes(root.resolve("tools/ck3_mod_acceptance_products.json")));
        var cases = products.path("products").path("financial-markets").path("cases");
        Map<String, com.fasterxml.jackson.databind.JsonNode> indexed = new HashMap<>();
        cases.forEach(c -> assertNull(indexed.put(c.path("id").asText(), c)));
        assertEquals(10800, indexed.get("market-evolution").path("budgets").path("timeout").intValue());
        assertFalse(indexed.get("market-evolution").path("whole_product_acceptance_credit").booleanValue());
        var newCase = FixtureEmitter.JSON.readTree(Files.readAllBytes(root.resolve("tools/ck3_mod_acceptance_cases/financial_markets_market_evolution.json")));
        assertEquals(35, newCase.path("maximum_natural_days").intValue());
        assertFalse(newCase.path("whole_product_release_pass").booleanValue());
        assertEquals(3, readCase(root, "spot").path("maximum_natural_days").intValue());
        assertEquals(14, readCase(root, "derivatives").path("maximum_natural_days").intValue());
        assertEquals(35, readCase(root, "lifecycle").path("maximum_natural_days").intValue());
        assertEquals(395, readCase(root, "ai_capacity").path("maximum_natural_days").intValue());
    }

    @Test void subscriptionInspectionHasAHardHundredRecordBodyBoundAndReportsTruncation() {
        Vm v = new Vm(request(null, null));
        Node coin = v.global("xfm_coin_registry").getFirst();
        for (int id = 1; id <= 101; id++) coin.nodes("xfm_subscriptions").add(
                v.node("subscription-" + id, "xfm_finance_reservation", true)
                        .put("xfm_reservation_id", id).put("xfm_subscription_state", 3)
                        .put("xfm_subscription_paid_cents", 20).put("xfm_remaining_cents", 0)
                        .ref("xfm_account", v.privateAccount));
        String product = v.productState(); v.arm(); Node record = v.coinRecord(1);
        assertEquals(100, record.n("xfma_subscriptions_sampled"));
        assertEquals(100, record.nodes("xfma_subscription_sources").size());
        assertEquals(0, record.n("xfma_subscriptions_available"));
        assertEquals(0, v.observer().n("xfma_refund_available"));
        assertEquals(product, v.productState());
    }
    private static com.fasterxml.jackson.databind.JsonNode readCase(Path root, String key) throws IOException {
        return FixtureEmitter.JSON.readTree(Files.readAllBytes(root.resolve("tools/ck3_mod_acceptance_cases/financial_markets_" + key + ".json")));
    }

    private sealed interface Value permits NumberValue, Reference { }
    private record NumberValue(long value) implements Value { }
    private record Reference(Node node) implements Value { }
    private static final class Node {
        final String key, kind; final boolean product;
        final Map<String, Value> vars = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new LinkedHashMap<>();
        Node owner, title; boolean ai, adult = true, alive = true, landed; int tier; long gold;
        Node(String key, String kind, boolean product) { this.key = key; this.kind = kind; this.product = product; }
        Node put(String key, long value) { vars.put(key, new NumberValue(value)); return this; }
        Node ref(String key, Node value) { vars.put(key, new Reference(value)); return this; }
        long n(String key) { return ((NumberValue) java.util.Objects.requireNonNull(vars.get(key), key)).value(); }
        Node node(String key) { return ((Reference) java.util.Objects.requireNonNull(vars.get(key), key)).node(); }
        List<Node> nodes(String key) { return lists.computeIfAbsent(key, ignored -> new ArrayList<>()); }
    }
    /** No product effects, implicit missing=zero, random business decisions or financial ports exist. */
    private static final class Vm {
        final Request input; final Map<String, Block> program = new HashMap<>();
        final Map<String, Node> aliases = new HashMap<>(); final Map<String, List<Node>> globals = new HashMap<>();
        final List<Node> nodes = new ArrayList<>(); final List<String> logs = new ArrayList<>();
        final Node exchange, player, privateAccount; long nativeDate = 53144448; boolean failRecordCreation;
        Vm(Request input) {
            this.input = input;
            FollowupObservationScripts.render(input).forEach((name, bytes) -> {
                if (name.startsWith("common/scripted_effects/") || name.startsWith("common/scripted_triggers/") || name.startsWith("common/script_values/"))
                    for (Entry e : parse(new String(bytes, StandardCharsets.UTF_8)).entries())
                        assertNull(program.put(e.key(), (Block)e.value()), e.key());
            });
            player = character("player", false); exchange = node("exchange", "xfm_finance_exchange", true); exchange.owner = player;
            exchange.put("xfm_day", 6).put("xfm_next_coin_id", 1).put("xfm_registered_coin_count", 1)
                    .put("xfm_pending_coin_count", 0).put("xfm_active_coin_count", 1).put("xfm_new_listings_today", 0)
                    .put("xfm_fee_cents", 0).put("xfm_ai_work_today", 512).put("xfm_ai_decisions_today", 500)
                    .put("xfm_ai_count", 35000).put("xfm_futures_open_positions_count", 0);
            privateAccount = account("private", 2, player, 6000); privateAccount.put("xfm_system_account", 0); player.ref("xfm_account", privateAccount);
            global("xfm_account_registry").add(privateAccount);
            global("xfm_coin_registry").add(coin("baseline-coin", 1, player, 1));
            Node fund = account("fund", 1, player, 0); exchange.ref("xfm_default_fund_account", fund);
        }
        Node node(String key, String kind, boolean product) { Node n = new Node(key, kind, product); nodes.add(n); return n; }
        Node character(String key, boolean ai) { Node n = node(key, "character", true); n.ai = ai; n.gold = 5; return n; }
        Node account(String key, long id, Node holder, long free) { return node(key, "xfm_finance_account", true).put("xfm_account_id", id).put("xfm_free_cents", free).put("xfm_reserved_cents", 0).ref("xfm_holder", holder); }
        Node coin(String key, long id, Node issuer, long state) {
            Node project = account(key + "-project", 1000 + id, issuer, 0);
            Node coin = node(key, "xfm_finance_coin", true).put("xfm_coin_id", id).put("xfm_listing_state", state)
                    .put("xfm_supply_units", 15000).put("xfm_trading_open", state == 0 ? 0 : 1)
                    .put("xfm_asset_age", 0).put("xfm_offer_age", 0).put("xfm_service_tier", 1)
                    .put("xfm_registration_paid_cents", 100).put("xfm_minimum_raised_cents", 2000)
                    .put("xfm_actual_raised_cents", state == 0 ? 0 : 2000).put("xfm_external_raised_cents", state == 0 ? 0 : 400)
                    .put("xfm_unresolved_claim_count", 0)
                    .ref("xfm_original_issuer", issuer).ref("xfm_controller", issuer).ref("xfm_issuer_account", project);
            if (state != 0) coin.put("xfm_listed_day", 0);
            return coin;
        }
        List<Node> global(String name) { return globals.computeIfAbsent(name, ignored -> new ArrayList<>()); }
        void arm() { run(input.prefix() + "_arm_effect", player, null); }
        void observe() { run(input.prefix() + "_observe_effect", observer(), null); }
        Node observer() { return player.node(input.prefix() + "_story"); }
        Node coinRecord(long id) { return observer().nodes("xfma_evolution_coins").stream().filter(n -> n.n("xfma_first_coin_id") == id).findFirst().orElseThrow(); }
        void day(long day) { nativeDate += Math.multiplyExact(day - exchange.n("xfm_day"), 24); exchange.put("xfm_day", day); }
        String productState() {
            StringBuilder s = new StringBuilder();
            for (Node n : nodes) if (n.product) {
                s.append(n.key).append(':').append(n.gold).append(':').append(n.ai).append(':').append(n.alive).append(':').append(n.adult).append(':').append(n.landed).append(':').append(n.tier);
                n.vars.forEach((k,v) -> { if (!k.startsWith("xfma_")) s.append('|').append(k).append('=').append(v instanceof NumberValue x ? x.value() : ((Reference)v).node().key); });
                n.lists.forEach((k,v) -> { if (!k.startsWith("xfma_")) s.append('|').append(k).append('=').append(v.stream().map(x -> x.key).toList()); });
                s.append('\n');
            }
            return s.toString();
        }
        void run(String name, Node here, Node prev) { execute(java.util.Objects.requireNonNull(program.get(name), name), here, prev); }
        void execute(Block b, Node here, Node prev) {
            boolean chain = false, taken = false;
            for (Entry e : b.entries()) {
                if (e.key().equals("limit")) continue;
                if (e.key().equals("if") || e.key().equals("else_if")) {
                    boolean first = e.key().equals("if"); assertTrue(first || chain, "orphan else_if");
                    if (first) { chain = true; taken = false; }
                    Block child = (Block)e.value();
                    if (!taken && matches(child.block("limit"), here, prev)) { execute(child, here, prev); taken = true; }
                    continue;
                }
                if (e.key().equals("else")) { assertTrue(chain, "orphan else"); if (!taken) execute((Block)e.value(), here, prev); chain = false; continue; }
                chain = false;
                String key = e.key();
                if (key.equals("save_scope_as")) { aliases.put(atom(e.value()), here); continue; }
                if (key.equals("clear_saved_scope")) { aliases.remove(atom(e.value())); continue; }
                if (key.equals("set_variable") || key.equals("change_variable")) {
                    Block child = (Block)e.value(); String name = atom(child.blockOrAtom("name"));
                    assertTrue(name.startsWith("xfma_"), "product mutation " + name);
                    if (key.equals("set_variable")) here.vars.put(name, requiredValue(child.blockOrAtom("value"), here, prev));
                    else {
                        Entry operation = child.entries().stream().filter(x -> !x.key().equals("name")).findFirst().orElseThrow();
                        long old = here.n(name), amount = number(operation.value(), here, prev);
                        here.put(name, operation.key().equals("add") ? Math.addExact(old, amount) : Math.subtractExact(old, amount));
                    }
                    continue;
                }
                if (key.equals("remove_variable")) { String name = atom(e.value()); assertTrue(name.startsWith("xfma_")); here.vars.remove(name); continue; }
                if (key.equals("clear_variable_list")) { String name = atom(e.value()); assertTrue(name.startsWith("xfma_")); here.nodes(name).clear(); continue; }
                if (key.equals("add_to_variable_list")) {
                    Block child = (Block)e.value(); String name = atom(child.blockOrAtom("name")); assertTrue(name.startsWith("xfma_"));
                    Node target = ref(requiredValue(child.blockOrAtom("target"), here, prev));
                    if (!here.nodes(name).contains(target)) here.nodes(name).add(target); continue;
                }
                if (key.equals("create_story")) {
                    Block child = (Block)e.value(); String type = atom(child.blockOrAtom("type"));
                    assertTrue(type.startsWith("xfma_"));
                    if (failRecordCreation && FollowupObservationScripts.marketEvolutionRecordTypes().contains(type)) continue;
                    Node created = node("observation-" + nodes.size(), type, false); created.owner = here;
                    aliases.put(atom(child.blockOrAtom("save_scope_as")), created); continue;
                }
                if (key.equals("debug_log")) { logs.add(unquote(atom(e.value()))); continue; }
                if (key.equals("every_in_list") || key.equals("every_in_global_list") || key.equals("ordered_in_list") || key.equals("ordered_in_global_list")) {
                    Block child = (Block)e.value(); String list = atom(child.blockOrAtom("variable"));
                    List<Node> selected = new ArrayList<>(key.contains("global") ? global(list) : here.lists.getOrDefault(list, List.of()));
                    Block predicate = optionalBlock(child, "limit");
                    if (predicate != null) selected.removeIf(n -> !matches(predicate, n, here));
                    if (key.startsWith("ordered")) {
                        Expr order = child.blockOrAtom("order_by"); selected.sort(Comparator.comparingLong((Node n) -> number(order, n, here)).reversed());
                        int maximum = Math.toIntExact(number(child.blockOrAtom("max"), here, prev));
                        if (selected.size() > maximum) selected = new ArrayList<>(selected.subList(0, maximum));
                    }
                    Block body = without(child, "variable", "limit", "order_by", "max", "check_range_bounds");
                    for (Node n : selected) execute(body, n, here); continue;
                }
                if (program.containsKey(key)) { run(key, here, prev); continue; }
                Value target = resolve(key, here, prev);
                if (e.value() instanceof Block child && target instanceof Reference n) { execute(child, n.node(), here); continue; }
                throw new AssertionError("unsupported emitted effect " + key);
            }
        }
        boolean matches(Block b, Node here, Node prev) { return b.entries().stream().allMatch(e -> check(e, here, prev)); }
        boolean check(Entry e, Node here, Node prev) {
            String key = e.key();
            if (key.equals("AND")) return matches((Block)e.value(), here, prev);
            if (key.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, here, prev));
            if (key.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, here, prev));
            if (key.equals("has_variable")) return here.vars.containsKey(atom(e.value()));
            if (key.equals("exists")) return resolve(atom(e.value()), here, prev) != null;
            if (key.equals("story_type")) return here.kind.equals(atom(e.value()));
            if (key.equals("is_target_in_variable_list")) {
                Block child = (Block)e.value(); Value target = value(child.blockOrAtom("target"), here, prev);
                return target instanceof Reference n && here.lists.getOrDefault(atom(child.blockOrAtom("name")), List.of()).contains(n.node());
            }
            if (key.equals("any_in_list") || key.equals("any_in_global_list")) {
                Block child = (Block)e.value(); String name = atom(child.blockOrAtom("variable"));
                return (key.contains("global") ? global(name) : here.lists.getOrDefault(name, List.of())).stream().anyMatch(n -> matches(without(child, "variable"), n, here));
            }
            if (program.containsKey(key)) return matches(program.get(key), here, prev);
            Value left = resolve(key, here, prev);
            if (left == null) return false;
            if (e.value() instanceof Block child && left instanceof Reference n) return matches(child, n.node(), here);
            Value right = value(e.value(), here, prev);
            if (left == null || right == null) return false;
            if (left instanceof Reference a && right instanceof Reference c) return e.operator().equals("=") ? a.node() == c.node() : e.operator().equals("!=") && a.node() != c.node();
            if (!(left instanceof NumberValue a) || !(right instanceof NumberValue c)) return false;
            return switch (e.operator()) {
                case "=" -> a.value() == c.value(); case "!=" -> a.value() != c.value();
                case ">" -> a.value() > c.value(); case "<" -> a.value() < c.value();
                case ">=" -> a.value() >= c.value(); case "<=" -> a.value() <= c.value();
                default -> throw new AssertionError("unknown comparison " + e.operator());
            };
        }
        Value requiredValue(Expr e, Node here, Node prev) { return java.util.Objects.requireNonNull(value(e, here, prev), "missing emitted operand " + e); }
        long number(Expr e, Node here, Node prev) { return ((NumberValue)requiredValue(e, here, prev)).value(); }
        Value value(Expr e, Node here, Node prev) {
            if (e instanceof Atom a) return resolve(a.word(), here, prev);
            long sum = 0;
            for (Entry operation : ((Block)e).entries()) {
                long operand = number(operation.value(), here, prev);
                sum = switch (operation.key()) {
                    case "value" -> operand; case "add" -> Math.addExact(sum, operand); case "subtract" -> Math.subtractExact(sum, operand);
                    default -> throw new AssertionError("unsupported observation arithmetic " + operation.key());
                };
            }
            return new NumberValue(sum);
        }
        Value resolve(String text, Node here, Node prev) {
            if (text.matches("-?[0-9]+")) return new NumberValue(Long.parseLong(text));
            if (text.equals("yes")) return new NumberValue(1); if (text.equals("no")) return new NumberValue(0);
            if (text.equals("current_date")) return new NumberValue(nativeDate);
            List<String> tiers = List.of("tier_barony", "tier_county", "tier_duchy", "tier_kingdom", "tier_empire");
            if (tiers.contains(text)) return new NumberValue(tiers.indexOf(text) + 1L);
            if (program.containsKey(text)) return value(program.get(text), here, prev);
            String[] parts = text.split("\\.");
            assertTrue(parts[0].startsWith("var:") || parts[0].startsWith("scope:") || parts[0].startsWith("global_var:")
                    || List.of("this", "prev", "story_owner", "primary_title", "gold", "is_ai", "is_adult", "is_alive", "is_landed", "highest_held_title_tier").contains(parts[0]),
                    "unsupported emitted reference " + text);
            Value current = new Reference(here);
            for (int i = 0; i < parts.length; i++) {
                String part = parts[i];
                if (i == 0 && part.equals("global_var:xfm_exchange")) { current = new Reference(exchange); continue; }
                if (i == 0 && part.startsWith("scope:")) { Node n = aliases.get(part.substring(6)); current = n == null ? null : new Reference(n); continue; }
                if (i == 0 && part.equals("prev")) { current = prev == null ? null : new Reference(prev); continue; }
                if (i == 0 && part.equals("this")) continue;
                if (!(current instanceof Reference reference)) return null;
                Node n = reference.node();
                if (part.startsWith("var:")) current = n.vars.get(part.substring(4));
                else current = switch (part) {
                    case "story_owner" -> n.owner == null ? null : new Reference(n.owner);
                    case "primary_title" -> n.title == null ? null : new Reference(n.title);
                    case "gold" -> new NumberValue(n.gold);
                    case "is_ai" -> new NumberValue(n.ai ? 1 : 0); case "is_adult" -> new NumberValue(n.adult ? 1 : 0);
                    case "is_alive" -> new NumberValue(n.alive ? 1 : 0); case "is_landed" -> new NumberValue(n.landed ? 1 : 0);
                    case "highest_held_title_tier" -> new NumberValue(n.tier);
                    default -> null;
                };
            }
            return current;
        }
        private static Node ref(Value value) { return ((Reference)value).node(); }
        private static String atom(Expr e) { return ((Atom)e).word(); }
        private static String unquote(String text) { return text.startsWith("\"") && text.endsWith("\"") ? text.substring(1, text.length() - 1) : text; }
        private static Block optionalBlock(Block b, String key) { return b.entries().stream().filter(e -> e.key().equals(key)).map(e -> (Block)e.value()).findFirst().orElse(null); }
        private static Block without(Block b, String... keys) { return new Block(b.entries().stream().filter(e -> !List.of(keys).contains(e.key())).toList()); }
    }
}
