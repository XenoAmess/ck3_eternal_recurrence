package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.FrontendFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract.*;

/** Original bounded custom-ruler orchestration over the sole actual menu port.
 * DATA classification never grants native selected/ineligible eligibility, a lease, or replay authority.
 */
public final class FrontendCustomRulerPreparation {
    public static final int MAX_DRAWS = 8;
    public static final Duration DESIGNER_OBSERVATION_TIMEOUT = Duration.ofSeconds(2);
    public static final String SELECT_RANDOM_STEP = "activate-frontend-select-random-playable-v1";
    private FrontendCustomRulerPreparation() { }

    public interface Port {
        Transition pickAny() throws IOException, InterruptedException;
        Tree randomTarget() throws IOException, InterruptedException;
        /** Send once and observe within DESIGNER_OBSERVATION_TIMEOUT; missing evidence never means ineligible. */
        DrawOutcome drawOnce(int attempt1to8) throws IOException, InterruptedException;
    }
    public sealed interface DrawOutcome permits DesignerReady, SelectedIneligible, Unavailable, Unresolved { }
    public record DesignerReady(ActionReceipt action, RawJson acknowledgement, Tree observation) implements DrawOutcome {
        public DesignerReady {
            resolved(action, acknowledgement, observation);
            StrictJson.require(!observation.actual().value().truncated()
                    && observation.actual().value().defaultDesignerReady(), "independent default designer target is unavailable");
        }
    }
    /** Only the actual selected/ineligible producer may classify this branch.
     * A negative GUI tree, ACK, timeout, or this record's construction is not such a proof.
     */
    public record SelectedIneligible(ActionReceipt action, RawJson acknowledgement, Tree observation) implements DrawOutcome {
        public SelectedIneligible {
            resolved(action, acknowledgement, observation);
            StrictJson.require(!observation.actual().value().truncated()
                    && !observation.actual().value().defaultDesignerReady(), "ineligible outcome contradicts its actual GUI observation");
        }
    }
    public record Unavailable(String reason) implements DrawOutcome {
        public Unavailable { requireReason(reason); }
    }
    public record Unresolved(ActionReceipt action, String reason) implements DrawOutcome {
        public Unresolved { Objects.requireNonNull(action); requireReason(reason); }
    }
    public static final class UnavailableStop extends IOException {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final String reason; private final transient List<ActionReceipt> completedSelections;
        private UnavailableStop(String reason, List<ActionReceipt> completedSelections) {
            super(reason); this.reason = reason; this.completedSelections = List.copyOf(completedSelections);
        }
        public String reason() { return reason; }
        public int drawsCompleted() { return completedSelections.size(); }
        public List<ActionReceipt> completedSelections() { return completedSelections; }
    }
    public static final class UnresolvedStop extends IOException {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final transient ActionReceipt action; private final String reason; private final transient List<ActionReceipt> completedSelections;
        private UnresolvedStop(ActionReceipt action, String reason, List<ActionReceipt> completedSelections) {
            super(reason); this.action = action; this.reason = reason; this.completedSelections = List.copyOf(completedSelections);
        }
        public ActionReceipt action() { return action; }
        public String reason() { return reason; }
        public int drawsCompleted() { return completedSelections.size(); }
        public List<ActionReceipt> completedSelections() { return completedSelections; }
    }
    public static final class Exhausted extends IOException {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final transient List<SelectedIneligible> draws;
        private Exhausted(List<SelectedIneligible> draws) {
            super("bounded random playable selection found no default ruler designer after 8 confirmed ineligible draws");
            this.draws = List.copyOf(draws);
            StrictJson.require(this.draws.size() == MAX_DRAWS, "exhaustion requires eight actual ineligible outcomes");
        }
        public List<SelectedIneligible> draws() { return draws; }
    }

