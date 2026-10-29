package org.xar.ck3.control.events.mandatorychoice;

import static org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;

/** Pure presented-choice ordering. Calling this does not authorize a domain route or submit a token. */
public final class MandatoryChoicePolicy {
    private static final Set<String> NONCHOICE_ROLES = Set.of(
            "close", "close_x", "window_close", "decoration", "hud", "navigation");
    private static final Set<String> EXISTING_DOMAINS = Set.of("event");
    private static final Set<String> PRESENTATION_PROOFS = Set.of(
            "native_event_rendered_order", "source_bound_stock_interaction_GUI_order");
    private static final BigInteger FALLBACK_RENDERED_INDEX = BigInteger.ONE.shiftLeft(63);
    private record SelectionScope(FrameBinding frame) { }
    private MandatoryChoicePolicy() { }

    public static Decision selectUnknownMandatory(NativeWindow window, Optional<FrameBinding> expectedFrame) {
        return select(window, expectedFrame, Mode.UNKNOWN_MANDATORY);
    }

    public static Decision selectExistingNative(NativeWindow window, Optional<FrameBinding> expectedFrame) {
        return select(window, expectedFrame, Mode.EXISTING_NATIVE_DOMAIN);
    }

    public static Decision select(NativeWindow window, Optional<FrameBinding> expectedFrame, Mode mode) {
        Objects.requireNonNull(window); Objects.requireNonNull(expectedFrame); Objects.requireNonNull(mode);
        // Confined to this synchronous pure selection. It never qualifies a source, crosses a request,
        // survives a submission, or grants the caller a reusable observation token.
        SelectionScope scope = new SelectionScope(window.frame());
        return IndexedNativeChoices.build(scope, current -> {
            if (current != scope || !window.frame().equals(current.frame())) {
                throw new IllegalStateException("mandatory-choice invocation frame changed");
            }
        }, window).select(expectedFrame, mode);
    }

    /** Package adapter owns the exact complete window/index pair and the live owner scope. */
    static <S> Decision selectIndexed(NativeWindow window, Optional<FrameBinding> expectedFrame, Mode mode,
            OrderedCandidateIndex<S, ChoiceIdentity, ChoiceEntry> candidates) {
        return candidates.use(ignored -> selectInternal(window, expectedFrame, mode, candidates));
    }

