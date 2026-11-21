package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;

/** Exact current Rite facts and a bounded callback receipt; never persistence or SAVE confirmation. */
public record RiteDoctrineFrameV1(Action action,Status status,boolean effectAttempted,boolean nativeReturned,
        boolean nativeHandled,boolean postSelectedEvaluated,boolean postSelected,BigInteger providerGeneration,
        BigInteger querySequence,BigInteger claimSequence,CoreFrame coreFrame,Optional<Facts> facts,
        Optional<GuiRootIndexFrame.OwnerWitness> ownerWitness,Optional<String> unavailableReason) {
    public static final String STEP="current-rite-doctrine-v1",REQUEST_SCHEMA="ck3_121003_rite_doctrine_v1",
            SCHEMA="ck3_121003_rite_doctrine_result_v1",CAPABILITY="game.command.current-rite-doctrine.v1",
            FINAL_STEP="current-rite-final-confirm-v1",FINAL_CAPABILITY="game.command.current-rite-final-confirm.v1",
            GROUP_KEY="des_dynastic_membership",TARGET_KEY="des_doctrine_dynastic";
    public static final int MAXIMUM_BYTES=16384;
    private static final Set<String> FIELDS=Set.of("schema","game_version","executable_sha256","adapter_id","backend","step",
            "action","status","facts_available","effect_attempted","native_returned","native_handled","post_selected_evaluated","post_selected",
            "addresses_redacted","complete_snapshot","complete_gui_tree","physical_save_confirmed","rite_edit_confirmed","group_key","target_key",
            "provider_generation","query_sequence","claim_sequence","core_frame","facts","owner_witness","unavailable_reason");
    public enum Action {
        QUERY("query"),OPEN_DYNASTIC_CATEGORY("open_dynastic_category"),SELECT_DYNASTIC("select_dynastic"),CONFIRM_EDIT("confirm_edit"),QUERY_FINAL_CONFIRMATION("query_final_confirmation"),ACCEPT_FINAL_CONFIRMATION("accept_final_confirmation");
        private final String wire;
        Action(String wire){this.wire=wire;}
        public String wire(){return wire;}
        public boolean finalConfirmation(){return this==QUERY_FINAL_CONFIRMATION||this==ACCEPT_FINAL_CONFIRMATION;}
        public boolean readOnly(){return this==QUERY||this==QUERY_FINAL_CONFIRMATION;}
        public String step(){return finalConfirmation()?FINAL_STEP:STEP;}
        public static Action wire(String value){for(var item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("fixed current Rite action required");}
    }
    public enum Status {
        UNAVAILABLE("unavailable"),AVAILABLE("available"),EXPIRED("expired"),STALE_CORE("stale_core"),SOURCE_CHANGED("source_changed"),
        QUERY_CONSUMED("query_consumed"),CLAIM_CONSUMED("claim_consumed"),CAPACITY_EXHAUSTED("capacity_exhausted"),
        PREREQUISITE_REJECTED("prerequisite_rejected"),CATEGORY_OPENED("category_opened"),DRAFT_SELECTED("draft_selected"),
        CONFIRMATION_DISPATCHED("confirmation_dispatched"),FINAL_CONFIRMATION_PENDING("final_confirmation_pending"),FINAL_CONFIRMATION_READY("final_confirmation_ready"),
        FINAL_CONFIRMATION_DISPATCHED("final_confirmation_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;
        Status(String wire){this.wire=wire;}
        public String wire(){return wire;}
        public static Status wire(String value){for(var item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("current Rite status required");}
    }
    public record Facts(long sourceRiteId,boolean categoryAvailable,boolean targetAvailable,
            boolean shouldDisplayEvaluated,boolean shouldDisplay,boolean canPickEvaluated,boolean canPick,
            boolean knowledgeEvaluated,boolean knownDoctrine,boolean selectedEvaluated,boolean selected,
            boolean canEditEvaluated,boolean canEdit,long pietyCostRaw,long pietyMissingSignedRaw) {
        public Facts {
            RiteDraftCostsFrameV2.sourceRiteId(sourceRiteId);
            RegistryJson.require((!shouldDisplay||shouldDisplayEvaluated)&&(!canPick||canPickEvaluated)
                    &&(!knownDoctrine||knowledgeEvaluated)&&(!selected||selectedEvaluated)&&(!canEdit||canEditEvaluated),"true Rite predicates require their actual evaluation");
        }
        /** Only known TRUE proves this supported OR branch; false known never proves the entire OR false. */
        public boolean pamGateAvailable(){return knowledgeEvaluated&&knownDoctrine;}
        public boolean selectable(){return targetAvailable&&shouldDisplayEvaluated&&shouldDisplay&&canPickEvaluated&&canPick&&pamGateAvailable();}
        public boolean confirmable(){return selectedEvaluated&&selected&&canEditEvaluated&&canEdit&&pietyMissingSignedRaw<=0;}
    }
    public RiteDoctrineFrameV1 {
        Objects.requireNonNull(action);Objects.requireNonNull(status);Objects.requireNonNull(coreFrame);
        Objects.requireNonNull(facts);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(unavailableReason);
        nonnegative64(providerGeneration);nonnegative64(querySequence);nonnegative64(claimSequence);
        RegistryJson.require(coreFrame.build()==GuiControlsFrameV2.BUILD,"current Rite nested Core tuple required");
        RegistryJson.require(facts.isPresent()==ownerWitness.isPresent(),"atomic facts/owner presence required");
        if(facts.isPresent()){
            RegistryJson.require(coreFrame instanceof CoreFrame.Partial,"actual available current Core required for Rite facts");
            GuiControlsFrameV2.requireCore((CoreFrame.Partial)coreFrame);
            RegistryJson.require(((CoreFrame.Partial)coreFrame).prefix().playedCharacterId()!=0,"current Rite actor cannot be zero");
        }else RegistryJson.require(coreFrame instanceof CoreFrame.Unavailable,"absent facts require unavailable current Core");
        RegistryJson.require(!postSelected||postSelectedEvaluated,"post-selected value requires a distinct actual post evaluation");
        RegistryJson.require(!nativeReturned||effectAttempted,"native return requires an attempted callback");
        RegistryJson.require(!nativeHandled||nativeReturned,"handled callback requires an actual native return");
        if(action.readOnly())RegistryJson.require(!effectAttempted&&!nativeReturned&&!nativeHandled&&claimSequence.signum()==0,"query cannot own an effect claim");
        if(status==Status.FINAL_CONFIRMATION_PENDING)RegistryJson.require(action==Action.QUERY_FINAL_CONFIRMATION&&facts.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0&&facts.orElseThrow().confirmable(),"known pending requires original validated Stage1 source; it is not final readiness");
        boolean claimed=effectAttempted&&nativeReturned&&claimSequence.signum()>0&&facts.isPresent();
        boolean coherent=switch(status){
            case AVAILABLE->action==Action.QUERY&&facts.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0;
            case CATEGORY_OPENED->action==Action.OPEN_DYNASTIC_CATEGORY&&claimed&&facts.orElseThrow().categoryAvailable();
            case DRAFT_SELECTED->action==Action.SELECT_DYNASTIC&&claimed&&facts.orElseThrow().selectable()&&postSelectedEvaluated&&postSelected;
            case CONFIRMATION_DISPATCHED->action==Action.CONFIRM_EDIT&&claimed&&nativeHandled&&facts.orElseThrow().confirmable();
            case FINAL_CONFIRMATION_READY->action==Action.QUERY_FINAL_CONFIRMATION&&facts.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0&&facts.orElseThrow().confirmable();
            case FINAL_CONFIRMATION_DISPATCHED->action==Action.ACCEPT_FINAL_CONFIRMATION&&claimed&&!nativeHandled&&facts.orElseThrow().confirmable();
            default->false;
        };
        boolean success=status==Status.AVAILABLE||status==Status.CATEGORY_OPENED||status==Status.DRAFT_SELECTED||status==Status.CONFIRMATION_DISPATCHED||status==Status.FINAL_CONFIRMATION_READY||status==Status.FINAL_CONFIRMATION_DISPATCHED;
        RegistryJson.require(success==coherent,"incoherent current Rite success cannot be promoted");
        RegistryJson.require(success?unavailableReason.isEmpty():unavailableReason.filter(value->!value.isEmpty()).isPresent(),"atomic Rite success/reason semantics required");
    }
    public boolean nativeOk(){return status==Status.AVAILABLE||status==Status.CATEGORY_OPENED||status==Status.DRAFT_SELECTED||status==Status.CONFIRMATION_DISPATCHED||status==Status.FINAL_CONFIRMATION_READY||status==Status.FINAL_CONFIRMATION_DISPATCHED;}
    public static RiteDoctrineFrameV1 decode(RawJson raw){
        RegistryJson.require(raw.bytes().length<=MAXIMUM_BYTES,"bounded current Rite DATA required");var row=RegistryJson.object(raw);RegistryJson.keys(row,FIELDS);
        var build=GuiControlsFrameV2.BUILD;var action=Action.wire(RegistryJson.text(row.get("action")));
        RegistryJson.require(SCHEMA.equals(RegistryJson.text(row.get("schema")))&&action.step().equals(RegistryJson.text(row.get("step")))
                &&build.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))
                &&build.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))&&GuiControlsFrameV2.BACKEND.equals(RegistryJson.text(row.get("backend")))
                &&GROUP_KEY.equals(RegistryJson.text(row.get("group_key")))&&TARGET_KEY.equals(RegistryJson.text(row.get("target_key"))),"exact current Rite tuple and two fixed doctrine keys required");
        RegistryJson.require(RegistryJson.bool(row.get("addresses_redacted"))&&!RegistryJson.bool(row.get("complete_snapshot"))&&!RegistryJson.bool(row.get("complete_gui_tree"))
                &&!RegistryJson.bool(row.get("physical_save_confirmed"))&&!RegistryJson.bool(row.get("rite_edit_confirmed")),"Rite callback cannot buy Full, persisted edit or physical SAVE authority");
        boolean available=RegistryJson.bool(row.get("facts_available"));Optional<Facts> facts=Optional.empty();Optional<GuiRootIndexFrame.OwnerWitness> owner=Optional.empty();
        if(available){
            var f=RegistryJson.object(row.get("facts"));RegistryJson.keys(f,Set.of("source_rite_id","category_available","target_available","should_display_evaluated","should_display","can_pick_evaluated","can_pick","knowledge_evaluated","known_doctrine","pam_gate_available","pam_gate_true","selected_evaluated","selected","can_edit_evaluated","can_edit","piety_cost_raw","piety_missing_signed_raw","raw_scale"));
            var value=new Facts(RegistryJson.integer(f.get("source_rite_id"),BigInteger.ZERO,BigInteger.valueOf(0xffff_fffeL)).longValueExact(),RegistryJson.bool(f.get("category_available")),RegistryJson.bool(f.get("target_available")),RegistryJson.bool(f.get("should_display_evaluated")),RegistryJson.bool(f.get("should_display")),RegistryJson.bool(f.get("can_pick_evaluated")),RegistryJson.bool(f.get("can_pick")),RegistryJson.bool(f.get("knowledge_evaluated")),RegistryJson.bool(f.get("known_doctrine")),RegistryJson.bool(f.get("selected_evaluated")),RegistryJson.bool(f.get("selected")),RegistryJson.bool(f.get("can_edit_evaluated")),RegistryJson.bool(f.get("can_edit")),signed64(f.get("piety_cost_raw")),signed64(f.get("piety_missing_signed_raw")));
            RegistryJson.require(RegistryJson.integer(f.get("raw_scale"),BigInteger.valueOf(100000),BigInteger.valueOf(100000)).intValueExact()==100000
                    &&RegistryJson.bool(f.get("pam_gate_available"))==value.pamGateAvailable()&&RegistryJson.bool(f.get("pam_gate_true"))==value.pamGateAvailable(),"exact CFixedPoint scale and known-TRUE PAM branch required");facts=Optional.of(value);
            var w=RegistryJson.object(row.get("owner_witness"));RegistryJson.keys(w,Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
            owner=Optional.of(new GuiRootIndexFrame.OwnerWitness(positive64(w.get("connection_generation")),positive64(w.get("ticket_sequence")),positive64(w.get("pump_epoch")),RegistryJson.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
        }else RegistryJson.require(row.get("facts").isNull()&&row.get("owner_witness").isNull(),"unavailable Rite facts and owner must be null");
        return new RiteDoctrineFrameV1(action,Status.wire(RegistryJson.text(row.get("status"))),RegistryJson.bool(row.get("effect_attempted")),RegistryJson.bool(row.get("native_returned")),RegistryJson.bool(row.get("native_handled")),RegistryJson.bool(row.get("post_selected_evaluated")),RegistryJson.bool(row.get("post_selected")),uint64(row.get("provider_generation")),uint64(row.get("query_sequence")),uint64(row.get("claim_sequence")),CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame"))),facts,owner,row.get("unavailable_reason").isNull()?Optional.empty():Optional.of(RegistryJson.text(row.get("unavailable_reason"))));
    }
    static BigInteger nonnegative64(BigInteger value){Objects.requireNonNull(value);RegistryJson.require(value.signum()>=0&&value.compareTo(RegistryJson.U64)<=0,"uint64 range required");return value;}
    static BigInteger uint64(com.fasterxml.jackson.databind.JsonNode value){String token=RegistryJson.text(value);RegistryJson.require(token.matches("0|[1-9][0-9]{0,19}"),"canonical uint64 decimal string required");return nonnegative64(new BigInteger(token));}
    private static BigInteger positive64(com.fasterxml.jackson.databind.JsonNode value){var result=uint64(value);RegistryJson.require(result.signum()>0,"positive actual owner witness required");return result;}
    private static long signed64(com.fasterxml.jackson.databind.JsonNode value){String token=RegistryJson.text(value);RegistryJson.require(token.matches("0|-?[1-9][0-9]{0,18}"),"canonical signed64 decimal string required");return new BigInteger(token).longValueExact();}
}
