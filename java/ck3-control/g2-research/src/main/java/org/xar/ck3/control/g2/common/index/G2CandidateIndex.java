package org.xar.ck3.control.g2.common.index;

import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;
import org.xar.ck3.control.contracts.observation.ObservationReuse;
import org.xar.ck3.control.events.mandatorychoice.IndexedNativeChoices;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Source;

/**
 * Common/host typed join for an already issued source/frame/writer token and all domain candidates.
 * Request provenance cannot issue this token, qualify its sourceRef, or grant I/O or submission.
 * A host without the original owner's token must keep using its ordinary complete evaluation;
 * it cannot enable cross-request reuse by treating self-claimed JSON as a scope grant.
 */
public final class G2CandidateIndex {
    private G2CandidateIndex() { }

    public static <F extends Record, V extends Record, K, T>
            OrderedCandidateIndex<ObservationReuse.Token<G2Source, F>, K, T> build(
                    G2Source requestSource, ObservationReuse.Token<G2Source, F> token,
                    ObservationReuse<G2Source, F, V> owner, List<? extends T> completeCandidates,
                    Function<? super T, ? extends OrderedCandidateIndex.Key<K>> keyExtractor) {
        return OrderedCandidateIndex.build(token, guard(requestSource, token, owner),
                completeCandidates, keyExtractor);
    }

    /**
     * Rank the original complete native window through the existing mandatory-choice policy.
     * The original owner must have issued the exact source/frame token before this join is called.
     * This adapter owns no ordering, eligibility, duplicate, serialization or action policy.
     */
    public static <V extends Record> IndexedNativeChoices<ObservationReuse.Token<G2Source, FrameBinding>>
            nativeChoices(G2Source requestSource, ObservationReuse.Token<G2Source, FrameBinding> token,
                    ObservationReuse<G2Source, FrameBinding, V> owner, NativeWindow window) {
        Objects.requireNonNull(window, "original complete native window");
        var sourceGuard = guard(requestSource, token, owner);
        OrderedCandidateIndex.ScopeGuard<ObservationReuse.Token<G2Source, FrameBinding>> frameGuard = current -> {
            sourceGuard.requireCurrent(current);
            if (!window.frame().equals(current.scope().frame())) {
                throw new G2Exception(G2HttpError.Code.SOURCE_MISMATCH,
                        "candidate native window differs from original owner's frame");
            }
        };
        return IndexedNativeChoices.build(token, frameGuard, window);
    }

    private static <F extends Record, V extends Record>
            OrderedCandidateIndex.ScopeGuard<ObservationReuse.Token<G2Source, F>> guard(
                    G2Source requestSource, ObservationReuse.Token<G2Source, F> token,
                    ObservationReuse<G2Source, F, V> owner) {
        Objects.requireNonNull(requestSource, "original G2 request source");
        Objects.requireNonNull(token, "original owner's issued source/frame token");
        Objects.requireNonNull(owner, "original single owner");
        return current -> {
            owner.requireCurrent(current);
            if (!requestSource.equals(current.scope().source())) {
                throw new G2Exception(G2HttpError.Code.SOURCE_MISMATCH,
                        "candidate index source differs from request source");
            }
        };
    }
}
