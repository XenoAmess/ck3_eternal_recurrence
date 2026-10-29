package org.xar.ck3.control.wave2.events.nativepulse;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;

/** Mandatory original caller/PE/DATA inputs, distinct from a loaded-object observation. */
class NativeScopeBaseAllocatorCapturedTest {
    @Test void actualCallerAndSlotsResolveTargetsWithoutInventingFinalScopeState() throws IOException {
        Path caller = requiredPath("xar.g2.m2.scopebase.caller.path", 184);
        Path pe = requiredPath("xar.g2.m2.scopebase.pe.path", 888);
        Path slots = requiredPath("xar.g2.m2.scopebase.slots.path", 24);
        ExactRef callerRef = new ExactRef(caller.toString(), 184,
                "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
        ExactRef peRef = new ExactRef(pe.toString(), 888,
                "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        ExactRef slotsRef = new ExactRef(slots.toString(), 24,
                "2c4dc362a8e0df15994d4e825fe8392e3f3995d18f8fdcc8eda17b93df426ca4");
        byte[] callerBytes = Files.readAllBytes(caller);
        byte[] peBytes = Files.readAllBytes(pe);
        byte[] slotBytes = Files.readAllBytes(slots);
        var review = NativeScriptMathProgram.reviewScopeBaseAllocator(
                callerRef, callerBytes, peRef, peBytes, slotsRef, slotBytes);
        assertEquals(0x44a2980L, review.installedVtableRva());
        assertEquals(0x855830L, review.slot10TargetRva());
        assertEquals(0x896b80L, review.slot20TargetRva());
        assertFalse(review.virtual10BodyReviewed());
        assertFalse(review.virtual20BodyReviewed());
        assertFalse(review.finalScopeChainKnown());
        assertFalse(review.currentLoadedSourceQualified());
        assertFalse(review.nativeGameExecuted());
        byte[] changed = slotBytes.clone();
        changed[16] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocator(
                callerRef, callerBytes, peRef, peBytes, slotsRef, changed));
    }

    @Test void actualBodiesGiveOnlyReviewedNormalInlineLayoutAndKeepNestedRouteUnknown() throws IOException {
        Retained caller = retained("xar.g2.m2.scopebase.caller.path", 184,
                "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
        Retained pe = retained("xar.g2.m2.scopebase.pe.path", 888,
                "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        Retained slots = retained("xar.g2.m2.scopebase.slots.path", 24,
                "2c4dc362a8e0df15994d4e825fe8392e3f3995d18f8fdcc8eda17b93df426ca4");
        var targets = NativeScriptMathProgram.reviewScopeBaseAllocator(
                caller.source(), caller.raw(), pe.source(), pe.raw(), slots.source(), slots.raw());
        Retained slot10 = retained("xar.g2.m2.scopebase.slot10.body.path", 58,
                "713f21ed3585fdf7d226ebef14cdd488cbe394d4a489fdc3227bea74f126a604");
        Retained unwind = retained("xar.g2.m2.scopebase.slot10.unwind.path", 12,
                "39455c244cd3d4de53471a0adec96067c74300ddc0ba6db9733fe8f8e3a9ffc4");
        Retained slot20 = retained("xar.g2.m2.scopebase.slot20.body.path", 64,
                "09e118536ec763b738f2080016e4fddacdc0b2ca15ad24355b42d8ec00d4098d");
        var bodies = NativeScriptMathProgram.reviewScopeBaseAllocatorBodies(targets,
                slot10.source(), slot10.raw(), unwind.source(), unwind.raw(), slot20.source(), slot20.raw());
        assertEquals(15, bodies.virtual20SemanticBytes());
        assertTrue(bodies.virtual10WholeBodyReviewed());
        assertEquals(0x20, bodies.normalPoststate().dataOffsetFromScopeBaseThis());
        assertEquals(4, bodies.normalPoststate().packedLowDword08());
        assertEquals(0, bodies.normalPoststate().signedCount0C());
        assertTrue(bodies.normalPoststate().scopeChainEmptyOnReviewedNormalReturn());
        assertFalse(bodies.nestedAllocatorRouteClosed());
        assertFalse(bodies.currentLoadedSourceQualified());
        assertFalse(bodies.nativeGameExecuted());
        byte[] changed = unwind.raw().clone();
        changed[2] = 0;
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorBodies(targets,
                slot10.source(), slot10.raw(), unwind.source(), changed, slot20.source(), slot20.raw()));
    }

