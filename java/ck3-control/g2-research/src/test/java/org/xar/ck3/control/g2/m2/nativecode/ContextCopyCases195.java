package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class ContextCopyCases195 {
    private ContextCopyCases195() { }
    public static List<ContextCopyScenario195.Scene> scenes() {
        long dst = 0x1000000000000000L;
        long src = 0x2000000000000000L;
        List<ContextCopyScenario195.Step> s1 = List.of(
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R64, src, 0x1111111111111111L, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W64, dst, 0x1111111111111111L, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C373, dst + 8, src + 8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C373, dst + 0x170, src + 0x170, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x2d8, 0x2d8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst + 0x2d8, 0x2d8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x2dc, 0x2dc, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst + 0x2dc, 0x2dc, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x2e0, 0x2e0, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst + 0x2e0, 0x2e0, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x2e4, 0x2e4, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst + 0x2e4, 0x2e4, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x2e8, 0x2e8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst + 0x2e8, 0x2e8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x2ec, 0x2ec, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst + 0x2ec, 0x2ec, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R128, src + 0x2f0, 0xFEDCBA9876543210L, 0x0123456789ABCDEFL, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W128, dst + 0x2f0, 0xFEDCBA9876543210L, 0x0123456789ABCDEFL, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src + 0x30c, -1, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R64, src + 0x300, 0xFEDCBA9800000300L, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C105, dst + 0x300, 0, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, dst + 0x30c, 0x30c, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.CBCB, dst + 0x300, 0x30c, 0xFEDCBA9800000300L, 0xFEDCBA98000002FFL),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C250, dst + 0x330, src, 0, 0)
        );
        long dst2 = 0x3000000000000000L;
        long src2 = 0x3000000000000000L;
        List<ContextCopyScenario195.Step> s2 = List.of(
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R64, src2, 0x2222222222222222L, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W64, dst2, 0x2222222222222222L, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C373, dst2 + 8, src2 + 8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C373, dst2 + 0x170, src2 + 0x170, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x2d8, 0x2d8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst2 + 0x2d8, 0x2d8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x2dc, 0x2dc, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst2 + 0x2dc, 0x2dc, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x2e0, 0x2e0, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst2 + 0x2e0, 0x2e0, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x2e4, 0x2e4, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst2 + 0x2e4, 0x2e4, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x2e8, 0x2e8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst2 + 0x2e8, 0x2e8, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x2ec, 0x2ec, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W32, dst2 + 0x2ec, 0x2ec, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R128, src2 + 0x2f0, 0xFEDCBA9876543210L, 0x0123456789ABCDEFL, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.W128, dst2 + 0x2f0, 0xFEDCBA9876543210L, 0x0123456789ABCDEFL, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, src2 + 0x30c, 16, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R64, src2 + 0x300, 0x8000000000000300L, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C105, dst2 + 0x300, 0, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.R32, dst2 + 0x30c, 0xFFFFFFFFL, 0, 0),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.CBCB, dst2 + 0x300, 0xFFFFFFFFL, 0x8000000000000300L, 0x8000000000000310L),
            new ContextCopyScenario195.Step(ContextCopyScenario195.Op.C250, dst2 + 0x330, src2, 0, 0)
        );
        return List.of(
            new ContextCopyScenario195.Scene("scene1", dst, src, s1),
            new ContextCopyScenario195.Scene("scene2", dst2, src2, s2)
        );
    }
}