package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.util.Base64;
import java.util.Map;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;

/** Original head47 and immutable saved Driver; fake archive permits DATA only, never a no-write or Entry authority. */
final class SavedRecoveryIdentity101DataTest {
    @Test void originalEpisodeAndNewTransportSessionRemainDistinctAndBoundToSavedData()throws Exception {
        var data=node(FullJsonTree.parse(resource("metadata.json.gz",1<<20),1<<20));
        byte[] head=Base64.getDecoder().decode(data.get("head").textValue());
        assertEquals("7187f2bc0cb525c8a136e3ad213fa6f2b2994e9f01b60d5025b5948c38afecce",ActionCodec.sha256(head));
        ObjectNode current=ContinuityJson.parseObject(head,1<<20);
        var state=state(current);assertEquals(47,state.sequence());
        byte[] receipt=Base64.getDecoder().decode(data.get("receipt").textValue());
        assertEquals("b00a8ea2a0d505858556d4f9594c7630f85ba03b009d04b7a08d4c67d6ce5094",ActionCodec.sha256(receipt));
        var row=ContinuityJson.parseObject(receipt,1<<20);
        ActionCommand command=ActionCodec.decodeCommand(ContinuityJson.canonical(row.get("command")));
        assertEquals("bd007706",ActionCodec.bodySha256(command).substring(0,8));
        var marker=node(current.get(SavedContinuityBootstrap.FIELD));
        SessionIdentity owner=OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
        assertNotEquals(owner.sessionId(),command.before().frame().episodeRunId());
        byte[] raw=resource("driver.json.gz",8*1024*1024);
        assertEquals(5255702,raw.length);
        assertEquals("1ebfad2356b17e4c56ec278bdaa701e20c819a6981abf132eb8de5665c6a6d4b",ActionCodec.sha256(raw));
        var original=ExactRef.fromJson(marker.get("full_driver"));int[] loads={0};
        var archive=archive(original,raw,loads,null);
        Map.Entry<String,java.math.BigInteger> actual=ContinuityBatchJournal.savedRecoveryIdentityData(state,owner,command,archive);
        assertEquals("resume91_after_user_20261105_01",actual.getKey());
        assertEquals(command.before().frame().identity().player(),actual.getValue());assertEquals(1,loads[0]);

        ObjectNode legacy=current.deepCopy();legacy.remove(SavedContinuityBootstrap.FIELD);loads[0]=0;
        assertEquals(owner.sessionId(),ContinuityBatchJournal.savedRecoveryIdentityData(state(legacy),owner,command,archive).getKey());assertEquals(0,loads[0]);
        var foreign=new SessionIdentity(owner.machineId(),owner.game(),owner.sessionId()+"-foreign");
        assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state,foreign,command,archive));assertEquals(0,loads[0]);
        ObjectNode differentGame=owner.game().toJson();differentGame.put("pid",owner.game().pid()+1);
        var wrongGame=new SessionIdentity(owner.machineId(),GameGeneration.fromJson(differentGame),owner.sessionId());
        assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state,wrongGame,command,archive));assertEquals(0,loads[0]);
        ObjectNode baseline=current.deepCopy();baseline.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,new ExactRef(original.path()+".wrong-DATA",original.bytes(),original.sha256()).toJson());
        assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state(baseline),owner,command,archive));assertEquals(0,loads[0]);
        ObjectNode episode=current.deepCopy();node(node(node(episode.get(SavedContinuityBootstrap.FIELD)).get("opening")).get("frame")).put("episode_run_id","foreign-DATA-episode");
        assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state(episode),owner,command,archive));
        ObjectNode actor=current.deepCopy();node(node(node(actor.get(SavedContinuityBootstrap.FIELD)).get("opening")).get("frame")).put("played_character_id","31255");
        assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state(actor),owner,command,archive));
        byte[] corrupt=raw.clone();boolean changed=false;
        for(int i=0;i+1<corrupt.length;i++)if(corrupt[i]=='"'&&corrupt[i+1]>='a'&&corrupt[i+1]<='z'){corrupt[i+1]=(byte)(corrupt[i+1]-32);changed=true;break;}
        assertTrue(changed);RawJson.fullMaterial(corrupt); // Valid JSON before the production SHA check is invoked.
        var hashFailure=assertThrows(IllegalArgumentException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state,owner,command,archive(original,corrupt,new int[1],null)));
        assertTrue(hashFailure.getMessage().contains("original Driver bytes differ"));
        UncheckedIOException originalFailure=new UncheckedIOException(new IOException("original archive load failure"));
        assertSame(originalFailure,assertThrows(UncheckedIOException.class,()->ContinuityBatchJournal.savedRecoveryIdentityData(state,owner,command,archive(original,raw,new int[1],originalFailure))));
        System.out.println("SAVED_RECOVERY101_IDENTITY_DATA_PASS actualhead47 originalDriver opening actor episode separateFromTransport legacy owner game baseline hash rejects");
    }
    private static ObjectNode node(JsonNode n){if(n instanceof ObjectNode o)return o;throw new AssertionError("DATA object required");}
    private static ContinuityState state(ObjectNode n){return ContinuityState.fromJson(n,n.get("machine_id").textValue());}
    private static ActionPorts.OutcomeArchive archive(ExactRef expected,byte[] raw,int[] loads,RuntimeException failure) {
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(SavedRecoveryIdentity101DataTest.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            if(!method.getName().equals("loadFullMaterial"))throw new AssertionError("no Root/native/archive writes or other DATA calls: "+method);
            assertEquals(expected,args[0]);loads[0]++;if(failure!=null)throw failure;return RawJson.fullMaterial(raw);
        });
    }
    private static byte[] resource(String name,int maximum)throws IOException {
        try(var input=SavedRecoveryIdentity101DataTest.class.getResourceAsStream("recovery101/"+name)) {
            if(input==null)throw new IOException("exact recovery DATA fixture missing");
            try(var gzip=new GZIPInputStream(input)){byte[] raw=gzip.readNBytes(maximum+1);if(raw.length==0||raw.length>maximum)throw new IOException("bounded recovery fixture required");return raw;}
        }
    }
}
