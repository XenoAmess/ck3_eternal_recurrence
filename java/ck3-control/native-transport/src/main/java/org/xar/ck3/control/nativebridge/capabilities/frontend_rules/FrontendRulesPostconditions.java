package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Pure postcondition reducers. Only an independently collected later native observation can yield a proof. */
public final class FrontendRulesPostconditions {
    private FrontendRulesPostconditions() { }
    public record SelectionProof(RuleSelections before, RuleWindow windowBefore, RulesAck acknowledgement, RuleSelections observation) {
        public SelectionProof { Objects.requireNonNull(before); Objects.requireNonNull(windowBefore); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(observation); }
        public boolean appliedSettingsProven() { return false; }
    }
    public record ClosureProof(RuleSelections before, RulesAck acknowledgement, RuleWindow windowObservation) {
        public ClosureProof { Objects.requireNonNull(before); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(windowObservation); }
        public boolean windowClosedProven() { return true; }
        public boolean appliedSettingsProven() { return false; }
    }
    public record RouteProof(ObservedRoute before, NativeAck acknowledgement, ObservedRoute after) {
        public RouteProof { Objects.requireNonNull(before); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(after); }
        public boolean postconditionVerified() { return true; }
    }
    public record MapPost(String snapshotId, BigInteger nativeRevision, int dateRaw, BigInteger playerId, boolean paused, boolean mapReady) {
        public MapPost { require(snapshotId != null && !snapshotId.isEmpty(), "actual map snapshot identity required"); positiveU64(nativeRevision); positiveU64(playerId); }
    }
    public record CampaignRootPost(boolean ready, BigInteger queriedNativeRevision, int dateRaw, BigInteger playerId, String governmentKey) {
        public CampaignRootPost { positiveU64(queriedNativeRevision); positiveU64(playerId); Objects.requireNonNull(governmentKey); }
    }
    public record StartProof(ObservedRoute before, Candidate selectedCandidate, NativeAck acknowledgement, MapPost afterSnapshot, CampaignRootPost campaignRoot) {
        public StartProof { Objects.requireNonNull(before); Objects.requireNonNull(selectedCandidate); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(afterSnapshot); Objects.requireNonNull(campaignRoot); }
        public boolean postconditionVerified() { return true; }
    }
    public static void selectionPrecondition(RuleSelections initial, RuleWindow window, FrontendRulesRequests.SelectRule request) {
        require(initial.ready() && window.ready() && window.mayEdit() && !initial.appliedSettingsProven(), "selection requires actual editable window/current selections");
        require(initial.source().equals(window.source()), "selection window crossed frontend identity");
        require(initial.selected(request.ruleKey()).orElseThrow(() -> new IllegalArgumentException("rule absent from actual selections")).equals(request.expectedCurrentSettingKey()), "expected rule setting absent or stale");
    }
    public static SelectionProof selected(RuleSelections initial, RuleWindow window, FrontendRulesRequests.SelectRule request,
            RulesAck acknowledgement, BigInteger actionSequence, RuleSelections after) {
        selectionPrecondition(initial, window, request); require(acknowledgement.action() == RulesAction.SELECT && acknowledgement.ready() && acknowledgement.build() == initial.source().build(), "selection ACK unready/source drift");
        require(after.ready() && !after.appliedSettingsProven() && after.source().equals(initial.source()) && after.querySequence().compareTo(actionSequence) > 0, "selection lacks later independent bound query");
        List<Selection> expected = new ArrayList<>(); for (Selection value : initial.selections()) expected.add(value.ruleKey().equals(request.ruleKey()) ? new Selection(value.ruleKey(), request.desiredSettingKey()) : value);
        require(after.selections().equals(expected), "target or unrelated rule values changed after native Next"); return new SelectionProof(initial, window, acknowledgement, after);
    }
    public static void closurePrecondition(RuleSelections initial, RuleWindow window, RulesAction action) {
        require(action != RulesAction.SELECT && window.ready() && window.visible() && window.enabled(), "rule window action requires visible enabled actual window");
        require(action != RulesAction.APPLY_AND_HIDE || window.mayEdit(), "Apply requires actual stock host/not-started predicate");
        require(initial.ready() && !initial.appliedSettingsProven() && initial.source().equals(window.source()), "window action lacks bound current selections");
    }
    public static ClosureProof closed(RuleSelections initial, RulesAck ack, BigInteger actionSequence, RuleWindow after) {
        require(ack.ready() && ack.action() != RulesAction.SELECT && ack.build() == initial.source().build(), "window ACK unavailable/source drift");
        require(after.ready() && after.closed() && after.source().equals(initial.source()) && after.querySequence().compareTo(actionSequence) > 0, "window closure lacks later independent bound observation");
        return new ClosureProof(initial, ack, after);
    }
    public static RouteProof route(ObservedRoute before, NativeAck ack, BigInteger actionSequence, ObservedRoute after,
            Route expectedBefore, Route expectedAfter, String expectedStep) {
        require(before.route() == expectedBefore && after.route() == expectedAfter && ack.step().equals(expectedStep), "native frontend route postcondition failed");
        require(before.source().equals(after.source()) && after.querySequence().compareTo(actionSequence) > 0, "route transition lacks later same-process query");
        return new RouteProof(before, ack, after);
    }
    public static StartProof started(ObservedRoute before, Candidate candidate, NativeAck ack, MapPost map, CampaignRootPost root) {
        require(before.route() == Route.BOOKMARKS && before.source().equals(candidate.source()) && !candidate.scenario() && candidate.governmentKey().equals("feudal_government"), "ordinary start lacks selected feudal native model");
        require(ack.step().equals("activate-frontend-start-selected-bookmark-v1") && map.paused() && map.mapReady(), "Start ACK lacks independent paused map");
        require(candidate.dateRaw() == map.dateRaw() && root.ready() && root.queriedNativeRevision().equals(map.nativeRevision()) && root.dateRaw() == map.dateRaw()
                && root.playerId().equals(map.playerId()) && root.governmentKey().equals("feudal_government"), "Start lacks independent exact-date/player feudal campaign-root postcondition");
        return new StartProof(before, candidate, ack, map, root);
    }
}
