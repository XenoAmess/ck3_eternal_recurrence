package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;

/** Reopens the original supervisor producer and measures current OS state; parsed DATA alone is not a launch permission. */
final class ExitedGameSource {
    private ExitedGameSource() { }
    record Terminal(String machineId,String sessionId,WindowsJobProcess.ProcessIdentity game,int exitCode,
            GameLifecycle.TerminalKind kind,Instant observedAt,ExactRef originalEvidence,ObjectNode actualTerminal) { }
    record Qualified(GameSupervisorControl.Descriptor descriptor,Terminal terminal,ExactRef descriptorReference,
            ExactRef terminalReference,ExactRef currentObservation,Instant observedAt) { }
    record KernelObservation(Win32Host.ProcessObservation originalPid,Win32Host.ProcessInventory gameInventory) { }
    /** Read-only predecessor provenance. This is not an ExitedGeneration submission/STOP capability. */
    record Historical(Qualified source,List<SharedSourceFiles.Witness> originals) {
        Historical {originals=List.copyOf(originals);}
        List<ExactRef> references(){return originals.stream().map(value->LifecycleEvidence.exact(value.source())).toList();}
        void requireOriginals()throws IOException {
            for(var witness:originals)SharedSourceFiles.assertUnchanged(witness);
            var current=readHistorical(source.currentObservation(),source.descriptor().generation());
            require(current.source().equals(source)&&current.originals().equals(originals),"historical exited producer originals changed");
        }
    }
    static Historical readHistorical(ExactRef observation,GameGeneration expected)throws IOException {
        Objects.requireNonNull(observation);Objects.requireNonNull(expected);verify(observation);
        var row=StrictJson.object(StrictJson.parse(GameSupervisorControl.readBounded(Path.of(observation.path()),262144),262144),
                Set.of("schema","machine_id","session_id","observed_at_utc","game","owner_reference","terminal_reference","terminal_evidence","kernel"));
        require("xar.java-exited-game-source-observation/v1".equals(StrictJson.text(row.get("schema")))&&GameGeneration.fromJson(row.get("game")).equals(expected),"original exited observation schema/Game differs");
        ExactRef owner=ExactRef.fromJson(row.get("owner_reference")),terminalRef=ExactRef.fromJson(row.get("terminal_reference"));verify(owner);verify(terminalRef);
        var descriptor=GameSupervisorControl.readDescriptor(Path.of(owner.path()));var terminal=readTerminal(GameSupervisorControl.readBounded(Path.of(terminalRef.path()),262144));
        require(descriptor.generation().equals(expected)&&descriptor.machineId().equals(WindowsJobProcess.currentMachineId())
                &&descriptor.machineId().equals(StrictJson.text(row.get("machine_id")))&&descriptor.sessionId().equals(StrictJson.text(row.get("session_id")))
                &&exact(descriptor.terminalPath()).equals(terminalRef)&&terminal.machineId().equals(descriptor.machineId())
                &&terminal.sessionId().equals(descriptor.sessionId())&&terminal.game().equals(descriptor.gameIdentity())
                &&terminal.originalEvidence().equals(ExactRef.fromJson(row.get("terminal_evidence"))),"original exited owner/terminal/session binding differs");
        verifyLaunch(descriptor);verifyTerminalEvent(descriptor,terminal);
        KernelObservation kernel=ControlBuild.strictMapper().treeToValue(row.get("kernel"),KernelObservation.class);
        requireExitObservation(kernel.originalPid(),descriptor.gameIdentity(),terminal.exitCode());
        require("ck3.exe".equalsIgnoreCase(kernel.gameInventory().exactName())&&kernel.gameInventory().qualifiedRunning().isEmpty(),"original pre-launch exited observation did not prove its empty exact Game inventory");
        Instant observed=Instant.parse(StrictJson.text(row.get("observed_at_utc")));
        require(!observed.isBefore(terminal.observedAt()),"original exited observation predates supervisor terminal");
        var source=new Qualified(descriptor,terminal,owner,terminalRef,observation,observed);
        var refs=List.of(observation,owner,terminalRef,descriptor.nativeHello(),descriptor.launchEvidence(),terminal.originalEvidence());
        var originals=new java.util.ArrayList<SharedSourceFiles.Witness>();
        for(ExactRef ref:refs){verify(ref);var witness=SharedSourceFiles.observe(Path.of(ref.path()));require(LifecycleEvidence.exact(witness.source()).equals(ref),"historical exited original identity changed");originals.add(witness);}
        return new Historical(source,originals);
    }
    /** The known successor may already be alive; only the old exact generation is required absent/exited. */
    static void requireOldGenerationExited(Historical old,Instant deadline)throws IOException {
        Win32Host.deadline(deadline);old.requireOriginals();
        requireExitObservation(Win32Host.inspectProcess(old.source().descriptor().gameIdentity().pid(),0,deadline),old.source().descriptor().gameIdentity(),old.source().terminal().exitCode());
    }
    private static void requireExitObservation(Win32Host.ProcessObservation original,WindowsJobProcess.ProcessIdentity expected,int exitCode)throws IOException {
        require(original.pid()==expected.pid(),"exited observation changed original PID");
        if(original.state()==Win32Host.ProcessState.UNAVAILABLE){
            require(original.failures().size()==1&&original.failures().getFirst().operation()==Win32Host.ProcessOperation.OPEN
                    &&Integer.valueOf(87).equals(original.failures().getFirst().win32Error()),"old Game identity unavailable rather than proved absent");
        }else {
            require(original.times()!=null,"old PID has no proved current birth identity");
            if(expected.creationFiletimeDecimal().equals(original.times().creationFiletimeDecimal())){
            require(original.state()==Win32Host.ProcessState.SIGNALLED&&original.exitCode()!=null&&original.exitCode()==Integer.toUnsignedLong(exitCode),"original Game still runs or its terminal differs");
            if(original.executable()!=null)require(samePath(original.executable(),expected.executable()),"original exited Game image differs");
            }
        }
    }

