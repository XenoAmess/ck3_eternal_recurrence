package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Operator retirement of a physically released failed launch; original UNKNOWN records remain immutable. */
public final class ReleasedLaunchFailure {
    private static final String EFFECT="RELEASED_FAILURE_RETIRED_UNKNOWN_RETAINED_NO_REPLAY";
    private static final int MAXIMUM_BYTES=65536;
    private ReleasedLaunchFailure() { }
    public record Request(String schema,String machineId,String requestId,String sessionId,String nonce,
            WindowsJobProcess.ProcessIdentity game,String stateDirectory,ControlBuild.FileRef claim,
            ControlBuild.FileRef unsafeMarker,ControlBuild.FileRef terminalEvidence,String operatorDecisionId,String deadlineUtc) {
        public Request {
            if(!"xar.java-game-released-failure-request/v1".equals(schema))throw new IllegalArgumentException("Released-failure request schema required");
            token(machineId);token(requestId);token(sessionId);token(nonce);token(operatorDecisionId);
            Objects.requireNonNull(game);Objects.requireNonNull(claim);Objects.requireNonNull(unsafeMarker);Objects.requireNonNull(terminalEvidence);
            if(stateDirectory==null||!Path.of(stateDirectory).isAbsolute())throw new IllegalArgumentException("Absolute original state directory required");
            Instant.parse(deadlineUtc);
        }
    }
    /** This record grants physical resource retirement only, never action success or a replay. */
    record Receipt(String schema,Request request,String observedAtUtc,Win32Host.ProcessInventory processInventory,String effect) { }
    private record Claim(String schema,String machineId,String requestId,String sessionId,String nonce,String state,
            WindowsJobProcess.ProcessIdentity game,String observedAtUtc) { }
    public static Request readRequest(Path source)throws IOException {
        SharedSourceFiles.plainAncestors(source);
        return readPinned(ControlBuild.FileRef.measure(source),Request.class);
    }
    /** No Game mutation: original evidence plus a fresh named process inventory under the lifecycle mutex. */
    public static ControlBuild.FileRef retire(Request request)throws IOException,InterruptedException {
        Instant deadline=Instant.parse(request.deadlineUtc());Win32Host.deadline(deadline);
        try(var mutex=Win32Host.mutex(JavaGameLifecycle.MUTEX,deadline)) {
            mutex.requireHeld();
            if(!request.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("Failure retirement belongs to another machine");
            validate(request);
            var actual=Win32Host.processInventory(Path.of(request.game().executable()).getFileName().toString(),deadline);
            if(!actual.qualifiedRunning().isEmpty())throw new IOException("A matching Game executable is still running; no retirement");
            return publish(request,actual);
        }
    }
    /** Shared persistence path, also exercised with explicit NoGame inventory DATA by unit tests. */
    static ControlBuild.FileRef publish(Request request,Win32Host.ProcessInventory actual)throws IOException {
        validate(request);
        if(!actual.exactName().equalsIgnoreCase(Path.of(request.game().executable()).getFileName().toString())
                ||!actual.qualifiedRunning().isEmpty())throw new IOException("Exact released Game inventory required");
        Instant observed=Instant.parse(actual.observedAtUtc());
        if(observed.isBefore(Instant.now().minusSeconds(30))||observed.isAfter(Instant.now().plusSeconds(1)))
            throw new IOException("Fresh release inventory required");
        Path destination=retirementPath(control(request),request.requestId());
        SharedSourceFiles.plainAncestors(destination);
        Receipt row=new Receipt("xar.java-game-released-failure-retirement/v1",request,Instant.now().toString(),actual,EFFECT);
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(row);
        if(raw.length>MAXIMUM_BYTES)throw new IOException("Bounded failure retirement required");
        // CREATE_NEW makes ambiguous prior publication a read-only decision, never a replay.
        Files.write(destination,raw,StandardOpenOption.CREATE_NEW);
        JavaGameLifecycle.releaseRetiredRegistry(request.machineId(),request.game(),request.requestId());
        return ControlBuild.FileRef.measure(destination);
    }
    /** Called before reserving a new request, so an unretired old marker cannot be overwritten. */
    static void requireFresh(Path control,String newRequestId)throws IOException {
        token(newRequestId);SharedSourceFiles.plainAncestors(control);
        List<Path> markers=new ArrayList<>();
        Path legacy=control.resolve("unsafe-cleanup.json");
        if(Files.exists(legacy,java.nio.file.LinkOption.NOFOLLOW_LINKS))markers.add(legacy);
        try(var entries=Files.newDirectoryStream(control,"unsafe-cleanup-*.json")) {
            for(Path entry:entries) {if(markers.size()>=4096)throw new IOException("Finite original unsafe marker retention exhausted");markers.add(entry);}
        }
        for(Path marker:markers) {
            var markerPin=ControlBuild.FileRef.measure(marker);Claim old=readPinned(markerPin,Claim.class);
            if(!"xar.java-game-unsafe/v1".equals(old.schema())||!"CREATE_ENTERED".equals(old.state()))
                throw new IOException("Unqualified unsafe launch marker");
            token(old.requestId());
            if(old.requestId().equals(newRequestId))throw new IOException("Original failed launch request cannot be replayed");
            Path retirement=retirementPath(control,old.requestId());
            if(!Files.exists(retirement,java.nio.file.LinkOption.NOFOLLOW_LINKS))throw new IOException("Unretired unsafe launch blocks a new request");
            Receipt receipt=readPinned(ControlBuild.FileRef.measure(retirement),Receipt.class);
            if(!"xar.java-game-released-failure-retirement/v1".equals(receipt.schema())||!EFFECT.equals(receipt.effect())
                    ||!receipt.request().unsafeMarker().equals(markerPin)
                    ||!control(receipt.request()).equals(control.toAbsolutePath().normalize()))throw new IOException("Retirement differs from original unsafe source");
            validate(receipt.request());
            if(!receipt.processInventory().exactName().equalsIgnoreCase(Path.of(receipt.request().game().executable()).getFileName().toString())
                    ||!receipt.processInventory().qualifiedRunning().isEmpty())throw new IOException("Retirement lacks original release inventory");
        }
    }
    private static void validate(Request request)throws IOException {
        Path control=control(request),claim=Path.of(request.claim().path()),marker=Path.of(request.unsafeMarker().path());
        Path expectedClaim=control.resolve("request-"+request.requestId()+".json");
        if(!claim.equals(expectedClaim)||!(marker.equals(control.resolve("unsafe-cleanup.json"))
                ||marker.equals(control.resolve("unsafe-cleanup-"+request.requestId()+".json"))))
            throw new IOException("Original claim/unsafe marker must belong to the same exact control root");
        Claim original=readPinned(request.claim(),Claim.class),unsafe=readPinned(request.unsafeMarker(),Claim.class);
        if(!"xar.java-game-launch-claim/v1".equals(original.schema())||!"UNKNOWN".equals(original.state())
                ||!"xar.java-game-unsafe/v1".equals(unsafe.schema())||!"CREATE_ENTERED".equals(unsafe.state())
                ||!matches(request,original)||!matches(request,unsafe))throw new IOException("Original UNKNOWN/CREATE_ENTERED identity and nonce required");
        var terminal=readPinned(request.terminalEvidence(),LifecycleEvidence.Row.class);
        if(!"xar.java-game-lifecycle-event/v1".equals(terminal.schema())||terminal.event()!=LifecycleEvidence.Event.STOPPED
                ||terminal.terminalKind()!=GameLifecycle.TerminalKind.UNKNOWN||!request.machineId().equals(terminal.machineId())
                ||!request.requestId().equals(terminal.requestId())||!request.sessionId().equals(terminal.sessionId())
                ||!request.game().equals(terminal.game())||terminal.accounting()==null||terminal.accounting().activeProcesses()!=0
                ||terminal.terminal()==null||!request.game().equals(terminal.terminal().identity())
                ||terminal.terminal().accounting().activeProcesses()!=0||!terminal.accounting().equals(terminal.terminal().accounting()))
            throw new IOException("Original failed-launch STOPPED/UNKNOWN terminal and Job zero required");
        Instant.parse(original.observedAtUtc());Instant.parse(unsafe.observedAtUtc());Instant.parse(terminal.observedAtUtc());
    }
    private static boolean matches(Request request,Claim row) {
        return request.machineId().equals(row.machineId())&&request.requestId().equals(row.requestId())
                &&request.sessionId().equals(row.sessionId())&&request.nonce().equals(row.nonce())&&request.game().equals(row.game());
    }
    private static Path control(Request request)throws IOException {
        Path root=Path.of(request.stateDirectory()).toAbsolutePath().normalize().resolve("control");
        SharedSourceFiles.plainAncestors(root);return root;
    }
    private static Path retirementPath(Path control,String id){return control.resolve("retirement-"+id+".json");}
    private static <T> T readPinned(ControlBuild.FileRef expected,Class<T> type)throws IOException {
        Path path=Path.of(expected.path());SharedSourceFiles.plainAncestors(path);
        var held=SharedSourceFiles.observe(path);
        if(!held.source().equals(expected)||expected.bytes()>MAXIMUM_BYTES)throw new IOException("Original retirement input changed or exceeds bound");
        byte[] raw;
        try(var input=Files.newInputStream(path)){raw=input.readNBytes(MAXIMUM_BYTES+1);}
        if(raw.length!=expected.bytes())throw new IOException("Complete bounded retirement input required");
        T value=ControlBuild.strictMapper().readValue(raw,type);SharedSourceFiles.assertUnchanged(held);return value;
    }
    private static void token(String text) {
        if(text==null||!text.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,255}"))throw new IllegalArgumentException("Bounded path-safe lifecycle identity required");
    }
}
