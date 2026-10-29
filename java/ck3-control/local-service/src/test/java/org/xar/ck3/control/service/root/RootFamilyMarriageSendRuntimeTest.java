package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import static org.junit.jupiter.api.Assertions.*;

/** DATA gates use the actual transport/Driver fixture; this never constructs or grants a ManagedGameSession. */
final class RootFamilyMarriageSendRuntimeTest {
    @TempDir Path temporary;
    private static final long HASH = 0xF1234567L;
    private static final List<FamilyOutgoingCodec.OptionRow> OPTIONS = List.of(
            new FamilyOutgoingCodec.OptionRow(0, 0xF0000001L, 1),
            new FamilyOutgoingCodec.OptionRow(1, 0xF0000001L, 0));

    @Test void originalPrivatePairAndSelectedOptionAreRequiredBeforeADataGateCanPass() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary, false)) {
            ActionCommand command = child(fixture);
            var roles = new FamilyOutgoingCodec.Roles(73L, 79L, 74L, 75L, null);
            var exact = observed(command, roles, true, true, true);
            assertDoesNotThrow(() -> RootFamilyMarriageSendRuntime.requireSendable(command, exact));
            assertEquals(OPTIONS, exact.outgoing().candidates().isEmpty()
                    ? ((FamilyMarriageSendReads.Prepared) exact.prepared().orElseThrow()).options()
                    : fail("before DATA unexpectedly contains a candidate"));
            assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(
                    command, observed(command, roles, true, true, false)));
            assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(
                    command, observed(command, roles, false, true, true)));
            assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(
                    command, observed(command, roles, true, false, true)));
            var material = (FamilyMarriageSendReads.Prepared) exact.prepared().orElseThrow();
            var differentEffective = new FamilyMarriageSendReads.Prepared(material.definitionHash(), material.roles(), material.options(),
                    true, true, false, Optional.of(false));
            assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(command,
                    new FamilyMarriageSendReads.Observation(exact.scope(), exact.frame(), Optional.of(differentEffective), exact.outgoing())));
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void changedOrNullPrivateRoleCannotPassAndRawOriginalsRemainUnchanged() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary, false)) {
            ActionCommand command = child(fixture);
            var exact = observed(command, new FamilyOutgoingCodec.Roles(73L, 79L, 74L, 75L, null), true, true, true);
            var original = FamilyOutgoingCodec.encodeGroup(exact.outgoing()).deepCopy();
            for (var roles : List.of(
                    new FamilyOutgoingCodec.Roles(79L, 79L, 74L, 75L, null),
                    new FamilyOutgoingCodec.Roles(73L, 80L, 74L, 75L, null),
                    new FamilyOutgoingCodec.Roles(73L, 79L, 75L, 74L, null),
                    new FamilyOutgoingCodec.Roles(73L, 79L, null, 75L, null)))
                assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(
                        command, observed(command, roles, true, true, true)));
            assertEquals(original, FamilyOutgoingCodec.encodeGroup(exact.outgoing()));
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void publicRulerDataRetainsActualRedirectedSenderWithoutReplacingThePlayedActor() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary, false)) {
            var basis = fixture.command("ruler-data-gate");
            var intent = new RulerMarriageIntent("73-75", 73, 75, Optional.empty());
            var sender = FamilyMarriageSendReads.sender(intent.toJson(), intent.step());
            var command = new ActionCommand(basis.actionId(), basis.before(), basis.source(), basis.sessionId(),
                    new OperationKey(intent.step()), intent.toJson(), MarriageSendEffects.expected(basis.before(), basis.source(), sender),
                    basis.claims(), basis.deadline());
            var actual = observed(command, new FamilyOutgoingCodec.Roles(79L, 73L, null, 75L, null), true, true, false);
            assertDoesNotThrow(() -> RootFamilyMarriageSendRuntime.requireSendable(command, actual));
            assertEquals(BigInteger.valueOf(73), actual.frame().actor());
            assertEquals(79L, actual.outgoing().senderCharacterId().orElseThrow());
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void sourceClosureRejectsMissingAndDuplicateOriginals() {
        var a = ref("a", 1);
        var b = ref("b", 2);
        assertDoesNotThrow(() -> sources(a, List.of(a)));
        assertThrows(IllegalArgumentException.class, () -> sources(a, List.of(b)));
        assertThrows(IllegalArgumentException.class, () -> sources(a, List.of(a, a)));
        assertThrows(IllegalArgumentException.class, () -> sources(a, List.of()));
    }

    @Test void fulfillmentUsesActualEffectiveLinealitySeparatelyFromTheSelectedOption() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary, false)) {
            var basis = fixture.command("fulfillment-effective-lineality");
            var intent = new FamilyMarriageIntent(FamilyMarriageIntent.Route.FULFILL_BETROTHAL, 73, 74, 75, 79,
                    true, List.of(), Optional.empty());
            var sender = FamilyMarriageSendReads.sender(intent.toJson(), intent.step());
            var command = new ActionCommand(basis.actionId(), basis.before(), basis.source(), basis.sessionId(),
                    new OperationKey(intent.step()), intent.toJson(), MarriageSendEffects.expected(basis.before(), basis.source(), sender),
                    basis.claims(), basis.deadline());
            var original = observed(command, new FamilyOutgoingCodec.Roles(73L, 79L, 74L, 75L, null), true, true, false);
            var material = (FamilyMarriageSendReads.Prepared) original.prepared().orElseThrow();
            var actualEffective = new FamilyMarriageSendReads.Prepared(material.definitionHash(), material.roles(), material.options(),
                    true, false, false, Optional.of(true));
            assertDoesNotThrow(() -> RootFamilyMarriageSendRuntime.requireSendable(command,
                    new FamilyMarriageSendReads.Observation(original.scope(), original.frame(), Optional.of(actualEffective), original.outgoing())));
            assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(command, original));
            var unavailable = new FamilyMarriageSendReads.Prepared(material.definitionHash(), material.roles(), material.options(),
                    true, false, false, Optional.empty());
            assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(command,
                    new FamilyMarriageSendReads.Observation(original.scope(), original.frame(), Optional.of(unavailable), original.outgoing())));
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void firstHeirUsesSelectedWhileDefaultChildSeparatelyRequiresFalseEffectiveLineality() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary, false)) {
            for (var route : List.of(FamilyMarriageIntent.Route.FIRST_HEIR, FamilyMarriageIntent.Route.CHILD_DEFAULT)) {
                var basis = fixture.command("route-lineality-" + route.name());
                var intent = new FamilyMarriageIntent(route, 73, 74, 75, 79, false,
                        route == FamilyMarriageIntent.Route.FIRST_HEIR ? List.of(75, 76, 77, 78, 79) : List.of(), Optional.empty());
                var sender = FamilyMarriageSendReads.sender(intent.toJson(), intent.step());
                var command = new ActionCommand(basis.actionId(), basis.before(), basis.source(), basis.sessionId(),
                        new OperationKey(intent.step()), intent.toJson(), MarriageSendEffects.expected(basis.before(), basis.source(), sender),
                        basis.claims(), basis.deadline());
                var original = observed(command, new FamilyOutgoingCodec.Roles(73L, 79L, 74L, 75L, null), true, true, false);
                assertDoesNotThrow(() -> RootFamilyMarriageSendRuntime.requireSendable(command, original));
                var material = (FamilyMarriageSendReads.Prepared) original.prepared().orElseThrow();
                var differentEffective = new FamilyMarriageSendReads.Prepared(material.definitionHash(), material.roles(), material.options(),
                        true, false, false, Optional.of(true));
                var changed = new FamilyMarriageSendReads.Observation(original.scope(), original.frame(), Optional.of(differentEffective), original.outgoing());
                if (route == FamilyMarriageIntent.Route.FIRST_HEIR)
                    assertDoesNotThrow(() -> RootFamilyMarriageSendRuntime.requireSendable(command, changed));
                else assertThrows(IllegalArgumentException.class, () -> RootFamilyMarriageSendRuntime.requireSendable(command, changed));
            }
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    private static RootFamilyMarriageSendRuntime.Sources sources(ExactRef source, List<ExactRef> closure) {
        return new RootFamilyMarriageSendRuntime.Sources(source, source, source, source, source, source, source, closure);
    }
    private static ExactRef ref(String name, int suffix) { return new ExactRef("data-source-" + name, 1, Integer.toHexString(suffix).repeat(64)); }

    private static ActionCommand child(ActionWriterIntegrationFixture fixture) throws Exception {
        var basis = fixture.command("child-data-gate");
        var intent = new FamilyMarriageIntent(FamilyMarriageIntent.Route.CHILD_MATRILINEAL, 73, 74, 75, 79,
                true, List.of(), Optional.empty());
        var sender = FamilyMarriageSendReads.sender(intent.toJson(), intent.step());
        return new ActionCommand(basis.actionId(), basis.before(), basis.source(), basis.sessionId(),
                new OperationKey(intent.step()), intent.toJson(), MarriageSendEffects.expected(basis.before(), basis.source(), sender),
                basis.claims(), basis.deadline());
    }

    private static FamilyMarriageSendReads.Observation observed(ActionCommand command, FamilyOutgoingCodec.Roles roles,
            boolean canSend, boolean complete, boolean matrilineal) {
        var frame = FamilyMarriageSendReads.frame(command.before(), BigInteger.valueOf(20));
        var effective = FamilyMarriageSendReads.sender(command).route() == FamilyMarriageSendReads.Route.RULER
                ? Optional.<Boolean>empty() : Optional.of(matrilineal);
        var prepared = new FamilyMarriageSendReads.Prepared(HASH, roles, OPTIONS, canSend, matrilineal, false, effective);
        var storage = new FamilyOutgoingCodec.Snapshot(frame, FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE, complete,
                complete ? OptionalLong.of(HASH) : OptionalLong.empty(), complete ? OptionalInt.of(4) : OptionalInt.empty(),
                complete ? OptionalLong.of(roles.actor()) : OptionalLong.empty(), List.of(), List.of(),
                complete ? Optional.empty() : Optional.of("controlled unavailable original source DATA"));
        return new FamilyMarriageSendReads.Observation(FamilyMarriageSendReads.Scope.ACTION_PREPARATION, frame,
                Optional.of(prepared), storage);
    }
}
