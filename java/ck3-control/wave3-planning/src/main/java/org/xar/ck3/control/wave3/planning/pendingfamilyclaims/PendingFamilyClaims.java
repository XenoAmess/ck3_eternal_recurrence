package org.xar.ck3.control.wave3.planning.pendingfamilyclaims;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.TreeSet;

/** Resource occupation only. It neither resolves a pending action nor reserves new resources. */
public final class PendingFamilyClaims {
    private PendingFamilyClaims() { }
    public enum AllianceIntent { HISTORICAL_CONSERVATIVE, EXPLICIT_ATTEMPT, EXPLICIT_NO_ATTEMPT }
    public record ActorEpisode(BigInteger actor, String episodeRunId) {
        public ActorEpisode { positive(actor); Objects.requireNonNull(episodeRunId);
            if (episodeRunId.isEmpty()) throw new IllegalArgumentException("empty episode"); }
    }
    public record FamilyPending(ActorEpisode scope, BigInteger heir, BigInteger candidate,
                                BigInteger recipient, AllianceIntent allianceIntent) {
        public FamilyPending { Objects.requireNonNull(scope); positive(heir); positive(candidate); positive(recipient); Objects.requireNonNull(allianceIntent); }
    }
    public record AlliancePair(BigInteger first, BigInteger second, boolean wouldAttemptIfAccepted) {
        public AlliancePair { positive(first); positive(second); }
    }
    public record ChildPending(ActorEpisode scope, BigInteger subject, BigInteger candidate,
                               BigInteger recipient, List<AlliancePair> observedPairs) {
        public ChildPending { Objects.requireNonNull(scope); positive(subject); positive(candidate); positive(recipient); observedPairs = List.copyOf(observedPairs); }
    }
    public record Claims(List<BigInteger> allyCharacterIds, List<BigInteger> characterIds, List<String> commitmentKeys) {
        public Claims {
            allyCharacterIds = List.copyOf(allyCharacterIds); characterIds = List.copyOf(characterIds); commitmentKeys = List.copyOf(commitmentKeys);
            allyCharacterIds.forEach(PendingFamilyClaims::positive); characterIds.forEach(PendingFamilyClaims::positive);
            require(allyCharacterIds.equals(sorted(allyCharacterIds)) && characterIds.equals(sorted(characterIds)), "claims must be sorted and distinct");
            require(new TreeSet<>(commitmentKeys).size() == commitmentKeys.size() && commitmentKeys.stream().noneMatch(String::isEmpty), "distinct nonempty commitment keys required");
        }
    }
    public static Claims family(ActorEpisode current, Optional<FamilyPending> pending) {
        Objects.requireNonNull(current); Objects.requireNonNull(pending);
        if (pending.isEmpty()) return empty();
        FamilyPending value = pending.orElseThrow(); require(current.equals(value.scope()), "pending family crossed actor episode");
        require(!value.heir().equals(value.candidate()) && !List.of(value.heir(), value.candidate(), value.recipient()).contains(current.actor()), "pending family role collision");
        return new Claims(value.allianceIntent() == AllianceIntent.EXPLICIT_NO_ATTEMPT ? List.of() : List.of(value.recipient()),
                sorted(List.of(value.heir(), value.candidate(), value.recipient())), List.of("first-heir-marriage:" + value.heir()));
    }
    public static Claims childDefault(ActorEpisode current, Optional<ChildPending> pending) {
        Objects.requireNonNull(current); Objects.requireNonNull(pending);
        if (pending.isEmpty()) return empty();
        ChildPending value = pending.orElseThrow(); require(current.equals(value.scope()), "pending child-default crossed actor episode");
        require(!value.subject().equals(value.candidate()) && !current.actor().equals(value.subject()) && !current.actor().equals(value.candidate()), "pending child-default role collision");
        TreeSet<BigInteger> allies = new TreeSet<>();
        for (AlliancePair pair : value.observedPairs()) if (pair.wouldAttemptIfAccepted()) {
            if (pair.first().equals(current.actor()) && !pair.second().equals(current.actor())) allies.add(pair.second());
            if (pair.second().equals(current.actor()) && !pair.first().equals(current.actor())) allies.add(pair.first());
        }
        TreeSet<BigInteger> characters = new TreeSet<>(List.of(value.subject(), value.candidate(), value.recipient())); characters.remove(current.actor());
        return new Claims(List.copyOf(allies), List.copyOf(characters), List.of("player-child-default-marriage:" + value.subject()));
    }
    private static Claims empty() { return new Claims(List.of(), List.of(), List.of()); }
    private static List<BigInteger> sorted(List<BigInteger> values) { return List.copyOf(new TreeSet<>(values)); }
    private static void positive(BigInteger value) { if (value == null || value.signum() <= 0) throw new IllegalArgumentException("positive integer identity required"); }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
