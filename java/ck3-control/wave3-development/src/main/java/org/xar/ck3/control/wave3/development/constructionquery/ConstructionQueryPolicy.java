package org.xar.ck3.control.wave3.development.constructionquery;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Field;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Presence;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Snapshot;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValuePolicy;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel.*;

/** Full query/envelope/source/ending-frame decision and unique authored selector.
 * Read-only material actor identity follows the shared Native signed32 contract. */
public final class ConstructionQueryPolicy {
    public static final String QUERY_NATIVE = "g2_player_construction_view_probe_v1";
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private ConstructionQueryPolicy() { }

    public static Result finalizeObservation(Observation observation) {
        if (observation.materialReceipt() && observation.wartimeObservation()) { return new Rejected(Rejection.SOURCE_MODES); }
        Frame starting = observation.starting(); Snapshot frame = starting.core();
        if (!bound(starting, observation.expectedRevision(), observation.wartimeObservation(), observation.materialReceipt())) { return new Rejected(Rejection.UNBOUND_FRAME); }
        Envelope envelope = observation.envelope();
        if (!envelope.type().is("command_result") || !envelope.protocolVersion().is(BigInteger.ONE)
                || !envelope.requestId().is(observation.requestId()) || !envelope.ok().is(true) || !envelope.result().known()) {
            return new Rejected(Rejection.NATIVE_READ_RETURN);
        }
        if (!(envelope.result().value() instanceof NativeResult result)) { return new SourceRed(); }
        if (!result.step().is(QUERY_NATIVE) || !result.accepted().is(true) || !result.probe().known()) { return new SourceRed(); }
        Probe probe = result.probe().value();
        if (!probe.advertised().is(false) || !same(probe.revision(), frame.nativeRevision()) || !same(probe.dateRaw(), frame.dateRaw())
                || !positiveU64(probe.proofEpoch()) || !probe.world().known()) { return new SourceRed(); }
        SourceWorld world = probe.world().value(); ConstructionValueModel.World values = world.values();
        if (!world.status().is("source_available") || !same(world.revision(), frame.nativeRevision())
                || !same(world.dateRaw(), frame.dateRaw()) || !same(world.actorId(), frame.actorId())
                || !world.nativeFinalLegalityEvaluated().is(true)
                || !(world.nativeCostEvaluated().is(true) || (observation.materialReceipt() && world.nativeCostEvaluated().is(false)))
                || !values.gold().known() || values.gold().value().signum() < 0 || !values.active().known()
                || !(values.inventoryObserved().is(true) && values.completed().known()
                    || values.inventoryObserved().is(false) && !values.completed().known())
                || !values.samples().known() || values.samples().value().stream().anyMatch(row -> !row.nativeCostObserved().is(true)
                    || !row.costs().known() || row.costs().value().size() != 10)
                || !same(observation.ending().core().snapshotId(), frame.snapshotId())
                || !same(observation.ending().core().publicRevision(), frame.publicRevision())
                || !getEqual(observation.ending().episode(), starting.episode())) { return new SourceRed(); }
        if (observation.materialReceipt()) { return new Ready(ReadyKind.MATERIAL_SOURCE, null); }
        ConstructionValueModel.Selection choice = ConstructionValuePolicy.select(new ConstructionValueModel.SelectionInput(values, observation.build().build()));
        if (choice instanceof ConstructionValueModel.Selected selected) { return new Ready(ReadyKind.SELECTED, selected.candidate()); }
        return new Ready(values.positiveIncomeCoverageComplete().is(true) ? ReadyKind.NO_LEGAL_BUDGETED_BUILDING : ReadyKind.EVIDENCE_INSUFFICIENT, null);
    }

    public static boolean bound(Frame observed, BigInteger expectedRevision, boolean wartimeObservation) {
        return bound(observed, expectedRevision, wartimeObservation, false);
    }
    private static boolean bound(Frame observed, BigInteger expectedRevision, boolean wartimeObservation, boolean materialReceipt) {
        Snapshot frame = observed.core();
        return frame.paused().is(true) && observed.mapReady().is(true) && observed.activeEvent() != Presence.VALUE
                && observed.pendingInteraction() != Presence.VALUE && frame.activeWarCount().known() && observed.armyCount().known()
                && (materialReceipt ? observedActor(frame.actorId()) : positiveActor(frame.actorId())) && observed.actorAlive().is(true) && positiveU64(frame.nativeRevision())
                && frame.snapshotId().is("native:" + frame.nativeRevision().value()) && frame.publicRevision().is(expectedRevision)
                && frame.dateRaw().known() && frame.dateRaw().value().compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0
                && frame.dateRaw().value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0
                && (wartimeObservation || observed.episode().known());
    }
    /** Read-only material world actors use Native signed32 identity; action/selection eligibility remains independent. */
    private static boolean observedActor(Field<BigInteger> value) {
        if (!value.known()) return false;
        try { NativeCharacterId.of(value.value()); return true; }
        catch (IllegalArgumentException invalid) { return false; }
    }
    private static boolean positiveActor(Field<BigInteger> value) {
        return value.known() && value.value().signum() > 0 && value.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0;
    }
    private static boolean positiveU64(Field<BigInteger> value) { return value.known() && value.value().signum() > 0 && value.value().compareTo(UINT64_MAX) <= 0; }
    private static <T> boolean same(Field<T> left, Field<T> right) { return left.known() && right.known() && left.value().equals(right.value()); }
    private static <T> boolean getEqual(Field<T> left, Field<T> right) {
        return !left.known() && !right.known() || same(left, right);
    }
}
