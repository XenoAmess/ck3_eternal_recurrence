package org.xar.ck3.control.wave2.events.nativepulse;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;

class NativeCandidateBankProjectionTest {
    @Test void nativePointerPrecedenceAndInputOrderAreRetained() {
        var a = new NativeCandidateBankProjection.NativeFields(0xffffffffL, true, true, true, true, true);
        var b = new NativeCandidateBankProjection.NativeFields(4, false, true, true, true, true);
        var c = new NativeCandidateBankProjection.NativeFields(8, false, false, true, true, true);
        var d = new NativeCandidateBankProjection.NativeFields(10, false, false, false, true, true);
        var e = new NativeCandidateBankProjection.NativeFields(12, false, false, false, false, true);
        var f = new NativeCandidateBankProjection.NativeFields(14, false, false, false, false, false);
        assertEquals(5, NativeCandidateBankProjection.classify(a).nativeTag());
        assertEquals(4, NativeCandidateBankProjection.classify(b).nativeTag());
        assertEquals(3, NativeCandidateBankProjection.classify(c).nativeTag());
        assertEquals(2, NativeCandidateBankProjection.classify(d).nativeTag());
        assertEquals(0, NativeCandidateBankProjection.classify(e).nativeTag());
        assertEquals(1, NativeCandidateBankProjection.classify(f).nativeTag());
        var output = NativeCandidateBankProjection.rebuild(NativePlayableAnnualGate.Executable.CURRENT_12004,
            NativeCandidateBankProjection.Bank.ONE, List.of(c, a, b, a, d, e, f));
        assertEquals(List.of(0xffffffffL, 0xffffffffL), output.vector00());
        assertEquals(List.of(0xffffffffL, 4L, 0xffffffffL), output.vector18());
        assertEquals(NativeCandidateBankProjection.Bank.ZERO, output.rebuildTarget());
        assertFalse(output.completeNativeInputUniverseProven());
        assertFalse(output.completeBankProjection()); assertFalse(output.eventSelected());
        assertThrows(UnsupportedOperationException.class, () -> output.vector00().add(3L));
    }
    @Test void bankOffsetsAgreeWithTheActualSchedulerConsumer() {
        assertEquals(0x2ee78, NativeCandidateBankProjection.Bank.ZERO.dataOffsetFromGameStateData());
        assertEquals(0x314b8, NativeCandidateBankProjection.Bank.ONE.dataOffsetFromGameStateData());
        assertEquals(0x33af8, NativeCandidateBankProjection.MANAGER_OFFSET + NativeCandidateBankProjection.SELECTOR_OFFSET);
        assertEquals(NativeCandidateBankProjection.Bank.ZERO, NativeCandidateBankProjection.Bank.ZERO.opposite().opposite());
        assertThrows(IllegalArgumentException.class, () -> NativeCandidateBankProjection.Bank.exact(2));
        assertThrows(IllegalArgumentException.class, () -> new NativeCandidateBankProjection.NativeFields(0x100000000L, false, false, false, false, false));
        assertThrows(IllegalArgumentException.class, () -> new NativeCandidateBankProjection.NativeFields(-1, false, false, false, false, false));
    }
}
