package org.xar.ck3.research.m3;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m3.PostRegistrationMainCasesApi178.Call;
import org.xar.ck3.research.m3.PostRegistrationMainCasesApi178.Case;
import org.xar.ck3.research.m3.PostRegistrationMainCasesApi178.Probe;
import org.xar.ck3.research.m3.PostRegistrationMainCasesApi178.Word;

/** Owner literal data derived independently from full held3790510; no target call here. */
public final class PostRegistrationMainBook178 {
    private static final long BASE = 0x140000000L;
    private static final long FILL = 0xa55aa55aa55aa55aL;
    private static final long RECEIVER = 0x1111222233334444L;
    private static final long MANAGER = 0x2222333344445555L;
    private static final long CONTEXT = 0x3333444455556666L;
    private static final long GS = 0x0000044400004000L;
    private static final long TLS = 0x0000055500005000L;
    private static final long STATIC = BASE + 0x5d1f5e0L;
    private static final long GUARD = BASE + 0x5d1f630L;

    private PostRegistrationMainBook178() { }

    private static Word w(long address, int width, long bits) {
        return new Word(address, width, bits);
    }

    private static Call c(String role, long returned, long... arguments) {
        return new Call(role, arguments, returned, List.of(), List.of());
    }

    private static Call c(String role, List<Word> observes, List<Word> effects, long... arguments) {
        return new Call(role, arguments, 0L, observes, effects);
    }

    private static String r(String kind, long address) {
        return kind + ":" + Long.toHexString(address);
    }

    private static String store(String kind, long address, long bits) {
        return r(kind, address) + ":" + Long.toHexString(bits);
    }

    private static Probe p(String kind, long address, int count) {
        return new Probe(r(kind, address), count);
    }

    private static ArrayList<Word> scratch(long rsp) {
        ArrayList<Word> initial = new ArrayList<>();
        for (int i = 0; i < 32; ++i) { initial.add(w(rsp + 8L * i, 8, FILL)); }
        return initial;
    }

    private static ArrayList<Word> normalInitial(long rsp, long vector, long table, long guardBits) {
        ArrayList<Word> initial = scratch(rsp);
        initial.addAll(List.of(
                w(BASE + 0x5cbeed8L, 8, RECEIVER),
                w(BASE + 0x5c6a4d0L, 8, MANAGER),
                w(BASE + 0x49f6430L, 4, 0x3f666666L),
                w(vector, 8, vector + 0x1000L),
                w(vector + 0xcL, 4, 0L),
                w(table + 4L, 1, 0L),
                w(table + 0x2cL, 1, 0x7fL),
                w(GS, 8, TLS), w(TLS + 0x10L, 4, 3L), w(GUARD, 4, guardBits)));
        return initial;
    }

    private static ArrayList<Call> normalCalls(long rsp, long table) {
        return new ArrayList<>(List.of(
                c("call3f542c0", 0L, RECEIVER, BASE + 0x4448998L),
                c("callc3e150", table),
                c("call3763f90", 0L, MANAGER, rsp + 0x58L),
                c("calla92eb0", CONTEXT), c("gs58", GS)));
    }

    private static ArrayList<Word> normalFinal(long rsp, long table, long allocator) {
        return new ArrayList<>(List.of(
                w(rsp + 0x20L, 8, FILL), w(rsp + 0x28L, 8, FILL),
                w(rsp + 0x38L, 8, table), w(rsp + 0x40L, 8, 0L),
                w(rsp + 0x48L, 1, 0L), w(rsp + 0x4cL, 4, 0x3f666666L),
                w(rsp + 0x50L, 8, allocator), w(rsp + 0x58L, 8, 0L),
                w(rsp + 0x60L, 8, 0L), w(rsp + 0x68L, 8, BASE + 0x54f2ac8L),
                w(rsp + 0xc8L, 8, FILL)));
    }

    private static Case earlyReturn() {
        long rsp = 0x100000L;
        long vector = 0x0000011100001000L;
        ArrayList<Word> initial = scratch(rsp);
        initial.addAll(List.of(w(BASE + 0x5cbeed8L, 8, RECEIVER),
                w(vector, 8, 0x4444555566667777L), w(vector + 0xcL, 4, 17L)));
        return new Case("eax-minus-one-no-scratch-effects", BASE, vector, rsp,
                List.copyOf(initial),
                List.of(c("call3f542c0", 0xffffffffL, RECEIVER, BASE + 0x4448998L)),
                List.of(w(rsp + 0x20L, 8, FILL), w(rsp + 0x38L, 8, FILL),
                        w(rsp + 0x50L, 8, FILL), w(rsp + 0x58L, 8, FILL)),
                List.of(p("R64", BASE + 0x5cbeed8L, 1), p("R64", vector, 0),
                        p("R32", vector + 0xcL, 0), p("R64", BASE + 0x4448998L, 0)),
                List.of(r("R64", BASE + 0x5cbeed8L)), true);
    }

