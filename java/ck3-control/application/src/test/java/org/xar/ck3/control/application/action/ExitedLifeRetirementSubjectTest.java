package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

final class ExitedLifeRetirementSubjectTest {
    private static final String MACHINE="software-exited-life";
    private static final String OWNER="software-runtime-owner";
    private static final String EPISODE="software-campaign-episode";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(77)));
    private static final Instant AT=Instant.parse("2026-11-26T18:58:00Z");
    @TempDir Path temporary;

    @Test void explicitExitedScopeBindsOwnerSessionCampaignEpisodeAndStableOriginalTerminal() {
        var fixture=fixture();
        byte[] raw=StrictJson.canonical(fixture.request());
        var request=CompositeOperatorQuarantineRequest.decode(raw);
        assertEquals(EPISODE,request.episodeRunId());
        assertEquals(OWNER,request.exitedLife().orElseThrow().ownerSessionId());
        assertTrue(request.matchesExitedOwner(MACHINE,GAME,OWNER,Optional.of(fixture.terminal())));
        assertFalse(request.matchesExitedOwner(MACHINE,GAME,EPISODE,Optional.of(fixture.terminal())));
        assertFalse(request.matchesExitedOwner(MACHINE,GAME,OWNER,Optional.empty()));
        var other=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(78)));
        assertFalse(request.matchesExitedOwner(MACHINE,other,OWNER,Optional.of(fixture.terminal())));
        assertEquals(request,source(fixture,fixture.decision(),Optional.of(new RawJson(fixture.terminalBytes()))).request());
    }

    @Test void exitedScopeRequiresItsOwnDecisionAndExactlyTwoOriginalReservations() {
        var fixture=fixture();
        var edited=fixture.decision().deepCopy().put("decision","continue-live");
        assertThrows(IllegalArgumentException.class,()->source(fixture,edited,Optional.of(new RawJson(fixture.terminalBytes()))));
        var wrongSaved=fixture.decision().deepCopy().put("saved_pair_sha256","8".repeat(64));
        assertThrows(IllegalArgumentException.class,()->source(fixture,wrongSaved,Optional.of(new RawJson(fixture.terminalBytes()))));
        assertThrows(IllegalArgumentException.class,()->source(fixture,fixture.decision(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->source(fixture,fixture.decision(),Optional.of(new RawJson(new byte[]{123,125}))));
        var extra=fixture.request().deepCopy();
        extra.withArray("children").addObject().put("ordinal",3).put("action_id","third").put("body_sha256","9".repeat(64));
        assertThrows(IllegalArgumentException.class,()->CompositeOperatorQuarantineRequest.decode(StrictJson.canonical(extra)));
        var old=fixture.request().deepCopy().put("schema",LIFE_SCHEMA).put("scope",LIFE_SCOPE);
        assertThrows(IllegalArgumentException.class,()->CompositeOperatorQuarantineRequest.decode(StrictJson.canonical(old)));
    }

    private record Fixture(ObjectNode request,ObjectNode decision,ExactRef terminal,byte[] terminalBytes) { }

    private Fixture fixture() {
        byte[] terminalBytes="{\"mode\":\"software-only no process exit\"}".getBytes(StandardCharsets.UTF_8);
        var terminal=ref("software-terminal.json",terminalBytes);
        var subject=StrictJson.object().put("machine_id",MACHINE).put("episode_run_id",EPISODE)
                .put("parent_action_id","software-parent").put("parent_body_sha256","1".repeat(64))
                .put("expected_head_sequence",57).put("expected_head_digest","2".repeat(64)).put("issued_at_utc",AT.toString());
        subject.set("game",GAME.toJson());
        var decision=subject.deepCopy().put("schema",EXITED_LIFE_DECISION_SCHEMA).put("decision",EXITED_LIFE_DECISION)
                .put("operator_statement","software fixture has no operator authority").put("owner_session_id",OWNER)
                .put("saved_pair_sha256","3".repeat(64));
        decision.set("original_terminal",terminal.toJson());
        var request=subject.deepCopy().put("schema",EXITED_LIFE_SCHEMA).put("scope",EXITED_LIFE_SCOPE)
                .put("observation_deadline_utc",AT.plusSeconds(180).toString());
        request.set("original_receipt_ref",ref("software-parent.json",new byte[]{1}).toJson());
        request.putArray("prior_requests");
        var children=request.putArray("children");
        children.addObject().put("ordinal",1).put("action_id","software-arm").put("body_sha256","4".repeat(64));
        children.addObject().put("ordinal",2).put("action_id","software-resume").put("body_sha256","5".repeat(64));
        request.putObject("exited_life").put("owner_session_id",OWNER).put("saved_pair_sha256","3".repeat(64))
                .set("original_terminal",terminal.toJson());
        request.set("authorized_by",ref("software-decision.json",StrictJson.canonical(decision)).toJson());
        return new Fixture(request,decision,terminal,terminalBytes);
    }

    private CompositeOperatorQuarantineSource source(Fixture fixture,ObjectNode decision,Optional<RawJson> originalTerminal) {
        byte[] authorization=StrictJson.canonical(decision);
        var request=fixture.request().deepCopy();
        request.set("authorized_by",ref("software-decision.json",authorization).toJson());
        byte[] raw=StrictJson.canonical(request);
        return new CompositeOperatorQuarantineSource(ref("software-request.json",raw),raw,authorization,GAME,EPISODE,
                new OperationKey("life-advance"),LifeAdvanceComposite.HANDLER,Clock.fixed(AT,ZoneOffset.UTC),originalTerminal);
    }

    private ExactRef ref(String name,byte[] bytes) {
        return new ExactRef(temporary.resolve(name).toString(),bytes.length,ActionCodec.sha256(bytes));
    }
}