    private static <S> Decision selectInternal(NativeWindow window, Optional<FrameBinding> expectedFrame, Mode mode,
            OrderedCandidateIndex<S, ChoiceIdentity, ChoiceEntry> candidates) {
        Objects.requireNonNull(window); Objects.requireNonNull(expectedFrame); Objects.requireNonNull(mode);
        List<Excluded> excluded = new ArrayList<>();
        List<Duplicate> duplicates = new ArrayList<>();
        if ("pending_character_interaction".equals(window.windowType())) {
            return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                    "pending_interaction_requires_dedicated_left_reply_policy", Status.MECHANISM_UNAVAILABLE);
        }
        if (mode == Mode.EXISTING_NATIVE_DOMAIN && !EXISTING_DOMAINS.contains(window.windowType())) {
            return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                    "existing_native_domain_not_authorized", Status.MECHANISM_UNAVAILABLE);
        }
        if (expectedFrame.isPresent() && !window.frame().equals(expectedFrame.orElseThrow())) {
            return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                    "native_frame_binding_changed", Status.STALE_FRAME);
        }
        boolean generic = mode == Mode.UNKNOWN_MANDATORY;
        if (generic && window.blockingProof().isEmpty()) {
            return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                    "native_simulation_or_exclusive_input_blocking_proof_unavailable", Status.NOT_MANDATORY);
        }
        if (generic && !window.choicesComplete()) {
            return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                    "native_complete_choice_list_unavailable", Status.MECHANISM_UNAVAILABLE);
        }
        List<NativeChoice> eligible = new ArrayList<>(), displayed = new ArrayList<>();
        for (int inputPosition = 0; inputPosition < window.choices().size(); inputPosition++) {
            ChoiceEntry row = window.choices().get(inputPosition);
            if (row instanceof NonChoiceRow nonChoice) {
                excluded.add(new Excluded(nonChoice.inputIndex(), Optional.empty(), "not_native_choice_mapping"));
                continue;
            }
            NativeChoice choice = (NativeChoice) row;
            var first = candidates.first(new OrderedCandidateIndex.Present<>(choice.identity())).orElseThrow();
            NativeChoice previous = first.position() == inputPosition ? null : (NativeChoice) first.value();
            if (previous != null) {
                if (!previous.original().equals(choice.original())) {
                    return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                            "conflicting_duplicate_native_choice_identity", Status.MECHANISM_UNAVAILABLE);
                }
                duplicates.add(new Duplicate(choice.inputIndex(), choice.identity()));
                continue;
            }
            if (generic && isTrue(choice.visible()) && isTrue(choice.isChoice())
                    && !(choice.role().hasValue() && NONCHOICE_ROLES.contains(choice.role().value()))) displayed.add(choice);
            String reason = !isTrue(choice.visible()) ? "invisible"
                    : !isTrue(choice.enabled()) ? "disabled" : !isTrue(choice.isChoice()) ? "nonchoice"
                    : choice.role().hasValue() && NONCHOICE_ROLES.contains(choice.role().value()) ? "nonchoice_role" : null;
            if (reason == null) { eligible.add(choice); }
            else { excluded.add(new Excluded(choice.inputIndex(), Optional.of(choice.identity()), reason)); }
        }
        // User continuation chooses the actual first display, then checks legality; a disabled left row cannot be skipped.
        if (generic && displayed.stream().anyMatch(choice -> !isTrue(choice.enabled()))) {
            if (displayed.size() > 1 && displayed.stream().anyMatch(choice -> choice.geometry().isEmpty()))
                return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                        "first_displayed_native_choice_order_unavailable", Status.MECHANISM_UNAVAILABLE);
            if (displayed.size() > 1) displayed.sort(boundsOrder());
            if (!isTrue(displayed.getFirst().enabled()))
                return unavailable(window, excluded, duplicates, Optional.of(displayed.size()==1?"single_visible_native_choice_no_geometry_needed":"native_bounds_top_then_left"),
                        displayed.stream().map(NativeChoice::identity).toList(),
                        displayed.getFirst().enabled().hasValue()?"first_displayed_native_choice_disabled":"first_displayed_native_choice_enabled_state_unavailable", Status.MECHANISM_UNAVAILABLE);
        }
        if (eligible.isEmpty()) {
            return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                    "no_visible_enabled_native_choice", Status.MECHANISM_UNAVAILABLE);
        }
        String order;
        if (eligible.size() == 1) {
            order = "single_visible_enabled_native_choice_no_geometry_needed";
        } else if (eligible.stream().allMatch(choice -> choice.geometry().isPresent())) {
            eligible.sort(boundsOrder());
            order = "native_bounds_top_then_left";
        } else {
            boolean proof = !generic && window.presentationOrderKind().hasValue()
                    && PRESENTATION_PROOFS.contains(window.presentationOrderKind().value());
            long distinctIndices = eligible.stream().filter(choice -> choice.renderedIndex().hasValue())
                    .map(choice -> choice.renderedIndex().value()).distinct().count();
            if (!proof || distinctIndices != eligible.size() || eligible.stream().anyMatch(choice ->
                    !choice.renderedIndex().hasValue() || choice.renderedIndex().value().signum() < 0)) {
                return unavailable(window, excluded, duplicates, Optional.empty(), List.of(),
                        "native_choice_geometry_or_authorized_presentation_order_unavailable", Status.MECHANISM_UNAVAILABLE);
            }
            eligible.sort(Comparator.comparing(choice -> choice.renderedIndex().value()));
            order = window.presentationOrderKind().value();
        }
        List<ChoiceIdentity> orderedIds = eligible.stream().map(NativeChoice::identity).toList();
        NativeChoice chosen = eligible.getFirst();
        if (chosen.nativeIndex().hasValue() && chosen.nativeIndex().value().signum() < 0) {
            return unavailable(window, excluded, duplicates, Optional.of(order), orderedIds,
                    "native_option_index_invalid", Status.MECHANISM_UNAVAILABLE);
        }
        boolean token = chosen.actionToken().hasValue() && !chosen.actionToken().value().isEmpty();
        if (!token && (generic || !chosen.existingTypedActionAvailable())) {
            return unavailable(window, excluded, duplicates, Optional.of(order), orderedIds,
                    "selected_native_choice_action_unavailable", Status.MECHANISM_UNAVAILABLE);
        }
        Evidence evidence = new Evidence(window, excluded, duplicates, Optional.of(order), orderedIds);
        return new Decision(Status.RECOMMENDED, "Select the first visible enabled native choice by " + order
                + "; label semantics do not block the user's continuation policy.", Optional.of(chosen), evidence);
    }

    private static Comparator<NativeChoice> boundsOrder() {
        return Comparator.comparingDouble((NativeChoice choice) -> orderCoordinate(choice.geometry().orElseThrow().top()))
                .thenComparingDouble(choice -> orderCoordinate(choice.geometry().orElseThrow().left()))
                .thenComparing(choice -> choice.renderedIndex().hasValue()
                        ? choice.renderedIndex().value() : FALLBACK_RENDERED_INDEX)
                .thenComparing(choice -> choice.identity().orderingKey(), MandatoryChoicePolicy::compareCodePoints);
    }
    private static boolean isTrue(Field<Boolean> value) { return value.hasValue() && value.value(); }
    /** Python numeric ordering equates signed zeros; only the derived key changes, never source bits. */
    private static double orderCoordinate(double value) { return value == 0.0 ? 0.0 : value; }
    /** Python compares Unicode code points; Java's default UTF-16 order differs for astral text. */
    private static int compareCodePoints(String left, String right) {
        int a = 0; int b = 0;
        while (a < left.length() && b < right.length()) {
            int leftPoint = left.codePointAt(a); int rightPoint = right.codePointAt(b);
            if (leftPoint != rightPoint) { return Integer.compare(leftPoint, rightPoint); }
            a += Character.charCount(leftPoint); b += Character.charCount(rightPoint);
        }
        return Integer.compare(left.length() - a, right.length() - b);
    }
    private static Decision unavailable(NativeWindow window, List<Excluded> excluded, List<Duplicate> duplicates,
            Optional<String> order, List<ChoiceIdentity> orderedIds, String reason, Status status) {
        return new Decision(status, reason, Optional.empty(), new Evidence(window, excluded, duplicates, order, orderedIds));
    }
}
