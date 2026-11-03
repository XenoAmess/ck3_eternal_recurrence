package org.xar.ck3.study.m6.full238;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.forward237.KnownStaticVirtualFull237;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Floating;

/** Only the four actual715 virtual sites may resolve to the supplied complete forwarding entries. */
public final class KnownTransferForward238 {
    private KnownTransferForward238() { }
    public static NormalReturn execute(Entry entry, Memory memory, Calls lower, LoopBudget childBudget,
            Floating floating, Budget budget) {
        long image=entry.imageBaseBits();
        Calls adapter=new Calls() {
            @Override public VolatileBits invoke(Call call) {
                long site=call.callSiteRva();
                boolean release=site==0x21A508FL || site==0x21A5159L || site==0x21A5223L;
                boolean allocate=site==0x21A51B9L;
                if(call.kind()==TargetKind.INDIRECT_ABSOLUTE
                        && ((release && call.targetBits()==image+0x855830L)
                            || (allocate && call.targetBits()==image+0x855870L))) {
                    Entry child=new Entry(image,call.rspBits()-0x8L,call.volatileBits(),call.nonvolatileBits());
                    NormalReturn returned=release
                            ? KnownStaticVirtualFull237.fromSlot10(child,memory,lower,childBudget)
                            : KnownStaticVirtualFull237.fromSlot08(child,memory,lower,childBudget);
                    if(returned.returnRipBits()!=image+site+0x3L || returned.callerRspBits()!=call.rspBits()
                            || !returned.nonvolatileBits().equals(call.nonvolatileBits()))
                        throw new UnsupportedOperationException("known forwarding child did not meet this normal CALL contract");
                    return returned.volatileBits();
                }
                return lower.invoke(call);
            }
            @Override public NormalReturn tail(Tail transfer) { return lower.tail(transfer); }
            @Override public long readGsQword58() { return lower.readGsQword58(); }
        };
        return TransferFull238.execute(entry,memory,adapter,floating,budget);
    }
}
