package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;

/** Actual managed-Game composition. Domain permissions alone never bypass physical source custody. */
public final class RootManagedLifecycleFactory {
    private final RootApplicationAssembly.Core core;
    private final RootRuntimeCatalogFactory catalogs;
    private final NativeLaunchPlan initialPlan;
    private final Clock clock;
    private List<NativePrivateActionPermission> permissions;
    private JavaGameLifecycle lifecycle;
    private IOException failure;

    public RootManagedLifecycleFactory(RootApplicationAssembly.Core core,RootRuntimeCatalogFactory catalogs,
            NativeLaunchPlan actualRetainedPlan,Clock clock) {
        this.core=Objects.requireNonNull(core);this.catalogs=Objects.requireNonNull(catalogs);
        initialPlan=Objects.requireNonNull(actualRetainedPlan);this.clock=Objects.requireNonNull(clock);
    }
    public void requireOwner(RootApplicationAssembly.Core actual)throws IOException {
        if(Objects.requireNonNull(actual)!=core)throw new IOException("managed lifecycle factory belongs to another original Core");
        catalogs.requireBoundCore(actual);
    }

    /** Source custody only; the caller still needs the actual held read/admission scope. */
    public void requireProducerSource(ExactRef actual)throws IOException {
        if(catalogs.sources().historicalPackage().isEmpty())return;
        Objects.requireNonNull(actual);requireOwner(core);core.configuration().requireCurrent(clock);
        var same=core.writer().borrowedSession();core.writer().requireSession(same);
        JavaGameLifecycle original;
        synchronized(this) {original=lifecycle;}
        if(original==null)throw new IOException("original managed creator is not retained");
        var game=original.currentSession().orElseThrow(()->new IOException("actual managed Game is unavailable"));
        game.verify();var plan=game.launchPlan();
        if(plan.sources()!=initialPlan.sources())throw new IOException("producer custody crossed the retained managed source authority");
        var context=catalogs.requireCurrent(new SessionIdentity(game.machineId(),game.generation(),game.sessionId()));
        if(context.game()!=game||context.core()!=core||context.archive()!=core.archive())
            throw new IOException("producer custody is outside the actual Root/context/archive");
        requireProducer(plan,actual);game.verify();core.writer().requireSession(same);
    }

    /** One creator is retained before CREATE, and reused by actual Saved replacement producers. */
    public synchronized JavaGameLifecycle create()throws IOException {
        if(failure!=null)throw new IOException("actual managed lifecycle binding already failed; partial setup is not replayed",failure);
        catalogs.requireBoundCore(core);
        if(lifecycle!=null)return lifecycle;
        boolean historical=catalogs.sources().historicalPackage().isPresent();
        if(historical) {
            core.configuration().requireCurrent(clock);initialPlan.sources().verify();
            var configured=NativeLaunchPlanCodec.fromJson(StrictJson.parse(RootRuntimeDefinitions.read(
                    RootApplicationConfiguration.file(core.configuration().nativeLaunchPlan()),NativeLaunchPlanCodec.MAXIMUM_BYTES)));
            if(!NativeLaunchPlanCodec.describe(initialPlan).equals(configured))
                throw new IOException("managed lifecycle did not receive the actual configured retained launch plan");
            if(!initialPlan.sources().review().machineId().equals(core.configuration().machineId()))
                throw new IOException("managed lifecycle source review belongs to another actual Core machine");
            for(Class<?> type:List.of(getClass(),JavaGameLifecycle.class,NativePrivateActionPermission.class))initialPlan.sources().requireLoadedClass(type);
        }
        var actual=catalogs.privatePermissions(this::qualifyPrivate);
        if(historical) {
            if(actual.isEmpty())throw new IOException("INCOMPLETE_ROOT_RUNTIME: actual private permission closure is empty");
            for(NativePrivateActionPermission permission:actual)requireProducer(initialPlan,permission.originalProducerSource());
        } else actual=actual.stream().map(NativePrivateActionPermission::withoutSourceQualification).toList();
        permissions=List.copyOf(actual);lifecycle=new JavaGameLifecycle(permissions);
        try {catalogs.sources().remainingDomains().bindManagedLifecycle(lifecycle,initialPlan);}
        catch(IOException|RuntimeException failed) {failure=new IOException("actual remaining-domain managed lifecycle binding failed",failed);throw failure;}
        return lifecycle;
    }

