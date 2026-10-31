package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentAbf170CaseApi.BudgetScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;

/** Scope172 data only: exact full193 inputs and literal finite observations, with no target evaluator. */
public final class GovernmentFull193172CaseApi {
    private GovernmentFull193172CaseApi() { }

    public record HashEvent(long headerRva,long r8Bits,long r9dBits,long rbxBits) { }
    private record HashStep(HashEvent event,Runnable sideEffect) { }

    /** Exact native loop-header observations, not a count clamp or a substitute hash implementation. */
    public static final class HashScript implements GovernmentByteUpdate169Api.LoopBudget {
        private final List<HashStep> expected=new ArrayList<>();
        public final List<HashEvent> actual=new ArrayList<>();
        private int index;

        public HashScript expect(long headerRva,long r8Bits,long r9dBits,long rbxBits,Runnable effect) {
            expected.add(new HashStep(new HashEvent(headerRva,r8Bits,r9dBits,rbxBits),Objects.requireNonNull(effect)));
            return this;
        }

        @Override public void beforeIteration(long headerRva,long r8Bits,long r9dBits,long rbxBits) {
            HashEvent event=new HashEvent(headerRva,r8Bits,r9dBits,rbxBits);
            actual.add(event);
            if(index==expected.size())
                throw new UnsupportedOperationException("unapproved hash work "+event);
            HashStep step=expected.get(index++);
            equal(step.event(),event,"literal hash work "+index);
            step.sideEffect().run();
        }

        public void done() { equal(expected.size(),index,"hash work event count"); }
    }

    /** ownedMxcsrAtHash is mandatory caller-owned input at this one actual hash boundary. */
    public record Case(String name,GovernmentRowResolve164Api.Entry entry,MemoryImage memory,
            CallScript delegate,GovernmentLookup167Api.SpinBudget lookupBudget,
            BudgetScript resolveBudget,HashScript hashBudget,Mxcsr32 ownedMxcsrAtHash,
            GovernmentRowResolve164Api.Result expected,int expectedGsReads,Runnable after) {
        public Case {
            Objects.requireNonNull(name);Objects.requireNonNull(entry);Objects.requireNonNull(memory);
            Objects.requireNonNull(delegate);Objects.requireNonNull(lookupBudget);Objects.requireNonNull(resolveBudget);
            Objects.requireNonNull(hashBudget);Objects.requireNonNull(ownedMxcsrAtHash);
            Objects.requireNonNull(expected);Objects.requireNonNull(after);
        }
    }
}
