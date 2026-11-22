package org.xar.ck3.markets.debt;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.HashSet;
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
 * Static positive random-list weights use explicit authored engine-RNG samples; no default draw.
 * Real context properties are fixture observations; missing fields/scopes never become zero.
 * All unknown commands fail. Test assets are fixtures, never written into a Game.
 * No death or news-dispatch primitive is supplied or executed by these software tests.
 */
final class CrisisAssetsScriptTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final List<String> INPUTS = List.of("scripted_triggers/xfm_crisis_triggers.txt",
            "script_values/xfm_debt_values.txt", "scripted_effects/xfm_finance_custody.txt",
            "scripted_effects/xfm_crisis_scenes.txt", "scripted_effects/xfm_crisis_progression.txt");
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

    @Test void allTwentyNarrativesRunTheOriginalContextualWeightedSelectionOnce() throws IOException {
        for (int expected = 1; expected <= 20; expected++) {
            Scene s = narrativeScene(); Node location = (Node) s.actor.vars.get("location");
            switch (expected) {
                case 1 -> s.actor.vars.put("is_landed", true);
                case 2 -> location.vars.put("terrain", "plains");
                case 3 -> location.vars.put("is_riverside_province", true);
                case 4 -> location.vars.put("is_coastal", true);
                case 5 -> location.vars.put("terrain", "taiga");
                case 6 -> location.vars.put("terrain", "mountains");
                case 7 -> location.vars.put("terrain", "forest");
                case 8 -> location.vars.put("terrain", "desert");
                case 9 -> s.actor.put("stewardship", 12);
                case 10 -> { s.actor.vars.put("is_landed", true); s.actor.put("dynasty", s.v.node("dynasty", "dynasty")); }
                case 11 -> s.actor.traits.add("gregarious");
                case 12 -> s.actor.traits.add("shy");
                case 13 -> s.actor.vars.put("is_knight", true);
                case 14 -> s.actor.put("learning", 12);
                case 15 -> s.actor.traits.add("devoted");
                case 16 -> s.actor.vars.put("is_imprisoned", true);
                case 17 -> { s.actor.vars.put("is_at_war", true); s.actor.put("martial", 8); }
                case 18 -> s.actor.traits.add("lifestyle_blademaster");
                case 19 -> s.actor.put("dynasty", s.v.node("dynasty", "dynasty"));
                case 20 -> { /* Real unconditional fallback; no invented context. */ }
                default -> throw new AssertionError(expected);
            }
            assertTrue(s.v.eligible(s.primary), "Only the authored mature adult-AI context is used");
            Map<String, Object> accountBefore = Map.copyOf(s.primary.vars), actorBefore = Map.copyOf(s.actor.vars);
            Map<String, Object> locationBefore = Map.copyOf(location.vars);
            // In the landed-dynasty context, branch1 occupies [0,10); branch10 starts at10.
            assertEquals(expected, selectNarrative(s, expected == 10 ? 10 : 0));
            assertEquals(List.of(20L, (long) expected), s.v.sceneWrites, "Default plus one actual branch result");
            assertEquals(1, s.v.randomChoices); assertTrue(s.v.randomDraws.isEmpty());
            Map<String, Object> accountAfter = new LinkedHashMap<>(s.primary.vars); accountAfter.remove("xfm_news_scene");
            assertEquals(accountBefore, accountAfter, "Selection cannot spend assets, erase debt or change eligibility");
            assertEquals(actorBefore, s.actor.vars); assertEquals(locationBefore, location.vars); assertTrue(s.actor.alive);
        }
    }

    @Test void actualSceneConditionsKeepMissingScopesThresholdsAndOverlappingWeightsDistinct() throws IOException {
        for (String missing : List.of("actor-scope", "location", "terrain", "stewardship", "learning", "martial", "dynasty")) {
            Scene s = narrativeScene();
            if (missing.equals("actor-scope")) s.v.scopes.remove("xfm_crisis_actor");
            else if (missing.equals("terrain")) ((Node) s.actor.vars.get("location")).vars.remove("terrain");
            else s.actor.vars.remove(missing);
            assertEquals(20, selectNarrative(s, 0), "Missing context never authorizes a conditional narrative: " + missing);
        }
        for (String terrain : List.of("farmlands", "floodplains", "desert_mountains", "jungle", "drylands", "steppe")) {
            Scene s = narrativeScene(); ((Node) s.actor.vars.get("location")).vars.put("terrain", terrain);
            int expected = switch (terrain) { case "farmlands", "floodplains" -> 2; case "desert_mountains" -> 6; case "jungle" -> 7; default -> 8; };
            assertEquals(expected, selectNarrative(s, 0), terrain);
        }
        for (String skill : List.of("stewardship", "learning")) {
            Scene below = narrativeScene(); below.actor.put(skill, 11); assertEquals(20, selectNarrative(below, 0));
            Scene exact = narrativeScene(); exact.actor.put(skill, 12); assertEquals(skill.equals("stewardship") ? 9 : 14, selectNarrative(exact, 0));
        }
        for (String defect : List.of("peace", "martial7", "missing-martial")) {
            Scene s = narrativeScene(); s.actor.vars.put("is_at_war", true); s.actor.put("martial", 8);
            if (defect.equals("peace")) s.actor.vars.put("is_at_war", false);
            else if (defect.equals("martial7")) s.actor.put("martial", 7);
            else s.actor.vars.remove("martial");
            assertEquals(20, selectNarrative(s, 0), "Scene17 requires actual war and martial>=8: " + defect);
        }
        Scene otherTrait = narrativeScene(); otherTrait.actor.traits.add("brave");
        assertEquals(20, selectNarrative(otherTrait, 0), "Another martial trait is not blademaster");
        for (int[] row : new int[][]{{0,1},{9,1},{10,10},{19,10},{20,19},{29,19},{30,20},{129,20}}) {
            Scene s = narrativeScene(); s.actor.vars.put("is_landed", true); s.actor.put("dynasty", s.v.node("dynasty", "dynasty"));
            assertEquals(row[1], selectNarrative(s, row[0]), "Actual eligible weights10/10/10/100 at draw" + row[0]);
            assertEquals(1, s.v.randomChoices);
        }
    }

    @Test void actualTerminalEntryRejectsProtectedCharactersBeforeSelectionOrAnyWrite() throws IOException {
        for (String defect : List.of("player", "child", "dead", "cash", "reserved", "holdings", "orders", "positions",
                "estate", "receivable", "rule", "relief", "immature", "one-review", "no-help", "holder-changed",
                "already-terminal", "missing-asset-field", "no-debt", "not-overdue", "stress2")) {
            Scene s = narrativeScene(); assertTrue(s.v.eligible(s.primary));
            switch (defect) {
                case "player" -> s.actor.ai = false;
                case "child" -> s.actor.adult = false;
                case "dead" -> s.actor.alive = false;
                case "cash" -> s.primary.put("xfm_free_cents", 1);
                case "reserved" -> s.primary.put("xfm_reserved_cents", 1);
                case "holdings" -> s.primary.put("xfm_holdings_count", 1);
                case "orders" -> s.primary.put("xfm_open_orders_count", 1);
                case "positions" -> s.primary.put("xfm_open_positions_count", 1);
                case "estate" -> { Node estate = s.v.account("inherited-private", s.actor); estate.put("xfm_inheritance_state", 1); estate.put("xfm_free_cents", 1); }
                case "receivable" -> s.primary.list("xfm_claims").add(s.v.claim("unpaid", s.primary, 1, s.primary, 0));
                case "rule" -> s.v.rule = false;
                case "relief" -> s.primary.put("xfm_crisis_relief_until", 61);
                case "immature" -> s.primary.put("xfm_crisis_started_day", 59);
                case "one-review" -> s.primary.put("xfm_crisis_reviews", 1);
                case "no-help" -> s.primary.vars.remove("xfm_aid_opportunity_recorded");
                case "holder-changed" -> s.primary.put("xfm_crisis_actor", s.v.node("old-holder", "character"));
                case "already-terminal" -> s.primary.put("xfm_crisis_terminal", 1);
                case "missing-asset-field" -> s.primary.vars.remove("xfm_holdings_count");
                case "no-debt" -> s.primary.put("xfm_total_debt_cents", 0);
                case "not-overdue" -> s.primary.put("xfm_max_overdue_days", 29);
                case "stress2" -> s.actor.put("stress_level", 2);
                default -> throw new AssertionError(defect);
            }
            assertFalse(s.v.eligible(s.primary), defect);
            Map<String, Object> before = Map.copyOf(s.primary.vars), actorBefore = Map.copyOf(s.actor.vars);
            boolean aliveBefore = s.actor.alive;
            // Run the actual outer if/limit, not a Java policy port; no draw is supplied to hide a leak.
            s.v.run("xfm_crisis_terminal_effect", s.primary);
            assertEquals(before, s.primary.vars, defect); assertEquals(actorBefore, s.actor.vars, defect);
            assertEquals(aliveBefore, s.actor.alive, defect); assertEquals(0, s.v.randomChoices, defect);
            assertTrue(s.v.sceneWrites.isEmpty(), defect); assertTrue(s.v.randomDraws.isEmpty(), defect);
        }
    }

    @Test void weightedPrimitiveUsesOnlyEligibleStaticWeightsAndFailsOutsideItsExplicitSubset() throws IOException {
        Block weighted = Clausewitz.parse("random_list = { 2 = { trigger = { has_variable = enabled } set_variable = { name = picked value = 11 } } 3 = { set_variable = { name = picked value = 22 } } }");
        for (int draw = 0; draw < 5; draw++) {
            Scene s = scene(); s.primary.put("enabled", 1); s.v.randomDraws.add(draw);
            s.v.execute(weighted, new Frame(s.primary, null));
            assertEquals(draw < 2 ? 11 : 22, s.primary.integer("picked")); assertEquals(1, s.v.randomChoices);
        }
        Scene filtered = scene(); filtered.v.randomDraws.add(2); filtered.v.execute(weighted, new Frame(filtered.primary, null));
        assertEquals(22, filtered.primary.integer("picked")); assertEquals(1, filtered.v.randomChoices);
        Scene none = scene(); none.v.execute(Clausewitz.parse("random_list = { 2 = { trigger = { has_variable = missing } set_variable = { name = picked value = 11 } } }"), new Frame(none.primary, null));
        assertFalse(none.primary.vars.containsKey("picked")); assertEquals(0, none.v.randomChoices);
        for (int bad : List.of(-1, 5)) {
            Scene s = scene(); s.primary.put("enabled", 1); s.v.randomDraws.add(bad);
            assertThrows(IllegalArgumentException.class, () -> s.v.execute(weighted, new Frame(s.primary, null)));
            assertFalse(s.primary.vars.containsKey("picked"));
        }
        Scene noDraw = scene(); assertThrows(IllegalArgumentException.class, () -> noDraw.v.execute(weighted, new Frame(noDraw.primary, null)));
        for (String unsupportedWeight : List.of("0", "-1", "1.5")) {
            Scene s = scene(); s.v.randomDraws.add(0);
            Block b = Clausewitz.parse("random_list = { " + unsupportedWeight + " = { set_variable = { name = picked value = 1 } } }");
            assertThrows(IllegalArgumentException.class, () -> s.v.execute(b, new Frame(s.primary, null)), "Static positive-weight subset only");
        }
        Scene unknown = scene(); unknown.v.randomDraws.add(0);
        assertThrows(IllegalArgumentException.class, () -> unknown.v.execute(Clausewitz.parse("random_list = { 1 = { unsupported_scene_effect = yes } }"), new Frame(unknown.primary, null)));
        assertThrows(IllegalArgumentException.class, () -> unknown.v.test(Clausewitz.parse("unknown_scene_trigger = yes"), new Frame(unknown.primary, null)));
        assertThrows(IllegalArgumentException.class, () -> unknown.v.test(Clausewitz.parse("unknown_scene_field = unknown_scene_field"), new Frame(unknown.primary, null)));
        assertThrows(IllegalArgumentException.class, () -> unknown.v.test(Clausewitz.parse("exists = unknown_scene_reference"), new Frame(unknown.primary, null)));
    }

    @Test void bothLocalesProvideTwentyDistinctTitlesAndDescriptionsForTheOriginalSceneIds() throws IOException {
        for (String language : List.of("english", "simp_chinese")) {
            List<String> lines = Files.readString(SOURCE.resolve("localization").resolve(language).resolve("xfm_crisis_l_" + language + ".yml")).lines().map(String::strip).toList();
            Set<String> titles = new HashSet<>(), descriptions = new HashSet<>();
            for (int id = 1; id <= 20; id++) {
                for (String kind : List.of("title", "desc")) {
                    String key = "xfm_crisis_scene_" + id + "_" + kind + ":0 ";
                    List<String> entries = lines.stream().filter(line -> line.startsWith(key)).toList();
                    assertEquals(1, entries.size(), language + key);
                    String text = entries.getFirst().substring(key.length());
                    assertTrue(text.startsWith("\"") && text.endsWith("\"") && text.length() > 2, language + key);
                    assertTrue((kind.equals("title") ? titles : descriptions).add(text), "Narratives need distinct text: " + language + key);
                }
            }
            assertEquals(20, titles.size()); assertEquals(20, descriptions.size());
        }
    }

    private static Scene narrativeScene() throws IOException {
        Scene s = scene();
        for (String property : List.of("is_landed", "is_knight", "is_at_war", "is_imprisoned")) s.actor.vars.put(property, false);
        for (String skill : List.of("stewardship", "martial", "learning")) s.actor.put(skill, 0);
        Node location = s.v.node("known-location", "province"); location.vars.put("terrain", "hills");
        location.vars.put("is_riverside_province", false); location.vars.put("is_coastal", false);
        s.actor.put("location", location); s.v.scopes.put("xfm_crisis_actor", s.actor); return s;
    }
    private static long selectNarrative(Scene s, int draw) {
        s.v.randomDraws.add(draw); s.v.run("xfm_crisis_select_scene_effect", s.primary); return s.primary.integer("xfm_news_scene");
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
        final Set<String> traits = new HashSet<>();
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
        final ArrayDeque<Integer> randomDraws = new ArrayDeque<>();
        final List<Long> sceneWrites = new ArrayList<>(); int randomChoices;
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
            if (Set.of("primary_heir", "location", "dynasty").contains(token)) return f.here().vars.get(token);
            if (token.equals("global_var:xfm_exchange")) return exchange;
            if (token.startsWith("var:")) return f.here().vars.get(token.substring(4));
            if (token.startsWith("scope:")) return scopes.get(token.substring(6));
            if (Set.of("gold", "stress_level", "monthly_character_income_minus_expenses", "terrain", "stewardship", "martial", "learning").contains(token)) return f.here().vars.get(token);
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
            if (k.equals("exists")) {
                String operand = atom(e.value()); Object observed = resolve(operand, f);
                if (observed instanceof String text && text.equals(operand)) throw new IllegalArgumentException("unsupported exists operand " + operand);
                return observed != null;
            }
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if (Set.of("is_landed", "is_knight", "is_at_war", "is_imprisoned", "is_riverside_province", "is_coastal").contains(k)) {
                Object observed = f.here().vars.get(k); if (observed == null) return false;
                String expected = atom(e.value());
                if (!(observed instanceof Boolean flag) || !(expected.equals("yes") || expected.equals("no"))) throw new IllegalArgumentException("known boolean property required " + k);
                return flag == expected.equals("yes");
            }
            if (k.equals("has_trait")) return f.here().traits.contains(atom(e.value()));
            if (k.equals("xfm_config_crisis_narratives_trigger")) return rule;
            if (k.equals("any_in_list")) { Block b = (Block)e.value(); boolean any = false; for (Node n : f.here().lists.getOrDefault(atom(field(b, "variable")), List.of())) any |= test(without(b, "variable"), f.enter(n)); return any; }
            if (k.endsWith("_trigger")) return test(definition(k), f);
            if (e.value() instanceof Block b) { Object scope = resolve(k, f); return scope instanceof Node n && test(b, f.enter(n)); }
            Object left = resolve(k, f), right = evaluate(e.value(), f);
            // Missing ordinary comparison inputs fail closed; new optional checks
            // are staged through trigger_if. No missing number is silently zero.
            if (left == null || right == null) return false;
            if (left instanceof String text && text.equals(k)) throw new IllegalArgumentException("unsupported trigger field " + k);
            if (left instanceof BigDecimal a && right instanceof BigDecimal b) {
                int cmp = a.compareTo(b); return switch (e.operator()) { case "=" -> cmp == 0; case "!=" -> cmp != 0;
                    case ">" -> cmp > 0; case "<" -> cmp < 0; case ">=" -> cmp >= 0; case "<=" -> cmp <= 0;
                    default -> throw new IllegalArgumentException(e.operator()); };
            }
            return switch (e.operator()) { case "=" -> Objects.equals(left, right); case "!=" -> !Objects.equals(left, right);
                default -> throw new IllegalArgumentException("non-number comparison " + k); };
        }
        // Only the actual scene selector's static positive-integer weighted subset is supported.
        // Samples are an explicit engine-randomness port, not a substitute for eligibility or effects.
        void randomList(Block options, Frame f) {
            List<Block> eligible = new ArrayList<>(); List<Integer> ends = new ArrayList<>(); int total = 0;
            for (Entry option : options.entries()) {
                int weight;
                try { weight = new BigDecimal(option.key()).intValueExact(); }
                catch (ArithmeticException | NumberFormatException error) { throw new IllegalArgumentException("unsupported static random weight " + option.key(), error); }
                if (weight <= 0 || !(option.value() instanceof Block branch)) throw new IllegalArgumentException("positive static weight/block required");
                List<Entry> predicates = branch.named("trigger");
                if (predicates.size() > 1 || !predicates.isEmpty() && !(predicates.getFirst().value() instanceof Block)) throw new IllegalArgumentException("one trigger block required");
                if (predicates.isEmpty() || test((Block) predicates.getFirst().value(), f)) {
                    total = Math.addExact(total, weight); eligible.add(without(branch, "trigger")); ends.add(total);
                }
            }
            if (eligible.isEmpty()) return;
            if (randomDraws.isEmpty()) throw new IllegalArgumentException("explicit engine-random sample required");
            int draw = randomDraws.removeFirst();
            if (draw < 0 || draw >= total) throw new IllegalArgumentException("random sample outside eligible total");
            for (int i = 0; i < eligible.size(); i++) if (draw < ends.get(i)) { randomChoices++; execute(eligible.get(i), f); return; }
            throw new AssertionError("eligible random selection missing");
        }
        void execute(Block b, Frame f) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                String k = e.key();
                if (k.equals("random_list")) { randomList((Block) e.value(), f); continue; }
                if (k.equals("if")) { Block c = (Block)e.value(); chain = test(c.block("limit"), f); if (chain) execute(without(c, "limit"), f); continue; }
                if (k.equals("else")) { if (!chain) execute((Block)e.value(), f); chain = false; continue; }
                if (k.equals("else_if")) { Block c = (Block)e.value(); if (!chain && test(c.block("limit"), f)) { execute(without(c, "limit"), f); chain = true; } continue; }
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("set_variable")) {
                    Block c = (Block) e.value(); String name = atom(field(c, "name")); Object observed = evaluate(field(c, "value"), f);
                    f.here().vars.put(name, observed);
                    if (name.equals("xfm_news_scene")) sceneWrites.add(number(observed).longValueExact());
                    continue;
                }
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
