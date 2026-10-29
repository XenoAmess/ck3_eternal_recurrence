package org.xar.ck3.control.wave3.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.wave3.military.routereroute.RoutePlanningConsumer;
import org.xar.ck3.control.wave3.military.routereroute.RoutePreviewConsumerCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.*;

/** Ordinary ranked route consumer. One actual frame binds preview, complete native horizon and endpoint Contact.
 * Existing unsafe/threatened/refill, stationary Contact, rally, native validator and submitter remain caller-owned.
 */
public final class OrdinaryMilitaryConsumer {
    private OrdinaryMilitaryConsumer() { }
    public record Rollback(int armyId, int originProvinceId, int targetProvinceId, List<Integer> routeProvinceIds,
                           Optional<String> episodeRunId) {
        public Rollback {
            StrictJson.require(armyId >= 0 && originProvinceId > 0 && targetProvinceId > 0, "rollback subject binding required");
            routeProvinceIds = List.copyOf(routeProvinceIds); routeProvinceIds.forEach(value -> StrictJson.require(value > 0, "positive rollback Province required"));
            Objects.requireNonNull(episodeRunId); episodeRunId.ifPresent(StrictJson::text);
        }
        boolean matches(Current frame, int army, int origin, int target, List<Integer> route) {
            return armyId == army && originProvinceId == origin && targetProvinceId == target
                    && MilitaryRouteAudit.remaining(routeProvinceIds, origin).equals(route)
                    && (episodeRunId.isEmpty() || episodeRunId.orElseThrow().equals(frame.snapshot().capture().episodeRunId()));
        }
    }
    public record Input(RouteReevaluationCodec.Request route, SourceBoundContactIndex.Context origin,
                        List<ProjectedContactPolicy.QueryRow> effectiveContactRows, Optional<Integer> ownerCharacterId,
                        HostileScope hostileScope, List<HorizonEntry> effectiveHorizonHistory, List<Rollback> rollbackMemory) {
        public Input {
            Objects.requireNonNull(route); Objects.requireNonNull(origin); effectiveContactRows = List.copyOf(effectiveContactRows);
            Objects.requireNonNull(ownerCharacterId); ownerCharacterId.ifPresent(value -> StrictJson.require(value > 0, "positive owner required"));
            Objects.requireNonNull(hostileScope); effectiveHorizonHistory = List.copyOf(effectiveHorizonHistory); rollbackMemory = List.copyOf(rollbackMemory);
        }
    }
    public enum RejectedReason { GEOMETRY, NATIVE_CONTACT_VETO, CONTACT_TIMELINE_UNAVAILABLE, ROLLED_BACK_ROUTE }
    public record Rejected(int objectiveRank, Audit audit, RejectedReason reason) {
        public Rejected { StrictJson.require(objectiveRank >= 0, "nonnegative original rank required"); Objects.requireNonNull(audit); Objects.requireNonNull(reason); }
    }
    public sealed interface Result permits Unavailable, RouteBoundary, ReadRequired, PlanningContinuation {
        List<Rejected> routeRejections();
        List<RouteReevaluationPlanner.Rejection> previewRejections();
        default boolean actionAuthorized() { return false; }
        default boolean authorizesCommandReplay() { return false; }
        default boolean actualArrivalObserved() { return false; }
    }
    public enum Gap { CURRENT_SOURCE_UNAVAILABLE, INVALIDATED_FRAME, ROUTE_FRAME_DIFFERS, DEGENERATE_ENDPOINT_ENTRY }
    public record Unavailable(Gap gap, List<Rejected> routeRejections, List<RouteReevaluationPlanner.Rejection> previewRejections) implements Result {
        public Unavailable { Objects.requireNonNull(gap); routeRejections = List.copyOf(routeRejections); previewRejections = List.copyOf(previewRejections); }
    }
    /** The full ordinary caller continues its existing stationary/readiness/date/rally branch. No clock action is selected here. */
    public record RouteBoundary(RouteReevaluationPlanner.Result boundary, int originalRankOffset,
                                 List<Rejected> routeRejections, List<RouteReevaluationPlanner.Rejection> previewRejections) implements Result {
        public RouteBoundary { Objects.requireNonNull(boundary); StrictJson.require(originalRankOffset >= 0, "rank offset required"); routeRejections = List.copyOf(routeRejections); previewRejections = List.copyOf(previewRejections); }
    }
    public enum ReadKind { EXACT_ONE_DAY_ROUTE_CONTACT, PROJECTED_ENDPOINT_CONTACT }
    public record ReadRequired(ReadKind kind, String requiredStep, boolean stepAdvertised, int objectiveRank,
                               RouteReroutePolicy.Preview preview, Audit audit, List<Rejected> routeRejections,
                               List<RouteReevaluationPlanner.Rejection> previewRejections) implements Result {
        public ReadRequired {
            Objects.requireNonNull(kind); StrictJson.text(requiredStep); StrictJson.require(objectiveRank >= 0, "original rank required");
            Objects.requireNonNull(preview); Objects.requireNonNull(audit); routeRejections = List.copyOf(routeRejections); previewRejections = List.copyOf(previewRejections);
            binding(preview, audit);
            if (kind == ReadKind.PROJECTED_ENDPOINT_CONTACT) {
                StrictJson.require(audit.accepted() && endpointKey(preview, audit).step().equals(requiredStep), "endpoint query crossed the selected preview/route");
            } else validateHorizonStep(requiredStep, preview.armyId(), preview.targetProvinceId());
        }
    }
    /** Existing native move/can-move, strength/model, strategy and one shared reservation consumer follow this boundary. */
    public record PlanningContinuation(int objectiveRank, RouteReevaluationPlanner.CandidateSource source,
            RouteReroutePolicy.Preview preview, Audit audit, IndexedContactIngress.Decision endpointContact,
            List<Rejected> routeRejections, List<RouteReevaluationPlanner.Rejection> previewRejections) implements Result {
        public PlanningContinuation {
            StrictJson.require(objectiveRank >= 0, "original objective rank required"); Objects.requireNonNull(source);
            Objects.requireNonNull(preview); Objects.requireNonNull(audit); Objects.requireNonNull(endpointContact);
            StrictJson.require(audit.accepted() && !(endpointContact instanceof IndexedContactIngress.NeedsQuery), "fresh accepted planning operands required");
            binding(preview, audit);
            var expected = endpointKey(preview, audit); var selected = endpointContact.selection();
            StrictJson.require(expected.equals(selected.key()), "endpoint Contact key crossed selected preview/route");
            var scope = ((ProjectedContactPolicy.Available) selected).projection();
            StrictJson.require(scope.subjectArmyId() == preview.armyId() && scope.subjectCurrentProvinceId() == preview.originProvinceId()
                    && scope.targetProvinceId() == preview.targetProvinceId() && scope.incomingEntryProvinceId() == expected.incomingEntryProvinceId()
                    && scope.dateRaw() == preview.previewedDateRaw(), "endpoint Contact projection crossed selected preview/frame");
            routeRejections = List.copyOf(routeRejections); previewRejections = List.copyOf(previewRejections);
        }
        public boolean battleWinProbabilityKnown() { return false; }
    }

