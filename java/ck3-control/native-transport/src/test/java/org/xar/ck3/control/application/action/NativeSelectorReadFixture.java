package org.xar.ck3.control.application.action;

/** Controlled adversarial read permits only. Never selected into any production artifact. */
public final class NativeSelectorReadFixture {
    private NativeSelectorReadFixture() { }
    public static ReadPermit issue(ReadContract<?> contract, PlanningReadRequest request,
            NativeRequest prepared, PlanningReadGuard guard, String requestId) {
        return new ReadPermit(contract, request, prepared, guard, requestId);
    }
}
