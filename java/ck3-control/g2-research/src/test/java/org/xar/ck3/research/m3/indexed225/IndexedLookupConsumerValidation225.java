package org.xar.ck3.research.m3.indexed225;
import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.out224.OutHelper224Api;
import org.xar.ck3.research.m3.out224.OutHelper424E620;
/** Owner mechanical fixture only. Newconsumer expected/body not yetwritten. */
public final class IndexedLookupConsumerValidation225 {
    static int checks,groups,eventCount,memoryEvents,portEvents;
    static String h(long v){return Long.toUnsignedString(v,16);}
    static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    static void equal(long a,long b,String why){check(a==b,why+" actual="+h(a)+" expected="+h(b));}
    static void same(Object a,Object b){check(a==b,"identity");}
    static void iae(Runnable r){checks++;try{r.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expectedIAE");}
    static void events(List<String> actual,String... expected){check(actual.equals(List.of(expected)),"trace actual="+actual+" expected="+List.of(expected));for(String e:actual){eventCount++;if(e.startsWith("R")||e.startsWith("W")||e.startsWith("X"))memoryEvents++;else portEvents++;}}
    static void done(String s){groups++;System.out.println("PASS "+s);}
    static final class Mem implements IndexedHelper225Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> log;Mem(List<String> l){log=l;}
        void seed(long a,int n,long v){for(int i=0;i<n;i++)bytes.put(a+i,(byte)(v >>> (i*8)));}
        void seed8(long a,int v){seed(a,1,v);}void seed32(long a,int v){seed(a,4,v);}void seed64(long a,long v){seed(a,8,v);}
        long peek(long a,int n){long v=0;for(int i=0;i<n;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n){long v=peek(a,n);log.add("R"+(8*n)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v){seed(a,n,v);log.add("W"+(8*n)+"@"+h(a)+"="+h(n==8?v:v&0xffffffffL));}
        @Override public long readPointer(long a){return get(a,8);}@Override public int readInt32(long a){return (int)get(a,4);}
        @Override public void writeInt32(long a,int v){put(a,4,v);}@Override public void writeInt64(long a,long v){put(a,8,v);}
        @Override public long exchangeInt64(long a,long v){long old=peek(a,8);seed(a,8,v);log.add("X64@"+h(a)+"="+h(old)+"->"+h(v));return old;}
    }
    static class Child implements IndexedHelper225Api.Ports {
        @Override public long call43da478(IndexedHelper225Api.Memory m,long site,long target,long rcx,int edx,int r8d){throw new AssertionError("unexpected478");}
        @Override public int call43da738(IndexedHelper225Api.Memory m,long site,long target){throw new AssertionError("unexpected738");}
        @Override public int call4246a60(IndexedHelper225Api.Memory m,long site,long rcx,long rdx,int r8d){throw new AssertionError("unexpectedA60");}
        @Override public void call43da7c0(IndexedHelper225Api.Memory m,long site,long target,long rcx){throw new AssertionError("unexpected7C0");}
        @Override public long call43da680(IndexedHelper225Api.Memory m,long site,long target,long rcx,long rdx){throw new AssertionError("unexpected680");}
    }
    static class OuterFallback implements OutHelper224Api.Ports {
        @Override public long call424e448(NativeTaskMemory m,long site,int ecx,long rdx,long r8,long r9){throw new AssertionError("activefallback replay");}
        @Override public long tail43dbba8(NativeTaskMemory m,long site,long target,long rax,long rcx,long rdx){throw new AssertionError("unexpectedtail");}
    }
    public static void main(String[] args){guards();cachedConsumer();System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);}
static void guards() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a),foreign=new Mem(a);
    OuterFallback fallback=new OuterFallback() {
        @Override public long tail43dbba8(NativeTaskMemory q,long site,long target,long rax,long rcx,long rdx) {
            same(q,foreign);equal(site,0x9999L,"passivetail site");equal(target,0xf100000000000001L,"passivetail target");equal(rax,0xf200000000000002L,"passivetail liveRAX");equal(rcx,0xf300000000000003L,"passivetail RCX");equal(rdx,0xf400000000000004L,"passivetail RDX");
            a.add("Ptail:"+h(site)+":"+h(target)+":"+h(rax)+":"+h(rcx)+":"+h(rdx));return 0x80000000cafebabeL;
        }
    };
    OutHelper224Api.Ports bound=IndexedLookupFromOutBinding225.bind(0x10000000L,m,new Child(),fallback);
    iae(()->bound.call424e448(foreign,0x424e643L,0x1c,0x14427010L,0x1442700cL,0x14427010L));events(a);
    iae(()->bound.call424e448(m,0x424e644L,0x1c,0x14427010L,0x1442700cL,0x14427010L));events(a);
    check(m.bytes.isEmpty()&&foreign.bytes.isEmpty(),"active guards before memory effects");
    equal(bound.tail43dbba8(foreign,0x9999L,0xf100000000000001L,0xf200000000000002L,0xf300000000000003L,0xf400000000000004L),0x80000000cafebabeL,"passivetail exactfullreturn");
    events(a,"Ptail:9999:f100000000000001:f200000000000002:f300000000000003:f400000000000004");
    check(m.bytes.isEmpty()&&foreign.bytes.isEmpty(),"passivetail no extra memory effect");
    done("guards");
}

static void cachedConsumer() {
    List<String> log = new ArrayList<>();
    Mem m = new Mem(log);
    long base = 0x10000000L;
    long entryRcx = 0xF000000000005000L;
    long tableAddr = base + 0x5C5D790L + 0x1CL * 8L;
    long cookieAddr = base + 0x542F0B8L;
    long iatAddr = base + 0x43DBBA8L;

    // Seed canaries (single byte)
    m.seed8(tableAddr - 1, 0x11);
    m.seed8(tableAddr + 8, 0x22);
    m.seed8(cookieAddr - 1, 0x33);
    m.seed8(cookieAddr + 8, 0x44);

    // Invocation 1: Cached Nonzero
    m.seed64(tableAddr, 0xF123456700000000L);
    m.seed64(cookieAddr, 0L);
    m.seed64(iatAddr, 0xE23456789ABCDEF0L);

    Child child = new Child();
    int[] edgeCount = new int[1];
    int[] tailCount = new int[1];

    // ACTUAL fallback with overridden tail
    OutHelper224Api.Ports fallback = new OutHelper224Api.Ports() {
        @Override public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
            throw new AssertionError("unexpected448");
        }
        @Override public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, long rcx, long rdx) {
            same(memory, m);
            equal(siteRva, 0x424E65CL, "tail site");
            equal(actualTarget, 0xE23456789ABCDEF0L, "tail target");
            equal(liveRax, 0xF123456700000000L, "tail liveRax");
            equal(rcx, 0xFFFFFFFFFFFFFFFAL, "tail rcx");
            equal(rdx, entryRcx, "tail rdx");
            tailCount[0]++;
            log.add("Ptail@" + h(siteRva) + "," + h(actualTarget) + "," + h(liveRax) + "," + h(rcx) + "," + h(rdx));
            return 0x80000000ABCDEF12L;
        }
    };

    OutHelper224Api.Ports bound = IndexedLookupFromOutBinding225.bind(base, m, child, fallback);

    // ACTUAL observing Ports
    OutHelper224Api.Ports observed = new OutHelper224Api.Ports() {
        @Override public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
            same(memory, m);
            equal(siteRva, 0x424E643L, "edge site");
            equal(ecx, 0x1C, "edge ecx");
            equal(rdx, base + 0x4427010L, "edge rdx");
            equal(r8, base + 0x442700CL, "edge r8");
            equal(r9, base + 0x4427010L, "edge r9");
            check(rdx == r9, "rdx==r9");
            edgeCount[0]++;
            log.add("Pedge@" + h(siteRva) + "," + h(ecx) + "," + h(rdx) + "," + h(r8) + "," + h(r9));
            return bound.call424e448(memory, siteRva, ecx, rdx, r8, r9);
        }
        @Override public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, long rcx, long rdx) {
            return bound.tail43dbba8(memory, siteRva, actualTarget, liveRax, rcx, rdx);
        }
    };

    long r1 = OutHelper424E620.execute(m, observed, new OutHelper224Api.Input(base, entryRcx));
    equal(r1, 0x80000000ABCDEF12L, "inv1 return");

    // Invocation 2: Cached Sentinel (-1)
    m.seed64(tableAddr, -1L);
    m.seed64(cookieAddr, 0L);

    long r2 = OutHelper424E620.execute(m, observed, new OutHelper224Api.Input(base, entryRcx));
    equal(r2, 0x00000000C0000225L, "inv2 return");

    // Verify counts
    equal(edgeCount[0], 2, "edge count");
    equal(tailCount[0], 1, "tail count");

    // Verify canaries unchanged
    equal(m.peek(tableAddr - 1, 1), 0x11L, "table left canary");
    equal(m.peek(tableAddr + 8, 1), 0x22L, "table right canary");
    equal(m.peek(cookieAddr - 1, 1), 0x33L, "cookie left canary");
    equal(m.peek(cookieAddr + 8, 1), 0x44L, "cookie right canary");

    // Verify trace
    String[] expected = {
        "Pedge@" + h(0x424E643L) + "," + h(0x1CL) + "," + h(base + 0x4427010L) + "," + h(base + 0x442700CL) + "," + h(base + 0x4427010L),
        "R64@" + h(tableAddr) + "=" + h(0xF123456700000000L),
        "R64@" + h(cookieAddr) + "=0",
        "R64@" + h(iatAddr) + "=" + h(0xE23456789ABCDEF0L),
        "Ptail@" + h(0x424E65CL) + "," + h(0xE23456789ABCDEF0L) + "," + h(0xF123456700000000L) + "," + h(0xFFFFFFFFFFFFFFFAL) + "," + h(entryRcx),
        "Pedge@" + h(0x424E643L) + "," + h(0x1CL) + "," + h(base + 0x4427010L) + "," + h(base + 0x442700CL) + "," + h(base + 0x4427010L),
        "R64@" + h(tableAddr) + "=" + h(-1L),
        "R64@" + h(cookieAddr) + "=0"
    };
    events(log, expected);

    equal(m.peek(tableAddr,8),-1L,"sentinel table remains unchanged");
    equal(m.peek(cookieAddr,8),0,"cookie remains unchanged");
    equal(m.peek(iatAddr,8),0xe23456789abcdef0L,"tail IAT remains unchanged");
    check(!m.bytes.containsKey(0x14427010L),"name/end pointer not preloaded");
    check(!m.bytes.containsKey(0x1442700cL),"list pointer not preloaded");
    check(!m.bytes.containsKey(entryRcx),"outer saved pointer not dereferenced");
    done("cachedConsumer");
}
}
