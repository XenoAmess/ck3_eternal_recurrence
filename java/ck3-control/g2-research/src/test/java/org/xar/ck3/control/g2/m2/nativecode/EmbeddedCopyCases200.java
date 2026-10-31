package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedCopyScenario200.Op;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedCopyScenario200.Step;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedCopyScenario200.Scene;
import static org.xar.ck3.control.g2.m2.nativecode.EmbeddedCopyScenario200.Op.*;

/** Owner literals from original233B; owner has reviewed target, not a blind-oracle claim. */
public final class EmbeddedCopyCases200 {
    private EmbeddedCopyCases200() { }
    private static Step s(Op op, long address, long value, long high) {
        return new Step(op, address, value, high);
    }
    public static List<Scene> scenes() {
        long d1 = 0x1000000000001000L;
        long s1 = 0x2000000000002000L;
        long m1 = 0x3000000000000000L;
        long d2 = 0x8000000000005000L;
        long m2 = 0x7FFFFFFFFFFF0000L;
        return List.of(
            new Scene("distinct-full64-and-raw-widths", d1, s1, m1, List.of(
                s(W32, d1, 0, 0),
                s(W64, d1 + 8, 0, 0),
                s(W32, d1 + 0x10, 0xFFFFFFFFL, 0),
                s(C889, d1 + 0x18, s1, 0),
                s(W64, d1 + 0x100, 0, 0),
                s(W64, d1 + 0x108, 0, 0),
                s(W64, d1 + 0x110, m1 + 0x54DE270L, 0),
                s(W64, d1 + 0x118, m1 + 0x448D1F8L, 0),
                s(W64, d1 + 0x120, m1 + 0x448D268L, 0),
                s(W64, d1 + 0x128, 0, 0),
                s(W64, d1 + 0x130, 0, 0),
                s(W64, d1 + 0x138, m1 + 0x54DE278L, 0),
                s(W32, d1 + 0x140, 0, 0),
                s(W64, d1 + 0x148, 0, 0),
                s(W64, d1 + 0x150, 0, 0),
                s(W64, d1 + 0x158, m1 + 0x54DE270L, 0),
                s(W32, d1 + 0x160, 0xFFFFFFFFL, 0),
                s(W16, d1 + 0x164, 0, 0),
                s(W8, d1 + 0x166, 0, 0),
                s(R128, s1, 0xFEDCBA9876543210L, 0x0123456789ABCDEFL),
                s(W128, d1, 0xFEDCBA9876543210L, 0x0123456789ABCDEFL),
                s(R32, s1 + 0x10, 0x80000000L, 0),
                s(W32, d1 + 0x10, 0x80000000L, 0),
                s(C37282, d1 + 0x100, s1 + 0x100, 0),
                s(C260, d1 + 0x18, s1 + 0x18, 0),
                s(C37271, d1 + 0x118, s1 + 0x118, 0)
            )),
            new Scene("alias-fresh-after-initialization-and-call", d2, d2, m2, List.of(
                s(W32, d2, 0, 0),
                s(W64, d2 + 8, 0, 0),
                s(W32, d2 + 0x10, 0xFFFFFFFFL, 0),
                s(C889, d2 + 0x18, d2, 0),
                s(W64, d2 + 0x100, 0, 0),
                s(W64, d2 + 0x108, 0, 0),
                s(W64, d2 + 0x110, m2 + 0x54DE270L, 0),
                s(W64, d2 + 0x118, m2 + 0x448D1F8L, 0),
                s(W64, d2 + 0x120, m2 + 0x448D268L, 0),
                s(W64, d2 + 0x128, 0, 0),
                s(W64, d2 + 0x130, 0, 0),
                s(W64, d2 + 0x138, m2 + 0x54DE278L, 0),
                s(W32, d2 + 0x140, 0, 0),
                s(W64, d2 + 0x148, 0, 0),
                s(W64, d2 + 0x150, 0, 0),
                s(W64, d2 + 0x158, m2 + 0x54DE270L, 0),
                s(W32, d2 + 0x160, 0xFFFFFFFFL, 0),
                s(W16, d2 + 0x164, 0, 0),
                s(W8, d2 + 0x166, 0, 0),
                s(R128, d2, 0xCAFEBABEFFFFFFFFL, 0xFEDCBA9876543210L),
                s(W128, d2, 0xCAFEBABEFFFFFFFFL, 0xFEDCBA9876543210L),
                s(R32, d2 + 0x10, 0xAABBCCDDL, 0),
                s(W32, d2 + 0x10, 0xAABBCCDDL, 0),
                s(C37282, d2 + 0x100, d2 + 0x100, 0),
                s(C260, d2 + 0x18, d2 + 0x18, 0),
                s(C37271, d2 + 0x118, d2 + 0x118, 0)
            ))
        );
    }
}
