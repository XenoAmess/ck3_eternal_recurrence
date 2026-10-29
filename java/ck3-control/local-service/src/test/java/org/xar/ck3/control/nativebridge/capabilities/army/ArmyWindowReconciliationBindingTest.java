package org.xar.ck3.control.nativebridge.capabilities.army;

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
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual writer UNKNOWN -> actual Window read producer -> pure binding/codecs, never a native Ready claim. */
final class ArmyWindowReconciliationBindingTest {
    @TempDir Path temporary;
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static PublicMethod close(ArmyWindowCodec.Kind kind) {
        return kind == ArmyWindowCodec.Kind.OVERVIEW ? PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 : PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1;
    }
    private static PublicMethod query(ArmyWindowCodec.Kind kind) {
        return kind == ArmyWindowCodec.Kind.OVERVIEW ? PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1 : PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1;
    }
    private static ArmyCalls.Frame queryCall(ArmyWindowCodec.Kind kind, ReconciliationIdentity identity) {
        return new ArmyCalls.Frame(query(kind), new ArmyCalls.Revision(new ArmyTypes.Present<>(identity.factual().frame().revision())));
    }
    private static ReconciliationIdentity identity(ActionWriterIntegrationFixture fixture, ActionReceipt pending) throws IOException {
        return fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> {
            var attempt = ActionTransitions.attempt(pending.state()).orElseThrow();
            ExactRef driver = archive.preserveMaterial(raw("{\"data_role\":\"original-driver\"}"));
            // Custody documents are deliberately not native/source qualification. Root alone can issue that authority.
            var evidence = new ReconciliationIdentity.Evidence(attempt.guard().nativeEvidence(), attempt.guard().capabilityEvidence(),
                    archive.preserveMaterial(raw("{\"data_role\":\"heartbeat\"}")),
                    archive.preserveMaterial(raw("{\"data_role\":\"manifest\"}")), driver,
                    archive.preserveMaterial(raw("{\"data_role\":\"source-qualification\"}")));
            return ReconciliationIdentity.fromCanonical(pending, pending.command().before(), pending.command().source(),
                    pending.command().sessionId(), attempt.guard().connectionGeneration(), archive.receiptReferenceOf(pending), driver,
                    evidence, Instant.now());
        }));
    }
    private record Fixture(ActionWriterIntegrationFixture writer, ActionReceipt pending, ReconciliationIdentity identity,
            ArmyWindowReads producer, RootReadContractCatalog catalog, ArmyWindowReads.ReconciliationSelection selection,
            ReadContract<ArmyWindowCodec.Observation> contract, PlanningReadRequest request, AtomicInteger dispatches, BigInteger driverGeneration) implements AutoCloseable {
        @Override public void close() throws IOException { writer.close(); }
        void verify() { ArmyWindowReconciliationBinding.verify(pending, ActionTransitions.attempt(pending.state()).orElseThrow(), identity, contract, request, driverGeneration); }
    }
    private Fixture fixture(String name, ArmyWindowCodec.Kind kind, boolean numericPublicRevision) throws Exception {
        return fixture(name,kind,numericPublicRevision,false,BigInteger.ZERO);
    }
    private Fixture fixture(String name,ArmyWindowCodec.Kind kind,boolean numericPublicRevision,boolean direct,BigInteger driverGeneration) throws Exception {
        var dispatches = new AtomicInteger();
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey(kind.step(ArmyWindowCodec.Operation.CLOSE)),
                kind.capability(ArmyWindowCodec.Operation.CLOSE),
                (command, attempt, original) -> new ActionPorts.Pending("controlled window poststate unavailable", List.of(attempt.guard().nativeEvidence())),
                dispatches::incrementAndGet);
        var writer = new ActionWriterIntegrationFixture(temporary.resolve(name), true, scenario);
        try {
            var template = writer.command("window-original-" + name);
            var publicArguments = new com.fasterxml.jackson.databind.ObjectMapper().createObjectNode();
            if (numericPublicRevision) publicArguments.put("expected_revision", template.before().frame().revision());
            else publicArguments.put("expected_revision", template.before().frame().revision().toString());
            ExactRef actualRead = writer.writer.locked(same -> writer.archive.inSession(same,
                    archive -> archive.readReferenceOf(writer.lastNestedRead.get())));
            var arguments = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.valueOf(close(kind).name()),
                    raw(publicArguments.toString()), direct?List.of():List.of(actualRead),
                    direct?ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW:ArmyOrdinaryActionArguments.ExecutionProfile.SDK_ORDINARY, Optional.empty());
            var command = new ActionCommand(template.actionId(), template.origin(), template.source(), template.sessionId(), template.operation(),
                    arguments.encode(), template.expectation(), template.claims(), template.deadline());
            var pending = writer.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, pending.state());
            var identity = identity(writer, pending);
            var producer = new ArmyWindowReads(command.source().sourceRef(), command.source().sourceRef(), writer.reads, writer.archive);
            var catalog = new RootReadContractCatalog(List.of(), producer.families());
            var selection = new ArmyWindowReads.ReconciliationSelection(identity, queryCall(kind, identity), Instant.now().plusSeconds(30),driverGeneration);
            return new Fixture(writer, pending, identity, producer, catalog, selection,
                    producer.issueReconciliation(catalog, selection), producer.requestReconciliation(selection), dispatches,driverGeneration);
        } catch (Exception failure) { writer.close(); throw failure; }
    }
    private static PlanningReadRequest request(Fixture actual, OpportunityJson.Obj arguments) {
        return PlanningReadRequest.newReconciliation(actual.identity(), actual.request().operation(), arguments, actual.request().deadline());
    }
    private static void verify(Fixture actual, PlanningReadRequest request) {
        ArmyWindowReconciliationBinding.verify(actual.pending(), ActionTransitions.attempt(actual.pending().state()).orElseThrow(),
                actual.identity(), actual.contract(), request,actual.driverGeneration());
    }
    @Test void bothActualWindowProducersBindTheirOwnCanonicalUnknownWithoutIssuingAnotherNativeRequest() throws Exception {
        for (var kind : ArmyWindowCodec.Kind.values()) try (var actual = fixture(kind.name(), kind, false)) {
            int reads = actual.writer().nativeReadWrites(); actual.verify();
            assertSame(actual.contract(), actual.producer().issueReconciliation(actual.catalog(), actual.selection()));
            assertTrue(actual.catalog().containsIdentity(actual.contract()));
            assertEquals(1, actual.dispatches().get()); assertEquals(1, actual.writer().nativeActionWrites());
            assertEquals(reads, actual.writer().nativeReadWrites()); assertFalse(actual.pending().settled());
            assertFalse(actual.pending().eligibleAdvance());
        }
    }
    @Test void admittedNumericOriginalRevisionUsesTheSolePublicCodecButTheIndependentProducerKeepsCanonicalText() throws Exception {
        try (var actual = fixture("numeric", ArmyWindowCodec.Kind.RESULTS, true)) {
            actual.verify();
            var original = ArmyOrdinaryActionArguments.decode(actual.pending().command().arguments());
            assertTrue(org.xar.ck3.control.contracts.StrictJson.parse(original.publicArguments().bytes()).get("expected_revision").isIntegralNumber());
            assertInstanceOf(OpportunityJson.Text.class, actual.request().arguments().get("expected_revision"));
            var numeric = new OpportunityJson.Obj(Map.of("expected_revision",
                    new OpportunityJson.IntegerValue(actual.identity().factual().frame().revision())));
            assertThrows(IllegalArgumentException.class, () -> verify(actual, request(actual, numeric)),
                    "a caller cannot substitute a raw public representation for the exact producer request");
        }
    }
    @Test void originalAndIndependentRequestSurviveTheSharedCommandIdentityAndPlanningCodecs() throws Exception {
        try (var actual = fixture("roundtrip", ArmyWindowCodec.Kind.OVERVIEW, false)) {
            assertEquals(actual.pending().command(), ActionCodec.decodeCommand(ActionCodec.encodeCommand(actual.pending().command())));
            var identity = ReconciliationIdentityCodec.decode(ReconciliationIdentityCodec.encode(actual.identity()));
            var request = CommandOriginCodec.planningRequest(CommandOriginCodec.planningRequest(actual.request(), identity.pending().originalBeforeDriver()), actual.request().arguments());
            assertEquals(actual.identity(), identity); assertEquals(actual.request(), request);
            ArmyWindowReconciliationBinding.verify(actual.pending(), ActionTransitions.attempt(actual.pending().state()).orElseThrow(),
                    identity, actual.contract(), request,actual.driverGeneration());
            ObjectNode encoded = ReconciliationIdentityCodec.encode(identity);
            ((ObjectNode) encoded.get("pending")).put("request_id", "another-attempt");
            var wrong = ReconciliationIdentityCodec.decode(encoded);
            assertThrows(IllegalArgumentException.class, () -> ArmyWindowReconciliationBinding.verify(actual.pending(),
                    ActionTransitions.attempt(actual.pending().state()).orElseThrow(), wrong, actual.contract(),
                    PlanningReadRequest.newReconciliation(wrong, request.operation(), request.arguments(), request.deadline()),actual.driverGeneration()));
            assertEquals(1, actual.writer().nativeActionWrites());
        }
    }
    @Test void ordinaryM5AnotherWindowAndInventedContractDescriptorsCannotBorrowWindow2() throws Exception {
        try (var actual = fixture("wrong-family", ArmyWindowCodec.Kind.RESULTS, false)) {
            var ordinary = new PlanningReadRequest(actual.identity().factual(), actual.identity().source(), actual.identity().sessionId(),
                    actual.request().operation(), actual.request().arguments(), actual.request().deadline());
            assertThrows(IllegalArgumentException.class, () -> verify(actual, ordinary));
            for (String step : List.of("query-war-declared-overview-v1", "query-battle-terminal-transition-v1")) {
                var wrong = PlanningReadRequest.newReconciliation(actual.identity(), new OperationKey(step), actual.request().arguments(), actual.request().deadline());
                assertThrows(IllegalArgumentException.class, () -> verify(actual, wrong));
            }
            var invented = new ReadContract<RawJson>("uninstalled-window-lookalike", actual.contract().operation(), actual.contract().requiredCapability(),
                    actual.contract().permissionKey(), actual.contract().permissionMode(), actual.contract().wireProfile(),
                    actual.contract().guardMode(), actual.contract().sourceRef(),
                    (query, id) -> actual.contract().prepare(query, id), receipt -> receipt.original().originalResultToken().orElseThrow());
            assertThrows(IllegalArgumentException.class, () -> ArmyWindowReconciliationBinding.verify(actual.pending(),
                    ActionTransitions.attempt(actual.pending().state()).orElseThrow(), actual.identity(), invented, actual.request(),actual.driverGeneration()));
        }
    }
    @Test void sourceSessionAndPrimitiveAttemptDriftFailWithoutRepeatingTheClose() throws Exception {
        try (var actual = fixture("origin-drift", ArmyWindowCodec.Kind.OVERVIEW, false);
                var foreign = fixture("foreign", ArmyWindowCodec.Kind.RESULTS, false)) {
            var original = actual.identity();
            var wrongSource = new ReconciliationIdentity(original.factual(), foreign.identity().source(), original.sessionId(),
                    original.connectionGeneration(), original.pending(), original.evidence(), original.observedAt());
            var wrongSession = new ReconciliationIdentity(original.factual(), original.source(), "foreign-session",
                    original.connectionGeneration(), original.pending(), original.evidence(), original.observedAt());
            for (var wrong : List.of(wrongSource, wrongSession)) {
                var request = PlanningReadRequest.newReconciliation(wrong, actual.request().operation(), actual.request().arguments(), actual.request().deadline());
                assertThrows(IllegalArgumentException.class, () -> ArmyWindowReconciliationBinding.verify(actual.pending(),
                        ActionTransitions.attempt(actual.pending().state()).orElseThrow(), wrong, actual.contract(), request,actual.driverGeneration()));
            }
            assertThrows(IllegalArgumentException.class, () -> ArmyWindowReconciliationBinding.verify(actual.pending(),
                    ActionTransitions.attempt(foreign.pending().state()).orElseThrow(), original, actual.contract(), actual.request(),actual.driverGeneration()));
            assertEquals(1, actual.writer().nativeActionWrites()); assertEquals(1, foreign.writer().nativeActionWrites());
        }
    }
    @Test void queryBoundaryRejectsWrongMissingNullBooleanFractionalUnsafeAndExtraSelectorFields() throws Exception {
        try (var actual = fixture("closed-fields", ArmyWindowCodec.Kind.RESULTS, false)) {
            for (String json : List.of("{}", "{\"expected_revision\":null}", "{\"expected_revision\":true}",
                    "{\"expected_revision\":1.0}", "{\"expected_revision\":9007199254740992}",
                    "{\"expected_revision\":\"01\"}", "{\"expected_revision\":\"-1\"}",
                    "{\"expected_revision\":\"1\",\"window_name\":\"war_results\"}")) {
                assertThrows(IllegalArgumentException.class, () -> {
                    var arguments = OpportunityJson.object(OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)), "invalid test arguments");
                    verify(actual, request(actual, arguments));
                }, json);
            }
            assertEquals(1, actual.writer().nativeActionWrites());
        }
    }

    @Test void explicitDirectZeroPreflightAndSemanticDriverZeroOrSeventeenBindWithoutBorrowingNativeGeneration() throws Exception {
        for(var kind:ArmyWindowCodec.Kind.values())for(BigInteger driver:List.of(BigInteger.ZERO,BigInteger.valueOf(17)))
            try(var actual=fixture("direct-"+kind+"-"+driver,kind,false,true,driver)){
                actual.verify();
                var original=ArmyOrdinaryActionArguments.decode(actual.pending().command().arguments());
                assertEquals(ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW,original.executionProfile());
                assertTrue(original.preflightReads().isEmpty());
                assertNotEquals(driver,actual.identity().connectionGeneration());
                assertThrows(IllegalArgumentException.class,()->ArmyWindowReconciliationBinding.verify(actual.pending(),
                        ActionTransitions.attempt(actual.pending().state()).orElseThrow(),actual.identity(),actual.contract(),actual.request(),
                        driver.equals(BigInteger.ZERO)?BigInteger.ONE:BigInteger.ZERO));
                assertThrows(IllegalArgumentException.class,()->ArmyWindowReconciliationBinding.verify(actual.pending(),
                        ActionTransitions.attempt(actual.pending().state()).orElseThrow(),actual.identity(),actual.contract(),actual.request(),BigInteger.valueOf(-1)));
                assertEquals(actual.pending().command(),ActionCodec.decodeCommand(ActionCodec.encodeCommand(actual.pending().command())));
                assertFalse(actual.pending().settled());assertEquals(1,actual.writer().nativeActionWrites());
            }
    }
}

