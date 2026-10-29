package org.xar.ck3.control.application.routecontact;

import java.util.Objects;
import java.util.Optional;
import java.util.List;
import java.time.Instant;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.CompositeActionPort.Children;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.AdvanceResult;
import org.xar.ck3.control.application.advance.AdvancePrimitiveEvidence;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceComposite;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceResultCodec;
import org.xar.ck3.control.application.routecontact.RouteContactModel.Proof;

/** Concrete wiring to the shared original clock translations; never a second native driver or an opaque composite step. */
public final class SharedRouteContactClocks implements RouteContactComposite.Clocks {
    private final BattleAdvanceComposite.WindowExecutor battle;
    private final AdvanceClock life;
    private final AdvanceObservationPort observations;
    private final Supplier<ActionPorts.OutcomeArchive> originals;
    private final Optional<NativeEffectEvidence.FrameLoader> frames;
    /** Historical construction only. A current clock must supply its actual same-writer archive before dispatch. */
    public SharedRouteContactClocks(BattleAdvanceComposite battle, AdvanceClock life, AdvanceObservationPort observations) {
        this(Objects.requireNonNull(battle)::executeWindow, life, observations,
                () -> {throw new IllegalStateException("current route clock requires its actual same-writer archive before dispatch");});
    }
    public SharedRouteContactClocks(BattleAdvanceComposite.WindowExecutor battle, AdvanceClock life, AdvanceObservationPort observations,
            Supplier<ActionPorts.OutcomeArchive> originals) {
        this(battle, life, observations, originals, Optional.empty());
    }
    public SharedRouteContactClocks(BattleAdvanceComposite.WindowExecutor battle, AdvanceClock life, AdvanceObservationPort observations,
            Supplier<ActionPorts.OutcomeArchive> originals, NativeEffectEvidence.FrameLoader frames) {
        this(battle, life, observations, originals, Optional.of(Objects.requireNonNull(frames)));
    }
    private SharedRouteContactClocks(BattleAdvanceComposite.WindowExecutor battle, AdvanceClock life, AdvanceObservationPort observations,
            Supplier<ActionPorts.OutcomeArchive> originals, Optional<NativeEffectEvidence.FrameLoader> frames) {
        this.battle = Objects.requireNonNull(battle); this.life = Objects.requireNonNull(life); this.observations = Objects.requireNonNull(observations);
        this.originals = Objects.requireNonNull(originals);
        this.frames = Objects.requireNonNull(frames);
    }
    private NativeEffectEvidence.FrameLoader actualFrames() { return frames.orElseThrow(() -> new IllegalStateException("current route clocks require the actual original Native/Driver frame loader before dispatch")); }
    @Override public RouteContactComposite.ClockResult window(ActionCommand parent, Children children, AdvanceObservationPort.Frame starting,
            Proof proof, int speed) throws InterruptedException {
        try {
            actualFrames();
            ActionPorts.OutcomeArchive archive = Objects.requireNonNull(originals.get(), "actual same-writer route archive required");
            var outcome = battle.executeWindow(parent, children, starting, new BattleAdvanceComposite.WindowRequest(proof.watchArmyIds(), proof.targetDateRaw(), speed));
            var progress = outcome.decisionBoundary().map(boundary -> switch (boundary.kind()) {
                case ACTIVE_EVENT, PENDING_CHARACTER_INTERACTION -> RouteContactComposite.ClockProgress.MODAL_INTERRUPTED;
                default -> RouteContactComposite.ClockProgress.BOUNDARY_INTERRUPTED;
            }).orElse(RouteContactComposite.ClockProgress.POSTCONDITION);
            return new RouteContactComposite.ClockResult(outcome.ending(), true, false, "native route window stop and original generation verified",
                    progress, outcome.plan().speed(), "bounded_frozen_route_window", outcome.decisionBoundary().isEmpty(), Optional.of(outcome.nativeStopRead()), List.of(),
                    Optional.of(BattleAdvanceResultCodec.completed(parent, outcome, archive)));
        } catch (BattleAdvanceComposite.Unresolved failure) {
            // The actual failure archive retains its own ending/Status. The last known start is not a progress poststate.
            return unresolved(starting, failure.getMessage(), failure.evidence(), speed, "bounded_frozen_route_window");
        }
    }
    @Override public RouteContactComposite.ClockResult exactDay(ActionCommand parent, Children children, AdvanceObservationPort.Frame starting,
            Proof proof, int speed) throws InterruptedException {
        try {
            actualFrames();
            ActionPorts.OutcomeArchive archive = Objects.requireNonNull(originals.get(), "actual same-writer route archive required");
            int firstChild = children.completed().size();
            String kind = proof.kind() == RouteContactModel.ProofKind.CONTACT_FREE ? "contact_free" : "unavoidable_current_province_contact";
            var detailed = life.executeExactDetailed(parent, children, starting, speed, kind);
            var outcome = detailed.outcome();
            var diagnostic = outcome.diagnostics();
            return new RouteContactComposite.ClockResult(outcome.endingFrame(), true, false, "native exact-day stop and original generation verified",
                    RouteContactComposite.ClockProgress.valueOf(diagnostic.progressStatus().name()), diagnostic.timelineSpeed(), diagnostic.timelinePolicy(),
                    diagnostic.progressStatus() == AdvanceClock.ProgressStatus.POSTCONDITION, diagnostic.nativeStopRead(), List.of(),
                    Optional.of(new AdvanceResult(parent, detailed.plan(), starting, outcome,
                            List.copyOf(children.completed().subList(firstChild, children.completed().size()))).encode(archive)));
        } catch (AdvanceClock.ChildUnresolved unknown) {
            return unresolved(starting, unknown.getMessage(), List.of(), speed, "exact_one_day_unresolved");
        } catch (RuntimeException failure) {
            return unresolved(starting, failure.getClass().getSimpleName() + ": " + failure.getMessage(), List.of(), speed, "exact_one_day_unresolved");
        }
    }
    static RouteContactComposite.ClockResult unresolved(AdvanceObservationPort.Frame starting, String reason, List<org.xar.ck3.control.contracts.ExactRef> originals, int speed, String policy) {
        return new RouteContactComposite.ClockResult(starting, false, true, reason, RouteContactComposite.ClockProgress.POSTCONDITION_FAILED,
                speed, policy, false, Optional.empty(), originals);
    }
    @Override public RouteContactComposite.PauseRefresh refreshPaused(ActionCommand parent, Children children, AdvanceObservationPort.Frame ending, Instant deadline) {
        NativeEffectEvidence.FrameLoader actualFrames = actualFrames();
        ActionPorts.OutcomeArchive archive = Objects.requireNonNull(originals.get(), "actual same-writer route archive required");
        ActionReceipt child;
        try { child = life.submit(parent, children, ending, "pause-map", deadline); }
        catch (AdvanceClock.ChildUnresolved unknown) { return new RouteContactComposite.PauseRefresh(unknown.receipt(), "unknown"); }
        if (!RouteContactComposite.currentPauseConfirmed(child)) return new RouteContactComposite.PauseRefresh(child, "rejected");
        String status;
        try { status = child.ack().map(ack -> AdvancePrimitives.nativeResult(ack, "pause-map").path("status"))
                .filter(node -> node.isTextual()).map(node -> node.textValue()).orElse("missing_original_ack_status"); }
        catch (IllegalArgumentException malformed) { status = "invalid_original_ack_status"; }
        return new RouteContactComposite.PauseRefresh(child, status, Optional.of(AdvancePrimitiveEvidence.compatiblePauseResult(child, archive, actualFrames)));
    }
}
