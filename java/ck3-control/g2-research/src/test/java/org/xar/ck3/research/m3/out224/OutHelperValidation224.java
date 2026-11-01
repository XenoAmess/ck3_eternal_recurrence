package org.xar.ck3.research.m3.out224;
import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
/** Owner mechanical fixture only. No scene or expected prior to first HTTP. */
public final class OutHelperValidation224 {
    static int checks,groups,eventCount,memoryEvents,portEvents;
    static String h(long v){return Long.toUnsignedString(v,16);}
    static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    static void equal(long a,long b,String why){check(a==b,why+" actual="+h(a)+" expected="+h(b));}
    static void same(Object a,Object b){check(a==b,"identity");}
    static void events(List<String> actual,String... expected){
        check(actual.equals(List.of(expected)),"orderedtrace actual="+actual+" expected="+List.of(expected));
        for(String e:actual){eventCount++;if(e.startsWith("R")||e.startsWith("W"))memoryEvents++;else portEvents++;}
    }
    static void done(String name){groups++;System.out.println("PASS "+name);}
    static final class Mem implements NativeTaskMemory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> log;
        Mem(List<String> log){this.log=log;}
        void seed(long a,int n,long v){for(int i=0;i<n;i++)bytes.put(a+i,(byte)(v >>> (i*8)));}
        void seed8(long a,int v){seed(a,1,v);}void seed32(long a,int v){seed(a,4,v);}void seed64(long a,long v){seed(a,8,v);}
        long peek(long a,int n){long v=0;for(int i=0;i<n;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n){long v=peek(a,n);log.add("R"+(n*8)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v){seed(a,n,v);log.add("W"+(n*8)+"@"+h(a)+"="+h(n==8?v:v&0xffffffffL));}
        @Override public long readPointer(long a){return get(a,8);}
        @Override public int readInt32(long a){return (int)get(a,4);}
        @Override public void writeInt32(long a,int v){put(a,4,v);}
        @Override public void writeInt64(long a,long v){put(a,8,v);}
    }
    static class Calls implements OutHelper224Api.Ports {
        @Override public long call424e448(NativeTaskMemory m,long site,int ecx,long rdx,long r8,long r9){throw new AssertionError("unexpected direct");}
        @Override public long tail43dbba8(NativeTaskMemory m,long site,long target,long rax,long rcx,long rdx){throw new AssertionError("unexpected tail");}
    }
    public static void main(String[] args){zero();nonzero();exception();System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);}
static void zero() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    Calls calls=new Calls() {
        @Override public long call424e448(NativeTaskMemory q,long site,int ecx,long rdx,long r8,long r9) {
            same(q,m);equal(site,0x424e643L,"zero directsite");equal(ecx,0x1c,"zero ECX");equal(rdx,0x4427010L,"zero RDX");equal(r8,0x442700cL,"zero R8");equal(r9,0x4427010L,"zero R9");equal(rdx,r9,"zero alias");
            a.add("Pcall:"+h(site)+":"+h(Integer.toUnsignedLong(ecx))+":"+h(rdx)+":"+h(r8)+":"+h(r9));return 0;
        }
    };
    equal(OutHelper424E620.execute(m,calls,new OutHelper224Api.Input(0,0xfedcba9876543210L)),0x00000000c0000225L,"MOV EAX zeroextends");
    events(a,"Pcall:424e643:1c:4427010:442700c:4427010");
    check(m.bytes.isEmpty(),"zero no source Memoryeffect or IATmapping");
    done("zero");
}

