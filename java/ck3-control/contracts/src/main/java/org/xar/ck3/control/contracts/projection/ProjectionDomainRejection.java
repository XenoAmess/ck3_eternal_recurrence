package org.xar.ck3.control.contracts.projection;

/** A domain adapter may explicitly preserve an original public business refusal. It grants no fallback. */
public final class ProjectionDomainRejection extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    public ProjectionDomainRejection(String publicReason) { super(publicReason); }
}
