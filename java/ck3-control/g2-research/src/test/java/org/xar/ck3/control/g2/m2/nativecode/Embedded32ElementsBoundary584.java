package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Fixed owner source oracle for the new composition, not a target-derived simulator. */
public final class Embedded32ElementsBoundary584 {
    private Embedded32ElementsBoundary584() { }
    private static final long I=0x140000000L,E=0x8000L,D=0x10000L,S=0x20000L;
    private static final Bits128 X0=new Bits128(0x101,0x102),X1=new Bits128(0x201,0x202),
        X2=new Bits128(0x301,0x302),X3=new Bits128(0x401,0x402),X4=new Bits128(0x501,0x502),
        X5=new Bits128(0x601,0x602),X6=new Bits128(0x701,0x702),SRC=new Bits128(0x12345678,0x87654321);
    private static final NonvolatileBits N=new NonvolatileBits(0xB1,0xB2,0xB3,0xB4,0xB5,0xB6,0xB7,0xB8,X6);
    private static final long RET=0x7172737475767778L;
    private static VolatileBits v(long a,long c,long d,long r8,Bits128 x0) {
        return new VolatileBits(a,c,d,r8,0x55,0x66,0x77,x0,X1,X2,X3,X4,X5);
    }
    private static final VolatileBits V=v(0x11,D,S,0x44,X0);
    private static NonvolatileBits n(long b,long p,long s,long d,long r14) {
        return new NonvolatileBits(b,p,s,d,0xB5,0xB6,r14,0xB8,X6);
    }
    private static void need(boolean value,String text) { if(!value) throw new AssertionError(text); }
    private static GovernmentCrtBoundary185Api.Entry entry(VolatileBits bits) {
        return new GovernmentCrtBoundary185Api.Entry(I,E,bits,N);
    }
    private static FullCopy437Api.CallResult returned(VolatileBits bits,NonvolatileBits saved,long rip,long sp,boolean df) {
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(bits,rip,sp,saved),df);
    }
    private static Embedded32Copy581Api.CallFrame frame(long site,long target,VolatileBits bits,boolean df) {
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E+8,bits,N);
        return new Embedded32Copy581Api.CallFrame(call,entry(bits),df,5,I+site+5);
    }
    private static void checkFrame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
            boolean df,int len,long ret,long site,long target,GovernmentCrtBoundary185Api.TargetKind kind,
            long sp,VolatileBits expectedV,NonvolatileBits expectedN,boolean expectedDF,int expectedLen) {
        need(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,sp,expectedV,expectedN)),"complete call");
        need(child.equals(new GovernmentCrtBoundary185Api.Entry(I,sp-8,expectedV,expectedN)),"complete child entry");
        need(df==expectedDF && len==expectedLen && ret==I+site+expectedLen,"DF/length/continuation");
    }
    private static final class Ram implements FullCopy437Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();
        int touches;
        void seed(int w,long a,long value) { put(bytes,w,a,value); }
        static void put(Map<Long,Byte> map,int w,long a,long value) {
            for(int j=0;j<w;j++) map.put(a+j,(byte)(value>>>(8*j)));
        }
        long raw(int w,long a) {
            long value=0;
            for(int j=0;j<w;j++) {
                Byte b=bytes.get(a+j);if(b==null) throw new AssertionError("unseeded "+Long.toHexString(a+j));
                value|=Byte.toUnsignedLong(b)<<(j*8);
            }
            return value;
        }
        void store(int w,long a,long value) {
            touches++;
            if(!((a>=E-0x100 && a+w<=E+0x30)||(a>=D && a+w<=D+0x200))) throw new AssertionError("write bounds");
            seed(w,a,value);
        }
        public int readDword(long a) { touches++;return (int)raw(4,a); }
        public long readQword(long a) { touches++;return raw(8,a); }
        public Bits128 read128(long a) { touches++;return new Bits128(raw(8,a),raw(8,a+8)); }
        public void writeDword(long a,int x) { store(4,a,Integer.toUnsignedLong(x)); }
        public void writeQword(long a,long x) { store(8,a,x); }
        public void writeWord(long a,int x) { store(2,a,x&0xFFFFL); }
        public void writeByte(long a,int x) { store(1,a,x&0xFFL); }
        public void write128(long a,Bits128 x) { store(8,a,x.lowBits());store(8,a+8,x.highBits()); }
        public int readUnsignedByte(long a) { throw new UnsupportedOperationException(); }
        public int readUnsignedWord(long a) { throw new UnsupportedOperationException(); }
        public int lockedXaddDword(long a,int x) { throw new UnsupportedOperationException(); }
        public void write128NonTemporal(long a,Bits128 x) { throw new UnsupportedOperationException(); }
        public FullCopy437Api.Bits256 read256(long a) { throw new UnsupportedOperationException(); }
        public void write256(long a,FullCopy437Api.Bits256 x) { throw new UnsupportedOperationException(); }
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 x) { throw new UnsupportedOperationException(); }
        public void sfence() { throw new UnsupportedOperationException(); }
    }
    private static VolatileBits post() {
        return new VolatileBits(0x9001,0x9002,0x9003,0x9004,0x9005,0x9006,0x9007,
            new Bits128(0x9101,0x9102),new Bits128(0x9201,0x9202),new Bits128(0x9301,0x9302),
            new Bits128(0x9401,0x9402),new Bits128(0x9501,0x9502),new Bits128(0x9601,0x9602));
    }
    private static void whole() {
        Ram ram=new Ram();ram.seed(8,E,RET);ram.seed(4,D+0x28,0xF0000001L);
        Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        long[][] cells={{8,E-8,0xB3},{8,E-0x10,0xB7},{8,E-0x18,0xB8},
            {8,E-0x50,I+0x37272FD},{8,E-0x48,0xB1},{8,E-0x40,0xB2},
            {8,E-0x38,D+0x10},{8,E-0x30,0xB4},{8,E-0x58,0xB5},
            {8,E-0x60,D},{8,E-0x68,D}};
        for(long[] c:cells) Ram.put(expected,(int)c[0],c[1],c[2]);
        int[] calls={0};GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{throw new AssertionError("self no budget");};
        var input=new FullCopy437Api.Input(entry(v(0x11,D,D,0x44,X0)),true,budget);
        var actual=Embedded32WithKnownElements584.execute(input,ram,f->{
            need(calls[0]++==0,"only foreign tailF8 remains");
            NonvolatileBits offeredN=new NonvolatileBits(0xB1,0xB2,D+0x10,0xB4,0xB5,0xB6,D,D,X6);
            checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                0x37272F8,0x3727EC0,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x48,
                v(D+0x30,D,D+0x30,0x44,X0),offeredN,true,5);
            need(ram.raw(8,E-0x50)==f.returnRipBits(),"actual parent push");
            return returned(post(),offeredN,f.returnRipBits(),f.call().rspBits(),false);
        },f->{throw new AssertionError("nested322self has no opaque lower call");});
        var p=post();var out=new VolatileBits(D,p.rcxBits(),p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),p.r11Bits(),
            p.xmm0(),p.xmm1(),p.xmm2(),p.xmm3(),p.xmm4(),p.xmm5());
        need(actual.equals(returned(out,N,RET,E+8,false)),"full actual394->actual322 NR/DF");
        need(calls[0]==1 && ram.bytes.equals(expected),"whole complete owned byteRAM");
    }
    private static FullCopy437Api.Input wrongTop(GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I+0x70000,0x700000,V,N),false,budget);
    }
    private static void foreignIdentity() {
        Ram ram=new Ram();var f=frame(0x37272F8,0x3727EC0,V,true);int[] count={0};
        var value=returned(V,N,0x1234,0x5678,false);
        var bound=Embedded32WithKnownElements584.bindElements(wrongTop((h,g)->{throw new AssertionError();}),ram,offered->{
            need(offered==f,"same foreign frame");count[0]++;return value;
        },offered->{throw new AssertionError();});
        need(bound.invoke(f)==value && count[0]==1 && ram.touches==0,"foreign identity without RAM");
    }
    private static void changedHome() {
        Ram ram=new Ram();ram.seed(8,E,I+0x37272F5);ram.seed(4,S+0xC,0xFFFFFFFFL);ram.seed(8,S,0x50000);
        ram.seed(4,D+0xC,0xFFFFFFFFL);ram.seed(8,D,0x60000);int[] count={0};
        var bound=Embedded32WithKnownElements584.bindElements(wrongTop((h,g)->{throw new AssertionError();}),ram,
            offered->{throw new AssertionError();},inner->{
                need(count[0]++==0,"one prepare only");
                NonvolatileBits offeredN=new NonvolatileBits(-1,0x50000,D,0xB4,0xB5,0xB6,0xB7,0xB8,X6);
                checkFrame(inner.call(),inner.childEntry(),inner.directionFlagSet(),inner.instructionLength(),inner.returnRipBits(),
                    0x37282E1,0x889780,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x48,V,offeredN,true,5);
                ram.writeQword(E+8,0xA3);
                return returned(inner.call().volatileBits(),inner.call().nonvolatileBits(),inner.returnRipBits(),inner.call().rspBits(),false);
            });
        try { bound.invoke(frame(0x37272F0,0x37282B0,V,true));throw new AssertionError("missing outer581 NRguard"); }
        catch(IllegalArgumentException expected) { need(count[0]==1 && ram.raw(8,E+8)==0xA3,"freshRBX not repaired"); }
    }
    private static void budgetMarker() {
        Ram ram=new Ram();ram.seed(8,E,I+0x37272F5);ram.seed(4,S+0xC,0);ram.seed(8,S,0x50000);
        ram.seed(4,D+0xC,1);ram.seed(8,D,0x60000);int[] calls={0},steps={0};
        var marker=new UnsupportedOperationException("original-budget584");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{
            need(h==0x3728390 && g==0x60000 && calls[0]==1,"source budget header/guard/order");steps[0]++;throw marker;
        };
        var bound=Embedded32WithKnownElements584.bindElements(wrongTop(budget),ram,f->{throw new AssertionError();},inner->{
            need(calls[0]++==0,"only prepare before budget");
            NonvolatileBits offeredN=new NonvolatileBits(0,0x50000,D,0xB4,0xB5,0xB6,0xB7,0xB8,X6);
            checkFrame(inner.call(),inner.childEntry(),inner.directionFlagSet(),inner.instructionLength(),inner.returnRipBits(),
                0x37282E1,0x889780,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x48,V,offeredN,true,5);
            return returned(inner.call().volatileBits(),inner.call().nonvolatileBits(),inner.returnRipBits(),inner.call().rspBits(),false);
        });
        try { bound.invoke(frame(0x37272F0,0x37282B0,V,true));throw new AssertionError("missing marker"); }
        catch(UnsupportedOperationException actual) { need(actual==marker && calls[0]==1 && steps[0]==1,"original marker identity"); }
    }
    public static int verify() { whole();foreignIdentity();changedHome();budgetMarker();return 4; }
    public static void main(String[] args) { System.out.println(verify()); }
}
