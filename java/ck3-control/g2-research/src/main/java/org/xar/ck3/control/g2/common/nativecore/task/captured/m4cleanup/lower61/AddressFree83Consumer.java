package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;

import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs;

public final class AddressFree83Consumer {
    private AddressFree83Consumer() { }

    public static void execute(Lower61Inputs.CallInput input, Lower61Inputs.Memory memory, Lower61Inputs.Calls calls) {
        long blockRaw = input.rcxRaw();
        if (blockRaw == 0L) {
            return;
        }

        long heapHandleRaw = memory.readPointer(input.moduleBaseRaw() + 0x5C5DE30L);

        Frame frame = new Frame(calls);

        Free83Candidate.release(blockRaw, heapHandleRaw, frame);

        if (frame.cell != null) {
            memory.writeInt32(frame.destination, frame.cell.value);
        }
    }

    private static final class Frame implements Free83Inputs.Calls {
        private final Lower61Inputs.Calls calls;
        private long destination;
        private Free83Inputs.Cell32 cell;

        Frame(Lower61Inputs.Calls calls) {
            this.calls = calls;
            this.destination = 0L;
            this.cell = null;
        }

        @Override
        public int heapFree(long heapHandleRaw, int flagsRaw32, long blockRaw) {
            Lower61Inputs.FirstCall fc = new Lower61Inputs.FirstCall(heapHandleRaw, Integer.toUnsignedLong(flagsRaw32), blockRaw);
            return calls.callSlot43DA748(fc);
        }

        @Override
        public Free83Inputs.Cell32 failureCell() {
            destination = calls.call423B18C();
            cell = new Free83Inputs.Cell32(0);
            return cell;
        }

        @Override
        public int lastErrorBits() {
            return calls.callSlot43DA738();
        }

        @Override
        public int mapCode(long zeroExtendedError32) {
            return calls.call423B0D4(zeroExtendedError32);
        }
    }
}
