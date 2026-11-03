package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import static org.xar.ck3.control.g2.m2.nativecode.ReverseFixture641.*;
/** Owner finite literal expectations independently frozen from held194; no target-generated oracle. */
public final class ReverseBoundary641 {
    private ReverseBoundary641() { }
    private static final long B=0x8000000000004100L,FEATURE=IMAGE+0x542f09c;
    private static final QueueFp604Api.Mxcsr FP=new QueueFp604Api.Mxcsr(8,12);
    private static final class Fault extends RuntimeException {private static final long serialVersionUID=1L;}
    private static Bits128 w(int a,int b,int c,int d) {return new Bits128(Integer.toUnsignedLong(a)|(long)b<<32,Integer.toUnsignedLong(c)|(long)d<<32);}
    private static FullCopy437Api.Bits256 y(int a,int b,int c,int d,int e,int f,int g,int h) {return new FullCopy437Api.Bits256(w(a,b,c,d),w(e,f,g,h));}
    private static void seedWords(Ram r,int[] words) {for(int j=0;j<words.length;j++)r.seed(B+4L*j,4,words[j]);}
    private static Ram ram(int[] words,int feature) {Ram r=new Ram();r.seed(SP,8,RIP);r.seed(FEATURE,4,feature);r.seed(B-1,1,0xaa);r.seed(B+4L*words.length,1,0xbb);seedWords(r,words);return r;}
    private static void e(List<Event> z,String k,long p,long v) {z.add(ReverseFixture641.e(k,p,v));}
    private static void e16(List<Event> z,String k,long p,Bits128 v) {z.add(e128(k,p,v));}
    private static void e32(List<Event> z,String k,long p,FullCopy437Api.Bits256 v) {z.add(e256(k,p,v));}
    private static VolatileBits want(VolatileBits v,long ax,long cx,long dx,long r8,Bits128 x0,Bits128 x1,Bits128 x2,Bits128 x3) {return new VolatileBits(ax,cx,dx,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),x0,x1,x2,x3,v.xmm4(),v.xmm5());}
    private static void compare(Ram r,Ram expected,List<Event> z) {
        if(!r.events.equals(z)){int j=0;while(j<r.events.size()&&j<z.size()&&r.events.get(j).equals(z.get(j)))j++;throw new AssertionError("641 cursor"+j+" actual="+(j<r.events.size()?r.events.get(j):"END")+" expected="+(j<z.size()?z.get(j):"END"));}
        check(r.bytes.equals(expected.bytes),"entireRAM including padding/RET/feature");
    }
    private static void checkNormal(QueueFp604Api.Normal result,VolatileBits vv,boolean df) {check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(vv,RIP,SP+8,initialN()))&&result.base().postDirectionFlagSet()==df&&result.postMxcsr()==FP,"fullV/N/SP/RIP/DF/samepartialMXCSR");}
    private static void scalar(int mode) {
        int[] data=mode==0?new int[]{}:mode==1?new int[]{0x80000001,2,0xfedcba98}:new int[]{1,-2,3,-4};Ram r=ram(data,0x20),expected=ram(data,0x20);long end=B+4L*data.length;VolatileBits a=initialV(B,end);List<Event> z=new ArrayList<>();VolatileBits vv;
        if(mode==0)vv=want(a,0,B,B,B,a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3());
        else if(mode==1){
            seedWords(expected,new int[]{0xfedcba98,2,0x80000001});
            e(z,"BUDGET",0x4220b49,B);e(z,"R32",B,0xffffffff80000001L);e(z,"R32",B+8,0xfffffffffedcba98L);e(z,"W32",B,0xfffffffffedcba98L);e(z,"W32",B+8,0xffffffff80000001L);e(z,"BUDGET",0x4220b49,B+4);
            vv=want(a,0xfedcba98L,0x80000001L,B+4,B+4,a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3());
        }else{
            seedWords(expected,new int[]{-4,3,-2,1});e(z,"BUDGET",0x4220b49,B);e(z,"R32",B,1);e(z,"R32",B+12,-4);e(z,"W32",B,-4);e(z,"W32",B+12,1);e(z,"BUDGET",0x4220b49,B+4);e(z,"R32",B+4,-2);e(z,"R32",B+8,3);e(z,"W32",B+4,3);e(z,"W32",B+8,-2);
            vv=want(a,3,0xfffffffeL,B+8,B+8,a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3());
        }
        e(z,"R64",SP,RIP);var out=ReverseFullState641.execute(input(B,end,true,FP,r::step),r);checkNormal(out,vv,true);compare(r,expected,z);
    }
    private static final int[] DATA16={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16};
    private static final int[] REVERSE16={16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1};
    private static void sse32() {
        int[] data={1,2,3,4,5,6,7,8};Ram r=ram(data,0x20),expected=ram(data,0x20);seedWords(expected,new int[]{8,7,6,5,4,3,2,1});var a=initialV(B,B+32);List<Event> z=new ArrayList<>();e(z,"BUDGET",0x4220b1e,B);e16(z,"R128",B,w(1,2,3,4));e16(z,"R128",B+16,w(5,6,7,8));e16(z,"W128",B,w(8,7,6,5));e16(z,"W128",B+16,w(4,3,2,1));e(z,"R64",SP,RIP);
        var out=ReverseFullState641.execute(input(B,B+32,false,FP,r::step),r);checkNormal(out,want(a,B+16,0x7ffffffffffffff0L,B+16,B+16,w(8,7,6,5),w(5,6,7,8),w(4,3,2,1),a.xmm3()),false);compare(r,expected,z);
    }
    private static void vector64(boolean avx) {
        Ram r=ram(DATA16,avx?0x20:0),expected=ram(DATA16,avx?0x20:0);seedWords(expected,REVERSE16);var a=initialV(B,B+64);List<Event> z=new ArrayList<>();e(z,"R32",FEATURE,avx?0x20:0);VolatileBits vv;
        if(avx){e(z,"BUDGET",0x4220ad0,B);e32(z,"R256",B,y(1,2,3,4,5,6,7,8));e32(z,"R256",B+32,y(9,10,11,12,13,14,15,16));e32(z,"W256",B,y(16,15,14,13,12,11,10,9));e32(z,"W256",B+32,y(8,7,6,5,4,3,2,1));e(z,"VZEROUPPER",0x4220afc,0);vv=want(a,0,0x7fffffffffffffe0L,B+32,B+32,a.xmm0(),w(13,14,15,16),w(16,15,14,13),w(8,7,6,5));}
        else{e(z,"BUDGET",0x4220b1e,B);e16(z,"R128",B,w(1,2,3,4));e16(z,"R128",B+48,w(13,14,15,16));e16(z,"W128",B,w(16,15,14,13));e16(z,"W128",B+48,w(4,3,2,1));e(z,"BUDGET",0x4220b1e,B+16);e16(z,"R128",B+16,w(5,6,7,8));e16(z,"R128",B+32,w(9,10,11,12));e16(z,"W128",B+16,w(12,11,10,9));e16(z,"W128",B+32,w(8,7,6,5));vv=want(a,B+32,0x7ffffffffffffff0L,B+32,B+32,w(12,11,10,9),w(9,10,11,12),w(8,7,6,5),a.xmm3());}
        e(z,"R64",SP,RIP);var out=ReverseFullState641.execute(input(B,B+64,true,FP,r::step),r);checkNormal(out,vv,true);compare(r,expected,z);
    }
    private static void budget() {
        Ram r=ram(DATA16,0x20),expected=ram(DATA16,0x20);Fault sentinel=new Fault();boolean caught=false;
        try{ReverseFullState641.execute(input(B,B+64,true,FP,(pc,cursor)->{r.events.add(ReverseFixture641.e("BUDGET",pc,cursor));throw sentinel;}),r);}catch(Fault ex){caught=ex==sentinel;}
        check(caught,"exactbudget exception/no artificialNormal");List<Event> z=new ArrayList<>();e(z,"R32",FEATURE,0x20);e(z,"BUDGET",0x4220ad0,B);compare(r,expected,z);
    }
    private static final class FaultMemory implements FullCopy437Api.Memory {
        final Ram m;final int mode;final Fault sentinel;int read16,read32,write32;
        FaultMemory(Ram memory,int selected,Fault exception){m=memory;mode=selected;sentinel=exception;}
        @Override public Bits128 read128(long p){if(++read16==2&&mode==0)throw sentinel;return m.read128(p);}
        @Override public FullCopy437Api.Bits256 read256(long p){if(++read32==2&&mode==1)throw sentinel;return m.read256(p);}
        @Override public void write256(long p,FullCopy437Api.Bits256 v){if(++write32==2&&mode==2)throw sentinel;m.write256(p,v);}
        @Override public int readDword(long p){return m.readDword(p);}
        @Override public long readQword(long p){return m.readQword(p);}
        @Override public void writeDword(long p,int v){m.writeDword(p,v);}
        @Override public void writeQword(long p,long v){m.writeQword(p,v);}
        @Override public void write128(long p,Bits128 v){m.write128(p,v);}
        @Override public int readUnsignedByte(long p){return m.readUnsignedByte(p);}
        @Override public int readUnsignedWord(long p){return m.readUnsignedWord(p);}
        @Override public void writeByte(long p,int v){m.writeByte(p,v);}
        @Override public void writeWord(long p,int v){m.writeWord(p,v);}
        @Override public int lockedXaddDword(long p,int v){return m.lockedXaddDword(p,v);}
        @Override public void write128NonTemporal(long p,Bits128 v){m.write128NonTemporal(p,v);}
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 v){m.write256NonTemporal(p,v);}
        @Override public void sfence(){m.sfence();}
    }
    private static void publicFailure(int mode) {
        Ram m=ram(DATA16,0x20),expected=ram(DATA16,0x20);Fault sentinel=new Fault();FaultMemory memory=new FaultMemory(m,mode,sentinel);long end=B+(mode==0?32:64);Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(IMAGE,SP,initialV(B,end),initialN()));r.r8=B;var a=r.volatileBits();boolean caught=false;VolatileBits vv;List<Event> z=new ArrayList<>();
        try{if(mode==0)ReverseSseStep641.step(r,memory);else ReverseAvxStep641.step(r,memory);}catch(Fault ex){caught=ex==sentinel;}
        check(caught,"exactmemory exception identity");
        if(mode==0){vv=want(a,a.raxBits(),B,B+16,B,w(1,2,3,4),a.xmm1(),w(4,3,2,1),a.xmm3());e16(z,"R128",B,w(1,2,3,4));}
        else if(mode==1){vv=want(a,a.raxBits(),B,B+32,B,a.xmm0(),w(5,6,7,8),a.xmm2(),w(8,7,6,5));e32(z,"R256",B,y(1,2,3,4,5,6,7,8));}
        else{vv=want(a,a.raxBits(),B,B+32,B+32,a.xmm0(),w(13,14,15,16),w(16,15,14,13),w(8,7,6,5));e32(z,"R256",B,y(1,2,3,4,5,6,7,8));e32(z,"R256",B+32,y(9,10,11,12,13,14,15,16));e32(z,"W256",B,y(16,15,14,13,12,11,10,9));seedWords(expected,new int[]{16,15,14,13,12,11,10,9,9,10,11,12,13,14,15,16});}
        check(r.rsp==SP&&r.nonvolatileBits().equals(initialN())&&r.volatileBits().equals(vv),"publicstepfullV/N/SP priorfirstfault state noRET/no rollback");compare(m,expected,z);
    }
    public static int verify(){scalar(0);scalar(1);scalar(2);sse32();vector64(true);vector64(false);budget();publicFailure(0);publicFailure(1);publicFailure(2);return 10;}
    public static void main(String[] args){System.out.println(verify());}
}
