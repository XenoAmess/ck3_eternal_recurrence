package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionState.Attempt;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Versioned Full111 event option DATA. Only the canonical submission permit can carry the private write. */
public final class CurrentFull111EventOption {
    public static final String REQUEST_SCHEMA = "ck3.full111.ordinary_event_option_request.v2";
    public static final String RESULT_SCHEMA = "ck3.full111.ordinary_event_option_result.v2";
    public static final Duration RENDERER_RENEWAL_WINDOW = Duration.ofSeconds(8);
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Set<String> TARGET_FIELDS = Set.of("instance_id", "recipient_character_id",
            "definition_key", "authored_option_index");
    private static final Set<String> LINEAGE_FIELDS = Set.of("source_revision", "renderer_request_id",
            "renderer_provider_generation", "renderer_query_sequence", "prepare_request_id", "lease_sequence",
            "effect_request_id", "claim_sequence");

    private CurrentFull111EventOption() { }

    public enum Action {
        PREPARE("prepare", "prepare-current-ordinary-event-option-26785313-v2",
                "game.query.prepare-current-ordinary-event-option.26785313.v2"),
        SELECT("select", "select-current-ordinary-event-option-26785313-v2",
                "game.command.select-current-ordinary-event-option.26785313.v2"),
        QUERY_QUEUE("query_queue", "query-current-ordinary-event-queue-26785313-v2",
                "game.query.current-ordinary-event-queue.26785313.v2");

        private final String wire;
        private final String step;
        private final String capability;

        Action(String wire, String step, String capability) {
            this.wire = wire;
            this.step = step;
            this.capability = capability;
        }
        public String step() { return step; }
        public String capability() { return capability; }
        public boolean readOnly() { return this != SELECT; }

        static Action parse(String wire) throws IOException {
            for (var action : values()) if (action.wire.equals(wire)) return action;
            throw new IOException("Unknown Full111 option action");
        }
    }

    public enum Status {
        AVAILABLE, SELECTION_DISPATCHED, UNAVAILABLE, EXPIRED, STALE_SOURCE, CLAIM_CONSUMED, INDETERMINATE;

        static Status parse(String wire) throws IOException {
            return switch (wire) {
                case "available" -> AVAILABLE;
                case "selection_dispatched" -> SELECTION_DISPATCHED;
                case "unavailable" -> UNAVAILABLE;
                case "expired" -> EXPIRED;
                case "stale_source" -> STALE_SOURCE;
                case "claim_consumed" -> CLAIM_CONSUMED;
                case "indeterminate" -> INDETERMINATE;
                default -> throw new IOException("Unknown Full111 option status");
            };
        }
    }

    public record Target(int instanceId, int recipientCharacterId, String definitionKey, int authoredOptionIndex) {
        public Target {
            StrictJson.require(instanceId > 0 && recipientCharacterId != -1
                    && authoredOptionIndex >= 0 && authoredOptionIndex < 64,
                    "Exact Full111 event/recipient/authored option required");
            CurrentLyd.key(definitionKey, 192);
        }

        /** The renderer is a read-only eligibility witness. It grants no prepare lease or command. */
        public boolean matchesSelectable(CurrentFull111EventRenderer.Source rendered) {
            return instanceId == rendered.instanceId() && recipientCharacterId == rendered.recipientCharacterId()
                    && definitionKey.equals(rendered.definitionKey())
                    && rendered.options().stream().anyMatch(row -> row.authoredOptionIndex() == authoredOptionIndex
                        && row.nativeCanSelect() && row.widgetVisible() && row.widgetEnabled());
        }

        private ObjectNode encode() {
            return StrictJson.object().put("instance_id", instanceId).put("recipient_character_id", recipientCharacterId)
                    .put("definition_key", definitionKey).put("authored_option_index", authoredOptionIndex);
        }

