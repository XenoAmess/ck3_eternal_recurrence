package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesDefinitions;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Regressions for fresh query drift and accidental positive-revision rules permission. */
final class FrontendGuardBindingTest {
    private static ExactRef ref(String name, char sha) { return new ExactRef("fixture:" + name, 1, String.valueOf(sha).repeat(64)); }
    private static FrontendIdentity frontend(FrontendFrame frame, char packet) {
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        return new FrontendIdentity("test-machine", game, "frontend-one", new BigInteger("9007199254740993"), game.pid(), frame, ref("packet", packet), ref("hello", 'f'));
    }
    @Test void independentMenuReadHasStablePermissionBinding() {
        var before = frontend(new FrontendFrame.Menu(BigInteger.ONE), 'a');
        var after = frontend(new FrontendFrame.Menu(BigInteger.TWO), 'b');
        assertNotEquals(before.nativeEvidence(), after.nativeEvidence());
        assertEquals(FrontendGuardBinding.digest(before), FrontendGuardBinding.digest(after));
        assertTrue(before.sameGuardFrame(after));
    }
    @Test void positiveSnapshotBindingRetainsItsRealSemanticFrame() {
        var before = frontend(new FrontendFrame.Snapshot("snapshot:1", BigInteger.ONE, BigInteger.TEN, 40, BigInteger.ONE), 'a');
        var refresh = frontend(new FrontendFrame.Snapshot("snapshot:1", BigInteger.ONE, BigInteger.TEN, 40, BigInteger.TWO), 'b');
        var drift = frontend(new FrontendFrame.Snapshot("snapshot:2", BigInteger.TWO, BigInteger.valueOf(11), 40, BigInteger.valueOf(3)), 'c');
        assertEquals(FrontendGuardBinding.digest(before), FrontendGuardBinding.digest(refresh));
        assertNotEquals(FrontendGuardBinding.digest(before), FrontendGuardBinding.digest(drift));
    }
    @Test void actualRulesDefinitionRejectsSnapshotEvenWithFrontendOrigin() {
        var definitions = new FrontendRulesDefinitions(FrontendRulesData.Build.CK3_12004, ref("definition", 'd'));
        var now = Instant.parse("2026-10-23T17:35:00Z");
        var source = new G2Source("test-machine", now.toString(), "1.20.0.4", ref("source", 'e'));
        var snapshot = frontend(new FrontendFrame.Snapshot("snapshot:1", BigInteger.ONE, BigInteger.TEN, 40, BigInteger.ONE), 'a');
        var request = new PlanningReadRequest(new CommandOrigin.Frontend(snapshot), source, snapshot.frontendSessionId(),
                definitions.selections().operation(), new OpportunityJson.Obj(Map.of()), now.plusSeconds(30));
        assertThrows(IllegalArgumentException.class, () -> definitions.selections().prepare(request, "real-query-id"));
        var menu = frontend(new FrontendFrame.Menu(BigInteger.ONE), 'b');
        var legal = new PlanningReadRequest(new CommandOrigin.Frontend(menu), source, menu.frontendSessionId(),
                definitions.selections().operation(), new OpportunityJson.Obj(Map.of()), now.plusSeconds(30));
        assertEquals("query-frontend-game-rule-selections-v1", definitions.selections().prepare(legal, "real-query-id").step());
    }
}
