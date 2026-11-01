package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Opt-in metadata from the existing producer's current decoded bound caches. */
public interface EncodedClear230BoundsPorts extends EncodedClear230Api.Ports {
    record DecodedBounds(long beginBits, long endBits) { }

    void call43dbba8WithBounds(NativeTaskMemory memory, long siteRva,
            long actualTarget, long liveRax,
            EncodedClear230Api.IndirectArguments arguments, DecodedBounds cachedBounds);

    void call424e364WithBounds(NativeTaskMemory memory, long siteRva,
            long rcx, DecodedBounds cachedBounds);
}
