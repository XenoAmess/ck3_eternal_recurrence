package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** New SOFTWARE copied wrapper rows. No actual native return, causal link or Root permit is supplied. */
public final class SwayWrapperOwner212Test {
    private static final BigInteger REV = new BigInteger("9223372036854775815");
    private static final int QUERY_DATE = 53290000, PRE_DATE = 53280000, POST_DATE = 53280024;
    private static final long SCHEME = 16777227;

    @Test void signedWrapperOwnerKeepsUnattributedEventAndColdFollowing() {
        for (long actor : new long[]{-2, Integer.MIN_VALUE, 0, Integer.MAX_VALUE}) {
            Episode episode = episode(actor); ObservationIdentity source = source(actor, REV, QUERY_DATE);
            for (long postOwner : new long[]{raw(actor), 0xffff_ffffL}) {
                ProjectionJson termination = json(journal(episode, end(episode, postOwner)));
                var result = M6TerminalSourceComposition.compose(episode, inputs(termination));
                assertTrue(result.wrapperEnd().isPresent(), "matching raw owner must retain signed actor wrapper return");
                assertEquals(M6TerminalSourceComposition.EndSource.RETAINED_WRAPPER_RETURN, result.wrapperEnd().orElseThrow().source());
                assertTrue(result.cause().isEmpty()); assertTrue(result.material().isEmpty()); assertTrue(result.current().isEmpty());
                assertFalse(result.actionAuthorized()); assertFalse(result.ledgerCommitted()); assertFalse(result.requestRetried());
                var state = observe(episode, source, termination);
                var terminal = state.terminal().orElseThrow(); assertEquals(SwayLifecycle.TerminalKind.WRAPPER_RETURN, terminal.kind());
                assertFalse(terminal.terminalCauseObserved()); assertEquals(Optional.of(POST_DATE), terminal.eventDateRaw());
                assertEquals(BigInteger.valueOf(QUERY_DATE), terminal.source().frame().identity().dateRaw());
                assertEquals(actor, state.identity().actorCharacterId()); assertTrue(state.material().isEmpty()); assertTrue(state.latest().isEmpty());
                assertEquals(state, SwayLifecycle.decode(SwayLifecycle.encode(state)));
                var after = SwayLifecycle.consumeFollowing(state, source(actor, REV.add(BigInteger.ONE), QUERY_DATE + 24));
                assertTrue(after.terminal().orElseThrow().consumption().nextTurnConsumed());
                assertEquals(after, SwayLifecycle.decode(SwayLifecycle.encode(after)));
            }
        }
    }

    @Test void mismatchedRawOwnerStatusReuseAndMissingFactsCannotProduceWrapperTerminal() {
        Episode episode = episode(-2); ObservationIdentity source = source(-2, REV, QUERY_DATE);
        for (String mutation : List.of("pre-owner", "post-owner", "pre-status", "post-status", "reuse", "post-read", "instance", "join", "state", "transition", "post-frame")) {
            ObjectNode row = end(episode, 0xffff_ffffL);
            switch (mutation) {
                case "pre-owner" -> row.put("pre_owner", 0);
                case "post-owner" -> row.put("post_owner", 1);
                case "pre-status" -> row.put("pre_status", 1);
                case "post-status" -> row.put("post_status", 0);
                case "reuse" -> row.put("post_storage_slot_reused", true);
                case "post-read" -> row.put("post_read_succeeded", false);
                case "instance" -> row.put("post_instance_present", false);
                case "join" -> row.put("post_exact_instance_join_ready", false);
                case "state" -> row.put("native_terminal_state_observed", false);
                case "transition" -> row.put("native_terminal_transition_observed", false);
                case "post-frame" -> { ((ObjectNode)row.get("native_invocation")).put("post_frame_observed", false).putNull("post_date_raw"); }
                default -> throw new AssertionError(mutation);
            }
            var state = observe(episode, source, json(journal(episode, row)));
            assertTrue(state.terminal().isEmpty(), mutation); assertTrue(state.material().isEmpty(), mutation);
        }
    }

