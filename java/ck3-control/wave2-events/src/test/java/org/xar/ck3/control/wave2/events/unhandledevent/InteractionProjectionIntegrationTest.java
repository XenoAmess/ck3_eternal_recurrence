package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.ServiceLoader;
import java.util.Set;
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
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.wave2.events.projection.InteractionProjectionPortCatalog;

/** Original producers and stock bytes on synthetic native frames; no current-machine or native qualification. */
final class InteractionProjectionIntegrationTest {
    private static final String MACHINE = "portable-interaction-source-fixture";
    private static final String RESOURCE = "/interactionbefore/interaction-source-host-golden-v1.json.gz";
    private static final Set<String> NAMES = Set.of("known", "unknown", "disabled", "unsupported", "acknowledge", "missing-definition",
            "false-notification", "stale-native", "wrong-pending", "signed-pending", "null-context", "null-snapshot");
    @TempDir Path temporary;

    @TestFactory Stream<DynamicTest> originalCompletePlannerAndBeforeBodiesCrossTheRegisteredHostBoundary() throws IOException {
        ObjectValue golden = golden(); List<ObjectValue> cases = objects(golden, "cases");
        assertEquals(12, cases.size()); assertEquals(NAMES, new HashSet<>(cases.stream().map(row -> text(row, "name")).toList()));
        return cases.stream().map(row -> DynamicTest.dynamicTest(text(row, "name"), () -> {
            Path root = temporary.resolve(text(row, "name")); ProjectionDispatcher dispatcher = configured(golden, root);
            byte[] output = success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN, o(row, "request")));
            Value actualPlan = RetainedJson.parse(output);
            byte[] original = text(row, "planned_utf8").getBytes(StandardCharsets.UTF_8); assertEquals(text(row, "planned_sha256"), sha(original));
            // Preserve every original producer field; current captures additionally bind the native GUI presentation.
            assertEquals(v(row, "expected_plan"), v(RetainedJson.object(RetainedJson.parse(original)), "plan"));
            ObjectValue currentRequest = o(row, "request"); Value currentExpected = v(row, "expected_plan");
            if ("acknowledge".equals(text(row, "name"))) {
                // This historical row changed only the snapshot notification bit; its native route still says false.
                assertEquals(b(true), v(o(o(currentRequest, "snapshot"), "pending_character_interaction"), "auto_accept_notification"));
                ObjectValue originalContext = o(currentRequest, "context");
                assertEquals(b(false), v(o(originalContext, "routing"), "auto_accept_notification"));
                assertEquals(NULL, actualPlan, "contradictory native notification routing must not become a current action");
                ObjectValue consistentContext = originalContext.with("routing", o(originalContext, "routing").with("auto_accept_notification", b(true)));
                currentRequest = currentRequest.with("context", consistentContext);
                ObjectValue retainedPlan = RetainedJson.object(currentExpected);
                currentExpected = retainedPlan.with("unhandled_interaction_fallback",
                        o(retainedPlan, "unhandled_interaction_fallback").with("context", consistentContext));
                actualPlan = RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN, currentRequest)));
            }
            if ("missing-definition".equals(text(row, "name"))) {
                // Native AVAILABLE packets require canonical identity; this old synthetic row has none.
                assertFalse(o(currentRequest, "context").fields().containsKey("definition"));
                assertEquals(NULL, actualPlan, "missing native canonical identity cannot qualify a current action");
                assertEquals(NULL, RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN,
                        currentRequest.with("context", o(currentRequest, "context").with("definition", NULL))))));
                ObjectValue unknown = named(golden, "unknown"), unknownRequest = o(unknown, "request");
                ObjectValue canonicalContext = o(unknownRequest, "context").with("build", v(o(o(named(golden, "known"), "request"), "context"), "build"));
                currentRequest = unknownRequest.with("context", canonicalContext).with("registry_requested", b(true));
                ObjectValue retainedPlan = o(unknown, "expected_plan"), capture = o(retainedPlan, "unhandled_interaction_fallback");
                ObjectValue unknownAudit = obj(f("status", s("unknown")), f("reason", s("no_match")), f("rejected_entries", new ArrayValue(List.of())));
                currentExpected = retainedPlan.with("unhandled_interaction_fallback", capture.with("context", canonicalContext).with("offline_registry_audit", unknownAudit));
                actualPlan = RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN, currentRequest)));
            }
            assertEquals(withExpectedCurrentPresentation(currentExpected, currentRequest), actualPlan);
            ObjectValue oldBefore = o(row, "before");
            String incident = oldBefore == null ? "0123456789abcdef0123456789abcdef" : text(oldBefore, "incident_id");
            String time = oldBefore == null ? "2026-10-22T00:00:00Z" : text(oldBefore, "captured_at_utc");
            byte[] before = success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_BEFORE, obj(
                    f("schema", s(InteractionHostJson.BEFORE_SCHEMA)), f("original_planned_base64", encoded(original)),
                    f("original_sha256", s(sha(original))), f("incident_id", s(incident)), f("captured_at_utc", s(time)))));
            assertEquals(oldBefore == null ? NULL : oldBefore.with("machine_id", s(MACHINE)), RetainedJson.parse(before));
            if (oldBefore != null) assertFalse(yes(RetainedJson.object(RetainedJson.parse(before)), "dispatch_attempted"));
            if (actualPlan instanceof ObjectValue currentPlan)
                assertCurrentBeforeConsumer(dispatcher, RetainedJson.object(RetainedJson.parse(original)), currentPlan, incident, time);
            assertFalse(Files.exists(root.resolve("state/evidence")), "read-only projections cannot publish or dispatch");
        }));
    }

    @Test void allOriginalServiceDriverAndMcpReplySamplesKeepAckSeparateFromResponseClaims() throws IOException {
        ObjectValue corpus = resource("/interactionreceipt/legacy-producer-golden-v1.json", false);
        List<ObjectValue> cases = objects(corpus, "cases"); assertEquals(23, cases.size());
        assertTrue(array(corpus, "actual_method_calls").size() >= 6);
        ProjectionDispatcher dispatcher = new ProjectionDispatcher(catalog().registrations());
        for (ObjectValue row : cases) {
            byte[] raw = text(row, "response_utf8").getBytes(StandardCharsets.UTF_8); assertEquals(text(row, "response_sha256"), sha(raw));
            ObjectValue request = obj(
                    f("schema", s(InteractionHostJson.RECEIPT_SCHEMA)), f("original_response_base64", encoded(raw)), f("original_sha256", s(sha(raw))),
                    f("expected", obj(f("pending_interaction_id", v(row, "pending_interaction_id")), f("action", v(row, "action")))),
                    f("origin", v(row, "origin")), f("error", v(row, "error")));
            ObjectValue result = RetainedJson.object(RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_RECEIPT, request))));
            assertEquals(v(row, "legacy_original_pending_advanced_verified"), v(result, "legacy_capture_would_mark_advanced"), text(row, "name"));
            assertEquals(b(false), v(result, "material_effects_verified")); assertEquals(b(false), v(result, "replay_allowed"));
            if (eq(row, "name", s("service_reject"))) {
                assertEquals(s("not_reported_as_ack"), v(result, "command_acknowledged"));
                assertEquals(b(true), v(result, "original_pending_advanced_in_response"));
                assertEquals(b(false), v(result, "legacy_capture_would_mark_advanced"));
            }
        }
    }

    @Test void sharedIdAcrossIndependentFixturesDoesNotProveIncidentCompletionOrAuthorizeDispatch() throws IOException {
        ObjectValue golden = golden(), row = named(golden, "known"); Path root = temporary.resolve("independent-incidents");
        ProjectionDispatcher dispatcher = configured(golden, root);
        ObjectValue before = o(row, "before").with("machine_id", s(MACHINE)); byte[] beforeRaw = RetainedJson.encode(before);
        Path saved = root.resolve("actual-before.json"); Files.write(saved, beforeRaw, StandardOpenOption.CREATE_NEW);
        ObjectValue originalReceipt = named(resource("/interactionreceipt/legacy-producer-golden-v1.json", false), "service_reject");
        byte[] response = text(originalReceipt, "response_utf8").getBytes(StandardCharsets.UTF_8);
        assertEquals(v(before, "pending_interaction_id"), v(originalReceipt, "pending_interaction_id"));
        ObjectValue ticket = obj(f("incident_id", v(before, "incident_id")), f("pending_interaction_id", v(before, "pending_interaction_id")),
                f("action", s("reject")), f("before", obj(f("path", s(saved.toString())), f("bytes", i(beforeRaw.length)), f("sha256", s(sha(beforeRaw))))));
        ObjectValue request = obj(
                f("schema", s(InteractionHostJson.AFTER_SCHEMA)), f("original_response_base64", encoded(response)), f("original_sha256", s(sha(response))),
                f("ticket", ticket), f("origin", v(originalReceipt, "origin")), f("error", NULL), f("captured_at_utc", v(before, "captured_at_utc")));
        ObjectValue result = RetainedJson.object(RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_RECEIPT, request))));
        assertEquals(b(false), v(result, "command_acknowledged")); assertEquals(s("not_reported_as_ack"), v(result, "command_acknowledgement"));
        assertEquals(b(false), v(result, "original_pending_advanced_verified"));
        assertEquals(b(true), v(result, "original_pending_advanced_in_response"));
        assertEquals(s("sdk-response-only"), v(result, "postcondition_scope")); assertEquals(b(false), v(result, "durable_completion_granted"));
        assertEquals(b(false), v(result, "replay_allowed")); assertArrayEquals(beforeRaw, Files.readAllBytes(saved));
    }

    @Test void originalOfflineProducerReachesStrictRegistryAndHistoricalFactsStillRequireTheExactGrant() throws IOException {
        ObjectValue corpus = golden(), registry = o(corpus, "registry"); assertNotNull(registry);
        assertEquals(b(false), v(o(corpus, "historical_build_ref"), "current_runtime_qualified"));
        Path root = temporary.resolve("original-offline-registry"); ProjectionDispatcher dispatcher = configured(corpus, root);
        byte[] oldFacts = text(registry, "facts_utf8").getBytes(StandardCharsets.UTF_8), oldEntry = text(registry, "entry_utf8").getBytes(StandardCharsets.UTF_8);
        assertEquals(text(registry, "facts_sha256"), sha(oldFacts)); assertEquals(text(registry, "entry_sha256"), sha(oldEntry));
        ObjectValue originalFacts = RetainedJson.object(RetainedJson.parse(oldFacts)), originalEntry = RetainedJson.object(RetainedJson.parse(oldEntry));
        Path source = root.resolve("game").resolve(text(originalFacts, "source_relative")); Path gui = root.resolve("game").resolve(InteractionFallback.GUI_SOURCE);
        String fingerprint = text(originalEntry, "fingerprint");
        Path facts = root.resolve("state/evidence/interaction-source-registry/facts").resolve(fingerprint + ".json"); Files.createDirectories(facts.getParent());
        byte[] projectedFacts = replaceString(replaceString(oldFacts, text(originalFacts, "source_path"), source.toString()), text(originalFacts, "gui_path"), gui.toString());
        Files.write(facts, projectedFacts, StandardOpenOption.CREATE_NEW);
        byte[] entry = replaceString(replaceString(oldEntry, text(originalEntry, "source_path"), source.toString()), text(originalEntry, "gui_path"), gui.toString());
        entry = replaceString(entry, text(o(originalEntry, "source_facts"), "path"), facts.toString());
        entry = replaceString(entry, text(o(originalEntry, "source_facts"), "sha256"), sha(projectedFacts));
        Path entryPath = facts.getParent().getParent().resolve(fingerprint + ".json"); Files.write(entryPath, entry, StandardOpenOption.CREATE_NEW);
        ObjectValue lookup = o(registry, "lookup");
        ObjectValue actual = RetainedJson.object(RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_REGISTRY_LOOKUP, lookup))));
        assertEquals(RetainedJson.parse(entry), v(actual, "reviewed"));
        assertEquals(s("offline-source-reviewed"), v(o(actual, "audit"), "status"));
        assertEquals(s(sha(entry)), v(o(actual, "audit"), "entry_sha256"));
        assertEquals(v(originalEntry, "source_sha256"), v(o(actual, "audit"), "source_sha256"));
        // Only declared path strings and their derived facts SHA change; source bytes, binding and effects remain original.
        assertEquals(v(originalFacts, "definition"), v(RetainedJson.object(RetainedJson.parse(projectedFacts)), "definition"));
        Path historical = root.resolve("historical-facts.json"); Files.copy(facts, historical);
        byte[] externalEntry = replaceString(entry, facts.toString(), historical.toString()); Files.write(entryPath, externalEntry);
        ObjectValue ungranted = RetainedJson.object(RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_REGISTRY_LOOKUP, lookup))));
        assertTrue(v(ungranted, "reviewed") instanceof NullValue);
        assertEquals(s("unknown"), v(o(ungranted, "audit"), "status"));
        ProjectionEvidenceGrant grant = new ProjectionEvidenceGrant(historical, projectedFacts.length, sha(projectedFacts), text(corpus, "machine_id"), ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        EventSourceReadContext granted = new EventSourceReadContext(MACHINE, root.resolve("state"), root.resolve("game"), List.of(grant));
        ProjectionDispatcher exact = new ProjectionDispatcher(catalog().registrations(new ProjectionHostContext(Optional.of(granted))));
        assertEquals(RetainedJson.parse(externalEntry), v(RetainedJson.object(RetainedJson.parse(success(dispatch(exact,
                ProjectionOperation.EVENTS_INTERACTION_REGISTRY_LOOKUP, lookup)))), "reviewed"));
        Files.writeString(historical, "changed", StandardOpenOption.APPEND);
        ObjectValue changed = RetainedJson.object(RetainedJson.parse(success(dispatch(exact, ProjectionOperation.EVENTS_INTERACTION_REGISTRY_LOOKUP, lookup))));
        assertTrue(v(changed, "reviewed") instanceof NullValue);
        assertEquals(s("unknown"), v(o(changed, "audit"), "status"));
        assertEquals(TrustedEventSourceContext.FailureKind.REQUIRED_SOURCE_UNAVAILABLE,
                new TrustedEventSourceContext.UnavailableException("legacy unclassified failure", null).failureKind());
    }

    @Test void fixedContextActualGuiAndOriginalSourcePinsRemainRequiredAndCallerRootsCannotGrantThem() throws IOException {
        ObjectValue golden = golden(), row = named(golden, "known"); ObjectValue request = o(row, "request");
        ProjectionDispatcher absent = new ProjectionDispatcher(catalog().registrations(ProjectionHostContext.empty()));
        assertEquals(1, absent.profiles().size());
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, rejected(dispatch(absent, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN, request)));
        Path root = temporary.resolve("stock-drift"); ProjectionDispatcher dispatcher = configured(golden, root);
        assertEquals(4, dispatcher.profiles().size());
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN,
                request.with("state_root", s(root.resolve("state").toString())))));
        ObjectValue nativeContext = o(request, "context"), legality = o(nativeContext, "legality");
        for (Value invalidAllowed : List.<Value>of(i(1), new FloatingValue(1.0), s("true"), new ArrayValue(List.of()), obj())) {
            ObjectValue malformed = request.with("context", nativeContext.with("legality", legality.with("reject", o(legality, "reject").with("allowed", invalidAllowed))));
            assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN, malformed)));
        }
        Files.writeString(root.resolve("game").resolve(InteractionFallback.GUI_SOURCE), "changed", StandardOpenOption.APPEND);
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, rejected(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN, request)));
        // The original native fixture deliberately has no actual executable SHA; it cannot qualify an offline registry build.
        ObjectValue context = o(o(named(golden, "unknown"), "request"), "context"), definition = o(context, "definition");
        ObjectValue lookup = obj(f("schema", s("xar.interaction-registry-lookup/v1")), f("build", v(context, "build")),
                f("definition", obj(f("canonical_key", v(definition, "canonical_key")), f("deterministic_key_hash", v(definition, "deterministic_key_hash")))),
                f("gui_sha256", s(InteractionFallback.GUI_SHA256)));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_REGISTRY_LOOKUP, lookup)));
        assertEquals(65_536, org.xar.ck3.control.contracts.StrictJson.INPUT_MAX_BYTES);
        assertEquals(131_072, dispatcher.profiles().stream().filter(profile -> profile.operation() == ProjectionOperation.EVENTS_INTERACTION_BEFORE)
                .findFirst().orElseThrow().inputMaximumBytes());
    }

    private static Value withExpectedCurrentPresentation(Value legacyPlan, ObjectValue request) {
        if (legacyPlan instanceof NullValue) return NULL;
        ObjectValue plan = RetainedJson.object(legacyPlan), capture = o(plan, "unhandled_interaction_fallback");
        ObjectValue context = o(request, "context"), pending = o(o(request, "snapshot"), "pending_character_interaction");
        ObjectValue binding = o(capture, "binding"), roles = o(context, "roles"), definition = o(context, "definition");
        boolean notification = yes(pending, "auto_accept_notification");
        List<Value> steps = new java.util.ArrayList<>();
        for (String step : List.of("accept-pending-character-interaction", "acknowledge-pending-character-interaction",
                "block-pending-character-interaction", "reject-pending-character-interaction"))
            if (array(request, "action_steps").contains(s(step))) steps.add(s(step));
        List<Value> buttons = notification
                ? List.of(expectedButton(context, steps, "acknowledge", "only", "GetAnswerAcknowledgeText", true, 0))
                : List.of(expectedButton(context, steps, "reject", "left", "GetAnswerRejectText", false, 0),
                        expectedButton(context, steps, "accept", "right", "GetAnswerAcceptText", false, 1));
        ObjectValue presentation = obj(f("schema", s("xar.pending-primary-reply-presentation/v1")),
                f("basis", s("source_condition_with_same_native_routing")), f("gui_source", s(InteractionFallback.GUI_SOURCE)),
                f("gui_sha256", s(InteractionFallback.GUI_SHA256)), f("channel", s(notification ? "AUTO_ACCEPT_ACK" : "NORMAL_REPLY")),
                f("primary_channel_complete", b(true)), f("full_widget_visibility_observed", b(false)), f("binding", binding),
                f("native_pending", obj(f("source", s("native")), f("instance_id", v(pending, "instance_id")),
                        f("sender_character_id", v(pending, "sender_character_id")), f("auto_accept_notification", v(pending, "auto_accept_notification")))),
                f("definition", definition == null ? NULL : obj(f("canonical_key", v(definition, "canonical_key")), f("deterministic_key_hash", v(definition, "deterministic_key_hash")))),
                f("participants", obj(f("sender_character_id", v(pending, "sender_character_id")), f("recipient_character_id", v(roles, "recipient_character_id")),
                        f("intermediary_character_id", v(roles, "intermediary_character_id")), f("played_character_id", v(binding, "actor_character_id")))),
                f("available_steps", new ArrayValue(steps)), f("buttons", new ArrayValue(buttons)),
                f("supplemental_block", obj(f("button", s("block_button")), f("source_visibility", s("CharacterInteractionNotificationWindow.CanPotentiallyBeBlocked")),
                        f("shown", NULL), f("rendered_index", NULL), f("visibility_observed", b(false)),
                        f("action_reachable", b(steps.contains(s("block-pending-character-interaction")))), f("native_legality", expectedLegality(context, "block")))));
        return plan.with("unhandled_interaction_fallback", capture.with("gui_binding", o(capture, "gui_binding").with("current_presentation", presentation)));
    }
    private static ObjectValue expectedButton(ObjectValue context, List<Value> steps, String action, String position,
            String label, boolean notification, int index) {
        ObjectValue legality = expectedLegality(context, action); boolean available = yes(legality, "available");
        Value allowed = v(legality, "allowed");
        return obj(f("button", s(action + "_button")), f("action", s(action)), f("step", s(action + "-pending-character-interaction")),
                f("position", s(position)), f("rendered_index", i(index)), f("shown", b(true)),
                f("source_visibility", s(notification ? "CharacterInteractionNotificationWindow.IsAutoAcceptNotification"
                        : "Not(CharacterInteractionNotificationWindow.IsAutoAcceptNotification)")),
                f("label_source_expression", s("CharacterInteractionNotificationWindow." + label)), f("resolved_label", NULL),
                f("native_legal", b(available && b(true).equals(allowed))), f("action_reachable", b(steps.contains(s(action + "-pending-character-interaction")))),
                f("enabled", available && allowed instanceof BooleanValue ? allowed : NULL), f("native_legality", legality));
    }
    private static ObjectValue expectedLegality(ObjectValue context, String action) {
        ObjectValue row = o(o(context, "legality"), action);
        return obj(f("available", b("available".equals(text(row, "status")))), f("allowed", v(row, "allowed")), f("reason", v(row, "reason")));
    }
    private static void assertCurrentBeforeConsumer(ProjectionDispatcher dispatcher, ObjectValue original, ObjectValue currentPlan,
            String incident, String time) {
        byte[] planned = RetainedJson.encode(original.with("plan", currentPlan));
        ObjectValue before = RetainedJson.object(RetainedJson.parse(success(dispatch(dispatcher, ProjectionOperation.EVENTS_INTERACTION_BEFORE, obj(
                f("schema", s(InteractionHostJson.BEFORE_SCHEMA)), f("original_planned_base64", encoded(planned)), f("original_sha256", s(sha(planned))),
                f("incident_id", s(incident)), f("captured_at_utc", s(time)))))));
        ObjectValue capture = o(currentPlan, "unhandled_interaction_fallback");
        assertEquals(capture.with("incident_id", s(incident)).with("stage", s("before_submission")).with("captured_at_utc", s(time))
                .with("machine_id", s(MACHINE)).with("dispatch_attempted", b(false)), before);
        assertTrue(org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation.validateCapture(
                org.xar.ck3.control.contracts.StrictJson.parse(RetainedJson.encode(before)), text(currentPlan, "selected_step"), true).isPresent());
        String selectedStep = text(currentPlan, "selected_step");
        if (selectedStep != null) {
            int instance = number(capture, "pending_interaction_id").intValueExact();
            assertEquals(instance, org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation.requireSubmission(
                    org.xar.ck3.control.contracts.StrictJson.parse(RetainedJson.encode(before)), selectedStep, instance).pending().instanceId());
        }
        assertEquals(b(false), v(before, "dispatch_attempted"));
    }

    private static ProjectionDispatcher configured(ObjectValue corpus, Path root) throws IOException {
        Path state = Files.createDirectories(root.resolve("state")), game = Files.createDirectories(root.resolve("game"));
        Set<String> paths = new HashSet<>();
        for (ObjectValue file : objects(corpus, "files")) {
            String relative = text(file, "relative"); Path target = game.resolve(relative).normalize();
            assertFalse(relative.contains("\\")); assertFalse(Path.of(relative).isAbsolute()); assertTrue(target.startsWith(game)); assertTrue(paths.add(relative));
            byte[] original;
            try (GZIPInputStream input = new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(text(file, "gzip_base64"))))) {
                original = input.readNBytes(2_097_153); assertTrue(original.length <= 2_097_152);
            }
            assertEquals(number(file, "bytes").intValueExact(), original.length); assertEquals(text(file, "sha256"), sha(original));
            Files.createDirectories(target.getParent()); Files.write(target, original, StandardOpenOption.CREATE_NEW);
        }
        assertEquals(Set.of(InteractionFallback.GUI_SOURCE, "common/character_interactions/clerical_chastity_interaction.txt"), paths);
        return new ProjectionDispatcher(catalog().registrations(new ProjectionHostContext(Optional.of(new EventSourceReadContext(MACHINE, state, game)))));
    }
    private static InteractionProjectionPortCatalog catalog() {
        List<ServiceLoader.Provider<ProjectionPortCatalog>> providers = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type() == InteractionProjectionPortCatalog.class).toList();
        assertEquals(1, providers.size()); return assertInstanceOf(InteractionProjectionPortCatalog.class, providers.getFirst().get());
    }
    private static ProjectionResult dispatch(ProjectionDispatcher dispatcher, ProjectionOperation operation, ObjectValue value) {
        return dispatcher.dispatch(ProjectionWire.encodeCall(new ProjectionCall(new ProjectionCall.Identity("interaction-actual-producer", operation),
                ProjectionJson.object(RetainedJson.encode(value), 1_048_576))));
    }
    private static byte[] success(ProjectionResult result) { return assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes(); }
    private static ProjectionError.Code rejected(ProjectionResult result) { return assertInstanceOf(ProjectionResult.Rejected.class, result).error().code(); }
    private static Value encoded(byte[] raw) { return s(Base64.getEncoder().encodeToString(raw)); }
    private static byte[] replaceString(byte[] original, String oldValue, String newValue) {
        String before = new String(RetainedJson.encode(s(oldValue)), StandardCharsets.UTF_8), after = new String(RetainedJson.encode(s(newValue)), StandardCharsets.UTF_8);
        String raw = new String(original, StandardCharsets.UTF_8); assertTrue(raw.contains(before), "declared original path/pin required");
        return raw.replace(before, after).getBytes(StandardCharsets.UTF_8);
    }
    private static ObjectValue named(ObjectValue corpus, String name) { return objects(corpus, "cases").stream().filter(row -> eq(row, "name", s(name))).findFirst().orElseThrow(); }
    private static ObjectValue golden() throws IOException {
        ObjectValue corpus = resource(RESOURCE, true); assertEquals(s("xar.interaction-source-host-golden/v1"), v(corpus, "schema")); return corpus;
    }
    private static ObjectValue resource(String name, boolean gzip) throws IOException {
        try (var resource = InteractionProjectionIntegrationTest.class.getResourceAsStream(name)) {
            assertNotNull(resource, "mandatory actual producer fixture: " + name); byte[] packed = resource.readNBytes(1_048_577);
            assertTrue(packed.length <= (gzip ? 65_536 : 1_048_576));
            if (!gzip) return RetainedJson.object(RetainedJson.parse(packed));
            try (GZIPInputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = input.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576); return RetainedJson.object(RetainedJson.parse(raw));
            }
        }
    }
}
