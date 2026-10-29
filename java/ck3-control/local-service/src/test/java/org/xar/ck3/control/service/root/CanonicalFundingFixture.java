package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave2.finance.giftpending.*;

/** Bounded software fixture using the actual writer/import/archive/journal/state reader and sole funding producer.
 * Fixture registrations establish unit source custody; they never mint a Core/private domain proof or Game qualification. */
public final class CanonicalFundingFixture {
    public enum Variant { CLEAR, MISSING_MERCENARY, PENDING_MERCENARY }
    /** A domain owner may replace the fixture construction body with its actual schema/codec/registration. */
    public record ConstructionOverride(FinanceStatePort.ReaderBinding reader,DomainBodies.Registration registration,byte[] body) {
        public ConstructionOverride {body=body.clone();if(reader.domain()!=FinanceStatePort.Domain.CONSTRUCTION||registration.slot()!=DomainBodies.Slot.CONSTRUCTION)throw new IllegalArgumentException("actual construction slot/reader required");}
        @Override public byte[] body(){return body.clone();}
    }
    @FunctionalInterface public interface Work<T>{T run(ContinuityStorePort.Session same)throws IOException;}
    private record Body(FinanceStatePort.ReaderBinding reader,DomainBodies.Registration registration,byte[] raw) { }
    private final ContinuityWriter writer;private final FinanceStatePort state;private final CanonicalFundingPending service;
    private CanonicalFundingFixture(ContinuityWriter writer,FinanceStatePort state,CanonicalFundingPending service){this.writer=writer;this.state=state;this.service=service;}
    public CanonicalFundingPending service(){return service;}
    public FinanceStatePort state(){return state;}
    public <T> T withSession(Work<T> work)throws IOException{return writer.locked(work::run);}
    public static CanonicalFundingFixture create(Path root,PlanningRequest request,Variant variant)throws IOException{return create(root,request,variant,Optional.empty());}
    public static CanonicalFundingFixture create(Path root,PlanningRequest request,Variant variant,Optional<ConstructionOverride> construction)throws IOException {
        return create(root,request,variant,construction,java.util.function.UnaryOperator.identity());
    }
    static CanonicalFundingFixture create(Path root,PlanningRequest request,Variant variant,Optional<ConstructionOverride> construction,
            java.util.function.UnaryOperator<List<CanonicalFinanceStateSource.Binding>> runtimeCatalog)throws IOException {
        Files.createDirectories(root);Path source=root.resolve("qualified-software-fixture.java");Files.writeString(source,"finite same-writer funding source fixture v1",StandardCharsets.UTF_8);
        ExactRef sourceRef=exact(source);Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");
        byte[] initial=ContinuityJson.canonical(seed(request));Files.write(snapshot,initial);Files.write(anchor,initial);Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var layout=new WriterContracts.Layout(snapshot,exact(anchor),request.before().machineId());Path artifactsRoot=root.resolve("artifacts");Files.createDirectory(artifactsRoot);
        var storageGuard=StorageWriteGuardTestSupport.create(layout);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactsRoot,layout.lock(),4*1024*1024),storageGuard);
        var bodies=new ArrayList<Body>();
        for(var domain:List.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,FinanceStatePort.Domain.MERCENARY,FinanceStatePort.Domain.FEAST,
                FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE)) {
            if(domain==FinanceStatePort.Domain.CONSTRUCTION&&construction.isPresent()){var override=construction.orElseThrow();bodies.add(new Body(override.reader(),override.registration(),override.body()));continue;}
            DomainBodies.Slot slot=slot(domain);String schema=domain==FinanceStatePort.Domain.MERCENARY?MercenaryProcurement.SCHEMA:domain==FinanceStatePort.Domain.FACTION_GIFT?GiftPendingModel.SCHEMA:"fixture.owned-submission/v1";
            byte[] raw=body(domain,request,variant);
            FinanceStatePort.ReaderBinding reader=domain==FinanceStatePort.Domain.FACTION_GIFT?FinanceStatePort.giftReader(sourceRef):new FinanceStatePort.ReaderBinding(domain,sourceRef,original->{
                if(domain==FinanceStatePort.Domain.MERCENARY)return MercenaryProcurement.decode(original.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR;
                Obj decoded=object(parse(original.bytes()),"fixture registered body");if(!decoded.members().keySet().equals(Set.of("schema","pending"))||!new Text(schema).equals(decoded.get("schema")))throw new IllegalArgumentException("fixture exact original domain schema required");
                if(decoded.get("pending")!=Nil.INSTANCE)throw new IllegalArgumentException("fixture body is not explicitly clear");return FinanceStatePort.Pending.CLEAR;
            });
            var registration=new DomainBodies.Registration(slot,schema,ContinuityJson.DOMAIN_MAX_BYTES,List.of(sourceRef),(head,previous,submitted,actual)->{
                if(previous.isPresent()||!Arrays.equals(actual,raw)||!Arrays.equals(submitted.producerInput(),WriterContracts.canonical(raw)))throw new IllegalArgumentException("fixture import must consume this exact source-qualified original producer body");
                reader.reader().decode(new FinanceStatePort.Document(domain,submitted.originalBody(),actual));return ActionCodec.sha256(actual);
            });bodies.add(new Body(reader,registration,raw));
        }
        WriterContracts.TransitionAuthority noOrdinary=new WriterContracts.TransitionAuthority(){
            @Override public String revalidate(ContinuityState before,WriterContracts.Request submitted){throw new AssertionError("funding fixture uses only actual registered domain imports");}
            @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request submitted){throw new AssertionError("funding fixture cannot grant an action transition");}
        };
        var writer=new ContinuityWriter(layout,List.of(sourceRef),noOrdinary,Clock.systemUTC(),new ContinuityWriter.Extensions(bodies.stream().map(Body::registration).toList(),Optional.of(artifacts),Optional.empty()),storageGuard);
        if(artifacts.storageGuard()!=storageGuard||writer.storageGuard()!=storageGuard)throw new IOException("actual artifact store and writer must retain the identical finite fixture storage guard");
        var archive=new NativeOutcomeArchive(artifacts,writer);var actions=new ActionSnapshotReader(new ContinuityActionJournal(writer,archive));
        writer.locked(same->{for(var body:bodies){if(variant==Variant.MISSING_MERCENARY&&body.reader().domain()==FinanceStatePort.Domain.MERCENARY)continue;
            ExactRef original=archive.withSession(same).preserveMaterial(new RawJson(body.raw()));
            var submitted=new DomainBodies.ImportRequest(body.registration().slot(),body.registration().contractSchema(),original,body.raw(),body.registration().producerSources(),"actual-fixture-import:"+body.registration().slot());
            same.commitImport(same.previewImport(submitted));}return null;});
        var bindings=bodies.stream().map(body->new CanonicalFinanceStateSource.Binding(body.reader(),body.registration().slot(),body.registration().contractSchema(),body.registration().maximumBodyBytes(),body.registration().producerSources())).toList();
        var original=new CanonicalFinanceStateSource(layout.lock(),writer,actions,(same,current)->request.before(),same->Optional.empty(),List.copyOf(runtimeCatalog.apply(bindings)));
        var state=new FinanceStatePort(original,original.owningReaders());var installed=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
        for(var operation:List.of(OrdinaryFinancePolicies.MERCENARY,OrdinaryFinancePolicies.GIFT)) {
            var effect=new NativeEffectRegistry.Binding(operation,sourceRef,command->{throw new AssertionError("funding observation cannot submit");},(command,attempt,dispatch)->{throw new AssertionError("funding observation cannot observe a Game effect");});
            installed.add(new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sourceRef));
            archived.add(new NativeRecordedEvidenceVerifier.Binding(operation,sourceRef,(head,receipt,evidence)->{throw new AssertionError("a read-only funding fixture cannot authorize action evidence");}));
        }
        var catalog=RootExecutableBindings.freeze(installed,RootReadContractCatalog.staticOnly(List.of()),List.of(),archived,List.of(),32);
        var service=new CanonicalFundingPending(actions,layout.lock(),state,original.owningReaders(),()->catalog,archive::withSession,request.before().game(),request.source(),request.sessionId());
        return new CanonicalFundingFixture(writer,state,service);
    }
    private static byte[] body(FinanceStatePort.Domain domain,PlanningRequest request,Variant variant) {
        if(domain==FinanceStatePort.Domain.MERCENARY) {
            if(variant!=Variant.PENDING_MERCENARY)return MercenaryProcurement.encode(MercenaryProcurement.emptyFreshEpisode());
            return encode(OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",OrdinaryFinanceCollector.obj("action_request_id",new Text("original-unknown-fixture"),"company_id",new IntegerValue(java.math.BigInteger.ONE),"source_frame",OrdinaryFinanceCollector.sourceFrame(request),"status",new Text("submission_unresolved"),"pre_capture_epoch",new IntegerValue(java.math.BigInteger.ONE),"pre_player_army_ids",new Arr(List.of()),"decision",new Obj(java.util.Map.of())),"observed",new Arr(List.of())));
        }
        if(domain==FinanceStatePort.Domain.FACTION_GIFT)return GiftPendingCodec.encodeLedger(GiftPendingCodec.decodeLedger(encode(OrdinaryFinanceCollector.obj("schema",new Text(GiftPendingModel.SCHEMA),"format_version",new IntegerValue(java.math.BigInteger.ONE),"pending",Nil.INSTANCE,"resolved_request_outcomes",new Obj(java.util.Map.of())))));
        return encode(OrdinaryFinanceCollector.obj("schema",new Text("fixture.owned-submission/v1"),"pending",Nil.INSTANCE));
    }
    private static DomainBodies.Slot slot(FinanceStatePort.Domain domain){return switch(domain){
        case CONSTRUCTION->DomainBodies.Slot.CONSTRUCTION;case FACTION_GIFT->DomainBodies.Slot.FACTION;case MERCENARY->DomainBodies.Slot.MERCENARY;
        case FEAST->DomainBodies.Slot.FEAST;case FIRST_HEIR_MARRIAGE->DomainBodies.Slot.FAMILY;case CHILD_MARRIAGE->DomainBodies.Slot.CHILD_MATRILINEAL;
        case CHILD_DEFAULT_MARRIAGE->DomainBodies.Slot.DEFAULT_MARRIAGE;case CROWN->throw new IllegalArgumentException("Crown has no owned gold-pending producer in this fixture");};}
    private static ExactRef exact(Path path)throws IOException {byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static com.fasterxml.jackson.databind.node.ObjectNode seed(PlanningRequest request) {
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",request.before().machineId());row.put("sequence",0);row.put("window_id",1);row.put("status","running");
        row.put("target_days",10958);row.put("target_years",30);row.put("calendar_year_days",365.25);row.put("start_date_raw",1000);row.put("target_date_raw",1000+10958*24);row.put("last_settled_date_raw",1000);row.put("last_settled_cycles",1);
        row.put("manual_repair_count",1);row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);var game=row.putObject("game_binding");game.put("pid",123);game.put("creation_date","2026-10-24T00:00:00Z");
        row.putNull("latest_binding");var pending=row.putObject("pending_cycle");pending.put("stage","auto_unsettled");pending.put("auto_sequence",11558);row.put("NEXT",11559);return row;
    }
}
