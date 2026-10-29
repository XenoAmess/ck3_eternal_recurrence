package org.xar.ck3.control.governance.council;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared Council19 observation contract. Candidate collection is not an assignment receipt. */
public final class CouncilModels {
    private CouncilModels() { }
    public enum Position {
        STEWARD("councillor_steward", "stewardship"), CHANCELLOR("councillor_chancellor", "diplomacy"),
        SPYMASTER("councillor_spymaster", "intrigue"), CHAPLAIN("councillor_court_chaplain", "learning");
        private final String key; private final String skill;
        Position(String key, String skill) { this.key = key; this.skill = skill; }
        public String key() { return key; }
        public String skill() { return skill; }
        public static Position exact(String key) {
            for (Position value : values()) if (value.key.equals(key)) return value;
            throw new IllegalArgumentException("unsupported council position");
        }
    }
    public enum ActionRoute { ASSIGN, REPLACE }
    public record Frame(String snapshotId, BigInteger publicRevision, BigInteger nativeRevision, int dateRaw, int ownerId) {
        public Frame {
            StrictJson.text(snapshotId); uint64(publicRevision, true); uint64(nativeRevision, true); characterId(ownerId);
        }
    }
    public record Fixed(long raw) { public static final int SCALE = 100_000; }
    public record TaskContext(int activeTaskId, int ownerId, OptionalInt incumbentId, Optional<String> taskKey,
            Optional<Boolean> frozen, int modifierId, int keywordId, Optional<String> observedKeywordKey) {
        public TaskContext {
            characterId(ownerId); Objects.requireNonNull(incumbentId); incumbentId.ifPresent(CouncilModels::characterId);
            Objects.requireNonNull(taskKey); Objects.requireNonNull(frozen); Objects.requireNonNull(observedKeywordKey);
            taskKey.ifPresent(StrictJson::text); observedKeywordKey.ifPresent(StrictJson::text);
            StrictJson.require(modifierId == 162 && keywordId == 11976, "actual4 current task tax descriptor mismatch");
        }
    }
    public sealed interface Tax permits AvailableTax, UnavailableTax { TaskContext context(); }
    public record AvailableTax(TaskContext context, Fixed value) implements Tax {
        public AvailableTax {
            Objects.requireNonNull(context); Objects.requireNonNull(value);
            StrictJson.require(context.incumbentId().isPresent() && context.taskKey().isPresent()
                    && context.frozen().isPresent() && context.observedKeywordKey().equals(Optional.of("domain_tax_mult")),
                    "available tax lacks the actual selected task component");
        }
    }
    public record UnavailableTax(TaskContext context, String reason) implements Tax {
        public UnavailableTax { Objects.requireNonNull(context); StrictJson.text(reason); }
    }
    public record Seat(Position position, OptionalInt incumbentId, OptionalInt incumbentSkill, ActionRoute route,
            Optional<Tax> tax) {
        public Seat {
            Objects.requireNonNull(position); Objects.requireNonNull(incumbentId); Objects.requireNonNull(incumbentSkill);
            Objects.requireNonNull(route); Objects.requireNonNull(tax); incumbentId.ifPresent(CouncilModels::characterId);
            StrictJson.require(incumbentId.isPresent() == incumbentSkill.isPresent(), "incumbent identity/skill readiness differs");
            incumbentSkill.ifPresent(value -> StrictJson.require(value >= 0, "negative incumbent skill"));
            StrictJson.require(route == (incumbentId.isPresent() ? ActionRoute.REPLACE : ActionRoute.ASSIGN), "vacancy/action route mismatch");
        }
    }
    public record Candidate(int characterId, long nativeCollectionOrdinal, int mainSkill, ActionRoute route) {
        public Candidate {
            CouncilModels.characterId(characterId); Objects.requireNonNull(route);
            StrictJson.require(nativeCollectionOrdinal >= 0 && nativeCollectionOrdinal <= 0xffff_ffffL && mainSkill >= 0,
                    "candidate ordinal or skill outside source domain");
        }
    }
    /** Defensively copied JSON for persistence and exact JSON-domain comparison. */
    public static final class JsonBody {
        private final byte[] bytes;
        public JsonBody(byte[] bytes) { this.bytes = StrictJson.canonical(StrictJson.parse(bytes)); }
        public byte[] bytes() { return bytes.clone(); }
        @Override public boolean equals(Object other) { return other instanceof JsonBody body && Arrays.equals(bytes, body.bytes); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }
    }
    public record Candidates(Frame frame, Seat seat, List<Candidate> candidates, JsonBody original) {
        public Candidates {
            Objects.requireNonNull(frame); Objects.requireNonNull(seat); candidates = List.copyOf(candidates); Objects.requireNonNull(original);
            StrictJson.require(candidates.stream().map(Candidate::characterId).distinct().count() == candidates.size(), "duplicate candidate identities");
            StrictJson.require(candidates.stream().allMatch(candidate -> candidate.route() == seat.route()), "candidate/seat action route mismatch");
        }
    }
    public static void characterId(int value) { StrictJson.require(value != -1, "invalid full CharacterID sentinel"); }
    public static void uint64(BigInteger value, boolean positive) {
        StrictJson.require(value != null && value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0
                && value.compareTo(StrictJson.UINT64_MAX) <= 0, "exact uint64 outside source domain");
    }
}
