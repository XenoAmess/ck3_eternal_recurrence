package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** The complete original workflow group, each real Python process owned by the shared native Job producer. */
public final class CanonicalColdWarmStage {
    private CanonicalColdWarmStage() { }
    public static final String SCHEMA = "xar.canonical-cold-warm-stage/v3";
    private static final long MIB = 1L << 20;
    private static final String STEP = "Check strict cold and owner types and boundary contracts";
    private static final String CHECK = "if not \"%errorlevel%\"==\"0\" exit /b %errorlevel%";
    public enum BootstrapMode { NONE, ROOT_SOFTWARE_FIXTURE }
    public enum CommandState { NOT_RUN, STARTED_WITHOUT_TERMINAL, RED, PASS }
    public record Config(String schema, String machineId, String reviewAtUtc, String repository, String workRoot,
            ControlBuild.FileRef pythonExecutable, ControlBuild.FileRef gitExecutable, ControlBuild.FileRef workflowRef, ControlBuild.FileRef reviewedWalRef,
            List<ControlBuild.FileRef> canonicalSources, List<String> dependencyRoots, List<ControlBuild.FileRef> dependencySources,
            ControlBuild.FileRef executionCardRef, BootstrapMode bootstrapMode, ControlBuild.FileRef rootBootstrapRef,
            long commandMemoryBytes, int timeoutSeconds) {
        public Config {
            canonicalSources = List.copyOf(canonicalSources); dependencyRoots = List.copyOf(dependencyRoots); dependencySources = List.copyOf(dependencySources);
            Path repo = absolute(repository), work = absolute(workRoot); Instant.parse(reviewAtUtc);
            if (!SCHEMA.equals(schema) || machineId == null || machineId.isBlank() || work.startsWith(repo) || repo.startsWith(work)
                    || commandMemoryBytes < 64 * MIB || commandMemoryBytes > 1536 * MIB || timeoutSeconds < 1 || timeoutSeconds > 2100
                    || canonicalSources.isEmpty() || canonicalSources.size() > 20000 || dependencyRoots.isEmpty() || dependencySources.isEmpty()
                    || gitExecutable == null || !Path.of(gitExecutable.path()).getFileName().toString().equalsIgnoreCase("git.exe")
                    || bootstrapMode == null || (bootstrapMode == BootstrapMode.NONE) != (rootBootstrapRef == null)) throw new IllegalArgumentException("Finite explicit original group and bootstrap scope required");
            for (String root : dependencyRoots) absolute(root);
            for (var refs : List.of(canonicalSources, dependencySources)) if (refs.stream().map(ControlBuild.FileRef::path).distinct().count() != refs.size()) throw new IllegalArgumentException("Unique explicit source pins required");
        }
    }
    public record ParsedStep(String name, String originalRun, Map<String, String> declaredEnvironment, List<String> commandLines, int pythonCommands) {
        public ParsedStep { declaredEnvironment = Map.copyOf(declaredEnvironment); commandLines = List.copyOf(commandLines); }
    }
    public record Sources(String schema, List<ControlBuild.FileRef> files) { public Sources { files = List.copyOf(files); } }
    public record Summary(int groups, int tests, int skipped, int expectedFailures, int unexpectedSuccesses, int failures, int errors, int emptyGroups) {
        public Summary {
            for (int value : new int[] {groups, tests, skipped, expectedFailures, unexpectedSuccesses, failures, errors, emptyGroups}) if (value < 0) throw new IllegalArgumentException("Nonnegative actual counts required");
            if (emptyGroups > groups) throw new IllegalArgumentException("Empty groups exceed observed groups");
        }
        public boolean accepted() { return skipped == 0 && expectedFailures == 0 && unexpectedSuccesses == 0 && failures == 0 && errors == 0 && emptyGroups == 0; }
    }
    public record PythonInput(String schema, BootstrapMode bootstrapMode, ControlBuild.FileRef bootstrapRef,
            CanonicalPythonInvocation.Invocation invocation, String observationPath) { }
    public record Observation(String schema, BootstrapMode bootstrapMode, RootSoftwareChildBootstrap.ChildEvidence bootstrapEvidence,
            int exitCode, String error) { }
    public record CommandActual(int index, CanonicalPythonInvocation.Invocation invocation, CommandState state,
            List<String> arguments, WindowsJobProcess.CommandResult result, ControlBuild.FileRef inputRef,
            ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef, ControlBuild.FileRef observationRef,
            Observation observation, Summary summary, String error) {
        public CommandActual {
            arguments = List.copyOf(arguments);
            if (index < 1 || index > 30 || invocation == null || state == null) throw new IllegalArgumentException("Exact indexed command outcome required");
            if (state == CommandState.NOT_RUN && (result != null || inputRef != null || stdoutRef != null || stderrRef != null || observationRef != null || observation != null || summary != null || !arguments.isEmpty())) throw new IllegalArgumentException("NOT_RUN cannot claim command evidence");
            if (state == CommandState.PASS) {
                if (result == null || !result.passed() || inputRef == null || stdoutRef == null || stderrRef == null || observationRef == null || observation == null || observation.exitCode() != 0 || observation.error() != null || summary == null || !summary.accepted() || error != null) throw new IllegalArgumentException("PASS needs actual clean terminal and outcomes");
                if (requiresTestSummary(invocation) && (summary.groups() == 0 || summary.tests() == 0)) throw new IllegalArgumentException("Proven test invocation requires non-empty summary");
            }
        }
    }

