package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;

/** Real original producer bytes enter the same typed Java boundary consumed by G2 M2. */
final class M2ProducerTest {
    private static final M2Producer.CaptureIdentity ID = new M2Producer.CaptureIdentity(
            "0123456789abcdef0123456789abcdef", "2026-10-23T00:00:00Z");
    private static final UnhandledEventFallback.ExistingPlan UNHANDLED =
            new UnhandledEventFallback.ExistingPlan("active_event_registry_contract_blocked", null, null);
    @TempDir Path temporary;

    @Test void allTwentyOneOriginalEventPlansProduceTheOriginalBeforeBodyAndKeepNativeDisplayOrder() throws IOException {
        ObjectValue corpus = resource("/unhandledevent/unhandled-event-golden-v1.json.gz");
        List<ObjectValue> rows = objects(corpus, "plan_cases"); assertEquals(21, rows.size());
        for (ObjectValue row : rows) {
            var actual = M2Producer.event(json(v(row, "request")), UNHANDLED, ID);
            assertEquals(v(row, "expected_plan"), parse(actual.plan().bytes()), text(row, "name"));
            assertFalse(actual.actionAuthorized()); assertFalse(actual.replayAllowed());
            if (v(row, "expected_plan") instanceof NullValue) {
                assertTrue(actual.proposal().isEmpty()); assertEquals(NULL, parse(actual.before().bytes()));
            } else {
                ObjectValue original = o(o(row, "expected_plan"), "unhandled_event_fallback");
                ObjectValue expected = put(original, f("incident_id", s(ID.incidentId())), f("stage", s("before_submission")),
                        f("captured_at_utc", s(ID.capturedAtUtc())), f("dispatch_attempted", b(false)));
                assertEquals(expected, parse(actual.before().bytes()), text(row, "name"));
                assertEquals(v(original, "window_context"), v(object(parse(actual.before().bytes())), "window_context"));
            }
        }
    }

    @Test void existingDedicatedChoiceOrRetainedUnknownAttemptCannotBeProposedAgain() throws IOException {
        ObjectValue row = objects(resource("/unhandledevent/unhandled-event-golden-v1.json.gz"), "plan_cases").getFirst();
        ProjectionJson request = json(v(row, "request"));
        var once = M2Producer.event(request, UNHANDLED, ID);
        ObjectValue retained = o(object(parse(once.plan().bytes())), "unhandled_event_fallback");
        for (var previous : List.of(new UnhandledEventFallback.ExistingPlan("active_event_registry_choice", "select-event-option-4", null),
                new UnhandledEventFallback.ExistingPlan("active_event_unhandled_first_rendered_option", null, retained))) {
            var result = M2Producer.event(request, previous, ID);
            assertTrue(result.proposal().isEmpty()); assertEquals(NULL, parse(result.before().bytes())); assertFalse(result.replayAllowed());
        }
    }

    @Test void tenActualOriginalAfterBodiesRetainAckPostconditionAndNoReplaySeparately() throws IOException {
        List<ObjectValue> rows = objects(resource("/unhandledevent/unhandled-event-evidence-body-golden-v1.json.gz"), "body_cases");
        assertEquals(10, rows.size());
        for (ObjectValue row : rows) {
            Value actual = parse(M2Producer.eventAfter(json(v(row, "after_request"))).bytes());
            assertEquals(v(row, "expected_after"), actual, text(row, "name"));
            assertFalse(yes(object(actual), "replay_allowed"));
        }
    }