        private static Target decode(JsonNode node) throws IOException {
            var target = StrictJson.object(node, TARGET_FIELDS);
            return new Target(CurrentLyd.i32(target.get("instance_id")), CurrentLyd.i32(target.get("recipient_character_id")),
                    NativeWire.text(target.get("definition_key")), CurrentLyd.i32(target.get("authored_option_index")));
        }
    }

    /** The same planned action may use a different renderer receipt only when its complete evidence still agrees. */
    public static boolean matchesPlannedRenderer(CurrentFull111EventRenderer planned, CurrentFull111EventRenderer fresh, Target target) {
        return planned.status() == CurrentFull111EventRenderer.Status.AVAILABLE
                && fresh.status() == CurrentFull111EventRenderer.Status.AVAILABLE
                && planned.providerGeneration().equals(fresh.providerGeneration())
                && fresh.querySequence().compareTo(planned.querySequence()) > 0
                && planned.factsBefore().equals(fresh.factsBefore()) && planned.source().equals(fresh.source())
                && target.matchesSelectable(fresh.source().orElseThrow());
    }

    public record Lineage(BigInteger sourceRevision, String rendererRequestId, BigInteger rendererProviderGeneration,
            BigInteger rendererQuerySequence, Optional<String> prepareRequestId, BigInteger leaseSequence,
            Optional<String> effectRequestId, BigInteger claimSequence) {
        public Lineage {
            CurrentLetter.unsigned(sourceRevision, true);
            requestId(rendererRequestId);
            CurrentLetter.unsigned(rendererProviderGeneration, true);
            CurrentLetter.unsigned(rendererQuerySequence, true);
            Objects.requireNonNull(prepareRequestId).ifPresent(CurrentFull111EventOption::requestId);
            Objects.requireNonNull(effectRequestId).ifPresent(CurrentFull111EventOption::requestId);
            CurrentLetter.unsigned(leaseSequence, false);
            CurrentLetter.unsigned(claimSequence, false);
            StrictJson.require(prepareRequestId.isPresent() == (leaseSequence.signum() > 0)
                    && effectRequestId.isPresent() == (claimSequence.signum() > 0)
                    && (effectRequestId.isEmpty() || prepareRequestId.isPresent()),
                    "Full111 v2 prepare and effect IDs must agree with actual sequences");
            StrictJson.require(prepareRequestId.filter(rendererRequestId::equals).isEmpty()
                    && effectRequestId.filter(rendererRequestId::equals).isEmpty()
                    && effectRequestId.filter(id -> prepareRequestId.filter(id::equals).isPresent()).isEmpty(),
                    "Different Full111 v2 stages require different request identities");
        }

        private ObjectNode encode() {
            var lineage = StrictJson.object().put("source_revision", sourceRevision.toString())
                    .put("renderer_request_id", rendererRequestId)
                    .put("renderer_provider_generation", rendererProviderGeneration.toString())
                    .put("renderer_query_sequence", rendererQuerySequence.toString())
                    .put("lease_sequence", leaseSequence.toString()).put("claim_sequence", claimSequence.toString());
            CurrentLyd.putText(lineage, "prepare_request_id", prepareRequestId);
            CurrentLyd.putText(lineage, "effect_request_id", effectRequestId);
            return lineage;
        }

        private static Lineage decode(JsonNode node) throws IOException {
            var lineage = StrictJson.object(node, LINEAGE_FIELDS);
            return new Lineage(CurrentLyd.decimal(lineage, "source_revision"), NativeWire.text(lineage.get("renderer_request_id")),
                    CurrentLyd.decimal(lineage, "renderer_provider_generation"), CurrentLyd.decimal(lineage, "renderer_query_sequence"),
                    CurrentLyd.nativeTextOptional(lineage.get("prepare_request_id")), CurrentLyd.decimal(lineage, "lease_sequence"),
                    CurrentLyd.nativeTextOptional(lineage.get("effect_request_id")), CurrentLyd.decimal(lineage, "claim_sequence"));
        }

        private void requirePhase(Action action) {
            StrictJson.require(prepareRequestId.isPresent() == (action != Action.PREPARE)
                    && effectRequestId.isPresent() == (action == Action.QUERY_QUEUE),
                    "Original Full111 v2 request stage differs from its lineage");
        }
    }

