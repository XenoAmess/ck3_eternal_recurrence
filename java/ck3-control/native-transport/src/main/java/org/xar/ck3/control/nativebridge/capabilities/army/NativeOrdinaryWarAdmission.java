package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.application.planning.military.OrdinaryWarAdmissionRules;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Concrete lock-held proposal admission, using the unique M0 decoder and the original canonical journal/archive. */
public final class NativeOrdinaryWarAdmission implements ArmyOrdinaryActionPreparation.WhitePeacePolicy {
    private final ContinuityWriter writer;
    private final ActionPorts.OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;
    public NativeOrdinaryWarAdmission(ContinuityWriter originalWriter, ActionPorts.OutcomeArchive sameArchive,
            NativeEffectEvidence.FrameLoader originalFrameLoader) {
        writer = Objects.requireNonNull(originalWriter);
        archive = Objects.requireNonNull(sameArchive); frames = Objects.requireNonNull(originalFrameLoader);
    }
    @Override public void verify(Complete current, BigInteger fullWar, List<ArmyOrdinaryPreflight.Read> originals) {
        throw new IllegalStateException("white-peace admission requires the actual original writer Session");
    }
    @Override public void verify(ContinuityStorePort.Session same, Complete current, BigInteger fullWar, List<ArmyOrdinaryPreflight.Read> originals) { qualify(same, current, fullWar, originals); }
    /** Same real admission for an ordinary proposal consumer; returned DATA never authorizes transport or settlement. */
    public OrdinaryWhitePeacePolicy.Ready qualify(ContinuityStorePort.Session same, Complete current, BigInteger fullWar, List<ArmyOrdinaryPreflight.Read> originals) {
        int id = fullWar.intValueExact(); StrictJson.require(id > 0, "positive complete white-peace WarID required");
        try {
            writer.requireSession(same); var bound = archive.withSession(same);
            List<ActionReceipt> canonical = ContinuityActionJournal.receipts(same.head().state(), bound);
            var ready = requireWhitePeace(current, id, originals, canonical, bound);
            writer.requireSession(same);
            return ready;
        } catch (IOException failure) { throw new UncheckedIOException("original lock-held white-peace admission unavailable", failure); }
    }
    private OrdinaryWhitePeacePolicy.Ready requireWhitePeace(Complete current, int id, List<ArmyOrdinaryPreflight.Read> originals,
            List<ActionReceipt> canonical, ActionPorts.OutcomeArchive bound) {
            Obj view = policyView(current, originals, bound); var decision = OrdinaryWhitePeacePolicy.evaluate(view, id);
            if (!(decision instanceof OrdinaryWhitePeacePolicy.Ready ready))
                throw new IllegalArgumentException("native white_peace fresh validation failed: " + ((OrdinaryWhitePeacePolicy.Unavailable) decision).reason());
            rejectUnresolved(canonical, current, "offer-white-peace-" + id);
            Arr history = history(current, canonical, bound);
            StrictJson.require(OrdinaryWarAdmissionRules.whitePeaceFence(history, id, view.get("episode_run_id"), ready.variant()).isEmpty(),
                    "native de-jure white_peace submission is suppressed by its same-episode one-shot full WarID fence");
            StrictJson.require(OrdinaryWarAdmissionRules.whitePeaceCooldown(history, id, view.get("date_raw"), view.get("episode_run_id")).isEmpty(),
                    "native white_peace proposal is suppressed by its thirty-day same-WarID cooldown");
            return ready;
    }
    /** Replays only the original admission before its INTENT; the paired domain verifier still owns every settlement claim. */
    public void replayAdmission(WriterContracts.Head actualLockedHead, ActionReceipt proposed, ActionPorts.OutcomeArchive sameWriterArchive) {
        Objects.requireNonNull(actualLockedHead); Objects.requireNonNull(proposed); Objects.requireNonNull(sameWriterArchive);
        var arguments = ArmyOrdinaryActionArguments.decode(proposed.command().arguments());
        StrictJson.require(arguments.kind() == ArmyOrdinaryActionArguments.Kind.OFFER_WHITE_PEACE
                || arguments.kind() == ArmyOrdinaryActionArguments.Kind.DECLARE_WAR, "war admission replay received an unrelated action");
        var canonical = ContinuityActionJournal.lookup(actualLockedHead.state(), proposed.command().actionId(), sameWriterArchive)
                .orElseThrow(() -> new IllegalArgumentException("original admission action is absent from the actual locked chain"));
        StrictJson.require(canonical.bodySha256().equals(proposed.bodySha256())
                && canonical.command().equals(proposed.command()), "original war admission command changed");
        Optional<ActionState.Attempt> originalAttempt = ActionTransitions.attempt(proposed.state());
        if (originalAttempt.isEmpty()) {
            StrictJson.require(ActionTransitions.dispatch(proposed.state()).isEmpty(), "war dispatch has no original preparation guard");
            return; // The paired verifier must independently prove this negative, unsubmitted result.
        }
        var attempt = originalAttempt.orElseThrow();
        Complete before = RootGuardEvidence.loadFrame(attempt.guard(), sameWriterArchive, frames);
        StrictJson.require(before.identity().equals(proposed.command().before())
                && before.source().equals(proposed.command().source()) && before.sessionId().equals(proposed.command().sessionId()),
                "war admission replay crossed its original complete frame/source");
        var prior = ContinuityActionJournal.receiptsBeforeIntent(actualLockedHead.state(), proposed.command().actionId(), sameWriterArchive);
        if (arguments.kind() == ArmyOrdinaryActionArguments.Kind.DECLARE_WAR) {
            requireDeclaration(before, arguments, attempt.preparedRequest(), prior);
            return;
        }
        var call = (ArmyCalls.War) ArmyCallCodec.decode(PublicMethod.OFFER_WHITE_PEACE, arguments.publicArguments());
        int id = call.warId().intValueExact();
        StrictJson.require(proposed.command().operation().value().equals("offer-white-peace-" + id)
                && attempt.preparedRequest().step().equals(proposed.command().operation().value()), "white-peace replay changed full WarID");
        List<ArmyOrdinaryPreflight.Read> originals = new ArrayList<>();
        for (var reference : arguments.preflightReads()) {
            var read = sameWriterArchive.loadRead(reference); NativeRecordedEvidenceVerifier.requireRead(read, sameWriterArchive);
            StrictJson.require(sameWriterArchive.readReferenceOf(read).equals(reference), "original white-peace quote custody changed");
            ArmyOrdinaryPreflight.Role role; PublicMethod method;
            if (read.request().operation().value().equals("query-war-termination-options-" + id)) {
                role = ArmyOrdinaryPreflight.Role.WAR_OPTIONS; method = PublicMethod.QUERY_WAR_TERMINATION_OPTIONS;
            } else if (read.request().operation().value().equals("query-war-termination-terms-v1-" + id)) {
                role = ArmyOrdinaryPreflight.Role.WAR_TERMS; method = PublicMethod.QUERY_WAR_TERMINATION_TERMS;
            } else throw new IllegalArgumentException("white-peace admission has an unrelated original quote operation");
            var decoded = decode(before, read, method);
            originals.add(new ArmyOrdinaryPreflight.Read(role, read, reference, ArmyWarReadCodec.encode(decoded)));
        }
        requireWhitePeace(before, id, originals, prior, sameWriterArchive);
    }
    /** Compose before the identical launcher's full selected-CB preflight. This adds no other Native request. */
    public void verifyDeclaration(ContinuityStorePort.Session same, Complete current, ArmyOrdinaryActionArguments arguments, NativeRequest primitive) {
        try {
            writer.requireSession(same); var bound = archive.withSession(same);
            var canonical = ContinuityActionJournal.receipts(same.head().state(), bound);
            requireDeclaration(current, arguments, primitive, canonical);
            writer.requireSession(same);
        } catch (IOException failure) { throw new UncheckedIOException("original declaration latch unavailable", failure); }
    }
    private static void requireDeclaration(Complete current, ArmyOrdinaryActionArguments arguments, NativeRequest primitive, List<ActionReceipt> canonical) {
        StrictJson.require(arguments.kind() == ArmyOrdinaryActionArguments.Kind.DECLARE_WAR, "declaration admission received another action kind");
        ArmyCalls.Call selected = ArmyCallCodec.decode(PublicMethod.DECLARE_WAR, arguments.publicArguments());
        StrictJson.require(primitive.step().equals("declare-war-" + ((ArmyCalls.Declaration) selected).declarationId()), "declaration primitive changed selected CB tuple");
        StrictJson.require(OrdinaryWarAdmissionRules.declaration(current.semantic(), canonical) == OrdinaryWarAdmissionRules.Declaration.CLEAR,
                "original declaration remains unresolved; collect its original request without a second submission");
        var physical = OrdinaryWarAdmissionRules.declarationBefore(current.semantic());
        StrictJson.require(physical.actorCharacterId() == current.identity().frame().identity().player().intValueExact()
                && physical.bridgePid() == current.identity().game().pid() && physical.connectionGeneration().equals(current.connectionGeneration()),
                "original declaration owner differs from the complete held Native/Driver frame");
    }
    /** The source-bound war/window checker runs in the same explicit archive scope, including public pre-INTENT preparation. */
    public ArmyOrdinaryActionPreparation.FinalGates finalGates(ArmyOrdinaryActionPreparation.FinalGates actualFamilyGates) {
        Objects.requireNonNull(actualFamilyGates);
        return new ArmyOrdinaryActionPreparation.FinalGates() {
            @Override public void verify(Complete current, ArmyOrdinaryActionArguments arguments, NativeRequest request) {
                throw new IllegalStateException("final war admission requires the original writer Session");
            }
            @Override public void verify(ContinuityStorePort.Session same, Complete current, ArmyOrdinaryActionArguments arguments, NativeRequest request) {
                try {
                    writer.requireSession(same);
                    archive.inSession(same, scoped -> {
                        if (arguments.kind() == ArmyOrdinaryActionArguments.Kind.DECLARE_WAR) verifyDeclaration(same, current, arguments, request);
                        actualFamilyGates.verify(same, current, arguments, request); return null;
                    });
                    writer.requireSession(same);
                } catch (IOException failure) { throw new UncheckedIOException("same-writer final war gates unavailable", failure); }
            }
        };
    }
    /** One original-receipt -> policy DATA projection, also used by the real first-phase terms consumer. */
    public static Obj policyView(Complete current, List<ArmyOrdinaryPreflight.Read> originals, ActionPorts.OutcomeArchive bound) {
        java.util.Map<String,Value> fields = new java.util.LinkedHashMap<>(current.semantic().members());
        List<Value> options = new ArrayList<>(), terms = new ArrayList<>();
        for (var original : List.copyOf(originals)) {
            if (original.role() != ArmyOrdinaryPreflight.Role.WAR_OPTIONS && original.role() != ArmyOrdinaryPreflight.Role.WAR_TERMS) continue;
            ArmyOrdinaryPreflight.bind(original.original(), current); NativeRecordedEvidenceVerifier.requireRead(original.original(), bound);
            StrictJson.require(bound.readReferenceOf(original.original()).equals(original.reference()), "white-peace quote custody changed");
            PublicMethod method = original.role() == ArmyOrdinaryPreflight.Role.WAR_OPTIONS ? PublicMethod.QUERY_WAR_TERMINATION_OPTIONS : PublicMethod.QUERY_WAR_TERMINATION_TERMS;
            ArmyWarReadCodec.Observation decoded = decode(current, original.original(), method);
            String key = method == PublicMethod.QUERY_WAR_TERMINATION_OPTIONS ? "war_termination_options" : "war_termination_terms";
            Obj row = OpportunityJson.object(decoded.normalizedResult().get(key), "complete normalized original war quote");
            (method == PublicMethod.QUERY_WAR_TERMINATION_OPTIONS ? options : terms).add(boundRow(current, row));
        }
        StrictJson.require(options.size() == 1 && terms.size() <= 1, "white-peace requires one exact original options receipt and at most one terms receipt");
        fields.put("war_termination_options", new Arr(options)); fields.put("war_termination_terms", new Arr(terms));
        return new Obj(fields); // Local consumer view; it is never presented as an original Native publication.
    }
    private static Obj boundRow(Complete current, Obj normalized) {
        java.util.Map<String,Value> fields = new java.util.LinkedHashMap<>(normalized.members());
        var before = current.identity().frame();
        fields.put("queried_snapshot_id", new Text(before.snapshotId())); fields.put("queried_revision", new IntegerValue(before.revision()));
        fields.put("queried_native_revision", new IntegerValue(before.identity().nativeRevision()));
        Obj diagnostics = OpportunityJson.object(current.semantic().get("diagnostics"), "actual diagnostics");
        Value generation = diagnostics.get("connection_generation"); StrictJson.require(generation != null && generation != Nil.INSTANCE, "actual source connection is absent");
        fields.put("queried_connection_generation", generation);
        Value episode = current.semantic().get("episode_run_id"); StrictJson.require(episode != null, "actual source episode field is absent"); fields.put("episode_run_id", episode);
        return new Obj(fields);
    }
    private static ArmyWarReadCodec.Observation decode(Complete frame, PlanningReadReceipt original, PublicMethod method) {
        var context = new ArmyTypes.Context(frame.identity(), frame.source(), frame.sessionId(), original.request().deadline());
        var input = ArmyCallCodec.decode(method, new RawJson(OpportunityJson.encode(original.request().arguments())));
        return ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(input, context, frame.semantic(), Optional.empty()), original);
    }
    private Arr history(Complete current, List<ActionReceipt> canonical, ActionPorts.OutcomeArchive bound) {
        Value raw = current.semantic().get("native_command_history");
        StrictJson.require(raw instanceof Arr, "complete original Driver history is required for the CB one-shot fence");
        Value export = current.semantic().get("native_command_history_export");
        StrictJson.require(export == null || export == Nil.INSTANCE, "an omitted/partial Driver history cannot grant white-peace replay admission");
        List<Value> rows = new ArrayList<>(((Arr) raw).items());
        List<ActionReceipt> ordered = canonical.stream().filter(receipt -> ActionTransitions.attempt(receipt.state()).isPresent())
                .sorted(java.util.Comparator.comparing((ActionReceipt receipt) -> ActionTransitions.attempt(receipt.state()).orElseThrow().submittedAt())
                        .thenComparingLong(ActionReceipt::sequence)).toList();
        for (ActionReceipt receipt : ordered) {
            if (!(receipt.command().origin() instanceof CommandOrigin.Gameplay) || !receipt.command().operation().value().startsWith("offer-white-peace-")
                    || !sameScope(receipt, current)) continue;
            Optional<ActionState.Attempt> attempt = ActionTransitions.attempt(receipt.state());
            var ack = receipt.ack(); if (attempt.isEmpty() || ack.isEmpty() || !ack.orElseThrow().nativeOk() || ack.orElseThrow().originalResultToken().isEmpty()) continue;
            Obj result = OpportunityJson.object(OpportunityJson.parse(ack.orElseThrow().originalResultToken().orElseThrow().bytes()), "original native white-peace result");
            if (!new Text(receipt.command().operation().value()).equals(result.get("step")) || !new Bool(true).equals(result.get("accepted")) || !new Text("submitted").equals(result.get("status"))) continue;
            var args = ArmyOrdinaryActionArguments.decode(receipt.command().arguments());
            StrictJson.require(args.kind() == ArmyOrdinaryActionArguments.Kind.OFFER_WHITE_PEACE, "canonical white-peace command has another argument contract");
            Complete before = RootGuardEvidence.loadFrame(attempt.orElseThrow().guard(), bound, frames);
            List<PlanningReadReceipt> quotes = new ArrayList<>();
            for (var ref : args.preflightReads()) {
                var original = bound.loadRead(ref); NativeRecordedEvidenceVerifier.requireRead(original, bound);
                if (original.request().operation().value().startsWith("query-war-termination-options-")) quotes.add(original);
            }
            StrictJson.require(quotes.size() == 1, "original canonical white-peace options quote is missing or ambiguous");
            var original = quotes.getFirst(); ArmyOrdinaryPreflight.bind(original, before);
            Obj options = OpportunityJson.object(decode(before, original, PublicMethod.QUERY_WAR_TERMINATION_OPTIONS).normalizedResult().get("war_termination_options"), "original options");
            var publicCall = (ArmyCalls.War) ArmyCallCodec.decode(PublicMethod.OFFER_WHITE_PEACE, args.publicArguments());
            java.util.Map<String,Value> action = new java.util.LinkedHashMap<>(); action.put("status", new Text("submitted_pending"));
            action.put("war_id", new IntegerValue(publicCall.warId())); action.put("outcome", new Text("white_peace"));
            action.put("submitted_date_raw", new IntegerValue(before.identity().frame().identity().dateRaw()));
            action.put("episode_run_id", before.semantic().get("episode_run_id"));
            action.put("casus_belli", options.get("active_casus_belli_identity"));
            rows.add(new Obj(java.util.Map.of("command", new Text(receipt.command().operation().value()), "ok", new Bool(true), "index", new IntegerValue(BigInteger.valueOf(receipt.sequence())),
                    "result", new Obj(java.util.Map.of("war_termination_result", new Obj(action))))));
        }
        return new Arr(rows);
    }
    private static void rejectUnresolved(List<ActionReceipt> canonical, Complete current, String operation) {
        for (ActionReceipt receipt : canonical) if (!receipt.settled() && receipt.command().operation().value().equals(operation)
                && sameScope(receipt, current) && ActionTransitions.attempt(receipt.state()).isPresent())
            throw new IllegalArgumentException("original white-peace request remains unresolved; no new action ID may resubmit it");
    }
    private static boolean sameScope(ActionReceipt receipt, Complete current) {
        if (!(receipt.command().origin() instanceof CommandOrigin.Gameplay)) return false;
        return Objects.equals(receipt.command().before().frame().episodeRunId(), current.identity().frame().episodeRunId());
    }
}
