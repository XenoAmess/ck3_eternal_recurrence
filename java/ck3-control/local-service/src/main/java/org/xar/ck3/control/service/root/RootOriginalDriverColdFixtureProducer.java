package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture.Case;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture.Control;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture.Fixture;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Root's standalone pre-CI caller. Validates actual prelaunch originals and publishes only a finite immutable DATA bundle.
 * No source, Driver/WAL, profile tree, process or Game is created/copied; the original reader never consolidates history. */
public final class RootOriginalDriverColdFixtureProducer {
    public static final String REQUEST_SCHEMA="xar.java-original-driver-cold-fixture-production/v1";
    public record Input(String name,ExactRef launchPlan,ExactRef runRequest,ExactRef episodePolicy,ExactRef storageLease,Control control) {
        public Input {
            require(name!=null&&name.matches("[A-Za-z0-9_-]{1,64}"),"bounded case name required");Objects.requireNonNull(control);
            RootOriginalDriverColdFixture.reference(launchPlan,1<<20);RootOriginalDriverColdFixture.reference(runRequest,65536);
            RootOriginalDriverColdFixture.reference(episodePolicy,1<<20);RootOriginalDriverColdFixture.reference(storageLease,1<<20);
        }
    }
    /** This storage admission has disjoint roots, so publishing the bundle cannot invalidate any case's signed census. */
    public record Publication(Path target,ExactRef storageLease,Control control) {
        public Publication {RootOriginalDriverColdFixture.absolute(target);RootOriginalDriverColdFixture.reference(storageLease,1<<20);Objects.requireNonNull(control);}
    }
    public record Request(String schema,String machineId,String observedAtUtc,String reviewAtUtc,List<Input> cases,Publication publication) {
        public Request {
            require(REQUEST_SCHEMA.equals(schema),"exact fixture-production request required");Objects.requireNonNull(publication);
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),"actual machine required");
            Instant observed=instant(observedAtUtc),review=instant(reviewAtUtc);
            require(observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(1))<=0,"finite fixture production review required");
            cases=List.copyOf(cases);require(!cases.isEmpty()&&cases.size()<=16,"finite actual input cases required");
            require(cases.stream().map(Input::name).distinct().count()==cases.size(),"distinct fixture cases required");
        }
    }
    public record Produced(FileWitness fixture,Fixture data) {
        public Produced {Objects.requireNonNull(fixture);Objects.requireNonNull(data);}
        public ExactRef reference(){return fixture.reference();}
    }
    private record Opened(RootRuntimeDefinitionModel.StorageLease lease,ContinuityWriter writer,
            RootRuntimeStorageGuard storage,CheckpointFiles files,Control control,RootOriginalDriverColdFixture.ReadOnlyScope scope) { }
    private record Captured(Input input,NativeLaunchPlan plan,RootFrozenRunProfile.FrozenRunProfile profile,Opened opened,Case expected) { }
    private RootOriginalDriverColdFixtureProducer() { }

    public static Produced produce(ExactRef productionRequest,Clock clock)throws IOException {
        Objects.requireNonNull(clock);
        Request request=RootOriginalDriverColdFixture.record(productionRequest,65536,Request.class);
        current(request,clock);
        Map<Control,RootOriginalDriverColdFixture.ReadOnlyScope> writers=new HashMap<>();Map<ExactRef,Opened> guards=new HashMap<>();
        Throwable failed=null;
        try {
        var captured=new ArrayList<Captured>();var cases=new ArrayList<Case>();
        for(Input input:request.cases()){
            NativeLaunchPlan plan=NativeLaunchPlan.readExact(input.launchPlan(),new NativeBridgeLaunchEvidence());
            RootOriginalDriverColdFixture.requirePrelaunch(plan,clock);
            require(request.machineId().equals(plan.sources().review().machineId()),"fixture case crossed its actual prelaunch machine");
            InitialEpisodePolicy policy=InitialEpisodePolicy.readExact(input.episodePolicy(),plan.preparedProfile().environmentManifest());
            var profile=RootFrozenRunProfile.readExact(input.runRequest(),plan,policy,clock);
            require(!instant(request.reviewAtUtc()).isAfter(plan.deadline())&&!instant(request.reviewAtUtc()).isAfter(profile.request().reviewAt()),
                    "fixture review cannot outlive its original plan or frozen profile");
            require(RootOriginalDriverColdFixture.requiredWriterSources(plan).stream().allMatch(required->input.control().sourceRefs().stream()
                            .anyMatch(source->RootOriginalDriverColdFixture.sameReference(source,required))),
                    "readonly writer must retain the actual loaded qualified source closure");
            Opened opened=open(input.storageLease(),input.control(),request.machineId(),clock,writers,guards);
            require(!instant(request.reviewAtUtc()).isAfter(instant(opened.lease().reviewAtUtc())),"fixture cannot outlive actual case storage");
            RootOriginalDriverColdFixture.requireStorage(plan,input.control(),opened.storage());
            var importer=new RootOriginalDriverJournal.Prepared(opened.files(),opened.storage(),plan,profile,clock);
            Case expected=opened.writer().locked(same->{
                String head=same.head().digest();var original=importer.load(opened.writer(),same,plan);original.requireRetained(same);
                String sha=null;Integer rows=null;
                switch(original.status()){
                    case BASE_ONLY,ALREADY_CONSOLIDATED,REPLAYED -> {
                        sha=OriginalDriverJournal.sha256(original.fullBytes());
                        var history=original.fullPayload().get("command_history");
                        if(!(history instanceof RetainedJson.ArrayValue array))throw new IOException("actual original full Driver history array required");
                        rows=array.values().size();
                    }
                    case MISSING,JOURNAL_INVALID -> { /* True observed absence/refusal, never fabricated empty history. */ }
                }
                original.requireRetained(same);require(head.equals(same.head().digest()),"fixture observation changed the original writer");
                return new Case(input.name(),input.launchPlan(),input.runRequest(),input.episodePolicy(),input.storageLease(),
                        original.status(),sha,rows,input.control());
            });
            captured.add(new Captured(input,plan,profile,opened,expected));cases.add(expected);
        }
        Opened output=open(request.publication().storageLease(),request.publication().control(),request.machineId(),clock,writers,guards);
        require(!instant(request.reviewAtUtc()).isAfter(instant(output.lease().reviewAtUtc())),"fixture cannot outlive actual publication storage");
        for(Captured item:captured)for(var source:item.opened().lease().roots())for(var target:output.lease().roots()){
            Path left=Path.of(source.path()),right=Path.of(target.path());
            require(!left.startsWith(right)&&!right.startsWith(left),"publication and case signed-census roots must be disjoint");
        }
        output.storage().requireManagedRoots(List.of(request.publication().target().getParent(),request.publication().control().snapshotPath().getParent()));
        output.storage().requireCompleteAdmission();
        Fixture data=new Fixture(RootOriginalDriverColdFixture.SCHEMA,request.machineId(),cases);
        byte[] wire=RootOriginalDriverColdFixture.encode(data);
        // Recheck actual prelaunch originals and read-only inputs before the one immutable guarded publication.
        for(Captured item:captured){
            RootOriginalDriverColdFixture.requirePrelaunch(item.plan(),clock);item.profile().requireCurrent(item.plan(),clock);
            item.opened().writer().locked(same->{
                require(item.input().control().expectedHeadDigest().equals(same.head().digest()),"case original writer drift before fixture publication");
                var reread=new RootOriginalDriverJournal.Prepared(item.opened().files(),item.opened().storage(),item.plan(),item.profile(),clock)
                        .load(item.opened().writer(),same,item.plan());reread.requireRetained(same);
                require(reread.status()==item.expected().expectedStatus(),"original Driver/WAL status drift before publication");
                if(item.expected().expectedFullPayloadSha256()!=null)
                    require(item.expected().expectedFullPayloadSha256().equals(OriginalDriverJournal.sha256(reread.fullBytes())),"original full Driver changed before publication");
                return null;
            });
        }
        current(request,clock);
        FileWitness published=output.files().createNew(request.publication().target(),wire);
        output.files().verify(published);
        Fixture readback=RootOriginalDriverColdFixture.readExact(published.reference());
        require(data.equals(readback),"actual immutable fixture readback differs");
        return new Produced(published,data);
        }catch(IOException|RuntimeException|Error rejected){failed=rejected;throw rejected;}
        finally{
            IOException closing=null;
            for(var opened:guards.values())try{opened.scope().close();}catch(IOException error){if(closing==null)closing=error;else closing.addSuppressed(error);}
            if(closing!=null){if(failed!=null)failed.addSuppressed(closing);else throw closing;}
        }
    }
    private static Opened open(ExactRef leaseRef,Control control,String machine,Clock clock,
            Map<Control,RootOriginalDriverColdFixture.ReadOnlyScope> writers,Map<ExactRef,Opened> guards)throws IOException {
        Opened old=guards.get(leaseRef);
        if(old!=null){require(old.control().equals(control),"same storage lease cannot borrow a different fixed readonly control");return old;}
        require(!writers.containsKey(control),"a fixed readonly control cannot acquire a second unrelated storage guard");
        var lease=RootOriginalDriverColdFixture.record(leaseRef,1<<20,RootRuntimeDefinitionModel.StorageLease.class);
        var scope=RootOriginalDriverColdFixture.openReadOnlyScope(control,leaseRef,machine,clock);
        var result=new Opened(lease,scope.writer(),scope.storage(),scope.files(),control,scope);
        writers.put(control,scope);guards.put(leaseRef,result);return result;
    }
    /** Three exact request arguments only; stdout is bounded publication metadata, never the original Driver payload. */
    public static void main(String[] arguments)throws Exception {
        if(arguments.length!=3)throw new IllegalArgumentException("expected production request path, exact bytes, SHA256");
        if(!arguments[1].matches("[1-9][0-9]{0,5}"))throw new IllegalArgumentException("canonical finite request byte count required");
        Produced result=produce(new ExactRef(arguments[0],Long.parseLong(arguments[1]),arguments[2]),Clock.systemUTC());
        var row=StrictJson.object();row.put("schema","xar.java-original-driver-cold-fixture-publication/v1");
        row.put("machine_id",result.data().machineId());row.set("fixture",CheckpointPairCodec.fileWitnessToJson(result.fixture()));
        row.put("cases",result.data().cases().size());row.put("game_launches",0);row.put("driver_wal_writes",0);
        System.out.println(new String(StrictJson.canonical(row,65536),java.nio.charset.StandardCharsets.UTF_8));
    }
    private static void current(Request request,Clock clock)throws IOException {
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||clock.instant().isBefore(instant(request.observedAtUtc()))
                ||!clock.instant().isBefore(instant(request.reviewAtUtc())))throw new IOException("fixture-production request is foreign, future-dated or expired");
    }
    private static Instant instant(String value){Instant result=Instant.parse(value);require(result.toString().equals(value),"canonical UTC time required");return result;}
    private static void require(boolean valid,String detail){if(!valid)throw new IllegalArgumentException(detail);}
}
