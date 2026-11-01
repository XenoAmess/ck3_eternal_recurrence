package org.xar.ck3.research.m3.span237;

import org.xar.ck3.research.m3.span228.CallbackSpan228Api;

/** Supplied known-entry business context, without unknown volatile-register synthesis. */
public interface SpanStaticDispatch237Api {
    @FunctionalInterface
    interface TailPort {
        int jumpRax(CallbackSpan228Api.Memory memory, long siteRva,
                    long targetRax, long knownRcx,
                    CallbackSpan228Api.EntryArguments entryArguments);
    }
}
