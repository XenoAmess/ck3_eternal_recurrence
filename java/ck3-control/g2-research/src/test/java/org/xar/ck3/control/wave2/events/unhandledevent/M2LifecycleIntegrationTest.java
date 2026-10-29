package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.M2LifecycleFixtures.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m2.M2Payload;
import org.xar.ck3.control.g2.m2.M2Payload.Operation;
import org.xar.ck3.control.g2.m2.M2Research;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;

/** Actual retained producers through the public Java adapter and the sole existing offline writer. No Game qualification. */
final class M2LifecycleIntegrationTest {
    @TempDir Path temporary;

    @Test void originalEventProducerBeforeAfterOfflinePublicationAndNextEncounterConsumptionFormOneChain() throws IOException {
        Fixture fixture = fixture(temporary.resolve("event-lifecycle")); M2Research domain = new M2Research(fixture.sources());
        ObjectValue request = o(fixture.row(), "request");
        UnhandledEventFallback.Request typed = UnhandledEventCodec.decodePlan(RetainedJson.encode(request));
        assertEquals(typed, UnhandledEventCodec.decodePlan(UnhandledEventCodec.encodeRequest(typed)));
        ObjectValue original = exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE, request);
        assertEquals(v(fixture.row(), "plan"), original, "the complete original planner output survives the public adapter");
        exportHttpSamplesWhenRequested(fixture, request, original);
        M2Producer.EventProduction produced = M2Producer.event(ProjectionJson.object(RetainedJson.encode(request), M2Payload.MAX_BYTES),
                new UnhandledEventFallback.ExistingPlan("active_event_unhandled", null, null),
                new M2Producer.CaptureIdentity("a".repeat(32), TIME));
        assertEquals(original, RetainedJson.parse(produced.plan().bytes()));
        assertEquals(exchange(domain, fixture.originalRequest(), Operation.EVENT_BEFORE, beforeInput(original, "a".repeat(32))),
                RetainedJson.parse(produced.before().bytes()));
        assertFalse(produced.actionAuthorized()); assertFalse(produced.replayAllowed());
        ObjectValue reviewedInput = sourceReviewedInput(original, o(fixture.row(), "snapshot"), v(fixture.row(), "action_steps"));
        ObjectValue unknown = exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_SOURCE_REVIEWED, reviewedInput);
        assertEquals(b(false), v(o(unknown, "unhandled_event_fallback"), "registry_known"));
        assertEquals(b(true), v(o(unknown, "unhandled_event_fallback"), "offline_followup_required"));
        assertEquals(v(original, "selected_step"), v(unknown, "selected_step"));
        assertEquals(b(false), v(o(unknown, "event_decision"), "material_effects_verified"));
        assertFalse(Files.exists(fixture.state().resolve("evidence")), "evaluation cannot publish source knowledge");

        ObjectValue before = exchange(domain, fixture.originalRequest(), Operation.EVENT_BEFORE, beforeInput(unknown, "a".repeat(32)));
        assertEquals(b(false), v(before, "dispatch_attempted"));
        assertEquals(v(o(original, "unhandled_event_fallback"), "window_context"), v(before, "window_context"));
        ExactRef beforeRef = write(fixture.incidents().resolve("a".repeat(32) + ".before.json"), RetainedJson.encode(before));
        ObjectValue ticket = ticket(before, beforeRef);
        ObjectValue ackOnly = exchange(domain, fixture.originalRequest(), Operation.EVENT_AFTER, afterInput(ticket, acknowledgedOutcome(before, false)));
        assertEquals(b(true), v(ackOnly, "command_acknowledged"));
        assertEquals(b(false), v(ackOnly, "event_instance_advanced_verified"));
        assertEquals(b(false), v(ackOnly, "replay_allowed"));
        assertEquals(ackOnly, RetainedJson.parse(M2Producer.eventAfter(ProjectionJson.object(
                RetainedJson.encode(afterInput(ticket, acknowledgedOutcome(before, false))), M2Payload.MAX_BYTES)).bytes()));
        assertTrue(UnhandledEventFallback.proposeForUnhandledPhase(new UnhandledEventFallback.ExistingPlan(
                text(unknown, "phase"), null, o(unknown, "unhandled_event_fallback")), typed).isEmpty(),
                "retained unresolved incident cannot create a second fallback proposal");
        M2Producer.EventProduction noReplay = M2Producer.event(ProjectionJson.object(RetainedJson.encode(request), M2Payload.MAX_BYTES),
                new UnhandledEventFallback.ExistingPlan(text(unknown, "phase"), null, o(unknown, "unhandled_event_fallback")),
                new M2Producer.CaptureIdentity("a".repeat(32), TIME));
        assertTrue(noReplay.proposal().isEmpty()); assertEquals(NULL, RetainedJson.parse(noReplay.before().bytes()));
        assertFalse(noReplay.replayAllowed());

        ObjectValue after = exchange(domain, fixture.originalRequest(), Operation.EVENT_AFTER, afterInput(ticket, acknowledgedOutcome(before, true)));
        assertEquals(b(true), v(after, "command_acknowledged"));
        assertEquals(b(true), v(after, "event_instance_advanced_verified"));
        assertEquals(b(false), v(after, "replay_allowed"));
        assertEquals(reference(beforeRef), v(after, "before"));
        OfflineEventBatchAnalyzer.Request batch = batch(fixture, "first", before, after);
        assertEquals(batch, OfflineEventBatchAnalyzer.decode(RetainedJson.encode(batchInput(batch))));
        OfflineEventBatchAnalyzer.Result result = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(), batch);
        assertFalse(result.idempotent()); assertEquals(1, array(result.reportDocument(), "entries").size());
        assertTrue(array(result.reportDocument(), "unresolved").isEmpty()); assertEquals(1, result.grants().added());
        assertDoesNotThrow(() -> OfflineEventBatchAnalyzer.encode(result));
        for (ExactRef output : result.outputs()) {
            byte[] actual = Files.readAllBytes(Path.of(output.path())); assertEquals(output.bytes(), actual.length); assertEquals(output.sha256(), sha(actual));
        }
        ObjectValue next = exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_SOURCE_REVIEWED, reviewedInput);
        ObjectValue capture = o(next, "unhandled_event_fallback");
        assertEquals(b(true), v(capture, "registry_known")); assertEquals(b(false), v(capture, "offline_followup_required"));
        assertEquals(s("offline-source-reviewed"), v(o(capture, "source_knowledge"), "status"));
        assertEquals(v(unknown, "selected_step"), v(next, "selected_step"));
        assertEquals(b(false), v(o(next, "event_decision"), "material_effects_verified"));
        assertEquals(b(false), v(o(next, "event_decision"), "registry_contract_accepted"));

        ObjectValue nextBefore = exchange(domain, fixture.originalRequest(), Operation.EVENT_BEFORE, beforeInput(next, "b".repeat(32)));
        ExactRef nextBeforeRef = write(fixture.incidents().resolve("b".repeat(32) + ".before.json"), RetainedJson.encode(nextBefore));
        ObjectValue nextAfter = exchange(domain, fixture.originalRequest(), Operation.EVENT_AFTER,
                afterInput(ticket(nextBefore, nextBeforeRef), acknowledgedOutcome(nextBefore, true)));
        OfflineEventBatchAnalyzer.Result nextBatch = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(), batch(fixture, "next", nextBefore, nextAfter));
        assertTrue(array(nextBatch.reportDocument(), "entries").isEmpty());
        assertEquals(1, array(nextBatch.reportDocument(), "already_known").size());
        assertTrue(array(nextBatch.reportDocument(), "unresolved").isEmpty()); assertEquals(0, nextBatch.grants().added());
        byte[] committed = Files.readAllBytes(Path.of(result.report().path()));
        OfflineEventBatchAnalyzer.Result replay = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(), batch);
        assertTrue(replay.idempotent()); assertEquals(result.report(), replay.report()); assertEquals(0, replay.grants().added());
        assertArrayEquals(committed, Files.readAllBytes(Path.of(replay.report().path())));
    }

    @Test void allOriginalPlanProducersKeepDisplayedOrderLegalityAndIndependentPublicNativeFrames() throws IOException {
        Fixture fixture = fixture(temporary.resolve("plan-producers"));
        ObjectValue corpus = resource("/unhandledevent/unhandled-event-golden-v1.json.gz", true);
        List<ObjectValue> rows = objects(corpus, "plan_cases"); assertEquals(21, rows.size());
        int independentFrames = 0;
        for (ObjectValue row : rows) {
            ObjectValue request = o(row, "request"); assertNotNull(request);
            ObjectValue actual = nullableExchange(new M2Research(), fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE, request);
            assertEquals(v(row, "expected_plan"), actual == null ? NULL : actual, text(row, "name"));
            UnhandledEventFallback.Request typed = UnhandledEventCodec.decodePlan(RetainedJson.encode(request));
            assertEquals(typed, UnhandledEventCodec.decodePlan(UnhandledEventCodec.encodeRequest(typed)));
            if (typed.snapshot() != null && typed.snapshot().binding().revision() != null
                    && !typed.snapshot().binding().revision().equals(typed.snapshot().binding().nativeRevision())) independentFrames++;
        }
        assertTrue(independentFrames > 0, "public revision must not be conflated with the native observation revision");
    }

    @Test void actualSourceReviewedPoliciesStillOverrideGenericFirstOptionAndRemainReadOnly() throws IOException {
        ObjectValue corpus = golden(); Set<String> phases = new HashSet<>(); int pipelines = 0;
        for (ObjectValue row : objects(corpus, "cases")) if (eq(row, "mode", s("pipeline"))) {
            Path root = temporary.resolve("policy-" + text(row, "name")); Relocated relocated = relocate(corpus, row, root);
            installStock(corpus, root.resolve("game")); Files.createDirectories(relocated.state());
            ExactRef source = write(root.resolve("request-source.json"), RetainedJson.encode(o(row, "request")));
            M2Research domain = new M2Research(new EventSourceReadContext(MACHINE, relocated.state(), root.resolve("game")));
            ObjectValue result = exchange(domain, source, Operation.EVENT_PLAN_SOURCE_REVIEWED,
                    sourceReviewedInput(relocated.plan(), o(row, "snapshot"), v(row, "action_steps")));
            assertEquals(relocated.expected(), result, text(row, "name")); phases.add(text(result, "phase")); pipelines++;
            for (Map.Entry<Path, byte[]> file : relocated.initialFiles().entrySet()) assertArrayEquals(file.getValue(), Files.readAllBytes(file.getKey()));
        }
        assertEquals(9, pipelines);
        int policies = 0;
        for (ObjectValue row : objects(corpus, "cases")) if (eq(row, "mode", s("policy"))) {
            Path root = temporary.resolve("policy-" + text(row, "name")); Relocated relocated = relocate(corpus, row, root);
            ObjectValue snapshot = o(row, "snapshot"), originalExpected = RetainedJson.object(relocated.expected());
            List<String> steps = array(row, "action_steps").stream().map(RetainedJson::string).toList();
            // These original vectors deliberately skip annotation (state_directory=null).
            // Keep their complete original policy result exact before exercising the public, configured route.
            assertEquals(originalExpected, ExistingFactionEventPolicies.choose(relocated.plan(), snapshot, steps), text(row, "name"));
            // A caller's synthetic rejected-entry audit is also replaced by current server evidence.
            // Its public decision therefore matches the original no-rejected-entry vector; the
            // original direct-policy negative result above remains mandatory and unchanged.
            boolean claimedRejection = text(row, "name").endsWith("-rejected-exact");
            ObjectValue expected = claimedRejection
                    ? o(named(corpus, text(row, "name").replace("-rejected-exact", "-none")), "expected") : originalExpected;
            installStock(corpus, root.resolve("game")); Files.createDirectories(relocated.state());
            ObjectValue input = sourceReviewedInput(relocated.plan(), snapshot, v(row, "action_steps"));
            ExactRef source = write(root.resolve("request-source.json"), RetainedJson.encode(input));
            M2Research domain = new M2Research(new EventSourceReadContext(MACHINE, relocated.state(), root.resolve("game")));
            ObjectValue result = exchange(domain, source, Operation.EVENT_PLAN_SOURCE_REVIEWED, input);
            // Server-owned nonempty state adds source audit fields. Compare the unchanged original
            // decision and native binding, without treating caller-supplied knowledge flags as grants.
            for (String field : List.of("phase", "selected_step", "reason"))
                assertEquals(v(expected, field), v(result, field), text(row, "name") + ":" + field);
            for (String field : List.of("instance_id", "option_count", "selected_option_number",
                    "selected_native_option_index", "selected_rendered_index", "semantic_optimal"))
                assertEquals(v(o(expected, "active_event"), field), v(o(result, "active_event"), field));
            ObjectValue capture = o(result, "unhandled_event_fallback"), expectedCapture = o(expected, "unhandled_event_fallback");
            for (String field : List.of("binding", "window_context", "selection", "policy",
                    "event_definition_key", "current_event_instance_id", "offline_followup_required",
                    "semantic_optimal", "native_ai_equivalent"))
                assertEquals(v(expectedCapture, field), v(capture, field), text(row, "name") + ":" + field);
            assertEquals(v(expected, "faction_demand_source_outcome"), v(result, "faction_demand_source_outcome"));
            assertEquals(b(false), v(o(result, "event_decision"), "material_effects_verified"));
            assertEquals(b(false), v(o(result, "event_decision"), "registry_contract_accepted"));
            if (eq(expected, "phase", s("active_event_source_reviewed_independence_refusal"))) {
                for (Map.Entry<String, Value> field : o(expected, "event_decision").fields().entrySet())
                    assertEquals(field.getValue(), v(o(result, "event_decision"), field.getKey()));
                ObjectValue audit = o(capture, "source_knowledge");
                if (claimedRejection) {
                    assertFalse(array(o(o(relocated.plan(), "unhandled_event_fallback"), "source_knowledge"), "rejected_entries").isEmpty());
                    ObjectValue prior = o(audit, "prior_source_knowledge");
                    assertEquals(s("unknown"), v(prior, "status"));
                    assertTrue(array(prior, "rejected_entries").isEmpty(), "caller audit cannot replace current source verification");
                }
                assertEquals(b(false), v(audit, "live_qualification"));
                assertEquals(b(false), v(audit, "material_effects_verified"));
                assertEquals(b(false), v(audit, "registry_contract_accepted"));
            } else {
                assertEquals(b(false), v(capture, "registry_known"), "raw claimed knowledge cannot grant server source qualification");
            }
            assertFalse(Files.exists(relocated.state().resolve("evidence")), "public evaluation remains read-only");
            for (Map.Entry<Path, byte[]> file : relocated.initialFiles().entrySet())
                assertArrayEquals(file.getValue(), Files.readAllBytes(file.getKey()));
            phases.add(text(result, "phase")); policies++;
        }
        assertEquals(14, policies);
        assertTrue(phases.contains("active_event_source_reviewed_independence_refusal"));
        assertTrue(phases.contains("active_event_source_reviewed_populist_refusal"));
    }

    @Test void wrongFieldsMissingFieldsAndWrongScalarTypesFailAtTheActualPublicBoundary() throws IOException {
        Fixture fixture = fixture(temporary.resolve("invalid-inputs")); M2Research domain = new M2Research(fixture.sources());
        ObjectValue request = o(fixture.row(), "request");
        assertThrows(IllegalArgumentException.class, () -> exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE,
                request.with("state_directory", s(fixture.state().toString()))));
        assertThrows(IllegalArgumentException.class, () -> exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE,
                request.with("schema", s("unsupported"))));
        ObjectValue missing = new ObjectValue(request.fields().entrySet().stream().filter(field -> !field.getKey().equals("registry_decision"))
                .collect(java.util.stream.Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)));
        assertThrows(IllegalArgumentException.class, () -> exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE, missing));
        ObjectValue snapshot = o(request, "snapshot"); assertNotNull(snapshot);
        for (Value invalid : List.<Value>of(b(true), new FloatingValue(3.0), s("3"))) {
            assertThrows(IllegalArgumentException.class, () -> exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE,
                    request.with("snapshot", snapshot.with("revision", invalid))));
        }
        ObjectValue ref = reference(fixture.originalRequest()).with("bytes", b(true));
        ObjectValue invalidBatch = obj(f("schema", s(OfflineEventBatchAnalyzer.REQUEST_SCHEMA)), f("batch_id", s("invalid")),
                f("manifest_ref", ref), f("captured_refs", new ArrayValue(List.of())));
        assertThrows(IllegalArgumentException.class, () -> OfflineEventBatchAnalyzer.decode(RetainedJson.encode(invalidBatch)));
        assertFalse(Files.exists(fixture.state().resolve("evidence")));
    }

    @Test void serverSourceContextCannotBeGrantedByThePayloadOrAClaimedKnownFlag() throws IOException {
        Fixture fixture = fixture(temporary.resolve("caller-claims")); ObjectValue plan = o(fixture.row(), "plan");
        ObjectValue capture = o(plan, "unhandled_event_fallback");
        ObjectValue forged = plan.with("unhandled_event_fallback", put(capture, f("registry_known", b(true)),
                f("offline_followup_required", b(false)), f("source_knowledge", obj(f("status", s("offline-source-reviewed"))))));
        ObjectValue request = sourceReviewedInput(forged, o(fixture.row(), "snapshot"), v(fixture.row(), "action_steps"));
        assertEquals(G2HttpError.Code.ENGINE_UNAVAILABLE, assertThrows(G2Exception.class,
                () -> exchange(new M2Research(), fixture.originalRequest(), Operation.EVENT_PLAN_SOURCE_REVIEWED, request)).code());
        ObjectValue actual = exchange(new M2Research(fixture.sources()), fixture.originalRequest(), Operation.EVENT_PLAN_SOURCE_REVIEWED, request);
        assertEquals(b(false), v(o(actual, "unhandled_event_fallback"), "registry_known"));
        assertEquals(b(true), v(o(actual, "unhandled_event_fallback"), "offline_followup_required"));
        G2Source wrongMachine = new G2Source("other-machine", TIME, "1.20.0.4", fixture.originalRequest());
        G2Request wrong = new G2Request("m2-wrong-machine", Milestone.M2, wrongMachine,
                M2Payload.input(Operation.EVENT_PLAN_SOURCE_REVIEWED, ProjectionJson.object(RetainedJson.encode(request), M2Payload.MAX_BYTES)));
        assertEquals(G2HttpError.Code.SOURCE_MISMATCH,
                assertThrows(G2Exception.class, () -> new M2Research(fixture.sources()).evaluate(wrong)).code());
    }

    @Test void originalInteractionAndEventIncidentsShareTheExistingBatchWriterAndBothBecomeKnown() throws IOException {
        Fixture fixture = fixture(temporary.resolve("mixed-lifecycle"));
        ObjectValue interactionCorpus = resource("/interactionbefore/interaction-source-host-golden-v1.json.gz", true);
        installInteractionStock(interactionCorpus, fixture.game()); M2Research domain = new M2Research(fixture.sources());
        ObjectValue originalPlan = exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_CANDIDATE, o(fixture.row(), "request"));
        ObjectValue eventPlan = exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_SOURCE_REVIEWED,
                sourceReviewedInput(originalPlan, o(fixture.row(), "snapshot"), v(fixture.row(), "action_steps")));
        ObjectValue eventBefore = exchange(domain, fixture.originalRequest(), Operation.EVENT_BEFORE, beforeInput(eventPlan, "d".repeat(32)));
        ExactRef eventBeforeRef = write(fixture.incidents().resolve("d".repeat(32) + ".before.json"), RetainedJson.encode(eventBefore));
        ObjectValue eventAfter = exchange(domain, fixture.originalRequest(), Operation.EVENT_AFTER,
                afterInput(ticket(eventBefore, eventBeforeRef), acknowledgedOutcome(eventBefore, true)));
        OfflineEventBatchAnalyzer.Request eventSeed = batch(fixture, "event-seed", eventBefore, eventAfter);

        InteractionRound interaction = interactionRound(fixture, interactionCorpus, domain, "c".repeat(32));
        assertInstanceOf(InteractionRegistry.Unknown.class,
                OfflineInteractionSourceAnalyzer.reviewed(interaction.before(), TrustedEventSourceContext.openEvidence(fixture.sources())));
        OfflineEventBatchAnalyzer.Request mixed = withInteraction(fixture, "mixed", eventSeed, interaction.before(), interaction.after());
        OfflineEventBatchAnalyzer.Result published = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(),
                OfflineEventBatchAnalyzer.decode(RetainedJson.encode(batchInput(mixed))));
        assertEquals(2, array(published.reportDocument(), "entries").size());
        assertTrue(array(published.reportDocument(), "unresolved").isEmpty()); assertEquals(2, published.grants().added());
        assertDoesNotThrow(() -> OfflineEventBatchAnalyzer.encode(published));
        assertInstanceOf(InteractionRegistry.Known.class,
                OfflineInteractionSourceAnalyzer.reviewed(interaction.before(), TrustedEventSourceContext.openEvidence(fixture.sources())));

        ObjectValue nativeContext = o(interaction.before(), "context"), definition = o(nativeContext, "definition");
        ObjectValue lookup = obj(f("schema", s("xar.interaction-registry-lookup/v1")), f("build", v(nativeContext, "build")),
                f("definition", obj(f("canonical_key", v(definition, "canonical_key")), f("deterministic_key_hash", v(definition, "deterministic_key_hash")))),
                f("gui_sha256", s(InteractionFallback.GUI_SHA256)));
        ObjectValue lookedUp = exchange(domain, fixture.originalRequest(), Operation.INTERACTION_REGISTRY_LOOKUP, lookup);
        assertEquals(s("offline-source-reviewed"), v(o(lookedUp, "audit"), "status"));
        assertNotNull(o(lookedUp, "reviewed"));
        ObjectValue reopened = exchange(new M2Research(fixture.sources()), fixture.originalRequest(), Operation.INTERACTION_REGISTRY_LOOKUP, lookup);
        assertEquals(v(lookedUp, "reviewed"), v(reopened, "reviewed"), "a fresh adapter reopens the published source knowledge");
        ObjectValue nextInteractionPlan = exchange(domain, fixture.originalRequest(), Operation.INTERACTION_PLAN,
                o(named(interactionCorpus, "known"), "request"));
        ObjectValue nextCapture = o(nextInteractionPlan, "unhandled_interaction_fallback");
        assertEquals(b(true), v(nextCapture, "registry_known")); assertEquals(b(false), v(nextCapture, "offline_followup_required"));
        assertEquals(v(interaction.plan(), "selected_step"), v(nextInteractionPlan, "selected_step"));
        assertEquals(b(false), v(nextCapture, "semantic_optimal"));
        ObjectValue nextEventPlan = exchange(domain, fixture.originalRequest(), Operation.EVENT_PLAN_SOURCE_REVIEWED,
                sourceReviewedInput(originalPlan, o(fixture.row(), "snapshot"), v(fixture.row(), "action_steps")));
        assertEquals(b(true), v(o(nextEventPlan, "unhandled_event_fallback"), "registry_known"));
        byte[] report = Files.readAllBytes(Path.of(published.report().path()));
        OfflineEventBatchAnalyzer.Result repeated = OfflineEventBatchAnalyzer.run(fixture.batchConfiguration(), mixed);
        assertTrue(repeated.idempotent()); assertEquals(0, repeated.grants().added());
        assertArrayEquals(report, Files.readAllBytes(Path.of(repeated.report().path())));
        Files.writeString(fixture.game().resolve(InteractionFallback.GUI_SOURCE), "\nchanged fixture GUI", java.nio.file.StandardOpenOption.APPEND);
        assertEquals(G2HttpError.Code.ENGINE_UNAVAILABLE, assertThrows(G2Exception.class,
                () -> exchange(new M2Research(fixture.sources()), fixture.originalRequest(), Operation.INTERACTION_REGISTRY_LOOKUP, lookup)).code(),
                "published knowledge cannot replace current source/GUI verification");
    }

    @Test void originalInvalidBuildInteractionIsNotPromotedUsingAnotherHistoricalBuildReceipt() throws IOException {
        Fixture fixture = fixture(temporary.resolve("invalid-interaction-build"));
        ObjectValue corpus = resource("/interactionbefore/interaction-source-host-golden-v1.json.gz", true);
        installInteractionStock(corpus, fixture.game()); ObjectValue before = o(named(corpus, "unknown"), "before"); assertNotNull(before);
        assertThrows(IllegalArgumentException.class,
                () -> OfflineInteractionSourceAnalyzer.analyze(before, TrustedEventSourceContext.openEvidence(fixture.sources())));
        assertFalse(Files.exists(fixture.state().resolve("evidence")));
    }

    private record InteractionRound(ObjectValue plan, ObjectValue before, ObjectValue after) { }
    private static InteractionRound interactionRound(Fixture fixture, ObjectValue corpus, M2Research domain, String incident) throws IOException {
        ObjectValue row = named(corpus, "known"), request = o(row, "request");
        M2Producer.InteractionProduction producer = M2Producer.interaction(
                ProjectionJson.object(RetainedJson.encode(request), M2Payload.MAX_BYTES), TrustedEventSourceContext.openEvidence(fixture.sources()),
                new M2Producer.CaptureIdentity(incident, TIME));
        ObjectValue plan = exchange(domain, fixture.originalRequest(), Operation.INTERACTION_PLAN, request);
        assertEquals(v(row, "expected_plan"), plan); assertEquals(plan, RetainedJson.parse(producer.plan().bytes()));
        assertFalse(producer.actionAuthorized()); assertFalse(producer.replayAllowed());
        ObjectValue snapshot = o(request, "snapshot"); byte[] planned = RetainedJson.encode(obj(
                f("snapshot_id", v(snapshot, "snapshot_id")), f("revision", v(snapshot, "revision")), f("plan", plan)));
        ObjectValue beforeInput = obj(f("schema", s(InteractionHostJson.BEFORE_SCHEMA)),
                f("original_planned_base64", s(Base64.getEncoder().encodeToString(planned))), f("original_sha256", s(sha(planned))),
                f("incident_id", s(incident)), f("captured_at_utc", s(TIME)));
        ObjectValue before = exchange(domain, fixture.originalRequest(), Operation.INTERACTION_BEFORE, beforeInput);
        assertEquals(before, RetainedJson.parse(producer.before().bytes())); assertEquals(b(false), v(before, "dispatch_attempted"));
        ExactRef beforeRef = write(fixture.incidents().resolve(incident + ".before.json"), RetainedJson.encode(before));
        ObjectValue receipt = named(resource("/interactionreceipt/legacy-producer-golden-v1.json", false), "service_reject");
        byte[] raw = text(receipt, "response_utf8").getBytes(StandardCharsets.UTF_8); assertEquals(text(receipt, "response_sha256"), sha(raw));
        assertEquals(v(before, "pending_interaction_id"), v(receipt, "pending_interaction_id"));
        ObjectValue ticket = obj(f("incident_id", s(incident)), f("pending_interaction_id", v(before, "pending_interaction_id")),
                f("action", s("reject")), f("before", reference(beforeRef)));
        ObjectValue afterInput = obj(f("schema", s(InteractionHostJson.AFTER_SCHEMA)),
                f("original_response_base64", s(Base64.getEncoder().encodeToString(raw))), f("original_sha256", s(sha(raw))),
                f("ticket", ticket), f("origin", v(receipt, "origin")), f("error", NULL), f("captured_at_utc", s(TIME)));
        ObjectValue after = exchange(domain, fixture.originalRequest(), Operation.INTERACTION_AFTER, afterInput);
        assertEquals(after, RetainedJson.parse(M2Producer.interactionAfter(
                ProjectionJson.object(RetainedJson.encode(afterInput), M2Payload.MAX_BYTES)).bytes()));
        // These are independent original response fixtures. Equal pending IDs cannot grant incident completion.
        assertEquals(b(false), v(after, "command_acknowledged")); assertEquals(b(false), v(after, "original_pending_advanced_verified"));
        assertEquals(b(false), v(after, "durable_completion_granted")); assertEquals(b(false), v(after, "material_effects_verified"));
        assertEquals(b(false), v(after, "replay_allowed"));
        return new InteractionRound(plan, before, after);
    }

    private static ObjectValue exchange(M2Research domain, ExactRef sourceRef, Operation operation, ObjectValue input) {
        ObjectValue result = nullableExchange(domain, sourceRef, operation, input); assertNotNull(result); return result;
    }
    private static ObjectValue nullableExchange(M2Research domain, ExactRef sourceRef, Operation operation, ObjectValue input) {
        G2Source source = new G2Source(MACHINE, TIME, "1.20.0.4", sourceRef);
        ProjectionJson payload = M2Payload.input(operation, ProjectionJson.object(RetainedJson.encode(input), M2Payload.MAX_BYTES));
        G2Request request = new G2Request("m2-" + operation.wire(), Milestone.M2, source, payload);
        G2Request transported = G2Wire.decodeRequest(G2Wire.encodeRequest(request));
        assertEquals(request.requestId(), transported.requestId()); assertEquals(request.milestone(), transported.milestone());
        assertEquals(request.source(), transported.source()); assertArrayEquals(request.payload().bytes(), transported.payload().bytes());
        G2Response response = domain.evaluate(transported);
        G2Response reloaded = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(request.requestId(), reloaded.requestId()); assertEquals(Milestone.M2, reloaded.milestone());
        assertEquals(source, reloaded.source()); assertArrayEquals(response.result().bytes(), reloaded.result().bytes());
        M2Payload.Result result = M2Payload.decodeResult(reloaded.result()); assertEquals(operation, result.operation());
        Value parsed = RetainedJson.parse(result.result().bytes()); return parsed instanceof NullValue ? null : RetainedJson.object(parsed);
    }

    /** Optional small delivery artifacts; the complete test still runs when export is not requested. */
    private static void exportHttpSamplesWhenRequested(Fixture fixture, ObjectValue originalRequest, ObjectValue expectedPlan) throws IOException {
        String requested = System.getProperty("g2.m2.httpOutput"); if (requested == null) return;
        Path output = Path.of(requested); assertTrue(output.isAbsolute(), "HTTP fixture output must be explicitly absolute");
        byte[] original = Files.readAllBytes(Path.of(fixture.originalRequest().path()));
        ExactRef retained = write(output.resolve("M2.original-input.json"), original);
        G2Source source = new G2Source(MACHINE, TIME, "1.20.0.4", retained);
        G2Request request = new G2Request("m2-http-original-plan", Milestone.M2, source,
                M2Payload.input(Operation.EVENT_PLAN_CANDIDATE, ProjectionJson.object(original, M2Payload.MAX_BYTES)));
        G2Response response = new M2Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        assertEquals(expectedPlan, RetainedJson.parse(M2Payload.unwrapResult(response.result()).bytes()));
        write(output.resolve("M2.request.json"), G2Wire.encodeRequest(request));
        write(output.resolve("M2.expected-result.json"), response.result().bytes());
        write(output.resolve("M2.response.json"), G2Wire.encodeResponse(response));
        G2Request rejected = new G2Request("m2-http-invalid-plan-schema", Milestone.M2, source,
                M2Payload.input(Operation.EVENT_PLAN_CANDIDATE, ProjectionJson.object(
                        RetainedJson.encode(originalRequest.with("schema", s("unsupported"))), M2Payload.MAX_BYTES)));
        assertThrows(IllegalArgumentException.class, () -> new M2Research().evaluate(rejected));
        write(output.resolve("M2.reject.request.json"), G2Wire.encodeRequest(rejected));
    }
}
