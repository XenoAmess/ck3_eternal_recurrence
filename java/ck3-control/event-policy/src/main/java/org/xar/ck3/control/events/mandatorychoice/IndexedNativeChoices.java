package org.xar.ck3.control.events.mandatorychoice;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceEntry;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Decision;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Mode;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;

/**
 * A reusable complete choice catalogue bound to the original owner's source/frame token.
 * Existing policy owns eligibility, duplicate conflicts and display ordering. The index stores
 * every input entry, including nonchoices, disabled entries and repeated identities.
 */
public final class IndexedNativeChoices<S> {
    private final NativeWindow window;
    private final OrderedCandidateIndex<S, ChoiceIdentity, ChoiceEntry> index;

    private IndexedNativeChoices(NativeWindow window,
            OrderedCandidateIndex<S, ChoiceIdentity, ChoiceEntry> index) {
        this.window = window;
        this.index = index;
    }

    public static <S> IndexedNativeChoices<S> build(S scope,
            OrderedCandidateIndex.ScopeGuard<? super S> guard, NativeWindow window) {
        Objects.requireNonNull(window, "original complete choice window");
        var index = OrderedCandidateIndex.<S, ChoiceIdentity, ChoiceEntry>build(scope, guard,
                window.choices(), entry -> entry instanceof NativeChoice choice
                        ? new OrderedCandidateIndex.Present<>(choice.identity())
                        : new OrderedCandidateIndex.Missing<>());
        return new IndexedNativeChoices<>(window, index);
    }

    public List<OrderedCandidateIndex.Slot<ChoiceIdentity, ChoiceEntry>> entries() {
        return index.slots();
    }

    public List<OrderedCandidateIndex.Slot<ChoiceIdentity, ChoiceEntry>> matching(ChoiceIdentity identity) {
        return index.matching(new OrderedCandidateIndex.Present<>(Objects.requireNonNull(identity)));
    }

    /** No action is submitted, no pending state is cleared, and UNKNOWN never becomes a recommendation. */
    public Decision select(Optional<FrameBinding> expectedFrame, Mode mode) {
        Objects.requireNonNull(expectedFrame, "expected native frame");
        Objects.requireNonNull(mode, "original policy mode");
        return MandatoryChoicePolicy.selectIndexed(window, expectedFrame, mode, index);
    }
}
