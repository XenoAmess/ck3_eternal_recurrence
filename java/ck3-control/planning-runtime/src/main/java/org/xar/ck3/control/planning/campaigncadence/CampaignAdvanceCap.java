package org.xar.ck3.control.planning.campaigncadence;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure absolute target proposal. The native deadline and original writer remain required. */
public record CampaignAdvanceCap(Status status, List<Integer> missedSampleIndices,
        int endpointDateRaw, int nextSampleIndex, Integer boundaryDateRaw, Integer targetDateRaw) {
    public enum Status {
        ADVANCE("advance"), SAMPLE_DUE("sample_due"), ENDPOINT_DUE("endpoint_due"), ENDPOINT_OVERSHOT("endpoint_overshot");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public CampaignAdvanceCap {
        require(status != null && missedSampleIndices != null, "cap status and missing slots required");
        missedSampleIndices = List.copyOf(missedSampleIndices);
        int previous = -1;
        for (int index : missedSampleIndices) {
            require(index > previous && index <= 360, "missing slots must be unique increasing 0..360 indices");
            previous = index;
        }
        CampaignCalendar.rawToDate(endpointDateRaw);
        require(nextSampleIndex >= 0 && nextSampleIndex <= 360, "invalid next sample index");
        boolean endpoint = status == Status.ENDPOINT_DUE || status == Status.ENDPOINT_OVERSHOT;
        require(endpoint == (boundaryDateRaw == null), "endpoint branch has no boundary field");
        require((status == Status.ADVANCE) == (targetDateRaw != null), "only advance has a target");
        if (boundaryDateRaw != null) { CampaignCalendar.rawToDate(boundaryDateRaw); }
        if (targetDateRaw != null) {
            CampaignCalendar.rawToDate(targetDateRaw);
            require(targetDateRaw <= boundaryDateRaw && boundaryDateRaw <= endpointDateRaw,
                    "cap exceeds exact boundary or endpoint");
        }
    }

    public static CampaignAdvanceCap plan(int currentRaw, int proposedTargetRaw, String startDate,
            int nextSampleIndex, int months) {
        CampaignCalendar.rawToDate(currentRaw);
        CampaignCalendar.rawToDate(proposedTargetRaw);
        List<CampaignCalendar.Boundary> rows = CampaignCalendar.monthBoundaries(startDate, months);
        require(currentRaw >= rows.getFirst().raw() && proposedTargetRaw > currentRaw,
                "advance must move forward from campaign start");
        require(nextSampleIndex >= 0 && nextSampleIndex <= months + 1, "invalid next sample slot");
        List<Integer> missed = new ArrayList<>();
        int index = nextSampleIndex;
        while (index <= months && rows.get(index).raw() < currentRaw) { missed.add(index++); }
        int endpoint = rows.getLast().raw();
        if (currentRaw >= endpoint) {
            return new CampaignAdvanceCap(currentRaw == endpoint ? Status.ENDPOINT_DUE : Status.ENDPOINT_OVERSHOT,
                    missed, endpoint, months, null, null);
        }
        require(index <= months, "future sample slot required before endpoint");
        int boundary = rows.get(index).raw();
        return new CampaignAdvanceCap(boundary == currentRaw ? Status.SAMPLE_DUE : Status.ADVANCE,
                missed, endpoint, index, boundary, boundary == currentRaw ? null : Math.min(proposedTargetRaw, boundary));
    }

    public ObjectNode toJson() {
        ObjectNode result = StrictJson.object();
        result.put("calendar_profile", CampaignCalendar.PROFILE);
        ArrayNode missed = result.putArray("missed_sample_indices");
        missedSampleIndices.forEach(missed::add);
        result.put("endpoint_date_raw", endpointDateRaw);
        result.put("new_clock_actions", 0);
        result.put("native_deadline_still_required", true);
        result.put("status", status.wire());
        result.put("next_sample_index", nextSampleIndex);
        if (boundaryDateRaw != null) { result.put("boundary_date_raw", boundaryDateRaw); }
        if (targetDateRaw == null) { result.putNull("target_date_raw"); }
        else { result.put("target_date_raw", targetDateRaw); }
        return result;
    }
}
