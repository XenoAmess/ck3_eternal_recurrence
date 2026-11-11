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
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Representative consumers of a real software canonical observation, not a production Sway execution or live Game. */
final class CompositeOperatorQuarantineConsumersTest {
    // These are the actual consumer discriminator names; the registered business handler remains explicitly SOFTWARE.
    private static final OperationKey PARENT = OrdinarySwayPolicy.OPERATION;
    private static final OperationKey CHILD = new OperationKey("pause-map");
    private static final String HANDLER = SwayOrdinaryComposite.HANDLER;
    @TempDir(cleanup = CleanupMode.NEVER) Path temporary;

    @Test void driverAndOptionalSwayConsumeCanonicalUnknownEffectWithoutInventingHistoryOrRunningCollector() throws Exception {
        var installed = new AtomicReference<CompositeOperatorQuarantineSource>();
        var sourceChecks = new AtomicInteger();
        var childId = new AtomicReference<String>();
        var reads = new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),
                "operator-consumer-software", ignored -> List.of(),
                request -> { throw new AssertionError("no extra scenario READ is registered"); });
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("writer"), false,
                reads, List.of(), List.of(softwareComposite(installed, sourceChecks, childId)))) {
            var firstChild = new AtomicBoolean(true);
            fixture.bindAdditionalBeforeIntent((same, command) -> {
                try { fixture.writer.requireSession(same); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
                if (command.operation().equals(CHILD) && firstChild.compareAndSet(true, false))
                    throw new IllegalStateException("software pending producer stops before original child Intent");
            });
            ActionCommand basis = fixture.command("consumer-original");
            PlanningRequest planning = fixture.lastPublishedReady.get();
            assertNotNull(planning);
            ActionReceipt original = fixture.coordinator.execute(command(basis, basis.actionId(), PARENT));
            assertEquals(1, assertInstanceOf(ActionState.CompositeUnknown.class, original.state()).execution().children().size());
            assertEquals(0, fixture.nativeActionWrites());
            DriverSnapshotFacts.Known before = known(fixture);
            byte[] fullBefore = before.driver().encode();
            ActionReceipt retired = fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same);
                var source = configuredSource(same, archive, original); installed.set(source);
                return fixture.coordinator.observeOperatorQuarantine(same, original.command().actionId(),
                        source.capture(same, original, archive));
            });
            assertEquals(ActionReceipt.Outcome.OPERATOR_ABANDONED_UNKNOWN_EFFECT, retired.outcome());
            int actionsBeforeConsumers = fixture.nativeActionWrites();
            int readsBeforeConsumers = fixture.nativeReadWrites();
            long headBeforePublisher = fixture.sequence();
            byte[] ledgerBeforePublisher = fixture.ledgerBytes();
            var missingMaterials = new CatalogMaterials(fixture, false);
            var rejectedPublisher = publisher(fixture, missingMaterials);
            UncheckedIOException missing = assertThrows(UncheckedIOException.class,
                    () -> fixture.writer.locked(same -> rejectedPublisher.completed(same, retired)));
            assertTrue(missing.getCause().getMessage().contains("operator quarantine history verifier is not installed"));
            assertEquals(headBeforePublisher, fixture.sequence());
            assertArrayEquals(ledgerBeforePublisher, fixture.ledgerBytes());

            var materials = new CatalogMaterials(fixture, true);
            var publisher = publisher(fixture, materials);
            var disposition = fixture.writer.locked(same -> publisher.completed(same, retired));
            assertEquals(DriverActionHistoryPublisher.Reason.OPERATOR_QUARANTINED_UNKNOWN_EFFECT_VERIFIED,
                    assertInstanceOf(DriverActionHistoryPublisher.Unchanged.class, disposition).reason());
            assertEquals(1, materials.operatorChecks.get());
            assertEquals(0, materials.captureCalls.get());
            assertFalse(fixture.writer.locked(publisher::hasPending));
            assertEquals(headBeforePublisher, fixture.sequence());
            assertArrayEquals(ledgerBeforePublisher, fixture.ledgerBytes());
            DriverSnapshotFacts.Known afterPublisher = known(fixture);
            assertEquals(before.stamp(), afterPublisher.stamp());
            assertArrayEquals(fullBefore, afterPublisher.driver().encode());
            assertEquals(before.actionRows(), afterPublisher.actionRows());
            assertEquals(actionsBeforeConsumers, fixture.nativeActionWrites());
            assertEquals(readsBeforeConsumers, fixture.nativeReadWrites(), "publisher must only reopen original archive evidence");

            // Unlike a mere DTO check, this enters the actual fresh collector and Driver assembler after the new head.
            fixture.ready();
            DriverSnapshotFacts.Known fresh = known(fixture);
            assertEquals(before.stamp().driverVersion(), fresh.stamp().driverVersion());
            assertEquals(before.stamp().episodeEpoch(), fresh.stamp().episodeEpoch());
            assertArrayEquals(fullBefore, fresh.driver().encode());
            assertTrue(fresh.driver().commandHistory().isEmpty());
            assertTrue(fresh.actionRows().isEmpty());
            assertEquals(before.driver().campaignGoal(), fresh.driver().campaignGoal());
            assertEquals(before.driver().successionExpectation(), fresh.driver().successionExpectation());
            assertFalse(retired.visibleGameplay()); assertFalse(retired.eligibleAdvance());
            long credit = fixture.writer.locked(same -> same.head().state().settledCycles());
            assertEquals(0L, credit);

            var collectorCalls = new AtomicInteger();
            OrdinarySwayPolicy.CopiedSource collector = request -> {
                collectorCalls.incrementAndGet();
                throw new AssertionError("collector must not run for the quarantined original episode");
            };
            OrdinarySwayPolicy.CompositePostcondition postcondition = (request, staged) -> {
                throw new AssertionError("no postcondition or new Sway action should be built");
            };
            var life = command(basis, "software-life-draft", new OperationKey("life-advance"));
            var draft = new OrdinaryPolicy.Draft("software-policy", "ordinary", "source-controlled input",
                    OrdinaryPolicy.Kind.ORDINARY, Optional.of(life), OrdinaryPolicy.Purpose.DATE_ADVANCE,
                    Optional.empty(), new OpportunityJson.Obj(java.util.Map.of()));
            // The same complete public input reaches collection without the new predicate, so the target is not a trivial Keep.
            var unbound = new OrdinarySwayPolicy(fixture.observationSource().sourceRef(), collector, postcondition);
            assertThrows(AssertionError.class, () -> unbound.evaluate(planning, draft));
            assertEquals(1, collectorCalls.get());
            var policy = new OrdinarySwayPolicy(fixture.observationSource().sourceRef(), collector, postcondition);
            policy.bindOperatorQuarantine(request -> CompositeOperatorQuarantinePolicy.quarantinedSway(
                    fixture.snapshot().actions(), request.before().game(), request.before().frame().episodeRunId()));
            var keep = assertInstanceOf(OrdinaryPolicy.Keep.class, policy.evaluate(planning, draft));
            assertTrue(keep.reason().contains("operator-quarantined"));
            assertEquals(1, collectorCalls.get());
            assertThrows(IllegalArgumentException.class, () -> policy.bindOperatorQuarantine(request -> false));

            int beforeActions = fixture.nativeActionWrites(), beforeReads = fixture.nativeReadWrites();
            int beforePreparations = fixture.pendingPreparations.get();
            byte[] beforeFences = fixture.ledgerBytes();
            int ordinal = 0;
            for (OperationKey operation : List.of(PARENT, new OperationKey(SwayNativeWire.START + "33946"),
                    new OperationKey(SwayNativeWire.STOP))) {
                var attempt = command(basis, "different-sway-identity-" + (++ordinal), operation);
                IllegalArgumentException refused = assertThrows(IllegalArgumentException.class,
                        () -> fixture.coordinator.execute(attempt));
                assertTrue(refused.getMessage().contains("operator-quarantined"));
            }
            assertEquals(beforeActions, fixture.nativeActionWrites());
            assertEquals(beforeReads, fixture.nativeReadWrites());
            assertEquals(beforePreparations, fixture.pendingPreparations.get());
            assertArrayEquals(beforeFences, fixture.ledgerBytes());
            assertDoesNotThrow(() -> CompositeOperatorQuarantinePolicy.requireNewActionAllowed(
                    fixture.snapshot().actions(), command(basis, "different-non-sway-identity", CHILD)));

            ObjectNode report = StrictJson.object();
            report.put("schema", "xar.operator-quarantine-consumers-software/v1");
            report.put("parent_role", PARENT.value()); report.put("handler_role", HANDLER);
            report.put("fixture_business", "explicit software handler, not the production Sway executor or actual NativeStart");
            report.put("publisher_reason", ((DriverActionHistoryPublisher.Unchanged) disposition).reason().name());
            report.put("material_source_catalog_replays", materials.operatorChecks.get());
            report.put("legacy_material_capture_calls", materials.captureCalls.get());
            report.put("driver_version_before", before.stamp().driverVersion());
            report.put("driver_version_after", fresh.stamp().driverVersion());
            report.put("full_driver_bytes_before", fullBefore.length);
            report.put("full_driver_sha256_before", ActionCodec.sha256(fullBefore));
            report.put("full_driver_sha256_after", ActionCodec.sha256(fresh.driver().encode()));
            report.put("legacy_rows", fresh.driver().commandHistory().size());
            report.put("coverage_rows", fresh.actionRows().size());
            report.put("control_collector_calls", 1); report.put("quarantined_collector_calls", 0);
            report.put("same_episode_sway_action_fences", ordinal);
            report.put("native_actions", fixture.nativeActionWrites()); report.put("cycle_credit", credit);
            report.put("actual_runtime_v7_nonnull_campaign_goal_and_succession", "NOT_CLAIMED: preserved separately by Runtime");
            report.put("controller_recovery", "NOT_CLAIMED: independently tested by Native");
            Path path = temporary.resolve("operator-quarantine-consumers-summary.json");
            Files.write(path, StrictJson.canonical(report), StandardOpenOption.CREATE_NEW);
            System.out.println("OPERATOR_CONSUMERS_SOFTWARE_REPORT=" + path);
        }
    }

    private static DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture fixture) throws IOException {
        return fixture.writer.locked(same -> fixture.driverAuthority().withFrozenFacts(same,
                frozen -> assertInstanceOf(DriverSnapshotFacts.Known.class, frozen.state())));
    }

    private static DriverActionHistoryPublisher publisher(ActionWriterIntegrationFixture fixture, CatalogMaterials materials) {
        return new DriverActionHistoryPublisher(fixture.driverAuthority(), fixture.journal, fixture.archive, materials,
                List.of(fixture.observationSource().sourceRef()));
    }

    /** The existing material contract delegates to the actual installed catalog; no legacy result or authority is mocked. */
    private static final class CatalogMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture fixture;
        private final boolean enabled;
        final AtomicInteger operatorChecks = new AtomicInteger(), captureCalls = new AtomicInteger();
        CatalogMaterials(ActionWriterIntegrationFixture fixture, boolean enabled) { this.fixture = fixture; this.enabled = enabled; }
        @Override public void requireOwner(DriverStateAssembler authority, ActionJournal journal, ActionPorts.OutcomeArchive archive) {
            assertSame(fixture.driverAuthority(), authority); assertSame(fixture.journal, journal); assertSame(fixture.archive, archive);
        }
        @Override public List<ExactRef> sources() { return List.of(fixture.observationSource().sourceRef()); }
        @Override public void requireOperatorQuarantine(ContinuityStorePort.Session same, ActionReceipt actual,
                ActionPorts.OutcomeArchive archive) throws IOException {
            if (!enabled) { DriverActionHistoryPublisher.MaterialSource.super.requireOperatorQuarantine(same, actual, archive); return; }
            operatorChecks.incrementAndGet();
            fixture.actualBindings().actualArchivedVerifier(actual.command().operation()).orElseThrow()
                    .verifier().verify(same.head(), actual, archive);
        }
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(ContinuityStorePort.Session same,
                ActionReceipt actual, ActionPorts.OutcomeArchive archive) {
            captureCalls.incrementAndGet(); throw new AssertionError("quarantine must not manufacture legacy material");
        }
        @Override public void requireOriginal(ContinuityStorePort.Session same, ActionReceipt actual,
                DriverActionHistoryCodec.OriginalMaterial captured, ActionPorts.OutcomeArchive archive) {
            throw new AssertionError("no fabricated legacy recording path is available");
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
