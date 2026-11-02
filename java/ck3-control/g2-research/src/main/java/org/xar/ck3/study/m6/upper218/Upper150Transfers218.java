package org.xar.ck3.study.m6.upper218;

import org.xar.ck3.study.m6.element150.Element150Candidate;
import org.xar.ck3.study.m6.element150.Element150Inputs;
import org.xar.ck3.study.m6.transfer216.Transfer216Api;
import org.xar.ck3.study.m6.transfer216.Transfer21a216;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217;
import org.xar.ck3.study.m6.transfer217.Transfer4Move217;

/** Thin binding for Element150Candidate.copy to actual Transfer21a216 and Transfer4Move217 bodies. */
public final class Upper150Transfers218 {
    private Upper150Transfers218() { }

    public static long copy(Upper150Inputs218.Input input, Upper150Inputs218.Memory memory, Transfer216Api.Calls calls16, Transfer4Api217.Calls calls4, Transfer216Api.Budget budget16, Transfer4Api217.Budget budget4) {
        Element150Inputs.Input parent = input.parent();
        long parentFrame = input.parentFrameRaw64();
        long imageBase = parent.imageBaseRaw64();

        Element150Inputs.Calls calls = new Element150Inputs.Calls() {
            @Override public void copy16_21a5050(long destinationHeader, long sourceHeader) {
                // Child frame for 21a5050: parentFrame - 0x480 (5 pushes + 0x450 sub)
                long childFrame = parentFrame - 0x480L;
                Transfer216Api.Input lowerInput = new Transfer216Api.Input(destinationHeader, sourceHeader, imageBase, childFrame);
                Transfer21a216.execute(lowerInput, memory, calls16, budget16);
            }

            @Override public void copy4_b2eee0(long destinationHeader, long sourceHeader) {
                // Child frame for b2eee0: parentFrame - 0x50 (3 pushes + 0x30 sub)
                long childFrame = parentFrame - 0x50L;
                Transfer4Api217.Input lowerInput = new Transfer4Api217.Input(destinationHeader, sourceHeader, imageBase, childFrame);
                Transfer4Move217.execute(lowerInput, memory, calls4, budget4);
            }
        };

        return Element150Candidate.copy(parent, memory, calls);
    }
}