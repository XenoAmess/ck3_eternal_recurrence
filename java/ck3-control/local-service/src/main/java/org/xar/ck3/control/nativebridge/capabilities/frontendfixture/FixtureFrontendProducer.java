package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.service.root.RootFixtureFrontendPort;

/** Actual original Robert/scenario algorithm; every Game write goes through the identical Root coordinator. */
public final class FixtureFrontendProducer {
    public record Mutation(Primitive primitive,ExactRef claim,ExactRef route,ExactRef model) {
        public Mutation { Objects.requireNonNull(primitive);Objects.requireNonNull(claim);Objects.requireNonNull(route);Objects.requireNonNull(model); }
    }
    public record Submitted(FixtureStartSubmission submission,ExactRef claim,List<ExactRef> originalReads,List<ActionReceipt> actualActions) {
        public Submitted { Objects.requireNonNull(submission);Objects.requireNonNull(claim);originalReads=List.copyOf(originalReads);actualActions=List.copyOf(actualActions); }
    }
    public interface Port {
        FrontendRulesData.Source currentSource()throws IOException;
        PlanningReadResult.Known<FrontendRulesData.ObservedRoute> route()throws IOException;
        PlanningReadResult.Known<FixtureModelContract.Observation> model(boolean scenario)throws IOException;
        ActionReceipt mutate(String actionId,Mutation mutation)throws IOException;
        ActionReceipt reconcileSelection(ActionReceipt original)throws IOException;
        ExactRef preserveClaim(RawJson original)throws IOException;
        RawJson originalModel(PlanningReadResult.Known<FixtureModelContract.Observation> model)throws IOException;
        Clock clock();
        Instant deadline();
        void pause(Duration duration)throws InterruptedException;
    }
    private final PreparedFixture fixture;
    private final Port port;
    private final Duration transitionTimeout;
    private boolean claimed;
    private boolean entered;
    private Claimed retainedClaim;
    private List<ActionReceipt> prior=List.of();
    public record Claimed(String parentActionId,FrontendRulesData.Source source,ExactRef original,Path journal) {
        public Claimed {StrictJson.text(parentActionId);Objects.requireNonNull(source);Objects.requireNonNull(original);Objects.requireNonNull(journal);}
    }
    public FixtureFrontendProducer(PreparedFixture fixture,RootFixtureFrontendPort actualRootPort,Duration transitionTimeout) {
        this(fixture,(Port)actualRootPort,transitionTimeout);
        actualRootPort.requireFixture(fixture);
    }
    /** Test seam is package-private; production can only supply the concrete installed Root consumer. */
    FixtureFrontendProducer(PreparedFixture fixture,Port port,Duration transitionTimeout) {
        this.fixture=Objects.requireNonNull(fixture);this.port=Objects.requireNonNull(port);this.transitionTimeout=Objects.requireNonNull(transitionTimeout);
        StrictJson.require(!transitionTimeout.isNegative()&&!transitionTimeout.isZero()&&transitionTimeout.compareTo(Duration.ofMinutes(5))<=0,"finite frontend transition timeout required");
    }
    public PreparedFixture fixture() { return fixture; }
    /** The durable cross-tool claim precedes the parent and all Game mutations; failure never removes it. */
    public synchronized Claimed claim(String parentActionId)throws IOException {
        StrictJson.text(parentActionId);requireDeadline();fixture.verifyBeforeClaim();var source=port.currentSource();
        StrictJson.require(!FixtureQualificationLogs.observe(fixture).any(),"fixture qualification was already present before original Start");
        source.build().requireRules();StrictJson.require(fixture.policy().kind()!=FrontendFixturePolicy.Kind.SCENARIO||source.build()==FrontendRulesData.Build.CK3_12004,"scenario fixture requires actual 1.20.0.4");
        if(claimed)throw new IOException("fixture Start already attempted; requests cannot be replayed");
        Path journal=fixture.stateDir().resolve("frontend-fixture-start-requests.jsonl");
        ObjectNode claim=StrictJson.object().put("phase","claimed-before-any-mutation").put("action_id",parentActionId);
        claim.set("binding",binding(source));claim.set("policy_binding",fixture.binding().toJson());claim.set("policy_source",fixture.policySource().toJson());
        write(journal,line(claim),true);claimed=true;
        retainedClaim=new Claimed(parentActionId,source,port.preserveClaim(new RawJson(StrictJson.canonical(claim))),journal);return retainedClaim;
    }
    public synchronized Submitted submitRobert(String actionId)throws IOException,InterruptedException {
        StrictJson.require(fixture.policy().kind()==FrontendFixturePolicy.Kind.ROBERT,"scenario fixture must use its separately admitted typed Start");
        return submit(actionId,false);
    }
    public synchronized Submitted submitScenario(String actionId)throws IOException,InterruptedException {
        StrictJson.require(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO,"Robert fixture cannot use scenario aliases");
        return submit(actionId,true);
    }
    /** Only the concrete Root port can submit; retained children are read, never run again. */
    public synchronized Submitted continueBeforeStart(Claimed original,List<ActionReceipt> canonicalSettled)throws IOException,InterruptedException {
        StrictJson.require(!entered&&!claimed&&canonicalSettled.stream().allMatch(ActionReceipt::settled)
                &&canonicalSettled.stream().noneMatch(value->value.command().operation().equals(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO?Primitive.SCENARIO_START.operation():Primitive.START_BOOKMARK.operation())),
                "fixture continuation cannot repeat an entered producer or an existing Start");
        retainedClaim=Objects.requireNonNull(original);claimed=true;prior=List.copyOf(canonicalSettled);
        return submit(original.parentActionId(),fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO);
    }
    private Submitted submit(String actionId,boolean scenario)throws IOException,InterruptedException {
        StrictJson.text(actionId);requireDeadline();if(entered)throw new IOException("original fixture mutation workflow was already entered; use read-only reconciliation");
        if(retainedClaim==null)claim(actionId);entered=true;
        var retained=retainedClaim.original();var source=retainedClaim.source();Path journal=retainedClaim.journal();
        StrictJson.require(retainedClaim.parentActionId().equals(actionId),"fixture producer changed its exclusively claimed original parent");fixture.verifySources();
        source.build().requireRules();StrictJson.require(!scenario||source.build()==FrontendRulesData.Build.CK3_12004,"scenario fixture requires actual 1.20.0.4");
        List<ExactRef> reads=new ArrayList<>();List<ActionReceipt> actions=new ArrayList<>(prior);
        var before=port.route();reads.add(before.originalReceipt());
        StrictJson.require(before.value().route()==FrontendRulesData.Route.BOOKMARKS&&before.value().source().equals(source),"fixture Start requires actual same-process Bookmarks");
        var model=port.model(scenario);reads.add(model.originalReceipt());bound(source);
        Optional<RawJson> bookmarkAck=priorAck(Primitive.SCENARIO_BOOKMARK),selectionAck=priorAck(scenario?Primitive.SCENARIO_CHARACTER:Primitive.SELECT_1066);
        if(scenario&&!model.value().selectedBookmarkKey().equals(Optional.of(FrontendFixturePolicy.SCENARIO_TARGET.bookmarkKey()))) {
            StrictJson.require(bookmarkAck.isEmpty(),"original settled bookmark selection drifted; never repeat setter");
            bookmarkAck=Optional.of(mutate(actionId+"-bookmark",Primitive.SCENARIO_BOOKMARK,retained,before.originalReceipt(),model.originalReceipt(),source,journal,actions,"before-native-bookmark-selection-request"));
            model=waitModel(true,false,source,reads);
        } else model.value().probeTarget(character(scenario),scenario);
        if(model.value().selectedIndex()!=model.value().targetIndex()) {
            StrictJson.require(selectionAck.isEmpty(),"original settled character selection drifted; never repeat setter");
            Primitive step=scenario?Primitive.SCENARIO_CHARACTER:Primitive.SELECT_1066;
            selectionAck=Optional.of(mutate(actionId+"-character",step,retained,before.originalReceipt(),model.originalReceipt(),source,journal,actions,"before-native-selection-request"));
        }
        model=waitModel(scenario,true,source,reads);
        for(int index=0;index<actions.size();index++) {
            ActionReceipt original=actions.get(index);
            if(!original.settled())original=port.reconcileSelection(original);
            StrictJson.require(original.settled(),"fixture selected model is visible but original selection outcome remains unresolved; no new Start");actions.set(index,original);
        }
        var candidate=model.value().selected(character(scenario),scenario,true);
        bound(source);var finalRoute=port.route();reads.add(finalRoute.originalReceipt());
        StrictJson.require(finalRoute.value().route()==FrontendRulesData.Route.BOOKMARKS&&finalRoute.value().source().equals(source),"fixture Start lost actual selected-bookmark route");
        var selected=new FixtureStartSubmission.Selected(fixture.policy().kind(),candidate.bookmarkGroupKey(),candidate.bookmarkKey(),candidate.characterNameKey(),
                candidate.governmentKey(),candidate.dateRaw(),scenario?Optional.of(port.originalModel(model)):Optional.empty(),Optional.empty());
        Primitive start=scenario?Primitive.SCENARIO_START:Primitive.START_BOOKMARK;
        ObjectNode beforeStart=StrictJson.object();beforeStart.put("step",start.operation().value());beforeStart.put("retry_allowed",false);beforeStart.set("selected_candidate",selected.toJson());
        journal(journal,"before-native-start-request",source,beforeStart);
        bound(source);requireDeadline();
        ActionReceipt actual=port.mutate(actionId+"-start",new Mutation(start,retained,finalRoute.originalReceipt(),model.originalReceipt()));actions.add(actual);
        RawJson ack=ack(actual);FixtureStartSubmission.requireAck(ack,start);
        ObjectNode route=StrictJson.object();route.put("route",before.value().route().wire());
        var result=new FixtureStartSubmission(fixture.policy().kind(),source.binding(),fixture.binding(),new RawJson(StrictJson.canonical(route)),selected,bookmarkAck,selectionAck,ack);
        StrictJson.require(result.equals(FixtureStartSubmission.fromJson(result.toJson())),"actual fixture submission JSON roundtrip differs");
        ObjectNode complete=StrictJson.object();complete.set("acknowledgement",StrictJson.parse(ack.bytes()));
        journal(journal,"native-start-acknowledged-post-state-pending",source,complete);
        return new Submitted(result,retained,reads,actions);
    }
    private Optional<RawJson> priorAck(Primitive step)throws IOException {
        var matches=prior.stream().filter(value->value.command().operation().equals(step.operation())).toList();
        StrictJson.require(matches.size()<=1,"fixture original setter appeared more than once");return matches.isEmpty()?Optional.empty():Optional.of(ack(matches.getFirst()));
    }
    private RawJson mutate(String id,Primitive step,ExactRef claim,ExactRef route,ExactRef model,FrontendRulesData.Source source,Path journal,List<ActionReceipt> actions,String phase)throws IOException {
        bound(source);requireDeadline();ObjectNode detail=StrictJson.object();detail.put("step",step.operation().value());detail.put("retry_allowed",false);journal(journal,phase,source,detail);
        ActionReceipt actual=port.mutate(id,new Mutation(step,claim,route,model));actions.add(actual);RawJson raw=ack(actual);FixtureStartSubmission.requireAck(raw,step);return raw;
    }
    private PlanningReadResult.Known<FixtureModelContract.Observation> waitModel(boolean scenario,boolean selected,FrontendRulesData.Source source,List<ExactRef> reads)throws IOException,InterruptedException {
        Instant until=port.clock().instant().plus(transitionTimeout.compareTo(Duration.ofSeconds(10))>0?Duration.ofSeconds(10):transitionTimeout);
        if(until.isAfter(port.deadline()))until=port.deadline();IllegalArgumentException last=null;
        while(true) {
            bound(source);var model=port.model(scenario);reads.add(model.originalReceipt());
            try {model.value().selected(character(scenario),scenario,selected);return model;}
            catch(IllegalArgumentException unavailable) {last=unavailable;}
            if(!port.clock().instant().isBefore(until))throw new IOException("single submitted fixture selection never published the actual selected model; no setter retry",last);
            Duration remaining=Duration.between(port.clock().instant(),until);port.pause(remaining.compareTo(Duration.ofMillis(100))<0?remaining:Duration.ofMillis(100));
        }
    }
    private void bound(FrontendRulesData.Source source)throws IOException {
        fixture.verifySources();requireDeadline();StrictJson.require(source.equals(port.currentSource()),"fixture selection crossed its admitted frontend process/build");
    }
    private void requireDeadline()throws IOException { if(!port.clock().instant().isBefore(port.deadline()))throw new IOException("original fixture deadline expired; no request replay"); }
    private static String character(boolean scenario) { return scenario?FrontendFixturePolicy.SCENARIO_TARGET.characterNameKey():FrontendFixturePolicy.ROBERT_KEY; }
    public static RawJson ack(ActionReceipt receipt)throws IOException {
        return receipt.ack().orElseThrow(()->new IOException("original native fixture ACK unknown; no retry")).originalResultToken().orElseThrow(()->new IOException("original native fixture result token missing; no retry"));
    }
    private static ObjectNode binding(FrontendRulesData.Source source) { ObjectNode n=StrictJson.object();n.put("bridge_pid",source.binding().bridgePid());n.put("connection_generation",source.binding().connectionGeneration());return n; }
    private static void journal(Path path,String phase,FrontendRulesData.Source source,ObjectNode detail)throws IOException {
        ObjectNode n=detail.deepCopy();n.put("phase",phase);n.set("binding",binding(source));write(path,line(n),false);
    }
    private static byte[] line(ObjectNode n) { byte[] raw=StrictJson.canonical(n,1<<20);byte[] line=java.util.Arrays.copyOf(raw,raw.length+1);line[raw.length]=(byte)'\n';return line; }
    private static void write(Path path,byte[] raw,boolean create)throws IOException {
        try(FileChannel channel=FileChannel.open(path,StandardOpenOption.WRITE,create?StandardOpenOption.CREATE_NEW:StandardOpenOption.APPEND)) {
            ByteBuffer data=ByteBuffer.wrap(raw);while(data.hasRemaining())channel.write(data);channel.force(true);
        }
    }
}
