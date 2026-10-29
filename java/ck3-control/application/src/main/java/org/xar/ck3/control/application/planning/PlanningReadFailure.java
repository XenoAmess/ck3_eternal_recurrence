package org.xar.ck3.control.application.planning;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Physical observation failure provenance; neither state authorizes replay of its original Native request. */
public final class PlanningReadFailure extends IOException {
    private static final long serialVersionUID = 1L;
    private enum Publication { NOT_COMPLETED, COMPLETED }
    private final Publication publication;

    private PlanningReadFailure(String message, Throwable original, Publication publication) {
        super(message, Objects.requireNonNull(original));
        this.publication = publication;
    }

    /** Only the physical observation transport boundary supplies this provenance, retaining its original failure. */
    public static PlanningReadFailure physical(IOException original) {
        return new PlanningReadFailure(physicalMessage(original),
                original, Publication.NOT_COMPLETED);
    }

    /** Retain the caught transport wrapper too: suppressed failures may belong to that wrapper. */
    public static PlanningReadFailure physical(UncheckedIOException original) {
        return new PlanningReadFailure(physicalMessage(original),
                original, Publication.NOT_COMPLETED);
    }

    private static String physicalMessage(Throwable original) {
        Objects.requireNonNull(original);
        return "actual physical observation READ failed; original request must not be replayed; original=" + original
                + (original.getCause() == null ? "" : "; original cause=" + original.getCause());
    }

    /** Called only after the original planning scope's one publication callback returned successfully. */
    public static Optional<PlanningReadFailure> afterPublication(Throwable original) {
        Objects.requireNonNull(original);
        Throwable physical = unwrap(original);
        if (!(physical instanceof PlanningReadFailure failure) || failure.publication != Publication.NOT_COMPLETED
                || !withoutSuppressed(original)) return Optional.empty();
        return Optional.of(new PlanningReadFailure("actual physical observation READ unavailable after original read publication completed; no request replay; physical=" + failure,
                original, Publication.COMPLETED));
    }

    /** Any suppressed failure, including one attached while releasing the writer, keeps the conservative writer path. */
    public static boolean hasCompletedPublication(Throwable original) {
        Objects.requireNonNull(original);
        return unwrap(original) instanceof PlanningReadFailure failure && failure.publication == Publication.COMPLETED
                && withoutSuppressed(original);
    }

    private static Throwable unwrap(Throwable original) {
        Throwable current = original;
        while (current instanceof UncheckedIOException wrapper) current = wrapper.getCause();
        return current;
    }

    private static boolean withoutSuppressed(Throwable original) {
        Set<Throwable> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (Throwable current = original; current != null && seen.add(current); current = current.getCause())
            if (current.getSuppressed().length != 0) return false;
        return true;
    }
}
