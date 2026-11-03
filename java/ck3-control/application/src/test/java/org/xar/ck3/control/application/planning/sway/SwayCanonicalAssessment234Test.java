package org.xar.ck3.control.application.planning.sway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts;
import org.xar.ck3.control.g2.m6.M6Research;
import org.xar.ck3.control.g2.m6.M6ServiceIntegration;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;

/** New finite DATA checks; no positive private Session, native packet capture or natural Sway claim. */
public final class SwayCanonicalAssessment234Test {
    private static final int MAX = M6SourceProducer.MAX_BYTES;
    private static final String CAUSE = "authored_sway_complete_100_source";
    private static int checks;
    private SwayCanonicalAssessment234Test() { }

    public static void main(String[] args) throws Exception {
        singleProjection(); recovered(); exactSource(); signedRoles(); labelOnly();
        qualifiedCopies(); copiedMismatch(); legacyIsolation(); stopIsNotNatural(); writerDenial();
        System.out.println("PASS scenes=10 checks=" + checks
                + " singleProjectionOnly=true positivePrivateSession=false ordinaryOrigin=false"
                + " naturalSway=false Native=false Game=false");
    }

    private static void singleProjection() {
        ObjectNode resolved = resolved(7, 8);
        // This entry assesses exactly one resolved object and does not reinterpret nested history.
        resolved.put("previous_interventions", "not a campaign traversal input");
        byte[] original = bytes(resolved);
        var result = assess(resolved, M6TerminalSourceComposition.Inputs.unqueried());
        check(result.evidence().episodes().size() == 1, "one current resolved episode");
        check(Arrays.equals(original, result.evidence().originalLedger().bytes()), "derived projection bytes retained");
        check(result.evidence().episodes().getFirst().start().orElseThrow().origin()
                == G2M6Contracts.StartOrigin.UNKNOWN, "canonical presence is not ordinary nomination");
        noAuthority(result);
        System.out.println("PASS singleProjection");
    }

    private static void recovered() {
        ObjectNode row = resolved(7, 8);
        row.putNull("native_receipt");
        ObjectNode observed = (ObjectNode) row.remove("applied_instance_observation");
        observed.put("schema", "xar.ck3.sway-recovered-instance-observation.v1");
        observed.put("source_kind", "matching_active_readback_recovery");
        observed.put("submission_receipt_available", false);
        row.set("recovered_instance_observation", observed);
        var result = assess(row, M6TerminalSourceComposition.Inputs.unqueried());
        check(result.evidence().episodes().getFirst().start().orElseThrow().origin()
                == G2M6Contracts.StartOrigin.RECOVERED_IDENTITY_ONLY, "recovery remains identity-only");
        noAuthority(result);
        System.out.println("PASS recovered");
    }

    private static void exactSource() {
        ObjectNode row = resolved(7, 8); byte[] raw = bytes(row); G2Source source = source(raw);
        reject(() -> M6SourceProducer.assessResolvedProjection(raw, new G2Source(source.machineId(),
                source.observedAtUtc(), source.exactBuild(), new ExactRef("software:wrong-sha", raw.length, "0".repeat(64))),
                M6TerminalSourceComposition.Inputs.unqueried(), new M6Research()), "wrong SHA");
        reject(() -> M6SourceProducer.assessResolvedProjection(raw, new G2Source(source.machineId(),
                source.observedAtUtc(), source.exactBuild(), new ExactRef("software:wrong-size", raw.length + 1L, source.sourceRef().sha256())),
                M6TerminalSourceComposition.Inputs.unqueried(), new M6Research()), "wrong size");
        reject(() -> M6SourceProducer.assessResolvedProjection(raw, new G2Source(source.machineId(),
                source.observedAtUtc(), "not-qualified", source.sourceRef()),
                M6TerminalSourceComposition.Inputs.unqueried(), new M6Research()), "wrong build");
        System.out.println("PASS exactSource");
    }

    private static void signedRoles() {
        var result = assess(resolved(0, Integer.MIN_VALUE), M6TerminalSourceComposition.Inputs.unqueried());
        check(result.evidence().episodes().getFirst().identity().actorCharacterId() == 0, "zero public character valid");
        check(result.evidence().episodes().getFirst().identity().targetCharacterId() == Integer.MIN_VALUE, "signed public minimum valid");
        check(result.evidence().episodes().getFirst().identity().schemeInstanceId() == 2, "scheme uint32 role preserved");
        reject(() -> assess(resolved(-1, 8), M6TerminalSourceComposition.Inputs.unqueried()), "public invalid sentinel");
        System.out.println("PASS signedRoles");
    }

