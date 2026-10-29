package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.Digest;
import org.xar.ck3.control.build.SdkSourceAssembly.SourceRole;
import org.xar.ck3.control.build.SdkSourceIntent.Cohort;
import org.xar.ck3.control.build.SdkSourceIntent.Plan;
import org.xar.ck3.control.build.SdkSourceIntent.ReferenceInputs;
import org.xar.ck3.control.build.SdkSourceIntent.RequiredReactorSource;
import org.xar.ck3.control.build.SdkSourceIntent.Selection;
import org.xar.ck3.control.build.SdkSourceIntent.SelectionKind;
import org.xar.ck3.control.build.SdkSourceIntentSuccessor.ReactorUpdate;
import org.xar.ck3.control.build.SdkSourceIntentSuccessor.Request;
import org.xar.ck3.control.build.SdkSourceIntentSuccessor.DataReviewScope;

/** Pure source metadata transitions only; these fixtures cannot qualify a runtime or a game. */
final class SdkSourceIntentSuccessorTest {
    @TempDir Path temporary;

    @Test void actualNewReactorLeafPreservesEveryUnrelatedSourceAndOldReview() throws Exception {
        Plan old = plan(); FileRef fresh = file("new-java-source.txt", "actual source bytes\n");
        Request request = request(old, List.of(new ReactorUpdate(null, "application/src/main/java/example/New.java", fresh)));
        Plan next = SdkSourceIntentSuccessor.apply(old, request);
        assertEquals("2026-10-25T10:29:30Z", old.reviewAtUtc());
        assertEquals("2026-10-25T22:00:00Z", next.reviewAtUtc());
        assertEquals(old.baselineTemplateRef(), next.baselineTemplateRef());
        assertEquals(old.legacyTemplateRef(), next.legacyTemplateRef());
        assertEquals(old.consumerTemplateRef(), next.consumerTemplateRef());
        assertEquals(old.referenceInputs(), next.referenceInputs());
        assertEquals(old.consumerSelections(), next.consumerSelections());
        assertEquals(old.cohorts(), next.cohorts());
        assertEquals(old.requiredReactorSources().getFirst(), next.requiredReactorSources().getFirst());
        assertEquals(new RequiredReactorSource("application/src/main/java/example/New.java",
                new Digest(fresh.bytes(), fresh.sha256())), next.requiredReactorSources().getLast());
        assertEquals(request, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(request), Request.class));
        assertEquals(next, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(next), Plan.class));
    }

    @Test void changedPreimageDuplicateTargetAndNoOpCannotHideUnmigratedCallers() throws Exception {
        Plan old = plan(); RequiredReactorSource before = old.requiredReactorSources().getFirst();
        FileRef fresh = file("replacement.txt", "new genuine source bytes\n");
        ReactorUpdate wrong = new ReactorUpdate(null, before.relativePath(), fresh);
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntentSuccessor.apply(old, request(old, List.of(wrong))));
        ReactorUpdate valid = new ReactorUpdate(before, before.relativePath(), fresh);
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntentSuccessor.apply(old, request(old, List.of(valid, valid))));
        FileRef same = old.consumerSelections().getFirst().selectedSource();
        ReactorUpdate noOp = new ReactorUpdate(before, before.relativePath(), same);
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntentSuccessor.apply(old, request(old, List.of(noOp))));
        assertThrows(IllegalArgumentException.class, () -> new Request(SdkSourceIntentSuccessor.SCHEMA, old.machineId(),
                "2026-10-25T22:00:00Z", same, same, List.of(), List.of(), List.of()));
    }

    @Test void strictRequestCodecRejectsUnknownMissingAndBooleanRefBytes() throws Exception {
        Plan old = plan(); FileRef fresh = file("codec.txt", "strict source fixture\n");
        Request request = request(old, List.of(new ReactorUpdate(null, "application/src/main/java/example/Codec.java", fresh)));
        var original = ControlBuild.strictMapper().valueToTree(request);
        var unknown = original.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) unknown).put("current_or_native_qualification", true);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(unknown, Request.class));
        var missing = original.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) missing).remove("review_authority_ref");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(missing, Request.class));
        var wrongBytes = original.deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode) wrongBytes.path("reactor_updates").get(0).path("selected_source")).put("bytes", true);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(wrongBytes, Request.class));
    }

    @Test void sourceIdentityListPreservesOriginalObjectsAndRejectsCanonicalConflicts() throws Exception {
        Plan old = plan(); FileRef fresh = file("refs.txt", "reference fixture\n");
        Request request = request(old, List.of(new ReactorUpdate(null, "application/src/main/java/example/Refs.java", fresh)));
        List<FileRef> refs = SdkSourceIntentSuccessor.inputRefs(request);
        assertEquals(request.predecessorRef(), refs.getFirst());
        assertEquals(fresh, refs.getLast());
        FileRef conflicting = new FileRef(fresh.path(), fresh.bytes() + 1, fresh.sha256());
        Request drift = request(old, List.of(new ReactorUpdate(null, "application/src/main/java/example/First.java", fresh),
                new ReactorUpdate(null, "application/src/main/java/example/Second.java", conflicting)));
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntentSuccessor.inputRefs(drift));
    }

    @Test void metadataWriteDeadlineCannotBeConfusedWithStaticDataReview() throws Exception {
        Plan old = plan(); FileRef fresh = file("review.txt", "bounded metadata fixture\n");
        Request request = request(old, List.of(new ReactorUpdate(null, "application/src/main/java/example/Review.java", fresh)));
        DataReviewScope authority = scope(old.consumerSelections().getFirst().selectedSource());
        SdkSourceIntentSuccessor.requireReview(request, authority, Instant.parse("2026-10-25T12:00:00Z"));
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntentSuccessor.requireReview(request, authority,
                Instant.parse("2026-10-25T13:00:00Z")));
        Request tooLate = new Request(request.schema(), request.machineId(), "2026-10-25T22:00:01Z", request.predecessorRef(),
                request.reviewAuthorityRef(), request.selectionUpdates(), request.reactorUpdates(), request.cohortUpdates());
        assertThrows(IllegalArgumentException.class, () -> SdkSourceIntentSuccessor.requireReview(tooLate, authority,
                Instant.parse("2026-10-25T12:00:00Z")));
        assertEquals(authority, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(authority), DataReviewScope.class));
    }

    private Plan plan() throws IOException {
        FileRef source = file("original.txt", "original metadata fixture\n");
        Selection selection = new Selection(SelectionKind.ADD_SOURCE, "sdk-fixture", "fixtures/original.json",
                SourceRole.SUPPORT_RESOURCE, null, source, List.of(), List.of());
        Cohort cohort = new Cohort("sdk-fixture", List.of(selection.relativePath()), List.of(selection.relativePath()),
                List.of(selection.relativePath()), List.of(source));
        return new Plan(SdkSourceIntent.PLAN_SCHEMA, "fixture-machine", "2026-10-25T10:29:30Z", source, source, source,
                new ReferenceInputs(List.of(), List.of()), List.of(selection), List.of(cohort),
                List.of(new RequiredReactorSource("application/src/main/java/example/Original.java", new Digest(source.bytes(), source.sha256()))));
    }
    private Request request(Plan predecessor, List<ReactorUpdate> updates) throws IOException {
        FileRef plan = file("predecessor.json", new String(ControlBuild.strictMapper().writeValueAsBytes(predecessor), StandardCharsets.UTF_8));
        FileRef authority = file("pure-metadata-authority-fixture.json", new String(ControlBuild.strictMapper().writeValueAsBytes(
                scope(predecessor.consumerSelections().getFirst().selectedSource())), StandardCharsets.UTF_8));
        return new Request(SdkSourceIntentSuccessor.SCHEMA, predecessor.machineId(), "2026-10-25T22:00:00Z", plan, authority,
                List.of(), updates, List.of());
    }
    private DataReviewScope scope(FileRef source) {
        return new DataReviewScope("xar.root.sdk-static-intent-data-review/v1", "fixture-machine", "/root", "/root/sdk_current",
                "2026-10-25T10:00:00Z", source, source, "2026-10-25T13:00:00Z", "2026-10-25T22:00:00Z", false,
                "Pure source metadata fixture; no execution authority.", "Writing and data review remain separate.", "No funding or physical credit.");
    }
    private FileRef file(String name, String contents) throws IOException {
        ProjectStoragePolicy.requireBulkOutput(temporary);
        Path path = temporary.resolve(name); byte[] body = contents.getBytes(StandardCharsets.UTF_8);
        if (Files.exists(path)) {
            if (!java.util.Arrays.equals(body, Files.readAllBytes(path))) throw new IOException("Test fixture attempted to replace different bytes");
        } else Files.write(path, body, java.nio.file.StandardOpenOption.CREATE_NEW);
        return FileRef.measure(path);
    }
}
