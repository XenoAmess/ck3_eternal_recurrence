package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original Full111 foreground widget observations and their fixed read-only wire contract. */
public record CurrentFull111EventRenderer(Status status, boolean cleanupKnown, BigInteger providerGeneration,
        BigInteger querySequence, Optional<CoreFrame.Prefix> factsBefore,
        Optional<CurrentLetterResult.OwnerWitness> owner, Optional<Source> source,
        Optional<String> unavailableReason) {
    public static final String STEP = "query-current-ordinary-event-renderer-26785313-v1";
    public static final String CAPABILITY = "game.query.current-ordinary-event-renderer.26785313.v1";
    private static final String SCHEMA = "ck3.full111.ordinary_event_renderer_result.v1";
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;

    public enum Status {
        AVAILABLE, UNAVAILABLE, EXPIRED, STALE_SOURCE, INDETERMINATE;

        static Status decode(String wire) throws IOException {
            return switch (wire) {
                case "available" -> AVAILABLE;
                case "unavailable" -> UNAVAILABLE;
                case "expired" -> EXPIRED;
                case "stale_source" -> STALE_SOURCE;
                case "indeterminate" -> INDETERMINATE;
                default -> throw new IOException("Unknown Full111 event renderer status");
            };
        }
    }

    public record Option(int authoredOptionIndex, boolean nativeCanSelect, boolean widgetVisible,
            boolean widgetEnabled, String text, String disabledReason) {
        public Option {
            StrictJson.require(authoredOptionIndex >= 0 && authoredOptionIndex < 64, "Actual authored option index required");
            CurrentLyd.text(text);
            CurrentLyd.text(disabledReason);
        }
    }

    public record Source(int instanceId, int recipientCharacterId, String definitionKey, int authoredOptionCount,
            List<Option> options) {
        public Source {
            StrictJson.require(instanceId > 0 && recipientCharacterId != -1 && authoredOptionCount > 0
                    && authoredOptionCount <= 64, "Actual Full111 foreground event identity and authored count required");
            CurrentLyd.key(definitionKey, 256);
            options = List.copyOf(options);
            StrictJson.require(!options.isEmpty() && options.size() <= 64, "Nonempty observed stock widget order required");
            var authored = new HashSet<Integer>();
            for (var option : options) {
                int index = option.authoredOptionIndex();
                StrictJson.require(index < authoredOptionCount && authored.add(index),
                        "Full111 renderer option index repeated or outside authored range");
            }
        }
    }

    public CurrentFull111EventRenderer {
        Objects.requireNonNull(status);
        CurrentLetter.unsigned(providerGeneration, false);
        CurrentLetter.unsigned(querySequence, false);
        Objects.requireNonNull(factsBefore);
        Objects.requireNonNull(owner);
        Objects.requireNonNull(source);
        Objects.requireNonNull(unavailableReason);
        StrictJson.require(factsBefore.isPresent() == owner.isPresent(), "Actual Core and renderer owner must agree");
        factsBefore.ifPresent(CurrentLetter::requirePrefix);
        boolean available = status == Status.AVAILABLE;
        StrictJson.require(available == source.isPresent(), "Renderer status differs from its exact source");
        if (available) {
            StrictJson.require(cleanupKnown && factsBefore.isPresent() && unavailableReason.isEmpty()
                    && providerGeneration.signum() > 0 && querySequence.signum() > 0
                    && source.orElseThrow().recipientCharacterId() == factsBefore.orElseThrow().playedCharacterId(),
                    "Available Full111 renderer lacks exact Core/owner/recipient evidence");
        } else {
            StrictJson.require(providerGeneration.signum() == 0 && querySequence.signum() == 0
                    && unavailableReason.filter(reason -> !reason.isEmpty()).isPresent(),
                    "Refused Full111 renderer must retain its actual reason without a source");
        }
    }

    public static byte[] queryPacket(String requestId, CoreFrame.Partial core, int instanceId, Instant deadline)
            throws IOException {
        StrictJson.require(core.build() == BUILD && instanceId > 0, "Exact Full111 Core and observed foreground ID required");
        var base = CurrentLyd.request(core, CurrentLyd.Action.QUERY_EVENTS, BigInteger.ZERO, BigInteger.ZERO, CurrentLyd.Target.none());
        var fields = NativeWire.object(NativeWire.parse(base.additionalFields().bytes()));
        NativeWire.object(fields.get("lyd")).put("instance_id", instanceId);
        long deadlineMs = deadline.toEpochMilli();
        StrictJson.require(deadlineMs > 0, "A positive renderer request deadline is required");
        fields.put("core_control_deadline_unix_ms", deadlineMs);
        return NativeWire.execute(requestId, STEP, BigInteger.ZERO, StrictJson.canonical(fields));
    }

    public static CurrentFull111EventRenderer decodeOutcome(AckReceived original) throws IOException {
        try {
            var envelope = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),
                    Set.of("type", "protocol_version", "request_id", "ok", "result"));
            require(envelope, "type", "command_result");
            require(envelope, "request_id", original.requestId());
            NativeWire.integer(envelope.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            var resultToken = original.originalResultToken().orElseThrow(() -> new IOException("Original renderer result token absent"));
            var token = NativeWire.parse(resultToken.bytes());
            if (!token.equals(envelope.get("result")) || CurrentLyd.bool(envelope, "ok") != original.nativeOk())
                throw new IOException("Original renderer result token or status differs from its ACK envelope");
            var result = decode(token);
            if ((result.status() == Status.AVAILABLE) != original.nativeOk())
                throw new IOException("Original renderer availability differs from its ACK status");
            return result;
        } catch (IllegalArgumentException | ArithmeticException malformed) {
            throw new IOException("Invalid Full111 renderer result", malformed);
        }
    }

    private static CurrentFull111EventRenderer decode(JsonNode node) throws IOException {
        var r = StrictJson.object(node, Set.of("schema", "game_version", "executable_sha256", "backend", "adapter_id",
                "action", "status", "source_available", "cleanup_known", "provider_generation", "query_sequence",
                "facts_before", "owner", "source", "addresses_redacted", "unavailable_reason"));
        require(r, "schema", SCHEMA);
        require(r, "action", CurrentLyd.Action.QUERY_EVENTS.wire());
        require(r, "backend", CurrentLyd.BACKEND);
        require(r, "adapter_id", BUILD.coreFrameAdapterId());
        if (!BUILD.matches(NativeWire.text(r.get("game_version")), NativeWire.text(r.get("executable_sha256")))
                || !CurrentLyd.bool(r, "addresses_redacted"))
            throw new IOException("Exact Full111 renderer build and redacted owner data required");

        var facts = r.get("facts_before").isNull() ? Optional.<CoreFrame.Prefix>empty()
                : Optional.of(CurrentLyd.readCore(r.get("facts_before")));
        var owner = r.get("owner").isNull() ? Optional.<CurrentLetterResult.OwnerWitness>empty()
                : Optional.of(owner(r.get("owner")));
        var source = r.get("source").isNull() ? Optional.<Source>empty() : Optional.of(source(r.get("source")));
        if (CurrentLyd.bool(r, "source_available") != source.isPresent())
            throw new IOException("Renderer availability/null source mismatch");
        return new CurrentFull111EventRenderer(Status.decode(NativeWire.text(r.get("status"))),
                CurrentLyd.bool(r, "cleanup_known"), CurrentLyd.decimal(r, "provider_generation"),
                CurrentLyd.decimal(r, "query_sequence"), facts, owner, source,
                CurrentLyd.nativeTextOptional(r.get("unavailable_reason")));
    }

    private static CurrentLetterResult.OwnerWitness owner(JsonNode node) throws IOException {
        var owner = StrictJson.object(node, Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
        return new CurrentLetterResult.OwnerWitness(CurrentLyd.decimal(owner, "connection_generation"),
                CurrentLyd.decimal(owner, "ticket_sequence"), CurrentLyd.decimal(owner, "pump_epoch"),
                NativeWire.integer(owner.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact());
    }

    private static Source source(JsonNode node) throws IOException {
        var source = StrictJson.object(node, Set.of("instance_id", "recipient_character_id", "definition_key",
                "authored_option_count", "options"));
        var rows = source.get("options");
        if (!rows.isArray() || rows.isEmpty() || rows.size() > 64)
            throw new IOException("Finite materialized Full111 renderer rows required");
        List<Option> options = new ArrayList<>(rows.size());
        for (var row : rows) {
            var option = StrictJson.object(row, Set.of("authored_option_index", "native_can_select", "widget_visible",
                    "widget_enabled", "text", "disabled_reason"));
            options.add(new Option(CurrentLyd.i32(option.get("authored_option_index")),
                    CurrentLyd.bool(option, "native_can_select"), CurrentLyd.bool(option, "widget_visible"),
                    CurrentLyd.bool(option, "widget_enabled"), CurrentLyd.nativeText(option.get("text")),
                    CurrentLyd.nativeText(option.get("disabled_reason"))));
        }
        return new Source(CurrentLyd.i32(source.get("instance_id")), CurrentLyd.i32(source.get("recipient_character_id")),
                NativeWire.text(source.get("definition_key")), CurrentLyd.i32(source.get("authored_option_count")), options);
    }

    private static void require(ObjectNode object, String key, String expected) throws IOException {
        if (!expected.equals(NativeWire.text(object.get(key)))) throw new IOException("Full111 renderer " + key + " differs");
    }
}
