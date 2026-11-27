package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest.EXITED_LIFE_DECISION;
import static org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest.EXITED_LIFE_DECISION_SCHEMA;
import static org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest.EXITED_LIFE_SCHEMA;
import static org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest.EXITED_LIFE_SCOPE;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineSource;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

final class RootOperatorQuarantineRuntimeTest {
    @Test
    void departedSavedOwnerAndCampaignEpisodeRemainDistinct(@TempDir Path directory) throws Exception {
        String machine = "xenoamess-full-tower-eb9d2c1186";
        String runtimeSession = "session-migration121003-current131-current-two-cycle56";
        String campaignEpisode = "resume91_offline04_20261111T071454Z";
        var game = GameGeneration.fromJson(StrictJson.object().put("pid", 50372)
                .put("creation_filetime", "134401544348311914"));
        var observedAt = Instant.parse("2026-11-27T07:04:08.145970500Z");
        var issuedAt = observedAt.plusSeconds(1);
        var terminal = write(directory, "terminal.json", StrictJson.canonical(StrictJson.object().put("software_fixture", true)));
        var subject = StrictJson.object().put("machine_id", machine).put("episode_run_id", campaignEpisode)
                .put("parent_action_id", "fixture-parent").put("parent_body_sha256", "1".repeat(64))
                .put("expected_head_sequence", 57).put("expected_head_digest", "2".repeat(64))
                .put("issued_at_utc", issuedAt.toString());
        subject.set("game", game.toJson());
        var decision = subject.deepCopy().put("schema", EXITED_LIFE_DECISION_SCHEMA).put("decision", EXITED_LIFE_DECISION)
                .put("owner_session_id", runtimeSession).put("saved_pair_sha256", "3".repeat(64))
                .put("operator_statement", "Software fixture");
        decision.set("original_terminal", terminal.toJson());
        var request = subject.deepCopy().put("schema", EXITED_LIFE_SCHEMA).put("scope", EXITED_LIFE_SCOPE)
                .put("observation_deadline_utc", issuedAt.plusSeconds(60).toString());
        request.set("authorized_by", write(directory, "decision.json", StrictJson.canonical(decision)).toJson());
        request.set("original_receipt_ref", write(directory, "parent.json", new byte[]{1}).toJson());
        request.putArray("prior_requests");
        var children = request.putArray("children");
        children.addObject().put("ordinal", 1).put("action_id", "fixture-arm").put("body_sha256", "4".repeat(64));
        children.addObject().put("ordinal", 2).put("action_id", "fixture-resume").put("body_sha256", "5".repeat(64));
        request.putObject("exited_life").put("owner_session_id", runtimeSession).put("saved_pair_sha256", "3".repeat(64))
                .set("original_terminal", terminal.toJson());
        var configured = write(directory, "request.json", StrictJson.canonical(request));
        var clock = Clock.fixed(issuedAt, ZoneOffset.UTC);
        var source = bind(new SessionIdentity(machine, game, runtimeSession), terminal, observedAt, configured, clock);
        assertEquals(campaignEpisode, source.request().episodeRunId());
        assertEquals(runtimeSession, source.request().exitedLife().orElseThrow().ownerSessionId());
        var failure = assertThrows(ContractViolationException.class, () ->
                bind(new SessionIdentity(machine, game, campaignEpisode), terminal, observedAt, configured, clock));
        assertTrue(failure.getMessage().contains("actual old configured Life terminal source"));
    }

    private static CompositeOperatorQuarantineSource bind(SessionIdentity owner, ExactRef terminal, Instant observedAt,
            ExactRef configured, Clock clock) throws Exception {
        var method = RootOperatorQuarantineRuntime.class.getDeclaredMethod("departedSource", SessionIdentity.class,
                Optional.class, Instant.class, ExactRef.class, Clock.class);
        method.setAccessible(true);
        try {
            return (CompositeOperatorQuarantineSource) method.invoke(null, owner, Optional.of(terminal), observedAt, configured, clock);
        } catch (InvocationTargetException failure) {
            throw (Exception) failure.getCause();
        }
    }

    private static ExactRef write(Path directory, String name, byte[] bytes) throws IOException {
        var file = Files.write(directory.resolve(name), bytes);
        return new ExactRef(file.toString(), bytes.length, ActionCodec.sha256(bytes));
    }
}
