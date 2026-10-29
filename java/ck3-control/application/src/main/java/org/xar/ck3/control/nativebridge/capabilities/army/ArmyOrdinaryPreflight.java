package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual registered queries, decoded identically during live preparation and archived revalidation. */
public final class ArmyOrdinaryPreflight {
    private ArmyOrdinaryPreflight() { }
    public enum Role { DEFAULT_RAISE, FAMILY_OBLIGATIONS, DECLARATIONS, DECLARATION_FINAL_ROLES,
        WAR_OPTIONS, WAR_TERMS, HOLDING_SIEGE, MERCENARY_MARKET, HOLY_ORDER_CONTEXT,
        OVERVIEW, RESULTS, GATHERING }
    public record Query<T>(Role role, ReadContract<T> contract, PlanningReadRequest request, Function<T,RawJson> encode) {
        public Query {
            Objects.requireNonNull(role); Objects.requireNonNull(contract); Objects.requireNonNull(request); Objects.requireNonNull(encode);
            StrictJson.require(contract.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    && contract.operation().equals(request.operation()), "Army preflight requires its installed gameplay read contract");
        }
        public RawJson replay(PlanningReadReceipt original) { return Objects.requireNonNull(encode.apply(contract.decode(original))); }
        public RawJson encodeReplay(PlanningReadReceipt original) { return Objects.requireNonNull(encode.apply(contract.replay(original))); }
    }
    @FunctionalInterface public interface Queries {
        /** Return the identical installed contracts used by actual public/domain read producers. */
        List<Query<?>> plans(ArmyCalls.Call input, ArmyTypes.Context source);
        /** Dependent reads may only construct their second contract after the first original Known receipt. */
        default List<Read> observe(ContinuityStorePort.Session same, ArmyCalls.Call call, ArmyTypes.Context context,
                Complete actual, PlanningReadPort reads, ActionPorts.OutcomeArchive archive) {
            return observePlans(same, ArmyOrdinaryPreflight.plans(this, call, context), actual, reads, archive);
        }
        /** Pure receipt replay has its own dependent-lease reconstruction and performs no Native read. */
        default List<Read> replay(ArmyCalls.Call call, ArmyTypes.Context context, Complete actual,
                List<ExactRef> references, ActionPorts.OutcomeArchive archive) {
            return replayPlans(ArmyOrdinaryPreflight.plans(this, call, context), actual, references, archive);
        }
    }
    public record Read(Role role, PlanningReadReceipt original, ExactRef reference, RawJson normalized) {
        public Read { Objects.requireNonNull(role); Objects.requireNonNull(original); Objects.requireNonNull(reference); Objects.requireNonNull(normalized); }
    }
    public static List<Read> observe(ContinuityStorePort.Session same, ArmyCalls.Call call, ArmyTypes.Context context,
            Complete actual, Queries queries, PlanningReadPort reads, ActionPorts.OutcomeArchive archive) {
        return List.copyOf(Objects.requireNonNull(queries).observe(same, call, context, actual, reads, archive));
    }
    private static List<Read> observePlans(ContinuityStorePort.Session same, List<Query<?>> plans, Complete actual,
            PlanningReadPort reads, ActionPorts.OutcomeArchive archive) {
        List<Read> result = new ArrayList<>(); for (Query<?> query : plans) result.add(observeOne(same, query, actual, reads, archive));
        return List.copyOf(result);
    }
    public static <T> Read observeOne(ContinuityStorePort.Session same, Query<T> query, Complete actual,
            PlanningReadPort reads, ActionPorts.OutcomeArchive archive) {
        var result = reads.read(same, query.contract(), query.request());
        if (!(result instanceof PlanningReadResult.Known<T> known))
            throw new IllegalStateException(((PlanningReadResult.Unavailable<T>) result).reason());
        return accept(query, known, actual, archive);
    }
    /** The real owning producer already returned Known and may have published its private lease. */
    public static <T> Read accept(Query<T> query, PlanningReadResult.Known<T> known, Complete actual, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(known.receipt().request().equals(query.request()), "actual Army producer returned a different original query");
        NativeRecordedEvidenceVerifier.requireRead(known.receipt(), archive);
        StrictJson.require(known.originalReceipt().equals(archive.readReferenceOf(known.receipt())), "preflight original receipt reference drift");
        bind(known.receipt(), actual);
        RawJson normalized = query.replay(known.receipt());
        StrictJson.require(normalized.equals(query.encode().apply(known.value())), "live Army query differs from its original receipt replay");
        return new Read(query.role(), known.receipt(), known.originalReceipt(), normalized);
    }
    public static List<Read> replay(ArmyCalls.Call call, ArmyTypes.Context context, Complete actual,
            List<ExactRef> references, Queries queries, ActionPorts.OutcomeArchive archive) {
        return List.copyOf(Objects.requireNonNull(queries).replay(call, context, actual, references, archive));
    }
    private static List<Read> replayPlans(List<Query<?>> plans, Complete actual, List<ExactRef> references, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(plans.size() == references.size(), "Army original preflight receipt inventory differs");
        List<Read> result = new ArrayList<>();
        for (int i = 0; i < plans.size(); i++) {
            result.add(replayOne(plans.get(i), actual, references.get(i), archive));
        }
        return List.copyOf(result);
    }
    public static Read replayOne(Query<?> query, Complete actual, ExactRef reference, ActionPorts.OutcomeArchive archive) {
        PlanningReadReceipt receipt = archive.loadRead(reference); NativeRecordedEvidenceVerifier.requireRead(receipt, archive);
        StrictJson.require(archive.readReferenceOf(receipt).equals(reference), "Army preflight receipt identity changed"); bind(receipt, actual);
        StrictJson.require(receipt.request().equals(query.request()), "Army original preflight request changed");
        RawJson normalized = query.encodeReplay(receipt);
        return new Read(query.role(), receipt, reference, normalized);
    }
    private static List<Query<?>> plans(Queries queries, ArmyCalls.Call call, ArmyTypes.Context source) {
        List<Query<?>> plans = List.copyOf(Objects.requireNonNull(queries).plans(call, source));
        requireInventory(plans);
        for (Query<?> query : plans) StrictJson.require(query.request().before().equals(source.before())
                && query.request().source().equals(source.source()) && query.request().sessionId().equals(source.sessionId())
                && query.request().deadline().equals(source.deadline()), "Army query factory crossed its actual caller source");
        return plans;
    }
    public static void requireInventory(List<Query<?>> plans) {
        StrictJson.require(plans.size() <= 16 && plans.stream().map(q -> q.request().operation()).distinct().count() == plans.size(), "bounded unique actual Army query operations required");
        for (Role role : Role.values()) if (role != Role.HOLDING_SIEGE)
            StrictJson.require(plans.stream().filter(q -> q.role() == role).count() <= 1, "duplicate Army preflight role");
    }
    public static void bind(PlanningReadReceipt read, Complete actual) {
        StrictJson.require(read.request().before().equals(actual.identity()) && read.request().source().equals(actual.source())
                && read.request().sessionId().equals(actual.sessionId()) && read.original().nativeOk(), "Army preflight is not from this actual frame");
        for (var guard : List.of(read.before(), read.after())) StrictJson.require(
                guard.binding().observed().equals(actual.identity()) && guard.binding().source().equals(actual.source())
                && guard.binding().sessionId().equals(actual.sessionId()) && guard.binding().connectionGeneration().equals(actual.connectionGeneration())
                && guard.binding().nativeEvidence().equals(actual.originalEvidence()) && guard.originalBindingSha256().equals(actual.fullBindingSha256()),
                "Army preflight crossed its complete Native/Driver binding");
    }
}
