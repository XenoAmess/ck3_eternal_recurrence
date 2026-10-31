package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Canonical DATA proof of an abandoned Life resume Intent. It grants no Native request or effect authority. */
public final class IntentAbandonmentProof {
    private IntentAbandonmentProof() { }

    public static Optional<ActionState.IntentAbandoned> capture(ContinuityState predecessor,
            ActionReceipt original, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(predecessor); Objects.requireNonNull(original); Objects.requireNonNull(archive);
        if (!(original.state() instanceof ActionState.IntentDurable)
                || !original.command().operation().value().equals("resume-map")) return Optional.empty();
        ExactRef head = ContinuityActionJournal.recordHead(predecessor).orElseThrow();
        Optional<Replay> replay = replay(head, original.command(), archive);
        if (replay.isEmpty()) return Optional.empty();
        ActionState.IntentAbandoned proof = replay.orElseThrow().proof();
        ActionReceipt intent = archive.loadRecord(proof.originalIntentRecord()).receipt();
        StrictJson.require(intent.sequence() == original.sequence() && intent.bodySha256().equals(original.bodySha256())
                && intent.command().origin().machineId().equals(predecessor.machineId()),
                "abandoned Intent is not the actual canonical original");
        return Optional.of(proof);
    }

    /** Invoked independently by the writer authority under its actual original lock before commit. */
    public static void verify(ContinuityState predecessor, ActionReceipt candidate, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(candidate.state() instanceof ActionState.IntentAbandoned,
                "only the typed abandoned Intent has a canonical no-submission proof");
        var proof = (ActionState.IntentAbandoned) candidate.state();
        StrictJson.require(ContinuityActionJournal.recordHead(predecessor).equals(Optional.of(proof.originalActionHead()))
                && candidate.sequence() == Math.addExact(predecessor.sequence(), 1)
                && candidate.command().origin().machineId().equals(predecessor.machineId()),
                "abandoned Intent proof does not bind the actual original writer predecessor");
        StrictJson.require(proof.equals(replay(proof.originalActionHead(), candidate.command(), archive).orElseThrow(
                    () -> new IllegalArgumentException("abandoned Intent lost its source-owned Life parent")).proof()),
                "abandoned Intent changed its actual complete canonical prefix");
    }

    /** Cold source replay. Canonical callers supply this actual child; these refs preserve its original full prefix. */
    public static void verifyArchived(ActionReceipt abandoned, ActionPorts.OutcomeArchive archive) {
        originalParent(abandoned, archive);
    }

    /** Returns the exact source-bound parent from the verified original prefix; its guard is BEFORE evidence only. */
    public static ActionReceipt originalParent(ActionReceipt abandoned, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(isAbandonedResume(abandoned), "only the original abandoned Life resume is supported");
        var proof = (ActionState.IntentAbandoned) abandoned.state();
        ActionReceipt head = archive.loadRecord(proof.originalActionHead()).receipt();
        Replay replay = replay(proof.originalActionHead(), abandoned.command(), archive).orElseThrow(
                () -> new IllegalArgumentException("abandoned Intent lost its source-owned Life parent"));
        StrictJson.require(abandoned.sequence() > head.sequence() && proof.equals(replay.proof()),
                "abandoned Intent archived prefix changed or followed its terminal");
        return replay.parent();
    }

    /** Shape only. Authority and archived source replay must still verify the complete original prefix. */
    public static boolean isAbandonedResume(ActionReceipt receipt) {
        return receipt.state() instanceof ActionState.IntentAbandoned
                && receipt.command().origin() instanceof CommandOrigin.Gameplay
                && receipt.command().operation().value().equals("resume-map")
                && receipt.command().arguments().members().isEmpty()
                && receipt.command().expected().equals(AdvancePrimitives.expected(receipt.command().before(),
                    receipt.command().source(), receipt.command().operation(), receipt.command().arguments()));
    }

