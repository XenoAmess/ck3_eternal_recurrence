package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class LoadRowReferenceLazyGuardCrt206Calls {
    private LoadRowReferenceLazyGuardCrt206Calls() { }

    public static Calls bind(long image, Memory memory, Calls fallback, LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(budget);
        return new Bridge(image, memory, fallback, budget);
    }

    private static final class Bridge implements Calls {
        private final long imageBase;
        private final Memory memory;
        private final Calls delegate;
        private final LoopBudget budget;

        Bridge(long imageBase, Memory memory, Calls delegate, LoopBudget budget) {
            this.imageBase = imageBase;
            this.memory = memory;
            this.delegate = delegate;
            this.budget = budget;
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }

        @Override
        public VolatileBits invoke(Call call) {
            Objects.requireNonNull(call);
            long site = call.callSiteRva();
            long target = call.targetBits();
            TargetKind kind = call.kind();

            if (kind == TargetKind.DIRECT_RVA) {
                if (site == 0x8CEEE3L && target == 0x4223A84L) {
                    Entry childEntry = new Entry(imageBase, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                    NormalReturn result = GovernmentCrtBoundary185.execute3A84(childEntry, memory, delegate, budget);
                    validateReturn(result, call, imageBase, 0x8CEEE8L);
                    return result.volatileBits();
                }
                if (site == 0x8CEF06L && target == 0x4223A24L) {
                    Entry childEntry = new Entry(imageBase, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                    NormalReturn result = GovernmentCrtBoundary185.execute3A24(childEntry, memory, delegate);
                    validateReturn(result, call, imageBase, 0x8CEF0BL);
                    return result.volatileBits();
                }
            }

            return delegate.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            Objects.requireNonNull(transfer);
            return delegate.tail(transfer);
        }

        private void validateReturn(NormalReturn result, Call call, long imageBase, long expectedNextRva) {
            if (result.returnRipBits() != imageBase + expectedNextRva) {
                throw new IllegalStateException("Return RIP mismatch");
            }
            if (result.callerRspBits() != call.rspBits()) {
                throw new IllegalStateException("Caller RSP mismatch");
            }
            if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                throw new IllegalStateException("Nonvolatile mismatch");
            }
        }
    }
}