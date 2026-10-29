package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnostics;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCapture;

/** Offline projection of matching original packets. No I/O, callback invocation, or action/read permission. */
public final class EventOptionLocatorDiagnostics {
    public static final String KIND = "event-option-locator-v1";
    private static final BigInteger U64 = StrictJson.UINT64_MAX;
    private EventOptionLocatorDiagnostics() { }

    /** Canonical wire string is retained; these bits do not establish a live pointer or object type. */
    public record UInt64(String decimal) {
        public UInt64 {
            Objects.requireNonNull(decimal);
            need(decimal.length() <= 20 && decimal.matches("0|[1-9][0-9]*"), "canonical uint64 decimal string required");
            need(new BigInteger(decimal).compareTo(U64) <= 0, "uint64 outside range");
        }
        public BigInteger value() { return new BigInteger(decimal); }
    }
    public record Occurrence(String requestId, long pid, UInt64 connectionGeneration, UInt64 querySequence,
            UInt64 mailboxTicketSequence, UInt64 applicationPumpEpoch, UInt64 threadId, BigInteger nativeRevision) {
        public Occurrence {
            StrictJson.text(requestId); need(pid > 0 && pid <= 0xffff_ffffL, "uint32 PID required");
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(querySequence);
            Objects.requireNonNull(mailboxTicketSequence); Objects.requireNonNull(applicationPumpEpoch);
            Objects.requireNonNull(threadId); Objects.requireNonNull(nativeRevision);
        }
    }
    public record Module(UInt64 base, Optional<UInt64> size) {
        public Module { Objects.requireNonNull(base); Objects.requireNonNull(size); }
        /** No mapped extent means no module-membership or RVA claim. */
        public Optional<BigInteger> rva(UInt64 address) {
            Objects.requireNonNull(address);
            if (size.isEmpty() || address.value().compareTo(base.value()) < 0) return Optional.empty();
            BigInteger relative = address.value().subtract(base.value());
            return relative.compareTo(size.orElseThrow().value()) < 0 ? Optional.of(relative) : Optional.empty();
        }
    }
    public record Receiver(UInt64 address, UInt64 vptr, Optional<UInt64> slot58,
            Optional<UInt64> slot60, Optional<UInt64> slotC8, Optional<String> unavailableReason) {
        public Receiver {
            Objects.requireNonNull(address); Objects.requireNonNull(vptr); Objects.requireNonNull(slot58);
            Objects.requireNonNull(slot60); Objects.requireNonNull(slotC8); Objects.requireNonNull(unavailableReason);
            if (vptr.value().signum() == 0) {
                need(slot58.isEmpty() && slot60.isEmpty() && slotC8.isEmpty()
                        && unavailableReason.filter("null_vptr"::equals).isPresent(), "observed zero vptr has unread slots");
            } else need(slot58.isPresent() && slot60.isPresent() && slotC8.isPresent()
                    && unavailableReason.isEmpty(), "nonzero vptr requires its copied slots");
        }
    }
    public record Row(int renderedIndex, int nativeOptionIndex, UInt64 authoredVectorSlot,
            UInt64 authoredOption, Receiver receiver80, Receiver receiver150) {
        public Row {
            need(renderedIndex >= 0 && nativeOptionIndex >= 0, "nonnegative option indices required");
            Objects.requireNonNull(authoredVectorSlot); Objects.requireNonNull(authoredOption);
            Objects.requireNonNull(receiver80); Objects.requireNonNull(receiver150);
            need(checkedAdd(authoredOption, 0x80).equals(receiver80.address())
                    && checkedAdd(authoredOption, 0x150).equals(receiver150.address()), "inline receiver address differs");
        }
    }
    public sealed interface Result permits Data, Unavailable { }
    /** Historical query occurrence DATA, never an enabled result, live frame, or typed-callable grant. */
    public record Data(Occurrence occurrence, Module module, List<Row> rows,
            RawJson originalNotice, RawJson originalResult) implements Result {
        public Data {
            Objects.requireNonNull(occurrence); Objects.requireNonNull(module); rows = List.copyOf(rows);
            Objects.requireNonNull(originalNotice); Objects.requireNonNull(originalResult);
        }
    }
    public enum Reason { NO_MATCHING_NOTICE, INVALID_DIAGNOSTIC, NATIVE_UNAVAILABLE, EVENT_CONTEXT_UNAVAILABLE }
    public record Unavailable(Reason reason, String detail) implements Result {
        public Unavailable { Objects.requireNonNull(reason); StrictJson.text(detail); }
    }

