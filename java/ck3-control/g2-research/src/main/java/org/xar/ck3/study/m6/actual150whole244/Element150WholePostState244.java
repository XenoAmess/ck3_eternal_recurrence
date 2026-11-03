package org.xar.ck3.study.m6.actual150whole244;

import org.xar.ck3.control.g2.m2.nativecode.Element150Fp643Api;
import org.xar.ck3.study.m6.full238.TransferFull238Api;
import org.xar.ck3.study.m6.postentry242.WholeTransferPostState242;
import org.xar.ck3.study.m6.poststate240.Element150KnownPostState240;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;

/** Explicit opt-in composition of actual643 with the new typed whole715/Move bodies. */
public final class Element150WholePostState244 {
    private Element150WholePostState244() { }

    public static Element150Fp643Api.Calls bind(Element150Fp643Api.Memory memory,
            PostState240Api.FloatingStages floatingStages, TransferFull238Api.Budget budget,
            CallOutcome242Api.OutcomePort opaqueCalls) {
        var whole = new WholeTransferPostState242(floatingStages,budget,opaqueCalls);
        return Element150KnownPostState240.bind(memory,whole::transfer715,whole::move4);
    }
}
