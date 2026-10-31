package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.ProducerCompositionScenario207.Op;
import org.xar.ck3.control.g2.m2.nativecode.ProducerCompositionScenario207.Step;
import org.xar.ck3.control.g2.m2.nativecode.ProducerCompositionScenario207.Scene;
import static org.xar.ck3.control.g2.m2.nativecode.ProducerCompositionScenario207.Op.*;

/** Composes already verified source-literal fixture DATA, never executes target to expect values.
 * Owner reviewed target; this is not a blind-oracle qualification.
 */
public final class ProducerCompositionCases207 {
    private ProducerCompositionCases207() { }
    private static final long MODULE = 0x100000000L;
    private static final long OBJECT = 0x10000000000015C8L;
    private static Step s(Op op, long a, long b, long c, long d) { return new Step(op, a, b, c, d); }
    private static void add(List<Step> result, Step... values) { result.addAll(List.of(values)); }
    private static long relocate(long value, long oldD, long newD, long oldS, long newS) {
        if (Long.compareUnsigned(value - oldD, 0x400L) <= 0) return newD + value - oldD;
        if (Long.compareUnsigned(value - oldS, 0x400L) <= 0) return newS + value - oldS;
        return value;
    }
    private static void embeddedLiteralData(List<Step> result, long dst, long src) {
        var scene = EmbeddedCopyCases200.scenes().get(0);
        long[] rvas = {0x54DE270L, 0x54DE278L, 0x448D1F8L, 0x448D268L};
        for (var old : scene.steps()) {
            Op op = Op.valueOf(old.op().name());
            long a = relocate(old.a(), scene.destination(), dst, scene.source(), src);
            long b = old.b();
            if (op == W64) {
                for (long rva : rvas) if (b == scene.moduleBase() + rva) b = MODULE + rva;
            } else if (op == C889 || op == C37282 || op == C260 || op == C37271) {
                b = relocate(b, scene.destination(), dst, scene.source(), src);
            }
            result.add(s(op, a, b, old.c(), 0));
        }
    }
    private static void contextLiteralData(List<Step> result, long dst, long src) {
        var scene = ContextCopyCases195.scenes().get(0);
        for (var old : scene.steps()) {
            long a = relocate(old.a(), scene.destination(), dst, scene.source(), src);
            if (old.op() == ContextCopyScenario195.Op.C373) {
                long childSource = relocate(old.b(), scene.destination(), dst, scene.source(), src);
                embeddedLiteralData(result, a, childSource);
            } else {
                Op op = Op.valueOf(old.op().name());
                long b = old.b();
                if (op == C250) b = relocate(b, scene.destination(), dst, scene.source(), src);
                result.add(s(op, a, b, old.c(), old.d()));
            }
        }
    }
    private static void initializerLiteralData(List<Step> result, long component) {
        long[][] qwords = {
            {0x18,0xF},{0,0},{0x78,0},{0x88,0},{0x90,0xF},{0x98,0},{0xA8,0},{0xB0,0xF},
            {0xB8,0},{0xC8,0},{0xD0,0xF},{0xD8,0},{0xE0,0},{0xE8,0x1054E62D8L},{0x1E8,component+0x78},
            {0x10,0},{0x20,0},{0x30,0},{0x38,0xF},{0x40,0},{0x50,0},{0x58,0xF},{0x60,0},{0x68,0},
            {0x70,0x1054E62D8L},{0xF0,0},{0x100,0},{0x108,0xF},{0x110,0},{0x120,0},{0x128,0xF},
            {0x130,0},{0x140,0},{0x148,0xF},{0x150,0},{0x158,0},{0x160,0x1054E62D8L},
            {0x168,0},{0x178,0},{0x180,0xF},{0x188,0},{0x198,0},{0x1A0,0xF},{0x1A8,0},{0x1B8,0},
            {0x1C0,0xF},{0x1C8,0},{0x1D0,0},{0x1D8,0x1054E62D8L},{0x1E0,component},{0x1F0,0},
            {0x200,0},{0x208,0xF},{0x210,0},{0x220,0},{0x228,0xF},{0x230,0},{0x240,0},{0x248,0xF},{0x250,-1L}
        };
        for (long[] value : qwords) result.add(s(W64, component + value[0], value[1], 0, 0));
        add(result, s(W32, component+0x258,0xFFFFFFFFL,0,0),s(W8,component+0x25C,0,0,0),
                s(W32,component+0x260,0,0,0),s(W8,component+0x264,1,0,0));
    }
    public static List<Scene> scenes() {
        List<Step> steps = new ArrayList<>();
        add(steps,
            s(R8,0x1048,0,0,0),s(R8,0x1049,0,0,0),s(R32,0x1040,1,0,0),s(R32,0x1040,1,0,0),
            s(PAGE,0x1008,2,1,0),s(R64,0x1008,0x5000,0,0),s(R64,0x5000,0x1000000000001000L,0,0),
            s(R64,0x1020,0x6000,0,0),s(R32,0x6010,2,0,0),s(W32,0x1040,2,0,0),s(R32,0x6010,3,0,0),
            s(W32,0x6034,0xFFFFFF,0,0),s(R64,0x1020,0x7000,0,0),s(W32,0x7010,0xFFFFFF,0,0),
            s(R64,0x1020,0x8000,0,0),s(R32,0x103C,10,0,0),s(W32,0x103C,11,0,0),s(W8,0x104A,1,0,0),
            s(R32,OBJECT+0x10,0x2A123456,0,0),s(W64,0x8018,OBJECT,0,0),s(R32,0x1038,0xFFFFFFFFL,0,0),
            s(W32,0x1038,1,0,0),s(R32,0x9000,1,0,0),s(R8,0xA000,2,0,0),s(R8,0xB000,1,0,0),
            s(R32,0xC000,0xDEADBEEFL,0,0),s(W32,OBJECT+0x10,0xFFFFFFFFL,0,0),
            s(W32,OBJECT+0x14,0x4368496E,0,0),s(W64,OBJECT,0x104759250L,0,0),s(W64,OBJECT+8,0x104759288L,0,0));
        contextLiteralData(steps, OBJECT+0x18, 0x2000);
        initializerLiteralData(steps, OBJECT+0x350);
        add(steps,s(W32,OBJECT+0x5B8,0,0,0),s(W32,OBJECT+0x5BC,0xDEADBEEFL,0,0),
            s(R32,0x22E8,0x2E8,0,0),s(W32,OBJECT+0x5C0,1,0,0),s(W8,OBJECT+0x5C4,1,0,0),
            s(W8,OBJECT+0x5C5,0,0,0),s(W8,OBJECT+0x5C6,1,0,0),s(W32,OBJECT+0x10,0x2B000001,0,0));
        var input = new PendingSlotProducer2A32770.Input(0x1000,0x2000,0xC000,0xB000,0xA000,0x9000,MODULE);
        return List.of(new Scene("known-three-body-call-composition", input, List.copyOf(steps), OBJECT));
    }
}
