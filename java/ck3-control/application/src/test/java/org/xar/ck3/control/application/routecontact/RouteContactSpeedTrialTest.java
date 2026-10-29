package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceReadiness;
import org.xar.ck3.control.application.routecontact.RouteContactModel.*;

final class RouteContactSpeedTrialTest {
    static final class Journal implements ActionJournal, ActionJournal.LockedJournal {
        final List<ActionReceipt> rows = new ArrayList<>();
        @Override public <T> T locked(Function<ActionJournal.LockedJournal, T> operation) { return operation.apply(this); }
        @Override public Optional<ActionReceipt> find(String id) { return rows.stream().filter(row -> row.command().actionId().equals(id)).reduce((left, right) -> right); }
        @Override public List<ActionReceipt> unresolved() { return rows.stream().filter(row -> !row.settled()).toList(); }
        @Override public ActionReceipt append(ActionCommand command, String body, ActionState state) { ActionReceipt result = new ActionReceipt(1, rows.size() + 1, command, body, state); rows.add(result); return result; }
        @Override public ActionJournal.Snapshot snapshot() { return new ActionJournal.Snapshot(rows.size(), "a".repeat(64), rows, new ActionJournal.MissingHistoryBasis()); }
    }
    static CampaignDeadline.Configuration campaign() {
        return new CampaignDeadline.Configuration(new CampaignDeadline.Founding("campaign-1", "1066.9.15", BigInteger.valueOf(100), 1),
                CampaignDeadline.CALENDAR_PROFILE, BigInteger.valueOf(820), List.of(BigInteger.valueOf(100), BigInteger.valueOf(820)));
    }
    static AdvanceReadiness.Port ready() {
        return (parent, frame) -> new AdvanceReadiness.Facts(frame.identity(), Set.of(new OperationKey("set-speed-5"), new OperationKey("resume-map"), new OperationKey("pause-map")),
                Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N", "game.command.research-query-tactical-daily-sentinel-v1",
                        "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N", "game.command.query-route-contact-horizon-v1-N"),
                false, false, false, 45, RouteContactCompositeTest.EVIDENCE);
    }
    static RouteContactSpeedTrial trial(Journal journal) {
        return new RouteContactSpeedTrial(new RouteContactSpeedTrial.Configuration("campaign-1", "trial-1", 100, 820, 3, 3, false), campaign(), new ActionSnapshotReader(journal), ready());
    }
    static Proof proof() {
        Frame starting = RouteContactProofsTest.starting(); return RouteContactProofs.oneDay(starting, List.of(RouteContactProofsTest.query(starting)), List.of()).values().iterator().next();
    }
    static ActionCommand tagged(ActionCommand command, RouteContactSpeedTrial.Receipt selection) {
        return new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(), command.arguments().with(RouteContactSpeedTrial.KEY, selection.tag()),
                command.expected(), command.claims(), command.deadline());
    }
    @Test void highSpeedSelectionCannotConsumeBeforeDurableParentIntent() {
        Journal journal = new Journal(); var trial = trial(journal); var parent = RouteContactCompositeTest.command(false); var raw = RouteContactCompositeTest.raw(RouteContactCompositeTest.START);
        var selected = trial.plan(parent, raw, proof(), 3); assertEquals(5, selected.selectedSpeed()); assertFalse(selected.liveReady());
        assertThrows(IllegalStateException.class, () -> trial.select(tagged(parent, selected), raw, proof(), 3));
    }
    @Test void exactDurableParentBodyConsumesBeforeAnySetterArmOrResume() {
        Journal journal = new Journal(); var trial = trial(journal); var parent = RouteContactCompositeTest.command(false); var raw = RouteContactCompositeTest.raw(RouteContactCompositeTest.START);
        var selected = tagged(parent, trial.plan(parent, raw, proof(), 3)); journal.append(selected, ActionCodec.bodySha256(selected), new ActionState.IntentDurable());
        assertEquals(5, trial.select(selected, raw, proof(), 3)); assertEquals(1, journal.rows.size());
    }
    @Test void retainedUnknownClaimExhaustsTrialAcrossNewTrialObjectAndNewAction() {
        Journal journal = new Journal(); var firstTrial = trial(journal); var parent = RouteContactCompositeTest.command(false); var raw = RouteContactCompositeTest.raw(RouteContactCompositeTest.START);
        var selected = tagged(parent, firstTrial.plan(parent, raw, proof(), 3));
        journal.append(selected, ActionCodec.bodySha256(selected), new ActionState.Unknown(Optional.empty(), Optional.empty(), "original child was unknown", List.of(RouteContactCompositeTest.EVIDENCE)));
        ActionCommand next = new ActionCommand("route-b", parent.before(), parent.source(), parent.sessionId(), parent.operation(), parent.arguments(), parent.expected(), parent.claims(), parent.deadline());
        var result = trial(journal).plan(next, raw, proof(), 3); assertEquals("controlled_trial_attempt_exhausted", result.selectionStatus()); assertEquals(3, result.selectedSpeed());
    }
    @Test void equalCampaignNameWithDifferentFoundingDatesCannotReuseTrial() {
        assertThrows(IllegalArgumentException.class, () -> new RouteContactSpeedTrial(new RouteContactSpeedTrial.Configuration("campaign-1", "trial-1", 124, 844, 3, 3, false), campaign(), new ActionSnapshotReader(new Journal()), ready()));
    }
}
