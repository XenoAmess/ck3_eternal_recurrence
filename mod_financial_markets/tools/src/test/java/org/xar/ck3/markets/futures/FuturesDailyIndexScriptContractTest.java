package org.xar.ck3.markets.futures;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.Clausewitz.Value;

/** Executes the actual three-leaf queue/dispatcher/match subset. This is not CK3.
 * Business journal, book maintenance, discovery and archive are explicit test ports.
 * The binary round trip is an authored scope graph, never represented as a CK3 SAVE.
 */
final class FuturesDailyIndexScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final Path REFERENCE = Path.of(System.getProperty("xfm.reference.source", SOURCE.toString()));
    private static final List<String> LEAVES = List.of("scripted_effects/xfm_futures_daily_index.txt",
        "scripted_effects/xfm_futures_settlement.txt", "scripted_effects/xfm_futures_match.txt",
        "scripted_triggers/xfm_futures_triggers.txt");

    public static void main(String[] ignored) throws Exception {
        int passed = 0;
        for (Method m : FuturesDailyIndexScriptContractTest.class.getDeclaredMethods()) {
            if (!m.isAnnotationPresent(Test.class)) continue;
            try { m.invoke(new FuturesDailyIndexScriptContractTest()); System.out.println("PASS " + m.getName()); passed++; }
            catch (InvocationTargetException e) { throw new AssertionError("FAIL " + m.getName(), e.getCause()); }
        }
        System.out.println("PRODUCTION_SUBSET groups=" + passed + " passed=" + passed + " CK3_NOT_RUN");
    }

    @Test void legacyTailObligationsAreMigratedBeforeAnyDailyAndHistoryIsNeverRescanned() throws IOException {
        Vm v = vm();
        for (int i = 0; i < 10000; i++) v.contract("empty-" + i);
        Node live = v.contract("tail-position"); v.position("live", live, 0, 2);
        Node pending = v.contract("tail-pending"); v.position("unpaid", pending, 3, 0).put("xfm_pending_payment", 1);
        Node gtc = v.contract("tail-expired-gtc"); v.order("gtc", gtc, 1, 1); gtc.put("xfm_expiry_day", 0);
        v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(10003, v.historyVisits);
        assertEquals(Set.of(live.id, pending.id, gtc.id), v.maintenance.keySet());
        assertEquals(Set.of("live", "unpaid"), v.positionCalls.keySet());
        assertEquals(10003, v.exchange.list("xfm_futures_contracts").size());
        assertEquals(3, v.exchange.integer("xfm_futures_daily_count")); v.assertQueue();
        v.exchange.put("xfm_day", 2); v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(10003, v.historyVisits); assertEquals(2, v.maintenance.get(live.id));
        assertEquals(10003, v.exchange.list("xfm_futures_contracts").size());
    }

    @Test void successfulOrdinaryMatchHookEnrollsTypedContractWithoutSettling() throws IOException {
        Vm v = vm(); v.run("xfm_futures_daily_index_ensure_effect", v.exchange);
        Node c = v.contract("new"); Node o = v.order("incoming", c, 0, 1);
        v.run("xfm_futures_match_effect", o); v.run("xfm_futures_match_effect", o);
        assertEquals(1, v.exchange.integer("xfm_futures_daily_count")); v.assertQueue();
        assertTrue(v.positionCalls.isEmpty()); assertFalse(c.vars.containsKey("xfm_last_daily_day"));
        Node invalid = v.node("invalid-order", "xfm_futures_order"); invalid.put("xfm_status", 0); invalid.put("xfm_remaining_lots", 1);
        Block hook = v.definition("xfm_futures_match_effect").block("if");
        v.execute(new Block(List.of(new Entry("if", "=", hook))), new Frame(invalid, null));
        Node foreign = v.node("wrong-contract", "xfm_finance_coin"); invalid.put("xfm_contract", foreign);
        v.execute(new Block(List.of(new Entry("if", "=", hook))), new Frame(invalid, null));
        assertFalse(foreign.vars.containsKey("xfm_futures_daily_queued"));
        assertEquals(1, v.exchange.integer("xfm_futures_daily_count"));
    }

    @Test void sameDayRepeatAndAuthoredGraphReloadKeepIdentityAndDoNoSecondBusinessTick() throws IOException {
        Vm v = vm(); Node c = v.contract("c"); Node p = v.position("p", c, 0, 2);
        p.put("xfm_debt_receipt_1", v.node("immutable-debt", "xfm_debt"));
        v.run("xfm_futures_daily_effect", v.exchange); byte[] graph = v.write();
        Vm restored = Vm.read(v.program, graph); restored.run("xfm_futures_daily_effect", restored.exchange);
        assertTrue(restored.maintenance.isEmpty()); assertTrue(restored.positionCalls.isEmpty());
        assertEquals(0, restored.historyVisits); restored.assertQueue();
        assertSame(restored.nodes.get("immutable-debt"), restored.nodes.get("p").ref("xfm_debt_receipt_1"));
        restored.exchange.put("xfm_day", 2); restored.run("xfm_futures_daily_effect", restored.exchange);
        assertEquals(1, restored.positionCalls.get("p")); assertEquals(0, restored.historyVisits); restored.assertQueue();
    }

    @Test void staleExpiredDefaultedPendingAndFreshPositionKeepTheirSeparateObligations() throws IOException {
        Vm v = vm(); Node c = v.contract("expired"); c.put("xfm_status", 3); c.put("xfm_expiry_day", 0); c.put("xfm_oracle_quality", 0);
        Node pending = v.position("pending", c, 3, 0); pending.put("xfm_pending_payment", 1); pending.put("xfm_created_day", 1);
        Node fresh = v.position("fresh", c, 0, 1); fresh.put("xfm_created_day", 1);
        Node order = v.order("gtc", c, 1, 1);
        v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(1, v.positionCalls.get("pending")); assertFalse(v.positionCalls.containsKey("fresh"));
        assertEquals(1, v.maintenance.get(c.id)); assertEquals(1, order.integer("xfm_remaining_lots"));
        v.exchange.put("xfm_day", 2); v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(1, v.positionCalls.get("fresh")); assertEquals(2, v.positionCalls.get("pending"));
    }

    @Test void callbackAdmissionAndCurrentReAdmissionCannotEnlargeCapturedPass() throws IOException {
        Vm v = vm(); Node a = v.contract("a"); v.position("pa", a, 0, 1);
        Node b = v.contract("b"); v.position("pb", b, 0, 1);
        Node later = v.contract("later");
        v.maintain = contract -> {
            if (contract != a) return;
            v.position("later-position", later, 0, 1);
            v.run("xfm_futures_daily_enroll_effect", later);
            v.run("xfm_futures_daily_enroll_effect", contract);
        };
        v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(Set.of("a", "b"), v.maintenance.keySet());
        assertEquals(3, v.exchange.integer("xfm_futures_daily_count")); assertEquals(0, v.exchange.integer("xfm_futures_daily_remaining"));
        assertEquals(1, v.maintenance.get("a")); v.assertQueue();
        v.run("xfm_futures_daily_effect", v.exchange); assertFalse(v.maintenance.containsKey("later"));
        v.maintain = ignored -> { }; v.exchange.put("xfm_day", 2); v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(1, v.maintenance.get("later")); v.assertQueue();
    }

    @Test void interruptedProcessingFlagSurvivesGraphReloadAndResumesRatherThanSwallowingHead() throws IOException {
        Vm v = vm(); Node a = v.contract("a"); v.position("pa", a, 0, 1);
        Node b = v.contract("b"); v.position("pb", b, 0, 1);
        v.maintain = ignored -> { throw new Checkpoint(); };
        assertThrows(Checkpoint.class, () -> v.run("xfm_futures_daily_effect", v.exchange));
        assertSame(a, v.exchange.ref("xfm_futures_daily_processing_contract"));
        assertEquals(1, a.integer("xfm_futures_daily_processing")); assertEquals(2, v.exchange.integer("xfm_futures_daily_remaining"));
        Vm restored = Vm.read(v.program, v.write()); restored.assertQueue();
        restored.run("xfm_futures_daily_effect", restored.exchange);
        assertEquals(Set.of("pa", "pb"), restored.positionCalls.keySet());
        assertEquals(1, restored.positionCalls.get("pa")); assertEquals(1, restored.positionCalls.get("pb"));
        assertFalse(restored.exchange.vars.containsKey("xfm_futures_daily_processing_contract"));
        assertEquals(0, restored.exchange.integer("xfm_futures_daily_remaining")); restored.assertQueue();
        assertTrue(restored.nodes.values().stream().noneMatch(n -> n.vars.containsKey("xfm_futures_daily_processing")));
        // A second real producer boundary: visit has committed its day guard, finish has not run.
        Vm completed = vm(); Node c = completed.contract("committed"); completed.position("pc", c, 0, 1);
        completed.run("xfm_futures_daily_index_ensure_effect", completed.exchange);
        completed.exchange.put("xfm_futures_daily_pass_day", 1); completed.exchange.put("xfm_futures_daily_remaining", 1);
        Block step = completed.definition("xfm_futures_daily_step_effect");
        completed.execute(new Block(List.of(step.entries().getFirst())), new Frame(completed.exchange, null));
        Block processing = (Block)step.named("if").get(1).value();
        Entry visit = processing.entries().stream().filter(e -> e.key().equals("var:xfm_futures_daily_processing_contract")).findFirst().orElseThrow();
        completed.execute(new Block(List.of(visit)), new Frame(completed.exchange, null));
        assertEquals(1, completed.positionCalls.get("pc"));
        Vm afterVisit = Vm.read(completed.program, completed.write()); afterVisit.run("xfm_futures_daily_effect", afterVisit.exchange);
        assertTrue(afterVisit.positionCalls.isEmpty()); assertTrue(afterVisit.maintenance.isEmpty());
        assertEquals(1, afterVisit.exchange.integer("xfm_futures_daily_count")); afterVisit.assertQueue();
    }

    @Test void partlySeededLegacyIndexRetriesWithoutResettingLinksOrLosingTail() throws IOException {
        Vm v = vm(); Node first = v.contract("first"); v.order("o1", first, 0, 1);
        for (int i = 0; i < 2048; i++) v.contract("old-" + i);
        Node last = v.contract("last"); v.position("p", last, 3, 0).put("xfm_pending_payment", 1);
        v.run("xfm_futures_daily_enroll_effect", first);
        Vm restored = Vm.read(v.program, v.write()); restored.run("xfm_futures_daily_effect", restored.exchange);
        assertEquals(2050, restored.historyVisits); assertEquals(2, restored.exchange.integer("xfm_futures_daily_count"));
        assertEquals(Set.of("first", "last"), restored.maintenance.keySet()); restored.assertQueue();
    }

    @Test void finishedOrdersAndClosedClaimsLeaveRingButPermanentDebtAndIdentityRemain() throws IOException {
        Vm v = vm(); Node c = v.contract("c"); Node order = v.order("order", c, 0, 1);
        Node p = v.position("position", c, 0, 1); Node debt = v.node("debt", "xfm_debt"); debt.put("xfm_outstanding_cents", 99);
        p.put("xfm_debt_receipt_1", debt); v.exchange.list("xfm_debts_active").add(debt);
        v.maintain = ignored -> { order.put("xfm_status", 3); order.put("xfm_remaining_lots", 0); };
        v.position = ignored -> { p.put("xfm_status", 3); p.put("xfm_lots", 0); p.vars.remove("xfm_pending_payment"); };
        v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(0, v.exchange.integer("xfm_futures_daily_count")); v.assertQueue();
        assertEquals(List.of(c), v.exchange.list("xfm_futures_contracts")); assertEquals(List.of(debt), v.exchange.list("xfm_debts_active"));
        assertEquals(99, debt.integer("xfm_outstanding_cents")); assertSame(debt, p.ref("xfm_debt_receipt_1"));
        int visits = v.historyVisits; v.exchange.put("xfm_day", 2); v.run("xfm_futures_daily_effect", v.exchange);
        assertEquals(visits, v.historyVisits); assertEquals(1, v.maintenance.get("c"));
    }

    @Test void sourceCompositionHasOneMigrationScanNoPermanentDeletionAndAtMostTwentyDirectEffects() throws IOException {
        Vm v = vm();
        assertEquals(1, occurrences(v.definition("xfm_futures_daily_index_ensure_effect"), "xfm_futures_contracts"));
        for (String name : List.of("xfm_futures_daily_effect", "xfm_futures_daily_dispatch_effect", "xfm_futures_daily_step_effect", "xfm_futures_daily_visit_effect"))
            assertEquals(0, occurrences(v.definition(name), "xfm_futures_contracts"));
        String index = Files.readString(SOURCE.resolve("common/scripted_effects/xfm_futures_daily_index.txt"));
        assertFalse(index.contains("end_story")); assertFalse(index.contains("remove_list_variable")); assertFalse(index.contains("xfm_debts_active" + " ="));
        for (String leaf : LEAVES.subList(0, 3)) {
            byte[] bytes = Files.readAllBytes(SOURCE.resolve("common").resolve(leaf));
            assertTrue(bytes.length > 3 && bytes[0] == (byte)0xef && bytes[1] == (byte)0xbb && bytes[2] == (byte)0xbf);
        }
        for (String name : v.program.keySet()) if (name.startsWith("xfm_futures_daily_")) assertDirectBound(v.definition(name));
        assertEquals(1, occurrences(v.definition("xfm_futures_match_effect"), "xfm_futures_daily_enroll_effect"));
        assertThrows(IllegalArgumentException.class, () -> v.execute(Clausewitz.parse("invented_effect = yes"), new Frame(v.exchange, null)));
    }

    private static void assertDirectBound(Block b) {
        assertTrue(b.entries().size() <= 20, () -> "too many direct entries " + b.entries().size());
        for (Entry e : b.entries()) if (e.value() instanceof Block child) assertDirectBound(child);
    }
    private static long occurrences(Block b, String token) {
        long n = 0;
        for (Entry e : b.entries()) { if (e.key().equals(token) || e.value() instanceof Atom a && a.token().equals(token)) n++; if (e.value() instanceof Block child) n += occurrences(child, token); }
        return n;
    }
    private static Vm vm() throws IOException {
        Map<String, Block> definitions = new LinkedHashMap<>();
        for (String leaf : LEAVES) {
            Path p = SOURCE.resolve("common").resolve(leaf); if (!Files.exists(p)) p = REFERENCE.resolve("common").resolve(leaf);
            for (Entry e : Clausewitz.parse(Files.readString(p)).entries()) {
                if (!(e.value() instanceof Block b) || definitions.putIfAbsent(e.key(), b) != null) throw new IllegalArgumentException("bad/duplicate definition " + e.key());
            }
        }
        return new Vm(definitions);
    }
    private sealed interface Datum permits Node, Num { }
    private record Num(long value) implements Datum { }
    private static final class Node implements Datum {
        final String id, type; final Map<String, Datum> vars = new LinkedHashMap<>(); final Map<String, List<Node>> lists = new LinkedHashMap<>();
        Node(String id, String type) { this.id = id; this.type = type; }
        void put(String key, long value) { vars.put(key, new Num(value)); }
        void put(String key, Node value) { vars.put(key, value); }
        long integer(String key) { Datum d = vars.get(key); return d == null ? 0 : ((Num)d).value(); }
        Node ref(String key) { return (Node)vars.get(key); }
        List<Node> list(String name) { return lists.computeIfAbsent(name, ignored -> new ArrayList<>()); }
    }
    private record Frame(Node here, Node previous) { Frame enter(Node n) { return new Frame(n, here); } }
    private static final class Checkpoint extends RuntimeException { private static final long serialVersionUID = 1L; }
    private static final class Vm {
        final Map<String, Block> program; final Map<String, Node> nodes = new LinkedHashMap<>(); final Map<String, Node> scopes = new HashMap<>();
        final Node exchange; final Map<String, Integer> maintenance = new LinkedHashMap<>(), positionCalls = new LinkedHashMap<>();
        Consumer<Node> maintain = ignored -> { }, position = ignored -> { }; int historyVisits, statements;
        Vm(Map<String, Block> program) { this.program = program; exchange = node("exchange", "xfm_finance_exchange"); exchange.put("xfm_day", 1); }
        Node node(String id, String type) { Node n = new Node(id, type); if (nodes.putIfAbsent(id, n) != null) throw new IllegalArgumentException("duplicate node " + id); return n; }
        Node contract(String id) { Node c = node(id, "xfm_futures_contract"); c.put("xfm_status", 0); exchange.list("xfm_futures_contracts").add(c); return c; }
        Node position(String id, Node c, int status, int lots) { Node p = node(id, "xfm_futures_position"); p.put("xfm_status", status); p.put("xfm_lots", lots); p.put("xfm_contract", c); c.list("xfm_positions").add(p); return p; }
        Node order(String id, Node c, int status, int lots) { Node o = node(id, "xfm_futures_order"); o.put("xfm_status", status); o.put("xfm_remaining_lots", lots); o.put("xfm_contract", c); o.put("xfm_side", 1); c.list("xfm_orders").add(o); return o; }
        Block definition(String name) { Block b = program.get(name); if (b == null) throw new IllegalArgumentException("unknown " + name); return b; }
        void run(String name, Node n) { execute(definition(name), new Frame(n, null)); }
        Datum resolve(String text, Frame f) {
            try { return new Num(Long.parseLong(text)); } catch (NumberFormatException ignored) { /* scope token */ }
            int dot = text.indexOf('.'); if (dot > 0) { Datum d = resolve(text.substring(0, dot), f); return d instanceof Node n ? resolve(text.substring(dot + 1), f.enter(n)) : null; }
            if (text.equals("this")) return f.here(); if (text.equals("prev")) return f.previous();
            if (text.equals("global_var:xfm_exchange")) return exchange;
            if (text.startsWith("var:")) return f.here().vars.get(text.substring(4));
            if (text.startsWith("scope:")) return scopes.get(text.substring(6));
            throw new IllegalArgumentException("unknown value " + text);
        }
        Datum evaluate(Value value, Frame f) { if (value instanceof Atom a) return resolve(a.token(), f); throw new IllegalArgumentException("unsupported numerical block"); }
        long number(Datum d) { if (d == null) return 0; if (d instanceof Num n) return n.value(); throw new IllegalArgumentException("number required"); }
        List<Node> list(Node n, String name) { List<Node> list = List.copyOf(n.list(name)); if (name.equals("xfm_futures_contracts")) historyVisits += list.size(); return list; }
        boolean test(Block b, Frame f) { for (Entry e : b.entries()) if (!check(e, f)) return false; return true; }
        boolean check(Entry e, Frame f) {
            String k = e.key();
            if (k.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, f));
            if (k.equals("AND")) return test((Block)e.value(), f);
            if (k.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, f));
            if (k.equals("exists")) return resolve(atom(e.value()), f) != null;
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("any_in_list")) { Block a = (Block)e.value(); for (Node n : list(f.here(), atom(field(a, "variable")))) if (test(without(a, "variable"), f.enter(n))) return true; return false; }
            if (k.endsWith("_trigger")) return test(definition(k), f);
            if (e.value() instanceof Block b) { Datum d = resolve(k, f); return d instanceof Node n && test(b, f.enter(n)); }
            Datum l = resolve(k, f), r = evaluate(e.value(), f);
            if (l instanceof Num a && r instanceof Num b) { int c = Long.compare(a.value(), b.value()); return switch (e.operator()) { case "=" -> c == 0; case "!=" -> c != 0; case ">" -> c > 0; case "<" -> c < 0; case ">=" -> c >= 0; case "<=" -> c <= 0; default -> throw new IllegalArgumentException("operator"); }; }
            return switch (e.operator()) { case "=" -> java.util.Objects.equals(l, r); case "!=" -> !java.util.Objects.equals(l, r); default -> false; };
        }
        void execute(Block b, Frame f) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                if (++statements > 5000000) throw new IllegalArgumentException("instruction bound");
                String k = e.key();
                if (k.equals("if") || k.equals("else_if")) { Block a = (Block)e.value(); boolean yes = (!k.equals("else_if") || !chain) && test(a.block("limit"), f); if (k.equals("if")) chain = false; if (yes) { execute(without(a, "limit"), f); chain = true; } continue; }
                if (k.equals("else")) { if (!chain) execute((Block)e.value(), f); chain = false; continue; }
                if (k.equals("while")) { Block a = (Block)e.value(); while (test(a.block("limit"), f)) execute(without(a, "limit"), f); continue; }
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("remove_variable")) { f.here().vars.remove(atom(e.value())); continue; }
                if (k.equals("set_variable") || k.equals("change_variable")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name"));
                    if (k.equals("set_variable")) { Datum value = evaluate(field(a, "value"), f); if (value == null) throw new IllegalArgumentException("null variable " + name); f.here().vars.put(name, value); }
                    else { boolean add = !a.named("add").isEmpty(); long value = number(evaluate(field(a, add ? "add" : "subtract"), f)); f.here().put(name, f.here().integer(name) + (add ? value : -value)); }
                    continue;
                }
                if (k.equals("every_in_list")) { Block a = (Block)e.value(); for (Node n : list(f.here(), atom(field(a, "variable")))) if (test(a.block("limit"), f.enter(n))) execute(without(without(a, "variable"), "limit"), f.enter(n)); continue; }
                if (k.equals("xfm_futures_maintain_orders_effect")) { maintenance.merge(f.here().id, 1, Integer::sum); maintain.accept(f.here()); continue; }
                if (k.equals("xfm_futures_position_daily_effect")) { positionCalls.merge(f.here().id, 1, Integer::sum); position.accept(f.here()); continue; }
                if (Set.of("xfm_futures_register_discovery_effect", "xfm_futures_archive_prune_effect").contains(k)) continue;
                if (e.value() instanceof Block child) { Datum d = resolve(k, f); if (!(d instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(child, f.enter(n)); continue; }
                execute(definition(k), f);
            }
        }
        void assertQueue() {
            Set<Node> seen = new HashSet<>(); Node n = exchange.ref("xfm_futures_daily_head"), last = null;
            while (n != null) { assertTrue(seen.add(n), "cycle/duplicate"); assertEquals(1, n.integer("xfm_futures_daily_queued")); last = n; n = n.ref("xfm_futures_daily_next"); }
            assertEquals(exchange.integer("xfm_futures_daily_count"), seen.size()); assertSame(last, exchange.ref("xfm_futures_daily_tail"));
            for (Node node : nodes.values()) assertEquals(seen.contains(node), node.vars.containsKey("xfm_futures_daily_queued"), node.id);
        }
        byte[] write() throws IOException {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (DataOutputStream out = new DataOutputStream(bytes)) {
                out.writeInt(nodes.size()); for (Node n : nodes.values()) {
                    out.writeUTF(n.id); out.writeUTF(n.type); out.writeInt(n.vars.size());
                    for (var e : n.vars.entrySet()) { out.writeUTF(e.getKey()); out.writeBoolean(e.getValue() instanceof Node); if (e.getValue() instanceof Node ref) out.writeUTF(ref.id); else out.writeLong(((Num)e.getValue()).value()); }
                    out.writeInt(n.lists.size()); for (var e : n.lists.entrySet()) { out.writeUTF(e.getKey()); out.writeInt(e.getValue().size()); for (Node item : e.getValue()) out.writeUTF(item.id); }
                }
            }
            return bytes.toByteArray();
        }
        static Vm read(Map<String, Block> program, byte[] bytes) throws IOException {
            Vm v = new Vm(program); v.nodes.clear(); Map<Node, Map<String, String>> refs = new LinkedHashMap<>(); Map<Node, Map<String, List<String>>> lists = new LinkedHashMap<>();
            try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes))) {
                int size = in.readInt(); for (int i = 0; i < size; i++) {
                    String id = in.readUTF(), type = in.readUTF(); Node n;
                    if (id.equals("exchange")) { n = v.exchange; n.vars.clear(); v.nodes.put(id, n); } else n = v.node(id, type);
                    int fields = in.readInt(); for (int j = 0; j < fields; j++) { String key = in.readUTF(); if (in.readBoolean()) refs.computeIfAbsent(n, ignored -> new LinkedHashMap<>()).put(key, in.readUTF()); else n.put(key, in.readLong()); }
                    int listCount = in.readInt(); for (int j = 0; j < listCount; j++) { String key = in.readUTF(); int count = in.readInt(); List<String> ids = new ArrayList<>(); for (int k = 0; k < count; k++) ids.add(in.readUTF()); lists.computeIfAbsent(n, ignored -> new LinkedHashMap<>()).put(key, ids); }
                }
                if (in.read() != -1) throw new IOException("trailing graph data");
            }
            refs.forEach((n, fields) -> fields.forEach((key, id) -> n.put(key, java.util.Objects.requireNonNull(v.nodes.get(id)))));
            lists.forEach((n, fields) -> fields.forEach((key, ids) -> ids.forEach(id -> n.list(key).add(java.util.Objects.requireNonNull(v.nodes.get(id))))));
            return v;
        }
    }
    private static String atom(Value value) { if (!(value instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Value field(Block b, String key) { List<Entry> found = b.named(key); if (found.size() != 1) throw new IllegalArgumentException("one field required " + key); return found.getFirst().value(); }
    private static Block without(Block b, String key) { return new Block(b.entries().stream().filter(e -> !e.key().equals(key)).toList()); }
}
