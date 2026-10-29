package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleResponses.*;

/**
 * Independent actual battle readback. Reuses the original raw decoders; a DTO,
 * ACK, conditional supply quote or forecast is not accepted in their place.
 * This projection never dispatches, settles a writer fact or permits replay.
 */
public final class BattleAfterStateObservation {
    private BattleAfterStateObservation() { }
    public enum Reason {
        NO_INDEPENDENT_POST, FRAME_OR_AUTHORITY_DRIFT, SOURCE_DRIFT,
        POST_UNAVAILABLE, REMOVAL_REQUIRES_JOURNAL, JOURNAL_NOT_OBSERVED,
        JOURNAL_GAP, PRIOR_IDENTITY_CHANGED, TERMINAL_INCOMPLETE
    }
    public enum TerminalKind { NORMAL_RESULT, NO_NORMAL_RESULT }
    public record Evidence(ObservationIdentity before, ObservationIdentity after,
            G2Source beforeSource, G2Source afterSource, ExactRef beforeReceipt,
            ExactRef afterReceipt, BigInteger connectionGeneration) {
        public Evidence {
            Objects.requireNonNull(before); Objects.requireNonNull(after);
            Objects.requireNonNull(beforeSource); Objects.requireNonNull(afterSource);
            Objects.requireNonNull(beforeReceipt); Objects.requireNonNull(afterReceipt);
            Objects.requireNonNull(connectionGeneration);
            require(beforeReceipt.bytes() > 0 && afterReceipt.bytes() > 0,
                    "original complete read references required");
        }
    }
    public sealed interface Result permits Pending, CurrentBattle, TerminalBattle {
        Evidence evidence();
        default boolean dispatchAllowed() { return false; }
        default boolean replayAllowed() { return false; }
        default boolean commandCausationVerified() { return false; }
        default boolean actualArrivalObserved() { return false; }
        default boolean warOutcomeVerified() { return false; }
        default boolean completeBattleConsequencesVerified() { return false; }
    }
    public record Pending(Evidence evidence, Reason reason) implements Result {
        public Pending { Objects.requireNonNull(evidence); Objects.requireNonNull(reason); }
    }
    /** Current winner/phase and roster are observations, including any actual reinforcement change. */
    public record CurrentBattle(Evidence evidence, Control original, Transition current) implements Result {
        public CurrentBattle { Objects.requireNonNull(evidence); Objects.requireNonNull(original); Objects.requireNonNull(current); }
    }
    /** A journal event may be observed while cleanup is pending. Removal is a separate value. */
    public record TerminalBattle(Evidence evidence, Control original, Terminal terminal,
            TerminalKind kind, Winner winner, boolean originalCombatRemoved) implements Result {
        public TerminalBattle {
            Objects.requireNonNull(evidence); Objects.requireNonNull(original);
            Objects.requireNonNull(terminal); Objects.requireNonNull(kind); Objects.requireNonNull(winner);
        }
    }

    public static Result transition(PlanningReadReceipt before, ExactRef beforeRef,
            PlanningReadReceipt after, ExactRef afterRef, PublicUnitId subject) {
        Evidence evidence = evidence(before, beforeRef, after, afterRef);
        Optional<Reason> failed = independent(before, after);
        if (failed.isPresent()) return new Pending(evidence, failed.orElseThrow());
        Control original = BattleResponseCodec.control(raw(before), context(before), new ArmyRequests.Unit(subject));
        Transition current = BattleResponseCodec.transition(raw(after), context(after), new ArmyRequests.Combat(original.combat()));
        frame(original.frame(), before); frame(current.frame(), after);
        return switch (current.status()) {
            case AVAILABLE -> {
                if (!current.ready() || !(current.lifecycle() instanceof Present<Lifecycle> lifecycle)
                        || !lifecycle.value().province().equals(original.combatProvince()))
                    yield new Pending(evidence, Reason.TERMINAL_INCOMPLETE);
                yield new CurrentBattle(evidence, original, current);
            }
            case COMBAT_NOT_FOUND -> new Pending(evidence, Reason.REMOVAL_REQUIRES_JOURNAL);
            case STATE_CHANGED, UNAVAILABLE -> new Pending(evidence, Reason.POST_UNAVAILABLE);
        };
    }

