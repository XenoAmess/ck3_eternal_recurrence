package org.xar.ck3.control.wave2.development.constructionscene;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Immutable declared projections of the existing SDK containers, never action authority. */
public final class ConstructionSceneModel {
    private ConstructionSceneModel() { }

    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("field presence and value disagree");
            }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nil() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean known() { return presence == Presence.VALUE; }
        public boolean is(T expected) { return known() && value.equals(expected); }
    }

    public record Snapshot(Field<Boolean> paused, Field<Integer> activeWarCount,
            Field<BigInteger> actorId, Field<BigInteger> nativeRevision, Field<BigInteger> publicRevision,
            Field<String> snapshotId, Field<BigInteger> dateRaw) {
        public Snapshot {
            Objects.requireNonNull(paused); Objects.requireNonNull(activeWarCount); Objects.requireNonNull(actorId);
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(publicRevision);
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(dateRaw);
            if (activeWarCount.known() && activeWarCount.value() < 0) { throw new IllegalArgumentException("negative war count"); }
        }
    }
    public record GovernmentObservation(Field<String> key, Field<List<String>> flags) {
        public GovernmentObservation {
            Objects.requireNonNull(key); Objects.requireNonNull(flags);
            if (flags.known()) { flags = Field.of(List.copyOf(flags.value())); }
        }
    }
    public record Position(Field<String> key, Field<BigInteger> incumbentId,
            Field<String> taskKey, Field<Boolean> frozen) {
        public Position {
            Objects.requireNonNull(key); Objects.requireNonNull(incumbentId);
            Objects.requireNonNull(taskKey); Objects.requireNonNull(frozen);
        }
    }
    public record Council(Field<String> status, Field<List<Position>> positions) {
        public Council {
            Objects.requireNonNull(status); Objects.requireNonNull(positions);
            if (positions.known()) { positions = Field.of(List.copyOf(positions.value())); }
        }
    }
    public record Root(Field<String> status, Field<BigInteger> revision, Field<BigInteger> dateRaw,
            Field<BigInteger> actorId, Field<GovernmentObservation> government, Field<Council> council) {
        public Root {
            Objects.requireNonNull(status); Objects.requireNonNull(revision); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(actorId); Objects.requireNonNull(government); Objects.requireNonNull(council);
        }
    }
    public record HistoryRow(Field<String> command, Field<Boolean> ok, Field<Root> root) {
        public HistoryRow { Objects.requireNonNull(command); Objects.requireNonNull(ok); Objects.requireNonNull(root); }
    }
    public record SceneInput(Snapshot snapshot, List<HistoryRow> history) {
        public SceneInput { Objects.requireNonNull(snapshot); history = List.copyOf(history); }
    }

    public enum Government { FEUDAL, CLAN }
    public enum RootScopeStatus { SCOPE_UNAVAILABLE, OUTSIDE_SCENE, ROOT_QUERY_NEEDED, ADMITTED }
    /** Unique helper result; the existing generic-perk wrapper requires a free government key. */
    public record RootScope(RootScopeStatus status, boolean atPeace, String governmentKey,
            BigInteger revision, BigInteger actorId, Field<Boolean> collectTaxesActive, GovernmentObservation government) {
        public RootScope {
            Objects.requireNonNull(status); Objects.requireNonNull(collectTaxesActive);
            if (status == RootScopeStatus.ADMITTED && (governmentKey == null || governmentKey.isEmpty()
                    || revision == null || actorId == null || government == null || collectTaxesActive.presence() == Presence.MISSING)) {
                throw new IllegalArgumentException("admitted root scope needs current observed government and nullable taxes");
            }
        }
    }
    public sealed interface Scope permits Unavailable, OutsideScene, RootQueryNeeded, Admitted { }
    public record Unavailable() implements Scope { }
    public record OutsideScene(boolean atPeace) implements Scope { }
    public record RootQueryNeeded(boolean atPeace) implements Scope { }
    /** Scene admission proves no final legality, affordability, submit or material postcondition. */
    public record Admitted(boolean atPeace, Government government, BigInteger revision,
            BigInteger actorId, Field<Boolean> collectTaxesActive) implements Scope {
        public Admitted {
            Objects.requireNonNull(government); Objects.requireNonNull(revision); Objects.requireNonNull(actorId);
            Objects.requireNonNull(collectTaxesActive);
            if (!ConstructionScenePolicy.validRevision(revision) || !ConstructionScenePolicy.validActor(actorId)) {
                throw new IllegalArgumentException("admitted scene needs native frame identity");
            }
            if (government == Government.CLAN && collectTaxesActive.presence() != Presence.MISSING) {
                throw new IllegalArgumentException("Clan scope has no collect_taxes_active field");
            }
            if (government == Government.FEUDAL && collectTaxesActive.presence() == Presence.MISSING) {
                throw new IllegalArgumentException("feudal scope retains nullable collect_taxes_active");
            }
        }
    }

    public record CashReadiness(Field<Boolean> sameFrame, Field<Boolean> treasury, Field<Boolean> gross,
            Field<Boolean> totalExpenses, Field<Boolean> net) {
        public CashReadiness {
            Objects.requireNonNull(sameFrame); Objects.requireNonNull(treasury); Objects.requireNonNull(gross);
            Objects.requireNonNull(totalExpenses); Objects.requireNonNull(net);
        }
    }
    public record CashPacket(Field<BigInteger> actorId, Field<BigInteger> revision, Field<BigInteger> dateRaw,
            Field<String> gameVersion, Field<Boolean> readOnly, Field<CashReadiness> readiness,
            Field<Boolean> monthlyIncomeSemanticsObject) {
        public CashPacket {
            Objects.requireNonNull(actorId); Objects.requireNonNull(revision); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(gameVersion); Objects.requireNonNull(readOnly); Objects.requireNonNull(readiness);
            Objects.requireNonNull(monthlyIncomeSemanticsObject);
        }
    }
    public record CashInput(Snapshot snapshot, Field<CashPacket> packet) {
        public CashInput { Objects.requireNonNull(snapshot); Objects.requireNonNull(packet); }
    }
    public enum CashReason {
        UNAVAILABLE("current native cash-v2 is unavailable for this Clan spend"),
        FRAME_MISMATCH("Clan cash and construction scene belong to different actor frames"),
        NET_UNOBSERVED("current native Clan NET or treasury is not observed");
        private final String wire;
        CashReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public sealed interface CashFrameResult permits CashFrameObserved, CashFrameDeferred { }
    public record CashFrameObserved() implements CashFrameResult { }
    public record CashFrameDeferred(CashReason reason) implements CashFrameResult {
        public CashFrameDeferred { Objects.requireNonNull(reason); }
    }
}
