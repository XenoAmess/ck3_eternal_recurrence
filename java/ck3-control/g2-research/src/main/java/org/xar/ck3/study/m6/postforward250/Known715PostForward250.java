package org.xar.ck3.study.m6.postforward250;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate249.AllocatorGetterChildren249;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;
import org.xar.ck3.study.m6.postvtable247.PostVtableForward247;

/** Exact held715 virtual CALLs into complete247 bodies, with only249 first getters known. */
public final class Known715PostForward250 {
    private Known715PostForward250() { }

    public static CallOutcome242Api.OutcomePort bind(GovernmentCrtBoundary185Api.Memory memory,
            PostVtable247Api.Children opaqueForwardChildren,CallOutcome242Api.OutcomePort remaining) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(remaining);
        var children=AllocatorGetterChildren249.bind(opaqueForwardChildren);
        return frame -> {
            Objects.requireNonNull(frame);
            var call=frame.call();long site=call.callSiteRva();
            boolean release=site==0x21a508fL||site==0x21a5159L||site==0x21a5223L;
            boolean allocate=site==0x21a51b9L;
            if(frame.ownerEntryRva()!=0x21a5050L||frame.instructionLength()!=3
                    ||call.kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                    ||!((release&&call.targetBits()==frame.imageBaseBits()+0x855830L)
                        ||(allocate&&call.targetBits()==frame.imageBaseBits()+0x855870L)))
                return remaining.invoke(frame);
            var input=new PostVtable247Api.Input(frame.childEntry(),frame.preDirectionFlagSet(),
                    frame.preMxcsr(),site);
            // Caller242 retains its original OPAQUE_PRESERVES_N admission; no second push or wrapper.
            return release?PostVtableForward247.fromSlot10(input,memory,children)
                    :PostVtableForward247.fromSlot08(input,memory,children);
        };
    }
}
