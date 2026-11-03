package org.xar.ck3.study.m6.poststate240;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** New source-only carrier proposal. No default DF, MXCSR, FP algorithm or hardware claim. */
public final class PostState240Api {
    private PostState240Api() { }

    /** originCallSiteRva is supplied by the actual caller, including known recursive CALLs. */
    public record Input(GovernmentCrtBoundary185Api.Entry entry, boolean directionFlagSet,
            QueueFp604Api.Mxcsr mxcsr, long originCallSiteRva) {
        public Input { Objects.requireNonNull(entry); Objects.requireNonNull(mxcsr); }
    }

    /** A whole qualified producer, never a wrapper that invents post-state around an old NR. */
    @FunctionalInterface
    public interface EntryExecutor {
        QueueFp604Api.Outcome execute(Input input, GovernmentCrtBoundary185Api.Memory memory);
    }

    /** Explicit typed suppliers. A missing implementation may truthfully stop, never wrap old NR. */
    public record KnownEntryRegistry(EntryExecutor whole715, EntryExecutor wholeMove4,
            EntryExecutor wholeSwap4) {
        public KnownEntryRegistry {
            Objects.requireNonNull(whole715); Objects.requireNonNull(wholeMove4);
            Objects.requireNonNull(wholeSwap4);
        }
    }

    /** Immutable actual register/DF/MXCSR snapshot immediately before one source SSE instruction. */
    public record FpFrame(QueueFp604Api.Snapshot before, long originCallSiteRva) {
        public FpFrame { Objects.requireNonNull(before); }
    }

    public sealed interface VectorResult permits VectorCompleted, StageStopped { }
    public sealed interface IntegerResult permits IntegerCompleted, StageStopped { }

    /** postMxcsr includes explicit knowledge of status as well as controls; no preservation inference. */
    public record VectorCompleted(Bits128 xmm0Bits, boolean postDirectionFlagSet,
            QueueFp604Api.Mxcsr postMxcsr) implements VectorResult {
        public VectorCompleted { Objects.requireNonNull(xmm0Bits); Objects.requireNonNull(postMxcsr); }
    }

    public record IntegerCompleted(int eaxRaw32, boolean postDirectionFlagSet,
            QueueFp604Api.Mxcsr postMxcsr) implements IntegerResult {
        public IntegerCompleted { Objects.requireNonNull(postMxcsr); }
    }

    /** The owned stage supplies the actual stop. This carrier never invents an entry snapshot. */
    public record StageStopped(QueueFp604Api.Stopped actual) implements VectorResult, IntegerResult {
        public StageStopped { Objects.requireNonNull(actual); }
    }

    /**
     * Stage qualification belongs to its explicit owner-supplied provider: exact source opcode/RVA,
     * lane preservation and retention of every previously known MXCSR control bit (mask FFC0).
     * Explicit post-state supplies status knowledge separately; no control-to-status inference.
     */
    public interface FloatingStages {
        VectorResult convertSignedDwords(FpFrame frame);
        VectorResult multiplyLowSingle(FpFrame frame, int multiplierRaw32);
        IntegerResult truncateLowSingle(FpFrame frame);
    }

    /** Mechanical source CALL hooks supplied at whole-entry construction; no default child effects. */
    public interface CallHooks {
        void indirect(long siteRva, long resolvedTargetBits);
        void direct(long siteRva, long targetRva);
        void recursive(long siteRva);
    }

    /** Optional ports are only required when their actual source operation is reached. */
    public record FrameBindings(Context context, FloatingStages floatingStages, CallHooks callHooks) {
        public FrameBindings { Objects.requireNonNull(context); }
    }

