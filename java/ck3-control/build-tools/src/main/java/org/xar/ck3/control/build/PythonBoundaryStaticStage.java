package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Two explicit static scopes in the existing ControlCi pipeline; this class is not a runner. */
public final class PythonBoundaryStaticStage {
    private PythonBoundaryStaticStage() {}

    public enum Kind { SDK_SENTINEL_EXTRACTED, MONTHLY_FIXTURE_WHOLE_MODULE }
    public enum Status { PASS, RED }
    public record Config(Kind kind, Path repoRoot, Path workRoot, Path pythonExecutable,
            Path temporaryRoot, Instant reviewAtUtc, String machineId) {
        public Config {
            Objects.requireNonNull(kind); Objects.requireNonNull(repoRoot); Objects.requireNonNull(workRoot);
            Objects.requireNonNull(pythonExecutable); Objects.requireNonNull(temporaryRoot);
            Objects.requireNonNull(reviewAtUtc); Objects.requireNonNull(machineId);
            if (!repoRoot.isAbsolute() || !workRoot.isAbsolute() || !pythonExecutable.isAbsolute()
                    || !temporaryRoot.isAbsolute() || machineId.isBlank()) throw new IllegalArgumentException("Explicit static stage paths and machine required");
        }
    }
    public record SourceRange(String symbol, String path, int firstLine, int lastLine) {
        public SourceRange {
            Objects.requireNonNull(symbol); Objects.requireNonNull(path);
            if (symbol.isBlank() || !Path.of(path).isAbsolute() || firstLine < 1 || lastLine < firstLine) {
                throw new IllegalArgumentException("Exact source range required");
            }
        }
    }
    public record ScopeManifest(String schema, Kind kind, boolean wholeModuleCredit, boolean completed,
            int errorCount, String pythonVersion, String mypyVersion, String mcpVersion,
            List<SourceRange> checkedDefinitions, List<SourceRange> signatureOnlyDefinitions,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> dependencySourceRefs) {
        public ScopeManifest {
            Objects.requireNonNull(schema); Objects.requireNonNull(kind); Objects.requireNonNull(pythonVersion);
            Objects.requireNonNull(mypyVersion); Objects.requireNonNull(mcpVersion);
            checkedDefinitions = List.copyOf(checkedDefinitions); signatureOnlyDefinitions = List.copyOf(signatureOnlyDefinitions);
            sourceRefs = List.copyOf(sourceRefs); dependencySourceRefs = List.copyOf(dependencySourceRefs);
            if (errorCount < 0) throw new IllegalArgumentException("Nonnegative diagnostic count required");
        }
    }
    public record Actual(String schema, Kind kind, String machineId, String startedAtUtc, String observedAtUtc,
            Status status, String error, WindowsJobProcess.CommandResult result,
            ControlBuild.FileRef pythonExecutableRef, List<ControlBuild.FileRef> producerClosure,
            List<ControlBuild.FileRef> sourcePins, List<ControlBuild.FileRef> sourcePostPins,
            ControlBuild.SourceState sourcePostcheck, ControlBuild.FileRef manifestRef,
            ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
            boolean wholeModuleCredit, int gameRpcCalls, int originalDriverOrSaveBodyReads) {
        public Actual {
            Objects.requireNonNull(schema); Objects.requireNonNull(kind); Objects.requireNonNull(machineId);
            Objects.requireNonNull(status); Objects.requireNonNull(sourcePostcheck); Objects.requireNonNull(pythonExecutableRef);
            producerClosure = List.copyOf(producerClosure); sourcePins = List.copyOf(sourcePins);
            sourcePostPins = List.copyOf(sourcePostPins);
        }
    }

    private static final String NATIVE = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py";
    private static final String MCP = "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py";
    private static final String DRIVER = "ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py";
    private static final String SERVICE = "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py";
    private static final String SDK_TEST = "ck3_autonomous_player/tests/unit/test_mcp_war_daily_watch_config_v1.py";
    private static final String FIXTURE = "ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py";

