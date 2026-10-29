package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrants;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Only portable, source-pinned original producer fixtures. No installed game, native endpoint or gameplay writer. */
final class M2LifecycleFixtures {
    static final String MACHINE = "portable-m2-lifecycle-fixture";
    static final String TIME = "2026-10-22T00:00:00Z";
    private static final List<String> COHORTS = List.of("generic", "council", "council-source-drift", "liberty",
            "liberty-source-drift", "sway", "sway-source-drift", "factions");
    private M2LifecycleFixtures() { }

    record Fixture(ObjectValue corpus, ObjectValue row, Path root, Path state, Path game, Path incidents,
            Path knowledge, Path grants, EventSourceReadContext sources,
            OfflineEventBatchAnalyzer.Configuration batchConfiguration, ExactRef originalRequest) { }
    record Relocated(ObjectValue plan, Value expected, Path state, Map<Path, byte[]> initialFiles) { }

    static ObjectValue golden() throws IOException {
        List<Value> cases = new ArrayList<>(); Map<String, Value> blobs = new LinkedHashMap<>();
        Set<String> names = new HashSet<>(); ObjectValue basis = null;
        for (String cohort : COHORTS) {
            ObjectValue corpus = resource("/unhandledevent/source-review-" + cohort + "-golden-v1.json.gz", true);
            assertEquals(s("xar.ck3.source-review-golden/v1"), v(corpus, "schema"));
            assertEquals(s("gzip-base64"), v(corpus, "blob_encoding"));
            if (basis == null) basis = corpus;
            else assertEquals(v(basis, "machine_id"), v(corpus, "machine_id"));
            for (ObjectValue row : objects(corpus, "cases")) {
                assertTrue(names.add(text(row, "name")), "original producer case appears once"); cases.add(row);
            }
            for (Map.Entry<String, Value> blob : o(corpus, "blobs").fields().entrySet()) {
                Value previous = blobs.putIfAbsent(blob.getKey(), blob.getValue());
                if (previous != null) assertEquals(previous, blob.getValue(), "same SHA must identify the same original bytes");
            }
        }
        assertNotNull(basis); assertEquals(58, cases.size());
        return basis.with("cases", new ArrayValue(cases)).with("blobs", new ObjectValue(blobs));
    }

    static Fixture fixture(Path root) throws IOException {
        Files.createDirectories(root); ObjectValue corpus = golden();
        ObjectValue row = named(corpus, "faction_demand.0101-exact-stock");
        Path state = Files.createDirectories(root.resolve("state")); Path game = Files.createDirectories(root.resolve("game"));
        installStock(corpus, game);
        Path incidents = Files.createDirectories(root.resolve("incidents")); Path knowledge = Files.createDirectories(root.resolve("knowledge"));
        Path grants = knowledge.resolve("fixed-grants.json"); EvidenceGrantManifestPublisher.publish(grants, List.of());
        ProjectionEvidenceGrants fresh = () -> {
            try { return ProjectionEvidenceCodec.decode(Files.readAllBytes(grants)); }
            catch (IOException error) { throw new UncheckedIOException(error); }
        };
        EventSourceReadContext sources = new EventSourceReadContext(MACHINE, state, game, fresh);
        ObjectValue input = o(row, "request"); assertNotNull(input, "the actual original producer request is mandatory");
        Path original = root.resolve("original-producer-request.json"); ExactRef originalRef = write(original, RetainedJson.encode(input));
        return new Fixture(corpus, row, root, state, game, incidents, knowledge, grants, sources,
                new OfflineEventBatchAnalyzer.Configuration(sources, incidents, knowledge, grants), originalRef);
    }

