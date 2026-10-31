package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentResult168Api;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;

/** Scope170 case DATA only. Reuses the existing strict owned byte memory and full call script. */
public final class GovernmentAbf170CaseApi {
    private GovernmentAbf170CaseApi() { }

    public record BudgetEvent(long instructionRva, long addressBits) { }
    private record BudgetStep(BudgetEvent event, Runnable sideEffect) { }

    /** Literal work observations; no target evaluation, implicit release or default completion. */
    public static final class BudgetScript implements GovernmentResult168Api.WorkBudget {
        private final List<BudgetStep> expected = new ArrayList<>();
        public final List<BudgetEvent> actual = new ArrayList<>();
        private int index;

        public BudgetScript expect(long instructionRva, long addressBits, Runnable sideEffect) {
            expected.add(new BudgetStep(new BudgetEvent(instructionRva, addressBits),
                    Objects.requireNonNull(sideEffect)));
            return this;
        }

        @Override public void beforeStep(long instructionRva, long addressBits) {
            BudgetEvent event = new BudgetEvent(instructionRva, addressBits);
            actual.add(event);
            if (index == expected.size())
                throw new UnsupportedOperationException("unapproved resolver work step " + event);
            BudgetStep step = expected.get(index++);
            equal(step.event(), event, "literal resolver work event " + index);
            step.sideEffect().run();
        }

        public void done() { equal(expected.size(), index, "resolver work event count"); }
    }

    /** Full193caller input/result; expected literals are owned by the separate independent book. */
    public record Case(String name, GovernmentRowResolve164Api.Entry entry, MemoryImage memory,
            CallScript delegate, GovernmentLookup167Api.SpinBudget lookupBudget,
            BudgetScript resolveBudget, GovernmentRowResolve164Api.Result expected,
            int expectedGsReads, Runnable after) {
        public Case {
            Objects.requireNonNull(name); Objects.requireNonNull(entry); Objects.requireNonNull(memory);
            Objects.requireNonNull(delegate); Objects.requireNonNull(lookupBudget);
            Objects.requireNonNull(resolveBudget); Objects.requireNonNull(expected); Objects.requireNonNull(after);
        }
    }
}
