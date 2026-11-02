package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Fixed owner source oracle for the new composition, not a target-derived simulator. */
public final class ContextInitElementsVectorBoundary580 {
    private ContextInitElementsVectorBoundary580() { }
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
    private static void whole() {
        Ram ram=new Ram();ram.seed(8,E,RET);ram.seed(8,S,SRC.lowBits());ram.seed(8,S+8,SRC.highBits());
        ram.seed(4,S+0x10,0xAABBCCDDL);ram.seed(8,S+0x100,0x50000);ram.seed(4,S+0x10C,0);
        ram.seed(8,S+0x18,0x60000);ram.seed(4,S+0x24,0);
        ram.seed(8,I+0x448D2B0,0xA100);ram.seed(8,I+0x448D2C0,0xA200);
        Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        // Final writes independently collected from the fixed original instruction path.
        long[][] cells={
            {8,E+0x10,0xB1},{8,E+0x18,0xB2},{8,E+8,D},{8,E-8,0xB3},{8,E-0x10,0xB4},{8,E-0x18,0xB7},
            {8,E-0x38,D+0x118},{8,E-0x30,0},{8,E-0x28,0xB4},{8,E-0x20,0xB4},
            {8,E-0x48,S},{8,E-0x50,D},{8,E-0x58,0xB8},{8,E-0x70,I+0x88963A},{8,E-0x90,I+0x37282E6},{8,E-0x40,I+0x373ADC2},
            {8,D,SRC.lowBits()},{8,D+8,SRC.highBits()},{4,D+0x10,0xAABBCCDDL},
            {8,D+0x18,0},{8,D+0x20,0},{8,D+0x28,D+0x30},{8,D+0x30,I+0x448D2A0},{8,D+0xF8,I+0x54DE2E0},
            {8,D+0x100,0},{8,D+0x108,0},{8,D+0x110,I+0x54DE270},{8,D+0x118,I+0x448D1F8},
            {8,D+0x120,I+0x448D268},{8,D+0x128,0},{8,D+0x130,0},{8,D+0x138,I+0x54DE278},
            {4,D+0x140,0},{8,D+0x148,0},{8,D+0x150,0},{8,D+0x158,I+0x54DE270},
            {4,D+0x160,0xFFFFFFFFL},{2,D+0x164,0},{1,D+0x166,0}};
        for(long[] c:cells) Ram.put(expected,(int)c[0],c[1],c[2]);
        int[] sequence={0};
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{throw new AssertionError("unexpected budget");};
        FullCopy437Api.Input input=new FullCopy437Api.Input(entry(V),true,budget);
        NonvolatileBits ctorN=n(D+0x30,0,D+0x18,0xB4,D);
        NonvolatileBits elementN=n(0,0x50000,D+0x100,0xB4,D);
        NonvolatileBits parentN=n(D+0x118,0,S,0xB4,D);
        VolatileBits finalV=new VolatileBits(D,0x9002,0x9003,0x9004,0x9005,0x9006,0x9007,
            new Bits128(0x9101,0x9102),new Bits128(0x9201,0x9202),new Bits128(0x9301,0x9302),
            new Bits128(0x9401,0x9402),new Bits128(0x9501,0x9502),new Bits128(0x9601,0x9602));
        FullCopy437Api.CallResult actual=ContextConstructorWithKnownInitElementsVector580.execute(input,ram,
            f->{
                need(sequence[0]++==3,"foreign sequence");
                checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                    0x373ADBD,0x3727180,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x38,
                    v(D+0x18,D+0x118,S+0x118,D+0x20,SRC),parentN,false,5);
                VolatileBits offered=new VolatileBits(0x9001,finalV.rcxBits(),finalV.rdxBits(),finalV.r8Bits(),finalV.r9Bits(),finalV.r10Bits(),finalV.r11Bits(),
                    finalV.xmm0(),finalV.xmm1(),finalV.xmm2(),finalV.xmm3(),finalV.xmm4(),finalV.xmm5());
                return returned(offered,f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),true);
            },
            (m,b,f)->{
                need(m==ram && b==budget,"embedded memory/budget identity");int index=sequence[0]++;
                need(index<2,"embedded count");long site=index==0?0x889620:0x889637;
                checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                    site,index==0?0xA100:0xA200,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,E-0x68,
                    v(I+0x448D2A0,D+0x30,index==0?0:D+0x18,index==0?8:D+0x20,X0),ctorN,index==0,3);
                return returned(f.call().volatileBits(),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),index!=0);
            },
            (m,b,f)->{throw new AssertionError("zero vector has no opaque call");},
            f->{
                need(sequence[0]++==2,"elements sequence");
                checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                    0x37282E1,0x889780,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,E-0x88,
                    v(0xAABBCCDDL,D+0x100,S+0x100,D+0x20,SRC),elementN,true,5);
                return returned(f.call().volatileBits(),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),false);
            });
        need(sequence[0]==4,"all four opaque calls");
        need(actual.equals(returned(finalV,N,RET,E+8,true)),"complete final result");
        need(ram.bytes.equals(expected),"whole strict RAM final bytes");
    }
    private static void foreignIdentity() {
        Ram ram=new Ram();var f=frame(0x373ADBD,0x3727180,V,true);
        var result=returned(V,N,0x1234,0x5678,false);int[] calls={0};
        var input=new FullCopy437Api.Input(entry(V),false,(h,g)->{throw new AssertionError();});
        var binding=ContextConstructorWithKnownInitElementsVector580.bindElements(input,ram,offered->{
            need(offered==f,"foreign frame identity");calls[0]++;return result;
        },offered->{throw new AssertionError();});
        need(binding.invoke(f)==result && calls[0]==1 && ram.touches==0,"foreign raw result identity");
    }
    private static Ram boundaryRam(int oldCount) {
        Ram ram=new Ram();ram.seed(8,E,I+0x373ADA6);ram.seed(4,S+0xC,0);ram.seed(8,S,0x50000);
        ram.seed(4,D+0xC,oldCount);ram.seed(8,D,0x60000);return ram;
    }
    private static void changedHome() {
        Ram ram=boundaryRam(0);int[] calls={0};var input=new FullCopy437Api.Input(entry(V),true,(h,g)->{throw new AssertionError();});
        var binding=ContextConstructorWithKnownInitElementsVector580.bindElements(input,ram,f->{throw new AssertionError();},f->{
            need(f.call().callSiteRva()==0x37282E1,"home callback");calls[0]++;
            ram.writeQword(E+8,0xDEAD);
            return returned(f.call().volatileBits(),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),false);
        });
        try { binding.invoke(frame(0x373ADA1,0x37282B0,V,true));throw new AssertionError("missing outer NR guard"); }
        catch(IllegalArgumentException expected) { need(calls[0]==1 && ram.raw(8,E+8)==0xDEAD,"fresh saved home"); }
    }
    private static void budgetMarker() {
        Ram ram=boundaryRam(1);int[] calls={0},steps={0};var marker=new UnsupportedOperationException("owned marker580");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{
            need(h==0x3728390 && g==0x60000 && calls[0]==1,"actual budget header/guard/order");steps[0]++;throw marker;
        };
        var input=new FullCopy437Api.Input(entry(V),true,budget);
        var binding=ContextConstructorWithKnownInitElementsVector580.bindElements(input,ram,f->{throw new AssertionError();},f->{
            need(f.call().callSiteRva()==0x37282E1,"budget callback");calls[0]++;
            return returned(f.call().volatileBits(),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),false);
        });
        try { binding.invoke(frame(0x373ADA1,0x37282B0,V,true));throw new AssertionError("missing budget stop"); }
        catch(UnsupportedOperationException actual) { need(actual==marker && calls[0]==1 && steps[0]==1,"original budget exception identity"); }
    }
    public static int verify() { whole();foreignIdentity();changedHome();budgetMarker();return 4; }
    public static void main(String[] args) { System.out.println(verify()); }
}
