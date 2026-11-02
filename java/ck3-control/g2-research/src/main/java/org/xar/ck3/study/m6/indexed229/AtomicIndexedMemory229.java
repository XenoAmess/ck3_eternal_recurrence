package org.xar.ck3.study.m6.indexed229;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Exact-width address operations for supplied storage; no process attachment.
 * One SAME logical RAM QWORD exchange observes old raw64 bits and writes new raw64 bits as one port effect.
 * Returns old bits. No separate readQword/writeQword emulation.
 * Interface does not promise physical hardware atomicity/DF/RFLAGS/EH/fullABI, nor default implementation.
 */
public interface AtomicIndexedMemory229 extends GovernmentCrtBoundary185Api.Memory {
    long exchangeQword(long address, long newBits);
}