    public static Result terminal(PlanningReadReceipt before, ExactRef beforeRef,
            PlanningReadReceipt after, ExactRef afterRef, PublicUnitId subject,
            ArmyRequests.Terminal requested) {
        Evidence evidence = evidence(before, beforeRef, after, afterRef);
        Optional<Reason> failed = independent(before, after);
        if (failed.isPresent()) return new Pending(evidence, failed.orElseThrow());
        Control original = BattleResponseCodec.control(raw(before), context(before), new ArmyRequests.Unit(subject));
        require(requested.priorCombat().equals(Optional.of(original.combat()))
                && requested.subject().equals(Optional.of(original.selected())),
                "terminal request must retain the actual selected subject and original full CombatID");
        Terminal terminal = BattleTerminalCodec.terminal(raw(after), context(after), requested);
        frame(original.frame(), before); frame(terminal.frame(), after);
        if (terminal.status() != Availability.AVAILABLE || !terminal.ready()
                || !(terminal.state() instanceof Present<TerminalState> observed))
            return new Pending(evidence, Reason.POST_UNAVAILABLE);
        Journal journal = terminal.journal();
        if (!journal.eventStatus().equals("observed") || !(journal.eventSequence() instanceof Present<UInt64>))
            return new Pending(evidence, Reason.JOURNAL_NOT_OBSERVED);
        BigInteger oldest = journal.oldest().value();
        if (journal.requestedAfter() instanceof NullValue<?> && !oldest.equals(BigInteger.ONE)
                || journal.requestedAfter() instanceof Present<UInt64> cursor
                && cursor.value().value().add(BigInteger.ONE).compareTo(oldest) < 0)
            return new Pending(evidence, Reason.JOURNAL_GAP);
        TerminalState state = observed.value(); Prior prior = state.prior();
        if (!prior.combat().equals(original.combat())
                || !prior.province().equals(new Present<>(original.combatProvince()))
                || !(prior.attackers() instanceof Present<List<PublicUnitId>> attackers)
                || !(prior.defenders() instanceof Present<List<PublicUnitId>> defenders)
                || !attackers.value().containsAll(ids(original.attacker()))
                || !defenders.value().containsAll(ids(original.defender())))
            return new Pending(evidence, Reason.PRIOR_IDENTITY_CHANGED);
        if (!(prior.terminalDate() instanceof Present<Long> date)
                || date.value() < original.frame().dateRaw() || date.value() > terminal.frame().dateRaw()
                || !(prior.winnerRaw() instanceof Present<Integer> winner))
            return new Pending(evidence, Reason.TERMINAL_INCOMPLETE);
        TerminalKind kind;
        if (prior.terminalKind().equals("normal_result")
                && prior.suppressResultEnvelopes().equals(new Present<>(false))) kind = TerminalKind.NORMAL_RESULT;
        else if (prior.terminalKind().equals("no_normal_result")
                && prior.suppressResultEnvelopes().equals(new Present<>(true))) kind = TerminalKind.NO_NORMAL_RESULT;
        else return new Pending(evidence, Reason.TERMINAL_INCOMPLETE);
        Winner actualWinner = switch (winner.value()) {
            case -1 -> Winner.NONE;
            case 0 -> Winner.ATTACKER;
            case 1 -> Winner.DEFENDER;
            default -> throw new IllegalArgumentException("native terminal winner is outside -1..1");
        };
        // A no-normal event can preserve NONE. No inferred defender win or derived warscore.
        return new TerminalBattle(evidence, original, terminal, kind, actualWinner, !state.removal().combatResolves());
    }