    /* This is the original CI owner's AST harness, retained as one Python child of ControlCi.
       Imported MCP types retain the installed SDK signatures; no replacement SDK stubs are emitted. */
    private static final String PYTHON = """
        import ast
        import copy
        import hashlib
        import importlib.metadata
        import inspect
        import json
        import os
        from pathlib import Path
        import sys
        from mypy.build import build
        from mypy.main import process_options
        from mypy.modulefinder import BuildSource

        kind, manifest_name = sys.argv[1:]
        root = Path.cwd()
        os.environ['MYPYPATH'] = os.pathsep.join((str(root), str(root / 'ck3_autonomous_player/src')))
        checked = []
        signatures = []
        dependencies = []

        def function(nodes: list[ast.stmt], name: str) -> ast.FunctionDef:
            found = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name]
            if len(found) != 1:
                raise ValueError('expected one actual function: ' + name)
            return found[0]

        def class_node(nodes: list[ast.stmt], name: str) -> ast.ClassDef:
            found = [n for n in nodes if isinstance(n, ast.ClassDef) and n.name == name]
            if len(found) != 1:
                raise ValueError('expected one actual class: ' + name)
            return found[0]

        def assignment(nodes: list[ast.stmt], name: str) -> ast.Assign:
            found = [n for n in nodes if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
            if len(found) != 1:
                raise ValueError('expected one actual assignment: ' + name)
            return found[0]

        def source(nodes: list[ast.stmt]) -> str:
            return ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])))

        def reference(path: Path) -> dict[str, object]:
            raw = path.read_bytes()
            return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

        def source_range(path: Path, node: ast.stmt, symbol: str) -> dict[str, object]:
            if node.end_lineno is None:
                raise ValueError('source range lacks an actual end line')
            return {'symbol': symbol, 'path': str(path), 'first_line': node.lineno, 'last_line': node.end_lineno}

        flags = ['--strict', '--strict-equality', '--explicit-package-bases',
            '--follow-imports=silent', '--no-incremental', '--cache-dir', 'nul']
        mcp_version = ''
        if kind == 'SDK_SENTINEL_EXTRACTED':
            from mcp.server import MCPServer
            from mcp.types import ToolAnnotations
            mcp_version = importlib.metadata.version('mcp')
            if mcp_version != '2.0.0':
                raise ValueError('exact installed MCP 2.0.0 signature producer required')
            native_path = root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
            mcp_path = root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
            test_path = root / 'ck3_autonomous_player/tests/unit/test_mcp_war_daily_watch_config_v1.py'
            driver_path = root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py'
            native_tree, mcp_tree, test_tree = (ast.parse(p.read_text(encoding='utf-8'))
                for p in (native_path, mcp_path, test_path))
            driver = class_node(native_tree.body, 'NativeHeadlessGameplayDriver')
            read_method = function(driver.body, 'read_tactical_daily_sentinel_status_private_v1')
            primitive = function(driver.body, '_execute_primitive_step')
            if primitive.decorator_list or read_method.decorator_list:
                raise ValueError('unexpected actual driver decorators')
            primitive_signature = copy.deepcopy(primitive)
            primitive_signature.body = ast.parse('raise NotImplementedError').body
            scoped_driver = copy.deepcopy(driver)
            scoped_driver.body = [primitive_signature, copy.deepcopy(read_method)]
            constants = [assignment(native_tree.body, '_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY'),
                         assignment(native_tree.body, '_TACTICAL_DAILY_SENTINEL_STATUS_STEP')]
            native_scope = source(ast.parse('from pathlib import Path').body
                + [copy.deepcopy(n) for n in constants] + [scoped_driver])
            checked.extend(source_range(native_path, n, n.targets[0].id) for n in constants)
            checked.append(source_range(native_path, read_method, read_method.name))
            signatures.append({'symbol': primitive.name, 'path': str(native_path),
                'first_line': primitive.lineno, 'last_line': primitive.body[0].lineno - 1})
            create = function(mcp_tree.body, 'create_server')
            annotations = assignment(create.body, 'read_only_tool')
            sentinel = assignment(create.body, 'sentinel_status')
            guard = create.body[create.body.index(sentinel) + 1]
            if not isinstance(guard, ast.If):
                raise ValueError('actual sentinel assignment must precede actual guard')
            handler = function(guard.body, 'ck3_read_tactical_daily_sentinel_status_private_v1')
            if len(handler.decorator_list) != 1:
                raise ValueError('actual handler decorator missing or duplicated')
            if create.args.args[0].arg != 'driver' or create.args.args[0].annotation is None:
                raise ValueError('actual create_server driver annotation missing')
            header = ast.parse('import json\\nfrom mcp.server import MCPServer\\n'
                + 'from mcp.types import ToolAnnotations\\nfrom .driver import GameplayBridgeDriver\\n')
            wrapper = function(ast.parse('def _actual_sentinel_registration_scope('
                + 'driver: GameplayBridgeDriver, server: MCPServer[object]) -> None:\\n    pass\\n').body,
                '_actual_sentinel_registration_scope')
            wrapper.args.args[0].annotation = copy.deepcopy(create.args.args[0].annotation)
            wrapper.body = [copy.deepcopy(annotations), copy.deepcopy(sentinel), copy.deepcopy(guard)]
            mcp_scope = source(header.body + [wrapper])
            checked.extend((source_range(mcp_path, annotations, 'read_only_tool'),
                source_range(mcp_path, sentinel, 'sentinel_status'),
                source_range(mcp_path, guard, 'sentinel_guard_and_handler')))
            tests = class_node(test_tree.body, 'McpWarDailyWatchConfigTests')
            case = function(tests.body, 'test_fixed_status_driver_uses_only_existing_capability_without_transcript')
            scoped_tests = copy.deepcopy(tests)
            scoped_tests.body = [copy.deepcopy(case)]
            test_scope = source(ast.parse('import unittest\\nfrom unittest.mock import patch\\n'
                + 'from xar_autoplayer.bridge import native_driver\\n').body + [scoped_tests])
            checked.append(source_range(test_path, case, case.name))
            paths = (native_path, mcp_path, driver_path, test_path)
            sdk_paths = sorted({Path(inspect.getfile(v)).resolve() for v in (MCPServer, MCPServer.tool, ToolAnnotations)})
            dependencies = [reference(p) for p in sdk_paths]
            sources = [BuildSource(str(native_path), 'xar_autoplayer.bridge.native_driver', native_scope),
                BuildSource(str(mcp_path), 'xar_autoplayer.bridge.mcp_server', mcp_scope),
                BuildSource(str(test_path), 'test_mcp_war_daily_watch_config_v1', test_scope)]
            whole_module = False
            python_version = str(sys.version_info.major) + '.' + str(sys.version_info.minor)
        elif kind == 'MONTHLY_FIXTURE_WHOLE_MODULE':
            test_path = root / 'ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py'
            paths = (test_path, root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py',
                root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py')
            raw = test_path.read_text(encoding='utf-8')
            checked.append({'symbol': 'whole_module', 'path': str(test_path),
                'first_line': 1, 'last_line': len(raw.splitlines())})
            sources = [BuildSource(str(test_path), 'test_conditional_monthly_loss_budgets', raw)]
            flags.extend(('--python-version', '3.11'))
            whole_module = True
            python_version = '3.11'
        else:
            raise ValueError('fixed typed static stage required')
        refs = [reference(path) for path in paths]
        _, options = process_options(flags + ['-c', 'pass'])
        result = build(sources=sources, options=options)
        for error in result.errors:
            print(error)
        for item in refs + dependencies:
            if reference(Path(item['path'])) != item:
                raise ValueError('actual static source/signature dependency changed')
        manifest = {'schema': 'xar.python-boundary-static-scope/v1', 'kind': kind,
            'whole_module_credit': whole_module, 'completed': True, 'error_count': len(result.errors),
            'python_version': python_version, 'mypy_version': importlib.metadata.version('mypy'),
            'mcp_version': mcp_version, 'checked_definitions': checked, 'signature_only_definitions': signatures,
            'source_refs': refs, 'dependency_source_refs': dependencies}
        payload = json.dumps(manifest, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if len(payload) > 65536:
            raise ValueError('bounded actual static scope manifest required')
        with Path(manifest_name).open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        print('PYTHON_BOUNDARY_STATIC ' + kind + ' ' + ('RED' if result.errors else 'PASS'), flush=True)
        sys.exit(1 if result.errors else 0)
        """;

