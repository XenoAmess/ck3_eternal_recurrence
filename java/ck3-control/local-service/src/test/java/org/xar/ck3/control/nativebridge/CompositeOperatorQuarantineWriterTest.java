package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.CleanupMode;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real software writer/catalog/archive. This never represents a live Game or the old incident. */
final class CompositeOperatorQuarantineWriterTest {
    private static final OperationKey PARENT = new OperationKey("software-operator-workflow-v1");
    private static final OperationKey CHILD = new OperationKey("pause-map");
    private static final String HANDLER = "software-operator-workflow";
    @TempDir(cleanup = CleanupMode.NEVER) Path temporary;

    @Test void configuredOperatorRetiresUnknownWithoutEffectCreditReplayOrHistoricalHeadLock() throws Exception {
        var installed = new AtomicReference<CompositeOperatorQuarantineSource>();
        var callbackChecks = new AtomicInteger();
        var childId = new AtomicReference<String>();
        var reads = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                "0".repeat(64), "operator-quarantine-software", ignored -> List.of(),
                request -> { throw new AssertionError("no extra scenario READ is registered"); });
        var composite = softwareComposite(installed, callbackChecks, childId);
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("writer"), false,
                reads, List.of(), List.of(composite))) {
            var failFirstChild = new AtomicBoolean(true);
            fixture.bindAdditionalBeforeIntent((same, command) -> {
                try { fixture.writer.requireSession(same); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
                if (command.operation().equals(CHILD) && failFirstChild.compareAndSet(true, false))
                    throw new IllegalStateException("controlled original pending producer failure before child Intent");
            });
            ActionCommand primitiveBasis = fixture.command("operator-original");
            ActionCommand parent = command(primitiveBasis, primitiveBasis.actionId(), PARENT);
            ActionReceipt original = fixture.coordinator.execute(parent);
            var unknown = assertInstanceOf(ActionState.CompositeUnknown.class, original.state());
            assertEquals(1, unknown.execution().children().size());
            assertEquals(childId.get(), unknown.execution().children().getFirst().actionId());
            assertTrue(fixture.snapshot().actions().stream().noneMatch(r -> r.command().actionId().equals(childId.get())));
            assertEquals(0, fixture.nativeActionWrites());
            assertFalse(original.settled());

            int readsBefore = fixture.nativeReadWrites();
            int preparationsBefore = fixture.pendingPreparations.get();
            long beforeSequence = fixture.sequence();
            byte[] beforeLedger = fixture.ledgerBytes();
            var proof = new AtomicReference<ExactRef>();
            var configured = new AtomicReference<CompositeOperatorQuarantineSource>();
            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same);
                var source = configuredSource(same, archive, original);
                configured.set(source);
                proof.set(source.capture(same, original, archive));
                return null;
            });
            // A valid DATA observation cannot bypass the installed source callback via settlement == null.
            int callbacksBefore = callbackChecks.get();
            IllegalArgumentException noSource = assertThrows(IllegalArgumentException.class,
                    () -> fixture.writer.locked(same -> fixture.coordinator.observeOperatorQuarantine(
                            same, parent.actionId(), proof.get())));
            assertTrue(noSource.getMessage().contains("configured software operator source absent"));
            assertTrue(callbackChecks.get() > callbacksBefore);
            assertEquals(beforeSequence, fixture.sequence());
            assertArrayEquals(beforeLedger, fixture.ledgerBytes());
            installed.set(configured.get());

            // A canonical, correctly shaped observation with the wrong original reservation record must fail replay.
            var wrongProof = new AtomicReference<ExactRef>();
            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same);
                var good = CompositeOperatorQuarantineObservation.decode(archive.loadMaterial(proof.get()).bytes());
                var child = good.reservations().getFirst();
                var wrong = new CompositeOperatorQuarantineObservation(good.requestSource(), good.requestMaterial(),
                        good.originalReceipt(), good.predecessorState(), good.predecessorSequence(), good.predecessorDigest(),
                        good.originalActionHead(), good.observedAt(), List.of(new CompositeOperatorQuarantineObservation.Reservation(
                                child.ordinal(), child.actionId(), child.bodySha256(), good.originalActionHead())));
                wrongProof.set(archive.preserveMaterial(new RawJson(wrong.encode())));
                return null;
            });
            IllegalArgumentException wrongRecord = assertThrows(IllegalArgumentException.class,
                    () -> fixture.writer.locked(same -> fixture.coordinator.observeOperatorQuarantine(
                            same, parent.actionId(), wrongProof.get())));
            assertTrue(wrongRecord.getMessage().contains("first reservation references changed"));
            assertEquals(beforeSequence, fixture.sequence());
            assertArrayEquals(beforeLedger, fixture.ledgerBytes());

            ActionReceipt retired = fixture.writer.locked(same -> fixture.coordinator.observeOperatorQuarantine(
                    same, parent.actionId(), proof.get()));
            var terminal = assertInstanceOf(ActionState.CompositeOperatorQuarantined.class, retired.state());
            assertEquals(unknown.execution(), terminal.execution());
            assertEquals(parent, retired.command());
            assertEquals(original.bodySha256(), retired.bodySha256());
            assertEquals(parent.deadline(), retired.command().deadline());
            assertEquals(beforeSequence + 1, retired.sequence());
            assertEquals(ActionReceipt.Outcome.OPERATOR_ABANDONED_UNKNOWN_EFFECT, retired.outcome());
            assertTrue(retired.settled());
            assertFalse(retired.visibleGameplay());
            assertFalse(retired.eligibleAdvance());
            assertTrue(retired.applied().isEmpty());
            assertTrue(retired.ack().isEmpty());
            assertEquals(0, fixture.nativeActionWrites());
            assertEquals(readsBefore, fixture.nativeReadWrites(), "operator observation is archive-only");
            assertEquals(preparationsBefore, fixture.pendingPreparations.get());
            long unchangedCredit = fixture.writer.locked(same -> same.head().state().settledCycles());
            assertEquals(0L, unchangedCredit);

            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same);
                byte[] encoded = ActionReceiptCodec.encodeReceipt(retired, archive);
                assertEquals(retired, ActionReceiptCodec.decodeReceipt(encoded, archive));
                assertEquals(retired, ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(encoded, archive));
                assertEquals(retired, archive.loadReceipt(archive.receiptReferenceOf(retired)));
                assertEquals(original, archive.loadRecord(ContinuityActionJournal.requireHistoricalReceipt(
                        same.head().state(), original, archive)).receipt());
                configured.get().verify(same, same.head(), retired, archive);
                return null;
            });
            byte[] retiredLedger = fixture.ledgerBytes();
            assertEquals(retired, fixture.writer.locked(same -> fixture.coordinator.observeOperatorQuarantine(
                    same, parent.actionId(), proof.get())));
            assertEquals(retired, fixture.coordinator.execute(parent));
            assertArrayEquals(retiredLedger, fixture.ledgerBytes());
            ActionCommand retiredChild = command(parent, childId.get(), CHILD);
            IllegalArgumentException refused = assertThrows(IllegalArgumentException.class,
                    () -> fixture.coordinator.execute(retiredChild));
            assertTrue(refused.getMessage().contains("operator-retired"));
            assertArrayEquals(retiredLedger, fixture.ledgerBytes());
            assertEquals(preparationsBefore, fixture.pendingPreparations.get());
            assertEquals(0, fixture.nativeActionWrites());
            assertEquals(readsBefore, fixture.nativeReadWrites());

            // Core admission does not globally retire other identities. This is not a live/Driver readiness claim.
            ActionCommand unrelated = command(primitiveBasis, "different-software-action-after-retirement", CHILD);
            assertDoesNotThrow(() -> CompositeOperatorQuarantinePolicy.requireNewActionAllowed(
                    fixture.snapshot().actions(), unrelated));
            assertEquals(0, fixture.nativeActionWrites());
            // The committed terminal head is already newer than its configured predecessor; archived replay must work.
            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same);
                var source = configured.get();
                var expired = new CompositeOperatorQuarantineSource(source.requestReference(),
                        archive.loadMaterial(source.requestReference()).bytes(),
                        archive.loadMaterial(source.request().authorizedBy()).bytes(), parent.origin().game(),
                        parent.before().frame().episodeRunId(), PARENT, HANDLER,
                        Clock.fixed(source.request().observationDeadline().plusSeconds(1), ZoneOffset.UTC));
                expired.verify(same, same.head(), retired, archive);
                assertEquals(retired, archive.loadReceipt(archive.receiptReferenceOf(retired)));
                assertEquals(0, same.head().state().settledCycles());
                return null;
            });
            long finalSequence = fixture.sequence();
            byte[] finalLedger = fixture.ledgerBytes();
            IllegalArgumentException directRejected = assertThrows(IllegalArgumentException.class,
                    () -> fixture.journal.locked(locked -> locked.append(retiredChild,
                            ActionCodec.bodySha256(retiredChild), new ActionState.IntentDurable())));
            assertTrue(directRejected.getMessage().contains("operator-retired"));
            assertEquals(finalSequence, fixture.sequence());
            assertArrayEquals(finalLedger, fixture.ledgerBytes());
            assertTrue(fixture.snapshot().actions().stream().noneMatch(r -> r.command().actionId().equals(childId.get())));
            ObjectNode report = StrictJson.object();
            report.put("schema", "xar.operator-quarantine-software-regression/v1");
            report.put("scope", "real software writer/catalog/archive; not live Game or new04 execution proof");
            report.put("retained_original_parent_id", parent.actionId());
            report.put("retired_child_id", childId.get());
            report.put("operator_outcome", retired.outcome().name());
            report.put("operator_sequence", retired.sequence());
            report.put("final_sequence", finalSequence);
            report.put("installed_callback_checks", callbackChecks.get());
            report.put("operator_native_action_writes", 0);
            report.put("total_native_action_writes", fixture.nativeActionWrites());
            report.put("unrelated_identity_policy_allowed", true);
            report.put("old_history_retained", true);
            report.put("archived_replay_after_committed_terminal_head_and_expired_decision_window", true);
            var gaps = report.putArray("coverage_not_claimed");
            gaps.add("fresh Driver canonical-only readiness/legacy publication: separate Root consumer qualification");
            gaps.add("Sway episode policy/action quarantine: this uses an explicitly controlled software operation");
            gaps.add("batch/controller restoration and runtime recovery: separate source and software qualification");
            report.put("cycle_credit", 0);
            Path reportPath = temporary.resolve("operator-quarantine-regression-summary.json");
            Files.write(reportPath, StrictJson.canonical(report), StandardOpenOption.CREATE_NEW);
            System.out.println("OPERATOR_QUARANTINE_SOFTWARE_REPORT=" + reportPath);
        }
    }

    private static ActionWriterIntegrationFixture.SoftwareCompositeScenario softwareComposite(
            AtomicReference<CompositeOperatorQuarantineSource> installed, AtomicInteger checks,
            AtomicReference<String> childId) {
        return new ActionWriterIntegrationFixture.SoftwareCompositeScenario(HANDLER, Set.of(PARENT),
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of("game.command.pause-map"), context -> {
            CompositeActionPort handler = new CompositeActionPort() {
                @Override public String handlerId() { return HANDLER; }
                @Override public boolean supports(OperationKey operation) { return PARENT.equals(operation); }
                @Override public void validate(ActionCommand parent) { assertEquals(PARENT, parent.operation()); }
                @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) {
                    String id = children.nextActionId(CHILD); childId.set(id);
                    children.submit(command(parent, id, CHILD));
                    throw new AssertionError("deliberate original pre-Intent producer failure must stop this software child");
                }
                @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution execution) {
                    return new ActionPorts.Pending("controlled original UNKNOWN; no action replay", List.of());
                }
            };
            var replay = new NativeRecordedEvidenceVerifier.Binding(PARENT, context.source().sourceRef(),
                    (head, proposed, archive) -> {
                checks.incrementAndGet();
                var source = installed.get();
                if (source == null) throw new IllegalArgumentException("configured software operator source absent");
                try { source.verify(context.journal().borrowedWriterSession(), head, proposed, archive); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
            return new ActionWriterIntegrationFixture.SoftwareCompositeInstallation(handler, List.of(replay));
        });
    }

    private static ActionCommand command(ActionCommand basis, String id, OperationKey operation) {
        return new ActionCommand(id, basis.before(), basis.source(), basis.sessionId(), operation,
                basis.arguments(), basis.expected(), basis.claims(), basis.deadline());
    }

    private static CompositeOperatorQuarantineSource configuredSource(ContinuityStorePort.Session same,
            ActionPorts.OutcomeArchive archive, ActionReceipt original) throws IOException {
        byte[] authorization = "{\"schema\":\"xar.software-operator-directive/v1\",\"decision\":\"retire this test workflow with UNKNOWN effects; no runtime permission\"}"
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        ExactRef authorizationRef = archive.preserveMaterial(new RawJson(authorization));
        Instant issued = Instant.now().minusSeconds(1);
        Instant observed = issued.plusSeconds(1);
        ObjectNode request = StrictJson.object();
        request.put("schema", CompositeOperatorQuarantineRequest.SCHEMA);
        request.set("authorized_by", authorizationRef.toJson());
        request.put("machine_id", original.command().origin().machineId());
        request.set("game", original.command().origin().game().toJson());
        request.put("episode_run_id", original.command().before().frame().episodeRunId());
        request.put("parent_action_id", original.command().actionId());
        request.put("parent_body_sha256", original.bodySha256());
        request.set("original_receipt_ref", archive.receiptReferenceOf(original).toJson());
        request.put("expected_head_sequence", same.head().state().sequence());
        request.put("expected_head_digest", same.head().digest());
        var rows = request.putArray("children");
        var execution = ((ActionState.CompositeUnknown) original.state()).execution();
        for (int i = 0; i < execution.children().size(); i++) {
            var value = execution.children().get(i); var row = rows.addObject();
            row.put("ordinal", i + 1); row.put("action_id", value.actionId()); row.put("body_sha256", value.bodySha256());
        }
        request.put("scope", CompositeOperatorQuarantineRequest.SCOPE);
        request.put("issued_at_utc", issued.toString());
        request.put("observation_deadline_utc", issued.plusSeconds(120).toString());
        byte[] bytes = StrictJson.canonical(request);
        ExactRef requestRef = archive.preserveMaterial(new RawJson(bytes));
        return new CompositeOperatorQuarantineSource(requestRef, bytes, authorization, original.command().origin().game(),
                original.command().before().frame().episodeRunId(), PARENT, HANDLER, Clock.fixed(observed, ZoneOffset.UTC));
    }
}
