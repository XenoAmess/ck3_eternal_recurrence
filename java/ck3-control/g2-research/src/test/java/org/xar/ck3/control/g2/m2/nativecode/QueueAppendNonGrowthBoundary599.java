package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner four rawEntry nongrowth cases, one explicit unsupported-growth boundary and
 * one post-review epilogue-only EAX probe. Not six all-branch/native implementations. */
public final class QueueAppendNonGrowthBoundary599 {
    private QueueAppendNonGrowthBoundary599() { }
    private static final long I=0x140000000L,E=0xC008L,S=0xBFE0L,RET=I+0x3727F12L;
    private static final Bits128 X6=new Bits128(0x61,0x62);
    private record Cell(int width,long address,long value) { }
    private record Access(boolean write,int width,long address,long value) { }
    private record Scenario(String name,List<Cell> initial,VolatileBits input,NonvolatileBits inputN,
            boolean df,List<Access> steps,VolatileBits post,NonvolatileBits postN,long rip,
            long sp,boolean unsupported) { }
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static VolatileBits v(long a,long c,long d){return new VolatileBits(a,c,d,0x1004,0x1005,0x1006,0x1007,
            new Bits128(0x1010,0x1011),new Bits128(0x1020,0x1021),new Bits128(0x1030,0x1031),
            new Bits128(0x1040,0x1041),new Bits128(0x1050,0x1051),new Bits128(0x1060,0x1061));}
    private static NonvolatileBits n(long bx,long si,long di,long r14){return new NonvolatileBits(bx,0x222,si,di,0x555,0x666,r14,0x888,X6);}
    private static final class Ram implements QueueAppend597Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<Access> steps;int cursor;
        Registers probe;int samples;
        Ram(List<Cell> initial,List<Access> events){steps=events;for(Cell c:initial)put(bytes,c.width(),c.address(),c.value());}
        static void put(Map<Long,Byte> m,int w,long a,long x){for(int i=0;i<w;i++)m.put(a+i,(byte)(x>>>(8*i)));}
        long raw(int w,long a){long x=0;for(int i=0;i<w;i++){Byte b=bytes.get(a+i);need(b!=null,"unseeded "+Long.toHexString(a+i));x|=Byte.toUnsignedLong(b)<<(8*i);}return x;}
        void event(boolean write,int w,long a,long x){need(cursor<steps.size(),"trace END");Access got=new Access(write,w,a,x);need(steps.get(cursor).equals(got),"event "+cursor+" got "+got+" expected "+steps.get(cursor));cursor++;}
        long read(int w,long a){long x=raw(w,a);event(false,w,a,x);return x;}
        void write(int w,long a,long x){if(w<8)x&=(1L<<(w*8))-1;event(true,w,a,x);put(bytes,w,a,x);}
        public int readDword(long a){return (int)read(4,a);}
        public long readQword(long a){
            if(probe!=null&&a==E+0x18){
                need(probe.volatileBits().equals(v(0xFFFFFFFFL,0x250000L,-1)),"actual zeroextended intermediate EAX before savedSI read");
                need(probe.nonvolatileBits().equals(n(0x111,0,0x250000,0x241000))&&probe.rsp==S,"current intermediate fullN/SP");samples++;
            }
            return read(8,a);
        }
        public void writeDword(long a,int x){write(4,a,Integer.toUnsignedLong(x));}
        public void writeQword(long a,long x){write(8,a,x);}
        public int readUnsignedByte(long a){throw new AssertionError("unusedBYTE");}
        public void writeByte(long a,int x){throw new AssertionError("unusedBYTE");}
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
        new Scenario("whole_nongrowth_ordinary",List.of(new Cell(8,0x230000L,0x250000L),new Cell(4,0x230008L,0x4L),new Cell(4,0x23000cL,0x1L),new Cell(8,0x241000L,0xa1b2c3d4e5f60718L),new Cell(8,0xc008L,0x143727f12L)),new VolatileBits(0x1001L,0x230000L,0x241000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),false,List.of(new Access(true,8,0xc018L,0x111L),new Access(true,8,0xc020L,0x333L),new Access(true,8,0xc028L,0x444L),new Access(true,8,0xc000L,0x777L),new Access(false,4,0x23000cL,0x1L),new Access(false,4,0x230008L,0x4L),new Access(false,8,0x230000L,0x250000L),new Access(false,8,0x241000L,0xa1b2c3d4e5f60718L),new Access(true,8,0x250008L,0xa1b2c3d4e5f60718L),new Access(false,4,0x23000cL,0x1L),new Access(true,4,0x23000cL,0x2L),new Access(false,4,0x23000cL,0x2L),new Access(false,8,0x230000L,0x250000L),new Access(false,8,0xc018L,0x111L),new Access(false,8,0xc020L,0x333L),new Access(false,8,0xc028L,0x444L),new Access(false,8,0xc000L,0x777L),new Access(false,8,0xc008L,0x143727f12L)),new VolatileBits(0x250008L,0x1L,0x1L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),0x143727f12L,0xc010L,false),
        new Scenario("whole_nongrowth_negative_index_signedafterEAXwrap",List.of(new Cell(8,0x130000L,0x160000L),new Cell(4,0x130008L,0x0L),new Cell(4,0x13000cL,0xfffffffeL),new Cell(8,0x141000L,0x8877665544332211L),new Cell(8,0xc008L,0x143727f12L)),new VolatileBits(0x1001L,0x130000L,0x141000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),true,List.of(new Access(true,8,0xc018L,0x111L),new Access(true,8,0xc020L,0x333L),new Access(true,8,0xc028L,0x444L),new Access(true,8,0xc000L,0x777L),new Access(false,4,0x13000cL,0xfffffffeL),new Access(false,4,0x130008L,0x0L),new Access(false,8,0x130000L,0x160000L),new Access(false,8,0x141000L,0x8877665544332211L),new Access(true,8,0x15fff0L,0x8877665544332211L),new Access(false,4,0x13000cL,0xfffffffeL),new Access(true,4,0x13000cL,0xffffffffL),new Access(false,4,0x13000cL,0xffffffffL),new Access(false,8,0x130000L,0x160000L),new Access(false,8,0xc018L,0x111L),new Access(false,8,0xc020L,0x333L),new Access(false,8,0xc028L,0x444L),new Access(false,8,0xc000L,0x777L),new Access(false,8,0xc008L,0x143727f12L)),new VolatileBits(0x15fff0L,0xfffffffffffffffeL,0xfffffffffffffffeL,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),0x143727f12L,0xc010L,false),
        new Scenario("whole_nongrowth_append_aliasfreshRET",List.of(new Cell(8,0x330000L,0xc000L),new Cell(4,0x330008L,0x4L),new Cell(4,0x33000cL,0x1L),new Cell(8,0x341000L,0x140123456L),new Cell(8,0xc008L,0x143727f12L)),new VolatileBits(0x1001L,0x330000L,0x341000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),true,List.of(new Access(true,8,0xc018L,0x111L),new Access(true,8,0xc020L,0x333L),new Access(true,8,0xc028L,0x444L),new Access(true,8,0xc000L,0x777L),new Access(false,4,0x33000cL,0x1L),new Access(false,4,0x330008L,0x4L),new Access(false,8,0x330000L,0xc000L),new Access(false,8,0x341000L,0x140123456L),new Access(true,8,0xc008L,0x140123456L),new Access(false,4,0x33000cL,0x1L),new Access(true,4,0x33000cL,0x2L),new Access(false,4,0x33000cL,0x2L),new Access(false,8,0x330000L,0xc000L),new Access(false,8,0xc018L,0x111L),new Access(false,8,0xc020L,0x333L),new Access(false,8,0xc028L,0x444L),new Access(false,8,0xc000L,0x777L),new Access(false,8,0xc008L,0x140123456L)),new VolatileBits(0xc008L,0x1L,0x1L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),0x140123456L,0xc010L,false),
        new Scenario("whole_nongrowth_append_aliassavedSIhome",List.of(new Cell(8,0x430000L,0xc018L),new Cell(4,0x430008L,0x4L),new Cell(4,0x43000cL,0x1L),new Cell(8,0x441000L,0x999aaaabbbcccdddL),new Cell(8,0xc008L,0x143727f12L)),new VolatileBits(0x1001L,0x430000L,0x441000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),false,List.of(new Access(true,8,0xc018L,0x111L),new Access(true,8,0xc020L,0x333L),new Access(true,8,0xc028L,0x444L),new Access(true,8,0xc000L,0x777L),new Access(false,4,0x43000cL,0x1L),new Access(false,4,0x430008L,0x4L),new Access(false,8,0x430000L,0xc018L),new Access(false,8,0x441000L,0x999aaaabbbcccdddL),new Access(true,8,0xc020L,0x999aaaabbbcccdddL),new Access(false,4,0x43000cL,0x1L),new Access(true,4,0x43000cL,0x2L),new Access(false,4,0x43000cL,0x2L),new Access(false,8,0x430000L,0xc018L),new Access(false,8,0xc018L,0x111L),new Access(false,8,0xc020L,0x999aaaabbbcccdddL),new Access(false,8,0xc028L,0x444L),new Access(false,8,0xc000L,0x777L),new Access(false,8,0xc008L,0x143727f12L)),new VolatileBits(0xc020L,0x1L,0x1L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x999aaaabbbcccdddL,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),0x143727f12L,0xc010L,false),
        new Scenario("growth_selected_explicitlyunsupported_beforeFP",List.of(new Cell(8,0x530000L,0x560000L),new Cell(4,0x530008L,0x1L),new Cell(4,0x53000cL,0x1L),new Cell(8,0x541000L,0x123456789abcdef0L),new Cell(8,0xc008L,0x143727f12L)),new VolatileBits(0x1001L,0x530000L,0x541000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x333L,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),true,List.of(new Access(true,8,0xc018L,0x111L),new Access(true,8,0xc020L,0x333L),new Access(true,8,0xc028L,0x444L),new Access(true,8,0xc000L,0x777L),new Access(false,4,0x53000cL,0x1L),new Access(false,4,0x530008L,0x1L)),null,null,0x0L,0x0L,true)
    };

    private static void scenario(Scenario c){
        Ram ram=new Ram(c.initial(),c.steps());Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        for(Access x:c.steps())if(x.write())Ram.put(expected,x.width(),x.address(),x.value());
        var entry=new GovernmentCrtBoundary185Api.Entry(I,E,c.input(),c.inputN());
        var input=new FullCopy437Api.Input(entry,c.df(),(header,guard)->{throw new AssertionError("no source loop/budget");});
        FullCopy437Api.CallResult result=null;UnsupportedOperationException failure=null;
        try{result=QueueAppendNonGrowthEntry599.execute(input,ram);}
        catch(UnsupportedOperationException ex){failure=ex;}
        if(c.unsupported())need(result==null&&failure!=null&&failure.getMessage().equals("growth FP input not represented"),"explicitunsupported no fakeNR");
        else{
            need(result!=null&&failure==null,"new supported non-growth path");var nr=result.normalReturn();
            need(nr.volatileBits().equals(c.post())&&nr.nonvolatileBits().equals(c.postN()),"all final represented GPR/XMM "+c.name());
            need(nr.returnRipBits()==c.rip()&&nr.callerRspBits()==c.sp()&&result.postDirectionFlagSet()==c.df(),"fresh actual RET/SP/DF "+c.name());
        }
        need(ram.cursor==c.steps().size()&&ram.bytes.equals(expected),"entire fixed newtrace/all defined RAM "+c.name());
    }
    private static void intermediateEax(){
        var initial=List.of(new Cell(8,E+0x10,0x111),new Cell(8,E+0x18,0x333),new Cell(8,E+0x20,0x444),new Cell(8,E-8,0x777),new Cell(8,E,RET));
        var steps=List.of(new Access(false,8,E+0x10,0x111),new Access(false,8,E+0x18,0x333),new Access(false,8,E+0x20,0x444),new Access(false,8,E-8,0x777),new Access(false,8,E,RET));
        Ram ram=new Ram(initial,steps);Map<Long,Byte> before=new HashMap<>(ram.bytes);
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,S,v(0x12345678,0x250000,-1),n(0x230000,0,0x250000,0x241000)));
        ram.probe=r;var result=QueueAppendEpilogue599.finish(r,ram,true);var nr=result.normalReturn();
        need(ram.samples==1&&ram.cursor==5&&ram.bytes.equals(before),"one directepilogue intermediateprobe/fivefreshreads");
        need(nr.volatileBits().equals(v(0x24FFF8,-1,-1))&&nr.nonvolatileBits().equals(n(0x111,0x333,0x444,0x777)),"directepilogue fullbanks");
        need(nr.returnRipBits()==RET&&nr.callerRspBits()==E+8&&result.postDirectionFlagSet(),"directepilogue actualRET/SP/DF");
    }
    public static int verify(){for(Scenario c:CASES)scenario(c);intermediateEax();return CASES.length+1;}
    public static void main(String[] args){System.out.println(verify());}
}
