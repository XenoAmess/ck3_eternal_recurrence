package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Fixed owner source oracle for the new composition, not a target-derived simulator. */
public final class ContextFourEmbeddedBoundary583 {
    private ContextFourEmbeddedBoundary583() { }
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
    private static ContextConstructor543Api.CallFrame frame(long site,long target,VolatileBits bits,boolean df) {
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E+8,bits,N);
        return new ContextConstructor543Api.CallFrame(call,entry(bits),df,5,I+site+5);
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
    private static VolatileBits postAt(long ax,long cx) {
        var p=post();return new VolatileBits(ax,cx,p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),p.r11Bits(),
            p.xmm0(),p.xmm1(),p.xmm2(),p.xmm3(),p.xmm4(),p.xmm5());
    }
    private static void whole() {
        Ram ram=new Ram();ram.seed(8,E,RET);ram.seed(4,D+4,0xA1B2C3D4L);
        ram.seed(8,I+0x448D2B0,0xA100);ram.seed(8,I+0x448D2C0,0xA200);
        Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        long[][] cells={
            {8,E+0x10,0xB1},{8,E+0x18,0xB2},{8,E+8,D},{8,E-8,0xB3},{8,E-0x10,0xB4},{8,E-0x18,0xB7},
            {8,E-0x38,D+0x118},{8,E-0x30,0},{8,E-0x28,D},{8,E-0x20,0xB4},
            {8,E-0x48,D},{8,E-0x50,D},{8,E-0x58,0xB8},{8,E-0x70,I+0x88963A},{8,E-0x90,I+0x37272FD},{8,E-0x40,I+0x373ADC2},
            {8,D,0xA1B2C3D400000000L},{8,D+8,0},{4,D+0x10,0xFFFFFFFFL},
            {8,D+0x18,0},{8,D+0x20,0},{8,D+0x28,D+0x30},{8,D+0x30,I+0x448D2A0},{8,D+0xF8,I+0x54DE2E0},
            {8,D+0x100,0},{8,D+0x108,0},{8,D+0x110,I+0x54DE270},{8,D+0x118,I+0x448D1F8},
            {8,D+0x120,I+0x448D268},{8,D+0x128,0},{8,D+0x130,0},{8,D+0x138,I+0x54DE278},
            {4,D+0x140,0},{8,D+0x148,0},{8,D+0x150,0},{8,D+0x158,I+0x54DE270},
            {4,D+0x160,0xFFFFFFFFL},{2,D+0x164,0},{1,D+0x166,0}};
        for(long[] c:cells) Ram.put(expected,(int)c[0],c[1],c[2]);
        int[] sequence={0};GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{throw new AssertionError("all self has no loop");};
        var input=new FullCopy437Api.Input(entry(v(0x11,D,D,0x44,X0)),true,budget);
        NonvolatileBits ctorN=n(D+0x30,0,D+0x18,0xB4,D);
        NonvolatileBits copyN=new NonvolatileBits(D+0x118,0,D+0x128,0xB4,0xB5,0xB6,D+0x118,D+0x118,X6);
        Bits128 header=new Bits128(0xA1B2C3D400000000L,0);
        var actual=ContextConstructorWithKnownFourEmbedded583.execute(input,ram,
            f->{throw new AssertionError("all four parent calls are now known");},
            (m,b,f)->{
                need(m==ram && b==budget,"original Memory/budget");int k=sequence[0]++;need(k<2,"init calls");
                checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                    k==0?0x889620:0x889637,k==0?0xA100:0xA200,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,E-0x68,
                    v(I+0x448D2A0,D+0x30,k==0?0:D+0x18,k==0?8:D+0x20,X0),ctorN,k==0,3);
                return returned(f.call().volatileBits(),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),k!=0);
            },
            (m,b,f)->{throw new AssertionError("vector self no lower call");},
            f->{throw new AssertionError("elements self no lower call");},
            f->{
                int k=sequence[0]++;need(k==2 || k==3,"two copy32 self tail calls");
                checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                    k==2?0x37272F0:0x37272F8,k==2?0x37282B0:0x3727EC0,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x88,
                    k==2?v(0,D+0x148,D+0x148,D+0x20,header):postAt(0x9001,D+0x118),copyN,k==2,5);
                need(ram.raw(8,E-0x90)==f.returnRipBits(),"actual physical push in same RAM");
                return returned(k==2?post():postAt(0x9001,D+0x118),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),k!=2);
            });
        need(sequence[0]==4,"complete nested call sequence");
        need(actual.equals(returned(postAt(D,D+0x118),N,RET,E+8,true)),"full composed NR/DF");
        need(ram.bytes.equals(expected),"complete owned byteRAM final map");
    }
    private static FullCopy437Api.Input wrongTop(GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I+0x70000,0x700000,V,N),false,budget);
    }
    private static void foreignIdentity() {
        Ram ram=new Ram();var f=frame(0x373AD20,0x8895D0,V,true);int[] calls={0};
        var value=returned(V,N,0x1234,0x5678,false);
        var bound=ContextConstructorWithKnownFourEmbedded583.bindCopy32(wrongTop((h,g)->{throw new AssertionError();}),ram,offered->{
            need(offered==f,"foreign frame identity");calls[0]++;return value;
        },offered->{throw new AssertionError();});
        need(bound.invoke(f)==value && calls[0]==1 && ram.touches==0,"foreign result identity no state access");
    }
    private static void changedHome() {
        Ram ram=new Ram();ram.seed(8,E,I+0x373ADC2);ram.seed(4,D+0x28,0xF0000001L);int[] calls={0};
        var bits=v(0x11,D,D,0x44,X0);var f=frame(0x373ADBD,0x3727180,bits,true);
        NonvolatileBits innerN=new NonvolatileBits(0xB1,0xB2,D+0x10,0xB4,0xB5,0xB6,D,D,X6);
        var bound=ContextConstructorWithKnownFourEmbedded583.bindCopy32(wrongTop((h,g)->{throw new AssertionError();}),ram,
            offered->{throw new AssertionError();},inner->{
                int k=calls[0]++;need(k<2,"self still exactly two calls");
                checkFrame(inner.call(),inner.childEntry(),inner.directionFlagSet(),inner.instructionLength(),inner.returnRipBits(),
                    k==0?0x37272F0:0x37272F8,k==0?0x37282B0:0x3727EC0,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x48,
                    v(0xF0000001L,k==0?D+0x30:D,D+0x30,0x44,X0),innerN,k==0,5);
                if(k==0) ram.writeQword(E-8,0xA3);
                return returned(inner.call().volatileBits(),inner.call().nonvolatileBits(),inner.returnRipBits(),inner.call().rspBits(),k!=0);
            });
        try { bound.invoke(f);throw new AssertionError("missing outer guard"); }
        catch(IllegalArgumentException expected) { need(calls[0]==2 && ram.raw(8,E-8)==0xA3,"source fresh RSI not repaired"); }
    }
    private static void budgetMarker() {
        Ram ram=new Ram();ram.seed(8,E,I+0x373ADC2);ram.seed(4,S+0x1C,0);ram.seed(8,S+0x10,0x50000);
        ram.seed(4,D+0x1C,1);ram.seed(8,D+0x10,0x60000);int[] calls={0},steps={0};
        var marker=new UnsupportedOperationException("owned samebudget583");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{
            need(h==0x3727273 && g==0x60000 && calls[0]==1,"source original header/guard/order");steps[0]++;throw marker;
        };
        var bound=ContextConstructorWithKnownFourEmbedded583.bindCopy32(wrongTop(budget),ram,f->{throw new AssertionError();},inner->{
            need(calls[0]++==0,"only prepare call before stop");
            NonvolatileBits offeredN=new NonvolatileBits(0xB1,0xB2,D+0x10,0,0xB5,0x50000,D,S,X6);
            checkFrame(inner.call(),inner.childEntry(),inner.directionFlagSet(),inner.instructionLength(),inner.returnRipBits(),
                0x37271BA,0x889660,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x48,
                v(S+0x10,D+0x10,S,0x44,X0),offeredN,true,5);
            return returned(inner.call().volatileBits(),inner.call().nonvolatileBits(),inner.returnRipBits(),inner.call().rspBits(),false);
        });
        try { bound.invoke(frame(0x373ADBD,0x3727180,V,true));throw new AssertionError("missing original budget stop"); }
        catch(UnsupportedOperationException actual) { need(actual==marker && calls[0]==1 && steps[0]==1,"original marker identity"); }
    }
    public static int verify() { whole();foreignIdentity();changedHome();budgetMarker();return 4; }
    public static void main(String[] args) { System.out.println(verify()); }
}
