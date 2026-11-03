package org.xar.ck3.research.m3.rangereverse261;

import java.util.Objects;
import org.xar.ck3.research.m3.range9d260.Range9DFp260Api;
import org.xar.ck3.research.m3.range9d260.Range9DFullState260;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.Reverse641Api;
import org.xar.ck3.control.g2.m2.nativecode.ReverseFullState641;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Same-RAM composition of the held three-call protocol and represented reverse body. */
public final class RangeReverse261 {
    private RangeReverse261() { }
    public interface Memory extends Range9DFp260Api.Memory, Reverse641Api.Memory { }
    public static Range9DFp260Api.Calls bind(Memory memory,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(memory);Objects.requireNonNull(budget);
        return frame->{
            Objects.requireNonNull(frame);
            var input=new QueueFp604Api.Input(new FullCopy437Api.Input(frame.childEntry(),frame.directionFlagSet(),budget),frame.preMxcsr());
            QueueFp604Api.Normal normal=ReverseFullState641.execute(input,memory);
            frame.checkNormalReturn(normal);
            return normal;
        };
    }
    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,Memory memory) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);
        return Range9DFullState260.execute(input,memory,bind(memory,input.base().budget()));
    }
}
