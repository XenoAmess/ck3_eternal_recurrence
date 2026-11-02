package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner three new both-actual-callee cases. Full growth remains unsupported. */
public final class EmbeddedQueueKnownBothBoundary601 {
    private EmbeddedQueueKnownBothBoundary601() { }
    private static final long I=0x140000000L,E=0x18008L;
    private record Cell(int width,long address,long value) { }
    private record Event(String kind,int width,long address,long value) { }
    private record Scenario(String name,List<Cell> initial,List<Event> events,VolatileBits post,
            NonvolatileBits postN,long rip,long sp,String failure) { }
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static final VolatileBits INPUT_V=new VolatileBits(0x3001L,0x430000L,0x341000L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L));
    private static final NonvolatileBits INPUT_N=new NonvolatileBits(0x1111L,0x2222L,0x3333L,0x4444L,0x5555L,0x6666L,0x7777L,0x8888L,new Bits128(0x601L,0x602L));
    private static final class Ram implements EmbeddedQueueWithKnownNonGrowth600.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<Event> events;int cursor;
        Ram(List<Cell> initial,List<Event> trace){events=trace;for(Cell c:initial)put(bytes,c.width(),c.address(),c.value());}
        static void put(Map<Long,Byte> map,int w,long a,long value){for(int i=0;i<w;i++)map.put(a+i,(byte)(value>>>(8*i)));}
        long raw(int w,long a){long x=0;for(int i=0;i<w;i++){Byte b=bytes.get(a+i);need(b!=null,"unseeded "+Long.toHexString(a+i));x|=Byte.toUnsignedLong(b)<<(8*i);}return x;}
        void event(String k,int w,long a,long x){need(cursor<events.size(),"trace END");Event got=new Event(k,w,a,x);need(events.get(cursor).equals(got),"event "+cursor+" got "+got+" expected "+events.get(cursor));cursor++;}
        long read(int w,long a){long x=raw(w,a);event("R",w,a,x);return x;}
        void write(int w,long a,long x){if(w<8)x&=(1L<<(w*8))-1;event("W",w,a,x);put(bytes,w,a,x);}
        public int readUnsignedByte(long a){return (int)read(1,a);}
        public void writeByte(long a,int x){write(1,a,x);}
        public int readDword(long a){return (int)read(4,a);}
        public void writeDword(long a,int x){write(4,a,Integer.toUnsignedLong(x));}
        public long readQword(long a){return read(8,a);}
        public void writeQword(long a,long x){write(8,a,x);}
        public int compareExchangeDword(long a,int expected,int desired){
            need(expected==0&&desired==1,"actual lock CAS operands");long old=raw(4,a);
            event("C",4,a,old);if((int)old==expected)put(bytes,4,a,Integer.toUnsignedLong(desired));return (int)old;
        }
        public int readUnsignedWord(long a){throw new AssertionError("unusedWORD");}
        public void writeWord(long a,int x){throw new AssertionError("unusedWORD");}
        public Bits128 read128(long a){throw new AssertionError("unused128");}
        public void write128(long a,Bits128 x){throw new AssertionError("unused128");}
        public int lockedXaddDword(long a,int x){throw new AssertionError("unusedXADD");}
        public void write128NonTemporal(long a,Bits128 x){throw new AssertionError("unusedNT");}
        public FullCopy437Api.Bits256 read256(long a){throw new AssertionError("unused256");}
        public void write256(long a,FullCopy437Api.Bits256 x){throw new AssertionError("unused256");}
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 x){throw new AssertionError("unused256NT");}
        public void sfence(){throw new AssertionError("unusedSFENCE");}
    }
    private static final Scenario[] CASES={
        new Scenario("bothactual_highfirstvector_partialAL",List.of(new Cell(1,0x43004eL,0x0L),new Cell(4,0x430048L,0xffffffffL),new Cell(4,0x43001cL,0x1L),new Cell(8,0x145468a68L,0x100650000L),new Cell(4,0x145468a70L,0x4L),new Cell(4,0x145468a74L,0x0L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0x18008L,0x142345600L),new Cell(8,0x430010L,0x1002500a0L),new Cell(4,0x1002500acL,0x0L)),List.of(new Event("W",8,0x18000L,0x1111L),new Event("R",1,0x43004eL,0x0L),new Event("W",8,0x17fd8L,0x143727ed4L),new Event("R",4,0x43001cL,0x1L),new Event("R",4,0x43001cL,0x1L),new Event("R",8,0x430010L,0x1002500a0L),new Event("R",4,0x1002500acL,0x0L),new Event("R",8,0x17fd8L,0x143727ed4L),new Event("R",4,0x430048L,0xffffffffL),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0x18018L,0x430000L),new Event("W",8,0x17fd8L,0x143727f12L),new Event("W",8,0x17fe8L,0x430000L),new Event("W",8,0x17ff0L,0x3333L),new Event("W",8,0x17ff8L,0x4444L),new Event("W",8,0x17fd0L,0x7777L),new Event("R",4,0x145468a74L,0x0L),new Event("R",4,0x145468a70L,0x4L),new Event("R",8,0x145468a68L,0x100650000L),new Event("R",8,0x18018L,0x430000L),new Event("W",8,0x100650000L,0x430000L),new Event("R",4,0x145468a74L,0x0L),new Event("W",4,0x145468a74L,0x1L),new Event("R",4,0x145468a74L,0x1L),new Event("R",8,0x145468a68L,0x100650000L),new Event("R",8,0x17fe8L,0x430000L),new Event("R",8,0x17ff0L,0x3333L),new Event("R",8,0x17ff8L,0x4444L),new Event("R",8,0x17fd0L,0x7777L),new Event("R",8,0x17fd8L,0x143727f12L),new Event("W",1,0x43004eL,0x1L),new Event("W",4,0x145c9ff68L,0x0L),new Event("R",8,0x18000L,0x1111L),new Event("R",8,0x18008L,0x142345600L)),new VolatileBits(0x100650000L,0x0L,0x0L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),new NonvolatileBits(0x1111L,0x2222L,0x3333L,0x4444L,0x5555L,0x6666L,0x7777L,0x8888L,new Bits128(0x601L,0x602L)),0x142345600L,0x18010L,null),
        new Scenario("bothactual_secondscan_twobudgets",List.of(new Cell(1,0x43004eL,0x0L),new Cell(4,0x430048L,0xffffffffL),new Cell(4,0x43001cL,0x0L),new Cell(8,0x145468a68L,0x100750000L),new Cell(4,0x145468a70L,0x4L),new Cell(4,0x145468a74L,0x1L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0x18008L,0x142345600L),new Cell(8,0x430030L,0x100350000L),new Cell(4,0x43003cL,0x2L),new Cell(1,0x100350044L,0x0L),new Cell(1,0x10035008cL,0x1L)),List.of(new Event("W",8,0x18000L,0x1111L),new Event("R",1,0x43004eL,0x0L),new Event("W",8,0x17fd8L,0x143727ed4L),new Event("R",4,0x43001cL,0x0L),new Event("R",8,0x430030L,0x100350000L),new Event("R",4,0x43003cL,0x2L),new Event("B",0,0x37275b0L,0x100350000L),new Event("R",1,0x100350044L,0x0L),new Event("B",0,0x37275b0L,0x100350048L),new Event("R",1,0x10035008cL,0x1L),new Event("R",8,0x17fd8L,0x143727ed4L),new Event("R",4,0x430048L,0xffffffffL),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0x18018L,0x430000L),new Event("W",8,0x17fd8L,0x143727f12L),new Event("W",8,0x17fe8L,0x430000L),new Event("W",8,0x17ff0L,0x3333L),new Event("W",8,0x17ff8L,0x4444L),new Event("W",8,0x17fd0L,0x7777L),new Event("R",4,0x145468a74L,0x1L),new Event("R",4,0x145468a70L,0x4L),new Event("R",8,0x145468a68L,0x100750000L),new Event("R",8,0x18018L,0x430000L),new Event("W",8,0x100750008L,0x430000L),new Event("R",4,0x145468a74L,0x1L),new Event("W",4,0x145468a74L,0x2L),new Event("R",4,0x145468a74L,0x2L),new Event("R",8,0x145468a68L,0x100750000L),new Event("R",8,0x17fe8L,0x430000L),new Event("R",8,0x17ff0L,0x3333L),new Event("R",8,0x17ff8L,0x4444L),new Event("R",8,0x17fd0L,0x7777L),new Event("R",8,0x17fd8L,0x143727f12L),new Event("W",1,0x43004eL,0x1L),new Event("W",4,0x145c9ff68L,0x0L),new Event("R",8,0x18000L,0x1111L),new Event("R",8,0x18008L,0x142345600L)),new VolatileBits(0x100750008L,0x1L,0x1L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),new NonvolatileBits(0x1111L,0x2222L,0x3333L,0x4444L,0x5555L,0x6666L,0x7777L,0x8888L,new Bits128(0x601L,0x602L)),0x142345600L,0x18010L,null),
        new Scenario("bothactual_childRETalias_guardfailure",List.of(new Cell(1,0x43004eL,0x0L),new Cell(4,0x430048L,0xffffffffL),new Cell(4,0x43001cL,0x1L),new Cell(8,0x145468a68L,0x17fd0L),new Cell(4,0x145468a70L,0x4L),new Cell(4,0x145468a74L,0x1L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0x18008L,0x142345600L),new Cell(8,0x430010L,0x1002500a0L),new Cell(4,0x1002500acL,0x0L)),List.of(new Event("W",8,0x18000L,0x1111L),new Event("R",1,0x43004eL,0x0L),new Event("W",8,0x17fd8L,0x143727ed4L),new Event("R",4,0x43001cL,0x1L),new Event("R",4,0x43001cL,0x1L),new Event("R",8,0x430010L,0x1002500a0L),new Event("R",4,0x1002500acL,0x0L),new Event("R",8,0x17fd8L,0x143727ed4L),new Event("R",4,0x430048L,0xffffffffL),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0x18018L,0x430000L),new Event("W",8,0x17fd8L,0x143727f12L),new Event("W",8,0x17fe8L,0x430000L),new Event("W",8,0x17ff0L,0x3333L),new Event("W",8,0x17ff8L,0x4444L),new Event("W",8,0x17fd0L,0x7777L),new Event("R",4,0x145468a74L,0x1L),new Event("R",4,0x145468a70L,0x4L),new Event("R",8,0x145468a68L,0x17fd0L),new Event("R",8,0x18018L,0x430000L),new Event("W",8,0x17fd8L,0x430000L),new Event("R",4,0x145468a74L,0x1L),new Event("W",4,0x145468a74L,0x2L),new Event("R",4,0x145468a74L,0x2L),new Event("R",8,0x145468a68L,0x17fd0L),new Event("R",8,0x17fe8L,0x430000L),new Event("R",8,0x17ff0L,0x3333L),new Event("R",8,0x17ff8L,0x4444L),new Event("R",8,0x17fd0L,0x7777L),new Event("R",8,0x17fd8L,0x430000L)),null,null,0L,0L,"Return RIP mismatch")
    };
    private static void scenario(Scenario c){
        Ram ram=new Ram(c.initial(),c.events());Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        for(Event e:c.events()){
            if(e.kind().equals("W"))Ram.put(expected,e.width(),e.address(),e.value());
            else if(e.kind().equals("C"))Ram.put(expected,4,e.address(),1);
        }
        var budget=(GovernmentCrtBoundary185Api.LoopBudget)(header,guard)->ram.event("B",0,header,guard);
        var input=new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,INPUT_V,INPUT_N),true,budget);
        FullCopy437Api.CallResult result=null;RuntimeException failure=null;
        try{result=EmbeddedQueueWithKnownBoth601.execute(input,ram);}
        catch(RuntimeException ex){failure=ex;}
        if(c.failure()==null){
            need(failure==null&&result!=null,"normal bothactualcallee "+c.name());var nr=result.normalReturn();
            need(nr.volatileBits().equals(c.post())&&nr.nonvolatileBits().equals(c.postN()),"normal fullV/N/XMM");
            need(nr.returnRipBits()==c.rip()&&nr.callerRspBits()==c.sp()&&result.postDirectionFlagSet(),"normal actual outerRET/SP/DF");
        }else{
            need(result==null&&failure!=null&&failure.getClass()==IllegalArgumentException.class&&failure.getMessage().equals(c.failure()),"actual originalcaller RETguardfailure "+c.name());
        }
        need(ram.cursor==c.events().size()&&ram.bytes.equals(expected),"wholebothactualtrace/sameRAM/zeroopaque/allownedbytes "+c.name());
    }
    public static int verify(){for(Scenario c:CASES)scenario(c);return CASES.length;}
    public static void main(String[] args){System.out.println(verify());}
}
