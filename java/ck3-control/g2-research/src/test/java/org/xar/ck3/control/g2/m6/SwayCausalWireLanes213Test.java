package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;

/** Synthetic copied producer rows only; neither a Native observation nor a private Root permit. */
public final class SwayCausalWireLanes213Test {
    private static final long SCHEME = 0xff00_0002L;
    private static final int DATE = 53280000;
    private static final BigInteger SESSION = new BigInteger("18446744073709551001");
    private static final BigInteger BRANCH = new BigInteger("9007199254740993");
    private record Fixture(Episode episode, ObjectNode execution, ObjectNode termination) { }

    @Test void actualProducerLanesRetainFullSignedIdentitiesThroughCopiedCause() {
        for (long[] pair : new long[][]{{-2, Integer.MIN_VALUE}, {Integer.MIN_VALUE, 0}, {0, Integer.MAX_VALUE}, {Integer.MAX_VALUE, -2}, {41, 73}}) {
            Fixture f = fixture(pair[0], pair[1]);
            byte[] original = f.episode().originalResolved().bytes();
            ProjectionJson ex = json(f.execution()), end = json(f.termination());
            assertArrayEquals(ex.bytes(), M6TerminalSourceComposition.validateExecution(ex, f.episode().identity()).bytes());
            assertArrayEquals(end.bytes(), M6TerminalSourceComposition.validateTermination(end, f.episode().identity()).bytes());
            var result = compose(f);
            assertTrue(result.cause().isPresent(), "exact signed/raw lane identity must retain copied dynamic cause");
            JsonNode cause = parse(result.cause().orElseThrow().observation());
            assertEquals(pair[0], cause.get("actor_character_id").longValue());
            assertEquals(pair[1], cause.get("target_character_id").longValue());
            assertArrayEquals(StrictJson.canonical(f.execution().at("/records/0"), M6SourceProducer.MAX_BYTES), StrictJson.canonical(cause.get("execution_record"), M6SourceProducer.MAX_BYTES));
            assertArrayEquals(StrictJson.canonical(f.termination().at("/records/0"), M6SourceProducer.MAX_BYTES), StrictJson.canonical(cause.get("termination_record"), M6SourceProducer.MAX_BYTES));
            assertEquals(raw(pair[0]), cause.at("/execution_record/actor_character_id").longValue());
            assertEquals(raw(pair[1]), cause.at("/termination_record/cause_relation/target_character_id").longValue());
            assertTrue(result.wrapperEnd().isPresent()); assertTrue(result.material().isEmpty()); assertTrue(result.current().isEmpty());
            assertFalse(cause.get("material_effect_observed").booleanValue());
            assertFalse(result.actionAuthorized()); assertFalse(result.ledgerCommitted()); assertFalse(result.requestRetried());
            assertArrayEquals(original, f.episode().originalResolved().bytes());
        }
    }

