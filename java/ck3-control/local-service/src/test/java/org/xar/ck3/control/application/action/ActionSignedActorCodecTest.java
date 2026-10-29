package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Shared DATA fixture -> actual ObservationIdentity and command/expected codecs; never a native qualification. */
final class ActionSignedActorCodecTest {
    private static ActionCommand dataCommand() {
        var at = java.time.Instant.parse("2026-10-24T00:00:00Z");
        var ref = new org.xar.ck3.control.contracts.ExactRef("D:/signed-data/source.json", 1, "a".repeat(64));
        var source = new org.xar.ck3.control.g2.common.G2Source("xenoamess-full-tower-eb9d2c1186", at.toString(), "1.20.0.4", ref);
        var game = new org.xar.ck3.control.contracts.GameGeneration(123, new org.xar.ck3.control.contracts.PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var observed = new ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.ONE, BigInteger.valueOf(100)), "native:1", BigInteger.ONE, "signed-data-episode"), 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observed, source, "signed-data/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("data_only"), true)));
        return new ActionCommand("signed-data", observed, source, "signed-data-session", new OperationKey("synthetic-signed-actor"), new OpportunityJson.Obj(java.util.Map.of()), expected,
                new JointBudgetSelector.Claims(java.util.Set.of(), java.util.Set.of(), java.util.Set.of(), java.util.Set.of()), at.plusSeconds(30));
    }
    @Test void signedActorRemainsSignedInActualCommandAndExpectedIdentityRoundTrip() {
        var base = dataCommand(); var original = base.before();
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(actor), original.frame().identity().nativeRevision(), original.frame().identity().dateRaw());
            var frame = new JointBudgetSelector.ProposalFrame(identity, original.frame().snapshotId(), original.frame().revision(), original.frame().episodeRunId());
            var observed = new ProposalLifecycle.ObservationIdentity(original.machineId(), original.game(), frame, original.observationVersion());
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, observed, base.source(), "xar.synthetic-signed-actor/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("data_only"), true)));
            var command = new ActionCommand(base.actionId(), observed, base.source(), base.sessionId(), new OperationKey("synthetic-signed-actor"),
                    new OpportunityJson.Obj(java.util.Map.of()), expected, base.claims(), base.deadline());
            var reopened = ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
            assertEquals(command, reopened); assertEquals(BigInteger.valueOf(actor), reopened.before().frame().identity().player());
            assertEquals(ActionCodec.bodySha256(command), ActionCodec.bodySha256(reopened));
            var fact = new ProposalLifecycle.ExternalFact(command.actionId(), ActionCodec.bodySha256(command), observed,
                    ProposalLifecycle.ExternalState.UNKNOWN, ProposalLifecycle.UnknownScope.GLOBAL,
                    org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.marriage, command.claims(), base.source().sourceRef());
            assertEquals(fact, ActionFactCodec.fromJson(ActionFactCodec.toJson(fact)));
            assertTrue(ActionFactCodec.fromJson(ActionFactCodec.toJson(fact)).unresolved());
            assertEquals(ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH,
                    ProposalLifecycle.compare(expected, reopened.before(), base.source(), expected.observerSchema(), expected.values()));
        }
    }
}
