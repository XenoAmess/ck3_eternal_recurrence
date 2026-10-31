package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels.Domain;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Private current-plan transcripts rerun the actual policies; requested cadence JSON never qualifies itself. */
public final class GovernanceCadenceReplay implements GovernanceCadencePublication.MaterialPort,GovernancePlanCompletion.EvidencePort {
    @FunctionalInterface public interface OriginalBodies { byte[] read(ContinuityStorePort.Session borrowed,ExactRef ref)throws IOException; }
    private sealed interface Arguments permits Empty,LifeArguments,PositionArguments,LawArguments,ProvinceArguments,SpendingArguments { }
    private enum Empty implements Arguments { INSTANCE }
    private record LifeArguments(String focus,boolean opening) implements Arguments { }
    private record PositionArguments(CouncilSelection.Position position) implements Arguments { }
    private record LawArguments(String law) implements Arguments { }
    private record ProvinceArguments(int provinceId) implements Arguments { }
    private record SpendingArguments(OrdinaryFinanceCollector.Spending actual) implements Arguments { }
    private record Entry<T>(Arguments arguments,Read<T> actual) { }
    private static final class Tape<T> {
        private final List<Entry<T>> entries=new ArrayList<>();private int cursor;
        Read<T> use(Arguments arguments,Supplier<Read<T>> actual,boolean replay) {
            if(!replay) { Read<T> result=Objects.requireNonNull(actual.get());entries.add(new Entry<>(arguments,result));return result; }
            StrictJson.require(cursor<entries.size(),"actual policy replay requested an unrecorded observation");
            Entry<T> entry=entries.get(cursor++);StrictJson.require(entry.arguments().equals(arguments),"actual policy replay changed its observed query arguments");return entry.actual();
        }
        void reset() { cursor=0; }
        void consumed() { StrictJson.require(cursor==entries.size(),"actual policy replay skipped original observations"); }
        List<ExactRef> originals() {
            var result=new ArrayList<ExactRef>();
            for(Entry<T> entry:entries) {
                if(entry.actual() instanceof Known<T> known)result.addAll(known.originals());
                else if(entry.actual() instanceof Unavailable<T> unavailable)
                    unavailable.councilTechnicalReadFailure().ifPresent(failure->result.addAll(failure.originals()));
            }
            return result;
        }
    }
    private static final class Transcript {
        final Tape<Durable> durable=new Tape<>();final Tape<Life> life=new Tape<>();final Tape<OpeningComparison> comparison=new Tape<>();
        final Tape<CouncilSelection.Query> council=new Tape<>();final Tape<CouncilSelection.Query> coreCouncil=new Tape<>();final Tape<CouncilRoot> councilRoot=new Tape<>();
        final Tape<CrownRetryDue.VerifiedDue> retryDue=new Tape<>();
        final Tape<Crown> crown=new Tape<>();final Tape<CrownRetryCodec.MatchRequest> retry=new Tape<>();final Tape<CrownCooldownCodec.ClockRequest> cooldown=new Tape<>();
        final Tape<FeastObservationSupplier.State> feastState=new Tape<>();final Tape<FeastObservationSupplier.Planner> planner=new Tape<>();
        final Tape<FeastObservationSupplier.Hosted> hosted=new Tape<>();final Tape<Obj> root=new Tape<>();
        final Tape<OrdinaryFinanceCollector.Spending> spending=new Tape<>();final Tape<OrdinaryFinanceCollector.Feast> feast=new Tape<>();
        final Tape<ActivityConfigurationModels.StageOne> one=new Tape<>();final Tape<ActivityConfigurationModels.StageTwo> two=new Tape<>();final Tape<ActivityConfigurationModels.Location> location=new Tape<>();
        List<Tape<?>> all() { return List.of(durable,life,comparison,council,coreCouncil,councilRoot,crown,retry,retryDue,cooldown,feastState,planner,hosted,root,spending,feast,one,two,location); }
        List<ExactRef> originals() { return all().stream().flatMap(tape->tape.originals().stream()).distinct().toList(); }
        void reset() { all().forEach(Tape::reset); }
        void consumed() { all().forEach(Tape::consumed); }
    }
    private record Active(Transcript transcript,boolean replay) { }
    private record Call(OrdinaryPolicy actualPolicy,PlanningRequest request,OrdinaryPolicy.Draft before,OrdinaryPolicy.Decision actual,
            GovernanceCadencePublication.Plan plan,List<Domain> added,boolean technicalAdded,Transcript transcript) { }
    private final ThreadLocal<Active> active=new ThreadLocal<>();
    private final List<Call> retained=new ArrayList<>();
    private final Supplier<ContinuityStorePort.Session> sessions;
    private final GovernanceBorrowedSession.Authority authority;
    private final OriginalBodies bodies;
    public GovernanceCadenceReplay(Supplier<ContinuityStorePort.Session> sessions,GovernanceBorrowedSession.Authority authority,OriginalBodies bodies) {
        this.sessions=Objects.requireNonNull(sessions);this.authority=Objects.requireNonNull(authority);this.bodies=Objects.requireNonNull(bodies);
    }
    private <T> Read<T> read(Tape<T> tape,Arguments arguments,Supplier<Read<T>> actual) {
        Active scope=active.get();return scope==null?actual.get():tape.use(arguments,actual,scope.replay());
    }
    private Transcript transcript() { Active scope=active.get();return scope==null?new Transcript():scope.transcript(); }
    public GovernanceObservationSupplier observe(GovernanceObservationSupplier actual) {
        Objects.requireNonNull(actual);return new GovernanceObservationSupplier() {
            public Read<Durable> durable(PlanningRequest request) {return read(transcript().durable,Empty.INSTANCE,()->actual.durable(request));}
            public Read<Life> lifestyle(PlanningRequest request,String focus,boolean opening) {return read(transcript().life,new LifeArguments(focus,opening),()->actual.lifestyle(request,focus,opening));}
            public Read<OpeningComparison> openingComparison(PlanningRequest request) {return read(transcript().comparison,Empty.INSTANCE,()->actual.openingComparison(request));}
            public Read<CouncilSelection.Query> council(PlanningRequest request,CouncilSelection.Position position) {return read(transcript().council,new PositionArguments(position),()->actual.council(request,position));}
            public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) {return read(transcript().coreCouncil,Empty.INSTANCE,()->actual.coreCouncil(request));}
            public Read<CouncilRoot> councilRoot(PlanningRequest request) {return read(transcript().councilRoot,Empty.INSTANCE,()->actual.councilRoot(request));}
            public Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) {return read(transcript().retryDue,Empty.INSTANCE,()->actual.crownRetryDue(request));}
            public Read<Crown> crown(PlanningRequest request) {return read(transcript().crown,Empty.INSTANCE,()->actual.crown(request));}
            public Read<CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request,String law) {return read(transcript().retry,new LawArguments(law),()->actual.crownRetry(request,law));}
            public Read<CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) {return read(transcript().cooldown,Empty.INSTANCE,()->actual.crownCooldown(request));}
        };
    }
    public FeastObservationSupplier observe(FeastObservationSupplier actual) {
        Objects.requireNonNull(actual);return new FeastObservationSupplier() {
            public Read<State> state(PlanningRequest request) {return read(transcript().feastState,Empty.INSTANCE,()->actual.state(request));}
            public Read<Planner> planner(PlanningRequest request) {return read(transcript().planner,Empty.INSTANCE,()->actual.planner(request));}
            public Read<Hosted> hosted(PlanningRequest request) {return read(transcript().hosted,Empty.INSTANCE,()->actual.hosted(request));}
            public Read<Obj> root(PlanningRequest request) {return read(transcript().root,Empty.INSTANCE,()->actual.root(request));}
            public Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request) {return read(transcript().spending,Empty.INSTANCE,()->actual.spending(request));}
            public Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request,OrdinaryFinanceCollector.Spending spending) {
                return read(transcript().feast,new SpendingArguments(spending),()->actual.feast(request,spending));
            }
            public Read<ActivityConfigurationModels.StageOne> stageOne(PlanningRequest request) {return read(transcript().one,Empty.INSTANCE,()->actual.stageOne(request));}
            public Read<ActivityConfigurationModels.StageTwo> stageTwo(PlanningRequest request) {return read(transcript().two,Empty.INSTANCE,()->actual.stageTwo(request));}
            public Read<ActivityConfigurationModels.Location> location(PlanningRequest request,int provinceId) {return read(transcript().location,new ProvinceArguments(provinceId),()->actual.location(request,provinceId));}
        };
    }
    public OrdinaryPolicy record(OrdinaryPolicy actualPolicy) {
        Objects.requireNonNull(actualPolicy);return new OrdinaryPolicy() {
            public PlanningStage stage() {return actualPolicy.stage();}
            public ExactRef implementationSource() {return actualPolicy.implementationSource();}
            public Decision evaluate(PlanningRequest request,Draft previous) {
                StrictJson.require(active.get()==null,"cadence policy recordings cannot nest");Transcript transcript=new Transcript();active.set(new Active(transcript,false));
                try {
                    Decision result=actualPolicy.evaluate(request,previous);Optional<GovernanceCadencePublication.Plan> produced=plan(result);
                    if(produced.isPresent()) {
                        var after=produced.orElseThrow();var before=GovernanceCadencePublication.fromDetail(previous.detail());
                        List<Domain> added=after.completeNoActionDomains().stream().filter(domain->before.isEmpty() || !before.orElseThrow().completeNoActionDomains().contains(domain)).toList();
                        boolean technicalAdded=after.councilTechnicalFailure().isPresent()
                                && (before.isEmpty() || before.orElseThrow().councilTechnicalFailure().isEmpty());
                        if(!added.isEmpty() || technicalAdded)retain(new Call(actualPolicy,request,previous,result,after,added,technicalAdded,transcript));
                    }
                    return result;
                } finally {active.remove();}
            }
        };
    }
    private synchronized void retain(Call call) {
        retained.removeIf(old->!old.request().before().equals(call.request().before()) || !old.request().source().equals(call.request().source())
                || !old.request().sessionId().equals(call.request().sessionId()));
        StrictJson.require(retained.size()<128,"bounded cadence replay records exhausted; fresh capture required");retained.add(call);
    }
    private static Optional<GovernanceCadencePublication.Plan> plan(OrdinaryPolicy.Decision result) {
        if(result instanceof OrdinaryPolicy.Replace replace)return GovernanceCadencePublication.fromDetail(replace.draft().detail());
        if(result instanceof OrdinaryPolicy.Annotate annotate)return GovernanceCadencePublication.fromDetail(annotate.retained().detail());
        return Optional.empty();
    }
    private synchronized List<Call> calls(GovernanceCadencePublication.Plan requested)throws IOException {
        List<Call> selected=new ArrayList<>();List<Domain> domains=new ArrayList<>();boolean technicalSeen=false;
        for(Call call:retained) {
            if(!call.plan().observed().equals(requested.observed()) || !call.plan().source().equals(requested.source())
                    || !call.plan().sessionId().equals(requested.sessionId()) || !call.plan().before().equals(requested.before()))continue;
            if(call.added().stream().allMatch(domains::contains) && (!call.technicalAdded() || technicalSeen))continue;
            StrictJson.require(call.added().stream().noneMatch(domains::contains) && !(call.technicalAdded() && technicalSeen),
                    "cadence replay domain was produced twice");
            if(call.technicalAdded()) {
                StrictJson.require(call.plan().councilTechnicalFailure().equals(requested.councilTechnicalFailure()),
                        "technical Council replay diagnostic differs from its actual producer");
                technicalSeen=true;
            }
            selected.add(call);domains.addAll(call.added());
            if(domains.equals(requested.completeNoActionDomains()) && technicalSeen==requested.councilTechnicalFailure().isPresent())return List.copyOf(selected);
        }
        throw new IOException("no actual recorded ordinary-policy producer closure matches the requested ordered cadence plan");
    }
    @Override public List<ExactRef> originals(PlanningRequest original,PlanningResult planned,GovernanceCadencePublication.Plan requested)throws IOException {
        StrictJson.require(requested.observed().equals(original.before()) && planned.trace().before().equals(original.before()),"cadence evidence crossed its real plan");
        var result=new ArrayList<ExactRef>();for(Call call:calls(requested)){result.addAll(call.transcript().originals());}
        List<ExactRef> evidence=result.stream().distinct().toList();StrictJson.require(!evidence.isEmpty() && evidence.size()<=32,"bounded complete actual cadence originals required");return evidence;
    }
    @Override public GovernanceCadencePublication.Material replay(WriterContracts.Head head,DomainBodies.BodyRef previous,
            GovernanceCadencePublication.Plan requested,List<ExactRef> originalReadEvidence)throws IOException {
        var borrowed=sessions.get();if(borrowed==null)throw new IOException("cadence replay has no original live writer Session");authority.requireSession(borrowed);
        StrictJson.require(borrowed.head().digest().equals(head.digest()) && DomainBodies.reference(head.state(),DomainBodies.Slot.OPTIONAL_CADENCE).filter(previous::equals).isPresent(),
                "cadence replay crossed the actual writer head/body");
        var evidence=new ArrayList<ExactRef>();GovernanceCadencePublication.Plan replayed=null;
        for(Call call:calls(requested)) {
            StrictJson.require(active.get()==null,"cadence replay cannot overlap actual collection");call.transcript().reset();active.set(new Active(call.transcript(),true));
            try {
                var actual=call.actualPolicy().evaluate(call.request(),call.before());call.transcript().consumed();
                StrictJson.require(actual.equals(call.actual()),"actual ordinary-policy replay differs from its original result");
                replayed=plan(actual).orElseThrow(()->new IllegalArgumentException("replayed policy no longer produces complete no-action cadence"));
            } finally {active.remove();}
            evidence.addAll(call.transcript().originals());
        }
        var exact=evidence.stream().distinct().toList();StrictJson.require(exact.equals(originalReadEvidence) && requested.equals(replayed),
                "actual replayed ordered domains/evidence differs from publication input");
        // Recorded read references are historical DATA; the actual current body is read below.
        byte[] original=bodies.read(borrowed,previous.payload());authority.requireSession(borrowed);
        return new GovernanceCadencePublication.Material(original,Objects.requireNonNull(replayed),exact);
    }
}
