package org.xar.ck3.control.application.action;

/** Test-only fixed original request ID; never included in a production artifact. */
public final class ClaimsReadPermitFixture {
    private ClaimsReadPermitFixture() { }
    public static ReadPermit issue(ReadContract<?> contract,PlanningReadRequest request,
            NativeRequest prepared,PlanningReadGuard guard,String originalRequestId) {
        return new ReadPermit(contract,request,prepared,guard,originalRequestId);
    }
}
