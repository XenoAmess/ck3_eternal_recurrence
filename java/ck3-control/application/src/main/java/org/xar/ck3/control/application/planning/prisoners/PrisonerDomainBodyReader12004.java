package org.xar.ck3.control.application.planning.prisoners;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;

/** Reads the sole writer's already imported originals. This adapter never imports, initializes, previews or commits a body. */
public final class PrisonerDomainBodyReader12004 implements LedgerReadPort {
    private final DomainBodies.Store store;
    private final String machineId;
    public PrisonerDomainBodyReader12004(DomainBodies.Store store, String machineId) {
        this.store = Objects.requireNonNull(store); this.machineId = StrictJson.text(machineId);
    }
    @Override public LedgerView read(PlanningRequest request) {
        if (!request.before().machineId().equals(machineId)) return new LedgerUnavailable("domain store belongs to another machine");
        try {
            DomainBodies.Read releaseRead = store.read(DomainBodies.Slot.PRISONER_RELEASE);
            DomainBodies.Read ransomRead = store.read(DomainBodies.Slot.PRISONER_RANSOM);
            if (releaseRead instanceof DomainBodies.Unavailable missing)
                return new LedgerUnavailable("release:" + missing.reason() + ":" + missing.detail());
            if (ransomRead instanceof DomainBodies.Unavailable missing)
                return new LedgerUnavailable("ransom:" + missing.reason() + ":" + missing.detail());
            var release = (DomainBodies.Available) releaseRead; var ransom = (DomainBodies.Available) ransomRead;
            StrictJson.require(release.reference().slot() == DomainBodies.Slot.PRISONER_RELEASE
                    && ransom.reference().slot() == DomainBodies.Slot.PRISONER_RANSOM
                    &&release.reference().contractSchema().equals(PrisonerEpisodeLedger12004.contractSchema(Family.RELEASE))
                    &&ransom.reference().contractSchema().equals(PrisonerEpisodeLedger12004.contractSchema(Family.RANSOM)), "domain body slot or explicit current contract differs");
            StrictJson.require(release.head().equals(ransom.head()) && release.headSources().equals(ransom.headSources()),
                    "domain documents were not read from one exact continuity head");
            var releaseEpoch=PrisonerEpisodeLedger12004.decode(Family.RELEASE,new RawJson(release.canonicalBody()));
            var ransomEpoch=PrisonerEpisodeLedger12004.decode(Family.RANSOM,new RawJson(ransom.canonicalBody()));
            releaseEpoch.epoch().owner().require(request.before(),request.source(),request.sessionId());
            ransomEpoch.epoch().owner().require(request.before(),request.source(),request.sessionId());
            OpportunityJson.Obj releaseBody = object(release.canonicalBody()), ransomBody = object(ransom.canonicalBody());
            Optional<Pending> releasePending = pending(request, Family.RELEASE, releaseBody.get("pending"), release.reference().payload());
            Optional<Pending> ransomPending = pending(request, Family.RANSOM, ransomBody.get("pending"), ransom.reference().payload());
            StrictJson.require(stable(release, store.read(DomainBodies.Slot.PRISONER_RELEASE))
                    && stable(ransom, store.read(DomainBodies.Slot.PRISONER_RANSOM)), "domain source/head changed during pair read");
            return new KnownLedger(release.head(), releasePending, ransomPending);
        } catch (IOException | IllegalArgumentException failure) {
            String message = failure.getMessage() == null ? "domain original unavailable" : failure.getMessage();
            return new LedgerUnavailable(message.substring(0, Math.min(1024, message.length())));
        }
    }
    private static Optional<Pending> pending(PlanningRequest request, Family family, OpportunityJson.Value value,
            org.xar.ck3.control.contracts.ExactRef source) {
        if (value == OpportunityJson.Nil.INSTANCE) return Optional.empty();
        OpportunityJson.Obj body = OpportunityJson.object(value, "pending");
        StrictJson.require(OpportunityJson.integer(body.get("player_character_id"), "player_character_id")
                .equals(request.before().frame().identity().player()), "pending belongs to another played actor");
        var nativeRevision = OpportunityJson.integer(body.get("pre_native_revision"), "pre_native_revision");
        var date = OpportunityJson.integer(body.get("pre_date_raw"), "pre_date_raw");
        StrictJson.require(nativeRevision.signum() > 0 && nativeRevision.compareTo(request.before().frame().identity().nativeRevision()) <= 0
                && date.signum() >= 0 && date.compareTo(request.before().frame().identity().dateRaw()) <= 0, "pending frame is unobserved or ahead");
        if (body.members().containsKey("pre_public_revision")) {
            var revision = OpportunityJson.integer(body.get("pre_public_revision"), "pre_public_revision");
            StrictJson.require(revision.signum() > 0 && revision.compareTo(request.before().frame().revision()) <= 0, "pending public frame is ahead");
        }
        return Optional.of(new Pending(family, body, source));
    }
    private static void objectOrNull(OpportunityJson.Value value, String name) {
        StrictJson.require(value == OpportunityJson.Nil.INSTANCE || value instanceof OpportunityJson.Obj, name + " must be explicit object/null");
    }
    private static boolean stable(DomainBodies.Available expected, DomainBodies.Read current) {
        return current instanceof DomainBodies.Available actual && expected.reference().equals(actual.reference())
                && expected.head().equals(actual.head()) && expected.headSources().equals(actual.headSources())
                && Arrays.equals(expected.canonicalBody(), actual.canonicalBody());
    }
}