    public static ControlBuild.FileRef run(Config config) throws IOException, InterruptedException {
        if (!config.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(config.reviewAtUtc())) {
            throw new IOException("Fresh machine-bound static stage required");
        }
        Files.createDirectories(config.workRoot());
        Path stdout = config.workRoot().resolve("stdout.log"), stderr = config.workRoot().resolve("stderr.log");
        Path manifestPath = config.workRoot().resolve("scope.json"), receipt = config.workRoot().resolve("actual.json");
        if (Files.exists(manifestPath) || Files.exists(receipt) || Files.exists(stdout) || Files.exists(stderr)) {
            throw new IOException("Static stage output must be create-only");
        }
        List<ControlBuild.FileRef> before = pins(config), after = List.of();
        ControlBuild.FileRef python = ControlBuild.FileRef.measure(config.pythonExecutable());
        List<ControlBuild.FileRef> closure = ControlBuild.producerClosure();
        String started = Instant.now().toString(), failure = null;
        WindowsJobProcess.CommandResult terminal = null;
        ControlBuild.SourceState sourceState = ControlBuild.SourceState.UNKNOWN;
        ControlBuild.FileRef manifestRef = null;
        try {
            Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
            String inherited = environment.getOrDefault("PYTHONPATH", "");
            environment.put("PYTHONPATH", config.repoRoot() + ";" + config.repoRoot().resolve("ck3_autonomous_player/src")
                    + (inherited.isEmpty() ? "" : ";" + inherited));
            environment.put("MYPYPATH", config.repoRoot() + ";" + config.repoRoot().resolve("ck3_autonomous_player/src"));
            environment.put("PYTHONDONTWRITEBYTECODE", "1"); environment.put("PYTHONIOENCODING", "utf-8");
            environment.put("TEMP", config.temporaryRoot().toString()); environment.put("TMP", config.temporaryRoot().toString());
            var command = new WindowsJobProcess.CommandSpec(config.pythonExecutable(),
                    List.of("-B", "-X", "utf8", "-c", PYTHON, config.kind().name(), manifestPath.toString()),
                    config.repoRoot(), Map.copyOf(environment), stdout, stderr, 1536L << 20);
            try (WindowsJobProcess process = WindowsJobProcess.start(command)) {
                terminal = process.await(Duration.ofMinutes(10), config.reviewAtUtc(), () -> {});
            }
            after = pins(config); sourceState = before.equals(after) ? ControlBuild.SourceState.MATCH : ControlBuild.SourceState.MISMATCH;
            python.verify(); for (var ref : closure) ref.verify();
            if (!terminal.passed()) throw new IOException("Static stage child failed or did not leave Job0: " + terminal);
            if (sourceState != ControlBuild.SourceState.MATCH) throw new IOException("Static source changed during execution");
            ScopeManifest manifest = readManifest(manifestPath);
            requireScope(config.kind(), manifest);
            if (!sorted(manifest.sourceRefs()).equals(sorted(before))) throw new IOException("Actual checker source closure differs from original pins");
            manifestRef = ControlBuild.FileRef.measure(manifestPath);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt(); failure = "InterruptedException: static stage interrupted";
        } catch (IOException | RuntimeException error) {
            failure = error.getClass().getSimpleName() + ": " + error.getMessage();
        } finally {
            if (manifestRef == null && Files.exists(manifestPath)) manifestRef = ControlBuild.FileRef.measure(manifestPath);
            if (failure == null && (terminal == null || !terminal.passed() || sourceState != ControlBuild.SourceState.MATCH || manifestRef == null)) {
                failure = "Static stage incomplete; no successful actual terminal/scope/source postcheck";
            }
            Actual actual = new Actual("xar.java-control-python-static-stage/v1", config.kind(), config.machineId(), started,
                    Instant.now().toString(), failure == null ? Status.PASS : Status.RED, failure, terminal, python, closure,
                    before, after, sourceState, manifestRef, Files.exists(stdout) ? ControlBuild.FileRef.measure(stdout) : null,
                    Files.exists(stderr) ? ControlBuild.FileRef.measure(stderr) : null,
                    config.kind() == Kind.MONTHLY_FIXTURE_WHOLE_MODULE, 0, 0);
            Files.write(receipt, ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(actual), StandardOpenOption.CREATE_NEW);
        }
        if (failure != null) throw new IOException(failure);
        return requireAccepted(receipt, config.kind(), config.machineId());
    }

