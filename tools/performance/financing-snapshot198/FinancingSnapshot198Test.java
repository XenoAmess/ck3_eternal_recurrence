package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Same-package access to the existing static DATA projection; no authority or performance fixture. */
public final class FinancingSnapshot198Test {
    @Test
    void sixLiteralCasesPreserveProjectedRolesOrderAndReferences() {
        noOuterUpdateStillProjectsAndKeepsMalformedValues();
        actorOnlyKeepsAnEqualProjectedValueAndItsLeafReferences();
        goldOnlyKeepsSignedExactRawAndInputOrder();
        warsOnlyProjectsObjectRowsAndKeepsOtherValues();
        diagnosticsOnlyKeepsMalformedHelloAsOriginalData();
        allBranchesKeepAliasesSeparateAndProjectNestedHello();
    }

    private static void noOuterUpdateStillProjectsAndKeepsMalformedValues() {
        Text secret = new Text("excluded-outer");
        IntegerValue date = number("53144328");
        Text actor = new Text("malformed-actor");
        Bool wars = new Bool(false);
        IntegerValue gold = number("-7");
        Bool paused = new Bool(true);
        Obj original = literal("secret_outer", secret, "date_raw", date, "diagnostics", Nil.INSTANCE,
                "played_character", actor, "active_wars", wars, "played_character_gold", gold, "paused", paused);
        Obj expected = literal("date_raw", date, "diagnostics", Nil.INSTANCE, "played_character", actor,
                "active_wars", wars, "played_character_gold", gold, "paused", paused);

        Obj result = OrdinaryFinanceCollector.financingSnapshot(original);

        assertNotSame(original, result); // The initial projection still runs even with no outer update.
        assertEquals(expected, result);
        keys(result, "date_raw", "diagnostics", "played_character", "active_wars", "played_character_gold", "paused");
        refs(result, "date_raw", date, "diagnostics", Nil.INSTANCE, "played_character", actor,
                "active_wars", wars, "played_character_gold", gold, "paused", paused);
        assertFalse(result.members().containsKey("secret_outer"));
        assertFalse(result.members().containsKey("map_ready"));
        assertEquals(literal("secret_outer", secret, "date_raw", date, "diagnostics", Nil.INSTANCE,
                "played_character", actor, "active_wars", wars, "played_character_gold", gold, "paused", paused), original);
        keys(original, "secret_outer", "date_raw", "diagnostics", "played_character", "active_wars", "played_character_gold", "paused");
    }

    private static void actorOnlyKeepsAnEqualProjectedValueAndItsLeafReferences() {
        Bool alive = new Bool(true);
        IntegerValue id = number("9007199254740993");
        IntegerValue date = number("53144328");
        Text secret = new Text("excluded-outer");
        Obj actor = literal("alive", alive, "character_id", id);
        Obj original = literal("date_raw", date, "played_character", actor, "secret_outer", secret, "played_character_id", id);
        Obj expectedActor = literal("alive", alive, "character_id", id);
        Obj expected = literal("date_raw", date, "played_character", expectedActor, "played_character_id", id);

        Obj result = OrdinaryFinanceCollector.financingSnapshot(original);

        assertEquals(expected, result);
        keys(result, "date_raw", "played_character", "played_character_id");
        Obj projected = child(result, "played_character");
        assertEquals(actor, projected);
        assertNotSame(actor, projected);
        keys(projected, "alive", "character_id");
        refs(projected, "alive", alive, "character_id", id);
        refs(result, "date_raw", date, "played_character_id", id);
        assertEquals(literal("date_raw", date, "played_character", actor, "secret_outer", secret, "played_character_id", id), original);
        keys(original, "date_raw", "played_character", "secret_outer", "played_character_id");
        refs(original, "played_character", actor, "secret_outer", secret);
        keys(actor, "alive", "character_id");
    }

    private static void goldOnlyKeepsSignedExactRawAndInputOrder() {
        IntegerValue raw = number("-9007199254740993");
        IntegerValue scale = number("100000");
        IntegerValue revision = number("8");
        Bool paused = new Bool(true);
        Text secret = new Text("excluded-gold");
        Obj gold = literal("secret_gold", secret, "raw", raw, "scale", scale);
        Obj original = literal("paused", paused, "played_character_gold", gold, "secret_outer", secret, "revision", revision);
        Obj expected = literal("paused", paused, "played_character_gold", literal("raw", raw, "scale", scale), "revision", revision);

        Obj result = OrdinaryFinanceCollector.financingSnapshot(original);

        assertEquals(expected, result);
        keys(result, "paused", "played_character_gold", "revision");
        Obj projected = child(result, "played_character_gold");
        assertNotSame(gold, projected);
        keys(projected, "raw", "scale");
        refs(projected, "raw", raw, "scale", scale);
        refs(result, "paused", paused, "revision", revision);
        assertEquals(literal("paused", paused, "played_character_gold", literal("secret_gold", secret, "raw", raw, "scale", scale),
                "secret_outer", secret, "revision", revision), original);
        keys(original, "paused", "played_character_gold", "secret_outer", "revision");
        refs(original, "played_character_gold", gold, "secret_outer", secret);
        keys(gold, "secret_gold", "raw", "scale");
    }

