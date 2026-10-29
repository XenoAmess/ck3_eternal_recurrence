package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.ServiceLoader;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.contracts.projection.ProjectionHostContext;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.wave2.events.projection.FullEventSourceProjectionCatalog;

/** Portable original source bytes and synthetic native frames; this does not qualify the current installation or machine. */
final class FullEventSourceProjectionTest {
    @TempDir Path temporary;

    @TestFactory Stream<DynamicTest> originalExistingPlansReachTheActualSourceReaderAndExistingPolicies() throws IOException {
        ObjectValue corpus = SourceReviewedEventConsumerTest.golden();
        List<ObjectValue> pipelines = objects(corpus, "cases").stream().filter(row -> eq(row, "mode", s("pipeline"))).toList();
        assertEquals(9, pipelines.size());
        return pipelines.stream().map(row -> DynamicTest.dynamicTest(text(row, "name"), () -> {
            Path root = temporary.resolve(text(row, "name"));
            SourceReviewedEventConsumerTest.Relocated input = SourceReviewedEventConsumerTest.relocate(corpus, row, root);
            installStock(corpus, root.resolve("game"));
            ProjectionDispatcher dispatcher = dispatcher(input.state(), root.resolve("game"));
            ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class,
                    dispatch(dispatcher, request(RetainedJson.object(input.plan()), v(row, "snapshot"), v(row, "action_steps"))));
            assertEquals(input.expected(), RetainedJson.parse(result.result().bytes()));
            for (Map.Entry<Path, byte[]> file : input.initialFiles().entrySet()) assertArrayEquals(file.getValue(), Files.readAllBytes(file.getKey()));
        }));
    }

    @Test void absentHostContextMakesTheFullOperationUnavailableAndCannotBeSuppliedByPayload() {
        FullEventSourceProjectionCatalog catalog = catalog();
        assertTrue(catalog.registrations().isEmpty());
        assertTrue(catalog.registrations(ProjectionHostContext.empty()).isEmpty());
        ProjectionResult.Rejected missing = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(new ProjectionDispatcher(catalog.registrations(ProjectionHostContext.empty())), obj()));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, missing.error().code());
        assertThrows(IllegalArgumentException.class, () -> SourceReviewedPlanJson.decode(RetainedJson.encode(obj(
                f("schema", s(SourceReviewedPlanJson.SCHEMA)), f("plan", obj()), f("snapshot", NULL),
                f("action_steps", new ArrayValue(List.of())), f("state_directory", s(temporary.toString()))))));
    }

    @Test void configuredButUnqualifiedSourceContextReturnsBoundUnavailable() throws IOException {
        ObjectValue corpus = SourceReviewedEventConsumerTest.golden(); ObjectValue row = pipeline(corpus);
        Path state = Files.createDirectories(temporary.resolve("empty-state")); Path game = Files.createDirectories(temporary.resolve("empty-game"));
        ProjectionResult.Rejected result = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(dispatcher(state, game), request(o(row, "plan"), v(row, "snapshot"), v(row, "action_steps"))));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, result.error().code());
        assertEquals(ProjectionOperation.EVENTS_UNHANDLED_PLAN_SOURCE_REVIEWED, result.identity().orElseThrow().operation());
    }

    @Test void callerKnownFlagsCannotReplaceAnActualRegistryRead() throws IOException {
        ObjectValue corpus = SourceReviewedEventConsumerTest.golden(); ObjectValue row = pipeline(corpus);
        Path state = Files.createDirectories(temporary.resolve("empty-registry")); Path game = temporary.resolve("known-game"); installStock(corpus, game);
        ObjectValue plan = o(row, "plan"); ObjectValue capture = o(plan, "unhandled_event_fallback");
        plan = plan.with("unhandled_event_fallback", put(capture, f("registry_known", b(true)),
                f("offline_followup_required", b(false)), f("source_knowledge", obj(f("status", s("offline-source-reviewed"))))));
        ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatch(dispatcher(state, game), request(plan, v(row, "snapshot"), v(row, "action_steps"))));
        ObjectValue actual = o(RetainedJson.object(RetainedJson.parse(result.result().bytes())), "unhandled_event_fallback");
        assertEquals(b(false), v(actual, "registry_known")); assertEquals(b(true), v(actual, "offline_followup_required"));
        assertEquals(s("unknown"), v(o(actual, "source_knowledge"), "status"));
    }

    @Test void historicalFactsRequireTheExactServerGrantAndStillValidateTheOriginalReviewDeclaration() throws IOException {
        ObjectValue corpus = SourceReviewedEventConsumerTest.golden(); ObjectValue row = pipeline(corpus); Path root = temporary.resolve("custody");
        SourceReviewedEventConsumerTest.Relocated input = SourceReviewedEventConsumerTest.relocate(corpus, row, root);
        Path game = root.resolve("game"); installStock(corpus, game);
        Path entry;
        try (Stream<Path> paths = Files.list(input.state().resolve("evidence/event-source-registry"))) {
            entry = paths.filter(path -> path.getFileName().toString().endsWith(".json")).findFirst().orElseThrow();
        }
        ObjectValue original = RetainedJson.object(RetainedJson.parse(Files.readAllBytes(entry))); ObjectValue facts = o(original, "source_facts");
        Path outside = root.resolve("outside-facts.json"); Files.copy(Path.of(text(facts, "path")), outside);
        Files.write(entry, RetainedJson.encode(original.with("source_facts", facts.with("path", s(outside.toString())))));
        ObjectValue request = request(RetainedJson.object(input.plan()), v(row, "snapshot"), v(row, "action_steps"));
        ProjectionResult.Rejected missing = assertInstanceOf(ProjectionResult.Rejected.class, dispatch(dispatcher(input.state(), game), request));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, missing.error().code());
        byte[] historical = Files.readAllBytes(outside);
        ProjectionEvidenceGrant grant = new ProjectionEvidenceGrant(outside, historical.length, sha(historical), "portable-original-fixture",
                ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        EventSourceReadContext configured = new EventSourceReadContext("portable-source-fixture", input.state(), game, List.of(grant));
        ProjectionDispatcher qualified = new ProjectionDispatcher(catalog().registrations(new ProjectionHostContext(Optional.of(configured))));
        ProjectionResult.Succeeded admitted = assertInstanceOf(ProjectionResult.Succeeded.class, dispatch(qualified, request));
        ObjectValue actualPlan = RetainedJson.object(RetainedJson.parse(admitted.result().bytes()));
        assertEquals(b(true), v(o(actualPlan, "unhandled_event_fallback"), "registry_known"));
        assertEquals(v(RetainedJson.object(input.expected()), "selected_step"), v(actualPlan, "selected_step"));
        TrustedEventSourceContext trusted = TrustedEventSourceContext.open(configured);
        assertArrayEquals(historical, trusted.readDeclared(outside, 1_048_576, ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
        assertThrows(TrustedEventSourceContext.UnavailableException.class,
                () -> trusted.readDeclared(outside, 1_048_576, ProjectionEvidenceRole.UI_RECOVERY_BEFORE));
        ObjectValue changed = RetainedJson.object(RetainedJson.parse(Files.readAllBytes(entry)));
        Files.write(entry, RetainedJson.encode(changed.with("source_facts", o(changed, "source_facts").with("sha256", s("0".repeat(64))))));
        ProjectionResult.Succeeded invalidDeclaration = assertInstanceOf(ProjectionResult.Succeeded.class, dispatch(qualified, request));
        assertEquals(b(false), v(o(RetainedJson.object(RetainedJson.parse(invalidDeclaration.result().bytes())), "unhandled_event_fallback"), "registry_known"));
        Files.writeString(outside, "changed", StandardOpenOption.APPEND);
        assertThrows(TrustedEventSourceContext.UnavailableException.class,
                () -> trusted.readDeclared(outside, 1_048_576, ProjectionEvidenceRole.EVENT_SOURCE_FACTS));
        Files.writeString(game.resolve("gui/event_windows/letter_event.gui"), "changed", StandardOpenOption.APPEND);
        assertThrows(TrustedEventSourceContext.UnavailableException.class, trusted::verifyCurrentRoots);
    }

    @Test void uiEvidenceReaderDoesNotRequireUnrelatedEventSourceAnchors() throws IOException {
        Path state = Files.createDirectories(temporary.resolve("ui-state")); Path game = Files.createDirectories(temporary.resolve("ui-game"));
        Path before = temporary.resolve("historical-before.json"); byte[] original = "{\"original\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(before, original);
        ProjectionEvidenceGrant grant = new ProjectionEvidenceGrant(before, original.length, sha(original), "unknown", ProjectionEvidenceRole.UI_RECOVERY_BEFORE);
        TrustedEventSourceContext trusted = TrustedEventSourceContext.openEvidence(new EventSourceReadContext("portable-source-fixture", state, game, List.of(grant)));
        assertArrayEquals(original, trusted.readDeclared(before, 65_536, ProjectionEvidenceRole.UI_RECOVERY_BEFORE));
        assertEquals("unknown", trusted.declaredGrant(before, ProjectionEvidenceRole.UI_RECOVERY_BEFORE).originMachineId());
        assertThrows(TrustedEventSourceContext.UnavailableException.class, trusted::verifyCurrentRoots);
    }

    private static ObjectValue pipeline(ObjectValue corpus) {
        return objects(corpus, "cases").stream().filter(row -> eq(row, "name", s("faction_demand.0101-exact-stock"))).findFirst().orElseThrow();
    }
    private static ObjectValue request(ObjectValue plan, Value snapshot, Value steps) {
        return obj(f("schema", s(SourceReviewedPlanJson.SCHEMA)), f("plan", plan), f("snapshot", snapshot), f("action_steps", steps));
    }
    private static ProjectionResult dispatch(ProjectionDispatcher dispatcher, ObjectValue request) {
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("source-review-integration", ProjectionOperation.EVENTS_UNHANDLED_PLAN_SOURCE_REVIEWED),
                ProjectionJson.object(RetainedJson.encode(request), 1_048_576));
        return dispatcher.dispatch(ProjectionWire.encodeCall(call));
    }
    private static ProjectionDispatcher dispatcher(Path state, Path game) {
        ProjectionHostContext context = new ProjectionHostContext(Optional.of(new EventSourceReadContext("portable-source-fixture", state, game)));
        return new ProjectionDispatcher(catalog().registrations(context));
    }
    private static FullEventSourceProjectionCatalog catalog() {
        List<ServiceLoader.Provider<ProjectionPortCatalog>> providers = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type() == FullEventSourceProjectionCatalog.class).toList();
        assertEquals(1, providers.size()); return assertInstanceOf(FullEventSourceProjectionCatalog.class, providers.getFirst().get());
    }
    private static void installStock(ObjectValue corpus, Path game) throws IOException {
        for (Map.Entry<String, String> pin : ReviewedLetterSourceRebind.installedSourceHashes().entrySet()) {
            byte[] packed = Base64.getDecoder().decode(text(o(corpus, "blobs"), pin.getValue())); byte[] original;
            try (GZIPInputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                original = input.readNBytes(2_097_153); if (original.length > 2_097_152) throw new IOException("original source bound exceeded");
            }
            assertEquals(pin.getValue(), sha(original)); Path target = game.resolve(pin.getKey()); Files.createDirectories(target.getParent());
            if (Files.exists(target)) assertArrayEquals(original, Files.readAllBytes(target));
            else Files.write(target, original, StandardOpenOption.CREATE_NEW);
        }
    }
}
