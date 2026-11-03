package org.xar.ck3.control.g2.m2.nativecode;
/** Owner narrow effect contract, no FP arithmetic or CPU qualification. */
public final class Reverse641Api {
    private Reverse641Api() { }
    /** VZEROUPPER is an explicit effect on unrepresented upper lanes, never silently omitted. */
    public interface Memory extends FullCopy437Api.Memory { void vzeroUpper(); }
}
