package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual canonical UNKNOWN producer -> typed readonly data/codecs. Fresh source/readiness remains the installed authority. */
final class ReconciliationContractTest {
    @TempDir Path temporary;
    private static final OperationKey OPERATION = new OperationKey("query-army-commander-candidates-v1-for-army-1");
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static ReconciliationIdentity identity(ActionWriterIntegrationFixture fixture, ActionReceipt original) throws IOException {
        return fixture.writer.locked(session -> fixture.archive.inSession(session, archive -> {
            ActionState.Attempt attempt = ActionTransitions.attempt(original.state()).orElseThrow();
            ExactRef driver = archive.preserveMaterial(raw("{\"software_data_role\":\"unchanged-driver\"}"));
            // These documents deliberately establish only copied artifact custody. They are not full Driver/source/heartbeat qualification.
            ExactRef heartbeat = archive.preserveMaterial(raw("{\"software_data_role\":\"heartbeat\"}"));
            ExactRef manifest = archive.preserveMaterial(raw("{\"software_data_role\":\"manifest\"}"));
            ExactRef source = archive.preserveMaterial(raw("{\"software_data_role\":\"source-proof\"}"));
            var evidence = new ReconciliationIdentity.Evidence(attempt.guard().nativeEvidence(), attempt.guard().capabilityEvidence(),
                    heartbeat, manifest, driver, source);
            return ReconciliationIdentity.fromCanonical(original, original.command().before(), original.command().source(),
                    original.command().sessionId(), attempt.guard().connectionGeneration(), archive.receiptReferenceOf(original), driver, evidence, Instant.now());
        }));
    }
    private static PlanningReadRequest request(ReconciliationIdentity identity) {
        return PlanningReadRequest.newReconciliation(identity, OPERATION,
                new OpportunityJson.Obj(Map.of("army_id", new OpportunityJson.IntegerValue(BigInteger.ONE))), identity.observedAt().plusSeconds(30));
    }
    private static GuardEvidence binding(ReconciliationIdentity identity) {
        return new GuardEvidence(new CommandOrigin.Reconciliation(identity), identity.source(), identity.sessionId(), identity.connectionGeneration(),
                OPERATION, identity.nativeEvidence(), identity.capabilityEvidence(), "reconciliation-data-fixture",
                identity.observedAt(), identity.observedAt().plusSeconds(30), List.of(identity.evidence().completeSourceQualification().orElseThrow()));
    }
    private static ReadContract<String> contract(ReconciliationIdentity identity, ReadContract.GuardMode mode) {
        return new ReadContract<>("army:commander:reconciliation/v1", OPERATION, Optional.of("game.command." + OPERATION.value()),
                "actual-source-qualified-reconciliation-query", ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                ReadContract.WireProfile.EXECUTE_STEP, mode, identity.source().sourceRef(),
                (actual, requestId) -> {
                    var factual = actual.reconciliationBefore();
                    assertEquals(identity.factual(), factual);
                    return new NativeRequest(OPERATION.value(), "game.command." + OPERATION.value(), raw("{\"army_id\":1}"));
                }, ignored -> "typed-original-data", ignored -> "typed-original-data");
    }
    @Test void actualCanonicalUnknownKeepsItsReadonlyOriginThroughTheSoleDurableCodec() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("origin"), true)) {
            ActionReceipt pending = fixture.coordinator.execute(fixture.command("reconciliation-codec-original"));
            assertInstanceOf(ActionState.Unknown.class, pending.state()); ReconciliationIdentity identity = identity(fixture, pending);
            var origin = new CommandOrigin.Reconciliation(identity);
            var row = CommandOriginCodec.origin(origin); assertEquals(CommandOriginCodec.RECONCILIATION_ORIGIN_SCHEMA, row.get("schema").textValue());
            assertEquals("RECONCILIATION", row.get("kind").textValue()); assertEquals(origin, CommandOriginCodec.origin(row));
            assertEquals(identity, ReconciliationIdentityCodec.decode(ReconciliationIdentityCodec.encode(identity)));
            assertThrows(IllegalStateException.class, origin::requireGameplay); assertThrows(IllegalStateException.class, origin::requireFrontend);
            assertThrows(IllegalStateException.class, origin::requireLifecycleTerminal); assertEquals(identity.factual().frame().identity().nativeRevision(), origin.expectedRevision());
            assertEquals(1, fixture.nativeActionWrites()); assertFalse(pending.settled());
        }
    }
    @Test void requestGuardAndReadinessRoundTripWithoutBorrowingOrdinaryBeforeOrLivingFlags() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("request"), true)) {
            ActionReceipt pending = fixture.coordinator.execute(fixture.command("reconciliation-read-original")); var identity = identity(fixture, pending);
            int originalReadWrites = fixture.nativeReadWrites();
            PlanningReadRequest request = request(identity); assertEquals(identity.factual(), request.reconciliationBefore());
            assertThrows(IllegalStateException.class, request::before);
            var row = CommandOriginCodec.planningRequest(request, identity.pending().originalBeforeDriver());
            assertEquals("xar.reconciliation-planning-request/v1", row.get("schema").textValue()); assertFalse(row.has("before"));
            assertEquals(request, CommandOriginCodec.planningRequest(row, request.arguments()));
            var guard = new PlanningReadGuard(binding(identity), new PlanningReadGuard.Reconciliation(), identity.bindingSha256());
            assertEquals(ReadContract.GuardMode.RECONCILIATION_OBSERVATION, guard.guardMode());
            assertEquals(guard, CommandOriginCodec.planningGuard(CommandOriginCodec.planningGuard(guard)));
            assertEquals(guard.binding(), CommandOriginCodec.guard(CommandOriginCodec.guard(guard.binding())));
            assertThrows(IllegalStateException.class, guard::paused); assertThrows(IllegalStateException.class, guard::mapReady); assertThrows(IllegalStateException.class, guard::playerAlive);
            assertThrows(IllegalArgumentException.class, () -> new PlanningReadGuard(binding(identity), true, true, true, identity.bindingSha256()));
            assertEquals(originalReadWrites, fixture.nativeReadWrites()); // Data parsing/preparation cannot issue a Root permit.
        }
    }
    @Test void onlyTheExplicitInstalledModeMayPrepareItsFactualQueryAndCouncilStatusIsExcluded() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("contract"), true)) {
            var pending = fixture.coordinator.execute(fixture.command("reconciliation-contract-original")); var identity = identity(fixture, pending);
            int originalReadWrites = fixture.nativeReadWrites();
            var contract = contract(identity, ReadContract.GuardMode.RECONCILIATION_OBSERVATION); var request = request(identity);
            assertEquals(OPERATION.value(), contract.prepare(request, "actual-independent-query-id").step());
            assertThrows(IllegalArgumentException.class, () -> contract(identity, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).prepare(request, "wrong-mode-query"));
            var ordinary = new PlanningReadRequest(identity.factual(), identity.source(), identity.sessionId(), OPERATION, request.arguments(), request.deadline());
            assertThrows(IllegalArgumentException.class, () -> contract.prepare(ordinary, "not-reconciliation"));
            assertThrows(IllegalArgumentException.class, () -> new ReadContract<String>("no-council-status-reconciliation/v1",
                    new OperationKey("private-council-application-main-status-v1"), Optional.empty(), "not-a-continuation-permit",
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS,
                    ReadContract.GuardMode.RECONCILIATION_OBSERVATION, identity.source().sourceRef(),
                    (actual, id) -> new NativeRequest("private-council-application-main-status-v1", Optional.empty(), raw("{}")), ignored -> "data"));
            assertEquals(originalReadWrites, fixture.nativeReadWrites()); assertEquals(1, fixture.nativeActionWrites());
        }
    }
    @Test void readonlyIdentityCanNeverConstructAnActionOrBorrowAnotherPendingGuard() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("no-action"), true)) {
            var pending = fixture.coordinator.execute(fixture.command("reconciliation-no-action-original")); var identity = identity(fixture, pending);
            var command = pending.command(); var origin = new CommandOrigin.Reconciliation(identity);
            assertThrows(IllegalArgumentException.class, () -> new ActionCommand("forbidden-reconciliation-action", origin, command.source(), command.sessionId(),
                    command.operation(), command.arguments(), command.expectation(), command.claims(), command.deadline()));
            var differentPending = new ReconciliationIdentity.Pending(identity.pending().actionId(), identity.pending().bodySha256(), "another-original-request",
                    identity.pending().originalBefore(), identity.pending().originalReceipt(), identity.pending().originalBeforeDriver());
            var another = new ReconciliationIdentity(identity.factual(), identity.source(), identity.sessionId(), identity.connectionGeneration(),
                    differentPending, identity.evidence(), identity.observedAt());
            assertFalse(origin.acceptsGuard(new CommandOrigin.Reconciliation(another)));
            assertFalse(origin.acceptsGuard(new CommandOrigin.Gameplay(identity.factual())));
            assertThrows(IllegalArgumentException.class, () -> new GuardEvidence(origin, identity.source(), identity.sessionId(), identity.connectionGeneration(), OPERATION,
                    identity.nativeEvidence(), identity.capabilityEvidence(), "no-physical-basis", identity.observedAt(), identity.observedAt().plusSeconds(1)));
        }
    }
    @Test void closedIdentityAndPhaseSchemasRejectMissingNullWrongTypesAndDriverDrift() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("strict"), true)) {
            var pending = fixture.coordinator.execute(fixture.command("reconciliation-strict-original")); var identity = identity(fixture, pending);
            int originalReadWrites = fixture.nativeReadWrites();
            var encoded = ReconciliationIdentityCodec.encode(identity);
            ObjectNode missing = encoded.deepCopy(); ((ObjectNode) missing.get("evidence")).remove("original_heartbeat");
            assertThrows(IllegalArgumentException.class, () -> ReconciliationIdentityCodec.decode(missing));
            ObjectNode numeric = encoded.deepCopy(); numeric.put("connection_generation", identity.connectionGeneration());
            assertThrows(IllegalArgumentException.class, () -> ReconciliationIdentityCodec.decode(numeric));
            ObjectNode nil = encoded.deepCopy(); ((ObjectNode) nil.get("pending")).putNull("request_id");
            assertThrows(IllegalArgumentException.class, () -> ReconciliationIdentityCodec.decode(nil));
            ObjectNode driver = encoded.deepCopy(); ((ObjectNode) ((ObjectNode) driver.get("evidence")).get("current_original_driver")).put("sha256", "f".repeat(64));
            assertThrows(IllegalArgumentException.class, () -> ReconciliationIdentityCodec.decode(driver));
            ObjectNode wrongPhase = CommandOriginCodec.origin(new CommandOrigin.Reconciliation(identity)); wrongPhase.put("schema", CommandOriginCodec.LIFECYCLE_ORIGIN_SCHEMA);
            assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.origin(wrongPhase));
            var guard = new PlanningReadGuard(binding(identity), new PlanningReadGuard.Reconciliation(), identity.bindingSha256());
            ObjectNode wrongGuard = CommandOriginCodec.planningGuard(guard); wrongGuard.put("schema", "xar.lifecycle-terminal-planning-guard/v1");
            assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.planningGuard(wrongGuard));
            assertEquals(64, identity.bindingSha256().length()); assertEquals(originalReadWrites, fixture.nativeReadWrites());
        }
    }
}
