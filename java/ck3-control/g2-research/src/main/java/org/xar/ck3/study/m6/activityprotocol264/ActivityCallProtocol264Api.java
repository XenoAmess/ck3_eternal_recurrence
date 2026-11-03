package org.xar.ck3.study.m6.activityprotocol264;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/**
 * SOURCE-ONLY CANDIDATE, UNCOMPILED. Thin represented full-Outcome protocol for all
 * 126 opaque CALL instructions in frozen RF [23FC970,23FDC67), BODY SHA-256
 * 07693bb596f281583c9c3262e3574e2373854c416bba49fd4bd3db9f04edf7db.
 * No whole 4855-byte algorithm, old715/B2 adapter, callee classification, native
 * proof, hidden DF/MXCSR preservation, RFLAGS, or XMM7..15 defaults are supplied.
 */
public final class ActivityCallProtocol264Api {
    private ActivityCallProtocol264Api() { }
    public static final long OWNER_ENTRY_RVA = 0x23FC970L;

    /** Instruction target form only; no formal native signature or target semantics. */
    public record SourceSite(long callSiteRva, String instructionBytes, int instructionLength,
            TargetKind kind, Long directTargetRva, String indirectExpression) {
        public SourceSite {
            Objects.requireNonNull(instructionBytes); Objects.requireNonNull(kind);
            if (kind == TargetKind.DIRECT_RVA) {
                Objects.requireNonNull(directTargetRva);
                if (instructionLength != 5 || instructionBytes.length() != 10
                        || !instructionBytes.startsWith("e8") || indirectExpression != null)
                    throw new IllegalArgumentException("Not a held E8 direct CALL");
            } else if (instructionLength != 3 || !instructionBytes.equals("ff5010")
                    || directTargetRva != null
                    || !"qword ptr [rax + 0x10]".equals(indirectExpression)) {
                throw new IllegalArgumentException("Not a held FF5010 indirect CALL");
            }
        }
        public long continuationRva() { return callSiteRva + instructionLength; }
    }