    /** Real supervisor exit and its original bytes, independent of an already running replacement. */
    record RetainedExit(GameSupervisorControl.Descriptor descriptor, Terminal terminal, ExactRef terminalReference,
            List<SharedSourceFiles.Witness> originals) {
        RetainedExit { originals = List.copyOf(originals); }

        void requireOriginals() throws IOException {
            for (var original : originals) SharedSourceFiles.assertUnchanged(original);
        }

        void requireExited(Instant deadline) throws IOException {
            Win32Host.deadline(deadline);
            requireOriginals();
            var game = descriptor.gameIdentity();
            requireExitObservation(Win32Host.inspectProcess(game.pid(), 0, deadline), game, terminal.exitCode());
        }
    }

    static RetainedExit retainExited(ExactRef owner, GameGeneration expected, Instant deadline) throws IOException {
        Win32Host.deadline(deadline);
        verify(owner);
        var descriptor = GameSupervisorControl.readDescriptor(Path.of(owner.path()));
        var terminalRef = exact(descriptor.terminalPath());
        var terminal = readTerminal(GameSupervisorControl.readBounded(descriptor.terminalPath(), 262144));
        require(descriptor.machineId().equals(WindowsJobProcess.currentMachineId())
                && descriptor.generation().equals(expected) && terminal.machineId().equals(descriptor.machineId())
                && terminal.sessionId().equals(descriptor.sessionId()) && terminal.game().equals(descriptor.gameIdentity()),
                "external save predecessor does not own its exact supervisor terminal");
        verifyLaunch(descriptor);
        verifyTerminalEvent(descriptor, terminal);
        var originals = new java.util.ArrayList<SharedSourceFiles.Witness>();
        for (var reference : List.of(owner, terminalRef, descriptor.nativeHello(), descriptor.launchEvidence(), terminal.originalEvidence())) {
            verify(reference);
            var witness = SharedSourceFiles.observe(Path.of(reference.path()));
            require(LifecycleEvidence.exact(witness.source()).equals(reference), "exited supervisor original changed");
            originals.add(witness);
        }
        var result = new RetainedExit(descriptor, terminal, terminalRef, originals);
        result.requireExited(deadline);
        return result;
    }

