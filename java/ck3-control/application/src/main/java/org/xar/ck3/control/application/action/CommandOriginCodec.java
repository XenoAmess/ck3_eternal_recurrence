package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Alias-free durable origin facts. Decoding never issues a SubmissionPermit or a ReadPermit. */
public final class CommandOriginCodec {
    public static final String SCHEMA = "xar.command-origin/v1";
    public static final String LIFECYCLE_ORIGIN_SCHEMA = "xar.command-origin/v2";
    public static final String RECONCILIATION_ORIGIN_SCHEMA = "xar.command-origin/v3";
    public static final String PHYSICAL_STATUS_ORIGIN_SCHEMA = "xar.command-origin/v4";
    private CommandOriginCodec() { }
    public static ObjectNode origin(CommandOrigin value) {
        ObjectNode row = StrictJson.object(); row.put("schema", value instanceof CommandOrigin.PhysicalStatusOnly ? PHYSICAL_STATUS_ORIGIN_SCHEMA : value instanceof CommandOrigin.Reconciliation ? RECONCILIATION_ORIGIN_SCHEMA : value instanceof CommandOrigin.LifecycleTerminal ? LIFECYCLE_ORIGIN_SCHEMA : SCHEMA);
        if (value instanceof CommandOrigin.Gameplay gameplay) {
            row.put("kind", "GAMEPLAY"); row.set("before", ProposalLifecycleCodec.observation(gameplay.before()));
        } else if (value instanceof CommandOrigin.Frontend observed) { row.put("kind", "FRONTEND"); row.set("identity", frontend(observed.identity())); }
        else if (value instanceof CommandOrigin.LifecycleTerminal) { row.put("kind", "LIFECYCLE_TERMINAL"); row.set("identity", LifecycleIdentityCodec.encode(value.requireLifecycleTerminal())); }
        else if (value instanceof CommandOrigin.PhysicalStatusOnly physical) { row.put("kind", "PHYSICAL_STATUS_ONLY"); row.set("identity", PhysicalStatusIdentityCodec.encode(physical.identity())); }
        else { row.put("kind", "RECONCILIATION"); row.set("identity", ReconciliationIdentityCodec.encode(value.requireReconciliation())); }
        return row;
    }
    public static CommandOrigin origin(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "typed command origin required"); ObjectNode row = (ObjectNode) value;
        boolean terminal = text(row, "kind").equals("LIFECYCLE_TERMINAL"), reconciliation = text(row, "kind").equals("RECONCILIATION"),
                physicalStatus = text(row, "kind").equals("PHYSICAL_STATUS_ONLY");
        StrictJson.require((physicalStatus ? PHYSICAL_STATUS_ORIGIN_SCHEMA : reconciliation ? RECONCILIATION_ORIGIN_SCHEMA : terminal ? LIFECYCLE_ORIGIN_SCHEMA : SCHEMA).equals(text(row, "schema")), "exact origin phase schema required");
        return switch (text(row, "kind")) {
            case "GAMEPLAY" -> { StrictJson.object(row, Set.of("schema", "kind", "before")); yield new CommandOrigin.Gameplay(ProposalLifecycleCodec.decodeObservation(row.get("before"))); }
            case "FRONTEND" -> { StrictJson.object(row, Set.of("schema", "kind", "identity")); yield new CommandOrigin.Frontend(frontend(row.get("identity"))); }
            case "LIFECYCLE_TERMINAL" -> { StrictJson.object(row, Set.of("schema", "kind", "identity")); yield new CommandOrigin.LifecycleTerminal(LifecycleIdentityCodec.decode(row.get("identity"))); }
            case "RECONCILIATION" -> { StrictJson.object(row, Set.of("schema", "kind", "identity")); yield new CommandOrigin.Reconciliation(ReconciliationIdentityCodec.decode(row.get("identity"))); }
            case "PHYSICAL_STATUS_ONLY" -> { StrictJson.object(row, Set.of("schema", "kind", "identity")); yield new CommandOrigin.PhysicalStatusOnly(PhysicalStatusIdentityCodec.decode(row.get("identity"))); }
            default -> throw new IllegalArgumentException("unknown command origin phase");
        };
    }
    public static ObjectNode frontend(FrontendIdentity value) {
        var row = StrictJson.object(); row.put("machine_id", value.machineId()); row.set("game", value.game().toJson());
        row.put("frontend_session_id", value.frontendSessionId()); row.put("connection_generation", decimal(value.connectionGeneration()));
        row.put("bridge_pid", value.bridgePid()); row.set("frame", frame(value.frame()));
        row.set("native_evidence", value.nativeEvidence().toJson()); row.set("capability_evidence", value.capabilityEvidence().toJson()); return row;
    }
    public static FrontendIdentity frontend(JsonNode value) {
        var row = StrictJson.object(value, Set.of("machine_id", "game", "frontend_session_id", "connection_generation", "bridge_pid", "frame", "native_evidence", "capability_evidence"));
        return new FrontendIdentity(text(row, "machine_id"), GameGeneration.fromJson(row.get("game")), text(row, "frontend_session_id"),
                uint64(row, "connection_generation", true), StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL), frame(row.get("frame")),
                ExactRef.fromJson(row.get("native_evidence")), ExactRef.fromJson(row.get("capability_evidence")));
    }
    public static ObjectNode frame(FrontendFrame value) {
        var row = StrictJson.object(); row.put("query_sequence", decimal(value.querySequence()));
        if (value instanceof FrontendFrame.Menu) row.put("kind", "MENU");
        else {
            var snapshot = (FrontendFrame.Snapshot) value; row.put("kind", "SNAPSHOT"); row.put("snapshot_id", snapshot.snapshotId());
            row.put("revision", decimal(snapshot.revision())); row.put("native_revision", decimal(snapshot.nativeRevision())); row.put("date_raw", Long.toString(snapshot.dateRaw()));
        }
        return row;
    }
    public static FrontendFrame frame(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "frontend frame object required"); var row = (ObjectNode) value;
        return switch (text(row, "kind")) {
            case "MENU" -> { StrictJson.object(row, Set.of("kind", "query_sequence")); yield new FrontendFrame.Menu(uint64(row, "query_sequence", true)); }
            case "SNAPSHOT" -> {
                StrictJson.object(row, Set.of("kind", "query_sequence", "snapshot_id", "revision", "native_revision", "date_raw"));
                String date = text(row, "date_raw"); long exactDate = Long.parseLong(date);
                StrictJson.require(Long.toString(exactDate).equals(date), "canonical signed i64 frontend date string required");
                yield new FrontendFrame.Snapshot(text(row, "snapshot_id"), uint64(row, "revision", true), uint64(row, "native_revision", true), exactDate, uint64(row, "query_sequence", true));
            }
            default -> throw new IllegalArgumentException("unknown frontend frame kind");
        };
    }
    public static ObjectNode expectation(CommandExpectation value) {
        var row = StrictJson.object();
        if (value instanceof CommandExpectation.OperatorRebind operator) {
            var expected = operator.expected(); row.put("kind", "OPERATOR_REBIND"); row.put("schema", OperatorRebindExpectation.SCHEMA);
            row.set("origin", origin(expected.origin())); row.set("source", ProposalLifecycleCodec.source(expected.source()));
            row.put("target_character_id", expected.request().characterId()); row.put("expected_revision", expected.request().expectedRevision().toString());
            row.put("episode_run_id", expected.episodeRunId()); row.put("episode_epoch", expected.episodeEpoch());
            row.set("before_driver", expected.beforeDriver().toJson());
        } else if (value instanceof CommandExpectation.Gameplay gameplay) { row.put("kind", "GAMEPLAY"); row.set("expected", ProposalLifecycleCodec.expected(gameplay.expected())); }
        else if (value instanceof CommandExpectation.Frontend frontend) {
            var expected = frontend.expected(); row.put("kind", "FRONTEND");
            row.set("before", frontend(expected.before())); row.set("source", ProposalLifecycleCodec.source(expected.source()));
            row.put("observer_schema", expected.observerSchema()); row.set("values", values(expected.values()));
        } else if (value instanceof CommandExpectation.GameplayEntry) {
            var expected = ((CommandExpectation.GameplayEntry) value).expected(); row.put("kind", "GAMEPLAY_ENTRY");
            row.set("before", frontend(expected.before())); row.set("source", ProposalLifecycleCodec.source(expected.source()));
            row.put("schema", FrontendGameplayExpectedPostcondition.SCHEMA); row.put("observer_schema", expected.observerSchema());
            row.put("selected_bookmark_key", expected.selectedBookmarkKey()); row.put("selected_character_name_key", expected.selectedCharacterNameKey());
            row.put("selected_date_raw", expected.selectedDateRaw());
            row.set("values", values(expected.values()));
        } else {
            var expected = value.requireLifecycleTerminal(); row.put("kind", "LIFECYCLE_TERMINAL");
            row.put("schema", LifecycleExpectedPostcondition.SCHEMA); row.set("before", LifecycleIdentityCodec.encode(expected.before()));
            row.set("source", ProposalLifecycleCodec.source(expected.source())); row.put("observer_schema", expected.observerSchema());
            row.put("operation", expected.operation().name()); row.set("values", values(expected.values()));
        }
        return row;
    }
    public static CommandExpectation expectation(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "typed expectation object required"); var row = (ObjectNode) value;
        return switch (text(row, "kind")) {
            case "OPERATOR_REBIND" -> {
                StrictJson.object(row, Set.of("kind", "schema", "origin", "source", "target_character_id", "expected_revision", "episode_run_id", "episode_epoch", "before_driver"));
                StrictJson.require(text(row, "schema").equals(OperatorRebindExpectation.SCHEMA), "exact operator rebind expectation schema required");
                yield new CommandExpectation.OperatorRebind(new OperatorRebindExpectation(origin(row.get("origin")), G2Wire.source(row.get("source")),
                        new org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.Request(
                                StrictJson.integer(row.get("target_character_id"), 1, Integer.MAX_VALUE), new java.math.BigInteger(new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(text(row, "expected_revision")).decimal())),
                        text(row, "episode_run_id"), StrictJson.integer(row.get("episode_epoch"), 0, StrictJson.MAX_SAFE_INTEGER), ExactRef.fromJson(row.get("before_driver"))));
            }
            case "GAMEPLAY" -> { StrictJson.object(row, Set.of("kind", "expected")); yield new CommandExpectation.Gameplay(gameplayExpected(row.get("expected"))); }
            case "FRONTEND" -> {
                StrictJson.object(row, Set.of("kind", "before", "source", "observer_schema", "values"));
                yield new CommandExpectation.Frontend(new FrontendExpectedPostcondition(frontend(row.get("before")), G2Wire.source(row.get("source")), text(row, "observer_schema"), ProposalLifecycleCodec.values(row.get("values"))));
            }
            case "GAMEPLAY_ENTRY" -> {
                StrictJson.object(row, Set.of("schema", "kind", "before", "source", "observer_schema", "selected_bookmark_key", "selected_character_name_key", "selected_date_raw", "values"));
                StrictJson.require(text(row, "schema").equals(FrontendGameplayExpectedPostcondition.SCHEMA), "exact native selection entry expectation schema required");
                yield new CommandExpectation.GameplayEntry(new FrontendGameplayExpectedPostcondition(frontend(row.get("before")), G2Wire.source(row.get("source")),
                        text(row, "observer_schema"), text(row, "selected_bookmark_key"), text(row, "selected_character_name_key"),
                        Math.toIntExact(StrictJson.integer(row.get("selected_date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE)), ProposalLifecycleCodec.values(row.get("values"))));
            }
            case "LIFECYCLE_TERMINAL" -> {
                StrictJson.object(row, Set.of("schema", "kind", "before", "source", "observer_schema", "operation", "values"));
                StrictJson.require(text(row, "schema").equals(LifecycleExpectedPostcondition.SCHEMA), "exact lifecycle terminal expectation schema required");
                yield new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(LifecycleIdentityCodec.decode(row.get("before")),
                        G2Wire.source(row.get("source")), text(row, "observer_schema"), LifecycleExpectedPostcondition.Operation.valueOf(text(row, "operation")),
                        ProposalLifecycleCodec.values(row.get("values"))));
            }
            default -> throw new IllegalArgumentException("unknown command expectation phase");
        };
    }
    public static ExpectedPostcondition gameplayExpected(JsonNode value) {
        var row = StrictJson.object(value, Set.of("version", "before", "source", "observer_schema", "values"));
        return new ExpectedPostcondition(Math.toIntExact(StrictJson.integer(row.get("version"), 1, 1)), ProposalLifecycleCodec.decodeObservation(row.get("before")),
                G2Wire.source(row.get("source")), text(row, "observer_schema"), ProposalLifecycleCodec.values(row.get("values")));
    }
    /** Existing gameplay encoding is byte-compatible; frontend facts carry an explicit schema and origin. */
    public static ObjectNode guard(GuardEvidence value) {
        var row = StrictJson.object();
        if (!value.supportingEvidence().isEmpty()) {
            row.put("schema", value.origin() instanceof CommandOrigin.PhysicalStatusOnly ? "xar.physical-status-guard/v1" : "xar.command-guard/v2"); row.set("origin", origin(value.origin()));
            var refs = row.putArray("supporting_evidence"); value.supportingEvidence().forEach(ref -> refs.add(ref.toJson()));
        } else if (value.origin() instanceof CommandOrigin.Gameplay) row.set("observed", ProposalLifecycleCodec.observation(value.observed()));
        else { row.put("schema", "xar.frontend-guard/v1"); row.set("origin", origin(value.origin())); }
        row.set("source", ProposalLifecycleCodec.source(value.source())); row.put("session_id", value.sessionId()); row.put("connection_generation", decimal(value.connectionGeneration()));
        row.put("operation", value.operation().value()); row.set("native_evidence", value.nativeEvidence().toJson()); row.set("capability_evidence", value.capabilityEvidence().toJson());
        row.put("authority_id", value.authorityId()); row.put("observed_at", value.observedAt().toString()); row.put("valid_until", value.validUntil().toString()); return row;
    }
    public static GuardEvidence guard(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "guard object required"); var row = (ObjectNode) value; CommandOrigin commandOrigin;
        List<ExactRef> supporting = new ArrayList<>();
        if (row.has("schema")) {
            if (text(row, "schema").equals("xar.command-guard/v2") || text(row, "schema").equals("xar.physical-status-guard/v1")) {
                StrictJson.object(row, Set.of("schema", "origin", "source", "session_id", "connection_generation", "operation", "native_evidence", "capability_evidence", "authority_id", "observed_at", "valid_until", "supporting_evidence"));
                StrictJson.require(row.get("supporting_evidence").isArray() && !row.get("supporting_evidence").isEmpty(), "v2 guard requires actual supporting evidence closure");
                row.get("supporting_evidence").forEach(ref -> supporting.add(ExactRef.fromJson(ref))); commandOrigin = origin(row.get("origin"));
                StrictJson.require(text(row, "schema").equals("xar.physical-status-guard/v1") == (commandOrigin instanceof CommandOrigin.PhysicalStatusOnly),
                        "physical status guard cannot use the historical command-guard schema");
            } else {
                StrictJson.object(row, Set.of("schema", "origin", "source", "session_id", "connection_generation", "operation", "native_evidence", "capability_evidence", "authority_id", "observed_at", "valid_until"));
                StrictJson.require(text(row, "schema").equals("xar.frontend-guard/v1"), "exact frontend guard schema required");
                commandOrigin = origin(row.get("origin")); StrictJson.require(commandOrigin instanceof CommandOrigin.Frontend, "frontend guard requires frontend origin");
            }
        } else {
            StrictJson.object(row, Set.of("observed", "source", "session_id", "connection_generation", "operation", "native_evidence", "capability_evidence", "authority_id", "observed_at", "valid_until"));
            commandOrigin = new CommandOrigin.Gameplay(ProposalLifecycleCodec.decodeObservation(row.get("observed")));
        }
        return new GuardEvidence(commandOrigin, G2Wire.source(row.get("source")), text(row, "session_id"), uint64(row, "connection_generation", true),
                new OperationKey(text(row, "operation")), ExactRef.fromJson(row.get("native_evidence")), ExactRef.fromJson(row.get("capability_evidence")), text(row, "authority_id"), Instant.parse(text(row, "observed_at")), Instant.parse(text(row, "valid_until")), supporting);
    }
    public static ObjectNode frontendEffect(FrontendEffectObservation value) {
        var row = StrictJson.object(); row.put("schema", value.supportingEvidence().isEmpty() ? "xar.frontend-effect/v1" : "xar.frontend-effect/v2"); row.set("after", frontend(value.after())); row.set("source", ProposalLifecycleCodec.source(value.source()));
        row.put("session_id", value.sessionId()); row.put("observer_schema", value.observerSchema()); row.set("actual", values(value.actual()));
        if (!value.supportingEvidence().isEmpty()) {
            var refs = row.putArray("supporting_evidence"); value.supportingEvidence().forEach(ref -> refs.add(ref.toJson()));
        }
        row.put("read_request_id", value.readRequestId()); row.put("observed_at", value.observedAt().toString()); row.set("original_evidence", value.originalEvidence().toJson()); return row;
    }
    public static FrontendEffectObservation frontendEffect(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "frontend effect object required"); var row = (ObjectNode) value;
        List<ExactRef> supporting = new ArrayList<>();
        switch (text(row, "schema")) {
            case "xar.frontend-effect/v1" -> StrictJson.object(row, Set.of("schema", "after", "source", "session_id", "observer_schema", "actual", "read_request_id", "observed_at", "original_evidence"));
            case "xar.frontend-effect/v2" -> {
                StrictJson.object(row, Set.of("schema", "after", "source", "session_id", "observer_schema", "actual", "read_request_id", "observed_at", "original_evidence", "supporting_evidence"));
                StrictJson.require(row.get("supporting_evidence").isArray() && !row.get("supporting_evidence").isEmpty()
                        && row.get("supporting_evidence").size() <= 64, "v2 frontend effect requires bounded actual domain evidence");
                row.get("supporting_evidence").forEach(ref -> supporting.add(ExactRef.fromJson(ref)));
            }
            default -> throw new IllegalArgumentException("exact frontend effect schema required");
        }
        return new FrontendEffectObservation(frontend(row.get("after")), G2Wire.source(row.get("source")), text(row, "session_id"), text(row, "observer_schema"),
                ProposalLifecycleCodec.values(row.get("actual")), text(row, "read_request_id"), Instant.parse(text(row, "observed_at")), ExactRef.fromJson(row.get("original_evidence")), supporting);
    }
    public static ObjectNode gameplayEntry(FrontendGameplayObservation value, Function<PlanningReadReceipt, ExactRef> archiveRead) {
        var row = StrictJson.object(); row.put("schema", "xar.frontend-gameplay-observation/v2"); row.set("before", frontend(value.before()));
        row.set("source", ProposalLifecycleCodec.source(value.source())); row.set("gameplay_session", OrdinaryCycleTransitions.sessionToJson(value.gameplaySession()));
        row.put("connection_generation", decimal(value.connectionGeneration())); row.put("observer_schema", value.observerSchema());
        row.set("actual", values(value.actual())); row.set("semantic_evidence", OrdinaryCycleTransitions.semanticToJson(value.semanticEvidence()));
        ExactRef read = java.util.Objects.requireNonNull(archiveRead.apply(value.campaignRootRead()));
        StrictJson.require(read.bytes() > 0, "actual archived campaign-root read required"); row.set("campaign_root_read", read.toJson());
        var supporting = row.putArray("supporting_evidence"); value.supportingEvidence().forEach(ref -> supporting.add(ref.toJson())); return row;
    }
    public static FrontendGameplayObservation gameplayEntry(JsonNode value, Function<ExactRef, PlanningReadReceipt> loadRead) {
        var row = StrictJson.object(value, Set.of("schema", "before", "source", "gameplay_session", "connection_generation", "observer_schema", "actual", "semantic_evidence", "campaign_root_read", "supporting_evidence"));
        StrictJson.require(text(row, "schema").equals("xar.frontend-gameplay-observation/v2"), "exact frontend gameplay publication schema required");
        StrictJson.require(row.get("supporting_evidence").isArray() && !row.get("supporting_evidence").isEmpty()
                && row.get("supporting_evidence").size() <= 64, "actual gameplay entry support closure required");
        List<ExactRef> supporting = new ArrayList<>(); row.get("supporting_evidence").forEach(ref -> supporting.add(ExactRef.fromJson(ref)));
        return new FrontendGameplayObservation(frontend(row.get("before")), G2Wire.source(row.get("source")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("gameplay_session")), uint64(row, "connection_generation", true), text(row, "observer_schema"),
                ProposalLifecycleCodec.values(row.get("actual")), OrdinaryCycleTransitions.semanticFromJson(row.get("semantic_evidence")),
                java.util.Objects.requireNonNull(loadRead.apply(ExactRef.fromJson(row.get("campaign_root_read")))), supporting);
    }
    /** Arguments remain one archived original; the archive owns and validates their actual bytes. */
    public static ObjectNode planningRequest(PlanningReadRequest value, ExactRef archivedArguments) {
        StrictJson.require(archivedArguments != null && archivedArguments.bytes() > 0, "actual archived planning arguments required");
        var row = StrictJson.object();
        if (value.origin() instanceof CommandOrigin.Gameplay) row.set("before", ProposalLifecycleCodec.observation(value.before()));
        else { row.put("schema", value.origin() instanceof CommandOrigin.PhysicalStatusOnly ? "xar.physical-status-planning-request/v1" : value.origin() instanceof CommandOrigin.Frontend ? "xar.frontend-planning-request/v1" : value.origin() instanceof CommandOrigin.LifecycleTerminal ? "xar.lifecycle-planning-request/v1" : "xar.reconciliation-planning-request/v1"); row.set("origin", origin(value.origin())); }
        row.set("source", ProposalLifecycleCodec.source(value.source())); row.put("session_id", value.sessionId());
        row.put("operation", value.operation().value()); row.put("deadline", value.deadline().toString()); row.set("arguments_ref", archivedArguments.toJson()); return row;
    }
    public static PlanningReadRequest planningRequest(JsonNode value, OpportunityJson.Obj arguments) {
        StrictJson.require(value instanceof ObjectNode, "planning request object required"); var row = (ObjectNode) value;
        CommandOrigin observed;
        if (row.has("schema")) {
            StrictJson.object(row, Set.of("schema", "origin", "source", "session_id", "operation", "deadline", "arguments_ref"));
            observed = origin(row.get("origin"));
            StrictJson.require(text(row, "schema").equals("xar.frontend-planning-request/v1") && observed instanceof CommandOrigin.Frontend
                    || text(row, "schema").equals("xar.lifecycle-planning-request/v1") && observed instanceof CommandOrigin.LifecycleTerminal
                    || text(row, "schema").equals("xar.reconciliation-planning-request/v1") && observed instanceof CommandOrigin.Reconciliation
                    || text(row, "schema").equals("xar.physical-status-planning-request/v1") && observed instanceof CommandOrigin.PhysicalStatusOnly,
                    "planning request schema requires its exact non-gameplay origin");
        } else {
            StrictJson.object(row, Set.of("before", "source", "session_id", "operation", "deadline", "arguments_ref"));
            observed = new CommandOrigin.Gameplay(ProposalLifecycleCodec.decodeObservation(row.get("before")));
        }
        StrictJson.require(ExactRef.fromJson(row.get("arguments_ref")).bytes() > 0, "actual archived planning arguments required");
        return new PlanningReadRequest(observed, G2Wire.source(row.get("source")), text(row, "session_id"),
                new OperationKey(text(row, "operation")), arguments, Instant.parse(text(row, "deadline")));
    }
    public static ObjectNode readiness(PlanningReadGuard.Readiness value) {
        var row = StrictJson.object();
        if (value instanceof PlanningReadGuard.Gameplay gameplay) {
            row.put("paused", gameplay.paused()); row.put("map_ready", gameplay.mapReady()); row.put("player_alive", gameplay.playerAlive());
        } else if (value instanceof PlanningReadGuard.Frontend) {
            row.put("schema", "xar.frontend-readiness/v1"); row.put("kind", "FRONTEND");
        } else if (value instanceof PlanningReadGuard.LifecycleTerminal) {
            row.put("schema", "xar.lifecycle-terminal-readiness/v1"); row.put("kind", "LIFECYCLE_TERMINAL");
        } else if (value instanceof PlanningReadGuard.PhysicalStatus physical) {
            row.put("schema", "xar.physical-status-readiness/v1"); row.put("kind", "PHYSICAL_STATUS_ONLY");
            row.set("identity", PhysicalStatusIdentityCodec.encode(physical.identity()));
        } else {
            StrictJson.require(value instanceof PlanningReadGuard.Reconciliation, "declared read readiness required");
            row.put("schema", "xar.reconciliation-readiness/v1"); row.put("kind", "RECONCILIATION");
        }
        return row;
    }
    public static PlanningReadGuard.Readiness readiness(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "read readiness object required"); var row = (ObjectNode) value;
        if (row.has("schema")) {
            if (text(row, "schema").equals("xar.physical-status-readiness/v1")) {
                StrictJson.object(row, Set.of("schema", "kind", "identity"));
                StrictJson.require(text(row, "kind").equals("PHYSICAL_STATUS_ONLY"), "exact physical readiness kind required");
                return new PlanningReadGuard.PhysicalStatus(PhysicalStatusIdentityCodec.decode(row.get("identity")));
            }
            StrictJson.object(row, Set.of("schema", "kind"));
            if (text(row, "schema").equals("xar.frontend-readiness/v1") && text(row, "kind").equals("FRONTEND")) return new PlanningReadGuard.Frontend();
            if (text(row, "schema").equals("xar.lifecycle-terminal-readiness/v1") && text(row, "kind").equals("LIFECYCLE_TERMINAL")) return new PlanningReadGuard.LifecycleTerminal();
            StrictJson.require(text(row, "schema").equals("xar.reconciliation-readiness/v1") && text(row, "kind").equals("RECONCILIATION"), "exact non-gameplay readiness phase required");
            return new PlanningReadGuard.Reconciliation();
        }
        StrictJson.object(row, Set.of("paused", "map_ready", "player_alive"));
        return new PlanningReadGuard.Gameplay(bool(row, "paused"), bool(row, "map_ready"), bool(row, "player_alive"));
    }
    public static ObjectNode planningGuard(PlanningReadGuard value) {
        var row = StrictJson.object(); row.set("binding", guard(value.binding()));
        if (value.readiness() instanceof PlanningReadGuard.Gameplay) row.setAll(readiness(value.readiness()));
        else { row.put("schema", value.readiness() instanceof PlanningReadGuard.PhysicalStatus ? "xar.physical-status-planning-guard/v1" : value.readiness() instanceof PlanningReadGuard.Frontend ? "xar.frontend-planning-guard/v1" : value.readiness() instanceof PlanningReadGuard.LifecycleTerminal ? "xar.lifecycle-terminal-planning-guard/v1" : "xar.reconciliation-planning-guard/v1"); row.set("readiness", readiness(value.readiness())); }
        row.put("original_binding_sha256", value.originalBindingSha256()); return row;
    }
    public static PlanningReadGuard planningGuard(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "planning guard object required"); var row = (ObjectNode) value;
        PlanningReadGuard.Readiness ready;
        if (row.has("schema")) {
            StrictJson.object(row, Set.of("schema", "binding", "readiness", "original_binding_sha256"));
            ready = readiness(row.get("readiness"));
            StrictJson.require(text(row, "schema").equals("xar.frontend-planning-guard/v1") && ready instanceof PlanningReadGuard.Frontend
                    || text(row, "schema").equals("xar.lifecycle-terminal-planning-guard/v1") && ready instanceof PlanningReadGuard.LifecycleTerminal
                    || text(row, "schema").equals("xar.reconciliation-planning-guard/v1") && ready instanceof PlanningReadGuard.Reconciliation
                    || text(row, "schema").equals("xar.physical-status-planning-guard/v1") && ready instanceof PlanningReadGuard.PhysicalStatus,
                    "planning guard schema requires its exact origin readiness phase");
        } else {
            StrictJson.object(row, Set.of("binding", "paused", "map_ready", "player_alive", "original_binding_sha256"));
            ready = new PlanningReadGuard.Gameplay(bool(row, "paused"), bool(row, "map_ready"), bool(row, "player_alive"));
        }
        return new PlanningReadGuard(guard(row.get("binding")), ready, text(row, "original_binding_sha256"));
    }
    public static ArrayNode values(List<ExpectedValue> values) {
        var array = StrictJson.object().putArray("values");
        for (ExpectedValue value : values) {
            var row = array.addObject(); row.put("field", value.field().value());
            switch (value) {
                case ExpectedBoolean item -> { row.put("kind", "BOOLEAN"); row.put("value", item.value()); }
                case ExpectedInteger item -> { row.put("kind", "INTEGER"); row.put("value", item.value()); }
                case ExpectedText item -> { row.put("kind", "TEXT"); row.put("value", item.value()); }
                case ExpectedNull ignored -> { row.put("kind", "NULL"); row.putNull("value"); }
                case ExpectedAbsent ignored -> row.put("kind", "ABSENT");
            }
        }
        return array;
    }
    private static BigInteger uint64(ObjectNode row, String key, boolean positive) {
        BigInteger value = new BigInteger(new CrossJsDecimalUInt64(text(row, key)).decimal());
        StrictJson.require(!positive || value.signum() > 0, "positive exact decimal uint64 required"); return value;
    }
    private static String decimal(BigInteger value) { return new CrossJsDecimalUInt64(value.toString()).decimal(); }
    private static boolean bool(ObjectNode row, String key) {
        StrictJson.require(row.get(key) != null && row.get(key).isBoolean(), "actual read readiness boolean required"); return row.get(key).booleanValue();
    }
    private static String text(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
}

