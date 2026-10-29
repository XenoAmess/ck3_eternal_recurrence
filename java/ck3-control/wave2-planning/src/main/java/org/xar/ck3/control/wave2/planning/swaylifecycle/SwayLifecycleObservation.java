package org.xar.ck3.control.wave2.planning.swaylifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** The complete pure prepare/sequence/finalize boundary of the active Sway reader bundle. */
public final class SwayLifecycleObservation {
    private static final String BUILD = "1.20.0.4";
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private SwayLifecycleObservation() { }

    public enum Reader { COMPLETION, OPINION, TERMINATION }
    public enum Status { OBSERVED, FRAME_CHANGED, QUERY_FAILED }
    public enum Presence { MISSING, NULL, VALUE }
    public enum FailureKind {
        BRIDGE_UNAVAILABLE("BridgeUnavailableError"), UNSUPPORTED_STEP("UnsupportedStepError"), VALUE_ERROR("ValueError");
        private final String pythonName;
        FailureKind(String pythonName) { this.pythonName = pythonName; }
        public String pythonName() { return pythonName; }
    }

    /** Missing and explicit null stay distinct; legacy get() comparison is explicit. */
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence, "presence");
            require((presence == Presence.VALUE) == (value != null), "field presence/value mismatch");
        }
        public boolean sameLegacyGet(Field<T> other) {
            Objects.requireNonNull(other, "other");
            return presence == Presence.VALUE && other.presence == Presence.VALUE
                    ? value.equals(other.value) : presence != Presence.VALUE && other.presence != Presence.VALUE;
        }
    }

    public record Permissions(boolean completion, boolean opinion, boolean termination) {
        public boolean enabled(Reader reader) {
            return switch (reader) { case COMPLETION -> completion; case OPINION -> opinion; case TERMINATION -> termination; };
        }
        public boolean any() { return completion || opinion || termination; }
    }

    public record FrameBinding(Field<String> snapshotId, BigInteger revision, BigInteger nativeRevision,
            Field<BigInteger> dateRaw, boolean paused, boolean mapReady, Field<String> episodeRunId,
            Field<BigInteger> episodeCharacterId, Field<String> terminalReason, long actorCharacterId, boolean alive) {
        public FrameBinding {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(episodeCharacterId);
            Objects.requireNonNull(terminalReason); characterId(actorCharacterId);
        }
        public boolean sameLegacyBinding(FrameBinding other) {
            Objects.requireNonNull(other);
            return snapshotId.sameLegacyGet(other.snapshotId) && revision.equals(other.revision)
                    && nativeRevision.equals(other.nativeRevision) && dateRaw.sameLegacyGet(other.dateRaw)
                    && paused == other.paused && mapReady == other.mapReady && episodeRunId.sameLegacyGet(other.episodeRunId)
                    && episodeCharacterId.sameLegacyGet(other.episodeCharacterId) && terminalReason.sameLegacyGet(other.terminalReason)
                    && actorCharacterId == other.actorCharacterId && alive == other.alive;
        }
    }

    public record RetainedAction(String actionId, long actorCharacterId, long targetCharacterId,
            long schemeInstanceId, int schemeInstanceGeneration) {
        public RetainedAction {
            StrictJson.text(actionId); characterId(actorCharacterId); characterId(targetCharacterId);
            require(actorCharacterId != targetCharacterId, "actor and target differ");
            require(schemeInstanceId >= 0 && schemeInstanceId < 0xffff_ffffL
                    && schemeInstanceGeneration >= 0 && schemeInstanceGeneration <= 255
                    && schemeInstanceGeneration == schemeInstanceId >> 24, "full instance/generation mismatch");
        }
    }

    public record ReadCommand(Reader reader, BigInteger expectedRevision, long targetCharacterId,
            OptionalLong schemeInstanceId, OptionalLong afterSequence) {
        public ReadCommand {
            Objects.requireNonNull(reader); Objects.requireNonNull(expectedRevision);
            Objects.requireNonNull(schemeInstanceId); Objects.requireNonNull(afterSequence);
            characterId(targetCharacterId);
            require(expectedRevision.signum() > 0, "public revision must be positive");
            require(schemeInstanceId.isPresent() == (reader != Reader.OPINION), "reader instance shape differs");
            require(afterSequence.isPresent() == (reader == Reader.TERMINATION), "termination alone uses after_sequence");
            require(schemeInstanceId.isEmpty() || (schemeInstanceId.orElseThrow() >= 0
                    && schemeInstanceId.orElseThrow() < 0xffff_ffffL), "reader instance outside full-ID domain");
            require(afterSequence.isEmpty() || afterSequence.orElseThrow() == 0, "independent termination sequence starts at zero");
        }
    }

    public record Plan(RetainedAction original, FrameBinding before, Permissions permissions, List<ReadCommand> commands) {
        public Plan {
            Objects.requireNonNull(original); Objects.requireNonNull(before); Objects.requireNonNull(permissions);
            commands = List.copyOf(commands);
            require(before.paused && before.mapReady && before.alive && before.actorCharacterId == original.actorCharacterId
                    && before.revision.signum() > 0 && before.nativeRevision.signum() > 0
                    && before.terminalReason.presence != Presence.VALUE && permissions.any(), "unready original observation frame");
            require(commands.equals(commandsFor(original, before, permissions)), "fixed reader plan differs");
        }
    }

    public record ReadMetadata(Field<String> status, Field<String> queriedSnapshotId, Field<BigInteger> queriedRevision,
            Field<BigInteger> queriedNativeRevision, Field<BigInteger> readDateRaw) {
        public ReadMetadata {
            Objects.requireNonNull(status); Objects.requireNonNull(queriedSnapshotId); Objects.requireNonNull(queriedRevision);
            Objects.requireNonNull(queriedNativeRevision); Objects.requireNonNull(readDateRaw);
        }
    }
    public sealed interface ReadReceipt permits Returned, Failed { ReadCommand command(); }
    public record Returned(ReadCommand command, ReadMetadata metadata) implements ReadReceipt {
        public Returned { Objects.requireNonNull(command); Objects.requireNonNull(metadata); }
    }
    public record Failed(ReadCommand command, FailureKind kind, String message) implements ReadReceipt {
        public Failed { Objects.requireNonNull(command); Objects.requireNonNull(kind); Objects.requireNonNull(message); }
        public String error() { return kind.pythonName() + ": " + message; }
    }
    public record Result(Status status, RetainedAction original, boolean sameFrame, List<ReadReceipt> reads) {
        public Result {
            Objects.requireNonNull(status); Objects.requireNonNull(original); reads = List.copyOf(reads);
            require(!reads.isEmpty(), "an eligible observation result requires an actual attempted read");
            int previous = -1;
            for (int index = 0; index < reads.size(); index++) {
                ReadReceipt read = reads.get(index);
                require(read.command().reader.ordinal() > previous, "result read sequence cannot repeat or reorder");
                require(!(read instanceof Failed) || index == reads.size() - 1, "no read may follow the first failure");
                require(read.command().targetCharacterId == original.targetCharacterId
                        && (read.command().schemeInstanceId.isEmpty()
                        || read.command().schemeInstanceId.orElseThrow() == original.schemeInstanceId), "result read identity differs");
                previous = read.command().reader.ordinal();
            }
            boolean failed = !reads.isEmpty() && reads.getLast() instanceof Failed;
            require(status == (failed ? Status.QUERY_FAILED : sameFrame ? Status.OBSERVED : Status.FRAME_CHANGED),
                    "result status must derive from read failure and actual frame binding");
        }
        public boolean requestRetried() { return false; }
        public boolean submissionAuthorized() { return false; }
        public boolean terminalOutcomeGranted() { return false; }
    }

    /** Original source eligibility; these are data checks, not native qualification. */
    public static Optional<Plan> prepare(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("resolved", "before", "permissions", "target_character_id"));
        return prepare(input);
    }

    private static Optional<Plan> prepare(ObjectNode input) {
        try {
            Permissions permissions = permissions(input.get("permissions"));
            if (!permissions.any()) { return Optional.empty(); }
            RetainedAction action = retained(input.get("resolved"));
            JsonNode selectedTarget = input.get("target_character_id");
            if (!selectedTarget.isNull()) {
                require(id(selectedTarget) == action.targetCharacterId, "explicit target differs");
            }
            FrameBinding before = frame(input.get("before"));
            return Optional.of(new Plan(action, before, permissions, commandsFor(action, before, permissions)));
        } catch (ContractViolationException unavailable) { return Optional.empty(); }
    }

    private static List<ReadCommand> commandsFor(RetainedAction action, FrameBinding before, Permissions permissions) {
        List<ReadCommand> commands = new ArrayList<>();
        for (Reader reader : Reader.values()) {
            if (permissions.enabled(reader)) {
                commands.add(new ReadCommand(reader, before.revision, action.targetCharacterId,
                        reader == Reader.OPINION ? OptionalLong.empty() : OptionalLong.of(action.schemeInstanceId),
                        reader == Reader.TERMINATION ? OptionalLong.of(0) : OptionalLong.empty()));
            }
        }
        return List.copyOf(commands);
    }

    /** Consume each original read once. First failure stops the bundle, without retry. */
    public static Result complete(Plan plan, List<ReadReceipt> reads, FrameBinding after) {
        Objects.requireNonNull(plan); Objects.requireNonNull(after); reads = List.copyOf(reads);
        require(reads.size() <= plan.commands.size(), "unexpected additional read");
        boolean failed = false;
        for (int index = 0; index < reads.size(); index++) {
            require(!failed && reads.get(index).command().equals(plan.commands.get(index)), "read order/arguments drifted or retried");
            failed = reads.get(index) instanceof Failed;
        }
        require(failed || reads.size() == plan.commands.size(), "enabled bundle ended before a returned read or failure");
        boolean sameFrame = plan.before.sameLegacyBinding(after);
        return new Result(failed ? Status.QUERY_FAILED : sameFrame ? Status.OBSERVED : Status.FRAME_CHANGED,
                plan.original, sameFrame, reads);
    }

    /** Evaluate a captured real service call trace; no input GREEN flag grants authority. */
    public static byte[] evaluate(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("resolved", "before", "after", "permissions",
                "target_character_id", "reads"));
        Optional<Plan> plan = prepare(input);
        JsonNode trace = input.get("reads");
        require(trace.isArray() && trace.size() <= 3, "bounded actual read trace required");
        if (plan.isEmpty()) {
            require(trace.isEmpty(), "ineligible source cannot claim executed reads");
            return new byte[] {'n', 'u', 'l', 'l'};
        }
        List<ReadReceipt> reads = new ArrayList<>();
        for (JsonNode row : trace) { reads.add(receipt(row)); }
        return encode(complete(plan.orElseThrow(), reads, frame(input.get("after"))));
    }

    public static byte[] encode(Result result) {
        Objects.requireNonNull(result);
        ObjectNode output = StrictJson.object();
        output.put("status", switch (result.status) { case OBSERVED -> "observed"; case FRAME_CHANGED -> "frame_changed"; case QUERY_FAILED -> "query_failed"; });
        output.put("original_action_id", result.original.actionId);
        output.put("actor_character_id", result.original.actorCharacterId);
        output.put("target_character_id", result.original.targetCharacterId);
        output.put("scheme_instance_id", result.original.schemeInstanceId);
        output.put("scheme_instance_generation", result.original.schemeInstanceGeneration);
        output.put("same_frame", result.sameFrame);
        output.put("request_retried", false);
        ObjectNode summaries = StrictJson.object();
        for (Reader reader : Reader.values()) {
            ObjectNode summary = StrictJson.object();
            Optional<ReadReceipt> receipt = result.reads.stream().filter(row -> row.command().reader == reader).findFirst();
            summary.put("requested", receipt.isPresent());
            if (receipt.isEmpty()) { summary.put("status", "not_requested"); }
            else if (receipt.orElseThrow() instanceof Failed failure) {
                summary.put("status", "query_failed"); summary.put("error", failure.error());
            } else if (receipt.orElseThrow() instanceof Returned returned) {
                textField(summary, "status", returned.metadata.status);
                textField(summary, "queried_snapshot_id", returned.metadata.queriedSnapshotId);
                integerField(summary, "queried_revision", returned.metadata.queriedRevision);
                integerField(summary, "queried_native_revision", returned.metadata.queriedNativeRevision);
                integerField(summary, "read_date_raw", returned.metadata.readDateRaw);
            }
            summaries.set(reader.name().toLowerCase(Locale.ROOT), summary);
        }
        output.set("reads", summaries);
        return StrictJson.canonical(output);
    }

    private static ReadReceipt receipt(JsonNode node) {
        require(node != null && node.isObject(), "read trace object required");
        String kind = StrictJson.text(node.get("kind"));
        StrictJson.object(node, kind.equals("returned") ? Set.of("reader", "arguments", "kind", "observation")
                : Set.of("reader", "arguments", "kind", "error_kind", "message"));
        Reader reader;
        try { reader = Reader.valueOf(StrictJson.text(node.get("reader")).toUpperCase(Locale.ROOT)); }
        catch (IllegalArgumentException invalid) { throw new ContractViolationException("unknown Sway reader", invalid); }
        JsonNode arguments = node.get("arguments");
        StrictJson.object(arguments, switch (reader) {
            case COMPLETION -> Set.of("expected_revision", "target_character_id", "scheme_instance_id");
            case OPINION -> Set.of("expected_revision", "target_character_id");
            case TERMINATION -> Set.of("expected_revision", "target_character_id", "scheme_instance_id", "after_sequence");
        });
        ReadCommand command = new ReadCommand(reader, integer(arguments.get("expected_revision")), id(arguments.get("target_character_id")),
                reader == Reader.OPINION ? OptionalLong.empty() : OptionalLong.of(StrictJson.integer(arguments.get("scheme_instance_id"), 0, 0xffff_fffeL)),
                reader == Reader.TERMINATION ? OptionalLong.of(StrictJson.integer(arguments.get("after_sequence"), 0, 0)) : OptionalLong.empty());
        if (kind.equals("returned")) {
            JsonNode observation = node.get("observation"); require(observation.isObject(), "normalized observation object required");
            return new Returned(command, new ReadMetadata(text(observation, "status"), text(observation, "queried_snapshot_id"),
                    number(observation, "queried_revision"), number(observation, "queried_native_revision"), number(observation, "date_raw")));
        }
        require(kind.equals("failed"), "read trace kind must be returned or failed");
        FailureKind failure = switch (StrictJson.text(node.get("error_kind"))) {
            case "BridgeUnavailableError" -> FailureKind.BRIDGE_UNAVAILABLE;
            case "UnsupportedStepError" -> FailureKind.UNSUPPORTED_STEP;
            case "ValueError" -> FailureKind.VALUE_ERROR;
            default -> throw new ContractViolationException("failure was not caught by the original observer");
        };
        JsonNode message = node.get("message"); require(message.isTextual(), "error message string required");
        return new Failed(command, failure, message.textValue());
    }

    private static Permissions permissions(JsonNode node) {
        StrictJson.object(node, Set.of("completion", "opinion", "termination"));
        return new Permissions(bool(node.get("completion")), bool(node.get("opinion")), bool(node.get("termination")));
    }

    private static FrameBinding frame(JsonNode node) {
        require(node != null && node.isObject(), "frame object required");
        JsonNode played = node.get("played_character");
        JsonNode actor = played != null && played.isObject() ? played.get("character_id") : node.get("played_character_id");
        JsonNode alive = played != null && played.isObject() ? played.get("alive") : node.get("played_character_alive");
        return new FrameBinding(text(node, "snapshot_id"), integer(node.get("revision")), integer(node.get("native_revision")),
                number(node, "date_raw"), bool(node.get("paused")), bool(node.get("map_ready")), text(node, "episode_run_id"),
                number(node, "episode_character_id"), text(node, "one_life_terminal_reason"), id(actor), bool(alive));
    }

    private static RetainedAction retained(JsonNode resolved) {
        require(resolved != null && resolved.isObject(), "resolved original required");
        eq(resolved.get("status"), "applied"); yes(resolved.get("postcondition_verified"));
        String action = StrictJson.text(resolved.get("action_id"));
        long actor = id(resolved.get("actor_character_id")), target = id(resolved.get("target_character_id"));
        JsonNode receipt = resolved.get("native_receipt"), identity;
        if (receipt != null && receipt.isObject()) {
            eq(receipt.get("schema"), "active-scheme-sway-formal-private-v1"); eq(receipt.get("stage"), "applied");
            yes(receipt.get("postcondition_verified")); eq(receipt.get("action_id"), action);
            if (isText(receipt.get("exact_ck3_build"), BUILD) && !receipt.has("actor_character_id") && !receipt.has("target_character_id")) {
                require(StrictJson.text(receipt.get("exe_sha256")).toUpperCase(Locale.ROOT).equals(SHA), "receipt exact executable differs");
                BigInteger before = integer(resolved.get("pre_capture_epoch")), copied = integer(receipt.get("post_capture_epoch")), after = integer(resolved.get("post_capture_epoch"));
                require(before.signum() > 0 && before.compareTo(copied) < 0 && copied.compareTo(after) <= 0, "receipt epoch chain differs");
                BigInteger date = integer(receipt.get("post_date_raw"));
                require(date.signum() > 0 && date.equals(integer(resolved.get("post_date_raw"))), "receipt date differs");
                require(StrictJson.integer(receipt.get("scheme_instance_id"), 1, 0xffff_fffeL) > 0, "projected receipt instance must be positive");
            } else {
                require(id(receipt.get("actor_character_id")) == actor && id(receipt.get("target_character_id")) == target,
                        "explicit receipt actor/target differs");
            }
            identity = receipt;
        } else {
            require(receipt == null || receipt.isNull(), "malformed receipt cannot use recovery fallback");
            identity = resolved.get("recovered_instance_observation");
            require(identity != null && identity.isObject(), "retained recovered identity required");
            eq(identity.get("schema"), "xar.ck3.sway-recovered-instance-observation.v1");
            eq(identity.get("source_kind"), "matching_active_readback_recovery");
            require(!bool(identity.get("submission_receipt_available")), "recovered identity must retain missing submission receipt");
            eq(identity.get("action_id"), action);
            require(id(identity.get("actor_character_id")) == actor && id(identity.get("target_character_id")) == target, "recovered actor/target differs");
            JsonNode active = identity.get("active_instance"), source = identity.get("source_read");
            require(active != null && active.isObject() && source != null && source.isObject(), "recovered active row and source read required");
            require(integer(active.get("scheme_instance_id")).equals(integer(identity.get("scheme_instance_id")))
                    && integer(active.get("scheme_instance_generation")).equals(integer(identity.get("scheme_instance_generation")))
                    && id(active.get("target_character_id")) == target, "recovered active identity differs");
            eq(source.get("schema"), "active-scheme-sway-private-read-v1");
            for (String field : Set.of("exact_ck3_build", "exe_sha256", "queried_snapshot_id", "queried_revision", "queried_native_revision",
                    "snapshot_revision", "date_raw", "capture_epoch", "container_generation", "post_snapshot_id")) {
                require(source.has(field), "recovered source field missing: " + field);
            }
        }
        return new RetainedAction(action, actor, target, StrictJson.integer(identity.get("scheme_instance_id"), 0, 0xffff_fffeL),
                Math.toIntExact(StrictJson.integer(identity.get("scheme_instance_generation"), 0, 255)));
    }

    private static Field<String> text(JsonNode row, String key) {
        JsonNode node = row.get(key);
        if (node == null) { return new Field<>(Presence.MISSING, null); }
        if (node.isNull()) { return new Field<>(Presence.NULL, null); }
        require(node.isTextual(), "actual string required: " + key);
        return new Field<>(Presence.VALUE, node.textValue());
    }
    private static Field<BigInteger> number(JsonNode row, String key) {
        JsonNode node = row.get(key);
        if (node == null) { return new Field<>(Presence.MISSING, null); }
        if (node.isNull()) { return new Field<>(Presence.NULL, null); }
        return new Field<>(Presence.VALUE, integer(node));
    }
    private static void textField(ObjectNode row, String key, Field<String> value) {
        if (value.presence == Presence.VALUE) { row.put(key, value.value); } else { row.putNull(key); }
    }
    private static void integerField(ObjectNode row, String key, Field<BigInteger> value) {
        if (value.presence == Presence.VALUE) { row.put(key, value.value); } else { row.putNull(key); }
    }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "actual integer required"); return node.bigIntegerValue(); }
    private static long id(JsonNode node) { return StrictJson.integer(node, 1, 0xffff_ffffL); }
    private static void characterId(long value) { require(value > 0 && value <= 0xffff_ffffL, "full character ID required"); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean required"); return node.booleanValue(); }
    private static void yes(JsonNode node) { require(bool(node), "actual true required"); }
    private static boolean isText(JsonNode node, String text) { return node != null && node.isTextual() && text.equals(node.textValue()); }
    private static void eq(JsonNode node, String text) { require(isText(node, text), "source text differs"); }
    private static void require(boolean value, String reason) { StrictJson.require(value, reason); }
}
