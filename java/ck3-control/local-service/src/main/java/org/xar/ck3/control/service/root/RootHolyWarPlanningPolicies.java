package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContext;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Actual Python ordinary holy-order alternative and readonly defender annotation, sharing the installed Army producers. */
public final class RootHolyWarPlanningPolicies {
    private RootHolyWarPlanningPolicies() { }
    public static final String HIRE="hire-holy-order-v1";
    public record Sources(ExactRef policy) {
        public Sources { StrictJson.require(policy!=null&&policy.bytes()>0,"actual complete holy-policy Java source required"); }
    }
    public static final class Prepared {
        private final Sources sources;
        public Prepared(Sources sources) { this.sources=Objects.requireNonNull(sources); }
        public RootDomainInstallation install(RootRuntimeContext context,RootRuntimeDomainAssembly.Shared shared,
                ArmyOrdinaryRuntimeBindings.Installed army,RootRuntimeCommands commands) throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(shared);Objects.requireNonNull(army);Objects.requireNonNull(commands);
            context.game().launchPlan().sources().requireLoadedClass(RootHolyWarPlanningPolicies.class);
            commands.requireArmy(army.service());
            StrictJson.require(army.quotes().producers().frames()==shared.army().products().frames()
                    &&army.quotes().producers().wars()==shared.military().warReads(),"holy policies require identical installed Army/war producers");
            var runtime=new Runtime(context,army,commands,sources.policy());
            return new RootDomainInstallation("ordinary-holy-war-planning",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                    List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(runtime.policy(PlanningStage.HOLY_ORDER_REINFORCEMENT),
                    runtime.policy(PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION)),List.of(),List.of(),List.of(),List.of());
        }
    }
    private static final class Runtime {
        private final RootRuntimeContext context;private final ArmyOrdinaryRuntimeBindings.Installed army;
        private final RootRuntimeCommands commands;private final ExactRef source;
        Runtime(RootRuntimeContext context,ArmyOrdinaryRuntimeBindings.Installed army,RootRuntimeCommands commands,ExactRef source) {
            this.context=context;this.army=army;this.commands=commands;this.source=source;
        }
        OrdinaryPolicy policy(PlanningStage stage) {
            return new OrdinaryPolicy() {
                public PlanningStage stage(){return stage;}
                public ExactRef implementationSource(){return source;}
                public Decision evaluate(PlanningRequest request,Draft previous) {
                    if(stage==PlanningStage.HOLY_ORDER_REINFORCEMENT&&need(request.observations().snapshot(),previous).isEmpty())
                        return new NotApplicable("the original blocked player siege without a selected action is absent");
                    if(stage==PlanningStage.HOLY_ORDER_REINFORCEMENT&&!request.observations().bridgeCapabilities().contains("game.command."+HIRE))
                        return new NotApplicable("actual native holy-order hire capability is absent");
                    try {
                        return context.withSession(same->context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                            StrictJson.require(original==request,"holy policy replaced the true original planning request");
                            Complete frame=lease.frame();Decision result;
                            if(stage==PlanningStage.HOLY_ORDER_REINFORCEMENT) {
                                var producer=army.quotes().producers().holyOrders();var contract=producer.contract();
                                var inquiry=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),new Obj(java.util.Map.of()),request.deadline());
                                var observed=producer.query_player_holy_order_context_private_v1(same,inquiry);
                                if(!(observed instanceof PlanningReadResult.Known<PlayerHolyOrderContextRead.Observation> known))
                                    result=annotate(previous,"holy_order_reinforcement_observation",diagnostic(request,"input_unavailable",((PlanningReadResult.Unavailable<PlayerHolyOrderContextRead.Observation>)observed).reason()));
                                else {
                                    requireOriginal(context,frame,known.receipt(),known.originalReceipt());
                                    var assessment=choose(request.observations().snapshot(),previous,known.value());
                                    Obj proposal=assessment.detail().with("original_read",value(known.originalReceipt().toJson()));
                                    if(assessment.selected().isEmpty())result=annotate(previous,"holy_order_reinforcement_observation",proposal);
                                    else {
                                        var plan=previous.detail().with("policy",new Text("one-life-turn-v1"))
                                                .with("phase",new Text("native_war_holy_order_siege_reinforcement"))
                                                .with("reason",new Text("current native legal order troops cover the observed blocked-siege deficit"))
                                                .with("selected_step",new Text(HIRE)).with("holy_order_hire_proposal",proposal)
                                                .with("deferred_siege_plan",previous.detail());
                                        var selection=new MilitaryPlanningDecision.Select("one-life-turn-v1","native_war_holy_order_siege_reinforcement",
                                                "current native legal order troops cover the observed blocked-siege deficit",new OperationKey(HIRE),
                                                object(StrictJson.object().put("holy_order_id",assessment.selected().orElseThrow().holyOrderId())),Purpose.WORLD_ACTION,plan);
                                        try {
                                            var prepared=MilitaryPlanningDecision.draft(request,selection,commands);
                                            requirePreparedQuote(same,frame,prepared,assessment.selected().orElseThrow(),producer);
                                            result=new Replace(prepared,selection.reason());
                                        } catch(RootRuntimeCommands.CommandUnavailable unavailable) {
                                            result=annotate(previous,"holy_order_reinforcement_observation",proposal.with("status",new Text("input_unavailable")).with("reason",new Text(unavailable.getMessage())));
                                        }
                                    }
                                }
                            } else result=defenders(same,request,previous,frame);
                            context.collector().requireHeldFrame(same,lease.frame());return result;
                        }));
                    } catch(IOException failure) {throw new UncheckedIOException("same-writer holy planning observation unavailable",failure);}
                }
            };
        }
        private void requirePreparedQuote(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Complete frame,Draft prepared,
                Candidate selected,PlayerHolyOrderContextRead producer) {
            var arguments=ArmyOrdinaryActionArguments.decode(prepared.command().orElseThrow().arguments());
            StrictJson.require(arguments.kind()==ArmyOrdinaryActionArguments.Kind.HIRE_HOLY_ORDER_V1&&arguments.preflightReads().size()==1,"holy reinforcement requires the actual Army preparation and one complete final quotation");
            var archive=context.archive().withSession(same);var reference=arguments.preflightReads().getFirst();var original=archive.loadRead(reference);
            requireOriginal(context,frame,original,reference);var finalQuote=producer.contract().replay(original);
            var rows=finalQuote.context().orders().stream().filter(order->order.holyOrderId()==selected.holyOrderId()).toList();
            StrictJson.require(finalQuote.context().available()&&rows.size()==1&&rows.getFirst().terms().isPresent()
                    &&rows.getFirst().terms().orElseThrow().resourceCostsRaw().equals(Optional.of(selected.quote())),"holy reinforcement final native cost changed since the actual selected proposal; replan without submit");
        }
        private Decision defenders(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,PlanningRequest request,Draft previous,Complete frame)throws IOException {
            var snapshot=request.observations().snapshot();
            if(!ready(snapshot))return annotate(previous,"ordinary_holy_war_candidate_observation",diagnostic(request,"frame_not_ready",null));
            var wars=army.quotes().producers().wars();var current=new ArmyRetreatFrames.Current(frame,request.deadline());
            var lease=wars.currentDeclarations(current);
            if(lease.isEmpty())lease=wars.canonicalDeclarations(same,context.readCatalog(),current);
            if(lease.isEmpty())return annotate(previous,"ordinary_holy_war_candidate_observation",diagnostic(request,"native_catalogue_unavailable","the current canonical declaration original is absent; no replacement prerequisite query was sent"));
            var choices=lease.orElseThrow().value().choices();int ordinal=-1;
            for(int i=0;i<choices.size();i++)if(HolyCostJsonAdapter.ORDINARY_HOLY_WAR_KEYS.contains(choices.get(i).casusBelliKey())){ordinal=i;break;}
            if(ordinal<0)return annotate(previous,"ordinary_holy_war_candidate_observation",diagnostic(request,"no_current_ordinary_holy_war_candidate",null));
            DeclarationContract.Choice selected=choices.get(ordinal);lease.orElseThrow().selected(current,selected.declarationId());
            var call=new ArmyCalls.Declaration(PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,revision(frame),selected.declarationId());
            var result=wars.read(same,context.readCatalog(),new ArmyWarReads.Selection(call,current,lease));
            if(!(result instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known))
                return annotate(previous,"ordinary_holy_war_candidate_observation",diagnostic(request,"query_failed",((PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation>)result).reason()));
            requireOriginal(context,frame,known.receipt(),known.originalReceipt());
            StrictJson.require(known.value() instanceof ArmyWarReadCodec.HolyContext,"holy-war read returned another typed domain");
            var holy=(ArmyWarReadCodec.HolyContext)known.value();
            return annotate(previous,"ordinary_holy_war_candidate_observation",defenderAnnotation(snapshot,holy,ordinal)
                    .with("original_read",value(known.originalReceipt().toJson())).with("original_declarations",value(lease.orElseThrow().evidence().toJson())));
        }
    }
    public record Need(int warId,int targetProvince,int garrison,int strength) {
        public Need {StrictJson.require(warId>0&&targetProvince>0&&strength>=0&&strength<garrison,"actual positive blocked-siege deficit required");}
        public int deficit(){return garrison-strength;}
    }
    public record Candidate(long holyOrderId,int sourceOrdinal,Optional<Long> priorEmployer,List<BigInteger> quote,int currentSoldiers) {
        public Candidate {quote=List.copyOf(quote);Objects.requireNonNull(priorEmployer);StrictJson.require(holyOrderId>=0&&holyOrderId<0xffff_ffffL&&sourceOrdinal>=0&&quote.size()==10&&currentSoldiers>=0,"actual bounded native order candidate required");}
    }
    public record Assessment(Optional<Need> need,Optional<Candidate> selected,Obj detail) {
        public Assessment {Objects.requireNonNull(need);Objects.requireNonNull(selected);Objects.requireNonNull(detail);}
    }
    static Optional<Need> need(Obj snapshot,Draft previous) {
        Value selected=previous.detail().get("selected_step");
        if(!previous.phase().equals("native_war_siege_exit_blocked")||previous.command().isPresent()
                ||selected!=null&&selected!=Nil.INSTANCE||!ready(snapshot))return Optional.empty();
        var plan=OpportunityJson.toNode(previous.detail());var siege=plan.get("siege_state");var pursuit=plan.get("pursuit");
        if(siege==null||!siege.isObject()||pursuit==null||!pursuit.isObject()
                ||!textEquals(siege.get("status"),"insufficient_strength")||!isTrue(siege.get("player_army_besieging")))return Optional.empty();
        var war=optionalInt(pursuit.get("war_id"));var province=optionalInt(siege.get("province_id"));
        var garrison=optionalInt(siege.get("garrison_size"));var strength=optionalInt(siege.get("besieging_strength"));
        if(war.isEmpty()||province.isEmpty()||garrison.isEmpty()||strength.isEmpty()||war.get()<1||province.get()<1||strength.get()<0||strength.get()>=garrison.get())return Optional.empty();
        JsonNode wars=OpportunityJson.toNode(snapshot).get("active_wars");if(wars==null||!wars.isArray())return Optional.empty();
        boolean found=false;for(JsonNode row:wars)if(row.isObject()&&optionalInt(row.get("war_id")).equals(war))found=true;
        return found?Optional.of(new Need(war.get(),province.get(),garrison.get(),strength.get())):Optional.empty();
    }
    static Assessment choose(Obj snapshot,Draft previous,PlayerHolyOrderContextRead.Observation observation) {
        var required=need(snapshot,previous);var out=StrictJson.object().put("schema","xar.ck3.holy-order-siege-reinforcement-proposal.v1")
                .put("status","not_applicable");out.set("source_frame",sourceFrame(snapshot));out.putNull("selected_step");var evaluations=out.putArray("candidate_rows");
        if(required.isEmpty()){out.putNull("military_need");return new Assessment(required,Optional.empty(),object(out));}
        Need need=required.orElseThrow();var needJson=out.putObject("military_need");needJson.put("war_id",need.warId()).put("target_province_id",need.targetProvince()).put("garrison_size",need.garrison()).put("besieging_strength",need.strength()).put("additional_soldiers_required",need.deficit());
        var raw=OpportunityJson.toNode(snapshot);var meta=observation.metadata();
        StrictJson.require(meta.queriedRevision().equals(StrictJson.integer(raw.get("revision"),BigInteger.ONE,StrictJson.UINT64_MAX))&&meta.queriedNativeRevision().equals(StrictJson.integer(raw.get("native_revision"),BigInteger.ONE,StrictJson.UINT64_MAX))
                &&meta.queriedSnapshotId().equals(raw.get("snapshot_id").textValue())&&meta.queryDateRaw()==raw.get("date_raw").intValue()
                &&meta.queriedPlayerCharacterId().equals(raw.get("played_character").get("character_id").bigIntegerValue()),"holy order proposal crossed its actual queried frame");
        var stocks=List.of(stock(raw,"gold"),stock(raw,"prestige"),stock(raw,"piety"));var stockJson=out.putObject("before_resource_stocks_raw");
        for(int i=0;i<3;i++){String key=List.of("gold","prestige","piety").get(i);if(stocks.get(i).isPresent())stockJson.put(key,stocks.get(i).orElseThrow());else stockJson.putNull(key);}
        var context=observation.context();if(!context.available()){out.put("status","input_unavailable");out.set("unavailable_reason",context.encode().get("unavailable_reason"));return new Assessment(required,Optional.empty(),object(out));}
        out.put("status","no_eligible_reinforcement");var candidates=new ArrayList<Candidate>();JsonNode originalRows=context.encode().get("rows");
        for(int i=0;i<context.orders().size();i++) {
            var order=context.orders().get(i);if(!order.military())continue;var terms=order.terms().orElseThrow();
            var original=originalRows.get(i).get("military_terms");var evaluation=evaluations.addObject().put("holy_order_id",order.holyOrderId()).put("source_ordinal",i);
            for(String field:List.of("can_hire","can_afford","can_hire_reason_literal","can_afford_reason_literal"))evaluation.set(field,original.get(field));
            String reason=null;Optional<Integer> troops=Optional.empty();JsonNode strength=original.get("troop_strength");
            if(order.employerId().equals(Optional.of(context.actorCharacterId())))reason="already_employed_by_player";
            else if(!terms.available())reason=original.get("unavailable_reason").textValue();
            else if(!terms.canHire().equals(Optional.of(true)))reason="native_can_hire_false";
            else if(!terms.canAfford().equals(Optional.of(true)))reason="native_can_afford_false";
            else if(strength==null||!isTrue(strength.get("available"))||(troops=optionalInt(strength.get("current_soldiers"))).isEmpty())reason="current_soldiers_unavailable";
            else if(troops.orElseThrow()<need.deficit())reason="current_troops_do_not_cover_measured_deficit";
            else for(int slot=0;slot<3;slot++) {
                String name=List.of("gold","prestige","piety").get(slot);var quote=terms.resourceCostsRaw().orElseThrow().get(slot);
                if(stocks.get(slot).isEmpty()){reason="current_"+name+"_stock_unavailable";break;}
                if(quote.signum()>0&&quote.compareTo(stocks.get(slot).orElseThrow())>0){reason="quoted_"+name+"_exceeds_current_stock";break;}
            }
            evaluation.put("status",reason==null?"eligible":"not_selected");if(reason==null){evaluation.putNull("reason");candidates.add(new Candidate(order.holyOrderId(),i,order.employerId(),terms.resourceCostsRaw().orElseThrow(),troops.orElseThrow()));}else evaluation.put("reason",reason);
        }
        var selected=candidates.stream().min(Comparator.comparing((Candidate c)->c.quote().get(2)).thenComparing(c->c.quote().get(0)).thenComparing(c->c.quote().get(1)).thenComparingLong(Candidate::holyOrderId).thenComparingInt(Candidate::sourceOrdinal));
        if(selected.isPresent()) {
            var row=selected.orElseThrow();out.put("status","actionable").put("selected_step",HIRE).put("holy_order_id",row.holyOrderId()).put("source_ordinal",row.sourceOrdinal()).put("current_soldiers",row.currentSoldiers());
            if(row.priorEmployer().isPresent())out.put("prior_employer_id",row.priorEmployer().orElseThrow());else out.putNull("prior_employer_id");
            var quote=out.putArray("native_quote_raw");row.quote().forEach(quote::add);
            out.put("ranking_policy","lowest_native_piety_then_gold_prestige_full_id").put("original_ai_ranking_observed",false);
        }
        return new Assessment(required,selected,object(out));
    }
    static Obj defenderAnnotation(Obj snapshot,ArmyWarReadCodec.HolyContext holy,int ordinal) {
        String status=holy.defenderJoin().isEmpty()?"defender_inputs_not_returned":!holy.defenderJoin().orElseThrow().nativeSetObserved()?"native_defender_set_unavailable":holy.defenderJoin().orElseThrow().joiners().isEmpty()?"no_extra_native_defenders_observed":"extra_native_defenders_observed";
        ObjectNode out=annotation(snapshot,status);out.put("source_ordinal",ordinal);ObjectNode original=(ObjectNode)OpportunityJson.toNode(holy.normalizedResult());
        for(String field:List.of("declaration_id","selected_declaration","final_can_send","cb_cost","generic_interaction_cost_raw","total_declaration_cost_raw","total_cost_ready","query_status","backend_id"))out.set(field,original.get(field));
        out.set("declaration_context_available",original.get("available"));out.set("declaration_context_unavailable_reason",original.get("unavailable_reason"));
        out.set(HolyWarDefenderJoinCodec.DOMAIN,holy.defenderJoin().map(join->(JsonNode)HolyWarDefenderJoinCodec.encode(join)).orElseGet(()->StrictJson.object().nullNode()));
        var roles=out.putObject("native_roles");for(String field:List.of("context_actor_character_id","context_recipient_character_id","context_additional_role_character_id","context_claimant_character_id","recipient_uses_native_fallback","additional_role_uses_native_fallback","claimant_uses_native_fallback"))roles.set(field,original.get(field));
        JsonNode child=out.get(HolyWarDefenderJoinCodec.DOMAIN);
        for(String field:List.of("primary_attacker_character_id","primary_defender_character_id","primary_defender_faith_available","primary_defender_faith_unavailable_reason","primary_defender_rite_id","primary_defender_faith_id","cb_flags_raw","defender_faith_can_join","native_joiner_set_observed","joiner_count","joiners","raw_scale","unit","is_final_join_score"))out.set(field,child.isNull()?null:child.get(field));
        out.set("defender_inputs_available",child.isNull()?null:child.get("available"));out.set("defender_inputs_unavailable_reason",child.isNull()?null:child.get("unavailable_reason"));
        JsonNode cost=original.get("cb_cost");out.set("cb_cost_available",cost!=null&&cost.isObject()?cost.get("available"):null);return object(out);
    }
    static Decision annotate(Draft previous,String key,Obj annotation) {
        return new Annotate(new Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),previous.purpose(),previous.domain(),previous.detail().with(key,annotation)),"current native holy observation retained the identical chosen action");
    }
    private static Obj diagnostic(PlanningRequest request,String status,String reason){var out=annotation(request.observations().snapshot(),status);if(reason!=null)out.put("reason",reason);return object(out);}
    private static ObjectNode annotation(Obj snapshot,String status){var out=StrictJson.object().put("status",status).put("read_only",true).put("automatic_declaration_enabled",false);out.set("source_frame",sourceFrame(snapshot));JsonNode wars=OpportunityJson.toNode(snapshot).get("active_wars");out.put("decision",wars!=null&&wars.isArray()&&!wars.isEmpty()?"continue_current_war":"observation_only");return out;}
    private static ObjectNode sourceFrame(Obj snapshot){var raw=OpportunityJson.toNode(snapshot);var out=StrictJson.object();for(String key:List.of("snapshot_id","revision","native_revision","date_raw"))out.set(key,raw.get(key));out.set("played_character_id",raw.get("played_character").get("character_id"));return out;}
    private static boolean ready(Obj snapshot){var raw=OpportunityJson.toNode(snapshot);var actor=raw.get("played_character");return isTrue(raw.get("paused"))&&isTrue(raw.get("map_ready"))&&actor!=null&&actor.isObject()&&isTrue(actor.get("alive"))&&nullish(raw.get("active_event"))&&nullish(raw.get("pending_character_interaction"));}
    private static Optional<BigInteger> stock(JsonNode snapshot,String name){JsonNode value=snapshot.get("played_character_"+name);if(value==null||!value.isObject()||value.get("raw")==null||!value.get("raw").isIntegralNumber()||value.get("scale")==null||!value.get("scale").isIntegralNumber()||!value.get("scale").bigIntegerValue().equals(BigInteger.valueOf(100000)))return Optional.empty();return Optional.of(value.get("raw").bigIntegerValue());}
    private static Optional<Integer> optionalInt(JsonNode value){return value!=null&&value.isIntegralNumber()&&value.canConvertToInt()?Optional.of(value.intValue()):Optional.empty();}
    private static boolean textEquals(JsonNode value,String expected){return value!=null&&value.isTextual()&&value.textValue().equals(expected);}
    private static boolean isTrue(JsonNode value){return value!=null&&value.isBoolean()&&value.booleanValue();}
    private static boolean nullish(JsonNode value){return value==null||value.isNull();}
    private static Obj object(JsonNode value){return OpportunityJson.object(DriverJson.fromNode(value),"complete holy policy JSON object");}
    private static Value value(JsonNode value){return DriverJson.fromNode(value);}
    private static ArmyCalls.Revision revision(Complete frame){return new ArmyCalls.Revision(new ArmyTypes.Present<>(frame.identity().frame().revision()));}
    private static void requireOriginal(RootRuntimeContext context,Complete frame,PlanningReadReceipt read,ExactRef reference){var archive=context.archive();NativeRecordedEvidenceVerifier.requireRead(read,archive);StrictJson.require(archive.readReferenceOf(read).equals(reference),"holy original read reference changed");ArmyOrdinaryPreflight.bind(read,frame);}
}
