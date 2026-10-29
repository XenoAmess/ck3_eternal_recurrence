package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** The actual Saved daemon route retains its original creator, result and input witnesses. */
public final class RootSavedNativeCoordinator {
    public static final String SCHEMA="xar.java-root-saved-native-startup/v1";
    public record Arguments(FileRef startup,Optional<FileRef> savedRoute) {
        public Arguments {Objects.requireNonNull(startup);Objects.requireNonNull(savedRoute);}
    }
    /** The single production CLI decoder preserves the ordinary exact3 and requires explicit Saved exact6. */
    public static Arguments arguments(String[] args) {
        Objects.requireNonNull(args);
        StrictJson.require(args.length==3||args.length==6,"RootApplicationMain requires startup exact3, optionally followed by explicit Saved route exact3");
        return new Arguments(argument(args,0),args.length==6?Optional.of(argument(args,3)):Optional.empty());
    }
    private static FileRef argument(String[] args,int offset) {
        long bytes=Long.parseLong(args[offset+1]);StrictJson.require(bytes>0&&Long.toString(bytes).equals(args[offset+1]),"canonical positive startup byte count required");
        return new FileRef(args[offset],bytes,args[offset+2]);
    }
    public record Request(String schema,String machineId,String reviewAtUtc,FileRef startup,
            FileRef checkpointPair,String evidenceDirectory) {
        public Request {
            StrictJson.require(SCHEMA.equals(schema),"explicit Saved native startup schema required");
            StrictJson.text(machineId);Instant until=Instant.parse(reviewAtUtc);
            StrictJson.require(reviewAtUtc.equals(until.toString()),"canonical Saved startup review required");
            Objects.requireNonNull(startup);Objects.requireNonNull(checkpointPair);
            for(String value:List.of(startup.path(),checkpointPair.path(),evidenceDirectory)) {
                Path path=Path.of(StrictJson.text(value));StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized Saved startup paths required");
            }
            StrictJson.require(checkpointPair.bytes()>0&&checkpointPair.bytes()<=65536,"bounded actual checkpoint pair source required");
        }
    }
    private final Request request;
    private final SharedSourceFiles.Witness requestWitness,pairWitness;
    private final CheckpointPair pair;
    private final NativeLaunchPlan plan;
    private final JavaGameLifecycle owner;
    private final Clock clock;
    private boolean launchEntered,adoptionEntered;
    private JavaGameLifecycle.Started originalStarted;
    private RootPrivateBootstrap.Original original;
    private RootSavedNativeCoordinator(Request request,SharedSourceFiles.Witness requestWitness,SharedSourceFiles.Witness pairWitness,
            CheckpointPair pair,NativeLaunchPlan plan,JavaGameLifecycle owner,Clock clock) {
        this.request=request;this.requestWitness=requestWitness;this.pairWitness=pairWitness;this.pair=pair;
        this.plan=plan;this.owner=owner;this.clock=clock;
    }
    public static RootSavedNativeCoordinator readExact(FileRef source,FileRef actualStartup,NativeLaunchPlan identicalPlan,
            JavaGameLifecycle actualOwner,Clock actualClock)throws IOException {
        Objects.requireNonNull(actualOwner);Objects.requireNonNull(actualClock);Objects.requireNonNull(identicalPlan);
        var held=SharedSourceFiles.observe(Path.of(source.path()));
        if(!held.source().equals(source))throw new IOException("Saved startup request differs from its original source");
        byte[] bytes=RootRuntimeDefinitions.read(source,65536);StrictJson.parse(bytes,65536);
        var request=ControlBuild.strictMapper().readValue(bytes,Request.class);
        if(!request.startup().equals(actualStartup))throw new IOException("Saved route crossed the actual Quarkus startup source");
        var pairHeld=SharedSourceFiles.observe(Path.of(request.checkpointPair().path()));
        if(!pairHeld.source().equals(request.checkpointPair()))throw new IOException("Saved pair differs from its exact request source");
        CheckpointPair pair=CheckpointPairCodec.decode(RootRuntimeDefinitions.read(request.checkpointPair(),65536));
        var result=new RootSavedNativeCoordinator(request,held,pairHeld,pair,identicalPlan,actualOwner,actualClock);
        result.requireCurrent();return result;
    }
    public synchronized JavaGameLifecycle.LaunchResult launch()throws IOException,InterruptedException {
        if(launchEntered)throw new IOException("Saved CREATE route is already entered; use original lifecycle query, never replay");
        requireCurrent();launchEntered=true;
        JavaGameLifecycle.LaunchResult result=owner.launchSaved(plan);
        if(result instanceof JavaGameLifecycle.Started started)originalStarted=started;
        return result;
    }
    public synchronized RootPrivateBootstrap.Original adopt(RootRuntimeContext context,RootLegacyResumeRuntime actualResume,
            int retainedFrames)throws IOException,InterruptedException {
        if(adoptionEntered||originalStarted==null)throw new IOException("Saved adoption requires this route's unconsumed original Started result");
        requireCurrent();
        if(context.game()!=originalStarted.session()||context.game().launchPlan()!=plan)
            throw new IOException("Saved adoption crossed the actual original creator Game or plan");
        adoptionEntered=true;
        try(var prepared=RootPrivateBootstrap.prepare(context,owner,originalStarted,pair,actualResume,
                Path.of(request.evidenceDirectory()),deadline())) {
            original=context.core().adoptColdOriginal(prepared,retainedFrames);requireCurrent();return original;
        }
    }
    public void requireOwner(JavaGameLifecycle actualOwner,NativeLaunchPlan actualPlan)throws IOException {
        if(owner!=actualOwner||plan!=actualPlan)throw new IOException("Saved route crossed its original lifecycle owner or Native plan");
        requireCurrent();
    }
    public Instant deadline(){return Instant.parse(request.reviewAtUtc());}
    public synchronized RootPrivateBootstrap.Original original()throws IOException {
        if(original==null)throw new IOException("Actual cold canonical adoption has not completed");return original;
    }
    private void requireCurrent()throws IOException {
        Instant review=deadline();
        if(!clock.instant().isBefore(review)||review.isAfter(plan.deadline())
                ||!request.machineId().equals(plan.sources().review().machineId())
                ||!(plan.load() instanceof NativeLaunchPlan.SavedGame saved)
                ||!new ExactRef(saved.save().path(),saved.save().bytes(),saved.save().sha256()).equals(pair.save().reference())
                ||!Path.of(request.evidenceDirectory()).getParent().equals(plan.evidenceRoot()))
            throw new IOException("Saved route lost its exact machine, deadline, Native SAVE/pair or fresh evidence location");
        SharedSourceFiles.assertUnchanged(requestWitness);SharedSourceFiles.assertUnchanged(pairWitness);
        if(!SharedSourceFiles.nativeFile(Path.of(requestWitness.source().path())).equals(requestWitness.nativeFile())
                ||!SharedSourceFiles.nativeFile(Path.of(pairWitness.source().path())).equals(pairWitness.nativeFile()))
            throw new IOException("Saved request or checkpoint pair native file identity changed");
        plan.sources().verify();plan.preparedProfile().verify(plan);
        for(var source:requiredSources())plan.sources().requireLoadedClass(source.type());
    }
    /** Actual configuration production and source consumers share this one typed source list. */
    public static List<RootRuntimeSourceProducts.RequiredSource> requiredSources() {
        var local=RootRuntimeSelectedSources.Module.LOCAL_SERVICE;var app=RootRuntimeSelectedSources.Module.APPLICATION;
        var result=new java.util.LinkedHashSet<>(List.of(new RootRuntimeSourceProducts.RequiredSource(local,RootSavedNativeCoordinator.class),
                new RootRuntimeSourceProducts.RequiredSource(local,Request.class),
                new RootRuntimeSourceProducts.RequiredSource(local,RootApplicationMain.class),
                new RootRuntimeSourceProducts.RequiredSource(local,RootQuarkusEntrypoint.class),
                new RootRuntimeSourceProducts.RequiredSource(local,RootRuntimeLaunchCommand.class),
                new RootRuntimeSourceProducts.RequiredSource(local,RootRuntimeStartup.class),
                new RootRuntimeSourceProducts.RequiredSource(local,RootRuntimeReadiness.class),
                new RootRuntimeSourceProducts.RequiredSource(app,CheckpointPairCodec.class)));
        for(Class<?> host:List.of(RootSavedNativeCoordinator.class,RootRuntimeStartup.class,RootRuntimeReadiness.class,
                RootQuarkusEntrypoint.class,RootRuntimeLaunchCommand.class))
            for(Class<?> actual:host.getDeclaredClasses())result.add(new RootRuntimeSourceProducts.RequiredSource(local,actual));
        return List.copyOf(result);
    }
    static void requireConfiguredSource(RootRuntimeDefinitionModel.Configuration configuration,ExactRef selected)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(selected);
        if(RootRuntimeDefinitions.configuredSources(configuration).stream().noneMatch(row->row.sourceRef().equals(selected)))
            throw new IOException("Saved native Java source is absent from the original configured closure: "+selected.path());
    }
}
