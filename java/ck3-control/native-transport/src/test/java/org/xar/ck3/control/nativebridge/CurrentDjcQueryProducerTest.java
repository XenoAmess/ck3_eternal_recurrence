package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Actual C++ parser/serializer originals through production Java; derived negatives are explicitly Java DATA. */
final class CurrentDjcQueryProducerTest {
    static ObjectNode result()throws Exception{return NativeWire.object(NativeWire.parse(CurrentDjcQueryCppFrames.result("choice")));}
    static CurrentDjcTargetWarQueryResult decode(ObjectNode n)throws IOException{return CurrentDjcTargetWarQueryResult.decode(new RawJson(StrictJson.canonical(n)));}
    @Test void genuineCppQueryVariantsRoundTripWithoutCreatingWarAuthority()throws Exception {
        for(String name:new String[]{"choice","blocked","incoherent","indeterminate","unavailable"}) {
            var original=CurrentDjcQueryCppFrames.response(name);var decoded=CurrentDjcTargetWarQueryResult.decode(new RawJson(original.result().token().orElseThrow().value()));
            assertEquals(original.nativeOk(),decoded.available());assertEquals(decoded,CurrentDjcTargetWarQueryResult.decode(decoded.encode()));
            assertEquals(NativeWire.parse(original.result().token().orElseThrow().value()),NativeWire.parse(decoded.encode().bytes()));
        }
        var d=decode(result());assertEquals(NativeWire.UINT64_MAX,d.providerGeneration());assertEquals(NativeWire.UINT64_MAX,d.querySequence());
        var choice=d.casusBelli().orElseThrow().getFirst().choices().getFirst();assertEquals(List.of(123,456,123),choice.targetTitleIds());assertEquals(List.of(7,9,7),choice.extraConfigurationIds());assertTrue(choice.claimant().isEmpty());
        var blocked=CurrentDjcTargetWarQueryResult.decode(new RawJson(CurrentDjcQueryCppFrames.result("blocked")));
        assertTrue(blocked.available());assertFalse(blocked.casusBelli().orElseThrow().getFirst().nativeAvailable().orElseThrow());assertTrue(blocked.casusBelli().orElseThrow().getFirst().choices().isEmpty());
    }
    @Test void actualCppRequestCoreFeedsExactJavaRequestAndReverseParserFiles()throws Exception {
        var core=CurrentDjcQueryCppFrames.core();var original=NativeWire.decodeExecuteRequest(NativeWire.packet(CurrentDjcQueryCppFrames.envelope("request")));
        var claim=NativeWire.object(NativeWire.object(NativeWire.parse(original.normalizedAdditionalFields().value())).get("djc_war_query"));
        var target=NativeCharacterId.fromJson(claim.get("target_character_id"));
        for(var actualTarget:new NativeCharacterId[]{target,new NativeCharacterId(-16777215)}) {
            var request=CurrentDjcTargetWarQuery.request(core,actualTarget);assertEquals(CurrentDjcTargetWarQuery.CAPABILITY,request.requiredCapability().orElseThrow());
            var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));assertEquals(2,fields.size());assertEquals(0,fields.get("arguments").size());assertEquals(14,fields.get("djc_war_query").size());
            fields.put("core_control_deadline_unix_ms",2800000000000L);byte[] packet=NativeWire.execute("djc-java-query-"+(actualTarget.value()<0?"signed":"positive"),request.step(),BigInteger.ZERO,StrictJson.canonical(fields));
            assertEquals(BigInteger.ZERO,NativeWire.decodeExecuteRequest(packet).expectedRevision().orElseThrow());
            String dir=System.getProperty("xar.current267.djc.java.requests");if(dir!=null){Files.createDirectories(Path.of(dir));Files.write(Path.of(dir).resolve(actualTarget.value()<0?"djc-signed-target-request.json":"djc-target-request.json"),Arrays.copyOfRange(packet,4,packet.length));}
        }
    }
    @Test void oldFullSelfUnpausedAndOutOfRangeTargetsCannotBecomeCurrentRequests()throws Exception {
        var core=CurrentDjcQueryCppFrames.core();var p=core.prefix();
        for(var old:new ExactCk3Build[]{ExactCk3Build.CK3_12004,ExactCk3Build.CK3_121003_STEAM_26785313_FULL111})assertThrows(IllegalArgumentException.class,()->CurrentDjcTargetWarQuery.request(new CoreFrame.Partial(old,p),new NativeCharacterId(39957)));
        assertThrows(IllegalArgumentException.class,()->CurrentDjcTargetWarQuery.request(core,new NativeCharacterId(p.playedCharacterId())));
        assertThrows(IllegalArgumentException.class,()->new NativeCharacterId(-1));assertThrows(IllegalArgumentException.class,()->NativeCharacterId.of(2147483648L));
        assertThrows(IllegalArgumentException.class,()->CurrentDjcTargetWarQuery.request(new CoreFrame.Partial(core.build(),new CoreFrame.Prefix(p.dateRaw(),p.speed(),false,p.localPlayerId(),true,true,p.playedCharacterId(),true)),new NativeCharacterId(39957)));
    }
    @Test void readonlyResultCannotSupplyCanDeclareDebitSubmissionWarOrForeignTuple()throws Exception {
        for(String k:new String[]{"ordinary_can_declare_war","total_debit","war_id","submission_available","war_submission_attempted","war_submitted"})assertThrows(IOException.class,()->decode(result().put(k,true)),k);
        for(String k:new String[]{"addresses_redacted","read_only"})assertThrows(IOException.class,()->decode(result().put(k,false)),k);
        for(String k:new String[]{"schema","game_version","executable_sha256","adapter_id","backend","step"})assertThrows(IOException.class,()->decode(result().put(k,"wrong-source")),k);
        assertThrows(IOException.class,()->decode(result().put("arbitrary_selector","anything")));
    }
    @Test void canonicalUint64AndSignedIntegerNullSemanticsRejectLossyData()throws Exception {
        for(String n:new String[]{"+1","01","-0","-1","18446744073709551616"})assertThrows(IOException.class,()->decode(result().put("provider_generation",n)),n);
        assertThrows(IOException.class,()->decode(result().put("query_sequence",1)));assertThrows(IOException.class,()->decode(result().put("target_character_id",2147483648L)));
        var n=result();((ObjectNode)n.get("owner_witness")).put("thread_id",4294967296L);assertThrows(IOException.class,()->decode(n));
        assertThrows(IOException.class,()->decode(result().putNull("owner_witness")));assertThrows(IOException.class,()->decode(result().put("target_character_id",36423)));
        var unavailable=NativeWire.object(NativeWire.parse(CurrentDjcQueryCppFrames.result("unavailable")));unavailable.putArray("casus_belli");assertThrows(IOException.class,()->decode(unavailable));
        byte[] fractional=new String(CurrentDjcQueryCppFrames.result("choice"),java.nio.charset.StandardCharsets.UTF_8).replace("\"target_character_id\":39957","\"target_character_id\":39957.0").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(Exception.class,()->CurrentDjcTargetWarQueryResult.decode(new RawJson(fractional)));
    }
    @Test void fixedCbOrderEvaluatorCoherenceAndOrderedChoiceDomainsRemainStrict()throws Exception {
        var n=result();var cb=(ObjectNode)n.get("casus_belli").get(0);cb.put("native_available",false);var unavailable=n;assertThrows(IOException.class,()->decode(unavailable));
        n=result();cb=(ObjectNode)n.get("casus_belli").get(0);cb.put("native_evaluation_returned",false);var bad=n;assertThrows(IOException.class,()->decode(bad));
        n=result();cb=(ObjectNode)n.get("casus_belli").get(0);cb.put("key","kingdom_de_jure_greatwar");var wrong=n;assertThrows(IOException.class,()->decode(wrong));
        n=result();var choice=(ObjectNode)n.get("casus_belli").get(0).get("choices").get(0);choice.putArray("extra_configuration_ids").add(-1).add(Integer.MIN_VALUE).add(-1);choice.put("claimant_character_id",-16777215);
        var actual=decode(n).casusBelli().orElseThrow().getFirst().choices().getFirst();assertEquals(List.of(-1,Integer.MIN_VALUE,-1),actual.extraConfigurationIds());assertEquals(-16777215,actual.claimant().orElseThrow().value());
        choice.putArray("target_title_ids").add(-1);var absent=n;assertThrows(IOException.class,()->decode(absent));
    }
}