    /** Called both in ControlCi and by its durable receipt-consumption workflow step. */
    public static ControlBuild.FileRef requireAccepted(Path receipt, Kind kind, String machineId) throws IOException {
        if (Files.size(receipt) > 65536) throw new IOException("Bounded actual static receipt required");
        Actual actual = ControlBuild.strictMapper().readValue(Files.readAllBytes(receipt), Actual.class);
        if (!actual.schema().equals("xar.java-control-python-static-stage/v1") || actual.kind() != kind
                || !actual.machineId().equals(machineId) || actual.status() != Status.PASS || actual.error() != null
                || actual.result() == null || !actual.result().passed() || actual.sourcePostcheck() != ControlBuild.SourceState.MATCH
                || !actual.sourcePins().equals(actual.sourcePostPins()) || actual.sourcePins().isEmpty()
                || actual.manifestRef() == null || actual.stdoutRef() == null || actual.stderrRef() == null
                || actual.wholeModuleCredit() != (kind == Kind.MONTHLY_FIXTURE_WHOLE_MODULE)
                || actual.gameRpcCalls() != 0 || actual.originalDriverOrSaveBodyReads() != 0
                || !actual.producerClosure().equals(ControlBuild.producerClosure())) throw new IOException("Complete successful actual static stage required");
        actual.pythonExecutableRef().verify(); actual.stdoutRef().verify(); actual.stderrRef().verify(); actual.manifestRef().verify();
        for (var ref : actual.sourcePins()) ref.verify(); for (var ref : actual.producerClosure()) ref.verify();
        ScopeManifest manifest = readManifest(Path.of(actual.manifestRef().path()));
        requireScope(kind, manifest);
        if (!sorted(manifest.sourceRefs()).equals(sorted(actual.sourcePins()))) throw new IOException("Static receipt does not bind actual scope");
        return ControlBuild.FileRef.measure(receipt);
    }

