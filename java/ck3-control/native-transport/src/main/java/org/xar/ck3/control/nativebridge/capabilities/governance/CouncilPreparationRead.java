package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.time.Clock;
import java.util.ArrayList;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.governance.council.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Refresh the native cached Council position/candidate collection in the original submit scope. */
public final class CouncilPreparationRead implements GovernanceActionPreparation.CouncilRefreshPort {
    private final PlanningReadPort reads; private final PrivateCouncilReads definitions; private final ActionPorts.OutcomeArchive archive;
    private final Clock clock; private final int maximumPolls; private final String version; private final String sha256;
    public CouncilPreparationRead(PlanningReadPort reads, PrivateCouncilReads actualDefinitions, ActionPorts.OutcomeArchive archive,
            Clock clock, int maximumPolls, String version, String sha256) {
        this.reads = Objects.requireNonNull(reads); definitions = Objects.requireNonNull(actualDefinitions); this.archive = Objects.requireNonNull(archive);
        this.clock = Objects.requireNonNull(clock); StrictJson.require(maximumPolls > 0 && maximumPolls <= 3000, "bounded Council preflight required"); this.maximumPolls = maximumPolls;
        CouncilCodec.requireBuild(version, sha256); this.version = version; this.sha256 = sha256;
    }
    @Override public void verify(ContinuityStorePort.Session borrowed, ActionCommand command, String originalRequestId) {
        GovernanceActionScope.Context context = GovernanceActionScope.current(command);
        StrictJson.require(context.session(command) == borrowed, "Council preflight borrowed a different writer Session"); context.mailbox(command);
        var expected = GovernanceActionPreparation.councilRequest(command, originalRequestId);
        var query = new PlanningReadRequest(command.before(), command.source(), command.sessionId(), definitions.gates().operation(),
                new Obj(Map.of()).with("position_key", new Text(expected.position().key())), command.deadline());
        var receipts = new ArrayList<PlanningReadReceipt>();
        PlanningReadResult<CouncilPrivateCodec.Reply> current = reads.read(borrowed, definitions.gates(), query);
        for (int polls = 0; ; polls++) {
            if (current instanceof PlanningReadResult.Unavailable<CouncilPrivateCodec.Reply> unavailable) {
                unavailable.original().ifPresent(original -> archive.inSession(borrowed, bound -> bound.preserve(original)));
                throw new IllegalStateException("fresh Council final gates unavailable; no assignment submitted: " + unavailable.reason());
            }
            var known = (PlanningReadResult.Known<CouncilPrivateCodec.Reply>) current; receipts.add(known.receipt());
            if (known.value() instanceof CouncilPrivateCodec.Terminal terminal) {
                CouncilPrivateCodec.requireTerminalBinding(terminal, CouncilPrivateCodec.GATES, PrivateCouncilReads.nativeFrame(query));
                var normalized = CouncilPrivateCodec.normalize(terminal, CouncilPrivateCodec.GATES, PrivateCouncilReads.nativeFrame(query),
                        GovernanceNativeReads.frame(query), expected.position(), version, sha256);
                var fresh = CouncilCodec.object(StrictJson.parse(normalized.bytes()));
                var previous = CouncilCodec.object(StrictJson.parse(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(command.arguments())).get("original_query"));
                StrictJson.require(CouncilCodec.text(fresh, "status").equals("available") && fresh.hasNonNull("council_composition_candidates") && fresh.hasNonNull("council_final_gates"), "fresh Council final gates contain no complete candidate material");
                StrictJson.require(fresh.get("council_composition_candidates").equals(previous.get("council_composition_candidates"))
                        && fresh.get("council_final_gates").equals(previous.get("council_final_gates")), "Council source changed between selection and original submit transaction");
                context.retainPreflight(command, receipts);
                // Do not complete the scope: the original one-submit operation and its canonical continuations follow.
                return;
            }
            if (polls >= maximumPolls || !clock.instant().isBefore(command.deadline())) throw new IllegalStateException("Council preflight pending/unknown; never requeue or submit");
            try { Thread.sleep(10); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("Council preflight interrupted; no assignment submitted", interrupted); }
            current = reads.read(borrowed, definitions.status(), new PlanningReadRequest(command.before(), command.source(), command.sessionId(), definitions.status().operation(), new Obj(Map.of()), command.deadline()));
        }
    }
}