    private static final List<SourceSite> SITES = List.of(
            direct(0x23FC9DCL, "e87fa7b501", 0x3F57160L),
            direct(0x23FCA05L, "e806a5e201", 0x4226F10L),
            direct(0x23FCA0EL, "e8cdcf48fe", 0x8899E0L),
            direct(0x23FCA32L, "e8e99ba101", 0x3E16620L),
            direct(0x23FCA42L, "e889d048fe", 0x889AD0L),
            indirect(0x23FCA56L, "ff5010"),
            direct(0x23FCA79L, "e8529548fe", 0x885FD0L),
            direct(0x23FCB01L, "e8dafcffff", 0x23FC7E0L),
            direct(0x23FCB26L, "e8f5d25ffe", 0x9F9E20L),
            direct(0x23FCB59L, "e892d53301", 0x373A0F0L),
            direct(0x23FCBAEL, "e83dd53301", 0x373A0F0L),
            direct(0x23FCBD2L, "e8890d7c00", 0x2BBD960L),
            direct(0x23FCC05L, "e82678d100", 0x3114430L),
            direct(0x23FCC18L, "e8c32cb501", 0x3F4F8E0L),
            direct(0x23FCC61L, "e80a2db601", 0x3F5F970L),
            direct(0x23FCCA0L, "e8eb6f6bff", 0x1AB3C90L),
            direct(0x23FCCC3L, "e818d53b00", 0x27BA1E0L),
            direct(0x23FCCFBL, "e8c0455dfe", 0x9D12C0L),
            direct(0x23FCD41L, "e83272e201", 0x4223F78L),
            direct(0x23FCD4BL, "e890cc48fe", 0x8899E0L),
            direct(0x23FCDC3L, "e828bba101", 0x3E188F0L),
            direct(0x23FCDEAL, "e83198a101", 0x3E16620L),
            direct(0x23FCE04L, "e8c7cc48fe", 0x889AD0L),
            indirect(0x23FCE1AL, "ff5010"),
            direct(0x23FCE36L, "e8e16de201", 0x4223C1CL),
            direct(0x23FCE55L, "e8769148fe", 0x885FD0L),
            direct(0x23FCE60L, "e8eb9145fe", 0x856050L),
            direct(0x23FCE8AL, "e831445dfe", 0x9D12C0L),
            direct(0x23FCEB4L, "e857a0e201", 0x4226F10L),
            direct(0x23FCEBDL, "e81ecb48fe", 0x8899E0L),
            direct(0x23FCEE3L, "e83897a101", 0x3E16620L),
            direct(0x23FCEF3L, "e8d8cb48fe", 0x889AD0L),
            indirect(0x23FCF07L, "ff5010"),
            direct(0x23FCF2AL, "e8a19048fe", 0x885FD0L),
            direct(0x23FCF35L, "e8169145fe", 0x856050L),
            direct(0x23FCF59L, "e862435dfe", 0x9D12C0L),
            direct(0x23FCF83L, "e8889fe201", 0x4226F10L),
            direct(0x23FCF8CL, "e84fca48fe", 0x8899E0L),
            direct(0x23FCFB2L, "e86996a101", 0x3E16620L),
            direct(0x23FCFC2L, "e809cb48fe", 0x889AD0L),
            indirect(0x23FCFD6L, "ff5010"),
            direct(0x23FCFF9L, "e8d28f48fe", 0x885FD0L),
            direct(0x23FD004L, "e8479045fe", 0x856050L),
            direct(0x23FD028L, "e8d3e3ffff", 0x23FB400L),
            direct(0x23FD044L, "e877425dfe", 0x9D12C0L),
            direct(0x23FD06EL, "e89d9ee201", 0x4226F10L),
            direct(0x23FD077L, "e864c948fe", 0x8899E0L),
            direct(0x23FD09DL, "e87e95a101", 0x3E16620L),
            direct(0x23FD0B0L, "e81bca48fe", 0x889AD0L),
            indirect(0x23FD0C4L, "ff5010"),
            direct(0x23FD0E7L, "e8e48e48fe", 0x885FD0L),
            direct(0x23FD0F2L, "e8598f45fe", 0x856050L),
            direct(0x23FD14FL, "e80ca0b501", 0x3F57160L),
            direct(0x23FD176L, "e8959de201", 0x4226F10L),
            direct(0x23FD17FL, "e85cc848fe", 0x8899E0L),
            direct(0x23FD1A6L, "e87594a101", 0x3E16620L),
            direct(0x23FD1BBL, "e810c948fe", 0x889AD0L),
            indirect(0x23FD1D1L, "ff5010"),
            direct(0x23FD1F6L, "e8d58d48fe", 0x885FD0L),
            direct(0x23FD201L, "e84a8e45fe", 0x856050L),
            direct(0x23FD24DL, "e80e9fb501", 0x3F57160L),
            direct(0x23FD277L, "e8949ce201", 0x4226F10L),
            direct(0x23FD283L, "e858c748fe", 0x8899E0L),
            direct(0x23FD2ADL, "e86e93a101", 0x3E16620L),
            direct(0x23FD2C8L, "e803c848fe", 0x889AD0L),
            indirect(0x23FD2E4L, "ff5010"),
            direct(0x23FD30FL, "e8bc8c48fe", 0x885FD0L),
            direct(0x23FD31AL, "e8318d45fe", 0x856050L),
            direct(0x23FD386L, "e8353f5dfe", 0x9D12C0L),
            direct(0x23FD3B0L, "e85b9be201", 0x4226F10L),
            direct(0x23FD3BCL, "e81fc648fe", 0x8899E0L),
            direct(0x23FD3E4L, "e83792a101", 0x3E16620L),
            direct(0x23FD3FEL, "e8cdc648fe", 0x889AD0L),
            indirect(0x23FD418L, "ff5010"),
            direct(0x23FD441L, "e88a8b48fe", 0x885FD0L),
            direct(0x23FD44CL, "e8ff8b45fe", 0x856050L),
            direct(0x23FD4C7L, "e8949cb501", 0x3F57160L),
            direct(0x23FD4F4L, "e8f748dcfe", 0x11C1DF0L),
            direct(0x23FD513L, "e8b88a48fe", 0x885FD0L),
            direct(0x23FD58FL, "e8cc9bb501", 0x3F57160L),
            direct(0x23FD5C0L, "e82b48dcfe", 0x11C1DF0L),
            direct(0x23FD5DFL, "e8ec8948fe", 0x885FD0L),
            direct(0x23FD608L, "e843f47b00", 0x2BBCA50L),
            direct(0x23FD661L, "e82e65e201", 0x4223B94L),
            direct(0x23FD670L, "e84b903c01", 0x37C66C0L),
            direct(0x23FD69AL, "e8b1f37b00", 0x2BBCA50L),
            direct(0x23FD6AAL, "e8e564e201", 0x4223B94L),
            direct(0x23FD6B9L, "e802903c01", 0x37C66C0L),
            direct(0x23FD6D4L, "e897da3e01", 0x37EB170L),
            direct(0x23FD6DCL, "e88fdb3e01", 0x37EB270L),
            direct(0x23FD6F5L, "e8a6053601", 0x375DCA0L),
            direct(0x23FD706L, "e8f526daff", 0x219FE00L),
            direct(0x23FD713L, "e82c68e201", 0x4223F44L),
            direct(0x23FD733L, "e8289ab501", 0x3F57160L),
            direct(0x23FD751L, "e87a8848fe", 0x885FD0L),
            direct(0x23FD78FL, "e8b067e201", 0x4223F44L),
            direct(0x23FD7CBL, "e8a0f77b00", 0x2BBCF70L),
            direct(0x23FD7FEL, "e85d99b501", 0x3F57160L),
            direct(0x23FD82BL, "e8c045dcfe", 0x11C1DF0L),
            direct(0x23FD84AL, "e8818748fe", 0x885FD0L),
            direct(0x23FD854L, "e8f78745fe", 0x856050L),
            direct(0x23FD8A4L, "e827c03901", 0x37998D0L),
            direct(0x23FD8CDL, "e8febf3901", 0x37998D0L),
            direct(0x23FD9DDL, "e8de385dfe", 0x9D12C0L),
            direct(0x23FDA06L, "e80595e201", 0x4226F10L),
            direct(0x23FDA12L, "e8c9bf48fe", 0x8899E0L),
            direct(0x23FDA37L, "e8e48ba101", 0x3E16620L),
            direct(0x23FDA4EL, "e87dc048fe", 0x889AD0L),
            indirect(0x23FDA6AL, "ff5010"),
            direct(0x23FDA81L, "e80a8bb501", 0x3F56590L),
            direct(0x23FDA8BL, "e8c08545fe", 0x856050L),
            direct(0x23FDAC1L, "e82a0c7c00", 0x2BBE6F0L),
            direct(0x23FDAD7L, "e8140cd100", 0x310E6F0L),
            direct(0x23FDAFCL, "e85f26f3ff", 0x2330160L),
            direct(0x23FDB0FL, "e8cc0548fe", 0x87E0E0L),
            direct(0x23FDB45L, "e81696b501", 0x3F57160L),
            direct(0x23FDB6EL, "e89d93e201", 0x4226F10L),
            direct(0x23FDB7AL, "e861be48fe", 0x8899E0L),
            direct(0x23FDB9FL, "e87c8aa101", 0x3E16620L),
            direct(0x23FDBB6L, "e815bf48fe", 0x889AD0L),
            indirect(0x23FDBD1L, "ff5010"),
            direct(0x23FDBF6L, "e8d58348fe", 0x885FD0L),
            direct(0x23FDC00L, "e84b8445fe", 0x856050L),
            direct(0x23FDC22L, "e8494ee301", 0x4232A70L),
            direct(0x23FDC2FL, "e8505ee201", 0x4223A84L),
            direct(0x23FDC5CL, "e8c35de201", 0x4223A24L));

