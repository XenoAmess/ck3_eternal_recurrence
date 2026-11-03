package org.xar.ck3.study.m6.poststate240;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.Element150Fp643Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;

/** Source-only thin binding for the two actual643 lower ports. No150/715/B2 algorithm is copied. */
public final class Element150KnownPostState240 {
    private Element150KnownPostState240() { }

    /** Supplied executors must implement whole typed post-state; old185-only NR wrappers do not qualify. */
    public static Element150Fp643Api.Calls bind(Element150Fp643Api.Memory memory,
            PostState240Api.EntryExecutor whole715, PostState240Api.EntryExecutor wholeMove4) {
        Objects.requireNonNull(memory);
        return frame -> {
            Objects.requireNonNull(frame);
            var call = frame.call();
            PostState240Api.EntryExecutor selected;
            if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x37295FBL
                    && call.targetBits() == 0x21A5050L && frame.instructionLength() == 5) selected = whole715;
            else if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x3729620L
                    && call.targetBits() == 0xB2EEE0L && frame.instructionLength() == 5) selected = wholeMove4;
            else throw new IllegalArgumentException("Not an actual150 held lower CALL");
            var input = new PostState240Api.Input(frame.childEntry(), frame.directionFlagSet(),
                    frame.preMxcsr(), call.callSiteRva());
            QueueFp604Api.Outcome offered = Objects.requireNonNull(
                    Objects.requireNonNull(selected).execute(input, memory));
            if (offered instanceof QueueFp604Api.Normal normal) frame.checkNormalReturn(normal);
            return offered;
        };
    }
}
