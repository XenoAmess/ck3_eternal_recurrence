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
import org.xar.ck3.research.m5.GovernmentCrtNative192WitnessApi.Kind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtNative192WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentWholeCrt189PortsApi.MemoryImage;

/** Owner reusable driver for new192protocol; new runWitness method model-first.
 * ByteMemory/guards reused from earlier accepted manual code, no target algorithm. */
public final class GovernmentCrtNative192Probe {
    private GovernmentCrtNative192Probe() { }
    private static void check(boolean condition,String message) {
        if(!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        List<Witness> witnesses=new GovernmentCrtNative192Fixtures().witnesses();
        check(witnesses.size()==3,"expected three independent witnesses");
        for(Witness w:witnesses) run(w);
        forwarding(witnesses.get(0));
        frameGuards(witnesses.stream().filter(w -> w.kind()==Kind.WAIT_CALL).findFirst().orElseThrow());
        System.out.println("cases=3 forwarding=7 frameGuards=3");
    }
    private static void run(Witness w) {
    boolean isNotify = w.kind() == Kind.NOTIFY_TAIL;
    long bindingImage = isNotify ? w.entry().imageBaseBits() + 0x100000L : w.entry().imageBaseBits();
    MapMemory mem = new MapMemory(w.memorySeed(), w.entry());
    GovernmentWholeCrt189Ports ports = new GovernmentWholeCrt189Ports(mem, w.events());
    Calls bound = GovernmentCrtNative192Calls.bind(bindingImage, mem, ports);
    NormalReturn term = terminal(w.events());
    if (isNotify) {
        Tail t = new Tail(0x4223A7FL, TargetKind.DIRECT_RVA, 0x4223AECL, w.entry());
        NormalReturn actual = bound.tail(t);
        check(actual.equals(w.expected()), "notify expected mismatch");
        check(actual == term, "notify identity mismatch");
    } else {
        Call c = new Call(0x4223AA9L, TargetKind.DIRECT_RVA, 0x4223B30L, w.entry().rspBits() + 8, w.entry().volatileBits(), w.entry().nonvolatileBits());
        VolatileBits actual = bound.invoke(c);
        check(actual.equals(w.expected().volatileBits()), "wait volatile mismatch");
        check(actual == term.volatileBits(), "wait volatile identity mismatch");
    }
    ports.verifyComplete();
    check(mem.snapshot().equals(w.expectedFinalBytes()), "final bytes mismatch");
    int callCount = 0;
    for (Event e : w.events()) if (e instanceof CallStep) callCount++;
    check(mem.callSlotWrites == callCount * 8, "call slot writes mismatch");
}
    private static void forwarding(Witness w) {
        MapMemory mem=new MapMemory(Map.of(),w.entry());
        Forwarding fallback=new Forwarding(w.entry().volatileBits(),w.expected(),0x8000000000000192L);
        Calls bound=GovernmentCrtNative192Calls.bind(w.entry().imageBaseBits(),mem,fallback);
        List<Call> foreignCalls=List.of(
                new Call(0x4223aa8L,TargetKind.DIRECT_RVA,0x4223b30L,w.entry().rspBits()+8,w.entry().volatileBits(),w.entry().nonvolatileBits()),
                new Call(0x4223aa9L,TargetKind.DIRECT_RVA,0x4223b31L,w.entry().rspBits()+8,w.entry().volatileBits(),w.entry().nonvolatileBits()),
                new Call(0x4223aa9L,TargetKind.INDIRECT_ABSOLUTE,0x4223b30L,w.entry().rspBits()+8,w.entry().volatileBits(),w.entry().nonvolatileBits()));
        for(Call call:foreignCalls) check(bound.invoke(call)==w.entry().volatileBits() && fallback.seenCall==call,"foreign invoke original object");
        List<Tail> foreignTails=List.of(
                new Tail(0x4223a80L,TargetKind.DIRECT_RVA,0x4223aecL,w.entry()),
                new Tail(0x4223a7fL,TargetKind.DIRECT_RVA,0x4223af0L,w.entry()),
                new Tail(0x4223a7fL,TargetKind.INDIRECT_ABSOLUTE,0x4223aecL,w.entry()));
        for(Tail tail:foreignTails) check(bound.tail(tail)==w.expected() && fallback.seenTail==tail,"foreign tail original object");
        check(bound.readGsQword58()==0x8000000000000192L && fallback.gsCount==1,"GS original port");
        check(mem.snapshot().isEmpty(),"forwarding memory untouched");
    }
    private static NormalReturn terminal(List<Event> events) {
        NormalReturn last=null;
        for(Event e:events) if(e instanceof TailStep tail) last=tail.normalPost();
        check(last!=null,"missing terminal tail");return last;
    }
    private static void frameGuards(Witness w) {
        NormalReturn good=terminal(w.events());NonvolatileBits n=good.nonvolatileBits();
        NonvolatileBits badNv=new NonvolatileBits(n.rbxBits()^1,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        List<NormalReturn> badFrames=List.of(
                new NormalReturn(good.volatileBits(),good.returnRipBits()^1,good.callerRspBits(),n),
                new NormalReturn(good.volatileBits(),good.returnRipBits(),good.callerRspBits()+8,n),
                new NormalReturn(good.volatileBits(),good.returnRipBits(),good.callerRspBits(),badNv));
        for(NormalReturn bad:badFrames) {
            List<Event> events=new ArrayList<>(w.events());int index=-1;
            for(int i=0;i<events.size();i++) if(events.get(i) instanceof TailStep) index=i;
            check(index>=0,"missing tail");TailStep old=(TailStep)events.get(index);
            events.set(index,new TailStep(old.expected(),old.expectedMemoryBefore(),old.mutation(),bad));
            MapMemory mem=new MapMemory(w.memorySeed(),w.entry());
            GovernmentWholeCrt189Ports ports=new GovernmentWholeCrt189Ports(mem,events);
            Calls bound=GovernmentCrtNative192Calls.bind(w.entry().imageBaseBits(),mem,ports);
            boolean rejected=false;
            try {
                bound.invoke(new Call(0x4223aa9L,TargetKind.DIRECT_RVA,0x4223b30L,w.entry().rspBits()+8,w.entry().volatileBits(),w.entry().nonvolatileBits()));
            } catch(IllegalStateException expected) { rejected=true; }
            check(rejected,"must reject one corrupted normal frame field");
            ports.verifyComplete();check(mem.snapshot().equals(w.expectedFinalBytes()),"guard final map");
            check(mem.callSlotWrites==16,"guard exactly two actual CALLpushes");
        }
    }
    private static final class MapMemory implements Memory,MemoryImage {
        private final Map<Long,Integer> map;
        private final long originalRsp,callSlot;
        private int callSlotWrites;
        MapMemory(Map<Long,Integer> seed,Entry entry) {
            for(int value:seed.values()) check(value>=0 && value<=255,"invalid seed byte");
            map=new LinkedHashMap<>(seed);originalRsp=entry.rspBits();callSlot=originalRsp-0x30L;
        }
        @Override public Map<Long,Integer> snapshot() { return Map.copyOf(map); }
        @Override public void mutate(Map<Long,Integer> mutation) {
            for(int value:mutation.values()) check(value>=0 && value<=255,"invalid mutation byte");
            for(var e:mutation.entrySet()) writeByte(e.getKey(),e.getValue());
        }
        @Override public int readUnsignedByte(long address) {
            for(int i=0;i<8;i++) check(address!=originalRsp+i,"unexpected caller RET read");
            Integer value=map.get(address);
            check(value!=null,"missing byte "+Long.toUnsignedString(address,16));
            return value;
        }
        @Override public void writeByte(long address,int value) {
            check(value>=0 && value<=255,"invalid write byte");
            for(int i=0;i<8;i++) if(address==callSlot+i) callSlotWrites++;
            map.put(address,value);
        }
        @Override public int lockedXaddDword(long address,int addend) {
            throw new AssertionError("unexpected190 atomic");
        }
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
