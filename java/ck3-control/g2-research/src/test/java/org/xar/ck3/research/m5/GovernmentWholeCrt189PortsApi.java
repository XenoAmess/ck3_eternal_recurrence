package org.xar.ck3.research.m5;

import java.util.Map;

/** Shared image of the existing whole recorder; snapshots are complete byte maps. */
public final class GovernmentWholeCrt189PortsApi {
    private GovernmentWholeCrt189PortsApi() { }
    public interface MemoryImage {
        Map<Long,Integer> snapshot();
        void mutate(Map<Long,Integer> bytes);
    }
}
