package org.xar.ck3.research.m5;

/** Shared owned memory for the whole token assembly and explicit CRT boundaries. */
public final class GovernmentWholeCrt189Api {
    private GovernmentWholeCrt189Api() { }
    public interface Memory extends GovernmentWholeToken184Api.Memory,
            GovernmentCrtBoundary185Api.Memory { }
}