    private static Case emptyStaticFastEpoch() {
        long rsp = 0x200000L;
        long vector = 0x0000022200002000L;
        ArrayList<Word> initial = normalInitial(rsp, vector, STATIC, 0xfffffffeL);
        ArrayList<Word> expected = normalFinal(rsp, STATIC, BASE + 0x54de200L);
        expected.addAll(List.of(w(GUARD, 4, 0xfffffffeL),
                w(STATIC + 4L, 1, 0L), w(STATIC + 0x2cL, 1, 0x7fL)));
        return new Case("empty-static-table-signed-epoch-fast", BASE, vector, rsp,
                List.copyOf(initial), List.copyOf(normalCalls(rsp, STATIC)), List.copyOf(expected),
                List.of(p("R32", vector + 0xcL, 2), p("R8", STATIC + 4L, 1),
                        p("R8", STATIC + 0x2cL, 1), p("R64", rsp + 0x38L, 1),
                        p("R32", TLS + 0x10L, 1), p("R32", GUARD, 1),
                        p("R64", rsp + 0x50L, 0),
                        new Probe(store("W8", STATIC + 4L, 0L), 0),
                        new Probe(store("W8", STATIC + 0x2cL, 0xffL), 0)),
                List.of(r("R32", BASE + 0x49f6430L), r("R32", vector + 0xcL),
                        r("R64", vector), r("R32", vector + 0xcL),
                        r("R64", rsp + 0x38L), r("R8", STATIC + 4L),
                        r("R8", STATIC + 0x2cL), r("R64", GS),
                        r("R32", TLS + 0x10L), r("R32", GUARD)), false);
    }

    private static Case emptyTlsInitFreshCleanup() {
        long rsp = 0x300000L;
        long vector = 0x0000033300003000L;
        long beforeInit = 0x0000066600006000L;
        long afterInit = 0x0000077700007000L;
        long afterField = 0x8000088800008000L;
        long firstAllocator = 0x0000099900009000L;
        long finalAllocator = 0x80000aaa0000a000L;
        long finalVtable = 0x80000bbb0000b000L;
        long releaseCode = 0x80000ccc0000c010L;
        ArrayList<Word> initial = normalInitial(rsp, vector, beforeInit, 4L);
        initial.addAll(List.of(w(STATIC + 4L, 1, 0x73L), w(STATIC + 0x2cL, 1, 0x74L),
                w(afterInit + 4L, 1, 1L), w(finalAllocator, 8, finalVtable),
                w(finalVtable + 0x10L, 8, releaseCode)));
        ArrayList<Call> calls = normalCalls(rsp, beforeInit);
        calls.addAll(List.of(
                c("call4223a84", List.of(w(GUARD, 4, 4L)),
                        List.of(w(GUARD, 4, 0xffffffffL)), GUARD),
                c("call4223a24", List.of(w(STATIC + 4L, 1, 0L), w(STATIC + 0x2cL, 1, 0xffL)),
                        List.of(w(rsp + 0x38L, 8, afterInit), w(rsp + 0x40L, 4, 1L),
                                w(rsp + 0x50L, 8, firstAllocator)), GUARD),
                c("call856050", List.of(w(rsp + 0x38L, 8, afterInit),
                                w(rsp + 0x40L, 4, 1L), w(rsp + 0x50L, 8, firstAllocator)),
                        List.of(w(rsp + 0x38L, 8, afterField),
                                w(rsp + 0x50L, 8, finalAllocator)), afterInit + 8L),
                c("allocatorSlot10", List.of(w(rsp + 0x38L, 8, afterField),
                                w(rsp + 0x50L, 8, finalAllocator)), List.of(),
                        releaseCode, finalAllocator, afterField, 8L)));
        ArrayList<Word> expected = normalFinal(rsp, afterField, finalAllocator);
        // Replace the common literal zero DWORD pair with the explicit opaque count1 effect.
        expected.set(3, w(rsp + 0x40L, 8, 1L));
        expected.addAll(List.of(w(GUARD, 4, 0xffffffffL),
                w(STATIC + 4L, 1, 0L), w(STATIC + 0x2cL, 1, 0xffL)));
        return new Case("empty-main-tls-init-fresh-two-cleanup-loads", BASE, vector, rsp,
                List.copyOf(initial), List.copyOf(calls), List.copyOf(expected),
                List.of(p("R32", vector + 0xcL, 2), p("R64", rsp + 0x38L, 3),
                        p("R64", rsp + 0x50L, 1), p("R32", rsp + 0x40L, 1),
                        p("R8", beforeInit + 4L, 1), p("R8", beforeInit + 0x2cL, 1),
                        p("R8", afterInit + 4L, 1), p("R8", afterField + 4L, 0),
                        p("R32", GUARD, 2), p("R32", TLS + 0x10L, 1),
                        new Probe(store("W8", STATIC + 4L, 0L), 1),
                        new Probe(store("W8", STATIC + 0x2cL, 0xffL), 1)),
                List.of(r("R64", rsp + 0x38L), r("R8", beforeInit + 4L),
                        r("R8", beforeInit + 0x2cL), r("R32", TLS + 0x10L),
                        r("R32", GUARD), r("R32", GUARD),
                        store("W8", STATIC + 4L, 0L), store("W8", STATIC + 0x2cL, 0xffL),
                        r("R64", rsp + 0x38L), r("R32", rsp + 0x40L),
                        r("R8", afterInit + 4L), r("R64", rsp + 0x38L),
                        r("R64", rsp + 0x50L), r("R64", finalAllocator),
                        r("R64", finalVtable + 0x10L)), false);
    }

    public static List<Case> cases() {
        return List.of(earlyReturn(), emptyStaticFastEpoch(), emptyTlsInitFreshCleanup());
    }
}
