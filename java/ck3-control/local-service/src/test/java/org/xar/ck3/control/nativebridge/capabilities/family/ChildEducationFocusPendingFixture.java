package org.xar.ck3.control.nativebridge.capabilities.family;

/** Test-only bridge to the actual pure pending producer. It grants no Root, native, writer or source authority. */
public final class ChildEducationFocusPendingFixture {
    private ChildEducationFocusPendingFixture(){}
    public static ChildEducationFocus.Pending fromContext(ChildEducationFocus.Context original,ChildEducationFocus.Selection selection,String requestId) {
        return ChildEducationFocusEffects.pendingData(original,selection,requestId,java.util.Optional.empty()).orElseThrow();
    }
}

