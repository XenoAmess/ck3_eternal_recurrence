package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ExactSourcePatch.Syntax;
import org.xar.ck3.control.build.SdkSourceAssembly.Digest;

/** Finite patch and wire regressions; no SDK imports, host, Driver, SAVE or Game. */
final class SdkSourceAssemblyTest {
    @TempDir Path temporary;
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }

    @Test void appliesActualArmyStyleMultiFileDiffToOnlyTheSelectedLeaf() throws IOException {
        String patch = "--- a/sdk/a.py\n+++ b/sdk/a.py\n@@ -1,2 +1,3 @@\n first\n-old\n+new\n+tail\n"
                + "--- a/sdk/b.py\n+++ b/sdk/b.py\n@@ -1 +1 @@\n-other\n+changed\n";
        ExactSourcePatch.Result result = ExactSourcePatch.apply(bytes("first\nold\n"), bytes(patch), Syntax.UNIFIED_DIFF, "sdk/a.py");
        assertArrayEquals(bytes("first\nnew\ntail\n"), result.bytes());
        assertEquals(1, result.hunks());
        assertEquals(1, result.selectedFileSections());
    }
    @Test void appliesActualConsumerStyleCodexHunkWithoutCreatingAnotherGenerator() throws IOException {
        String patch = "*** Begin Patch\n*** Update File: tools/owner.py\n@@\n-def load():\n- reader=Local()\n+def load(reader=None):\n+ reader=Local() if reader is None else reader\n*** End Patch\n";
        assertArrayEquals(bytes("start\ndef load(reader=None):\n reader=Local() if reader is None else reader\nend\n"),
                ExactSourcePatch.apply(bytes("start\ndef load():\n reader=Local()\nend\n"), bytes(patch), Syntax.CODEX_UPDATE, "tools/owner.py").bytes());
    }
    @Test void preservesCrlfAndUnchangedByteContent() throws IOException {
        String patch = "--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n keep\n-old\n+new\n";
        assertArrayEquals(bytes("keep\r\nnew\r\n"), ExactSourcePatch.apply(bytes("keep\r\nold\r\n"), bytes(patch), Syntax.UNIFIED_DIFF, "a.py").bytes());
    }
    @Test void preservesExplicitNoNewlineAtEndOfFile() throws IOException {
        String patch = "--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old\n\\ No newline at end of file\n+new\n\\ No newline at end of file\n";
        assertArrayEquals(bytes("new"), ExactSourcePatch.apply(bytes("old"), bytes(patch), Syntax.UNIFIED_DIFF, "a.py").bytes());
    }
    @Test void acceptsQuotedWindowsGitOldHeaderFromPreparedLane() throws IOException {
        String patch = "--- \"a/tools\\\\g2_saved_campaign\\\\owner.py\"\n+++ \"b/D:\\\\stage\\\\owner.py\"\n@@ -1 +1 @@\n-old\n+new\n";
        assertArrayEquals(bytes("new\n"), ExactSourcePatch.apply(bytes("old\n"), bytes(patch), Syntax.UNIFIED_DIFF, "tools/g2_saved_campaign/owner.py").bytes());
    }
    @Test void absoluteDiffHeaderRequiresItsExplicitFullIdentityAndNeverSelectsAnOutputPath() throws IOException {
        String patch = "--- a/D:/stage/base/owner.py\n+++ b/D:/stage/result/owner.py\n@@ -1 +1 @@\n-old\n+new\n";
        assertArrayEquals(bytes("new\n"), ExactSourcePatch.apply(bytes("old\n"), bytes(patch), Syntax.UNIFIED_DIFF, "D:/stage/base/owner.py").bytes());
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(bytes("old\n"), bytes(patch), Syntax.UNIFIED_DIFF, "owner.py"));
    }
    @Test void rejectsAmbiguousContextInsteadOfGuessingAnOffset() {
        String patch = "*** Begin Patch\n*** Update File: a.py\n@@\n-old\n+new\n*** End Patch\n";
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(bytes("old\nold\n"), bytes(patch), Syntax.CODEX_UPDATE, "a.py"));
    }
    @Test void rejectsChangedBaseMissingTargetAndTruncatedCounts() {
        String valid = "--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old\n+new\n";
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(bytes("drift\n"), bytes(valid), Syntax.UNIFIED_DIFF, "a.py"));
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(bytes("old\n"), bytes(valid), Syntax.UNIFIED_DIFF, "other.py"));
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(bytes("old\n"), bytes(valid.replace("@@ -1 +1 @@", "@@ -1,2 +1 @@")), Syntax.UNIFIED_DIFF, "a.py"));
    }
    @Test void orderedDisjointDomainHunksMergeAndOverlappingChangesReject() throws IOException {
        String first = "*** Begin Patch\n*** Update File: a.py\n@@\n-one\n+first\n*** End Patch\n";
        String second = "*** Begin Patch\n*** Update File: a.py\n@@\n-two\n+second\n*** End Patch\n";
        byte[] once = ExactSourcePatch.apply(bytes("one\ntwo\n"), bytes(first), Syntax.CODEX_UPDATE, "a.py").bytes();
        assertArrayEquals(bytes("first\nsecond\n"), ExactSourcePatch.apply(once, bytes(second), Syntax.CODEX_UPDATE, "a.py").bytes());
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(once, bytes(first), Syntax.CODEX_UPDATE, "a.py"));
    }
    @Test void sourcePatchResultDefensivelyCopiesBytes() throws IOException {
        byte[] output = bytes("hello");
        ExactSourcePatch.Result result = new ExactSourcePatch.Result(output, 1, 1);
        output[0] = 0;
        byte[] exposed = result.bytes(); exposed[1] = 0;
        assertArrayEquals(bytes("hello"), result.bytes());
    }
    @Test void malformedUtf8AndIncompleteCodexPatchReject() {
        String patch = "*** Begin Patch\n*** Update File: a.py\n@@\n-old\n+new\n";
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(bytes("old\n"), bytes(patch), Syntax.CODEX_UPDATE, "a.py"));
        assertThrows(IOException.class, () -> ExactSourcePatch.apply(new byte[]{(byte) 0xc3, 0x28}, bytes(patch + "*** End Patch\n"), Syntax.CODEX_UPDATE, "a.py"));
    }
    @Test void exactDigestJsonRoundtripRejectsBoolFloatUnknownMissingAndNull() throws Exception {
        var mapper = ControlBuild.strictMapper();
        Digest expected = Digest.of(bytes("original source\n"));
        assertEquals(expected, mapper.readValue(mapper.writeValueAsBytes(expected), Digest.class));
        for (String raw : List.of(
                "{\"bytes\":true,\"sha256\":\"" + expected.sha256() + "\"}",
                "{\"bytes\":1.0,\"sha256\":\"" + expected.sha256() + "\"}",
                "{\"bytes\":null,\"sha256\":\"" + expected.sha256() + "\"}",
                "{\"sha256\":\"" + expected.sha256() + "\"}",
                "{\"bytes\":1,\"sha256\":null}",
                "{\"bytes\":1,\"sha256\":\"" + expected.sha256() + "\",\"extra\":0}")) {
            assertThrows(Exception.class, () -> mapper.readValue(raw, Digest.class));
        }
    }
    @Test void sourceOverlayContractRoundtripKeepsOriginalAndStandaloneResultDistinct() throws Exception {
        Path original = temporary.resolve("source.py"); Files.write(original, bytes("old\n"));
        Path patch = temporary.resolve("source.patch"); Files.write(patch, bytes("*** Begin Patch\n*** Update File: source.py\n@@\n-old\n+new\n*** End Patch\n"));
        var overlay = new SdkSourceAssembly.Overlay("consumer-warm", SdkSourceAssembly.OverlayBase.ORIGINAL_SOURCE, FileRef.measure(patch), Syntax.CODEX_UPDATE, "source.py", Digest.of(bytes("old\n")), Digest.of(bytes("new\n")));
        var source = new SdkSourceAssembly.Source("source.py", SdkSourceAssembly.SourceRole.SHARED_TRANSPORT,
                SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, FileRef.measure(original), List.of(overlay));
        var mapper = ControlBuild.strictMapper();
        assertEquals(source, mapper.readValue(mapper.writeValueAsBytes(source), SdkSourceAssembly.Source.class));
        JsonNode wire = mapper.valueToTree(source);
        ((ObjectNode) wire).remove("overlays");
        assertThrows(Exception.class, () -> mapper.treeToValue(wire, SdkSourceAssembly.Source.class));
    }
    @Test void noAlternativePackagerOrAssemblyQualificationCanBeConstructed() {
        assertThrows(IllegalArgumentException.class, () -> new SdkSourceAssembly.ProducerReuse("other.py", "other", "compose", "owner", "check"));
        var actual = new SdkSourceAssembly.ProducerReuse("tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py",
                "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1",
                "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1");
        assertEquals("compose_v1", actual.callable());
        assertFalse(SdkSourceAssembly.AssemblyStatus.SOURCE_ASSEMBLED_NOT_IMPORTED.name().contains("QUALIFIED"));
    }
    @Test void consumerAtomicReplacementPreservesRealBaselineAndLegacyHardlinkBytesAndIdentity() throws IOException {
        Path baseline = temporary.resolve("baseline/source.py"), legacy = temporary.resolve("legacy/source.py"), consumer = temporary.resolve("consumer/source.py");
        Files.createDirectories(baseline.getParent()); Files.write(baseline, bytes("original\n"));
        SharedSourceFiles.Witness base = SharedSourceFiles.observe(baseline);
        SharedSourceFiles.Witness old = SharedSourceFiles.link(baseline, legacy);
        SharedSourceFiles.Witness linked = SharedSourceFiles.link(baseline, consumer);
        Path privateRoot = consumer.getParent().resolve(".assembly"); Files.createDirectory(privateRoot);
        SharedSourceFiles.Witness changed = SharedSourceFiles.replacePrivate(consumer, privateRoot, bytes("java consumer\n"), List.of(base, old));
        SharedSourceFiles.assertUnchanged(base); SharedSourceFiles.assertUnchanged(old);
        assertEquals("original\n", Files.readString(baseline)); assertEquals("original\n", Files.readString(legacy));
        assertEquals("java consumer\n", Files.readString(consumer));
        assertEquals(base.nativeFile().identityKey(), linked.nativeFile().identityKey());
        assertFalse(changed.nativeFile().identityKey().equals(base.nativeFile().identityKey()));
        assertFalse(Files.isSameFile(consumer, baseline));
        assertEquals(true, Files.isSameFile(baseline, legacy));
        try (var files = Files.list(privateRoot)) { assertEquals(0L, files.count()); }
    }
    @Test void bothFixturePatchesUsePrivateFilesAndLeaveBaselineUnmodified() throws IOException {
        Path baseline = temporary.resolve("base/test_fixture.py"), legacy = temporary.resolve("old/test_fixture.py"), consumer = temporary.resolve("new/test_fixture.py");
        Files.createDirectories(baseline.getParent()); Files.write(baseline, bytes("player=None\n"));
        SharedSourceFiles.Witness base = SharedSourceFiles.observe(baseline);
        SharedSourceFiles.Witness old = SharedSourceFiles.link(baseline, legacy), fresh = SharedSourceFiles.link(baseline, consumer);
        Path oldTemp = legacy.getParent().resolve(".assembly"), newTemp = consumer.getParent().resolve(".assembly"); Files.createDirectory(oldTemp); Files.createDirectory(newTemp);
        byte[] repaired = bytes("player=12345\n");
        SharedSourceFiles.Witness oldFixed = SharedSourceFiles.replacePrivate(legacy, oldTemp, repaired, List.of(base, fresh));
        SharedSourceFiles.Witness newFixed = SharedSourceFiles.replacePrivate(consumer, newTemp, repaired, List.of(base, oldFixed));
        SharedSourceFiles.assertUnchanged(base); SharedSourceFiles.assertUnchanged(oldFixed);
        assertArrayEquals(repaired, Files.readAllBytes(legacy)); assertArrayEquals(repaired, Files.readAllBytes(consumer));
        assertEquals("player=None\n", Files.readString(baseline));
        assertFalse(oldFixed.nativeFile().identityKey().equals(newFixed.nativeFile().identityKey()));
    }
    @Test void nativeSourceAllocationCensusCountsHardlinkedDataOnlyOnce() throws IOException {
        Path baseline = temporary.resolve("baseline/block.py"), legacy = temporary.resolve("legacy/block.py"), consumer = temporary.resolve("consumer/block.py");
        Files.createDirectories(baseline.getParent()); Files.write(baseline, new byte[65536]);
        var base = SharedSourceFiles.observe(baseline); var old = SharedSourceFiles.link(baseline, legacy); var fresh = SharedSourceFiles.link(baseline, consumer);
        var census = SdkSourceAssembly.physicalCensus(Map.of("block.py", base), Map.of("block.py", old), Map.of("block.py", fresh));
        assertEquals(3, census.sourcePaths()); assertEquals(1, census.distinctNativeFiles());
        assertEquals(3L * 65536, census.logicalBytesAcrossAllSourcePaths());
        assertEquals(base.nativeFile().allocatedBytes(), census.nativeUniqueSourceAllocationBytes());
        assertEquals(2 * base.nativeFile().allocatedBytes(), census.nativeDataAllocationAvoidedByLinksBytes());
    }
    @Test void copyOnWriteRefusesProtectedTargetAndEscapeBeforeAnyWrite() throws IOException {
        Path target = temporary.resolve("consumer/source.py"), privateRoot = temporary.resolve("consumer/.assembly"), other = temporary.resolve("other.py");
        Files.createDirectories(privateRoot); Files.write(target, bytes("old\n")); Files.write(other, bytes("protected\n"));
        var before = SharedSourceFiles.observe(target); var protectedOther = SharedSourceFiles.observe(other);
        assertThrows(IOException.class, () -> SharedSourceFiles.replacePrivate(target, privateRoot, bytes("bad\n"), List.of(before)));
        assertThrows(IOException.class, () -> SharedSourceFiles.replacePrivate(other, privateRoot, bytes("bad\n"), List.of(before)));
        SharedSourceFiles.assertUnchanged(before); SharedSourceFiles.assertUnchanged(protectedOther);
    }
    @Test void existingHardlinkDestinationIsNeverOverwritten() throws IOException {
        Path first = temporary.resolve("first.py"), second = temporary.resolve("second.py");
        Files.write(first, bytes("first\n")); Files.write(second, bytes("second\n"));
        assertThrows(IOException.class, () -> SharedSourceFiles.link(first, second));
        assertEquals("first\n", Files.readString(first)); assertEquals("second\n", Files.readString(second));
    }
    @Test void selectedImportRouteUsesExplicitPhysicalReferenceInsteadOfRelativePathPriority() throws Exception {
        Path fresh = temporary.resolve("fresh/test_original.py"), canonical = temporary.resolve("canonical/test_original.py");
        Files.createDirectories(fresh.getParent()); Files.createDirectories(canonical.getParent()); Files.write(fresh, bytes("fresh\n")); Files.write(canonical, bytes("canonical\n"));
        var selected = new SdkSourceAssembly.SelectedImportRoute("test_original", "test_original.py", SdkSourceAssembly.ImportSourceLocation.FRESH_GRAPH, FileRef.measure(fresh), true);
        var mapper = ControlBuild.strictMapper();
        assertEquals(selected, mapper.readValue(mapper.writeValueAsBytes(selected), SdkSourceAssembly.SelectedImportRoute.class));
        ObjectNode malformed = mapper.valueToTree(selected); malformed.remove("physical_ref");
        assertThrows(Exception.class, () -> mapper.treeToValue(malformed, SdkSourceAssembly.SelectedImportRoute.class));
        assertFalse(selected.physicalRef().equals(FileRef.measure(canonical)));
    }
    @Test void independentDomainChainUsesItsExplicitPreviousOwnerResultDespiteOtherDomains() throws IOException {
        Path original = temporary.resolve("source.py"); Files.write(original, bytes("one\ntwo\n"));
        Path first = temporary.resolve("one.patch"), unrelated = temporary.resolve("two.patch"), amendment = temporary.resolve("amend.patch");
        Files.write(first, bytes("*** Begin Patch\n*** Update File: source.py\n@@\n-one\n+first\n*** End Patch\n"));
        Files.write(unrelated, bytes("*** Begin Patch\n*** Update File: source.py\n@@\n-two\n+other\n*** End Patch\n"));
        Files.write(amendment, bytes("*** Begin Patch\n*** Update File: source.py\n@@\n-first\n+final\n*** End Patch\n"));
        var firstPatch = new SdkSourceAssembly.Overlay("timeline", SdkSourceAssembly.OverlayBase.ORIGINAL_SOURCE, FileRef.measure(first), Syntax.CODEX_UPDATE, "source.py", Digest.of(bytes("one\ntwo\n")), Digest.of(bytes("first\ntwo\n")));
        var otherPatch = new SdkSourceAssembly.Overlay("deadline", SdkSourceAssembly.OverlayBase.ORIGINAL_SOURCE, FileRef.measure(unrelated), Syntax.CODEX_UPDATE, "source.py", Digest.of(bytes("one\ntwo\n")), Digest.of(bytes("one\nother\n")));
        var amendPatch = new SdkSourceAssembly.Overlay("timeline", SdkSourceAssembly.OverlayBase.PREVIOUS_SAME_OWNER_RESULT, FileRef.measure(amendment), Syntax.CODEX_UPDATE, "source.py", Digest.of(bytes("first\ntwo\n")), Digest.of(bytes("final\ntwo\n")));
        var source = new SdkSourceAssembly.Source("source.py", SdkSourceAssembly.SourceRole.SHARED_TRANSPORT, SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, FileRef.measure(original), List.of(firstPatch, otherPatch, amendPatch));
        assertArrayEquals(bytes("final\ntwo\n"), SdkSourceAssembly.standaloneMaterial(source, Files.readAllBytes(original), 2));
        var missing = new SdkSourceAssembly.Source("source.py", source.role(), source.origin(), source.original(), List.of(amendPatch));
        assertThrows(IOException.class, () -> SdkSourceAssembly.standaloneMaterial(missing, Files.readAllBytes(original), 0));
    }
    @Test void reusedBaselineAndTwoViewsPreserveFrozenShaNativeBirthAndMtimeAcrossConsumerCow() throws IOException {
        Path frozen = temporary.resolve("frozen/source.py"), canonical = temporary.resolve("canonical/source.py"), basePath = temporary.resolve("baseline/source.py");
        Files.createDirectories(frozen.getParent()); Files.createDirectories(canonical.getParent()); Files.write(frozen, bytes("original\n")); Files.write(canonical, bytes("original\n"));
        var before = SharedSourceFiles.observe(frozen); var original = FileRef.measure(canonical);
        var source = new SdkSourceAssembly.Source("source.py", SdkSourceAssembly.SourceRole.SDK_SOURCE, SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, original, List.of());
        var reviewed = new SdkSourceAssembly.ReviewedSource(source.relativePath(), source.role(), source.origin(), original, Digest.of(bytes("original\n")), List.of());
        var baseline = SdkSourceAssembly.baselineLeaf(source, reviewed, basePath, Optional.of(before));
        Path oldPath = temporary.resolve("legacy/source.py"), freshPath = temporary.resolve("consumer/source.py"), privateRoot = freshPath.getParent().resolve(".assembly");
        var old = SharedSourceFiles.link(basePath, oldPath); SharedSourceFiles.link(basePath, freshPath); Files.createDirectory(privateRoot);
        SharedSourceFiles.replacePrivate(freshPath, privateRoot, bytes("new consumer\n"), List.of(before, baseline, old));
        SharedSourceFiles.assertUnchanged(before); SharedSourceFiles.assertUnchanged(baseline); SharedSourceFiles.assertUnchanged(old);
        var after = SharedSourceFiles.observe(frozen);
        assertEquals(before.source(), after.source()); assertEquals(before.nativeFile().identityKey(), after.nativeFile().identityKey());
        assertEquals(before.nativeFile().creationFiletimeDecimal(), after.nativeFile().creationFiletimeDecimal());
        assertEquals(before.nativeFile().lastWriteFiletimeDecimal(), after.nativeFile().lastWriteFiletimeDecimal());
        assertEquals(before.nativeFile().linkCount() + 2, after.nativeFile().linkCount());
        assertEquals("original\n", Files.readString(frozen)); assertEquals("new consumer\n", Files.readString(freshPath));
    }
    @Test void changedAndAddedCanonicalBaselineLeavesArePrivateAndMismatchedReuseRejects() throws IOException {
        Path frozen = temporary.resolve("frozen/source.py"), canonical = temporary.resolve("canonical/source.py"), added = temporary.resolve("canonical/added.py");
        Files.createDirectories(frozen.getParent()); Files.createDirectories(canonical.getParent()); Files.write(frozen, bytes("old\n")); Files.write(canonical, bytes("changed\n")); Files.write(added, bytes("added\n"));
        var old = SharedSourceFiles.observe(frozen);
        for (Path input : List.of(canonical, added)) {
            FileRef original = FileRef.measure(input); String relative = input.getFileName().toString();
            var source = new SdkSourceAssembly.Source(relative, SdkSourceAssembly.SourceRole.SDK_SOURCE, SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, original, List.of());
            var reviewed = new SdkSourceAssembly.ReviewedSource(relative, source.role(), source.origin(), original, new Digest(original.bytes(), original.sha256()), List.of());
            assertThrows(IOException.class, () -> SdkSourceAssembly.baselineLeaf(source, reviewed, temporary.resolve("wrong/" + relative), Optional.of(old)));
            var result = SdkSourceAssembly.baselineLeaf(source, reviewed, temporary.resolve("private/" + relative), Optional.empty());
            assertFalse(result.nativeFile().identityKey().equals(old.nativeFile().identityKey()));
            assertFalse(Files.isSameFile(input, Path.of(result.source().path()))); assertArrayEquals(Files.readAllBytes(input), Files.readAllBytes(Path.of(result.source().path())));
        }
        SharedSourceFiles.assertUnchanged(old); assertEquals("old\n", Files.readString(frozen));
    }
    @Test void frozenContractRejectsUnreviewedIdentityInvariantsAndNonIntegerSourceLengths() throws Exception {
        var mapper = ControlBuild.strictMapper();
        ObjectNode freeze = mapper.createObjectNode(); freeze.put("source_file_count", 1); freeze.put("source_bytes", 4);
        ObjectNode row = freeze.putArray("files").addObject(); row.put("relative", "a.py"); row.put("bytes", 4); row.put("sha256", Digest.of(bytes("old\n")).sha256()); row.put("git_blob_sha1", "0".repeat(40)); row.put("git_mode", "100644");
        assertEquals(1, SdkSourceAssembly.frozenRows(freeze).size());
        row.put("links", 2); assertThrows(IOException.class, () -> SdkSourceAssembly.frozenRows(freeze)); row.remove("links");
        row.put("change_filetime_decimal", "123"); assertThrows(IOException.class, () -> SdkSourceAssembly.frozenRows(freeze)); row.remove("change_filetime_decimal");
        row.put("bytes", 4.0); assertThrows(IOException.class, () -> SdkSourceAssembly.frozenRows(freeze));
        row.put("bytes", true); assertThrows(IOException.class, () -> SdkSourceAssembly.frozenRows(freeze));
    }
    @Test void smallNativeFileLinkKeepsObservedAllocationChangesWithoutInventingBeforeFacts() throws Exception {
        Path original = temporary.resolve("small/CrossJsDecimalUInt64.java");
        Files.createDirectories(original.getParent()); Files.write(original, new byte[536]);
        var first = SharedSourceFiles.observe(original); long growth = 0;
        var changes = new java.util.ArrayList<SharedSourceFiles.LinkResult>();
        for (int index = 0; index < 8; index++) {
            var operation = SharedSourceFiles.linkObserved(original, temporary.resolve("link-" + index + "/CrossJsDecimalUInt64.java"));
            assertEquals(first.source(), operation.before().source());
            assertEquals(first.nativeFile().identityKey(), operation.destinationAfter().nativeFile().identityKey());
            assertEquals(operation.before().nativeFile().linkCount() + 1, operation.sourceAfter().nativeFile().linkCount());
            assertEquals(operation.sourceAfter().nativeFile(), operation.destinationAfter().nativeFile());
            growth = Math.addExact(growth, operation.allocatedGrowthBytes());
            if (operation.before().nativeFile().allocatedBytes() != operation.sourceAfter().nativeFile().allocatedBytes()) changes.add(operation);
        }
        var actual = new SdkSourceAssembly.HardlinkAllocationActual("xar.sdk-hardlink-allocation-actual/v1", "test-machine", java.time.Instant.now().toString(), 8, growth, changes, "Actual Windows observations; no required resident-promotion outcome.");
        var mapper = ControlBuild.strictMapper();
        assertEquals(actual, mapper.readValue(mapper.writeValueAsBytes(actual), SdkSourceAssembly.HardlinkAllocationActual.class));
        SharedSourceFiles.assertUnchanged(first);
        assertEquals(first.nativeFile().linkCount() + 8, SharedSourceFiles.nativeFile(original).linkCount());
        Files.write(original, bytes("changed body\n"));
        assertThrows(IOException.class, () -> SharedSourceFiles.assertUnchanged(first));
    }
}
