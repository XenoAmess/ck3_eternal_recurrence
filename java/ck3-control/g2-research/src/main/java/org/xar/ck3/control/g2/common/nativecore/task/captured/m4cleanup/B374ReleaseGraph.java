package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup;

import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower54.Lower54Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower54.Lower54Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower108.Lower108Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower108.Lower108Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower266.Lower266Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower266.Lower266Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower264.Lower264Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower264.Lower264Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower88.Lower88Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower88.Lower88Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.AddressFree83Consumer;

public final class B374ReleaseGraph {

    public interface SharedMemory extends B374Inputs.Memory, Lower54Inputs.Memory, Lower108Inputs.Memory, Lower266Inputs.Memory, Lower264Inputs.Memory, Lower88Inputs.Memory, Lower61Inputs.Memory {
    }

    public static B374Inputs.Calls assemble(long moduleBaseRaw, SharedMemory memory, Lower61Inputs.Calls actual61, Lower61Inputs.EdgeObserver observer) {
        return new Assembly(moduleBaseRaw, memory, actual61, observer);
    }

    private static final class Assembly implements B374Inputs.Calls, Lower54Inputs.Calls, Lower108Inputs.Calls, Lower266Inputs.Calls, Lower264Inputs.Calls, Lower88Inputs.Calls {
        private final long base;
        private final SharedMemory mem;
        private final Lower61Inputs.Calls a61;
        private final Lower61Inputs.EdgeObserver obs;

        Assembly(long base, SharedMemory mem, Lower61Inputs.Calls a61, Lower61Inputs.EdgeObserver obs) {
            this.base = base;
            this.mem = mem;
            this.a61 = a61;
            this.obs = obs;
        }

        @Override public void call424E364(long rcx) {
            obs.normal(rcx);
            AddressFree83Consumer.execute(new Lower61Inputs.CallInput(base, rcx), mem, a61);
        }

        @Override public void tail424E364(long rcx) {
            obs.tail(rcx);
            AddressFree83Consumer.execute(new Lower61Inputs.CallInput(base, rcx), mem, a61);
        }

        @Override public void call42552D0(long rcx) {
            Lower266Candidate.execute(new Lower266Inputs.CallInput(base, rcx), mem, this);
        }

        @Override public void call4255910(long rcx) {
            Lower108Candidate.execute(new Lower108Inputs.CallInput(base, rcx), mem, this);
        }

        @Override public void call425689C(long rcx) {
            Lower54Candidate.execute(new Lower54Inputs.CallInput(base, rcx), mem, this);
        }

        @Override public void call4255FFC(long rcx) {
            Lower264Candidate.execute(new Lower264Inputs.CallInput(rcx), mem, this);
        }

        @Override public void call4255C64(long rcx, long rdx) {
            Lower88Candidate.execute(new Lower88Inputs.CallInput(rcx, rdx), mem, this);
        }
    }
}