    private static void requestId(String id) {
        StrictJson.require(id != null && id.matches("[A-Za-z0-9_.-]{1,96}"), "Bounded original Native request identity required");
    }

    /** Only the application transport may dispatch a request using the real Native lease and writer permit. */
    public record Request(Action action, CoreFrame.Partial core, Target target, Lineage lineage, Instant deadline) {
        public Request {
            Objects.requireNonNull(action);
            Objects.requireNonNull(core);
            Objects.requireNonNull(target);
            Objects.requireNonNull(lineage);
            Objects.requireNonNull(deadline);
            CurrentLetter.requirePrefix(core.prefix());
            StrictJson.require(core.build() == BUILD && core.prefix().playedCharacterId() == target.recipientCharacterId()
                    && deadline.toEpochMilli() > 0, "Exact Full111 Core, observed recipient and finite wire deadline required");
            lineage.requirePhase(action);
        }

        /** There is no direct write packet emitter for SELECT. */
        public byte[] readPacket(String requestId) throws IOException {
            requestId(requestId);
            StrictJson.require(action.readOnly(), "Full111 SELECT requires the canonical submission permit");
            return NativeWire.execute(requestId, action.step(), BigInteger.ZERO, fields());
        }

        public NativeRequest selectionRequest() {
            StrictJson.require(action == Action.SELECT, "Only a prepared Full111 selection is an ACTION request");
            return new NativeRequest(action.step(), action.capability(), new RawJson(fields()));
        }

        /** Strict inverse for a canonical prepared ACTION. The submitted revision remains fixed by the permit. */
        public static Request decodeSelectionRequest(NativeRequest request) throws IOException {
            if (!request.step().equals(Action.SELECT.step())
                    || !request.requiredCapability().equals(Optional.of(Action.SELECT.capability())))
                throw new IOException("Expected the fixed private Full111 option ACTION");
            return decodeFields(Action.SELECT, request.additionalFields().bytes());
        }

        /** DATA replay of the independently issued original after-ACK query. */
        public static Request decodeQueueRequest(AckReceived original) throws IOException {
            var outbound = original.outbound().orElseThrow(() -> new IOException("Original queue request absent"));
            var sent = NativeWire.decodeExecuteRequest(outbound.originalPacket());
            if (!original.requestId().equals(sent.requestId()) || !Action.QUERY_QUEUE.step().equals(sent.step())
                    || !sent.expectedRevision().equals(Optional.of(BigInteger.ZERO)))
                throw new IOException("Original request is not the fixed independent Full111 queue query");
            return decodeFields(Action.QUERY_QUEUE, sent.normalizedAdditionalFields().value());
        }

        private static Request decodeFields(Action action, byte[] original) throws IOException {
            try {
                var fields = StrictJson.object(NativeWire.parse(original),
                        Set.of("arguments", "ordinary_event", "core_control_deadline_unix_ms"));
                StrictJson.object(fields.get("arguments"), Set.of());
                var claimFields = new HashSet<>(Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                        "backend", "action", "expected_core"));
                claimFields.addAll(TARGET_FIELDS);
                claimFields.addAll(LINEAGE_FIELDS);
                var claim = StrictJson.object(fields.get("ordinary_event"), claimFields);
                require(claim, "schema", REQUEST_SCHEMA);
                require(claim, "adapter_id", BUILD.coreFrameAdapterId());
                require(claim, "backend", CurrentLyd.BACKEND);
                require(claim, "action", action.wire);
                if (!BUILD.matches(NativeWire.text(claim.get("game_version")), NativeWire.text(claim.get("executable_sha256"))))
                    throw new IOException("Exact Full111 option action build required");
                var target = StrictJson.object();
                TARGET_FIELDS.forEach(field -> target.set(field, claim.get(field)));
                var lineage = StrictJson.object();
                LINEAGE_FIELDS.forEach(field -> lineage.set(field, claim.get(field)));
                long until = NativeWire.integer(fields.get("core_control_deadline_unix_ms"), BigInteger.ONE,
                        BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();
                return new Request(action, new CoreFrame.Partial(BUILD, CurrentLyd.readCore(claim.get("expected_core"))),
                        Target.decode(target), Lineage.decode(lineage), Instant.ofEpochMilli(until));
            } catch (IllegalArgumentException | ArithmeticException malformed) {
                throw new IOException("Invalid original Full111 option request", malformed);
            }
        }

