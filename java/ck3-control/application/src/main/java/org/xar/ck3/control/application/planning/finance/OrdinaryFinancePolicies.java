package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.application.effects.FinanceEvidenceArchive;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.WarFinancingCapabilityGap;

/** Sole pending barrier, current-cash reinforcement and faction-gift producers. No action is submitted here. */
public final class OrdinaryFinancePolicies {
    public static final OperationKey CONSTRUCTION=new OperationKey("g2_player_world_building_action_private_v1");
    public static final OperationKey MERCENARY=new OperationKey("hire-mercenary-v1");
    public static final OperationKey GIFT=new OperationKey("private-submit-faction-gift-member-v1");
    public static final OperationKey FEAST=new OperationKey("start-activity-feast-stage5-v1-private");
    public static final OperationKey FEAST_CONFIG=new OperationKey("open-activity-feast-planner-v1-private");
    /** Reconciliation scope includes domain leaves installed by the construction and Feast owners. */
    public static final Set<OperationKey> OWNED=Set.of(CONSTRUCTION,MERCENARY,GIFT,FEAST,FEAST_CONFIG);
    /** Only exact installed independent handlers can provide an expected result. */
    public interface Effects {
        Optional<ExpectedPostcondition> expected(OperationKey operation,PlanningRequest request,Obj validatedArguments);
    }
    @FunctionalInterface public interface PendingContributor {
        /** Empty means no actual pending body. A contributor cannot select another new spending action. */
        Optional<OrdinaryPolicy.Decision> pending(PlanningRequest request,OrdinaryPolicy.Draft previous);
    }
    private final ExactRef source; private final OrdinaryFinanceCollector collector; private final Effects effects;
    private final List<PendingContributor> pendingContributors;
    private final Optional<FinanceEvidenceArchive> quoteEvidence;
    public OrdinaryFinancePolicies(ExactRef source,OrdinaryFinanceCollector collector,Effects effects,List<PendingContributor> orderedPendingContributors) {
        this(source,collector,effects,orderedPendingContributors,Optional.empty());
    }
    public OrdinaryFinancePolicies(ExactRef source,OrdinaryFinanceCollector collector,Effects effects,List<PendingContributor> orderedPendingContributors,FinanceEvidenceArchive quoteEvidence) {
        this(source,collector,effects,orderedPendingContributors,Optional.of(Objects.requireNonNull(quoteEvidence)));
    }
    private OrdinaryFinancePolicies(ExactRef source,OrdinaryFinanceCollector collector,Effects effects,List<PendingContributor> orderedPendingContributors,Optional<FinanceEvidenceArchive> quoteEvidence) {
        this.source=Objects.requireNonNull(source);this.collector=Objects.requireNonNull(collector);
        this.effects=Objects.requireNonNull(effects);this.pendingContributors=List.copyOf(orderedPendingContributors);
        this.quoteEvidence=Objects.requireNonNull(quoteEvidence);
    }
    public List<OrdinaryPolicy> stages() { return List.of(new Stage(PlanningStage.PENDING_MATERIAL_PUBLICATION),
            new Stage(PlanningStage.WAR_MERCENARY_CURRENT_CASH),new Stage(PlanningStage.FACTION_GIFT)); }
    /** Public Army route delegates to this same complete finance body, then submits through the sole Root coordinator. */
    public ActionCommand publicHire(Session borrowed,PlanningRequest actual,BigInteger companyId,String actionId) {
        org.xar.ck3.control.contracts.StrictJson.text(actionId);require(ordinaryFrame(actual)&&actual.observations().actionSteps().contains(MERCENARY),"actual legal paused hire route unavailable");
        var result=collector.current(borrowed,actual);if(!(result instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Current> known))throw new IllegalArgumentException("actual full finance quote unavailable");
        var current=known.value();
        var ledger=current.state().ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow();
        require(MercenaryProcurement.barrier(actual.observations().snapshot(),MercenaryProcurement.decode(ledger.document().bytes()))==MercenaryProcurement.NewHireBarrier.CLEAR,"actual durable procurement forbids another hire");
        var company=current.market().companies().stream().filter(value->value.id().equals(companyId)).toList();require(company.size()==1,"public hire requires one actual full CompanyID");
        Obj decision=publicDecision(actual,current.root(),current.market(),company.getFirst());
        Obj args=obj("company_id",new IntegerValue(companyId),"pre_capture_epoch",new IntegerValue(current.market().captureEpoch()),"decision",decision,
                "operational_detail",obj("explicit_public_request",new Bool(true)),"source_frame",OrdinaryFinanceCollector.sourceFrame(actual),"quoted_company",company.getFirst().original(),
                "pre_player_army_ids",new Arr(array(actual.observations().snapshot().get("player_armies"),"actual armies").stream().map(value->object(value,"actual army").get("army_id")).toList()),
                "explicit_public_hire",new Bool(true));
        args=quoteEvidence.orElseThrow().bind(borrowed,actual,MERCENARY,current,Optional.empty(),args);
        return new ActionCommand(actionId,actual.before(),actual.source(),actual.sessionId(),MERCENARY,args,effects.expected(MERCENARY,actual,args).orElseThrow(),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of("mercenary-company:"+companyId)),actual.deadline());
    }
    /** Explicit public Gift selection uses the same live quote, budget, pending and independent material producer. */
    public ActionCommand publicGift(Session same,PlanningRequest actual,Obj suppliedCandidate,Obj suppliedCheckpoint,String actionId) {
        require(actual.observations().actionSteps().contains(GIFT),"actual Gift action registration absent");
        var read=collector.current(same,actual);
        if(!(read instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Current> currentKnown))
            throw new IllegalArgumentException("complete current finance source required for public Gift");
        var current=currentKnown.value();
        Obj suppliedChoice=object(suppliedCandidate.get("choice"),"actual public candidate choice");
        BigInteger minimum=giftMinimumReserve(suppliedChoice);
        var selected=collector.gift(same,actual,current,minimum);
        if(!(selected instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Gift> giftKnown))
            throw new IllegalArgumentException("current native Gift eligibility/budget/checkpoint is unavailable");
        var gift=giftKnown.value();
        requirePublicGiftSelection(object(gift.candidate().get("choice"),"actual Gift choice"),gift.candidate().get("observation"),minimum,gift.checkpoint(),suppliedCandidate,suppliedCheckpoint);
        Obj args=obj("choice",object(parse(FactionGiftPolicy.encode(gift.selected())),"actual gift choice"),
                "minimum_gold_reserve_raw",new IntegerValue(minimum),"candidate",gift.candidate(),
                "pre_faction_alert",gift.nativeAlert(),"source_frame",OrdinaryFinanceCollector.sourceFrame(actual),
                "checkpoint_sha256",new Text(gift.checkpoint().saveReference().sha256()));
        args=quoteEvidence.orElseThrow().bind(same,actual,GIFT,current,Optional.of(gift),args);
        return new ActionCommand(actionId,actual.before(),actual.source(),actual.sessionId(),GIFT,args,
                effects.expected(GIFT,actual,args).orElseThrow(),new Claims(Set.of(),Set.of(),Set.of(gift.selected().recipientCharacterId()),
                Set.of("faction-gift:"+gift.selected().sourceFactionId())),actual.deadline());
    }
    /** The selected reserve survives public projection, command persistence and final current-budget revalidation. */
    static BigInteger giftMinimumReserve(Obj retained) {
        BigInteger minimum=integer(retained.get("minimum_gold_reserve_raw"),"original Gift minimum reserve");
        require(minimum.signum()>=0,"original Gift minimum reserve must be nonnegative");
        return minimum;
    }
    /** Pure source-selection comparison only; constructing these DATA arguments never grants submission authority. */
    static void requirePublicGiftSelection(Obj sourceChoice,Value sourceObservation,BigInteger minimum,FinanceStatePort.Checkpoint sourceCheckpoint,
            Obj suppliedCandidate,Obj suppliedCheckpoint) {
        Obj suppliedChoice=object(suppliedCandidate.get("choice"),"supplied public Gift choice");
        var exactChoice=new java.util.LinkedHashMap<String,Value>(object(sourceChoice,"quoted Gift choice").members());
        exactChoice.remove("status");exactChoice.remove("reason");
        exactChoice.put("minimum_gold_reserve_raw",new IntegerValue(minimum));
        require(new Obj(exactChoice).equals(suppliedChoice)
                &&sourceObservation.equals(suppliedCandidate.get("observation")),
                "public Gift must retain this same current native candidate and observation");
        require(new Text(sourceCheckpoint.saveReference().sha256()).equals(suppliedCheckpoint.get("sha256"))
                &&new Text(sourceCheckpoint.episodeRunId()).equals(suppliedCheckpoint.get("episode_run_id"))
                &&new IntegerValue(sourceCheckpoint.dateRaw()).equals(suppliedCheckpoint.get("date_raw")),
                "public Gift checkpoint differs from the actual saved checkpoint");
    }
    private static Obj publicDecision(PlanningRequest actual,Obj root,NativeMercenaryMarket.Observation market,NativeMercenaryMarket.Company company) {
        require(market.available()&&company.employer().isEmpty()&&company.terms().available()
                &&company.terms().canHire()==NativeMercenaryMarket.Truth.TRUE&&company.terms().canAfford()==NativeMercenaryMarket.Truth.TRUE,
                "actual native hire/affordability rejects the selected public company");
        var costs=company.terms().costs().orElseThrow();require(costs.size()==10&&costs.stream().allMatch(value->value.signum()>=0),"complete ten-resource quote required");
        Obj finance=object(parse(org.xar.ck3.control.warbudget.OrdinaryWarPriority.finance(new org.xar.ck3.control.warbudget.OrdinaryWarPriority.FinanceRequest(
                new org.xar.ck3.control.warbudget.OrdinaryWarPriority.Input(org.xar.ck3.control.application.driver.DriverJson.encode(actual.observations().snapshot()),org.xar.ck3.control.application.driver.DriverJson.encode(root)),Optional.of(costs.getFirst()),company.terms().durationMonths(),
                BigInteger.valueOf(20000000),18,BigInteger.ZERO))),"actual current contract and military allocation");
        require(new Text("available").equals(finance.get("status"))&&new Bool(true).equals(finance.get("retains_military_allocation")),"public hire cannot spend unavailable or retained military cash");
        return obj("status",new Text("explicit_public_hire_qualified"),"selected_candidate",obj("company_id",new IntegerValue(company.id()),"gold_cost_raw",new IntegerValue(costs.getFirst()),
                "predicted_auto_raise_province_id",company.spawnProvince().<Value>map(IntegerValue::new).orElse(Nil.INSTANCE),"purpose_war_ids",new Arr(List.of()),"finance",finance),
                "future_funding_credited_raw",new IntegerValue(BigInteger.ZERO));
    }
    private final class Stage implements OrdinaryPolicy {
        private final PlanningStage stage; private Stage(PlanningStage stage){this.stage=stage;}
        @Override public PlanningStage stage(){return stage;}
        @Override public ExactRef implementationSource(){return source;}
        @Override public Decision evaluate(PlanningRequest request,Draft previous) {
            try { return switch(stage) {
                case PENDING_MATERIAL_PUBLICATION -> pending(request,previous);
                case WAR_MERCENARY_CURRENT_CASH -> mercenary(request,previous);
                case FACTION_GIFT -> gift(request,previous);
                default -> throw new IllegalStateException("unowned finance stage");
            }; } catch(IllegalArgumentException unavailable) {
                return defer("current typed finance input rejected: "+unavailable.getMessage(),stage.name());
            }
        }
    }
    private OrdinaryPolicy.Decision pending(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        for(PendingContributor contributor:pendingContributors) {
            Optional<OrdinaryPolicy.Decision> observed=Objects.requireNonNull(contributor.pending(request,previous));
            if(observed.isPresent()) {
                OrdinaryPolicy.Decision decision=observed.orElseThrow();
                require(decision instanceof OrdinaryPolicy.ReconcileExisting || decision instanceof OrdinaryPolicy.Defer
                        || decision instanceof OrdinaryPolicy.Wait || decision instanceof OrdinaryPolicy.Refresh
                        || decision instanceof OrdinaryPolicy.Stop,"pending contributor may only reconcile or wait for real evidence");
                return decision;
            }
        }
        var retained=collector.state(request);
        if(!(retained instanceof FinanceStatePort.Known known))return defer(((FinanceStatePort.Missing)retained).reason(),"pending_material");
        List<ActionReceipt> unresolved=known.snapshot().unresolved().stream().filter(r->OWNED.contains(r.command().operation())).toList();
        if(unresolved.size()>1)return defer("multiple original unresolved finance commands require exact reconciliation scope","pending_material");
        if(unresolved.size()==1){ActionReceipt receipt=unresolved.get(0);return new OrdinaryPolicy.ReconcileExisting(receipt.command().actionId(),
                obj("original_command",object(parse(ActionCodec.encodeCommand(receipt.command())),"original action command"),
                    "original_receipt_sequence",new IntegerValue(BigInteger.valueOf(receipt.sequence())),
                    "original_body_sha256",new Text(receipt.bodySha256()),"business_credit",new Bool(false)),
                "independently observe the durable original finance command; UNKNOWN is never resubmitted");}
        for(FinanceStatePort.Domain domain:List.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,
                FinanceStatePort.Domain.MERCENARY,FinanceStatePort.Domain.FEAST)) {
            var ledger=known.snapshot().ledger(domain);
            if(ledger.isEmpty())return defer("original "+domain+" ledger is not imported; no implicit CLEAR","pending_material");
            if(ledger.orElseThrow().pending()==FinanceStatePort.Pending.PENDING)
                return defer("legacy "+domain+" pending body needs original command import before exact reconciliation","pending_material");
        }
        return new OrdinaryPolicy.Keep("actual imported finance pending bodies explicitly clear");
    }
    private OrdinaryPolicy.Decision mercenary(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        if(!request.observations().warInProgress()||!ordinaryFrame(request))return new OrdinaryPolicy.NotApplicable("mercenary current-cash stage preserves selected war/window work");
        if(!quiet(previous))return observeRecovery(request,previous);
        var current=collector.current(request);
        if(!(current instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Current> known))return missing(current,"war_cash");
        var c=known.value();var procurement=c.state().ledger(FinanceStatePort.Domain.MERCENARY);
        if(procurement.isEmpty()||procurement.orElseThrow().pending()!=FinanceStatePort.Pending.CLEAR)return defer("actual mercenary procurement ledger unavailable or pending","war_cash");
        Obj gap=OrdinaryFinanceCollector.financingGap(request,c);
        if(WarFinancingCapabilityGap.observe(FinancingGapCodec.decode(org.xar.ck3.control.application.driver.DriverJson.encode(gap))).isPresent())
            previous=financingObservation(previous,gap,collector.loan(request));
        var durable=MercenaryProcurement.decode(procurement.orElseThrow().document().bytes());
        var barrier=MercenaryProcurement.barrier(request.observations().snapshot(),durable);
        if(barrier!=MercenaryProcurement.NewHireBarrier.CLEAR)return annotate(previous,"war_mercenary_pending_v1",
                obj("status",new Text(barrier.name()),"unknown_replay_allowed",new Bool(false)),"actual original mercenary procurement blocks another hire");
        var choice=OrdinaryMercenaryChoice.assess(request,previous,c.priority(),c.market(),Optional.of(c.root()),procurement.orElseThrow(),c.spending());
        if(choice.selected().isEmpty())return annotate(previous,"war_mercenary_decision_v1",choice.original(),"current actual mercenary assessment retained");
        var company=choice.selected().orElseThrow();
        Obj args=obj("company_id",new IntegerValue(company.id()),"pre_capture_epoch",new IntegerValue(c.market().captureEpoch()),
                "decision",choice.original(),"operational_detail",previous.detail(),"source_frame",OrdinaryFinanceCollector.sourceFrame(request),"quoted_company",company.original(),
                "pre_player_army_ids",new Arr(array(request.observations().snapshot().get("player_armies"),"actual armies").stream()
                    .map(value->object(value,"army").get("army_id")).toList()));
        args=quoteEvidence.orElseThrow(()->new IllegalArgumentException("actual original finance quote archive is not installed")).bind(request,MERCENARY,c,Optional.empty(),args);
        return selected(request,previous,MERCENARY,args,"war_mercenary_native_hire","native-legal current-cash local reinforcement",Domain.war,
                OrdinaryPolicy.Purpose.WORLD_ACTION,new Claims(Set.of(),Set.of(),Set.of(),Set.of("mercenary-company:"+company.id())),choice.original());
    }
    private OrdinaryPolicy.Decision gift(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        if(!quiet(previous)||!ordinaryFrame(request))return new OrdinaryPolicy.NotApplicable("faction gift preserves independently selected work");
        var current=collector.current(request);
        if(!(current instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Current> known))return missing(current,"faction_gift");
        var gift=collector.gift(request,known.value());
        if(!(gift instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Gift> chosen))return missing(gift,"faction_gift");
        var g=chosen.value();Obj args=obj("choice",object(parse(FactionGiftPolicy.encode(g.selected())),"actual gift choice"),
                "minimum_gold_reserve_raw",new IntegerValue(g.minimumGoldReserveRaw()),
                "candidate",g.candidate(),"pre_faction_alert",g.nativeAlert(),"source_frame",OrdinaryFinanceCollector.sourceFrame(request),
                "checkpoint_sha256",new Text(g.checkpoint().saveReference().sha256()));
        args=quoteEvidence.orElseThrow(()->new IllegalArgumentException("actual original finance quote archive is not installed")).bind(request,GIFT,known.value(),Optional.of(g),args);
        return selected(request,previous,GIFT,args,"faction_gift_typed_submit","native legal budgeted dangerous-faction mitigation gift",Domain.diplomacy,
                OrdinaryPolicy.Purpose.WORLD_ACTION,new Claims(Set.of(),Set.of(),Set.of(g.selected().recipientCharacterId()),Set.of("faction-gift:"+g.selected().sourceFactionId())),g.candidate());
    }
    private OrdinaryPolicy.Decision observeRecovery(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        var actual=collector.state(request);if(!(actual instanceof FinanceStatePort.Known known))return new OrdinaryPolicy.NotApplicable("actual original emergency recovery body unavailable; current war order retained");
        var body=known.snapshot().ledger(FinanceStatePort.Domain.MERCENARY);if(body.isEmpty())return new OrdinaryPolicy.NotApplicable("actual original mercenary body unavailable; current war order retained");
        Optional<Obj> root=Optional.empty();var read=collector.query(FinanceReadContracts.Query.ROOT,request);
        if(read instanceof OrdinaryFinanceCollector.Known<FinanceReadContracts.Packet> value&&value.value().result().get("campaign_root_context") instanceof Obj actualRoot)root=Optional.of(actualRoot);
        var recovery=MercenaryProcurement.recovery(request.observations().snapshot(),MercenaryProcurement.decode(body.orElseThrow().document().bytes()),root);
        return recovery.<OrdinaryPolicy.Decision>map(value->annotate(previous,"war_emergency_recovery_v1",value,"actual emergency cash-buffer recovery retained beside the current war order"))
                .orElseGet(()->new OrdinaryPolicy.NotApplicable("no source-qualified prior emergency procurement"));
    }
    private OrdinaryPolicy.Decision selected(PlanningRequest request,OrdinaryPolicy.Draft previous,OperationKey operation,Obj args,String phase,String reason,
            Domain domain,OrdinaryPolicy.Purpose purpose,Claims claims,Obj detail) {
        if(!request.observations().actionSteps().contains(operation))return defer("actual action registration absent: "+operation.value(),phase);
        Optional<ExpectedPostcondition> expected=effects.expected(operation,request,args);
        if(expected.isEmpty())return defer("actual independent material handler absent: "+operation.value(),phase);
        String actionId=ActionIds.forDecision(request.sessionId(),request.before(),operation.value()+":"+ActionCodec.sha256(org.xar.ck3.control.application.driver.DriverJson.encode(args)));
        ActionCommand command=new ActionCommand(actionId,request.before(),request.source(),request.sessionId(),operation,args,expected.orElseThrow(),claims,request.deadline());
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("ordinary-finance-java-v1",phase,reason,OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command),purpose,Optional.of(domain),obj("step",new Text(operation.value()),"assessment",detail,"original_plan",previous.detail(),"arguments",args)),reason);
    }
    /** Run by the exact registered preparation inside the sole writer lock, before its intent is appended. */
    public void revalidate(Session borrowed,ActionCommand command,PlanningRequest fresh) {
        quoteEvidence.orElseThrow(()->new IllegalArgumentException("original finance quote verifier is not installed")).verify(borrowed,command);
        require((command.operation().equals(MERCENARY)||command.operation().equals(GIFT))
                &&command.before().equals(fresh.before())&&command.source().equals(fresh.source())
                &&command.sessionId().equals(fresh.sessionId())&&ordinaryFrame(fresh),"finance dispatch current source drift");
        var observed=collector.current(borrowed,fresh);
        if(!(observed instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Current> known))
            throw new IllegalArgumentException("fresh current finance inputs unavailable");
        var current=known.value();
        if(command.operation().equals(MERCENARY)) {
            var procurement=current.state().ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow();
            require(procurement.pending()==FinanceStatePort.Pending.CLEAR,"original mercenary pending must be reconciled");
            require(MercenaryProcurement.barrier(fresh.observations().snapshot(),MercenaryProcurement.decode(procurement.document().bytes()))
                    ==MercenaryProcurement.NewHireBarrier.CLEAR,"actual original procurement prohibits another hire");
            if(new Bool(true).equals(command.arguments().get("explicit_public_hire"))) {
                var company=current.market().companies().stream().filter(value->new IntegerValue(value.id()).equals(command.arguments().get("company_id"))).toList();
                require(company.size()==1&&company.getFirst().original().equals(command.arguments().get("quoted_company"))
                        &&publicDecision(fresh,current.root(),current.market(),company.getFirst()).equals(command.arguments().get("decision")),"current public hire terms/cash drift");
                require(effects.expected(MERCENARY,fresh,command.arguments()).filter(command.expected()::equals).isPresent(),"public hire material expected contract drift");return;
            }
            var originalDetail=object(command.arguments().get("operational_detail"),"original operational comparison basis");
            var basis=new OrdinaryPolicy.Draft("retained-operational-comparison","final-lock","original comparison details",
                    OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),originalDetail);
            var choice=OrdinaryMercenaryChoice.assess(fresh,basis,current.priority(),current.market(),Optional.of(current.root()),procurement,current.spending());
            var selected=choice.selected().orElseThrow(()->new IllegalArgumentException("fresh cash/quote no longer selects a company"));
            require(new IntegerValue(selected.id()).equals(command.arguments().get("company_id"))
                    &&selected.original().equals(command.arguments().get("quoted_company"))
                    &&choice.original().equals(command.arguments().get("decision"))
                    &&current.market().captureEpoch().compareTo(integer(command.arguments().get("pre_capture_epoch"),"planned native market epoch"))>=0,
                    "fresh selected mercenary quote, cash or purpose changed");
        } else {
            var result=collector.gift(borrowed,fresh,current,giftMinimumReserve(command.arguments()));
            if(!(result instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.Gift> knownGift))
                throw new IllegalArgumentException("fresh faction/cash/checkpoint unavailable");
            var gift=knownGift.value();
            require(object(parse(FactionGiftPolicy.encode(gift.selected())),"fresh gift choice").equals(command.arguments().get("choice"))
                    &&gift.candidate().equals(command.arguments().get("candidate"))
                    &&new IntegerValue(gift.minimumGoldReserveRaw()).equals(command.arguments().get("minimum_gold_reserve_raw"))
                    &&gift.nativeAlert().equals(command.arguments().get("pre_faction_alert"))
                    &&new Text(gift.checkpoint().saveReference().sha256()).equals(command.arguments().get("checkpoint_sha256")),
                    "fresh gift source, threat, budget or checkpoint changed");
        }
        require(effects.expected(command.operation(),fresh,command.arguments()).filter(command.expected()::equals).isPresent(),
                "fresh independent expected material contract changed");
    }
    private static boolean ordinaryFrame(PlanningRequest request) {
        return request.observations().paused()&&request.observations().mapReady()&&!request.observations().foregroundPresent()
                &&new Bool(true).equals(object(request.observations().snapshot().get("played_character"),"player").get("alive"));
    }
    public static boolean quiet(OrdinaryPolicy.Draft previous) {
        if(previous.kind()!=OrdinaryPolicy.Kind.ORDINARY)return false;
        return previous.command().isEmpty()||previous.purpose()==OrdinaryPolicy.Purpose.DATE_ADVANCE;
    }
    private static OrdinaryPolicy.Decision annotate(OrdinaryPolicy.Draft previous,String key,Value value,String reason) {
        var fields=new java.util.LinkedHashMap<>(previous.detail().members());fields.put(key,value);
        return new OrdinaryPolicy.Annotate(new OrdinaryPolicy.Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),previous.purpose(),previous.domain(),new Obj(fields)),reason);
    }
    /** Actual ordinary-war diagnostic consumer. Missing CASH never blocks the existing war action or supplies funds. */
    static OrdinaryPolicy.Draft financingObservation(OrdinaryPolicy.Draft previous,Obj gap,
            OrdinaryFinanceCollector.Read<OrdinaryFinanceCollector.LoanObservation> observed) {
        Optional<OrdinaryFinanceCollector.LoanObservation> loan=observed instanceof OrdinaryFinanceCollector.Known<OrdinaryFinanceCollector.LoanObservation> known
                ?Optional.of(known.value()):Optional.empty();
        Obj request=OrdinaryFinanceCollector.financingRequest(gap,loan,Nil.INSTANCE);
        var assessment=EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(org.xar.ck3.control.application.driver.DriverJson.encode(request)));
        var fields=new java.util.LinkedHashMap<>(previous.detail().members());
        fields.put("emergency_financing_assessment",org.xar.ck3.control.application.driver.DriverJson.object(EmergencyFinancingAssessmentCodec.encode(assessment),262_144));
        fields.remove("war_financing_loan_read_unavailable");
        if(observed instanceof OrdinaryFinanceCollector.Unavailable<OrdinaryFinanceCollector.LoanObservation> missing)
            fields.put("war_financing_loan_read_unavailable",new Text(missing.missing().reason()));
        return new OrdinaryPolicy.Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),previous.purpose(),previous.domain(),new Obj(fields));
    }
    private static OrdinaryPolicy.Defer defer(String reason,String stage){return new OrdinaryPolicy.Defer(reason,obj("stage",new Text(stage),"future_funding_credited_raw",new IntegerValue(BigInteger.ZERO),"continue_ordinary_war",new Bool(true)));}
    private static OrdinaryPolicy.Decision missing(OrdinaryFinanceCollector.Read<?> read,String stage){return defer(((OrdinaryFinanceCollector.Unavailable<?>)read).missing().reason(),stage);}
}
