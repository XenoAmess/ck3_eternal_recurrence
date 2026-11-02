package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner four new actual591-to599 binding cases. Full growth remains unsupported. */
public final class EmbeddedQueueKnownNonGrowthBoundary600 {
    private EmbeddedQueueKnownNonGrowthBoundary600() { }
    private static final long I=0x140000000L,E=0xE008L,S=0xDFE0L,CE=0xDFD8L,O=0x330000L;
    private record Cell(int width,long address,long value) { }
    private record Event(String kind,int width,long address,long value) { }
    private record Scenario(String name,List<Cell> initial,List<Event> events,VolatileBits post,
            NonvolatileBits postN,long rip,long sp,String failure) { }
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static final VolatileBits INPUT_V=new VolatileBits(0x1001L,0x330000L,0x241000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L));
    private static final NonvolatileBits INPUT_N=new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L));
    private static final NonvolatileBits PRIMARY_N=new NonvolatileBits(0x330000L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L));
    private static final FullCopy437Api.CallResult PRIMARY_RESULT=new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(new VolatileBits(0xab00L,0x2102L,0x1234L,0x2004L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),I+0x3727ED4L,S,new NonvolatileBits(0x330000L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L))),true);
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
        new Scenario("newwhole_591_to_actual599_nonGrowth",List.of(new Cell(1,0x33004eL,0x0L),new Cell(4,0x330048L,0x7L),new Cell(8,0x145468a68L,0x250000L),new Cell(4,0x145468a70L,0x4L),new Cell(4,0x145468a74L,0x0L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0xe008L,0x141234500L)),List.of(new Event("W",8,0xe000L,0x111L),new Event("R",1,0x33004eL,0x0L),new Event("W",8,0xdfd8L,0x143727ed4L),new Event("I",0,0x0L,0x0L),new Event("R",4,0x330048L,0x7L),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0xe018L,0x330000L),new Event("W",8,0xdfd8L,0x143727f12L),new Event("W",8,0xdfe8L,0x330000L),new Event("W",8,0xdff0L,0x333L),new Event("W",8,0xdff8L,0x444L),new Event("W",8,0xdfd0L,0x777L),new Event("R",4,0x145468a74L,0x0L),new Event("R",4,0x145468a70L,0x4L),new Event("R",8,0x145468a68L,0x250000L),new Event("R",8,0xe018L,0x330000L),new Event("W",8,0x250000L,0x330000L),new Event("R",4,0x145468a74L,0x0L),new Event("W",4,0x145468a74L,0x1L),new Event("R",4,0x145468a74L,0x1L),new Event("R",8,0x145468a68L,0x250000L),new Event("R",8,0xdfe8L,0x330000L),new Event("R",8,0xdff0L,0x333L),new Event("R",8,0xdff8L,0x444L),new Event("R",8,0xdfd0L,0x777L),new Event("R",8,0xdfd8L,0x143727f12L),new Event("W",1,0x33004eL,0x1L),new Event("W",4,0x145c9ff68L,0x0L),new Event("R",8,0xe000L,0x111L),new Event("R",8,0xe008L,0x141234500L)),new VolatileBits(0x250000L,0x0L,0x0L,0x2004L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),0x141234500L,0xe010L,null),
        new Scenario("newwhole_append_alias_childsavedSI",List.of(new Cell(1,0x33004eL,0x0L),new Cell(4,0x330048L,0x7L),new Cell(8,0x145468a68L,0xdfe8L),new Cell(4,0x145468a70L,0x4L),new Cell(4,0x145468a74L,0x1L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0xe008L,0x141234500L)),List.of(new Event("W",8,0xe000L,0x111L),new Event("R",1,0x33004eL,0x0L),new Event("W",8,0xdfd8L,0x143727ed4L),new Event("I",0,0x0L,0x0L),new Event("R",4,0x330048L,0x7L),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0xe018L,0x330000L),new Event("W",8,0xdfd8L,0x143727f12L),new Event("W",8,0xdfe8L,0x330000L),new Event("W",8,0xdff0L,0x333L),new Event("W",8,0xdff8L,0x444L),new Event("W",8,0xdfd0L,0x777L),new Event("R",4,0x145468a74L,0x1L),new Event("R",4,0x145468a70L,0x4L),new Event("R",8,0x145468a68L,0xdfe8L),new Event("R",8,0xe018L,0x330000L),new Event("W",8,0xdff0L,0x330000L),new Event("R",4,0x145468a74L,0x1L),new Event("W",4,0x145468a74L,0x2L),new Event("R",4,0x145468a74L,0x2L),new Event("R",8,0x145468a68L,0xdfe8L),new Event("R",8,0xdfe8L,0x330000L),new Event("R",8,0xdff0L,0x330000L),new Event("R",8,0xdff8L,0x444L),new Event("R",8,0xdfd0L,0x777L),new Event("R",8,0xdfd8L,0x143727f12L)),null,null,0L,0L,"Nonvolatile mismatch"),
        new Scenario("newwhole_append_alias_childRET",List.of(new Cell(1,0x33004eL,0x0L),new Cell(4,0x330048L,0x7L),new Cell(8,0x145468a68L,0xdfd0L),new Cell(4,0x145468a70L,0x4L),new Cell(4,0x145468a74L,0x1L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0xe008L,0x141234500L)),List.of(new Event("W",8,0xe000L,0x111L),new Event("R",1,0x33004eL,0x0L),new Event("W",8,0xdfd8L,0x143727ed4L),new Event("I",0,0x0L,0x0L),new Event("R",4,0x330048L,0x7L),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0xe018L,0x330000L),new Event("W",8,0xdfd8L,0x143727f12L),new Event("W",8,0xdfe8L,0x330000L),new Event("W",8,0xdff0L,0x333L),new Event("W",8,0xdff8L,0x444L),new Event("W",8,0xdfd0L,0x777L),new Event("R",4,0x145468a74L,0x1L),new Event("R",4,0x145468a70L,0x4L),new Event("R",8,0x145468a68L,0xdfd0L),new Event("R",8,0xe018L,0x330000L),new Event("W",8,0xdfd8L,0x330000L),new Event("R",4,0x145468a74L,0x1L),new Event("W",4,0x145468a74L,0x2L),new Event("R",4,0x145468a74L,0x2L),new Event("R",8,0x145468a68L,0xdfd0L),new Event("R",8,0xdfe8L,0x330000L),new Event("R",8,0xdff0L,0x333L),new Event("R",8,0xdff8L,0x444L),new Event("R",8,0xdfd0L,0x777L),new Event("R",8,0xdfd8L,0x330000L)),null,null,0L,0L,"Return RIP mismatch"),
        new Scenario("newwhole_growth_explicitlyunsupported",List.of(new Cell(1,0x33004eL,0x0L),new Cell(4,0x330048L,0x7L),new Cell(8,0x145468a68L,0x250000L),new Cell(4,0x145468a70L,0x2L),new Cell(4,0x145468a74L,0x2L),new Cell(4,0x145c9ff68L,0x0L),new Cell(8,0xe008L,0x141234500L)),List.of(new Event("W",8,0xe000L,0x111L),new Event("R",1,0x33004eL,0x0L),new Event("W",8,0xdfd8L,0x143727ed4L),new Event("I",0,0x0L,0x0L),new Event("R",4,0x330048L,0x7L),new Event("B",0,0x3727ee4L,0x145c9ff68L),new Event("R",4,0x145c9ff68L,0x0L),new Event("C",4,0x145c9ff68L,0x0L),new Event("W",8,0xe018L,0x330000L),new Event("W",8,0xdfd8L,0x143727f12L),new Event("W",8,0xdfe8L,0x330000L),new Event("W",8,0xdff0L,0x333L),new Event("W",8,0xdff8L,0x444L),new Event("W",8,0xdfd0L,0x777L),new Event("R",4,0x145468a74L,0x2L),new Event("R",4,0x145468a70L,0x2L)),null,null,0L,0L,"growth FP input not represented")
    };
    private static void scenario(Scenario c){
        Ram ram=new Ram(c.initial(),c.events());Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        for(Event e:c.events()){
            if(e.kind().equals("W"))Ram.put(expected,e.width(),e.address(),e.value());
            else if(e.kind().equals("C"))Ram.put(expected,4,e.address(),1);
        }
        var budget=(GovernmentCrtBoundary185Api.LoopBudget)(header,guard)->ram.event("B",0,header,guard);
        var input=new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,INPUT_V,INPUT_N),false,budget);
        int[] invocations={0};
        EmbeddedQueue591Api.Calls primary=frame->{
            ram.event("I",0,0,0);invocations[0]++;
            var call=frame.call();var child=frame.childEntry();
            need(call.callSiteRva()==0x3727ECFL&&call.kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA&&call.targetBits()==0x3727580L,"only first original predicate opaque");
            need(frame.instructionLength()==5&&frame.returnRipBits()==I+0x3727ED4L&&!frame.directionFlagSet(),"actual primary CALL length/RIP/DF");
            need(call.rspBits()==S&&call.volatileBits().equals(INPUT_V)&&call.nonvolatileBits().equals(PRIMARY_N),"full primary beforestate");
            need(child.imageBaseBits()==I&&child.rspBits()==CE&&child.volatileBits().equals(INPUT_V)&&child.nonvolatileBits().equals(PRIMARY_N),"actual primary childEntry");
            return PRIMARY_RESULT;
        };
        FullCopy437Api.CallResult result=null;RuntimeException failure=null;
        try{result=EmbeddedQueueWithKnownNonGrowth600.execute(input,ram,primary);}
        catch(RuntimeException ex){failure=ex;}
        if(c.failure()==null){
            need(failure==null&&result!=null,"normal actual591-to599 "+c.name());var nr=result.normalReturn();
            need(nr.volatileBits().equals(c.post())&&nr.nonvolatileBits().equals(c.postN()),"normal fullV/N/XMM");
            need(nr.returnRipBits()==c.rip()&&nr.callerRspBits()==c.sp()&&result.postDirectionFlagSet(),"normal actual outerRET/SP/DF");
        }else{
            boolean growth=c.failure().equals("growth FP input not represented");
            need(result==null&&failure!=null&&failure.getMessage().equals(c.failure()),"exact failurepoint "+c.name());
            need(growth?failure.getClass()==UnsupportedOperationException.class:failure.getClass()==IllegalArgumentException.class,"actual failure class");
        }
        need(invocations[0]==1&&ram.cursor==c.events().size()&&ram.bytes.equals(expected),"whole newtrace/sameRAM/oneopaque/allownedbytes "+c.name());
    }
    public static int verify(){for(Scenario c:CASES)scenario(c);return CASES.length;}
    public static void main(String[] args){System.out.println(verify());}
}
