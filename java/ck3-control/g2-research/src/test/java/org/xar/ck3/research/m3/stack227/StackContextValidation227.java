package org.xar.ck3.research.m3.stack227;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class StackContextValidation227 {
    private StackContextValidation227() { }
    @FunctionalInterface
    private interface Child {
        long run(Fixture f, long rcx, long rdx, long r8, long r9);
    }
    private record Step(String kind, long[] values) { }
    private static final class Fixture implements NativeTaskMemory, StackContext227Api.Ports {
        private final Map<Long,Integer> bytes = new HashMap<>();
        private final List<Step> expected = new ArrayList<>();
        private final Child child;
        private int cursor;
        private int producerWrites;
        private int producerReads;
        private int childMemory;
        private int calls;
        private boolean inChild;
        Fixture(Child child) { this.child=child; }
        void expect(String kind, long... values) { expected.add(new Step(kind,values.clone())); }
        void seed(long address, int width, long value) {
            for (int i=0;i<width;i++) bytes.put(address+i,(int)(value >>> (8*i)) & 255);
        }
        long peek(long address, int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Integer b=bytes.get(address+i);
                if(b==null) throw new AssertionError("unseeded byte "+Long.toHexString(address+i));
                value |= ((long)b) << (8*i);
            }
            return value;
        }
        private void take(String kind, long... values) {
            if(cursor==expected.size()) throw new AssertionError("extra event "+kind);
            Step wanted=expected.get(cursor++);
            if(!wanted.kind().equals(kind) || !Arrays.equals(wanted.values(),values))
                throw new AssertionError("event "+(cursor-1)+" wanted "+wanted.kind()+Arrays.toString(wanted.values())+" got "+kind+Arrays.toString(values));
        }
        private String phase() { return inChild ? "C." : "P."; }
        private void count(boolean write) {
            if(inChild) childMemory++;
            else if(write) producerWrites++;
            else producerReads++;
        }
        @Override public long readPointer(long address) {
            long value=peek(address,8); take(phase()+"R64",address,value); count(false); return value;
        }
        @Override public int readInt32(long address) {
            int value=(int)peek(address,4); take(phase()+"R32",address,Integer.toUnsignedLong(value)); count(false); return value;
        }
        @Override public void writeInt32(long address,int value) {
            take(phase()+"W32",address,Integer.toUnsignedLong(value)); count(true); seed(address,4,Integer.toUnsignedLong(value));
        }
        @Override public void writeInt64(long address,long value) {
            take(phase()+"W64",address,value); count(true); seed(address,8,value);
        }
        @Override public long call424db74(NativeTaskMemory memory,long site,long rcx,long rdx,long r8,long r9) {
            if(memory!=this || inChild) throw new AssertionError("memory identity / reentry");
            take("CALL",site,rcx,rdx,r8,r9); calls++; inChild=true;
            long value=child.run(this,rcx,rdx,r8,r9); inChild=false; return value;
        }
        void exhausted() {
            if(cursor!=expected.size()) throw new AssertionError("events not exhausted "+cursor+"/"+expected.size());
            equal(4,producerWrites,"producer writes");
            equal(0,producerReads,"producer reads");
            equal(1,calls,"child calls");
        }
    }
    private static void equal(long expected,long actual,String label) {
        if(expected!=actual) throw new AssertionError(label+": "+Long.toHexString(expected)+" != "+Long.toHexString(actual));
    }
    private static void invoke(Fixture f,long e,long entry,long expectedReturn) {
        long actual=StackContext424DE88.execute(f,f,new StackContext227Api.Context(e,entry));
        equal(expectedReturn,actual,"full opaque RAX"); f.exhausted();
    }
    private static void scenarios227() {
        // Scene 1: Standard positive E, high entryRCX, poison E+0x10, disjoint byte canaries.
        {
            long e = 0x1000L;
            long entryRCX = 0x1234567890ABCDEFL;
            Fixture f = new Fixture((fx, rcx, rdx, r8, r9) -> {
                // Callback reads: saved entry (E+8), pointer to saved entry (E-0x18), untouched E+0x10, and the two W32 cells (E+0x18, E+0x20)
                long savedEntry = fx.readPointer(e + 8);
                long ptrToSaved = fx.readPointer(e - 0x18);
                long untouched10 = fx.readPointer(e + 0x10);
                long cell18 = fx.readPointer(e + 0x18);
                long cell20 = fx.readPointer(e + 0x20);

                // Verify callback sees expected values
                if (savedEntry != entryRCX) throw new AssertionError("savedEntry mismatch");
                if (ptrToSaved != e + 8) throw new AssertionError("ptrToSaved mismatch");
                if (untouched10 != 0xDEADBEEFCAFEBABEL) throw new AssertionError("untouched10 mismatch");
                // W32 writes only change low 4 bytes. High 4 bytes remain poison (0xFFFFFFFF).
                // So E+0x18 becomes 0xFFFFFFFF00000002, E+0x20 becomes 0xFFFFFFFF00000002
                if (cell18 != 0xFFFFFFFF00000002L) throw new AssertionError("cell18 mismatch");
                if (cell20 != 0xFFFFFFFF00000002L) throw new AssertionError("cell20 mismatch");

                // Opaque callback changes the source temp low DWORD, then observes it afresh.
                fx.writeInt32(e + 0x18, 0x11111111);
                equal(0xFFFFFFFF11111111L,fx.readPointer(e + 0x18),"mutated temp fresh");

                // Return full64 value with low32 neither 0 nor 2
                return 0x9999999999999999L;
            });

            // Seed poison for E+0x10 (entire 8 bytes)
            f.seed(e + 0x10, 8, 0xDEADBEEFCAFEBABEL);
            // Disjoint byte canaries before source slots and after the final observed cell
            f.seed(e + 0x07, 1, 0xAA); // before saved entry
            f.seed(e - 0x19, 1, 0xBB); // disjoint neighbor
            f.seed(e + 0x28, 1, 0xCC); // disjoint neighbor
            // Seed poison for E+0x18 and E+0x20 (8-byte cells before W32 overwrite)
            f.seed(e + 0x18, 8, 0xFFFFFFFFFFFFFFFFL);
            f.seed(e + 0x20, 8, 0xFFFFFFFFFFFFFFFFL);

            // Expected events:
            // P.W64 E+8 entryRCX
            // P.W64 E-0x18 E+8
            // P.W32 E+0x18 2
            // P.W32 E+0x20 2
            // CALL site, rcx, rdx, r8, r9
            // C.R64 E+8 savedEntry
            // C.R64 E-0x18 ptrToSaved
            // C.R64 E+0x10 untouched10
            // C.R64 E+0x18 cell18 (0xFFFFFFFF00000002)
            // C.R64 E+0x20 cell20 (0xFFFFFFFF00000002)
            // C.W32 E+18 followed by fresh C.R64 E+18

            f.expect("P.W64", e + 8, entryRCX);
            f.expect("P.W64", e - 0x18, e + 8);
            f.expect("P.W32", e + 0x18, 2L);
            f.expect("P.W32", e + 0x20, 2L);
            f.expect("CALL", 0x424DEB8L, e + 0x10, e + 0x20, e - 0x18, e + 0x18);
            f.expect("C.R64", e + 8, entryRCX);
            f.expect("C.R64", e - 0x18, e + 8);
            f.expect("C.R64", e + 0x10, 0xDEADBEEFCAFEBABEL);
            f.expect("C.R64", e + 0x18, 0xFFFFFFFF00000002L);
            f.expect("C.R64", e + 0x20, 0xFFFFFFFF00000002L);
            f.expect("C.W32", e + 0x18, 0x11111111L);
            f.expect("C.R64", e + 0x18, 0xFFFFFFFF11111111L);

            invoke(f,e,entryRCX,0x9999999999999999L);
            if (f.childMemory != 7) throw new AssertionError("childMemory mismatch");

            // Verify final state
            if (f.peek(e + 8, 8) != entryRCX) throw new AssertionError("E+8 final");
            if (f.peek(e - 0x18, 8) != e + 8) throw new AssertionError("E-0x18 final");
            if (f.peek(e + 0x18, 8) != 0xFFFFFFFF11111111L) throw new AssertionError("E+0x18 final");
            if (f.peek(e + 0x20, 8) != 0xFFFFFFFF00000002L) throw new AssertionError("E+0x20 final");
            if (f.peek(e + 0x10, 8) != 0xDEADBEEFCAFEBABEL) throw new AssertionError("E+0x10 preserved");
            if (f.peek(e + 0x07, 1) != 0xAA) throw new AssertionError("canary E+0x07");
            if (f.peek(e - 0x19, 1) != 0xBB) throw new AssertionError("canary E-0x19");
            if (f.peek(e + 0x28, 1) != 0xCC) throw new AssertionError("canary E+0x28");
        }

        // Scene 2: E near unsigned64 wrap boundary
        {
            long e = 0xFFFFFFFFFFFFFFF0L;
            long entryRCX = 0x0000000000000001L;
            Fixture f = new Fixture((fx, rcx, rdx, r8, r9) -> {
                long savedEntry = fx.readPointer(e + 8);
                long ptrToSaved = fx.readPointer(e - 0x18);
                long untouched10 = fx.readPointer(e + 0x10);
                long cell18 = fx.readPointer(e + 0x18);
                long cell20 = fx.readPointer(e + 0x20);

                if (savedEntry != entryRCX) throw new AssertionError("savedEntry mismatch");
                if (ptrToSaved != e + 8) throw new AssertionError("ptrToSaved mismatch");
                if (untouched10 != 0x1234567890ABCDEFL) throw new AssertionError("untouched10 mismatch");
                if (cell18 != 0xFFFFFFFF00000002L) throw new AssertionError("cell18 mismatch");
                if (cell20 != 0xFFFFFFFF00000002L) throw new AssertionError("cell20 mismatch");

                fx.writeInt32(e + 0x18, 0x22222222);
                equal(0xFFFFFFFF22222222L,fx.readPointer(e + 0x18),"mutated temp fresh");
                return 0x8888888888888888L;
            });

            f.seed(e + 0x10, 8, 0x1234567890ABCDEFL);
            f.seed(e + 0x07, 1, 0x11);
            f.seed(e - 0x19, 1, 0x22);
            f.seed(e + 0x28, 1, 0x33);
            f.seed(e + 0x18, 8, 0xFFFFFFFFFFFFFFFFL);
            f.seed(e + 0x20, 8, 0xFFFFFFFFFFFFFFFFL);

            f.expect("P.W64", e + 8, entryRCX);
            f.expect("P.W64", e - 0x18, e + 8);
            f.expect("P.W32", e + 0x18, 2L);
            f.expect("P.W32", e + 0x20, 2L);
            f.expect("CALL", 0x424DEB8L, e + 0x10, e + 0x20, e - 0x18, e + 0x18);
            f.expect("C.R64", e + 8, entryRCX);
            f.expect("C.R64", e - 0x18, e + 8);
            f.expect("C.R64", e + 0x10, 0x1234567890ABCDEFL);
            f.expect("C.R64", e + 0x18, 0xFFFFFFFF00000002L);
            f.expect("C.R64", e + 0x20, 0xFFFFFFFF00000002L);
            f.expect("C.W32", e + 0x18, 0x22222222L);
            f.expect("C.R64", e + 0x18, 0xFFFFFFFF22222222L);

            invoke(f,e,entryRCX,0x8888888888888888L);
            if (f.childMemory != 7) throw new AssertionError("childMemory mismatch");

            if (f.peek(e + 8, 8) != entryRCX) throw new AssertionError("E+8 final");
            if (f.peek(e - 0x18, 8) != e + 8) throw new AssertionError("E-0x18 final");
            if (f.peek(e + 0x18, 8) != 0xFFFFFFFF22222222L) throw new AssertionError("E+0x18 final");
            if (f.peek(e + 0x20, 8) != 0xFFFFFFFF00000002L) throw new AssertionError("E+0x20 final");
            if (f.peek(e + 0x10, 8) != 0x1234567890ABCDEFL) throw new AssertionError("E+0x10 preserved");
            if (f.peek(e + 0x07, 1) != 0x11) throw new AssertionError("canary E+0x07");
            if (f.peek(e - 0x19, 1) != 0x22) throw new AssertionError("canary E-0x19");
            if (f.peek(e + 0x28, 1) != 0x33) throw new AssertionError("canary E+0x28");
        }
    }
    public static void main(String[] args) {
        scenarios227();
        System.out.println("StackContextValidation227 groups=2 sourceInvocations=2 producerWrites=8 producerReads=0 childCalls=2 callbackMemory=14 steps=24 finalCells=16");
    }

}