    static boolean requiresTestSummary(CanonicalPythonInvocation.Invocation invocation) {
        if (invocation == null) return false;
        switch (invocation.mode()) {
            case MODULE:
                return invocation.moduleName().equals("unittest");
            case INLINE_SOURCE:
                return invocation.inlineSource().contains("TextTestRunner");
            case SCRIPT_FILE:
                String script = invocation.relativeScript();
                return script.equals("tools/g2_saved_campaign/candidates/native32_passive_journal_diagnostics_20261021/cold/test_observer_journal_v1.py")
                    || script.equals("tools/g2_saved_campaign/candidates/native32_runtime_journal_adapter_20261021/test_native32_runtime_journal_adapter_v1.py")
                    || script.equals("tools/g2_saved_campaign/candidates/native32_production_builder_20261021/test_recipe_v1.py")
                    || script.equals("ck3_autonomous_player/tests/unit/test_cold_checkpoint_type_contract.py")
                    || script.equals("ck3_autonomous_player/tests/unit/test_driver_resume_type_contract.py")
                    || script.equals("tools/g2_saved_campaign/test_owner_prepare_contract_v1.py")
                    || script.equals("ck3_autonomous_player/tests/unit/test_driver_state_wal_diagnostics.py")
                    || script.equals("tools/g2_saved_campaign/candidates/native32_entry_registration_20261021/test_native32_entry_registration_v1.py")
                    || script.equals("tools/g2_saved_campaign/test_source31_a19_cold_union_v1.py")
                    || script.equals("tools/g2_saved_campaign/test_source31_a20_cold_union_v1.py")
                    || script.equals("tools/g2_saved_campaign/test_saved_campaign_visual_text_preflight_v1.py");
            default:
                return false;
        }
    }
    public record Actual(String schema, String machineId, String startedAtUtc, String observedAtUtc,
            SupplementalFixtureCi.Status status, String error, ControlBuild.FileRef configRef,
            ControlBuild.FileRef workflowRef, ControlBuild.FileRef reviewedWalRef, List<ControlBuild.FileRef> producerClosure,
            WindowsJobProcess.ConsoleMode consoleMode, List<CommandActual> commands, ControlBuild.FileRef sourceBeforeRef,
            ControlBuild.FileRef sourceAfterRef, ControlBuild.SourceState sourcePostcheck, BootstrapMode bootstrapMode,
            boolean freshSdkImportQualification) {
        public Actual {
            producerClosure = List.copyOf(producerClosure); commands = List.copyOf(commands);
            if (freshSdkImportQualification) throw new IllegalArgumentException("Canonical group does not qualify a fresh SDK import graph");
        }
    }
    static ParsedStep parseStep(String workflow) throws IOException {
        String header = "      - name: " + STEP; List<String> all = workflow.lines().toList(); int start = all.indexOf(header);
        if (start < 0 || all.lastIndexOf(header) != start) throw new IOException("Unique original canonical workflow group required");
        Map<String, String> environment = new TreeMap<>(); List<String> run = new ArrayList<>(); boolean env = false, body = false;
        for (int index = start + 1; index < all.size(); index++) {
            String line = all.get(index); if (line.startsWith("      - ")) break;
            if (line.equals("        env:")) { if (body) throw new IOException("Unexpected workflow ordering"); env = true; continue; }
            if (line.equals("        run: |")) { env = false; body = true; continue; }
            if (line.isBlank()) continue;
            if (env) {
                if (!line.startsWith("          ")) throw new IOException("Unsupported canonical environment shape");
                String value = line.substring(10); int colon = value.indexOf(": "); if (colon < 1) throw new IOException("Explicit scalar environment required");
                String key = value.substring(0, colon), text = value.substring(colon + 2);
                if (!key.matches("[A-Z][A-Z0-9_]*")) throw new IOException("Explicit environment key required");
                if (text.startsWith("\"") && text.endsWith("\"")) text = text.substring(1, text.length() - 1);
                if (environment.putIfAbsent(key, text) != null) throw new IOException("Duplicate canonical environment key");
            } else if (body) { if (!line.startsWith("          ")) throw new IOException("Unsupported canonical command indentation"); run.add(line.substring(10)); }
            else throw new IOException("Unexpected canonical workflow property");
        }
        if (run.size() != 60) throw new IOException("Complete original30 commands and30 original exit checks required");
        for (int index = 0; index < run.size(); index += 2) if (!run.get(index).startsWith("python ") || !run.get(index + 1).equals(CHECK)) throw new IOException("Canonical command/check sequence differs");
        if (run.stream().filter(line -> line.contains("CurrentSavedSdkPersistenceTests.test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations")).count() != 1) throw new IOException("Independent original SDK continuation command required");
        return new ParsedStep(STEP, String.join("\n", run) + "\n", environment, run, 30);
    }
    private static final String PRELUDE = """
        import builtins,json,os,pathlib,runpy,sys,traceback,types,importlib.machinery
        def _canonical_pairs(pairs):
            value={}
            for key,item in pairs:
                if key in value: raise ValueError('duplicate canonical input field')
                value[key]=item
            return value
        with open(sys.argv[1],encoding='utf-8') as stream: request=json.load(stream,object_pairs_hook=_canonical_pairs)
        if type(request) is not dict or set(request)!={'schema','bootstrap_mode','bootstrap_ref','invocation','observation_path'} or request['schema']!='xar.canonical-python-input/v1': raise ValueError('exact canonical input required')
        root_bootstrap_ref=request['bootstrap_ref']
        _xar_root_stack=None
        _xar_root_bootstrap_evidence=None
        _canonical_code=1
        _canonical_error=None
        """;
    private static final String BODY = """
        invocation=request['invocation']
        try:
            if type(invocation) is not dict or set(invocation)!={'original_command','interpreter_arguments','mode','module_name','inline_source','relative_script','arguments'}: raise ValueError('exact original invocation fields required')
            args=invocation['arguments']
            if type(args) is not list or any(type(value) is not str for value in args): raise ValueError('exact original string arguments required')
            mode=invocation['mode']
            if mode=='MODULE':
                sys.argv=[invocation['module_name'],*args]
                sys.path[0]=os.getcwd()
                runpy.run_module(invocation['module_name'],run_name='__main__',alter_sys=True)
            else:
                main=types.ModuleType('__main__'); main.__dict__['__builtins__']=builtins
                main.__package__=None; main.__spec__=None; main.__cached__=None
                sys.modules['__main__']=main
                if mode=='INLINE_SOURCE':
                    sys.argv=['-c',*args]; sys.path[0]=''
                    exec(compile(invocation['inline_source'],'<string>','exec'),main.__dict__)
                elif mode=='SCRIPT_FILE':
                    path=pathlib.Path(invocation['relative_script']).resolve(strict=True)
                    sys.argv=[invocation['relative_script'],*args]; sys.path[0]=str(path.parent)
                    main.__file__=str(path); main.__loader__=importlib.machinery.SourceFileLoader('__main__',str(path))
                    with path.open('rb') as source: body=source.read()
                    exec(compile(body,str(path),'exec'),main.__dict__)
                else: raise ValueError('unknown original invocation mode')
            _canonical_code=0
        except SystemExit as outcome:
            _canonical_code=0 if outcome.code is None else int(outcome.code) if isinstance(outcome.code,int) else 1
            if outcome.code is not None and not isinstance(outcome.code,int): print(outcome.code,file=sys.stderr)
        except BaseException as failure:
            _canonical_error=type(failure).__name__+': '+str(failure); traceback.print_exc()
        finally:
            if _xar_root_stack is not None:
                try: _xar_root_stack.close()
                except BaseException as failure:
                    _canonical_error=(_canonical_error+'; ' if _canonical_error else '')+'bootstrap cleanup: '+type(failure).__name__+': '+str(failure); _canonical_code=1; traceback.print_exc()
            observed={'schema':'xar.canonical-python-observation/v1','bootstrap_mode':request['bootstrap_mode'],'bootstrap_evidence':_xar_root_bootstrap_evidence,'exit_code':_canonical_code,'error':_canonical_error}
            try:
                raw=json.dumps(observed,separators=(',',':'),ensure_ascii=False).encode('utf-8')
                if len(raw)>1048576: raise ValueError('bounded canonical observation required')
                with open(request['observation_path'],'xb') as stream: stream.write(raw)
            except BaseException:
                traceback.print_exc(); print(json.dumps(observed,separators=(',',':')),file=sys.stderr); _canonical_code=1
        raise SystemExit(_canonical_code)
        """;
    static String observer(BootstrapMode mode) { return PRELUDE + (mode == BootstrapMode.ROOT_SOFTWARE_FIXTURE ? RootSoftwareChildBootstrap.pythonPrefix() : "") + BODY; }
    static List<String> arguments(CanonicalPythonInvocation.Invocation invocation, BootstrapMode mode, Path input) {
        List<String> result = new ArrayList<>(invocation.interpreterArguments()); result.addAll(List.of("-c", observer(mode), input.toString())); return List.copyOf(result);
    }
    static CommandActual execute(int index, CanonicalPythonInvocation.Invocation invocation, BootstrapMode mode,
            ControlBuild.FileRef bootstrapRef, ControlBuild.FileRef python, Path cwd, Path root, Map<String, String> environment,
            long memory, Duration timeout, Instant deadline, FreshSdkFixtureStage.ResourceGuard guard) throws IOException, InterruptedException {
        Files.createDirectory(root); Path input = root.resolve("input.json"), out = root.resolve("stdout.log"), err = root.resolve("stderr.log"), observed = root.resolve("observation.json");
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(new PythonInput("xar.canonical-python-input/v1", mode, bootstrapRef, invocation, observed.toString()));
        guard.revalidate(raw.length); Files.write(input, raw, StandardOpenOption.CREATE_NEW); ControlBuild.FileRef inputRef = ControlBuild.FileRef.measure(input);
        List<String> argv = arguments(invocation, mode, input); WindowsJobProcess.CommandResult terminal = null; String error = null;
        Observation observation = null; Summary summary = null; ControlBuild.FileRef outRef = null, errRef = null, observationRef = null;
        try {
            python.verify(); inputRef.verify(); guard.revalidate(0);
            try (var child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(python.path()), argv, cwd, environment, out, err, memory), WindowsJobProcess.ConsoleMode.DETACHED)) {
                terminal = child.await(timeout, deadline, () -> { try { guard.revalidate(0); } catch (IOException unavailable) { throw new IllegalStateException(unavailable); } });
            }
        } catch (InterruptedException interrupted) { error = "Native wait interrupted without an observed terminal"; Thread.currentThread().interrupt(); }
        catch (IOException | RuntimeException failure) { error = failure.getClass().getSimpleName() + ": " + failure.getMessage(); }
        finally {
            if (terminal == null) error = append(error, "No observed native command terminal");
            try {
                outRef = maybe(out); errRef = maybe(err); observationRef = maybe(observed);
                if (outRef == null || errRef == null || observationRef == null) throw new IOException("Actual independent command evidence incomplete");
            } catch (IOException | RuntimeException failure) { error = append(error, "Actual native terminal retained; evidence references: " + failure.getMessage()); }
            try { observation = read(observed, Observation.class); requireObservation(mode, bootstrapRef, observation); }
            catch (IOException | RuntimeException failure) { error = append(error, "Body/bootstrap observation: " + failure.getMessage()); }
            try {
                summary = summary(text(out) + "\n" + text(err));
                if (requiresTestSummary(invocation) && (summary.groups() == 0 || summary.tests() == 0)) throw new IOException("Actual test summary missing for proven test invocation");
                if (!summary.accepted()) throw new IOException("Original command skipped/expected-failed/unexpected-success/failed/empty");
            } catch (IOException | RuntimeException failure) { error = append(error, "Original test summary: " + failure.getMessage()); }
            try { inputRef.verify(); python.verify(); }
            catch (IOException | RuntimeException failure) { error = append(error, "Input/interpreter custody: " + failure.getMessage()); }
            if (terminal != null && (!terminal.passed() || observation != null && terminal.exitCode() != observation.exitCode())) error = append(error, "Actual native command exit/stop differs or failed");
        }
        return new CommandActual(index, invocation, terminal == null ? CommandState.STARTED_WITHOUT_TERMINAL : error == null ? CommandState.PASS : CommandState.RED,
                argv, terminal, inputRef, outRef, errRef, observationRef, observation, summary, error);
    }
    private static void requireObservation(BootstrapMode mode, ControlBuild.FileRef bootstrapRef, Observation observed) throws IOException {
        if (!"xar.canonical-python-observation/v1".equals(observed.schema()) || observed.bootstrapMode() != mode || observed.error() != null || observed.exitCode() != 0) throw new IOException("Successful exact original body observation required");
        if (mode == BootstrapMode.NONE) { if (observed.bootstrapEvidence() != null || bootstrapRef != null) throw new IOException("NONE cannot claim fixture bootstrap evidence"); }
        else {
            RootSoftwareChildBootstrap.requireEvidence(RootSoftwareChildBootstrap.readConfiguration(bootstrapRef), observed.bootstrapEvidence());
            if (!bootstrapRef.equals(observed.bootstrapEvidence().bootstrapRef())) throw new IOException("Exact requested child bootstrap ref required");
            // The observed executing Python may differ from the native venv redirector. Both identities remain distinct; no ancestry is invented.
        }
    }
    public static ControlBuild.FileRef run(Config config, FreshSdkFixtureStage.ResourceGuard resources) throws IOException, InterruptedException {
        String started = Instant.now().toString(); check(config, resources); verifyInputs(config);
        if (Duration.between(Instant.now(), Instant.parse(config.reviewAtUtc())).getSeconds() < config.timeoutSeconds() + 900L) throw new IOException("Lease must contain full group timeout and original fixture reviews");
        ParsedStep step = parseStep(Files.readString(Path.of(config.workflowRef().path()), StandardCharsets.UTF_8)); Path work = absolute(config.workRoot()); SharedSourceFiles.plainAncestors(work);
        if (Files.exists(work, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Canonical root must be create-only"); Files.createDirectories(work); Path scratch = Files.createDirectory(work.resolve("scratch"));
        List<CommandActual> commands = new ArrayList<>();
        for (int index = 0; index < 30; index++) commands.add(new CommandActual(index + 1, CanonicalPythonInvocation.parse(step.commandLines().get(index * 2), scratch), CommandState.NOT_RUN, List.of(), null, null, null, null, null, null, null, null));
        Path configPath = work.resolve("config.json"), beforePath = work.resolve("sources-before.json"), afterPath = work.resolve("sources-after.json");
        write(configPath, config, config, resources); Sources before = inventory(config); write(beforePath, before, config, resources);
        ControlBuild.FileRef configRef = ControlBuild.FileRef.measure(configPath), beforeRef = ControlBuild.FileRef.measure(beforePath), afterRef = null;
        List<ControlBuild.FileRef> closure = ControlBuild.producerClosure(); String error = null; ControlBuild.SourceState postcheck = ControlBuild.SourceState.UNKNOWN;
        long groupStart = System.nanoTime(), limit = Duration.ofSeconds(config.timeoutSeconds()).toNanos();
        try {
            for (int index = 0; index < 30; index++) {
                verifyInputs(config); for (var ref : closure) ref.verify(); check(config, resources);
                long remaining = limit - (System.nanoTime() - groupStart); if (remaining <= 0) throw new IOException("Original complete group timeout consumed before next command");
                CommandActual command = execute(index + 1, commands.get(index).invocation(), config.bootstrapMode(), config.rootBootstrapRef(), config.pythonExecutable(), absolute(config.repository()),
                        work.resolve(String.format(java.util.Locale.ROOT, "command-%02d", index + 1)), environment(config, step, scratch), config.commandMemoryBytes(),
                        Duration.ofNanos(remaining), Instant.parse(config.reviewAtUtc()), pending -> { check(config, resources); resources.revalidate(pending); });
                commands.set(index, command); if (command.state() != CommandState.PASS) throw new IOException("Actual original command failed: " + (index + 1) + ": " + command.error());
            }
            requireAbsent(scratch.resolve("pycache-no-read"));
        } catch (IOException | RuntimeException failure) { error = failure.getClass().getSimpleName() + ": " + failure.getMessage(); }
        finally {
            if (error == null && commands.stream().anyMatch(command -> command.state() != CommandState.PASS)) error = "Original group interrupted or incomplete";
            try {
                Sources after = inventory(config); write(afterPath, after, config, resources); afterRef = ControlBuild.FileRef.measure(afterPath);
                postcheck = before.equals(after) ? ControlBuild.SourceState.MATCH : ControlBuild.SourceState.MISMATCH;
                if (postcheck != ControlBuild.SourceState.MATCH) error = append(error, "Declared original source inventory changed");
                verifyInputs(config); for (var ref : closure) ref.verify();
            } catch (IOException | RuntimeException failure) { error = append(error, "Source recheck: " + failure.getMessage()); }
            writeActual(work.resolve("actual.json"), new Actual(SCHEMA, config.machineId(), started, Instant.now().toString(), error == null ? SupplementalFixtureCi.Status.PASS : SupplementalFixtureCi.Status.RED,
                    error, configRef, config.workflowRef(), config.reviewedWalRef(), closure, WindowsJobProcess.ConsoleMode.DETACHED, commands, beforeRef, afterRef, postcheck, config.bootstrapMode(), false), config, resources);
        }
        if (error != null) throw new IOException(error); return requireAccepted(work.resolve("actual.json"), resources);
    }
    public static ControlBuild.FileRef requireAccepted(Path path, FreshSdkFixtureStage.ResourceGuard resources) throws IOException {
        Actual actual = read(path, Actual.class); Config config = read(Path.of(actual.configRef().path()), Config.class); check(config, resources); verifyInputs(config);
        Path work = absolute(config.workRoot()); ParsedStep step = parseStep(Files.readString(Path.of(config.workflowRef().path()), StandardCharsets.UTF_8));
        if (!path.toRealPath().equals(work.resolve("actual.json").toRealPath()) || !actual.schema().equals(SCHEMA) || actual.status() != SupplementalFixtureCi.Status.PASS || actual.error() != null
                || !actual.machineId().equals(config.machineId()) || !actual.workflowRef().equals(config.workflowRef()) || !actual.reviewedWalRef().equals(config.reviewedWalRef())
                || !actual.producerClosure().equals(ControlBuild.producerClosure()) || actual.consoleMode() != WindowsJobProcess.ConsoleMode.DETACHED || actual.commands().size() != 30
                || actual.sourcePostcheck() != ControlBuild.SourceState.MATCH || actual.bootstrapMode() != config.bootstrapMode() || actual.freshSdkImportQualification()) throw new IOException("Complete exact original canonical30 actual required");
        for (var ref : List.of(actual.configRef(), actual.sourceBeforeRef(), actual.sourceAfterRef())) ref.verify(); for (var ref : actual.producerClosure()) ref.verify();
        if (!Path.of(actual.configRef().path()).toRealPath().equals(work.resolve("config.json").toRealPath()) || !Path.of(actual.sourceBeforeRef().path()).toRealPath().equals(work.resolve("sources-before.json").toRealPath())
                || !Path.of(actual.sourceAfterRef().path()).toRealPath().equals(work.resolve("sources-after.json").toRealPath())) throw new IOException("Owned exact canonical source/config paths required");
        Sources before = read(Path.of(actual.sourceBeforeRef().path()), Sources.class), after = read(Path.of(actual.sourceAfterRef().path()), Sources.class);
        if (!before.equals(after) || !before.equals(inventory(config))) throw new IOException("Canonical declared source custody changed");
        for (int index = 0; index < 30; index++) {
            CommandActual command = actual.commands().get(index); Path root = work.resolve(String.format(java.util.Locale.ROOT, "command-%02d", index + 1));
            var invocation = CanonicalPythonInvocation.parse(step.commandLines().get(index * 2), work.resolve("scratch"));
            if (command.index() != index + 1 || !command.invocation().equals(invocation) || command.state() != CommandState.PASS || command.error() != null || command.result() == null || !command.result().passed()) throw new IOException("Ordered original actual command failed");
            for (var ref : List.of(command.inputRef(), command.stdoutRef(), command.stderrRef(), command.observationRef())) ref.verify();
            if (!Path.of(command.inputRef().path()).toRealPath().equals(root.resolve("input.json").toRealPath()) || !Path.of(command.stdoutRef().path()).toRealPath().equals(root.resolve("stdout.log").toRealPath())
                    || !Path.of(command.stderrRef().path()).toRealPath().equals(root.resolve("stderr.log").toRealPath()) || !Path.of(command.observationRef().path()).toRealPath().equals(root.resolve("observation.json").toRealPath())
                    || !command.arguments().equals(arguments(invocation, config.bootstrapMode(), root.resolve("input.json")))
                    || !Path.of(command.result().identity().executable()).toRealPath().equals(Path.of(config.pythonExecutable().path()).toRealPath())) throw new IOException("Exact owned original argv/log/native redirector required");
            PythonInput expected = new PythonInput("xar.canonical-python-input/v1", config.bootstrapMode(), config.rootBootstrapRef(), invocation, root.resolve("observation.json").toString());
            if (!read(Path.of(command.inputRef().path()), PythonInput.class).equals(expected)) throw new IOException("Original invocation or bootstrap input differs");
            Observation observed = read(Path.of(command.observationRef().path()), Observation.class); requireObservation(config.bootstrapMode(), config.rootBootstrapRef(), observed);
            Summary summary = summary(text(Path.of(command.stdoutRef().path())) + "\n" + text(Path.of(command.stderrRef().path())));
            if (!summary.accepted() || (requiresTestSummary(invocation) && (summary.groups() == 0 || summary.tests() == 0))
                    || !summary.equals(command.summary()) || !observed.equals(command.observation())) throw new IOException("Actual original outcomes changed");
        }
        requireAbsent(work.resolve("scratch/pycache-no-read")); return ControlBuild.FileRef.measure(path);
    }
    private static Map<String, String> environment(Config config, ParsedStep step, Path scratch) throws IOException {
        Map<String, String> values = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); values.putAll(System.getenv()); values.keySet().removeIf(key -> key.toUpperCase(java.util.Locale.ROOT).startsWith("XAR_"));
        for (String key : List.of("PYTHONPATH", "PYTHONHOME", "PYTHONSAFEPATH", "PYTHONINSPECT", "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS")) values.remove(key);
        for (var row : step.declaredEnvironment().entrySet()) {
            String value = row.getValue().replace("${{ github.workspace }}", config.repository()).replace("${{ runner.temp }}", scratch.toString());
            if (value.contains("${{")) throw new IOException("Undeclared workflow environment expression"); values.put(row.getKey(), value);
        }
        values.put("PYTHONPATH", values.get("PYTHONPATH") + ";" + String.join(";", config.dependencyRoots()));
        values.put("PATH", Path.of(config.gitExecutable().path()).getParent() + ";" + values.get("PATH"));
        for (String key : List.of("RUNNER_TEMP", "TMP", "TEMP", "TMPDIR", "XAR_DEADLINE_TEST_SCRATCH")) values.put(key, scratch.toString());
        for (String key : List.of("PYTHONDONTWRITEBYTECODE", "PYTHONUTF8", "PYTHONNOUSERSITE", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")) values.put(key, "1");
        values.put("PYTHONIOENCODING", "utf-8"); values.put("PYTHONPYCACHEPREFIX", scratch.resolve("pycache-no-read").toString());
        values.put("XAR_PREFLIGHT_FIXTURE_ROOT", scratch.resolve("preflight").toString()); values.put("XAR_PREFLIGHT_APPROVED_ROOT", scratch.resolve("preflight").toString());
        values.put("XAR_WAL_DIAGNOSTIC_ACTUAL_WAL", config.reviewedWalRef().path()); values.put("XAR_WAL_DIAGNOSTIC_ACTUAL_SHA256", SupplementalFixtureCi.WAL_SHA256); return Map.copyOf(values);
    }
    private static Sources inventory(Config config) throws IOException {
        Path repo = absolute(config.repository()).toRealPath(); List<ControlBuild.FileRef> refs = new ArrayList<>();
        for (var pin : config.canonicalSources()) { Path path = absolute(pin.path()); SharedSourceFiles.plainAncestors(path); if (!path.toRealPath().startsWith(repo)) throw new IOException("Declared canonical source escapes repository"); pin.verify(); refs.add(ControlBuild.FileRef.measure(path.toRealPath())); }
        refs.addAll(config.dependencySources()); refs.addAll(List.of(config.pythonExecutable(), config.gitExecutable(), config.workflowRef(), config.reviewedWalRef(), config.executionCardRef()));
        if (config.rootBootstrapRef() != null) { refs.add(config.rootBootstrapRef()); refs.addAll(RootSoftwareChildBootstrap.inputRefs(RootSoftwareChildBootstrap.readConfiguration(config.rootBootstrapRef()))); }
        refs.sort(Comparator.comparing(ControlBuild.FileRef::path)); if (refs.stream().mapToLong(ControlBuild.FileRef::bytes).sum() > 512 * MIB) throw new IOException("Source byte bound");
        for (var ref : refs) ref.verify(); return new Sources("xar.canonical-step-sources/v2", refs);
    }
    private static void verifyInputs(Config config) throws IOException {
        for (var ref : List.of(config.pythonExecutable(), config.gitExecutable(), config.workflowRef(), config.reviewedWalRef(), config.executionCardRef())) { SharedSourceFiles.plainAncestors(Path.of(ref.path())); ref.verify(); }
        for (var refs : List.of(config.canonicalSources(), config.dependencySources())) for (var ref : refs) ref.verify();
        if (config.reviewedWalRef().bytes() != SupplementalFixtureCi.WAL_BYTES || !config.reviewedWalRef().sha256().equals(SupplementalFixtureCi.WAL_SHA256)) throw new IOException("Exact reviewed small WAL required");
        if (config.rootBootstrapRef() != null) { var bootstrap = RootSoftwareChildBootstrap.readConfiguration(config.rootBootstrapRef()); if (!bootstrap.machineId().equals(config.machineId())) throw new IOException("Software bootstrap machine differs"); for (var ref : RootSoftwareChildBootstrap.inputRefs(bootstrap)) ref.verify(); }
        Path work = absolute(config.workRoot()); for (String root : config.dependencyRoots()) if (work.startsWith(absolute(root)) || absolute(root).startsWith(work)) throw new IOException("Dependency/output roots overlap");
    }
    private static void check(Config config, FreshSdkFixtureStage.ResourceGuard resources) throws IOException {
        if (!config.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(Instant.parse(config.reviewAtUtc()))
                || !CanonicalColdWarmStage.class.getProtectionDomain().getCodeSource().getLocation().equals(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation())) throw new IOException("Fresh admitted same shared producer required");
        config.executionCardRef().verify(); resources.revalidate(0);
    }
    static Summary summary(String source) throws IOException {
        int groups = 0, tests = 0, skipped = 0, expected = 0, unexpected = 0, failures = 0, errors = 0, empty = 0;
        for (String line : source.lines().map(String::strip).toList()) {
            Matcher ran = Pattern.compile("Ran ([0-9]+) tests? in .+").matcher(line);
            if (ran.matches()) { int value = count(ran.group(1)); groups++; tests = Math.addExact(tests, value); if (value == 0) empty++; }
            Matcher result = Pattern.compile("(?:OK|FAILED)(?: \\(([^()]*)\\))?").matcher(line);
            if (result.matches() && result.group(1) != null) for (String field : result.group(1).split(", ")) {
                String[] pair = field.split("=", -1); if (pair.length != 2) throw new IOException("Unknown unittest result field"); int value = count(pair[1]);
                switch (pair[0]) {
                    case "skipped" -> skipped = Math.addExact(skipped, value);
                    case "expected failures" -> expected = Math.addExact(expected, value);
                    case "unexpected successes" -> unexpected = Math.addExact(unexpected, value);
                    case "failures" -> failures = Math.addExact(failures, value);
                    case "errors" -> errors = Math.addExact(errors, value);
                    default -> throw new IOException("Unknown unittest result field: " + pair[0]);
                }
            }
            if (line.matches("=+ .* in .+ =+") || line.matches("[0-9]+ (?:passed|failed|skipped|xfailed|xpassed|error|errors).* in .+")) {
                Matcher value = Pattern.compile("(?:^|[ ,=])([0-9]+) (passed|failed|skipped|xfailed|xpassed|error|errors)(?=[ ,=]|$)").matcher(line);
                while (value.find()) { int number = count(value.group(1)); switch (value.group(2)) {
                    case "skipped" -> skipped = Math.addExact(skipped, number);
                    case "xfailed" -> expected = Math.addExact(expected, number);
                    case "xpassed" -> unexpected = Math.addExact(unexpected, number);
                    case "failed" -> failures = Math.addExact(failures, number);
                    case "error", "errors" -> errors = Math.addExact(errors, number);
                    default -> { }
                } }
            }
        }
        return new Summary(groups, tests, skipped, expected, unexpected, failures, errors, empty);
    }
    private static int count(String value) throws IOException { if (!value.matches("0|[1-9][0-9]{0,8}")) throw new IOException("Bounded actual count required"); return Integer.parseInt(value); }
    private static Path absolute(String value) { Path path = Path.of(value); if (!path.isAbsolute() || !path.equals(path.normalize()) || value.contains("\r") || value.contains("\n")) throw new IllegalArgumentException("Normalized absolute path required"); return path; }
    private static void requireAbsent(Path path) throws IOException { SharedSourceFiles.plainAncestors(path); if (Files.exists(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Owned cache remains"); }
    private static ControlBuild.FileRef maybe(Path path) throws IOException { return Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) ? ControlBuild.FileRef.measure(path) : null; }
    private static String text(Path path) throws IOException { if (Files.size(path) > 16 * MIB) throw new IOException("Bounded original logs required"); return Files.readString(path, StandardCharsets.UTF_8); }
    private static <T> T read(Path path, Class<T> type) throws IOException { SharedSourceFiles.plainAncestors(path); if (Files.size(path) > 16 * MIB) throw new IOException("Bounded original metadata required"); return ControlBuild.strictMapper().readValue(Files.readAllBytes(path), type); }
    private static void write(Path path, Record value, Config config, FreshSdkFixtureStage.ResourceGuard resources) throws IOException {
        byte[] raw = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value); if (raw.length > 16 * MIB) throw new IOException("Bounded original metadata required");
        check(config, resources); resources.revalidate(raw.length); SharedSourceFiles.plainAncestors(path); Files.write(path, raw, StandardOpenOption.CREATE_NEW);
    }
    static void writeActual(Path path, Actual actual, Config config, FreshSdkFixtureStage.ResourceGuard resources) throws IOException {
        try { write(path, actual, config, resources); }
        catch (IOException | RuntimeException unavailable) {
            Actual retained = new Actual(actual.schema(), actual.machineId(), actual.startedAtUtc(), actual.observedAtUtc(), SupplementalFixtureCi.Status.RED,
                    append(actual.error(), "Actual publication unavailable: " + unavailable.getMessage()), actual.configRef(), actual.workflowRef(), actual.reviewedWalRef(), actual.producerClosure(),
                    actual.consoleMode(), actual.commands(), actual.sourceBeforeRef(), actual.sourceAfterRef(), actual.sourcePostcheck(), actual.bootstrapMode(), false);
            byte[] raw = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(retained); if (raw.length <= 16 * MIB) System.err.println(new String(raw, StandardCharsets.UTF_8)); throw unavailable;
        }
    }
    private static String append(String previous, String next) { return previous == null ? next : previous + "; " + next; }
}
