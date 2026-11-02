package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure current-seat DATA check; original canonical receipt and fresh-READ custody stay caller obligations. */
final class CouncilRecoverySeatProof {
    private CouncilRecoverySeatProof() { }

    static CouncilModels.Candidates require(ActionCommand command, ActionState.Attempt attempt,
            CouncilActionCodec.Receipt applied, NativeEffectSnapshots.Pair pair, GuardEvidence observation,
            List<PlanningReadReceipt> reads, PrivateCouncilReads definitions, String version, String sha) throws IOException {
        Objects.requireNonNull(command); Objects.requireNonNull(attempt); Objects.requireNonNull(applied);
        Objects.requireNonNull(pair); Objects.requireNonNull(observation); Objects.requireNonNull(definitions);
        reads = List.copyOf(Objects.requireNonNull(reads)); CouncilCodec.requireBuild(version, sha);
        StrictJson.require(command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN)
                && applied.status() == CouncilActionCodec.ReceiptStatus.APPLIED,
                "recovered seat proof requires the original private Council APPLIED receipt");
        var expected = GovernanceActionPreparation.councilRequest(command, attempt.requestId());
        var ack = CouncilActionCodec.decodeAck(applied.ack().original().bytes(), expected);
        StrictJson.require(ack.equals(applied.ack())
                && CouncilActionCodec.decodeReceipt(applied.original().bytes(), ack).equals(applied),
                "original Council APPLIED DTO differs from its actual selected request and native bytes");

        StrictJson.require(observation.origin() instanceof CommandOrigin.Reconciliation,
                "recovered Council seat requires the actual same-capture reconciliation guard");
        var identity = observation.origin().requireReconciliation(); var pending = identity.pending();
        var before = pair.before(); var after = pair.after(); var actual = after.identity();
        StrictJson.require(pair.reconciliation().filter(identity::sameGuardFrame).isPresent()
                && pending.actionId().equals(command.actionId())
                && pending.bodySha256().equals(ActionCodec.bodySha256(command))
                && pending.requestId().equals(attempt.requestId()) && pending.originalBefore().equals(command.before())
                && observation.operation().equals(command.operation())
                && observation.authorityId().equals(attempt.guard().authorityId()),
                "recovered Council seat changed its original pending command or same-capture guard");
        identity.requireOriginalConnection(attempt.guard());
        StrictJson.require(before.identity().equals(command.before())
                && before.source().equals(command.source()) && before.sessionId().equals(command.sessionId())
                && before.originalEvidence().equals(attempt.guard().nativeEvidence())
                && actual.equals(identity.factual())
                && actual.machineId().equals(command.before().machineId()) && actual.game().equals(command.before().game())
                && actual.frame().episodeRunId().equals(command.before().frame().episodeRunId())
                && after.source().equals(command.source()) && after.sessionId().equals(command.sessionId())
                && observation.source().equals(after.source()) && observation.sessionId().equals(after.sessionId())
                && observation.connectionGeneration().equals(after.connectionGeneration())
                && observation.nativeEvidence().equals(after.originalEvidence())
                && observation.observedAt().equals(after.observedAt())
                && identity.evidence().observationManifest().equals(NativeEffectEvidence.basis(after).driverFacts()),
                "recovered Council seat crossed its actual original/new frame, actor, source or full Driver binding");
        StrictJson.require(actual.frame().identity().nativeRevision().compareTo(applied.postNativeRevision()) >= 0
                && actual.frame().identity().nativeRevision().compareTo(applied.postPublicRevision()) >= 0
                && actual.frame().identity().dateRaw().intValueExact() >= applied.postDateRaw()
                && actual.frame().identity().player().intValueExact() == applied.ownerId()
                && applied.ownerId() == expected.frame().ownerId()
                && applied.position() == expected.position() && applied.incumbentId() == expected.candidateId(),
                "current Council seat regressed its original applied Native-layer frame or selected owner/position/candidate");

