package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner fixed original-source75B postallocation cases. Not full227 or native execution. */
public final class QueueAppendGrowthBoundary598 {
    private QueueAppendGrowthBoundary598() { }
    private static final long I=0x140000000L,S=0xC000L;
    private static final RuntimeException MARKER=new UnsupportedOperationException("owned598");
    private sealed interface Step permits Access,Invoke { }
    private record Cell(int width,long address,long value) { }
    private record Access(boolean write,int width,long address,long value) implements Step { }
    private record Invoke(long site,GovernmentCrtBoundary185Api.TargetKind kind,long target,
            int length,long rip,long sp,long childSP,boolean df,VolatileBits offered,
            NonvolatileBits n,VolatileBits post,boolean postDF,long resultRIP,long resultSP,
            List<Access> effects,boolean throwMarker) implements Step { }
    private record Scenario(String name,List<Cell> initial,VolatileBits input,NonvolatileBits inputN,
            boolean inputDF,List<Step> steps,VolatileBits post,NonvolatileBits postN,
            long postSP,boolean postDF,String failure) { }
    private static void need(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static final class Ram implements QueueAppend597Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final Scenario scenario;int cursor;
        Ram(Scenario c){scenario=c;for(Cell x:c.initial())put(bytes,x.width(),x.address(),x.value());}
        static void put(Map<Long,Byte> map,int width,long a,long v){for(int i=0;i<width;i++)map.put(a+i,(byte)(v>>>(8*i)));}
        long raw(int width,long a){long value=0;for(int i=0;i<width;i++){Byte b=bytes.get(a+i);need(b!=null,"unseeded "+Long.toHexString(a+i));value|=Byte.toUnsignedLong(b)<<(8*i);}return value;}
        Step next(){need(cursor<scenario.steps().size(),"trace exhausted");return scenario.steps().get(cursor);}
        void access(boolean write,int width,long a,long v){need(next() instanceof Access,"expected memory event "+cursor);Access x=(Access)next();need(x.equals(new Access(write,width,a,v)),"memory mismatch "+cursor+" got "+new Access(write,width,a,v)+" expected "+x);cursor++;}
        long read(int width,long a){long v=raw(width,a);access(false,width,a,v);return v;}
        void write(int width,long a,long v){if(width<8)v&=(1L<<(width*8))-1;access(true,width,a,v);put(bytes,width,a,v);}
        public int readDword(long a){return (int)read(4,a);}
        public long readQword(long a){return read(8,a);}
        public void writeDword(long a,int v){write(4,a,Integer.toUnsignedLong(v));}
        public void writeQword(long a,long v){write(8,a,v);}
        public int readUnsignedByte(long a){throw new AssertionError("unused BYTE");}
        public void writeByte(long a,int v){throw new AssertionError("unused BYTE");}
        public int readUnsignedWord(long a){throw new AssertionError("unused WORD");}
        public void writeWord(long a,int v){throw new AssertionError("unused WORD");}
        public Bits128 read128(long a){throw new AssertionError("unused128");}
        public void write128(long a,Bits128 v){throw new AssertionError("unused128");}
        public int lockedXaddDword(long a,int v){throw new AssertionError("unused XADD");}
        public void write128NonTemporal(long a,Bits128 v){throw new AssertionError("unusedNT");}
        public FullCopy437Api.Bits256 read256(long a){throw new AssertionError("unused256");}
        public void write256(long a,FullCopy437Api.Bits256 v){throw new AssertionError("unused256");}
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 v){throw new AssertionError("unused256NT");}
        public void sfence(){throw new AssertionError("unusedSFENCE");}
        FullCopy437Api.CallResult invoke(QueueAppend597Api.CallFrame f){
            need(next() instanceof Invoke,"expected invoke "+cursor);Invoke x=(Invoke)next();
            var c=f.call();var child=f.childEntry();
            need(c.callSiteRva()==x.site()&&c.kind()==x.kind()&&c.targetBits()==x.target()&&c.rspBits()==x.sp(),"exact actual CALL");
            need(c.volatileBits().equals(x.offered())&&c.nonvolatileBits().equals(x.n()),"current full CALL bank");
            need(child.imageBaseBits()==I&&child.rspBits()==x.childSP()&&child.volatileBits().equals(x.offered())&&child.nonvolatileBits().equals(x.n()),"exact child Entry");
            need(f.instructionLength()==x.length()&&f.returnRipBits()==x.rip()&&f.directionFlagSet()==x.df(),"typed Frame/DF");
            cursor++;
            for(Access effect:x.effects()){
                need(effect.write(),"effect writes only");
                if(effect.width()==4)writeDword(effect.address(),(int)effect.value());
                else if(effect.width()==8)writeQword(effect.address(),effect.value());
                else throw new AssertionError("unsupported effect width");
            }
            if(x.throwMarker())throw MARKER;
            return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                    x.post(),x.resultRIP(),x.resultSP(),x.n()),x.postDF());
        }
        Map<Long,Byte> expectedBytes(){
            Map<Long,Byte> result=new HashMap<>();for(Cell c:scenario.initial())put(result,c.width(),c.address(),c.value());
            for(Step step:scenario.steps())if(step instanceof Access a&&a.write())put(result,a.width(),a.address(),a.value());
            return result;
        }
    }
    private static final Scenario[] CASES={
        new Scenario("positiveCOPY_then_freshallocator_FREE_then_freshsavedhome",
            List.of(new Cell(8,0x30000L,0x50000L),new Cell(4,0x30008L,0x1L),new Cell(4,0x3000cL,0x1L),new Cell(8,0x30010L,0x60000L),new Cell(8,0x41000L,0x1122334455667788L),new Cell(8,0xc030L,0x222L),new Cell(8,0x61000L,0x81000L),new Cell(8,0x81010L,0x7ff612345670L)),
            new VolatileBits(0x70000L,0x1002L,0x1003L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x30000L,0x2L,0x2L,0x444L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),true,
            List.<Step>of(
            new Access(false,4,0x3000cL,0x1L),
            new Access(false,8,0x41000L,0x1122334455667788L),
            new Access(true,8,0x70008L,0x1122334455667788L),
            new Access(false,4,0x3000cL,0x1L),
            new Access(false,8,0x30000L,0x50000L),
            new Access(true,8,0xbff8L,0x1408803caL),
            new Invoke(0x8803c5L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860L,5,0x1408803caL,0xc000L,0xbff8L,true,new VolatileBits(0x1L,0x70000L,0x50000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x30000L,0x2L,0x2L,0x70000L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x2001L,0x2002L,0x2003L,0x2004L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),false,0x1408803caL,0xc000L,List.of(new Access(true,8,0x30010L,0x61000L),new Access(true,8,0x30000L,0x51000L)),false),
            new Access(true,8,0x30010L,0x61000L),
            new Access(true,8,0x30000L,0x51000L),
            new Access(false,8,0x30010L,0x61000L),
            new Access(false,8,0x30000L,0x51000L),
            new Access(false,8,0x61000L,0x81000L),
            new Access(false,8,0x81010L,0x7ff612345670L),
            new Access(true,8,0xbff8L,0x1408803ddL),
            new Invoke(0x8803daL,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x7ff612345670L,3,0x1408803ddL,0xc000L,0xbff8L,false,new VolatileBits(0x81000L,0x61000L,0x51000L,0x8L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),new NonvolatileBits(0x30000L,0x2L,0x2L,0x70000L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),true,0x1408803ddL,0xc000L,List.of(new Access(true,8,0xc030L,0xf1f2f3f4f5f6f7f8L),new Access(true,8,0x30000L,0xdead0000L),new Access(true,4,0x30008L,0xaabbccddL),new Access(true,4,0x3000cL,0x55667788L)),false),
            new Access(true,8,0xc030L,0xf1f2f3f4f5f6f7f8L),
            new Access(true,8,0x30000L,0xdead0000L),
            new Access(true,4,0x30008L,0xaabbccddL),
            new Access(true,4,0x3000cL,0x55667788L),
            new Access(true,4,0x30008L,0x2L),
            new Access(false,8,0xc030L,0xf1f2f3f4f5f6f7f8L),
            new Access(true,8,0x30000L,0x70000L),
            new Access(true,4,0x3000cL,0x2L)),
            new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),
            new NonvolatileBits(0x30000L,0xf1f2f3f4f5f6f7f8L,0x2L,0x70000L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),0xc000L,true,null),
        new Scenario("high64append_aliascount_zero_skipsCOPY_and_changesallocator",
            List.of(new Cell(8,0x110000030000L,0x550000070000L),new Cell(4,0x110000030008L,0x1L),new Cell(4,0x11000003000cL,0x1L),new Cell(8,0x110000030010L,0x333344445555L),new Cell(8,0x220000041000L,0x2233445500000000L),new Cell(8,0xc030L,0x222L),new Cell(8,0x333322334455L,0x440000060000L),new Cell(8,0x440000060010L,0x7ff612345680L)),
            new VolatileBits(0x110000030004L,0x1002L,0x1003L,0xffffffff000000aaL,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x110000030000L,0x2L,0x2L,0x444L,0x555L,0x666L,0x220000041000L,0x888L,new Bits128(0x61L,0x62L)),false,
            List.<Step>of(
            new Access(false,4,0x11000003000cL,0x1L),
            new Access(false,8,0x220000041000L,0x2233445500000000L),
            new Access(true,8,0x11000003000cL,0x2233445500000000L),
            new Access(false,4,0x11000003000cL,0x0L),
            new Access(false,8,0x110000030010L,0x333322334455L),
            new Access(false,8,0x110000030000L,0x550000070000L),
            new Access(false,8,0x333322334455L,0x440000060000L),
            new Access(false,8,0x440000060010L,0x7ff612345680L),
            new Access(true,8,0xbff8L,0x1408803ddL),
            new Invoke(0x8803daL,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x7ff612345680L,3,0x1408803ddL,0xc000L,0xbff8L,false,new VolatileBits(0x440000060000L,0x333322334455L,0x550000070000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x110000030000L,0x2L,0x2L,0x110000030004L,0x555L,0x666L,0x220000041000L,0x888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),true,0x1408803ddL,0xc000L,List.of(new Access(true,8,0xc030L,0xf1f2f3f4f5f6f7f8L),new Access(true,4,0x11000003000cL,0xffffffffL)),false),
            new Access(true,8,0xc030L,0xf1f2f3f4f5f6f7f8L),
            new Access(true,4,0x11000003000cL,0xffffffffL),
            new Access(true,4,0x110000030008L,0x2L),
            new Access(false,8,0xc030L,0xf1f2f3f4f5f6f7f8L),
            new Access(true,8,0x110000030000L,0x110000030004L),
            new Access(true,4,0x11000003000cL,0x2L)),
            new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),
            new NonvolatileBits(0x110000030000L,0xf1f2f3f4f5f6f7f8L,0x2L,0x110000030004L,0x555L,0x666L,0x220000041000L,0x888L,new Bits128(0x61L,0x62L)),0xc000L,true,null),
        new Scenario("negative_freshcount_skipsCOPY_preserves_capturedincrement_zero",
            List.of(new Cell(8,0x130000L,0x150000L),new Cell(4,0x130008L,0xffffffffL),new Cell(4,0x13000cL,0xffffffffL),new Cell(8,0x130010L,0x160000L),new Cell(8,0x141000L,0x8877665544332211L),new Cell(8,0xc030L,0x222L),new Cell(8,0x160000L,0x180000L),new Cell(8,0x180010L,0x7ff612345690L)),
            new VolatileBits(0x170000L,0x1002L,0x1003L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x130000L,0x0L,0x0L,0x444L,0x555L,0x666L,0x141000L,0x888L,new Bits128(0x61L,0x62L)),true,
            List.<Step>of(
            new Access(false,4,0x13000cL,0xffffffffL),
            new Access(false,8,0x141000L,0x8877665544332211L),
            new Access(true,8,0x16fff8L,0x8877665544332211L),
            new Access(false,4,0x13000cL,0xffffffffL),
            new Access(false,8,0x130010L,0x160000L),
            new Access(false,8,0x130000L,0x150000L),
            new Access(false,8,0x160000L,0x180000L),
            new Access(false,8,0x180010L,0x7ff612345690L),
            new Access(true,8,0xbff8L,0x1408803ddL),
            new Invoke(0x8803daL,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x7ff612345690L,3,0x1408803ddL,0xc000L,0xbff8L,true,new VolatileBits(0x180000L,0x160000L,0x150000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x130000L,0x0L,0x0L,0x170000L,0x555L,0x666L,0x141000L,0x888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),false,0x1408803ddL,0xc000L,List.of(),false),
            new Access(true,4,0x130008L,0x0L),
            new Access(false,8,0xc030L,0x222L),
            new Access(true,8,0x130000L,0x170000L),
            new Access(true,4,0x13000cL,0x0L)),
            new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),
            new NonvolatileBits(0x130000L,0x222L,0x0L,0x170000L,0x555L,0x666L,0x141000L,0x888L,new Bits128(0x61L,0x62L)),0xc000L,false,null),
        new Scenario("COPY_badactualNR_keeps_prior_effects_no_poststate_repair",
            List.of(new Cell(8,0x30000L,0x50000L),new Cell(4,0x30008L,0x1L),new Cell(4,0x3000cL,0x1L),new Cell(8,0x30010L,0x60000L),new Cell(8,0x41000L,0x1122334455667788L),new Cell(8,0xc030L,0x222L),new Cell(8,0x61000L,0x81000L),new Cell(8,0x81010L,0x7ff612345670L)),
            new VolatileBits(0x70000L,0x1002L,0x1003L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x30000L,0x2L,0x2L,0x444L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),true,
            List.<Step>of(
            new Access(false,4,0x3000cL,0x1L),
            new Access(false,8,0x41000L,0x1122334455667788L),
            new Access(true,8,0x70008L,0x1122334455667788L),
            new Access(false,4,0x3000cL,0x1L),
            new Access(false,8,0x30000L,0x50000L),
            new Access(true,8,0xbff8L,0x1408803caL),
            new Invoke(0x8803c5L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860L,5,0x1408803caL,0xc000L,0xbff8L,true,new VolatileBits(0x1L,0x70000L,0x50000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x30000L,0x2L,0x2L,0x70000L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x2001L,0x2002L,0x2003L,0x2004L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),false,0x1408803cbL,0xc000L,List.of(new Access(true,8,0xc030L,0xa1a2a3a4a5a6a7a8L)),false),
            new Access(true,8,0xc030L,0xa1a2a3a4a5a6a7a8L)),
            new VolatileBits(0x1L,0x70000L,0x50000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x30000L,0x2L,0x2L,0x70000L,0x555L,0x666L,0x41000L,0x888L,new Bits128(0x61L,0x62L)),0xbff8L,false,"IllegalArgumentException"),
        new Scenario("FREE_callback_marker_identity_no_final_writeback",
            List.of(new Cell(8,0x90000L,0x93000L),new Cell(4,0x90008L,0x0L),new Cell(4,0x9000cL,0x0L),new Cell(8,0x90010L,0x94000L),new Cell(8,0x91000L,0x123456789abcdef0L),new Cell(8,0xc030L,0x222L),new Cell(8,0x94000L,0x95000L),new Cell(8,0x95010L,0x7ff6123456a0L)),
            new VolatileBits(0x92000L,0x1002L,0x1003L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x90000L,0x1L,0x1L,0x444L,0x555L,0x666L,0x91000L,0x888L,new Bits128(0x61L,0x62L)),true,
            List.<Step>of(
            new Access(false,4,0x9000cL,0x0L),
            new Access(false,8,0x91000L,0x123456789abcdef0L),
            new Access(true,8,0x92000L,0x123456789abcdef0L),
            new Access(false,4,0x9000cL,0x0L),
            new Access(false,8,0x90010L,0x94000L),
            new Access(false,8,0x90000L,0x93000L),
            new Access(false,8,0x94000L,0x95000L),
            new Access(false,8,0x95010L,0x7ff6123456a0L),
            new Access(true,8,0xbff8L,0x1408803ddL),
            new Invoke(0x8803daL,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x7ff6123456a0L,3,0x1408803ddL,0xc000L,0xbff8L,true,new VolatileBits(0x95000L,0x94000L,0x93000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x90000L,0x1L,0x1L,0x92000L,0x555L,0x666L,0x91000L,0x888L,new Bits128(0x61L,0x62L)),new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),true,0x1408803ddL,0xc000L,List.of(new Access(true,8,0xc030L,0xb1b2b3b4b5b6b7b8L)),true),
            new Access(true,8,0xc030L,0xb1b2b3b4b5b6b7b8L)),
            new VolatileBits(0x95000L,0x94000L,0x93000L,0x8L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),
            new NonvolatileBits(0x90000L,0x1L,0x1L,0x92000L,0x555L,0x666L,0x91000L,0x888L,new Bits128(0x61L,0x62L)),0xbff8L,false,"same_marker_identity")
    };

    private static void verify(Scenario c){
        Ram ram=new Ram(c);Map<Long,Byte> expected=ram.expectedBytes();
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,S,c.input(),c.inputN()));
        RuntimeException caught=null;boolean postDF=false;
        try{postDF=QueueAppendGrowthContinuation598.resume(I,r,c.inputDF(),ram,ram::invoke);}
        catch(IllegalArgumentException|UnsupportedOperationException ex){caught=ex;}
        if(c.failure()==null){need(caught==null,"unexpected failure "+c.name());need(postDF==c.postDF(),"actual postDF "+c.name());}
        else if(c.failure().equals("same_marker_identity"))need(caught==MARKER,"callback same failure identity");
        else need(caught instanceof IllegalArgumentException,"bad actual normal return rejected");
        need(ram.cursor==c.steps().size(),"whole fixed new trace consumed "+c.name());
        need(r.volatileBits().equals(c.post()),"all actual volatile/XMM "+c.name());
        need(r.nonvolatileBits().equals(c.postN())&&r.rsp==c.postSP(),"all current N/XMM6/SP "+c.name());
        need(ram.bytes.equals(expected),"all fixed defined RAM bytes "+c.name());
    }
    public static int verify(){for(Scenario c:CASES)verify(c);return CASES.length;}
    public static void main(String[] args){System.out.println(verify());}
}
