package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;

/** Actionless public reads use the same complete parser as retained ordinary Sway episodes. */
final class NativeSwaySubjectJournalTest {
    private static final NativeSubject SUBJECT = new NativeSubject(41, 73, 0x0800_0102L, 8);
    private static final BigInteger SEQUENCE = new BigInteger("9007199254740993");

    @Test void actionlessExecutionAndTerminationShareTheExistingIdentityParserWithoutFakeAction() {
        Identity first = new Identity("canonical-first", 41, 73, SUBJECT.schemeInstanceId(), 8);
        Identity second = new Identity("canonical-second", 41, 73, SUBJECT.schemeInstanceId(), 8);
        assertEquals(SUBJECT, first.nativeSubject()); assertEquals(SUBJECT, second.nativeSubject());
        for (boolean execution : new boolean[]{true, false}) {
            ProjectionJson raw = json(journal(execution, SUBJECT));
            ProjectionJson direct = validate(raw, SUBJECT, execution);
            ProjectionJson ordinary = execution
                    ? M6TerminalSourceComposition.validateExecution(raw, first)
                    : M6TerminalSourceComposition.validateTermination(raw, first);
            ProjectionJson anotherOrigin = execution
                    ? M6TerminalSourceComposition.validateExecution(raw, second)
                    : M6TerminalSourceComposition.validateTermination(raw, second);
            assertArrayEquals(direct.bytes(), ordinary.bytes()); assertArrayEquals(direct.bytes(), anotherOrigin.bytes());
            var decoded = StrictJson.parse(direct.bytes());
            assertFalse(decoded.has("action_id")); assertFalse(decoded.at("/records/0").has("action_id"));
            assertEquals(SEQUENCE, decoded.at("/records/0/sequence").bigIntegerValue());
            assertEquals(8, decoded.get("scheme_instance_generation").intValue());
        }
    }

    @Test void completeNativeIdentityRecordTypesAndFieldsRemainMandatoryOnBothPublicPlanes() {
        for (boolean execution : new boolean[]{true, false}) {
            ObjectNode generation = journal(execution, SUBJECT);
            ((ObjectNode) generation.at("/records/0")).put("scheme_instance_generation", 9);
            assertThrows(IllegalArgumentException.class, () -> validate(json(generation), SUBJECT, execution));
            ObjectNode actor = journal(execution, SUBJECT); actor.put("actor_character_id", 41.0);
            assertThrows(IllegalArgumentException.class, () -> validate(json(actor), SUBJECT, execution));
            ObjectNode sequence = journal(execution, SUBJECT);
            ((ObjectNode) sequence.at("/records/0")).put("sequence", true);
            assertThrows(IllegalArgumentException.class, () -> validate(json(sequence), SUBJECT, execution));
            ObjectNode missing = journal(execution, SUBJECT);
            ((ObjectNode) missing.at("/records/0")).remove("target_character_id");
            assertThrows(IllegalArgumentException.class, () -> validate(json(missing), SUBJECT, execution));
            NativeSubject another = new NativeSubject(41, 74, SUBJECT.schemeInstanceId(), 8);
            assertThrows(IllegalArgumentException.class, () -> validate(json(journal(execution, SUBJECT)), another, execution));
        }
    }

    @Test void zeroGenerationIsRealButSentinelWrongGenerationAndAliasedCharactersAreRejected() {
        NativeSubject zero = new NativeSubject(41, 73, 0, 0);
        assertEquals(0, StrictJson.parse(validate(json(journal(true, zero)), zero, true).bytes())
                .get("scheme_instance_id").intValue());
        assertThrows(IllegalArgumentException.class, () -> new NativeSubject(41, 73, 0xffff_ffffL, 255));
        assertThrows(IllegalArgumentException.class, () -> new NativeSubject(41, 73, 0x0800_0102L, 7));
        assertThrows(IllegalArgumentException.class, () -> new NativeSubject(41, 41, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new NativeSubject(0, 73, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new Identity("", 41, 73, 0, 0));
    }

    private static ProjectionJson validate(ProjectionJson raw, NativeSubject subject, boolean execution) {
        return execution ? M6TerminalSourceComposition.validateExecution(raw, subject)
                : M6TerminalSourceComposition.validateTermination(raw, subject);
    }
    private static ProjectionJson json(ObjectNode row) {
        return ProjectionJson.object(StrictJson.canonical(row, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES);
    }
    private static ObjectNode identity(NativeSubject subject) {
        return StrictJson.object().put("actor_character_id", subject.actorCharacterId())
                .put("target_character_id", subject.targetCharacterId()).put("scheme_instance_id", subject.schemeInstanceId())
                .put("scheme_instance_generation", subject.schemeInstanceGeneration());
    }
    private static ObjectNode journal(boolean execution, NativeSubject subject) {
        ObjectNode result = identity(subject);
        result.put("schema", execution ? "xar.ck3.sway-completion-execution.v1" : "xar.ck3.sway-completion-termination.v1")
                .put("build_version", M6TerminalSourceComposition.BUILD).put("executable_sha256", M6TerminalSourceComposition.EXE)
                .put("available", true).put("retention_gap", false).put("read_only", true)
                .put("snapshot_revision", SEQUENCE).put("date_raw", 53290000)
                .put("earliest_sequence", SEQUENCE).put("latest_sequence", SEQUENCE);
        ObjectNode row = identity(subject).put("sequence", SEQUENCE).put("date_raw", 53289976)
                .put("material_effect_observed", false);
        if (execution) {
            row.put("source_branch", "hidden_phase_success_source").put("stock_event", "sway_outcome.0001")
                    .put("phase_result", "success").put("executing_input_observed", true)
                    .put("exact_scope_join_ready", true).put("message_enqueue_observed", false)
                    .put("native_terminal_state_observed", false);
        } else {
            row.put("source_class", "end_scheme_command_execute").put("input_root_scope_kind", 4)
                    .put("executing_source_observed", true).put("pre_status", 0).put("pre_owner", subject.actorCharacterId())
                    .put("post_read_succeeded", true).put("post_instance_present", true)
                    .put("post_storage_slot_reused", false).put("post_exact_instance_join_ready", true)
                    .put("post_status_observed", true).put("post_status", 1).put("post_owner", subject.actorCharacterId())
                    .put("native_terminal_state_observed", true).put("native_terminal_transition_observed", true)
                    .putNull("specific_invalidation_reason");
        }
        result.putArray("records").add(row); return result;
    }
}

