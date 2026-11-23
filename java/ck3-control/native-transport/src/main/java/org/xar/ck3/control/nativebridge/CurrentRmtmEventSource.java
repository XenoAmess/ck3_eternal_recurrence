package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete ordinary-event census DATA. No ordinal, generic event or old LYD permission is granted. */
public record CurrentRmtmEventSource(CurrentLydSource.Events eventCensus,
        Optional<Integer> fixedInstanceId, boolean caseBound, boolean ackAdmissible, boolean sampledTwice) {
    public CurrentRmtmEventSource {
        Objects.requireNonNull(eventCensus); Objects.requireNonNull(fixedInstanceId);
        StrictJson.require(sampledTwice&&eventCensus.censusComplete(), "Complete RMTM event query requires actual double sampling");
        for (var row : eventCensus.events()) {
            requireKey(row.definitionKey()); requireText(row.opening()); requireText(row.description());
            for (var option : row.options()) {
                requireText(option.text()); requireText(option.disabledReason());
                option.sourceBoundOptionKey().ifPresent(CurrentRmtmEventSource::requireKey);
            }
        }
        if(fixedInstanceId.isPresent()){
            StrictJson.require(fixedInstanceId.orElseThrow()>0&&eventCensus.namedRootCount()==1&&eventCensus.events().size()==1
                    &&eventCensus.events().get(0).instanceId()==fixedInstanceId.orElseThrow(),"Fixed instance requires complete unique original census");
        }
        if(ackAdmissible){
            StrictJson.require(caseBound&&fixedInstanceId.isPresent(),"Actual own RMTM case and original instance required");
            var row=eventCensus.events().get(0);
            StrictJson.require((row.definitionKey().equals(CurrentRmtmEvent.SUMMARY_DEFINITION)||row.definitionKey().equals(CurrentRmtmEvent.CHAOS_DEFINITION))
                    &&row.authoredOptionCount()==1&&row.namedRootBound()&&row.windowVisible()&&row.windowEnabled()&&row.options().size()==1,
                    "Only actual single-option summary or Chaos source is admissible");
            var option=row.options().get(0);StrictJson.require(option.authoredOptionIndex()==0&&option.nativeCanSelect()&&!option.text().isEmpty(),"Actual authored0 nativeCan/nonempty text required");
        }
    }

    private static void requireKey(String text) {
        StrictJson.require(text.length() >= 1 && text.length() <= 256 && text.matches("[A-Za-z0-9_.:-]+"),
                "Actual RMTM event cached key must match the native ASCII key shape");
    }
    private static void requireText(String text) {
        for (int offset = 0; offset < text.length();) {
            char c = text.charAt(offset++);
            if (Character.isHighSurrogate(c)) {
                StrictJson.require(offset < text.length() && Character.isLowSurrogate(text.charAt(offset)),
                        "Actual cached text cannot contain an unpaired high surrogate"); ++offset;
            } else StrictJson.require(!Character.isLowSurrogate(c), "Actual cached text cannot contain an unpaired low surrogate");
        }
        // Read DATA retains NUL/controls/richtext. Existing Events applies the full16384 UTF8-byte bound.
    }

    public static CurrentRmtmEventSource decode(JsonNode node) throws IOException {
        try {
            var r = StrictJson.object(node, Set.of("schema", "event_census", "fixed_instance_id", "case_bound", "ack_admissible", "sampled_twice"));
            CurrentRmtmEvent.identity(r, "schema", CurrentRmtmEvent.SOURCE_SCHEMA);
            return new CurrentRmtmEventSource(CurrentLydSource.Events.decode(r.get("event_census")),
                    r.get("fixed_instance_id").isNull() ? Optional.empty() : Optional.of(CurrentRmtmEvent.i32(r.get("fixed_instance_id"))),
                    CurrentRmtmEvent.bool(r, "case_bound"), CurrentRmtmEvent.bool(r, "ack_admissible"), CurrentRmtmEvent.bool(r, "sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid RMTM event complete source DATA", invalid);
        }
    }

    public ObjectNode encode() {
        var r = StrictJson.object().put("schema", CurrentRmtmEvent.SOURCE_SCHEMA);
        var census = r.putObject("event_census").put("census_complete", eventCensus.censusComplete()).put("named_root_count", eventCensus.namedRootCount());
        var rows = census.putArray("events");
        for (var row : eventCensus.events()) {
            var e = rows.addObject().put("instance_id", row.instanceId()).put("recipient_character_id", row.recipientCharacterId())
                    .put("authored_option_count", row.authoredOptionCount()).put("definition_key", row.definitionKey())
                    .put("opening", row.opening()).put("description", row.description()).put("named_root_bound", row.namedRootBound())
                    .put("window_visible", row.windowVisible()).put("window_enabled", row.windowEnabled());
            var options = e.putArray("options");
            for (var option : row.options()) {
                var o = options.addObject().put("authored_option_index", option.authoredOptionIndex()).put("native_can_select", option.nativeCanSelect())
                        .put("text", option.text()).put("disabled_reason", option.disabledReason());
                if (option.sourceBoundOptionKey().isPresent()) o.put("source_bound_option_key", option.sourceBoundOptionKey().orElseThrow()); else o.putNull("source_bound_option_key");
                if (option.permittedRole().isPresent()) o.put("permitted_role", option.permittedRole().orElseThrow().wire()); else o.putNull("permitted_role");
            }
        }
        if (fixedInstanceId.isPresent()) r.put("fixed_instance_id", fixedInstanceId.orElseThrow()); else r.putNull("fixed_instance_id");
        return r.put("case_bound",caseBound).put("ack_admissible",ackAdmissible).put("sampled_twice", sampledTwice);
    }
}
