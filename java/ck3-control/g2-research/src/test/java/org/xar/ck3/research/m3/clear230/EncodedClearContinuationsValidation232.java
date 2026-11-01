package org.xar.ck3.research.m3.clear230;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class EncodedClearContinuationsValidation232 {
    private EncodedClearContinuationsValidation232() { }
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
    private static long unchanged232Encoded(long value,long cookie) {
        return Long.rotateLeft(value,(int)(cookie & 63)) ^ cookie;
    }
    private static void unchanged232() {
        long base=0x1000L,s=0x1000L,o=0x2000L,d=0x3000L,b=0x4000L,e=b+16;
        long g=base+0x542F0B8L,i=base+0x43DBBA8L;
        long c0=1L,c1=2L,c2=3L;
        long h1=0xAABBCCDDEEFF0011L,h2=0x1122334455667788L,target=0x1020304050607080L;
        long begin0=unchanged232Encoded(b,c0),end0=unchanged232Encoded(e,c0);
        long begin1=unchanged232Encoded(b,c1),end1=unchanged232Encoded(e,c1);
        long begin2=unchanged232Encoded(b,c2),end2=unchanged232Encoded(e,c2);
        long raw1=unchanged232Encoded(h1,c0),raw2=unchanged232Encoded(h2,c1);
        Fixture f=new Fixture((m,n,t,r,a)->{
            if(n==1) {
                m.writeInt64(g,c1);m.writeInt64(d,begin1);m.writeInt64(d+8,end1);
            } else if(n==2) {
                m.writeInt64(g,c2);m.writeInt64(d,begin2);m.writeInt64(d+8,end2);
            } else throw new AssertionError("unexpected IAT ordinal");
        },(m,rcx)->equal(b,rcx,"unchanged current begin free"));
        f.seed64(s,o);f.seed64(o,d);f.seed64(g,c0);
        f.seed64(d,begin0);f.seed64(d+8,end0);
        f.seed64(b+8,raw1);f.seed64(b,raw2);f.seed64(i,target);
        f.expect("P.R64",s,o);f.expect("P.R64",o,d);f.expect("P.R64",g,c0);
        f.expect("P.R64",d,begin0);f.expect("P.R64",d+8,end0);
        f.expect("P.R64",b+8,raw1);f.expect("P.W64",b+8,c0);
        f.expect("P.R64",i,target);
        f.expectIat(0x424DDE5L,target,h1,new EncodedClear230Api.IndirectArguments(1,c0,EncodedClear230Api.EntryUnknown.UNKNOWN));
        f.expect("C.W64",g,c1);f.expect("C.W64",d,begin1);f.expect("C.W64",d+8,end1);
        f.expect("P.R64",g,c1);f.expect("P.R64",s,o);f.expect("P.R64",o,d);
        f.expect("P.R64",d,begin1);f.expect("P.R64",d+8,end1);
        // Equal decoded bounds continue at the earlier cell without rereading b+8.
        f.expect("P.R64",b,raw2);f.expect("P.W64",b,c0);f.expect("P.R64",i,target);
        f.expectIat(0x424DDE5L,target,h2,new EncodedClear230Api.IndirectArguments(2,c1,new EncodedClear230Api.Reloaded(d,b)));
        f.expect("C.W64",g,c2);f.expect("C.W64",d,begin2);f.expect("C.W64",d+8,end2);
        f.expect("P.R64",g,c2);f.expect("P.R64",s,o);f.expect("P.R64",o,d);
        f.expect("P.R64",d,begin2);f.expect("P.R64",d+8,end2);
        f.expectFree(0x424DE32L,b);f.expect("P.R64",g,c2);
        f.expect("P.R64",s,o);f.expect("P.R64",o,d);f.expect("P.W64",d,c2);
        f.expect("P.R64",s,o);f.expect("P.R64",o,d);f.expect("P.W64",d+8,c2);
        f.expect("P.R64",s,o);f.expect("P.R64",o,d);f.expect("P.W64",d+0x10,c2);
        equal(0L,invoke(f,base,s),"unchanged return");f.done(26,5,6,2,1);
        equal(c0,f.peek64(b+8),"first marker");equal(c0,f.peek64(b),"earlier second marker");
        equal(c2,f.peek64(g),"current cookie");
        equal(c2,f.peek64(d),"final0");equal(c2,f.peek64(d+8),"final8");equal(c2,f.peek64(d+0x10),"final10");
    }

    private static long sentinel232Encoded(long value,long cookie) {
        return Long.rotateLeft(value,(int)(cookie & 63)) ^ cookie;
    }
    private static void sentinel232() {
        long base=0x2000L,s=0x6000L,o=0x7000L,d=0x8000L,b=0x9000L;
        long g=base+0x542F0B8L,i=base+0x43DBBA8L,c0=5L,c1=~o;
        long handler=0xFEDCBA9876543210L,target=0x1020304050607080L;
        long begin=sentinel232Encoded(b,c0),end=sentinel232Encoded(b+8,c0);
        long raw=sentinel232Encoded(handler,c0);
        Fixture f=new Fixture((m,n,t,r,a)->{
            m.writeInt64(g,c1);m.writeInt64(o,o);m.writeInt64(o+8,c1);
        },(m,rcx)->{throw new AssertionError("free on callback-updated -1");});
        f.seed64(s,o);f.seed64(o,d);f.seed64(g,c0);
        f.seed64(d,begin);f.seed64(d+8,end);f.seed64(b,raw);f.seed64(i,target);
        f.expect("P.R64",s,o);f.expect("P.R64",o,d);f.expect("P.R64",g,c0);
        f.expect("P.R64",d,begin);f.expect("P.R64",d+8,end);
        f.expect("P.R64",b,raw);f.expect("P.W64",b,c0);f.expect("P.R64",i,target);
        f.expectIat(0x424DDE5L,target,handler,new EncodedClear230Api.IndirectArguments(5,c0,EncodedClear230Api.EntryUnknown.UNKNOWN));
        f.expect("C.W64",g,c1);f.expect("C.W64",o,o);f.expect("C.W64",o+8,c1);
        // New descriptor is o; o XOR ~o decodes to -1, and c1 XOR c1 to0.
        f.expect("P.R64",g,c1);f.expect("P.R64",s,o);f.expect("P.R64",o,o);
        f.expect("P.R64",o,o);f.expect("P.R64",o+8,c1);
        // No FREE or second global read: final chains begin immediately.
        f.expect("P.R64",s,o);f.expect("P.R64",o,o);f.expect("P.W64",o,c1);
        f.expect("P.R64",s,o);f.expect("P.R64",o,c1);f.expect("P.W64",c1+8,c1);
        f.expect("P.R64",s,o);f.expect("P.R64",o,c1);f.expect("P.W64",c1+0x10,c1);
        equal(0L,invoke(f,base,s),"updated sentinel return");f.done(18,4,3,1,0);
        equal(c0,f.peek64(b),"initial marker");equal(c1,f.peek64(g),"callback cookie");
        equal(c1,f.peek64(o),"first reset alias");equal(c1,f.peek64(o+8),"opaque endencoding");
        equal(c1,f.peek64(c1+8),"fresh second reset");equal(c1,f.peek64(c1+0x10),"fresh third reset");
    }

    public static void main(String[] args) {
        unchanged232();
        sentinel232();
        System.out.println("EncodedClearContinuationsValidation232 groups=2 newSourceInvocations=2 events=66 targetR64=44 targetW64=9 opaqueW64=9 IATcalls=3 freeCalls=1 finalCells=12");
    }

}