        private byte[] fields() {
            var claim = StrictJson.object().put("schema", REQUEST_SCHEMA).put("game_version", BUILD.version())
                    .put("executable_sha256", BUILD.executableSha256()).put("adapter_id", BUILD.coreFrameAdapterId())
                    .put("backend", CurrentLyd.BACKEND).put("action", action.wire);
            claim.set("expected_core", CurrentLyd.core(core.prefix()));
            claim.setAll(target.encode());
            claim.setAll(lineage.encode());
            var fields = StrictJson.object().put("core_control_deadline_unix_ms", deadline.toEpochMilli());
            fields.set("arguments", StrictJson.object());
            fields.set("ordinary_event", claim);
            return StrictJson.canonical(fields);
        }
    }

    public enum TargetState {
        PRESENT, ABSENT;

        static TargetState parse(String wire) throws IOException {
            return switch (wire) {
                case "present" -> PRESENT;
                case "absent" -> ABSENT;
                default -> throw new IOException("Unknown Full111 queue target state");
            };
        }
    }

    /** Only a complete successful census may carry instance IDs, including a stable empty result. */
    public record Queue(List<Integer> instanceIds, TargetState targetState) {
        public Queue {
            instanceIds = List.copyOf(instanceIds);
            Objects.requireNonNull(targetState);
            StrictJson.require(instanceIds.size() <= 32 && instanceIds.stream().allMatch(id -> id > 0)
                    && new HashSet<>(instanceIds).size() == instanceIds.size(), "Complete bounded event queue identities required");
        }

        private static Queue decode(JsonNode node) throws IOException {
            var queue = StrictJson.object(node, Set.of("complete", "count", "instance_ids", "target_state"));
            var ids = queue.get("instance_ids");
            int count = CurrentLyd.i32(queue.get("count"));
            if (!CurrentLyd.bool(queue, "complete") || count < 0 || count > 32 || !ids.isArray() || ids.size() != count)
                throw new IOException("Complete exact Full111 queue and count required");
            var values = new ArrayList<Integer>(count);
            for (var id : ids) values.add(CurrentLyd.i32(id));
            return new Queue(values, TargetState.parse(NativeWire.text(queue.get("target_state"))));
        }
    }

