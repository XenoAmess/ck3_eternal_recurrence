package org.xar.ck3.control.wave2.military.warresultssource;

import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;

/** Pure native wire consistency validator. It establishes neither transport origin nor action success. */
public final class WarResultsSourceContract {
    public static final String VERSION = "1.20.0.4";
    public static final String EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");

    private WarResultsSourceContract() { }

    public enum Operation { QUERY, CLOSE }
    public enum Status { ABSENT, VISIBLE, HIDDEN, CLOSED_VERIFIED, ALREADY_ABSENT, ALREADY_HIDDEN, VERIFICATION_PENDING, UNAVAILABLE }
    public enum LookupSource { NONE, GUARDED_REGISTERED_TOP_LEVEL, GUARDED_TOP_LEVEL_AND_COMPLETE_OWNER_TREE }
    public enum DismissStage { NOT_ATTEMPTED, PREFLIGHT_REJECTED, CALLBACK_ENTERED, CALLBACK_RETURNED, CALLBACK_EXCEPTION }

    public record Build(String gameVersion, String executableSha256) {
        public Build { Objects.requireNonNull(gameVersion); Objects.requireNonNull(executableSha256); }
    }
    public record Binding(int actorId, int dateRaw, BigInteger nativeRevision) {
        public Binding { unsigned64(nativeRevision, false); }
    }
    public record NativeFrame(int actorId, int dateRaw, boolean paused, BigInteger revision, BigInteger connectionGeneration) {
        public NativeFrame { unsigned64(revision, false); unsigned64(connectionGeneration, false); }
    }
    public record OwnerReceipt(String requestId, BigInteger ticketSequence, BigInteger executorStartedSequence,
                               BigInteger completedSequence, BigInteger pumpEpoch, long threadId, int dateRaw,
                               BigInteger connectionGeneration) {
        public OwnerReceipt {
            text(requestId); unsigned64(ticketSequence, true); unsigned64(executorStartedSequence, true);
            unsigned64(completedSequence, true); unsigned64(pumpEpoch, true); unsigned32(threadId, true);
            unsigned64(connectionGeneration, true);
        }
    }
    public record LeafOwner(String requestId, BigInteger ticketSequence, BigInteger pumpEpoch, long threadId) {
        public LeafOwner { Objects.requireNonNull(requestId); unsigned64(ticketSequence, false); unsigned64(pumpEpoch, false); unsigned32(threadId, false); }
    }
    public record Visibility(boolean observed, boolean windowPresent, boolean effectiveVisible, LookupSource source) {
        public Visibility { Objects.requireNonNull(source); }
    }
    public record PostObservation(Visibility visibility, boolean scopeUnchanged) {
        public PostObservation { Objects.requireNonNull(visibility); }
    }
    public record Availability(boolean available, boolean accepted, Status status, String unavailableReason, boolean closureVerified) {
        public Availability { Objects.requireNonNull(status); Objects.requireNonNull(unavailableReason); }
    }
    public record DismissTrace(DismissStage stage, long exceptionCode) {
        public DismissTrace { Objects.requireNonNull(stage); unsigned32(exceptionCode, false); }
    }
    public record Dispatch(boolean attempted, boolean invoked, boolean nativeHandled, boolean ownerThreadVerified,
                           String buttonName, Optional<DismissTrace> dismissTrace) {
        public Dispatch { Objects.requireNonNull(buttonName); Objects.requireNonNull(dismissTrace); }
    }
    public record NativeLeaf(Operation operation, NativeFrame frame, Build build, LeafOwner owner, Visibility before,
                             PostObservation post, Availability availability, Dispatch dispatch) {
        public NativeLeaf {
            Objects.requireNonNull(operation); Objects.requireNonNull(frame); Objects.requireNonNull(build);
            Objects.requireNonNull(owner); Objects.requireNonNull(before); Objects.requireNonNull(post);
            Objects.requireNonNull(availability); Objects.requireNonNull(dispatch);
        }
    }
    public record Input(String expectedRequestId, Operation operation, Binding binding, BigInteger nativeGeneration,
                        OwnerReceipt ownerReceipt, NativeLeaf leaf) {
        public Input {
            text(expectedRequestId); Objects.requireNonNull(operation); Objects.requireNonNull(binding);
            unsigned64(nativeGeneration, false); Objects.requireNonNull(ownerReceipt); Objects.requireNonNull(leaf);
        }
    }

