package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.UUID;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.application.driver.InitialDriverState;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Shared fresh Robert startup and Day0 Driver construction. Never launches/stops Game. */
public final class RootNativeFreshStartup {
    public record DayZero(NativeActionPort.AckReceived startAck, NativeFreshSnapshotPort.Received read,
            InitialDriverState.Produced produced, Originals originals) {
        public DayZero {
            if(startAck==null||read==null||produced==null||originals==null) throw new IllegalArgumentException("DayZero requires actual start, read, produced and originals");
        }
    }

    public record Originals(Path core, Path driver, Path auxiliary, Path snapshot, Path state, Path startAck, Path readAck) {
        public Originals {
            if(core==null||driver==null||auxiliary==null||snapshot==null||state==null||startAck==null||readAck==null) throw new IllegalArgumentException("Originals requires all paths");
        }
    }

    public static DayZero startFreshRobert(ManagedGameSession actualGame, NativeLaunchPlan plan, InitialEpisodePolicy.Lifecycle kind,
            RawJson actualLifecycle, Clock clock, Instant deadline) throws IOException, InterruptedException {
        if(actualGame == null || plan == null || kind == null || actualLifecycle == null || clock == null || deadline == null) throw new IOException("startFreshRobert requires non-null actualGame, plan, kind, actualLifecycle, clock, deadline");
        if(!(plan.load() instanceof NativeLaunchPlan.NewGame)) throw new IOException("startFreshRobert requires plan.load() instanceof NativeLaunchPlan.NewGame");
        var transport = actualGame.nativeTransport();
        var originalStartAck = startRobert(transport, clock, deadline);
        var actual = transport.readCoreFrame(queryDeadline(clock, deadline));
        String previousReason = null;
        while(clock.instant().isBefore(deadline)) {
            actualGame.verify();
            if(actual instanceof NativeActionPort.AckReceived pending && pending.nativeOk() && pending.originalResultToken().isPresent()) {
                var frame = decodeCore(pending.originalResultToken().orElseThrow());
                if(isCampaignReady(frame)) break;
                String reason = frame instanceof CoreFrame.Unavailable unavailable ? unavailable.reason() : "native_core_not_ready";
                if(!reason.equals(previousReason)) {
                    var progress = result(clock, "NATIVE_INITIALIZING");
                    progress.put("detail", reason);
                    emit(progress);
                    previousReason = reason;
                }
            }
            Thread.sleep(1000);
            if(!clock.instant().isBefore(deadline)) break;
            actual = transport.readCoreFrame(queryDeadline(clock, deadline));
        }
        if(!(actual instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || !ack.originalResultToken().isPresent()) {
            throw new IOException("Native core frame unavailable for fresh Robert: " + (actual instanceof NativeActionPort.AckReceived ? ((NativeActionPort.AckReceived)actual).toString() : actual.toString()));
        }
        var frame = decodeCore(ack.originalResultToken().orElseThrow());
        if(!isCampaignReady(frame)) {
            throw new IOException("Campaign not ready for fresh Robert");
        }
        var corePath = plan.evidenceRoot().resolve("native-core-frame-" + UUID.randomUUID() + ".json");
        Files.createDirectories(plan.evidenceRoot());
        Files.write(corePath, ack.originalResultToken().orElseThrow().bytes(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);

        var freshRead = transport.readFreshFullState(queryDeadline(clock, deadline));
        if(!(freshRead instanceof NativeFreshSnapshotPort.Received)) {
            if(freshRead instanceof NativeFreshSnapshotPort.Unavailable) {
                var unavailable = (NativeFreshSnapshotPort.Unavailable)freshRead;
                throw new IOException("Fresh full state read unavailable: reason=" + unavailable.reason() + " dispatch=" + unavailable.dispatch());
            }
            throw new IOException("Fresh full state read unavailable: " + freshRead.toString());
        }
        var received = (NativeFreshSnapshotPort.Received)freshRead;
        NativeFreshSnapshotPort.verifyAfter(originalStartAck, received);
        var actualFrame = received.originalFrame();
        var produced = InitialDriverState.create(actualFrame, plan.pipeName(), plan.sessionId(), kind, actualLifecycle);

        var driverBytes = produced.driver().encode();
        var auxBytes = DriverJson.encode(produced.auxiliary());
        var driverPath = plan.evidenceRoot().resolve("day0-driver-" + UUID.randomUUID() + ".bin");
        Files.write(driverPath, driverBytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var auxPath = plan.evidenceRoot().resolve("day0-auxiliary-" + UUID.randomUUID() + ".json");
        Files.write(auxPath, auxBytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var snapshotPath = plan.evidenceRoot().resolve("fresh-snapshot-" + UUID.randomUUID() + ".bin");
        Files.write(snapshotPath, actualFrame.originalPacket(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var statePath = plan.evidenceRoot().resolve("fresh-state-" + UUID.randomUUID() + ".json");
        Files.write(statePath, actualFrame.state().bytes(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var startAckPath = plan.evidenceRoot().resolve("start-ack-" + UUID.randomUUID() + ".bin");
        Files.write(startAckPath, originalStartAck.originalPacket(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var readAckPath = plan.evidenceRoot().resolve("read-ack-" + UUID.randomUUID() + ".bin");
        Files.write(readAckPath, received.acknowledgement().originalPacket(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);

        var success = result(clock, "DAY0_DRIVER_CREATED");
        success.put("episode_id", produced.driver().session().episodeRunId());
        success.put("pipe", plan.pipeName());
        success.put("date_raw", ((CoreFrame.Partial) frame).prefix().dateRaw());
        success.put("date_source", "native_core_frame");
        success.put("player_id", produced.driver().session().actorId().toString());
        success.put("snapshot_id", actualFrame.snapshotId());
        success.put("native_revision", actualFrame.nativeRevision().toString());
        success.put("session_id", actualFrame.session().sessionId());
        success.put("ordinary_planner_executed", false);
        success.put("driver_path", driverPath.toString());
        success.put("auxiliary_path", auxPath.toString());
        success.put("snapshot_path", snapshotPath.toString());
        success.put("state_path", statePath.toString());
        success.put("start_ack_path", startAckPath.toString());
        success.put("read_ack_path", readAckPath.toString());
        emit(success);

        return new DayZero(originalStartAck, received, produced, new Originals(corePath, driverPath, auxPath, snapshotPath, statePath, startAckPath, readAckPath));
    }

    static CoreFrame decodeCore(RawJson original) throws IOException {
        try {
            return CoreFrame.decode(original);
        } catch (IllegalArgumentException invalid) {
            throw new IOException("actual core-frame profile or partial result is unavailable", invalid);
        }
    }

    static boolean isCampaignReady(CoreFrame frame) {
        return frame instanceof CoreFrame.Partial partial && partial.prefix().mapReady()
                && partial.prefix().hasPlayedCharacter() && partial.prefix().playedCharacterAlive();
    }

    static boolean isMapReady(CoreFrame frame) {
        return frame instanceof CoreFrame.Partial partial && partial.prefix().mapReady();
    }

    static boolean isObservedCoreReady(CoreFrame frame, boolean freshRobert) {
        return frame instanceof CoreFrame.Partial && (!freshRobert || isCampaignReady(frame));
    }

    public static NativeActionPort.AckReceived observeBootstrapCore(ManagedGameSession actualGame, Clock clock, Instant deadline) throws IOException, InterruptedException {
        if (actualGame == null || clock == null || deadline == null) throw new IOException("observeBootstrapCore requires non-null actualGame, clock, deadline");
        var transport = actualGame.nativeTransport();
        String lastDetail = "No core frame observed";
        while (clock.instant().isBefore(deadline)) {
            actualGame.verify();
            var actual = transport.readCoreFrame(queryDeadline(clock, deadline));
            if (actual instanceof NativeActionPort.AckReceived ack && ack.nativeOk() && ack.originalResultToken().isPresent()) {
                return ack;
            }
            if (actual instanceof NativeActionPort.AckReceived ack) {
                lastDetail = new String(ack.originalFrame().bytes(), java.nio.charset.StandardCharsets.UTF_8);
            } else {
                lastDetail = actual.toString();
            }
            Thread.sleep(1000);
        }
        throw new IOException("Native core frame observation timeout: " + lastDetail);
    }

    public static NativeActionPort.AckReceived startRobert(NativeGameTransport transport, Clock clock, Instant until) throws IOException, InterruptedException {
        var hello = transport.originalHello();
        var source = new FrontendRulesData.Source(new FrontendRulesData.Binding(hello.pid(), hello.connectionGeneration()), FrontendRulesData.Build.CK3_12004);
        FrontendRulesData.Route route;
        do {
            route = frontendRoute(transport, source, clock, until).route();
            if(route != FrontendRulesData.Route.UNAVAILABLE) break;
            Thread.sleep(1000);
        } while(clock.instant().isBefore(until));
        if(route == FrontendRulesData.Route.MAIN_MENU) {
            frontendMutation(transport, Primitive.NEW_GAME, clock, until);
            do {
                route = frontendRoute(transport, source, clock, until).route();
                if(route == FrontendRulesData.Route.BOOKMARKS) break;
                Thread.sleep(1000);
            } while(clock.instant().isBefore(until));
        }
        if(route != FrontendRulesData.Route.BOOKMARKS) throw new IOException("Fresh Robert requires the actual bookmarks route; observed " + route);
        var model = awaitModel(transport, source, value -> value.accepted(), clock, until);
        if(!model.supported1066BookmarkSelected()) {
            frontendMutation(transport, Primitive.SELECT_1066_BOOKMARK, clock, until);
        }
        model = awaitModel(transport, source, value -> value.supported1066BookmarkSelected() && value.candidateIdentityReady() && value.targetIndex() >= 0 && value.status().equals("identity_ready"), clock, until);
        model.requireSupported1066Bookmark();
        model.selected("bookmark_rags_to_riches_duke_robert", false, false);
        if(model.selectedIndex() != model.targetIndex()) {
            frontendMutation(transport, Primitive.SELECT_1066, clock, until);
            model = awaitModel(transport, source, value -> value.supported1066BookmarkSelected() && value.candidateIdentityReady() && value.targetIndex() >= 0 && value.selectedIndex() == value.targetIndex(), clock, until);
        }
        var candidate = model.selected("bookmark_rags_to_riches_duke_robert", false, true);
        var selected = result(clock, "ROBERT_1066_SELECTED");
        selected.put("character_key", candidate.characterNameKey());
        selected.put("date_raw", candidate.dateRaw());
        emit(selected);
        return frontendMutation(transport, Primitive.START_BOOKMARK, clock, until);
    }

    private static Instant queryDeadline(Clock clock, Instant until) {
        Instant next = clock.instant().plusSeconds(30);
        return next.isBefore(until) ? next : until;
    }

    private static void emitHeartbeat(NativeGameTransport transport, Clock clock) throws IOException {
        var cached = transport.diagnostics().latestHeartbeat();
        if(cached.isEmpty()) return;
        var notice = cached.orElseThrow();
        var diagnostic = result(clock, "NATIVE_HEARTBEAT_DIAGNOSTIC");
        diagnostic.put("received_at", notice.observedAt().toString());
        diagnostic.put("original_payload", new String(notice.original().payload().value(), java.nio.charset.StandardCharsets.UTF_8));
        emit(diagnostic);
    }

    private static NativeActionPort.AckReceived frontendReply(NativeGameTransport transport, Primitive step, Clock clock, Instant until) throws IOException, InterruptedException {
        boolean readOnly = step == Primitive.ROUTE || step == Primitive.BOOKMARK_MODEL;
        String previousFailure = null, lastDetail = "No frontend result before the operation timeout";
        while(clock.instant().isBefore(until)) {
            var actual = transport.frontendBootstrap(step, queryDeadline(clock, until));
            if(actual instanceof NativeActionPort.AckReceived ack && ack.nativeOk() && ack.originalResultToken().isPresent() && ack.custody().isPresent()) return ack;
            String failureKey;
            if(actual instanceof NativeActionPort.AckReceived ack) {
                lastDetail = new String(ack.originalFrame().bytes(), java.nio.charset.StandardCharsets.UTF_8);
                var frame = FrontendRulesCodec.object(ack.originalFrame());
                failureKey = frame.has("error") ? frame.get("error").toString() : lastDetail;
            } else { lastDetail = actual.toString(); failureKey = lastDetail; }
            if(!failureKey.equals(previousFailure)) {
                var pending = result(clock, readOnly ? "FRONTEND_READ_UNAVAILABLE" : "FRONTEND_MUTATION_UNCONFIRMED");
                pending.put("step", step.name());
                pending.put("detail", lastDetail);
                emit(pending);
                previousFailure = failureKey;
                emitHeartbeat(transport, clock);
            }
            if(!readOnly) throw new IOException("Native frontend " + step + " did not return its result; no mutation replay: " + lastDetail);
            Thread.sleep(1000);
        }
        throw new IOException("Native frontend " + step + " did not become available before the operation timeout: " + lastDetail);
    }

    private static FrontendRulesData.ObservedRoute frontendRoute(NativeGameTransport transport, FrontendRulesData.Source source, Clock clock, Instant until) throws IOException, InterruptedException {
        var ack = frontendReply(transport, Primitive.ROUTE, clock, until);
        return FrontendRulesCodec.route(ack.originalResultToken().orElseThrow(), source, ack.custody().orElseThrow().responseReceived().order());
    }

    private static FrontendRulesData.BookmarkModel frontendModel(NativeGameTransport transport, FrontendRulesData.Source source, Clock clock, Instant until) throws IOException, InterruptedException {
        var ack = frontendReply(transport, Primitive.BOOKMARK_MODEL, clock, until);
        return FrontendRulesCodec.bookmarkModel(ack.originalResultToken().orElseThrow(), source, ack.custody().orElseThrow().responseReceived().order());
    }

    private static FrontendRulesData.BookmarkModel awaitModel(NativeGameTransport transport, FrontendRulesData.Source source, Predicate<FrontendRulesData.BookmarkModel> ready, Clock clock, Instant until) throws IOException, InterruptedException {
        while(clock.instant().isBefore(until)) {
            var model = frontendModel(transport, source, clock, until);
            if(ready.test(model)) return model;
            Thread.sleep(1000);
        }
        throw new IOException("Robert bookmark model did not become ready before the operation timeout");
    }

    private static NativeActionPort.AckReceived frontendMutation(NativeGameTransport transport, Primitive step, Clock clock, Instant until) throws IOException, InterruptedException {
        var ack = frontendReply(transport, step, clock, until);
        FrontendRulesCodec.nativeAck(ack.originalResultToken().orElseThrow(), step.emptyRequest().step());
        var progress = result(clock, "FRONTEND_ACK_POSTSTATE_PENDING");
        progress.put("step", step.name());
        progress.put("request_id", ack.requestId());
        emit(progress);
        return ack;
    }

    private static ObjectNode result(Clock clock, String status) {
        return StrictJson.object().put("schema", "xar.java-root-startup-result/v1")
                .put("machine_id", WindowsJobProcess.currentMachineId())
                .put("observed_at_utc", clock.instant().toString()).put("status", status);
    }

    private static void emit(ObjectNode result) throws IOException {
        System.out.write(StrictJson.canonical(result, StrictJson.EXPLICIT_MAX_BYTES));
        System.out.write(10);
        System.out.flush();
        if(System.out.checkError()) throw new IOException("physical launch result stdout failed");
    }
}
