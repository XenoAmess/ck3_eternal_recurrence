package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionFixtures.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

/** Executes the retained original producer as a test oracle; no second Python implementation is authored. */
final class KnownPendingInteractionOriginalProducerTest {
    private static final int MAXIMUM_BYTES=1_048_576;
    private static final String ORACLE="""
            import hashlib,json,pathlib,sys
            root=pathlib.Path(sys.argv[1])
            sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.strategy import _degraded_pending_interaction_decision
            source=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'strategy.py'
            before=hashlib.sha256(source.read_bytes()).hexdigest()
            outputs=[]
            for item in json.load(sys.stdin)['cases']:
                snapshot=item['snapshot']
                outputs.append(_degraded_pending_interaction_decision(snapshot['pending_character_interaction'],
                    item['wire']['pending_character_interaction_context'],snapshot=snapshot,
                    active_wars=snapshot['active_wars'],available_steps=set(item['steps'])))
            if before!=hashlib.sha256(source.read_bytes()).hexdigest():
                raise RuntimeError('original producer changed during compatibility evaluation')
            json.dump({'source_sha256':before,'outputs':outputs},sys.stdout)
            """;
    @Test void fullNativeDecoderAndKnownRuleSelectionsMatchTheActualOriginalProducer() throws Exception {
        var c=context();List<ObjectNode> wires=new ArrayList<>();List<ObjectNode> snapshots=new ArrayList<>();
        for(String key:List.of("spar_with_knight_interaction","arrange_marriage_interaction","grant_vassal_interaction",
                "perk_alliance_interaction","negotiate_alliance_interaction","call_ally_interaction","pay_ransom_interaction")) {
            wires.add(wire(c,key));snapshots.add(snapshot(c));
        }
        ObjectNode defense=snapshots.get(4).withArray("active_wars").addObject().put("war_id",17).put("player_side","defender")
                .put("player_is_primary_war_leader",true).put("player_relative_war_score",0).put("primary_opponent_character_id",888);
        defense.putArray("targeted_title_ids").add(33);
        ObjectNode unique=wire(c,"spar_with_knight_interaction");
        ((ObjectNode)unique.path("pending_character_interaction_context").path("legality").get("reject"))
                .put("allowed",false).put("reason","native_reply_not_allowed");
        wires.add(unique);snapshots.add(snapshot(c));
        ObjectNode blockedMarriage=wire(c,"arrange_marriage_interaction");
        ((ObjectNode)blockedMarriage.path("pending_character_interaction_context").path("send_options").path("rows").get(0)).put("selected",true);
        wires.add(blockedMarriage);snapshots.add(snapshot(c));
        ObjectNode request=F.objectNode();var cases=request.putArray("cases");
        for(int i=0;i<wires.size();i++) {
            ObjectNode entry=cases.addObject();entry.set("snapshot",snapshots.get(i));entry.set("wire",wires.get(i));
            var actions=entry.putArray("steps");steps().forEach(operation->actions.add(operation.value()));
        }
        Path repo=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path source=repo.resolve("ck3_autonomous_player/src/xar_autoplayer/strategy.py");
        assertTrue(Files.isRegularFile(source),"the actual complete compatibility producer is mandatory");
        String digest=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
        ProcessBuilder builder=new ProcessBuilder(required("xar.python"),"-B","-X","utf8","-c",ORACLE,repo.toString());
        builder.directory(repo.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();
        try(var readers=Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout=readers.submit(()->read(process.getInputStream()));var stderr=readers.submit(()->read(process.getErrorStream()));
            try {
                try(var stdin=process.getOutputStream()) { stdin.write(encode(request).bytes()); }
                assertTrue(process.waitFor(30,TimeUnit.SECONDS),"actual original pending producer timed out; no skip credit");
                byte[] output=stdout.get(5,TimeUnit.SECONDS),errors=stderr.get(5,TimeUnit.SECONDS);
                assertEquals(0,process.exitValue(),new String(errors,StandardCharsets.UTF_8));
                ObjectNode result=parse(new org.xar.ck3.control.application.action.RawJson(output));
                assertEquals(digest,result.path("source_sha256").textValue());assertEquals(wires.size(),result.path("outputs").size());
                for(int i=0;i<wires.size();i++) {
                    var actual=KnownPendingInteractionRules.evaluate(input(c,snapshots.get(i),wires.get(i),false));
                    ObjectNode original=object(field(result.path("outputs").get(i),"decision"));
                    assertEquals(text(original,"classification"),actual.classification().key(),"classification case "+i);
                    assertEquals(text(original,"rule_id"),actual.ruleId(),"rule case "+i);
                    String selected=actual.selected().map(KnownPendingInteractionRules.Action::key).orElse(null);
                    assertEquals(nullableText(original,"selected_action"),selected,"actual selection case "+i);
                }
            } finally { if(process.isAlive())process.destroyForcibly(); }
        }
    }
    private static byte[] read(InputStream input) throws IOException {
        byte[] raw=input.readNBytes(MAXIMUM_BYTES+1);
        if(raw.length>MAXIMUM_BYTES)throw new IOException("original pending producer output exceeded explicit bound");return raw;
    }
    private static String required(String property) {
        String value=System.getProperty(property);assertNotNull(value,"missing required producer regression property "+property);
        assertFalse(value.isBlank(),"empty required producer regression property "+property);return value;
    }
}
