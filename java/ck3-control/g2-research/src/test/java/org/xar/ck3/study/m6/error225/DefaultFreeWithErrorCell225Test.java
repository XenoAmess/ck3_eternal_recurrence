package org.xar.ck3.study.m6.error225;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New225 same-RAM composition checks, not old204/224 suites or Native execution. */
public final class DefaultFreeWithErrorCell225Test {
    private DefaultFreeWithErrorCell225Test() { }
    private static final long I=0x140000000L,S=0x200008L,RET=0x1111222233334444L,CHANGED=0x5555666677778888L;
    private static final long BLOCK=0x8888000000000055L,HEAP=0x7777000000000033L;
    private static final long T1=0x7FFF001122330001L,T2=0x7FFF001122330002L,LATE=0x7FFF00112233F002L;
    private static final long[] BASE={0x8000000000001101L,0xF000000000001102L,BLOCK,
            0x8000000000001108L,0xF000000000001109L,0x800000000000110AL,0xF00000000000110BL,
            0x1100L,0x1101L,0x1102L,0x1103L,0x1104L,0x1105L,0x1106L,0x1107L,0x1108L,0x1109L,0x110AL,0x110BL};
    private static final NonvolatileBits N=new NonvolatileBits(0x1234567887654321L,0xB002L,0xB003L,0xB004L,
            0xA00000000000B012L,0xB013L,0xB014L,0xB015L,new Bits128(0x6001L,0x6002L));
    private static int checks,scenes;
    public static void main(String[] args) {
        scenario("nonnull-object",0x7000000000000200L,0);
        scenario("zero-object-fallback",0,0);
        scenario("high64-nonzero-low32zero",0x100000000L,0);
        scenario("corrupt-child-RET",0x7000000000000200L,1);
        scenario("deep-port-throws",0x7000000000000200L,2);
        zero();
        System.out.println("PASS scenes="+scenes+" checks="+checks
                +" normalWhole=4 guardedPrefix=1 thrownPrefix=1 represented185Only=true Native=false Game=false");
    }
    private static void scenario(String id,long object,int mode) {
        Ram m=new Ram();m.seed(S,RET,8);m.seed(I+0x5C5DE30L,HEAP,8);m.seed(I+0x43DA748L,T1,8);m.seed(I+0x43DA738L,T2,8);
        long cell=object==0?I+0x542F210L:object+0x20L;
        long[] first=vector(0xA000000000000000L),second=vector(0xB000000000000000L),last=vector(0xC000000000000000L),mapped=vector(0xD000000000000000L);
        second[0]=object;last[0]=0xC000000080000001L;mapped[0]=0xD0000000FEDCBA98L;
        int[] count={0};UnsupportedOperationException marker=new UnsupportedOperationException("opaque FC74 lacks unrepresented input");
        Calls lower=new Calls(){
            @Override public VolatileBits invoke(Call c){
                count[0]++;
                if(count[0]==1){
                    long[] expected=BASE.clone();expected[0]=0;expected[1]=HEAP;expected[2]=0;expected[3]=BLOCK;
                    call(c,0x424E37AL,TargetKind.INDIRECT_ABSOLUTE,T1,S-0x28L,vol(expected),N);
                    return m.callback(()->{eq(m.readQword(S-0x30L),I+0x424E380L,"first IAT ownedRET");return vol(first);});
                }
                if(count[0]==2){
                    call(c,0x423B190L,TargetKind.DIRECT_RVA,0x424FC74L,S-0x58L,vol(first),N);
                    if(mode==2)throw marker;
                    return m.callback(()->{
                        eq(m.readQword(S-0x60L),I+0x423B195L,"actual deep ownedRET");
                        if(mode==1)m.writeQword(S-0x30L,0xBADL);
                        else {m.writeQword(S,CHANGED);m.writeQword(I+0x43DA738L,LATE);}
                        return vol(second);
                    });
                }
                NonvolatileBits temporary=nWithRbx(cell);
                if(count[0]==3){
                    long[] expected=second.clone();expected[0]=cell;
                    call(c,0x424E38CL,TargetKind.INDIRECT_ABSOLUTE,LATE,S-0x28L,vol(expected),temporary);
                    return m.callback(()->{eq(m.readQword(S-0x30L),I+0x424E392L,"fresh lastError ownedRET");return vol(last);});
                }
                if(count[0]==4){
                    long[] expected=last.clone();expected[1]=0x80000001L;
                    call(c,0x424E394L,TargetKind.DIRECT_RVA,0x423B0D4L,S-0x28L,vol(expected),temporary);
                    return m.callback(()->{eq(m.readQword(S-0x30L),I+0x424E399L,"map ownedRET");return vol(mapped);});
                }
                throw new AssertionError("extra lower invoke "+c);
            }
            @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected external tail "+t);}
            @Override public long readGsQword58(){throw new AssertionError("unexpected GS");}
        };
        Entry entry=new Entry(I,S,vol(BASE),N);
        if(mode==0){
            NormalReturn nr=DefaultFreeWithErrorCell225.execute(entry,m,lower);
            eq(nr.volatileBits(),vol(mapped),"full mappedV including high RAX and all XMM");eq(nr.nonvolatileBits(),N,"fresh restored originalN");
            eq(nr.returnRipBits(),CHANGED,"fresh outerRET");eq(nr.callerRspBits(),S+8,"actual finalSP");
            eq(m.load(cell,4),0xFEDCBA98L,"only low mapped DWORD stored");eq(count[0],4,"exact 4 external lower calls");
        } else if(mode==1){
            try {DefaultFreeWithErrorCell225.execute(entry,m,lower);throw new AssertionError("corrupt Error204RET accepted");}
            catch(IllegalStateException ex){eq(ex.getMessage(),"returnRip mismatch","existing204actualguard");}
            eq(count[0],2,"no lastError/map after childguard");
        } else {
            try {DefaultFreeWithErrorCell225.execute(entry,m,lower);throw new AssertionError("deep exception swallowed");}
            catch(UnsupportedOperationException ex){ok(ex==marker,"identical ownedexception propagated");}
            eq(count[0],2,"no followup after deepthrow");
        }
        List<String> expected=new ArrayList<>(List.of(e("P","W32",S+0x10L,0),e("P","R32",S+0x10L,0),
                e("P","W64",S-8,N.rbxBits()),e("P","R64",I+0x5C5DE30L,HEAP),e("P","R64",I+0x43DA748L,T1),
                e("P","W64",S-0x30L,I+0x424E380L),e("C","R64",S-0x30L,I+0x424E380L),
                e("P","W64",S-0x30L,I+0x424E389L),e("P","W64",S-0x60L,I+0x423B195L)));
        if(mode!=2)expected.add(e("C","R64",S-0x60L,I+0x423B195L));
        if(mode==0)expected.addAll(List.of(e("C","W64",S,CHANGED),e("C","W64",I+0x43DA738L,LATE),
                e("P","R64",S-0x30L,I+0x424E389L),e("P","R64",I+0x43DA738L,LATE),
                e("P","W64",S-0x30L,I+0x424E392L),e("C","R64",S-0x30L,I+0x424E392L),
                e("P","W64",S-0x30L,I+0x424E399L),e("C","R64",S-0x30L,I+0x424E399L),
                e("P","W32",cell,0xFEDCBA98L),e("P","R64",S-8,N.rbxBits()),e("P","R64",S,CHANGED)));
        else if(mode==1)expected.addAll(List.of(e("C","W64",S-0x30L,0xBADL),e("P","R64",S-0x30L,0xBADL)));
        eq(m.trace,expected,"complete ordered actual source and callbackRAM");
        scenes++;System.out.println("PASS "+id);
    }
    private static void zero(){
        Ram m=new Ram();m.seed(S,RET,8);long[] in=BASE.clone();in[2]=0;
        NormalReturn nr=DefaultFreeWithErrorCell225.execute(new Entry(I,S,vol(in),N),m,null);
        eq(nr,new NormalReturn(vol(in),RET,S+8,N),"newconsumer preserves zeroRDX nullLower branch");
        eq(m.trace,List.of(e("P","R64",S,RET)),"zero route only owns RET");
        scenes++;System.out.println("PASS zeroRDX-nullLower");
    }
    private static NonvolatileBits nWithRbx(long value){return new NonvolatileBits(value,N.rbpBits(),N.rsiBits(),N.rdiBits(),N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());}
    private static long[] vector(long base){long[] a=new long[19];for(int i=0;i<a.length;i++)a[i]=base+i;return a;}
    private static VolatileBits vol(long... a){
        if(a.length!=19)throw new IllegalArgumentException("19 explicit values required");
        return new VolatileBits(a[0],a[1],a[2],a[3],a[4],a[5],a[6],new Bits128(a[7],a[8]),new Bits128(a[9],a[10]),
                new Bits128(a[11],a[12]),new Bits128(a[13],a[14]),new Bits128(a[15],a[16]),new Bits128(a[17],a[18]));
    }
    private static void call(Call got,long site,TargetKind kind,long target,long sp,VolatileBits v,NonvolatileBits n){eq(got,new Call(site,kind,target,sp,v,n),"complete actual lower frame");}
    private static String e(String who,String op,long a,long value){return who+":"+op+":"+Long.toUnsignedString(a,16)+":"+Long.toUnsignedString(value,16);}
    private static void eq(Object a,Object b,String label){checks++;if(!a.equals(b))throw new AssertionError(label+" actual="+a+" expected="+b);}
    private static void eq(long a,long b,String label){checks++;if(a!=b)throw new AssertionError(label+" actual="+Long.toHexString(a)+" expected="+Long.toHexString(b));}
    private static void ok(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();private final List<String> trace=new ArrayList<>();private String who="P";
        void seed(long a,long value,int width){for(int i=0;i<width;i++)bytes.put(a+i,(byte)(value>>>(8*i)));}
        long load(long a,int width){long value=0;for(int i=0;i<width;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unowned RAM "+Long.toHexString(a+i));value|=(long)Byte.toUnsignedInt(b)<<(8*i);}return value;}
        <T>T callback(Supplier<T> f){String previous=who;who="C";try{return f.get();}finally{who=previous;}}
        @Override public int readDword(long a){long v=load(a,4);trace.add(e(who,"R32",a,v));return(int)v;}
        @Override public long readQword(long a){long v=load(a,8);trace.add(e(who,"R64",a,v));return v;}
        @Override public int readUnsignedByte(long a){long v=load(a,1);trace.add(e(who,"R8",a,v));return(int)v;}
        @Override public void writeDword(long a,int v){seed(a,Integer.toUnsignedLong(v),4);trace.add(e(who,"W32",a,Integer.toUnsignedLong(v)));}
        @Override public void writeQword(long a,long v){seed(a,v,8);trace.add(e(who,"W64",a,v));}
        @Override public void writeByte(long a,int v){seed(a,v&0xFFL,1);trace.add(e(who,"W8",a,v&0xFFL));}
        @Override public int lockedXaddDword(long a,int v){throw new AssertionError("unexpected LOCK");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpected memory vector access");}
        @Override public void write128(long a,Bits128 v){throw new AssertionError("unexpected memory vector access");}
    }
}
