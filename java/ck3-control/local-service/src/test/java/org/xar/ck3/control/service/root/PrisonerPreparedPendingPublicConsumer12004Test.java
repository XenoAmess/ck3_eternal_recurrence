package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreviewCodec;

/** Public command-to-pending serialization DATA. The fixture issues no Root/Native admission or writer ticket. */
final class PrisonerPreparedPendingPublicConsumer12004Test {
    private static final ExactRef REF=new ExactRef("D:/fixture/prisoner-player-source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-29T00:00:00Z","1.20.0.4",REF);
    private static final Instant NOW=Instant.parse("2026-10-29T00:00:00Z"),DEADLINE=NOW.plusSeconds(30);

    @Test void actualPreparedRansomPassesOwnerIdentityAndPublicSerdeForEveryModernPlayer() { composite(false); }
    @Test void actualPreparedReleasePassesOwnerIdentityAndPublicSerdeForEveryModernPlayer() { composite(true); }
    private static void composite(boolean release) {
        for(long actor:List.of(0L,-2L,(long)Integer.MIN_VALUE,(long)Integer.MAX_VALUE)) {
            Fixture fixture=fixture(actor,303,404,release);var command=fixture.command();
            var family=release?PrisonerPlanningPorts.Family.RELEASE:PrisonerPlanningPorts.Family.RANSOM;
            var owner=new PrisonerEpisodeLedger12004.Owner(new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                    SOURCE.machineId(),command.before().game(),command.sessionId()),actor,command.before().frame().episodeRunId(),SOURCE);
            RawJson initial=PrisonerEpisodeLedger12004.fresh(family,owner,REF);
            RawJson prepared=PrisonerLedgerReducer12004.prepare(family,initial,command,fixture.selected());
            var ledger=PrisonerEpisodeLedger12004.decode(family,prepared);
            assertEquals(actor,ledger.epoch().owner().player());assertTrue(ledger.resolved().isEmpty());assertTrue(ledger.inheritedUnknowns().isEmpty());
            RawJson rawPending=ledger.pending().orElseThrow();var identity=PrisonerPendingIdentity12004.decode(family,rawPending);
            assertEquals(actor,identity.actor());assertEquals(303,identity.target());
            assertEquals(Optional.of(command.actionId()),identity.actionId());
            assertEquals(Optional.of(command.before().frame().revision()),identity.publicRevision());
            assertFalse(StrictJson.parse(rawPending.bytes()).get("material_result").booleanValue());
            assertEquals(prepared,PrisonerEpisodeLedger12004.encode(ledger));
            RawJson publicWire=PrisonerPublicPendingCodec12004.fromAcknowledgement(command,fixture.ack(),fixture.selected());
            assertRoundTrip(publicWire,actor,303,404,release);
            assertEquals(identity.actor(),PrisonerPublicPendingCodec12004.decode(publicWire).player());
        }
    }
    private record Fixture(ActionCommand command,PrisonerActionBinding12004.SelectedRead selected,NativeActionPort.AckReceived ack) { }
    private static void assertRoundTrip(RawJson wire,long player,long target,long payer,boolean release) {
        var decoded=PrisonerPublicPendingCodec12004.decode(wire);
        assertEquals(player,decoded.player());assertEquals(target,decoded.prisoner());
        assertEquals(wire,PrisonerPublicPendingCodec12004.encode(decoded));
        JsonNode value=StrictJson.parse(wire.bytes());assertTrue(value.get("player_character_id").isIntegralNumber());
        assertEquals(player,value.get("player_character_id").longValue());
        assertFalse(value.get("material_result").booleanValue());assertFalse(value.get("advertised").booleanValue());
        assertEquals("submitted_verification_pending",value.get("status").textValue());
        if(release)assertTrue(decoded.release().isPresent());else assertEquals(payer,decoded.ransom().orElseThrow().payer());
    }
    private static Fixture fixture(long player,long target,long payer,boolean release) {
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(player),BigInteger.valueOf(90),BigInteger.valueOf(53220000)),
                "native:90",BigInteger.valueOf(56),"software-pending-episode");
        var before=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(321,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        var operation=release?PrisonerOrdinaryPolicy12004.RELEASE:PrisonerOrdinaryPolicy12004.RANSOM;
        ObjectNode args=StrictJson.object().put("submission_schema",PrisonerActionBinding12004.PUBLIC_SCHEMA).put("prisoner_character_id",target);
        args.set("selected_collection_read",REF.toJson());
        if(release)args.put("release_query_sequence",11).put("release_option_mask_bits",0);
        else args.put("payer_character_id",payer).put("selected_option","gold").put("quoted_gold_raw",30_000_000)
                .put("amount_is_acceptance_time_quote",false).put("pre_player_gold_raw",100_000_000);
        var command=new ActionCommand("software-pending-action",before,SOURCE,"software-pending-session",operation,
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"command DATA"),
                PrisonerActionBinding12004.expected(before,SOURCE,operation,target),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
        var queries=new PrisonerNativeQueries(REF,(ordinal,request,intent)->{throw new AssertionError("pending serde must not request native admission");});
        var contract=queries.contract(0);
        var readRequest=new PlanningReadRequest(before,SOURCE,command.sessionId(),contract.operation(),
                PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),java.util.OptionalLong.empty()),DEADLINE);
        ObjectNode normalized=StrictJson.object();
        var preview=normalized.putObject("player_prisoner_collection").putArray("prisoners").addObject().put("prisoner_character_id",target).putObject("unconditional_release_preview");
        preview.set("costs",ReleasePreviewValues12003.writeCosts(new ReleasePreviewValues12003.Costs(
                Arrays.stream(ReleasePreviewValues12003.Resource.values()).map(resource->new ReleasePreviewValues12003.CostEntry(resource,0)).toList())));
        preview.set("acceptance",NegotiatedPreviewCodec.writeAcceptance(new NegotiatedPreview12003.AutoAccept()));
        var readAck=ack("software-pending-read",normalized);
        var guardEvidence=new GuardEvidence(before,SOURCE,command.sessionId(),BigInteger.TWO,contract.operation(),REF,REF,"software-data-only",NOW,DEADLINE);
        var guard=new PlanningReadGuard(guardEvidence,true,true,true,"b".repeat(64));
        var read=new PlanningReadReceipt(readRequest,contract.contractId(),readAck.requestId(),guard,guard,readAck);
        var selected=new PrisonerActionBinding12004.SelectedRead(REF,read,contract,raw(normalized),0,
                PrisonerOptionIntent.decode(StrictJson.object()));
        assertTrue(PrisonerActionBinding12004.selectedFrameMatches(command,read));
        ObjectNode result=StrictJson.object().put("step",operation.value()).put("accepted",true).put("status","submitted_verification_pending");
        return new Fixture(command,selected,ack("software-pending-submit",result));
    }
    private static NativeActionPort.AckReceived ack(String id,JsonNode result) {
        ObjectNode outer=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
        outer.set("result",result);RawJson original=raw(outer);byte[] bytes=original.bytes();
        byte[] packet=ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        return new NativeActionPort.AckReceived(id,true,Optional.of(raw(result)),original,packet);
    }
    private static RawJson raw(JsonNode value) {return new RawJson(StrictJson.canonical(value));}
    private static JsonNode token(String json) {return StrictJson.parse(("{\"v\":"+json+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8)).get("v");}
}