    public record Result(Action action, Status status, boolean cleanupKnown, boolean effectAttempted,
            boolean nativeReturned, Optional<CoreFrame.Prefix> factsBefore,
            Optional<CurrentLetterResult.OwnerWitness> owner, Optional<Target> target, Optional<Lineage> lineage,
            Optional<Queue> queue, Optional<String> unavailableReason) {
        public Result {
            Objects.requireNonNull(action);
            Objects.requireNonNull(status);
            Objects.requireNonNull(factsBefore);
            Objects.requireNonNull(owner);
            Objects.requireNonNull(target);
            Objects.requireNonNull(lineage);
            Objects.requireNonNull(queue);
            Objects.requireNonNull(unavailableReason);
            StrictJson.require(factsBefore.isPresent() == owner.isPresent() && target.isPresent() == lineage.isPresent(),
                    "Full111 option result contains a partial source identity");
            StrictJson.require(!nativeReturned || effectAttempted, "A Native return requires an actual effect attempt");
            StrictJson.require(!action.readOnly() || !effectAttempted, "Event option reads cannot report a mutation");
            boolean positive = status == Status.AVAILABLE || status == Status.SELECTION_DISPATCHED;
            StrictJson.require(queue.isPresent() == (positive && action == Action.QUERY_QUEUE),
                    "A complete queue belongs only to a successful independent queue read");
            if (positive) {
                StrictJson.require(cleanupKnown && owner.isPresent() && target.isPresent() && unavailableReason.isEmpty()
                        && (action.readOnly() ? status == Status.AVAILABLE
                            : status == Status.SELECTION_DISPATCHED && effectAttempted && nativeReturned),
                        "Full111 option stage does not match its available evidence");
                var exact = target.orElseThrow();
                StrictJson.require(factsBefore.orElseThrow().playedCharacterId() == exact.recipientCharacterId(),
                        "Full111 result changed its observed recipient");
                var actualLineage = lineage.orElseThrow();
                StrictJson.require(actualLineage.prepareRequestId().isPresent()
                        && actualLineage.effectRequestId().isPresent() == (action != Action.PREPARE),
                        "Full111 option result lost a required prior stage");
                queue.ifPresent(census -> StrictJson.require(census.instanceIds().contains(exact.instanceId())
                        == (census.targetState() == TargetState.PRESENT), "Queue membership differs from the reported target state"));
            } else {
                StrictJson.require(unavailableReason.filter(reason -> !reason.isEmpty()).isPresent(),
                        "An unavailable Full111 stage must retain its actual reason");
                StrictJson.require(target.isPresent() || factsBefore.isEmpty() && !effectAttempted,
                        "A rejected request cannot publish partial evidence");
            }
        }

        public boolean successful() {
            return status == Status.AVAILABLE || status == Status.SELECTION_DISPATCHED;
        }

        /** DATA comparison after decoding. This does not qualify the live owner or mint a lease. */
        public boolean matchesSuccessfulRequest(Request request) {
            if (!successful() || action != request.action() || factsBefore.filter(request.core().prefix()::equals).isEmpty()
                    || target.filter(request.target()::equals).isEmpty()) return false;
            var before = request.lineage();
            var after = lineage.orElseThrow();
            if (!before.sourceRevision().equals(after.sourceRevision())
                    || !before.rendererRequestId().equals(after.rendererRequestId())
                    || !before.rendererProviderGeneration().equals(after.rendererProviderGeneration())
                    || !before.rendererQuerySequence().equals(after.rendererQuerySequence())) return false;
            return switch (action) {
                case PREPARE -> true;
                case SELECT -> before.prepareRequestId().equals(after.prepareRequestId()) && before.leaseSequence().equals(after.leaseSequence());
                case QUERY_QUEUE -> before.equals(after);
            };
        }
    }

