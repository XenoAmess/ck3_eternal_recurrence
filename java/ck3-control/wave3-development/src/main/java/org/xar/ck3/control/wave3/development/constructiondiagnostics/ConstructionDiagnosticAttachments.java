package org.xar.ck3.control.wave3.development.constructiondiagnostics;

import java.util.Optional;
import static org.xar.ck3.control.wave3.development.constructiondiagnostics.ConstructionDiagnosticModel.*;

/** Typed replacement for the original exception attribute; no cause/object introspection or action authority. */
public final class ConstructionDiagnosticAttachments {
    private ConstructionDiagnosticAttachments() { }
    public interface DiagnosticCarrier { Projection constructionDiagnostic(); }
    public static Optional<Projection> extract(Throwable error) {
        if (!(error instanceof DiagnosticCarrier carrier)) return Optional.empty();
        Projection projection = carrier.constructionDiagnostic(); if (projection == null) return Optional.empty();
        ConstructionDiagnosticCodec.encode(projection); return Optional.of(projection);
    }
    public static final class TransportFailure extends IllegalStateException implements DiagnosticCarrier {
        private static final long serialVersionUID = 1L;
        private final transient Projection diagnostic;
        public TransportFailure(String message, Projection diagnostic, Throwable cause) {
            super(message, cause); ConstructionDiagnosticCodec.encode(diagnostic); this.diagnostic = diagnostic;
        }
        @Override public Projection constructionDiagnostic() { return diagnostic; }
    }
}
