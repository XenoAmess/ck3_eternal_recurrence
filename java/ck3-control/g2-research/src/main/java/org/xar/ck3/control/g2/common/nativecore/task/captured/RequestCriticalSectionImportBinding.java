package org.xar.ck3.control.g2.common.nativecore.task.captured;

/**
 * Adapter mapping existing machine-level tail ports to declared Windows API imports.
 * Scope: Static IAT metadata only. Does not validate pointers, simulate lock state,
 * or infer runtime behavior beyond the declared API signature.
 */
public final class RequestCriticalSectionImportBinding {
    private RequestCriticalSectionImportBinding() { }

    /**
     * Declared Windows API ports based on SDK declarations:
     * EnterCriticalSection(LPCRITICAL_SECTION)
     * LeaveCriticalSection(LPCRITICAL_SECTION)
     * Both return VOID.
     */
    public interface WindowsApiPorts {
        void enterCriticalSection(long criticalSectionPtr);
        void leaveCriticalSection(long criticalSectionPtr);
    }

    /**
     * Adapts RequestIndexedTails4247ffc.Ports to WindowsApiPorts.
     *
     * Mapping:
     * - jump43da500(knownRCX, liveRAX) -> enterCriticalSection(knownRCX)
     *   liveRAX is discarded as it is not a formal argument of EnterCriticalSection.
     * - jump43da4f0(knownRCX, liveRAX, liveRBX) -> leaveCriticalSection(knownRCX)
     *   liveRAX and liveRBX are discarded as they are not formal arguments of LeaveCriticalSection.
     *
     * @param api The caller-supplied Windows API ports.
     * @return A RequestIndexedTails4247ffc.Ports implementation that delegates to the API.
     */
    public static RequestIndexedTails4247ffc.Ports toTails(WindowsApiPorts api) {
        return new RequestIndexedTails4247ffc.Ports() {
            @Override
            public void jump43da500(long knownRCX, long liveRAX) {
                // Map knownRCX to the critical section pointer.
                // Discard liveRAX as it is not a Windows API argument.
                api.enterCriticalSection(knownRCX);
            }

            @Override
            public void jump43da4f0(long knownRCX, long liveRAX, long liveRBX) {
                // Map knownRCX to the critical section pointer.
                // Discard liveRAX and liveRBX as they are not Windows API arguments.
                api.leaveCriticalSection(knownRCX);
            }
        };
    }
}