    /**
     * Only this typed control transfer may be caught by a new whole-Outcome entry.
     * Arbitrary Memory/Budget/legacy-port exceptions must keep propagating as themselves.
     */
    public static final class StoppedTransfer extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final transient QueueFp604Api.Stopped actual;
        private StoppedTransfer(QueueFp604Api.Stopped actual) {
            super(null, null, false, false);
            this.actual = Objects.requireNonNull(actual);
        }
        public QueueFp604Api.Stopped actual() { return actual; }
    }

    /**
     * Holds the SAME mutable Registers as the instruction body. No RAM or register replay.
     * Source sites explicitly mark the current instruction before an effectful operation.
     */
    public static final class Context {
        private final long image;
        private final Registers registers;
        private final long originCallSiteRva;
        private boolean directionFlagSet;
        private QueueFp604Api.Mxcsr mxcsr;
        private long instructionRva;

        public Context(long image, Registers actualRegisters, boolean directionFlagSet,
                QueueFp604Api.Mxcsr mxcsr, long entryInstructionRva, long originCallSiteRva) {
            this.image = image;
            registers = Objects.requireNonNull(actualRegisters);
            this.directionFlagSet = directionFlagSet;
            this.mxcsr = Objects.requireNonNull(mxcsr);
            instructionRva = entryInstructionRva;
            this.originCallSiteRva = originCallSiteRva;
        }

        public boolean directionFlagSet() { return directionFlagSet; }
        public QueueFp604Api.Mxcsr mxcsr() { return mxcsr; }
        public long instructionRva() { return instructionRva; }
        public long originCallSiteRva() { return originCallSiteRva; }
        public boolean boundTo(long actualImage, Registers actualRegisters) {
            return image == actualImage && registers == actualRegisters;
        }

        /** Marker only: does not execute, read memory, manufacture flags, or consume a budget. */
        public void beforeInstruction(long actualInstructionRva) { instructionRva = actualInstructionRva; }

        public GovernmentCrtBoundary185Api.Entry currentState() {
            return new GovernmentCrtBoundary185Api.Entry(image, registers.rsp,
                    registers.volatileBits(), registers.nonvolatileBits());
        }

        public QueueFp604Api.Snapshot snapshot() {
            return new QueueFp604Api.Snapshot(currentState(), instructionRva, directionFlagSet, mxcsr);
        }

        public FpFrame fpFrame(long actualInstructionRva) {
            beforeInstruction(actualInstructionRva);
            return new FpFrame(snapshot(), originCallSiteRva);
        }

        /** For an already typed child Outcome; Stopped is carried by identity, with no parent snapshot. */
        public static QueueFp604Api.Normal normalOrTransfer(QueueFp604Api.Outcome offered) {
            Objects.requireNonNull(offered);
            if (offered instanceof QueueFp604Api.Stopped stopped) throw new StoppedTransfer(stopped);
            return (QueueFp604Api.Normal) offered;
        }

        /**
         * Apply a validated actual whole-child normal return once. Opaque ports preserve supplied N;
         * known source bodies may return their actual freshly restored N. No RAX-only adapter.
         */
        public void acceptNormal(QueueFp604Api.Normal actual, long expectedReturnRip,
                long expectedCallerRsp, boolean applyActualNonvolatile) {
            Objects.requireNonNull(actual);
            var returned = actual.base().normalReturn();
            if (returned.returnRipBits() != expectedReturnRip || returned.callerRspBits() != expectedCallerRsp)
                throw new IllegalArgumentException("Child normal return RIP/RSP mismatch");
            if (!applyActualNonvolatile && !returned.nonvolatileBits().equals(registers.nonvolatileBits()))
                throw new IllegalArgumentException("Opaque child changed supplied nonvolatile state");
            registers.apply(returned.volatileBits());
            if (applyActualNonvolatile) applyNonvolatile(returned.nonvolatileBits());
            registers.rsp = returned.callerRspBits();
            directionFlagSet = actual.base().postDirectionFlagSet();
            mxcsr = actual.postMxcsr();
        }

        private void applyNonvolatile(NonvolatileBits n) {
            registers.rbx = n.rbxBits(); registers.rbp = n.rbpBits();
            registers.rsi = n.rsiBits(); registers.rdi = n.rdiBits();
            registers.r12 = n.r12Bits(); registers.r13 = n.r13Bits();
            registers.r14 = n.r14Bits(); registers.r15 = n.r15Bits(); registers.x6 = n.xmm6();
        }

        /** Whole source epilogue has already read its actual RET and incremented actual RSP. */
        public QueueFp604Api.Normal finishNormal(long actualReturnRip) {
            var nr = new GovernmentCrtBoundary185Api.NormalReturn(registers.volatileBits(),
                    actualReturnRip, registers.rsp, registers.nonvolatileBits());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr, directionFlagSet), mxcsr);
        }

        private void requireCurrent(FpFrame offered) {
            Objects.requireNonNull(offered);
            if (offered.originCallSiteRva() != originCallSiteRva || !offered.before().equals(snapshot()))
                throw new IllegalArgumentException("FP frame is not this exact current instruction state");
        }

        private void acceptStageStop(FpFrame before, QueueFp604Api.Stopped stopped) {
            var actual = stopped.snapshot();
            if (stopped.originCallSiteRva() != originCallSiteRva
                    || actual.instructionRva() != before.before().instructionRva()
                    || !actual.currentState().equals(before.before().currentState())
                    || actual.directionFlagSet() != before.before().directionFlagSet())
                throw new IllegalArgumentException("FP stopped snapshot changed the pre-commit instruction state");
            if (stopped.reason() != QueueFp604Api.StopReason.ARCHITECTURAL_FP_CONDITION
                    && !actual.mxcsr().equals(before.before().mxcsr()))
                throw new IllegalArgumentException("Unexecuted FP stop changed MXCSR");
            directionFlagSet = actual.directionFlagSet(); mxcsr = actual.mxcsr();
            throw new StoppedTransfer(stopped);
        }

        /** Commit XMM0 only after successful stage; unmasked/unsupported stops commit no destination. */
        public void acceptVector(FpFrame before, VectorResult result) {
            requireCurrent(before); Objects.requireNonNull(result);
            if (result instanceof StageStopped stopped) { acceptStageStop(before, stopped.actual()); return; }
            VectorCompleted completed = (VectorCompleted) result;
            if (completed.postDirectionFlagSet() != before.before().directionFlagSet())
                throw new IllegalArgumentException("SSE instruction changed DF");
            registers.x0 = completed.xmm0Bits();
            directionFlagSet = completed.postDirectionFlagSet(); mxcsr = completed.postMxcsr();
        }

        /** Commit zero-extended EAX only after successful CVTT stage; XMM0 remains unchanged. */
        public void acceptInteger(FpFrame before, IntegerResult result) {
            requireCurrent(before); Objects.requireNonNull(result);
            if (result instanceof StageStopped stopped) { acceptStageStop(before, stopped.actual()); return; }
            IntegerCompleted completed = (IntegerCompleted) result;
            if (completed.postDirectionFlagSet() != before.before().directionFlagSet())
                throw new IllegalArgumentException("SSE instruction changed DF");
            registers.rax = Integer.toUnsignedLong(completed.eaxRaw32());
            directionFlagSet = completed.postDirectionFlagSet(); mxcsr = completed.postMxcsr();
        }
    }
}
