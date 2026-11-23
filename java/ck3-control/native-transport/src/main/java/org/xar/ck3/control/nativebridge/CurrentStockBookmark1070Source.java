package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete ordinary-event census DATA. No ordinal, generic event or old LYD permission is granted. */
public record CurrentStockBookmark1070Source(CurrentLydSource.Events eventCensus,
        Optional<Integer> fixedInstanceId, boolean selectCAdmissible, boolean sampledTwice) {
    public CurrentStockBookmark1070Source {
        Objects.requireNonNull(eventCensus); Objects.requireNonNull(fixedInstanceId);
        StrictJson.require(sampledTwice, "Complete bookmark query requires actual double sampling");
        for (var row : eventCensus.events()) {
            requireKey(row.definitionKey()); requireText(row.opening()); requireText(row.description());
            for (var option : row.options()) {
                requireText(option.text()); requireText(option.disabledReason());
                option.sourceBoundOptionKey().ifPresent(CurrentStockBookmark1070Source::requireKey);
            }
        }
        if (fixedInstanceId.isPresent()) {
            StrictJson.require(fixedInstanceId.orElseThrow() > 0 && eventCensus.namedRootCount() == 1
                    && eventCensus.events().size() == 1, "Fixed instance requires the complete unique census");
            var row = eventCensus.events().get(0);
            StrictJson.require(row.instanceId() == fixedInstanceId.orElseThrow()
                    && row.definitionKey().equals(CurrentStockBookmark1070.DEFINITION_KEY)
                    && row.authoredOptionCount() == 3 && row.options().size() == 3
                    && row.namedRootBound() && row.windowVisible() && row.windowEnabled()
                    && Set.copyOf(row.options().stream().map(CurrentLydSource.EventOption::authoredOptionIndex).toList()).equals(Set.of(0, 1, 2)),
                    "Fixed instance lacks the actual bound authored three-option model");
        }
        if (selectCAdmissible) {
            StrictJson.require(fixedInstanceId.isPresent(), "Admissible C requires the fixed original instance");
            StrictJson.require(eventCensus.events().get(0).options().stream().anyMatch(o -> o.authoredOptionIndex() == 2
                    && o.nativeCanSelect() && !o.text().isEmpty()), "Admissible C requires actual authored C NativeCan and text");
        }
    }

    private static void requireKey(String text) {
        StrictJson.require(text.length() >= 1 && text.length() <= 256 && text.matches("[A-Za-z0-9_.]+"),
                "Actual fixed bookmark cached key must match the native ASCII key shape");
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

    public static CurrentStockBookmark1070Source decode(JsonNode node) throws IOException {
        try {
            var r = StrictJson.object(node, Set.of("schema", "event_census", "fixed_instance_id", "select_c_admissible", "sampled_twice"));
            CurrentStockBookmark1070.identity(r, "schema", CurrentStockBookmark1070.SOURCE_SCHEMA);
            return new CurrentStockBookmark1070Source(CurrentLydSource.Events.decode(r.get("event_census")),
                    r.get("fixed_instance_id").isNull() ? Optional.empty() : Optional.of(CurrentStockBookmark1070.i32(r.get("fixed_instance_id"))),
                    CurrentStockBookmark1070.bool(r, "select_c_admissible"), CurrentStockBookmark1070.bool(r, "sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid fixed bookmark complete source DATA", invalid);
        }
    }

    public ObjectNode encode() {
        var r = StrictJson.object().put("schema", CurrentStockBookmark1070.SOURCE_SCHEMA);
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
        return r.put("select_c_admissible", selectCAdmissible).put("sampled_twice", sampledTwice);
    }
}