    /** Narrow bridge for the once-bound pre-Core Activity source producer; no caller-supplied verifier is accepted. */
    public ExactRef qualifyPrivate(NativePipeEndpoint.Config config,NativeWire.Hello hello,
            GuardEvidence guard,NativeRequest request)throws IOException {
        if(catalogs.sources().historicalPackage().isEmpty())throw new IOException("historical source qualification is not configured");
        requireFrame(config,hello,guard,request,clock.instant());catalogs.requireBoundCore(core);
        core.configuration().requireCurrent(clock);
        // The coordinator must already own this exact writer scope. Never open a replacement lock here.
        var same=core.writer().borrowedSession();core.writer().requireSession(same);
        JavaGameLifecycle original;
        List<NativePrivateActionPermission> installed;
        synchronized(this) { original=lifecycle;installed=permissions; }
        if(original==null||installed==null)throw new IOException("original managed creator is not retained");
        var permission=installed.stream().filter(value->value.operation().value().equals(request.step())).findFirst()
                .orElseThrow(()->new IOException("private action is absent from the retained actual permission closure"));
        var game=original.currentSession().orElseThrow(()->new IOException("actual managed Game is unavailable"));
        game.verify();var plan=game.launchPlan();
        if(plan.sources()!=initialPlan.sources()||!game.generation().equals(config.game())
                ||!game.machineId().equals(config.machineId())||!game.sessionId().equals(config.sessionId())
                ||!plan.pipeName().equals(config.pipeName()))
            throw new IOException("private action crossed the original creator, actual Game or retained source authority");
        requireProducer(plan,permission.originalProducerSource());
        var transport=game.nativeTransport();
        if(transport.originalHello()!=hello)throw new IOException("private action did not retain the actual transport hello object");
        var context=catalogs.requireCurrent(new SessionIdentity(config.machineId(),config.game(),config.sessionId()));
        if(context.game()!=game||context.core()!=core||context.archive()!=core.archive()||!context.source().equals(guard.source()))
            throw new IOException("private action is outside the actual admitted Root/context/archive");
        var session=new TransportSession(config.machineId(),config.game(),hello.connectionGeneration(),config.sessionId());
        var qualification=context.sources().verifyPhysicalOrigin(same,session,guard.source(),guard.nativeEvidence(),
                transport.diagnostics(),guard.validUntil());
        qualification.assertCurrent(same);
        // Source qualification is separately archived from business completion; it grants no action or game-day credit.
        var row=StrictJson.object();row.put("schema","xar.java-managed-private-source-qualification/v1");
        row.put("machine_id",config.machineId());row.put("observed_at_utc",clock.instant().toString());
        row.set("game",config.game().toJson());row.put("session_id",config.sessionId());
        row.put("connection_generation",hello.connectionGeneration().toString());row.put("operation",request.step());
        row.put("permission_key",permission.permissionKey());row.set("producer",permission.originalProducerSource().toJson());
        row.set("native_evidence",guard.nativeEvidence().toJson());row.set("source_qualification",qualification.proof().orElseThrow().toJson());
        row.set("host_configuration",exact(catalogs.sources().hostConfiguration()).toJson());
        byte[] bytes=StrictJson.canonical(row);var proof=core.archive().preserveArtifact(same,bytes,StrictJson.EXPLICIT_MAX_BYTES);
        if(!java.util.Arrays.equals(bytes,core.archive().readArtifact(same,proof,StrictJson.EXPLICIT_MAX_BYTES)))
            throw new IOException("actual private source qualification readback changed");
        qualification.assertCurrent(same);game.verify();return proof;
    }

    /** Narrow data gate shared with regression tests; passing it alone grants no authority. */
    static void requireFrame(NativePipeEndpoint.Config config,NativeWire.Hello hello,GuardEvidence guard,
            NativeRequest request,Instant now)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(hello);Objects.requireNonNull(guard);Objects.requireNonNull(request);Objects.requireNonNull(now);
        if(request.requiredCapability().isPresent()||!guard.operation().value().equals(request.step())
                ||!guard.origin().game().equals(config.game())||!guard.origin().machineId().equals(config.machineId())
                ||!guard.source().machineId().equals(config.machineId())||!guard.sessionId().equals(config.sessionId())
                ||!guard.connectionGeneration().equals(hello.connectionGeneration())||hello.pid()!=config.game().pid()
                ||!hello.bridgeVersion().equals(config.expectedBridgeVersion())||!hello.gameSha256().equalsIgnoreCase(config.expectedGameSha256())
                ||!hello.adapterId().equals(config.expectedAdapterId())||!hello.buildMatch()
                ||now.isBefore(guard.observedAt())||!now.isBefore(guard.validUntil()))
            throw new IOException("private action requires its exact current native/guard/source/session/build binding");
    }

    private static void requireProducer(NativeLaunchPlan plan,ExactRef producer)throws IOException {
        var nativeFiles=plan.sources().nativeProof().expected().completeSources();
        var runtimeFiles=plan.sources().review().completeRuntimeSources();
        boolean found=false;
        for(FileRef source:java.util.stream.Stream.concat(nativeFiles.stream(),runtimeFiles.stream()).toList())
            if(source.bytes()==producer.bytes()&&source.sha256().equals(producer.sha256())
                    &&Path.of(source.path()).toRealPath().equals(Path.of(producer.path()).toRealPath())) {source.verify();found=true;break;}
        if(!found)throw new IOException("private producer is outside the actual complete native/runtime source closure");
    }
    private static ExactRef exact(FileRef source) {return new ExactRef(source.path(),source.bytes(),source.sha256());}
}
