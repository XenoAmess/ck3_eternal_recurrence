package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.io.InputStream;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;

/** Actual old producers; only declared path fields and their derived reference SHAs are relocated. */
final class SourceReviewedEventConsumerTest {
    @TempDir Path temporary;
    private static final List<String> COHORTS = List.of("generic", "council", "council-source-drift", "liberty", "liberty-source-drift", "sway", "sway-source-drift", "factions");
    static ObjectValue golden() throws IOException {
        ObjectValue combined = null; Map<String, Value> blobs = new HashMap<>(); List<Value> cases = new ArrayList<>(), evidence = new ArrayList<>(); Set<String> names = new HashSet<>();
        for (String cohort : COHORTS) {
            String path = "/unhandledevent/source-review-" + cohort + "-golden-v1.json.gz";
            try (InputStream resource = SourceReviewedEventConsumerTest.class.getResourceAsStream(path)) {
                if (resource == null) throw new IOException("mandatory actual source-review cohort missing; NOT RUN: " + cohort);
                byte[] packed = resource.readNBytes(65_537); if (packed.length > 65_536) throw new IOException("source-review cohort compression budget exceeded");
                try (InputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                    byte[] bytes = input.readNBytes(1_048_577);
                    if (bytes.length > 1_048_576) throw new IOException("source-review cohort decompression budget exceeded");
                    ObjectValue corpus = RetainedJson.object(RetainedJson.parse(bytes));
                    assertEquals("xar.ck3.source-review-golden/v1", text(corpus, "schema")); assertEquals("gzip-base64", text(corpus, "blob_encoding"));
                    if (combined == null) combined = corpus;
                    else assertEquals(v(combined, "machine_id"), v(corpus, "machine_id"), "cohort source machines differ");
                    for (ObjectValue row : objects(corpus, "cases")) {
                        assertTrue(names.add(text(row, "name")), "duplicate source-review case across cohorts"); cases.add(row);
                    }
                    for (Map.Entry<String, Value> blob : RetainedJson.object(v(corpus, "blobs")).fields().entrySet()) {
                        Value existing = blobs.putIfAbsent(blob.getKey(), blob.getValue());
                        if (existing != null) assertEquals(existing, blob.getValue(), "same original SHA has different blob bytes");
                    }
                    evidence.add(corpus);
                }
            }
        }
        assertNotNull(combined); assertEquals(58, cases.size(), "all fixed cohorts and all original cases are mandatory");
        return put(combined, f("cases", new ArrayValue(cases)), f("blobs", new ObjectValue(blobs)), f("cohort_evidence", new ArrayValue(evidence)));
    }
    @TestFactory Stream<DynamicTest> actualAnnotationSourceReadsAndFullExistingPolicyOutputs() throws IOException {
        ObjectValue corpus = golden();
        return objects(corpus, "cases").stream().map(row -> DynamicTest.dynamicTest(text(row, "name"), () -> {
            Relocated input = relocate(corpus, row, temporary.resolve(text(row, "name")));
            ObjectValue actual;
            if (eq(row, "mode", s("policy"))) {
                actual = ExistingFactionEventPolicies.choose(RetainedJson.object(input.plan()), o(row, "snapshot"), steps(row));
            } else {
                SourceReviewedEventConsumer.ReviewedPlan annotated = SourceReviewedEventConsumer.annotate(RetainedJson.encode(input.plan()), input.state());
                actual = annotated.plan();
                assertFalse(annotated.actionAuthorized()); assertFalse(annotated.replayAllowed());
                ObjectValue capture = o(actual, "unhandled_event_fallback");
                SourceReviewedEventConsumer.FollowupPresence presence = capture == null || !capture.contains("offline_followup_required")
                    ? SourceReviewedEventConsumer.FollowupPresence.MISSING : v(capture, "offline_followup_required") instanceof NullValue
                    ? SourceReviewedEventConsumer.FollowupPresence.NULL : SourceReviewedEventConsumer.FollowupPresence.VALUE;
                assertEquals(presence, annotated.offlineFollowupRequired().presence());
                if (presence == SourceReviewedEventConsumer.FollowupPresence.VALUE) assertEquals(RetainedJson.bool(v(capture, "offline_followup_required")), annotated.offlineFollowupRequired().required());
                if (eq(row, "mode", s("pipeline"))) actual = ExistingFactionEventPolicies.choose(actual, o(row, "snapshot"), steps(row));
            }
            assertEquals(input.expected(), actual, text(row, "name"));
            for (Map.Entry<Path, byte[]> file : input.initialFiles().entrySet()) assertArrayEquals(file.getValue(), Files.readAllBytes(file.getKey()), "consumer must remain read-only");
        }));
    }
    @Test void mandatoryActualSpecialCoverageCannotBeReportedFromGenericSamples() throws IOException {
        ObjectValue corpus = golden(); Set<String> covered = new HashSet<>();
        boolean genericExact = false, genericRebound = false, independence = false, populist = false, noTodo = false;
        for (ObjectValue row : objects(corpus, "cases")) {
            ObjectValue expected = o(row, "expected"), capture = o(expected, "unhandled_event_fallback"), audit = o(capture, "source_knowledge");
            if (eq(audit, "binding_mode", s("reviewed_letter_source_rebound"))) covered.add(text(capture, "event_definition_key"));
            genericExact |= eq(row, "name", s("generic-exact-known")); genericRebound |= eq(row, "name", s("generic-character-rebound"));
            independence |= eq(expected, "phase", s("active_event_source_reviewed_independence_refusal"));
            populist |= eq(audit, "binding_mode", s("populist1001_source_rebound")) && eq(expected, "phase", s("active_event_source_reviewed_populist_refusal"));
            noTodo |= eq(row, "name", s("generic-repeat-known-no-new-todo")) && eq(capture, "offline_followup_required", b(false));
        }
        assertEquals(ReviewedLetterSourceRebind.KEYS, covered, "all three actual stock letter rebinds are mandatory");
        assertTrue(genericExact && genericRebound && independence && populist && noTodo, "full actual source-review and policy chain required");
    }
    @Test void completeSnapshotIsRetainedForTheRealDedicatedConsumer() throws IOException {
        ObjectValue corpus = golden();
        for (ObjectValue row : objects(corpus, "cases")) if (eq(row, "mode", s("pipeline"))) {
            ObjectValue request = o(row, "request"); assertNotNull(request);
            UnhandledEventFallback.Request typed = UnhandledEventCodec.decodePlan(RetainedJson.encode(request));
            assertEquals(o(request, "snapshot"), typed.snapshot().originalSnapshot());
            assertEquals(typed, UnhandledEventCodec.decodePlan(UnhandledEventCodec.encodeRequest(typed)));
            Relocated input = relocate(corpus, row, temporary.resolve("typed-" + text(row, "name")));
            UnhandledEventFallback.Plan proposal = UnhandledEventFallback.plan(typed).orElseThrow();
            assertEquals(input.plan(), UnhandledEventCodec.legacyPlan(proposal), "actual old producer plan feeds the real Java planner");
            SourceReviewedEventConsumer.ReviewedPlan output = SourceReviewedEventConsumer.continueWithExistingPolicies(proposal, typed, input.state());
            assertEquals(input.expected(), output.plan()); assertFalse(output.actionAuthorized()); assertFalse(output.replayAllowed());
        }
    }
    @Test void canonicalFingerprintKeepsPythonAsciiUnicodeAndExactIntegerDomain() {
        Value value = RetainedJson.parse("{\"text\":\"中😀\",\"identity\":9007199254740993}".getBytes(StandardCharsets.UTF_8));
        assertEquals("{\"identity\":9007199254740993,\"text\":\"\\u4e2d\\ud83d\\ude00\"}", canonical(value));
        assertThrows(IllegalArgumentException.class, () -> canonical(RetainedJson.parse("{\"identity\":1.0}".getBytes(StandardCharsets.UTF_8))));
    }
    @Test void notRequestedPlanPreservesMissingNullAndExplicitFalseFollowup() {
        ObjectValue ordinary = obj(f("phase", s("ordinary_governance")));
        assertEquals(SourceReviewedEventConsumer.FollowupPresence.MISSING,
            SourceReviewedEventConsumer.annotate(RetainedJson.encode(ordinary), null).offlineFollowupRequired().presence());
        ObjectValue explicitNull = ordinary.with("unhandled_event_fallback", obj(f("offline_followup_required", NULL)));
        assertEquals(SourceReviewedEventConsumer.FollowupPresence.NULL,
            SourceReviewedEventConsumer.annotate(RetainedJson.encode(explicitNull), null).offlineFollowupRequired().presence());
        ObjectValue reviewed = ordinary.with("unhandled_event_fallback", obj(f("offline_followup_required", b(false))));
        assertEquals(Boolean.FALSE, SourceReviewedEventConsumer.annotate(RetainedJson.encode(reviewed), null).offlineFollowupRequired().required());
    }
    @Test void actualSecondBatchRecognizesKnownSourceWithoutAnotherAnalysisTodo() throws IOException {
        ObjectValue corpus = golden(), repeated = o(corpus, "repeat_known_batch"); assertNotNull(repeated);
        ObjectValue reference = o(repeated, "original_report"), report = o(repeated, "report"); assertNotNull(reference); assertNotNull(report);
        byte[] packed = Base64.getDecoder().decode(text(o(corpus, "blobs"), text(reference, "sha256"))); byte[] original;
        try (InputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
            original = input.readNBytes(1_048_577); if (original.length > 1_048_576) throw new IOException("repeat source-review report exceeds original JSON bound");
        }
        assertEquals(number(reference, "bytes"), java.math.BigInteger.valueOf(original.length));
        assertEquals(text(reference, "sha256"), sha(original)); assertEquals(report, RetainedJson.parse(original));
        assertTrue(array(report, "entries").isEmpty()); assertTrue(array(report, "unresolved").isEmpty());
        List<ObjectValue> known = objects(report, "already_known"); assertEquals(1, known.size());
        assertTrue(eq(known.getFirst(), "offline_followup_required", b(false)));
    }
    record Relocated(Value plan, Value expected, Path state, Map<Path, byte[]> initialFiles) { }
    static Relocated relocate(ObjectValue corpus, ObjectValue row, Path root) throws IOException {
        Files.createDirectories(root); Map<String, Path> paths = new HashMap<>(); Map<String, String> hashes = new HashMap<>();
        List<ObjectValue> files = objects(row, "files"); ObjectValue blobs = o(corpus, "blobs");
        for (ObjectValue file : files) {
            Path destination = root.resolve(text(file, "relative")).normalize();
            assertTrue(destination.startsWith(root), "declared finite test projection stays inside temporary root");
            paths.put(text(file, "path"), destination);
        }
        Map<Path, byte[]> installed = new HashMap<>();
        for (String kind : List.of("source", "gui", "facts", "entry")) for (ObjectValue file : files) if (eq(file, "kind", s(kind))) {
            String oldSha = text(file, "sha256"); byte[] packed = Base64.getDecoder().decode(text(blobs, oldSha)); byte[] original;
            try (InputStream input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                original = input.readNBytes(2_097_153); if (original.length > 2_097_152) throw new IOException("source-review blob exceeds original source bound");
            }
            assertEquals(number(file, "bytes"), java.math.BigInteger.valueOf(original.length)); assertEquals(oldSha, sha(original));
            byte[] output = original;
            if (kind.equals("facts") || kind.equals("entry")) output = RetainedJson.encode(project(RetainedJson.parse(original), paths, hashes));
            Path destination = paths.get(text(file, "path")); Files.createDirectories(destination.getParent()); Files.write(destination, output);
            installed.put(destination, output); hashes.put(oldSha, sha(output));
        }
        Value plan = project(v(row, "plan"), paths, hashes), expected = project(v(row, "expected"), paths, hashes);
        Path state = v(row, "state_directory") instanceof NullValue ? null : root.resolve("state");
        return new Relocated(plan, expected, state, Map.copyOf(installed));
    }
    /** Only schema-declared paths/reference hashes move; binding, source bytes and option hashes never move. */
    private static Value project(Value value, Map<String, Path> paths, Map<String, String> hashes) {
        if (value instanceof ArrayValue array) return new ArrayValue(array.values().stream().map(child -> project(child, paths, hashes)).toList());
        if (!(value instanceof ObjectValue object)) return value;
        ObjectValue result = object;
        for (Map.Entry<String, Value> field : object.fields().entrySet()) {
            Value child = project(field.getValue(), paths, hashes);
            if (field.getValue() instanceof StringValue text) {
                if (Set.of("path", "source_path", "entry_path").contains(field.getKey()) && paths.containsKey(text.value())) child = s(paths.get(text.value()).toString());
                else if (Set.of("sha256", "entry_sha256").contains(field.getKey()) && hashes.containsKey(text.value())) child = s(hashes.get(text.value()));
            }
            result = result.with(field.getKey(), child);
        }
        return result;
    }
    static List<String> steps(ObjectValue row) {
        List<String> result = new ArrayList<>(); for (Value step : array(row, "action_steps")) result.add(RetainedJson.string(step)); return List.copyOf(result);
    }
}
