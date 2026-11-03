package org.xar.ck3.study.m6.poststate249;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/** Opt-in binding of only the two held first virtual CALLs to the complete8B getter. */
public final class AllocatorGetterChildren249 {
    private AllocatorGetterChildren249() { }

    public static PostVtable247Api.Children bind(PostVtable247Api.Children remaining) {
        Objects.requireNonNull(remaining);
        var getter=new AllocatorGetterPostState249();
        return new PostVtable247Api.Children() {
            @Override
            public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                Objects.requireNonNull(frame);
                var call=frame.call();
                boolean first=(frame.ownerEntryRva()==0x855870L&&call.callSiteRva()==0x855883L)
                        ||(frame.ownerEntryRva()==0x855830L&&call.callSiteRva()==0x85584cL);
                if(!first||frame.instructionLength()!=3
                        ||call.kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                        ||call.targetBits()!=frame.imageBaseBits()+0x86e140L)
                    return remaining.invoke(frame,sameMemory);
                var child=frame.childInput();
                return getter.execute(new PostState240Api.Input(child.entry(),
                        child.directionFlagSet(),child.mxcsr(),child.originCallSiteRva()),sameMemory);
            }

            @Override
            public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                return remaining.tail(frame,sameMemory);
            }
        };
    }
}
