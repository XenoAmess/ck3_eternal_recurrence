package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRelationJson.*;

/** Registered complete current first-title-heir relationship. The title observation does not authorize player succession. */
public final class FamilyCurrentRelation {
    public static final String STEP="query-current-first-heir-relationship-v1-private",SCHEMA="xar.ck3.current-first-heir-relationship.v1";
    private static final Set<Status> PAIR_STATES=Set.of(Status.AVAILABLE,Status.UNAVAILABLE,Status.NOT_APPLICABLE);
    private static final List<String> PAIR_IDS=List.of("actor_character_id","heir_character_id","partner_character_id","recipient_character_id","intermediary_character_id");
    private static final List<String> ADULT=List.of("heir_is_adult","partner_is_adult","heir_adult_measure_raw","partner_adult_measure_raw","heir_adult_threshold_raw","partner_adult_threshold_raw");
    private static final List<String> COSTS=List.of("gold_raw","prestige_raw","piety_raw","renown_raw","influence_raw","herd_raw","treasury_raw","treasury_or_gold_raw","merit_raw","barter_goods_raw");
    private FamilyCurrentRelation() { }
    public enum State {AVAILABLE,UNAVAILABLE}
    public enum PairState {AVAILABLE,UNAVAILABLE,NOT_APPLICABLE}
    public static final class Pair {
        private final PairState state;private final OpportunityJson.Obj original;
        private Pair(PairState state,JsonNode n){this.state=state;original=retain(n);}
        public PairState state(){return state;}public OpportunityJson.Obj original(){return original;}
    }
    public static final class Observation {
        private final FamilyRootBinding.Basis root;private final State state;private final Long betrothed,primary;private final Optional<List<Long>> spouses;private final Pair pair;
        private final Optional<FamilyRelationDescendants.Observation> descendants;private final Optional<FamilyRelationReproductive.Observation> reproductive;
        private final Optional<FamilyRelationGuardianMaterials.Observation> materials;private final OpportunityJson.Obj original;
        private Observation(FamilyRootBinding.Basis root,State state,Long betrothed,Long primary,Optional<List<Long>> spouses,Pair pair,
                Optional<FamilyRelationDescendants.Observation> descendants,Optional<FamilyRelationReproductive.Observation> reproductive,Optional<FamilyRelationGuardianMaterials.Observation> materials,JsonNode original){
            this.root=Objects.requireNonNull(root);this.state=state;this.betrothed=betrothed;this.primary=primary;this.spouses=spouses.map(List::copyOf);this.pair=Objects.requireNonNull(pair);this.descendants=Objects.requireNonNull(descendants);this.reproductive=Objects.requireNonNull(reproductive);this.materials=Objects.requireNonNull(materials);this.original=retain(original);
        }
        public FamilyRootBinding.Basis root(){return root;}public State state(){return state;}public Optional<Long> betrothed(){return Optional.ofNullable(betrothed);}public Optional<Long> primarySpouse(){return Optional.ofNullable(primary);}public Optional<List<Long>> spouses(){return spouses;}public Pair actionability(){return pair;}
        public Optional<FamilyRelationDescendants.Observation> descendants(){return descendants;}public Optional<FamilyRelationReproductive.Observation> reproductive(){return reproductive;}public Optional<FamilyRelationGuardianMaterials.Observation> materials(){return materials;}public OpportunityJson.Obj original(){return original;}
    }
    public static Observation decode(PlanningReadReceipt receipt,FamilyRootBinding.Basis basis,FamilyRelationMaterialExports.Captured sidecar){
        Objects.requireNonNull(receipt);Objects.requireNonNull(basis);Objects.requireNonNull(sidecar);Context c=basis.binding().context();need(c.build()==Build.CROZIER4,"current relation requires actual exact .4 native source");
        FamilyRelationMaterialExports.requireCaptured(receipt,sidecar);
        JsonNode command=parse(receipt.original().originalFrame()),n=field(command,"result");
        eq(n,"step",STEP);yes(n,"accepted");yes(n,"private_build");yes(n,"read_only");no(n,"advertised");eq(n,"native_revision",c.revision());eq(n,"subject_source","public_campaign_root_primary_first_heir");Long heir=basis.binding().observedFirstHeir().isPresent()?basis.binding().observedFirstHeir().orElseThrow():null;eq(n,"heir_character_id",BigInteger.valueOf(heir==null?-1:heir));
        String status=text(n,"status");need(Set.of("available","unavailable").contains(status),"current relationship status differs");boolean available=status.equals("available");String reason=optionalString(n,"unavailable_reason");
        Long betrothed=null,primary=null;Optional<List<Long>> spouses=Optional.empty();
        if(!available){need(reason!=null&&!reason.isEmpty()&&isFalse(maybe(n,"bilateral_verified")),"unavailable relationship lost explicit reason/bilateral false");nilOptional(n,"betrothed_character_id","primary_spouse_character_id","spouse_character_ids");}
        else {
            need(heir!=null&&reason==null&&isTrue(maybe(n,"bilateral_verified")),"available relationship lacks actual root heir or bilateral proof");BigInteger b=optionalNumber(n,"betrothed_character_id",BigInteger.ONE,I32_MAX),p=optionalNumber(n,"primary_spouse_character_id",BigInteger.ONE,I32_MAX);betrothed=b==null?null:b.longValueExact();primary=p==null?null:p.longValueExact();List<Long> ids=integers(n,"spouse_character_ids",65536,BigInteger.ONE,I32_MAX).stream().map(BigInteger::longValueExact).toList();need(ids.size()==new java.util.HashSet<>(ids).size()&&!ids.contains(heir)&&!Objects.equals(betrothed,heir)&&!Objects.equals(primary,heir)&&(betrothed==null||!betrothed.equals(primary)&&!ids.contains(betrothed)),"current spouse/betrothal vector is malformed or crossed heir identity");spouses=Optional.of(ids);
        }
        ObjectNode out=F.objectNode().put("schema",SCHEMA).put("schema_version",1).put("exact_ck3_build",c.build().version()).put("exe_sha256",c.build().sha256()).put("read_only",true).put("advertised",false).put("native_revision",c.revision()).put("root_query_sequence",basis.binding().rootQuerySequence());if(heir==null)out.putNull("heir_character_id");else out.put("heir_character_id",heir);out.put("status",status);if(reason==null)out.putNull("unavailable_reason");else out.put("unavailable_reason",reason);
        Optional<FamilyRelationDescendants.Observation> descendants=Optional.empty();if(n.has(FamilyRelationDescendants.LEAF)){
            descendants=FamilyRelationDescendants.decode(field(n,FamilyRelationDescendants.LEAF),c.actor().longValueExact(),heir,c.revision(),c.date());out.set(FamilyRelationDescendants.LEAF,descendants.isPresent()?OpportunityJson.toNode(descendants.orElseThrow().original()):F.nullNode());out.set(FamilyRelationDescendants.SUMMARY,descendants.isPresent()?OpportunityJson.toNode(FamilyRelationDescendants.summary(descendants.orElseThrow())):F.nullNode());out.set("family_generation_education_decision_inputs_v1",OpportunityJson.toNode(FamilyRelationEducationSources.decision(descendants)));
        }
        Optional<FamilyRelationReproductive.Observation> reproductive=Optional.empty();if(n.has(FamilyRelationReproductive.LEAF)){var observed=FamilyRelationReproductive.decode(field(n,FamilyRelationReproductive.LEAF),c.actor().longValueExact(),heir,c.revision(),c.date(),n);reproductive=Optional.of(observed);out.set(FamilyRelationReproductive.LEAF,OpportunityJson.toNode(observed.original()));}
        Pair pair=actionability(maybe(n,"betrothal_actionability"),c.actor().longValueExact(),heir,available?betrothed:null);out.set("betrothal_actionability",OpportunityJson.toNode(pair.original()));
        if(available){out.put("bilateral_verified",true);if(betrothed==null)out.putNull("betrothed_character_id");else out.put("betrothed_character_id",betrothed);if(primary==null)out.putNull("primary_spouse_character_id");else out.put("primary_spouse_character_id",primary);ArrayNodeWriter.spouses(out,spouses.orElseThrow());out.set("source_frame",sourceFrame(receipt,c));}
        Optional<FamilyRelationGuardianMaterials.Observation> materials=FamilyRelationGuardianMaterials.decode(parse(sidecar.original()),command,out,c.actor().longValueExact(),heir,c.revision(),c.date());
        ObjectNode materialProof=out.putObject("guardian_factory_materials_v2").put("schema_version",2).put("native_hash_proof_verified",true).put("same_request_export_completed",true).put("typed_factory_inputs_present",materials.isPresent());InteractionArguments.ref(materialProof.putObject("original_sidecar"),sidecar.reference());
        if(materials.isPresent()){
            JsonNode owned=nativeObject(materials.orElseThrow().original());materialProof.put("qualified",materials.orElseThrow().qualified());materialProof.set("observation",owned);
            for(String leaf:List.of(FamilyRelationEducationProvider.LEAF,FamilyRelationGuardianMaterials.CHILD_MATERIALS))if(owned.has(leaf)){
                out.set(leaf,field(owned,leaf));ObjectNode source=out.putObject(leaf.equals(FamilyRelationEducationProvider.LEAF)?FamilyRelationEducationProvider.SOURCE_LEAF:"current_child_relation_materials_source_v1");source.put("request_id",receipt.requestId()).put("binding_scope","query_before_after").put("bridge_pid",c.before().game().pid()).put("connection_generation",c.connectionGeneration()).put("native_revision",c.revision()).put("date_raw",c.date()).put("played_character_id",c.actor()).put("sidecar_bytes",sidecar.reference().bytes()).put("sidecar_sha256",sidecar.reference().sha256()).put("same_request_export_completed",true);if(heir==null)source.putNull("heir_character_id");else source.put("heir_character_id",heir);
            }
        }else {materialProof.put("qualified",false).putNull("observation").put("unavailable_reason","legacy_factory_input_version_not_observed");}
        return new Observation(basis,available?State.AVAILABLE:State.UNAVAILABLE,betrothed,primary,spouses,pair,descendants,reproductive,materials,out);
    }
    private static ObjectNode sourceFrame(PlanningReadReceipt receipt,Context c){
        ObjectNode source=F.objectNode().put("binding_scope","query_before_after_native_frame"),nativeFrame=source.putObject("native_frame");nativeFrame.put("native_revision",c.revision()).put("date_raw",c.date()).put("actor_character_id",c.actor()).put("episode_run_id",c.before().frame().episodeRunId()).put("bridge_pid",c.before().game().pid()).put("connection_generation",c.connectionGeneration()).put("exact_ck3_build",c.build().version()).put("exe_sha256",c.build().sha256());
        var before=receipt.before().binding().observed().frame();var after=receipt.after().binding().observed().frame();source.putObject("public_before").put("snapshot_id",before.snapshotId()).put("revision",before.revision());source.putObject("public_after").put("snapshot_id",after.snapshotId()).put("revision",after.revision());return source;
    }
    private static Pair actionability(JsonNode input,long actor,Long heir,Long partner){
        if(absent(input)){
            ObjectNode unknown=F.objectNode().put("status","unavailable").put("unavailable_reason","native_readback_not_supplied").put("actor_character_id",actor).put("adult_readback_available",false).putNull("ready_to_marry_betrothed").put("final_legality_sampled",false).putNull("complete_can_send").put("recipient_acceptance_ready",false).putNull("recipient_ai_accept_raw").putNull("recipient_answer_status_raw").putNull("generic_costs").putNull("matrilineal_option_selected").putNull("native_child_house_preview").putNull("effective_matrilineal_if_accepted").putNull("predicted_outcome_if_accepted");if(heir==null)unknown.putNull("heir_character_id");else unknown.put("heir_character_id",heir);if(partner==null)unknown.putNull("partner_character_id");else unknown.put("partner_character_id",partner);ADULT.forEach(unknown::putNull);unknown.putNull("recipient_character_id").putNull("intermediary_character_id");return new Pair(PairState.UNAVAILABLE,unknown);
        }
        JsonNode n=object(input);FamilyRelationJson.Availability a=FamilyRelationJson.availability(n,PAIR_STATES);for(String key:PAIR_IDS)optionalNumber(n,key,BigInteger.ONE,I32_MAX);need(optionalIdentity(n,"actor_character_id",actor)&&optionalIdentity(n,"heir_character_id",heir)&&optionalIdentity(n,"partner_character_id",partner),"betrothal actionability crossed finalized pair identities");
        boolean adult=bool(n,"adult_readback_available"),sampled=bool(n,"final_legality_sampled"),acceptance=bool(n,"recipient_acceptance_ready");Boolean ready=optionalBoolean(n,"ready_to_marry_betrothed");
        if(adult){need(partner!=null,"adult pair readback lacks actual betrothed partner");boolean h=bool(n,"heir_is_adult"),p=bool(n,"partner_is_adult");BigInteger hm=number(n,"heir_adult_measure_raw",I16_MIN,I16_MAX),pm=number(n,"partner_adult_measure_raw",I16_MIN,I16_MAX),ht=number(n,"heir_adult_threshold_raw",I32_MIN,I32_MAX),pt=number(n,"partner_adult_threshold_raw",I32_MIN,I32_MAX);need(h==(hm.compareTo(ht)>=0)&&p==(pm.compareTo(pt)>=0)&&ready!=null&&ready==(h&&p),"pair adulthood lost native runtime thresholds");}else{need(ready==null,"unread pair adulthood became ready");nilOptional(n,ADULT.toArray(String[]::new));}
        Boolean complete=optionalBoolean(n,"complete_can_send"),lineality=optionalBoolean(n,"effective_matrilineal_if_accepted"),selected=optionalBoolean(n,"matrilineal_option_selected");BigInteger score=optionalNumber(n,"recipient_ai_accept_raw",I64_MIN,I64_MAX),answer=optionalNumber(n,"recipient_answer_status_raw",BigInteger.ZERO,BigInteger.TWO);need(sampled?complete!=null:complete==null,"pair final legality became inferred boolean");need(acceptance?score!=null&&answer!=null:score==null&&answer==null,"pair recipient acceptance lost native signed value");String outcome=optionalString(n,"predicted_outcome_if_accepted");need(outcome==null||Set.of("marriage","betrothal").contains(outcome),"pair predicted native outcome differs");JsonNode costs=maybe(n,"generic_costs");if(!absent(costs)){eq(costs,"raw_scale",BigInteger.valueOf(100000));eq(costs,"payer_role","actor");eq(costs,"application_timing","on_send");for(String key:COSTS)number(costs,key,I64_MIN,I64_MAX);}
        if(a.available()){need(adult&&sampled&&acceptance&&!absent(costs)&&lineality!=null&&outcome!=null,"available pair native value incomplete");for(String key:PAIR_IDS.subList(0,4))need(!absent(maybe(n,key)),"available pair lost native participants");}
        if(a.status()==Status.NOT_APPLICABLE)need(partner==null&&!adult&&!sampled&&!acceptance&&absent(costs)&&lineality==null&&selected==null&&outcome==null,"inapplicable pair retained actual native value");housePreview(maybe(n,"native_child_house_preview"),heir,partner,selected,lineality,complete);return new Pair(PairState.valueOf(a.status().name()),n);
    }
    private static boolean optionalIdentity(JsonNode n,String key,Long expected){BigInteger value=optionalNumber(n,key,BigInteger.ONE,I32_MAX);return value==null||expected!=null&&value.equals(BigInteger.valueOf(expected));}
    private static void housePreview(JsonNode n,Long heir,Long partner,Boolean selected,Boolean effective,Boolean complete){
        if(absent(n))return;String status=text(n,"status"),reason=text(n,"reason");need(Set.of("available","unavailable","not_applicable").contains(status)&&(status.equals("available")?reason.isEmpty():!reason.isEmpty()),"child House preview availability differs");for(String key:List.of("subject_character_id","candidate_character_id"))optionalNumber(n,key,BigInteger.ONE,I32_MAX);need(equal(n,"subject_character_id",heir==null?null:BigInteger.valueOf(heir))&&equal(n,"candidate_character_id",partner==null?null:BigInteger.valueOf(partner))&&isFalse(maybe(n,"requested_matrilineal_option")),"child House preview changed finalized pair");
        List<String> fields=List.of("selected_matrilineal_option","effective_matrilineal_if_accepted","complete_can_send","native_selected_parent_character_id","house_id","dynasty_id");
        if(status.equals("available")){
            bool(n,"selected_matrilineal_option");bool(n,"effective_matrilineal_if_accepted");bool(n,"complete_can_send");
            need(partner!=null&&selected!=null&&equal(n,"selected_matrilineal_option",selected)&&equal(n,"effective_matrilineal_if_accepted",effective)&&equal(n,"complete_can_send",complete),"child House preview lineality/final terms differ");BigInteger parent=number(n,"native_selected_parent_character_id",BigInteger.ONE,I32_MAX);need(parent.equals(BigInteger.valueOf(heir))||parent.equals(BigInteger.valueOf(partner)),"child House preview selected another parent");optionalNumber(n,"house_id",BigInteger.ZERO,I32_MAX);optionalNumber(n,"dynasty_id",BigInteger.ZERO,I32_MAX);
        }else {nilOptional(n,fields.toArray(String[]::new));need(!status.equals("not_applicable")||partner==null,"inapplicable child House preview retained partner");}
    }
    private static final class ArrayNodeWriter{private ArrayNodeWriter(){}static void spouses(ObjectNode out,List<Long> values){var rows=out.putArray("spouse_character_ids");values.forEach(rows::add);}}
}