    public static List<SourceSite> allSites() { return SITES; }

    public static SourceSite requireSite(long siteRva) {
        for (SourceSite source : SITES)
            if (source.callSiteRva() == siteRva) return source;
        throw new UnsupportedOperationException("Not a frozen activity259 CALL: "
                + Long.toHexString(siteRva));
    }

    private static SourceSite direct(long site, String bytes, long target) {
        return new SourceSite(site, bytes, 5, TargetKind.DIRECT_RVA, target, null);
    }
    private static SourceSite indirect(long site, String bytes) {
        return new SourceSite(site, bytes, 3, TargetKind.INDIRECT_ABSOLUTE, null,
                "qword ptr [rax + 0x10]");
    }

    /** SAME actual Registers/Context and SAME owned RAM as the future instruction body. */
    public record Binding(long imageBaseBits, Registers registers,
            PostState240Api.Context context, GovernmentCrtBoundary185Api.Memory memory) {
        public Binding {
            Objects.requireNonNull(registers); Objects.requireNonNull(context);
            Objects.requireNonNull(memory);
            if (!context.boundTo(imageBaseBits, registers))
                throw new IllegalArgumentException("Context is not bound to these actual registers/image");
        }
    }

    /** Immutable, internally prepared frame. The port receives the same Memory object by identity. */
    public static final class Frame {
        private final SourceSite source;
        private final PostState240Api.Input before;
        private final GovernmentCrtBoundary185Api.Call call;
        private final PostState240Api.Input childInput;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final long returnRipBits;