    static Qualified qualify(Path descriptorPath,GameGeneration expected,NativeLaunchPlan template,Instant deadline)throws IOException {
        Win32Host.deadline(deadline);Objects.requireNonNull(expected);Objects.requireNonNull(template);
        var descriptor=GameSupervisorControl.readDescriptor(descriptorPath);
        String machine=WindowsJobProcess.currentMachineId();
        require(descriptor.generation().equals(expected)&&descriptor.machineId().equals(machine)
                &&machine.equals(template.sources().review().machineId()),"exited owner crossed the expected full Game birth or actual machine");
        require(descriptor.configuration().review().gameExecutable().equals(template.sources().review().gameExecutable())
                &&samePath(descriptor.gameIdentity().executable(),template.sources().review().gameExecutable().path())
                &&descriptor.configuration().profileDirectory().equals(template.profileDirectory())
                &&descriptor.configuration().stateDirectory().equals(template.stateDirectory()),
                "exited owner differs from the original executable or retained profile/state lineage");
        ExactRef owner=exact(descriptorPath),terminalReference=exact(descriptor.terminalPath());
        var terminal=readTerminal(GameSupervisorControl.readBounded(descriptor.terminalPath(),262144));
        require(terminal.machineId().equals(machine)&&terminal.sessionId().equals(descriptor.sessionId())
                &&terminal.game().equals(descriptor.gameIdentity()),"supervisor terminal crossed its original descriptor Game/session");
        verifyLaunch(descriptor);verifyTerminalEvent(descriptor,terminal);
        var kernel=observeKernel(descriptor.gameIdentity(),terminal.exitCode(),deadline);
        Instant observed=Instant.now();
        Path directory=template.stateDirectory().resolve("control/exited-generations");Files.createDirectories(directory);
        Path target=directory.resolve("observation-"+UUID.randomUUID()+".json");
        var row=StrictJson.object().put("schema","xar.java-exited-game-source-observation/v1")
                .put("machine_id",machine).put("session_id",descriptor.sessionId()).put("observed_at_utc",observed.toString());
        row.set("game",expected.toJson());row.set("owner_reference",owner.toJson());
        row.set("terminal_reference",terminalReference.toJson());row.set("terminal_evidence",terminal.originalEvidence().toJson());
        row.set("kernel",ControlBuild.strictMapper().valueToTree(kernel));
        byte[] raw=StrictJson.canonical(row,262144);Files.write(target,raw,StandardOpenOption.CREATE_NEW);
        return new Qualified(descriptor,terminal,owner,terminalReference,exact(target),observed);
    }
    static void revalidate(Qualified actual,NativeLaunchPlan template,Instant deadline)throws IOException {
        Win32Host.deadline(deadline);revalidateOriginals(actual,template);
        observeKernel(actual.descriptor().gameIdentity(),actual.terminal().exitCode(),deadline);
    }
    /** Historical exit remains a fact after its actual successor starts; this grants no current dispatch. */
    static void revalidateOriginals(Qualified actual,NativeLaunchPlan template)throws IOException {
        verify(actual.descriptorReference());verify(actual.terminalReference());
        verify(actual.currentObservation());verify(actual.terminal().originalEvidence());
        var descriptor=GameSupervisorControl.readDescriptor(Path.of(actual.descriptorReference().path()));
        require(descriptor.equals(actual.descriptor())&&descriptor.machineId().equals(WindowsJobProcess.currentMachineId())
                &&descriptor.machineId().equals(template.sources().review().machineId())
                &&descriptor.configuration().review().gameExecutable().equals(template.sources().review().gameExecutable())
                &&descriptor.configuration().profileDirectory().equals(template.profileDirectory())
                &&descriptor.configuration().stateDirectory().equals(template.stateDirectory()),
                "exited source revalidation changed its original producer or replacement lineage");
        verifyLaunch(descriptor);verifyTerminalEvent(descriptor,actual.terminal());
    }
    static KernelObservation observeKernel(WindowsJobProcess.ProcessIdentity expected,int exitCode,Instant deadline)throws IOException {
        var original=Win32Host.inspectProcess(expected.pid(),0,deadline);
        if(original.state()==Win32Host.ProcessState.UNAVAILABLE) {
            require(original.failures().size()==1&&original.failures().getFirst().operation()==Win32Host.ProcessOperation.OPEN
                    &&Integer.valueOf(87).equals(original.failures().getFirst().win32Error()),
                    "old Game process identity is unavailable rather than proved absent");
        } else if(original.times()!=null&&expected.creationFiletimeDecimal().equals(original.times().creationFiletimeDecimal())) {
            require(original.state()==Win32Host.ProcessState.SIGNALLED&&original.exitCode()!=null
                    &&original.exitCode()==Integer.toUnsignedLong(exitCode),"original Game is running or disagrees with the supervisor exit");
            if(original.executable()!=null)require(samePath(original.executable(),expected.executable()),"original exited Game image changed");
        }
        var inventory=Win32Host.processInventory(Path.of(expected.executable()).getFileName().toString(),deadline);
        require(inventory.qualifiedRunning().isEmpty(),"another current Game blocks exited-generation replacement");
        return new KernelObservation(original,inventory);
    }
    /** Exact consumer of GameSupervisor.encodeTerminal. This creates DATA only. */
    static Terminal readTerminal(byte[] raw)throws IOException {
        try {
            var row=StrictJson.object(StrictJson.parse(raw,262144),Set.of("schema","machine_id","session_id","observed_at_utc",
                    "status","stop_request_id","cleanup_proven","terminal_kind","game","actual_terminal","evidence"));
            require("xar.java-game-supervisor-result/v1".equals(StrictJson.text(row.get("schema")))
                    &&row.get("cleanup_proven").isBoolean()&&row.get("cleanup_proven").booleanValue(),
                    "completed original supervisor cleanup required");
            var kind=GameLifecycle.TerminalKind.valueOf(StrictJson.text(row.get("terminal_kind")));
            require(kind!=GameLifecycle.TerminalKind.UNKNOWN&&StrictJson.text(row.get("status")).equals(
                    kind==GameLifecycle.TerminalKind.NATURAL_EXIT?"GAME_EXITED":"OWNER_STOP_COMPLETED"),
                    "supervisor terminal status/kind is unresolved");
            require(row.get("stop_request_id").isTextual(),"explicit original stop request field required");
            if(kind==GameLifecycle.TerminalKind.NATURAL_EXIT)require(row.get("stop_request_id").textValue().isEmpty(),
                    "natural exit cannot claim an owner STOP request");
            var game=identity(row.get("game"),"creation_filetime");
            var terminal=StrictJson.object(row.get("actual_terminal"),Set.of("identity","exit_code","elapsed_seconds_decimal","accounting","stop_reason"));
            require(game.equals(identity(terminal.get("identity"),"creation_filetime_decimal")),"supervisor terminal changed its actual held process identity");
            int exit=(int)StrictJson.integer(terminal.get("exit_code"),Integer.MIN_VALUE,Integer.MAX_VALUE);
            String elapsed=StrictJson.text(terminal.get("elapsed_seconds_decimal"));
            require(new BigDecimal(elapsed).signum()>=0,"nonnegative original elapsed seconds required");
            accounting(terminal.get("accounting"));
            require(terminal.get("stop_reason").isNull()||terminal.get("stop_reason").isTextual(),"original terminal stop reason must be explicit");
            return new Terminal(StrictJson.text(row.get("machine_id")),StrictJson.text(row.get("session_id")),game,exit,kind,
                    Instant.parse(StrictJson.text(row.get("observed_at_utc"))),ExactRef.fromJson(row.get("evidence")),terminal);
        }catch(IllegalArgumentException|java.time.DateTimeException invalid) {
            throw new IOException("invalid original exited supervisor terminal",invalid);
        }
    }
    private static void verifyLaunch(GameSupervisorControl.Descriptor descriptor)throws IOException {
        verify(descriptor.launchEvidence());verify(descriptor.nativeHello());
        var launch=event(descriptor.launchEvidence());
        require("HELLO".equals(StrictJson.text(launch.get("event"))),"original supervisor launch needs its actual HELLO event");
        subject(descriptor,launch);
    }
    private static void verifyTerminalEvent(GameSupervisorControl.Descriptor descriptor,Terminal terminal)throws IOException {
        verify(terminal.originalEvidence());var event=event(terminal.originalEvidence());subject(descriptor,event);
        require("STOPPED".equals(StrictJson.text(event.get("event")))
                &&terminal.kind().name().equals(StrictJson.text(event.get("terminal_kind"))),"supervisor did not retain its actual cleanup event");
        var actual=StrictJson.object(event.get("terminal"),Set.of("identity","exit_code","elapsed_seconds","accounting","stop_reason"));
        require(identity(actual.get("identity"),"creation_filetime_decimal").equals(terminal.game())
                &&StrictJson.integer(actual.get("exit_code"),Integer.MIN_VALUE,Integer.MAX_VALUE)==terminal.exitCode()
                &&actual.get("accounting").equals(terminal.actualTerminal().get("accounting"))
                &&actual.get("stop_reason").equals(terminal.actualTerminal().get("stop_reason")),
                "supervisor result changed its actual source terminal, accounting or failure");
        require(actual.get("elapsed_seconds").isNumber()
                &&new BigDecimal(StrictJson.text(terminal.actualTerminal().get("elapsed_seconds_decimal")))
                    .compareTo(actual.get("elapsed_seconds").decimalValue())==0,"supervisor elapsed seconds differ from the original native terminal");
        accounting(actual.get("accounting"));
    }
    private static ObjectNode event(ExactRef reference)throws IOException {
        var row=StrictJson.object(StrictJson.parse(GameSupervisorControl.readBounded(Path.of(reference.path()),65536)),
                Set.of("schema","machine_id","observed_at_utc","request_id","session_id","event","game","accounting","terminal","terminal_kind","detail"));
        require("xar.java-game-lifecycle-event/v1".equals(StrictJson.text(row.get("schema"))),"original Java lifecycle event schema required");
        return row;
    }
    private static void subject(GameSupervisorControl.Descriptor descriptor,ObjectNode event)throws IOException {
        require(descriptor.machineId().equals(StrictJson.text(event.get("machine_id")))
                &&descriptor.sessionId().equals(StrictJson.text(event.get("session_id")))
                &&descriptor.configuration().requestId().equals(StrictJson.text(event.get("request_id")))
                &&descriptor.gameIdentity().equals(identity(event.get("game"),"creation_filetime_decimal")),
                "original lifecycle event crossed its supervisor source/session/Game");
    }
    private static WindowsJobProcess.ProcessIdentity identity(JsonNode value,String creationField) {
        var row=StrictJson.object(value,Set.of("pid",creationField,"executable"));
        return new WindowsJobProcess.ProcessIdentity(StrictJson.integer(row.get("pid"),1,4294967295L),
                GameGeneration.parseCreationFiletime(row.get(creationField)).value().toString(),StrictJson.text(row.get("executable")));
    }
    private static void accounting(JsonNode value)throws IOException {
        var row=StrictJson.object(value,Set.of("active_processes","limit_flags","memory_limit_bytes","peak_job_memory_bytes"));
        require(StrictJson.integer(row.get("active_processes"),0,Integer.MAX_VALUE)==0,"original Job still has active processes");
        StrictJson.integer(row.get("limit_flags"),0,Integer.MAX_VALUE);
        StrictJson.integer(row.get("memory_limit_bytes"),0,Long.MAX_VALUE);
        StrictJson.integer(row.get("peak_job_memory_bytes"),0,Long.MAX_VALUE);
    }
    private static boolean samePath(String first,String second) {
        return Path.of(first).toAbsolutePath().normalize().equals(Path.of(second).toAbsolutePath().normalize());
    }
    private static ExactRef exact(Path value)throws IOException {return LifecycleEvidence.exact(ControlBuild.FileRef.measure(value));}
    private static void verify(ExactRef ref)throws IOException {new ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()).verify();}
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
