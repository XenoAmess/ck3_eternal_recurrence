package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Shared finite physical launch: ordinary configuration, managed Game, one native read, cleanup. */
@QuarkusMain(name="finite-first-live")
public final class RootFiniteFirstLiveMain implements QuarkusApplication {
    public static void main(String... args) throws Exception { System.exit(new RootFiniteFirstLiveMain().run(args)); }

    /** One plain configuration path; the existing invocation's configuration body is also accepted. */
    @Override public int run(String... args)throws Exception {
        if(args.length<1||args.length>2)throw new IllegalArgumentException("finite-first-live requires one ordinary launch configuration path and optionally one policy path");
        Clock clock=Clock.systemUTC();
        NativeLaunchPlan plan=readConfiguration(Path.of(args[0]),clock);
        boolean driverRequested=args.length==2;
        InitialEpisodePolicy.Lifecycle driverKind=null;
        RawJson driverLifecycle=null;
        if(driverRequested) {
            if(!(plan.load() instanceof NativeLaunchPlan.NewGame)) {
                var rejected=result(clock,"DRIVER_REQUIRES_FRESH_ROBERT_START");
                rejected.put("detail","Driver policy requires fresh Robert start; saved-game policy path is unsupported");
                emit(rejected);return 4;
            }
            var policyDoc=StrictJson.parse(Files.readAllBytes(Path.of(args[1])),StrictJson.EXPLICIT_MAX_BYTES);
            var succession=policyDoc.get("succession_lifecycle");
            if(!(succession instanceof ObjectNode))throw new IOException("policy requires succession_lifecycle object");
            String lifecycle=StrictJson.text(succession.get("lifecycle"));
            driverKind=switch(lifecycle) {
                case "rogue_one_life" -> InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE;
                case "ordinary_campaign_succession" -> InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION;
                default -> throw new IllegalArgumentException("unsupported succession lifecycle: "+lifecycle);
            };
            driverLifecycle=new RawJson(StrictJson.canonical(succession));
        }
        JavaGameLifecycle lifecycle=new JavaGameLifecycle(List.of());
        ManagedGameSession game=null;
        NativeGameTransport transport=null;
        Exception primary=null;
        try {
            var launch=plan.load() instanceof NativeLaunchPlan.SavedGame
                    ?lifecycle.launchSaved(plan):lifecycle.launchNew(plan);
            if(launch instanceof JavaGameLifecycle.Unknown unknown) {
                var result=result(clock,"LAUNCH_UNKNOWN_NO_REPLAY");
                result.put("request_id",unknown.requestId());result.put("detail",unknown.reason());
                emit(result);return 3;
            }
            if(launch instanceof JavaGameLifecycle.Rejected rejected) {
                var result=result(clock,"LAUNCH_REJECTED");result.put("detail",rejected.reason());
                emit(result);return 2;
            }
            var started=(JavaGameLifecycle.Started)launch;
            game=started.session();
            transport=game.nativeTransport();
            var result=result(clock,"PHYSICAL_GAME_AND_NATIVE_HELLO");
            result.set("game",game.generation().toJson());result.set("native_hello",started.nativeHello().toJson());
            emit(result);
            Instant readDeadline=clock.instant().plus(plan.startupTimeout());
            if(readDeadline.isAfter(plan.deadline()))readDeadline=plan.deadline();
            boolean freshRobert=plan.load() instanceof NativeLaunchPlan.NewGame;
            if(freshRobert&&driverRequested) {
                RootNativeFreshStartup.startFreshRobert(game,plan,driverKind,driverLifecycle,clock,readDeadline);
                return 0;
            }
            if(freshRobert)RootNativeFreshStartup.startRobert(transport,clock,readDeadline);
            var actual=transport.readCoreFrame(queryDeadline(clock,readDeadline));
            String previousReason=null;
            while(clock.instant().isBefore(readDeadline)) {
                game.verify();
                if(actual instanceof NativeActionPort.AckReceived pending&&pending.nativeOk()&&pending.originalResultToken().isPresent()) {
                    var frame=RootNativeFreshStartup.decodeCore(pending.originalResultToken().orElseThrow());
                    if(RootNativeFreshStartup.isObservedCoreReady(frame,freshRobert))break;
                    String reason=frame instanceof CoreFrame.Unavailable unavailable?unavailable.reason():"native_core_not_ready";
                    if(!reason.equals(previousReason)) {
                        var progress=result(clock,"NATIVE_INITIALIZING");progress.put("detail",reason);emit(progress);
                        previousReason=reason;
                    }
                }
                Thread.sleep(1000);
                if(!clock.instant().isBefore(readDeadline))break;
                actual=transport.readCoreFrame(queryDeadline(clock,readDeadline));
            }
            var read=result(clock,"NATIVE_CORE_FRAME_UNAVAILABLE");
            read.set("game",game.generation().toJson());
            boolean success=false;
            if(actual instanceof NativeActionPort.AckReceived ack) {
                read.put("native_ok",ack.nativeOk());
                if(ack.originalResultToken().isPresent()) {
                    byte[] bytes=ack.originalResultToken().orElseThrow().bytes();
                    Files.createDirectories(plan.evidenceRoot());
                    Path target=plan.evidenceRoot().resolve("native-core-frame-"+UUID.randomUUID()+".json");
                    Files.write(target,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
                    read.put("original_result_path",target.toString());read.put("original_result_bytes",bytes.length);
                    var frame=RootNativeFreshStartup.decodeCore(ack.originalResultToken().orElseThrow());
                    success=ack.nativeOk()&&RootNativeFreshStartup.isObservedCoreReady(frame,freshRobert);
                    if(frame instanceof CoreFrame.Partial partial) {
                        var prefix=partial.prefix();
                        read.put("core_available",true);read.put("application_main_observed",true);
                        read.put("campaign_ready",RootNativeFreshStartup.isCampaignReady(frame));
                        read.put("date_raw",prefix.dateRaw());read.put("speed",prefix.speed());read.put("paused",prefix.paused());
                        read.put("local_player_id",prefix.localPlayerId());read.put("map_ready",prefix.mapReady());
                        read.put("played_character_id",prefix.playedCharacterId());read.put("played_character_alive",prefix.playedCharacterAlive());
                        if(success)read.put("status",freshRobert?"FRESH_ROBERT_CAMPAIGN_OBSERVED":"NATIVE_CORE_AVAILABLE");
                    } else if(frame instanceof CoreFrame.Unavailable unavailable) {
                        read.put("core_available",false);read.put("application_main_observed",unavailable.applicationMainObserved());
                        read.put("detail",unavailable.reason());
                        read.put("campaign_ready",false);
                        for(String field:List.of("date_raw","speed","paused","map_ready","local_player_id","played_character_id","played_character_alive"))read.putNull(field);
                    }
                }
                emit(read);
                if(!freshRobert)emit(result(clock,"DRIVER_NOT_REQUESTED_NO_FRESH_START"));
                else emit(result(clock,"DRIVER_NOT_REQUESTED"));
                return success?0:4;
            }
            read.put("detail",actual.toString());emit(read);
            if(!driverRequested) {
                if(!freshRobert)emit(result(clock,"DRIVER_NOT_REQUESTED_NO_FRESH_START"));
                else emit(result(clock,"DRIVER_NOT_REQUESTED"));
            } else {
                emit(result(clock,"DRIVER_BLOCKED_CORE_NOT_READY"));
            }
            return 4;
        }catch(Exception failure) {
            primary=failure;
            var failed=result(clock,"PHYSICAL_LAUNCH_OR_READ_FAILED");
            failed.put("exception_type",failure.getClass().getName());failed.put("detail",String.valueOf(failure.getMessage()));
            emit(failed);throw failure;
        }finally {
            if(game!=null)try {
                if(transport!=null)emitHeartbeat(transport,clock);
                var stopped=game.stopTracked(game.generation(),clock.instant().plusSeconds(25),false);
                var closed=result(clock,"ORIGINAL_GAME_CLEANUP");
                closed.set("game",stopped.generation().toJson());closed.put("cleanup_proven",stopped.cleanupProven());
                closed.put("active_processes",stopped.terminal().accounting().activeProcesses());
                closed.put("full_job_terminal_passed",stopped.terminal().passed());emit(closed);
            }catch(Exception cleanup) {
                if(primary!=null)primary.addSuppressed(cleanup);else throw cleanup;
            }
        }
    }

    private static Instant queryDeadline(Clock clock,Instant until) {
        Instant next=clock.instant().plusSeconds(30);return next.isBefore(until)?next:until;
    }

    private static void emitHeartbeat(NativeGameTransport transport,Clock clock)throws IOException {
        var cached=transport.diagnostics().latestHeartbeat();
        if(cached.isEmpty())return;
        var notice=cached.orElseThrow();
        var diagnostic=result(clock,"NATIVE_HEARTBEAT_DIAGNOSTIC");
        diagnostic.put("received_at",notice.observedAt().toString());
        diagnostic.put("original_payload",new String(notice.original().payload().value(),java.nio.charset.StandardCharsets.UTF_8));
        emit(diagnostic);
    }

    static NativeLaunchPlan readConfiguration(Path source,Clock clock)throws IOException {
        var document=StrictJson.parse(Files.readAllBytes(source),StrictJson.EXPLICIT_MAX_BYTES);
        var body=document.has("configuration")?document.get("configuration"):document;
        if(!(body instanceof ObjectNode configuration))throw new IOException("ordinary launch configuration object required");
        ObjectNode actual=configuration.deepCopy();
        Instant deadline=clock.instant().plusSeconds(900);
        actual.put("deadline",deadline.toString());
        if(!(actual.get("steam") instanceof ObjectNode steam))throw new IOException("Steam launch configuration required");
        steam.put("deadline",deadline.toString());
        return NativeLaunchPlanCodec.fromJson(actual).accept();
    }

    private static ObjectNode result(Clock clock,String status) {
        return StrictJson.object().put("schema","xar.java-root-startup-result/v1")
                .put("machine_id",WindowsJobProcess.currentMachineId())
                .put("observed_at_utc",clock.instant().toString()).put("status",status);
    }
    private static void emit(ObjectNode result)throws IOException {
        System.out.write(StrictJson.canonical(result,StrictJson.EXPLICIT_MAX_BYTES));
        System.out.write(10);System.out.flush();
        if(System.out.checkError())throw new IOException("physical launch result stdout failed");
    }
}
