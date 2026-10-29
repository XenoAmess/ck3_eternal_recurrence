package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmUnavailable;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Readiness callback and original Realm state; software packets grant no Managed or Game qualification. */
final class M7PublicTerminalDataScopeTest {
    @TempDir Path temporary;

    /** A previous query slot is produced by the actual Realm methods; this software command is never submitted. */
    private static ActionReceipt stagePreviousQuery(RealmLifecycle realm, PlanningRequest previous) {
        var expected = new ExpectedPostcondition(1, previous.before(), previous.source(), "software-realm-slot/v1",
                List.of(new ExpectedInteger(new FieldKey("target_date_raw"), BigInteger.ZERO)));
        var command = new ActionCommand("previous-realm-query", previous.before(), previous.source(), previous.sessionId(),
                new OperationKey(M7CampaignPolicies.FACTION_QUERY), new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), previous.deadline());
        var draft = queryDraft(command);
        var scope = realm.begin(previous);
        try {
            realm.evaluate(previous, draft);
            realm.finalizePlan(scope, new PlanningResult.ActionSelected(command,
                    new PlanTrace(previous.before(), List.of(), Optional.of(draft))));
        } catch (RuntimeException | Error failure) { realm.cancel(scope); throw failure; }
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "software-realm-slot-unknown", List.of()));
    }
    private static OrdinaryPolicy.Draft queryDraft(ActionCommand command) {
        return new OrdinaryPolicy.Draft("software-realm-slot", "ordinary", "previous query slot",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(),
                new OpportunityJson.Obj(Map.of("selected_step", new OpportunityJson.Text(M7CampaignPolicies.FACTION_QUERY))));
    }

    /** Only the M7 envelope guard is under test here; Planner owns the full original terminal DATA codec. */
    private static OpportunityJson.Obj terminal(String step) {
        OpportunityJson.Value selected = step == null ? OpportunityJson.Nil.INSTANCE : new OpportunityJson.Text(step);
        return new OpportunityJson.Obj(Map.of("policy", new OpportunityJson.Text("one-life-turn-v1"), "selected_step", selected));
    }
    private static void requireCleared(RealmLifecycle realm, ActionReceipt previous) {
        assertEquals("original_query_plan_slot_unavailable",
                assertInstanceOf(RealmUnavailable.class, realm.afterExecution(previous)).reason());
    }

    @Test void actualMissingPlayerTerminalDataFinalizesAndCannotPublishFactionOrEnterOrdinaryScope() throws Exception {
        for (String step : List.of("null", "death-terminal", "start-next-episode", "continue-as-reconciled-successor")) {
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(step), false)) {
                actual.ready(); PlanningRequest previous = actual.lastPublishedReady.get();
                var realm = new RealmLifecycle(previous.source().sourceRef());
                var old = stagePreviousQuery(realm, previous);
                NativePublicPlanningProducerConsumerTest.bindSoftwareSource(actual);
                NativePublicPlanningProducerConsumerTest.publish(actual, state -> state.putNull("played_character"));
                byte[] ledger = actual.ledgerBytes(); var actions = actual.snapshot().actions();
                int writes = actual.nativeActionWrites(), reads = actual.nativeReadWrites();
                actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                        Instant.now().plusSeconds(10), union -> {
                            assertInstanceOf(NativeReadinessCollector.PublicObserved.class, union);
                            assertInstanceOf(DriverObservationAssembler.Incomplete.class, union.frame().joined());
                            var scope = realm.beginPublicTerminalData(union.frame(), same);
                            assertThrows(IllegalArgumentException.class, () -> realm.evaluate(previous, OrdinaryPolicy.Draft.empty()));
                            assertThrows(IllegalArgumentException.class, () -> realm.begin(previous));
                            var other = new RealmLifecycle(previous.source().sourceRef());
                            assertThrows(IllegalArgumentException.class, () -> other.cancelPublicTerminalData(scope));
                            realm.finalizePublicTerminalData(scope, terminal(step.equals("null") ? null : step));
                            realm.cancelPublicTerminalData(scope); requireCleared(realm, old);
                            assertThrows(IllegalArgumentException.class, () -> realm.finalizePublicTerminalData(scope, terminal(null)));
                            union.assertCurrent(same); return null;
                        }));
                assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(actions, actual.snapshot().actions());
                assertSame(previous, actual.lastPublishedReady.get());
                assertEquals(writes, actual.nativeActionWrites()); assertEquals(reads, actual.nativeReadWrites());
            }
        }
    }

    @Test void cancellationFormatterFailureAndRejectedFinalDataClearOldSlotAndPreserveOrdinaryScopeDiscipline() throws Exception {
        for (String failureKind : List.of("cancel", "formatter", "ordinary-step", "wrong-policy", "missing-step", "numeric-step")) {
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(failureKind), false)) {
                actual.ready(); PlanningRequest previous = actual.lastPublishedReady.get();
                var realm = new RealmLifecycle(previous.source().sourceRef());
                var old = stagePreviousQuery(realm, previous);
                NativePublicPlanningProducerConsumerTest.bindSoftwareSource(actual);
                NativePublicPlanningProducerConsumerTest.publish(actual, state -> state.putNull("played_character"));
                byte[] ledger = actual.ledgerBytes(); var actions = actual.snapshot().actions();
                actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                        Instant.now().plusSeconds(10), union -> {
                            var outer = realm.begin(previous);
                            var scope = realm.beginPublicTerminalData(union.frame(), same);
                            if (!failureKind.equals("cancel") && !failureKind.equals("formatter")) {
                                OpportunityJson.Obj invalid = switch (failureKind) {
                                    case "ordinary-step" -> terminal(M7CampaignPolicies.FACTION_QUERY);
                                    case "wrong-policy" -> terminal(null).with("policy", new OpportunityJson.Text("other-policy"));
                                    case "missing-step" -> new OpportunityJson.Obj(Map.of("policy", new OpportunityJson.Text("one-life-turn-v1")));
                                    case "numeric-step" -> terminal(null).with("selected_step", new OpportunityJson.IntegerValue(BigInteger.ONE));
                                    default -> throw new AssertionError(failureKind);
                                };
                                assertThrows(IllegalArgumentException.class, () -> realm.finalizePublicTerminalData(scope, invalid));
                            } else if (failureKind.equals("formatter")) {
                                IOException original = new IOException("actual terminal presentation failed");
                                IOException retained = assertThrows(IOException.class, () -> {
                                    try { throw original; }
                                    catch (IOException failure) {
                                        try { realm.cancelPublicTerminalData(scope); }
                                        catch (RuntimeException | Error cancellation) { failure.addSuppressed(cancellation); }
                                        throw failure;
                                    }
                                });
                                assertSame(original, retained);
                            } else realm.cancelPublicTerminalData(scope);
                            realm.cancelPublicTerminalData(scope); requireCleared(realm, old);
                            // The original outer scope is restored, but its older epoch cannot publish a new pending query.
                            var stale = queryDraft(old.command()); realm.evaluate(previous, stale);
                            realm.finalizePlan(outer, new PlanningResult.ActionSelected(old.command(),
                                    new PlanTrace(previous.before(), List.of(), Optional.of(stale))));
                            requireCleared(realm, old);
                            var next = stagePreviousQuery(realm, previous);
                            assertEquals("original_query_not_confirmed",
                                    assertInstanceOf(RealmUnavailable.class, realm.afterExecution(next)).reason());
                            union.assertCurrent(same); return null;
                        }));
                assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(actions, actual.snapshot().actions());
                assertSame(previous, actual.lastPublishedReady.get());
            }
        }
    }

    @Test void escapedFrameAndRealCorruptSourceAreRejectedBeforeClearingAnotherPendingQuery() throws Exception {
        for (String kind : List.of("escaped", "corrupt-source", "corrupt-after-entry")) {
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(kind), false)) {
                actual.ready(); PlanningRequest previous = actual.lastPublishedReady.get();
                var realm = new RealmLifecycle(previous.source().sourceRef());
                var old = stagePreviousQuery(realm, previous);
                NativePublicPlanningProducerConsumerTest.bindSoftwareSource(actual);
                NativePublicPlanningProducerConsumerTest.publish(actual, state -> state.putNull("played_character"));
                byte[] ledger = actual.ledgerBytes(); var actions = actual.snapshot().actions();
                if (kind.equals("escaped")) {
                    AtomicReference<NativeReadinessCollector.PublicPlanningFrame> escaped = new AtomicReference<>();
                    actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                            Instant.now().plusSeconds(10), union -> { escaped.set(union.frame()); return null; }));
                    actual.writer.locked(same -> {
                        assertThrows(IllegalArgumentException.class, () -> realm.beginPublicTerminalData(escaped.get(), same)); return null;
                    });
                } else {
                    Path source = Path.of(actual.observationSource().sourceRef().path()).toAbsolutePath().normalize();
                    assertTrue(source.startsWith(actual.root.toAbsolutePath().normalize()));
                    byte[] original = Files.readAllBytes(source);
                    try {
                        actual.writer.locked(same -> {
                            IOException failure = assertThrows(IOException.class, () -> actual.collector.withOwnedPublicPlanning(same,
                                    actual.observationIdentity(), Instant.now().plusSeconds(10), union -> {
                                        if (kind.equals("corrupt-after-entry")) {
                                            var scope = realm.beginPublicTerminalData(union.frame(), same);
                                            Files.write(source, Arrays.copyOf(original, original.length + 1));
                                            assertThrows(IOException.class, () -> realm.finalizePublicTerminalData(scope, terminal(null)));
                                            realm.cancelPublicTerminalData(scope);
                                        } else {
                                            Files.write(source, Arrays.copyOf(original, original.length + 1));
                                            assertThrows(IOException.class, () -> realm.beginPublicTerminalData(union.frame(), same));
                                        }
                                        throw new IOException("intentional corrupt-source callback exit");
                                    }));
                            assertEquals("intentional corrupt-source callback exit", failure.getMessage()); return null;
                        });
                    } finally { Files.write(source, original); }
                }
                assertEquals(kind.equals("corrupt-after-entry") ? "original_query_plan_slot_unavailable" : "original_query_not_confirmed",
                        assertInstanceOf(RealmUnavailable.class, realm.afterExecution(old)).reason());
                assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(actions, actual.snapshot().actions());
                assertSame(previous, actual.lastPublishedReady.get());
            }
        }
    }

    @Test void actualCanonicalUnknownAndItsOriginalAttemptSurviveRawFinalizationAndCancellation() throws Exception {
        for (boolean cancel : List.of(false, true)) {
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("canonical-unknown-" + cancel), true)) {
                actual.ready(); PlanningRequest previous = actual.lastPublishedReady.get();
                var realm = new RealmLifecycle(previous.source().sourceRef()); var old = stagePreviousQuery(realm, previous);
                var command = actual.command("m7-public-terminal-unknown");
                var canonical = actual.coordinator.execute(command);
                var unknown = assertInstanceOf(ActionState.Unknown.class, canonical.state());
                assertTrue(unknown.attempt().isPresent());
                NativePublicPlanningProducerConsumerTest.bindSoftwareSource(actual);
                byte[] ledger = actual.ledgerBytes(); var actions = actual.snapshot().actions();
                int writes = actual.nativeActionWrites(), reads = actual.nativeReadWrites();
                actual.writer.locked(same -> actual.collector.withOwnedPublicPlanning(same, actual.observationIdentity(),
                        Instant.now().plusSeconds(10), union -> {
                            assertInstanceOf(NativeReadinessCollector.PublicObserved.class, union);
                            var scope = realm.beginPublicTerminalData(union.frame(), same);
                            if (cancel) realm.cancelPublicTerminalData(scope);
                            else realm.finalizePublicTerminalData(scope, terminal(null));
                            requireCleared(realm, old);
                            assertEquals(actions, union.frame().actions());
                            assertEquals(canonical, union.frame().actions().stream()
                                    .filter(row -> row.command().actionId().equals(command.actionId())).findFirst().orElseThrow());
                            union.assertCurrent(same); return null;
                        }));
                assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(actions, actual.snapshot().actions());
                assertEquals(writes, actual.nativeActionWrites()); assertEquals(reads, actual.nativeReadWrites());
            }
        }
    }
}