static void exception() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed32(0x24427010L,0x11111111);m.seed8(0x2442700fL,0xe7);m.seed8(0x24427014L,0x7e);
    RuntimeException marker=new RuntimeException("controlled directcallback failure");
    Calls calls=new Calls() {
        @Override public long call424e448(NativeTaskMemory q,long site,int ecx,long rdx,long r8,long r9) {
            same(q,m);equal(site,0x424e643L,"exception directsite");equal(ecx,0x1c,"exception ECX");equal(rdx,0x24427010L,"exception RDX");equal(r8,0x2442700cL,"exception R8");equal(r9,0x24427010L,"exception R9");equal(rdx,r9,"exception alias");
            a.add("Pcall:"+h(site)+":"+h(Integer.toUnsignedLong(ecx))+":"+h(rdx)+":"+h(r8)+":"+h(r9));
            q.writeInt32(rdx,0x12345678);throw marker;
        }
    };
    try {
        OutHelper424E620.execute(m,calls,new OutHelper224Api.Input(0x20000000L,0xabcdef1234567890L));
        throw new AssertionError("direct exception was swallowed");
    } catch(RuntimeException actual) {same(actual,marker);}
    events(a,"Pcall:424e643:1c:24427010:2442700c:24427010","W32@24427010=12345678");
    equal(m.peek(0x24427010L,4),0x12345678L,"prefix opaqueeffect preserved");equal(m.peek(0x2442700fL,1),0xe7,"exception beforeDWORD");equal(m.peek(0x24427014L,1),0x7e,"exception afterDWORD");
    check(!m.bytes.containsKey(0x243dbba8L),"exception no IATmapping");check(!m.bytes.containsKey(0xabcdef1234567890L),"exception savedentrypointer not dereferenced");
    done("exception");
}

    static void nonzero() {
        long base = 0x10000000L;
        long entryRcx = 0xf000000000005000L;
        long actualRDX = base + 0x4427010L;
        long actualR8 = base + 0x442700CL;
        long actualR9 = base + 0x4427010L;
        long iatSlot = base + 0x43DBBA8L;

        List<String> log = new ArrayList<>();
        Mem m = new Mem(log);

        // Seed entryRcx slot and neighbors
        m.seed32(entryRcx, 0xcafed00d);
        m.seed8(entryRcx - 1, 0x11);
        m.seed8(entryRcx + 4, 0x22);

        // Seed R8 canary and neighbors
        m.seed32(actualR8, 0xdeadbeef);
        m.seed8(actualR8 - 1, 0x33);

        // Seed RDX canary and neighbors
        m.seed32(actualRDX, 0x12345678);
        m.seed8(actualRDX + 4, 0x66);

        // Seed old IAT code
        m.seed64(iatSlot, 0x0L);

        OutHelper224Api.Ports ports = new OutHelper224Api.Ports() {
            @Override public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
                same(memory,m);
                check(siteRva == 0x424e643L, "direct site");
                check(ecx == 0x1c, "direct ecx");
                check(rdx == actualRDX, "direct rdx");
                check(r8 == actualR8, "direct r8");
                check(r9 == actualR9, "direct r9");
                check(rdx == r9, "rdx r9 alias");
                log.add("P call424e448 site=424e643 ecx=1c rdx=" + h(rdx) + " r8=" + h(r8) + " r9=" + h(r9));

                // Opaque effects
                memory.writeInt64(iatSlot, 0xe23456789abcdef0L);
                memory.writeInt32(rdx, 0x87654321);
                int readBack = memory.readInt32(r9);
                check(readBack == 0x87654321, "opaque readback");

                return 0xf123456700000000L;
            }
            @Override public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, long rcx, long rdx) {
                same(memory,m);
                check(siteRva == 0x424e65cL, "tail site");
                check(actualTarget == 0xe23456789abcdef0L, "tail target");
                check(liveRax == 0xf123456700000000L, "tail liveRax");
                check(rcx == -6L, "tail rcx");
                check(rdx == entryRcx, "tail rdx");
                log.add("P tail43dbba8 site=424e65c target=" + h(actualTarget) + " rax=" + h(liveRax) + " rcx=" + h(rcx) + " rdx=" + h(rdx));
                return 0x80000000ABCDEF12L;
            }
        };

        long result = OutHelper424E620.execute(m, ports, new OutHelper224Api.Input(base, entryRcx));

        // Verify final state
        equal(result, 0x80000000ABCDEF12L, "execute return");
        equal(m.peek(iatSlot, 8), 0xe23456789abcdef0L, "final IAT");
        equal(m.peek(actualRDX, 4), 0x87654321L, "final RDX data");
        equal(m.peek(actualR8, 4), 0xdeadbeefL, "R8 canary unchanged");
        equal(m.peek(entryRcx, 4), 0xcafed00dL, "entryRcx slot unchanged");
        equal(m.peek(entryRcx - 1, 1), 0x11L, "entryRcx before canary");
        equal(m.peek(entryRcx + 4, 1), 0x22L, "entryRcx after canary");
        equal(m.peek(actualR8 - 1, 1), 0x33L, "R8 before canary");
        equal(m.peek(actualRDX + 4, 1), 0x66L, "RDX after canary");

        events(log,
            "P call424e448 site=424e643 ecx=1c rdx=" + h(actualRDX) + " r8=" + h(actualR8) + " r9=" + h(actualR9),
            "W64@" + h(iatSlot) + "=" + h(0xe23456789abcdef0L),
            "W32@" + h(actualRDX) + "=" + h(0x87654321L),
            "R32@" + h(actualR9) + "=" + h(0x87654321L),
            "R64@" + h(iatSlot) + "=" + h(0xe23456789abcdef0L),
            "P tail43dbba8 site=424e65c target=" + h(0xe23456789abcdef0L) + " rax=" + h(0xf123456700000000L) + " rcx=" + h(-6L) + " rdx=" + h(entryRcx)
        );

        done("nonzero");
    }
}
