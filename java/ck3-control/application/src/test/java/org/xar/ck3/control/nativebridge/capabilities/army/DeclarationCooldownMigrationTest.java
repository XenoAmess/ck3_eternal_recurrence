package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** The real original file-backed producer supplies every expected transition; Java uses the sole pure reducer and schema codec. */
final class DeclarationCooldownMigrationTest {
    @Test void completedRoundVerifiedAdvanceColdRollbackAndWarResetMatchActualOriginalProducer() throws Exception {
        verifyOriginal();
        ObjectNode vectors = BattleOriginalOracle.call("""
                import json,copy,tempfile
                from pathlib import Path
                from xar_autoplayer.bridge import declaration_opportunity_cooldown_v1 as original
                rows=[]
                def frame(date,revision,pid=10,actor=101,episode='a'):
                    return dict(actor_character_id=actor,episode_run_id=episode,date_raw=date,native_revision=revision,bridge_pid=pid,snapshot_id='native:'+str(revision))
                def peace():return dict(paused=True,active_wars=[])
                def advance(start,end):return dict(status='executed',selected_step='life-advance',result=dict(step='life-advance',progress_status='postcondition',paused=True,starting_date_raw=start,ending_date_raw=end))
                with tempfile.TemporaryDirectory(prefix='xar-original-declaration-cooldown-') as directory:
                    directory=Path(directory)
                    def run(op,current,**kw):
                        if op=='completed':
                            result=dict(step='query-declarable-wars',accepted=True,status='available',declarable_wars=[],query_sequence=kw['sequence'])
                            value=original.observe_completed_query(directory,current,result)
                        elif op=='after':value=original.observe_after_turn(directory,kw['source'],kw['outcome'],kw['snapshot'],current)
                        elif op=='seed':
                            original._save(directory,kw['state']);value=original.view(directory,kw.get('snapshot',{}),current)
                        else:value=original.view(directory,kw.get('snapshot',{}),current)
                        state=original._load(directory,current)
                        rows.append(dict(op=op,current=current,**kw,expected_view=value,expected_state=state))
                    run('view',frame(100,5),snapshot=peace())
                    run('completed',frame(100,5),sequence=1)
                    run('after',frame(124,6),source=frame(100,5),outcome=advance(100,124),snapshot=peace())
                    run('after',frame(124,6),source=frame(100,5),outcome=advance(100,124),snapshot=peace())
                    run('completed',frame(124,6),sequence=1)
                    run('completed',frame(124,6),sequence=2)
                    blocked=peace();blocked['active_event']={}
                    run('after',frame(148,7),source=frame(124,6),outcome=advance(124,148),snapshot=blocked)
                    unresolved=peace();unresolved['war_declaration_continuity_v1']=dict(status='submitted')
                    run('after',frame(148,7),source=frame(124,6),outcome=advance(124,148),snapshot=unresolved)
                    run('after',frame(172,8),source=frame(148,7),outcome=advance(148,172),snapshot=peace())
                    run('view',frame(892,9),snapshot=peace())
                    run('completed',frame(892,9),sequence=3)
                    run('view',frame(800,4,pid=20),snapshot=peace())
                    run('after',frame(824,5,pid=20),source=frame(892,9),outcome=advance(892,824),snapshot=peace())
                    run('completed',frame(824,5,pid=20),sequence=4)
                    defensive=dict(paused=True,active_wars=[dict(war_id=30,player_side='defender')])
                    run('view',frame(824,5,pid=20),snapshot=defensive)
                    run('completed',frame(824,5,pid=20),sequence=5)
                    verified=dict(paused=True,active_wars=[dict(war_id=31,player_side='attacker')],war_declaration_continuity_v1=dict(schema='war-declaration-continuity-v1',status='war_started',native_response='accepted',postcondition_verified=True,war_id=31))
                    run('view',frame(824,5,pid=20),snapshot=verified)
                    run('completed',frame(824,5,pid=20),sequence=6)
                    run('view',frame(824,5,pid=20),snapshot=verified)
                    zero=copy.deepcopy(verified);zero['active_wars'][0]['war_id']=0;zero['war_declaration_continuity_v1']['war_id']=0
                    run('view',frame(824,5,pid=20),snapshot=zero)
                    run('view',frame(100,1,pid=20,actor=202,episode='b'),snapshot=peace())
                    legacy=original._new(frame(100,1,pid=20,actor=202,episode='b'));legacy['cooldown_until_date_raw']=1000;legacy['last_confirmed_war_id']='war-A'
                    run('seed',frame(100,1,pid=20,actor=202,episode='b'),state=legacy,snapshot=peace())
                print(json.dumps({'cases':rows},allow_nan=False))
                """, ArmyJson.empty());
        verifyOriginal(); DeclarationOpportunityCooldown.State state = null;
        for (JsonNode row : vectors.path("cases")) {
            var current = frame(row.path("current")); if (state == null) state = DeclarationOpportunityCooldown.initial(current);
            DeclarationOpportunityCooldown.Reduction result = switch (row.path("op").textValue()) {
                case "completed" -> DeclarationOpportunityCooldown.completed(state, current, UInt64.positive(row.path("sequence").bigIntegerValue()));
                case "after" -> DeclarationOpportunityCooldown.afterTurn(state, frame(row.path("source")), DeclarationOpportunityCooldown.outcome(row.path("outcome")),
                        DeclarationOpportunityCooldown.snapshot(row.path("snapshot")), current);
                case "seed" -> DeclarationOpportunityCooldown.view(DeclarationOpportunityCooldown.decode(row.path("state"), current), DeclarationOpportunityCooldown.snapshot(row.path("snapshot")), current);
                default -> DeclarationOpportunityCooldown.view(state, DeclarationOpportunityCooldown.snapshot(row.path("snapshot")), current);
            };
            sameJson(row.path("expected_state"), DeclarationOpportunityCooldown.encode(result.state()));
            sameJson(row.path("expected_view"), DeclarationOpportunityCooldown.encodeView(result.view()));
            assertEquals(result.view(), DeclarationOpportunityCooldown.decodeView(DeclarationOpportunityCooldown.encodeView(result.view()), current));
            state = DeclarationOpportunityCooldown.decode(DeclarationOpportunityCooldown.encode(result.state()), current);
            assertEquals(result.state(), state);
        }
        assertEquals(22, vectors.path("cases").size());
    }
    @Test void strictWireCannotCountMalformedAdvanceOrLosePersistedDeadlineDuringColdLoad() {
        var current = frame(ArmyJson.empty().put("actor_character_id", 101).put("episode_run_id", "a").put("date_raw", 100).put("native_revision", 5).put("bridge_pid", 10).put("snapshot_id", "native:5"));
        var state = DeclarationOpportunityCooldown.completed(DeclarationOpportunityCooldown.initial(current), current, UInt64.positive(BigInteger.ONE)).state();
        ObjectNode broken = DeclarationOpportunityCooldown.encode(state); ((ObjectNode) broken.path("pending_query")).put("query_sequence", true);
        assertThrows(IllegalArgumentException.class, () -> DeclarationOpportunityCooldown.decode(broken, current));
        ObjectNode wrongAdvance = ArmyJson.empty(); wrongAdvance.putObject("result").put("starting_date_raw", true);
        assertThrows(IllegalArgumentException.class, () -> DeclarationOpportunityCooldown.outcome(wrongAdvance), "bool is not a date even when the original simply declined credit");
        assertThrows(IllegalArgumentException.class, () -> DeclarationOpportunityCooldown.completed(state, current, new UInt64(BigInteger.ZERO)));
        ObjectNode old = DeclarationOpportunityCooldown.encode(state); old.put("cooldown_until_date_raw", 900).put("consecutive_no_war_rounds", 0);
        var restored = DeclarationOpportunityCooldown.decode(old, current); assertEquals(2, restored.consecutiveNoWarRounds());
        var cold = new DeclarationOpportunityCooldown.Frame(current.actorCharacterId(), current.episodeRunId(), current.dateRaw(), current.nativeRevision(), BigInteger.valueOf(20), current.snapshotId());
        var view = DeclarationOpportunityCooldown.view(restored, DeclarationOpportunityCooldown.Snapshot.empty(), cold);
        assertTrue(view.state().pendingQuery().isEmpty()); assertEquals(BigInteger.valueOf(900), view.state().cooldownUntilDateRaw().orElseThrow());
        assertEquals(2, view.view().consecutiveNoWarRounds()); assertTrue(view.view().active());
    }
    private static DeclarationOpportunityCooldown.Frame frame(JsonNode n) {
        return new DeclarationOpportunityCooldown.Frame(n.path("actor_character_id").bigIntegerValue(), n.path("episode_run_id").textValue(), n.path("date_raw").bigIntegerValue(),
                n.path("native_revision").bigIntegerValue(), n.path("bridge_pid").bigIntegerValue(), n.hasNonNull("snapshot_id") ? Optional.of(n.path("snapshot_id").textValue()) : Optional.empty());
    }
    private static void sameJson(JsonNode expected, JsonNode actual) {
        assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8), new String(StrictJson.canonical(actual), StandardCharsets.UTF_8));
    }
    private static void verifyOriginal() throws Exception {
        String configured = System.getProperty("xar.repository.root"); if (configured == null || configured.isBlank()) throw new IllegalStateException("actual original root required");
        Path root = Path.of(configured).toRealPath(), original = root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/declaration_opportunity_cooldown_v1.py").toRealPath();
        assertTrue(original.startsWith(root)); assertEquals("2174bdd8e2e0f53631a8fda1e490f0f02ea583203b17b9419b8c4f2efda56178", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(original)))) ;
    }
}
