package org.xar.ck3.research.m3.hash188;

import org.xar.ck3.research.m3.PostRegistrationApi178;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.hash188.HashInsertC39C60;

public final class PostRegistrationHashInsertBinding188 {
    private PostRegistrationHashInsertBinding188() { }

    public interface Memory extends PostRegistrationApi178.Memory, HashInsert188Api.Memory { }

    public static PostRegistrationApi178.Ports bind(Memory memory, long moduleBase,
            PostRegistrationApi178.CallerOwnedScratch callerScratch,
            HashInsert188Api.Ports hashPorts, PostRegistrationApi178.Ports opaque) {
        return new BoundPorts(memory, moduleBase, callerScratch, hashPorts, opaque);
    }

    private static final class BoundPorts implements PostRegistrationApi178.Ports {
        private final Memory strongMemory;
        private final long moduleBase;
        private final PostRegistrationApi178.CallerOwnedScratch callerScratch;
        private final HashInsert188Api.Ports hashPorts;
        private final PostRegistrationApi178.Ports opaque;

        BoundPorts(Memory strongMemory, long moduleBase,
                PostRegistrationApi178.CallerOwnedScratch callerScratch,
                HashInsert188Api.Ports hashPorts, PostRegistrationApi178.Ports opaque) {
            this.strongMemory = strongMemory;
            this.moduleBase = moduleBase;
            this.callerScratch = callerScratch;
            this.hashPorts = hashPorts;
            this.opaque = opaque;
        }

        @Override
        public int call3f542c0(PostRegistrationApi178.Memory memory, long receiver, long descriptor) {
            return opaque.call3f542c0(memory, receiver, descriptor);
        }

        @Override
        public long callc3e150(PostRegistrationApi178.Memory memory) {
            return opaque.callc3e150(memory);
        }

        @Override
        public int call86e160(PostRegistrationApi178.Memory memory, int requested, int zeroEdx) {
            return opaque.call86e160(memory, requested, zeroEdx);
        }

        @Override
        public void callc3b700(PostRegistrationApi178.Memory memory, long header, int exponent) {
            opaque.callc3b700(memory, header, exponent);
        }

        @Override
        public void call3763f90(PostRegistrationApi178.Memory memory, long receiver, long outputVector) {
            opaque.call3763f90(memory, receiver, outputVector);
        }

        @Override
        public long objectSlot80(PostRegistrationApi178.Memory memory, long code, long receiver) {
            return opaque.objectSlot80(memory, code, receiver);
        }

        @Override
        public int call3f7e220(PostRegistrationApi178.Memory memory, long dataRdx, int lengthR8d) {
            return opaque.call3f7e220(memory, dataRdx, lengthR8d);
        }

        @Override
        public void callc39c60(PostRegistrationApi178.Memory memory, long header, long output, int hash, long descriptor) {
            if (memory != strongMemory) {
                throw new IllegalArgumentException("Memory mismatch");
            }
            HashInsert188Api.Input input = new HashInsert188Api.Input(
                    moduleBase,
                    header,
                    output,
                    hash,
                    descriptor,
                    new HashInsert188Api.Scratch(callerScratch.sourceRsp() - 0xB0L)
            );
            HashInsertC39C60.execute(input, strongMemory, hashPorts);
        }

        @Override
        public long calla92eb0(PostRegistrationApi178.Memory memory) {
            return opaque.calla92eb0(memory);
        }

        @Override
        public long call3793900(PostRegistrationApi178.Memory memory, long context, int hash) {
            return opaque.call3793900(memory, context, hash);
        }

        @Override
        public int call3f6d2b0Al(PostRegistrationApi178.Memory memory, long descriptor, long data) {
            return opaque.call3f6d2b0Al(memory, descriptor, data);
        }

        @Override
        public void call857a70(PostRegistrationApi178.Memory memory, long output, long format, long operands) {
            opaque.call857a70(memory, output, format, operands);
        }

        @Override
        public long gs58(PostRegistrationApi178.Memory memory) {
            return opaque.gs58(memory);
        }

        @Override
        public long call3f5f970(PostRegistrationApi178.Memory memory, int flag) {
            return opaque.call3f5f970(memory, flag);
        }

        @Override
        public void call857b60(PostRegistrationApi178.Memory memory, long logger, long descriptor, int line, int level, long sourceRsp) {
            opaque.call857b60(memory, logger, descriptor, line, level, sourceRsp);
        }

        @Override
        public int atomicXadd32(PostRegistrationApi178.Memory memory, long address, int delta) {
            return opaque.atomicXadd32(memory, address, delta);
        }

        @Override
        public void call4223f44(PostRegistrationApi178.Memory memory, long base, long bytes) {
            opaque.call4223f44(memory, base, bytes);
        }

        @Override
        public void call4232a70(PostRegistrationApi178.Memory memory) {
            opaque.call4232a70(memory);
        }

        @Override
        public void objectSlot00(PostRegistrationApi178.Memory memory, long code, long receiver, int flag) {
            opaque.objectSlot00(memory, code, receiver, flag);
        }

        @Override
        public void allocatorSlot10(PostRegistrationApi178.Memory memory, long code, long receiver, long rows, int alignment) {
            opaque.allocatorSlot10(memory, code, receiver, rows, alignment);
        }

        @Override
        public void call4223a84(PostRegistrationApi178.Memory memory, long guard) {
            opaque.call4223a84(memory, guard);
        }

        @Override
        public void call4223a24(PostRegistrationApi178.Memory memory, long guard) {
            opaque.call4223a24(memory, guard);
        }

        @Override
        public void call856050(PostRegistrationApi178.Memory memory, long field) {
            opaque.call856050(memory, field);
        }
    }
}