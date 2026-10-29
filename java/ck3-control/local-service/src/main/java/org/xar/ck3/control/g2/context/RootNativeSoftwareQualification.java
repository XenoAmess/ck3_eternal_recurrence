package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedOwnedCommand;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Runs the necessary finite cold software command group; no stored JSON can mint Qualified. */
public final class RootNativeSoftwareQualification {
    public enum StepKind { STRICT_JAVA_COLD, JAVA_COLD_REGRESSION, WHOLE_ORIGINAL_COLD_STEP,
        INDEPENDENT_SDK_CONTINUATION, WHOLE_MCP_SOURCE_STEP }
    public record Step(StepKind kind, ControlBuild.FileRef requestRef, List<String> expectedInvokedTests,
            int expectedInvocations, String junitSummaryRelative) {
        public Step {
            Objects.requireNonNull(kind); Objects.requireNonNull(requestRef);
            expectedInvokedTests=List.copyOf(expectedInvokedTests);
            if(kind==StepKind.STRICT_JAVA_COLD ? expectedInvocations!=0 || !expectedInvokedTests.isEmpty() || junitSummaryRelative!=null
                    : expectedInvocations<1 || expectedInvokedTests.isEmpty())
                throw new IllegalArgumentException("Actual finite test selection and invocation count required");
            if(kind==StepKind.JAVA_COLD_REGRESSION ? junitSummaryRelative==null : junitSummaryRelative!=null)
                throw new IllegalArgumentException("Only actual Java JUnit step has its summary output");
            if(junitSummaryRelative!=null && (Path.of(junitSummaryRelative).isAbsolute()
                    || !Path.of(junitSummaryRelative).normalize().equals(Path.of(junitSummaryRelative))
                    || Path.of(junitSummaryRelative).startsWith(".."))) throw new IllegalArgumentException("Ordinary bounded JUnit output path");
        }
    }
    public record Plan(String machineId, Instant deadline, ControlBuild.FileRef bindingRef,
            List<ControlBuild.FileRef> completeCodeSources, List<ControlBuild.FileRef> completeLoadedFiles,
            List<Step> steps) {
        public Plan {
            StrictJson.text(machineId); Objects.requireNonNull(deadline); Objects.requireNonNull(bindingRef);
            completeCodeSources = List.copyOf(completeCodeSources); completeLoadedFiles = List.copyOf(completeLoadedFiles);
            steps = List.copyOf(steps);
            if (completeCodeSources.isEmpty() || completeLoadedFiles.isEmpty() || completeCodeSources.size() > 4096
                    || completeLoadedFiles.size() > 8192 || steps.size() != StepKind.values().length
                    || !steps.stream().map(Step::kind).collect(java.util.stream.Collectors.toSet()).equals(EnumSet.allOf(StepKind.class)))
                throw new IllegalArgumentException("One complete finite changed cold command group and exact loaded source closure required");
        }
    }
    /** Private production result from actual shared runner outcomes in this same JVM. No public mint. */
    public static final class Qualified {
        private final Plan plan;
        private final List<SharedSourceFiles.Witness> witnesses;
        private final List<ControlBuild.FileRef> terminals;
        private Qualified(Plan plan, List<SharedSourceFiles.Witness> witnesses, List<ControlBuild.FileRef> terminals) {
            this.plan=plan; this.witnesses=List.copyOf(witnesses); this.terminals=List.copyOf(terminals);
        }
        public List<ControlBuild.FileRef> completeCodeSources() { return plan.completeCodeSources(); }
        public List<ControlBuild.FileRef> completeLoadedFiles() { return plan.completeLoadedFiles(); }
        public List<ControlBuild.FileRef> actualTerminals() { return terminals; }
        public void requirePlan(Plan expected) throws IOException {
            if(plan!=expected) throw new IOException("Same actual software producer plan instance required");
            requireCurrent();
        }
        public void requireCurrent() throws IOException {
            current(plan);
            for (var witness : witnesses) SharedSourceFiles.assertUnchanged(witness);
            for (var ref : terminals) ref.verify();
        }
    }
    private RootNativeSoftwareQualification() { }