    static void requireScope(Kind kind, ScopeManifest manifest) throws IOException {
        if (!manifest.schema().equals("xar.python-boundary-static-scope/v1") || manifest.kind() != kind
                || !manifest.completed() || manifest.errorCount() != 0 || manifest.mypyVersion().isBlank()
                || manifest.wholeModuleCredit() != (kind == Kind.MONTHLY_FIXTURE_WHOLE_MODULE)) throw new IOException("Actual completed zero-error strict scope required");
        if (kind == Kind.SDK_SENTINEL_EXTRACTED) {
            if (!manifest.mcpVersion().equals("2.0.0") || manifest.checkedDefinitions().size() != 7
                    || manifest.signatureOnlyDefinitions().size() != 1 || manifest.sourceRefs().size() != 4
                    || manifest.dependencySourceRefs().size() < 2
                    || !manifest.signatureOnlyDefinitions().getFirst().symbol().equals("_execute_primitive_step")
                    || !manifest.checkedDefinitions().stream().map(SourceRange::symbol).toList().equals(List.of(
                            "_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY", "_TACTICAL_DAILY_SENTINEL_STATUS_STEP",
                            "read_tactical_daily_sentinel_status_private_v1", "read_only_tool", "sentinel_status",
                            "sentinel_guard_and_handler", "test_fixed_status_driver_uses_only_existing_capability_without_transcript"))) {
                throw new IOException("Exact actual SDK method/guard/handler/one-case scope and installed dependency signatures required");
            }
        } else if (!manifest.pythonVersion().equals("3.11") || !manifest.mcpVersion().isEmpty()
                || manifest.checkedDefinitions().size() != 1 || !manifest.checkedDefinitions().getFirst().symbol().equals("whole_module")
                || !manifest.signatureOnlyDefinitions().isEmpty() || manifest.sourceRefs().size() != 3
                || !manifest.dependencySourceRefs().isEmpty()) throw new IOException("Whole modified fixture Python 3.11 strict scope required");
        List<String> paths = manifest.sourceRefs().stream().map(ControlBuild.FileRef::path).toList();
        if (paths.stream().distinct().count() != paths.size()) throw new IOException("Repeated static source reference");
        for (SourceRange range : manifest.checkedDefinitions()) if (!paths.contains(range.path())) throw new IOException("Checked range escapes actual source closure");
        for (SourceRange range : manifest.signatureOnlyDefinitions()) if (!paths.contains(range.path())) throw new IOException("Signature range escapes actual source closure");
        for (var ref : manifest.sourceRefs()) ref.verify(); for (var ref : manifest.dependencySourceRefs()) ref.verify();
    }