    @Test void actualTwelveInteractionCasesKeepBothRolesLeftReplyAndOriginalNullableFields() throws IOException {
        ObjectValue corpus = resource("/interactionbefore/interaction-source-host-golden-v1.json.gz");
        Path game = Files.createDirectories(temporary.resolve("stock"));
        Path state = Files.createDirectories(temporary.resolve("state"));
        Set<String> permitted = Set.of("gui/interaction_notification_window.gui", "common/character_interactions/clerical_chastity_interaction.txt");
        for (ObjectValue file : objects(corpus, "files")) {
            String relative = text(file, "relative"); assertTrue(permitted.contains(relative));
            byte[] raw;
            try (var input = new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(text(file, "gzip_base64"))))) {
                raw = input.readNBytes(2_097_153); assertTrue(raw.length <= 2_097_152);
            }
            assertEquals(text(file, "sha256"), sha(raw)); assertEquals(number(file, "bytes").intValueExact(), raw.length);
            Path target = game.resolve(relative); Files.createDirectories(target.getParent()); Files.write(target, raw);
        }
        var trusted = TrustedEventSourceContext.openEvidence(new EventSourceReadContext("m2-producer-fixture", state, game));
        List<ObjectValue> cases = objects(corpus, "cases"); assertEquals(12, cases.size());
        for (ObjectValue row : cases) {
            ObjectValue oldBefore = o(row, "before");
            var identity = oldBefore == null ? ID : new M2Producer.CaptureIdentity(text(oldBefore, "incident_id"), text(oldBefore, "captured_at_utc"));
            var actual = M2Producer.interaction(json(v(row, "request")), trusted, identity);
            ObjectValue retainedRequest = o(row, "request"), retainedContext = o(retainedRequest, "context");
            ObjectValue pending = o(o(retainedRequest, "snapshot"), "pending_character_interaction");
            ObjectValue routing = o(retainedContext, "routing");
            if (eq(retainedContext, "status", s("available")) && o(retainedContext, "definition") == null) {
                // The current available native contract requires definition fields (PendingContextCodec); old missing-definition input is retained as a negative case.
                assertTrue(actual.proposal().isEmpty(), text(row, "name"));
                assertEquals(NULL, parse(actual.plan().bytes())); assertEquals(NULL, parse(actual.before().bytes()));
                assertFalse(actual.actionAuthorized()); assertFalse(actual.replayAllowed());
                continue;
            }
            if (pending != null && routing != null
                    && v(pending, "auto_accept_notification") instanceof BooleanValue
                    && v(routing, "auto_accept_notification") instanceof BooleanValue
                    && !v(pending, "auto_accept_notification").equals(v(routing, "auto_accept_notification"))) {
                // The immutable old ACK corpus predates same-frame channel equality. Its conflicting input now correctly rejects.
                assertTrue(actual.proposal().isEmpty(), text(row, "name"));
                assertEquals(NULL, parse(actual.plan().bytes())); assertEquals(NULL, parse(actual.before().bytes()));
                assertFalse(actual.actionAuthorized()); assertFalse(actual.replayAllowed());
                Value channel = v(pending, "auto_accept_notification");
                ObjectValue alignedContext = retainedContext.with("routing", routing.with("auto_accept_notification", channel));
                ObjectValue automatic = o(alignedContext, "auto_accept");
                if (automatic != null) alignedContext = alignedContext.with("auto_accept", automatic.with("value", channel));
                ObjectValue channelLegality = o(alignedContext, "legality");
                for (String action : List.of("accept", "reject", "block")) channelLegality = channelLegality.with(action,
                        o(channelLegality, action).with("allowed", b(false)).with("reason", s("auto_accept_notification")));
                alignedContext = alignedContext.with("legality", channelLegality);
                // This explicitly derived SOFTWARE case does not edit or upgrade the original retained corpus.
                var aligned = M2Producer.interaction(json(retainedRequest.with("context", alignedContext)), trusted, identity);
                assertTrue(aligned.proposal().isPresent(), "the software-consistent channel must retain a proposal");
                ObjectValue alignedPlan = object(parse(aligned.plan().bytes()));
                assertEquals(v(o(row, "expected_plan"), "selected_step"), v(alignedPlan, "selected_step"));
                assertTrue(org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation.validateCapture(
                        org.xar.ck3.control.contracts.StrictJson.parse(encode(o(alignedPlan, "unhandled_interaction_fallback"))),
                        text(alignedPlan, "selected_step"), true).isPresent());
                assertInstanceOf(ObjectValue.class, parse(aligned.before().bytes()));
                assertFalse(aligned.actionAuthorized()); assertFalse(aligned.replayAllowed());
                continue;
            }
            assertEquals(v(row, "expected_plan"), legacyInteractionView(parse(actual.plan().bytes())), text(row, "name"));
            assertEquals(oldBefore == null ? NULL : oldBefore.with("machine_id", s("m2-producer-fixture")), legacyInteractionView(parse(actual.before().bytes())), text(row, "name"));
            assertFalse(actual.actionAuthorized()); assertFalse(actual.replayAllowed());
            if (oldBefore != null) {
                ObjectValue before = object(parse(actual.before().bytes()));
                assertEquals(v(o(o(row, "request"), "context"), "roles"), v(o(before, "context"), "roles"));
                assertEquals(List.of("reject", "accept"), objects(before, "reply_options").stream().map(r -> text(r, "action")).toList());
                assertFalse(yes(before, "dispatch_attempted"));
            }
        }
        ObjectValue knownRequest = o(cases.getFirst(), "request"), context = o(knownRequest, "context"), legality = o(context, "legality");
        ObjectValue originalPlan = o(knownRequest, "original_plan");
        ObjectValue unknownAttempt = obj(f("replay_allowed", b(false)), f("response_assessment", s("UNKNOWN")));
        for (ObjectValue existing : List.of(originalPlan.with("selected_step", s("accept-pending-character-interaction")),
                originalPlan.with("unhandled_interaction_fallback", unknownAttempt))) {
            ObjectValue guarded = knownRequest.with("original_plan", existing).with("context", context.with("legality",
                    legality.with("reject", o(legality, "reject").with("allowed", i(1)))));
            var suppressed = M2Producer.interaction(json(guarded), trusted, ID);
            assertTrue(suppressed.proposal().isEmpty(), "existing choice or UNKNOWN attempt retains caller priority");
            assertEquals(NULL, parse(suppressed.plan().bytes()));
            assertEquals(NULL, parse(suppressed.before().bytes()), "no second incident may be created");
            assertEquals(existing, o(guarded, "original_plan"));
            assertFalse(suppressed.actionAuthorized()); assertFalse(suppressed.replayAllowed());
        }
        for (Value wrong : List.<Value>of(i(1), new FloatingValue(1.0), s("true"), new ArrayValue(List.of()), obj())) {
            ObjectValue invalid = knownRequest.with("context", context.with("legality",
                    legality.with("reject", o(legality, "reject").with("allowed", wrong))));
            assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                    () -> M2Producer.interaction(json(invalid), trusted, ID));
        }
    }

    @Test void missingNextInstanceCannotCrossTheProducerAfterBoundaryButExplicitNullCan() throws IOException {
        ObjectValue row = objects(resource("/unhandledevent/unhandled-event-evidence-body-golden-v1.json.gz"), "body_cases")
                .stream().filter(item -> eq(item, "name", s("independent-next-none-verified"))).findFirst().orElseThrow();
        ObjectValue request = o(row, "after_request"), outcome = o(request, "outcome"), result = o(outcome, "result");
        ObjectValue selection = o(result, "event_selection");
        assertTrue(selection.contains("new_event_instance_id")); assertInstanceOf(NullValue.class, selection.get("new_event_instance_id"));
        ObjectValue verified = object(parse(M2Producer.eventAfter(json(request)).bytes()));
        assertTrue(yes(verified, "command_acknowledged")); assertTrue(yes(verified, "event_instance_advanced_verified"));
        assertFalse(yes(verified, "replay_allowed"));
        ObjectValue missing = selection.project(selection.fields().keySet().stream()
                .filter(name -> !name.equals("new_event_instance_id")).toList());
        ObjectValue changed = request.with("outcome", outcome.with("result", result.with("event_selection", missing)));
        assertThrows(IllegalArgumentException.class, () -> M2Producer.eventAfter(json(changed)));
    }

    @Test void malformedRawFieldTypesAndMissingWrapperFieldsCannotCreateAnIncident() throws IOException {
        ObjectValue original = o(objects(resource("/unhandledevent/unhandled-event-golden-v1.json.gz"), "plan_cases").getFirst(), "request");
        ObjectValue snapshot = o(original, "snapshot");
        for (Value wrong : List.<Value>of(b(true), new FloatingValue(7.0), s("7"))) {
            ProjectionJson malformed = json(original.with("snapshot", snapshot.with("native_revision", wrong)));
            assertThrows(IllegalArgumentException.class, () -> M2Producer.event(malformed, UNHANDLED, ID));
        }
        assertThrows(IllegalArgumentException.class, () -> M2Producer.event(json(original.with("unexpected", NULL)), UNHANDLED, ID));
        ObjectValue missingActions = original.project(List.of("schema", "snapshot", "event_context", "event_summary", "registry_decision"));
        assertThrows(IllegalArgumentException.class, () -> M2Producer.event(json(missingActions), UNHANDLED, ID));
        assertThrows(IllegalArgumentException.class, () -> new M2Producer.CaptureIdentity("wrong", ID.capturedAtUtc()));
    }

    @Test void signedNativeCharacterRolesReachBothProducerAndPublicEvaluateWithoutSilentAbsence() throws Exception {
        ObjectValue corpus = resource("/interactionbefore/interaction-source-host-golden-v1.json.gz");
        Path game = Files.createDirectories(temporary.resolve("signed-stock"));
        Path state = Files.createDirectories(temporary.resolve("signed-state"));
        for (ObjectValue file : objects(corpus, "files")) {
            byte[] raw;
            try (var input = new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(text(file, "gzip_base64"))))) {
                raw = input.readNBytes(2_097_153); assertTrue(raw.length <= 2_097_152);
            }
            assertEquals(text(file, "sha256"), sha(raw));
            Path target = game.resolve(text(file, "relative")); Files.createDirectories(target.getParent()); Files.write(target, raw);
        }
        String machine = "m2-signed-character-fixture";
        var sources = new EventSourceReadContext(machine, state, game);
        var trusted = TrustedEventSourceContext.openEvidence(sources);
        ObjectValue original = o(objects(corpus, "cases").stream().filter(row -> eq(row, "name", s("known"))).findFirst().orElseThrow(), "request");
        // Each row is played actor, sender and route-kind; -1 remains optional intermediary absence.
        int[][] cases = {{Integer.MIN_VALUE, -2, 0}, {0, Integer.MIN_VALUE, 0}, {-2, 0, 1}, {0, -2, 1}};
        for (int[] ids : cases) {
            int actor = ids[0], sender = ids[1], kind = ids[2];
            assertEquals(actor, org.xar.ck3.control.contracts.NativeCharacterId.of(actor).value());
            assertEquals(sender, org.xar.ck3.control.contracts.NativeCharacterId.of(sender).value());
            ObjectValue snapshot = o(original, "snapshot"), context = o(original, "context");
            snapshot = snapshot.with("played_character", o(snapshot, "played_character").with("character_id", i(actor)))
                    .with("pending_character_interaction", o(snapshot, "pending_character_interaction").with("sender_character_id", i(sender)));
            ObjectValue roles = o(context, "roles").with("actor_character_id", i(sender))
                    .with("recipient_character_id", i(kind == 1 ? 101 : actor))
                    .with("intermediary_character_id", i(kind == 1 ? actor : -1));
            String responder = kind == 1 ? "intermediary" : "recipient";
            ObjectValue routing = o(context, "routing").with("kind", i(kind)).with("played_character_id", i(actor))
                    .with("current_responder_role", s(responder)).with("reply_execution_channel", s(responder));
            context = context.with("roles", roles).with("routing", routing);
            ObjectValue request = original.with("snapshot", snapshot).with("context", context);
            byte[] raw = encode(request); Path retained = temporary.resolve("signed-" + actor + "-" + sender + "-" + kind + ".json");
            Files.write(retained, raw);
            var source = new org.xar.ck3.control.g2.common.G2Source(machine, ID.capturedAtUtc(), "1.20.0.4",
                    new org.xar.ck3.control.contracts.ExactRef(retained.toString(), raw.length, sha(raw)));
            var payload = org.xar.ck3.control.g2.m2.M2Payload.input(org.xar.ck3.control.g2.m2.M2Payload.Operation.INTERACTION_PLAN, json(request));
            var envelope = new org.xar.ck3.control.g2.common.G2Request("m2-signed-roles", org.xar.ck3.control.g2.common.Milestone.M2, source, payload);
            var transported = org.xar.ck3.control.g2.common.G2Wire.decodeRequest(org.xar.ck3.control.g2.common.G2Wire.encodeRequest(envelope));
            assertArrayEquals(payload.bytes(), transported.payload().bytes());
            assertAll("present original Native roles actor=" + actor + ",sender=" + sender,
                    () -> {
                        var produced = M2Producer.interaction(json(request), trusted, ID);
                        assertTrue(produced.proposal().isPresent(), "legal signed character roles must not become an absent producer proposal");
                        ObjectValue plan = object(parse(produced.plan().bytes())), capture = o(plan, "unhandled_interaction_fallback");
                        assertEquals(i(actor), v(o(capture, "binding"), "actor_character_id"));
                        assertEquals(v(o(request, "context"), "roles"), v(o(capture, "context"), "roles"));
                        assertEquals(i(actor), v(o(object(parse(produced.before().bytes())), "binding"), "actor_character_id"));
                        assertEquals(s("reject-pending-character-interaction"), v(plan, "selected_step"));
                        ObjectValue rawContext = o(request, "context");
                        ObjectValue codecContext = rawContext.project(List.of("status", "snapshot_revision", "date_raw", "pending_interaction_id", "definition", "legality"))
                                .with("definition", o(rawContext, "definition").project(List.of("canonical_key", "deterministic_key_hash")));
                        var previous = SourceReviewedInteractionContinuation.originalPlan(v(request, "original_plan"));
                        ObjectValue codecInput = obj(f("schema", s(org.xar.ck3.control.events.interactionfallback.InteractionFallback.REQUEST_SCHEMA)),
                                f("binding", o(capture, "binding")), f("pending", o(o(request, "snapshot"), "pending_character_interaction")),
                                f("context", codecContext), f("action_steps", v(request, "action_steps")),
                                f("original_plan", obj(f("phase", s(previous.phase())), f("selected_step", s(previous.selectedStep())),
                                        f("blocked_marriage_reply", b(previous.blockedMarriageReply())),
                                        f("existing_interaction_fallback", b(previous.existingInteractionFallback())))));
                        var decoded = org.xar.ck3.control.events.interactionfallback.InteractionFallbackCodec.parseRequest(encode(codecInput));
                        assertEquals(actor, decoded.binding().actorCharacterId()); assertEquals(sender, decoded.pending().senderCharacterId());
                        assertEquals(decoded, org.xar.ck3.control.events.interactionfallback.InteractionFallbackCodec.parseRequest(
                                org.xar.ck3.control.events.interactionfallback.InteractionFallbackCodec.encodeRequest(decoded)));
                        assertFalse(produced.actionAuthorized()); assertFalse(produced.replayAllowed());
                    },
                    () -> {
                        var response = new org.xar.ck3.control.g2.m2.M2Research(sources).evaluate(transported);
                        Value result = parse(org.xar.ck3.control.g2.m2.M2Payload.unwrapResult(response.result()).bytes());
                        assertInstanceOf(ObjectValue.class, result, "public evaluate must retain a present plan, not silently return null");
                        ObjectValue capture = o(object(result), "unhandled_interaction_fallback");
                        assertEquals(i(actor), v(o(capture, "binding"), "actor_character_id"));
                        assertEquals(v(o(request, "context"), "roles"), v(o(capture, "context"), "roles"));
                    });
        }
    }

    @Test void malformedRequiredCharacterRolesCannotBecomeProducerIncidentsOrPublicPlans() throws Exception {
        ObjectValue corpus = resource("/interactionbefore/interaction-source-host-golden-v1.json.gz");
        Path game = Files.createDirectories(temporary.resolve("signed-stock"));
        Path state = Files.createDirectories(temporary.resolve("signed-state"));
        for (ObjectValue file : objects(corpus, "files")) {
            byte[] raw;
            try (var input = new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(text(file, "gzip_base64"))))) {
                raw = input.readNBytes(2_097_153); assertTrue(raw.length <= 2_097_152);
            }
            assertEquals(text(file, "sha256"), sha(raw));
            Path target = game.resolve(text(file, "relative")); Files.createDirectories(target.getParent()); Files.write(target, raw);
        }
        String machine = "m2-signed-character-fixture";
        var sources = new EventSourceReadContext(machine, state, game);
        var trusted = TrustedEventSourceContext.openEvidence(sources);
        ObjectValue original = o(objects(corpus, "cases").stream().filter(row -> eq(row, "name", s("known"))).findFirst().orElseThrow(), "request");
        List<Value> invalid = List.of(i(-1), b(true), new FloatingValue(0.0), s("0"), i(2147483648L), i(-2147483649L), NULL);
        int sequence = 0;
        for (String role : List.of("actor", "sender")) for (Value wrong : invalid) {
            ObjectValue snapshot = o(original, "snapshot"), context = o(original, "context");
            if (role.equals("actor")) {
                snapshot = snapshot.with("played_character", o(snapshot, "played_character").with("character_id", wrong));
                context = context.with("roles", o(context, "roles").with("recipient_character_id", wrong))
                        .with("routing", o(context, "routing").with("played_character_id", wrong));
            } else {
                snapshot = snapshot.with("pending_character_interaction", o(snapshot, "pending_character_interaction").with("sender_character_id", wrong));
                context = context.with("roles", o(context, "roles").with("actor_character_id", wrong));
            }
            ObjectValue request = original.with("snapshot", snapshot).with("context", context);
            var produced = M2Producer.interaction(json(request), trusted, ID);
            assertTrue(produced.proposal().isEmpty(), "invalid required " + role + " identity must not create an incident");
            assertEquals(NULL, parse(produced.before().bytes()));
            byte[] raw = encode(request); Path retained = temporary.resolve("invalid-role-" + sequence++ + ".json"); Files.write(retained, raw);
            var source = new org.xar.ck3.control.g2.common.G2Source(machine, ID.capturedAtUtc(), "1.20.0.4",
                    new org.xar.ck3.control.contracts.ExactRef(retained.toString(), raw.length, sha(raw)));
            var payload = org.xar.ck3.control.g2.m2.M2Payload.input(org.xar.ck3.control.g2.m2.M2Payload.Operation.INTERACTION_PLAN, json(request));
            var envelope = new org.xar.ck3.control.g2.common.G2Request("m2-invalid-role", org.xar.ck3.control.g2.common.Milestone.M2, source, payload);
            var transported = org.xar.ck3.control.g2.common.G2Wire.decodeRequest(org.xar.ck3.control.g2.common.G2Wire.encodeRequest(envelope));
            var response = new org.xar.ck3.control.g2.m2.M2Research(sources).evaluate(transported);
            assertEquals(NULL, parse(org.xar.ck3.control.g2.m2.M2Payload.unwrapResult(response.result()).bytes()));
            assertFalse(produced.actionAuthorized()); assertFalse(produced.replayAllowed());
        }
    }

    /** Compare immutable legacy golden fields only after the actual current capture consumer validates the complete new projection. */
    private static Value legacyInteractionView(Value actual) {
        if (actual instanceof NullValue) return actual;
        ObjectValue body = object(actual);
        ObjectValue nested = o(body, "unhandled_interaction_fallback");
        ObjectValue capture = nested == null ? body : nested;
        var verified = org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation.validateCapture(
                org.xar.ck3.control.contracts.StrictJson.parse(encode(capture)), text(body, "selected_step"), true);
        assertTrue(verified.isPresent(), "complete current presentation must reach its real consumer");
        ObjectValue gui = o(capture, "gui_binding");
        assertNotNull(o(gui, "current_presentation"));
        ObjectValue legacyGui = gui.project(gui.fields().keySet().stream()
                .filter(key -> !key.equals("current_presentation")).toList());
        ObjectValue legacyCapture = capture.with("gui_binding", legacyGui);
        return nested == null ? legacyCapture : body.with("unhandled_interaction_fallback", legacyCapture);
    }

    private static ProjectionJson json(Value value) { return ProjectionJson.value(encode(value), 1_048_576); }
    private static ObjectValue resource(String name) throws IOException {
        try (var source = M2ProducerTest.class.getResourceAsStream(name)) {
            assertNotNull(source, "required original producer fixture cannot be skipped");
            byte[] packed = source.readNBytes(131_073); assertTrue(packed.length <= 131_072);
            try (var input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = input.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576); return object(parse(raw));
            }
        }
    }
}