    public static Result decodeOutcome(AckReceived original) throws IOException {
        try {
            var envelope = StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),
                    Set.of("type", "protocol_version", "request_id", "ok", "result"));
            require(envelope, "type", "command_result");
            require(envelope, "request_id", original.requestId());
            requestId(original.requestId());
            NativeWire.integer(envelope.get("protocol_version"), BigInteger.ONE, BigInteger.ONE);
            var retained = original.originalResultToken().orElseThrow(() -> new IOException("Original Full111 option token absent"));
            var token = NativeWire.parse(retained.bytes());
            if (!token.equals(envelope.get("result")) || CurrentLyd.bool(envelope, "ok") != original.nativeOk())
                throw new IOException("Original Full111 option result differs from its ACK envelope");
            var result = decode(token);
            if (result.successful() != original.nativeOk())
                throw new IOException("Full111 option stage differs from its real ACK status");
            if (result.successful()) {
                var before = result.lineage().orElseThrow();
                switch (result.action()) {
                    case PREPARE -> requireSelf(before.prepareRequestId(), original.requestId());
                    case SELECT -> requireSelf(before.effectRequestId(), original.requestId());
                    case QUERY_QUEUE -> {
                        var id = original.requestId();
                        if (id.equals(before.rendererRequestId()) || before.prepareRequestId().filter(id::equals).isPresent()
                                || before.effectRequestId().filter(id::equals).isPresent())
                            throw new IOException("An independent queue read requires a new original request ID");
                    }
                }
            }
            return result;
        } catch (IllegalArgumentException | ArithmeticException malformed) {
            throw new IOException("Invalid exact Full111 event option result", malformed);
        }
    }

    /** The v2 quote and select repeat the original renderer's exact wire deadline. */
    public static Instant rendererDeadline(AckReceived original) throws IOException {
        var model = CurrentFull111EventRenderer.decodeOutcome(original);
        if (model.status() != CurrentFull111EventRenderer.Status.AVAILABLE)
            throw new IOException("An actual available renderer reply is required");
        var outbound = original.outbound().orElseThrow(() -> new IOException("Original renderer request absent"));
        var sent = NativeWire.decodeExecuteRequest(outbound.originalPacket());
        if (!original.requestId().equals(sent.requestId()) || !CurrentFull111EventRenderer.STEP.equals(sent.step())
                || !sent.expectedRevision().equals(Optional.of(BigInteger.ZERO)))
            throw new IOException("Original renderer request identity changed");
        var fields = NativeWire.object(NativeWire.parse(sent.normalizedAdditionalFields().value()));
        long originalMs = NativeWire.integer(fields.get("core_control_deadline_unix_ms"), BigInteger.ONE,
                BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();
        Instant deadline = Instant.ofEpochMilli(originalMs);
        var core = new CoreFrame.Partial(BUILD, model.factsBefore().orElseThrow());
        if (!java.util.Arrays.equals(outbound.originalPacket(), CurrentFull111EventRenderer.queryPacket(
                original.requestId(), core, model.source().orElseThrow().instanceId(), deadline)))
            throw new IOException("Original renderer target, Core or wire deadline differs");
        return deadline;
    }

    /** Tests only closure of the original queue instance. The Root still binds these originals to its canonical attempt and later Full. */
    public static boolean confirmsAbsence(Attempt original, AckReceived dispatched, Request queue, AckReceived observed)
            throws IOException {
        var selection = Request.decodeSelectionRequest(original.preparedRequest());
        var guard = original.guard();
        if (!(guard.origin() instanceof CommandOrigin.Gameplay gameplay)
                || !guard.operation().value().equals(Action.SELECT.step())
                || !gameplay.expectedRevision().equals(selection.lineage().sourceRevision())
                || !gameplay.before().frame().identity().player().equals(BigInteger.valueOf(selection.target().recipientCharacterId()))
                || !gameplay.before().frame().identity().dateRaw().equals(BigInteger.valueOf(selection.core().prefix().dateRaw()))
                || !original.requestId().equals(dispatched.requestId()) || queue.action() != Action.QUERY_QUEUE
                || !selection.core().prefix().equals(queue.core().prefix())) return false;
        var effect = decodeOutcome(dispatched);
        var sampled = decodeOutcome(observed);
        if (!effect.matchesSuccessfulRequest(selection) || !sampled.matchesSuccessfulRequest(queue)
                || !effect.target().equals(sampled.target()) || !effect.lineage().equals(sampled.lineage()))
            return false;
        if (sampled.queue().orElseThrow().targetState() != TargetState.ABSENT) return false;

        var earlier = dispatched.custody().orElseThrow(() -> new IOException("Original Full111 SELECT custody unavailable"));
        var later = observed.custody().orElseThrow(() -> new IOException("Independent Full111 queue custody unavailable"));
        earlier.verify(dispatched, original.guard());
        later.verify(observed);
        if (!earlier.session().equals(later.session()) || !earlier.custodyEpoch().equals(later.custodyEpoch())
                || earlier.writeEntered().observedAt().isBefore(original.submittedAt())
                || !earlier.writeEntered().observedAt().isBefore(selection.deadline())
                || later.writeEntered().order().compareTo(earlier.responseReceived().order()) <= 0
                || later.writeEntered().observedAt().isBefore(earlier.responseReceived().observedAt())
                || !later.writeEntered().observedAt().isBefore(queue.deadline())
                || later.responseReceived().observedAt().isAfter(queue.deadline())
                || !effect.owner().orElseThrow().connectionGeneration().equals(earlier.session().connectionGeneration())
                || !sampled.owner().orElseThrow().connectionGeneration().equals(later.session().connectionGeneration()))
            return false;
        return matchesOutbound(selection, dispatched, selection.lineage().sourceRevision())
                && matchesOutbound(queue, observed, BigInteger.ZERO);
    }

    private static boolean matchesOutbound(Request request, AckReceived response, BigInteger expectedRevision) throws IOException {
        var original = response.outbound().orElseThrow(() -> new IOException("Actual Full111 option request packet unavailable"));
        var sent = NativeWire.decodeExecuteRequest(original.originalPacket());
        return response.requestId().equals(sent.requestId()) && request.action().step().equals(sent.step())
                && sent.expectedRevision().equals(Optional.of(expectedRevision))
                && request.equals(Request.decodeFields(request.action(), sent.normalizedAdditionalFields().value()));
    }

    private static void requireSelf(Optional<String> actual, String expected) throws IOException {
        if (actual.filter(expected::equals).isEmpty()) throw new IOException("Positive Full111 option reply changed its stage request ID");
    }

    private static Result decode(JsonNode token) throws IOException {
        var r = StrictJson.object(token, Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                "backend", "action", "status", "cleanup_known", "source_available", "effect_attempted", "native_returned",
                "facts_before", "owner", "target", "lineage", "queue", "addresses_redacted", "unavailable_reason"));
        require(r, "schema", RESULT_SCHEMA);
        require(r, "adapter_id", BUILD.coreFrameAdapterId());
        require(r, "backend", CurrentLyd.BACKEND);
        if (!BUILD.matches(NativeWire.text(r.get("game_version")), NativeWire.text(r.get("executable_sha256")))
                || !CurrentLyd.bool(r, "addresses_redacted"))
            throw new IOException("Exact Full111 v2 build and redacted provenance required");

        var facts = r.get("facts_before").isNull() ? Optional.<CoreFrame.Prefix>empty()
                : Optional.of(CurrentLyd.readCore(r.get("facts_before")));
        var owner = r.get("owner").isNull() ? Optional.<CurrentLetterResult.OwnerWitness>empty()
                : Optional.of(owner(r.get("owner")));
        var target = r.get("target").isNull() ? Optional.<Target>empty() : Optional.of(Target.decode(r.get("target")));
        var lineage = r.get("lineage").isNull() ? Optional.<Lineage>empty() : Optional.of(Lineage.decode(r.get("lineage")));
        var queue = r.get("queue").isNull() ? Optional.<Queue>empty() : Optional.of(Queue.decode(r.get("queue")));
        var result = new Result(Action.parse(NativeWire.text(r.get("action"))), Status.parse(NativeWire.text(r.get("status"))),
                CurrentLyd.bool(r, "cleanup_known"), CurrentLyd.bool(r, "effect_attempted"), CurrentLyd.bool(r, "native_returned"),
                facts, owner, target, lineage, queue, CurrentLyd.nativeTextOptional(r.get("unavailable_reason")));
        if (CurrentLyd.bool(r, "source_available") != result.successful())
            throw new IOException("Full111 v2 original source availability differs from its exact stage");
        return result;
    }

    private static CurrentLetterResult.OwnerWitness owner(JsonNode node) throws IOException {
        var witness = StrictJson.object(node, Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
        return new CurrentLetterResult.OwnerWitness(CurrentLyd.decimal(witness, "connection_generation"),
                CurrentLyd.decimal(witness, "ticket_sequence"), CurrentLyd.decimal(witness, "pump_epoch"),
                NativeWire.integer(witness.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact());
    }

    private static void require(ObjectNode node, String field, String expected) throws IOException {
        if (!expected.equals(NativeWire.text(node.get(field)))) throw new IOException("Full111 v2 " + field + " differs");
    }
}
