package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer;

/** Fresh original-producer differential test. The Python snippet is test-only IO replacement; no deployed interpreter route. */
final class FinanceOriginalProducerParityTest {
    private static final String ORIGINAL_SHA="2152c3e2c7f48bad6864c06d43a6e32e731736a72e65df5b134250a156450293";
    private static final String SCRIPT="""
import json,sys,copy
from pathlib import Path
from xar_autoplayer import faction_gift_pending_v1 as original
payload=json.load(sys.stdin)
state={"ledger":original._empty()}
original.read_faction_gift_ledger_v1=lambda ignored:copy.deepcopy(state["ledger"])
original.write_json_atomic=lambda ignored,value:state.__setitem__("ledger",copy.deepcopy(value))
answers=[]
for receipt in payload["receipts"]:
    state["ledger"]=original._empty()
    original.begin_faction_gift_submission_v1(Path("."),**payload["begin"])
    original.mark_faction_gift_ack_pending_v1(Path("."),request_id=payload["begin"]["request_id"],ack=payload["ack"])
    try:
        result=original.complete_faction_gift_after_independent_receipt_v1(Path("."),request_id=payload["begin"]["request_id"],receipt=receipt)
        answers.append({"accepted":True,"ledger":result})
    except ValueError:
        answers.append({"accepted":False})
json.dump(answers,sys.stdout,separators=(",",":"))
""";
    private static ObjectNode begin() {
        return (ObjectNode)StrictJson.parse(("""
{"request_id":"gift-fixture-actual-1","episode_run_id":"episode-finance","source_round_id":"R240",
"source_bridge_pid":123,"source_bridge_creation_date":"2026-10-23T17:00:00Z",
"minimum_gold_reserve_raw":10000000,"checkpoint_sha256_before_submit":"%s",
"observation":{"queried_source_faction_id":44,"recipient_character_id":55,"snapshot_revision":10,
"native_snapshot_revision":10,"observed_date_raw":100,"player_character_id":1,"player_gold_raw":50000000,
"recipient_opinion_of_player":-12,"gift_opinion_present":false,"source_faction_power_raw":150000,
"source_faction_discontent_raw":75000,"source_faction_member_character_ids":[55,66],
"source_faction_targeting_player":true,"gift_preview":{"gold_cost_raw":1000000,"opinion_delta":25}}}
""").formatted("a".repeat(64)).getBytes(StandardCharsets.UTF_8));
    }
    private static ObjectNode ack() {
        return (ObjectNode)StrictJson.parse(("""
{"schema_version":1,"status":"submitted_verification_pending","verification_pending":true,
"request_id":"gift-fixture-actual-1","source_faction_id":44,"recipient_character_id":55}
""").getBytes(StandardCharsets.UTF_8));
    }
    private static ObjectNode receipt() {
        return (ObjectNode)StrictJson.parse(("""
{"schema_version":1,"status":"mitigated","request_id":"gift-fixture-actual-1","postcondition_verified":true,
"mitigation_applied":true,"post_gift_opinion_present":true,"source_faction_id":44,"recipient_character_id":55,
"player_character_id":1,"post_snapshot_revision":11,"post_native_snapshot_revision":11,"post_observed_date_raw":100,
"post_player_gold_raw":49000000,"post_gift_opinion_modifier_value":25}
""").getBytes(StandardCharsets.UTF_8));
    }
    private static byte[] bytes(JsonNode json) { return StrictJson.canonical(json,1048576); }
    @Test void originalBeginAckCompleteMatchesSharedJavaReducerAndRejectsFiveRealFailurePaths() throws Exception {
        String configured=System.getProperty("xar.repository.root");
        assertNotNull(configured,"fresh original producer requires -Dxar.repository.root; absent is not skipped");
        Path repository=Path.of(configured).toAbsolutePath().normalize();
        Path source=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py");
        assertEquals(ORIGINAL_SHA,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))),
                "original producer source changed; repin and recapture instead of reusing a golden");
        List<ObjectNode> receipts=new ArrayList<>();receipts.add(receipt());
        ObjectNode wallet=receipt();wallet.put("post_player_gold_raw",49000001);receipts.add(wallet);
        ObjectNode request=receipt();request.put("request_id","another-original-request");receipts.add(request);
        ObjectNode revision=receipt();revision.put("post_native_snapshot_revision",10);receipts.add(revision);
        ObjectNode date=receipt();date.put("post_observed_date_raw",124);receipts.add(date);
        ObjectNode opinion=receipt();opinion.put("post_gift_opinion_modifier_value",24);receipts.add(opinion);
        ObjectNode payload=StrictJson.object();payload.set("begin",begin());payload.set("ack",ack());
        var array=payload.putArray("receipts");receipts.forEach(array::add);
        String interpreter=System.getProperty("xar.python","python");
        ProcessBuilder builder=new ProcessBuilder(interpreter,"-c",SCRIPT).directory(repository.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH",repository.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process child=builder.start();
        try {
            try(var input=child.getOutputStream()) { input.write(bytes(payload)); }
            assertTrue(child.waitFor(45,TimeUnit.SECONDS),"original producer process timed out");
            byte[] output=child.getInputStream().readNBytes(1048577);
            assertEquals(0,child.exitValue(),new String(output,StandardCharsets.UTF_8));
            assertTrue(output.length<=1048576,"original producer result exceeded bounded fixture");
            JsonNode original=StrictJson.parse(output);assertTrue(original.isArray());assertEquals(receipts.size(),original.size());
            for(int index=0;index<receipts.size();index++) {
                var ledger=GiftPendingReducer.begin(GiftPendingModel.Ledger.empty(),GiftPendingCodec.decodeBegin(bytes(begin())));
                ledger=GiftPendingReducer.markAck(ledger,"gift-fixture-actual-1",GiftPendingCodec.decodeAck(bytes(ack())));
                final var pending=ledger;final var raw=receipts.get(index);
                if(original.get(index).get("accepted").booleanValue()) {
                    var applied=GiftPendingCodec.decodeReceipt(bytes(raw));
                    GiftPendingReducer.verifyReceipt(pending.pending().orElseThrow().baseline(),"gift-fixture-actual-1",applied);
                    var actual=GiftPendingReducer.complete(pending,"gift-fixture-actual-1",applied);
                    assertEquals(original.get(index).get("ledger"),StrictJson.parse(GiftPendingCodec.encodeLedger(actual)));
                    assertEquals(actual,GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(actual)));
                } else assertThrows(IllegalArgumentException.class,()->GiftPendingReducer.complete(pending,"gift-fixture-actual-1",GiftPendingCodec.decodeReceipt(bytes(raw))));
            }
        } finally { if(child.isAlive()) { child.destroyForcibly();child.waitFor(5,TimeUnit.SECONDS); } }
    }
    @Test void independentReceiptRefusesAckBooleanVersionAndUnquotedCompanySentinel() {
        assertThrows(IllegalArgumentException.class,()->GiftPendingCodec.decodeReceipt(bytes(ack())));
        ObjectNode wrong=receipt();wrong.put("schema_version",true);
        assertThrows(IllegalArgumentException.class,()->GiftPendingCodec.decodeReceipt(bytes(wrong)));
        for(String input:List.of("{\"company_id\":true}","{\"company_id\":1.0}","{\"company_id\":4294967295}","{}"))
            assertThrows(IllegalArgumentException.class,()->NativeFinanceEffects.company(org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(input.getBytes(StandardCharsets.UTF_8)),"arguments")));
    }
}