    @Test void rawAndSignedLanesRejectAliasesMalformedTokensAndDifferentFullIdentities() {
        for (String token : List.of("-2", "4294967295", "4294967296", "4294967294.0", "\"4294967294\"", "true", "null")) {
            Fixture f = fixture(-2, Integer.MIN_VALUE); f.execution().put("actor_character_id", "lane213-token");
            assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateExecution(tokenWire(f.execution(), token), f.episode().identity()), token);
            Fixture relation = fixture(-2, Integer.MIN_VALUE); node(relation.termination(), "/records/0/cause_relation").put("actor_character_id", "lane213-token");
            assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateTermination(tokenWire(relation.termination(), token), relation.episode().identity()), token);
        }
        for (String token : List.of("4294967294", "-1", "-2147483649", "2147483648", "-2.0", "\"-2\"", "false", "null")) {
            Fixture f = fixture(-2, Integer.MIN_VALUE); f.termination().put("actor_character_id", "lane213-token");
            assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateTermination(tokenWire(f.termination(), token), f.episode().identity()), token);
        }
        Fixture different = fixture(-2, Integer.MIN_VALUE); different.execution().put("actor_character_id", 7);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateExecution(json(different.execution()), different.episode().identity()));
        Fixture missing = fixture(-2, Integer.MIN_VALUE); node(missing.execution(), "/records/0").remove("target_character_id");
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateExecution(json(missing.execution()), missing.episode().identity()));
        Fixture differentRelation = fixture(-2, Integer.MIN_VALUE); node(differentRelation.termination(), "/records/0/cause_relation").put("actor_character_id", 7);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateTermination(json(differentRelation.termination()), differentRelation.episode().identity()));
    }

    @Test void dynamicKeysDatesAndTransitionFactsCannotBorrowTheLaneConversion() {
        for (String mutation : List.of("session", "thread", "parent", "branch", "pre-date", "post-date", "reuse", "retention")) {
            Fixture f = fixture(-2, Integer.MIN_VALUE);
            ObjectNode end = node(f.termination(), "/records/0"), inv = node(end, "/native_invocation"), relation = node(end, "/cause_relation");
            switch (mutation) {
                case "session" -> { inv.put("observer_session_identity", 22); relation.put("observer_session_identity", 22); }
                case "thread" -> { inv.put("owner_thread_id", 56); relation.put("owner_thread_id", 56); }
                case "parent" -> relation.put("parent_toast_invocation_id", 77);
                case "branch" -> relation.put("branch_source_sequence", BRANCH.add(BigInteger.ONE));
                case "pre-date" -> { end.put("date_raw", DATE + 24); inv.put("pre_date_raw", DATE + 24).put("post_date_raw", DATE + 24); }
                case "post-date" -> inv.put("post_date_raw", DATE + 24);
                case "reuse" -> end.put("post_storage_slot_reused", true);
                case "retention" -> f.execution().put("retention_gap", true);
                default -> throw new AssertionError(mutation);
            }
            M6TerminalSourceComposition.validateExecution(json(f.execution()), f.episode().identity());
            M6TerminalSourceComposition.validateTermination(json(f.termination()), f.episode().identity());
            assertTrue(compose(f).cause().isEmpty(), mutation);
        }
    }

    @Test void causalReturnOriginalScopeAndUnsignedSchemeGatesRemainExact() {
        for (String mutation : List.of("returns-order", "original-id", "original-rva", "scope", "generation", "scheme")) {
            Fixture f = fixture(-2, Integer.MIN_VALUE); ObjectNode relation = node(f.termination(), "/records/0/cause_relation");
            switch (mutation) {
                case "returns-order" -> { relation.putArray("native_return_rvas").add(0x2d67c04).add(0x2cc93cc).add(0x3766146); }
                case "original-id" -> relation.put("end_original_invocation_id", 45);
                case "original-rva" -> relation.put("end_original_rva", 0x2d11b30);
                case "scope" -> node(f.execution(), "/records/0/native_invocation/copied_scopes/target").put("payload", 123);
                case "generation" -> relation.put("scheme_instance_generation", 0);
                case "scheme" -> relation.put("scheme_instance_id", 0xff00_0003L);
                default -> throw new AssertionError(mutation);
            }
            if (mutation.equals("scope")) assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateExecution(json(f.execution()), f.episode().identity()), mutation);
            else assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateTermination(json(f.termination()), f.episode().identity()), mutation);
        }
    }

    private static Fixture fixture(long actor, long target) {
        Identity id = new Identity("software-causal-lanes213", actor, target, SCHEME, 255);
        ObjectNode resolved = StrictJson.object().put("status", "applied").put("postcondition_verified", true).put("action_id", id.actionId())
                .put("actor_character_id", actor).put("target_character_id", target);
        ObjectNode receipt = resolved.putObject("native_receipt").put("schema", "active-scheme-sway-formal-private-v1").put("stage", "applied")
                .put("postcondition_verified", true).put("action_id", id.actionId()).put("scheme_instance_id", SCHEME).put("scheme_instance_generation", 255); build(receipt);
        Episode episode = new Episode(id, Optional.empty(), Optional.empty(), Optional.empty(), json(resolved));
        ObjectNode ex = journal(id, true), termination = journal(id, false);
        ObjectNode parent = identity(id, true).put("sequence", BRANCH).put("date_raw", DATE).put("source_branch", M6TerminalSourceComposition.COMPLETE)
                .putNull("stock_event").putNull("phase_result").put("executing_input_observed", true).put("exact_scope_join_ready", true)
                .put("message_enqueue_observed", false).put("material_effect_observed", false).put("native_terminal_state_observed", false);
        ObjectNode invocation = parent.putObject("native_invocation").put("observer_session_identity", SESSION).put("owner_thread_id", 55)
                .put("toast_invocation_id", 33).put("branch_source_sequence", BRANCH);
        ObjectNode scopes = invocation.putObject("copied_scopes");
        scope(scopes, "root", 4, raw(actor)); scope(scopes, "owner", 4, raw(actor)); scope(scopes, "target", 4, raw(target)); scope(scopes, "scheme", 9, SCHEME);
        ex.putArray("records").add(parent);
        ObjectNode end = identity(id, false).put("sequence", BRANCH).put("date_raw", DATE).put("source_class", "authored_end_scheme_true_execute")
                .put("input_root_scope_kind", 9).put("pre_status", 0).put("pre_owner", raw(actor)).put("post_status", 1).put("post_owner", 0xffff_ffffL)
                .put("post_storage_slot_reused", false).put("material_effect_observed", false).putNull("specific_invalidation_reason");
        for (String flag : List.of("executing_source_observed", "post_read_succeeded", "post_instance_present", "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed", "native_terminal_transition_observed")) end.put(flag, true);
        end.putObject("native_invocation").put("observer_session_identity", SESSION).put("owner_thread_id", 55).put("original_invocation_id", 44)
                .put("original_rva", 0x2d11ad0).put("incoming_return_address_observed", true).put("caller_return_rva", 0x2d67c04)
                .put("original_forwarded_once", true).put("original_returned", true).put("pre_frame_observed", true).put("pre_date_raw", DATE)
                .put("post_frame_observed", true).put("post_date_raw", DATE);
        ObjectNode relation = identity(id, true).put("source_contract", "sway_child_end_causal_path_12004_v1").put("source_contract_version", 1)
                .put("relationship_observed", true).put("observer_session_identity", SESSION).put("owner_thread_id", 55).put("branch_source_sequence", BRANCH)
                .put("parent_toast_invocation_id", 33).put("end_original_invocation_id", 44).put("end_original_rva", 0x2d11ad0)
                .put("native_returns_observed", true).put("native_returns_truncated", false);
        relation.putArray("native_return_rvas").add(0x2d67c04).add(0x3766146).add(0x2cc93cc); end.set("cause_relation", relation);
        termination.putArray("records").add(end); return new Fixture(episode, ex, termination);
    }
    private static ObjectNode journal(Identity id, boolean execution) {
        ObjectNode row = identity(id, execution).put("schema", execution ? "xar.ck3.sway-completion-execution.v1" : "xar.ck3.sway-completion-termination.v1")
                .put("available", true).put("retention_gap", false).put("read_only", true).put("snapshot_revision", BRANCH.add(BigInteger.TEN)).put("date_raw", DATE + 48)
                .put("earliest_sequence", BRANCH).put("latest_sequence", BRANCH);
        build(row); return row;
    }
    private static ObjectNode identity(Identity id, boolean raw) { return StrictJson.object().put("actor_character_id", raw ? raw(id.actorCharacterId()) : id.actorCharacterId())
            .put("target_character_id", raw ? raw(id.targetCharacterId()) : id.targetCharacterId()).put("scheme_instance_id", SCHEME).put("scheme_instance_generation", 255); }
    private static void scope(ObjectNode scopes, String name, int type, long low) { scopes.putObject(name).put("type", type).put("subtype", 0).put("reserved", 0)
            .put("payload", new BigInteger("16045690981097406464").add(BigInteger.valueOf(low))); }
    private static M6TerminalSourceComposition.Result compose(Fixture f) { return M6TerminalSourceComposition.compose(f.episode(), new M6TerminalSourceComposition.Inputs(Optional.empty(), Optional.of(json(f.execution())), Optional.of(json(f.termination())), Optional.empty())); }
    private static ObjectNode node(JsonNode root, String path) { return (ObjectNode) root.at(path); }
    private static long raw(long value) { return Integer.toUnsignedLong(Math.toIntExact(value)); }
    private static void build(ObjectNode row) { row.put("build_version", M6SourceProducer.BUILD).put("executable_sha256", M6SourceProducer.EXE).put("exact_ck3_build", M6SourceProducer.BUILD).put("exe_sha256", M6SourceProducer.EXE); }
    private static ProjectionJson tokenWire(ObjectNode row, String token) { String wire = new String(StrictJson.canonical(row, M6SourceProducer.MAX_BYTES), StandardCharsets.UTF_8).replace("\"lane213-token\"", token); return ProjectionJson.object(wire.getBytes(StandardCharsets.UTF_8), M6SourceProducer.MAX_BYTES); }
    private static JsonNode parse(ProjectionJson value) { return StrictJson.parse(value.bytes(), M6SourceProducer.MAX_BYTES); }
    private static ProjectionJson json(JsonNode value) { return ProjectionJson.object(StrictJson.canonical(value, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES); }
}