        GovernanceReadChronology.requireOrderedReads(reads);
        CouncilModels.Candidates verified = null;
        for (int index = 0; index < reads.size(); index++) {
            PlanningReadReceipt read = reads.get(index); var request = read.request();
            boolean initial = index == 0; String operation = initial ? CouncilPrivateCodec.QUERY : CouncilPrivateCodec.STATUS;
            StrictJson.require(request.operation().value().equals(operation)
                    && read.adoption().isEmpty() && read.retainedMaterial().isEmpty()
                    && read.archiveVersion() == PlanningReadReceipt.ArchiveVersion.CURRENT_V2
                    && !read.requestId().equals(attempt.requestId()),
                    "new Council seat chain requires only original QUERY then STATUS receipts, never adoption, GATES or old action ID");
            if (initial) {
                var arguments = StrictJson.object(StrictJson.parse(OpportunityJson.encode(request.arguments())), Set.of("position_key"));
                StrictJson.require(CouncilCodec.text(arguments, "position_key").equals(expected.position().key()),
                        "new Council seat QUERY selected a different position");
            } else StrictJson.require(request.arguments().members().isEmpty(), "Council seat STATUS arguments must be empty");
            StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay
                    && request.before().equals(actual) && request.source().equals(after.source())
                    && request.sessionId().equals(after.sessionId()), "new Council seat request changed the actual captured frame/source/session");
            for (var guard : List.of(read.before(), read.after())) {
                StrictJson.require(guard.binding().origin() instanceof CommandOrigin.Gameplay
                        && guard.binding().observed().equals(actual)
                        && guard.binding().source().equals(after.source()) && guard.binding().sessionId().equals(after.sessionId())
                        && guard.binding().connectionGeneration().equals(after.connectionGeneration())
                        && guard.binding().nativeEvidence().equals(after.originalEvidence())
                        && guard.binding().capabilityEvidence().equals(observation.capabilityEvidence())
                        && guard.originalBindingSha256().equals(after.fullBindingSha256()),
                        "new Council seat read guard escaped the same captured Native/full Driver/connection originals");
            }
            var custody = read.original().custody().orElseThrow();
            StrictJson.require(!custody.writeEntered().observedAt().isBefore(after.observedAt())
                    && !custody.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                    "new Council seat query predates the actual after capture or original submission");
            CouncilContinuationPolicy.result(read.original());
            var reply = initial ? definitions.query().replay(read) : definitions.status().replay(read);
            if (reply instanceof CouncilPrivateCodec.Pending) {
                StrictJson.require(index < reads.size() - 1, "pending Council seat mailbox is not an incumbent proof");
                continue;
            }
            StrictJson.require(reply instanceof CouncilPrivateCodec.Terminal && index == reads.size() - 1,
                    "Council seat proof requires exactly one final terminal and no records after it");
            var terminal = (CouncilPrivateCodec.Terminal) reply;
            var nativeFrame = PrivateCouncilReads.nativeFrame(request); var publicFrame = GovernanceNativeReads.frame(request);
            CouncilPrivateCodec.requireTerminalBinding(terminal, CouncilPrivateCodec.QUERY, nativeFrame);
            var normalized = CouncilPrivateCodec.normalize(terminal, CouncilPrivateCodec.QUERY, nativeFrame, publicFrame,
                    expected.position(), version, sha);
            var material = CouncilCodec.object(StrictJson.parse(normalized.bytes()));
            StrictJson.require(CouncilCodec.text(material, "status").equals("available"), "current Council seat material is unavailable");
            var payload = material.get("council_composition_candidates");
            StrictJson.require(payload != null && payload.isObject(), "current Council seat lacks its actual candidate/position payload");
            // normalize preserves the native six-field payload; only its enclosing source_frame uses Java public revision.
            verified = CouncilCodec.decode(StrictJson.canonical(payload), nativeFrame, expected.position());
            StrictJson.require(verified.seat().position() == expected.position()
                    && verified.frame().ownerId() == expected.frame().ownerId()
                    && verified.seat().incumbentId().isPresent()
                    && verified.seat().incumbentId().orElseThrow() == expected.candidateId(),
                    "current Council position/owner/incumbent does not prove the original selected candidate");
        }
        StrictJson.require(verified != null, "Council seat chain ended without actual terminal incumbent material");
        return verified;
    }
}
