package org.xar.ck3.study.m6.embedded219;

import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedElements37282B0;
import org.xar.ck3.study.m6.transfer216.Transfer216Api;
import org.xar.ck3.study.m6.transfer216.Transfer21a216;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217;
import org.xar.ck3.study.m6.transfer217.Transfer4Move217;

public final class EmbeddedKnownTransfers219 {
    private EmbeddedKnownTransfers219() { }

    public static long copy(
            EmbeddedInputs219.Input input,
            EmbeddedInputs219.Memory memory,
            PendingEmbeddedElements37282B0.Calls delegate,
            Transfer216Api.Calls calls16,
            Transfer4Api217.Calls calls4,
            Transfer216Api.Budget budget16,
            Transfer4Api217.Budget budget4) {

        PendingEmbeddedElements37282B0.Calls facade = new PendingEmbeddedElements37282B0.Calls() {
            @Override
            public void call889780(PendingEmbeddedElements37282B0.Memory mem, long rcx, long rdx) {
                delegate.call889780(mem, rcx, rdx);
            }

            @Override
            public long allocate(PendingEmbeddedElements37282B0.Memory mem, long target, long rcx, long rdx, int r8d) {
                return delegate.allocate(mem, target, rcx, rdx, r8d);
            }

            @Override
            public void callDBDB80(PendingEmbeddedElements37282B0.Memory mem, long rcx, long rdx, int r8d, int r9d) {
                delegate.callDBDB80(mem, rcx, rdx, r8d, r9d);
            }

            @Override
            public void virtualDestroy(PendingEmbeddedElements37282B0.Memory mem, long target, long rcx, long rdx) {
                delegate.virtualDestroy(mem, target, rcx, rdx);
            }

            @Override
            public void copy16_21A5050(PendingEmbeddedElements37282B0.Memory mem, long destinationHeader, long sourceHeader) {
                // Override deep 150 port: call actual Transfer21a216 kernel
                // Frame calculation: parent322postframe - 0x4B0
                long frame = input.parentFrameRaw64() - 0x4B0L;
                Transfer216Api.Input t216Input = new Transfer216Api.Input(destinationHeader, sourceHeader, input.imageBaseRaw64(), frame);
                Transfer21a216.execute(t216Input, memory, calls16, budget16);
            }

            @Override
            public void copy4_B2EEE0(PendingEmbeddedElements37282B0.Memory mem, long destinationHeader, long sourceHeader) {
                // Override deep 150 port: call actual Transfer4Move217 kernel
                // Frame calculation: parent322postframe - 0x80
                long frame = input.parentFrameRaw64() - 0x80L;
                Transfer4Api217.Input t4Input = new Transfer4Api217.Input(destinationHeader, sourceHeader, input.imageBaseRaw64(), frame);
                Transfer4Move217.execute(t4Input, memory, calls4, budget4);
            }

            @Override
            public void copy16_8C70B0(PendingEmbeddedElements37282B0.Memory mem, long destinationHeader, long rdxZero, long begin, long end) {
                delegate.copy16_8C70B0(mem, destinationHeader, rdxZero, begin, end);
            }

            @Override
            public void copy4_ADD0D0(PendingEmbeddedElements37282B0.Memory mem, long destinationHeader, long rdxZero, long begin, long end) {
                delegate.copy4_ADD0D0(mem, destinationHeader, rdxZero, begin, end);
            }

            @Override
            public long range16Virtual8(PendingEmbeddedElements37282B0.Memory mem, long target, long rcx, long rdx, long r8, long r9) {
                return delegate.range16Virtual8(mem, target, rcx, rdx, r8, r9);
            }

            @Override
            public void range16Virtual16(PendingEmbeddedElements37282B0.Memory mem, long target, long rcx, long rdx, long r8, long r9) {
                delegate.range16Virtual16(mem, target, rcx, rdx, r8, r9);
            }

            @Override
            public void range16Direct8F8550(PendingEmbeddedElements37282B0.Memory mem, long rcx, long rdx, long r8, long r9) {
                delegate.range16Direct8F8550(mem, rcx, rdx, r8, r9);
            }
        };

        return PendingEmbeddedElements37282B0.copy(memory, facade, input.destinationRaw64(), input.sourceRaw64(), input.imageBaseRaw64());
    }
}