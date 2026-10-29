package org.xar.ck3.control.g2.m6;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m6.G2M6Contracts.CampaignAssessment;
import org.xar.ck3.control.g2.m6.G2M6Contracts.CampaignEvidence;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.EpisodeAssessment;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Gate;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NamedGainEvidence;
import org.xar.ck3.control.g2.m6.G2M6Contracts.StartEvidence;
import org.xar.ck3.control.g2.m6.G2M6Contracts.StartOrigin;
import org.xar.ck3.control.g2.m6.G2M6Contracts.TerminalCause;
import org.xar.ck3.control.g2.m6.G2M6Contracts.TerminalEvidence;

/**
 * P55 offline Sway evidence assessment. It reads no files, submits no action, and changes no authoritative milestone.
 * A neutral retained terminal can prepare an evidence packet; it supplies no attributed successful outcome.
 */
public final class M6Research implements G2Domain {
    public static final String EVIDENCE_PACKET_SCHEMA = "xar.g2.m6.evidence-packet/v1";
    public static final String RESULT_SCHEMA = "xar.g2.m6.sway-evidence-assessment/v1";

    @Override public Milestone milestone() { return Milestone.M6; }

    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request);
        StrictJson.require(request.milestone() == Milestone.M6, "M6 domain receives only the M6 milestone");
        var envelope = StrictJson.parse(request.payload().bytes(),StrictJson.EXPLICIT_MAX_BYTES);
        if (envelope.has("schema") && envelope.get("schema").isTextual()
                && M6ServiceIntegration.PACKET_SCHEMA.equals(envelope.get("schema").textValue())) {
            return M6ServiceIntegration.evaluate(request, this);
        }
        boolean packet = envelope.has("schema") && envelope.get("schema").isTextual()
                && EVIDENCE_PACKET_SCHEMA.equals(envelope.get("schema").textValue());
        CampaignEvidence evidence = packet
                ? M6SourceProducer.fromEvidencePacket(request.payload().bytes(),request.source())
                : M6SourceProducer.fromClosedLedger(request.payload().bytes(),request.source());
        CampaignAssessment assessment = evaluateCampaign(evidence);
        return new G2Response(request.requestId(),Milestone.M6,request.source(),toJson(assessment));
    }

    public CampaignAssessment evaluateCampaign(CampaignEvidence evidence) {
        Objects.requireNonNull(evidence);
        List<EpisodeAssessment> episodes = new ArrayList<>();
        for (Episode episode : evidence.episodes()) { episodes.add(evaluateEpisode(episode)); }
        return new CampaignAssessment(episodes,episodes.stream().anyMatch(EpisodeAssessment::evidencePacketReady),
                episodes.stream().anyMatch(EpisodeAssessment::usefulSchemeComplete),false);
    }

    public EpisodeAssessment evaluateEpisode(Episode episode) {
        Objects.requireNonNull(episode);
        EnumSet<Gate> satisfied = EnumSet.noneOf(Gate.class);
        StartEvidence start = episode.start().orElse(null);
        NamedGainEvidence gain = episode.firstNamedGain().orElse(null);
        TerminalEvidence terminal = episode.terminal().orElse(null);
        boolean ordinary = start != null && start.postconditionVerified()
                && start.origin() == StartOrigin.ORDINARY_FULL_PLANNER
                && start.independentActive().notEarlierThan(start.applied());
        if (ordinary) { satisfied.add(Gate.ORDINARY_START); }
        boolean baseline = gain != null && gain.trackedInstanceActive() && gain.before().points().isPresent()
                && gain.observed().laterThan(gain.baseline()) && start != null
                && gain.baseline().notEarlierThan(start.independentActive());
        if (baseline) { satisfied.add(Gate.EARLY_NAMED_BASELINE); }
        boolean namedGain = baseline && gain.incrementalNamedGainObserved() && gain.after().points().isPresent()
                && gain.after().points().orElseThrow().compareTo(BigInteger.ZERO) > 0
                && gain.after().points().orElseThrow().compareTo(gain.before().points().orElseThrow()) > 0;
        if (namedGain) { satisfied.add(Gate.INCREMENTAL_NAMED_GAIN); }
        boolean naturalTerminal = terminal != null && terminal.independentNatural()
                && terminal.instanceTerminalOutcomeObserved() && gain != null
                && terminal.observed().laterThan(gain.observed());
        if (naturalTerminal) { satisfied.add(Gate.NATURAL_RETAINED_TERMINAL); }
        boolean laterConsumption = start != null && gain != null && terminal != null
                && start.consumption().consumedAfter(start.independentActive())
                && gain.consumption().consumedAfter(gain.observed())
                && terminal.consumption().consumedAfter(terminal.observed());
        if (laterConsumption) { satisfied.add(Gate.LATER_ORDINARY_CONSUMPTION); }
        EnumSet<Gate> missing = EnumSet.allOf(Gate.class); missing.removeAll(satisfied);
        boolean packetReady = missing.isEmpty();
        boolean attributed = packetReady && terminal.terminalCauseObserved()
                && terminal.cause() == TerminalCause.AUTHORED_SWAY_COMPLETE_100;
        return new EpisodeAssessment(episode.identity(),satisfied,missing,packetReady,attributed);
    }

    public ProjectionJson toJson(CampaignAssessment assessment) {
        Objects.requireNonNull(assessment);
        ObjectNode result = StrictJson.object();
        result.put("schema",RESULT_SCHEMA); result.put("milestone_status","in_progress");
        result.put("evidence_packet_ready",assessment.evidencePacketReady());
        result.put("attributed_success_evidence",assessment.schemeComplete());
        result.put("whole_m6_complete",false); result.put("grants_submission_authority",false);
        result.put("game_day_credit",0); result.put("ordinary_cycle_credit",0);
        result.put("institution_or_prisoner","not_assessed_from_sway_ledger");
        result.put("nonreligious_decision_or_law","not_assessed_from_sway_ledger");
        result.put("activity_lifecycle","not_assessed_from_sway_ledger");
        var episodes = result.putArray("episodes");
        for (EpisodeAssessment episode : assessment.episodes()) {
            ObjectNode row = episodes.addObject(); var identity = episode.identity();
            row.put("action_id",identity.actionId()); row.put("actor_character_id",identity.actorCharacterId());
            row.put("target_character_id",identity.targetCharacterId()); row.put("scheme_instance_id",identity.schemeInstanceId());
            row.put("scheme_instance_generation",identity.schemeInstanceGeneration());
            row.put("evidence_packet_ready",episode.evidencePacketReady());
            row.put("attributed_success_evidence",episode.usefulSchemeComplete());
            var satisfied = row.putArray("satisfied"); var missing = row.putArray("missing");
            for (Gate gate : Gate.values()) {
                if (episode.satisfied().contains(gate)) { satisfied.add(gate.name()); }
                else { missing.add(gate.name()); }
            }
        }
        return ProjectionJson.object(StrictJson.canonical(result),StrictJson.INPUT_MAX_BYTES);
    }
}

