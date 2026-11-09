package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Pure public DATA projection checks; no protocol, authority, parser or performance measurement. */
public final class CashProjection190Test {
    @Test
    void fourLiteralCasesKeepValuesOrderAndIdentity() {
        neitherOuterRoleIsAnObject();
        snapshotOnlyEqualValueStillReturnsNewOuterObject();
        rootOnlyEqualValueStillReturnsNewOuterObject();
        bothRolesShareInputButKeepIndependentProjections();
    }

    private static void neitherOuterRoleIsAnObject() {
        Text snapshot = new Text("not-an-object");
        Bool root = new Bool(false);
        Obj unknown = literal("opaque", Nil.INSTANCE);
        Obj original = literal("unknown_outer", unknown, "root", root, "snapshot", snapshot);
        Obj expected = literal("unknown_outer", unknown, "root", root, "snapshot", snapshot);

        Obj result = OrdinaryFinanceCollector.projectCashContext(original);

        assertSame(original, result);
        assertEquals(expected, result);
        keys(result, "unknown_outer", "root", "snapshot");
        refs(result, "unknown_outer", unknown, "root", root, "snapshot", snapshot);
        assertEquals(expected, original);
        keys(original, "unknown_outer", "root", "snapshot");
    }

    private static void snapshotOnlyEqualValueStillReturnsNewOuterObject() {
        IntegerValue generation = number("17");
        IntegerValue pid = number("9007199254740993");
        Bool connected = new Bool(true);
        IntegerValue date = number("53144328");
        Bool paused = new Bool(true);
        Text root = new Text("not-an-object");
        Obj unknown = literal("opaque", Nil.INSTANCE);
        Obj diagnostics = literal("connection_generation", generation, "bridge_pid", pid, "connected", connected);
        Obj snapshot = literal("diagnostics", diagnostics, "date_raw", date, "paused", paused);
        Obj original = literal("root", root, "unknown_outer", unknown, "snapshot", snapshot);
        Obj expectedDiagnostics = literal("connection_generation", generation, "bridge_pid", pid, "connected", connected);
        Obj expectedSnapshot = literal("diagnostics", expectedDiagnostics, "date_raw", date, "paused", paused);
        Obj expected = literal("root", root, "unknown_outer", unknown, "snapshot", expectedSnapshot);

        Obj result = OrdinaryFinanceCollector.projectCashContext(original);

        assertEquals(original, expected); // The branch must not become an equals-based original return.
        assertNotSame(original, result);
        assertEquals(expected, result);
        keys(result, "root", "unknown_outer", "snapshot");
        Obj projectedSnapshot = (Obj) result.get("snapshot");
        Obj projectedDiagnostics = (Obj) projectedSnapshot.get("diagnostics");
        assertNotSame(snapshot, projectedSnapshot);
        assertNotSame(diagnostics, projectedDiagnostics);
        keys(projectedSnapshot, "diagnostics", "date_raw", "paused");
        keys(projectedDiagnostics, "connection_generation", "bridge_pid", "connected");
        refs(result, "root", root, "unknown_outer", unknown);
        refs(projectedSnapshot, "date_raw", date, "paused", paused);
        refs(projectedDiagnostics, "connection_generation", generation, "bridge_pid", pid, "connected", connected);
        assertEquals(expected, original);
        keys(original, "root", "unknown_outer", "snapshot");
        refs(original, "snapshot", snapshot, "root", root, "unknown_outer", unknown);
        keys(snapshot, "diagnostics", "date_raw", "paused");
        keys(diagnostics, "connection_generation", "bridge_pid", "connected");
        assertSame(diagnostics, snapshot.get("diagnostics"));
    }

    private static void rootOnlyEqualValueStillReturnsNewOuterObject() {
        IntegerValue income = number("9007199254740995");
        IntegerValue identity = number("9007199254740997");
        Text status = new Text("available");
        Bool snapshot = new Bool(false);
        Obj unknown = literal("opaque", Nil.INSTANCE);
        Obj root = literal("player_monthly_gold_income", income, "player_character_id", identity, "status", status);
        Obj original = literal("snapshot", snapshot, "root", root, "unknown_outer", unknown);
        Obj expectedRoot = literal("player_monthly_gold_income", income, "player_character_id", identity, "status", status);
        Obj expected = literal("snapshot", snapshot, "root", expectedRoot, "unknown_outer", unknown);

        Obj result = OrdinaryFinanceCollector.projectCashContext(original);

        assertEquals(original, expected);
        assertNotSame(original, result);
        assertEquals(expected, result);
        keys(result, "snapshot", "root", "unknown_outer");
        Obj projectedRoot = (Obj) result.get("root");
        assertNotSame(root, projectedRoot);
        keys(projectedRoot, "player_monthly_gold_income", "player_character_id", "status");
        refs(projectedRoot, "player_monthly_gold_income", income, "player_character_id", identity, "status", status);
        refs(result, "snapshot", snapshot, "unknown_outer", unknown);
        assertEquals(expected, original);
        keys(original, "snapshot", "root", "unknown_outer");
        refs(original, "snapshot", snapshot, "root", root, "unknown_outer", unknown);
        keys(root, "player_monthly_gold_income", "player_character_id", "status");
    }