    private static void warsOnlyProjectsObjectRowsAndKeepsOtherValues() {
        IntegerValue id = number("9007199254740995");
        IntegerValue revision = number("9");
        Text secret = new Text("excluded-war");
        Text malformedRow = new Text("non-object-war-row");
        Obj row = literal("secret_war", secret, "war_id", id);
        Arr wars = new Arr(List.of(row, malformedRow, Nil.INSTANCE));
        Obj original = literal("active_wars", wars, "secret_outer", secret, "native_revision", revision);
        Obj expected = literal("active_wars", new Arr(List.of(literal("war_id", id), malformedRow, Nil.INSTANCE)), "native_revision", revision);

        Obj result = OrdinaryFinanceCollector.financingSnapshot(original);

        assertEquals(expected, result);
        keys(result, "active_wars", "native_revision");
        Arr projected = assertInstanceOf(Arr.class, result.get("active_wars"));
        assertNotSame(wars, projected);
        Obj projectedRow = assertInstanceOf(Obj.class, projected.items().get(0));
        assertNotSame(row, projectedRow);
        keys(projectedRow, "war_id");
        assertSame(id, projectedRow.get("war_id"));
        assertSame(malformedRow, projected.items().get(1));
        assertSame(Nil.INSTANCE, projected.items().get(2));
        assertSame(revision, result.get("native_revision"));
        assertEquals(literal("active_wars", new Arr(List.of(literal("secret_war", secret, "war_id", id), malformedRow, Nil.INSTANCE)),
                "secret_outer", secret, "native_revision", revision), original);
        keys(original, "active_wars", "secret_outer", "native_revision");
        refs(original, "active_wars", wars, "secret_outer", secret);
        assertSame(row, wars.items().get(0));
        keys(row, "secret_war", "war_id");
    }

    private static void diagnosticsOnlyKeepsMalformedHelloAsOriginalData() {
        Text hello = new Text("non-object-hello");
        IntegerValue pid = number("42");
        IntegerValue generation = number("11");
        Bool ready = new Bool(true);
        Text secret = new Text("excluded-diagnostics");
        Obj diagnostics = literal("secret_diag", secret, "hello", hello, "bridge_pid", pid, "connection_generation", generation);
        Obj original = literal("diagnostics", diagnostics, "map_ready", ready, "secret_outer", secret);
        Obj expected = literal("diagnostics", literal("hello", hello, "bridge_pid", pid, "connection_generation", generation), "map_ready", ready);

        Obj result = OrdinaryFinanceCollector.financingSnapshot(original);

        assertEquals(expected, result);
        keys(result, "diagnostics", "map_ready");
        Obj projected = child(result, "diagnostics");
        assertNotSame(diagnostics, projected);
        keys(projected, "hello", "bridge_pid", "connection_generation");
        refs(projected, "hello", hello, "bridge_pid", pid, "connection_generation", generation);
        assertSame(ready, result.get("map_ready"));
        assertEquals(literal("diagnostics", literal("secret_diag", secret, "hello", hello, "bridge_pid", pid, "connection_generation", generation),
                "map_ready", ready, "secret_outer", secret), original);
        keys(original, "diagnostics", "map_ready", "secret_outer");
        assertSame(diagnostics, original.get("diagnostics"));
        keys(diagnostics, "secret_diag", "hello", "bridge_pid", "connection_generation");
    }

