package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.study.m6.indexed230.Indexed448FullState230;

/** State carrier only; the mature470B producer owns lookup, exchange, budget and stack effects. */
public final class KnownE900IndexedFp628 {
    private KnownE900IndexedFp628() { }
    private static final class StopSignal extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;
        StopSignal(QueueFp604Api.Stopped outcome) { this.outcome=outcome; }
    }
    public static E900Fp627Api.Calls bind(AtomicIndexedMemory229 memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,Indexed448Fp628Api.Calls inner,
            E900Fp627Api.Calls foreign) {
        Objects.requireNonNull(memory);Objects.requireNonNull(budget);
        Objects.requireNonNull(inner);Objects.requireNonNull(foreign);
        return new E900Fp627Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(E900Fp627Api.CallFrame frame) {
                Objects.requireNonNull(frame);var call=frame.original();
                if(call.callSiteRva()!=0x424E922L||call.kind()!=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA||call.targetBits()!=0x424E448L)
                    return Objects.requireNonNull(foreign.invoke(frame));
                boolean[] df={frame.directionFlagSet()};QueueFp604Api.Mxcsr[] fp={frame.preMxcsr()};
                var lower=new GovernmentCrtBoundary185Api.Calls() {
                    @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call actual) {
                        var child=new GovernmentCrtBoundary185Api.Entry(frame.childEntry().imageBaseBits(),actual.rspBits()-8,
                                actual.volatileBits(),actual.nonvolatileBits());
                        var offeredFrame=new Indexed448Fp628Api.CallFrame(actual,child,df[0],fp[0]);
                        var outcome=Objects.requireNonNull(inner.invoke(offeredFrame));
                        if(outcome instanceof QueueFp604Api.Stopped stopped)throw new StopSignal(stopped);
                        var normal=(QueueFp604Api.Normal)outcome;
                        offeredFrame.checkNormalReturn(normal.base());
                        df[0]=normal.base().postDirectionFlagSet();fp[0]=normal.postMxcsr();
                        return normal.base().normalReturn().volatileBits();
                    }
                    @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                        throw new UnsupportedOperationException("No tail in held Indexed448 normal body");
                    }
                    @Override public long readGsQword58() {
                        throw new UnsupportedOperationException("No GS read in held Indexed448 normal body");
                    }
                };
                try {
                    var actual=Indexed448FullState230.execute(frame.childEntry(),memory,lower,budget);
                    var base=new FullCopy437Api.CallResult(actual,df[0]);frame.checkNormalReturn(base);
                    return new QueueFp604Api.Normal(base,fp[0]);
                } catch(StopSignal stopped) {return stopped.outcome;}
            }
            @Override public QueueFp604Api.Outcome tail(E900Fp627Api.TailFrame frame) {
                return Objects.requireNonNull(foreign.tail(Objects.requireNonNull(frame)));
            }
        };
    }
}
