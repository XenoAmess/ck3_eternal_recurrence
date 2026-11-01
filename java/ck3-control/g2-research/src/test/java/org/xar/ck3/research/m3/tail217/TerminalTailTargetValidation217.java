package org.xar.ck3.research.m3.tail217;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal207.Terminal4232CF4;
import org.xar.ck3.research.m3.tail212.TerminalTailBinding212;
import org.xar.ck3.research.m3.tail212.TerminalTail212Api;
import org.xar.ck3.research.m3.tail212.Tail4242354;

/** Independent finite owner witness from original188/12/86 and exact supplied-storage APIs. */
public final class TerminalTailTargetValidation217 {
    private TerminalTailTargetValidation217() { }
    private static int checks, memoryEvents, portEvents;
    private static String h(long value) { return Long.toHexString(value); }
    private static String i(int value) { return Integer.toUnsignedString(value, 16); }
    private static void check(boolean condition, String label) { checks++; if (!condition) throw new AssertionError(label); }
    private static void equal(long actual, long expected, String label) { check(actual == expected, label + ": " + h(actual) + " != " + h(expected)); }
    private static void events(List<String> actual, String... expected) { check(actual.equals(List.of(expected)), "complete events " + actual); }
    private static void port(List<String> events, String value) { portEvents++; events.add(value); }
    private static void sameBytes(Mem actual, Map<Long, Byte> expected, String label) { check(actual.bytes.equals(expected), label); }
    private static void normal(TerminalTailTarget217Api.Outcome actual, long expected) {
        check(actual instanceof TerminalTailTarget217Api.NormalReturn, "NormalReturn expected");
        equal(((TerminalTailTarget217Api.NormalReturn) actual).rawRax(), expected, "full64 normal RAX");
    }
    private static void expectIAE(Runnable action, String label) {
        try { action.run(); } catch (IllegalArgumentException expected) { checks++; return; }
        throw new AssertionError(label);
    }
    private static void expectUOE(Runnable action, String label) {
        try { action.run(); } catch (UnsupportedOperationException expected) { checks++; return; }
        throw new AssertionError(label);
    }

