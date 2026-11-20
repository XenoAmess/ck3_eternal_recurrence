package org.xar.ck3.markets.debt;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.Clausewitz.Value;

/** Runs the actual custody effect and crisis trigger AST. This is software, not CK3.
 * The only trigger port is the existing crisis-narratives game rule. No financial,
 * inheritance, eligibility or list predicate is replaced by a policy-model port.
 * All unknown commands fail. Test assets are fixtures, never written into a Game.
 */
final class CrisisAssetsScriptTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final List<String> INPUTS = List.of("scripted_triggers/xfm_crisis_triggers.txt",
            "script_values/xfm_debt_values.txt", "scripted_effects/xfm_finance_custody.txt");
    private static final List<String> ASSETS = List.of("xfm_free_cents", "xfm_reserved_cents",
            "xfm_holdings_count", "xfm_open_orders_count", "xfm_open_positions_count");

    @Test void actualInheritanceKeepsPrimaryIdentityAndBlocksEveryPositiveEstateAsset() throws IOException {
        for (String asset : ASSETS) {
            Scene s = scene(); Node parent = s.v.node("parent", "character");
            Node estate = s.v.account("estate", parent); estate.put(asset, 1);
            parent.put("primary_heir", s.actor);
            s.v.run("xfm_finance_holder_death_effect", parent);
            assertSame(s.actor, estate.vars.get("xfm_holder"), asset);
            assertEquals(1, estate.integer("xfm_inheritance_state"));
            assertEquals(0, estate.integer("xfm_account_frozen"));
            assertEquals(2, s.actor.list("xfm_accounts").size());
            assertSame(s.primary, s.actor.vars.get("xfm_account"));
            assertEquals(2, estate.integer("xfm_account_id"));
            assertEquals(3_000, s.primary.integer("xfm_total_debt_cents"));
            assertFalse(s.v.eligible(s.primary), asset);
            assertEquals(1, estate.integer(asset), "review must not spend or release the estate");
        }
    }

    @Test void actualZeroEstateInheritanceAndAllKnownZeroPrivateAccountsAllowReview() throws IOException {
        Scene s = scene(); Node parent = s.v.node("parent", "character");
        Node estate = s.v.account("estate", parent); parent.put("primary_heir", s.actor);
        s.v.run("xfm_finance_holder_death_effect", parent);
        assertTrue(s.v.eligible(s.primary));
        assertFalse(s.v.eligible(estate), "the inherited liability itself remains protected");
        assertSame(s.actor, estate.vars.get("xfm_holder"));
        assertEquals(0, estate.integer("xfm_free_cents"));
    }

    @Test void KnownSystemAndOtherOwnedAccountsDoNotBecomeThisPersonsPrivateAssets() throws IOException {
        Scene s = scene(); Node other = s.v.node("other", "character");
        Node system = s.v.account("system", s.actor); system.put("xfm_system_account", 1);
        system.put("xfm_free_cents", 1_000_000); system.vars.remove("xfm_holdings_count");
        Node foreign = s.v.account("foreign", other); foreign.put("xfm_free_cents", 1_000_000);
        s.actor.list("xfm_accounts").add(foreign); // stale index row, still legally owned by other
        assertTrue(s.v.eligible(s.primary));
        assertSame(other, foreign.vars.get("xfm_holder"));
        assertEquals(1_000_000, system.integer("xfm_free_cents"));
    }

    @Test void UnknownAccountIndexOwnershipTypeOrAssetFieldsNeverEstablishZeroWealth() throws IOException {
        for (String missing : ASSETS) {
            Scene s = scene(); Node second = s.v.account("second", s.actor);
            second.vars.remove(missing); assertFalse(s.v.eligible(s.primary), missing);
        }
        for (String missing : List.of("xfm_holder", "xfm_system_account")) {
            Scene s = scene(); Node second = s.v.account("second", s.actor);
            second.vars.remove(missing); assertFalse(s.v.eligible(s.primary), missing);
        }
        Scene bad = scene(); Node unknown = bad.v.node("unknown", "wrong_story");
        bad.actor.list("xfm_accounts").add(unknown); assertFalse(bad.v.eligible(bad.primary));
        Scene absent = scene(); absent.actor.lists.remove("xfm_accounts"); assertFalse(absent.v.eligible(absent.primary));
        Scene illegal = scene(); Node account = illegal.v.account("unknown-system", illegal.actor);
        account.put("xfm_system_account", 2); assertFalse(illegal.v.eligible(illegal.primary));
    }

    @Test void ReceivableWinnerAndFundPartsRemainAssetsAndCannotBeCountedForTheWrongAccount() throws IOException {
        for (String role : List.of("winner", "fund")) {
            Scene s = scene(); Node second = s.v.account("second", s.actor);
            Node claim = s.v.claim("receivable", second, role.equals("winner") ? 1 : 0,
                    second, role.equals("fund") ? 1 : 0);
            second.list("xfm_claims").add(claim);
            assertFalse(s.v.eligible(s.primary), role);
            assertEquals(1, claim.integer(role.equals("winner") ? "xfm_winner_unpaid_cents" : "xfm_fund_recourse_cents"));
        }
        Scene s = scene(); Node other = s.v.account("other-account", s.v.node("other", "character"));
        Node paidWinner = s.v.claim("paid-winner", s.primary, 0, other, 500);
        s.primary.list("xfm_claims").add(paidWinner);
        assertTrue(s.v.eligible(s.primary), "the fund's remaining recourse is not the original winner's asset");
        paidWinner.put("xfm_winner_unpaid_cents", 1); assertFalse(s.v.eligible(s.primary));
        paidWinner.put("xfm_winner_unpaid_cents", 0); paidWinner.put("xfm_fund_recourse_cents", 0);
        assertTrue(s.v.eligible(s.primary), "fully paid historical receipts do not block forever");
    }

    @Test void MissingOrNegativeClaimAmountsAndMissingPositiveClaimPayeeReject() throws IOException {
        for (String field : List.of("xfm_winner_unpaid_cents", "xfm_fund_recourse_cents")) {
            Scene s = scene(); Node c = s.v.claim("claim", s.primary, 0, s.primary, 0);
            s.primary.list("xfm_claims").add(c); c.vars.remove(field);
            assertFalse(s.v.eligible(s.primary), field);
            c.put(field, -1); assertFalse(s.v.eligible(s.primary), field + " negative");
        }
        for (String field : List.of("xfm_creditor_account", "xfm_fund_account")) {
            Scene s = scene(); Node c = s.v.claim("claim", s.primary, 1, s.primary, 1);
            s.primary.list("xfm_claims").add(c); c.vars.remove(field);
            assertFalse(s.v.eligible(s.primary), field);
        }
    }

    @Test void OriginalPlayerAgeRuleStressMaturityReliefAndTerminalGuardsRemainEffective() throws IOException {
        Scene s = scene(); assertTrue(s.v.eligible(s.primary));
        s.actor.ai = false; assertFalse(s.v.eligible(s.primary)); s.actor.ai = true;
        s.actor.adult = false; assertFalse(s.v.eligible(s.primary)); s.actor.adult = true;
        s.actor.alive = false; assertFalse(s.v.eligible(s.primary)); s.actor.alive = true;
        s.actor.put("stress_level", 2); assertFalse(s.v.eligible(s.primary)); s.actor.put("stress_level", 3);
        s.actor.put("gold", 1); assertFalse(s.v.eligible(s.primary)); s.actor.put("gold", 0);
        s.primary.put("xfm_crisis_started_day", 59); assertFalse(s.v.eligible(s.primary)); s.primary.put("xfm_crisis_started_day", 30);
        s.primary.put("xfm_crisis_relief_until", 61); assertFalse(s.v.eligible(s.primary)); s.primary.put("xfm_crisis_relief_until", 0);
        s.primary.put("xfm_crisis_reviews", 1); assertFalse(s.v.eligible(s.primary)); s.primary.put("xfm_crisis_reviews", 2);
        s.v.rule = false; assertFalse(s.v.eligible(s.primary)); s.v.rule = true;
        s.primary.put("xfm_crisis_terminal", 1); assertFalse(s.v.eligible(s.primary));
    }

    private record Scene(Vm v, Node actor, Node primary) { }
    private static Scene scene() throws IOException {
        Map<String, Block> definitions = new LinkedHashMap<>();
        for (String input : INPUTS) {
            Path p = SOURCE.resolve("common").resolve(input);
            if (!Files.exists(p)) p = SOURCE.resolve("../baseline/mod_financial_markets/common").normalize().resolve(input);
            for (Entry e : Clausewitz.parse(Files.readString(p)).entries()) {
                if (!(e.value() instanceof Block b) || definitions.putIfAbsent(e.key(), b) != null)
                    throw new IllegalArgumentException("invalid/duplicate definition " + e.key());
            }
        }
        Vm v = new Vm(definitions); Node actor = v.node("adult-ai", "character");
        actor.put("gold", 0); actor.put("stress_level", 3); actor.put("monthly_character_income_minus_expenses", 0);
        Node primary = v.account("primary", actor); actor.put("xfm_account", primary);
        primary.put("xfm_total_debt_cents", 3_000); primary.put("xfm_max_overdue_days", 40);
        primary.put("xfm_crisis_started_day", 30); primary.put("xfm_crisis_reviews", 2);
        primary.put("xfm_crisis_relief_until", 0); primary.put("xfm_aid_opportunity_recorded", 1);
        primary.put("xfm_crisis_actor", actor); return new Scene(v, actor, primary);
    }
    private static final class Node {
        final String id, type; boolean ai = true, adult = true, alive = true;
        final Map<String, Object> vars = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new HashMap<>();
        Node(String id, String type) { this.id = id; this.type = type; }
        void put(String key, long value) { vars.put(key, BigDecimal.valueOf(value)); }
        void put(String key, Node value) { vars.put(key, value); }
        long integer(String key) { return ((BigDecimal)vars.get(key)).longValueExact(); }
        List<Node> list(String key) { return lists.computeIfAbsent(key, ignored -> new ArrayList<>()); }
    }
    private record Frame(Node here, Node previous) { Frame enter(Node n) { return new Frame(n, here); } }
    private static String atom(Value value) { if (value instanceof Atom a) return a.token(); throw new IllegalArgumentException("atom required"); }
    private static Value field(Block b, String key) { List<Entry> e = b.named(key); if (e.size() != 1) throw new IllegalArgumentException("one " + key); return e.getFirst().value(); }
    private static Block without(Block b, String... keys) { Set<String> removed = Set.of(keys); return new Block(b.entries().stream().filter(e -> !removed.contains(e.key())).toList()); }
    private static final class Vm {
        final Map<String, Block> definitions; final Map<String, Node> scopes = new HashMap<>();
        final Map<String, List<Node>> temporary = new HashMap<>(); final Node exchange;
        boolean rule = true; int accountSequence;
        Vm(Map<String, Block> definitions) { this.definitions = definitions; exchange = node("exchange", "xfm_finance_exchange"); exchange.put("xfm_day", 60); }
        Node node(String id, String type) { return new Node(id, type); }
        Node account(String id, Node holder) {
            Node a = node(id, "xfm_finance_account"); a.put("xfm_holder", holder); a.put("xfm_beneficial_owner", holder);
            a.put("xfm_system_account", 0); a.put("xfm_inheritance_state", 0); a.put("xfm_account_frozen", 0);
            a.put("xfm_account_id", ++accountSequence); for (String key : ASSETS) a.put(key, 0);
            holder.list("xfm_accounts").add(a); return a;
        }
        Node claim(String id, Node creditor, long winner, Node fund, long recourse) {
            Node c = node(id, "xfm_debt_claim"); c.put("xfm_creditor_account", creditor); c.put("xfm_fund_account", fund);
            c.put("xfm_winner_unpaid_cents", winner); c.put("xfm_fund_recourse_cents", recourse); return c;
        }
        Block definition(String name) { Block b = definitions.get(name); if (b == null) throw new IllegalArgumentException("unknown definition " + name); return b; }
        boolean eligible(Node account) { return test(definition("xfm_crisis_terminal_review_trigger"), new Frame(account, null)); }
        void run(String name, Node node) { execute(definition(name), new Frame(node, null)); }
        Object resolve(String token, Frame f) {
            try { return new BigDecimal(token); } catch (NumberFormatException ignored) { }
            int dot = token.indexOf('.'); if (dot > 0) { Object base = resolve(token.substring(0, dot), f); return base instanceof Node n ? resolve(token.substring(dot + 1), f.enter(n)) : null; }
            if (token.equals("this")) return f.here(); if (token.equals("prev")) return f.previous();
            if (token.equals("primary_heir")) return f.here().vars.get(token);
            if (token.equals("global_var:xfm_exchange")) return exchange;
            if (token.startsWith("var:")) return f.here().vars.get(token.substring(4));
            if (token.startsWith("scope:")) return scopes.get(token.substring(6));
            if (Set.of("gold", "stress_level", "monthly_character_income_minus_expenses").contains(token)) return f.here().vars.get(token);
            if (definitions.containsKey(token)) return value(definition(token), f);
            return token;
        }
        Object evaluate(Value value, Frame f) { return value instanceof Block b ? value(b, f) : resolve(atom(value), f); }
        BigDecimal number(Object value) { if (value instanceof BigDecimal n) return n; throw new IllegalArgumentException("known number required: " + value); }
        BigDecimal value(Block b, Frame f) {
            BigDecimal n = BigDecimal.ZERO;
            for (Entry e : b.entries()) {
                if (e.key().equals("floor")) { n = n.setScale(0, RoundingMode.FLOOR); continue; }
                BigDecimal x = number(evaluate(e.value(), f));
                n = switch (e.key()) { case "value" -> x; case "add" -> n.add(x); case "subtract" -> n.subtract(x);
                    case "multiply" -> n.multiply(x); case "min" -> n.max(x); case "max" -> n.min(x);
                    default -> throw new IllegalArgumentException("unsupported value command " + e.key()); };
            }
            return n;
        }
        boolean test(Block b, Frame f) { boolean all = true; for (Entry e : b.entries()) all &= check(e, f); return all; }
        boolean check(Entry e, Frame f) {
            String k = e.key();
            if (k.equals("AND")) return test((Block)e.value(), f);
            if (k.equals("OR") || k.equals("NOT")) { boolean any = false; for (Entry child : ((Block)e.value()).entries()) any |= check(child, f); return k.equals("OR") ? any : !any; }
            if (k.equals("trigger_if")) { Block b = (Block)e.value(); return !test(b.block("limit"), f) || test(without(b, "limit"), f); }
            if (k.equals("exists")) return resolve(atom(e.value()), f) != null;
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if (k.equals("xfm_config_crisis_narratives_trigger")) return rule;
            if (k.equals("any_in_list")) { Block b = (Block)e.value(); boolean any = false; for (Node n : f.here().lists.getOrDefault(atom(field(b, "variable")), List.of())) any |= test(without(b, "variable"), f.enter(n)); return any; }
            if (k.endsWith("_trigger") && definitions.containsKey(k)) return test(definition(k), f);
            if (e.value() instanceof Block b) { Object scope = resolve(k, f); return scope instanceof Node n && test(b, f.enter(n)); }
            Object left = resolve(k, f), right = evaluate(e.value(), f);
            // Missing ordinary comparison inputs fail closed; new optional checks
            // are staged through trigger_if. No missing number is silently zero.
            if (left == null || right == null) return false;
            if (left instanceof BigDecimal a && right instanceof BigDecimal b) {
                int cmp = a.compareTo(b); return switch (e.operator()) { case "=" -> cmp == 0; case "!=" -> cmp != 0;
                    case ">" -> cmp > 0; case "<" -> cmp < 0; case ">=" -> cmp >= 0; case "<=" -> cmp <= 0;
                    default -> throw new IllegalArgumentException(e.operator()); };
            }
            return switch (e.operator()) { case "=" -> Objects.equals(left, right); case "!=" -> !Objects.equals(left, right);
                default -> throw new IllegalArgumentException("non-number comparison " + k); };
        }
        void execute(Block b, Frame f) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                String k = e.key();
                if (k.equals("if")) { Block c = (Block)e.value(); chain = test(c.block("limit"), f); if (chain) execute(without(c, "limit"), f); continue; }
                if (k.equals("else")) { if (!chain) execute((Block)e.value(), f); chain = false; continue; }
                if (k.equals("else_if")) { Block c = (Block)e.value(); if (!chain && test(c.block("limit"), f)) { execute(without(c, "limit"), f); chain = true; } continue; }
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("set_variable")) { Block c = (Block)e.value(); f.here().vars.put(atom(field(c, "name")), evaluate(field(c, "value"), f)); continue; }
                if (k.equals("every_in_list")) { Block c = (Block)e.value(); List<Node> list;
                    if (!c.named("list").isEmpty()) list = temporary.getOrDefault(atom(field(c, "list")), List.of());
                    else list = f.here().lists.getOrDefault(atom(field(c, "variable")), List.of());
                    for (Node n : List.copyOf(list)) if (test(c.block("limit"), f.enter(n))) execute(without(c, "list", "variable", "limit"), f.enter(n)); continue;
                }
                if (k.equals("add_to_variable_list")) { Block c = (Block)e.value(); f.here().list(atom(field(c, "name"))).add((Node)evaluate(field(c, "target"), f)); continue; }
                if (k.equals("add_to_temporary_list")) { temporary.computeIfAbsent(atom(e.value()), ignored -> new ArrayList<>()).add(f.here()); continue; }
                if (e.value() instanceof Block c) { Object scope = resolve(k, f); if (!(scope instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(c, f.enter(n)); continue; }
                throw new IllegalArgumentException("unsupported effect command " + k);
            }
        }
    }
}