    @Test void malformedPrivateRawTokensAndUnsignedPublicAliasesFailAtRealSourceValidation() {
        Episode episode = episode(-2); ObservationIdentity source = source(-2, REV, QUERY_DATE);
        for (String field : List.of("pre_owner", "post_owner")) {
            for (String token : List.of("-2", "4294967296", "\"4294967294\"", "true", "0.0", "null")) {
                ObjectNode row = end(episode, 0xffff_ffffL); row.put(field, "wrapper212-token");
                ProjectionJson wire = tokenWire(journal(episode, row), token);
                assertThrows(IllegalArgumentException.class, () -> observe(episode, source, wire), field + ":" + token);
            }
        }
        ObjectNode alias = journal(episode, end(episode, 0xffff_ffffL)); alias.put("actor_character_id", 4294967294L);
        assertThrows(IllegalArgumentException.class, () -> observe(episode, source, json(alias)));
        ObjectNode generation = end(episode, 0xffff_ffffL); generation.put("scheme_instance_generation", 0);
        assertThrows(IllegalArgumentException.class, () -> observe(episode, source, json(journal(episode, generation))));
        ObjectNode query = journal(episode, end(episode, 0xffff_ffffL)); query.put("snapshot_revision", REV.subtract(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> observe(episode, source, json(query)));
    }

    @Test void nativeOriginalReturnAndFrameRequirementsRemainMandatoryWithoutCausalInput() {
        Episode episode = episode(-2); ObservationIdentity source = source(-2, REV, QUERY_DATE);
        for (String field : List.of("original_forwarded_once", "original_returned", "pre_frame_observed")) {
            ObjectNode row = end(episode, 0xffff_ffffL); ((ObjectNode)row.get("native_invocation")).put(field, false);
            assertThrows(IllegalArgumentException.class, () -> observe(episode, source, json(journal(episode, row))), field);
        }
        ObjectNode rva = end(episode, 0xffff_ffffL); ((ObjectNode)rva.get("native_invocation")).put("original_rva", 1);
        assertThrows(IllegalArgumentException.class, () -> observe(episode, source, json(journal(episode, rva))));
    }

    private static SwayLifecycle.State observe(Episode episode, ObservationIdentity source, ProjectionJson termination) {
        return SwayLifecycle.observe(SwayLifecycle.empty(episode.identity(), source), episode, inputs(termination), source);
    }
    private static M6TerminalSourceComposition.Inputs inputs(ProjectionJson termination) {
        return new M6TerminalSourceComposition.Inputs(Optional.empty(), Optional.empty(), Optional.of(termination), Optional.empty());
    }
    private static Episode episode(long actor) {
        long target = actor == 0 ? -2 : 0; Identity identity = new Identity("software-wrapper212", actor, target, SCHEME, 1);
        ObjectNode resolved = StrictJson.object(); resolved.put("status", "applied"); resolved.put("postcondition_verified", true); resolved.put("action_id", identity.actionId());
        resolved.put("actor_character_id", actor); resolved.put("target_character_id", target);
        ObjectNode receipt = resolved.putObject("native_receipt"); receipt.put("schema", "active-scheme-sway-formal-private-v1"); receipt.put("stage", "applied");
        receipt.put("postcondition_verified", true); receipt.put("action_id", identity.actionId()); receipt.put("scheme_instance_id", SCHEME); receipt.put("scheme_instance_generation", 1); build(receipt);
        return new Episode(identity, Optional.empty(), Optional.empty(), Optional.empty(), json(resolved));
    }
    private static ObjectNode end(Episode episode, long postOwner) {
        ObjectNode row = identity(episode); row.put("sequence", 1); row.put("source_class", "end_scheme_command_execute"); row.put("date_raw", PRE_DATE);
        row.put("input_root_scope_kind", 9); row.put("pre_status", 0); row.put("pre_owner", raw(episode.identity().actorCharacterId()));
        row.put("post_status", 1); row.put("post_owner", postOwner); row.put("post_storage_slot_reused", false); row.put("material_effect_observed", false); row.putNull("specific_invalidation_reason");
        for (String flag : List.of("executing_source_observed", "post_read_succeeded", "post_instance_present", "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed", "native_terminal_transition_observed")) row.put(flag, true);
        ObjectNode invocation = row.putObject("native_invocation"); invocation.put("observer_session_identity", new BigInteger("18446744073709551001")); invocation.put("owner_thread_id", 55);
        invocation.put("original_invocation_id", 44); invocation.put("original_rva", 0x299c320); invocation.put("incoming_return_address_observed", false); invocation.put("caller_return_rva", 0);
        invocation.put("original_forwarded_once", true); invocation.put("original_returned", true); invocation.put("pre_frame_observed", true); invocation.put("pre_date_raw", PRE_DATE);
        invocation.put("post_frame_observed", true); invocation.put("post_date_raw", POST_DATE); row.putNull("cause_relation"); return row;
    }
    private static ObjectNode journal(Episode episode, ObjectNode row) {
        ObjectNode journal = identity(episode); build(journal); journal.put("schema", "xar.ck3.sway-completion-termination.v1"); journal.put("available", true); journal.put("retention_gap", false);
        journal.put("snapshot_revision", REV); journal.put("date_raw", QUERY_DATE); journal.put("earliest_sequence", 1); journal.put("latest_sequence", 1); journal.putArray("records").add(row); return journal;
    }
    private static ObjectNode identity(Episode episode) { ObjectNode row = M6TerminalSourceComposition.identityJson(episode.identity()); row.remove("action_id"); return row; }
    private static ObservationIdentity source(long actor, BigInteger revision, int date) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), revision, BigInteger.valueOf(date)), "software212:" + revision, revision, "software212");
        return new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(8000, new PythonOnlyUInt64(new BigInteger("134371234567890123"))), frame, 1);
    }
    private static long raw(long actor) { return Integer.toUnsignedLong(Math.toIntExact(actor)); }
    private static void build(ObjectNode row) { row.put("build_version", M6SourceProducer.BUILD); row.put("executable_sha256", M6SourceProducer.EXE); row.put("exact_ck3_build", M6SourceProducer.BUILD); row.put("exe_sha256", M6SourceProducer.EXE); }
    private static ProjectionJson tokenWire(ObjectNode row, String token) { String wire = new String(StrictJson.canonical(row, M6SourceProducer.MAX_BYTES), StandardCharsets.UTF_8).replace("\"wrapper212-token\"", token); return ProjectionJson.object(wire.getBytes(StandardCharsets.UTF_8), M6SourceProducer.MAX_BYTES); }
    private static ProjectionJson json(JsonNode value) { return ProjectionJson.object(StrictJson.canonical(value, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES); }
}
