package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrants;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Real original stock bytes and original Python facts, with synthetic native frames; no installation/Game qualification. */
final class OfflineEventBatchAnalyzerTest {
    @TempDir Path temporary;
    private record Fixture(ObjectValue corpus, ObjectValue row, ObjectValue plan, Path game, Path state, Path incidents,
            Path knowledge, Path manifest, OfflineEventBatchAnalyzer.Configuration configuration) { }

    @Test void actualBeforeProducerToSourceAnalysisPublicationReplayAndNextKnownBatchIsClosed() throws IOException {
        Fixture fixture = fixture("closed");
        OfflineEventBatchAnalyzer.Request request = batch(fixture, "first", "a".repeat(32), fixture.plan());
        OfflineEventBatchAnalyzer.Result first = OfflineEventBatchAnalyzer.run(fixture.configuration(), request);
        assertFalse(first.idempotent()); assertEquals(1, array(first.reportDocument(), "entries").size());
        assertTrue(array(first.reportDocument(), "unresolved").isEmpty()); assertEquals(1, first.grants().added());
        ObjectValue published = RetainedJson.object(array(first.reportDocument(), "entries").getFirst());
        Path factsPath = Path.of(text(o(published, "canonical_source_facts"), "path"));
        byte[] original = originalFacts(fixture.corpus(), fixture.row());
        ObjectValue originalFacts = RetainedJson.object(RetainedJson.parse(original));
        String oldPathToken = new String(RetainedJson.encode(v(originalFacts, "source_path")), StandardCharsets.UTF_8);
        Path actualSource = fixture.game().resolve(text(originalFacts, "source_relative"));
        String newPathToken = new String(RetainedJson.encode(s(actualSource.toString())), StandardCharsets.UTF_8);
        String originalText = new String(original, StandardCharsets.UTF_8);
        assertEquals(1, originalText.split(java.util.regex.Pattern.quote(oldPathToken), -1).length - 1);
        assertArrayEquals(originalText.replace(oldPathToken, newPathToken).getBytes(StandardCharsets.UTF_8), Files.readAllBytes(factsPath),
                "original Python immutable encoding survives the sole declared source-path projection");
        byte[] committed = Files.readAllBytes(Path.of(first.report().path()));
        OfflineEventBatchAnalyzer.Result replay = OfflineEventBatchAnalyzer.run(fixture.configuration(), request);
        assertTrue(replay.idempotent()); assertEquals(0, replay.grants().added());
        assertEquals(first.report(), replay.report()); assertArrayEquals(committed, Files.readAllBytes(Path.of(replay.report().path())));
        TrustedEventSourceContext trusted = TrustedEventSourceContext.open(fixture.configuration().sources());
        SourceReviewedEventConsumer.ReviewedPlan known = SourceReviewedEventConsumer.continueWithExistingPlan(fixture.plan(), o(fixture.row(), "snapshot"),
                SourceReviewedEventConsumerTest.steps(fixture.row()), trusted);
        assertEquals(b(true), v(o(known.plan(), "unhandled_event_fallback"), "registry_known"));
        OfflineEventBatchAnalyzer.Result repeatedKnown = OfflineEventBatchAnalyzer.run(fixture.configuration(), batch(fixture, "next", "b".repeat(32), known.plan()));
        assertTrue(array(repeatedKnown.reportDocument(), "entries").isEmpty());
        assertEquals(1, array(repeatedKnown.reportDocument(), "already_known").size()); assertTrue(array(repeatedKnown.reportDocument(), "unresolved").isEmpty());
        assertEquals(0, repeatedKnown.grants().added());
        assertDoesNotThrow(() -> OfflineEventBatchAnalyzer.encode(first));
        for (ExactRef output : first.outputs()) {
            byte[] raw = Files.readAllBytes(Path.of(output.path())); assertEquals(output.bytes(), raw.length); assertEquals(output.sha256(), sha(raw));
        }
    }

