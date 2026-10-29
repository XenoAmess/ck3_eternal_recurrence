package org.xar.ck3.control.g2.m6.nativeai;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Pure reconstruction of current EXE 292E8D0/292E9B0 and inline 1A2B480.
 * Inputs are supplied raw character fields after the native full-ID lookup.
 * This class does not enumerate a family, resolve native memory, qualify a
 * source, evaluate CanSend, submit an action or grant a live planner input.
 */
public final class NativeInteractionQuickFilter {
    public static final String SOURCE_GRAPH = "m6-native-12004-source07";
    private NativeInteractionQuickFilter() {}

    /** Definition+2288..228B, bound by the current four parser branches. */
    public record QuickFlags(boolean adult, boolean attractedToOwner,
            boolean ownerAttracted, boolean prison) {}

    /** Actual unsigned byte fields +1A1 and +1A0, without invented enum names. */
    public record AttractionRaw(int sexByte, int preferenceByte) {
        public AttractionRaw { unsignedByte(sexByte); unsignedByte(preferenceByte); }
    }

    public sealed interface Component permits MissingComponent, PresentComponent {}
    public record MissingComponent() implements Component {}
    /** The prison quick gate only tests whether Character+1B0+288 is nonzero. */
    public record PresentComponent(boolean prisonComponentPresent) implements Component {}

    public record CharacterFacts(int ageSignedWord, AttractionRaw attraction, Component component) {
        public CharacterFacts {
            if (ageSignedWord < Short.MIN_VALUE || ageSignedWord > Short.MAX_VALUE) {
                throw new IllegalArgumentException("actual signed age WORD required");
            }
            Objects.requireNonNull(attraction, "attraction");
            Objects.requireNonNull(component, "component");
        }
    }

    /** Signed current settings at 5C6A15C and 5C69D10; no authored default. */
    public record AdultThresholds(int sexZero, int sexNonzero) {}

    /** Six bytes emitted by 292E8D0, expressed as distinct typed fields. */
    public record PreparedFlags(boolean adult, boolean allowSexNonzero, boolean allowSexZero,
            boolean attractedToOwner, int ownerSexByte, boolean prison) {
        public PreparedFlags { unsignedByte(ownerSexByte); }
    }

    public enum Resolution { EXACT_NATIVE_LOOKUP, NATIVE_FALLBACK }

    /**
     * The native manager uses a fallback character on a failed full-ID lookup.
     * Keep that supplied result explicit: the quick filter does not silently
     * replace native semantics with unconditional rejection or current proof.
     * Sentinel input is preserved here; later native preparation is separate.
     */
    public record ResolvedCandidate(long requestedFullId, Resolution resolution, CharacterFacts resolved) {
        public ResolvedCandidate {
            if (requestedFullId < 0 || requestedFullId > 0xFFFF_FFFFL) {
                throw new IllegalArgumentException("original uint32 candidate required");
            }
            Objects.requireNonNull(resolution, "resolution");
            Objects.requireNonNull(resolved, "resolved");
        }
    }

    public static PreparedFlags derive(QuickFlags flags, AttractionRaw owner) {
        Objects.requireNonNull(flags, "flags");
        Objects.requireNonNull(owner, "owner");
        boolean allowNonzero = true, allowZero = true;
        if (flags.ownerAttracted()) {
            switch (owner.preferenceByte()) {
                case 0 -> {
                    allowNonzero = owner.sexByte() != 1;
                    allowZero = owner.sexByte() != 0;
                }
                case 1 -> {
                    allowNonzero = owner.sexByte() == 1;
                    allowZero = owner.sexByte() == 0;
                }
                case 2 -> { /* Both bytes retain their native true default. */ }
                default -> { allowNonzero = false; allowZero = false; }
            }
        }
        return new PreparedFlags(flags.adult(), allowNonzero, allowZero,
                flags.attractedToOwner(), owner.sexByte(), flags.prison());
    }

    public static boolean passes(PreparedFlags flags, CharacterFacts target, AdultThresholds thresholds) {
        Objects.requireNonNull(flags, "flags");
        Objects.requireNonNull(target, "target");
        Objects.requireNonNull(thresholds, "thresholds");
        int sex = target.attraction().sexByte();
        if (flags.adult() && target.ageSignedWord()
                < (sex == 0 ? thresholds.sexZero() : thresholds.sexNonzero())) return false;
        if (!(sex == 0 ? flags.allowSexZero() : flags.allowSexNonzero())) return false;
        if (flags.attractedToOwner()) {
            boolean attracted = switch (target.attraction().preferenceByte()) {
                case 0 -> sex != flags.ownerSexByte();
                case 1 -> sex == flags.ownerSexByte();
                case 2 -> true;
                default -> false;
            };
            if (!attracted) return false;
        }
        return !flags.prison() || target.component() instanceof PresentComponent component
                && component.prisonComponentPresent();
    }

    /**
     * The caller walks backwards and removes failures by swapping with the
     * current last row. The surviving order feeds the subsequent max trim,
     * chance draw and native preparation; stable stream filtering differs.
     */
    public static List<ResolvedCandidate> filter(List<ResolvedCandidate> original,
            PreparedFlags flags, AdultThresholds thresholds) {
        List<ResolvedCandidate> rows = new ArrayList<>(List.copyOf(original));
        Objects.requireNonNull(flags, "flags");
        Objects.requireNonNull(thresholds, "thresholds");
        for (int i = rows.size() - 1; i >= 0; i--) {
            if (!passes(flags, rows.get(i).resolved(), thresholds)) {
                int last = rows.size() - 1;
                rows.set(i, rows.get(last));
                rows.remove(last);
            }
        }
        return List.copyOf(rows);
    }

    private static void unsignedByte(int value) {
        if (value < 0 || value > 255) throw new IllegalArgumentException("actual uint8 required");
    }
}
