package org.xar.ck3.study.m6.upper218;

import org.xar.ck3.study.m6.element150.Element150Inputs;
import org.xar.ck3.study.m6.transfer216.Transfer216Api;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217;

/** Nominal same-RAM join only. No Root authority or complete native caller ABI is introduced. */
public final class Upper150Inputs218 {
    private Upper150Inputs218() { }
    /** parentFrameRaw64 denotes the original150 body's post-prologue RSP in the logical scratch model. */
    public record Input(Element150Inputs.Input parent, long parentFrameRaw64) { }
    public interface Memory extends Transfer216Api.Memory, Transfer4Api217.Memory { }
}
