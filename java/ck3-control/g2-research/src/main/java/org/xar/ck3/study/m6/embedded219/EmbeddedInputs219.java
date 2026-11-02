package org.xar.ck3.study.m6.embedded219;

import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedElements37282B0;
import org.xar.ck3.study.m6.transfer216.Transfer216Api;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217;

/** Nominal logical-RAM bridge to the existing pointer-only322 producer, not its full185 ABI variant. */
public final class EmbeddedInputs219 {
    private EmbeddedInputs219() { }
    public record Input(long destinationRaw64, long sourceRaw64, long imageBaseRaw64, long parentFrameRaw64) { }
    public interface Memory extends PendingEmbeddedElements37282B0.Memory, Transfer216Api.Memory, Transfer4Api217.Memory { }
}
