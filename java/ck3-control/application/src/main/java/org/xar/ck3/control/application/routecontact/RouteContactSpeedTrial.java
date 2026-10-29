package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvanceReadiness;
import org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original explicit speed5 route-only trial. The existing durable parent intent is the sole consumed-attempt marker. */
public final class RouteContactSpeedTrial implements RouteContactComposite.SpeedSelection {
    public static final String KEY = "contact_free_exact_route_speed_trial_v1";
    public static final String SCHEMA = "xar.ck3.contact-free-exact-route-speed-trial/v1";
    private static final Set<String> REQUIRED = Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1", "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
            "game.command.query-route-contact-horizon-v1-N");
    public record Configuration(String campaignId, String trialId, int startDateRaw, int endpointDateRaw,
            int globalRouteSpeed, int effectiveRouteSpeed, boolean globalHighSpeedAb) {
        public Configuration { StrictJson.text(campaignId); StrictJson.text(trialId);
            StrictJson.require(trialId.length() <= 160 && endpointDateRaw > startDateRaw && globalRouteSpeed == 3 && effectiveRouteSpeed == 3 && !globalHighSpeedAb,
                    "explicit route-only trial requires configured campaign dates, baseline3 and high-speed A/B false"); }
    }
    public record Receipt(Configuration configuration, String selectionStatus, int selectedSpeed, boolean attemptConsumed,
            boolean liveReady, int attemptLimit) {
        public Receipt { Objects.requireNonNull(configuration); StrictJson.text(selectionStatus); StrictJson.require(selectedSpeed >= 1 && selectedSpeed <= 5
                && !liveReady && attemptLimit == 1, "controlled pending-live single-attempt trial only"); }
        public Obj tag() { return new Obj(Map.of("schema", new Text(SCHEMA), "campaign_id", new Text(configuration.campaignId()),
                "trial_id", new Text(configuration.trialId()), "selection_status", new Text(selectionStatus), "selected_speed", new IntegerValue(java.math.BigInteger.valueOf(selectedSpeed)),
                "attempt_consumed", new Bool(attemptConsumed), "live_ready", new Bool(false), "attempt_limit", new IntegerValue(java.math.BigInteger.ONE),
                "start_date_raw", new IntegerValue(java.math.BigInteger.valueOf(configuration.startDateRaw())),
                "endpoint_date_raw", new IntegerValue(java.math.BigInteger.valueOf(configuration.endpointDateRaw())))); }
    }
    private final Configuration configuration;
    private final ActionSnapshotReader receipts;
    private final AdvanceReadiness.Port readiness;
    public RouteContactSpeedTrial(Configuration configuration, CampaignDeadline.Configuration actualCampaign, ActionSnapshotReader receipts, AdvanceReadiness.Port readiness) {
        this.configuration = Objects.requireNonNull(configuration); this.receipts = Objects.requireNonNull(receipts); this.readiness = Objects.requireNonNull(readiness);
        Objects.requireNonNull(actualCampaign);
        StrictJson.require(actualCampaign.founding().campaignId().equals(configuration.campaignId())
                && actualCampaign.founding().startDateRaw().intValueExact() == configuration.startDateRaw()
                && actualCampaign.endpointDateRaw().intValueExact() == configuration.endpointDateRaw(), "route trial must retain the exact same immutable configured campaign deadline");
    }
    /** Planner may bind this exact tag before its sole durable parent intent. This method never consumes or submits. */
    public Receipt plan(ActionCommand proposed, AdvanceObservationPort.Frame original, Proof proof, int fallbackSpeed) {
        Frame frame = RouteContactCodec.frame(original); AdvanceReadiness.Facts facts = readiness.inspect(proposed, original);
        StrictJson.require(facts.observed().equals(original.identity()) && original.source().equals(proposed.source())
                && original.sessionId().equals(proposed.sessionId()), "trial input source/capability frame differs");
        String status = "not_contact_free"; int selected = fallbackSpeed;
        if (proof.kind() == ProofKind.CONTACT_FREE) {
            if (priorClaim(proposed.actionId(), proposed.sessionId())) status = "controlled_trial_attempt_exhausted";
            else if (frame.dateRaw() >= configuration.endpointDateRaw()) status = "campaign_endpoint_reached";
            else if (!facts.bridgeCapabilities().containsAll(REQUIRED) || !facts.actionSteps().containsAll(Set.of(new OperationKey("set-speed-5"), new OperationKey("resume-map"), new OperationKey("pause-map"))))
                status = "native_clock_or_speed_capability_missing";
            else if (!frame.paused() || !frame.mapReady() || frame.playerDecision()) status = "player_decision_or_map_boundary";
            else { selected = 5; status = "selected_controlled_trial"; }
        }
        return new Receipt(configuration, status, selected, status.equals("selected_controlled_trial"), false, 1);
    }
    @Override public int select(ActionCommand parent, AdvanceObservationPort.Frame starting, Proof proof, int fallbackSpeed) {
        Receipt selection = plan(parent, starting, proof, fallbackSpeed);
        Value supplied = parent.arguments().get(KEY);
        StrictJson.require(supplied != null && supplied.equals(selection.tag()), "configured route-only trial must bind its actual selected tag in the original parent body");
        if (selection.attemptConsumed()) {
            // The same writer lock already committed this complete body. A process restart sees this marker and may only reconcile.
            ActionReceipt own = receipts.find(parent.actionId()).orElseThrow(() -> new IllegalStateException("trial cannot consume before original durable parent intent"));
            StrictJson.require(own.bodySha256().equals(ActionCodec.bodySha256(parent)) && own.command().equals(parent), "trial durable parent differs");
        }
        return selection.selectedSpeed();
    }
    private boolean priorClaim(String currentActionId, String sessionId) {
        return receipts.withFrozen(lease -> {
            List<Obj> tags = lease.snapshot().actions().stream().filter(receipt -> !receipt.command().actionId().equals(currentActionId) && receipt.command().sessionId().equals(sessionId))
                    .map(receipt -> receipt.command().arguments().get(KEY)).filter(Obj.class::isInstance).map(Obj.class::cast)
                    .filter(tag -> new Text(SCHEMA).equals(tag.get("schema")) && new Text(configuration.campaignId()).equals(tag.get("campaign_id"))).toList();
            for (Obj tag : tags) StrictJson.require(new Text(configuration.trialId()).equals(tag.get("trial_id"))
                    && new IntegerValue(java.math.BigInteger.valueOf(configuration.startDateRaw())).equals(tag.get("start_date_raw"))
                    && new IntegerValue(java.math.BigInteger.valueOf(configuration.endpointDateRaw())).equals(tag.get("endpoint_date_raw")), "a held driver session cannot replace its configured trial identity or dates");
            boolean used = tags.stream().anyMatch(tag -> new Bool(true).equals(tag.get("attempt_consumed")));
            lease.assertCurrent(); return used;
        });
    }
}