    /** Construction is restricted to this validator, and the scope remains wire consistency only. */
    public static final class ValidatedWire {
        private final Input input;
        private ValidatedWire(Input input) { this.input = input; }
        public Input input() { return input; }
        public NativeLeaf leaf() { return input.leaf(); }
    }

    public static OwnerReceipt validateOwner(OwnerReceipt owner, String expectedRequestId) {
        Objects.requireNonNull(owner); text(expectedRequestId);
        require(owner.requestId().equals(expectedRequestId), "independent TOP request differs");
        require(owner.ticketSequence().equals(owner.executorStartedSequence())
                && owner.ticketSequence().equals(owner.completedSequence()), "owner ticket did not start and complete independently");
        return owner;
    }

    public static ValidatedWire validate(Input input) {
        Objects.requireNonNull(input); OwnerReceipt receipt = validateOwner(input.ownerReceipt(), input.expectedRequestId());
        NativeLeaf leaf = input.leaf(); NativeFrame frame = leaf.frame(); LeafOwner owner = leaf.owner();
        Visibility before = leaf.before(); Visibility after = leaf.post().visibility();
        Availability availability = leaf.availability(); Dispatch dispatch = leaf.dispatch();
        require(leaf.operation() == input.operation(), "fixed operation differs");
        require(VERSION.equals(leaf.build().gameVersion()) && EXECUTABLE_SHA256.equals(leaf.build().executableSha256().toUpperCase(Locale.ROOT)), "different exact build");
        require(dispatch.buttonName().isEmpty() || dispatch.buttonName().equals("close_button"), "different fixed close target");
        require(frame.revision().equals(input.binding().nativeRevision()) && frame.connectionGeneration().equals(input.nativeGeneration()), "native revision/generation differs");
        require(owner.requestId().equals(receipt.requestId()) && owner.ticketSequence().equals(receipt.ticketSequence())
                && owner.pumpEpoch().equals(receipt.pumpEpoch()) && owner.threadId() == receipt.threadId()
                && frame.dateRaw() == receipt.dateRaw() && frame.connectionGeneration().equals(receipt.connectionGeneration()), "leaf differs from independent TOP owner receipt");
        validateVisibility(before); validateVisibility(after);
        if (before.observed() || availability.available() || dispatch.attempted()) {
            require(frame.actorId() == input.binding().actorId() && frame.dateRaw() == input.binding().dateRaw() && frame.paused(), "actor/date/pause differs from before lease");
        }
        require(!before.effectiveVisible() || before.windowPresent(), "visibility without window");
        require(!after.effectiveVisible() || after.windowPresent(), "post visibility without window");
        require(!dispatch.nativeHandled() || dispatch.invoked(), "native handled without invocation");
        require(!dispatch.invoked() || dispatch.attempted(), "invoked without attempted dispatch");
        if (dispatch.attempted()) {
            require(input.operation() == Operation.CLOSE && before.observed() && dispatch.ownerThreadVerified()
                    && before.windowPresent() && before.effectiveVisible() && !dispatch.buttonName().isEmpty(), "dispatch lacks qualified visible fixed target");
        }
        dispatch.dismissTrace().ifPresent(trace -> validateTrace(dispatch, trace));
        if (availability.available()) {
            require(before.observed() && after.observed() && leaf.post().scopeUnchanged() && dispatch.ownerThreadVerified()
                    && owner.pumpEpoch().signum() > 0 && owner.threadId() > 0 && availability.unavailableReason().isEmpty(), "availability lacks owner/post observation");
            if (input.operation() == Operation.QUERY) {
                Status expected = !before.windowPresent() ? Status.ABSENT : before.effectiveVisible() ? Status.VISIBLE : Status.HIDDEN;
                require(availability.status() == expected && availability.accepted() && !dispatch.attempted() && !dispatch.invoked()
                        && !dispatch.nativeHandled() && !availability.closureVerified() && dispatch.buttonName().isEmpty()
                        && after.windowPresent() == before.windowPresent() && after.effectiveVisible() == before.effectiveVisible(), "query differs from stable independent reads");
            } else if (availability.status() == Status.CLOSED_VERIFIED) {
                require(availability.accepted() && availability.closureVerified() && dispatch.attempted() && dispatch.invoked()
                        && !(after.windowPresent() && after.effectiveVisible()), "close is not post verified");
            } else {
                Status expected = !before.windowPresent() ? Status.ALREADY_ABSENT : Status.ALREADY_HIDDEN;
                require(availability.status() == expected && !before.effectiveVisible() && !availability.accepted()
                        && !availability.closureVerified() && !dispatch.attempted() && !dispatch.invoked() && !dispatch.nativeHandled()
                        && dispatch.buttonName().isEmpty() && after.windowPresent() == before.windowPresent()
                        && after.effectiveVisible() == before.effectiveVisible(), "no-op differs from actual non-dispatch observation");
            }
        } else {
            Status expected = dispatch.attempted() ? Status.VERIFICATION_PENDING : Status.UNAVAILABLE;
            require(availability.status() == expected && !availability.accepted() && !availability.closureVerified()
                    && hasPythonNonWhitespace(availability.unavailableReason()) && !(input.operation() == Operation.QUERY && dispatch.attempted()), "unavailable/pending overclaims an outcome");
        }
        return new ValidatedWire(input);
    }

