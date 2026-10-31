package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageNativeRequests;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual held originals -> route's fresh native reads -> complete policy review; cold replay never issues a query. */
public final class RootFamilyMarriageFreshPreparation {
    public static final String SCHEMA="xar.java.family-fresh-marriage-review/v1";
    private static final int MAX=16*1024*1024;
    private static final List<Slot> SLOTS=List.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE);
    public record Fresh(FamilyNativePreparation.VerifiedBasis basis,List<ExactRef> freshReads,ExactRef reviewManifest) {
        public Fresh {Objects.requireNonNull(basis);freshReads=List.copyOf(freshReads);Objects.requireNonNull(reviewManifest);
            StrictJson.require(basis.preparedPlan().isPresent()&&!freshReads.isEmpty()&&freshReads.size()<=32&&reviewManifest.bytes()>0,
                    "actual complete reviewed marriage preparation and its original manifest are required");}
    }
    private record Read(FamilyPorts.Query query,Obj requested,ExactRef original) { }
    @FunctionalInterface private interface QueryReader {FamilyPorts.ObservedRead read(FamilyPorts.Query query,Obj arguments)throws IOException;}
    private final RootRuntimeContext context;
    private final RootFamilyBridge bridge;
    private final RootFamilyReadProducts products;
    private final RootFamilyNativeReadProducts nativeProducts;
    private final RootFamilyPlanningOriginals originals;
    private final RootFamilyMarriageSendAuthority.FreshContracts contracts;
    private final ExactRef implementation;
    public RootFamilyMarriageFreshPreparation(RootRuntimeContext actual,RootFamilyBridge sameBridge,RootFamilyNativeReadProducts actualNativeProducts,RootFamilyReadProducts actualProducts,
            RootFamilyPlanningOriginals sameOriginals,ExactRef implementation) {
        context=Objects.requireNonNull(actual);bridge=Objects.requireNonNull(sameBridge);products=Objects.requireNonNull(actualProducts);
        nativeProducts=Objects.requireNonNull(actualNativeProducts);nativeProducts.requireContext(context);nativeProducts.requireComplete(products);
        originals=Objects.requireNonNull(sameOriginals);contracts=nativeProducts.freshContracts();this.implementation=Objects.requireNonNull(implementation);
        products.requireContext(context);originals.requireContext(context);StrictJson.require(implementation.bytes()>0,"actual fresh-review implementation required");
    }
    public void requireContext(RootRuntimeContext actual) {StrictJson.require(context==actual,"fresh marriage producer belongs to another physical Game");}
    public RootFamilyMarriageSendAuthority.FreshContracts freshContracts() {return contracts;}
    public RootFamilyPlanningOriginals planningOriginals() {return originals;}
    public FamilyNativePreparation.Replay replay() {return this::replayOriginal;}
    public Fresh prepare(Session same,ActionCommand command)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(command.deadline());
        StrictJson.require(ActionCommandScope.current().filter(command::equals).isPresent(),"actual family primitive command scope required");
        Optional<ExactRef> publicQuery=publicQuery(command);
        if(publicQuery.isPresent())return preparePublic(same,command,publicQuery.orElseThrow());
        ExactRef requestRef=originals.reference(same,command);PlanningRequest request=originals.original(same,command,requestRef);
        return context.collector().currentPlanning(same,request,command,command.deadline(),(exact,lease)->{
            var basis=bridge.verified(same,lease,command);var head=same.head();
            Map<Slot,ExactRef> domains=new EnumMap<>(Slot.class);
            for(Slot slot:SLOTS) {
                var read=same.readDomain(slot);if(!(read instanceof DomainBodies.Available body))throw new IOException("actual full family domain is missing: "+slot);
                domains.put(slot,body.reference().payload());
            }
            var state=state(same,head.state().sequence(),head.digest(),domains);
            List<Read> retained=new ArrayList<>();
            Obj plan=review(command,basis.snapshot(),basis.bridgeIdentity(),state,(query,args)->{
                FamilyPorts.ObservedRead observed=currentRead(same,exact,query,args);
                retained.add(new Read(query,args,observed.originalReceipt()));return observed;
            });
            verifyFreshContracts(same,command,retained);
            var manifest=StrictJson.object().put("schema",SCHEMA).put("command_sha256",ActionCodec.sha256(ActionCodec.encodeCommand(command)))
                    .put("head_sequence",head.state().sequence()).put("head_digest",head.digest()).put("origin","ORDINARY_PLANNING");
            manifest.set("implementation",implementation.toJson());manifest.set("planning_request",requestRef.toJson());
            manifest.putNull("public_original_query");
            manifest.set("snapshot",basis.snapshotEvidence().toJson());manifest.set("bridge",basis.bridgeEvidence().toJson());
            var domainRows=manifest.putObject("domains");domains.forEach((slot,ref)->domainRows.set(slot.name(),ref.toJson()));
            var rows=manifest.putArray("reads");for(var read:retained) {
                var row=rows.addObject().put("query",read.query().name());row.set("requested",OpportunityJson.toNode(read.requested()));row.set("original",read.original().toJson());
            }
            manifest.set("prepared_plan",OpportunityJson.toNode(plan));
            ExactRef ref=context.archive().preserveMaterial(encodeReviewMaterial(manifest));
            StrictJson.require(same.head().digest().equals(head.digest()),"writer head changed during observation-only family preparation");
            return new Fresh(new FamilyNativePreparation.VerifiedBasis(basis.snapshot(),basis.bridgeIdentity(),basis.snapshotEvidence(),basis.bridgeEvidence(),Optional.of(plan)),
                    retained.stream().map(Read::original).toList(),ref);
        });
    }
    private Fresh preparePublic(Session same,ActionCommand command,ExactRef originalQuery)throws IOException {
        verifyPublicOriginal(same,command,originalQuery);
        return context.readiness().current(same,command.before(),command.deadline(),lease->{
            var basis=bridge.verified(same,lease,command);
            List<Read> retained=new ArrayList<>();
            Obj plan=review(command,basis.snapshot(),basis.bridgeIdentity(),Optional.empty(),(query,args)->{
                StrictJson.require(query==FamilyPorts.Query.RULER_CHOICES,"public ruler cannot borrow private family/domain reads");
                var actual=nativeProducts.currentRuler(same,command,lease);retained.add(new Read(query,args,actual.originalReceipt()));return actual;
            });
            verifyFreshContracts(same,command,retained);
            var m=StrictJson.object().put("schema",SCHEMA).put("command_sha256",ActionCodec.sha256(ActionCodec.encodeCommand(command))).put("origin","PUBLIC_RULER");
            m.putNull("head_sequence");m.putNull("head_digest");m.putNull("domains");m.putNull("planning_request");
            m.set("implementation",implementation.toJson());m.set("public_original_query",originalQuery.toJson());
            m.set("snapshot",basis.snapshotEvidence().toJson());m.set("bridge",basis.bridgeEvidence().toJson());
            var rows=m.putArray("reads");for(var read:retained) {var row=rows.addObject().put("query",read.query().name());row.set("requested",OpportunityJson.toNode(read.requested()));row.set("original",read.original().toJson());}
            m.set("prepared_plan",OpportunityJson.toNode(plan));var ref=context.archive().preserveMaterial(encodeReviewMaterial(m));
            return new Fresh(new FamilyNativePreparation.VerifiedBasis(basis.snapshot(),basis.bridgeIdentity(),basis.snapshotEvidence(),basis.bridgeEvidence(),Optional.of(plan)),retained.stream().map(Read::original).toList(),ref);
        });
    }
    private static Optional<ExactRef> publicQuery(ActionCommand command) {
        if(!command.operation().value().startsWith("arrange-marriage-"))return Optional.empty();
        var intent=RulerMarriageIntent.fromJson(command.arguments());if(intent.planningProof().isEmpty())return Optional.empty();var proof=intent.planningProof().orElseThrow();
        if(!proof.members().containsKey("original_query"))return Optional.empty();
        StrictJson.require(proof.members().keySet().equals(Set.of("query_sequence","original_query")),"public ruler original query locator has unknown fields");
        positive(proof.get("query_sequence"));return Optional.of(ExactRef.fromJson(OpportunityJson.toNode(object(proof.get("original_query")))));
    }
    private void verifyPublicOriginal(Session same,ActionCommand command,ExactRef originalQuery)throws IOException {
        var actual=nativeProducts.originalRuler(same,command,originalQuery);var intent=RulerMarriageIntent.fromJson(command.arguments());
        var proof=intent.planningProof().orElseThrow();StrictJson.require(eq(actual.value().get("query_sequence"),proof.get("query_sequence")),"public ruler original query sequence differs");
        var selected=array(actual.value().get("arrange_marriage_choices")).stream().map(RootFamilyMarriageFreshPreparation::object)
                .filter(row->eq(row.get("choice_id"),t(intent.choiceId()))&&eq(row.get("played_character_id"),n(intent.actorId()))&&eq(row.get("candidate_character_id"),n(intent.candidateId()))).toList();
        StrictJson.require(selected.size()==1,"public ruler intent is not the unique pair in its actual original native choices");
    }
    /** The fresh-review manifest has its own finite full-material role and sorted typed wire. */
    static RawJson encodeReviewMaterial(com.fasterxml.jackson.databind.JsonNode manifest) {
        return RawJson.fullMaterial(PublicDataJson.encodeTypedBytes(DriverJson.fromNode(manifest),MAX));
    }
    static com.fasterxml.jackson.databind.JsonNode loadReviewMaterial(ActionPorts.OutcomeArchive archive,ExactRef ref) {
        RawJson material=archive.loadFullMaterial(ref);
        StrictJson.require(archive.materialReferenceOf(material).equals(ref),"original preparation evidence identity differs");
        return FullJsonTree.parse(material.bytes(),MAX);
    }
    private FamilyNativePreparation.VerifiedBasis replayOriginal(ActionCommand command,NativeRequest prepared,ActionPorts.OutcomeArchive archive)throws IOException {
        var same=context.borrowedSession();context.writer().requireSession(same);List<com.fasterxml.jackson.databind.JsonNode> manifests=new ArrayList<>();
        for(var ref:prepared.preparationEvidence()) {
            var value=loadReviewMaterial(archive,ref);
            if(value.isObject()&&value.has("schema")&&value.get("schema").isTextual()&&SCHEMA.equals(value.get("schema").textValue()))manifests.add(value);
        }
        StrictJson.require(manifests.size()==1,"one actual fresh-review manifest required; current plan is not replay");
        var m=StrictJson.object(manifests.getFirst(),Set.of("schema","command_sha256","head_sequence","head_digest","implementation","planning_request","public_original_query","origin","snapshot","bridge","domains","reads","prepared_plan"));
        ExactRef.fromJson(m.get("implementation"));
        StrictJson.require(ActionCodec.sha256(ActionCodec.encodeCommand(command)).equals(StrictJson.text(m.get("command_sha256"))),
                "fresh-review immutable command differs");
        var original=bridge.replay(same,ExactRef.fromJson(m.get("bridge")));
        StrictJson.require(original.semantic().equals(ExactRef.fromJson(m.get("snapshot")))&&original.frame().identity().equals(command.before())
                &&original.frame().source().equals(command.source())&&original.frame().sessionId().equals(command.sessionId()),"fresh-review original full native/Driver basis differs");
        FamilyNativePreparation.requireCommandFrame(command,original.frame().semantic());
        boolean publicOrigin="PUBLIC_RULER".equals(StrictJson.text(m.get("origin")));
        if(publicOrigin) {
            StrictJson.require(m.get("planning_request").isNull()&&m.get("domains").isNull()&&m.get("head_sequence").isNull()&&m.get("head_digest").isNull(),"public ruler original cannot borrow an ordinary request/domain default");
            ExactRef actual=publicQuery(command).orElseThrow(()->new IllegalArgumentException("public ruler original proof absent"));
            StrictJson.require(actual.equals(ExactRef.fromJson(m.get("public_original_query"))),"public ruler original source query changed");
            verifyPublicOriginal(same,command,actual);
        } else {
            StrictJson.require("ORDINARY_PLANNING".equals(StrictJson.text(m.get("origin")))&&m.get("public_original_query").isNull(),"unknown or mixed family preparation origin");
            var request=originals.original(same,command,ExactRef.fromJson(m.get("planning_request")));
            RootFamilyBridge.requireSameSemantic(request.observations().snapshot(),original.frame().semantic(),
                    RootFamilyBridge.nativeOwnedNoticeKeys(original.frame(),archive),original.frame().identity().game().pid(),
                    "fresh-review complete actual planning snapshot differs");
        }
        Optional<FamilyPendingProducer.State> state;
        if(publicOrigin)state=Optional.empty();
        else {
            var domainRows=StrictJson.object(m.get("domains"),Set.of("FAMILY","CHILD_MATRILINEAL","DEFAULT_MARRIAGE"));
            Map<Slot,ExactRef> domains=new EnumMap<>(Slot.class);for(Slot slot:SLOTS)domains.put(slot,ExactRef.fromJson(domainRows.get(slot.name())));
            state=Optional.of(state(same,StrictJson.integer(m.get("head_sequence"),0,Long.MAX_VALUE),StrictJson.text(m.get("head_digest")),domains));
        }
        var wire=m.get("reads");StrictJson.require(wire.isArray()&&!wire.isEmpty()&&wire.size()<=32,"complete actual original fresh read sequence required");
        List<Read> retained=new ArrayList<>();for(var raw:wire) {
            var row=StrictJson.object(raw,Set.of("query","requested","original"));
            retained.add(new Read(FamilyPorts.Query.valueOf(StrictJson.text(row.get("query"))),object(DriverJson.fromNode(row.get("requested"))),ExactRef.fromJson(row.get("original"))));
        }
        var roots=nativeProducts.campaignRoot();var retainedRefs=retained.stream().map(Read::original).toList();
        var target=roots.freshTarget(same,command,original.frame(),retainedRefs);
        return roots.withHistoricalTarget(same,target,original.frame(),()->{
        verifyFreshContracts(same,command,retained);var index=new int[]{0};
        Obj plan=review(command,original.frame().semantic(),original.observation().identity(),state,(query,args)->{
            StrictJson.require(index[0]<retained.size(),"archived fresh read sequence is incomplete");var row=retained.get(index[0]++);
            StrictJson.require(row.query()==query&&row.requested().equals(args),"archived fresh query order or policy-derived requested arguments differ");
            PlanningReadReceipt read=archive.loadRead(row.original());NativeRecordedEvidenceVerifier.requireRead(read,archive);
            StrictJson.require(archive.readReferenceOf(read).equals(row.original())
                    &&read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId()),"archived fresh original source/session differs");
            if(!read.request().before().equals(command.before())) {
                StrictJson.require(query==FamilyPorts.Query.CAMPAIGN_ROOT,"only the qualified ROOT original may precede the target public frame");
                roots.requireFreshOriginal(same,read,command,original.frame(),retainedRefs);
            }
            return new FamilyPorts.ObservedRead(products.reads().decode(query,read),read,row.original());
        });
        StrictJson.require(index[0]==retained.size()&&OpportunityJson.toNode(plan).equals(m.get("prepared_plan")),"complete original fresh policy replay changed selected plan");
        return new FamilyNativePreparation.VerifiedBasis(original.frame().semantic(),original.observation().identity(),original.semantic(),original.observation().evidence(),Optional.of(plan));
        });
    }
    private FamilyPorts.ObservedRead currentRead(Session same,PlanningRequest request,FamilyPorts.Query query,Obj args)throws IOException {
        PlanningReadResult<Obj> result;Obj canonical=args;
        if(products.reads().projected(query).isPresent()) {
            var projected=products.reads().projected(query).orElseThrow().read(request,args);canonical=projected.canonicalArguments();result=projected.result();
        } else {
            var contract=products.reads().find(query).orElseThrow(()->new IllegalArgumentException("actual fresh native contract unavailable: "+query));
            StrictJson.require(context.readCatalog().containsIdentity(contract),"fresh native contract is not the identical installed product");
            result=context.reads().read(same,contract,new PlanningReadRequest(request.before(),request.source(),request.sessionId(),query.operation(),args,request.deadline()));
        }
        if(!(result instanceof PlanningReadResult.Known<Obj> known))throw new IOException("actual fresh family read is unavailable: "+query);
        var actual=known.receipt().request();
        if(!actual.before().equals(request.before())) {
            StrictJson.require(query==FamilyPorts.Query.CAMPAIGN_ROOT,"fresh native leaf changed actual held frame");
            nativeProducts.campaignRoot().requireCurrentOriginal(same,known.receipt(),new PlanningReadRequest(request.before(),request.source(),request.sessionId(),query.operation(),canonical,request.deadline()));
        }
        StrictJson.require(actual.source().equals(request.source())
                &&actual.sessionId().equals(request.sessionId())&&actual.operation().equals(query.operation())&&actual.arguments().equals(canonical),"fresh read changed actual held request");
        return new FamilyPorts.ObservedRead(known.value(),known.receipt(),known.originalReceipt());
    }
    private static FamilyPendingProducer.State state(Session same,long sequence,String digest,Map<Slot,ExactRef> refs)throws IOException {
        var historical=same.requireHistoricalState(sequence,digest);Map<Slot,Obj> bodies=new EnumMap<>(Slot.class);
        for(Slot slot:SLOTS) {
            var registered=DomainBodies.reference(historical,slot).orElseThrow(()->new IllegalArgumentException("actual full family domain absent from historical head"));
            StrictJson.require(registered.payload().equals(refs.get(slot))&&registered.contractSchema().equals(FamilyDomainSource.schema(slot)),"fresh-review source domain differs from original canonical registry");
            var pin=same.capturePin(refs.get(slot),org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES);
            StrictJson.require(pin.identity().equals(registered.identity()),"original full family domain file identity changed");
            bodies.put(slot,FamilyDomainSource.validate(slot,same.readPinned(pin,org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES)));
            same.verifyPin(pin);
        }
        return new FamilyPendingProducer.State(bodies.get(Slot.FAMILY),bodies.get(Slot.CHILD_MATRILINEAL),bodies.get(Slot.DEFAULT_MARRIAGE));
    }
    private void verifyFreshContracts(Session same,ActionCommand command,List<Read> reads)throws IOException {
        var expected=contracts.forRoute(FamilyMarriageSendReads.sender(command).route());var seen=new HashSet<ExactRef>();var counts=new java.util.HashMap<ReadContract<?>,Integer>();
        var archive=context.archive().withSession(same);
        for(var item:reads) {
            StrictJson.require(seen.add(item.original()),"one original cannot stand in for two fresh native queries");var read=archive.loadRead(item.original());
            var matching=expected.stream().filter(row->row.contract().contractId().equals(read.contractId())&&row.contract().operation().equals(read.request().operation())).toList();
            StrictJson.require(matching.size()==1,"actual fresh route queried a source outside its complete installed closure");var row=matching.getFirst();
            StrictJson.require(context.readCatalog().containsIdentity(row.contract())&&counts.merge(row.contract(),1,Integer::sum)<=row.maximum(),"fresh native source identity or cardinality differs");
            row.contract().replay(read);
        }
        for(var row:expected)StrictJson.require(counts.getOrDefault(row.contract(),0)>=row.minimum(),"actual fresh route did not consume every required native source");
    }
    private static Obj review(ActionCommand command,Obj snapshot,FamilyPorts.BridgeIdentity bridge,FamilyPendingProducer.State state,QueryReader reader)throws IOException {
        return review(command,snapshot,bridge,Optional.of(state),reader);
    }
    private static Obj review(ActionCommand command,Obj snapshot,FamilyPorts.BridgeIdentity bridge,Optional<FamilyPendingProducer.State> actualState,QueryReader reader)throws IOException {
        FamilyNativePreparation.requireCommandFrame(command,snapshot);
        if(command.operation().value().startsWith("arrange-marriage-")) {
            var intent=RulerMarriageIntent.fromJson(command.arguments());Obj choices=reader.read(FamilyPorts.Query.RULER_CHOICES,obj("expected_revision",snapshot.get("revision"))).value();
            var selected=array(choices.get("arrange_marriage_choices")).stream().map(RootFamilyMarriageFreshPreparation::object).filter(row->eq(row.get("choice_id"),t(intent.choiceId()))
                    &&eq(row.get("played_character_id"),n(intent.actorId()))&&eq(row.get("candidate_character_id"),n(intent.candidateId()))).toList();
            StrictJson.require(selected.size()==1,"immutable ruler pair is absent or duplicated in actual complete fresh choices");
            return obj("schema",t(FamilyMarriageNativeRequests.RULER_PLAN_SCHEMA),"selected_step",t(intent.step()),"marriage_choice",selected.getFirst(),"marriage_choices",choices);
        }
        var state=actualState.orElseThrow(()->new IllegalArgumentException("private family preparation cannot substitute an absent original domain"));
        var intent=FamilyMarriageIntent.fromJson(command.arguments());var policy=policy(snapshot);
        FamilyMarriagePreparationReview.FreshReads fresh=switch(intent.route()) {
            case FIRST_HEIR -> {
                Obj relation=reader.read(FamilyPorts.Query.CURRENT_RELATION,obj("expected_native_revision",snapshot.get("native_revision"))).value();
                var legality=reader.read(FamilyPorts.Query.HEIR_LEGALITY,obj("expected_native_revision",snapshot.get("native_revision")));
                var candidates=FamilyMarriagePreparationReview.heirComparisonCandidates(snapshot,bridge,state,relation,legality.value());
                Obj projection=reader.read(FamilyPorts.Query.HEIR_PROJECTION,obj("legality",legality.value(),"legality_read",reference(legality.originalReceipt()),
                        "candidate_character_ids",new Arr(candidates.stream().<Value>map(IntegerValue::new).toList()))).value();
                List<Obj> previews=new ArrayList<>();var actual=new FamilyMarriagePreparationReview.FirstHeir(relation,legality.value(),projection,previews);
                while(true) {
                    var remaining=FamilyMarriagePreparationReview.heirPreviewCandidates(snapshot,bridge,state,policy,actual);if(remaining.isEmpty())break;
                    BigInteger candidate=remaining.getFirst();var rows=array(projection.get("rows")).stream().map(RootFamilyMarriageFreshPreparation::object)
                            .filter(row->eq(row.get("candidate_character_id"),new IntegerValue(candidate))).toList();
                    StrictJson.require(rows.size()==1,"fresh lineage candidate has no unique actual projection row");
                    previews.add(reader.read(FamilyPorts.Query.CHILD_HOUSE_PREVIEW,obj("expected_revision",snapshot.get("revision"),"subject_character_id",n(intent.subjectId()),
                            "candidate_character_id",new IntegerValue(candidate),"request_matrilineal_option",rows.getFirst().get("matrilineal_option_selected"))).value());
                    actual=new FamilyMarriagePreparationReview.FirstHeir(relation,legality.value(),projection,previews);
                }
                yield actual;
            }
            case FULFILL_BETROTHAL -> new FamilyMarriagePreparationReview.Fulfillment(reader.read(FamilyPorts.Query.CURRENT_RELATION,obj("expected_native_revision",snapshot.get("native_revision"))).value());
            case CHILD_MATRILINEAL -> {
                var subject=reader.read(FamilyPorts.Query.CHILD_SUBJECT,obj("expected_native_revision",snapshot.get("native_revision"),"subject_character_id",n(intent.subjectId())));
                Obj value=reader.read(FamilyPorts.Query.CHILD_VALUE,obj("legality",subject.value(),"subject_read",reference(subject.originalReceipt()),"candidate_character_id",n(intent.candidateId()),"request_matrilineal_option",new Bool(true))).value();
                yield new FamilyMarriagePreparationReview.ChildMatrilineal(subject.value(),value);
            }
            case CHILD_DEFAULT -> {
                Obj root=reader.read(FamilyPorts.Query.CAMPAIGN_ROOT,obj("expected_revision",snapshot.get("revision"))).value();
                var subject=reader.read(FamilyPorts.Query.CHILD_SUBJECT,obj("expected_native_revision",snapshot.get("native_revision"),"subject_character_id",n(intent.subjectId())));
                List<Obj> values=new ArrayList<>();for(var candidate:FamilyMarriagePreparationReview.defaultComparisonCandidates(snapshot,root,subject.value(),state))
                    values.add(reader.read(FamilyPorts.Query.CHILD_VALUE,obj("legality",subject.value(),"subject_read",reference(subject.originalReceipt()),"candidate_character_id",new IntegerValue(candidate),"request_matrilineal_option",new Bool(false))).value());
                yield new FamilyMarriagePreparationReview.ChildDefault(root,subject.value(),values);
            }
        };
        return FamilyMarriagePreparationReview.review(intent,snapshot,bridge,state,policy,fresh);
    }
    /** Exactly the existing planner policy: an actual non-null retained goal enables dynasty preference. */
    private static FamilyMarriagePreparationReview.Policy policy(Obj snapshot) {
        if(!snapshot.members().containsKey("campaign_goal"))throw new IllegalArgumentException("actual Driver campaign_goal missing; no policy default allowed");
        Value raw=snapshot.get("campaign_goal");if(raw==Nil.INSTANCE)return new FamilyMarriagePreparationReview.Policy(false);
        var goal=GoalCodec.decodeGoal(bytes(object(raw)));
        StrictJson.require(BigInteger.valueOf(goal.currentCharacterId()).equals(positive(object(snapshot.get("played_character")).get("character_id"))),"actual retained goal belongs to another played character");
        return new FamilyMarriagePreparationReview.Policy(true);
    }
    private static Obj reference(ExactRef ref) {return obj("path",t(ref.path()),"bytes",n(ref.bytes()),"sha256",t(ref.sha256()));}
    private static Obj object(Value value) {return OpportunityJson.object(value,"actual family preparation object");}
    private static List<Value> array(Value value) {return OpportunityJson.array(value,"actual family preparation array");}
    private static BigInteger positive(Value value) {var id=OpportunityJson.integer(value,"actual family preparation ID");StrictJson.require(id.signum()>0,"positive actual family ID required");return id;}
    private static boolean eq(Value left,Value right) {return left!=null&&left.equals(right);}
    private static Text t(String value) {return new Text(value);}
    private static IntegerValue n(long value) {return new IntegerValue(BigInteger.valueOf(value));}
    private static byte[] bytes(Value value) {return OpportunityJson.encode(value);}
    /** Narrow private dynamic JSON assembly; all pairs must be explicit immutable JSON values. */
    private static Obj obj(Object... pairs) {
        StrictJson.require(pairs.length%2==0,"explicit family preparation JSON pairs required");Map<String,Value> result=new java.util.LinkedHashMap<>();
        for(int index=0;index<pairs.length;index+=2) {
            if(!(pairs[index] instanceof String key)||!(pairs[index+1] instanceof Value value))throw new IllegalArgumentException("typed family preparation JSON pair required");
            StrictJson.require(result.putIfAbsent(key,value)==null,"duplicate family preparation field");
        }
        return new Obj(result);
    }
}
