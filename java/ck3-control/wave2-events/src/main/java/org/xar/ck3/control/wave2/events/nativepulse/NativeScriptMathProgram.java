package org.xar.ck3.control.wave2.events.nativepulse;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Concrete current4 math factory -> ordered base evaluator -> SimpleScriptMath operand/arithmetic.
 * Complete parsed source, current +70 writer/capture and arbitrary node classes remain unavailable.
 */
public final class NativeScriptMathProgram {
    public static final long MATH_PRIMARY_VTABLE_RVA = 0x44a2a18L;
    public static final long MATH_BASE_VTABLE_RVA = 0x44a2a58L;
    public static final long SIMPLE_VTABLE_RVA = 0x492cde8L;
    public static final int SIMPLE_ALLOCATION_BYTES = 0x128;
    public static final int SIMPLE_OPERAND_OFFSET = 0x30;
    public static final int SIMPLE_OPCODE_OFFSET = 0x120;
    public static final String FACTORY_SHA256 = "0b6ea76eb7c27121db34004cf81b5e245c8169e5f810258e62feb7cabe743f60";
    /** Physical factory evidence, independently of any currently loaded object or successful operand Load. */
    public record FactoryReview(ExactRef original, int allocationBytes, int operandOffset, int opcodeOffset,
                                long nodeVtableRva, int loadVtableSlot) {
        public FactoryReview { evidence(original); StrictJson.require(original.bytes() == 2922 && original.sha256().equals(FACTORY_SHA256)
            && allocationBytes == SIMPLE_ALLOCATION_BYTES && operandOffset == SIMPLE_OPERAND_OFFSET
            && opcodeOffset == SIMPLE_OPCODE_OFFSET && nodeVtableRva == SIMPLE_VTABLE_RVA && loadVtableSlot == 0x18,
            "exact reviewed physical factory layout required"); }
        public boolean currentLoadedAstQualified() { return false; }
        public boolean operandLoadClosed() { return false; }
    }
    /** Consumes the complete retained original RF including its trailing tables; never opens a native image. */
    public static FactoryReview reviewFactory(ExactRef original, byte[] retainedRaw) {
        Objects.requireNonNull(retainedRaw); Objects.requireNonNull(original);
        final String digest;
        try { digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(retainedRaw)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        StrictJson.require(retainedRaw.length == 2922 && original.bytes() == retainedRaw.length
            && original.sha256().equals(digest) && FACTORY_SHA256.equals(digest), "complete exact original factory RF required");
        var raw = java.nio.ByteBuffer.wrap(retainedRaw).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        int allocation = raw.getInt(0x374cc05 - 0x374c250);
        int operand = Byte.toUnsignedInt(raw.get(0x374cc2a - 0x374c250));
        int opcode = raw.getInt(0x374cc32 - 0x374c250);
        long vtable = 0x374cc24L + raw.getInt(0x374cc20 - 0x374c250);
        int loadSlot = Byte.toUnsignedInt(raw.get(0x374cc70 - 0x374c250));
        return new FactoryReview(original, allocation, operand, opcode, vtable, loadSlot);
    }
    /** Actual A06830 caller plus Raw29 PE/vtable bytes; target identity is distinct from callee semantics. */
    public record ScopeBaseAllocatorReview(ExactRef originalCaller, ExactRef originalPe, ExactRef originalSlots,
                                           long installedVtableRva, long slot10TargetRva, long slot20TargetRva) {
        public ScopeBaseAllocatorReview {
            capturedReference(originalCaller, 184, "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
            capturedReference(originalPe, 888, "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
            capturedReference(originalSlots, 24, "2c4dc362a8e0df15994d4e825fe8392e3f3995d18f8fdcc8eda17b93df426ca4");
            StrictJson.require(installedVtableRva == 0x44a2980L
                    && slot10TargetRva == 0x855830L && slot20TargetRva == 0x896b80L,
                    "actual A06830 installed allocator and both Raw29 static targets required");
        }
        public boolean virtual10BodyReviewed() { return false; }
        public boolean virtual20BodyReviewed() { return false; }
        public boolean finalScopeChainKnown() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }

    /** Consumes retained originals only; never reads an EXE or infers a loaded container from zero stores. */
    public static ScopeBaseAllocatorReview reviewScopeBaseAllocator(
            ExactRef originalCaller, byte[] callerBytes, ExactRef originalPe, byte[] peBytes,
            ExactRef originalSlots, byte[] slotBytes) {
        capturedBytes(originalCaller, callerBytes, 184, "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
        capturedBytes(originalPe, peBytes, 888, "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        capturedBytes(originalSlots, slotBytes, 24, "2c4dc362a8e0df15994d4e825fe8392e3f3995d18f8fdcc8eda17b93df426ca4");
        var caller = java.nio.ByteBuffer.wrap(callerBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        long installed = 0xa06863L + caller.getInt(0xa0685f - 0xa06830);
        StrictJson.require(Byte.toUnsignedInt(caller.get(0xa068b4 - 0xa06830)) == 0x10
                && Byte.toUnsignedInt(caller.get(0xa068cb - 0xa06830)) == 0x20,
                "retained caller must use the actual allocator virtual10 and virtual20 edges");
        var pe = java.nio.ByteBuffer.wrap(peBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        int nt = pe.getInt(0x3c);
        int optional = nt + 24;
        int section = optional + Short.toUnsignedInt(pe.getShort(nt + 20));
        long imageBase = pe.getLong(optional + 24);
        long textSize = Integer.toUnsignedLong(pe.getInt(section + 8));
        long textRva = Integer.toUnsignedLong(pe.getInt(section + 12));
        StrictJson.require(pe.getInt(nt) == 0x00004550 && Short.toUnsignedInt(pe.getShort(nt + 4)) == 0x8664
                && Short.toUnsignedInt(pe.getShort(optional)) == 0x20b
                && (pe.getInt(section + 36) & 0x20000000) != 0,
                "retained current4 executable PE text geometry required");
        var slots = java.nio.ByteBuffer.wrap(slotBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        long target10 = slots.getLong(0) - imageBase;
        long target20 = slots.getLong(16) - imageBase;
        StrictJson.require(target10 >= textRva && target10 - textRva < textSize
                && target20 >= textRva && target20 - textRva < textSize,
                "both original static allocator targets must be inside executable text");
        return new ScopeBaseAllocatorReview(originalCaller, originalPe, originalSlots, installed, target10, target20);
    }

    private static void capturedReference(ExactRef original, int bytes, String sha256) {
        evidence(original);
        StrictJson.require(original.bytes() == bytes && original.sha256().equals(sha256),
                "exact retained allocator source reference required");
    }
    private static void capturedBytes(ExactRef original, byte[] retained, int bytes, String sha256) {
        capturedReference(original, bytes, sha256);
        Objects.requireNonNull(retained);
        final String actual;
        try { actual = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(retained)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        StrictJson.require(retained.length == bytes && actual.equals(sha256),
                "actual complete retained allocator source bytes required");
    }

    /** Offset-named fields after the reviewed fresh constructor's normal static virtual20 return. */
    public record FreshScopeBaseLayout(int dataOffsetFromScopeBaseThis, int packedLowDword08, int signedCount0C) {
        public FreshScopeBaseLayout {
            StrictJson.require(dataOffsetFromScopeBaseThis == 0x20 && packedLowDword08 == 4 && signedCount0C == 0,
                    "actual inline pointer offset and packed constructor fields required");
        }
        public boolean scopeChainEmptyOnReviewedNormalReturn() { return signedCount0C == 0; }
    }
    public record ScopeBaseAllocatorBodies(ScopeBaseAllocatorReview targets, ExactRef originalSlot10Body,
                                           ExactRef originalSlot10Unwind, ExactRef originalSlot20Capture,
                                           FreshScopeBaseLayout normalPoststate) {
        public ScopeBaseAllocatorBodies {
            Objects.requireNonNull(targets); Objects.requireNonNull(normalPoststate);
            capturedReference(originalSlot10Body, 58, "713f21ed3585fdf7d226ebef14cdd488cbe394d4a489fdc3227bea74f126a604");
            capturedReference(originalSlot10Unwind, 12, "39455c244cd3d4de53471a0adec96067c74300ddc0ba6db9733fe8f8e3a9ffc4");
            capturedReference(originalSlot20Capture, 64, "09e118536ec763b738f2080016e4fddacdc0b2ca15ad24355b42d8ec00d4098d");
        }
        public int virtual20SemanticBytes() { return 15; }
        public boolean virtual10WholeBodyReviewed() { return true; }
        public boolean nestedAllocatorRouteClosed() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }

    /**
     * Decodes the actual15B leaf within its retained64B observation and the complete58B/12B RF/UW.
     * The normal layout is not a currently loaded Pdx value or proof that nested allocator calls completed.
     */
    public static ScopeBaseAllocatorBodies reviewScopeBaseAllocatorBodies(ScopeBaseAllocatorReview targets,
            ExactRef originalSlot10Body, byte[] slot10Bytes, ExactRef originalSlot10Unwind, byte[] unwindBytes,
            ExactRef originalSlot20Capture, byte[] slot20Bytes) {
        Objects.requireNonNull(targets);
        capturedBytes(originalSlot10Body, slot10Bytes, 58, "713f21ed3585fdf7d226ebef14cdd488cbe394d4a489fdc3227bea74f126a604");
        capturedBytes(originalSlot10Unwind, unwindBytes, 12, "39455c244cd3d4de53471a0adec96067c74300ddc0ba6db9733fe8f8e3a9ffc4");
        capturedBytes(originalSlot20Capture, slot20Bytes, 64, "09e118536ec763b738f2080016e4fddacdc0b2ca15ad24355b42d8ec00d4098d");
        StrictJson.require(Byte.toUnsignedInt(slot10Bytes[30]) == 0x38
                && Byte.toUnsignedInt(slot10Bytes[46]) == 0x10
                && Byte.toUnsignedInt(slot10Bytes[57]) == 0xc3,
                "actual virtual38 then returned-object virtual10 route must remain explicit");
        StrictJson.require(Byte.toUnsignedInt(unwindBytes[0]) == 1 && Byte.toUnsignedInt(unwindBytes[1]) == 10
                && Byte.toUnsignedInt(unwindBytes[2]) == 4,
                "complete actual no-handler no-chain unwind source required");
        StrictJson.require(Byte.toUnsignedInt(slot20Bytes[14]) == 0xc3,
                "actual virtual20 semantic terminal required; the rest is not this leaf");
        int inlineOffset = Byte.toUnsignedInt(slot20Bytes[3]);
        int packedLow = java.nio.ByteBuffer.wrap(slot20Bytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt(10);
        // A06830 zeros packed+0x08 after virtual10, then supplies allocatorThis=scopeBaseThis+0x18.
        // The leaf writes only packed's lowDWORD; the signed count at+0C therefore remains zero.
        var layout = new FreshScopeBaseLayout(0x18 + inlineOffset, packedLow, 0);
        return new ScopeBaseAllocatorBodies(targets, originalSlot10Body, originalSlot10Unwind, originalSlot20Capture, layout);
    }

    /** Actual virtual38 leaf and caller field producer; the returned global's vptr is still unobserved. */
    public record ScopeBaseAllocatorReturn(ScopeBaseAllocatorBodies bodies, ExactRef originalSlot38,
            ExactRef originalPrecedingRf, ExactRef originalFollowingRf, ExactRef originalSlot38Capture,
            int returnedOffsetFromEmbeddedThis, long returnedGlobalRva, long returnedGlobalFileOffset) {
        public ScopeBaseAllocatorReturn {
            Objects.requireNonNull(bodies);
            capturedReference(originalSlot38, 8, "2b8bb2eeff7cd96c2b4aa1ec8d4be3f2f1337ee812f4987d4814d4d5cb1d0c44");
            capturedReference(originalPrecedingRf, 12, "d844cd4ead3b64af2522b3100d32c271dab8183c406e85aa6b6c7684445999b9");
            capturedReference(originalFollowingRf, 24, "9b0fb2062291c90f71828636004fbd011c22bbce78849daf95b7312a09f0ee2a");
            capturedReference(originalSlot38Capture, 16, "d277b4c03adefb939866b86c52daf3944fea1e7c69f41b7fc6a6b079c356a790");
            StrictJson.require(returnedOffsetFromEmbeddedThis == 0x48 && returnedGlobalRva == 0x54de3a0L
                    && returnedGlobalFileOffset == 88984992L, "actual virtual38 field producer and static data mapping required");
        }
        public int virtual38SemanticBytes() { return 5; }
        public long virtual38TargetRva() { return 0x855820L; }
        public boolean returnedGlobalFileValueObserved() { return false; }
        public boolean returnedGlobalLoadedObjectQualified() { return false; }
        public boolean nestedAllocatorRouteClosed() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }

    /** Decodes only retained originals. A static global address is not its file contents or a loaded vptr. */
    public static ScopeBaseAllocatorReturn reviewScopeBaseAllocatorReturn(ScopeBaseAllocatorBodies bodies,
            byte[] callerBytes, byte[] peBytes, ExactRef originalSlot38, byte[] slot38Bytes,
            ExactRef originalPrecedingRf, byte[] precedingRfBytes, ExactRef originalFollowingRf, byte[] followingRfBytes,
            ExactRef originalSlot38Capture, byte[] slot38CaptureBytes) {
        Objects.requireNonNull(bodies);
        capturedBytes(bodies.targets().originalCaller(), callerBytes, 184, "10ef14ddce6e6f965561d8be09ffd0494682aa269d7f9bc3a28cd2e7e83e9e86");
        capturedBytes(bodies.targets().originalPe(), peBytes, 888, "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        capturedBytes(originalSlot38, slot38Bytes, 8, "2b8bb2eeff7cd96c2b4aa1ec8d4be3f2f1337ee812f4987d4814d4d5cb1d0c44");
        capturedBytes(originalPrecedingRf, precedingRfBytes, 12, "d844cd4ead3b64af2522b3100d32c271dab8183c406e85aa6b6c7684445999b9");
        capturedBytes(originalFollowingRf, followingRfBytes, 24, "9b0fb2062291c90f71828636004fbd011c22bbce78849daf95b7312a09f0ee2a");
        capturedBytes(originalSlot38Capture, slot38CaptureBytes, 16, "d277b4c03adefb939866b86c52daf3944fea1e7c69f41b7fc6a6b079c356a790");
        var pe = java.nio.ByteBuffer.wrap(peBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        int nt = pe.getInt(0x3c), optional = nt + 24;
        long imageBase = pe.getLong(optional + 24);
        int sections = optional + Short.toUnsignedInt(pe.getShort(nt + 20));
        int dataSection = sections + 2 * 40;
        long dataRva = Integer.toUnsignedLong(pe.getInt(dataSection + 12));
        long dataRawBytes = Integer.toUnsignedLong(pe.getInt(dataSection + 16));
        long dataRawOffset = Integer.toUnsignedLong(pe.getInt(dataSection + 20));
        long target = java.nio.ByteBuffer.wrap(slot38Bytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).getLong() - imageBase;
        var previous = java.nio.ByteBuffer.wrap(precedingRfBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        var following = java.nio.ByteBuffer.wrap(followingRfBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        StrictJson.require(target == 0x855820L && Integer.toUnsignedLong(previous.getInt(4)) == 0x85580cL
                && Integer.toUnsignedLong(following.getInt(0)) == 0x855830L
                && Integer.toUnsignedLong(previous.getInt(4)) <= target && target < Integer.toUnsignedLong(following.getInt(0)),
                "actual adjacent RF rows must leave the observed target in the actual gap");
        StrictJson.require(Byte.toUnsignedInt(slot38CaptureBytes[0]) == 0x48
                && Byte.toUnsignedInt(slot38CaptureBytes[1]) == 0x8b
                && Byte.toUnsignedInt(slot38CaptureBytes[2]) == 0x41
                && Byte.toUnsignedInt(slot38CaptureBytes[4]) == 0xc3,
                "actual five-byte virtual38 qword getter must terminate without an outside control-flow edge");
        int fieldOffset = Byte.toUnsignedInt(slot38CaptureBytes[3]);
        var caller = java.nio.ByteBuffer.wrap(callerBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        StrictJson.require(Byte.toUnsignedInt(callerBytes[0xa06870 - 0xa06830]) == fieldOffset,
                "constructor field store must match the actual getter offset");
        long global = 0xa0686dL + caller.getInt(0xa06869 - 0xa06830);
        StrictJson.require(dataRva == 0x542f000L && dataRawOffset == 0x542da00L
                && global >= dataRva && global - dataRva <= dataRawBytes - 8,
                "returned address must have an actual eight-byte file-backed data range");
        return new ScopeBaseAllocatorReturn(bodies, originalSlot38, originalPrecedingRf, originalFollowingRf,
                originalSlot38Capture, fieldOffset, global, dataRawOffset + global - dataRva);
    }

    /** The actual on-disk global qword is distinct from its initialized, loaded vptr. */
    public record ScopeBaseAllocatorStaticGlobal(ScopeBaseAllocatorReturn returned, ExactRef originalGlobalQword,
            long onDiskVtableRva, long virtual10SlotRva, long virtual10SlotFileOffset) {
        public ScopeBaseAllocatorStaticGlobal {
            Objects.requireNonNull(returned);
            capturedReference(originalGlobalQword, 8, "6cbdc8d4ed0e9c97780465e6aa9c3f4dd915cf0b737dbac66e4941b0422efab0");
            StrictJson.require(onDiskVtableRva == 0x448af50L && virtual10SlotRva == 0x448af60L
                    && virtual10SlotFileOffset == 71867744L, "actual file qword and exact next static slot mapping required");
        }
        public boolean staticGlobalQwordObserved() { return true; }
        public boolean virtual10SlotObserved() { return false; }
        public boolean returnedGlobalLoadedVptrObserved() { return false; }
        public boolean nestedAllocatorRouteClosed() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }

    /** Retained raw bytes only. No transport-label rewrite, image IO or loaded-memory observation occurs. */
    public static ScopeBaseAllocatorStaticGlobal reviewScopeBaseAllocatorStaticGlobal(ScopeBaseAllocatorReturn returned,
            byte[] peBytes, ExactRef originalGlobalQword, byte[] globalQwordBytes) {
        Objects.requireNonNull(returned);
        capturedBytes(returned.bodies().targets().originalPe(), peBytes, 888, "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        capturedBytes(originalGlobalQword, globalQwordBytes, 8, "6cbdc8d4ed0e9c97780465e6aa9c3f4dd915cf0b737dbac66e4941b0422efab0");
        var pe = java.nio.ByteBuffer.wrap(peBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        int nt = pe.getInt(0x3c), optional = nt + 24;
        long imageBase = pe.getLong(optional + 24);
        int sections = optional + Short.toUnsignedInt(pe.getShort(nt + 20));
        int rdataSection = sections + 40;
        long rdataVirtualBytes = Integer.toUnsignedLong(pe.getInt(rdataSection + 8));
        long rdataRva = Integer.toUnsignedLong(pe.getInt(rdataSection + 12));
        long rdataRawBytes = Integer.toUnsignedLong(pe.getInt(rdataSection + 16));
        long rdataRawOffset = Integer.toUnsignedLong(pe.getInt(rdataSection + 20));
        long onDiskVtable = java.nio.ByteBuffer.wrap(globalQwordBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).getLong() - imageBase;
        long slot = onDiskVtable + 0x10;
        StrictJson.require(rdataRva == 0x43da000L && rdataRawOffset == 0x43d8e00L && onDiskVtable >= rdataRva
                && slot >= onDiskVtable && slot - rdataRva <= Math.min(rdataVirtualBytes, rdataRawBytes) - 8,
                "the static vtable candidate and its full next slot must be inside retained file-backed rdata");
        return new ScopeBaseAllocatorStaticGlobal(returned, originalGlobalQword, onDiskVtable, slot,
                rdataRawOffset + slot - rdataRva);
    }

    /** Actual static slot target; function body and runtime invocation remain independent evidence. */
    public record ScopeBaseAllocatorStaticTarget(ScopeBaseAllocatorStaticGlobal global, ExactRef originalVirtual10Slot,
            long targetRva, long targetFileOffset) {
        public ScopeBaseAllocatorStaticTarget {
            Objects.requireNonNull(global);
            capturedReference(originalVirtual10Slot, 8, "f00c696b491529947c39272856ace0f7e63e4a33ef2237bc55790f3ca789cd51");
            StrictJson.require(targetRva == 0x8571c0L && targetFileOffset == 8742336L,
                    "exact actual returned-global virtual10 static target required");
        }
        public boolean staticVirtual10SlotObserved() { return true; }
        public boolean callbackBodyReviewed() { return false; }
        public boolean callbackAbiQualified() { return false; }
        public boolean returnedGlobalLoadedVptrObserved() { return false; }
        public boolean nestedAllocatorRouteClosed() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }

    public static ScopeBaseAllocatorStaticTarget reviewScopeBaseAllocatorStaticTarget(ScopeBaseAllocatorStaticGlobal global,
            byte[] peBytes, ExactRef originalVirtual10Slot, byte[] virtual10SlotBytes) {
        Objects.requireNonNull(global);
        capturedBytes(global.returned().bodies().targets().originalPe(), peBytes, 888, "e3eb8c25ebb10a76ee978743936a258b31d820d9bf862c2894e3a110976a8014");
        capturedBytes(originalVirtual10Slot, virtual10SlotBytes, 8, "f00c696b491529947c39272856ace0f7e63e4a33ef2237bc55790f3ca789cd51");
        var pe = java.nio.ByteBuffer.wrap(peBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        int nt = pe.getInt(0x3c), optional = nt + 24;
        long imageBase = pe.getLong(optional + 24);
        int textSection = optional + Short.toUnsignedInt(pe.getShort(nt + 20));
        long textVirtualBytes = Integer.toUnsignedLong(pe.getInt(textSection + 8));
        long textRva = Integer.toUnsignedLong(pe.getInt(textSection + 12));
        long textRawBytes = Integer.toUnsignedLong(pe.getInt(textSection + 16));
        long textRawOffset = Integer.toUnsignedLong(pe.getInt(textSection + 20));
        long target = java.nio.ByteBuffer.wrap(virtual10SlotBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).getLong() - imageBase;
        StrictJson.require((pe.getInt(textSection + 36) & 0x20000000) != 0 && target >= textRva
                && target - textRva < Math.min(textVirtualBytes, textRawBytes), "actual static target must map inside executable text");
        return new ScopeBaseAllocatorStaticTarget(global, originalVirtual10Slot, target, textRawOffset + target - textRva);
    }

    private NativeScriptMathProgram() { }

    /** These two original wrappers zero the output before the common base virtual+30 call. */
    public enum Entry { RAW_PDX_B8_9D7141, NAMED_VALUE_70_375438F }
    public enum Operator {
        ASSIGN(0), ADD(1), SUBTRACT(2), MULTIPLY(3), DIVIDE(4), MODULO(5), MINIMUM(6), MAXIMUM(7),
        UNREVIEWED_CALLEE_8(8), ROUND(9), CEILING(10), FLOOR(11), ABSOLUTE(12), UNREVIEWED_CALLEE_13(13), NO_WRITE_14(14);
        private final int nativeOpcode;
        Operator(int nativeOpcode) { this.nativeOpcode = nativeOpcode; }
        public int nativeOpcode() { return nativeOpcode; }
    }
    public enum OperandLoad { CONSTRUCTOR_FIELDS_RETAINED, RAW_PDX_VIRTUAL_18 }
    /** Retained03 whole374A0C0 leaf: only9..12 return before the operand Load virtual. */
    public static OperandLoad operandLoad(Operator operator) {
        Objects.requireNonNull(operator);int opcode=operator.nativeOpcode();
        return opcode>=9&&opcode<=12?OperandLoad.CONSTRUCTOR_FIELDS_RETAINED:OperandLoad.RAW_PDX_VIRTUAL_18;
    }
    public static void validateOperandLoad(SimpleField field) {
        Objects.requireNonNull(field);validateOperandLoad(operatorForToken(field.nativeToken()).orElseThrow(),field.originalOperand());
    }
    private static void validateOperandLoad(Operator operator,NativeRawScriptValue.Input operand) {
        if(operandLoad(operator)!=OperandLoad.CONSTRUCTOR_FIELDS_RETAINED)return;
        NativeRawScriptValue.Pdx value=operand.value();
        StrictJson.require(value.nativeKindC0()==0&&value.storedRaw98()==0&&value.upperRawA0()==0
            &&value.lowerA8().isEmpty()&&value.upperB0().isEmpty()&&value.overrideB8().isEmpty(),
            "native unary Load is skipped: require the actual A13AE0 zero/null constructor fields, never a parsed unary operand");
        // The reviewed fresh static layout is separate from a loaded chain. Native kind0 bypasses that chain and every callback.
    }
    /** This binds exact reviewed RTTI/vtables, not an assertion that an object was currently loaded. */
    public record Root(BigInteger originalObjectU64, long primaryVtableRva, long baseVtableRva, Entry entry) {
        public Root { NativeRawScriptValue.u64(originalObjectU64); Objects.requireNonNull(entry);
            StrictJson.require(originalObjectU64.signum() > 0 && primaryVtableRva == MATH_PRIMARY_VTABLE_RVA && baseVtableRva == MATH_BASE_VTABLE_RVA,
                "exact reviewed current4 math-object identity required"); }
    }
    public sealed interface Field permits SimpleField, UnreviewedField { int nativeToken(); ExactRef originalSource(); }
    /** Original parsed token and operand remain the producer inputs. Callers cannot choose an arbitrary opcode. */
    public record SimpleField(int nativeToken, ExactRef originalSource, NativeRawScriptValue.Input originalOperand) implements Field {
        public SimpleField { token(nativeToken); evidence(originalSource); Objects.requireNonNull(originalOperand);
            StrictJson.require(operatorForToken(nativeToken).isPresent(), "only source-closed SimpleScriptMath token accepted");
            validateOperandLoad(operatorForToken(nativeToken).orElseThrow(),originalOperand); }
    }
    /** Registry fallback or a different native node class cannot silently become NO_WRITE or SimpleScriptMath. */
    public record UnreviewedField(int nativeToken, ExactRef originalSource, String diagnosis) implements Field {
        public UnreviewedField { token(nativeToken); evidence(originalSource); StrictJson.text(diagnosis); }
    }
    public record Input(NativePlayableAnnualGate.Executable executable, ExactRef originalObservation, Root root,
                        NativeRawScriptValue.Context originalContext, Optional<NativeRawScriptValue.Random> originalRandom,
                        List<Field> originalFields) {
        public Input { Objects.requireNonNull(executable); evidence(originalObservation); Objects.requireNonNull(root);
            Objects.requireNonNull(originalContext); Objects.requireNonNull(originalRandom); originalFields = List.copyOf(originalFields);
            StrictJson.require(originalFields.size() <= 256, "bounded original math-node occurrences required");
            for (Field field : originalFields) if (field instanceof SimpleField simple) {
                StrictJson.require(simple.originalOperand().executable() == executable, "same executable for every original operand required");
                StrictJson.require(simple.originalOperand().context().equals(originalContext), "original operand context must equal root context");
            }
        }
    }
    public sealed interface Node permits SimpleNode, UnknownNode { int originalIndex(); }
    public record SimpleNode(int originalIndex, Operator operator, long nativeVtableRva, SimpleField original) implements Node {
        public SimpleNode { Objects.requireNonNull(operator); Objects.requireNonNull(original);
            StrictJson.require(originalIndex >= 0 && nativeVtableRva == SIMPLE_VTABLE_RVA
                && operatorForToken(original.nativeToken()).orElseThrow() == operator, "actual token/opcode/vtable producer binding required"); }
    }
    public record UnknownNode(int originalIndex, UnreviewedField original) implements Node {
        public UnknownNode { StrictJson.require(originalIndex >= 0, "original index required"); Objects.requireNonNull(original); }
    }
    public record Produced(Input original, List<Node> originalOrder) {
        public Produced { Objects.requireNonNull(original); originalOrder = List.copyOf(originalOrder);
            StrictJson.require(originalOrder.size() == original.originalFields().size(), "producer cannot drop original source occurrences"); }
    }
    public enum Status { RECONSTRUCTED, UNKNOWN_NODE_CLASS, OPERAND_UNAVAILABLE, ORIGINAL_RANDOM_MISMATCH, UNKNOWN_OPERATION, NATIVE_DIVIDE_OVERFLOW }
    public enum Diagnostic { DIVIDE_ZERO_NO_WRITE, MODULO_ZERO_NO_WRITE, OPERATION_8_ZERO_NO_WRITE }
    public record Applied(int originalIndex, Operator operator, long beforeRaw, long operandRaw, long afterRaw,
                          Optional<Diagnostic> diagnostic, NativeRawScriptValue.Result originalOperandResult) {
        public Applied { Objects.requireNonNull(operator); Objects.requireNonNull(diagnostic); Objects.requireNonNull(originalOperandResult); }
    }
    public record Result(Status status, long reconstructedPrefixRaw, Optional<NativeRawScriptValue.Random> afterRandom,
                         List<Applied> applied, int blockedOriginalIndex, String diagnosis) {
        public Result { Objects.requireNonNull(status); Objects.requireNonNull(afterRandom); applied = List.copyOf(applied); StrictJson.text(diagnosis);
            StrictJson.require((status == Status.RECONSTRUCTED) == (blockedOriginalIndex == -1), "exact terminal/prefix boundary required"); }
        public boolean completeNativeAst() { return false; }
        public boolean originalNamed70WriterClosed() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }
    /** Actual 374C250 switch values; token names are not guessed from arithmetic or historical builds. */
    public static Optional<Operator> operatorForToken(int token) {
        return Optional.ofNullable(switch (token) {
            case 0x2d2 -> Operator.ASSIGN;
            case 0x4f3 -> Operator.ADD;
            case 0x4f4 -> Operator.SUBTRACT;
            case 0x4f5 -> Operator.MULTIPLY;
            case 0x4f6 -> Operator.DIVIDE;
            case 0x4f7 -> Operator.MODULO;
            case 0x2a4 -> Operator.MINIMUM;
            case 0x2a3 -> Operator.MAXIMUM;
            case 0x99b -> Operator.UNREVIEWED_CALLEE_8;
            case 0x548 -> Operator.ROUND;
            case 0x56e -> Operator.CEILING;
            case 0x56f -> Operator.FLOOR;
            case 0x74b -> Operator.ABSOLUTE;
            case 0x93d -> Operator.UNREVIEWED_CALLEE_13;
            default -> null;
        });
    }
    /** 374CC04..CC79 allocates 0x128 bytes, embeds Raw Pdx at+0x30 and writes native op at+0x120. */
    public static Produced produce(Input input) {
        List<Node> nodes = new ArrayList<>();
        for (int index = 0; index < input.originalFields().size(); index++) {
            Field field = input.originalFields().get(index);
            nodes.add(field instanceof SimpleField simple ? new SimpleNode(index, operatorForToken(simple.nativeToken()).orElseThrow(), SIMPLE_VTABLE_RVA, simple)
                : new UnknownNode(index, (UnreviewedField) field));
        }
        return new Produced(input, nodes);
    }
    /** Only original producer output is consumed; a fabricated or reordered Produced value is refused. */
    public static Result consume(Produced produced) {
        Input input = produced.original(); StrictJson.require(produced.equals(produce(input)), "consumer requires same original producer nodes/order");
        long current = 0; Optional<NativeRawScriptValue.Random> random = input.originalRandom(); List<Applied> applied = new ArrayList<>();
        for (Node node : produced.originalOrder()) {
            if (node instanceof UnknownNode unknown) return result(Status.UNKNOWN_NODE_CLASS, current, random, applied, node.originalIndex(), unknown.original().diagnosis());
            SimpleNode simple = (SimpleNode) node; NativeRawScriptValue.Input operandInput = simple.original().originalOperand();
            if (!operandInput.originalRandom().equals(random)) return result(Status.ORIGINAL_RANDOM_MISMATCH, current, random, applied, node.originalIndex(), "operand original RNG must match prior node's actual reconstructed after state");
            // 374A870 evaluates Raw Pdx even for ROUND/ABS/NO_WRITE whose arithmetic does not use its numeric output.
            NativeRawScriptValue.Result operand = NativeRawScriptValue.analyze(operandInput); random = operand.afterRandom();
            if (operand.status() != NativeRawScriptValue.Status.RECONSTRUCTED) return result(Status.OPERAND_UNAVAILABLE, current, random, applied, node.originalIndex(), operand.diagnosis());
            long value = operand.raw().orElseThrow(); Arithmetic operation = arithmetic(current, value, simple.operator());
            if (operation.status() != Status.RECONSTRUCTED) return result(operation.status(), current, random, applied, node.originalIndex(), operation.diagnosis());
            applied.add(new Applied(node.originalIndex(), simple.operator(), current, value, operation.raw(), operation.diagnostic(), operand)); current = operation.raw();
        }
        return result(Status.RECONSTRUCTED, current, random, applied, -1, "concrete simple-node control/arithmetic reconstructed; loaded +70 writer/current capture and other AST classes unqualified");
    }
    public static Result run(Input input) { return consume(produce(input)); }
    /** Existing weighted consumer accepts only fully reconstructed programs without virtual-leaf/RNG consumption. */
    public static NativeOnActionWeightProgram.RawValue weightOperand(Input input) {
        Result result = run(input);
        boolean stateful = result.applied().stream().flatMap(row -> row.originalOperandResult().trace().stream())
            .anyMatch(row -> row.kind() == NativeRawScriptValue.TraceKind.RANGE64 || row.kind() == NativeRawScriptValue.TraceKind.RAW_VIRTUAL_30 || row.kind() == NativeRawScriptValue.TraceKind.SCOPE_VIRTUAL_20);
        return result.status() == Status.RECONSTRUCTED && !stateful ? new NativeOnActionWeightProgram.InlineRaw(result.reconstructedPrefixRaw())
            : new NativeOnActionWeightProgram.DynamicRaw(1, result.status() == Status.RECONSTRUCTED ? "math AST requires original callback/RNG propagation before weighted consumer adoption" : result.diagnosis());
    }
    private record Arithmetic(Status status, long raw, Optional<Diagnostic> diagnostic, String diagnosis) { }
    private static Arithmetic arithmetic(long current, long value, Operator operator) {
        if (operator == Operator.UNREVIEWED_CALLEE_8 && value == 0)
            return new Arithmetic(Status.RECONSTRUCTED, current, Optional.of(Diagnostic.OPERATION_8_ZERO_NO_WRITE), "native operation8 zero operand diagnoses/no-write before its unknown callee");
        if (operator == Operator.UNREVIEWED_CALLEE_8 || operator == Operator.UNREVIEWED_CALLEE_13)
            return new Arithmetic(Status.UNKNOWN_OPERATION, current, Optional.empty(), "actual operation callee3FA33A0/3FB3FD0 not read in bounded02; no inferred exponent/random semantics");
        if (value == 0 && (operator == Operator.DIVIDE || operator == Operator.MODULO))
            return new Arithmetic(Status.RECONSTRUCTED, current, Optional.of(operator == Operator.DIVIDE ? Diagnostic.DIVIDE_ZERO_NO_WRITE : Diagnostic.MODULO_ZERO_NO_WRITE), "native diagnostic path preserves accumulator and continues outer ordered nodes");
        if (operator == Operator.MODULO && current == Long.MIN_VALUE && value == -1)
            return new Arithmetic(Status.NATIVE_DIVIDE_OVERFLOW, current, Optional.empty(), "actual idiv MIN_VALUE/-1 faults; operand RNG mutation already retained");
        long output = switch (operator) {
            case ASSIGN -> value;
            case ADD -> current + value;
            case SUBTRACT -> current - value;
            case MULTIPLY -> NativeOnActionWeightProgram.multiplyRaw(current, value);
            case DIVIDE -> divideRaw(current, value);
            case MODULO -> current % value;
            case MINIMUM -> Math.min(current, value);
            case MAXIMUM -> Math.max(current, value);
            case ROUND -> narrowUnits((current + (current < 0 ? -50000L : 50000L)) / 100000L);
            case CEILING -> narrowUnits(current / 100000L + (current % 100000L != 0 && current > 0 ? 1 : 0));
            case FLOOR -> narrowUnits(current / 100000L - (current % 100000L != 0 && current < 0 ? 1 : 0));
            case ABSOLUTE -> current < 0 ? -current : current;
            case NO_WRITE_14 -> current;
            case UNREVIEWED_CALLEE_8, UNREVIEWED_CALLEE_13 -> throw new IllegalStateException("unreviewed operators return earlier");
        };
        return new Arithmetic(Status.RECONSTRUCTED, output, Optional.empty(), "actual raw arithmetic");
    }
    /** 374A373..A45D; division zero is handled by the native no-write branch before this method. */
    private static long divideRaw(long current, long divisor) {
        if (current >= -92233720368547L && current <= 92233720368547L) return (current * 100000L) / divisor;
        // abs(MIN_VALUE) intentionally wraps negative, matching native XOR/sub; it takes the small-divisor decomposition.
        if (Math.abs(divisor) >= 10000000000L) return current / (divisor / 100000L);
        long high = (current / 100000L) * 100000L;
        long quotient = high / divisor, remainder = high % divisor;
        long low = current - high;
        return (low * 100000L) / divisor + (remainder * 100000L) / divisor + quotient * 100000L;
    }
    private static long narrowUnits(long quotient) { return (long) (int) quotient * 100000L; }
    private static Result result(Status status, long current, Optional<NativeRawScriptValue.Random> random, List<Applied> applied, int blocked, String diagnosis) {
        return new Result(status, current, random, applied, blocked, diagnosis);
    }
    private static void token(int value) { StrictJson.require(value >= 0, "nonnegative original native token required"); }
    private static void evidence(ExactRef value) { Objects.requireNonNull(value); StrictJson.require(value.bytes() > 0 && value.bytes() <= NativeScriptMathProgramJson.MAX_BYTES, "bounded exact original source required"); }
}