    private static final class Mem implements TerminalTailTarget217Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<String> events;
        private Mem(List<String> events) { this.events = events; }
        private void seed(long address, long value, int width) { for (int n=0; n<width; n++) bytes.put(address+n, (byte)(value >>> (8*n))); }
        private void seed8(long a, int v) { seed(a,v,1); }
        private void seed16(long a, int v) { seed(a,v,2); }
        private void seed32(long a, int v) { seed(a,v,4); }
        private void seed64(long a, long v) { seed(a,v,8); }
        private Map<Long, Byte> snapshot() { return new HashMap<>(bytes); }
        private long peek(long address, int width) {
            long value=0;
            for (int n=0; n<width; n++) {
                Byte part=bytes.get(address+n);
                if (part==null) throw new AssertionError("unmapped byte "+h(address+n));
                value|=(long)(part&255) << (8*n);
            }
            return value;
        }
        private void record(String operation, long a, long v) { memoryEvents++; events.add(operation+":"+h(a)+":"+h(v)); }
        @Override public long readPointer(long a) { long v=peek(a,8); record("R64",a,v); return v; }
        @Override public int readInt32(long a) { int v=(int)peek(a,4); memoryEvents++; events.add("R32:"+h(a)+":"+i(v)); return v; }
        @Override public int readUnsigned8(long a) { int v=(int)peek(a,1); record("R8",a,v); return v; }
        @Override public int readUnsigned16(long a) { int v=(int)peek(a,2); record("R16",a,v); return v; }
        @Override public void writeInt32(long a, int v) { seed(a,v,4); memoryEvents++; events.add("W32:"+h(a)+":"+i(v)); }
        @Override public void writeInt64(long a, long v) { seed(a,v,8); record("W64",a,v); }
        @Override public void write8(long a, int v) { seed(a,v,1); record("W8",a,v&255L); }
    }
    private static class LeafPorts implements TerminalTailTarget217Api.Ports {
        @Override public long call43da620(TerminalTailTarget217Api.Memory m,long site,long code,int ecx) { throw new AssertionError("unexpected IAT"); }
        @Override public void call42422d0(TerminalTailTarget217Api.Memory m,long site,int ecx) { throw new AssertionError("unexpected header action"); }
        @Override public long call42420c0(TerminalTailTarget217Api.Memory m,long site,long rcx,long rdx,long r8,long r9) { throw new AssertionError("unexpected helper"); }
        @Override public void call4242284(TerminalTailTarget217Api.Memory m,long site,int ecx) { throw new AssertionError("unexpected terminal"); }
    }
    private static class TailPorts implements TerminalTail212Api.Ports {
        @Override public long tail42421c8(Terminal207Api.Memory m,long site,long rcx,int edx,int r8d) { throw new AssertionError("unexpected legacy tail"); }
        @Override public long tail42421c8(Terminal207Api.Memory m,long site,long rcx,int edx,int r8d,long entry) { throw new AssertionError("unexpected context tail"); }
    }

    private static class TerminalPorts implements Terminal207Api.Ports {
        @Override public long call4246fb4(Terminal207Api.Memory m,long site) { throw new AssertionError("unexpected first2"); }
        @Override public long call4246fb4(Terminal207Api.Memory m,long site,long entry) { throw new AssertionError("unexpected first3"); }
        @Override public void call4247004(Terminal207Api.Memory m,long site,int ecx) { throw new AssertionError("unexpected handler3"); }
        @Override public void call4247004(Terminal207Api.Memory m,long site,int ecx,long entry) { throw new AssertionError("unexpected handler4"); }
        @Override public int call43da258(Terminal207Api.Memory m,long site,long code,int ecx) { throw new AssertionError("unexpected trace IAT"); }
        @Override public void call423283c(Terminal207Api.Memory m,long site,int ecx,int edx,int r8d) { throw new AssertionError("unexpected signal5"); }
        @Override public void call423283c(Terminal207Api.Memory m,long site,int ecx,int edx,int r8d,long entry) { throw new AssertionError("unexpected signal6"); }
        @Override public void call4242354(Terminal207Api.Memory m,long site,int ecx) { throw new AssertionError("unexpected final3"); }
        @Override public void call4242354(Terminal207Api.Memory m,long site,int ecx,long entry) { throw new AssertionError("unexpected final4"); }
    }

    private static void assertHelper(Mem expectedMemory, TerminalTailTarget217Api.Memory actualMemory,
            long site, long rcx, long rdx, long r8, long r9,
            long expectedRcx, long expectedRdx, long expectedR8, long expectedR9,
            long firstPointer, long secondPointer, long thirdPointer) {
        check(actualMemory == expectedMemory, "helper identical Memory");
        equal(site, 0x4242266L, "helper actual site");
        equal(rcx, expectedRcx, "helper actual RCX"); equal(rdx, expectedRdx, "helper actual RDX");
        equal(r8, expectedR8, "helper actual R8"); equal(r9, expectedR9, "helper actual R9");
        equal(expectedMemory.peek(expectedRdx, 4), 2, "helper source DWORD at RDX");
        equal(expectedMemory.peek(expectedR9, 4), 2, "helper source DWORD at R9");
        equal(expectedMemory.peek(expectedR8, 8), firstPointer, "pointer array first");
        equal(expectedMemory.peek(expectedR8 + 8, 8), secondPointer, "pointer array second");
        equal(expectedMemory.peek(expectedR8 + 16, 8), thirdPointer, "pointer array third");
        check(!expectedMemory.bytes.containsKey(expectedRcx), "unwritten helper RCX storage not fabricated");
    }

    private static void entryBranchTrap() {
        List<String> ev = new ArrayList<>(); Mem m = new Mem(ev);
        m.seed64(0x1010L, 0x1122334455667788L); m.seed64(0x1018L, 0xA1B2C3D4E5F60718L);
        m.seed64(0x1020L, 0x8877665544332211L);
        Map<Long, Byte> before = m.snapshot();
        LeafPorts ports = new LeafPorts() {
            @Override public long call42420c0(TerminalTailTarget217Api.Memory a,long site,long rcx,long rdx,long r8,long r9) {
                assertHelper(m,a,site,rcx,rdx,r8,r9,0xFC8L,0xFD0L,0xFD8L,0xFCCL,0x1010L,0x1018L,0x1020L);
                equal(m.peek(0x1018L,4), 0x80000000L, "entry nonzero home before helper");
                port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":123456789abcdef");
                m.seed32(0x1018L,0); return 0x0123456789ABCDEFL;
            }
            @Override public void call4242284(TerminalTailTarget217Api.Memory a,long site,int ecx) {
                check(a==m,"entry terminal Memory"); equal(site,0x424227EL,"entry terminal site");
                equal(ecx,0x89ABCDEF,"entry original ECX"); port(ev,"TERMINAL:"+h(site)+":"+i(ecx));
            }
        };
        TerminalTailTarget217Api.Outcome result = TerminalTailTarget217.execute(m,ports,
                new TerminalTailTarget217Api.Input(0x10000000L,0x89ABCDEF,0xFEDCBA98,0x80000000,new TerminalTailTarget217Api.Scratch(0x1000L)));
        check(result==TerminalTailTarget217Api.Trap.INT3_4242283,"entry register skips IAT but freshhome0 traps");
        events(ev,"W32:1018:80000000","W32:1010:fedcba98","W8:1020:0",
                "W64:fd8:1010","W64:fe0:1018","W64:fe8:1020","W32:fcc:2","W32:fd0:2",
                "HELPER:4242266:fc8:fd0:fd8:fcc:123456789abcdef","R32:1018:0","TERMINAL:424227e:89abcdef");
        Mem expected = new Mem(new ArrayList<>()); expected.bytes.putAll(before);
        expected.seed64(0x1010L,0x11223344FEDCBA98L); expected.seed64(0x1018L,0xA1B2C3D400000000L);
        expected.seed64(0x1020L,0x8877665544332200L);
        expected.seed64(0xFD8L,0x1010L); expected.seed64(0xFE0L,0x1018L); expected.seed64(0xFE8L,0x1020L);
        expected.seed32(0xFCCL,2); expected.seed32(0xFD0L,2);
        sameBytes(m,expected.bytes,"entry trap all bytes / W8 and DWORD high canaries");
    }
    private static void signedHeaderNormal() {
        List<String> ev = new ArrayList<>(); Mem m = new Mem(ev);
        m.seed64(0x2010L,0xAABBCCDDEEFF0011L); m.seed64(0x2018L,0x99AABBCCDDEEFF00L);
        m.seed64(0x2020L,0x0102030405060708L); m.seed64(0x143DA620L,0xFEDCBA9876543210L);
        m.seed16(0x100000000L,0x5A4D); m.seed32(0x10000003CL,0xFFFFFF00);
        m.seed32(0xFFFFFF00L,0x4550); m.seed16(0xFFFFFF18L,0x20B);
        m.seed32(0xFFFFFF84L,0x80000000); m.seed32(0xFFFFFFF8L,0x80000001);
        Map<Long, Byte> before = m.snapshot();
        LeafPorts ports = new LeafPorts() {
            @Override public long call43da620(TerminalTailTarget217Api.Memory a,long site,long code,int ecx) {
                check(a==m,"header IAT Memory"); equal(site,0x42421E7L,"header IAT site");
                equal(code,0xFEDCBA9876543210L,"header IAT code"); equal(ecx,0,"header IAT ECX");
                port(ev,"IAT:"+h(site)+":"+h(code)+":"+i(ecx)+":100000000"); return 0x100000000L;
            }
            @Override public void call42422d0(TerminalTailTarget217Api.Memory a,long site,int ecx) {
                check(a==m,"header action Memory"); equal(site,0x424222AL,"header action site");
                equal(ecx,0x80000001,"header original ECX"); port(ev,"D0:"+h(site)+":"+i(ecx));
                m.seed32(0x2010L,0x55667788); m.seed32(0x2018L,0x12345678);
            }
            @Override public long call42420c0(TerminalTailTarget217Api.Memory a,long site,long rcx,long rdx,long r8,long r9) {
                assertHelper(m,a,site,rcx,rdx,r8,r9,0x1FC8L,0x1FD0L,0x1FD8L,0x1FCCL,0x2010L,0x2018L,0x2020L);
                equal(m.peek(0x2010L,4),0x55667788L,"action changed supplied EDX home");
                equal(m.peek(0x2018L,4),0x12345678L,"action changed R8 home");
                port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":f123456789abcdef");
                m.seed32(0x2018L,0x80000001); return 0xF123456789ABCDEFL;
            }
        };
        normal(TerminalTailTarget217.execute(m,ports,new TerminalTailTarget217Api.Input(
                0x10000000L,0x80000001,0x11223344,0,new TerminalTailTarget217Api.Scratch(0x2000L))),0xF123456789ABCDEFL);
        events(ev,"W32:2018:0","W32:2010:11223344","R64:143da620:fedcba9876543210",
                "IAT:42421e7:fedcba9876543210:0:100000000","R16:100000000:5a4d","R32:10000003c:ffffff00",
                "R32:ffffff00:4550","R16:ffffff18:20b","R32:ffffff84:80000000","R32:fffffff8:80000001",
                "D0:424222a:80000001","W8:2020:0","W64:1fd8:2010","W64:1fe0:2018","W64:1fe8:2020",
                "W32:1fcc:2","W32:1fd0:2","HELPER:4242266:1fc8:1fd0:1fd8:1fcc:f123456789abcdef","R32:2018:80000001");
        Mem expected = new Mem(new ArrayList<>()); expected.bytes.putAll(before);
        expected.seed64(0x2010L,0xAABBCCDD55667788L); expected.seed64(0x2018L,0x99AABBCC80000001L);
        expected.seed64(0x2020L,0x0102030405060700L);
        expected.seed64(0x1FD8L,0x2010L); expected.seed64(0x1FE0L,0x2018L); expected.seed64(0x1FE8L,0x2020L);
        expected.seed32(0x1FCCL,2); expected.seed32(0x1FD0L,2);
        sameBytes(m,expected.bytes,"header all final fields and unchanged source validation bytes");
    }
    private static void directoryBoundary() {
        List<String> ev = new ArrayList<>(); Mem m = new Mem(ev);
        m.seed64(0x3010L,0x1234567890ABCDEFL); m.seed64(0x3018L,0x2233445566778899L);
        m.seed64(0x3020L,0xAABBCCDDEEFF0011L); m.seed64(0x143DA620L,0x8765432100ABCDEFL);
        m.seed16(0x200000000L,0x5A4D); m.seed32(0x20000003CL,0x80);
        m.seed32(0x200000080L,0x4550); m.seed16(0x200000098L,0x20B); m.seed32(0x200000104L,0xE);
        check(!m.bytes.containsKey(0x200000178L),"directory lastfield deliberately unmapped");
        Map<Long, Byte> before = m.snapshot();
        LeafPorts ports = new LeafPorts() {
            @Override public long call43da620(TerminalTailTarget217Api.Memory a,long site,long code,int ecx) {
                check(a==m,"boundary IAT Memory"); equal(site,0x42421E7L,"boundary IAT site");
                equal(code,0x8765432100ABCDEFL,"boundary IAT code"); equal(ecx,0,"boundary IAT ECX");
                port(ev,"IAT:"+h(site)+":"+h(code)+":"+i(ecx)+":200000000"); return 0x200000000L;
            }
            @Override public long call42420c0(TerminalTailTarget217Api.Memory a,long site,long rcx,long rdx,long r8,long r9) {
                assertHelper(m,a,site,rcx,rdx,r8,r9,0x2FC8L,0x2FD0L,0x2FD8L,0x2FCCL,0x3010L,0x3018L,0x3020L);
                port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":80000001fedcba98");
                m.seed32(0x3018L,1); return 0x80000001FEDCBA98L;
            }
        };
        normal(TerminalTailTarget217.execute(m,ports,new TerminalTailTarget217Api.Input(
                0x10000000L,0x7FFFFFFF,0xFFFFFFFE,0,new TerminalTailTarget217Api.Scratch(0x3000L))),0x80000001FEDCBA98L);
        events(ev,"W32:3018:0","W32:3010:fffffffe","R64:143da620:8765432100abcdef",
                "IAT:42421e7:8765432100abcdef:0:200000000","R16:200000000:5a4d","R32:20000003c:80",
                "R32:200000080:4550","R16:200000098:20b","R32:200000104:e",
                "W8:3020:0","W64:2fd8:3010","W64:2fe0:3018","W64:2fe8:3020","W32:2fcc:2","W32:2fd0:2",
                "HELPER:4242266:2fc8:2fd0:2fd8:2fcc:80000001fedcba98","R32:3018:1");
        Mem expected = new Mem(new ArrayList<>()); expected.bytes.putAll(before);
        expected.seed64(0x3010L,0x12345678FFFFFFFEL); expected.seed64(0x3018L,0x2233445500000001L);
        expected.seed64(0x3020L,0xAABBCCDDEEFF0000L);
        expected.seed64(0x2FD8L,0x3010L); expected.seed64(0x2FE0L,0x3018L); expected.seed64(0x2FE8L,0x3020L);
        expected.seed32(0x2FCCL,2); expected.seed32(0x2FD0L,2);
        sameBytes(m,expected.bytes,"boundary exact bytes, F8 still unobserved");
    }
    private static void bindingPerCall() {
        List<String> ev = new ArrayList<>(); Mem m = new Mem(ev);
        m.seed8(0x1542F208L,0); m.seed64(0x143DA620L,0xF123456789ABCDEFL);
        m.seed64(0x5010L,0xAABBCCDD55667788L); m.seed64(0x5018L,0x1122334499AABBCCL); m.seed64(0x5020L,0xDEADBEEF01234567L);
        m.seed64(0x7010L,0x8877665544332211L); m.seed64(0x7018L,0x99AABBCCDDEEFF00L); m.seed64(0x7020L,0x0102030405060708L);
        Map<Long, Byte> before = m.snapshot(); int[] completed = {0};
        LeafPorts child = new LeafPorts() {
            @Override public long call43da620(TerminalTailTarget217Api.Memory a,long site,long code,int ecx) {
                check(a==m,"chain IAT Memory"); equal(site,0x42421E7L,"chain IAT site");
                equal(code,0xF123456789ABCDEFL,"chain fresh IAT code"); equal(ecx,0,"chain IAT ECX");
                port(ev,"IAT:"+h(site)+":"+h(code)+":"+i(ecx)+":0"); return 0;
            }
            @Override public long call42420c0(TerminalTailTarget217Api.Memory a,long site,long rcx,long rdx,long r8,long r9) {
                if (completed[0]==0) {
                    assertHelper(m,a,site,rcx,rdx,r8,r9,0x4FC8L,0x4FD0L,0x4FD8L,0x4FCCL,0x5010L,0x5018L,0x5020L);
                    equal(m.peek(0x5010L,4),2,"chain1 tail EDX2"); equal(m.peek(0x5018L,4),0,"chain1 initial R8zero");
                    port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":fedcba9876543210");
                    m.seed32(0x5018L,1); completed[0]++; return 0xFEDCBA9876543210L;
                }
                equal(completed[0],1,"chain exactly two helper calls");
                assertHelper(m,a,site,rcx,rdx,r8,r9,0x6FC8L,0x6FD0L,0x6FD8L,0x6FCCL,0x7010L,0x7018L,0x7020L);
                equal(m.peek(0x7010L,4),2,"chain2 tail EDX2"); equal(m.peek(0x7018L,4),0,"chain2 initial R8zero");
                port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":123456789abcdef");
                completed[0]++; return 0x0123456789ABCDEFL;
            }
            @Override public void call4242284(TerminalTailTarget217Api.Memory a,long site,int ecx) {
                check(a==m,"chain terminal Memory"); equal(completed[0],2,"terminal only second trace");
                equal(site,0x424227EL,"chain terminal site"); equal(ecx,3,"chain terminal original ECX");
                port(ev,"TERMINAL:"+h(site)+":"+i(ecx));
            }
        };
        TerminalPorts fallback = new TerminalPorts() {
            @Override public long call4246fb4(Terminal207Api.Memory a,long site,long entry) {
                check(a==m,"chain first Memory"); equal(site,0x4232CF8L,"chain first site");
                equal(entry,completed[0]==0?0x5000L:0x7000L,"trace actual percall T-30");
                port(ev,"FIRST:"+h(site)+":"+h(entry)); return 0;
            }
        };
        TerminalTail212Api.Ports leafBound = TerminalTailTargetBinding217.bind(0x10000000L,m,child,new TailPorts());
        Terminal207Api.Ports terminalBound = TerminalTailBinding212.bind(m,leafBound,fallback);
        events(ev);
        check(Terminal4232CF4.trace(m,terminalBound,0x10000000L,0x5030L)==Terminal207Api.Stop.INT3_4232D49,"normal leaf follows void consumer to software Stop");
        events(ev,"FIRST:4232cf8:5000","R8:1542f208:0","W32:5018:0","W32:5010:2",
                "R64:143da620:f123456789abcdef","IAT:42421e7:f123456789abcdef:0:0",
                "W8:5020:0","W64:4fd8:5010","W64:4fe0:5018","W64:4fe8:5020","W32:4fcc:2","W32:4fd0:2",
                "HELPER:4242266:4fc8:4fd0:4fd8:4fcc:fedcba9876543210","R32:5018:1");
        Mem expected = new Mem(new ArrayList<>()); expected.bytes.putAll(before);
        expected.seed64(0x5010L,0xAABBCCDD00000002L); expected.seed64(0x5018L,0x1122334400000001L);
        expected.seed64(0x5020L,0xDEADBEEF01234500L); expected.seed64(0x4FD8L,0x5010L);
        expected.seed64(0x4FE0L,0x5018L); expected.seed64(0x4FE8L,0x5020L); expected.seed32(0x4FCCL,2); expected.seed32(0x4FD0L,2);
        sameBytes(m,expected.bytes,"first T frame only, second frame input unchanged");
        ev.clear();
        expectUOE(() -> Terminal4232CF4.trace(m,terminalBound,0x10000000L,0x7030L),"second T leaf trap must stop actual trace chain");
        events(ev,"FIRST:4232cf8:7000","R8:1542f208:0","W32:7018:0","W32:7010:2",
                "R64:143da620:f123456789abcdef","IAT:42421e7:f123456789abcdef:0:0",
                "W8:7020:0","W64:6fd8:7010","W64:6fe0:7018","W64:6fe8:7020","W32:6fcc:2","W32:6fd0:2",
                "HELPER:4242266:6fc8:6fd0:6fd8:6fcc:123456789abcdef","R32:7018:0","TERMINAL:424227e:3");
        expected.seed64(0x7010L,0x8877665500000002L); expected.seed64(0x7018L,0x99AABBCC00000000L);
        expected.seed64(0x7020L,0x0102030405060700L); expected.seed64(0x6FD8L,0x7010L);
        expected.seed64(0x6FE0L,0x7018L); expected.seed64(0x6FE8L,0x7020L); expected.seed32(0x6FCCL,2); expected.seed32(0x6FD0L,2);
        sameBytes(m,expected.bytes,"same bound two T exact frames, first frame preserved"); equal(completed[0],2,"two chain leaf consumers");
    }
    private static void bindingTrap() {
        List<String> ev = new ArrayList<>(); Mem m = new Mem(ev); Mem foreign = new Mem(ev);
        m.seed64(0x4010L,0x1122334455667788L); m.seed64(0x4018L,0x99AABBCCDDEEFF00L); m.seed64(0x4020L,0x1234567890ABCDEFL);
        m.seed64(0x8010L,0x8877665544332211L); m.seed64(0x8018L,0xAABBCCDDEEFF0011L); m.seed64(0x8020L,0xFEDCBA9876543210L);
        foreign.seed64(0xB000L,0x0102030405060708L);
        Map<Long, Byte> before=m.snapshot(), foreignBefore=foreign.snapshot();
        LeafPorts child = new LeafPorts() {
            @Override public long call42420c0(TerminalTailTarget217Api.Memory a,long site,long rcx,long rdx,long r8,long r9) {
                if (rcx==0x7FC8L) {
                    assertHelper(m,a,site,rcx,rdx,r8,r9,0x7FC8L,0x7FD0L,0x7FD8L,0x7FCCL,0x8010L,0x8018L,0x8020L);
                    port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":8877665544332211");
                    m.seed32(0x8018L,1); return 0x8877665544332211L;
                }
                assertHelper(m,a,site,rcx,rdx,r8,r9,0x3FC8L,0x3FD0L,0x3FD8L,0x3FCCL,0x4010L,0x4018L,0x4020L);
                port(ev,"HELPER:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(r8)+":"+h(r9)+":fedcba9876543210");
                m.seed32(0x4018L,0); return 0xFEDCBA9876543210L;
            }
            @Override public void call4242284(TerminalTailTarget217Api.Memory a,long site,int ecx) {
                check(a==m,"binding terminal Memory"); equal(site,0x424227EL,"binding terminal site");
                equal(ecx,0x89ABCDEF,"binding casts received RCX low32"); port(ev,"TERMINAL:"+h(site)+":"+i(ecx));
            }
        };
        TailPorts fallback = new TailPorts() {
            @Override public long tail42421c8(Terminal207Api.Memory a,long site,long rcx,int edx,int r8d) {
                check(a==foreign,"legacy exact callback Memory"); equal(site,0x76543210L,"legacy site");
                equal(rcx,0xFEDCBA9876543210L,"legacy full64 RCX"); equal(edx,0x89ABCDEF,"legacy EDX"); equal(r8d,0x80000000,"legacy R8D");
                port(ev,"LEGACY:"+h(site)+":"+h(rcx)+":"+i(edx)+":"+i(r8d)); return 0x80000001FEDCBA98L;
            }
        };
        TerminalTail212Api.Ports bound=TerminalTailTargetBinding217.bind(0x10000000L,m,child,fallback);
        events(ev);
        expectIAE(() -> bound.tail42421c8(foreign,0x424235BL,3,2,0,0x4000L),"new6 foreign before effects");
        events(ev); sameBytes(m,before,"foreign captured unchanged"); sameBytes(foreign,foreignBefore,"foreign unchanged");
        expectIAE(() -> bound.tail42421c8(m,0x424235CL,3,2,0,0x4000L),"new6 wrong site before effects");
        events(ev); sameBytes(m,before,"site captured unchanged"); sameBytes(foreign,foreignBefore,"site foreign unchanged");
        equal(bound.tail42421c8(foreign,0x76543210L,0xFEDCBA9876543210L,0x89ABCDEF,0x80000000),0x80000001FEDCBA98L,"legacy exact full64 return");
        events(ev,"LEGACY:76543210:fedcba9876543210:89abcdef:80000000"); sameBytes(m,before,"legacy zero leaf effects"); sameBytes(foreign,foreignBefore,"legacy zero Memory effects");
        ev.clear();
        equal(bound.tail42421c8(m,0x424235BL,0xAABBCCDD89ABCDEFL,0x7FFFFFFF,0x80000000,0x8000L),0x8877665544332211L,"new6 full64 normal RAX return");
        events(ev,"W32:8018:80000000","W32:8010:7fffffff","W8:8020:0","W64:7fd8:8010","W64:7fe0:8018","W64:7fe8:8020",
                "W32:7fcc:2","W32:7fd0:2","HELPER:4242266:7fc8:7fd0:7fd8:7fcc:8877665544332211","R32:8018:1");
        Mem expected=new Mem(new ArrayList<>()); expected.bytes.putAll(before);
        expected.seed64(0x8010L,0x887766557FFFFFFFL); expected.seed64(0x8018L,0xAABBCCDD00000001L); expected.seed64(0x8020L,0xFEDCBA9876543200L);
        expected.seed64(0x7FD8L,0x8010L); expected.seed64(0x7FE0L,0x8018L); expected.seed64(0x7FE8L,0x8020L); expected.seed32(0x7FCCL,2); expected.seed32(0x7FD0L,2);
        sameBytes(m,expected.bytes,"new6 normal exact bytes"); ev.clear();
        expectUOE(() -> bound.tail42421c8(m,0x424235BL,0xAABBCCDD89ABCDEFL,0x7FFFFFFF,0x80000000,0x4000L),"binding leaf Trap maps to UOE");
        events(ev,"W32:4018:80000000","W32:4010:7fffffff","W8:4020:0","W64:3fd8:4010","W64:3fe0:4018","W64:3fe8:4020",
                "W32:3fcc:2","W32:3fd0:2","HELPER:4242266:3fc8:3fd0:3fd8:3fcc:fedcba9876543210","R32:4018:0","TERMINAL:424227e:89abcdef");
        expected.seed64(0x4010L,0x112233447FFFFFFFL); expected.seed64(0x4018L,0x99AABBCC00000000L); expected.seed64(0x4020L,0x1234567890ABCD00L);
        expected.seed64(0x3FD8L,0x4010L); expected.seed64(0x3FE0L,0x4018L); expected.seed64(0x3FE8L,0x4020L); expected.seed32(0x3FCCL,2); expected.seed32(0x3FD0L,2);
        sameBytes(m,expected.bytes,"binding trap exact bytes and normal frame preserved"); sameBytes(foreign,foreignBefore,"binding never touches foreign object");
    }

    public static void main(String[] args) {
        entryBranchTrap(); signedHeaderNormal(); directoryBoundary(); bindingPerCall(); bindingTrap();
        equal(memoryEvents,80,"finite source Memory events"); equal(portEvents,18,"finite source port events");
        System.out.println("TerminalTailTargetValidation217 groups=5 events="+(memoryEvents+portEvents)+" memory="+memoryEvents+" ports="+portEvents+" checks="+checks+" software_only=true");
    }
}
