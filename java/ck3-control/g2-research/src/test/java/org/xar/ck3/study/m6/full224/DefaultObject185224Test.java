package org.xar.ck3.study.m6.full224;

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

/** Manual finite owned-RAM checks. No Game, native execution, flags or EH claim. */
public final class DefaultObject185224Test {
    private DefaultObject185224Test() { }
    private static final long I=0x140000000L,S=0x100008L;
    private static final long RET=0x1111222233334444L,CHANGED=0x5555666677778888L;
    private static final long HEAP=0x7000000000000011L,IAT=0x7FFF000000000123L;
    private static final long BLOCK=0xF000000000000550L;
    private static final long[] BASE={0x8000000000000101L,0xF000000000000102L,0x30L,
            0x8000000000000108L,0xF000000000000109L,0x800000000000010AL,0xF00000000000010BL,
            0x1000L,0x1001L,0x1002L,0x1003L,0x1004L,0x1005L,0x1006L,0x1007L,0x1008L,0x1009L,0x100AL,0x100BL};
    private static final NonvolatileBits N=new NonvolatileBits(0xB001L,0xB002L,0xB003L,0xB004L,
            0xA00000000000B012L,0xB013L,0xB014L,0xB015L,new Bits128(0x6001L,0x6002L));
    private static final VolatileBits OUT=vol(0x8000000000000201L,0x8000000000000202L,0x8000000000000203L,
            0x8000000000000204L,0x8000000000000205L,0x8000000000000206L,0x8000000000000207L,
            0x8000000000000208L,0x8000000000000209L,0x800000000000020AL,0x800000000000020BL,
            0x800000000000020CL,0x800000000000020DL,0x800000000000020EL,0x800000000000020FL,
            0x8000000000000210L,0x8000000000000211L,0x8000000000000212L,0x8000000000000213L);
    private static int checks,scenes;

    public static void main(String[] args) {
        direct08();directZero();directTail();thunkZero();thunkFree();
        known08(0);known08(1);known08(2);knownFree();knownZero();throwingPort();budgetStops();
        System.out.println("PASS scenes="+scenes+" checks="+checks
                +" represented185Only=true noDFRFLAGSorEH=true Native=false Game=false");
    }