    @Test void changedCapturedPinRejectsBeforeAnyOutputAndActualGuiDriftCannotPublish() throws IOException {
        Fixture fixture = fixture("refusal"); OfflineEventBatchAnalyzer.Request request = batch(fixture, "refused", "c".repeat(32), fixture.plan());
        Path before = Path.of(request.capturedRefs().getFirst().path()); Files.writeString(before, "changed");
        byte[] manifestBefore = Files.readAllBytes(fixture.manifest());
        assertThrows(IllegalArgumentException.class, () -> OfflineEventBatchAnalyzer.run(fixture.configuration(), request));
        assertFalse(Files.exists(fixture.knowledge().resolve("refused"))); assertArrayEquals(manifestBefore, Files.readAllBytes(fixture.manifest()));
        Files.writeString(fixture.game().resolve("gui/event_windows/letter_event.gui"), "drift");
        assertThrows(TrustedEventSourceContext.UnavailableException.class, () -> OfflineEventBatchAnalyzer.run(fixture.configuration(), request));
        assertArrayEquals(manifestBefore, Files.readAllBytes(fixture.manifest()));
    }

    @Test void metadataContractRejectsCallerOutputPathAndBooleanByteCount() {
        ObjectValue ref = obj(f("path", s(temporary.resolve("manifest.json").toString())), f("bytes", b(true)), f("sha256", s("0".repeat(64))));
        ObjectValue request = obj(f("schema", s(OfflineEventBatchAnalyzer.REQUEST_SCHEMA)), f("batch_id", s("bad")), f("manifest_ref", ref), f("captured_refs", new ArrayValue(List.of())));
        assertThrows(IllegalArgumentException.class, () -> OfflineEventBatchAnalyzer.decode(RetainedJson.encode(request)));
        assertThrows(IllegalArgumentException.class, () -> OfflineEventBatchAnalyzer.decode(RetainedJson.encode(request.with("knowledge_root", s(temporary.toString())))));
    }