    public static Result plan(Input input) {
        Objects.requireNonNull(input);
        if (!(input.origin() instanceof Current current)) return new Unavailable(Gap.CURRENT_SOURCE_UNAVAILABLE, List.of(), List.of());
        if (current.invalidation() != SourceBoundContactIndex.Invalidation.NONE) return new Unavailable(Gap.INVALIDATED_FRAME, List.of(), List.of());
        RouteReroutePolicy.Lookup lookup = RoutePreviewConsumerCodec.decode(input.route().lookupPacket());
        if (!sameFrame(current, lookup.query())) return new Unavailable(Gap.ROUTE_FRAME_DIFFERS, List.of(), List.of());
        IndexedContactIngress.Frame contact = IndexedContactIngress.prepare(current, input.effectiveContactRows());
        List<RouteReevaluationPlanner.Objective> goals = input.route().orderedObjectives();
        List<Rejected> rejected = new ArrayList<>(); int offset = 0;
        List<RouteReevaluationPlanner.Rejection> previewRejected = new ArrayList<>();
        var newlyBlocked = new HashSet<Integer>();
        while (offset < goals.size()) {
            List<RouteReevaluationPlanner.Objective> remaining = new ArrayList<>();
            for (var goal : goals.subList(offset, goals.size())) remaining.add(new RouteReevaluationPlanner.Objective(
                    goal.targetProvinceId(), goal.source(), goal.blocked() || newlyBlocked.contains(goal.targetProvinceId())));
            RouteReevaluationPlanner.Result selected = RoutePlanningConsumer.planOrdinary(input.route().lookupPacket(), input.route().context(),
                    remaining, input.route().availableSteps());
            previewRejected.addAll(selected.rejections());
            if (!(selected instanceof RouteReevaluationPlanner.AuditContinuation candidate))
                return new RouteBoundary(selected, offset, rejected, previewRejected);
            int rank = offset + candidate.objectiveRank(); RouteReroutePolicy.Preview preview = candidate.preview();
            Audit audit = MilitaryRouteAudit.geometry(preview.routeProvinceIds(), lookup.query().originProvinceId(), candidate.targetProvinceId(), input.hostileScope().geometricRows());
            if (audit.status() == Status.ROUTE_DOES_NOT_REACH_TARGET) {
                rejected.add(new Rejected(rank, audit, RejectedReason.GEOMETRY)); newlyBlocked.add(candidate.targetProvinceId()); offset = rank + 1; continue;
            }
            if (input.hostileScope().nativeScopeSupported()) {
                HorizonLookup horizon = MilitaryRouteAudit.freshHorizon(input.effectiveHorizonHistory(), current, lookup.query().armyId(),
                        lookup.query().originProvinceId(), candidate.targetProvinceId(), input.hostileScope().armyIds(), preview.routeProvinceIds());
                if (horizon instanceof UnavailableHorizon) {
                    rejected.add(new Rejected(rank, audit, RejectedReason.CONTACT_TIMELINE_UNAVAILABLE)); newlyBlocked.add(candidate.targetProvinceId()); offset = rank + 1; continue;
                }
                if (horizon instanceof MissingHorizon) {
                    String step = MilitaryRouteAudit.horizonStep(lookup.query().armyId(), candidate.targetProvinceId(), input.hostileScope().armyIds());
                    return new ReadRequired(ReadKind.EXACT_ONE_DAY_ROUTE_CONTACT, step, input.route().availableSteps().contains(step), rank, preview, audit, rejected, previewRejected);
                }
                audit = MilitaryRouteAudit.consumeHorizon(audit, ((FoundHorizon) horizon).value(), candidate.source(), input.hostileScope().hostileOperationalOvermatch());
            }
            if (!audit.accepted()) {
                rejected.add(new Rejected(rank, audit, audit.horizonDecision() == HorizonDecision.NEGATIVE_VETO ? RejectedReason.NATIVE_CONTACT_VETO : RejectedReason.GEOMETRY));
                newlyBlocked.add(candidate.targetProvinceId()); offset = rank + 1; continue;
            }
            final Audit accepted = audit;
            if (input.rollbackMemory().stream().anyMatch(value -> value.matches(current, lookup.query().armyId(), lookup.query().originProvinceId(), candidate.targetProvinceId(), accepted.routeProvinceIds()))) {
                rejected.add(new Rejected(rank, audit, RejectedReason.ROLLED_BACK_ROUTE)); newlyBlocked.add(candidate.targetProvinceId()); offset = rank + 1; continue;
            }
            List<Integer> route = audit.routeProvinceIds(); int incoming = route.size() == 1 ? lookup.query().originProvinceId() : route.get(route.size() - 2);
            if (incoming == candidate.targetProvinceId()) return new Unavailable(Gap.DEGENERATE_ENDPOINT_ENTRY, rejected, previewRejected);
            var key = new ProjectedContactPolicy.QueryKey(lookup.query().armyId(), candidate.targetProvinceId(), incoming);
            var request = new ProjectedContactPolicy.Request(key, lookup.query().originProvinceId(), input.ownerCharacterId().orElse(null));
            IndexedContactIngress.Decision endpoint = contact.select(current, request);
            if (endpoint instanceof IndexedContactIngress.NeedsQuery)
                return new ReadRequired(ReadKind.PROJECTED_ENDPOINT_CONTACT, key.step(), input.route().availableSteps().contains(key.step()), rank, preview, audit, rejected, previewRejected);
            return new PlanningContinuation(rank, candidate.source(), preview, audit, endpoint, rejected, previewRejected);
        }
        return new RouteBoundary(new RouteReevaluationPlanner.Exhausted(List.of()), offset, rejected, previewRejected);
    }

