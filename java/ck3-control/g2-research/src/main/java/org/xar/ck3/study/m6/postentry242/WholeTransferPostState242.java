package org.xar.ck3.study.m6.postentry242;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.full238.TransferFull238;
import org.xar.ck3.study.m6.full238.TransferFull238Api;
import org.xar.ck3.study.m6.full239.Move4Full239;
import org.xar.ck3.study.m6.full239.Swap4Full239;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;

/**
 * New whole-Outcome entry wiring, using each original source body exactly once on its actual Frame.
 * Requires the sole240 post-mode Frame/direct guard and sole243 growth-stage hunks as one source cohort.
 * It never executes old execute first or invents post DF/MXCSR around an old standalone NR.
 */
public final class WholeTransferPostState242 {
    private final PostState240Api.FloatingStages floatingStages;
    private final TransferFull238Api.Budget budget;
    private final CallOutcome242Api.OutcomePort opaqueCalls;

    /** Explicit typed FP and child ports are required; no default stage or child algorithm. */
    public WholeTransferPostState242(PostState240Api.FloatingStages floatingStages,
            TransferFull238Api.Budget budget,CallOutcome242Api.OutcomePort opaqueCalls) {
        this.floatingStages=Objects.requireNonNull(floatingStages);
        this.budget=Objects.requireNonNull(budget);
        this.opaqueCalls=Objects.requireNonNull(opaqueCalls);
    }

    public QueueFp604Api.Outcome transfer715(PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        return execute(Whole.TRANSFER715,input,memory);
    }
    public QueueFp604Api.Outcome move4(PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        return execute(Whole.MOVE4,input,memory);
    }
    public QueueFp604Api.Outcome swap4(PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        return execute(Whole.SWAP4,input,memory);
    }

    private QueueFp604Api.Outcome execute(Whole whole,PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(input);
        GovernmentCrtBoundary185Api.Entry entry=input.entry();
        // Same source entry budget before Frame construction and every prologue Memory effect.
        budget.before(whole.entryRva,entry.rspBits(),0L);
        // Sole240 constructor binds the same Registers/Context and source target registry.
        TransferFull238Api.Frame frame=new TransferFull238Api.Frame(input,memory,floatingStages,
                budget,opaqueCalls,new PostState240Api.KnownEntryRegistry(
                        this::transfer715,this::move4,this::swap4),whole.entryRva);
        PostState240Api.Context context=frame.postStateContext();
        try {
            GovernmentCrtBoundary185Api.NormalReturn returned=switch(whole) {
                case TRANSFER715 -> TransferFull238.executePreparedFrame(frame);
                case MOVE4 -> Move4Full239.executePreparedFrame(frame);
                case SWAP4 -> Swap4Full239.executePreparedFrame(frame);
            };
            // Body already read its true RET and advanced this SAME Registers, with no replay.
            if(returned.callerRspBits()!=frame.r.rsp
                    || !returned.volatileBits().equals(frame.r.volatileBits())
                    || !returned.nonvolatileBits().equals(frame.r.nonvolatileBits()))
                throw new IllegalStateException("Shared whole body NR differs from its actual Registers");
            return context.finishNormal(returned.returnRipBits());
        } catch(PostState240Api.StoppedTransfer stopped) {
            // No catch-all, parent snapshot, epilogue, second execution or fabricated normal return.
            return stopped.actual();
        }
    }

    private enum Whole {
        TRANSFER715(0x21A5050L),MOVE4(0xB2EEE0L),SWAP4(0xB2EDF0L);
        private final long entryRva;
        Whole(long entryRva) { this.entryRva=entryRva; }
    }
}
