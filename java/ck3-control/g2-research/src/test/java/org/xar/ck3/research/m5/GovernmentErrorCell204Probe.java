package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentErrorCell204WitnessApi.Dispatch;
import org.xar.ck3.research.m5.GovernmentErrorCell204WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentWholeCrt189PortsApi.MemoryImage;

/** Normal-only new204 protocol probe; reusable byte memory is owner code. */
public final class GovernmentErrorCell204Probe {
    private GovernmentErrorCell204Probe() { }
    private static void check(boolean condition,String message) {
        if(!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        List<Witness> data=new GovernmentErrorCell204Fixtures().witnesses();
        check(data.size()==4,"four normal scenes");
        for(Witness witness:data) runDispatch(witness);
        System.out.println("cases=4 direct=2 bound=2 orderedCalls=4");
    }
    // This genuinely new method is the only model-owned missing implementation.
    private static void runDispatch(Witness witness) {
        MapMemory memory = new MapMemory(witness.memorySeed(), witness.entry());
        GovernmentWholeCrt189Ports ports = new GovernmentWholeCrt189Ports(memory, witness.events());
        if (witness.dispatch() == Dispatch.DIRECT) {
            NormalReturn actual = GovernmentErrorCell204.execute(witness.entry(), memory, ports);
            check(actual.equals(witness.expectedReturn()), "direct return mismatch");
        } else {
            Calls bound = GovernmentErrorCell204Calls.bind(witness.entry().imageBaseBits(), memory, ports);
            Call request = new Call(witness.callerSiteRva(), TargetKind.DIRECT_RVA, 0x423B18CL,
                    witness.entry().rspBits() + 8L, witness.entry().volatileBits(), witness.entry().nonvolatileBits());
            VolatileBits actualV = bound.invoke(request);
            check(actualV.equals(witness.expectedReturn().volatileBits()), "bound return mismatch");
        }
        ports.verifyComplete();
        check(memory.snapshot().equals(witness.expectedFinalBytes()), "final bytes mismatch");
        check(memory.callSlotWrites == 8, "call slot writes mismatch");
    }
    private static final class MapMemory implements Memory,MemoryImage {
        private final Map<Long,Integer> bytes;
        private final long slot;
        private int callSlotWrites;
        MapMemory(Map<Long,Integer> initial,Entry entry) {
            bytes=new LinkedHashMap<>(initial);slot=entry.rspBits()-0x30L;
        }
        @Override public Map<Long,Integer> snapshot() { return Map.copyOf(bytes); }
        @Override public void mutate(Map<Long,Integer> mutation) {
            for(var e:mutation.entrySet()) writeByte(e.getKey(),e.getValue());
        }
        @Override public int readUnsignedByte(long address) {
            Integer b=bytes.get(address);
            check(b!=null,"unowned read "+Long.toUnsignedString(address,16));return b;
        }
        @Override public void writeByte(long address,int value) {
            check(value>=0 && value<=255,"byte range");
            if(address>=slot && address<slot+8) callSlotWrites++;
            bytes.put(address,value);
        }
        @Override public int readDword(long a) {
            return readUnsignedByte(a) | (readUnsignedByte(a+1)<<8)
                    | (readUnsignedByte(a+2)<<16) | (readUnsignedByte(a+3)<<24);
        }
        @Override public long readQword(long a) {
            return Integer.toUnsignedLong(readDword(a)) | ((long)readDword(a+4)<<32);
        }
        @Override public void writeDword(long a,int value) {
            for(int i=0;i<4;i++) writeByte(a+i,(value >>> (8*i)) & 255);
        }
        @Override public void writeQword(long a,long value) {
            writeDword(a,(int)value);writeDword(a+4,(int)(value >>> 32));
        }
        @Override public Bits128 read128(long a) { return new Bits128(readQword(a),readQword(a+8)); }
        @Override public void write128(long a,Bits128 value) {
            writeQword(a,value.lowBits());writeQword(a+8,value.highBits());
        }
        @Override public int lockedXaddDword(long a,int addend) {
            throw new AssertionError("unexpected204 atomic");
        }
    }
}