    private static Optional<Replay> replay(ExactRef originalHead, ActionCommand command,
            ActionPorts.OutcomeArchive archive) {
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay && command.operation().value().equals("resume-map")
                && command.arguments().members().isEmpty(), "only the original Life resume Intent can be abandoned");
        var latest = new LinkedHashMap<String, ActionReceipt>();
        var matching = new ArrayList<Referenced>();
        var seen = new HashSet<ExactRef>();
        Optional<ExactRef> cursor = Optional.of(originalHead);
        long previous = Long.MAX_VALUE;
        while (cursor.isPresent()) {
            ExactRef reference = cursor.orElseThrow();
            StrictJson.require(seen.add(reference) && seen.size() <= 100_000, "abandoned Intent requires the finite complete original action chain");
            ActionRecord record = archive.loadRecord(reference); ActionReceipt receipt = record.receipt();
            StrictJson.require(receipt.sequence() < previous && receipt.command().origin().machineId().equals(command.origin().machineId()),
                    "abandoned Intent chain crossed its original machine or sequence");
            previous = receipt.sequence(); latest.putIfAbsent(receipt.command().actionId(), receipt);
            if (receipt.command().actionId().equals(command.actionId())) matching.add(new Referenced(reference, receipt));
            cursor = record.previous();
        }
        // A latest-state projection cannot establish this fact. Inspect every event back to genesis.
        StrictJson.require(matching.size() == 1 && matching.getFirst().receipt().state() instanceof ActionState.IntentDurable
                && matching.getFirst().receipt().bodySha256().equals(ActionCodec.bodySha256(command)),
                "original resume has another durable event or an actual submission; no abandonment");
        var parents = latest.values().stream().filter(value -> value.state() instanceof ActionState.CompositeUnknown unknown
                && LifeAdvanceComposite.accepts(value.command().operation().value())
                && unknown.execution().handlerId().equals(LifeAdvanceComposite.HANDLER)
                && unknown.execution().children().stream().anyMatch(child -> child.actionId().equals(command.actionId()))).toList();
        if (parents.isEmpty()) return Optional.empty();
        StrictJson.require(parents.size() == 1, "abandoned resume needs its one canonical unresolved Life parent");
        ActionReceipt parent = parents.getFirst();
        CompositeExecution execution = ((ActionState.CompositeUnknown) parent.state()).execution();
        StrictJson.require(execution.children().size() >= 2 && execution.children().size() <= 4,
                "abandoned resume must follow a finite independently confirmed original ARM prefix");
        var bound = execution.children().getLast(); int ordinal = execution.children().size();
        StrictJson.require(bound.actionId().equals(command.actionId()) && bound.bodySha256().equals(ActionCodec.bodySha256(command))
                && command.actionId().equals(ActionIds.child(parent.command().actionId(), ordinal, command.operation()))
                && command.source().equals(parent.command().source()) && command.sessionId().equals(parent.command().sessionId())
                && command.claims().equals(parent.command().claims()) && !command.deadline().isAfter(parent.command().deadline())
                && command.expected().equals(AdvancePrimitives.expected(command.before(), command.source(), command.operation(), command.arguments())),
                "abandoned resume changed its canonical parent/ordinal/body/source/deadline");
        var prefix = new ArrayList<ActionReceipt>();
        for (var child : execution.children().subList(0, ordinal - 1)) {
            ActionReceipt actual = Objects.requireNonNull(latest.get(child.actionId()), "original ARM prefix child absent");
            StrictJson.require(actual.bodySha256().equals(child.bodySha256()), "original ARM prefix body changed");
            prefix.add(actual);
        }
        var armedExecution = new CompositeExecution(execution.handlerId(), execution.startedAt(), execution.guard(),
                execution.children().subList(0, ordinal - 1));
        LifeAdvanceComposite.requireArmedInitializationPrefix(parent.command(), armedExecution, prefix);
        var original = parent.command().before(); var before = command.before();
        StrictJson.require(matching.getFirst().receipt().sequence() > prefix.getLast().sequence()
                && before.machineId().equals(original.machineId()) && before.game().equals(original.game())
                && before.frame().episodeRunId().equals(original.frame().episodeRunId())
                && before.frame().identity().player().equals(original.frame().identity().player())
                && before.frame().identity().dateRaw().equals(original.frame().identity().dateRaw())
                && before.frame().identity().nativeRevision().compareTo(original.frame().identity().nativeRevision()) >= 0,
                "abandoned resume predates the confirmed ARM or changed its same-game initialization frame");
        return Optional.of(new Replay(new ActionState.IntentAbandoned(matching.getFirst().reference(), originalHead), parent));
    }

    private record Referenced(ExactRef reference, ActionReceipt receipt) { }
    private record Replay(ActionState.IntentAbandoned proof, ActionReceipt parent) { }
}
