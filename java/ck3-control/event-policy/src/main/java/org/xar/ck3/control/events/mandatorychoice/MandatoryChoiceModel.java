package org.xar.ck3.control.events.mandatorychoice;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Immutable domain values. Native evidence is retained separately from fields used to choose. */
public final class MandatoryChoiceModel {
    private MandatoryChoiceModel() { }

    public enum Mode { UNKNOWN_MANDATORY, EXISTING_NATIVE_DOMAIN }
    public enum Status {
        RECOMMENDED("recommended"), MECHANISM_UNAVAILABLE("mechanism_unavailable"),
        STALE_FRAME("stale_frame"), NOT_MANDATORY("not_mandatory");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("field presence/value disagreement");
            }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nullValue() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean hasValue() { return presence == Presence.VALUE; }
    }
    /** Canonical JSON text, defensively immutable; only the boundary codec inspects it. */
    public record EvidenceDocument(String json) {
        public EvidenceDocument { Objects.requireNonNull(json); }
    }
    public sealed interface ChoiceIdentity permits TextIdentity, IntegerIdentity {
        String orderingKey();
    }
    public record TextIdentity(String value) implements ChoiceIdentity {
        public TextIdentity {
            Objects.requireNonNull(value);
            if (value.isEmpty()) { throw new IllegalArgumentException("choice identity cannot be empty"); }
        }
        @Override public String orderingKey() {
            StringBuilder output = new StringBuilder("\"");
            String hexadecimal = "0123456789abcdef";
            for (int index = 0; index < value.length(); index++) {
                char current = value.charAt(index);
                switch (current) {
                    case '"' -> output.append("\\\"");
                    case '\\' -> output.append("\\\\");
                    case '\b' -> output.append("\\b");
                    case '\f' -> output.append("\\f");
                    case '\n' -> output.append("\\n");
                    case '\r' -> output.append("\\r");
                    case '\t' -> output.append("\\t");
                    default -> {
                        if (current < 0x20) {
                            output.append("\\u00").append(hexadecimal.charAt(current >> 4))
                                    .append(hexadecimal.charAt(current & 15));
                        } else { output.append(current); }
                    }
                }
            }
            return output.append('"').toString();
        }
    }
    public record IntegerIdentity(BigInteger value) implements ChoiceIdentity {
        public IntegerIdentity { Objects.requireNonNull(value); }
        @Override public String orderingKey() { return value.toString(); }
    }
    public record FrameBinding(long gamePid, BigInteger connectionGeneration, BigInteger revision,
            BigInteger nativeRevision, BigInteger dateRaw, BigInteger actorCharacterId,
            String episodeRunId, String snapshotId, EvidenceDocument original) {
        public FrameBinding {
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(revision);
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(actorCharacterId); Objects.requireNonNull(episodeRunId);
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(original);
            if (gamePid < 1 || gamePid > 0xffff_ffffL || connectionGeneration.signum() <= 0
                    || revision.signum() < 0 || nativeRevision.signum() <= 0 || actorCharacterId.signum() <= 0
                    || episodeRunId.isEmpty() || snapshotId.isEmpty()) {
                throw new IllegalArgumentException("incomplete native frame");
            }
        }
    }
    public record Geometry(double top, double left) {
        public Geometry {
            if (!Double.isFinite(top) || !Double.isFinite(left)) {
                throw new IllegalArgumentException("nonfinite geometry");
            }
        }
    }
    public sealed interface ChoiceEntry permits NativeChoice, NonChoiceRow { }
    public record NonChoiceRow(int inputIndex) implements ChoiceEntry { }
    public record NativeChoice(int inputIndex, ChoiceIdentity identity,
            Field<Boolean> visible, Field<Boolean> enabled, Field<Boolean> isChoice,
            Field<String> role, Optional<Geometry> geometry, Field<BigInteger> renderedIndex,
            Field<BigInteger> nativeIndex, Field<String> actionToken,
            boolean existingTypedActionAvailable, EvidenceDocument original) implements ChoiceEntry {
        public NativeChoice {
            Objects.requireNonNull(identity); Objects.requireNonNull(visible); Objects.requireNonNull(enabled);
            Objects.requireNonNull(isChoice); Objects.requireNonNull(role); Objects.requireNonNull(geometry);
            Objects.requireNonNull(renderedIndex); Objects.requireNonNull(nativeIndex);
            Objects.requireNonNull(actionToken); Objects.requireNonNull(original);
        }
    }
    public record NativeWindow(FrameBinding frame, Field<ChoiceIdentity> windowId, String windowType,
            Field<String> queryId, Field<ChoiceIdentity> windowInstanceId,
            Field<EvidenceDocument> sourceIdentity, Optional<EvidenceDocument> blockingProof,
            boolean choicesComplete, Field<String> presentationOrderKind,
            List<ChoiceEntry> choices, EvidenceDocument originalChoices, EvidenceDocument original) {
        public NativeWindow {
            Objects.requireNonNull(frame); Objects.requireNonNull(windowId); Objects.requireNonNull(windowType);
            Objects.requireNonNull(queryId); Objects.requireNonNull(windowInstanceId); Objects.requireNonNull(sourceIdentity);
            Objects.requireNonNull(blockingProof); Objects.requireNonNull(presentationOrderKind);
            choices = List.copyOf(choices); Objects.requireNonNull(originalChoices); Objects.requireNonNull(original);
        }
    }
    public record Excluded(int index, Optional<ChoiceIdentity> choiceId, String reason) {
        public Excluded { Objects.requireNonNull(choiceId); Objects.requireNonNull(reason); }
    }
    public record Duplicate(int index, ChoiceIdentity choiceId) { }
    public record Evidence(NativeWindow window, List<Excluded> excluded, List<Duplicate> duplicatesRemoved,
            Optional<String> sortOrder, List<ChoiceIdentity> orderedEligibleChoiceIds) {
        public Evidence {
            Objects.requireNonNull(window); excluded = List.copyOf(excluded);
            duplicatesRemoved = List.copyOf(duplicatesRemoved); Objects.requireNonNull(sortOrder);
            orderedEligibleChoiceIds = List.copyOf(orderedEligibleChoiceIds);
        }
    }
    public record Decision(Status status, String reason, Optional<NativeChoice> selectedChoice,
            Evidence evidence) {
        public Decision {
            Objects.requireNonNull(status); Objects.requireNonNull(reason);
            Objects.requireNonNull(selectedChoice); Objects.requireNonNull(evidence);
            if ((status == Status.RECOMMENDED) != selectedChoice.isPresent()) {
                throw new IllegalArgumentException("recommended must identify exactly one native choice");
            }
        }
        public boolean dispatchAttempted() { return false; }
        public boolean commandAcknowledged() { return false; }
        public boolean originalWindowAdvancedVerified() { return false; }
        public boolean materialEffectsVerified() { return false; }
        public boolean replayAllowed() { return false; }
    }
}
