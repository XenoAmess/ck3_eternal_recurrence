package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** The actual specification consumer runs on bounded metadata only. No persistence target is opened. */
class NativeOwnerResumeSessionTest {
    private record Fixture(ObjectNode basis, ClosedInputsSessionAuthority.NativeRestoreInputs inputs,
            WindowsJobProcess.OwnedStdioSpec specification, Instant deadline, Path state) { }

    private static ExactRef ref(Path path) { return new ExactRef(path.toString(),7,"a".repeat(64)); }
    private static ControlBuild.FileRef pin(ExactRef ref) { return new ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256()); }
    private static RecoveryEvidence evidence(ObjectNode basis) {
        byte[] bytes = StrictJson.canonical(basis);
        return new RecoveryEvidence(new ExactRef("D:/synthetic/basis.json",bytes.length,RecoveryEvidence.sha256(bytes)),bytes);
    }
    static ObjectNode basis() throws IOException {
        try (var input = NativeOwnerResumeSessionTest.class.getResourceAsStream("/n46-prior-basis.actual.json")) {
            assertNotNull(input,"preserved bounded Java213 metadata resource required");
            byte[] bytes = input.readNBytes(RecoveryEvidence.MAX_BYTES + 1);
            assertEquals("4b53ffa1a422df36cd18d29f47737fed8417a257ff42d2dc4b7093de56d27afa",RecoveryEvidence.sha256(bytes));
            return (ObjectNode) StrictJson.parse(bytes);
        }
    }
    static ClosedInputsSessionAuthority.NativeRestoreInputs inputs(ObjectNode basis) {
        Path runtime = Path.of("D:/synthetic/new-attempt/runtime");
        return new ClosedInputsSessionAuthority.NativeRestoreInputs(runtime,ref(runtime.resolve("plan.json")),
                ref(runtime.resolve("quote.json")),ref(runtime.resolve("preflight.json")),"b".repeat(32),"c".repeat(32),
                evidence(basis),ref(runtime.resolve("qualification.json")),ref(runtime.resolve("head.json")),
                "synthetic-original-pipe",ref(runtime.resolve("root_p37c23_mcp_entry.py")),Path.of("D:/synthetic/sdk/src"),
                ref(runtime.resolve("sdk-freeze.json")));
    }
    private static Fixture fixture() throws IOException {
        ObjectNode basis = basis(); var inputs = inputs(basis);
        Path state = Path.of(basis.get("refs").get("driver").get("path").textValue()).getParent().getParent();
        Path environment = state.resolve("profile/xar-autoplayer-environment.json");
        List<String> args = List.of(inputs.entrypoint().path(),"--driver","native-headless","--transport","stdio",
                "--pipe-name",inputs.pipeName(),"--state-dir",state.toString(),"--environment-manifest",environment.toString(),
                "--succession-lifecycle","ordinary_campaign_succession","--ordinary-campaign-no-pact","--private-semantic-snapshot-readonly");
        Instant deadline = Instant.now().plusSeconds(120);
        var command = new WindowsJobProcess.CommandSpec(Path.of("D:/synthetic/python.exe"),args,inputs.runtimeRoot(),
                Map.of(),Path.of("D:/synthetic/output/stdio.jsonl"),Path.of("D:/synthetic/output/stderr.txt"),128L << 20);
        var spec = new WindowsJobProcess.OwnedStdioSpec(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,refPin(command.executable()),
                List.of(pin(inputs.entrypoint()),refPin(environment)),deadline.minusSeconds(1),4096,8192,8192,() -> { });
        return new Fixture(basis,inputs,spec,deadline,state);
    }
    private static ControlBuild.FileRef refPin(Path path) { return pin(ref(path)); }
    private static WindowsJobProcess.OwnedStdioSpec spec(Fixture f,List<String> args,List<ControlBuild.FileRef> pins,Instant deadline) {
        var old = f.specification(); var command = old.command();
        var changed = new WindowsJobProcess.CommandSpec(command.executable(),args,command.cwd(),command.environment(),
                command.stdout(),command.stderr(),command.memoryLimitBytes());
        return new WindowsJobProcess.OwnedStdioSpec(changed,old.consoleMode(),old.executableRef(),pins,deadline,
                old.maxFrameBytes(),old.maxSentBytes(),old.maxReceivedBytes(),old.guard());
    }
    private static void validate(Fixture f,WindowsJobProcess.OwnedStdioSpec spec) {
        NativeOwnerResumeSession.validateMcpSpecification(f.inputs(),spec,f.deadline());
    }
    private static void rejects(Fixture f,List<String> args) {
        assertThrows(RuntimeException.class,() -> validate(f,spec(f,args,f.specification().programSourceRefs(),f.specification().deadline())));
    }
    private static void rejectsBasis(Fixture f,ObjectNode changed) {
        assertThrows(RuntimeException.class,() -> NativeOwnerResumeSession.validateMcpSpecification(inputs(changed),f.specification(),f.deadline()));
    }

    @Test void originalSharedStateSurvivesDistinctPreparedRuntimeWithoutStartingAnyOwner() throws Exception {
        Fixture f = fixture(); assertFalse(f.state().equals(f.inputs().runtimeRoot().resolve("state")));
        AtomicBoolean entered = new AtomicBoolean(); var s = f.specification();
        var guarded = new WindowsJobProcess.OwnedStdioSpec(s.command(),s.consoleMode(),s.executableRef(),s.programSourceRefs(),
                s.deadline(),s.maxFrameBytes(),s.maxSentBytes(),s.maxReceivedBytes(),() -> entered.set(true));
        assertDoesNotThrow(() -> validate(f,guarded)); assertFalse(entered.get(),"data validation never starts or grants a process");
        assertEquals("native-40526-1bec95182886",f.basis().get("frame").get("episode_run_id").textValue());
    }
    @Test void newAttemptStateCannotReplaceTheOriginalQualifiedSharedState() throws Exception {
        Fixture f = fixture(); var args = new ArrayList<>(f.specification().command().arguments());
        args.set(args.indexOf("--state-dir") + 1,f.inputs().runtimeRoot().resolve("state").toString()); rejects(f,args);
    }
    @Test void changedPipeDriverTransportAndLifecycleOptionsFailAtActualConsumer() throws Exception {
        Fixture f = fixture();
        for (String flag : List.of("--pipe-name","--driver","--transport","--succession-lifecycle","--environment-manifest")) {
            var args = new ArrayList<>(f.specification().command().arguments()); args.set(args.indexOf(flag) + 1,"wrong"); rejects(f,args);
        }
    }
    @Test void duplicateUnknownMissingAndOrdinaryFlagOptionsCannotRelaxBootstrap() throws Exception {
        Fixture f = fixture(); var base = f.specification().command().arguments();
        for (List<String> extra : List.of(List.of("--pipe-name",f.inputs().pipeName()),List.of("--save-dir",f.state().toString()),
                List.of("--private-semantic-snapshot-readonly"),List.of("--unknown"))) {
            var args = new ArrayList<>(base); args.addAll(extra); rejects(f,args);
        }
        for (String required : List.of("--ordinary-campaign-no-pact","--private-semantic-snapshot-readonly")) {
            var args = new ArrayList<>(base); args.remove(required); rejects(f,args);
        }
    }
    @Test void checkpointPathHashDateAndStrictIntegerHistoryRemainBoundToSavedTuple() throws Exception {
        Fixture f = fixture();
        for (String field : List.of("path","sha256","name","load_save_name")) {
            var changed = f.basis().deepCopy(); ((ObjectNode)changed.get("checkpoint")).put(field,"changed"); rejectsBasis(f,changed);
        }
        var date = f.basis().deepCopy(); ((ObjectNode)date.get("checkpoint")).put("saved_date_raw",1); rejectsBasis(f,date);
        var history = f.basis().deepCopy(); ((ObjectNode)history.get("checkpoint")).put("history_index",true); rejectsBasis(f,history);
        var size = f.basis().deepCopy(); ((ObjectNode)size.get("checkpoint")).put("size",117661285.0); rejectsBasis(f,size);
    }
    @Test void fullLifecycleProfileRejectsNullUnknownBooleanAndInconsistentNoPactClaims() throws Exception {
        Fixture f = fixture();
        var missing = f.basis().deepCopy(); ((ObjectNode)missing.get("checkpoint")).putNull("succession_lifecycle"); rejectsBasis(f,missing);
        for (String field : List.of("lifecycle","source","pact_contract","environment_sha256")) {
            var changed = f.basis().deepCopy(); ((ObjectNode)changed.get("checkpoint").get("succession_lifecycle")).put(field,"unknown"); rejectsBasis(f,changed);
        }
        var changed = f.basis().deepCopy(); ((ObjectNode)changed.get("checkpoint").get("succession_lifecycle")).put("xar_enabled",false); rejectsBasis(f,changed);
    }
    @Test void arbitraryEntryHashAndUnpinnedEnvironmentCannotSelectAnExecutableSource() throws Exception {
        Fixture f = fixture(); var args = new ArrayList<>(f.specification().command().arguments());
        args.set(0,"D:/synthetic/canonical-wrapper.py"); rejects(f,args);
        var pins = new ArrayList<>(f.specification().programSourceRefs());
        pins.set(0,new ControlBuild.FileRef(f.inputs().entrypoint().path(),7,"f".repeat(64)));
        assertThrows(RuntimeException.class,() -> validate(f,spec(f,f.specification().command().arguments(),pins,f.specification().deadline())));
        assertThrows(RuntimeException.class,() -> validate(f,spec(f,f.specification().command().arguments(),List.of(pin(f.inputs().entrypoint())),f.specification().deadline())));
    }
    @Test void programPinsCannotCauseDriverSaveOrAnotherSaveBodyHash() throws Exception {
        Fixture f = fixture();
        for (String target : List.of(f.basis().get("refs").get("driver").get("path").textValue(),
                f.basis().get("refs").get("save").get("path").textValue(),"D:/synthetic/other.CK3","D:/synthetic/other.sav")) {
            var pins = new ArrayList<>(f.specification().programSourceRefs()); pins.add(refPin(Path.of(target)));
            assertThrows(RuntimeException.class,() -> validate(f,spec(f,f.specification().command().arguments(),pins,f.specification().deadline())));
        }
    }
    @Test void expiredOrExtendedDeadlineCannotOutliveOriginalRootScope() throws Exception {
        Fixture f = fixture();
        for (Instant deadline : List.of(Instant.now().minusSeconds(1),f.deadline().plusSeconds(1))) {
            assertThrows(RuntimeException.class,() -> validate(f,spec(f,f.specification().command().arguments(),f.specification().programSourceRefs(),deadline)));
        }
    }
}