    /** Explicit output spelling; every 64-bit frame/time/sequence crosses JSON as decimal text. */
    public static ObjectNode toJson(Result result) {
        Objects.requireNonNull(result); ObjectNode out = StrictJson.object();
        out.put("schema", "xar.actual-battle-after-state.v1");
        out.put("status", result instanceof Pending ? "pending" : result instanceof CurrentBattle ? "current_battle_observed" : "terminal_event_observed");
        out.put("machine_id", result.evidence().after().machineId());
        out.put("exact_build", result.evidence().afterSource().exactBuild());
        out.put("before_public_revision", result.evidence().before().frame().revision().toString());
        out.put("post_public_revision", result.evidence().after().frame().revision().toString());
        out.put("post_native_revision", result.evidence().after().frame().identity().nativeRevision().toString());
        out.put("post_date_raw", result.evidence().after().frame().identity().dateRaw().toString());
        out.put("connection_generation", result.evidence().connectionGeneration().toString());
        out.set("before_receipt", result.evidence().beforeReceipt().toJson());
        out.set("post_receipt", result.evidence().afterReceipt().toJson());
        out.put("dispatch_allowed", false); out.put("replay_allowed", false);
        out.put("command_causation_verified", false); out.put("actual_arrival_observed", false);
        out.put("war_outcome_verified", false); out.put("complete_battle_consequences_verified", false);
        if (result instanceof Pending pending) out.put("reason", pending.reason().name());
        else if (result instanceof CurrentBattle current) {
            if (!(current.current().lifecycle() instanceof Present<Lifecycle> observed))
                throw new IllegalArgumentException("current observation lacks lifecycle");
            Lifecycle lifecycle = observed.value();
            out.put("combat_id", current.original().combat().value());
            out.put("phase", lifecycle.phase().name()); out.put("winner", lifecycle.winner().name());
            out.put("finalized", lifecycle.finalized());
            out.set("attacker_public_cunit_ids", idsJson(current.current().attackers()));
            out.set("defender_public_cunit_ids", idsJson(current.current().defenders()));
        } else if (result instanceof TerminalBattle terminal) {
            out.put("combat_id", terminal.original().combat().value());
            out.put("terminal_kind", terminal.kind().name()); out.put("winner", terminal.winner().name());
            out.put("original_combat_removed", terminal.originalCombatRemoved());
            if (!(terminal.terminal().journal().eventSequence() instanceof Present<UInt64> observed))
                throw new IllegalArgumentException("terminal observation lacks event sequence");
            out.put("event_sequence", observed.value().decimal());
        }
        return out;
    }
    private static com.fasterxml.jackson.databind.node.ArrayNode idsJson(List<PublicUnitId> ids) {
        var out = StrictJson.object().arrayNode(); ids.forEach(id -> out.add(id.value())); return out;
    }
    private static List<PublicUnitId> ids(CombatSide side) { return side.orderedArmies().stream().map(Army::publicId).toList(); }
    private static Context context(PlanningReadReceipt receipt) {
        var request = receipt.request(); return new Context(request.before(), request.source(), request.sessionId(), request.deadline());
    }
    private static byte[] raw(PlanningReadReceipt receipt) {
        require(receipt.original().nativeOk(), "native read rejected");
        return receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("native original result missing")).bytes();
    }
    private static Evidence evidence(PlanningReadReceipt before, ExactRef beforeRef, PlanningReadReceipt after, ExactRef afterRef) {
        Objects.requireNonNull(before); Objects.requireNonNull(after);
        return new Evidence(before.request().before(), after.request().before(),
                before.request().source(), after.request().source(), beforeRef, afterRef,
                after.before().binding().connectionGeneration());
    }
    private static Optional<Reason> independent(PlanningReadReceipt before, PlanningReadReceipt after) {
        if (!stable(before) || !stable(after)) return Optional.of(Reason.FRAME_OR_AUTHORITY_DRIFT);
        ObservationIdentity a = before.request().before(), b = after.request().before();
        GuardEvidence ga = before.before().binding(), gb = after.before().binding();
        if (!a.machineId().equals(b.machineId()) || !a.game().equals(b.game())
                || !a.frame().episodeRunId().equals(b.frame().episodeRunId())
                || !a.frame().identity().player().equals(b.frame().identity().player())
                || !ga.connectionGeneration().equals(gb.connectionGeneration())
                || !ga.authorityId().equals(gb.authorityId())
                || !before.request().sessionId().equals(after.request().sessionId()))
            return Optional.of(Reason.FRAME_OR_AUTHORITY_DRIFT);
        if (!before.request().source().exactBuild().equals(after.request().source().exactBuild()))
            return Optional.of(Reason.SOURCE_DRIFT);
        if (before.requestId().equals(after.requestId())
                || b.frame().revision().compareTo(a.frame().revision()) <= 0
                || b.frame().identity().nativeRevision().compareTo(a.frame().identity().nativeRevision()) < 0
                || b.frame().identity().dateRaw().compareTo(a.frame().identity().dateRaw()) < 0
                || gb.observedAt().isBefore(ga.observedAt()))
            return Optional.of(Reason.NO_INDEPENDENT_POST);
        return Optional.empty();
    }
    private static boolean stable(PlanningReadReceipt receipt) {
        var request = receipt.request(); var pre = receipt.before(); var post = receipt.after();
        var a = pre.binding(); var b = post.binding();
        return pre.paused() && post.paused() && pre.mapReady() && post.mapReady()
                && pre.playerAlive() && post.playerAlive()
                && pre.originalBindingSha256().equals(post.originalBindingSha256())
                && request.before().equals(a.observed()) && request.before().equals(b.observed())
                && request.source().equals(a.source()) && request.source().equals(b.source())
                && request.operation().equals(a.operation()) && request.operation().equals(b.operation())
                && request.sessionId().equals(a.sessionId()) && request.sessionId().equals(b.sessionId())
                && a.connectionGeneration().equals(b.connectionGeneration()) && a.authorityId().equals(b.authorityId());
    }
    private static void frame(Frame frame, PlanningReadReceipt receipt) {
        require(frame.nativeRevision().value().equals(receipt.request().before().frame().identity().nativeRevision())
                && BigInteger.valueOf(frame.dateRaw()).equals(receipt.request().before().frame().identity().dateRaw()),
                "decoded native frame must bind native revision, not the independent public revision");
    }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