    private static void allBranchesKeepAliasesSeparateAndProjectNestedHello() {
        IntegerValue id = number("9007199254740997");
        IntegerValue raw = number("-9007199254740999");
        IntegerValue scale = number("100000");
        IntegerValue date = number("53144328");
        IntegerValue pid = number("43");
        IntegerValue generation = number("12");
        Bool alive = new Bool(true);
        Bool ready = new Bool(true);
        Text secret = new Text("excluded-data");
        Text executable = new Text("data-executable-hash");
        Text game = new Text("data-game-version");
        Text expectedHash = new Text("data-expected-hash");
        Text expectedVersion = new Text("data-expected-version");
        Obj shared = literal("raw", raw, "war_id", id, "alive", alive, "scale", scale, "character_id", id, "secret_shared", secret);
        Arr wars = new Arr(List.of(shared));
        Obj hello = literal("executable_sha256", executable, "secret_build", secret, "game_version", game,
                "expected_ck3_sha256", expectedHash, "expected_ck3_version", expectedVersion);
        Obj diagnostics = literal("hello", hello, "secret_diag", secret, "connection_generation", generation, "bridge_pid", pid);
        Obj original = literal("diagnostics", diagnostics, "secret_outer", secret, "active_wars", wars, "played_character_gold", shared,
                "map_ready", ready, "played_character", shared, "played_character_id", id, "date_raw", date);
        Obj expectedHello = literal("executable_sha256", executable, "game_version", game, "expected_ck3_sha256", expectedHash, "expected_ck3_version", expectedVersion);
        Obj expected = literal("diagnostics", literal("hello", expectedHello, "connection_generation", generation, "bridge_pid", pid),
                "active_wars", new Arr(List.of(literal("war_id", id))), "played_character_gold", literal("raw", raw, "scale", scale),
                "map_ready", ready, "played_character", literal("alive", alive, "character_id", id), "played_character_id", id, "date_raw", date);

        Obj result = OrdinaryFinanceCollector.financingSnapshot(original);

        assertEquals(expected, result);
        keys(result, "diagnostics", "active_wars", "played_character_gold", "map_ready", "played_character", "played_character_id", "date_raw");
        Obj actor = child(result, "played_character");
        Obj gold = child(result, "played_character_gold");
        Obj projectedDiagnostics = child(result, "diagnostics");
        Obj projectedHello = child(projectedDiagnostics, "hello");
        Arr projectedWars = assertInstanceOf(Arr.class, result.get("active_wars"));
        Obj war = assertInstanceOf(Obj.class, projectedWars.items().get(0));
        assertNotSame(shared, actor); assertNotSame(shared, gold); assertNotSame(shared, war);
        assertNotSame(wars, projectedWars); assertNotSame(diagnostics, projectedDiagnostics); assertNotSame(hello, projectedHello);
        keys(actor, "alive", "character_id"); keys(gold, "raw", "scale"); keys(war, "war_id");
        keys(projectedDiagnostics, "hello", "connection_generation", "bridge_pid");
        keys(projectedHello, "executable_sha256", "game_version", "expected_ck3_sha256", "expected_ck3_version");
        refs(result, "map_ready", ready, "played_character_id", id, "date_raw", date);
        refs(actor, "alive", alive, "character_id", id); refs(gold, "raw", raw, "scale", scale); assertSame(id, war.get("war_id"));
        refs(projectedDiagnostics, "connection_generation", generation, "bridge_pid", pid);
        refs(projectedHello, "executable_sha256", executable, "game_version", game, "expected_ck3_sha256", expectedHash, "expected_ck3_version", expectedVersion);
        assertEquals(literal("diagnostics", diagnostics, "secret_outer", secret, "active_wars", wars, "played_character_gold", shared,
                "map_ready", ready, "played_character", shared, "played_character_id", id, "date_raw", date), original);
        keys(original, "diagnostics", "secret_outer", "active_wars", "played_character_gold", "map_ready", "played_character", "played_character_id", "date_raw");
        refs(original, "diagnostics", diagnostics, "active_wars", wars, "played_character_gold", shared, "played_character", shared, "secret_outer", secret);
        keys(shared, "raw", "war_id", "alive", "scale", "character_id", "secret_shared");
        refs(shared, "raw", raw, "war_id", id, "alive", alive, "scale", scale, "character_id", id, "secret_shared", secret);
        assertSame(shared, wars.items().get(0));
        keys(diagnostics, "hello", "secret_diag", "connection_generation", "bridge_pid");
        refs(diagnostics, "hello", hello, "secret_diag", secret);
        keys(hello, "executable_sha256", "secret_build", "game_version", "expected_ck3_sha256", "expected_ck3_version");
        assertSame(secret, hello.get("secret_build"));
    }

    private static IntegerValue number(String decimal) { return new IntegerValue(new BigInteger(decimal)); }
    /** Literal construction only, with no role filter, production with-chain or derived projection oracle. */
    private static Obj literal(Object... entries) {
        assertEquals(0, entries.length % 2);
        LinkedHashMap<String, Value> members = new LinkedHashMap<>();
        for (int i = 0; i < entries.length; i += 2) members.put((String) entries[i], (Value) entries[i + 1]);
        return new Obj(members);
    }
    private static Obj child(Obj value, String key) { return assertInstanceOf(Obj.class, value.get(key)); }
    private static void keys(Obj value, String... expected) { assertEquals(List.of(expected), new ArrayList<>(value.members().keySet())); }
    private static void refs(Obj value, Object... entries) {
        assertEquals(0, entries.length % 2);
        for (int i = 0; i < entries.length; i += 2) assertSame(entries[i + 1], value.get((String) entries[i]));
    }
}