    private static void direct08() {
        Ram m=ram();int[] calls={0};
        Calls port=new Forbidden(){@Override public VolatileBits invoke(Call c){
            calls[0]++;call(c,0x8571D7L,TargetKind.DIRECT_RVA,0x4223B94L,S-0x28L,changed(1,0x30L),N);
            return m.callback(()->{eq(m.readQword(S-0x30L),I+0x8571DCL,"owned outer CALL RET");m.writeQword(S,CHANGED);return OUT;});
        }};
        result(DefaultObject185Wrappers224.fromSlot08(entry(vol(BASE)),m,port),OUT,CHANGED,N);
        eq(calls[0],1,"exact external invoke");
        memory(m,e("producer","W64",S-0x30L,I+0x8571DCL),e("callback","R64",S-0x30L,I+0x8571DCL),
                e("callback","W64",S,CHANGED),e("producer","R64",S,CHANGED));pass("wrapper08-full-call");
    }
    private static void directZero() {
        Ram m=ram();VolatileBits in=changed(2,0);
        result(DefaultObject185Wrappers224.fromSlot10(entry(in),m,null),in,RET,N);
        memory(m,e("producer","R64",S,RET));pass("wrapper10-zero-nullCalls");
    }
    private static void directTail() {
        Ram m=ram();VolatileBits in=changed(2,0xF000000000000440L);int[] calls={0};
        NormalReturn nr=new NormalReturn(OUT,CHANGED,S+8,N);
        Calls port=new Forbidden(){@Override public NormalReturn tail(Tail t){
            calls[0]++;eq(t,new Tail(0x8571C8L,TargetKind.DIRECT_RVA,0x40EC530L,
                    entry(changed(1,0xF000000000000440L,2,0xF000000000000440L))),"actual tail full entry");
            return m.callback(()->{m.writeQword(S,CHANGED);eq(m.readQword(S),CHANGED,"tail owned RET");return nr;});
        }};
        NormalReturn got=DefaultObject185Wrappers224.fromSlot10(entry(in),m,port);
        ok(got==nr,"tail returns actual port result");eq(calls[0],1,"one tail");
        memory(m,e("callback","W64",S,CHANGED),e("callback","R64",S,CHANGED));pass("wrapper10-tail-no-extraRET");
    }
    private static void thunkZero() {
        Ram m=ram();VolatileBits in=changed(1,0);
        result(DefaultFreeThunks185224.execute(entry(in),m,new Forbidden()),changed(0,0,1,0),RET,N);
        memory(m,e("producer","W32",S+0x10L,0),e("producer","R32",S+0x10L,0),e("producer","R64",S,RET));pass("thunk-zero-rcx");
    }
    private static void thunkFree() {
        Ram m=freeRam();VolatileBits in=changed(1,BLOCK);int[] calls={0};
        result(DefaultFreeThunks185224.execute(entry(in),m,freePort(m,calls)),OUT,CHANGED,N);
        eq(calls[0],1,"one actual Free61 IAT invoke");freeMemory(m);pass("thunk-nonzero-actualFree61");
    }
    private static void known08(int corrupt) {
        Ram m=ram();int[] calls={0},steps={0};
        Calls lower=new Forbidden(){@Override public VolatileBits invoke(Call c){
            calls[0]++;
            NonvolatileBits childN=new NonvolatileBits(0x30L,N.rbpBits(),N.rsiBits(),N.rdiBits(),N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
            call(c,0x4223BAEL,TargetKind.DIRECT_RVA,0x42420B8L,S-0x58L,changed(1,0x30L),childN);
            return m.callback(()->{
                eq(m.readQword(S-0x60L),I+0x4223BB3L,"actual nested CALL push");
                if(corrupt==1)m.writeQword(S-0x30L,0xBADL);
                if(corrupt==2)m.writeQword(S-0x38L,0xBADL);
                if(corrupt==0)m.writeQword(S,CHANGED);
                return OUT;
            });
        }};
        GovernmentCrtBoundary185Api.LoopBudget budget=(site,size)->{eq(site,0x4223BAEL,"actual budget site");eq(size,0x30L,"budget size");steps[0]++;};
        if(corrupt==0)result(DefaultObject185Known224.fromSlot08(entry(vol(BASE)),m,lower,budget),OUT,CHANGED,N);
        else {
            try {DefaultObject185Known224.fromSlot08(entry(vol(BASE)),m,lower,budget);throw new AssertionError("corrupt child accepted");}
            catch(IllegalStateException ex){ok(ex.getMessage().contains(corrupt==1?"return RIP":"Nonvolatile"),"actual child return guard");}
        }
        eq(calls[0],1,"one actual lower invoke");eq(steps[0],1,"one actual budget step");
        List<String> expected=new ArrayList<>(List.of(
                e("producer","W64",S-0x30L,I+0x8571DCL),e("producer","W64",S-0x38L,N.rbxBits()),
                e("producer","W64",S-0x60L,I+0x4223BB3L),e("callback","R64",S-0x60L,I+0x4223BB3L)));
        if(corrupt!=0)expected.add(e("callback","W64",corrupt==1?S-0x30L:S-0x38L,0xBADL));
        else expected.add(e("callback","W64",S,CHANGED));
        expected.add(e("producer","R64",S-0x38L,corrupt==2?0xBADL:N.rbxBits()));
        expected.add(e("producer","R64",S-0x30L,corrupt==1?0xBADL:I+0x8571DCL));
        if(corrupt==0)expected.add(e("producer","R64",S,CHANGED));
        eq(m.trace,expected,"actual nested RAM order");pass("known08-actualRetry60-"+corrupt);
    }
    private static void knownFree() {
        Ram m=freeRam();int[] calls={0};
        result(DefaultObject185Known224.fromSlot10(entry(changed(2,BLOCK)),m,freePort(m,calls),null),OUT,CHANGED,N);
        eq(calls[0],1,"known thunk actual lower invoke");freeMemory(m);pass("known10-actualGenericThunkAndFree61");
    }
    private static void knownZero() {
        Ram m=ram();VolatileBits in=changed(2,0);
        result(DefaultObject185Known224.fromSlot10(entry(in),m,null,null),in,RET,N);
        memory(m,e("producer","R64",S,RET));pass("known10-zero-nullLowerBudget");
    }
    private static void throwingPort() {
        Ram m=ram();UnsupportedOperationException marker=new UnsupportedOperationException("owned unsupported machine input");
        Calls port=new Forbidden(){@Override public VolatileBits invoke(Call c){throw marker;}};
        try {DefaultObject185Wrappers224.fromSlot08(entry(vol(BASE)),m,port);throw new AssertionError("port error swallowed");}
        catch(UnsupportedOperationException ex){ok(ex==marker,"same owned exception");}
        memory(m,e("producer","W64",S-0x30L,I+0x8571DCL));pass("opaque-port-throws-no-fakeRET");
    }
    private static void budgetStops() {
        Ram m=ram();UnsupportedOperationException marker=new UnsupportedOperationException("finite budget");
        try {DefaultObject185Known224.fromSlot08(entry(vol(BASE)),m,new Forbidden(),(site,size)->{throw marker;});throw new AssertionError("budget ignored");}
        catch(UnsupportedOperationException ex){ok(ex==marker,"same actual child budget exception");}
        memory(m,e("producer","W64",S-0x30L,I+0x8571DCL),e("producer","W64",S-0x38L,N.rbxBits()));pass("actualRetry60-budget-before-innerCALL");
    }
    private static Calls freePort(Ram m,int[] count) {
        return new Forbidden(){@Override public VolatileBits invoke(Call c){
            count[0]++;call(c,0x424E37AL,TargetKind.INDIRECT_ABSOLUTE,IAT,S-0x28L,changed(0,0,1,HEAP,2,0,3,BLOCK),N);
            return m.callback(()->{eq(m.readQword(S-0x30L),I+0x424E380L,"actual IAT CALL RET");m.writeQword(S,CHANGED);return OUT;});
        }};
    }
    private static void freeMemory(Ram m) {
        memory(m,e("producer","W32",S+0x10L,0),e("producer","R32",S+0x10L,0),
                e("producer","W64",S-8,N.rbxBits()),e("producer","R64",I+0x5C5DE30L,HEAP),
                e("producer","R64",I+0x43DA748L,IAT),e("producer","W64",S-0x30L,I+0x424E380L),
                e("callback","R64",S-0x30L,I+0x424E380L),e("callback","W64",S,CHANGED),
                e("producer","R64",S-8,N.rbxBits()),e("producer","R64",S,CHANGED));
    }
    private static Entry entry(VolatileBits v){return new Entry(I,S,v,N);}
    private static Ram ram(){Ram m=new Ram();m.seed(S,RET,8);return m;}
    private static Ram freeRam(){Ram m=ram();m.seed(I+0x5C5DE30L,HEAP,8);m.seed(I+0x43DA748L,IAT,8);return m;}
    private static VolatileBits changed(long... pairs){long[] a=BASE.clone();for(int i=0;i<pairs.length;i+=2)a[(int)pairs[i]]=pairs[i+1];return vol(a);}
    private static VolatileBits vol(long... a){
        if(a.length!=19)throw new IllegalArgumentException("full19 values required");
        return new VolatileBits(a[0],a[1],a[2],a[3],a[4],a[5],a[6],new Bits128(a[7],a[8]),
                new Bits128(a[9],a[10]),new Bits128(a[11],a[12]),new Bits128(a[13],a[14]),new Bits128(a[15],a[16]),new Bits128(a[17],a[18]));
    }
    private static void call(Call actual,long site,TargetKind kind,long target,long sp,VolatileBits v,NonvolatileBits n){
        eq(actual,new Call(site,kind,target,sp,v,n),"complete represented CALL frame");
    }
    private static void result(NormalReturn actual,VolatileBits v,long rip,NonvolatileBits n){
        eq(actual.volatileBits(),v,"all returned V");eq(actual.nonvolatileBits(),n,"all actual N");
        eq(actual.returnRipBits(),rip,"fresh return RIP");eq(actual.callerRspBits(),S+8,"actual caller SP");
    }
    private static String e(String origin,String op,long address,long value){return origin+":"+op+":"+Long.toUnsignedString(address,16)+":"+Long.toUnsignedString(value,16);}
    private static void memory(Ram m,String... expected){eq(m.trace,List.of(expected),"ordered owned RAM trace");}
    private static void eq(Object a,Object b,String label){checks++;if(!a.equals(b))throw new AssertionError(label+" actual="+a+" expected="+b);}
    private static void eq(long a,long b,String label){checks++;if(a!=b)throw new AssertionError(label+" actual="+Long.toHexString(a)+" expected="+Long.toHexString(b));}
    private static void ok(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
    private static void pass(String id){scenes++;System.out.println("PASS "+id);}
    private static class Forbidden implements Calls {
        @Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected invoke "+c);}
        @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected tail "+t);}
        @Override public long readGsQword58(){throw new AssertionError("unexpected GS read");}
    }
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final List<String> trace=new ArrayList<>();
        private String origin="producer";
        void seed(long a,long value,int width){for(int i=0;i<width;i++)bytes.put(a+i,(byte)(value>>>(8*i)));}
        long load(long a,int width){long value=0;for(int i=0;i<width;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unowned byte "+Long.toHexString(a+i));value|=(long)Byte.toUnsignedInt(b)<<(8*i);}return value;}
        <T>T callback(Supplier<T> action){String previous=origin;origin="callback";try{return action.get();}finally{origin=previous;}}
        @Override public int readDword(long a){long v=load(a,4);trace.add(e(origin,"R32",a,v));return(int)v;}
        @Override public long readQword(long a){long v=load(a,8);trace.add(e(origin,"R64",a,v));return v;}
        @Override public int readUnsignedByte(long a){long v=load(a,1);trace.add(e(origin,"R8",a,v));return(int)v;}
        @Override public void writeDword(long a,int v){seed(a,Integer.toUnsignedLong(v),4);trace.add(e(origin,"W32",a,Integer.toUnsignedLong(v)));}
        @Override public void writeQword(long a,long v){seed(a,v,8);trace.add(e(origin,"W64",a,v));}
        @Override public void writeByte(long a,int v){seed(a,v&0xFFL,1);trace.add(e(origin,"W8",a,v&0xFFL));}
        @Override public int lockedXaddDword(long a,int add){throw new AssertionError("unexpected locked XADD");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpected native-width memory access");}
        @Override public void write128(long a,Bits128 v){throw new AssertionError("unexpected native-width memory access");}
    }
}
