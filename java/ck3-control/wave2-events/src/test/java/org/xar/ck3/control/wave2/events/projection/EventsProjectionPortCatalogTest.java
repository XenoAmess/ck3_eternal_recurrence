package org.xar.ck3.control.wave2.events.projection;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.ServiceLoader;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;

/** Original producers cross standard provider discovery, the public envelope and the registered typed domain codecs. */
final class EventsProjectionPortCatalogTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private record Corpus(ProjectionOperation operation, String resource, String cases, String output, int count) { }
    private record Vector(Corpus corpus, JsonNode row, int ordinal) { }
    private static final List<Corpus> CORPORA = List.of(
            new Corpus(ProjectionOperation.EVENTS_MANDATORY_CHOICE_PLAN, "/choiceplanning/producer-golden-v1.json.gz", "cases", "output", 20),
            new Corpus(ProjectionOperation.EVENTS_UI_RECOVERY_FINGERPRINT, "/uirecoveryidentity/producer-golden-v1.json", "cases", "output", 20),
            new Corpus(ProjectionOperation.EVENTS_MANDATORY_BEFORE, "/mandatorybefore/producer-golden-v1.json.gz", "cases", "output", 14),
            new Corpus(ProjectionOperation.EVENTS_MANDATORY_RECEIPT, "/mandatoryreceipt/producer-golden-v1.json", "cases", "output", 15),
            new Corpus(ProjectionOperation.EVENTS_UNHANDLED_PLAN_CANDIDATE, "/unhandledevent/unhandled-event-golden-v1.json.gz", "plan_cases", "expected_plan", 21));

    @TestFactory Stream<DynamicTest> actualProducerResultsSurviveTheRegisteredDispatcherBoundary() throws IOException {
        ProjectionDispatcher dispatcher = dispatcher();
        List<Vector> vectors = new ArrayList<>();
        for (Corpus corpus : CORPORA) {
            JsonNode rows = fixture(corpus.resource()).get(corpus.cases());
            assertEquals(corpus.count(), rows.size(), corpus.resource());
            for (JsonNode row : rows) { vectors.add(new Vector(corpus, row, vectors.size())); }
        }
        assertEquals(90, vectors.size());
        return vectors.stream().map(vector -> DynamicTest.dynamicTest(
                vector.corpus().operation().wire() + "/" + vector.row().get("name").textValue(), () -> {
                    byte[] payload = JSON.writeValueAsBytes(vector.row().get("request"));
                    ProjectionCall.Identity identity = new ProjectionCall.Identity("events-producer-" + vector.ordinal(), vector.corpus().operation());
                    ProjectionResult result = dispatch(dispatcher, identity, payload);
                    if (vector.row().path("rejected").booleanValue()) {
                        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, result);
                        assertEquals(identity, rejected.identity().orElseThrow());
                        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
                    } else {
                        ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, result);
                        assertEquals(identity, succeeded.identity());
                        assertEquals(vector.row().get(vector.corpus().output()), JSON.readTree(succeeded.result().bytes()));
                        JsonNode wireResult = JSON.readTree(ProjectionWire.encodeResult(succeeded));
                        assertEquals(identity.requestId(), wireResult.get("request_id").textValue());
                        assertEquals(identity.operation().wire(), wireResult.get("operation").textValue());
                    }
                }));
    }

    @Test void standardServiceProviderRegistersOnlyTheFiveExplicitPureOperationsAndTheirOriginalBudgets() {
        ProjectionDispatcher dispatcher = dispatcher();
        assertEquals(5, dispatcher.profiles().size());
        assertEquals(65_536, StrictJson.INPUT_MAX_BYTES, "the shared JSON boundary must retain its original bound");
        for (Corpus corpus : CORPORA) {
            ProjectionDispatcher.OperationProfile profile = dispatcher.profiles().stream()
                    .filter(value -> value.operation() == corpus.operation()).findFirst().orElseThrow();
            int maximum = corpus.operation() == ProjectionOperation.EVENTS_UNHANDLED_PLAN_CANDIDATE ? 1_048_576 : 65_536;
            assertEquals(maximum, profile.inputMaximumBytes()); assertEquals(maximum, profile.outputMaximumBytes());
        }
    }

    @Test void eachDomainCodecRejectsAnEmptyPayloadThroughTheSamePublicConsumer() {
        ProjectionDispatcher dispatcher = dispatcher();
        for (Corpus corpus : CORPORA) {
            ProjectionCall.Identity identity = new ProjectionCall.Identity("invalid-events-payload", corpus.operation());
            ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatch(dispatcher, identity, "{}".getBytes(StandardCharsets.UTF_8)));
            assertEquals(identity, rejected.identity().orElseThrow());
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
        }
    }

    @Test void candidateKeepsItsExplicitOneMiBBoundaryWithoutBorrowingSourceKnowledgeOrWideningTheOtherPorts() throws IOException {
        ProjectionDispatcher dispatcher = dispatcher();
        for (Corpus corpus : CORPORA) {
            JsonNode row = fixture(corpus.resource()).get(corpus.cases()).get(0);
            byte[] original = JSON.writeValueAsBytes(row.get("request"));
            String extended = new String(original, StandardCharsets.UTF_8) + " ".repeat(65_537 - original.length);
            byte[] payload = extended.getBytes(StandardCharsets.UTF_8);
            assertEquals(65_537, payload.length);
            ProjectionResult result = dispatch(dispatcher, new ProjectionCall.Identity("events-role-boundary", corpus.operation()), payload);
            if (corpus.operation() == ProjectionOperation.EVENTS_UNHANDLED_PLAN_CANDIDATE) {
                ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, result);
                JsonNode candidate = JSON.readTree(succeeded.result().bytes());
                assertEquals(row.get(corpus.output()), candidate);
                JsonNode capture = candidate.get("unhandled_event_fallback");
                assertFalse(capture.has("registry_known"));
                assertTrue(capture.get("offline_followup_required").booleanValue());
                assertFalse(capture.has("source_knowledge"));
            } else {
                assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE,
                        assertInstanceOf(ProjectionResult.Rejected.class, result).error().code());
            }
        }
    }

    private static ProjectionResult dispatch(ProjectionDispatcher dispatcher, ProjectionCall.Identity identity, byte[] payload) {
        ProjectionCall call = new ProjectionCall(identity, ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
        return dispatcher.dispatch(ProjectionWire.encodeCall(call));
    }

    private static ProjectionDispatcher dispatcher() {
        List<ServiceLoader.Provider<ProjectionPortCatalog>> providers = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type() == EventsProjectionPortCatalog.class).toList();
        assertEquals(1, providers.size(), "standard META-INF/services discovery must expose the events catalog once");
        return ProjectionDispatcher.fromCatalogs(List.of(providers.getFirst().get()));
    }

    private static JsonNode fixture(String name) throws IOException {
        try (InputStream resource = EventsProjectionPortCatalogTest.class.getResourceAsStream(name)) {
            assertNotNull(resource, "actual original producer resource is mandatory: " + name);
            try (InputStream input = name.endsWith(".gz") ? new GZIPInputStream(resource) : resource) {
                byte[] raw = input.readNBytes(1_048_577);
                if (raw.length > 1_048_576) { throw new IOException("producer golden exceeds its explicit fixture bound"); }
                return JSON.readTree(raw);
            }
        }
    }
}