    private static void labelOnly() {
        ObjectNode row = terminalResolved();
        terminal(row).put("terminal_cause_observed", true).put("terminal_cause", CAUSE);
        terminal(row).putObject("causal_observation");
        reject(() -> assess(row, M6TerminalSourceComposition.Inputs.unqueried()), "derived label alone");
        terminal(row).put("terminal_cause", "invented-success");
        reject(() -> assess(row, causalInputs()), "wrong cause key");
        terminal(row).put("terminal_cause", CAUSE).put("instance_terminal_outcome_observed", false);
        reject(() -> assess(row, causalInputs()), "cause cannot label unobserved retained terminal");
        System.out.println("PASS labelOnly");
    }

    private static void qualifiedCopies() {
        ObjectNode row = terminalResolved(); var inputs = causalInputs();
        var neutral = assess(row, inputs);
        check(neutral.compositions().getFirst().cause().isPresent(), "raw copied dynamic relation composes");
        claim(row, neutral);
        byte[] before = bytes(row); var result = assess(row, inputs);
        check(result.compositions().getFirst().cause().isPresent(), "matching copied cause retained");
        check(!result.evidence().episodes().getFirst().terminal().orElseThrow().terminalCauseObserved(), "original typed evidence is not directly relabeled");
        check(result.evidence().episodes().getFirst().terminal().orElseThrow().cause()
                == G2M6Contracts.TerminalCause.TERMINATED_UNATTRIBUTED, "raw evidence stays neutral for assessment enrichment");
        check(StrictJson.parse(result.evidence().episodes().getFirst().originalResolved().bytes(), MAX)
                .at("/terminal_intervention/terminal_cause_observed").booleanValue(), "original derived label not sanitized");
        check(Arrays.equals(before, result.evidence().originalLedger().bytes()), "exact claimed projection retained");
        noAuthority(result);
        System.out.println("PASS qualifiedCopies");
    }

    private static void copiedMismatch() {
        ObjectNode row = terminalResolved(); claim(row, assess(row, causalInputs()));
        ((ObjectNode) terminal(row).get("causal_observation")).put("owner_counter", true);
        reject(() -> assess(row, causalInputs()), "different copied causal observation");
        ObjectNode exact = terminalResolved(); claim(exact, assess(exact, causalInputs()));
        ObjectNode execution = journal(true), termination = journal(false);
        execution.withArray("records").add(parent());
        ObjectNode end = end(); ((ObjectNode) end.get("cause_relation")).put("parent_toast_invocation_id", 34);
        termination.withArray("records").add(end);
        reject(() -> assess(exact, inputs(execution, termination)), "dynamic relation mismatch cannot reuse label");
        System.out.println("PASS copiedMismatch");
    }

    private static void legacyIsolation() {
        ObjectNode row = terminalResolved(); claim(row, assess(row, causalInputs()));
        ObjectNode ledger = StrictJson.object(); ledger.put("schema", "xar.ck3.active-scheme-sway-formal-private.v1");
        ledger.putNull("pending"); ledger.set("resolved", row);
        byte[] raw = bytes(ledger);
        reject(() -> M6SourceProducer.fromClosedLedger(raw, source(raw)), "old strict legacy entry must still reject derived label");
        System.out.println("PASS legacyIsolation");
    }

    private static void stopIsNotNatural() {
        ObjectNode row = terminalResolved(); claim(row, assess(row, causalInputs()));
        row.putObject("stop_intervention").put("status", "software-stop-present");
        var result = assess(row, causalInputs());
        check(result.compositions().getFirst().cause().isPresent(), "copied proof remains separate");
        check(!result.evidence().episodes().getFirst().terminal().orElseThrow().independentNatural(), "typed Stop prevents natural terminal");
        check(result.assessment().episodes().getFirst().missing().contains(G2M6Contracts.Gate.NATURAL_RETAINED_TERMINAL), "natural gate stays missing");
        noAuthority(result);
        System.out.println("PASS stopIsNotNatural");
    }

    private static void writerDenial() throws Exception {
        String denial = "software-denied-writer";
        ContinuityStorePort.Session session = ContinuityStorePort.Session.class.cast(Proxy.newProxyInstance(
                SwayCanonicalAssessment234Test.class.getClassLoader(), new Class<?>[]{ContinuityStorePort.Session.class},
                (proxy, method, values) -> { check(method.getName().equals("requireWriter"), "writer guard is first session access"); throw new IllegalStateException(denial); }));
        SwayCanonicalDomain domain = new SwayCanonicalDomain(Path.of("software-denied-lock"), Path.of("never-read"),
                denied(ActionPorts.OutcomeArchive.class), List.of(new ExactRef("software:source", 1, "0".repeat(64))),
                denied(SwayCanonicalDomain.SchedulerVerifier.class), denied(NativeEffectEvidence.FrameLoader.class));
        try { SwayCanonicalAssessment234.readCurrentResolved(domain, session, "2026-11-03T00:00:00Z", new M6Research());
            throw new AssertionError("denied writer must not export");
        } catch (IllegalStateException expected) { check(denial.equals(expected.getMessage()), "actual existing load writer denial propagates"); }
        System.out.println("PASS writerDenial");
    }

