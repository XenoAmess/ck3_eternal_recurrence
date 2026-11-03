package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213;
import org.xar.ck3.control.g2.common.nativecore.task.captured.WordCompare4246a60221;
import org.xar.ck3.control.g2.m2.nativecode.Indexed448Fp628Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Source-scoped carrier for Indexed448 FP/DF knowledge in the queue/append context.
 * No FP implementation, no native proof, no old file rewrite.
 */
public final class WordCompareFp630 {
    private WordCompareFp630() { }

    /**
     * Binds a foreign Indexed448 Calls implementation to handle specific direct calls
     * to the WordCompare4246A60 algorithm, delegating to the existing captured implementation.
     */
    public static Indexed448Fp628Api.Calls bind(TerminalTailTarget42421c8213.Memory16 memory, Indexed448Fp628Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(foreign);

        return new Indexed448Fp628Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Indexed448Fp628Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                // Match only full sites 424E514/424E52A DIRECT_RVA target 4246A60
                long site = frame.original().callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = frame.original().kind();
                long target = frame.original().targetBits();

                if (kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    target == 0x4246A60L &&
                    (site == 0x424E514L || site == 0x424E52AL)) {

                    // Incoming 628Frame already owns actual 5B push.
                    // One existing WordCompare4246a60221.execute(frame.childEntry(), same memory), not copy 44 algorithm/MemoryView.
                    GovernmentCrtBoundary185Api.NormalReturn actual = WordCompare4246a60221.execute(frame.childEntry(), memory);

                    // Wrap old NormalReturn as FullCopy437Api.CallResult(actual, frame.directionFlagSet())
                    FullCopy437Api.CallResult base = new FullCopy437Api.CallResult(actual, frame.directionFlagSet());

                    // Validate frame.checkNormalReturn BEFORE new QueueFp604Api.Normal(base, frame.preMxcsr())
                    frame.checkNormalReturn(base);

                    // Preserve exact incoming partial Mxcsr object, no default or KnownControl requirement.
                    // Body normal 44 has integer instructions/0 CALL/0 write; does not write DF/XMM/MXCSR.
                    return new QueueFp604Api.Normal(base, frame.preMxcsr());
                }

                // Others 5 legal IAT frames foreign same frame once/exact Outcome identity/null reject
                QueueFp604Api.Outcome foreignOutcome = foreign.invoke(frame);
                Objects.requireNonNull(foreignOutcome);
                return foreignOutcome;
            }
        };
    }
}