package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeCombinedSourceCut.CmakeComposition;
import org.xar.ck3.control.build.NativeCombinedSourceCut.CompositionStep;
import org.xar.ck3.control.build.NativeCombinedSourceCut.CompositionSyntax;
import org.xar.ck3.control.build.NativeCombinedSourceCut.Content;

final class NativeCombinedSourceCutTest {
    @TempDir Path directory;

    @Test void independentOwnerPreimagesComposeThroughTheRealSharedPatchReader() throws IOException {
        String original = "head\nleft\nright\n";
        FileRef base = put("base.txt", original);
        FileRef a = put("a.patch", patch("left", "left_changed"));
        FileRef b = put("b.patch", patch("right", "right_changed"));
        String afterA = "head\nleft_changed\nright\n";
        String isolatedB = "head\nleft\nright_changed\n";
        String finalText = "head\nleft_changed\nright_changed\n";
        FileRef selected = put("selected.txt", finalText);
        FileRef plan = plan(base, selected, List.of(
                step("a", a, original, afterA, original, afterA),
                step("b", b, original, isolatedB, afterA, finalText)));
        assertArrayEquals(finalText.getBytes(StandardCharsets.UTF_8),
                NativeCombinedSourceCut.verifyCmake(plan, new ArrayList<>(), new HashSet<>()));
    }

    @Test void aChangedCompositeCannotBorrowAnOriginalOwnersWholePreimage() throws IOException {
        String original = "head\nleft\nright\n";
        FileRef base = put("base.txt", original);
        FileRef a = put("a.patch", patch("left", "left_changed"));
        FileRef b = put("b.patch", patch("right", "right_changed"));
        String afterA = "head\nleft_changed\nright\n";
        String finalText = "head\nleft_changed\nright_changed\n";
        FileRef selected = put("selected.txt", finalText);
        FileRef plan = plan(base, selected, List.of(
                step("a", a, original, afterA, original, afterA),
                step("b", b, original, "head\nleft\nright_changed\n", original, finalText)));
        assertThrows(IOException.class, () -> NativeCombinedSourceCut.verifyCmake(plan, new ArrayList<>(), new HashSet<>()));
    }

    @Test void matchingMoreThanOneContextNeverSelectsAnOffset() throws IOException {
        String original = "same\nsame\n";
        FileRef base = put("base.txt", original);
        FileRef patch = put("ambiguous.patch", patch("same", "changed"));
        FileRef selected = put("selected.txt", "changed\nsame\n");
        FileRef plan = plan(base, selected, List.of(step("ambiguous", patch, original,
                "changed\nsame\n", original, "changed\nsame\n")));
        assertThrows(IOException.class, () -> NativeCombinedSourceCut.verifyCmake(plan, new ArrayList<>(), new HashSet<>()));
    }

    @Test void anExactAppendCanBecomeTheNextDeclaredSourcePreimage() throws IOException {
        String original = "head\n";
        FileRef base = put("base.txt", original);
        String afterAppend = "head\ntail\n";
        FileRef patch = put("tail.patch", patch("tail", "tail_changed"));
        String finalText = "head\ntail_changed\n";
        FileRef selected = put("selected.txt", finalText);
        CompositionStep append = new CompositionStep("append", CompositionSyntax.APPEND_EXACT, null, null,
                null, null, content(original), content(afterAppend), null, "tail\n");
        FileRef plan = plan(base, selected, List.of(append,
                step("tail", patch, afterAppend, finalText, afterAppend, finalText)));
        assertArrayEquals(finalText.getBytes(StandardCharsets.UTF_8),
                NativeCombinedSourceCut.verifyCmake(plan, new ArrayList<>(), new HashSet<>()));
    }

    private FileRef plan(FileRef base, FileRef selected, List<CompositionStep> steps) throws IOException {
        var plan = new CmakeComposition("xar.native-cmake-strict-composition/v1", WindowsJobProcess.currentMachineId(),
                "TEST_COMPLETE_BODY", base, steps, selected, "OFF");
        Path output = directory.resolve("plan.json");
        Files.write(output, RootNativePlanJson.mapper().writeValueAsBytes(plan)); return FileRef.measure(output);
    }
    private static CompositionStep step(String id, FileRef patch, String original, String isolated, String parent, String next) {
        return new CompositionStep(id, CompositionSyntax.UNIFIED_DIFF, "CMakeLists.txt", patch,
                content(original), content(isolated), content(parent), content(next), "Exact test owner source", null);
    }
    private FileRef put(String name, String value) throws IOException {
        Path output = directory.resolve(name); Files.writeString(output, value); return FileRef.measure(output);
    }
    private static String patch(String from, String to) {
        return "--- a/CMakeLists.txt\n+++ b/CMakeLists.txt\n@@ -1,1 +1,1 @@\n-" + from + "\n+" + to + "\n";
    }
    private static Content content(String value) {
        byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
        try { return new Content(bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