    private static void validateVisibility(Visibility visibility) {
        require(!visibility.observed() || visibility.source() != LookupSource.NONE, "observed lookup lacks a guarded source");
        require(!visibility.observed() || visibility.windowPresent()
                || visibility.source() == LookupSource.GUARDED_TOP_LEVEL_AND_COMPLETE_OWNER_TREE, "absence lacks complete owner-tree observation");
    }
    private static void validateTrace(Dispatch dispatch, DismissTrace trace) {
        boolean valid = switch (trace.stage()) {
            case NOT_ATTEMPTED -> !dispatch.attempted() && !dispatch.invoked() && trace.exceptionCode() == 0;
            case PREFLIGHT_REJECTED, CALLBACK_ENTERED -> dispatch.attempted() && !dispatch.invoked() && trace.exceptionCode() == 0;
            case CALLBACK_RETURNED -> dispatch.attempted() && dispatch.invoked() && dispatch.nativeHandled() && trace.exceptionCode() == 0;
            case CALLBACK_EXCEPTION -> dispatch.attempted() && !dispatch.invoked() && trace.exceptionCode() != 0;
        };
        require(valid, "Dismiss stage contradicts dispatch");
    }
    private static boolean hasPythonNonWhitespace(String text) {
        return text.codePoints().anyMatch(code -> !(code >= 0x09 && code <= 0x0d || code >= 0x1c && code <= 0x20
                || code == 0x85 || code == 0xa0 || code == 0x1680 || code >= 0x2000 && code <= 0x200a
                || code == 0x2028 || code == 0x2029 || code == 0x202f || code == 0x205f || code == 0x3000));
    }
    private static void unsigned64(BigInteger value, boolean positive) {
        require(value != null && value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0 && value.compareTo(UINT64_MAX) <= 0, "uint64 outside domain");
    }
    private static void unsigned32(long value, boolean positive) { require(value >= (positive ? 1 : 0) && value <= 0xffff_ffffL, "uint32 outside domain"); }
    private static void text(String value) { require(value != null && !value.isEmpty(), "nonempty text required"); }
    private static void require(boolean valid, String message) { if (!valid) { throw new IllegalArgumentException(message); } }
}
