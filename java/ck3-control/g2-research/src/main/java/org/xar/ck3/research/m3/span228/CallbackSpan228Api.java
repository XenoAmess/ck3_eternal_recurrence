package org.xar.ck3.research.m3.span228;

import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;

/** Normal supplied-RAM business projection; no physical stack, final CPU return or EH. */
public interface CallbackSpan228Api {
    interface Memory extends DispatchMiddle219Api.Memory {}

    record Input(long moduleBase, long startAddress, long endAddress) {}

    /** Only RCX/RDX are represented; all other volatile arguments remain opaque. */
    sealed interface Arguments permits EntryArguments, AfterOpaqueReturn {}

    record EntryArguments(long rcx, long rdx) implements Arguments {}

    /** Actual post-callback RCX/RDX bits are unobserved here; this never means zero. */
    enum AfterOpaqueReturn implements Arguments { UNKNOWN }

    interface Ports {
        void call43dbba8(Memory memory, long siteRva, long actualTarget,
                        long liveRax, Arguments arguments);
    }
}
