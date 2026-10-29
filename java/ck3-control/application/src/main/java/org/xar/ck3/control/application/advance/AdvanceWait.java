package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.ActionCommand;

/** The original lean semantic wait: actual frames only; no sleep is ever game progress. */
public final class AdvanceWait {
    private final AdvanceObservationPort observations;
    private final Clock clock;
    private final int maximumFrames;
    public AdvanceWait(AdvanceObservationPort observations, Clock clock, int maximumFrames) {
        this.observations = Objects.requireNonNull(observations); this.clock = Objects.requireNonNull(clock);
        require(maximumFrames >= 1 && maximumFrames <= 65_536, "finite actual frame budget required"); this.maximumFrames = maximumFrames;
    }
    public AdvanceObservationPort.Frame until(ActionCommand parent, AdvanceObservationPort.Frame initial,
            Predicate<AdvanceObservationPort.Frame> predicate, Instant deadline) {
        Objects.requireNonNull(predicate); require(!deadline.isAfter(parent.deadline()), "wait cannot extend original action deadline");
        AdvanceObservationPort.Frame current = initial;
        for (int frames = 0; frames <= maximumFrames; frames++) {
            binding(parent, initial, current);
            if (predicate.test(current) || !clock.instant().isBefore(deadline)) return current;
            require(frames < maximumFrames, "life advance actual frame budget exhausted");
            AdvanceObservationPort.Frame next = observations.next(parent, current.identity(), deadline);
            require(next.identity().frame().identity().nativeRevision().compareTo(current.identity().frame().identity().nativeRevision()) > 0,
                    "next must contain a newly received native frame, not a cached observation");
            require(next.identity().frame().revision().compareTo(current.identity().frame().revision()) >= 0, "public revision regressed");
            current = next;
        }
        throw new IllegalStateException("finite semantic wait exhausted");
    }
    public static void binding(ActionCommand parent, AdvanceObservationPort.Frame initial, AdvanceObservationPort.Frame current) {
        require(current.source().equals(parent.source()) && current.sessionId().equals(parent.sessionId())
                && current.identity().machineId().equals(parent.before().machineId()) && current.identity().game().equals(parent.before().game()),
                "life advance crossed actual source/session/Game generation");
        boolean terminal = current.semantic().get("one_life_terminal_reason") instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Text
                && java.util.Objects.equals(current.semantic().get("episode_character_id"), initial.semantic().get("episode_character_id"));
        require(current.identity().frame().episodeRunId().equals(initial.identity().frame().episodeRunId())
                && (terminal || current.identity().frame().identity().player().equals(initial.identity().frame().identity().player())), "episode/actor changed outside a real terminal; no replay");
        require(current.identity().frame().identity().dateRaw().compareTo(initial.identity().frame().identity().dateRaw()) >= 0, "native date regressed");
    }
}
