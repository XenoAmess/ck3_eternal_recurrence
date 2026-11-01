package org.xar.ck3.research.m3.lookup236;

import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;

public interface Lookup236Api {
    @FunctionalInterface
    public interface DispatchSupplier {
        int jumpRax(ModuleLookup221Api.Memory memory, long siteRva, long targetRax, long knownRcx);
    }
}