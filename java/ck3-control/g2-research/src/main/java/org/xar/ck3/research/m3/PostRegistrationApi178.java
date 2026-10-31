package org.xar.ck3.research.m3;

/** Frozen normal-call observation API of held1295B3790510. */
public final class PostRegistrationApi178 {
    private PostRegistrationApi178() { }

    /** Shares the already formal byte-width memory contract; no process access. */
    public interface Memory extends RegistryConsumerApi176.Memory { }

    public record CallerOwnedScratch(long sourceRsp) {
        public long sourceRbp() { return sourceRsp + 0xc9L; }
    }

    /** Exact observed scalar instruction result, including CVTT exceptional output. */
    @FunctionalInterface
    public interface ScalarObservation {
        int cvtdq2psMulssAddssCvttss2si(int sourceInteger, int multiplierBits, int addendBits);
    }

    /** Calls may mutate Memory or throw. No unestablished volatile RCX is fabricated. */
    public interface Ports {
        int call3f542c0(Memory memory, long receiver, long descriptor);
        long callc3e150(Memory memory);
        int call86e160(Memory memory, int requested, int zeroEdx);
        void callc3b700(Memory memory, long header, int exponent);
        void call3763f90(Memory memory, long receiver, long outputVector);
        long objectSlot80(Memory memory, long code, long receiver);
        /** Only the explicitly established RDX/R8D and consumed EAX are projected. */
        int call3f7e220(Memory memory, long dataRdx, int lengthR8d);
        void callc39c60(Memory memory, long header, long output, int hash, long descriptor);
        long calla92eb0(Memory memory);
        long call3793900(Memory memory, long context, int hash);
        int call3f6d2b0Al(Memory memory, long descriptor, long data);
        void call857a70(Memory memory, long output, long format, long operands);
        long gs58(Memory memory);
        long call3f5f970(Memory memory, int flag);
        /** sourceRsp exposes unchanged stack+20 and explicitly written stack+28. */
        void call857b60(Memory memory, long logger, long descriptor, int line, int level, long sourceRsp);
        int atomicXadd32(Memory memory, long address, int delta);
        void call4223f44(Memory memory, long base, long bytes);
        /** If it returns, source09DF falls through NOP into09E5 TLS initialization. */
        void call4232a70(Memory memory);
        void objectSlot00(Memory memory, long code, long receiver, int flag);
        void allocatorSlot10(Memory memory, long code, long receiver, long rows, int alignment);
        void call4223a84(Memory memory, long guard);
        void call4223a24(Memory memory, long guard);
        void call856050(Memory memory, long field);
    }
}
