package org.xar.ck3.research.m3.span228;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public final class CallbackSpanValidation228 {
    private CallbackSpanValidation228() { }
    @FunctionalInterface private interface Child {
        void call(Fixture memory,int ordinal,long target,long liveRax,CallbackSpan228Api.Arguments arguments);
    }
    private record Step(String kind,long[] values,CallbackSpan228Api.Arguments arguments) { }
    private static final class Fixture implements CallbackSpan228Api.Memory, CallbackSpan228Api.Ports {
        private final Map<Long,Integer> bytes=new HashMap<>();
        private final List<Step> expected=new ArrayList<>();
        private final Child child;
        private int cursor;
        private int producerReads;
        private int producerWrites;
        private int opaqueMemory;
        private int calls;
        private boolean inCallback;
        Fixture() { this((f,n,t,r,a)->{}); }
        Fixture(Child child) { this.child=child; }
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
        void expectCall(long site,long target,long liveRax,CallbackSpan228Api.Arguments arguments) {
            expected.add(new Step("CALL",new long[]{site,target,liveRax},arguments));
        }
        private void take(String kind,CallbackSpan228Api.Arguments arguments,long... values) {
            if(cursor==expected.size()) throw new AssertionError("extra "+kind+Arrays.toString(values));
            Step wanted=expected.get(cursor++);
            if(!wanted.kind().equals(kind) || !Arrays.equals(wanted.values(),values) || !Objects.equals(wanted.arguments(),arguments))
                throw new AssertionError("step "+(cursor-1)+" wanted "+wanted.kind()+Arrays.toString(wanted.values())+"/"+wanted.arguments()+" got "+kind+Arrays.toString(values)+"/"+arguments);
        }
        @Override public long readPointer(long address) {
            long value=peek64(address);
            take(inCallback?"C.R64":"P.R64",null,address,value);
            if(inCallback) opaqueMemory++; else producerReads++;
            return value;
        }
        @Override public void writeInt64(long address,long value) {
            take(inCallback?"C.W64":"P.W64",null,address,value);
            if(inCallback) opaqueMemory++; else producerWrites++;
            seed64(address,value);
        }
        @Override public int readInt32(long address) { throw new AssertionError("unexpected R32"); }
        @Override public void writeInt32(long address,int value) { throw new AssertionError("unexpected W32"); }
        @Override public int readUnsigned8(long address) { throw new AssertionError("unexpected R8"); }
        @Override public int readUnsigned16(long address) { throw new AssertionError("unexpected R16"); }
        @Override public void write8(long address,int value) { throw new AssertionError("unexpected W8"); }
        @Override public void exchangeInt32(long address,int value) { throw new AssertionError("unexpected X32"); }
        @Override public void call43dbba8(CallbackSpan228Api.Memory memory,long site,long target,long liveRax,CallbackSpan228Api.Arguments arguments) {
            if(memory!=this || inCallback) throw new AssertionError("identity/reentry");
            take("CALL",arguments,site,target,liveRax); calls++; inCallback=true;
            try { child.call(this,calls,target,liveRax,arguments); }
            finally { inCallback=false; }
        }
        void done(int reads,int opaque,int ports) {
            if(cursor!=expected.size()) throw new AssertionError("not exhausted "+cursor+"/"+expected.size());
            equal(reads,producerReads,"target R64"); equal(0,producerWrites,"target writes");
            equal(opaque,opaqueMemory,"callback Memory"); equal(ports,calls,"opaque calls");
        }
    }
    private static void equal(long expected,long actual,String message) {
        if(expected!=actual) throw new AssertionError(message+": "+Long.toHexString(expected)+" != "+Long.toHexString(actual));
    }
    private static void invoke(Fixture memory,long base,long start,long end) {
        CallbackSpan424E1AC.execute(memory,memory,new CallbackSpan228Api.Input(base,start,end));
    }
    private static void boundaries228() {
        // 1. Equal interval: count 0, no reads
        Fixture f1 = new Fixture();
        invoke(f1, 0x1000L, 0x2000L, 0x2000L);
        f1.done(0, 0, 0);

        // 2. Reversed interval (unsigned start > end): count 0, no reads
        // start = 0x8000000000000000 (sign bit set), end = 0x0000000000000000
        // unsigned comparison: start > end -> CMOV forces count 0
        Fixture f2 = new Fixture();
        invoke(f2, 0x1000L, 0x8000000000000000L, 0x0000000000000000L);
        f2.done(0, 0, 0);

        // 3. Unsigned nonreversed [0, UINT64_MAX): +7 wraps to6, >>>3 gives0.
        // The empty Memory proves the source performs no read for this raw64 span.
        Fixture f3 = new Fixture();
        invoke(f3, 0x1000L, 0x0000000000000000L, 0xFFFFFFFFFFFFFFFFL);
        f3.done(0, 0, 0);

        // 4. Small positive non-multiple-of-8 span, all zero elements
        // Address difference7; source ceil count1 reads the complete QWORD at start.
        // One iteration: read element at 0x2000, value 0 -> skip IAT and callback
        Fixture f4 = new Fixture();
        f4.seed64(0x2000L, 0L);
        f4.expect("P.R64", 0x2000L, 0L);
        invoke(f4, 0x1000L, 0x2000L, 0x2007L);
        f4.done(1, 0, 0);

        // 5. High64 start/end with exact single all-zero iteration
        // start = 0x7FFFFFFFFFFFFFF8L, end = 0x7FFFFFFFFFFFFFFFL
        // Address difference7, source count1.
        Fixture f5 = new Fixture();
        f5.seed64(0x7FFFFFFFFFFFFFF8L, 0L);
        f5.expect("P.R64", 0x7FFFFFFFFFFFFFF8L, 0L);
        invoke(f5, 0x1000L, 0x7FFFFFFFFFFFFFF8L, 0x7FFFFFFFFFFFFFFFL);
        f5.done(1, 0, 0);
    }
    private static void callbacks228() {
        // Scene 1: Leading zero, then nonzero with mutation and UNKNOWN args
        {
            long base = 0x1000L;
            long start = 0x1000L;
            long end = 0x1018L; // 3 elements: 0x1000, 0x1008, 0x1010
            long iatSlot = base + 0x43DBBA8L;
            long iatTarget = 0x2000000000000000L;
            long elem0 = 0L;
            long elem1 = 0x1111111111111111L;
            long elem2 = 0x2222222222222222L;
            long mutatedElem1 = 0x3333333333333333L;
            long mutatedIatTarget = 0x4444444444444444L;

            Fixture f = new Fixture((Fixture mem, int ordinal, long target, long liveRax, CallbackSpan228Api.Arguments args) -> {
                if (ordinal == 1) {
                    // First callback: EntryArguments(start, end)
                    if (!(args instanceof CallbackSpan228Api.EntryArguments)) throw new AssertionError("Expected EntryArguments");
                    // Mutate future element (index 2) and IAT slot
                    mem.writeInt64(start + 0x10L, mutatedElem1); // C.W64
                    mem.writeInt64(iatSlot, mutatedIatTarget);   // C.W64
                } else if (ordinal == 2) {
                    // Second callback: AfterOpaqueReturn.UNKNOWN
                    if (args != CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN) throw new AssertionError("Expected UNKNOWN");
                }
            });

            f.seed64(start, elem0);
            f.seed64(start + 0x08L, elem1);
            f.seed64(start + 0x10L, elem2);
            f.seed64(iatSlot, iatTarget);

            // Expected sequence:
            // 1. Read elem0 (0x1000) -> 0. Skip IAT/Call.
            f.expect("P.R64", start, elem0);
            // 2. Read elem1 (0x1008) -> 0x1111... Nonzero.
            f.expect("P.R64", start + 0x08L, elem1);
            // 3. Read IAT (0x43DBBA8) -> 0x2000...
            f.expect("P.R64", iatSlot, iatTarget);
            // 4. Call 43dbba8 with EntryArguments.
            f.expectCall(0x424E1E9L, iatTarget, elem1, new CallbackSpan228Api.EntryArguments(start, end));
            // 5. Callback writes elem2 (0x1010) -> C.W64
            f.expect("C.W64", start + 0x10L, mutatedElem1);
            // 6. Callback writes IAT (0x43DBBA8) -> C.W64
            f.expect("C.W64", iatSlot, mutatedIatTarget);
            // 7. Read elem2 (0x1010) -> Fresh read sees mutated value.
            f.expect("P.R64", start + 0x10L, mutatedElem1);
            // 8. Read IAT (0x43DBBA8) -> Fresh read sees mutated target.
            f.expect("P.R64", iatSlot, mutatedIatTarget);
            // 9. Call 43dbba8 with UNKNOWN.
            f.expectCall(0x424E1E9L, mutatedIatTarget, mutatedElem1, CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN);

            invoke(f, base, start, end);
            f.done(5, 2, 2); // 5 P.R64, 2 C.W64, 2 Calls

            // Verify final bytes
            if (f.peek64(start + 0x10L) != mutatedElem1) throw new AssertionError("Final elem mismatch");
            if (f.peek64(iatSlot) != mutatedIatTarget) throw new AssertionError("Final IAT mismatch");
        }

        // Scene 2: First nonzero callback writes then throws
        {
            long base = 0x2000L;
            long start = 0x2000L;
            long end = 0x2010L; // 2 elements: 0x2000, 0x2008
            long iatSlot = base + 0x43DBBA8L;
            long iatTarget = 0x3000000000000000L;
            long elem0 = 0x5555555555555555L;
            long elem1 = 0x6666666666666666L;
            long mutatedElem1 = 0x7777777777777777L;
            RuntimeException expectedThrow = new RuntimeException("Callback failure");

            Fixture f = new Fixture((Fixture mem, int ordinal, long target, long liveRax, CallbackSpan228Api.Arguments args) -> {
                if (ordinal == 1) {
                    if (!(args instanceof CallbackSpan228Api.EntryArguments)) throw new AssertionError("Expected EntryArguments");
                    // Write future element
                    mem.writeInt64(start + 0x08L, mutatedElem1); // C.W64
                    // Throw
                    throw expectedThrow;
                }
            });

            f.seed64(start, elem0);
            f.seed64(start + 0x08L, elem1);
            f.seed64(iatSlot, iatTarget);

            // Expected sequence:
            // 1. Read elem0 (0x2000) -> 0x5555... Nonzero.
            f.expect("P.R64", start, elem0);
            // 2. Read IAT (0x43DBBA8) -> 0x3000...
            f.expect("P.R64", iatSlot, iatTarget);
            // 3. Call 43dbba8 with EntryArguments.
            f.expectCall(0x424E1E9L, iatTarget, elem0, new CallbackSpan228Api.EntryArguments(start, end));
            // 4. Callback writes elem1 (0x2008) -> C.W64
            f.expect("C.W64", start + 0x08L, mutatedElem1);
            // 5. Callback throws -> No further reads/calls.

            try {
                invoke(f, base, start, end);
                throw new AssertionError("Expected RuntimeException");
            } catch (RuntimeException e) {
                if (e != expectedThrow) throw new AssertionError("Wrong exception");
            }

            f.done(2, 1, 1); // 2 P.R64, 1 C.W64, 1 Call

            // Verify final bytes
            if (f.peek64(start + 0x08L) != mutatedElem1) throw new AssertionError("Final elem mismatch");
        }
    }
    public static void main(String[] args) {
        boundaries228();
        callbacks228();
        System.out.println("CallbackSpanValidation228 groups=7 sourceInvocations=7 events=15 producerR64=9 producerWrites=0 callbackW64=3 opaqueCalls=3 finalCells=3 expectedThrowable=1");
    }

}