    @Test void firstDisplayedDisabledSurvivesActualPublicationSourceRebindAndNextBatch() throws IOException {
        Fixture fixture = fixture("first-displayed");
        OfflineEventBatchAnalyzer.Result first = OfflineEventBatchAnalyzer.run(fixture.configuration(),
                batch(fixture, "original", "d".repeat(32), fixture.plan()));
        assertEquals(1, array(first.reportDocument(), "entries").size());
        assertDoesNotThrow(() -> OfflineEventBatchAnalyzer.encode(first));

        UnhandledEventFallback.Request request = disabledFirstRequest(fixture);
        UnhandledEventFallback.Plan proposed = UnhandledEventFallback.planFirstDisplayed(request).orElseThrow();
        assertEquals(UnhandledEventFallback.Phase.FIRST_RENDERED_DISABLED, proposed.phase());
        assertNull(proposed.selectedStep()); assertFalse(proposed.actionAuthorized());
        ObjectValue plan = RetainedJson.object(RetainedJson.parse(UnhandledEventCodec.encode(Optional.of(proposed))));
        ObjectValue capture = o(plan, "unhandled_event_fallback"), selection = o(capture, "selection");
        assertEquals(s(UnhandledEventFallback.DisplayPolicy.FIRST_DISPLAYED.wire()), v(selection, "selection_order"));
        assertEquals(i(0), v(selection, "native_option_index")); assertEquals(b(false), v(selection, "enabled"));
        assertEquals(NULL, v(plan, "selected_step"));

        TrustedEventSourceContext trusted = TrustedEventSourceContext.open(fixture.configuration().sources());
        ObjectValue lookupInput = obj(f("schema", s("xar.events-source-reviewed-lookup-input/v1")), f("capture", capture));
        SourceReviewedEventConsumer.ReviewLookup lookup = SourceReviewedEventConsumer.lookup(RetainedJson.encode(lookupInput), trusted);
        assertTrue(lookup.entry().isPresent());
        assertEquals(s("reviewed_letter_source_rebound"), v(lookup.audit(), "binding_mode"));
        assertEquals(v(o(capture, "window_context"), "calculated_event_id"), v(o(lookup.audit(), "fresh_binding"), "calculated_event_id"));
        assertDoesNotThrow(lookup::encode);

        SourceReviewedEventConsumer.ReviewedPlan reviewed = SourceReviewedEventConsumer.annotate(RetainedJson.encode(plan), fixture.state());
        assertEquals(SourceReviewedEventConsumer.KnowledgeStatus.SOURCE_REVIEWED, reviewed.status());
        assertEquals(NULL, v(reviewed.plan(), "selected_step"));
        assertEquals(s("active_event_source_reviewed_first_rendered_disabled"), v(reviewed.plan(), "phase"));
        assertEquals(s("Source-reviewed event: the first displayed native option is disabled."), v(reviewed.plan(), "reason"));
        assertEquals(b(false), v(o(reviewed.plan(), "event_decision"), "material_effects_verified"));
        assertFalse(reviewed.actionAuthorized()); assertFalse(reviewed.replayAllowed());
        OfflineEventBatchAnalyzer.Result next = OfflineEventBatchAnalyzer.run(fixture.configuration(),
                batch(fixture, "next-disabled", "e".repeat(32), RetainedJson.object(RetainedJson.parse(reviewed.encode()))));
        assertTrue(array(next.reportDocument(), "entries").isEmpty());
        assertEquals(1, array(next.reportDocument(), "already_known").size());
        assertTrue(array(next.reportDocument(), "unresolved").isEmpty()); assertEquals(0, next.grants().added());
        assertDoesNotThrow(() -> OfflineEventBatchAnalyzer.encode(next));

        ObjectValue wrongSelection = put(selection, f("rendered_index", i(1)), f("native_option_index", i(2)),
                f("option_number", i(3)), f("enabled", b(true)), f("selected_step", s("select-event-option-3")));
        assertTrue(SourceReviewedEventConsumer.lookup(capture.with("selection", wrongSelection), trusted).entry().isEmpty(),
                "current first-displayed policy cannot rebind to the later enabled option");
        assertTrue(SourceReviewedEventConsumer.lookup(capture.with("selection", selection.with("rendered_index", b(false))), trusted).entry().isEmpty());
        ObjectValue legacyPlan = UnhandledEventCodec.legacyPlan(UnhandledEventFallback.plan(request).orElseThrow());
        assertEquals(i(2), v(o(o(legacyPlan, "unhandled_event_fallback"), "selection"), "native_option_index"));
        assertTrue(SourceReviewedEventConsumer.lookup(o(legacyPlan, "unhandled_event_fallback"), trusted).entry().isPresent(),
                "retained legacy selection-order contract stays distinct");

        Path source = Path.of(text(lookup.entry().orElseThrow(), "source_path"));
        byte[] original = Files.readAllBytes(source); Files.writeString(source, new String(original, StandardCharsets.UTF_8) + "\n# changed source\n");
        try {
            assertTrue(SourceReviewedEventConsumer.lookup(capture, trusted).entry().isEmpty(), "actual source SHA drift cannot remain source-known");
        } catch (TrustedEventSourceContext.UnavailableException unavailable) {
            // The trusted-root reader may reject the changed original source before registry lookup.
        }
    }

    private static UnhandledEventFallback.Request disabledFirstRequest(Fixture fixture) {
        ObjectValue original = o(fixture.plan(), "unhandled_event_fallback"), context = o(original, "window_context");
        Value instance = RetainedJson.value(number(context, "current_event_instance_id").add(java.math.BigInteger.ONE));
        List<Value> options = objects(context, "options").stream()
                .<Value>map(option -> eq(option, "rendered_index", i(0)) ? option.with("enabled", b(false)) : option).toList();
        context = put(context, f("calculated_event_id", RetainedJson.value(number(context, "calculated_event_id").add(java.math.BigInteger.ONE))),
                f("current_event_instance_id", instance), f("options", new ArrayValue(options)));
        ObjectValue snapshot = o(fixture.row(), "snapshot");
        snapshot = snapshot.with("active_event", o(snapshot, "active_event").with("instance_id", instance));
        ObjectValue wrapper = obj(f("schema", s(UnhandledEventCodec.PLAN_SCHEMA)), f("snapshot", snapshot), f("event_context", context),
                f("event_summary", o(fixture.plan(), "active_event").with("instance_id", instance)),
                f("registry_decision", v(original, "original_registry_decision")), f("action_steps", v(fixture.row(), "action_steps")));
        return UnhandledEventCodec.decodePlan(RetainedJson.encode(wrapper));
    }