    private static <T> T denied(Class<T> type) {
        return type.cast(Proxy.newProxyInstance(SwayCanonicalAssessment234Test.class.getClassLoader(),
                new Class<?>[]{type}, (proxy, method, values) -> { throw new AssertionError("no archive/scheduler/native loader calls permitted"); }));
    }
    private static void claim(ObjectNode row, M6ServiceIntegration.Result result) {
        terminal(row).put("terminal_cause_observed", true).put("terminal_cause", CAUSE);
        terminal(row).set("causal_observation", StrictJson.parse(result.compositions().getFirst().cause().orElseThrow().observation().bytes(), MAX));
    }
    private static void noAuthority(M6ServiceIntegration.Result result) {
        check(result.assessment().episodes().getFirst().missing().contains(G2M6Contracts.Gate.ORDINARY_START), "ordinary origin not proved by projection");
        check(!result.assessment().evidencePacketReady() && !result.assessment().schemeComplete()
                && !result.assessment().wholeM6Complete(), "finite projection does not complete M6");
        check(!result.actionAuthorized() && !result.ledgerCommitted() && !result.requestRetried()
                && !result.assessment().grantsSubmissionAuthority(), "no authority/writer/retry flags");
    }
    private static M6ServiceIntegration.Result assess(ObjectNode row, M6TerminalSourceComposition.Inputs inputs) {
        byte[] raw = bytes(row); return M6SourceProducer.assessResolvedProjection(raw, source(raw), inputs, new M6Research());
    }
    private static byte[] bytes(JsonNode row) { return StrictJson.canonical(row, MAX); }
    private static G2Source source(byte[] raw) {
        return new G2Source("software-m6-owner", "2026-11-03T00:00:00Z", M6SourceProducer.BUILD,
                new ExactRef("software:derived-current-resolved", raw.length, ActionCodec.sha256(raw)));
    }
    private static void check(boolean value, String reason) { checks++; if (!value) throw new AssertionError(reason); }
    private static void reject(Runnable action, String reason) {
        try { action.run(); throw new AssertionError("must reject: " + reason); }
        catch (IllegalArgumentException expected) { checks++; }
    }
    private static ObjectNode resolved(long actor, long target) {
        ObjectNode row = identity(actor, target, true); row.remove("scheme_instance_id"); row.remove("scheme_instance_generation");
        row.put("status", "applied").put("postcondition_verified", true).put("post_native_revision", 3).put("post_date_raw", 100).put("next_turn_consumed", false);
        ObjectNode receipt = identity(actor, target, true); normalized(receipt);
        receipt.put("schema", "active-scheme-sway-formal-private-v1").put("stage", "applied").put("postcondition_verified", true); row.set("native_receipt", receipt);
        ObjectNode applied = identity(actor, target, true); applied.put("schema", "xar.ck3.sway-applied-instance-observation.v1");
        applied.put("source_kind", "independent_active_read_after_native_receipt");
        applied.putObject("active_instance").put("scheme_instance_id", 2).put("scheme_instance_generation", 0).put("target_character_id", target)
                .put("progress", 0).put("progress_goal", 100).put("is_exposed", false).put("is_frozen", false);
        ObjectNode read = StrictJson.object(); normalized(read); read.put("schema", "active-scheme-sway-private-read-v1").put("snapshot_revision", 4).put("date_raw", 100)
                .put("queried_revision", 4).put("capture_epoch", 2).put("container_generation", new BigInteger("18446744073709551001"))
                .put("queried_native_revision", 4).put("queried_snapshot_id", "native:4").put("post_snapshot_id", "native:4");
        applied.set("source_read", read); row.set("applied_instance_observation", applied); return row;
    }
    private static ObjectNode terminalResolved() {
        ObjectNode row = resolved(7, 8), terminal = identity(7, 8, true); normalized(terminal);
        terminal.put("source_native_revision", 10).put("source_date_raw", 300).put("instance_terminal_outcome_observed", true)
                .put("native_status_key", "terminated_unattributed").put("terminal_cause_observed", false).put("terminal_cause", "unknown").put("next_turn_consumed", false);
        ObjectNode completion = identity(7, 8, false); build(completion);
        completion.put("schema", "xar.ck3.sway_completion.v1").put("snapshot_revision", 10).put("date_raw", 300).put("available", true)
                .put("instance_present", true).put("instance_source_observed", true).put("storage_slot_reused", false).put("exact_instance_join_ready", true)
                .put("native_status_observed", true).put("native_status_raw", 1).put("native_owner_raw", 0xffff_ffffL).put("native_terminal_state_observed", true);
        terminal.set("native_observation", completion); row.set("terminal_intervention", terminal); return row;
    }
    private static ObjectNode terminal(ObjectNode row) { return (ObjectNode) row.get("terminal_intervention"); }
    private static ObjectNode identity(long actor, long target, boolean action) {
        ObjectNode row = StrictJson.object(); if (action) row.put("action_id", "sway-0123456789abcdef0123456789abcdef");
        row.put("actor_character_id", actor).put("target_character_id", target).put("scheme_instance_id", 2).put("scheme_instance_generation", 0); return row;
    }
    private static void normalized(ObjectNode row) { row.put("exact_ck3_build", M6SourceProducer.BUILD).put("exe_sha256", M6SourceProducer.EXE); }
    private static void build(ObjectNode row) { row.put("build_version", M6SourceProducer.BUILD).put("executable_sha256", M6SourceProducer.EXE); }
    private static void dynamic(ObjectNode row) { row.put("observer_session_identity", new BigInteger("18446744073709551001")).put("owner_thread_id", 55); }
    private static ObjectNode journal(boolean execute) {
        ObjectNode row = identity(7, 8, false); build(row);
        row.put("schema", execute ? "xar.ck3.sway-completion-execution.v1" : "xar.ck3.sway-completion-termination.v1")
                .put("available", true).put("retention_gap", false).put("snapshot_revision", 11).put("date_raw", 301); row.putArray("records"); return row;
    }
    private static ObjectNode parent() {
        ObjectNode row = identity(7, 8, false); row.put("source_branch", CAUSE).put("sequence", 21).put("date_raw", 300);
        row.putNull("stock_event").putNull("phase_result").put("executing_input_observed", true).put("exact_scope_join_ready", true)
                .put("message_enqueue_observed", false).put("material_effect_observed", false).put("native_terminal_state_observed", false);
        ObjectNode call = row.putObject("native_invocation"); dynamic(call); call.put("toast_invocation_id", 33).put("branch_source_sequence", 21);
        ObjectNode scopes = call.putObject("copied_scopes");
        for (String name : List.of("root", "owner", "target", "scheme")) scopes.putObject(name).put("type", name.equals("scheme") ? 9 : 4)
                .put("subtype", 0).put("reserved", 0).put("payload", name.equals("scheme") ? 2 : name.equals("target") ? 8 : 7);
        return row;
    }
    private static ObjectNode end() {
        ObjectNode row = identity(7, 8, false); row.put("source_class", "authored_end_scheme_false_execute").put("date_raw", 300)
                .put("pre_status", 0).put("post_status", 1).put("pre_owner", 7).put("post_owner", 0xffff_ffffL);
        for (String flag : List.of("executing_source_observed", "post_read_succeeded", "post_instance_present", "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed", "native_terminal_transition_observed")) row.put(flag, true);
        row.put("post_storage_slot_reused", false).put("input_root_scope_kind", 9);
        ObjectNode call = row.putObject("native_invocation"); dynamic(call); call.put("original_invocation_id", 44).put("original_rva", 0x2d11b30)
                .put("incoming_return_address_observed", true).put("caller_return_rva", 0x2d67c04).put("original_forwarded_once", true).put("original_returned", true)
                .put("pre_frame_observed", true).put("pre_date_raw", 300).put("post_frame_observed", true).put("post_date_raw", 300);
        ObjectNode relation = identity(7, 8, false); dynamic(relation);
        relation.put("source_contract", "sway_child_end_causal_path_12004_v1").put("source_contract_version", 1).put("relationship_observed", true)
                .put("branch_source_sequence", 21).put("parent_toast_invocation_id", 33).put("end_original_invocation_id", 44).put("end_original_rva", 0x2d11b30)
                .put("native_returns_observed", true).put("native_returns_truncated", false);
        relation.putArray("native_return_rvas").add(0x2d67c04).add(0x3766146).add(0x2cc93cc); row.set("cause_relation", relation); return row;
    }
    private static M6TerminalSourceComposition.Inputs causalInputs() {
        ObjectNode execute = journal(true), terminate = journal(false); execute.withArray("records").add(parent()); terminate.withArray("records").add(end());
        return inputs(execute, terminate);
    }
    private static M6TerminalSourceComposition.Inputs inputs(ObjectNode execute, ObjectNode terminate) {
        return new M6TerminalSourceComposition.Inputs(Optional.empty(), Optional.of(ProjectionJson.object(bytes(execute), MAX)),
                Optional.of(ProjectionJson.object(bytes(terminate), MAX)), Optional.empty());
    }
}