    @Test void actualSlot38GetterReturnsOnlyTheConstructedGlobalAddress() throws IOException {
        Retained caller = retained("xar.g2.m2.scopebase.caller.path", 184,
                "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
        Retained pe = retained("xar.g2.m2.scopebase.pe.path", 888,
                "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        Retained slots = retained("xar.g2.m2.scopebase.slots.path", 24,
                "2c4dc362a8e0df15994d4e825fe8392e3f3995d18f8fdcc8eda17b93df426ca4");
        var targets = NativeScriptMathProgram.reviewScopeBaseAllocator(
                caller.source(), caller.raw(), pe.source(), pe.raw(), slots.source(), slots.raw());
        Retained slot10 = retained("xar.g2.m2.scopebase.slot10.body.path", 58,
                "713f21ed3585fdf7d226ebef14cdd488cbe394d4a489fdc3227bea74f126a604");
        Retained unwind = retained("xar.g2.m2.scopebase.slot10.unwind.path", 12,
                "39455c244cd3d4de53471a0adec96067c74300ddc0ba6db9733fe8f8e3a9ffc4");
        Retained slot20 = retained("xar.g2.m2.scopebase.slot20.body.path", 64,
                "09e118536ec763b738f2080016e4fddacdc0b2ca15ad24355b42d8ec00d4098d");
        var bodies = NativeScriptMathProgram.reviewScopeBaseAllocatorBodies(targets,
                slot10.source(), slot10.raw(), unwind.source(), unwind.raw(), slot20.source(), slot20.raw());
        Retained slot38 = retained("xar.g2.m2.scopebase.slot38.slot.path", 8,
                "2b8bb2eeff7cd96c2b4aa1ec8d4be3f2f1337ee812f4987d4814d4d5cb1d0c44");
        Retained previous = retained("xar.g2.m2.scopebase.slot38.preceding.path", 12,
                "d844cd4ead3b64af2522b3100d32c271dab8183c406e85aa6b6c7684445999b9");
        Retained following = retained("xar.g2.m2.scopebase.slot38.following.path", 24,
                "9b0fb2062291c90f71828636004fbd011c22bbce78849daf95b7312a09f0ee2a");
        Retained getter = retained("xar.g2.m2.scopebase.slot38.body.path", 16,
                "d277b4c03adefb939866b86c52daf3944fea1e7c69f41b7fc6a6b079c356a790");
        var reviewed = NativeScriptMathProgram.reviewScopeBaseAllocatorReturn(bodies, caller.raw(), pe.raw(),
                slot38.source(), slot38.raw(), previous.source(), previous.raw(), following.source(), following.raw(),
                getter.source(), getter.raw());
        assertEquals(5, reviewed.virtual38SemanticBytes());
        assertEquals(0x855820L, reviewed.virtual38TargetRva());
        assertEquals(0x48, reviewed.returnedOffsetFromEmbeddedThis());
        assertEquals(0x54de3a0L, reviewed.returnedGlobalRva());
        assertEquals(88984992L, reviewed.returnedGlobalFileOffset());
        assertSame(bodies, reviewed.bodies());
        assertFalse(reviewed.returnedGlobalFileValueObserved());
        assertFalse(reviewed.returnedGlobalLoadedObjectQualified());
        assertFalse(reviewed.nestedAllocatorRouteClosed());
        assertFalse(reviewed.currentLoadedSourceQualified());
        assertFalse(reviewed.nativeGameExecuted());
        byte[] changed = getter.raw().clone(); changed[3] ^= 8;
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorReturn(
                bodies, caller.raw(), pe.raw(), slot38.source(), slot38.raw(), previous.source(), previous.raw(),
                following.source(), following.raw(), getter.source(), changed));
        byte[] changedRf = previous.raw().clone(); changedRf[4] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorReturn(
                bodies, caller.raw(), pe.raw(), slot38.source(), slot38.raw(), previous.source(), changedRf,
                following.source(), following.raw(), getter.source(), getter.raw()));
    }

    @Test void actualOnDiskGlobalQwordMapsOnlyTheNextStaticSlot() throws IOException {
        var returned = retainedReturnReview();
        Retained pe = retained("xar.g2.m2.scopebase.pe.path", 888,
                "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        Retained global = retained("xar.g2.m2.scopebase.returned.global.path", 8,
                "6cbdc8d4ed0e9c97780465e6aa9c3f4dd915cf0b737dbac66e4941b0422efab0");
        var observed = NativeScriptMathProgram.reviewScopeBaseAllocatorStaticGlobal(returned, pe.raw(), global.source(), global.raw());
        assertSame(returned, observed.returned());
        assertEquals(0x448af50L, observed.onDiskVtableRva());
        assertEquals(0x448af60L, observed.virtual10SlotRva());
        assertEquals(71867744L, observed.virtual10SlotFileOffset());
        assertTrue(observed.staticGlobalQwordObserved());
        assertFalse(observed.virtual10SlotObserved());
        assertFalse(observed.returnedGlobalLoadedVptrObserved());
        assertFalse(observed.nestedAllocatorRouteClosed());
        assertFalse(observed.currentLoadedSourceQualified());
        assertFalse(observed.nativeGameExecuted());
        byte[] changed = global.raw().clone(); changed[0] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorStaticGlobal(
                returned, pe.raw(), global.source(), changed));
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorStaticGlobal(
                returned, pe.raw(), global.source(), new byte[8]));
    }

    @Test void actualStaticVirtual10TargetDoesNotQualifyBodyAbiOrLoadedVptr() throws IOException {
        var returned = retainedReturnReview();
        Retained pe = retained("xar.g2.m2.scopebase.pe.path", 888,
                "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        Retained global = retained("xar.g2.m2.scopebase.returned.global.path", 8,
                "6cbdc8d4ed0e9c97780465e6aa9c3f4dd915cf0b737dbac66e4941b0422efab0");
        var globalReview = NativeScriptMathProgram.reviewScopeBaseAllocatorStaticGlobal(returned, pe.raw(), global.source(), global.raw());
        Retained slot = retained("xar.g2.m2.scopebase.returned.virtual10.path", 8,
                "f00c696b491529947c39272856ace0f7e63e4a33ef2237bc55790f3ca789cd51");
        var target = NativeScriptMathProgram.reviewScopeBaseAllocatorStaticTarget(globalReview, pe.raw(), slot.source(), slot.raw());
        assertSame(globalReview, target.global());
        assertEquals(0x8571c0L, target.targetRva());
        assertEquals(8742336L, target.targetFileOffset());
        assertTrue(target.staticVirtual10SlotObserved());
        assertFalse(target.callbackBodyReviewed());
        assertFalse(target.callbackAbiQualified());
        assertFalse(target.returnedGlobalLoadedVptrObserved());
        assertFalse(target.nestedAllocatorRouteClosed());
        assertFalse(target.currentLoadedSourceQualified());
        assertFalse(target.nativeGameExecuted());
        byte[] changed = slot.raw().clone(); changed[0] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorStaticTarget(
                globalReview, pe.raw(), slot.source(), changed));
        assertThrows(IllegalArgumentException.class, () -> NativeScriptMathProgram.reviewScopeBaseAllocatorStaticTarget(
                globalReview, pe.raw(), slot.source(), new byte[8]));
    }

    private static NativeScriptMathProgram.ScopeBaseAllocatorReturn retainedReturnReview() throws IOException {
        Retained caller = retained("xar.g2.m2.scopebase.caller.path", 184,
                "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
        Retained pe = retained("xar.g2.m2.scopebase.pe.path", 888,
                "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        Retained slots = retained("xar.g2.m2.scopebase.slots.path", 24,
                "2c4dc362a8e0df15994d4e825fe8392e3f3995d18f8fdcc8eda17b93df426ca4");
        var targets = NativeScriptMathProgram.reviewScopeBaseAllocator(
                caller.source(), caller.raw(), pe.source(), pe.raw(), slots.source(), slots.raw());
        Retained slot10 = retained("xar.g2.m2.scopebase.slot10.body.path", 58,
                "713f21ed3585fdf7d226ebef14cdd488cbe394d4a489fdc3227bea74f126a604");
        Retained unwind = retained("xar.g2.m2.scopebase.slot10.unwind.path", 12,
                "39455c244cd3d4de53471a0adec96067c74300ddc0ba6db9733fe8f8e3a9ffc4");
        Retained slot20 = retained("xar.g2.m2.scopebase.slot20.body.path", 64,
                "09e118536ec763b738f2080016e4fddacdc0b2ca15ad24355b42d8ec00d4098d");
        var bodies = NativeScriptMathProgram.reviewScopeBaseAllocatorBodies(targets,
                slot10.source(), slot10.raw(), unwind.source(), unwind.raw(), slot20.source(), slot20.raw());
        Retained slot38 = retained("xar.g2.m2.scopebase.slot38.slot.path", 8,
                "2b8bb2eeff7cd96c2b4aa1ec8d4be3f2f1337ee812f4987d4814d4d5cb1d0c44");
        Retained previous = retained("xar.g2.m2.scopebase.slot38.preceding.path", 12,
                "d844cd4ead3b64af2522b3100d32c271dab8183c406e85aa6b6c7684445999b9");
        Retained following = retained("xar.g2.m2.scopebase.slot38.following.path", 24,
                "9b0fb2062291c90f71828636004fbd011c22bbce78849daf95b7312a09f0ee2a");
        Retained getter = retained("xar.g2.m2.scopebase.slot38.body.path", 16,
                "d277b4c03adefb939866b86c52daf3944fea1e7c69f41b7fc6a6b079c356a790");
        var reviewed = NativeScriptMathProgram.reviewScopeBaseAllocatorReturn(bodies, caller.raw(), pe.raw(),
                slot38.source(), slot38.raw(), previous.source(), previous.raw(), following.source(), following.raw(),
                getter.source(), getter.raw());
        return reviewed;
    }

    private record Retained(ExactRef source, byte[] raw) { }
    private static Retained retained(String property, int bytes, String sha256) throws IOException {
        Path path = requiredPath(property, bytes);
        return new Retained(new ExactRef(path.toString(), bytes, sha256), Files.readAllBytes(path));
    }

    private static Path requiredPath(String property, long bytes) throws IOException {
        String configured = System.getProperty(property);
        if (configured == null || configured.isBlank()) {
            throw new IllegalArgumentException("mandatory retained source property absent: " + property);
        }
        Path path = Path.of(configured).toAbsolutePath().normalize();
        if (Files.size(path) != bytes) {
            throw new IllegalArgumentException("retained source has the wrong complete extent: " + property);
        }
        return path;
    }
}