    /** Consumes existing originals only. A missing/overwritten latest notice never affects the ordinary event read. */
    public static Result project(BridgeDiagnostics.Received received, PlanningReadReceipt receipt) {
        Objects.requireNonNull(received); Objects.requireNonNull(receipt);
        var retained = received.original().latestSnapshotDiagnostic();
        if (retained.isEmpty()) return new Unavailable(Reason.NO_MATCHING_NOTICE, "matching original event diagnostic absent");
        try {
            need(received.equals(BridgeDiagnosticsCapture.capture(received.pipeName(), received.original(),
                    received.retainedSnapshot())), "diagnostic projection differs from original received packets");
            var actual = retained.orElseThrow().original();
            var rebuilt = NativeWire.decode(actual.packet().value());
            need(rebuilt instanceof NativeWire.Notice, "original Notice required");
            var notice = (NativeWire.Notice) rebuilt;
            need(notice.kind() == NativeWire.NoticeKind.SNAPSHOT_PUBLISH_DIAGNOSTIC
                    && java.util.Arrays.equals(actual.payload().value(), notice.payload().value()), "notice role/payload differs");
            ObjectNode envelope = parse(new RawJson(notice.payload().value()));
            if (!text(envelope, "request_id").equals(receipt.requestId())
                    || !envelope.has("diagnostic_kind") || !KIND.equals(text(envelope, "diagnostic_kind")))
                return new Unavailable(Reason.NO_MATCHING_NOTICE, "latest original diagnostic belongs to another query or kind");
            exact(envelope, "protocol_version type request_id phase status revision payload_bytes diagnostic_kind detail");
            integer(envelope, "protocol_version", 1, 1); eq(envelope, "type", "snapshot_publish_diagnostic");
            eq(envelope, "phase", "end");
            need(receipt.contractId().equals("native/event-window-v1")
                    && receipt.request().operation().value().equals(EventWindowRead.STEP), "event read receipt required");
            var session = received.session().orElseThrow(() -> new IllegalArgumentException("original transport session absent"));
            var before = receipt.request().before();
            need(session.game().equals(before.game()) && session.machineId().equals(before.machineId())
                    && session.sessionId().equals(receipt.request().sessionId())
                    && session.connectionGeneration().equals(receipt.before().binding().connectionGeneration()), "diagnostic receipt session differs");
            var hello = received.original().originalHello().orElseThrow().original();
            var build = EventWindowRead.connectedBuild(hello.packet().value(), session.game().pid(), session.connectionGeneration());
            var binding = new EventWindowModels.Binding(build, before.frame().identity().nativeRevision(),
                    before.frame().identity().dateRaw().intValueExact(), EventWindowRead.activeEvent(receipt.request()));
            ObjectNode result = EventWindowRead.originalResult(receipt.original(), receipt.requestId(), binding);
            exact(result, "step accepted status query_sequence snapshot_revision current_event_window_context backend_id");
            eq(result, "step", EventWindowRead.STEP); yes(result, "accepted"); eq(result, "backend_id", "native-headless");
            need(number(result, "snapshot_revision", BigInteger.ONE, U64).equals(binding.nativeRevision()), "event native revision differs");
            BigInteger sequence = number(result, "query_sequence", BigInteger.ONE, U64);
            need(number(envelope, "revision", BigInteger.ONE, U64).equals(binding.nativeRevision()), "diagnostic native revision differs");
            number(envelope, "payload_bytes", BigInteger.ZERO, U64);
            JsonNode detail = field(envelope, "detail");
            exact(detail, "schema_version pid connection_generation query_sequence mailbox_ticket_sequence application_pump_epoch thread_id module_base module_size frame_identity snapshot_identity unavailable_reason rows");
            integer(detail, "schema_version", 1, 1); nil(detail, "frame_identity"); nil(detail, "snapshot_identity");
            UInt64 generation = u64(detail, "connection_generation"), querySequence = u64(detail, "query_sequence");
            long pid = number(detail, "pid", BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact();
            need(pid == session.game().pid() && generation.value().equals(session.connectionGeneration())
                    && querySequence.value().equals(sequence), "diagnostic occurrence differs from original result/session");
            var occurrence = new Occurrence(receipt.requestId(), pid, generation, querySequence,
                    u64(detail, "mailbox_ticket_sequence"), u64(detail, "application_pump_epoch"),
                    u64(detail, "thread_id"), binding.nativeRevision());
            var module = new Module(u64(detail, "module_base"), optionalU64(detail, "module_size"));
            String status = text(envelope, "status");
            if (status.equals("unavailable")) {
                nil(detail, "rows");
                return new Unavailable(Reason.NATIVE_UNAVAILABLE, nonempty(detail, "unavailable_reason"));
            }
            need(status.equals("available"), "unknown locator diagnostic status"); nil(detail, "unavailable_reason");
            var context = EventWindowCodec.decode(EventWindowRead.raw(field(result, "current_event_window_context")), binding);
            eq(result, "status", context instanceof EventWindowModels.Available ? "available" : "unavailable");
            if (!(context instanceof EventWindowModels.Available available))
                return new Unavailable(Reason.EVENT_CONTEXT_UNAVAILABLE, "original event presentation unavailable");
            var rows = new ArrayList<Row>(); var source = array(detail, "rows", 64);
            need(source.size() == available.options().size(), "diagnostic option count differs");
            BigInteger vectorBase = null;
            for (JsonNode item : source) {
                exact(item, "rendered_index native_option_index authored_vector_slot authored_option receiver80 receiver150");
                int rendered = integer(item, "rendered_index", 0, Integer.MAX_VALUE);
                int nativeIndex = integer(item, "native_option_index", 0, Integer.MAX_VALUE);
                var option = available.options().get(rows.size());
                need(rendered == option.renderedIndex() && nativeIndex == option.nativeOptionIndex(), "diagnostic option identity differs");
                var row = new Row(rendered, nativeIndex, u64(item, "authored_vector_slot"), u64(item, "authored_option"),
                        receiver(field(item, "receiver80")), receiver(field(item, "receiver150")));
                BigInteger base = row.authoredVectorSlot().value().subtract(BigInteger.valueOf(nativeIndex).multiply(BigInteger.valueOf(8)));
                need(base.signum() >= 0 && (vectorBase == null || vectorBase.equals(base)), "authored vector slot stride differs");
                vectorBase = base; rows.add(row);
            }
            return new Data(occurrence, module, rows, new RawJson(notice.payload().value()),
                    receipt.original().originalResultToken().orElseThrow());
        } catch (IOException | IllegalArgumentException | ArithmeticException | java.util.NoSuchElementException invalid) {
            return new Unavailable(Reason.INVALID_DIAGNOSTIC, "invalid matching locator: " + invalid.getMessage());
        }
    }
    private static Receiver receiver(JsonNode row) {
        exact(row, "address vptr slot58 slot60 slotC8 unavailable_reason");
        Optional<String> reason = field(row, "unavailable_reason").isNull() ? Optional.empty() : Optional.of(nonempty(row, "unavailable_reason"));
        return new Receiver(u64(row, "address"), u64(row, "vptr"), optionalU64(row, "slot58"),
                optionalU64(row, "slot60"), optionalU64(row, "slotC8"), reason);
    }
    private static UInt64 u64(JsonNode row, String key) { return new UInt64(text(row, key)); }
    private static Optional<UInt64> optionalU64(JsonNode row, String key) {
        return field(row, key).isNull() ? Optional.empty() : Optional.of(u64(row, key));
    }
    private static UInt64 checkedAdd(UInt64 base, long delta) {
        BigInteger value = base.value().add(BigInteger.valueOf(delta));
        need(value.compareTo(U64) <= 0, "receiver address overflows uint64"); return new UInt64(value.toString());
    }
}