    static ObjectValue sourceReviewedInput(ObjectValue plan, ObjectValue snapshot, Value steps) {
        return obj(f("schema", s(SourceReviewedPlanJson.SCHEMA)), f("plan", plan), f("snapshot", snapshot), f("action_steps", steps));
    }
    static ObjectValue beforeInput(ObjectValue plan, String incident) {
        ObjectValue binding = o(o(plan, "unhandled_event_fallback"), "binding");
        return obj(f("schema", s(UnhandledEventEvidenceJson.BEFORE_SCHEMA)),
                f("planned", obj(f("snapshot_id", v(binding, "snapshot_id")), f("revision", v(binding, "revision")), f("plan", plan))),
                f("incident_id", s(incident)), f("captured_at_utc", s(TIME)));
    }
    static ObjectValue ticket(ObjectValue before, ExactRef beforeRef) {
        return obj(f("incident_id", v(before, "incident_id")), f("current_event_instance_id", v(before, "current_event_instance_id")),
                f("selected_native_option_index", v(o(before, "selection"), "native_option_index")), f("before", reference(beforeRef)));
    }
    static ObjectValue afterInput(ObjectValue ticket, Value outcome) {
        return obj(f("schema", s(UnhandledEventEvidenceJson.AFTER_SCHEMA)), f("ticket", ticket), f("outcome", outcome),
                f("error", NULL), f("captured_at_utc", s(TIME)));
    }
    static ObjectValue acknowledgedOutcome(ObjectValue before, boolean disappeared) {
        Value selected = disappeared ? obj(f("status", s("event_instance_advanced")), f("postcondition_verified", b(true)),
                f("old_event_instance_id", v(before, "current_event_instance_id")),
                f("new_event_instance_id", i(number(before, "current_event_instance_id").longValueExact() + 1)),
                f("selected_native_option_index", v(o(before, "selection"), "native_option_index"))) : NULL;
        return obj(f("status", s("available")), f("result", obj(f("accepted", b(true)), f("event_selection", selected))));
    }
    static OfflineEventBatchAnalyzer.Request batch(Fixture fixture, String batchId, ObjectValue before, ObjectValue after) throws IOException {
        String incident = text(before, "incident_id"); assertNotNull(incident); assertEquals(v(before, "incident_id"), v(after, "incident_id"));
        Path beforePath = fixture.incidents().resolve(incident + ".before.json");
        ExactRef beforeRef;
        if (Files.exists(beforePath)) {
            byte[] actual = Files.readAllBytes(beforePath); assertArrayEquals(RetainedJson.encode(before), actual);
            beforeRef = new ExactRef(beforePath.toString(), actual.length, sha(actual));
        } else beforeRef = write(beforePath, RetainedJson.encode(before));
        ExactRef afterRef = write(fixture.incidents().resolve(incident + ".after.json"), RetainedJson.encode(after));
        assertEquals(reference(beforeRef), o(after, "before"), "the after response belongs to the exact persisted before");
        ObjectValue item = obj(f("incident_id", s(incident)), f("event_definition_key", v(before, "event_definition_key")),
                f("before", s(beforeRef.path())), f("before_sha256", s(beforeRef.sha256())),
                f("after", s(afterRef.path())), f("after_sha256", s(afterRef.sha256())));
        ExactRef manifest = write(fixture.incidents().resolve(batchId + ".json"), RetainedJson.encode(obj(
                f("completed_control_sequence", i(1)), f("new_incidents", new ArrayValue(List.of(item))))));
        return new OfflineEventBatchAnalyzer.Request(batchId, manifest, List.of(beforeRef, afterRef));
    }
    static ObjectValue batchInput(OfflineEventBatchAnalyzer.Request request) {
        return obj(f("schema", s(OfflineEventBatchAnalyzer.REQUEST_SCHEMA)), f("batch_id", s(request.batchId())),
                f("manifest_ref", reference(request.manifest())),
                f("captured_refs", new ArrayValue(request.capturedRefs().stream().map(ref -> (Value) reference(ref)).toList())));
    }
    static OfflineEventBatchAnalyzer.Request withInteraction(Fixture fixture, String batchId, OfflineEventBatchAnalyzer.Request eventBatch,
            ObjectValue before, ObjectValue after) throws IOException {
        String incident = text(before, "incident_id"); assertNotNull(incident); assertEquals(v(before, "incident_id"), v(after, "incident_id"));
        Path beforePath = fixture.incidents().resolve(incident + ".before.json");
        byte[] beforeRaw = RetainedJson.encode(before); ExactRef beforeRef;
        if (Files.exists(beforePath)) {
            assertArrayEquals(beforeRaw, Files.readAllBytes(beforePath)); beforeRef = new ExactRef(beforePath.toString(), beforeRaw.length, sha(beforeRaw));
        } else beforeRef = write(beforePath, beforeRaw);
        ExactRef afterRef = write(fixture.incidents().resolve(incident + ".after.json"), RetainedJson.encode(after));
        assertEquals(reference(beforeRef), o(after, "before"));
        ObjectValue original = RetainedJson.object(RetainedJson.parse(Files.readAllBytes(Path.of(eventBatch.manifest().path()))));
        List<Value> incidents = new ArrayList<>(array(original, "new_incidents"));
        incidents.add(obj(f("kind", s("pending_character_interaction")), f("incident_id", s(incident)),
                f("interaction_definition_key", v(before, "interaction_definition_key")),
                f("before", s(beforeRef.path())), f("before_sha256", s(beforeRef.sha256())),
                f("after", s(afterRef.path())), f("after_sha256", s(afterRef.sha256()))));
        ExactRef manifest = write(fixture.incidents().resolve(batchId + ".json"), RetainedJson.encode(original.with("new_incidents", new ArrayValue(incidents))));
        List<ExactRef> refs = new ArrayList<>(eventBatch.capturedRefs()); refs.add(beforeRef); refs.add(afterRef);
        return new OfflineEventBatchAnalyzer.Request(batchId, manifest, refs);
    }
    static ExactRef write(Path path, byte[] raw) throws IOException {
        Files.createDirectories(path.getParent()); Files.write(path, raw, StandardOpenOption.CREATE_NEW);
        return new ExactRef(path.toString(), raw.length, sha(raw));
    }
    static ObjectValue reference(ExactRef ref) { return obj(f("path", s(ref.path())), f("bytes", i(ref.bytes())), f("sha256", s(ref.sha256()))); }
    static ObjectValue named(ObjectValue corpus, String name) {
        return objects(corpus, "cases").stream().filter(row -> eq(row, "name", s(name))).findFirst().orElseThrow();
    }
    static ObjectValue resource(String name, boolean compressed) throws IOException {
        try (var input = M2LifecycleFixtures.class.getResourceAsStream(name)) {
            if (input == null) throw new IOException("mandatory actual producer fixture missing; NOT RUN: " + name);
            byte[] packed = input.readNBytes(1_048_577);
            if (packed.length > (compressed ? 65_536 : 1_048_576)) throw new IOException("original fixture exceeds its recorded role bound");
            if (!compressed) return RetainedJson.object(RetainedJson.parse(packed));
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                byte[] raw = gzip.readNBytes(1_048_577);
                if (raw.length > 1_048_576) throw new IOException("original fixture decompression bound exceeded");
                return RetainedJson.object(RetainedJson.parse(raw));
            }
        }
    }
    static byte[] blob(ObjectValue corpus, String digest) throws IOException {
        byte[] packed = Base64.getDecoder().decode(text(o(corpus, "blobs"), digest));
        try (var input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
            byte[] raw = input.readNBytes(2_097_153); if (raw.length > 2_097_152) throw new IOException("original stock blob exceeds role bound");
            assertEquals(digest, sha(raw)); return raw;
        }
    }
    static void installStock(ObjectValue corpus, Path game) throws IOException {
        for (Map.Entry<String, String> pin : ReviewedLetterSourceRebind.installedSourceHashes().entrySet()) {
            Path target = game.resolve(pin.getKey()); byte[] raw = blob(corpus, pin.getValue()); Files.createDirectories(target.getParent());
            if (Files.exists(target)) assertArrayEquals(raw, Files.readAllBytes(target));
            else Files.write(target, raw, StandardOpenOption.CREATE_NEW);
        }
    }
    static void installInteractionStock(ObjectValue corpus, Path game) throws IOException {
        Set<String> actual = new HashSet<>();
        for (ObjectValue file : objects(corpus, "files")) {
            String relative = text(file, "relative"); assertTrue(actual.add(relative));
            Path target = game.resolve(relative).normalize(); assertTrue(target.startsWith(game));
            byte[] packed = Base64.getDecoder().decode(text(file, "gzip_base64")); byte[] raw;
            try (var input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
                raw = input.readNBytes(2_097_153); if (raw.length > 2_097_152) throw new IOException("original interaction stock bound exceeded");
            }
            assertEquals(number(file, "bytes").intValueExact(), raw.length); assertEquals(text(file, "sha256"), sha(raw));
            Files.createDirectories(target.getParent()); Files.write(target, raw, StandardOpenOption.CREATE_NEW);
        }
        assertEquals(Set.of("gui/interaction_notification_window.gui", "common/character_interactions/clerical_chastity_interaction.txt"), actual);
    }
    static Relocated relocate(ObjectValue corpus, ObjectValue row, Path root) throws IOException {
        Files.createDirectories(root); Map<String, Path> paths = new HashMap<>(); Map<String, String> hashes = new HashMap<>();
        List<ObjectValue> files = objects(row, "files"); Map<Path, byte[]> installed = new LinkedHashMap<>();
        for (ObjectValue file : files) {
            Path destination = root.resolve(text(file, "relative")).normalize(); assertTrue(destination.startsWith(root));
            assertNull(paths.put(text(file, "path"), destination));
        }
        for (String kind : List.of("source", "gui", "facts", "entry")) for (ObjectValue file : files) if (eq(file, "kind", s(kind))) {
            String digest = text(file, "sha256"); byte[] raw = blob(corpus, digest);
            assertEquals(number(file, "bytes"), java.math.BigInteger.valueOf(raw.length));
            byte[] output = kind.equals("facts") || kind.equals("entry") ? RetainedJson.encode(project(RetainedJson.parse(raw), paths, hashes)) : raw;
            Path destination = paths.get(text(file, "path")); write(destination, output); installed.put(destination, output); hashes.put(digest, sha(output));
        }
        return new Relocated(RetainedJson.object(project(v(row, "plan"), paths, hashes)), project(v(row, "expected"), paths, hashes),
                root.resolve("state"), Map.copyOf(installed));
    }
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
}
