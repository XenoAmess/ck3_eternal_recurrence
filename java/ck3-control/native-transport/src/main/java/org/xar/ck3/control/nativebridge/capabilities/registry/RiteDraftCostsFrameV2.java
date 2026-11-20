package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Full native CanEdit evaluation and exact cost DATA; never observer/action/save authority. */
public sealed interface RiteDraftCostsFrameV2 permits RiteDraftCostsFrameV2.Partial,RiteDraftCostsFrameV2.Unavailable {
    String STEP="query-rite-draft-costs-v2",SCHEMA="ck3.rite_draft_costs.v2",REQUEST_SCHEMA="ck3.rite_draft_costs_request.v2";
    String BACKEND=GuiRootIndexFrame.BACKEND,WINDOW_NAME="rite_creation_window";
    ExactCk3Build BUILD=GuiRootIndexFrame.BUILD;
    Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","backend","status",
            "draft_available","application_main_observed","source_abi_pins_verified","full_native_can_edit_evaluated","addresses_redacted",
            "complete_snapshot","complete_gui_tree","control_actions_available","observer_guard_evaluated","physical_save_confirmed",
            "core_frame","draft","owner_witness","unavailable_reason");
    CoreFrame coreFrame();
    default ExactCk3Build build(){return BUILD;}
    static long sourceRiteId(long value){RegistryJson.require(value>=0&&value<0xffff_ffffL,"uint32 source Rite excluding FFFFFFFF required");return value;}
    record Draft(long sourceRiteId,int playedCharacterId,boolean canEditRiteNative,long pietyCostRaw,long pietyMissingSignedRaw,boolean hasEnoughPiety){
        public Draft{RiteDraftCostsFrameV2.sourceRiteId(sourceRiteId);RegistryJson.require(playedCharacterId!=-1&&hasEnoughPiety==(pietyMissingSignedRaw<=0),"actual actor and exact signed missing-piety predicate required");}
    }
    record Partial(CoreFrame.Partial coreFrame,Draft draft,GuiRootIndexFrame.OwnerWitness ownerWitness)implements RiteDraftCostsFrameV2 {
        public Partial{GuiRootIndexFrame.requireExpectedCore(coreFrame);Objects.requireNonNull(draft);Objects.requireNonNull(ownerWitness);RegistryJson.require(draft.playedCharacterId()==coreFrame.prefix().playedCharacterId(),"draft actor differs from exact nested Core");}
    }
    record Unavailable(CoreFrame.Unavailable coreFrame,String reason)implements RiteDraftCostsFrameV2 {
        public Unavailable{Objects.requireNonNull(coreFrame);RegistryJson.require(coreFrame.build()==BUILD&&reason!=null&&!reason.isEmpty()&&reason.equals(coreFrame.reason()),"atomic unavailable Core/draft reason required");}
    }
    static RiteDraftCostsFrameV2 decode(RawJson original){
        RegistryJson.require(original.bytes().length<=16384,"bounded draft-cost response required");var row=RegistryJson.object(original);RegistryJson.keys(row,FIELDS);
        RegistryJson.require(STEP.equals(RegistryJson.text(row.get("step")))&&SCHEMA.equals(RegistryJson.text(row.get("schema")))
                &&BUILD.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))
                &&BUILD.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(row.get("backend"))),"exact current draft source tuple required");
        RegistryJson.require(RegistryJson.bool(row.get("addresses_redacted"))&&!RegistryJson.bool(row.get("complete_snapshot"))&&!RegistryJson.bool(row.get("complete_gui_tree"))
                &&!RegistryJson.bool(row.get("control_actions_available"))&&!RegistryJson.bool(row.get("observer_guard_evaluated"))&&!RegistryJson.bool(row.get("physical_save_confirmed")),"draft Can/cost DATA cannot buy observer/action/save or Full authority");
        var core=CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));RegistryJson.require(core.build()==BUILD,"nested Core exact build mismatch");
        boolean available=RegistryJson.bool(row.get("draft_available")),main=RegistryJson.bool(row.get("application_main_observed")),pins=RegistryJson.bool(row.get("source_abi_pins_verified")),evaluated=RegistryJson.bool(row.get("full_native_can_edit_evaluated"));
        if(!available){
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status")))&&!pins&&!evaluated&&core instanceof CoreFrame.Unavailable&&row.get("draft").isNull()&&row.get("owner_witness").isNull(),"unavailable draft retains nulls and unavailable Core");
            var absent=(CoreFrame.Unavailable)core;RegistryJson.require(main==absent.applicationMainObserved(),"draft main flag differs from Core");return new Unavailable(absent,RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status")))&&main&&pins&&evaluated&&core instanceof CoreFrame.Partial&&row.get("unavailable_reason").isNull(),"available native Can evaluation required even when Can is false");
        var draft=RegistryJson.object(row.get("draft"));RegistryJson.keys(draft,Set.of("source_rite_id","played_character_id","window_name","can_edit_rite_native","piety_cost_raw","piety_missing_signed_raw","raw_scale","has_enough_piety"));
        RegistryJson.require(WINDOW_NAME.equals(RegistryJson.text(draft.get("window_name")))&&RegistryJson.integer(draft.get("raw_scale"),BigInteger.valueOf(100000),BigInteger.valueOf(100000)).equals(BigInteger.valueOf(100000)),"fixed original Rite window and CFixedPoint scale required");
        var owner=RegistryJson.object(row.get("owner_witness"));RegistryJson.keys(owner,Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
        return new Partial((CoreFrame.Partial)core,new Draft(RegistryJson.integer(draft.get("source_rite_id"),BigInteger.ZERO,BigInteger.valueOf(0xffff_fffeL)).longValueExact(),RegistryJson.int32(draft.get("played_character_id")),RegistryJson.bool(draft.get("can_edit_rite_native")),signed64(draft.get("piety_cost_raw")),signed64(draft.get("piety_missing_signed_raw")),RegistryJson.bool(draft.get("has_enough_piety"))),
                new GuiRootIndexFrame.OwnerWitness(witness(owner.get("connection_generation")),witness(owner.get("ticket_sequence")),witness(owner.get("pump_epoch")),RegistryJson.integer(owner.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
    }
    private static long signed64(com.fasterxml.jackson.databind.JsonNode node){String token=RegistryJson.text(node);RegistryJson.require(token.matches("0|-?[1-9][0-9]{0,18}"),"canonical signed64 decimal string required");var value=new BigInteger(token);RegistryJson.require(value.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&value.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"signed64 CFixedPoint overflow");return value.longValueExact();}
    private static BigInteger witness(com.fasterxml.jackson.databind.JsonNode node){String token=RegistryJson.text(node);RegistryJson.require(token.matches("[1-9][0-9]{0,19}"),"canonical uint64 witness string required");var value=new BigInteger(token);RegistryJson.require(value.compareTo(RegistryJson.U64)<=0,"uint64 witness overflow");return value;}
}
