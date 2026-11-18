package org.xar.ck3.markets.futures;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.Clausewitz.Value;

/** Executes actual selected-series projection, funding guards, legal-owner refresh and normal
 * GUI -> reduce -> real order/reservation producers. Engine random/story allocation/config are explicit
 * ports; matching only records invocation and never invents a fill. This is not CK3 or a saved game. */
final class FuturesBookUiScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final Path REFERENCE = SOURCE;
    private static final List<String> INPUTS = List.of(
        "scripted_effects/xfm_market_ui_futures_book.txt",
        "scripted_triggers/xfm_market_futures_book_triggers.txt",
        "script_values/xfm_market_futures_book_values.txt",
        "scripted_guis/xfm_market_futures_book.txt",
        "scripted_guis/xfm_market_futures_positions.txt",
        "scripted_guis/xfm_market_futures_stops.txt",
        "scripted_effects/xfm_futures_margin.txt",
        "scripted_effects/xfm_futures_reduce.txt",
        "scripted_effects/xfm_finance_policy.txt",
        "scripted_effects/xfm_issuer_governance.txt",
        "scripted_effects/xfm_finance_cash.txt",
        "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_reserve.txt",
        "scripted_triggers/xfm_finance_triggers.txt",
        "scripted_triggers/xfm_futures_triggers.txt",
        "script_values/xfm_finance_values.txt",
        "script_values/xfm_futures_values.txt",
        "script_values/xfm_numeric_comparison_values.txt",
        "script_values/xfm_config_values.txt");
    public static void main(String[] ignored) throws Exception {
        int passed = 0;
        for (var method : FuturesBookUiScriptContractTest.class.getDeclaredMethods()) {
            if (!method.isAnnotationPresent(Test.class)) continue;
            try { method.invoke(new FuturesBookUiScriptContractTest()); passed++; System.out.println("PASS " + method.getName()); }
            catch (java.lang.reflect.InvocationTargetException error) { throw new AssertionError("FAIL " + method.getName(), error.getCause()); }
        }
        System.out.println("PRODUCTION_SUBSET groups=" + passed + " passed=" + passed + " CK3_NOT_RUN");
    }
    private record Market(Vm vm, Node actor, Node asset, Node contract) { }
    private static Market market() throws IOException {
        Vm v = vm(); Node a = v.node("viewer", ""); a.ai = false;
        Node own = primary(v, a, 10000); a.put("xfm_active_account", own); a.put("xfm_ui_step", 1);
        Node asset = v.asset("asset"), contract = v.contract("series-77", asset, 0, 30);
        contract.put("xfm_contract_id", 77); a.put("xfm_selected_coin", asset); a.put("xfm_futures_contract", contract);
        a.put("xfm_order_limit_cents", 88); return new Market(v, a, asset, contract);
    }
    private static Node quote(Market m, String name, Node contract, int side, int price, int lots, int id) {
        Vm v = m.vm; Node holder = v.node(name + "-holder", ""), account = v.account(name + "-wallet", holder, 0);
        v.order(name, contract, account, side, price); Node order = v.nodes.get(name), reserve = order.ref("xfm_reservation");
        order.put("xfm_order_id", id); order.put("xfm_leverage", 1); order.put("xfm_reserve_price_cents", 120);
        order.put("xfm_filled_gross_cents", 0); order.put("xfm_fee_paid_cents", 0); order.put("xfm_remaining_lots", lots);
        long required = lots * 120L + (long)Math.ceil(lots * 120 * 0.003);
        reserve.put("xfm_remaining_cents", required); account.put("xfm_reserved_cents", required); return order;
    }
    private static void refresh(Market m) { m.vm.runGui("xfm_market_futures_book_refresh_gui", m.actor); }
    private static List<Node> bids(Market m) { return m.actor.list("xfm_ui_futures_bids"); }
    private static List<Node> asks(Market m) { return m.actor.list("xfm_ui_futures_asks"); }

    @Test void twoSameAssetSeriesHaveDifferentRealBooksAndExecutionSnapshots() throws IOException {
        Market m = market(); Node b = m.vm.contract("series-88", m.asset, 0, 60); b.put("xfm_contract_id", 88);
        Node aBid = quote(m, "a-bid", m.contract, 1, 94, 2, 1), bAsk = quote(m, "b-ask", b, 2, 114, 3, 2);
        m.contract.put("xfm_last_execution_cents", 97); m.contract.put("xfm_execution_day", 0); m.contract.put("xfm_execution_lots", 8);
        refresh(m); assertEquals(List.of(aBid), bids(m)); assertTrue(asks(m).isEmpty());
        assertSame(m.contract, m.actor.ref("xfm_ui_futures_book_contract")); assertEquals(97, m.actor.integer("xfm_ui_futures_execution_cents"));
        m.actor.put("xfm_futures_contract", b); refresh(m);
        assertTrue(bids(m).isEmpty()); assertEquals(List.of(bAsk), asks(m)); assertSame(b, m.actor.ref("xfm_ui_futures_book_contract"));
        assertEquals(0, m.actor.integer("xfm_ui_futures_execution_present")); assertEquals(88, m.actor.integer("xfm_order_limit_cents"));
        assertEquals(77, m.contract.integer("xfm_contract_id")); assertEquals(88, b.integer("xfm_contract_id")); assertEquals(0, m.vm.created("xfm_futures_contract"));
    }
    @Test void onlyFundedRemainingPartialOrdersSurviveBlockedCancelledWrongSeriesAndSelf() throws IOException {
        Market m = market(); Node valid = quote(m, "partial", m.contract, 1, 99, 1, 1); valid.put("xfm_status", 1);
        valid.put("xfm_filled_gross_cents", 200); valid.put("xfm_fee_paid_cents", 1);
        Node noMoney = quote(m, "underfunded", m.contract, 1, 100, 2, 2); noMoney.ref("xfm_reservation").put("xfm_remaining_cents", 1);
        Node frozen = quote(m, "frozen", m.contract, 2, 101, 1, 3); frozen.ref("xfm_account").put("xfm_account_frozen", 1);
        Node cancelled = quote(m, "cancelled", m.contract, 1, 102, 1, 4); cancelled.put("xfm_status", 3);
        Node other = m.vm.contract("other-series", m.asset, 0, 60); Node foreign = quote(m, "wrong-series", other, 1, 103, 1, 5); m.contract.list("xfm_orders").add(foreign);
        Node self = quote(m, "self", m.contract, 1, 104, 1, 6); self.ref("xfm_account").put("xfm_holder", m.actor);
        Node reduced = quote(m, "reduce", m.contract, 2, 105, 1, 7); reduced.put("xfm_reduce_order", 1);
        Node mismatch = quote(m, "reserve-mismatch", m.contract, 1, 106, 1, 8); mismatch.ref("xfm_reservation").put("xfm_account", m.actor.ref("xfm_active_account"));
        refresh(m); assertEquals(List.of(valid), bids(m)); assertTrue(asks(m).isEmpty());
        assertEquals(1, m.actor.integer("xfm_ui_futures_bid_lots")); assertEquals(0, m.actor.integer("xfm_ui_futures_ask_lots"));
        assertEquals(0, valid.ref("xfm_account").integer("xfm_free_cents")); // Real frozen funds, not free cash, make this order eligible.
        valid.put("xfm_status", 3); m.vm.scopes.put("xfm_ui_item", valid);
        assertFalse(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor));
        refresh(m); assertTrue(bids(m).isEmpty()); assertEquals(0, m.actor.integer("xfm_ui_futures_bid_lots"));
    }
    @Test void actualControllerRefreshExcludesNewlyOwnedProjectAndRestoresExternalOwner() throws IOException {
        Market m = market(); Node order = quote(m, "political", m.contract, 1, 100, 1, 1), account = order.ref("xfm_account");
        Node issuer = m.vm.node("bound-coin", "xfm_finance_coin"), title = m.vm.node("title", "landed_title");
        issuer.put("xfm_entity_type", 4); issuer.put("xfm_bound_entity", title); issuer.put("xfm_controller", account.ref("xfm_holder"));
        issuer.put("xfm_issuer_account", account); title.links.put("holder", account.ref("xfm_holder")); account.put("xfm_legal_entity", issuer);
        refresh(m); assertEquals(List.of(order), bids(m));
        title.links.put("holder", m.actor); refresh(m); assertTrue(bids(m).isEmpty()); assertSame(m.actor, account.ref("xfm_beneficial_owner"));
        Node outsider = m.vm.node("new-controller", ""); title.links.put("holder", outsider); refresh(m); assertEquals(List.of(order), bids(m));
        assertSame(outsider, account.ref("xfm_holder"));
    }
    @Test void exactPriceFifoTopFiveHasBoundedRowsAndFullEligibleDepth() throws IOException {
        Market m = market(); List<Node> all = new ArrayList<>();
        for (int i = 0; i < 6; i++) all.add(quote(m, "bid-" + i, m.contract, 1, i == 0 ? 99 : 100, 1, 20 - i));
        quote(m, "ask-1", m.contract, 2, 110, 2, 21); Node firstAsk = quote(m, "ask-2", m.contract, 2, 109, 1, 22);
        refresh(m); assertEquals(List.of(all.get(5), all.get(4), all.get(3), all.get(2), all.get(1)), bids(m));
        assertSame(firstAsk, asks(m).getFirst()); assertEquals(6, m.actor.integer("xfm_ui_futures_bid_lots"));
        assertEquals(3, m.actor.integer("xfm_ui_futures_ask_lots")); assertTrue(m.actor.list("xfm_ui_futures_candidates").isEmpty());
        assertEquals(0, m.vm.historyVisits); assertEquals(64, m.vm.integerValue("xfm_config_coin_order_capacity_value", m.actor));
    }
    @Test void staleOracleClosedMarketAndExpiredSeriesNeverSubstituteSpotOrMarkForExecution() throws IOException {
        Market m = market(); quote(m, "bid", m.contract, 1, 100, 1, 1); refresh(m);
        assertEquals(0, m.actor.integer("xfm_ui_futures_execution_present")); assertFalse(m.actor.vars.containsKey("xfm_ui_futures_execution_cents"));
        m.asset.put("xfm_oracle_day", 0); refresh(m); assertTrue(bids(m).isEmpty());
        m.asset.put("xfm_oracle_day", 1); m.asset.put("xfm_derivatives_reduce_only", 1); refresh(m); assertTrue(bids(m).isEmpty());
        m.asset.put("xfm_derivatives_reduce_only", 0); m.vm.open = false; refresh(m); assertTrue(bids(m).isEmpty());
        m.vm.open = true; m.contract.put("xfm_expiry_day", 1); refresh(m); assertTrue(bids(m).isEmpty());
        m.contract.put("xfm_expiry_day", 30); m.contract.put("xfm_last_execution_cents", 105); m.contract.put("xfm_execution_day", 0); m.contract.put("xfm_execution_lots", 7);
        refresh(m); assertEquals(105, m.actor.integer("xfm_ui_futures_execution_cents")); assertEquals(0, m.actor.integer("xfm_ui_futures_execution_day")); assertEquals(7, m.actor.integer("xfm_ui_futures_execution_lots"));
        m.actor.put("xfm_selected_coin", m.vm.asset("different-index")); m.vm.run("xfm_market_ui_futures_book_effect", m.actor);
        assertEquals(0, m.actor.integer("xfm_ui_futures_book_ready")); assertTrue(bids(m).isEmpty()); assertFalse(m.actor.vars.containsKey("xfm_ui_futures_book_contract"));
    }
    @Test void inheritedHolderCanSelectThenReduceAtThisGuiLimitWithoutAnyOpeningOrSpotCopy() throws IOException {
        Market m = market(); Node inherited = m.vm.account("inherited-stable-99", m.actor, 10000); inherited.put("xfm_account_id", 99); m.actor.put("xfm_active_account", inherited);
        Node other = m.vm.node("old-counterparty", ""), otherAccount = m.vm.account("old-counterparty-account", other, 1000);
        Node position = m.vm.node("old-position", "xfm_futures_position"); position.put("xfm_contract", m.contract); position.put("xfm_long_account", inherited); position.put("xfm_short_account", otherAccount);
        position.put("xfm_status", 0); position.put("xfm_lots", 3); position.put("xfm_mark_cents", 96); position.put("xfm_long_stop_cents", 80); position.put("xfm_long_take_profit_cents", 115);
        Node longReserve = m.vm.node("old-long-reserve", "xfm_finance_reservation"), shortReserve = m.vm.node("old-short-reserve", "xfm_finance_reservation");
        position.put("xfm_long_reservation", longReserve); position.put("xfm_short_reservation", shortReserve);
        m.actor.put("xfm_futures_limit_cents", 42); m.vm.scopes.put("xfm_ui_item", position);
        m.vm.runGui("xfm_market_select_futures_position_gui", m.actor); m.actor.put("xfm_ui_step", 7);
        m.vm.runGui("xfm_market_futures_limit_up_gui", m.actor); assertEquals(107, m.actor.integer("xfm_futures_limit_cents"));
        m.vm.runGui("xfm_market_futures_reduce_gui", m.actor); assertEquals(1, m.actor.integer("xfm_futures_result"));
        Node close = m.contract.list("xfm_orders").getLast(); assertEquals(107, close.integer("xfm_limit_cents")); assertSame(inherited, close.ref("xfm_account"));
        assertEquals(88, m.actor.integer("xfm_order_limit_cents")); assertEquals(1, close.ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(0, m.vm.created("xfm_futures_position")); assertEquals(1, m.vm.matchCalls); // Order exists; no synthetic fill.
        m.actor.put("xfm_ui_step", 1); m.vm.runGui("xfm_market_futures_stop_up_gui", m.actor); m.vm.runGui("xfm_market_futures_take_profit_up_gui", m.actor); m.vm.runGui("xfm_market_futures_set_stops_gui", m.actor);
        assertEquals(81, position.integer("xfm_long_stop_cents")); assertEquals(116, position.integer("xfm_long_take_profit_cents")); assertEquals(107, m.actor.integer("xfm_futures_limit_cents"));
    }
    @Test void normalUiReferencesRefreshHooksAndInventoryCloseWithoutAnyDailyHistoryHook() throws IOException {
        var report = org.xar.ck3.markets.build.ContentValidator.validate(SOURCE);
        assertTrue(report.runtimeFiles().containsAll(List.of(
            "common/script_values/xfm_market_futures_book_values.txt", "common/scripted_triggers/xfm_market_futures_book_triggers.txt",
            "common/scripted_effects/xfm_market_ui_futures_book.txt", "common/scripted_guis/xfm_market_futures_book.txt",
            "gui/xfm_market_futures_book.gui", "localization/english/xfm_market_futures_book_l_english.yml",
            "localization/simp_chinese/xfm_market_futures_book_l_simp_chinese.yml")));
        String opening = Files.readString(SOURCE.resolve("common/scripted_guis/xfm_market_futures_open.txt"));
        assertFalse(opening.contains("xfm_order_limit_cents")); assertEquals(3, opening.split("xfm_market_ui_futures_book_effect = yes", -1).length - 1);
        String gui = Files.readString(SOURCE.resolve("gui/xfm_market_futures.gui")); assertTrue(gui.contains("xfm_market_futures_book_panel = {}")); assertFalse(gui.contains("xfm_market_price_up"));
        String book = Files.readString(SOURCE.resolve("common/scripted_effects/xfm_market_ui_futures_book.txt"));
        for (String forbidden : List.of("every_living_character", "xfm_futures_contracts", "xfm_finance_reserve_effect", "add_gold", "trigger_event")) assertFalse(book.contains(forbidden), forbidden);
        String loc = Files.readString(SOURCE.resolve("localization/english/xfm_market_futures_book_l_english.yml")); assertTrue(loc.contains("daily VWAP")); assertTrue(loc.contains("Closing and own/related orders are excluded"));
        for (String dayFile : List.of("xfm_futures_daily_index.txt", "xfm_futures_settlement.txt")) assertFalse(Files.readString(SOURCE.resolve("common/scripted_effects/" + dayFile)).contains("xfm_market_ui_futures_book_effect"));
    }
    private static Vm vm() throws IOException {
        Map<String, Block> definitions = new LinkedHashMap<>();
        for (String input : INPUTS) {
            Path p = SOURCE.resolve("common").resolve(input);
            if (!Files.exists(p)) p = REFERENCE.resolve("common").resolve(input);
            for (Entry e : Clausewitz.parse(Files.readString(p)).entries()) {
                Block b = e.value() instanceof Block block ? block : new Block(List.of(new Entry("value", "=", e.value())));
                if (definitions.put(e.key(), b) != null) throw new IllegalArgumentException("duplicate " + e.key());
            }
        }
        return new Vm(definitions);
    }
    private static Node ticket(Vm v, String gold) {
        Node a = v.node("actor", ""); a.gold = new BigDecimal(gold);
        Node asset = v.asset("asset"), contract = v.contract("ticket-contract", asset, 1, 0);
        a.put("xfm_selected_coin", asset); a.put("xfm_futures_contract", contract);
        a.put("xfm_futures_perpetual", 1); a.put("xfm_futures_expiry_day", 0);
        a.put("xfm_futures_side", 1); a.put("xfm_futures_leverage", 1);
        a.put("xfm_futures_limit_cents", 100); a.put("xfm_futures_lots", 1);
        return a;
    }
    private static Node primary(Vm v, Node actor, int free) { Node p = v.account("private", actor, free); actor.put("xfm_account", p); return p; }
    private sealed interface Datum permits NumberDatum, TextDatum, Node { }
    private record NumberDatum(BigDecimal value) implements Datum { }
    private record TextDatum(String text) implements Datum { }
    private static final class Node implements Datum {
        final String id, type;
        final Map<String, Datum> vars = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new HashMap<>();
        final Set<String> traits = new HashSet<>(); final Map<String, Node> links = new HashMap<>();
        BigDecimal gold = BigDecimal.ZERO; Node owner; boolean ai = true, alive = true, adult = true, ended;
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
        final Map<String, List<Node>> globalLists = new HashMap<>();
        final Node exchange, custodian;
        final List<String> trace = new ArrayList<>(); String failType = ""; boolean open = true, randomEnabled = true; int sequence, matchCalls, historyVisits, maxDiscoveryEntries;
        Vm(Map<String, Block> program) {
            this.program = program; custodian = node("technical-owner", ""); exchange = node("exchange", "xfm_finance_exchange"); exchange.owner = custodian;
            exchange.put("xfm_day", 1); exchange.put("xfm_ai_seeded", 1); exchange.put("xfm_next_account_id", 0); exchange.put("xfm_next_reservation_id", 0);
            exchange.put("xfm_next_futures_contract_id", 0); exchange.put("xfm_next_futures_position_id", 0);
            exchange.put("xfm_active_orders_count", 0); exchange.put("xfm_futures_open_positions_count", 0);
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
            return sum.stripTrailingZeros();
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
            if (text.equals("story_owner")) return f.here().owner;
            if (text.startsWith("scope:")) return scopes.get(text.substring(6));
            if (text.startsWith("var:")) return f.here().vars.get(text.substring(4));
            if (text.equals("gold")) return new NumberDatum(f.here().gold);
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
        boolean test(Block b, Frame f) { for (Entry e : b.entries()) if (!check(e, f)) { if (trace.size() > 40) trace.removeFirst(); trace.add(f.here().id + ":" + e.key() + e.operator() + (e.value() instanceof Atom a ? a.token() : "{...}")); return false; } return true; }
        boolean check(Entry e, Frame f) {
            String k = e.key();
            if (k.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, f));
            if (k.equals("AND")) return test((Block)e.value(), f);
            if (k.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, f));
            if (k.equals("exists")) return resolve(atom(e.value()), f) != null;
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("has_trait")) return f.here().traits.contains(atom(e.value()));
            if (k.equals("has_game_rule")) return false; // explicit default-rules port
            if (k.equals("xfm_config_futures_open_trigger")) return open;
            if (k.equals("any_in_list")) {
                Block b = (Block)e.value(); for (Node n : list(f.here(), atom(field(b, "variable")))) if (test(without(b, "variable"), f.enter(n))) return true; return false;
            }
            if (k.endsWith("_trigger") && program.containsKey(k)) return test(definition(k), f);
            if (e.value() instanceof Block child && !(resolve(k, f) instanceof NumberDatum)) {
                Datum scope = resolve(k, f); return scope instanceof Node n && test(child, f.enter(n));
            }
            Datum left = resolve(k, f), right = evaluate(e.value(), f);
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
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("remove_variable")) { f.here().vars.remove(atom(e.value())); continue; }
                if (k.equals("clear_variable_list")) { f.here().list(atom(e.value())).clear(); continue; }
                if (k.equals("while")) {
                    Block a = (Block)e.value(); int bound = 0;
                    while (test(a.block("limit"), f)) { if (++bound > 10) throw new IllegalArgumentException("UI top-five loop exceeded bound"); execute(without(a, "limit"), f); }
                    continue;
                }
                if (k.equals("ordered_in_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> ordered = new ArrayList<>();
                    for (Node n : list(f.here(), name)) if (test(a.block("limit"), f.enter(n))) ordered.add(n);
                    ordered.sort((left, right) -> number(evaluate(field(a, "order_by"), f.enter(right))).compareTo(number(evaluate(field(a, "order_by"), f.enter(left)))));
                    int count = Math.min(ordered.size(), number(evaluate(field(a, "max"), f)).intValueExact());
                    Block effect = without(without(without(without(without(a, "variable"), "limit"), "order_by"), "max"), "check_range_bounds");
                    for (int i = 0; i < count; i++) execute(effect, f.enter(ordered.get(i)));
                    continue;
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
                if (k.equals("create_story")) {
                    Block a = (Block)e.value(); String type = atom(field(a, "type"));
                    if (!type.equals(failType)) { Node created = node("created-" + ++sequence, type); created.owner = f.here(); scopes.put(atom(field(a, "save_scope_as")), created); }
                    continue;
                }
                if (k.equals("end_story")) { f.here().ended = true; continue; }
                if (k.equals("add_to_variable_list") || k.equals("remove_list_variable") || k.equals("add_to_global_variable_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name")); Node target = (Node)evaluate(field(a, "target"), f);
                    List<Node> list = k.equals("add_to_global_variable_list") ? globalLists.computeIfAbsent(name, ignored -> new ArrayList<>()) : f.here().list(name);
                    if (k.equals("remove_list_variable")) list.remove(target); else list.add(target); continue;
                }
                if (k.equals("every_in_list") || k.equals("random_in_list") || k.equals("random_in_global_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> list = k.equals("random_in_global_list") ? List.copyOf(globalLists.getOrDefault(name, List.of())) : list(f.here(), name);
                    for (Node n : list) if (test(a.block("limit"), f.enter(n))) {
                        execute(without(without(a, "variable"), "limit"), f.enter(n)); if (!k.equals("every_in_list")) break;
                    }
                    continue;
                }
                if (k.equals("random")) { Block a = (Block)e.value(); if (randomEnabled && number(evaluate(field(a, "chance"), f)).signum() > 0) execute(without(a, "chance"), f); continue; }
                if (k.equals("xfm_futures_match_effect")) { matchCalls++; continue; } // no fictitious fill; reservation remains held
                if (e.value() instanceof Block child) { Datum scope = resolve(k, f); if (!(scope instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(child, f.enter(n)); continue; }
                execute(definition(k), f);
            }
        }
    }
    private static String atom(Value value) { if (!(value instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Value field(Block block, String name) { List<Entry> found = block.named(name); if (found.size() != 1) throw new IllegalArgumentException("one field required " + name); return found.getFirst().value(); }
    private static Block without(Block block, String name) { return new Block(block.entries().stream().filter(e -> !e.key().equals(name)).toList()); }
}
