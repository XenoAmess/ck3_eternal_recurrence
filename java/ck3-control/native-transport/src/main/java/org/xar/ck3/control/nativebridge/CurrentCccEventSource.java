package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete ordinary-event census DATA. No ordinal, generic event or old LYD permission is granted. */
public record CurrentCccEventSource(CurrentLydSource.Events eventCensus,
        Optional<Integer> fixedInstanceId, boolean caseBound, boolean selectDAdmissible, boolean selectFAdmissible, boolean sampledTwice) {
    public CurrentCccEventSource {
        Objects.requireNonNull(eventCensus); Objects.requireNonNull(fixedInstanceId);
        StrictJson.require(sampledTwice, "Complete CCC event query requires actual double sampling");
        for (var row : eventCensus.events()) {
            requireKey(row.definitionKey()); requireText(row.opening()); requireText(row.description());
            for (var option : row.options()) {
                requireText(option.text()); requireText(option.disabledReason());
                option.sourceBoundOptionKey().ifPresent(CurrentCccEventSource::requireKey);
            }
        }
        if (fixedInstanceId.isPresent()) {
            StrictJson.require(fixedInstanceId.orElseThrow()>0&&eventCensus.namedRootCount()==1&&eventCensus.events().size()==1,"Fixed instance requires unique complete event census");
            var row=eventCensus.events().get(0);
            StrictJson.require(row.instanceId()==fixedInstanceId.orElseThrow()&&row.definitionKey().equals(CurrentCccEvent.DEFINITION_KEY)&&row.authoredOptionCount()==6
                    &&row.namedRootBound()&&row.windowVisible()&&row.windowEnabled(),"Fixed CCC source is actual xccc.1001 authored6, not a filtered ordinal");
        }
        if(selectDAdmissible||selectFAdmissible){
            StrictJson.require(caseBound&&fixedInstanceId.isPresent(),"Admissibility requires independent native CCC case proof and original instance");
            var options=eventCensus.events().get(0).options();
            if(selectDAdmissible)StrictJson.require(options.stream().anyMatch(o->o.authoredOptionIndex()==3&&o.nativeCanSelect()&&!o.text().isEmpty()),"Tier-four uses real authored3 Can/text; material rows may hide it");
            if(selectFAdmissible)StrictJson.require(options.stream().anyMatch(o->o.authoredOptionIndex()==4&&o.nativeCanSelect()&&!o.text().isEmpty()),"Temporary cancel uses real authored4 Can/text");
        }
    }

    private static void requireKey(String text) {
        StrictJson.require(text.length() >= 1 && text.length() <= 256 && text.matches("[A-Za-z0-9_.-]+"),
                "Actual CCC event cached key must match the native ASCII key shape");
    }
    private static void requireText(String text) {
        StrictJson.require(text.indexOf(0) < 0, "Existing ordinary-event cached text forbids embedded NUL");
        for (int offset = 0; offset < text.length();) {
            char c = text.charAt(offset++);
            if (Character.isHighSurrogate(c)) {
                StrictJson.require(offset < text.length() && Character.isLowSurrogate(text.charAt(offset)),
                        "Actual cached text cannot contain an unpaired high surrogate"); ++offset;
            } else StrictJson.require(!Character.isLowSurrogate(c), "Actual cached text cannot contain an unpaired low surrogate");
        }
        // The reused Events DATA constructor already applies the full 16384 UTF8-byte bound.
    }

    public static CurrentCccEventSource decode(JsonNode node) throws IOException {
        try {
            var r = StrictJson.object(node, Set.of("schema", "event_census", "fixed_instance_id", "case_bound", "select_d_admissible", "select_f_admissible", "sampled_twice"));
            CurrentCccEvent.identity(r, "schema", CurrentCccEvent.SOURCE_SCHEMA);
            return new CurrentCccEventSource(CurrentLydSource.Events.decode(r.get("event_census")),
                    r.get("fixed_instance_id").isNull() ? Optional.empty() : Optional.of(CurrentCccEvent.i32(r.get("fixed_instance_id"))),
                    CurrentCccEvent.bool(r, "case_bound"), CurrentCccEvent.bool(r, "select_d_admissible"), CurrentCccEvent.bool(r, "select_f_admissible"), CurrentCccEvent.bool(r, "sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid CCC event complete source DATA", invalid);
        }
    }

    public ObjectNode encode() {
        var r = StrictJson.object().put("schema", CurrentCccEvent.SOURCE_SCHEMA);
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
        return r.put("case_bound",caseBound).put("select_d_admissible",selectDAdmissible).put("select_f_admissible",selectFAdmissible).put("sampled_twice", sampledTwice);
    }
}
