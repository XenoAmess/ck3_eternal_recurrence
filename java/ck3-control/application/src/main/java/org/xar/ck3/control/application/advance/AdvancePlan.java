package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One durable, versioned requested slice. A clock request is never a completed game day. */
public record AdvancePlan(BigInteger startingDateRaw, BigInteger targetDateRaw, int horizonDays,
        int speed, String policy, boolean exactOneDay, ClockMode clockMode,
        Optional<CampaignDeadline.Cap> campaignDeadline, Optional<WarDailyWatch.Context> dailyWatch) {
    public static final String KEY = "advance_v1";
    public static final String SCHEMA = "xar.ck3.java-life-advance-plan/v2";
    public static final String LEGACY_SCHEMA = "xar.ck3.java-life-advance-plan/v1";
    public static final String OBSERVER = "xar.ck3.java-life-advance-observation/v1";
    public static final BigInteger DAY = BigInteger.valueOf(24);
    public enum ClockMode { POLLED, EXACT_SENTINEL, CAMPAIGN_SENTINEL }
    public AdvancePlan {
        Objects.requireNonNull(startingDateRaw); Objects.requireNonNull(targetDateRaw);
        require(startingDateRaw.signum() >= 0 && targetDateRaw.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0
                && horizonDays >= 1 && horizonDays <= 45 && targetDateRaw.equals(startingDateRaw.add(DAY.multiply(BigInteger.valueOf(horizonDays)))),
                "bounded native int32 whole-day slice required");
        require(speed >= 1 && speed <= 5 && policy != null && !policy.isEmpty(), "actual selected speed/policy required");
        Objects.requireNonNull(clockMode); Objects.requireNonNull(campaignDeadline); Objects.requireNonNull(dailyWatch);
        require(!exactOneDay || horizonDays == 1, "exact day must retain its +24 target");
        require(clockMode != ClockMode.EXACT_SENTINEL || exactOneDay, "exact sentinel requires exact-day semantics");
        require(clockMode != ClockMode.CAMPAIGN_SENTINEL || campaignDeadline.isPresent(), "campaign clock requires its actual cap");
        campaignDeadline.ifPresent(cap -> require(cap.status() == CampaignDeadline.Status.ADVANCE
                && cap.startingDateRaw().equals(startingDateRaw) && cap.targetDateRaw().equals(targetDateRaw)
                && targetDateRaw.compareTo(cap.boundaryDateRaw()) <= 0, "advance plan crossed its frozen campaign boundary"));
        require(dailyWatch.isPresent() == WarDailyWatch.POLICY.equals(policy), "watch policy and frozen complete roster must occur together");
        dailyWatch.ifPresent(watch -> require(exactOneDay && speed == 2 && clockMode == ClockMode.EXACT_SENTINEL
                && watch.starting().frame().identity().dateRaw().equals(startingDateRaw), "watch requires its exact native one-day speed-two starting frame"));
    }
    public AdvancePlan(BigInteger startingDateRaw, BigInteger targetDateRaw, int horizonDays, int speed, String policy,
            boolean exactOneDay, ClockMode clockMode, Optional<CampaignDeadline.Cap> campaignDeadline) {
        this(startingDateRaw,targetDateRaw,horizonDays,speed,policy,exactOneDay,clockMode,campaignDeadline,Optional.empty());
    }
    public List<Integer> watchArmyIds() { return dailyWatch.map(WarDailyWatch.Context::watchArmyIds).orElse(List.of()); }
    public String armStep() {
        require(clockMode != ClockMode.POLLED, "a polled plan has no native clock arm");
        List<Integer> ids = watchArmyIds();
        return ClockStatusRead.ARM_PREFIX + startingDateRaw + "-to-" + targetDateRaw + "-speed-" + speed + "-mode-terminal-a-" + ids.size()
                + (ids.isEmpty() ? "" : "-" + ids.stream().map(Object::toString).collect(java.util.stream.Collectors.joining("-")));
    }
    public List<ExpectedValue> expected() {
        return List.of(new ExpectedBoolean(new FieldKey("advance.completion_verified"), true),
                new ExpectedBoolean(new FieldKey("paused"), true),
                new ExpectedInteger(new FieldKey("advance.target_date_raw"), targetDateRaw),
                new ExpectedInteger(new FieldKey("advance.requested_horizon_days"), BigInteger.valueOf(horizonDays)),
                new ExpectedInteger(new FieldKey("advance.timeline_speed"), BigInteger.valueOf(speed)));
    }
    public Obj json() {
        var fields = new LinkedHashMap<String, Value>();
        fields.put("schema", new Text(SCHEMA)); fields.put("starting_date_raw", new IntegerValue(startingDateRaw));
        fields.put("target_date_raw", new IntegerValue(targetDateRaw)); fields.put("horizon_days", new IntegerValue(BigInteger.valueOf(horizonDays)));
        fields.put("speed", new IntegerValue(BigInteger.valueOf(speed))); fields.put("policy", new Text(policy));
        fields.put("exact_one_day", new Bool(exactOneDay)); fields.put("clock_mode", new Text(clockMode.name()));
        fields.put("campaign_deadline", campaignDeadline.<Value>map(AdvancePlan::capJson).orElse(Nil.INSTANCE));
        fields.put("war_daily_watch",dailyWatch.<Value>map(WarDailyWatch::encode).orElse(Nil.INSTANCE));
        return new Obj(fields);
    }
    public static AdvancePlan decode(ActionCommand command) { return decode(object(command.arguments().get(KEY), KEY)); }
    public static AdvancePlan decode(Obj row) {
        boolean legacy = new Text(LEGACY_SCHEMA).equals(row.get("schema"));
        var fields = new java.util.HashSet<>(Set.of("schema", "starting_date_raw", "target_date_raw", "horizon_days", "speed", "policy", "exact_one_day", "clock_mode", "campaign_deadline"));
        if (!legacy) fields.add("war_daily_watch");
        require(row.members().keySet().equals(fields), "advance plan fields differ");
        require(legacy || SCHEMA.equals(text(row.get("schema"), "schema")), "unsupported advance plan version");
        Value cap = row.get("campaign_deadline");
        return new AdvancePlan(integer(row.get("starting_date_raw"), "starting_date_raw"), integer(row.get("target_date_raw"), "target_date_raw"),
                integer(row.get("horizon_days"), "horizon_days").intValueExact(), integer(row.get("speed"), "speed").intValueExact(),
                text(row.get("policy"), "policy"), bool(row.get("exact_one_day"), "exact_one_day"),
                ClockMode.valueOf(text(row.get("clock_mode"), "clock_mode")), cap == Nil.INSTANCE ? Optional.empty() : Optional.of(capDecode(object(cap, "campaign_deadline"))),
                legacy || row.get("war_daily_watch") == Nil.INSTANCE ? Optional.empty() : Optional.of(WarDailyWatch.decode(object(row.get("war_daily_watch"),"war_daily_watch"))));
    }
    public static Obj capJson(CampaignDeadline.Cap cap) {
        return new Obj(java.util.Map.of("campaign_id", new Text(cap.campaignId()), "calendar_profile", new Text(cap.calendarProfile()),
                "starting_date_raw", new IntegerValue(cap.startingDateRaw()), "requested_target_date_raw", new IntegerValue(cap.requestedTargetDateRaw()),
                "boundary_date_raw", new IntegerValue(cap.boundaryDateRaw()), "endpoint_date_raw", new IntegerValue(cap.endpointDateRaw()),
                "target_date_raw", new IntegerValue(cap.targetDateRaw()), "status", new Text(cap.status().wire())));
    }
    public static CampaignDeadline.Cap capDecode(Obj row) {
        require(row.members().keySet().equals(Set.of("campaign_id", "calendar_profile", "starting_date_raw", "requested_target_date_raw",
                "boundary_date_raw", "endpoint_date_raw", "target_date_raw", "status")), "campaign cap fields differ");
        CampaignDeadline.Status status = switch(text(row.get("status"), "status")) {
            case "advance" -> CampaignDeadline.Status.ADVANCE; case "endpoint_reached" -> CampaignDeadline.Status.ENDPOINT_REACHED;
            case "endpoint_overshot" -> CampaignDeadline.Status.ENDPOINT_OVERSHOT; default -> throw new IllegalArgumentException("unknown campaign status");
        };
        return new CampaignDeadline.Cap(text(row.get("campaign_id"), "campaign_id"), text(row.get("calendar_profile"), "calendar_profile"),
                integer(row.get("starting_date_raw"), "starting_date_raw"), integer(row.get("requested_target_date_raw"), "requested_target_date_raw"),
                integer(row.get("boundary_date_raw"), "boundary_date_raw"), integer(row.get("endpoint_date_raw"), "endpoint_date_raw"),
                integer(row.get("target_date_raw"), "target_date_raw"), status);
    }
}