    private static ScopeManifest readManifest(Path path) throws IOException {
        if (Files.size(path) > 65536) throw new IOException("Bounded actual scope manifest required");
        return ControlBuild.strictMapper().readValue(Files.readAllBytes(path), ScopeManifest.class);
    }

    /** Consume pytest's actual report: a zero command exit with skipped tests is insufficient. */
    static void requireSuccessfulPytest(Path path) throws IOException {
        if (Files.size(path) > (8L << 20)) throw new IOException("Bounded actual pytest report required");
        try {
            var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
            factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, "");
            factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            var document = factory.newDocumentBuilder().parse(path.toFile());
            var suites = document.getElementsByTagName("testsuite");
            if (suites.getLength() < 1 || suites.getLength() > 64) throw new IOException("Actual pytest suites required");
            int tests = 0;
            for (int index = 0; index < suites.getLength(); index++) {
                if (!(suites.item(index) instanceof org.w3c.dom.Element suite)) throw new IOException("Actual pytest suite required");
                if (!suite.getAttribute("failures").equals("0") || !suite.getAttribute("errors").equals("0")
                        || !suite.getAttribute("skipped").equals("0") || !suite.getAttribute("tests").matches("[0-9]{1,6}")
                        || suite.getElementsByTagName("skipped").getLength() != 0
                        || suite.getElementsByTagName("failure").getLength() != 0
                        || suite.getElementsByTagName("error").getLength() != 0) throw new IOException("Pytest failure, error, skip or missing terminal counters");
                int count = Integer.parseInt(suite.getAttribute("tests"));
                if (count != suite.getElementsByTagName("testcase").getLength()) throw new IOException("Pytest testcase count differs from actual report body");
                tests = Math.addExact(tests, count);
            }
            if (tests == 0) throw new IOException("Positive executed pytest count required");
        } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException | NumberFormatException error) {
            throw new IOException("Actual pytest report invalid", error);
        }
    }
    private static List<ControlBuild.FileRef> pins(Config config) throws IOException {
        List<ControlBuild.FileRef> result = new ArrayList<>();
        for (String name : config.kind() == Kind.SDK_SENTINEL_EXTRACTED ? List.of(NATIVE, MCP, DRIVER, SDK_TEST) : List.of(FIXTURE, DRIVER, SERVICE)) {
            result.add(ControlBuild.FileRef.measure(config.repoRoot().resolve(name).toRealPath()));
        }
        return List.copyOf(result);
    }
    private static List<ControlBuild.FileRef> sorted(List<ControlBuild.FileRef> refs) {
        return refs.stream().sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
    }
}
