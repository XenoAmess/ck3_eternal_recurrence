package org.xar.ck3.control.wave2.finance.factionculture;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Culture grievance inputs only; these types do not authorize any faction action. */
public final class FactionCultureModel {
    public static final int MAX_FACTIONS = 256;
    public static final int MAX_COUNTIES_PER_FACTION = 4096;
    private FactionCultureModel() { }

    public sealed interface CultureRelation permits AvailableCulture, UnavailableCulture { }
    public record AvailableCulture(int countyCultureId, int targetCultureId, boolean sameCulture) implements CultureRelation {
        public AvailableCulture {
            cultureId(countyCultureId); cultureId(targetCultureId);
            if (sameCulture != (countyCultureId == targetCultureId)) {
                throw new IllegalArgumentException("same culture must compare full CultureIDs");
            }
        }
    }
    public record UnavailableCulture(Optional<Integer> countyCultureId, Optional<Integer> targetCultureId) implements CultureRelation {
        public UnavailableCulture {
            Objects.requireNonNull(countyCultureId, "countyCultureId");
            Objects.requireNonNull(targetCultureId, "targetCultureId");
            countyCultureId.ifPresent(FactionCultureModel::cultureId);
            targetCultureId.ifPresent(FactionCultureModel::cultureId);
            if (countyCultureId.isPresent() && targetCultureId.isPresent()) {
                throw new IllegalArgumentException("unavailable relation requires at least one missing culture");
            }
        }
    }

    public record Frame(BigInteger snapshotRevision, int dateRaw, int playerCharacterId) {
        public Frame {
            Objects.requireNonNull(snapshotRevision, "snapshotRevision");
            if (snapshotRevision.signum() <= 0 || snapshotRevision.bitLength() > 64) {
                throw new IllegalArgumentException("snapshot revision must be uint64");
            }
            positive(playerCharacterId);
        }
    }
    public static final class ProvenanceDocument {
        private final byte[] json;
        ProvenanceDocument(byte[] json) { this.json = json.clone(); }
        public byte[] json() { return json.clone(); }
    }
    public record CountyMaterial(int countyTitleId, Optional<CultureRelation> relation) {
        public CountyMaterial {
            positive(countyTitleId);
            Objects.requireNonNull(relation, "relation");
        }
    }
    public record FactionProjection(int factionId, String factionTypeKey, int targetCharacterId,
                                     List<Integer> countyTitleIds, List<CountyMaterial> materials) {
        public FactionProjection {
            positive(factionId); positive(targetCharacterId);
            Objects.requireNonNull(factionTypeKey, "factionTypeKey");
            if (!factionTypeKey.matches("[a-z0-9_]+")) throw new IllegalArgumentException("stable faction key required");
            countyTitleIds = List.copyOf(countyTitleIds); materials = List.copyOf(materials);
            if (countyTitleIds.size() > MAX_COUNTIES_PER_FACTION || materials.size() > MAX_COUNTIES_PER_FACTION) {
                throw new IllegalArgumentException("county projection limit");
            }
            countyTitleIds.forEach(FactionCultureModel::positive);
        }
    }
    /** Supplied after the original complete alert/frame/provider checks. */
    public record AlertProjection(Frame frame, ProvenanceDocument provenance, List<FactionProjection> factions) {
        public AlertProjection {
            Objects.requireNonNull(frame, "frame"); Objects.requireNonNull(provenance, "provenance");
            factions = List.copyOf(factions);
            if (factions.size() > MAX_FACTIONS) throw new IllegalArgumentException("faction projection limit");
        }
    }

    public enum UnavailableReason {
        CULTURE_RELATION_UNAVAILABLE("culture_relation_unavailable"),
        CULTURE_FIELDS_NOT_PUBLISHED("culture_fields_not_published"),
        COUNTY_MEMBER_OBSERVATION_NOT_PUBLISHED("county_member_observation_not_published");
        private final String wire;
        UnavailableReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ContextStatus {
        NOT_APPLICABLE("not_applicable"), AVAILABLE("available"), PARTIAL("partial"), UNAVAILABLE("unavailable");
        private final String wire;
        ContextStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record ContextRow(int factionId, String factionTypeKey, int targetCharacterId, int countyTitleId,
                               Optional<CultureRelation> relation, Optional<UnavailableReason> unavailableReason) {
        public ContextRow {
            positive(factionId); positive(targetCharacterId); positive(countyTitleId);
            Objects.requireNonNull(factionTypeKey, "factionTypeKey");
            if (!factionTypeKey.matches("[a-z0-9_]+")) throw new IllegalArgumentException("stable faction key required");
            Objects.requireNonNull(relation, "relation"); Objects.requireNonNull(unavailableReason, "unavailableReason");
            if (relation.filter(AvailableCulture.class::isInstance).isPresent() != unavailableReason.isEmpty()) {
                throw new IllegalArgumentException("culture row readiness/reason mismatch");
            }
            if (relation.filter(UnavailableCulture.class::isInstance).isPresent()
                    && unavailableReason.orElseThrow() != UnavailableReason.CULTURE_RELATION_UNAVAILABLE) {
                throw new IllegalArgumentException("unknown relation reason mismatch");
            }
            if (relation.isEmpty() && unavailableReason.filter(reason -> reason == UnavailableReason.CULTURE_RELATION_UNAVAILABLE).isPresent()) {
                throw new IllegalArgumentException("unpublished culture differs from an observed unavailable relation");
            }
        }
        public boolean relationInputReady() { return relation.filter(AvailableCulture.class::isInstance).isPresent(); }
    }
    public record Context(Frame frame, ProvenanceDocument provenance, List<ContextRow> rows) {
        public Context {
            Objects.requireNonNull(frame, "frame"); Objects.requireNonNull(provenance, "provenance");
            rows = List.copyOf(rows);
        }
        public int availableRelationCount() { return Math.toIntExact(rows.stream().filter(ContextRow::relationInputReady).count()); }
        public boolean relationInputReady() { return !rows.isEmpty() && availableRelationCount() == rows.size(); }
        public ContextStatus status() {
            if (rows.isEmpty()) return ContextStatus.NOT_APPLICABLE;
            if (relationInputReady()) return ContextStatus.AVAILABLE;
            return availableRelationCount() > 0 ? ContextStatus.PARTIAL : ContextStatus.UNAVAILABLE;
        }
    }

    private static void cultureId(int value) {
        if (value == -1) throw new IllegalArgumentException("full CultureID sentinel -1 is not a culture");
    }
    private static void positive(int value) { if (value <= 0) throw new IllegalArgumentException("positive identity required"); }
}
