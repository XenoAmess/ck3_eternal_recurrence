package org.xar.ck3.control.application.routecontact;

import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.routecontact.RouteContactComposite.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Thin domain adapter over the one Root archive. Session/writer scope is enforced by that archive. */
public final class RouteContactEvidenceArchive implements EvidenceArchive {
    private final ActionPorts.OutcomeArchive archive;
    public RouteContactEvidenceArchive(ActionPorts.OutcomeArchive archive) { this.archive = Objects.requireNonNull(archive); }
    @Override public ExactRef completed(ActionCommand parent, Completion completion) {
        return archive.preserveMaterial(RouteContactEvidenceCodec.encode(new RouteContactEvidenceCodec.Completed(parent, completion), archive));
    }
    @Override public ExactRef failed(ActionCommand parent, ContactFailure failure) {
        return archive.preserveMaterial(RouteContactEvidenceCodec.encode(new RouteContactEvidenceCodec.Failed(parent, failure), archive));
    }
    /** Driver assembler calls this only with the actual canonical parent receipt, under its original writer lock. */
    public static Obj compatibleResult(ActionReceipt actual, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(RouteContactSteps.supports(actual.command().operation().value()), "route result adapter received another operation");
        ExactRef reference;
        if (actual.state() instanceof ActionState.CompositeSettled settled) {
            if (settled.settlement() instanceof ActionState.Applied applied) reference = basis(applied.observation());
            else if (settled.settlement() instanceof ActionState.CompositeControlApplied control) reference = basis(control.observation().semantic());
            else throw new IllegalArgumentException("route parent has no verified domain completion");
        } else if (actual.state() instanceof ActionState.CompositeUnknown unknown) {
            StrictJson.require(!unknown.evidence().isEmpty(), "unknown route parent lacks its original failure evidence"); reference = unknown.evidence().getFirst();
        } else throw new IllegalArgumentException("route result requires its actual composite parent receipt");
        RouteContactEvidenceCodec.Document document = RouteContactEvidenceCodec.decode(archive.loadFullMaterial(reference), archive);
        StrictJson.require(document.parent().equals(actual.command()) && ActionCodec.bodySha256(document.parent()).equals(actual.bodySha256()), "route archive is for another parent body");
        boolean completed = actual.state() instanceof ActionState.CompositeSettled settled
                && (settled.settlement() instanceof ActionState.Applied || settled.settlement() instanceof ActionState.CompositeControlApplied);
        StrictJson.require((document instanceof RouteContactEvidenceCodec.Completed) == completed, "route archive completion differs from actual typed writer settlement");
        if (document instanceof RouteContactEvidenceCodec.Completed done) {
            StrictJson.require(done.completion().clockResult().originalReport().isPresent(), "historical route evidence lacks its actual complete clock report; full current result unavailable");
            done.completion().refresh().ifPresent(refresh -> StrictJson.require(refresh.originalDriverResult().isPresent(), "historical pause ACK token is not its complete current Driver result"));
        }
        return RouteContactEvidenceCodec.result(document);
    }
    public static ExactRef basis(ActionState.EffectObservation effect) {
        StrictJson.require(effect.observerSchema().equals(RouteContactComposite.OBSERVER) && effect.supportingEvidence().size() == 1,
                "route settlement requires its single exact domain basis"); return effect.supportingEvidence().getFirst();
    }
}
