package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.*;
import org.xar.ck3.control.build.SdkSourceIntent.*;

final class SdkSourceIntentTest {
    @TempDir Path temporary;
    private static final String PRODUCER = "tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py";
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private FileRef write(String name, Object value) throws IOException {
        Path path = temporary.resolve(name); Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value)); return FileRef.measure(path);
    }
    private Request fixture() throws IOException {
        Path repository = Files.createDirectories(temporary.resolve("repository"));
        Path sdk = Files.createDirectories(repository.resolve("ck3_autonomous_player/src"));
        Path source = Files.writeString(sdk.resolve("sample.py"), "original = 1\n");
        Path producer = repository.resolve(PRODUCER); Files.createDirectories(producer.getParent()); Files.writeString(producer, "def compose_v1(): pass\n");
        return new Request(SdkSourceAssembly.REQUEST_SCHEMA, "fixture-machine", repository.toString(), "a".repeat(40), repository.toString(),
                temporary.resolve("future-view").toString(), sdk.toString(), "ck3_autonomous_player/src", List.of(".", "ck3_autonomous_player/src"),
                List.of(repository.toString()), List.of(new ProtectedRoot(ProtectedRole.FROZEN_SDK, sdk.toString()),
                new ProtectedRoot(ProtectedRole.FROZEN_HOST, temporary.resolve("host").toString()), new ProtectedRoot(ProtectedRole.FROZEN_RUNTIME, temporary.resolve("runtime").toString())),
                List.of(new Source("ck3_autonomous_player/src/sample.py", SourceRole.SDK_SOURCE, InputOrigin.CURRENT_CANONICAL, FileRef.measure(source), List.of()),
                        new Source(PRODUCER, SourceRole.PRODUCER, InputOrigin.CURRENT_CANONICAL, FileRef.measure(producer), List.of())),
                List.of(new ImportRoute("tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", PRODUCER, ImportSourceLocation.FRESH_GRAPH, true)),
                List.of(new Deployment("fixture", FileRef.measure(producer), ControlBuild.TargetKind.SERVICE_FAST_JAR)),
                new ProducerReuse(PRODUCER, "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1", "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1"), 1 << 20);
    }
    private Plan plan(FileRef template, List<Selection> selections, List<Cohort> cohorts) {
        return new Plan(SdkSourceIntent.PLAN_SCHEMA, "fixture-machine", Instant.now().plusSeconds(3600).toString(), template, template, template, new ReferenceInputs(List.of(), List.of()), selections, cohorts,
                List.of(new RequiredReactorSource("module/Actual.java", Digest.of(utf8("paired Java source\n")))));
    }
    @Test void exactPatchReplaysChangedDistantLinesAndRetainsSurroundingBytes() throws Exception {
        byte[] old = utf8("first\na\nb\nc\nd\ne\nf\ng\nlast\n"), desired = utf8("first\nchanged\nb\nc\nd\ne\nf\nnew\nlast\n");
        byte[] patch = SdkSourceIntent.exactPatch("tools/actual.py", old, desired);
        assertArrayEquals(desired, ExactSourcePatch.apply(old, patch, ExactSourcePatch.Syntax.UNIFIED_DIFF, "tools/actual.py").bytes());
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(old, patch, ExactSourcePatch.Syntax.UNIFIED_DIFF, "wrong.py"));
    }
    @Test void exactPatchPreservesCrlfAndMissingFinalNewlineAndRejectsNormalization() throws Exception {
        for (String[] pair : List.of(new String[]{"first\r\nold\r\n", "first\r\nnew\r\n"}, new String[]{"first\nold", "first\nnew"}, new String[]{"old\n", ""})) {
            byte[] old = utf8(pair[0]), desired = utf8(pair[1]);
            assertArrayEquals(desired, ExactSourcePatch.apply(old, SdkSourceIntent.exactPatch("a.py", old, desired), ExactSourcePatch.Syntax.UNIFIED_DIFF, "a.py").bytes());
        }
        assertThrows(IOException.class, () -> SdkSourceIntent.exactPatch("a.py", utf8(""), utf8("new\n")));
        assertThrows(IOException.class, () -> SdkSourceIntent.exactPatch("a.py", utf8("same\r\n"), utf8("same\n")));
        assertThrows(IOException.class, () -> SdkSourceIntent.exactPatch("a.py", utf8("same\n"), utf8("same\n")));
    }
    @Test void realPlanPreservesReferenceViewsAndSelectsOnlyDeclaredConsumerOverlayAndAddition() throws Exception {
        Request before = fixture(); FileRef template = write("template.json", before);
        Source original = before.sources().getFirst(); var witness = SharedSourceFiles.observe(Path.of(original.original().path()));
        FileRef selected = FileRef.measure(Files.writeString(temporary.resolve("selected.py"), "original = 2\n"));
        Path canonicalExtra = Path.of(before.canonicalRepository()).resolve("tools/extra.py"); Files.writeString(canonicalExtra, "value = 3\n");
        FileRef extra = FileRef.measure(canonicalExtra);
        var selections = List.of(new Selection(SelectionKind.REPLACE_CONTENT, "fixture", original.relativePath(), original.role(), original, selected, List.of(), List.of()),
                new Selection(SelectionKind.ADD_SOURCE, "fixture", "tools/extra.py", SourceRole.SUPPORT_RESOURCE, null, extra, List.of(),
                        List.of(new ImportRoute("tools.extra", "tools/extra.py", ImportSourceLocation.FRESH_GRAPH, true))));
        var cohort = new Cohort("fixture", List.of(PRODUCER), List.of(original.relativePath(), "tools/extra.py"), List.of("tools/extra.py"), List.of(template));
        FileRef plan = write("plan.json", plan(template, selections, List.of(cohort)));
        PreparedIntents output = SdkSourceIntent.prepare(plan, temporary.resolve("metadata"), pending -> assertTrue(pending <= 2 << 20));
        assertEquals(before, SdkSourceIntent.resolve(output.baselineIntentRef()).request());
        assertEquals(before, SdkSourceIntent.resolve(output.legacyIntentRef()).request());
        ResolvedIntent consumer = SdkSourceIntent.resolve(output.consumerIntentRef());
        assertEquals(1, consumer.requiredReactorSources().size()); assertTrue(SdkSourceIntent.resolve(output.baselineIntentRef()).requiredReactorSources().isEmpty());
        assertEquals(3, consumer.request().sources().size());
        Source changed = consumer.request().sources().getFirst(); assertEquals(original.original(), changed.original()); assertEquals(original.role(), changed.role());
        assertEquals(Digest.of(utf8("original = 2\n")), changed.overlays().getFirst().standaloneResult());
        Source added = consumer.request().sources().get(2); assertEquals(InputOrigin.STAGED_NEW_SOURCE, added.origin());
        assertFalse(Path.of(added.original().path()).startsWith(Path.of(before.canonicalRepository())));
        assertEquals(extra.sha256(), added.original().sha256()); assertTrue(consumer.inputRefs().contains(selected));
        SharedSourceFiles.assertUnchanged(witness); assertEquals("original = 1\n", Files.readString(Path.of(original.original().path())));
        var mapper = ControlBuild.strictMapper(); assertEquals(output, mapper.readValue(mapper.writeValueAsBytes(output), PreparedIntents.class));
    }
    @Test void exactTemplatePreimageAndCohortClosureMustMatchBeforeAdoption() throws Exception {
        Request before = fixture(); FileRef template = write("template.json", before);
        FileRef desired = FileRef.measure(Files.writeString(temporary.resolve("selected.py"), "different\n"));
        Source old = before.sources().getFirst(); Source wrong = new Source(old.relativePath(), old.role(), old.origin(), desired, List.of());
        var selection = new Selection(SelectionKind.REPLACE_CONTENT, "fixture", old.relativePath(), old.role(), wrong, desired, List.of(), List.of());
        var cohort = new Cohort("fixture", List.of(PRODUCER), List.of(old.relativePath()), List.of(old.relativePath()), List.of(template));
        assertThrows(IOException.class, () -> SdkSourceIntent.prepare(write("wrong-plan.json", plan(template, List.of(selection), List.of(cohort))), temporary.resolve("wrong-out"), pending -> { }));
        var missing = new Cohort("fixture", List.of(PRODUCER), List.of("missing.py"), List.of(old.relativePath()), List.of(template));
        var good = new Selection(SelectionKind.REPLACE_CONTENT, "fixture", old.relativePath(), old.role(), old, desired, List.of(), List.of());
        assertThrows(IOException.class, () -> SdkSourceIntent.prepare(write("missing-plan.json", plan(template, List.of(good), List.of(missing))), temporary.resolve("missing-out"), pending -> { }));
    }
    @Test void originalReferenceIntentCannotHideDeltasOrAcceptExpiredReview() throws Exception {
        Request before = fixture(); FileRef template = write("template.json", before);
        Source added = new Source("new.py", SourceRole.SUPPORT_RESOURCE, InputOrigin.STAGED_NEW_SOURCE, before.sources().getFirst().original(), List.of());
        assertThrows(IllegalArgumentException.class, () -> new Intent(SdkSourceIntent.SCHEMA, "fixture-machine", Instant.now().plusSeconds(3600).toString(), View.BASELINE, template, List.of(), List.of(added), List.of(), List.of(), List.of(), List.of()));
        Intent expired = new Intent(SdkSourceIntent.SCHEMA, "fixture-machine", Instant.now().minusSeconds(1).toString(), View.CONSUMER, template, List.of(), List.of(), List.of(), List.of(), List.of(), List.of());
        assertThrows(IOException.class, () -> SdkSourceIntent.resolve(write("expired.json", expired)));
    }
    @Test void strictIntentJsonRejectsMissingUnknownNullAndWrongPrimitive() throws Exception {
        Request before = fixture(); FileRef template = write("template.json", before);
        Intent value = new Intent(SdkSourceIntent.SCHEMA, "fixture-machine", Instant.now().plusSeconds(3600).toString(), View.CONSUMER, template, List.of(), List.of(), List.of(), List.of(), List.of(), List.of());
        var mapper = ControlBuild.strictMapper(); String encoded = mapper.writeValueAsString(value);
        for (String invalid : List.of(encoded.replace("\"view\":\"CONSUMER\"", "\"view\":null"), encoded.replace("\"view\":\"CONSUMER\",", ""),
                encoded.replace("\"schema\":", "\"unknown\":1,\"schema\":"), encoded.replace("\"bytes\":" + template.bytes(), "\"bytes\":true"), encoded.replace("\"bytes\":" + template.bytes(), "\"bytes\":1.0")))
            assertThrows(Exception.class, () -> mapper.readValue(invalid, Intent.class));
        assertEquals(value, mapper.readValue(encoded, Intent.class));
    }
    @Test void stagedConsumerRolesRoundtripAndRequireExplicitStagedProvenance() throws Exception {
        Request before = fixture(); FileRef file = FileRef.measure(Files.writeString(temporary.resolve("current.py"), "value = 1\n"));
        for (SourceRole role : List.of(SourceRole.STAGED_CONSUMER_TEST, SourceRole.CONSUMER_SOURCE)) {
            Source staged = new Source("tools/current.py", role, InputOrigin.STAGED_NEW_SOURCE, file, List.of());
            var mapper = ControlBuild.strictMapper(); assertEquals(staged, mapper.readValue(mapper.writeValueAsBytes(staged), Source.class));
            OutputSource output = new OutputSource(staged.relativePath(), staged.role(), staged.original());
            assertEquals(output, mapper.readValue(mapper.writeValueAsBytes(output), OutputSource.class));
            SdkSourceAssembly.validateSourceOrigin(before, staged);
            assertThrows(IllegalArgumentException.class, () -> new Source(staged.relativePath(), staged.role(), InputOrigin.CURRENT_CANONICAL, file, List.of()));
            assertThrows(IllegalArgumentException.class, () -> new Source(staged.relativePath(), staged.role(), InputOrigin.FROZEN_SDK_SOURCE, file, List.of()));
        }
    }
    @Test void stagedConsumerRolesKeepOriginalCanonicalAndSdkProductionGuards() throws Exception {
        Request before = fixture(); FileRef external = FileRef.measure(Files.writeString(temporary.resolve("current.py"), "value = 1\n"));
        Source originalOutside = new Source("tools/test_current.py", SourceRole.ORIGINAL_CONSUMER_TEST, InputOrigin.STAGED_NEW_SOURCE, external, List.of());
        assertThrows(IOException.class, () -> SdkSourceAssembly.validateSourceOrigin(before, originalOutside));
        for (SourceRole role : List.of(SourceRole.STAGED_CONSUMER_TEST, SourceRole.CONSUMER_SOURCE)) {
            Source stagedCanonical = new Source("tools/current.py", role, InputOrigin.STAGED_NEW_SOURCE, before.sources().getFirst().original(), List.of());
            assertThrows(IOException.class, () -> SdkSourceAssembly.validateSourceOrigin(before, stagedCanonical));
            Source hiddenProduction = new Source("ck3_autonomous_player/src/current.py", role, InputOrigin.STAGED_NEW_SOURCE, external, List.of());
            assertThrows(IOException.class, () -> SdkSourceAssembly.validateSourceOrigin(before, hiddenProduction));
        }
    }
    @Test void exactPatchSelectionReplaysPinnedOriginalWithoutMaterializingFullPostimage() throws Exception {
        Request before = fixture(); Source original = before.sources().getFirst(); FileRef template = write("template-patch.json", before);
        byte[] desired = utf8("original = 17\n");
        Path patchPath = temporary.resolve("selected.patch");
        Files.write(patchPath, SdkSourceIntent.exactPatch(original.relativePath(), Files.readAllBytes(Path.of(original.original().path())), desired));
        var overlay = new Overlay("fixture", OverlayBase.ORIGINAL_SOURCE, FileRef.measure(patchPath), ExactSourcePatch.Syntax.UNIFIED_DIFF,
                original.relativePath(), new Digest(original.original().bytes(), original.original().sha256()), Digest.of(desired));
        var selection = new Selection(SelectionKind.APPLY_EXACT_PATCH, "fixture", original.relativePath(), original.role(), original, original.original(), List.of(overlay), List.of());
        FileRef planRef = write("plan-patch.json", plan(template, List.of(selection), List.of(new Cohort("fixture", List.of(PRODUCER),
                List.of(original.relativePath()), List.of(original.relativePath()), List.of(template)))));
        var witness = SharedSourceFiles.observe(Path.of(original.original().path()));
        var prepared = SdkSourceIntent.prepare(planRef, temporary.resolve("patch-intents"), pending -> { });
        var resolved = SdkSourceIntent.resolve(prepared.consumerIntentRef()); Source selected = resolved.request().sources().getFirst();
        assertEquals(original.original(), selected.original()); assertEquals(List.of(overlay), selected.overlays());
        assertArrayEquals(desired, ExactSourcePatch.apply(Files.readAllBytes(Path.of(selected.original().path())), Files.readAllBytes(patchPath), overlay.syntax(), selected.relativePath()).bytes());
        SharedSourceFiles.assertUnchanged(witness);
        assertTrue(resolved.inputRefs().contains(overlay.patchRef()));
        FileRef unrelated = FileRef.measure(Files.writeString(temporary.resolve("unrelated.py"), "unrelated\n"));
        assertThrows(IllegalArgumentException.class, () -> new Selection(SelectionKind.APPLY_EXACT_PATCH, "fixture", original.relativePath(), original.role(), original, unrelated, List.of(overlay), List.of()));
        var bad = new Overlay("fixture", OverlayBase.ORIGINAL_SOURCE, overlay.patchRef(), overlay.syntax(), overlay.patchTarget(), overlay.standaloneBase(), new Digest(desired.length, "0".repeat(64)));
        var badSelection = new Selection(SelectionKind.APPLY_EXACT_PATCH, "fixture", original.relativePath(), original.role(), original, original.original(), List.of(bad), List.of());
        FileRef badPlan = write("wrong-patch-plan.json", plan(template, List.of(badSelection), List.of(new Cohort("fixture", List.of(PRODUCER), List.of(original.relativePath()), List.of(original.relativePath()), List.of(template)))));
        assertThrows(IOException.class, () -> SdkSourceIntent.prepare(badPlan, temporary.resolve("bad-patch-intents"), pending -> { }));
    }
    @Test void originalReferenceInputsExtendAllViewsWithoutChangingSdkOrProductionBytes() throws Exception {
        Request before = fixture(); FileRef template = write("reference-template.json", before);
        Path path = Path.of(before.canonicalTestRepository()).resolve("tools/test_reference.py"); Files.writeString(path, "def test_reference(): pass\n");
        var original = new Source("tools/test_reference.py", SourceRole.ORIGINAL_CONSUMER_TEST, InputOrigin.CURRENT_CANONICAL, FileRef.measure(path), List.of());
        var route = new ImportRoute("tools.test_reference", original.relativePath(), ImportSourceLocation.FRESH_GRAPH, false);
        Plan originalPlan = plan(template, List.of(new Selection(SelectionKind.ADD_SOURCE, "fixture", "tools/extra.py", SourceRole.SUPPORT_RESOURCE, null,
                FileRef.measure(Files.writeString(temporary.resolve("extra.py"), "extra\n")), List.of(), List.of())),
                List.of(new Cohort("fixture", List.of(PRODUCER), List.of(original.relativePath()), List.of(PRODUCER), List.of(template))));
        var plan = new Plan(originalPlan.schema(), originalPlan.machineId(), originalPlan.reviewAtUtc(), template, template, template,
                new ReferenceInputs(List.of(original), List.of(route)), originalPlan.consumerSelections(), originalPlan.cohorts(), originalPlan.requiredReactorSources());
        FileRef planRef = write("reference-plan.json", plan);
        var prepared = SdkSourceIntent.prepare(planRef, temporary.resolve("reference-intents"), pending -> { });
        for (FileRef ref : List.of(prepared.baselineIntentRef(), prepared.legacyIntentRef(), prepared.consumerIntentRef())) {
            var resolved = SdkSourceIntent.resolve(ref);
            assertTrue(resolved.request().sources().contains(original)); assertTrue(resolved.request().importRoutes().contains(route));
            assertEquals(before.sources().getFirst(), resolved.request().sources().getFirst()); assertTrue(resolved.inputRefs().contains(original.original()));
        }
        assertThrows(IllegalArgumentException.class, () -> new ReferenceInputs(List.of(before.sources().getFirst()), List.of()));
        var changed = new Source(original.relativePath(), SourceRole.STAGED_CONSUMER_TEST, InputOrigin.STAGED_NEW_SOURCE, original.original(), List.of());
        assertThrows(IllegalArgumentException.class, () -> new ReferenceInputs(List.of(changed), List.of()));
    }
    @Test void coveredCanonicalInputParentsKeepTheFiniteRootGuard() throws Exception {
        Request before = fixture(); FileRef template = write("many-roots-template.json", before);
        Source original = before.sources().getFirst(); var witness = SharedSourceFiles.observe(Path.of(original.original().path()));
        var selected = new ArrayList<Selection>(); var consumers = new ArrayList<String>();
        for (int index = 0; index < 33; index++) {
            String relative = "inputs/branch" + index + "/caller.py"; Path file = Path.of(before.canonicalRepository()).resolve(relative);
            Files.createDirectories(file.getParent()); Files.writeString(file, "value = " + index + "\n");
            selected.add(new Selection(SelectionKind.ADD_SOURCE, "fixture", relative, SourceRole.CONSUMER_SOURCE, null,
                    FileRef.measure(file), List.of(), List.of())); consumers.add(relative);
        }
        var cohort = new Cohort("fixture", List.of(PRODUCER), consumers, List.of(PRODUCER), List.of(template));
        var prepared = SdkSourceIntent.prepare(write("many-roots-plan.json", plan(template, selected, List.of(cohort))),
                temporary.resolve("many-roots-metadata"), pending -> { });
        Request resolved = SdkSourceIntent.resolve(prepared.consumerIntentRef()).request();
        assertEquals(35, resolved.sources().size()); assertEquals(2, resolved.approvedInputSourceRoots().size());
        assertEquals(before.approvedInputSourceRoots().getFirst(), resolved.approvedInputSourceRoots().getFirst());
        for (int index = 0; index < selected.size(); index++) {
            Source staged = resolved.sources().get(index + 2); SdkSourceAssembly.validateSourceOrigin(resolved, staged);
            assertEquals(selected.get(index).selectedSource().sha256(), staged.original().sha256());
            assertFalse(Path.of(staged.original().path()).startsWith(Path.of(before.canonicalRepository())));
        }
        var outside = new ArrayList<Selection>();
        for (int index = 0; index < 33; index++) {
            Path file = temporary.resolve("uncovered/branch" + index + "/caller.py"); Files.createDirectories(file.getParent());
            Files.writeString(file, "outside\n"); String relative = consumers.get(index);
            outside.add(new Selection(SelectionKind.ADD_SOURCE, "fixture", relative, SourceRole.CONSUMER_SOURCE, null,
                    FileRef.measure(file), List.of(), List.of()));
        }
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntent.prepare(
                write("uncovered-roots-plan.json", plan(template, outside, List.of(cohort))),
                temporary.resolve("uncovered-roots-metadata"), pending -> { }));
        SharedSourceFiles.assertUnchanged(witness);
    }
    @Test void canonicalOriginalAdditionsKeepTheirExactOriginWhileStagedTestsUseSeparateCopies() throws Exception {
        Request before = fixture(); FileRef template = write("original-add-template.json", before);
        String relative = "tools/test_original.py";
        Path canonical = Path.of(before.canonicalTestRepository()).resolve(relative);
        Files.writeString(canonical, "def test_original(): pass\n");
        FileRef originalRef = FileRef.measure(canonical);
        var original = new Selection(SelectionKind.ADD_SOURCE, "fixture", relative, SourceRole.ORIGINAL_CONSUMER_TEST,
                null, originalRef, List.of(), List.of(new ImportRoute("tools.test_original", relative, ImportSourceLocation.FRESH_GRAPH, true)));
        var staged = new Selection(SelectionKind.ADD_SOURCE, "fixture", "tools/test_adapted.py", SourceRole.STAGED_CONSUMER_TEST,
                null, originalRef, List.of(), List.of());
        var cohort = new Cohort("fixture", List.of(PRODUCER), List.of(relative, staged.relativePath()),
                List.of(PRODUCER), List.of(template));
        var prepared = SdkSourceIntent.prepare(write("original-add-plan.json", plan(template, List.of(original, staged), List.of(cohort))),
                temporary.resolve("original-add-metadata"), pending -> { });
        assertEquals(before, SdkSourceIntent.resolve(prepared.baselineIntentRef()).request());
        assertEquals(before, SdkSourceIntent.resolve(prepared.legacyIntentRef()).request());
        var resolved = SdkSourceIntent.resolve(prepared.consumerIntentRef());
        Source kept = resolved.request().sources().get(2), copied = resolved.request().sources().get(3);
        assertEquals(SourceRole.ORIGINAL_CONSUMER_TEST, kept.role());
        assertEquals(InputOrigin.CURRENT_CANONICAL, kept.origin()); assertEquals(originalRef, kept.original());
        assertTrue(kept.overlays().isEmpty()); assertTrue(resolved.inputRefs().contains(originalRef));
        assertEquals(SourceRole.STAGED_CONSUMER_TEST, copied.role()); assertEquals(InputOrigin.STAGED_NEW_SOURCE, copied.origin());
        assertFalse(Path.of(copied.original().path()).startsWith(Path.of(before.canonicalRepository())));
        assertEquals(originalRef.sha256(), copied.original().sha256());
        SdkSourceAssembly.validateSourceOrigin(resolved.request(), kept);
        SdkSourceAssembly.validateSourceOrigin(resolved.request(), copied);
        var mapper = ControlBuild.strictMapper();
        assertEquals(kept, mapper.readValue(mapper.writeValueAsBytes(kept), Source.class));
        FileRef outside = FileRef.measure(Files.writeString(temporary.resolve("test_outside.py"), "outside\n"));
        for (var invalid : List.of(
                new Selection(SelectionKind.ADD_SOURCE, "fixture", relative, SourceRole.ORIGINAL_CONSUMER_TEST,
                        null, outside, List.of(), List.of()),
                new Selection(SelectionKind.ADD_SOURCE, "fixture", "tools/not_a_test.py", SourceRole.ORIGINAL_CONSUMER_TEST,
                        null, originalRef, List.of(), List.of()))) {
            Path rejected = temporary.resolve("original-add-rejected-" + invalid.selectedSource().bytes());
            assertThrows(IOException.class, () -> SdkSourceIntent.prepare(write("invalid-" + invalid.selectedSource().bytes() + ".json",
                    plan(template, List.of(invalid), List.of(cohort))), rejected, pending -> { }));
            assertFalse(Files.exists(rejected));
        }
        assertEquals("def test_original(): pass\n", Files.readString(canonical));
    }
}
