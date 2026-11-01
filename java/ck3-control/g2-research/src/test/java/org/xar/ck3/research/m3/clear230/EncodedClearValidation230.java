package org.xar.ck3.research.m3.clear230;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class EncodedClearValidation230 {
    private EncodedClearValidation230() { }
    @FunctionalInterface private interface Indirect {
        void call(Fixture memory,int ordinal,long target,long liveRax,EncodedClear230Api.IndirectArguments arguments);
    }
    @FunctionalInterface private interface Free {
        void call(Fixture memory,long rcx);
    }
    private record Step(String kind,long[] values,EncodedClear230Api.IndirectArguments arguments) { }
    private static final class Fixture implements NativeTaskMemory, EncodedClear230Api.Ports {
        private final Map<Long,Integer> bytes=new HashMap<>();
        private final List<Step> expected=new ArrayList<>();
        private final Indirect indirect;
        private final Free free;
        private int cursor;
        private int reads;
        private int writes;
        private int opaqueMemory;
        private int indirectCalls;
        private int freeCalls;
        private boolean opaque;
        Fixture() { this((m,n,t,r,a)->{},(m,r)->{}); }
        Fixture(Indirect indirect,Free free) { this.indirect=indirect;this.free=free; }
        void seed64(long address,long value) {
            for(int i=0;i<8;i++) bytes.put(address+i,(int)(value >>> (8*i)) & 255);
        }
        long peek64(long address) {
            long value=0;
            for(int i=0;i<8;i++) {
                Integer b=bytes.get(address+i);
                if(b==null) throw new AssertionError("unseeded byte "+Long.toHexString(address+i));
                value |= ((long)b) << (8*i);
            }
            return value;
        }
        void expect(String kind,long... values) { expected.add(new Step(kind,values.clone(),null)); }
        void expectIat(long site,long target,long liveRax,EncodedClear230Api.IndirectArguments args) {
            expected.add(new Step("IAT",new long[]{site,target,liveRax},args));
        }
        void expectFree(long site,long rcx) { expect("FREE",site,rcx); }
        private void take(String kind,EncodedClear230Api.IndirectArguments args,long... values) {
            if(cursor==expected.size()) throw new AssertionError("extra "+kind+Arrays.toString(values));
            Step wanted=expected.get(cursor++);
            if(!wanted.kind().equals(kind) || !Arrays.equals(wanted.values(),values) || !Objects.equals(wanted.arguments(),args))
                throw new AssertionError("step "+(cursor-1)+" wanted "+wanted.kind()+Arrays.toString(wanted.values())+"/"+wanted.arguments()+" got "+kind+Arrays.toString(values)+"/"+args);
        }
        @Override public long readPointer(long address) {
            long value=peek64(address);take(opaque?"C.R64":"P.R64",null,address,value);
            if(opaque) opaqueMemory++;else reads++;return value;
        }
        @Override public void writeInt64(long address,long value) {
            take(opaque?"C.W64":"P.W64",null,address,value);
            if(opaque) opaqueMemory++;else writes++;seed64(address,value);
        }
        @Override public int readInt32(long address) { throw new AssertionError("unexpected R32"); }
        @Override public void writeInt32(long address,int value) { throw new AssertionError("unexpected W32"); }
        @Override public void call43dbba8(NativeTaskMemory memory,long site,long target,long liveRax,EncodedClear230Api.IndirectArguments args) {
            if(memory!=this || opaque) throw new AssertionError("indirect identity/reentry");
            take("IAT",args,site,target,liveRax);indirectCalls++;opaque=true;
            try { indirect.call(this,indirectCalls,target,liveRax,args); }
            finally { opaque=false; }
        }
        @Override public void call424e364(NativeTaskMemory memory,long site,long rcx) {
            if(memory!=this || opaque) throw new AssertionError("free identity/reentry");
            take("FREE",null,site,rcx);freeCalls++;opaque=true;
            try { free.call(this,rcx); }
            finally { opaque=false; }
        }
        void done(int expectedReads,int expectedWrites,int expectedOpaque,int expectedIat,int expectedFree) {
            if(cursor!=expected.size()) throw new AssertionError("not exhausted "+cursor+"/"+expected.size());
            equal(expectedReads,reads,"target R64");equal(expectedWrites,writes,"target W64");
            equal(expectedOpaque,opaqueMemory,"opaque Memory");equal(expectedIat,indirectCalls,"IAT calls");equal(expectedFree,freeCalls,"free calls");
        }
    }
    private static void equal(long expected,long actual,String label) {
        if(expected!=actual) throw new AssertionError(label+": "+Long.toHexString(expected)+" != "+Long.toHexString(actual));
    }
    private static long invoke(Fixture memory,long moduleBase,long storage) {
        return EncodedClear424DD60.execute(memory,memory,new EncodedClear230Api.Input(moduleBase,storage));
    }
private static void boundaries230() {
    // 1. Actual two-level pointer NULL case: first pointer 0, second read at 0 returns 0.
    {
        Fixture f = new Fixture();
        long base = 0x1000L;
        long entryRcx = 0x2000L;
        // Seed entryRcx -> 0 (first pointer)
        f.seed64(entryRcx, 0L);
        // Seed address 0 -> 0 (second read)
        f.seed64(0L, 0L);

        f.expect("P.R64", entryRcx, 0L);
        f.expect("P.R64", 0L, 0L);

        long result = invoke(f, base, entryRcx);
        if (result != 0x00000000FFFFFFFFL) throw new AssertionError("null second value return mismatch");
        f.done(2, 0, 0, 0, 0);
    }

    // 2. Initial decoded begin 0, valid non-null descriptor, supplied cookie/encoded fields.
    {
        Fixture f = new Fixture();
        long base = 0x1000L;
        long entryRcx = 0x2000L;
        long cookie = 0x1234567890ABCDEFL;
        long globalAddr = base + 0x542F0B8L;

        // Seed entryRcx -> outer
        long outer = 0x3000L;
        f.seed64(entryRcx, outer);
        // Seed outer -> descriptor
        long descriptor = 0x4000L;
        f.seed64(outer, descriptor);

        // Seed global cookie
        f.seed64(globalAddr, cookie);

        // Seed descriptor -> begin (encoded)
        // Decode: ROR64(R64[descriptor] ^ cookie, cookie & 63) == 0
        // Let's pick a value for R64[descriptor] such that after XOR and ROR it is 0.
        // If ROR result is 0, then (val ^ cookie) must be 0 (since ROR of 0 is 0).
        // So val = cookie.
        long encodedBegin = cookie;
        f.seed64(descriptor, encodedBegin);

        // Seed descriptor+8 -> end (encoded)
        // Decode: ROR64(R64[descriptor+8] ^ cookie, cookie & 63)
        // Let's make end something valid, e.g., 0x100.
        // val ^ cookie = ROL64(0x100, cookie & 63)
        int rot = (int)(cookie & 63);
        long targetEnd = 0x100L;
        long encodedEnd = Long.rotateLeft(targetEnd, rot) ^ cookie;
        f.seed64(descriptor + 8, encodedEnd);

        // Expect reads:
        // 1. R64[entryRcx] -> outer
        f.expect("P.R64", entryRcx, outer);
        // 2. R64[outer] -> descriptor
        f.expect("P.R64", outer, descriptor);
        // 3. R64[globalAddr] -> cookie
        f.expect("P.R64", globalAddr, cookie);
        // 4. R64[descriptor] -> encodedBegin
        f.expect("P.R64", descriptor, encodedBegin);
        // 5. R64[descriptor+8] -> encodedEnd
        f.expect("P.R64", descriptor + 8, encodedEnd);

        // Initial decoded begin is 0. Contract: "Initial unsigned(begin-1wrap64)>0xFFFFFFFFFFFFFFFD means exactly initialbegin0 or-1 returns0; nofree/finalwrites."
        // So it returns 0 immediately after decoding begin/end.

        long result = invoke(f, base, entryRcx);
        if (result != 0L) throw new AssertionError("begin 0 return mismatch");
        f.done(5, 0, 0, 0, 0);
    }

    // 3. Initial decoded begin FFFFFFFFFFFFFFFF (UINT64_MAX).
    {
        Fixture f = new Fixture();
        long base = 0x1000L;
        long entryRcx = 0x2000L;
        long cookie = 0x1234567890ABCDEFL;
        long globalAddr = base + 0x542F0B8L;

        long outer = 0x3000L;
        f.seed64(entryRcx, outer);
        long descriptor = 0x4000L;
        f.seed64(outer, descriptor);

        // We need decoded begin to be -1L (0xFFFFFFFFFFFFFFFF).
        // Decode: ROR64(R64[descriptor] ^ cookie, cookie & 63) == -1L
        // ROR64(x, r) == -1L implies x == -1L (since ROR of -1 is -1).
        // So R64[descriptor] ^ cookie == -1L => R64[descriptor] = cookie ^ -1L.
        long encodedBegin = cookie ^ 0xFFFFFFFFFFFFFFFFL;
        f.seed64(descriptor, encodedBegin);

        // Seed descriptor+8 -> end (encoded)
        // Let's make end 0x200.
        long targetEnd = 0x200L;
        int rot = (int)(cookie & 63);
        long encodedEnd = Long.rotateLeft(targetEnd, rot) ^ cookie;
        f.seed64(descriptor + 8, encodedEnd);

        // Seed global cookie
        f.seed64(globalAddr, cookie);

        // Expect reads:
        // 1. R64[entryRcx] -> outer
        f.expect("P.R64", entryRcx, outer);
        // 2. R64[outer] -> descriptor
        f.expect("P.R64", outer, descriptor);
        // 3. R64[globalAddr] -> cookie
        f.expect("P.R64", globalAddr, cookie);
        // 4. R64[descriptor] -> encodedBegin
        f.expect("P.R64", descriptor, encodedBegin);
        // 5. R64[descriptor+8] -> encodedEnd
        f.expect("P.R64", descriptor + 8, encodedEnd);

        // Initial decoded begin is -1L. Contract: "Initial unsigned(begin-1wrap64)>0xFFFFFFFFFFFFFFFD means exactly initialbegin0 or-1 returns0"
        // So it returns 0 immediately.

        long result = invoke(f, base, entryRcx);
        if (result != 0L) throw new AssertionError("begin -1 return mismatch");
        f.done(5, 0, 0, 0, 0);
    }
}
    private static long stateful230Encoded(long decoded,long cookie) {
        return Long.rotateLeft(decoded,(int)(cookie & 63)) ^ cookie;
    }

    private static void stateful230() {
        {
            long base=0x1000L;
            long s=0x1000L, o=0x2000L, d=0x3000L;
            long g=base+0x542F0B8L, i=base+0x43DBBA8L;
            long b=0x4000L, exit=0x5000L;
            long c0=1L,c1=2L,c2=3L,c3=4L;
            long handler=0x9000L, firstIat=0xABCDEF1234567890L;
            long begin0=stateful230Encoded(b,c0),end0=stateful230Encoded(b+16,c0);
            long begin1=stateful230Encoded(i,c1),end1=stateful230Encoded(i+8,c1);
            long begin2=stateful230Encoded(exit,c2),end2=stateful230Encoded(exit,c2);
            long cell0=stateful230Encoded(handler,c0);
            Fixture f=new Fixture((m,n,t,r,a)->{
                if(n==1) {
                    m.writeInt64(g,c1);
                    m.writeInt64(d,begin1);
                    m.writeInt64(d+8,end1);
                    m.writeInt64(i,c1);
                } else if(n==2) {
                    m.writeInt64(g,c2);
                    m.writeInt64(d,begin2);
                    m.writeInt64(d+8,end2);
                } else throw new AssertionError("unexpected indirect ordinal");
            },(m,rcx)->{
                equal(exit,rcx,"current begin free input");
                m.writeInt64(g,c3);
                m.writeInt64(o,o);
            });
            f.seed64(s,o);
            f.seed64(o,d);
            f.seed64(g,c0);
            f.seed64(d,begin0);
            f.seed64(d+8,end0);
            f.seed64(b,cell0);
            f.seed64(b+8,c0);
            f.seed64(i,firstIat);

            f.expect("P.R64",s,o);
            f.expect("P.R64",o,d);
            f.expect("P.R64",g,c0);
            f.expect("P.R64",d,begin0);
            f.expect("P.R64",d+8,end0);
            f.expect("P.R64",b+8,c0);
            f.expect("P.R64",b,cell0);
            f.expect("P.W64",b,c0);
            f.expect("P.R64",i,firstIat);
            f.expectIat(0x424DDE5L,firstIat,handler,
                new EncodedClear230Api.IndirectArguments(1,c0,EncodedClear230Api.EntryUnknown.UNKNOWN));
            f.expect("C.W64",g,c1);
            f.expect("C.W64",d,begin1);
            f.expect("C.W64",d+8,end1);
            f.expect("C.W64",i,c1);
            f.expect("P.R64",g,c1);
            f.expect("P.R64",s,o);
            f.expect("P.R64",o,d);
            f.expect("P.R64",d,begin1);
            f.expect("P.R64",d+8,end1);
            // The restarted cell IS the IAT slot. The marker store changes its target.
            f.expect("P.R64",i,c1);
            f.expect("P.W64",i,c0);
            f.expect("P.R64",i,c0);
            f.expectIat(0x424DDE5L,c0,0L,
                new EncodedClear230Api.IndirectArguments(2,c1,new EncodedClear230Api.Reloaded(d,i)));
            f.expect("C.W64",g,c2);
            f.expect("C.W64",d,begin2);
            f.expect("C.W64",d+8,end2);
            f.expect("P.R64",g,c2);
            f.expect("P.R64",s,o);
            f.expect("P.R64",o,d);
            f.expect("P.R64",d,begin2);
            f.expect("P.R64",d+8,end2);
            f.expectFree(0x424DE32L,exit);
            f.expect("C.W64",g,c3);
            f.expect("C.W64",o,o);
            f.expect("P.R64",g,c3);
            // First reset aliases [outer]; both later chains must observe its new value.
            f.expect("P.R64",s,o);
            f.expect("P.R64",o,o);
            f.expect("P.W64",o,c3);
            f.expect("P.R64",s,o);
            f.expect("P.R64",o,c3);
            f.expect("P.W64",c3+8,c3);
            f.expect("P.R64",s,o);
            f.expect("P.R64",o,c3);
            f.expect("P.W64",c3+0x10,c3);

            equal(0L,invoke(f,base,s),"normal source result");
            f.done(27,5,9,2,1);
            equal(c0,f.peek64(b),"first marker");
            equal(c0,f.peek64(i),"IAT alias marker");
            equal(c3,f.peek64(g),"postfree cookie");
            equal(c3,f.peek64(o),"first reset alias");
            equal(c3,f.peek64(c3+8),"fresh second reset");
            equal(c3,f.peek64(c3+0x10),"fresh third reset");
        }
        {
            long base=0x2000L;
            long s=0x6000L,o=0x7000L,d=0x8000L,b=0x9000L;
            long g=base+0x542F0B8L,i=base+0x43DBBA8L;
            long c=5L,handler=0xFEDCBA9876543210L,target=0x1020304050607080L;
            long begin=stateful230Encoded(b,c),end=stateful230Encoded(b+8,c);
            long encodedHandler=stateful230Encoded(handler,c),changed=0xFFEEDDCCBBAA9988L;
            RuntimeException marker=new RuntimeException("opaque230");
            Fixture f=new Fixture((m,n,t,r,a)->{
                m.writeInt64(d+8,changed);
                throw marker;
            },(m,rcx)->{throw new AssertionError("free after throwing indirect");});
            f.seed64(s,o);
            f.seed64(o,d);
            f.seed64(g,c);
            f.seed64(d,begin);
            f.seed64(d+8,end);
            f.seed64(b,encodedHandler);
            f.seed64(i,target);
            f.expect("P.R64",s,o);
            f.expect("P.R64",o,d);
            f.expect("P.R64",g,c);
            f.expect("P.R64",d,begin);
            f.expect("P.R64",d+8,end);
            f.expect("P.R64",b,encodedHandler);
            f.expect("P.W64",b,c);
            f.expect("P.R64",i,target);
            f.expectIat(0x424DDE5L,target,handler,
                new EncodedClear230Api.IndirectArguments(5,c,EncodedClear230Api.EntryUnknown.UNKNOWN));
            f.expect("C.W64",d+8,changed);
            try {
                invoke(f,base,s);
                throw new AssertionError("missing opaque exception");
            } catch(RuntimeException actual) {
                if(actual!=marker) throw new AssertionError("different opaque exception",actual);
            }
            f.done(7,1,1,1,0);
            equal(c,f.peek64(b),"marker before throwing IAT");
            equal(changed,f.peek64(d+8),"opaque write survives exact throw");
        }
    }

    public static void main(String[] args) {
        boundaries230();
        stateful230();
        System.out.println("EncodedClearValidation230 groups=5 sourceInvocations=5 events=66 producerR64=46 producerW64=6 opaqueW64=10 IATcalls=3 freeCalls=1 finalCells=8 exactThrow=1");
    }

}