    private static boolean sameFrame(Current current, RouteReroutePolicy.Query query) {
        if (query.dateRaw().isEmpty() || query.expectedLease().isEmpty() || query.dateRaw().orElseThrow() != current.snapshot().dateRaw()) return false;
        var lease = query.expectedLease().orElseThrow(); var capture = current.snapshot().capture();
        return capture.snapshotId().equals(lease.snapshotId()) && capture.episodeRunId().equals(lease.episodeRunId())
                && capture.revision().equals(BigInteger.valueOf(lease.revision())) && capture.nativeRevision().equals(BigInteger.valueOf(lease.nativeRevision()))
                && capture.connectionGeneration().equals(BigInteger.valueOf(lease.connectionGeneration()));
    }
    private static void binding(RouteReroutePolicy.Preview preview, Audit audit) {
        StrictJson.require(preview.status() == RouteReroutePolicy.PreviewStatus.AVAILABLE
                && preview.targetProvinceId() == audit.targetProvinceId()
                && MilitaryRouteAudit.remaining(preview.routeProvinceIds(), preview.originProvinceId()).equals(audit.routeProvinceIds()), "audit crossed selected preview/route");
    }
    private static ProjectedContactPolicy.QueryKey endpointKey(RouteReroutePolicy.Preview preview, Audit audit) {
        List<Integer> route = audit.routeProvinceIds();
        StrictJson.require(!route.isEmpty() && route.getLast() == preview.targetProvinceId(), "complete selected route required");
        int incoming = route.size() == 1 ? preview.originProvinceId() : route.get(route.size() - 2);
        return new ProjectedContactPolicy.QueryKey(preview.armyId(), preview.targetProvinceId(), incoming);
    }
    private static void validateHorizonStep(String step, int army, int target) {
        String prefix = "query-route-contact-horizon-v1-" + army + "-to-" + target + "-h-";
        StrictJson.require(step.startsWith(prefix), "horizon query crossed the selected subject/target");
        String[] parts = step.substring(prefix.length()).split("-", -1);
        StrictJson.require(parts.length > 1, "complete native hostile query required");
        int count = Integer.parseInt(parts[0]); StrictJson.require(count == parts.length - 1, "native hostile count differs");
        List<Integer> hostiles = new ArrayList<>(); for (int i = 1; i < parts.length; i++) hostiles.add(Integer.valueOf(parts[i]));
        StrictJson.require(step.equals(MilitaryRouteAudit.horizonStep(army, target, hostiles)), "canonical native hostile query required");
    }
}
