package org.xar.ck3.study.m6.poststate240;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Provider;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Sites;

/** Context-only adapter to the sole242 site/push/Outcome provider; no child body or second push. */
public final class FrameCallHooks240 implements PostState240Api.CallHooks {
    private final long ownerEntryRva;
    private final PostState240Api.Context context;
    private final GovernmentCrtBoundary185Api.Memory memory;
    private final CallOutcome242Api.Ports ports;

    public FrameCallHooks240(long ownerEntryRva, PostState240Api.Context context,
            GovernmentCrtBoundary185Api.Memory memory, CallOutcome242Api.Ports ports) {
        this.ownerEntryRva = ownerEntryRva;
        this.context = Objects.requireNonNull(context);
        this.memory = Objects.requireNonNull(memory);
        this.ports = Objects.requireNonNull(ports);
    }

    @Override public void indirect(long siteRva, long resolvedTargetBits) {
        var source = CallOutcome242Sites.require(ownerEntryRva, siteRva);
        if (source.kind() != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE)
            throw new IllegalArgumentException("Not a held indirect CALL");
        invoke(siteRva, resolvedTargetBits);
    }

    @Override public void direct(long siteRva, long targetRva) {
        var source = CallOutcome242Sites.require(ownerEntryRva, siteRva);
        if (source.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                || source.normalRule() != CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N)
            throw new IllegalArgumentException("Not a held external direct CALL");
        invoke(siteRva, targetRva);
    }

    @Override public void recursive(long siteRva) {
        var source = CallOutcome242Sites.require(ownerEntryRva, siteRva);
        if (source.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                || source.normalRule() != CallOutcome242Api.NormalRule.KNOWN_ACTUAL_N)
            throw new IllegalArgumentException("Not a held known recursive or mutual CALL");
        invoke(siteRva, source.directTargetRva());
    }

    private void invoke(long siteRva, long targetBits) {
        context.beforeInstruction(siteRva);
        var frame = CallOutcome242Provider.prepare(ownerEntryRva, siteRva, targetBits,
                context.currentState(), context.directionFlagSet(), context.mxcsr());
        QueueFp604Api.Outcome offered = CallOutcome242Provider.invokePrepared(frame, memory, ports);
        context.acceptNormal(PostState240Api.Context.normalOrTransfer(offered),
                frame.returnRipBits(), frame.call().rspBits(),
                frame.normalRule() == CallOutcome242Api.NormalRule.KNOWN_ACTUAL_N);
    }

    /** Only typed whole entries qualify. This is not an adapter for old185-only NR producers. */
    public static CallOutcome242Api.OutcomePort knownEntries(GovernmentCrtBoundary185Api.Memory memory,
            PostState240Api.EntryExecutor whole715, PostState240Api.EntryExecutor wholeMove4,
            PostState240Api.EntryExecutor wholeSwap4) {
        Objects.requireNonNull(memory);
        return frame -> {
            Objects.requireNonNull(frame);
            if (frame.normalRule() != CallOutcome242Api.NormalRule.KNOWN_ACTUAL_N
                    || frame.call().kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA)
                throw new IllegalArgumentException("Not a qualified known whole CALL");
            PostState240Api.EntryExecutor selected;
            if (frame.call().targetBits() == 0x21A5050L) selected = whole715;
            else if (frame.call().targetBits() == 0xB2EEE0L) selected = wholeMove4;
            else if (frame.call().targetBits() == 0xB2EDF0L) selected = wholeSwap4;
            else throw new IllegalArgumentException("Not a held whole target");
            var input = new PostState240Api.Input(frame.childEntry(), frame.preDirectionFlagSet(),
                    frame.preMxcsr(), frame.call().callSiteRva());
            return Objects.requireNonNull(Objects.requireNonNull(selected).execute(input, memory));
        };
    }
}
