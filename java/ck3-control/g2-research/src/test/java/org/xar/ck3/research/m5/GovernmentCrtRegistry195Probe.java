package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtRegistry195WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentWholeCrt189PortsApi.MemoryImage;

/** Owner reusable driver for new195normal-call protocol; new runWitness method model-first.
 * ByteMemory/guards reused from earlier accepted manual code, no target algorithm. */
public final class GovernmentCrtRegistry195Probe {
    private GovernmentCrtRegistry195Probe() { }
    private static void check(boolean condition,String message) {
        if(!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        List<Witness> witnesses=new GovernmentCrtRegistry195Fixtures().witnesses();
        check(witnesses.size()==1,"expected ONE independent protocol witness");
        for(Witness w:witnesses) run(w);
        forwarding(witnesses.get(0));
        System.out.println("cases=1 forwarding=7");
    }
    private static void run(Witness w) {
    MapMemory mem = new MapMemory(w.memorySeed(), w.request().rspBits() - 8L);
    GovernmentWholeCrt189Ports ports = new GovernmentWholeCrt189Ports(mem, w.events());
    Calls bound = GovernmentCrtRegistry195Calls.bind(w.imageBaseBits(), mem, ports);
    VolatileBits actualVolatile = bound.invoke(w.request());
    check(actualVolatile.equals(w.expectedVolatileBits()), "volatile mismatch");
    ports.verifyComplete();
    check(mem.snapshot().equals(w.expectedFinalBytes()), "final bytes mismatch");
    check(mem.totalByteWrites == 52, "byte write count mismatch");
    check(mem.callerReturnWrites == 0, "caller return rewritten");
    check(mem.callerReturnReads == 8, "caller return read count mismatch");
}
    private static void forwarding(Witness w) {
        MapMemory mem=new MapMemory(Map.of(),w.request().rspBits()-8);
        NormalReturn ownedReturn=new NormalReturn(w.expectedVolatileBits(),0x1111222233334444L,0x5555666677778888L,w.request().nonvolatileBits());
        Forwarding fallback=new Forwarding(w.request().volatileBits(),ownedReturn,0x8000000000000195L);
        Calls bound=GovernmentCrtRegistry195Calls.bind(w.imageBaseBits(),mem,fallback);
        List<Call> foreign=List.of(
                new Call(0x424df28L,TargetKind.DIRECT_RVA,0x424db38L,w.request().rspBits(),w.request().volatileBits(),w.request().nonvolatileBits()),
                new Call(0x424df29L,TargetKind.DIRECT_RVA,0x424db39L,w.request().rspBits(),w.request().volatileBits(),w.request().nonvolatileBits()),
                new Call(0x424df29L,TargetKind.INDIRECT_ABSOLUTE,0x424db38L,w.request().rspBits(),w.request().volatileBits(),w.request().nonvolatileBits()));
        for(Call call:foreign) check(bound.invoke(call)==w.request().volatileBits() && fallback.seenCall==call,"foreign invoke original object");
        Entry e=new Entry(w.imageBaseBits(),w.request().rspBits(),w.request().volatileBits(),w.request().nonvolatileBits());
        List<Tail> tails=List.of(new Tail(0x4223a7fL,TargetKind.DIRECT_RVA,0x4223aecL,e),
                new Tail(0x424df29L,TargetKind.DIRECT_RVA,0x424db38L,e),
                new Tail(0x424df29L,TargetKind.INDIRECT_ABSOLUTE,0x424db38L,e));
        for(Tail tail:tails) check(bound.tail(tail)==ownedReturn && fallback.seenTail==tail,"all tail original object");
        check(bound.readGsQword58()==0x8000000000000195L && fallback.gsCount==1,"GS original port");
        check(mem.snapshot().isEmpty() && mem.totalByteWrites==0 && mem.callerReturnReads==0,"no foreign memory qualification");
    }


    private static final class MapMemory implements Memory,MemoryImage {
        private final Map<Long,Integer> map;
        private final long callerReturnSlot;
        private int callerReturnReads,callerReturnWrites,totalByteWrites;
        MapMemory(Map<Long,Integer> seed,long callerReturnSlot) {
            for(int value:seed.values()) check(value>=0 && value<=255,"invalid seed byte");
            map=new LinkedHashMap<>(seed);this.callerReturnSlot=callerReturnSlot;
        }
        @Override public Map<Long,Integer> snapshot() { return Map.copyOf(map); }
        @Override public void mutate(Map<Long,Integer> mutation) {
            for(int value:mutation.values()) check(value>=0 && value<=255,"invalid mutation byte");
            for(var e:mutation.entrySet()) writeByte(e.getKey(),e.getValue());
        }
        @Override public int readUnsignedByte(long address) {
            for(int i=0;i<8;i++) if(address==callerReturnSlot+i) callerReturnReads++;
            Integer value=map.get(address);check(value!=null,"missing byte "+Long.toUnsignedString(address,16));
            return value;
        }
        @Override public void writeByte(long address,int value) {
            check(value>=0 && value<=255,"invalid write byte");
            for(int i=0;i<8;i++) if(address==callerReturnSlot+i) callerReturnWrites++;
            totalByteWrites++;map.put(address,value);
        }
        @Override public int lockedXaddDword(long address,int addend) { throw new AssertionError("unexpected195 atomic"); }
        @Override
        public int readDword(long addressBits) {
            int b0 = readUnsignedByte(addressBits);
            int b1 = readUnsignedByte(addressBits + 1);
            int b2 = readUnsignedByte(addressBits + 2);
            int b3 = readUnsignedByte(addressBits + 3);
            return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
        }

        @Override
        public long readQword(long addressBits) {
            long low = Integer.toUnsignedLong(readDword(addressBits));
            long high = Integer.toUnsignedLong(readDword(addressBits + 4));
            return low | (high << 32);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            writeByte(addressBits, valueBits & 0xFF);
            writeByte(addressBits + 1, (valueBits >> 8) & 0xFF);
            writeByte(addressBits + 2, (valueBits >> 16) & 0xFF);
            writeByte(addressBits + 3, (valueBits >> 24) & 0xFF);
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            writeDword(addressBits, (int) valueBits);
            writeDword(addressBits + 4, (int) (valueBits >> 32));
        }

        @Override
        public Bits128 read128(long addressBits) {
            long low = readQword(addressBits);
            long high = readQword(addressBits + 8);
            return new Bits128(low, high);
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            writeQword(addressBits, valueBits.lowBits());
            writeQword(addressBits + 8, valueBits.highBits());
        }
    }

    private static class Forwarding implements Calls {
        private final VolatileBits fixedV;
        private final NormalReturn fixedR;
        private final long gsVal;
        private Call seenCall;
        private Tail seenTail;
        private int gsCount;

        Forwarding(VolatileBits v, NormalReturn r, long gs) {
            this.fixedV = v;
            this.fixedR = r;
            this.gsVal = gs;
            this.gsCount = 0;
        }

        @Override
        public VolatileBits invoke(Call call) {
            this.seenCall = call;
            return this.fixedV;
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            this.seenTail = transfer;
            return this.fixedR;
        }

        @Override
        public long readGsQword58() {
            this.gsCount++;
            return this.gsVal;
        }
    }
}