    /** Caller must already hold actual launcher operation cards/slots for every exact request. */
    public static Qualified run(Plan plan) throws IOException,InterruptedException {
        Objects.requireNonNull(plan); current(plan);
        Map<Path,ControlBuild.FileRef> closure = new LinkedHashMap<>();
        for (var ref : plan.completeCodeSources()) add(closure,ref);
        for (var ref : plan.completeLoadedFiles()) add(closure,ref);
        List<SharedSourceFiles.Witness> witnesses = new ArrayList<>();
        for (var ref : closure.values()) {
            ref.verify(); var witness=SharedSourceFiles.observe(Path.of(ref.path()));
            if (witness.source().bytes()!=ref.bytes() || !witness.source().sha256().equals(ref.sha256()))
                throw new IOException("Qualified software source changed before the full group");
            witnesses.add(witness);
        }
        List<ControlBuild.FileRef> terminals = new ArrayList<>();
        for (StepKind kind : StepKind.values()) {
            current(plan); for (var witness:witnesses) SharedSourceFiles.assertUnchanged(witness);
            Step step=plan.steps().stream().filter(value->value.kind()==kind).findFirst().orElseThrow();
            JsonNode request=read(step.requestRef());
            if (!plan.machineId().equals(text(request,"machine_id"))) throw new IOException("Software step machine differs");
            JsonNode arguments=request.get("arguments");
            if(arguments==null || !arguments.isArray()) throw new IOException("Actual cold command arguments missing");
            List<String> invoked=new ArrayList<>(); for(JsonNode argument:arguments) invoked.add(StrictJson.text(argument));
            for(String expected:step.expectedInvokedTests()) if(!invoked.contains(expected))
                throw new IOException("Actual whole cold test selection differs from the reviewed command group");
            if(kind==StepKind.STRICT_JAVA_COLD) for(var source:plan.completeCodeSources())
                if(source.path().endsWith(".java") && !invoked.contains(source.path()))
                    throw new IOException("Strict compilation omitted a selected changed Java source");
            String executable=Path.of(text(request.path("executable"),"path")).getFileName().toString().toLowerCase(java.util.Locale.ROOT);
            if(kind==StepKind.STRICT_JAVA_COLD ? !executable.equals("javac.exe")
                    : kind==StepKind.JAVA_COLD_REGRESSION ? !executable.equals("java.exe") : !executable.equals("python.exe"))
                throw new IOException("Concrete original Java/Python software producer required, no shell pass command");
            JsonNode inputs=request.get("inputs");
            if (inputs==null || !inputs.isArray()) throw new IOException("Actual command input custody is missing");
            List<ControlBuild.FileRef> inputRefs=new ArrayList<>();
            for (JsonNode input:inputs) inputRefs.add(ref(input));
            // Executed Java sources/classes and independent Python producer modules must belong
            // to the same source-bound command custody, not a sibling old artifact.
            for (var source:plan.completeCodeSources()) if (!inputRefs.contains(source))
                throw new IOException("Whole cold command omits a selected code source: "+source.path());
            if (kind==StepKind.JAVA_COLD_REGRESSION) for (var file:plan.completeLoadedFiles()) if (!inputRefs.contains(file))
                throw new IOException("Cold regression omits an actually loaded deployment input");
            final SharedOwnedCommand.Outcome outcome;
            try { outcome=SharedOwnedCommand.execute(plan.bindingRef(),step.requestRef()); }
            catch (InterruptedException failure) { Thread.currentThread().interrupt(); throw failure; }
            catch (Exception failure) { throw new IOException("Actual cold software step failed before completion: "+kind,failure); }
            terminals.add(outcome.terminalRef());
            if (outcome.status()!=SharedOwnedCommand.Status.PASS) throw new IOException("Actual cold software step RED: "+kind);
            JsonNode actual=read(outcome.terminalRef());
            if (!ref(actual.get("request_ref")).equals(step.requestRef()) || !plan.machineId().equals(text(actual,"machine_id"))
                    || !actual.path("child_started").isBoolean() || !actual.path("child_started").booleanValue()
                    || !"PASS".equals(text(actual,"status")) || !actual.path("failure").isNull())
                throw new IOException("Actual shared command terminal is not the same completed cold operation");
            for(String check:List.of("input_precheck","input_postcheck","runtime_postcheck"))
                if(!"MATCH".equals(text(actual,check))) throw new IOException("Actual cold source/runtime postcheck failed");
            JsonNode child=actual.path("child"); StrictJson.integer(child.get("exit_code"),0,0);
            StrictJson.integer(child.path("accounting").get("active_processes"),0,0);
            if(!child.path("stop_reason").isNull()) throw new IOException("Cold software timeout/cleanup failure is not qualification");
            if(kind==StepKind.STRICT_JAVA_COLD) {
                int outputIndex=invoked.indexOf("-d");
                if(outputIndex<0 || outputIndex+1>=invoked.size()) throw new IOException("Actual javac class output required");
                Path compiled=Path.of(invoked.get(outputIndex+1)).toRealPath();
                int count=0;
                try(var walk=Files.walk(compiled)) {
                    for(Path file:walk.toList()) if(Files.isRegularFile(file) && file.toString().endsWith(".class")) {
                        SharedSourceFiles.plainAncestors(file);
                        if(++count>8192) throw new IOException("Bounded complete selected Java class output required");
                        ControlBuild.FileRef output=ControlBuild.FileRef.measure(file);
                        String relative=compiled.relativize(file).toString().replace('\\','/');
                        boolean same=plan.completeLoadedFiles().stream().anyMatch(selected->selected.path().replace('\\','/').endsWith("/"+relative)
                                && selected.bytes()==output.bytes() && selected.sha256().equals(output.sha256()));
                        if(!same) throw new IOException("Actual strict output differs from the selected live class: "+relative);
                    }
                }
                if(count==0) throw new IOException("Strict javac produced no selected classes");
            } else if(kind==StepKind.JAVA_COLD_REGRESSION) {
                Path summary=Path.of(text(request,"output_root")).resolve(step.junitSummaryRelative());
                JsonNode report=read(ControlBuild.FileRef.measure(summary));
                if(!"xar.standard-junit-summary/v1".equals(text(report,"schema")) || !"PASS".equals(text(report,"status")))
                    throw new IOException("Actual standard JUnit completion required");
                List<String> classes=new ArrayList<>(); for(JsonNode name:report.path("class_names")) classes.add(StrictJson.text(name));
                if(!classes.equals(step.expectedInvokedTests())) throw new IOException("JUnit did not execute the complete selected class list");
                for(String count:List.of("found","started","succeeded")) StrictJson.integer(report.path("tests").get(count),step.expectedInvocations(),step.expectedInvocations());
                for(String group:List.of("tests","containers")) for(String count:List.of("failed","skipped","aborted"))
                    StrictJson.integer(report.path(group).get(count),0,0);
                terminals.add(ControlBuild.FileRef.measure(summary));
            } else if(kind!=StepKind.STRICT_JAVA_COLD) {
                ControlBuild.FileRef stderr=ref(actual.get("stderr_ref"));
                stderr.verify(); String summary=Files.readString(Path.of(stderr.path())); stderr.verify();
                if(!summary.matches("(?s).*\\nRan "+step.expectedInvocations()+" tests? in [^\\n]+\\n\\nOK\\s*")
                        || summary.contains("skipped=")) throw new IOException("Actual entire original Python command group did not pass with zero skips");
                terminals.add(stderr);
            }
            for (var witness:witnesses) SharedSourceFiles.assertUnchanged(witness);
        }
        Qualified actual=new Qualified(plan,witnesses,terminals); actual.requireCurrent(); return actual;
    }
    private static void current(Plan plan) throws IOException {
        if(!plan.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(plan.deadline()))
            throw new IOException("Actual current software qualification machine/lease required");
        plan.bindingRef().verify();
    }
    private static JsonNode read(ControlBuild.FileRef ref) throws IOException {
        ref.verify(); if(ref.bytes()<1 || ref.bytes()>2_097_152) throw new IOException("Bounded exact cold command/terminal required");
        byte[] raw=Files.readAllBytes(Path.of(ref.path())); ref.verify();
        return ControlBuild.strictMapper().readTree(raw);
    }
    private static ControlBuild.FileRef ref(JsonNode value) throws IOException {
        if(value==null) throw new IOException("Exact cold input reference missing");
        return ControlBuild.strictMapper().treeToValue(value,ControlBuild.FileRef.class);
    }
    private static String text(JsonNode value,String field) throws IOException {
        JsonNode node=value.get(field); if(node==null || !node.isTextual() || node.textValue().isBlank())
            throw new IOException("Cold command field rejected: "+field); return node.textValue();
    }
    private static void add(Map<Path,ControlBuild.FileRef> values,ControlBuild.FileRef ref) throws IOException {
        ref.verify(); Path path=Path.of(ref.path()).toRealPath(); ControlBuild.FileRef prior=values.putIfAbsent(path,ref);
        if(prior!=null && !prior.equals(ref)) throw new IOException("Conflicting cold software closure references");
    }
}
