package org.xar.ck3.research.m3.callee246;

import org.xar.ck3.research.m3.callee246.Callee68fcApi246;

/** Exact-width address operations for supplied storage; no process attachment. */
public interface Callee68d4Memory246 extends Callee68fcApi246.Memory {
    /** One 32-bit wrapping exchange-add; returns the actual old int32 bits. */
    int exchangeAddInt32(long address, int deltaBits);
}