        private Frame(SourceSite source, PostState240Api.Input before, long targetBits,
                GovernmentCrtBoundary185Api.Memory memory) {
            this.source = Objects.requireNonNull(source);
            this.before = Objects.requireNonNull(before);
            this.memory = Objects.requireNonNull(memory);
            var pre = before.entry();
            call = new GovernmentCrtBoundary185Api.Call(source.callSiteRva(), source.kind(),
                    targetBits, pre.rspBits(), pre.volatileBits(), pre.nonvolatileBits());
            childInput = new PostState240Api.Input(new GovernmentCrtBoundary185Api.Entry(
                    pre.imageBaseBits(), pre.rspBits() - 8L, pre.volatileBits(), pre.nonvolatileBits()),
                    before.directionFlagSet(), before.mxcsr(), source.callSiteRva());
            returnRipBits = pre.imageBaseBits() + source.continuationRva();
            if (source != requireSite(source.callSiteRva())
                    || (source.kind() == TargetKind.DIRECT_RVA
                        && targetBits != source.directTargetRva().longValue()))
                throw new IllegalArgumentException("Not the exact frozen source CALL");
        }
        public SourceSite source() { return source; }
        public PostState240Api.Input before() { return before; }
        public GovernmentCrtBoundary185Api.Call call() { return call; }
        public PostState240Api.Input childInput() { return childInput; }
        public GovernmentCrtBoundary185Api.Memory memory() { return memory; }
        public long returnRipBits() { return returnRipBits; }

        /** Validate represented opaque normal preservation before any caller register commit. */
        public void checkNormalReturn(QueueFp604Api.Normal normal) {
            Objects.requireNonNull(normal);
            var nr = normal.base().normalReturn();
            if (nr.returnRipBits() != returnRipBits)
                throw new IllegalArgumentException("Normal continuation RIP mismatch");
            if (nr.callerRspBits() != call.rspBits())
                throw new IllegalArgumentException("Normal caller preSP mismatch");
            if (!nr.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Opaque normal changed supplied represented N");
        }
    }

    /**
     * Required whole-entry producer contract only; no implementation is supplied here.
     * Execute actual entry RVA 23FC970 from this exact 240 Input and the same owned RAM.
     * The producer must execute the full normal source and actual epilogue/RET, returning
     * an explicit 604 Outcome. Old185 scalar/NormalReturn producers cannot implement this
     * contract by inventing DF/MXCSR, absent flags, vector state or child effects.
     */
    @FunctionalInterface
    public interface WholeActivityEntry extends PostState240Api.EntryExecutor { }

    @FunctionalInterface
    public interface FullOutcomePort {
        /**
         * Execute the actual whole qualified child from childInput(), using frame.memory()
         * by identity. CALL push already exists: do not push again or repair/replay the parent.
         * Supply all represented V/DF/partial-MXCSR and actual RIP/SP/N on Normal; a scalar
         * or old NormalReturn cannot be upgraded by assuming preservation. Any Stopped must
         * be the actual owned child's object/snapshot; no fabricated parent snapshot.
         * Unsupported unrepresented effects remain ordinary errors unless an actual typed
         * whole child independently supplies its truthful Stopped.
         */
        QueueFp604Api.Outcome invoke(Frame actualFrame);
    }

    /**
     * Exactly one push per invocation. No catch, retry, stack restore, hardware query, or
     * fabricated Outcome. Indirect address evaluation uses the same RAM once before push.
     * Child ports mutate shared RAM, never the bound caller Registers/Context themselves.
     * Stopped returns by identity without a normal check, commit, continuation or snapshot rewrite.
     */
    public static QueueFp604Api.Outcome invokeOwnedCall(long siteRva, Binding binding,
            FullOutcomePort wholeQualifiedOpaque) {
        Objects.requireNonNull(binding); Objects.requireNonNull(wholeQualifiedOpaque);
        SourceSite source = requireSite(siteRva);
        var context = binding.context();
        context.beforeInstruction(siteRva);
        var before = new PostState240Api.Input(context.currentState(), context.directionFlagSet(),
                context.mxcsr(), context.originCallSiteRva());
        long target = source.kind() == TargetKind.DIRECT_RVA
                ? source.directTargetRva().longValue()
                : binding.memory().readQword(before.entry().volatileBits().raxBits() + 0x10L);
        var frame = new Frame(source, before, target, binding.memory());
        binding.memory().writeQword(frame.childInput().entry().rspBits(), frame.returnRipBits());
        QueueFp604Api.Outcome offered = wholeQualifiedOpaque.invoke(frame);
        if (offered == null)
            throw new IllegalStateException("Whole child supplied no explicit Outcome");
        if (offered instanceof QueueFp604Api.Stopped) return offered;
        QueueFp604Api.Normal normal = (QueueFp604Api.Normal) offered;
        frame.checkNormalReturn(normal);
        if (context.instructionRva() != siteRva
                || !context.currentState().equals(before.entry())
                || context.directionFlagSet() != before.directionFlagSet()
                || !context.mxcsr().equals(before.mxcsr()))
            throw new IllegalStateException("Child port mutated the bound caller state outside its Outcome");
        context.acceptNormal(normal, frame.returnRipBits(), frame.call().rspBits(), false);
        return offered;
    }
}
