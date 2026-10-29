package org.xar.ck3.control.application.planning.governance;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadFailure;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual read-only failed mailbox closure. Native owns original-chain/transport classification and replay. */
public record CouncilTechnicalReadFailure(PlanningReadRequest originalRequest, PlanningReadFailure failure,
        List<PlanningReadReceipt> priorReads, List<ExactRef> originals, ExactRef diagnostic) {
    public static final String QUERY = "private-query-council-composition-candidates-v1";
    public static final String GATES = "private-query-council-final-gates-v1";
    public static final String STATUS = "private-council-application-main-status-v1";
    public CouncilTechnicalReadFailure {
        Objects.requireNonNull(originalRequest); Objects.requireNonNull(failure); Objects.requireNonNull(diagnostic);
        priorReads = List.copyOf(priorReads); originals = List.copyOf(originals);
        StrictJson.require(priorReads.size() <= 3001 && !originals.isEmpty() && originals.size() <= 32 && originals.contains(diagnostic)
                && originals.contains(failure.originalRef()) && originals.contains(failure.preparedRef())
                && originals.stream().allMatch(ref -> ref.bytes() > 0)
                && originals.stream().distinct().count() == originals.size(), "complete actual Council failed-read originals required");
    }
    /** DATA validation never creates a read permit or marks an action settled. */
    public void requireCurrent(PlanningRequest current, CouncilSelection.Position position) {
        Objects.requireNonNull(current); Objects.requireNonNull(position);
        String initial = originalRequest.operation().value();
        StrictJson.require((initial.equals(QUERY) || initial.equals(GATES))
                && originalRequest.arguments().equals(new Obj(Map.of()).with("position_key", new Text(position.key())))
                && originalRequest.before().equals(current.before()) && originalRequest.source().equals(current.source())
                && originalRequest.sessionId().equals(current.sessionId()) && originalRequest.deadline().equals(current.deadline()),
                "technical Council read crossed its actual current role/frame/source/session/deadline");
        var request = failure.request();
        boolean initialFailure = request.operation().equals(originalRequest.operation());
        StrictJson.require((initialFailure || request.operation().value().equals(STATUS))
                && request.before().equals(originalRequest.before()) && request.source().equals(originalRequest.source())
                && request.sessionId().equals(originalRequest.sessionId()) && request.deadline().equals(originalRequest.deadline())
                && (initialFailure ? request.equals(originalRequest) && priorReads.isEmpty() : request.arguments().equals(new Obj(Map.of())) && !priorReads.isEmpty())
                && failure.prepared().step().equals(request.operation().value())
                && parse(failure.prepared().additionalFields().bytes()).equals(request.arguments()),
                "technical Council failure is not the original read-only query/status chain");
        var ids = new HashSet<String>();
        ids.add(failure.requestId());
        for (int index = 0; index < priorReads.size(); index++) {
            PlanningReadReceipt read = priorReads.get(index);
            OperationKey expectedOperation = index == 0 ? originalRequest.operation() : new OperationKey(STATUS);
            var expectedArguments = index == 0 ? originalRequest.arguments() : new Obj(Map.of());
            StrictJson.require(read.request().before().equals(originalRequest.before())
                    && read.request().source().equals(originalRequest.source())
                    && read.request().sessionId().equals(originalRequest.sessionId())
                    && read.request().deadline().equals(originalRequest.deadline())
                    && read.request().operation().equals(expectedOperation)
                    && read.request().arguments().equals(expectedArguments) && ids.add(read.requestId()),
                    "technical Council prior reads crossed their actual chain or repeated a request ID");
            requireFrame(read.before(), read.request(), failure.before());
            requireFrame(read.after(), read.request(), failure.before());
            StrictJson.require(read.before().originalBindingSha256().equals(read.after().originalBindingSha256()),
                    "technical Council prior READ changed its actual before/after native binding");
        }
        var before = failure.before(); var after = failure.after();
        var first = before.binding(); var last = after.binding();
        StrictJson.require(before.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && after.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && before.paused() && before.mapReady() && before.playerAlive() && after.paused() && after.mapReady() && after.playerAlive()
                && first.origin() instanceof CommandOrigin.Gameplay && first.origin().equals(last.origin())
                && first.observed().equals(current.before()) && last.observed().equals(first.observed()) && first.source().equals(current.source()) && last.source().equals(first.source())
                && first.sessionId().equals(current.sessionId()) && last.sessionId().equals(first.sessionId())
                && first.operation().equals(request.operation()) && last.operation().equals(first.operation())
                && first.connectionGeneration().equals(last.connectionGeneration()) && first.authorityId().equals(last.authorityId())
                && before.originalBindingSha256().equals(after.originalBindingSha256()),
                "technical Council failure has no actual same living paused frame after-read proof");
    }
    private static void requireFrame(PlanningReadGuard actual, PlanningReadRequest request, PlanningReadGuard failedBefore) {
        var binding = actual.binding(); var original = failedBefore.binding();
        StrictJson.require(actual.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && actual.paused() && actual.mapReady() && actual.playerAlive()
                && binding.origin().equals(request.origin()) && binding.observed().equals(request.before())
                && binding.source().equals(request.source()) && binding.sessionId().equals(request.sessionId())
                && binding.operation().equals(request.operation())
                && binding.connectionGeneration().equals(original.connectionGeneration())
                && binding.authorityId().equals(original.authorityId()),
                "technical Council prior read has no same living paused frame/source/session/connection proof");
    }
}
