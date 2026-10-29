package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;

/** Shared data boundary for actual owned-submission facts. Decoding this audit grants no live observation or funds. */
public final class ConstructionFundingEvidence {
    public static final String FIELD = "funding_source_evidence";
    private ConstructionFundingEvidence() { }
    public static Obj capture(CanonicalFundingPending.Observed actual, Obj financingRequest) {
        Objects.requireNonNull(actual); var evidence = actual.sourceEvidence();
        requirePending(financingRequest, evidence);
        require(actual.pending().equals(CanonicalFundingPending.pending(evidence))
                && actual.pending() instanceof EmergencyFinancingAssessment.NoPendingAction,
                "actual owned-submission inventory must explicitly permit optional construction");
        return CanonicalFundingPending.evidenceJson(evidence);
    }
    public static CanonicalFundingPending.SourceEvidence command(ActionCommand command) {
        Objects.requireNonNull(command);
        var evidence = decode(object(command.arguments().get(FIELD), "actual construction funding source evidence"));
        Obj request = object(command.arguments().get("ordinary_cash_request"), "original ordinary cash request");
        requirePending(object(request.get("financing_request"), "actual financing request"), evidence);
        require(evidence.current().equals(command.before()) && evidence.source().equals(command.source()) && evidence.sessionId().equals(command.sessionId()),
                "funding evidence crossed the complete original Game/frame/source/session");
        return evidence;
    }
    public static CanonicalFundingPending.SourceEvidence decode(Obj value) {
        var evidence = CanonicalFundingPending.decodeEvidence(encode(Objects.requireNonNull(value)));
        require(CanonicalFundingPending.pending(evidence) instanceof EmergencyFinancingAssessment.NoPendingAction,
                "construction funding data must preserve explicitly clear owned submissions; UNKNOWN never authorizes spend");
        return evidence;
    }
    public static void requireCurrent(ActionCommand command, CanonicalFundingPending.Observed current, Obj currentFinancingRequest) {
        var planned=command(command); capture(Objects.requireNonNull(current), currentFinancingRequest);
        require(current.sourceEvidence().current().equals(command.before()) && current.sourceEvidence().source().equals(command.source())
                && current.sourceEvidence().sessionId().equals(command.sessionId()), "fresh funding source crossed the current command frame/source/session");
        require(current.sourceEvidence().ledgerSequence() >= planned.ledgerSequence(), "fresh owned-submission evidence predates the retained planned writer point");
        // A fresh readonly query may advance the canonical Head. The actual same-writer producer revalidates its own new point.
        // New commitments, UNKNOWN and cash changes are independently reevaluated by the identical live construction gate.
    }
    private static void requirePending(Obj financingRequest, CanonicalFundingPending.SourceEvidence evidence) {
        var request = EmergencyFinancingAssessmentCodec.decode(encode(Objects.requireNonNull(financingRequest)));
        require(request.pending().equals(CanonicalFundingPending.pending(evidence)),
                "financing request differs from the sole owned-submission producer's complete facts");
    }
}