    public static Prepared prepare(Port port) throws IOException, InterruptedException {
        Objects.requireNonNull(port);
        Transition pick = Objects.requireNonNull(port.pickAny());
        StrictJson.require(pick.method() == Method.PICK_ANY, "custom-ruler preparation requires the actual Pick Any transition");
        FrontendRulesCodec.encode(pick);
        Tree target = Objects.requireNonNull(port.randomTarget());
        FrontendRulesCodec.read(target);
        laterTree(pick.action(), target);
        if (target.actual().value().truncated() || !target.actual().value().randomPlayableReady())
            throw new UnavailableStop("actual lobby random playable target unavailable; no draw submitted", List.of());

        List<ActionReceipt> selections = new ArrayList<>(); List<RawJson> acknowledgements = new ArrayList<>();
        List<SelectedIneligible> ineligible = new ArrayList<>();
        var actionIds = new HashSet<String>(); var requestIds = new HashSet<String>(); Tree previous = target;
        for (int attempt = 1; attempt <= MAX_DRAWS; attempt++) {
            DrawOutcome outcome = Objects.requireNonNull(port.drawOnce(attempt));
            if (outcome instanceof Unavailable missing) throw new UnavailableStop(missing.reason(), selections);
            if (outcome instanceof Unresolved unknown) throw new UnresolvedStop(unknown.action(), unknown.reason(), selections);
            ActionReceipt action; RawJson acknowledgement; Tree after;
            if (outcome instanceof DesignerReady ready) { action = ready.action(); acknowledgement = ready.acknowledgement(); after = ready.observation(); }
            else { var rejected = (SelectedIneligible) outcome; action = rejected.action(); acknowledgement = rejected.acknowledgement(); after = rejected.observation(); }
            var before = action.command().origin().requireFrontend(); var previousIdentity = previous.receipt().after().binding().origin().requireFrontend();
            StrictJson.require(action.command().source().equals(pick.action().command().source())
                    && before.sameSession(previousIdentity)
                    && before.frame().querySequence().compareTo(previousIdentity.frame().querySequence()) >= 0,
                    "draw did not follow its actual same-source previous observation");
            var settled = (ActionState.Settled) action.state();
            StrictJson.require(actionIds.add(action.command().actionId()) && requestIds.add(settled.attempt().requestId()),
                    "one confirmed draw cannot be counted or submitted again");
            selections.add(action); acknowledgements.add(acknowledgement); previous = after;
            if (outcome instanceof DesignerReady) {
                Prepared result = new Prepared(pick, target, selections, acknowledgements, after);
                FrontendRulesCodec.encode(result); return result;
            }
            ineligible.add((SelectedIneligible) outcome);
        }
        throw new Exhausted(ineligible);
    }

    private static void resolved(ActionReceipt action, RawJson acknowledgement, Tree tree) {
        confirmed(action); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(tree);
        StrictJson.require(action.command().operation().value().equals(SELECT_RANDOM_STEP)
                && action.ack().orElseThrow().originalResultToken().orElseThrow().equals(acknowledgement),
                "draw requires its actual SELECT_RANDOM command and complete original acknowledgement");
        var settled = (ActionState.Settled) action.state();
        var observed = ((ActionState.FrontendApplied) settled.settlement()).observation();
        observed.validate(action.command(), settled.attempt());
        FrontendRulesCodec.read(tree); laterTree(action, tree);
    }
    private static void laterTree(ActionReceipt action, Tree tree) {
        confirmed(action);
        var observed = ((ActionState.FrontendApplied) ((ActionState.Settled) action.state()).settlement()).observation();
        var receipt = tree.receipt(); var identity = receipt.after().binding().origin().requireFrontend();
        StrictJson.require(observed.after().sameSession(identity) && identity.frame() instanceof FrontendFrame.Menu
                && identity.frame().querySequence().compareTo(observed.after().frame().querySequence()) >= 0
                && receipt.request().source().equals(action.command().source())
                && receipt.request().sessionId().equals(action.command().sessionId()),
                "independent GUI observation crossed the confirmed source/session/connection or chronology");
    }
    private static void requireReason(String reason) {
        StrictJson.require(reason != null && !reason.isBlank() && reason.codePointCount(0, reason.length()) <= 4096,
                "bounded original unavailable/unknown reason required");
    }
}