    private Fixture fixture(String name) throws IOException {
        Path root = Files.createDirectories(temporary.resolve(name)); ObjectValue corpus = SourceReviewedEventConsumerTest.golden();
        ObjectValue row = objects(corpus, "cases").stream().filter(value -> eq(value, "name", s("faction_demand.0101-exact-stock"))).findFirst().orElseThrow();
        Path game = root.resolve("game");
        for (Map.Entry<String, String> source : ReviewedLetterSourceRebind.installedSourceHashes().entrySet()) {
            Path path = game.resolve(source.getKey()); Files.createDirectories(path.getParent()); byte[] raw = blob(corpus, source.getValue());
            assertEquals(source.getValue(), sha(raw)); Files.write(path, raw);
        }
        Path state = Files.createDirectories(root.resolve("state")), incidents = Files.createDirectories(root.resolve("incidents")), knowledge = Files.createDirectories(root.resolve("knowledge"));
        Path manifest = knowledge.resolve("fixed-grants.json"); EvidenceGrantManifestPublisher.publish(manifest, List.of());
        ProjectionEvidenceGrants fresh = () -> {
            try { return ProjectionEvidenceCodec.decode(Files.readAllBytes(manifest)); }
            catch (IOException unavailable) { throw new UncheckedIOException(unavailable); }
        };
        EventSourceReadContext sources = new EventSourceReadContext("portable-source-fixture", state, game, fresh);
        return new Fixture(corpus, row, o(row, "plan"), game, state, incidents, knowledge, manifest,
                new OfflineEventBatchAnalyzer.Configuration(sources, incidents, knowledge, manifest));
    }
    private static OfflineEventBatchAnalyzer.Request batch(Fixture fixture, String batchId, String incident, ObjectValue plan) throws IOException {
        ObjectValue binding = o(o(plan, "unhandled_event_fallback"), "binding");
        ObjectValue planned = obj(f("snapshot_id", v(binding, "snapshot_id")), f("revision", v(binding, "revision")), f("plan", plan));
        ObjectValue before = UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(planned), incident, "2026-10-22T00:00:00Z")).orElseThrow();
        Path beforePath = fixture.incidents().resolve(incident + ".before.json"); byte[] raw = RetainedJson.encode(before); Files.write(beforePath, raw);
        ExactRef beforeRef = new ExactRef(beforePath.toString(), raw.length, sha(raw));
        ObjectValue item = obj(f("incident_id", s(incident)), f("event_definition_key", v(before, "event_definition_key")), f("before", s(beforePath.toString())), f("before_sha256", s(beforeRef.sha256())));
        ObjectValue batch = obj(f("completed_control_sequence", i(1)), f("new_incidents", new ArrayValue(List.of(item))));
        Path path = fixture.incidents().resolve(batchId + ".json"); byte[] bytes = RetainedJson.encode(batch); Files.write(path, bytes);
        return new OfflineEventBatchAnalyzer.Request(batchId, new ExactRef(path.toString(), bytes.length, sha(bytes)), List.of(beforeRef));
    }
    private static byte[] originalFacts(ObjectValue corpus, ObjectValue row) throws IOException {
        ObjectValue facts = objects(row, "files").stream().filter(file -> eq(file, "kind", s("facts"))).findFirst().orElseThrow();
        return blob(corpus, text(facts, "sha256"));
    }
    private static byte[] blob(ObjectValue corpus, String sha) throws IOException {
        byte[] packed = Base64.getDecoder().decode(text(o(corpus, "blobs"), sha));
        try (GZIPInputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
            byte[] raw = input.readNBytes(2_097_153); if (raw.length > 2_097_152) throw new IOException("original source fixture exceeds its role"); return raw;
        }
    }
}
