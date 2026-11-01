package org.xar.ck3.research.m3.word226;
import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.indexed225.IndexedLookupHelper424E448;
/** Owner mechanical fixture only; no newbindingtest/expected beforefirstHTTP. */
public final class WordCompareCallerValidation226 {
    static int checks,groups,eventCount,memoryEvents,portEvents;
    static String h(long v){return Long.toUnsignedString(v,16);}
    static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    static void equal(long a,long b,String why){check(a==b,why+" actual="+h(a)+" expected="+h(b));}
    static void same(Object a,Object b){check(a==b,"identity");}
    static void iae(Runnable r){checks++;try{r.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expectedIAE");}
    static void events(List<String> actual,String... expected){check(actual.equals(List.of(expected)),"trace actual="+actual+" expected="+List.of(expected));for(String e:actual){eventCount++;if(e.startsWith("R")||e.startsWith("W")||e.startsWith("X"))memoryEvents++;else portEvents++;}}
    static void done(String s){groups++;System.out.println("PASS "+s);}
    static final class Mem implements WordCompareBinding226Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> log;Mem(List<String> l){log=l;}
        void seed(long a,int n,long v){for(int i=0;i<n;i++)bytes.put(a+i,(byte)(v >>> (i*8)));}
        void seed8(long a,int v){seed(a,1,v);}void seed16(long a,int v){seed(a,2,v);}void seed32(long a,int v){seed(a,4,v);}void seed64(long a,long v){seed(a,8,v);}
        long peek(long a,int n){long v=0;for(int i=0;i<n;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n){long v=peek(a,n);log.add("R"+(8*n)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v){seed(a,n,v);log.add("W"+(8*n)+"@"+h(a)+"="+h(n==8?v:v&0xffffffffL));}
        @Override public long readPointer(long a){return get(a,8);}@Override public int readInt32(long a){return (int)get(a,4);}
        @Override public void writeInt32(long a,int v){put(a,4,v);}@Override public void writeInt64(long a,long v){put(a,8,v);}
        @Override public long exchangeInt64(long a,long v){long old=peek(a,8);seed(a,8,v);log.add("X64@"+h(a)+"="+h(old)+"->"+h(v));return old;}
        @Override public int readWord16(long a){return (int)get(a,2);}
    }
    static class Fallback implements IndexedHelper225Api.Ports {
        @Override public long call43da478(IndexedHelper225Api.Memory m,long site,long target,long rcx,int edx,int r8d){throw new AssertionError("unexpected478");}
        @Override public int call43da738(IndexedHelper225Api.Memory m,long site,long target){throw new AssertionError("unexpected738");}
        @Override public int call4246a60(IndexedHelper225Api.Memory m,long site,long rcx,long rdx,int r8d){throw new AssertionError("activefallback replay");}
        @Override public void call43da7c0(IndexedHelper225Api.Memory m,long site,long target,long rcx){throw new AssertionError("unexpected7C0");}
        @Override public long call43da680(IndexedHelper225Api.Memory m,long site,long target,long rcx,long rdx){throw new AssertionError("unexpected680");}
    }
    static class Forward implements IndexedHelper225Api.Ports {
        final IndexedHelper225Api.Ports delegate;Forward(IndexedHelper225Api.Ports d){delegate=d;}
        @Override public long call43da478(IndexedHelper225Api.Memory m,long site,long target,long rcx,int edx,int r8d){return delegate.call43da478(m,site,target,rcx,edx,r8d);}
        @Override public int call43da738(IndexedHelper225Api.Memory m,long site,long target){return delegate.call43da738(m,site,target);}
        @Override public int call4246a60(IndexedHelper225Api.Memory m,long site,long rcx,long rdx,int r8d){return delegate.call4246a60(m,site,rcx,rdx,r8d);}
        @Override public void call43da7c0(IndexedHelper225Api.Memory m,long site,long target,long rcx){delegate.call43da7c0(m,site,target,rcx);}
        @Override public long call43da680(IndexedHelper225Api.Memory m,long site,long target,long rcx,long rdx){return delegate.call43da680(m,site,target,rcx,rdx);}
    }
    public static void main(String[] args){firstComparisonZero();retryComparisonFailure();System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);}
static void firstComparisonZero() {
    List<String> log = new ArrayList<>();
    Mem m = new Mem(log);
    long base = 0x10000000L;
    long idx = 3L;
    long nameAddr = 7000L;
    long listBegin = 5000L;
    long listEnd = 5004L;

    // Seed inputs and canaries
    m.seed64(base + 0x5C5D790L + idx * 8L, 0L);
    m.seed64(base + 0x542F0B8L, 0L);
    m.seed32(listBegin, 2);
    m.seed64(base + 0x5C5D6F0L + 2L * 8L, 0L);
    m.seed64(base + 0x44269D0L + 2L * 8L, 6000L);
    m.seed64(base + 0x43DA478L, 0xF100000000000001L);
    m.seed64(base + 0x43DA738L, 0xF200000000000002L);
    m.seed16(6000L, 0x0041);
    m.seed16(6002L, 0x0000);
    long rdxConst = base + 0x44226A0L;
    m.seed16(rdxConst, 0x0041);
    m.seed16(rdxConst + 2L, 0x0000);

    // Exact outside-width byte canaries; skipped secondconstant/name remain unmapped.
    m.seed8(6000L-1,0xa1);m.seed8(6000L+4,0xa2);
    m.seed8(rdxConst-1,0xb1);m.seed8(rdxConst+4,0xb2);
    m.seed8(base+0x5c5d6f0L+2L*8L-1,0xc1);m.seed8(base+0x5c5d6f0L+2L*8L+8,0xc2);
    m.seed8(base+0x5c5d790L+idx*8L-1,0xd1);m.seed8(base+0x5c5d790L+idx*8L+8,0xd2);

    int[] compareCount = new int[]{0};
    int[] loadCount = new int[]{0};
    int[] errorCount = new int[]{0};

    IndexedHelper225Api.Ports fallback = new IndexedHelper225Api.Ports() {
        @Override public long call43da478(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, int edx, int r8d) {
            same(memory,m);equal(siteRva,0x424e4ebL,"load actualsite");equal(actualTarget,0xf100000000000001L,"load actualIATcode");
            equal(rcx,6000L,"load path");equal(edx,0,"load EDX");equal(r8d,0x800,"firstload R8D");
            loadCount[0]++;
            log.add("Pload@424E4EB target=" + h(actualTarget) + " rcx=" + h(rcx) + " edx=" + h(edx) + " r8d=" + h(r8d));
            return 0L;
        }
        @Override public int call43da738(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget) {
            same(memory,m);equal(siteRva,0x424e4f9L,"error actualsite");equal(actualTarget,0xf200000000000002L,"error actualIATcode");
            errorCount[0]++;
            log.add("Perror@424E4F9 target=" + h(actualTarget));
            return 0x57;
        }
        @Override public int call4246a60(IndexedHelper225Api.Memory memory, long siteRva, long rcx, long rdx, int r8d) {
            throw new AssertionError("activeFallbackA60");
        }
        @Override public void call43da7c0(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx) {
            throw new AssertionError("unexpected7C0");
        }
        @Override public long call43da680(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, long rdx) {
            throw new AssertionError("unexpected680");
        }
    };

    WordCompare226Api algorithm = new WordCompare4246A60();
    IndexedHelper225Api.Ports bound = WordCompareFromIndexedBinding226.bind(m, algorithm, fallback);

    IndexedHelper225Api.Ports observed = new IndexedHelper225Api.Ports() {
        @Override public long call43da478(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, int edx, int r8d) {
            return bound.call43da478(memory, siteRva, actualTarget, rcx, edx, r8d);
        }
        @Override public int call43da738(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget) {
            return bound.call43da738(memory, siteRva, actualTarget);
        }
        @Override public int call4246a60(IndexedHelper225Api.Memory memory, long siteRva, long rcx, long rdx, int r8d) {
            same(memory, m);
            equal(siteRva, 0x424E514L, "site");
            equal(rcx, 6000L, "rcx");
            equal(rdx, rdxConst, "rdx");
            equal(r8d, 7, "r8d");
            compareCount[0]++;
            log.add("Pcompare@424E514 rcx=" + h(rcx) + " rdx=" + h(rdx) + " r8d=" + h(r8d));
            int res = bound.call4246a60(memory, siteRva, rcx, rdx, r8d);
            equal(res, 0, "compareResult");
            return res;
        }
        @Override public void call43da7c0(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx) {
            bound.call43da7c0(memory, siteRva, actualTarget, rcx);
        }
        @Override public long call43da680(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, long rdx) {
            return bound.call43da680(memory, siteRva, actualTarget, rcx, rdx);
        }
    };

    IndexedHelper225Api.Input input = new IndexedHelper225Api.Input(base, 3, nameAddr, listBegin, listEnd);
    long result = IndexedLookupHelper424E448.execute(m, observed, input);

    equal(result, 0L, "finalResult");
    equal(compareCount[0], 1, "compareCount");
    equal(loadCount[0], 1, "loadCount");
    equal(errorCount[0], 1, "errorCount");

    String[] expected = {
        "R64@" + h(base + 0x5C5D790L + idx * 8L) + "=" + h(0L),
        "R64@" + h(base + 0x542F0B8L) + "=" + h(0L),
        "R32@" + h(listBegin) + "=" + h(2L),
        "R64@" + h(base + 0x5C5D6F0L + 2L * 8L) + "=" + h(0L),
        "R64@" + h(base + 0x44269D0L + 2L * 8L) + "=" + h(6000L),
        "R64@" + h(base + 0x43DA478L) + "=" + h(0xF100000000000001L),
        "Pload@424E4EB target=" + h(0xF100000000000001L) + " rcx=" + h(6000L) + " edx=" + h(0L) + " r8d=" + h(0x800L),
        "R64@" + h(base + 0x43DA738L) + "=" + h(0xF200000000000002L),
        "Perror@424E4F9 target=" + h(0xF200000000000002L),
        "Pcompare@424E514 rcx=" + h(6000L) + " rdx=" + h(rdxConst) + " r8d=" + h(7L),
        "R16@" + h(6000L) + "=" + h(0x41L),
        "R16@" + h(rdxConst) + "=" + h(0x41L),
        "R16@" + h(6002L) + "=" + h(0L),
        "R16@" + h(6002L) + "=" + h(0L),
        "R16@" + h(rdxConst + 2L) + "=" + h(0L),
        "X64@" + h(base + 0x5C5D6F0L + 2L * 8L) + "=" + h(0L) + "->" + h(-1L),
        "R64@" + h(base + 0x542F0B8L) + "=" + h(0L),
        "X64@" + h(base + 0x5C5D790L + idx * 8L) + "=" + h(0L) + "->" + h(-1L)
    };

    events(log, expected);
    equal(m.peek(base + 0x5C5D6F0L + 2L * 8L, 8), -1L, "cacheFinal");
    equal(m.peek(base + 0x5C5D790L + idx * 8L, 8), -1L, "tableFinal");
    equal(m.peek(base + 0x542F0B8L, 8), 0L, "cookieFinal");
    equal(m.peek(6000L, 2), 0x41L, "word1");
    equal(m.peek(6002L, 2), 0L, "word2");
    equal(m.peek(rdxConst, 2), 0x41L, "word3");
    equal(m.peek(rdxConst + 2L, 2), 0L, "word4");

    equal(m.peek(6000L-1,1),0xa1,"path before");equal(m.peek(6000L+4,1),0xa2,"path after");
    equal(m.peek(rdxConst-1,1),0xb1,"firstconstant before");equal(m.peek(rdxConst+4,1),0xb2,"firstconstant after");
    equal(m.peek(base+0x5c5d6f0L+2L*8L-1,1),0xc1,"modulecache before");equal(m.peek(base+0x5c5d6f0L+2L*8L+8,1),0xc2,"modulecache after");
    equal(m.peek(base+0x5c5d790L+idx*8L-1,1),0xd1,"functioncache before");equal(m.peek(base+0x5c5d790L+idx*8L+8,1),0xd2,"functioncache after");
    equal(m.peek(listBegin,4),2,"list input unchanged");
    check(!m.bytes.containsKey(nameAddr),"unused name unmapped");check(!m.bytes.containsKey(base+0x4426ec8L),"skipped secondconstant unmapped");
    done("firstComparisonZero");
}
static void retryComparisonFailure() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed64(0x25c5d7b0L,0);m.seed64(0x2542f0b8L,0);m.seed32(0x7000L,3);
    m.seed64(0x25c5d708L,0);m.seed64(0x244269e8L,0x8000L);
    m.seed64(0x243da478L,0xf100000000000001L);m.seed64(0x243da738L,0xf200000000000002L);
    m.seed16(0x8000L,0x41);m.seed16(0x8002L,0);
    m.seed16(0x244226a0L,0x42);m.seed16(0x244226a2L,0);
    m.seed16(0x24426ec8L,0x43);m.seed16(0x24426ecaL,0);
    m.seed8(0x25c5d7afL,0xa1);m.seed8(0x25c5d7b8L,0xa2);m.seed8(0x25c5d707L,0xb1);m.seed8(0x25c5d710L,0xb2);
    m.seed8(0x7fffL,0xc1);m.seed8(0x8004L,0xc2);m.seed8(0x2442269fL,0xd1);m.seed8(0x244226a4L,0xd2);m.seed8(0x24426ec7L,0xe1);m.seed8(0x24426eccL,0xe2);
    int[] loads={0},errors={0},compares={0};
    Fallback fallback=new Fallback() {
        @Override public long call43da478(IndexedHelper225Api.Memory q,long site,long target,long rcx,int edx,int r8d) {
            same(q,m);int n=loads[0]++;check(n<2,"retry exactlytwoloads");
            equal(site,n==0?0x424e4ebL:0x424e53bL,"actual first/retry site");
            equal(target,n==0?0xf100000000000001L:0xf400000000000004L,"actual freshfirst/retry code");
            equal(rcx,0x8000L,"retry path");equal(edx,0,"load EDX");equal(r8d,n==0?0x800:0,"first/retry R8D");
            a.add("Pload:"+h(site)+":"+h(target)+":"+h(rcx)+":"+h(Integer.toUnsignedLong(edx))+":"+h(Integer.toUnsignedLong(r8d)));return 0;
        }
        @Override public int call43da738(IndexedHelper225Api.Memory q,long site,long target) {
            same(q,m);equal(site,0x424e4f9L,"error actualsite");equal(target,0xf200000000000002L,"error actualcode");errors[0]++;
            a.add("Perror:"+h(site)+":"+h(target));q.writeInt64(0x243da478L,0xf400000000000004L);return 0x57;
        }
    };
    IndexedHelper225Api.Ports bound=WordCompareFromIndexedBinding226.bind(m,new WordCompare4246A60(),fallback);
    Forward observed=new Forward(bound) {
        @Override public int call4246a60(IndexedHelper225Api.Memory q,long site,long rcx,long rdx,int r8d) {
            same(q,m);int n=compares[0]++;check(n<2,"two actual comparison edges");
            equal(site,n==0?0x424e514L:0x424e52aL,"actual comparison site");equal(rcx,0x8000L,"comparison path");
            equal(rdx,n==0?0x244226a0L:0x24426ec8L,"actual fixedcomparison RDX");equal(r8d,7,"source R8D7");
            a.add("Pcompare:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(Integer.toUnsignedLong(r8d)));
            int difference=super.call4246a60(q,site,rcx,rdx,r8d);equal(difference,n==0?-1:-2,"real nonzero comparison");return difference;
        }
    };
    equal(IndexedLookupHelper424E448.execute(m,observed,new IndexedHelper225Api.Input(0x20000000L,4,0x9000L,0x7000L,0x7004L)),0,"actual225 retryfailure return");
    events(a,"R64@25c5d7b0=0","R64@2542f0b8=0","R32@7000=3","R64@25c5d708=0","R64@244269e8=8000",
        "R64@243da478=f100000000000001","Pload:424e4eb:f100000000000001:8000:0:800","R64@243da738=f200000000000002",
        "Perror:424e4f9:f200000000000002","W64@243da478=f400000000000004","Pcompare:424e514:8000:244226a0:7",
        "R16@8000=41","R16@244226a0=42","R16@8000=41","R16@244226a0=42","Pcompare:424e52a:8000:24426ec8:7",
        "R16@8000=41","R16@24426ec8=43","R16@8000=41","R16@24426ec8=43","R64@243da478=f400000000000004",
        "Pload:424e53b:f400000000000004:8000:0:0","X64@25c5d708=0->ffffffffffffffff","R64@2542f0b8=0","X64@25c5d7b0=0->ffffffffffffffff");
    equal(loads[0],2,"exactfirst/retry loads");equal(errors[0],1,"exacterror observation");equal(compares[0],2,"both actualA60 edges");
    equal(m.peek(0x25c5d7b0L,8),-1L,"failure functionencoded cache");equal(m.peek(0x25c5d708L,8),-1L,"failure modulecache");equal(m.peek(0x2542f0b8L,8),0,"cookie unchanged");equal(m.peek(0x243da478L,8),0xf400000000000004L,"freshretry IATeffect");
    equal(m.peek(0x7000L,4),3,"listDWORD unchanged");equal(m.peek(0x8000L,2),0x41,"path firstWORD");equal(m.peek(0x8002L,2),0,"path NUL");equal(m.peek(0x244226a0L,2),0x42,"firstconstant WORD");equal(m.peek(0x244226a2L,2),0,"firstconstant NUL");equal(m.peek(0x24426ec8L,2),0x43,"secondconstant WORD");equal(m.peek(0x24426ecaL,2),0,"secondconstant NUL");
    equal(m.peek(0x25c5d7afL,1),0xa1,"function before");equal(m.peek(0x25c5d7b8L,1),0xa2,"function after");equal(m.peek(0x25c5d707L,1),0xb1,"module before");equal(m.peek(0x25c5d710L,1),0xb2,"module after");
    equal(m.peek(0x7fffL,1),0xc1,"path before");equal(m.peek(0x8004L,1),0xc2,"path after");equal(m.peek(0x2442269fL,1),0xd1,"firstconstant before");equal(m.peek(0x244226a4L,1),0xd2,"firstconstant after");equal(m.peek(0x24426ec7L,1),0xe1,"secondconstant before");equal(m.peek(0x24426eccL,1),0xe2,"secondconstant after");
    check(!m.bytes.containsKey(0x9000L),"unusedname unmapped");check(!m.bytes.containsKey(0x243da680L),"resolve IATunmapped");
    done("retryComparisonFailure");
}

}
