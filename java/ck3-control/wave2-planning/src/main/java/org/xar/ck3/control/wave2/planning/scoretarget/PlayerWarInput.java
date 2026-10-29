package org.xar.ck3.control.wave2.planning.scoretarget;

import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;

/** Declared projection of the existing saved character/war extension containers. */
public record PlayerWarInput(BigInteger actor, CharacterWars character, Map<String, WarEntry> wars) {
    public PlayerWarInput {
        Objects.requireNonNull(actor, "actor required");
        Objects.requireNonNull(character, "character fields required");
        wars = Map.copyOf(wars);
    }

    public record CharacterWars(ScalarField list, boolean explicitPresence, boolean conflicting, boolean incomplete) {
        public CharacterWars { Objects.requireNonNull(list, "list field required"); }
    }

    public sealed interface WarEntry permits ObservedWar, InvalidWar { }
    public record ObservedWar(ScalarField defender, boolean conflictingDefender) implements WarEntry {
        public ObservedWar { Objects.requireNonNull(defender, "defender field required"); }
    }
    public record InvalidWar(InvalidKind kind) implements WarEntry {
        public InvalidWar { Objects.requireNonNull(kind, "invalid row kind required"); }
    }
    public enum InvalidKind { NULL, BOOLEAN, INTEGER, FRACTIONAL, STRING, ARRAY }
}