    private static void bothRolesShareInputButKeepIndependentProjections() {
        IntegerValue income = number("9007199254740999");
        IntegerValue identity = number("9007199254741001");
        IntegerValue date = number("53144328");
        IntegerValue generation = number("23");
        IntegerValue pid = number("42");
        Bool connected = new Bool(true);
        Bool paused = new Bool(false);
        Text status = new Text("available");
        Text secret = new Text("prune-shared-secret");
        Text diagnosticSecret = new Text("prune-diagnostic-secret");
        Obj unknown = literal("opaque", Nil.INSTANCE, "keep", new Bool(true));
        Obj diagnostics = literal("secret", diagnosticSecret, "connection_generation", generation, "connected", connected, "bridge_pid", pid);
        Obj shared = literal("player_monthly_gold_income", income, "diagnostics", diagnostics, "status", status,
                "date_raw", date, "paused", paused, "player_character_id", identity, "secret", secret);
        Obj original = literal("root", shared, "unknown_outer", unknown, "snapshot", shared);
        Obj expectedDiagnostics = literal("connection_generation", generation, "connected", connected, "bridge_pid", pid);
        Obj expectedSnapshot = literal("diagnostics", expectedDiagnostics, "date_raw", date, "paused", paused);
        Obj expectedRoot = literal("player_monthly_gold_income", income, "status", status, "date_raw", date, "player_character_id", identity);
        Obj expected = literal("root", expectedRoot, "unknown_outer", unknown, "snapshot", expectedSnapshot);
        Obj expectedInputDiagnostics = literal("secret", diagnosticSecret, "connection_generation", generation, "connected", connected, "bridge_pid", pid);
        Obj expectedInputShared = literal("player_monthly_gold_income", income, "diagnostics", expectedInputDiagnostics, "status", status,
                "date_raw", date, "paused", paused, "player_character_id", identity, "secret", secret);
        Obj expectedInput = literal("root", expectedInputShared, "unknown_outer", unknown, "snapshot", expectedInputShared);

        Obj result = OrdinaryFinanceCollector.projectCashContext(original);

        assertNotSame(original, result);
        assertEquals(expected, result);
        keys(result, "root", "unknown_outer", "snapshot");
        Obj projectedRoot = (Obj) result.get("root");
        Obj projectedSnapshot = (Obj) result.get("snapshot");
        Obj projectedDiagnostics = (Obj) projectedSnapshot.get("diagnostics");
        assertNotSame(shared, projectedRoot);
        assertNotSame(shared, projectedSnapshot);
        assertNotSame(diagnostics, projectedDiagnostics);
        keys(projectedRoot, "player_monthly_gold_income", "status", "date_raw", "player_character_id");
        keys(projectedSnapshot, "diagnostics", "date_raw", "paused");
        keys(projectedDiagnostics, "connection_generation", "connected", "bridge_pid");
        refs(result, "unknown_outer", unknown);
        refs(projectedRoot, "player_monthly_gold_income", income, "status", status, "date_raw", date, "player_character_id", identity);
        refs(projectedSnapshot, "date_raw", date, "paused", paused);
        refs(projectedDiagnostics, "connection_generation", generation, "connected", connected, "bridge_pid", pid);
        assertEquals(expectedInput, original);
        keys(original, "root", "unknown_outer", "snapshot");
        refs(original, "root", shared, "unknown_outer", unknown, "snapshot", shared);
        keys(shared, "player_monthly_gold_income", "diagnostics", "status", "date_raw", "paused", "player_character_id", "secret");
        refs(shared, "diagnostics", diagnostics, "secret", secret);
        keys(diagnostics, "secret", "connection_generation", "connected", "bridge_pid");
        assertSame(diagnosticSecret, diagnostics.get("secret"));
    }

    private static IntegerValue number(String decimal) {
        return new IntegerValue(new BigInteger(decimal));
    }

    /** Literal construction only: no filtering, role logic or production with-chain oracle. */
    private static Obj literal(Object... entries) {
        assertEquals(0, entries.length % 2);
        LinkedHashMap<String, Value> members = new LinkedHashMap<>();
        for (int i = 0; i < entries.length; i += 2) members.put((String) entries[i], (Value) entries[i + 1]);
        return new Obj(members);
    }

    private static void keys(Obj actual, String... expected) {
        assertEquals(List.of(expected), new ArrayList<>(actual.members().keySet()));
    }

    /** Explicit literal key/ref assertions; this helper does not derive expected projections. */
    private static void refs(Obj actual, Object... entries) {
        assertEquals(0, entries.length % 2);
        for (int i = 0; i < entries.length; i += 2) assertSame(entries[i + 1], actual.get((String) entries[i]));
    }
}
