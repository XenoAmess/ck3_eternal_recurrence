package org.xar.ck3.markets.oracle;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
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

/** Actual production-script subset comparison, not a CK3 interpreter or physical SAVE.
 * Model-index bootstrap/daily and futures terminal dispatch are explicit unchanged ports.
 */
final class IdleMarketScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final String REFERENCE_SOURCE = System.getProperty("xfm.reference.source");
    private static final List<String> INPUTS = List.of("scripted_effects/xfm_spot_history.txt",
        "scripted_effects/xfm_oracle_reference.txt", "scripted_effects/xfm_oracle_samples.txt",
        "scripted_effects/xfm_listing_daily.txt", "scripted_effects/xfm_futures_settlement.txt", "scripted_triggers/xfm_oracle_triggers.txt",
        "scripted_triggers/xfm_market_idle_triggers.txt", "script_values/xfm_oracle_values.txt",
        "script_values/xfm_numeric_comparison_values.txt");

    public static void main(String[] ignored) throws Exception {
        int pass = 0;
        for (Method m : IdleMarketScriptContractTest.class.getDeclaredMethods()) if (m.isAnnotationPresent(Test.class)) {
            try { m.invoke(new IdleMarketScriptContractTest()); System.out.println("PASS " + m.getName()); pass++; }
            catch (InvocationTargetException e) { throw new AssertionError("FAIL " + m.getName(), e.getCause()); }
        }
        System.out.println("PRODUCTION_SUBSET groups=" + pass + " passed=" + pass + " CK3_NOT_RUN");
    }

    @Test void retiredFixedPointElidesOnlyIdenticalWritesAfterThirtyRealOriginalCloses() throws IOException {
        for (int state : List.of(5, 6)) {
            Vm old = fixture(false, state), now = fixture(true, state);
            int saved = 0;
            for (int d = 1; d <= 50; d++) {
                old.day = d; now.day = d; old.run("xfm_spot_close_day_effect"); now.run("xfm_spot_close_day_effect");
                assertHistoryEqual(old, now); assertEquals(old.n("xfm_day_volume_units"), now.n("xfm_day_volume_units"));
                if (d <= 30) assertEquals(155, now.barWrites);
                else {
                    assertEquals(0, now.barWrites); saved += old.barWrites - now.barWrites;
                    assertEquals(164, old.scalarWrites); assertEquals(5, now.scalarWrites);
                }
                assertEquals(Math.min(d, 30), now.n("xfm_idle_bar_close_count"));
                old.barWrites = 0; now.barWrites = 0; old.scalarWrites = 0; now.scalarWrites = 0;
            }
            assertEquals(3100, saved);
            assertEquals(77, now.n("xfm_coin_id")); assertEquals(100, now.n("xfm_last_price_cents"));
        }
    }

    @Test void activeWarningNoticeSuspensionAndRelistingKeepOriginalBarsAndOracleEveryDay() throws IOException {
        for (int state : List.of(0, 1, 2, 3, 4, 8)) {
            Vm old = fixture(false, state), now = fixture(true, state);
            for (int day = 100; day < 117; day++) {
                old.day = day; now.day = day;
                old.run("xfm_spot_close_day_effect"); now.run("xfm_spot_close_day_effect");
                old.run("xfm_oracle_daily_effect"); now.run("xfm_oracle_daily_effect");
                assertHistoryEqual(old, now); assertOracleEqual(old, now);
                assertEquals(14, now.slotVisits); assertEquals(old.barWrites, now.barWrites);
                assertEquals(state == 8 ? 0 : 155, now.barWrites);
                assertFalse(now.vars.containsKey("xfm_idle_bar_close_count"));
                old.slotVisits = 0; now.slotVisits = 0; old.barWrites = 0; now.barWrites = 0;
            }
        }
    }

    @Test void noticeWindowD15ThroughD20AndTerminalCertificateAreUnchanged() throws IOException {
        Vm old = fixture(false, 3), now = fixture(true, 3);
        for (Vm v : List.of(old, now)) {
            v.put("xfm_notice_day", 100); v.put("xfm_delisting_age", 14);
            v.put("xfm_termination_samples", 0); v.put("xfm_termination_price_sum_cents", 0);
        }
        for (int day = 115; day <= 121; day++) {
            for (Vm v : List.of(old, now)) {
                v.day = day; seedFourteen(v, day); v.run("xfm_oracle_daily_effect"); v.run("xfm_listing_notice_daily_effect");
            }
            assertEquals(old.n("xfm_termination_samples"), now.n("xfm_termination_samples"));
            assertEquals(old.n("xfm_termination_price_sum_cents"), now.n("xfm_termination_price_sum_cents"));
            assertOracleEqual(old, now);
        }
        assertEquals(6, now.n("xfm_termination_samples")); assertEquals(1, now.n("xfm_termination_price_certified"));
        assertEquals(100, now.n("xfm_termination_price_cents")); assertEquals(1, now.terminalDispatches);
    }

    @Test void archivedIdleExplicitlyRevokesRiskWithoutRefreshingHistoricalDatesOrErasingClaims() throws IOException {
        Vm v = fixture(true, 7); v.day = 100; archiveProof(v); v.put("xfm_oracle_quality", 1); v.put("xfm_max_leverage", 10);
        // Exercise the actual new guard against a distinct explicit exchange scope.
        // A same-named coin variable cannot change the exchange's recovery mode.
        Block recoveryGuard = v.def("xfm_oracle_daily_effect").block("if").block("limit");
        v.put("xfm_calendar_recovery", 1);
        assertFalse(v.test(recoveryGuard));
        v.exchangeVars.put("xfm_calendar_recovery", BigDecimal.ONE);
        v.put("xfm_calendar_recovery", 0);
        assertTrue(v.test(recoveryGuard));
        Vm persisted = Vm.read(v.program, v.write());
        assertTrue(persisted.test(recoveryGuard), "the actual exchange guard survives the authored graph round trip");
        v.exchangeVars.put("xfm_calendar_recovery", BigDecimal.ZERO);
        assertFalse(v.test(recoveryGuard)); v.vars.remove("xfm_calendar_recovery");
        assertThrows(IllegalArgumentException.class, () -> v.test(Clausewitz.parse("global_var:unknown_exchange = { var:xfm_calendar_recovery = 1 }")));
        assertThrows(IllegalArgumentException.class, () -> v.test(Clausewitz.parse("global_var:xfm_exchange = { var:unknown_global_value = 1 }")));
        v.put("xfm_oracle_reason", 0); v.put("xfm_oracle_day", 100); v.put("xfm_oracle_last_valid_day", 99);
        Map<String, BigDecimal> history = new LinkedHashMap<>(v.vars);
        v.run("xfm_oracle_daily_effect");
        assertEquals(0, v.slotVisits); assertEquals(0, v.n("xfm_oracle_quality")); assertEquals(0, v.n("xfm_max_leverage"));
        assertEquals(2, v.n("xfm_oracle_reason")); assertFalse(v.trigger("xfm_oracle_reliable_trigger"));
        assertEquals(100, v.n("xfm_oracle_day")); assertEquals(99, v.n("xfm_oracle_last_valid_day"));
        // Execute the unchanged actual position consumer with a closed-status pending journal.
        // The explicit port records a resume request, never fabricates a paid debt receipt.
        v.put("xfm_status", 3); v.put("xfm_pending_payment", 1);
        v.run("xfm_futures_position_daily_effect");
        assertEquals(1, v.resumeRequests); assertEquals(1, v.n("xfm_pending_payment"));
        for (String k : List.of("xfm_coin_id", "xfm_mark_cents", "xfm_index_cents", "xfm_termination_price_cents", "xfm_termination_window_end_day", "xfm_debt_identity")) assertEquals(history.get(k), v.vars.get(k), k);
        v.day = 500; v.run("xfm_oracle_daily_effect"); assertEquals(0, v.slotVisits);
        assertEquals(100, v.n("xfm_oracle_day")); assertEquals(99, v.n("xfm_oracle_last_valid_day"));
    }

    @Test void anyArchivedObligationOrMissingOldFieldKeepsOriginalOraclePath() throws IOException {
        List<String> zeros = List.of("xfm_supply_units", "xfm_open_orders_count", "xfm_unresolved_claim_count",
            "xfm_unpaid_debt_cents", "xfm_promises_due_cents", "xfm_maintenance_arrears_cents",
            "xfm_settlement_price_pending", "xfm_maker_withdrawal_pending", "xfm_oracle_bucket_samples",
            "xfm_oracle_bucket_notional", "xfm_oracle_bucket_lots", "xfm_qualified_volume_cents");
        for (String key : zeros) {
            for (boolean missing : List.of(false, true)) {
                Vm old = fixture(false, 7), now = fixture(true, 7); archiveProof(old); archiveProof(now);
                for (Vm v : List.of(old, now)) { v.day = 101; if (missing) v.vars.remove(key); else v.put(key, 1); }
                old.run("xfm_oracle_daily_effect"); now.run("xfm_oracle_daily_effect");
                assertEquals(14, now.slotVisits, key + " missing=" + missing); assertOracleEqual(old, now);
            }
        }
        for (String flag : List.of("xfm_unresolved_claims", "xfm_unclaimed_assets")) {
            Vm v = fixture(true, 7); archiveProof(v); v.put(flag, 1); v.run("xfm_oracle_daily_effect"); assertEquals(14, v.slotVisits);
        }
        for (int state : List.of(5, 6)) {
            Vm v = fixture(true, state); archiveProof(v); v.put("xfm_listing_state", state); v.put("xfm_settlement_price_pending", 1);
            v.run("xfm_oracle_daily_effect"); assertEquals(14, v.slotVisits); assertEquals(1, v.n("xfm_settlement_price_pending"));
            assertEquals(9001, v.n("xfm_debt_identity"));
        }
    }

    @Test void authoredColdGraphPriceChangeTradeAndYearGapRelistingCannotInventFreshness() throws IOException {
        Vm old = fixture(false, 5), now = fixture(true, 5);
        for (int day = 100; day < 135; day++) { old.day = day; now.day = day; old.run("xfm_spot_close_day_effect"); now.run("xfm_spot_close_day_effect"); }
        now = Vm.read(now.program, now.write()); old = Vm.read(old.program, old.write());
        for (int state : List.of(8, 2)) {
            for (Vm v : List.of(old, now)) { v.day = 500 + state; v.put("xfm_listing_state", state); v.put("xfm_trading_open", state == 2 ? 1 : 0); v.run("xfm_spot_close_day_effect"); v.run("xfm_oracle_daily_effect"); }
            assertHistoryEqual(old, now); assertOracleEqual(old, now);
            assertEquals(0, now.n("xfm_max_leverage")); assertEquals(0, now.n("xfm_oracle_quality"));
            assertFalse(now.vars.containsKey("xfm_idle_bar_close_count"));
        }
        for (Vm v : List.of(old, now)) { v.put("xfm_listing_state", 6); v.put("xfm_trading_open", 0); v.put("xfm_last_price_cents", 120); v.put("xfm_day_volume_units", 100); v.put("xfm_day_close_cents", 120); v.run("xfm_spot_close_day_effect"); }
        assertHistoryEqual(old, now); assertFalse(now.vars.containsKey("xfm_idle_bar_close_count"));
        // Old saves missing the proof must perform 30 actual shifts, even after a year jump.
        now.vars.remove("xfm_idle_bar_price_cents"); now.vars.remove("xfm_idle_bar_close_count"); now.day = 9000; now.barWrites = 0;
        now.run("xfm_spot_close_day_effect"); assertEquals(155, now.barWrites); assertEquals(1, now.n("xfm_idle_bar_close_count"));
        // An archived oracle's original dated slots cannot regain 14 valid days after a year gap.
        Vm archived = fixture(true, 7); archiveProof(archived); archived.run("xfm_oracle_daily_effect");
        archived = Vm.read(archived.program, archived.write()); archived.day = 500; archived.put("xfm_listing_state", 8);
        archived.run("xfm_oracle_daily_effect"); assertEquals(14, archived.slotVisits);
        assertEquals(0, archived.n("xfm_oracle_valid_days")); assertEquals(0, archived.n("xfm_max_leverage")); assertFalse(archived.trigger("xfm_oracle_new_risk_trigger"));
    }

    @Test void sourceMutationStaysInsideHotWritesAndNeverTouchesIdsDebtsOrFreshnessPolicy() throws IOException {
        Vm v = load(true);
        for (String name : List.of("xfm_spot_track_idle_bars_effect", "xfm_spot_idle_bars_eligible_trigger", "xfm_spot_idle_bars_fixed_trigger", "xfm_oracle_archived_idle_trigger")) bound(v.program.get(name));
        Block oracle = v.program.get("xfm_oracle_daily_effect"); assertEquals(1, count(oracle, "xfm_oracle_recalculate_effect"));
        assertEquals(14, count(v.program.get("xfm_oracle_recalculate_effect"), "xfm_oracle_scan_slot_effect"));
        for (String path : List.of("scripted_effects/xfm_spot_history.txt", "scripted_effects/xfm_oracle_reference.txt", "scripted_triggers/xfm_market_idle_triggers.txt")) {
            byte[] bytes = Files.readAllBytes(SOURCE.resolve("common").resolve(path)); assertTrue(bytes[0] == (byte)0xef && bytes[1] == (byte)0xbb && bytes[2] == (byte)0xbf);
        }
        assertThrows(IllegalArgumentException.class, () -> v.execute(Clausewitz.parse("made_up_effect = yes")));
    }

    private static void archiveProof(Vm v) {
        for (String name : List.of("xfm_supply_units", "xfm_open_orders_count", "xfm_unresolved_claim_count", "xfm_unpaid_debt_cents", "xfm_promises_due_cents", "xfm_maintenance_arrears_cents", "xfm_settlement_price_pending", "xfm_maker_withdrawal_pending", "xfm_oracle_bucket_samples", "xfm_oracle_bucket_notional", "xfm_oracle_bucket_lots", "xfm_qualified_volume_cents")) v.put(name, 0);
    }
    private static Vm fixture(boolean candidate, int state) throws IOException {
        Vm v = load(candidate); v.day = 100; v.run("xfm_spot_init_history_effect");
        v.put("xfm_coin_id", 77); v.put("xfm_debt_identity", 9001); v.put("xfm_listing_state", state); v.put("xfm_trading_open", state <= 3 ? 1 : 0);
        v.put("xfm_last_price_cents", 100); v.put("xfm_day_open_cents", 100); v.put("xfm_day_high_cents", 100); v.put("xfm_day_low_cents", 100); v.put("xfm_day_close_cents", 100); v.put("xfm_day_volume_units", 0);
        v.put("xfm_candle_0_close_cents", 999); v.put("xfm_candle_0_volume_units", 12345);
        v.run("xfm_oracle_init_coin_effect"); v.put("xfm_listed_day", 0); seedFourteen(v, 100);
        v.put("xfm_index_cents", 100); v.put("xfm_mark_cents", 100); v.put("xfm_termination_price_cents", 97); v.put("xfm_termination_window_end_day", 90);
        v.barWrites = 0; v.slotVisits = 0; v.scalarWrites = 0;
        return v;
    }
    private static void seedFourteen(Vm v, int day) { for (int i = 0; i < 14; i++) { v.put("xfm_oracle_slot_" + i + "_day", day - 14 + i); v.put("xfm_oracle_slot_" + i + "_participants", 8); v.put("xfm_oracle_slot_" + i + "_price", 100); } }
    private static void assertHistoryEqual(Vm a, Vm b) { for (var e : a.vars.entrySet()) if (e.getKey().startsWith("xfm_candle_") || e.getKey().startsWith("xfm_prev_")) assertEquals(e.getValue(), b.vars.get(e.getKey()), e.getKey()); }
    private static void assertOracleEqual(Vm a, Vm b) { for (var e : a.vars.entrySet()) if (e.getKey().startsWith("xfm_oracle_") || Set.of("xfm_max_leverage", "xfm_mark_cents", "xfm_index_cents", "xfm_last_completed_volume_day", "xfm_last_completed_qualified_volume_cents").contains(e.getKey())) assertEquals(e.getValue(), b.vars.get(e.getKey()), e.getKey()); }
    private static void bound(Block b) { assertTrue(b.entries().size() <= 20); for (Entry e : b.entries()) if (e.value() instanceof Block child) bound(child); }
    private static long count(Block b, String key) { long n = 0; for (Entry e : b.entries()) { if (e.key().equals(key)) n++; if (e.value() instanceof Block child) n += count(child, key); } return n; }
    private static Vm load(boolean candidate) throws IOException {
        Map<String, Block> program = new LinkedHashMap<>();
        for (String input : INPUTS) {
            if (!candidate && input.endsWith("xfm_market_idle_triggers.txt")) continue; // absent from the original production baseline
            String script;
            if (candidate || REFERENCE_SOURCE != null) {
                Path root = candidate ? SOURCE : Path.of(REFERENCE_SOURCE);
                script = Files.readString(root.resolve("common").resolve(input));
            } else {
                String resource = "/idle-market-baseline/common/" + input;
                try (var stream = IdleMarketScriptContractTest.class.getResourceAsStream(resource)) {
                    if (stream == null) throw new IOException("missing original production source fixture: " + resource);
                    script = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
                }
            }
            for (Entry e : Clausewitz.parse(script).entries()) {
                Block b = e.value() instanceof Block block ? block : new Block(List.of(new Entry("value", "=", e.value())));
                if (program.putIfAbsent(e.key(), b) != null) throw new IllegalArgumentException("duplicate " + e.key());
            }
        }
        return new Vm(program);
    }
    private static final class Vm {
        final Map<String, Block> program; final Map<String, BigDecimal> vars = new LinkedHashMap<>(); final Set<String> lists = new HashSet<>();
        final Map<String, BigDecimal> exchangeVars = new LinkedHashMap<>();
        boolean exchangeScope;
        long day = 100; int barWrites, scalarWrites, slotVisits, terminalDispatches, resumeRequests, instructions;
        Vm(Map<String, Block> program) {
            this.program = program;
            // Explicit ordinary-world fixture input, independent of coin variables.
            exchangeVars.put("xfm_calendar_recovery", BigDecimal.ZERO);
        }
        void put(String key, long n) { vars.put(key, BigDecimal.valueOf(n)); }
        long n(String key) { return vars.getOrDefault(key, BigDecimal.ZERO).longValueExact(); }
        Block def(String key) { Block b = program.get(key); if (b == null) throw new IllegalArgumentException("unknown definition " + key); return b; }
        void run(String name) { if (name.equals("xfm_oracle_scan_slot_effect")) slotVisits++; execute(def(name)); }
        boolean trigger(String name) { return test(def(name)); }
        BigDecimal resolve(String key) {
            try { return new BigDecimal(key); } catch (NumberFormatException ignored) { /* value token */ }
            if (key.startsWith("global_var:xfm_exchange.var:")) return exchangeValue(key.substring("global_var:xfm_exchange.var:".length()));
            if (key.startsWith("var:")) return exchangeScope ? exchangeValue(key.substring(4)) : vars.getOrDefault(key.substring(4), BigDecimal.ZERO);
            if (program.containsKey(key)) return value(def(key));
            throw new IllegalArgumentException("unknown scalar " + key);
        }
        BigDecimal exchangeValue(String name) {
            if (name.equals("xfm_day")) return BigDecimal.valueOf(day);
            BigDecimal result = exchangeVars.get(name);
            if (result == null) throw new IllegalArgumentException("unknown exchange scalar " + name);
            return result;
        }
        BigDecimal eval(Value v) { return v instanceof Block b ? value(b) : resolve(atom(v)); }
        BigDecimal value(Block b) {
            BigDecimal n = BigDecimal.ZERO;
            for (Entry e : b.entries()) {
                if (e.key().equals("floor")) { n = n.setScale(0, RoundingMode.FLOOR); continue; }
                if (e.key().equals("ceiling")) { n = n.setScale(0, RoundingMode.CEILING); continue; }
                BigDecimal x = eval(e.value());
                n = switch (e.key()) { case "value" -> x; case "add" -> n.add(x); case "subtract" -> n.subtract(x); case "multiply" -> n.multiply(x); case "divide" -> n.divide(x, 18, RoundingMode.HALF_EVEN); case "modulo" -> n.remainder(x); case "min" -> n.max(x); case "max" -> n.min(x); default -> throw new IllegalArgumentException("unknown numeric op " + e.key()); };
            }
            return n.stripTrailingZeros();
        }
        boolean test(Block b) { for (Entry e : b.entries()) if (!check(e)) return false; return true; }
        boolean check(Entry e) {
            String k = e.key();
            if (k.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(this::check);
            if (k.equals("AND")) return test((Block)e.value());
            if (k.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(this::check);
            if (k.equals("global_var:xfm_exchange")) {
                if (!e.operator().equals("=") || !(e.value() instanceof Block child)) throw new IllegalArgumentException("exchange predicate block required");
                boolean previous = exchangeScope; exchangeScope = true;
                try { return test(child); } finally { exchangeScope = previous; }
            }
            if (k.equals("has_variable")) return exchangeScope
                    ? atom(e.value()).equals("xfm_day") || exchangeVars.containsKey(atom(e.value())) : vars.containsKey(atom(e.value()));
            if (k.equals("has_variable_list")) {
                if (exchangeScope) throw new IllegalArgumentException("exchange list predicate is outside this source subset");
                return lists.contains(atom(e.value()));
            }
            if (k.equals("story_type")) return atom(e.value()).equals(exchangeScope ? "xfm_finance_exchange" : "xfm_finance_coin");
            if (k.endsWith("_trigger")) return trigger(k);
            int c = resolve(k).compareTo(eval(e.value()));
            return switch (e.operator()) { case "=" -> c == 0; case "!=" -> c != 0; case ">" -> c > 0; case "<" -> c < 0; case ">=" -> c >= 0; case "<=" -> c <= 0; default -> throw new IllegalArgumentException("operator"); };
        }
        void execute(Block b) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                if (++instructions > 3000000) throw new IllegalArgumentException("instruction bound"); String k = e.key();
                if (k.equals("if") || k.equals("else_if")) { Block a = (Block)e.value(); boolean yes = (!k.equals("else_if") || !chain) && test(a.block("limit")); if (k.equals("if")) chain = false; if (yes) { execute(without(a, "limit")); chain = true; } continue; }
                if (k.equals("else")) { if (!chain) execute((Block)e.value()); chain = false; continue; }
                if (k.equals("set_variable") || k.equals("change_variable")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name"));
                    if (k.equals("set_variable")) vars.put(name, eval(field(a, "value")));
                    else { boolean add = !a.named("add").isEmpty(); BigDecimal x = eval(field(a, add ? "add" : "subtract")); vars.put(name, vars.getOrDefault(name, BigDecimal.ZERO).add(add ? x : x.negate())); }
                    scalarWrites++; if (name.startsWith("xfm_candle_") || name.startsWith("xfm_prev_")) barWrites++; continue;
                }
                if (k.equals("remove_variable")) { vars.remove(atom(e.value())); continue; }
                if (k.equals("clear_variable_list")) { lists.remove(atom(e.value())); continue; }
                if (k.equals("every_in_global_list")) { Block a = (Block)e.value(); if (!atom(field(a, "variable")).equals("xfm_coin_registry")) throw new IllegalArgumentException("unexpected directory"); execute(without(a, "variable")); continue; }
                if (Set.of("xfm_oracle_index_bootstrap_effect", "xfm_oracle_index_daily_effect").contains(k)) continue;
                if (k.equals("xfm_futures_terminate_market_effect")) { terminalDispatches++; continue; }
                if (k.equals("xfm_futures_resume_settlement_effect")) { resumeRequests++; continue; }
                if (e.value() instanceof Block args) {
                    Block expanded = Clausewitz.mapAtoms(def(k), text -> { String out = text; for (Entry arg : args.entries()) out = out.replace("$" + arg.key() + "$", atom(arg.value())); return out; });
                    if (k.equals("xfm_oracle_scan_slot_effect")) slotVisits++; execute(expanded); continue;
                }
                run(k);
            }
        }
        byte[] write() throws IOException { ByteArrayOutputStream bytes = new ByteArrayOutputStream(); try (DataOutputStream out = new DataOutputStream(bytes)) { out.writeLong(day); out.writeInt(exchangeVars.size()); for (var e : exchangeVars.entrySet()) { out.writeUTF(e.getKey()); out.writeUTF(e.getValue().toPlainString()); } out.writeInt(vars.size()); for (var e : vars.entrySet()) { out.writeUTF(e.getKey()); out.writeUTF(e.getValue().toPlainString()); } out.writeInt(lists.size()); for (String name : lists) out.writeUTF(name); } return bytes.toByteArray(); }
        static Vm read(Map<String, Block> program, byte[] bytes) throws IOException { Vm v = new Vm(program); try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes))) { v.day = in.readLong(); v.exchangeVars.clear(); int n = in.readInt(); for (int i = 0; i < n; i++) v.exchangeVars.put(in.readUTF(), new BigDecimal(in.readUTF())); n = in.readInt(); for (int i = 0; i < n; i++) v.vars.put(in.readUTF(), new BigDecimal(in.readUTF())); n = in.readInt(); for (int i = 0; i < n; i++) v.lists.add(in.readUTF()); if (in.read() != -1) throw new IOException("trailing graph"); } return v; }
    }
    private static String atom(Value v) { if (!(v instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Value field(Block b, String key) { List<Entry> found = b.named(key); if (found.size() != 1) throw new IllegalArgumentException("one field required " + key); return found.getFirst().value(); }
    private static Block without(Block b, String key) { return new Block(b.entries().stream().filter(e -> !e.key().equals(key)).toList()); }
}
