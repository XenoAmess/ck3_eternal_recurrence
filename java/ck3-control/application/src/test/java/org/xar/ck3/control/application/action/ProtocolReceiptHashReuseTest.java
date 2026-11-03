package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic public DATA for the pure admission function; no writer, Native, Game, or submit authority. */
final class ProtocolReceiptHashReuseTest {
    private static final String CONFLICT = "original native protocol request ID is already bound to another complete canonical command";
    private static final ExactRef SOURCE = new ExactRef("D:/synthetic-public-data/source.java", 1, "a".repeat(64));
    private static final OperationKey COUNCIL = new OperationKey("private-assign-councillor-v1");

    private static final class ChangingInteger extends BigInteger {
        private static final long serialVersionUID = 1L;
        private boolean changed;
        private boolean fail;
        private final IllegalStateException failure = new IllegalStateException("public DATA encoder fault");
        ChangingInteger() { super("1"); }
        @Override public String toString() {
            if (fail) throw failure;
            return changed ? "2" : "1";
        }
    }

    @Test void stableDefaultsAndExplicitDerivedRoleCollisionsKeepCompleteBinding() {
        var command = command("same", "software-data", integer(BigInteger.ONE), BigInteger.ONE,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        var retained = receipt(command);
        assertEquals(RequestIds.forActionBody(retained.bodySha256()), RequestIds.forCommand(command));
        assertDoesNotThrow(() -> ProtocolIdentityAdmission.requireUnique(List.of(retained), command));

        String defaultId = RequestIds.forCommand(command);
        var explicit = command("same", "software-data", integer(BigInteger.ONE), BigInteger.ONE, explicit(defaultId));
        assertEquals(defaultId, RequestIds.forCommand(explicit));
        assertFalse(java.util.Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(explicit)));
        assertEquals(CONFLICT, assertThrows(IllegalArgumentException.class,
                () -> ProtocolIdentityAdmission.requireUnique(List.of(retained), explicit)).getMessage());
        var explicitReceipt = receipt(explicit);
        assertEquals(CONFLICT, assertThrows(IllegalArgumentException.class,
                () -> ProtocolIdentityAdmission.requireUnique(List.of(explicitReceipt), command)).getMessage());

        var changed = command("another-action", "software-data", integer(BigInteger.TWO), BigInteger.TWO,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        assertNotEquals(RequestIds.forCommand(command), RequestIds.forCommand(changed));
        assertDoesNotThrow(() -> ProtocolIdentityAdmission.requireUnique(List.of(retained), changed));
    }

    @Test void postReceiptArgumentAndExpectedMutationUseCurrentDefaultIdThenRejectStaleHash() {
        for (boolean inArguments : List.of(true, false)) {
            var mutable = new ChangingInteger();
            var original = command("mutable-" + inArguments, "software-data",
                    integer(inArguments ? mutable : BigInteger.ONE), inArguments ? BigInteger.ONE : mutable,
                    ProtocolRequestIdentity.BodyDerived.INSTANCE);
            var retained = receipt(original);
            String oldId = RequestIds.forCommand(original);
            mutable.changed = true;
            var proposed = command("mutable-" + inArguments, "software-data",
                    integer(inArguments ? BigInteger.TWO : BigInteger.ONE), inArguments ? BigInteger.ONE : BigInteger.TWO,
                    ProtocolRequestIdentity.BodyDerived.INSTANCE);
            assertArrayEquals(ActionCodec.encodeCommand(original), ActionCodec.encodeCommand(proposed));
            assertEquals(RequestIds.forCommand(original), RequestIds.forCommand(proposed));
            assertNotEquals(oldId, RequestIds.forCommand(proposed));
            assertNotEquals(retained.bodySha256(), ActionCodec.bodySha256(proposed));
            assertEquals(CONFLICT, assertThrows(IllegalArgumentException.class,
                    () -> ProtocolIdentityAdmission.requireUnique(List.of(retained), proposed)).getMessage());
        }
        // A nullable public numerical record must not acquire a new classifier NPE.
        var nullable = command("nullable", "software-data", integer(null), BigInteger.ONE,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        assertDoesNotThrow(() -> ProtocolIdentityAdmission.requireUnique(List.of(receipt(nullable)), nullable));
    }

    @Test void foreignPriorFilterAndDefaultEncodingFailuresKeepOriginalOrder() {
        var mutable = new ChangingInteger();
        var foreign = command("foreign", "foreign-data", integer(mutable), BigInteger.ONE,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        var foreignReceipt = receipt(foreign);
        var local = command("proposed", "software-data", integer(BigInteger.ONE), BigInteger.ONE,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        mutable.fail = true;
        assertDoesNotThrow(() -> ProtocolIdentityAdmission.requireUnique(List.of(foreignReceipt), local));

        var sameScope = new ChangingInteger();
        var original = command("prior", "software-data", integer(sameScope), BigInteger.ONE,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        var retained = receipt(original);
        sameScope.fail = true;
        assertSame(sameScope.failure, assertThrows(IllegalStateException.class,
                () -> ProtocolIdentityAdmission.requireUnique(List.of(retained), local)));

        // Arguments fit their public constructor budget; the complete command envelope still must fit1MiB.
        var large = new OpportunityJson.Obj(Map.of("payload",
                new OpportunityJson.Text("x".repeat(ActionCodec.MAX_COMMAND_BYTES - 128))));
        var overWholeRole = command("full-envelope", "software-data", large, BigInteger.ONE,
                ProtocolRequestIdentity.BodyDerived.INSTANCE);
        assertThrows(IllegalArgumentException.class,
                () -> ProtocolIdentityAdmission.requireUnique(List.of(), overWholeRole));
    }

    private static OpportunityJson.Obj integer(BigInteger value) {
        return new OpportunityJson.Obj(Map.of("value", new OpportunityJson.IntegerValue(value)));
    }

    private static ExplicitOriginalProtocolId explicit(String value) {
        return new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT, value, SOURCE);
    }

    private static ActionCommand command(String id, String machine, OpportunityJson.Obj arguments,
            BigInteger expectedValue, ProtocolRequestIdentity protocol) {
        var source = new G2Source(machine, "2026-11-03T00:00:00Z", "synthetic-public-data", SOURCE);
        var game = new GameGeneration(11, new PythonOnlyUInt64(BigInteger.valueOf(7)));
        var frame = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.ZERO),
                "synthetic:1", BigInteger.ONE, "synthetic-episode");
        var before = new ProposalLifecycle.ObservationIdentity(machine, game, frame, 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "synthetic-observer",
                List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("value"), expectedValue)));
        return new ActionCommand(id, new CommandOrigin.Gameplay(before), source, "synthetic-session", COUNCIL, arguments,
                new CommandExpectation.Gameplay(expected),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                Instant.parse("2030-01-01T00:00:00Z"), protocol);
    }

    private static ActionReceipt receipt(ActionCommand command) {
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
    }
}
