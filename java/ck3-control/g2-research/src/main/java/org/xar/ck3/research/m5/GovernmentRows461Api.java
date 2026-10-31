package org.xar.ck3.research.m5;

import java.util.Objects;
/** Exact two-entry boundary of held461B, reusing raw registers and owned effects. */
public final class GovernmentRows461Api {
    private GovernmentRows461Api() { }
    public enum Start {
        AT_35A1(0x30A35A1L), AT_35A4(0x30A35A4L);
        private final long rva;
        Start(long value) { rva=value; }
        public long rva() { return rva; }
    }
    /** nextRva376E, with every represented incoming/outgoing GPR/XMM bit explicit. */
    public record Join(long nextRva, GovernmentCompaction160Api.Entry entry) {
        public Join { Objects.requireNonNull(entry); }
    }
    /** Mechanical snapshot only, no row algorithm. */
    public static Join join(GovernmentCompaction160Api.Entry incoming, GovernmentPrimaryTail155Api.Registers r) {
        return new Join(0x30A376EL, new GovernmentCompaction160Api.Entry(
                incoming.imageBaseBits(),r.rsp,r.volatileBits(),r.nonvolatileBits()));
    }
}
