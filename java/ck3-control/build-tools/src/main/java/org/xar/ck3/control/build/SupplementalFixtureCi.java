package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.FileVisitResult;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Pattern;
import org.w3c.dom.Element;

/** Complete fixture checks in the shared Java CI producer. No Game endpoint or Python CI module. */
public final class SupplementalFixtureCi {
    private SupplementalFixtureCi() {}
    public static final String SCHEMA = "xar.supplemental-fixture-ci/v1";
    private static final String INVENTORY_SCHEMA = "xar.supplemental-fixture-sources/v1";
    private static final long METADATA_LIMIT = 16L << 20;
    private static final long OUTPUT_LIMIT = 64L << 20;
    private static final long FINAL_METADATA_RESERVE = 1L << 20;
    public static final String WAL_RELATIVE = "java/ck3-control/build-tools/src/test/resources/ci-reviewed-small-wal/ROOT-FIRST-NATURAL-H-WAL01.json";
    public static final long WAL_BYTES = 42506;
    public static final String WAL_SHA256 = "a7f9ec3a0462a61846185a52334d2010e28652ca2ccec22050c2f45aae176c84";
    private static final String PREFIX = "ck3_autonomous_player/tests/unit/";

    public enum Status { PASS, RED }
    public enum Stage { PYTHON_VERSION, MYPY_VERSION, MYPY_DISTRIBUTION, PYTEST_VERSION, WHOLE_SEVEN_STATIC, CORE_34_AND_SUPPLEMENTAL_2 }
    public record Config(Path repoRoot, Path workRoot, Path pythonExecutable,
            Path temporaryRoot, Instant reviewAtUtc, String machineId, Path checkerSitePackages) {
        public Config {
            for (Path path : List.of(repoRoot, workRoot, pythonExecutable, temporaryRoot)) {
                if (!path.isAbsolute()) throw new IllegalArgumentException("Explicit absolute CI paths required");
            }
            Objects.requireNonNull(reviewAtUtc);
            if (checkerSitePackages != null && !checkerSitePackages.isAbsolute()) throw new IllegalArgumentException("Explicit checker site-packages required");
            for (Path path : List.of(workRoot, temporaryRoot)) if (path.normalize().startsWith(repoRoot.normalize()) || repoRoot.normalize().startsWith(path.normalize())) throw new IllegalArgumentException("CI outputs and source repository must be disjoint");
            if (workRoot.normalize().startsWith(temporaryRoot.normalize()) || temporaryRoot.normalize().startsWith(workRoot.normalize())) throw new IllegalArgumentException("Distinct admitted parent scratch and work roots required");
            if (machineId == null || machineId.isBlank()) throw new IllegalArgumentException("Machine identity required");
        }
    }
    public record SourceInventory(String schema, List<ControlBuild.FileRef> sources) {
        public SourceInventory {
            sources = List.copyOf(sources);
            if (!INVENTORY_SCHEMA.equals(schema) || sources.isEmpty() || sources.size() > 20000
                    || sources.stream().map(ControlBuild.FileRef::path).distinct().count() != sources.size()) {
                throw new IllegalArgumentException("Complete bounded unique source inventory required");
            }
        }
    }
    public record CommandEvidence(Stage stage, List<String> arguments, WindowsJobProcess.CommandResult result,
            ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef) {
        public CommandEvidence { arguments = List.copyOf(arguments); Objects.requireNonNull(stage); }
    }
    public record ModuleCount(String path, int parents) {
        public ModuleCount {
            requireModule(path);
            if (parents < 1) throw new IllegalArgumentException("Every complete module must execute a parent test");
        }
    }
    /** JUnit counts include subtests; testcase elements represent parents in pytest 9. */
    public record PytestCounts(int junitTests, int testcaseElements, int parentPassed, int parentFailed,
            int parentErrors, int parentSkipped, int subtestsPassed, int subtestsFailed,
            int subtestsSkipped, int aggregateFailed, int aggregateErrors, List<ModuleCount> modules) {
        public PytestCounts {
            modules = List.copyOf(modules);
            for (int count : List.of(junitTests, testcaseElements, parentPassed, parentFailed, parentErrors,
                    parentSkipped, subtestsPassed, subtestsFailed, subtestsSkipped, aggregateFailed, aggregateErrors)) {
                if (count < 0) throw new IllegalArgumentException("Negative actual pytest count");
            }
            int parents = Math.addExact(Math.addExact(parentPassed, parentFailed), Math.addExact(parentErrors, parentSkipped));
            int subtests = Math.addExact(subtestsPassed, Math.addExact(subtestsFailed, subtestsSkipped));
            if (testcaseElements < 1 || modules.isEmpty() || parents != testcaseElements
                    || junitTests != Math.addExact(parents, subtests) || aggregateFailed != Math.addExact(parentFailed, subtestsFailed)
                    || aggregateErrors < parentErrors || (aggregateErrors == 0) != (parentErrors == 0)
                    || modules.stream().map(ModuleCount::path).distinct().count() != modules.size()
                    || modules.stream().mapToInt(ModuleCount::parents).reduce(0, Math::addExact) != parents) {
                throw new IllegalArgumentException("Actual parent/subtest/module count equations required");
            }
        }
    }
    public enum FixtureKind { SOLDIER, SCOPED, FRESH }
    public record FixtureEvidence(FixtureKind kind, ControlBuild.FileRef fileRef) {}
    private record OutputSlot(FixtureKind kind, String directory, String environmentName) {}
    private static List<OutputSlot> outputSlots() {
        return List.of(new OutputSlot(FixtureKind.SOLDIER, "soldier", "XAR_CURRENT_CALLBACK_SOLDIER_EFFECTS_FIRST_OUTPUT"),
                new OutputSlot(FixtureKind.SCOPED, "scoped", "XAR_PREPARE_SCOPED_CORE_OUTPUT"),
                new OutputSlot(FixtureKind.FRESH, "fresh", "XAR_FRESH_ORDERED_B_OUTPUT"));
    }
    public record Actual(String schema, String machineId, String startedAtUtc, String observedAtUtc, String reviewAtUtc,
            Status status, String error, String repoRoot, List<String> coreModules,
            List<String> supplementaryModules, List<String> wholeStaticModules,
            ControlBuild.FileRef pythonExecutableRef, List<ControlBuild.FileRef> producerClosure,
            ControlBuild.FileRef sourceBeforeRef, ControlBuild.FileRef sourceAfterRef,
            ControlBuild.SourceState sourcePostcheck, List<CommandEvidence> commands,
            ControlBuild.FileRef junitRef, PytestCounts pytestCounts, String temporaryRoot, String checkerSitePackages,
            List<ControlBuild.FileRef> checkerSourcePins, List<ControlBuild.FileRef> checkerSourcePostPins,
            List<FixtureEvidence> fixtureOutputs) {
        public Actual {
            coreModules = List.copyOf(coreModules); supplementaryModules = List.copyOf(supplementaryModules);
            wholeStaticModules = List.copyOf(wholeStaticModules); producerClosure = List.copyOf(producerClosure);
            commands = List.copyOf(commands); checkerSourcePins = List.copyOf(checkerSourcePins);
            checkerSourcePostPins = List.copyOf(checkerSourcePostPins); fixtureOutputs = List.copyOf(fixtureOutputs);
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact supplemental CI contract required");
            Instant.parse(startedAtUtc); Instant.parse(observedAtUtc); Instant.parse(reviewAtUtc);
        }
    }

    public static List<String> coreModules() {
        return modules("army_chunk_loss_writeback_projection conditional_current_helper_domain_updates conditional_current_helper_point_stores conditional_daily_queue_transfer conditional_loss_sequence_replay conditional_manager_cleanup conditional_monthly_caller_effects conditional_monthly_loss_budgets current_assault_first_removal_context_service current_callback_soldier_effects_service_12004 current_callback_supply_risk_service_12004 current_candidate_detachment_mapper_service current_daily_assault_loss_service current_daily_assault_normal_return_release_service current_daily_assault_queue_append_service explicit_preparation_scoped_core_mcp fixed_chunk0_preparation_service fresh_ordered_b_preparation_mcp post_refill_besieging_current_service selected_refill_monthly_assembly_service selected_refill_monthly_fleet_service wartime_army_working_copy_costs army_current_post_admission_refresh_service_12003 current_daily_assault_table_service current_replenishment_normal_plan_v1 daily_assault_general_carried_collision_service daily_assault_placement_service daily_assault_roster_admission_service ordered_refill_besieging_assault_service post_refill_land_rate_service_join pre_date_character_prefix_service pre_date_dated_append_service pre_date_pending_update_service scoped_ordered_refill_service");
    }
    public static List<String> supplementaryModules() {
        return modules("mcp_war_daily_watch_config_v1 holy_order_siege_reinforcement_service_v1");
    }
    public static List<String> wholeStaticModules() {
        return modules("mcp_war_daily_watch_config_v1 scoped_ordered_refill_service post_refill_land_rate_service_join ordered_refill_besieging_assault_service conditional_loss_sequence_replay holy_order_siege_reinforcement_service_v1 current_callback_soldier_effects_service_12004");
    }
    public static List<String> haltAndArmyModules() {
        return modules("unsafe_committed_route_halt unsafe_embarked_route_halt army_auto_scalar_projection_v1 army_private_auto_scalar_ab_v1 native_negative_route_regroup clock_observation_timing_v1 planner_stage_timing_v1 planner_consumer_timing_v1 mcp_war_daily_watch_config_v1 planner_prep_timing_v1 native_kernel32_cache p51_successor_relay_binding_v1 p51_resident_successor_adoption_v1 contact_free_exact_route_speed_trial_v1 battle_reader_exact_speed defender_refuge_candidates arrived_refuge_lifecycle retreating_only_committed_route event_history_free native_assault_lifecycle_scan_reuse_v1 recent_command_index_no_materialization_v1 raiktor_history_factory_v1 forecast_history_factory_v1 rendezvous_history_factory_v1 origin_history_factory_v1 war_termination_history_read_guard assault_holding_history_projection_copy");
    }
    public static PytestCounts requireHaltAndArmyPytest(Path xml, Path stdout) throws IOException {
        PytestCounts counts = readPytest(xml, stdout, haltAndArmyModules()); requirePassed(counts); return counts;
    }
    private static List<String> allRuntimeModules() {
        List<String> all = new ArrayList<>(coreModules()); all.addAll(supplementaryModules()); return List.copyOf(all);
    }
    private static List<String> modules(String names) {
        return java.util.Arrays.stream(names.split(" ")).map(name -> PREFIX + "test_" + name + ".py").toList();
    }
    private static void requireModule(String path) {
        if (path == null || !path.matches("(?:[A-Za-z_][A-Za-z0-9_]*/)+test_[A-Za-z0-9_]+\\.py")) {
            throw new IllegalArgumentException("Whole source modules required; selectors refused");
        }
    }

    /** Fixed reviewed production journal; a repository copy never inherits the historical file identity. */
    public static ControlBuild.FileRef requireReviewedWal(Path repoRoot) throws IOException {
        Path expected = repoRoot.toRealPath().resolve(WAL_RELATIVE);
        if (!Files.isRegularFile(expected, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(expected)
                || !expected.toRealPath().startsWith(repoRoot.toRealPath())) throw new IOException("Reviewed WAL fixture unavailable");
        ControlBuild.FileRef actual = ControlBuild.FileRef.measure(expected.toRealPath());
        if (actual.bytes() != WAL_BYTES || !actual.sha256().equals(WAL_SHA256)) throw new IOException("Reviewed WAL fixture bytes/SHA differ");
        return actual;
    }
    public static ControlBuild.FileRef requireReviewedWalEnvironment(Path repoRoot, Map<String, String> environment) throws IOException {
        String path = environment.get("XAR_WAL_DIAGNOSTIC_ACTUAL_WAL"), sha = environment.get("XAR_WAL_DIAGNOSTIC_ACTUAL_SHA256");
        if (path == null || path.isBlank() || sha == null || !sha.equals(WAL_SHA256)) throw new IOException("Explicit reviewed WAL environment and SHA required; missing input cannot skip");
        ControlBuild.FileRef actual = requireReviewedWal(repoRoot);
        if (!Path.of(path).isAbsolute() || !Path.of(path).toRealPath().equals(Path.of(actual.path()))) throw new IOException("Reviewed WAL environment selects another file");
        return actual;
    }

    public static ControlBuild.FileRef run(Config config) throws IOException, InterruptedException {
        requireCurrent(config);
        if (Files.exists(config.workRoot())) throw new IOException("Supplemental work root must be create-only");
        SharedSourceFiles.plainAncestors(config.repoRoot()); SharedSourceFiles.plainAncestors(config.workRoot());
        SharedSourceFiles.plainAncestors(config.temporaryRoot());
        Files.createDirectories(config.workRoot()); Files.createDirectory(config.workRoot().resolve("scratch"));
        if (!Files.isDirectory(config.temporaryRoot(), LinkOption.NOFOLLOW_LINKS)) throw new IOException("Admitted temporary root required");
        String started = Instant.now().toString();
        SourceInventory before = inventory(config.repoRoot(), config.reviewAtUtc());
        Path beforePath = config.workRoot().resolve("sources-before.json"), afterPath = config.workRoot().resolve("sources-after.json");
        write(beforePath, before);
        ControlBuild.FileRef beforeRef = ControlBuild.FileRef.measure(beforePath), afterRef = null;
        ControlBuild.FileRef python = ControlBuild.FileRef.measure(config.pythonExecutable());
        List<ControlBuild.FileRef> closure = ControlBuild.producerClosure();
        List<CommandEvidence> commands = new ArrayList<>();
        List<ControlBuild.FileRef> checkerPins = List.of(), checkerAfter = List.of();
        List<FixtureEvidence> fixtureOutputs = List.of();
        Path xml = config.workRoot().resolve("pytest.xml"); ControlBuild.FileRef xmlRef = null;
        PytestCounts counts = null; String failure = null; boolean complete = false;
        ControlBuild.SourceState postcheck = ControlBuild.SourceState.UNKNOWN;
        try {
            Map<String, String> environment = environment(config);
            CommandEvidence version = command(config, environment, Stage.PYTHON_VERSION, List.of("-V"), Duration.ofSeconds(30));
            commands.add(version); requireCommand(version);
            String versionText = output(version).trim();
            if (!versionText.matches("Python 3\\.13\\.[0-9]+")) throw new IOException("Actual native Python 3.13 required: " + versionText);
            CommandEvidence mypy = command(config, environment, Stage.MYPY_VERSION, List.of("-B", "-m", "mypy", "--version"), Duration.ofSeconds(30));
            commands.add(mypy); requireCommand(mypy);
            if (!output(mypy).trim().matches("mypy 1\\.15\\.0(?: \\(.*\\))?")) throw new IOException("Configured actual mypy 1.15.0 required");
            CommandEvidence origin = command(config, environment, Stage.MYPY_DISTRIBUTION,
                    List.of("-B", "-m", "pip", "show", "--files", "mypy"), Duration.ofSeconds(30));
            commands.add(origin); requireCommand(origin); checkerPins = checkerSources(output(origin), config.checkerSitePackages());
            CommandEvidence pytestVersion = command(config, environment, Stage.PYTEST_VERSION,
                    List.of("-B", "-m", "pytest", "--version"), Duration.ofSeconds(30));
            commands.add(pytestVersion); requireCommand(pytestVersion);
            if (!output(pytestVersion).trim().equals("pytest 9.1.1")) throw new IOException("Actual configured pytest 9.1.1 required");
            CommandEvidence strict = command(config, environment, Stage.WHOLE_SEVEN_STATIC, staticArguments(), Duration.ofMinutes(10));
            commands.add(strict); requireCommand(strict);
            CommandEvidence pytest = command(config, environment, Stage.CORE_34_AND_SUPPLEMENTAL_2,
                    pytestArguments(xml, config.workRoot().resolve("pytest-temp")), Duration.ofMinutes(15));
            commands.add(pytest);
            if (Files.isRegularFile(xml)) {
                xmlRef = ControlBuild.FileRef.measure(xml);
                counts = readPytest(xml, Path.of(pytest.stdoutRef().path()), allRuntimeModules());
            }
            fixtureOutputs = fixtureOutputs(config.workRoot());
            requireCommand(pytest);
            if (counts == null) throw new IOException("Actual pytest JUnit and summary are required");
            requirePassed(counts); complete = true;
        } catch (IOException | RuntimeException error) { failure = error.getClass().getSimpleName() + ": " + error.getMessage(); }
        finally {
            if (!complete && failure == null) failure = "Supplemental CI interrupted or incomplete";
            try {
                SourceInventory after = inventory(config.repoRoot(), config.reviewAtUtc()); write(afterPath, after);
                afterRef = ControlBuild.FileRef.measure(afterPath);
                List<ControlBuild.FileRef> observedChecker = new ArrayList<>();
                for (var ref : checkerPins) { SharedSourceFiles.plainAncestors(Path.of(ref.path())); observedChecker.add(ControlBuild.FileRef.measure(Path.of(ref.path()))); }
                checkerAfter = List.copyOf(observedChecker);
                postcheck = before.equals(after) && checkerPins.equals(checkerAfter) ? ControlBuild.SourceState.MATCH : ControlBuild.SourceState.MISMATCH;
                if (postcheck != ControlBuild.SourceState.MATCH) failure = append(failure, "Complete source inventory changed");
                python.verify(); for (var ref : closure) ref.verify(); requireCurrent(config); requireUnusedPycache(config.workRoot()); guardOutput(config.workRoot(), FINAL_METADATA_RESERVE);
            } catch (IOException | RuntimeException error) { failure = append(failure, "Source/producer/final check unavailable: " + error.getMessage()); }
            write(config.workRoot().resolve("actual.json"), new Actual(SCHEMA, config.machineId(), started, Instant.now().toString(), config.reviewAtUtc().toString(),
                    failure == null ? Status.PASS : Status.RED, failure, config.repoRoot().toString(), coreModules(),
                    supplementaryModules(), wholeStaticModules(), python, closure, beforeRef, afterRef, postcheck,
                    commands, xmlRef, counts, config.workRoot().resolve("scratch").toString(),
                    config.checkerSitePackages() == null ? null : config.checkerSitePackages().toString(), checkerPins, checkerAfter, fixtureOutputs));
        }
        if (failure != null) throw new IOException(failure);
        return requireAccepted(config.workRoot().resolve("actual.json"), config.machineId());
    }

    static List<String> staticArguments() {
        List<String> args = new ArrayList<>(List.of("-B", "-X", "utf8", "-m", "mypy", "--strict", "--strict-equality",
                "--explicit-package-bases", "--follow-imports=silent", "--no-incremental", "--cache-dir", "nul", "--python-version", "3.13"));
        args.addAll(wholeStaticModules()); return List.copyOf(args);
    }
    static List<String> pytestArguments(Path xml, Path temporary) {
        List<String> args = new ArrayList<>(List.of("-B", "-X", "utf8", "-m", "pytest", "-q", "-ra", "--color=no",
                "-o", "verbosity_subtests=1", "-p", "no:cacheprovider", "--junitxml=" + xml, "--basetemp=" + temporary));
        args.addAll(allRuntimeModules()); return List.copyOf(args);
    }
    private static Map<String, String> environment(Config config) throws IOException {
        Map<String, String> env = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); env.putAll(System.getenv());
        env.keySet().removeIf(key -> key.toUpperCase(java.util.Locale.ROOT).startsWith("XAR_"));
        for (String name : List.of("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONHOME")) env.remove(name);
        env.put("PYTHONPATH", String.join(System.getProperty("path.separator"), config.repoRoot().toString(),
                config.repoRoot().resolve("ck3_autonomous_player/src").toString(), config.repoRoot().resolve("ck3_autonomous_player/tests/unit").toString()));
        env.put("MYPYPATH", env.get("PYTHONPATH")); env.put("PYTHONOPTIMIZE", "0");
        if (config.checkerSitePackages() != null) {
            SharedSourceFiles.plainAncestors(config.checkerSitePackages());
            env.put("PYTHONPATH", env.get("PYTHONPATH") + System.getProperty("path.separator") + config.checkerSitePackages());
        }
        for (OutputSlot slot : outputSlots()) {
            Path directory = Files.createDirectory(config.workRoot().resolve(slot.directory()));
            env.put(slot.environmentName(), directory.resolve("cases.json").toString());
        }
        for (String name : List.of("PYTHONDONTWRITEBYTECODE", "PYTHONUTF8", "PYTHONNOUSERSITE", "PYTEST_DISABLE_PLUGIN_AUTOLOAD")) env.put(name, "1");
        env.put("PYTHONIOENCODING", "utf-8");
        requireUnusedPycache(config.workRoot());
        env.put("PYTHONPYCACHEPREFIX", config.workRoot().resolve("scratch/pycache-no-read").toString());
        for (String name : List.of("TEMP", "TMP", "TMPDIR", "RUNNER_TEMP", "XAR_DEADLINE_TEST_SCRATCH")) env.put(name, config.workRoot().resolve("scratch").toString());
        return Map.copyOf(env);
    }
    private static CommandEvidence command(Config config, Map<String, String> environment, Stage stage,
            List<String> arguments, Duration timeout) throws IOException, InterruptedException {
        requireCurrent(config); guardOutput(config.workRoot(), FINAL_METADATA_RESERVE);
        String label = stage.name().toLowerCase(java.util.Locale.ROOT);
        Path stdout = config.workRoot().resolve(label + ".stdout.log"), stderr = config.workRoot().resolve(label + ".stderr.log");
        WindowsJobProcess.CommandResult result;
        try (WindowsJobProcess process = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(config.pythonExecutable(), arguments,
                config.repoRoot(), environment, stdout, stderr, 1536L << 20))) {
            result = process.await(timeout, config.reviewAtUtc(), () -> {
                try { requireCurrent(config); guardOutput(config.workRoot(), FINAL_METADATA_RESERVE); }
                catch (IOException error) { throw new IllegalStateException(error); }
            });
        }
        return new CommandEvidence(stage, arguments, result, ControlBuild.FileRef.measure(stdout), ControlBuild.FileRef.measure(stderr));
    }
    private static void requireCommand(CommandEvidence command) throws IOException {
        if (command.result() == null || !command.result().passed()) throw new IOException("Actual " + command.stage() + " failed/timeout/nonempty Job: " + command.result());
    }
    private static String output(CommandEvidence command) throws IOException {
        return readText(Path.of(command.stdoutRef().path())) + readText(Path.of(command.stderrRef().path()));
    }
    private static void requireCurrent(Config config) throws IOException {
        if (!config.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(config.reviewAtUtc())) {
            throw new IOException("Fresh machine-bound supplemental CI lease required");
        }
    }

    public static ControlBuild.FileRef requireAccepted(Path receipt, String machineId) throws IOException {
        Actual actual = ControlBuild.strictMapper().readValue(readBytes(receipt), Actual.class);
        if (!SCHEMA.equals(actual.schema()) || actual.status() != Status.PASS || actual.error() != null
                || !machineId.equals(actual.machineId()) || !machineId.equals(WindowsJobProcess.currentMachineId())
                || !Instant.now().isBefore(Instant.parse(actual.reviewAtUtc())) || actual.sourcePostcheck() != ControlBuild.SourceState.MATCH
                || !actual.coreModules().equals(coreModules()) || !actual.supplementaryModules().equals(supplementaryModules())
                || !actual.wholeStaticModules().equals(wholeStaticModules()) || actual.commands().size() != Stage.values().length
                || !actual.commands().stream().map(CommandEvidence::stage).toList().equals(List.of(Stage.values()))
                || !actual.producerClosure().equals(ControlBuild.producerClosure()) || actual.junitRef() == null || actual.pytestCounts() == null
                || actual.sourceBeforeRef() == null || actual.sourceAfterRef() == null) throw new IOException("Complete successful supplemental actual required");
        Path work = receipt.toAbsolutePath().normalize().getParent();
        if (!receipt.getFileName().toString().equals("actual.json")) throw new IOException("Exact owned actual path required");
        SharedSourceFiles.plainAncestors(work); guardOutput(work);
        requirePath(actual.sourceBeforeRef(), work.resolve("sources-before.json")); requirePath(actual.sourceAfterRef(), work.resolve("sources-after.json"));
        requirePath(actual.junitRef(), work.resolve("pytest.xml"));
        if (!Path.of(actual.temporaryRoot()).toRealPath().equals(work.resolve("scratch").toRealPath())) throw new IOException("Exact owned Python scratch required");
        requireUnusedPycache(work);
        actual.pythonExecutableRef().verify(); for (var ref : actual.producerClosure()) ref.verify();
        actual.sourceBeforeRef().verify(); actual.sourceAfterRef().verify(); actual.junitRef().verify();
        SourceInventory before = readInventory(actual.sourceBeforeRef()), after = readInventory(actual.sourceAfterRef());
        if (!before.equals(after) || !before.equals(inventory(Path.of(actual.repoRoot()), Instant.parse(actual.reviewAtUtc())))) throw new IOException("Supplemental source closure differs");
        for (CommandEvidence evidence : actual.commands()) {
            requireCommand(evidence); evidence.stdoutRef().verify(); evidence.stderrRef().verify();
            String label = evidence.stage().name().toLowerCase(java.util.Locale.ROOT);
            requirePath(evidence.stdoutRef(), work.resolve(label + ".stdout.log")); requirePath(evidence.stderrRef(), work.resolve(label + ".stderr.log"));
            if (!Path.of(evidence.result().identity().executable()).toRealPath().equals(Path.of(actual.pythonExecutableRef().path()).toRealPath())) throw new IOException("Actual child executable differs from pinned Python");
        }
        if (!output(actual.commands().get(0)).trim().matches("Python 3\\.13\\.[0-9]+")
                || !output(actual.commands().get(1)).trim().matches("mypy 1\\.15\\.0(?: \\(.*\\))?")) {
            throw new IOException("Actual checked Python/mypy versions differ");
        }
        if (!evidence(actual, Stage.PYTHON_VERSION).arguments().equals(List.of("-V"))
                || !evidence(actual, Stage.MYPY_VERSION).arguments().equals(List.of("-B", "-m", "mypy", "--version"))
                || !evidence(actual, Stage.MYPY_DISTRIBUTION).arguments().equals(List.of("-B", "-m", "pip", "show", "--files", "mypy"))
                || !evidence(actual, Stage.PYTEST_VERSION).arguments().equals(List.of("-B", "-m", "pytest", "--version"))
                || !output(evidence(actual, Stage.PYTEST_VERSION)).trim().equals("pytest 9.1.1")
                || !evidence(actual, Stage.WHOLE_SEVEN_STATIC).arguments().equals(staticArguments())
                || !evidence(actual, Stage.CORE_34_AND_SUPPLEMENTAL_2).arguments().equals(pytestArguments(work.resolve("pytest.xml"), work.resolve("pytest-temp")))) {
            throw new IOException("Actual complete fixed command inventory differs");
        }
        List<ControlBuild.FileRef> engine = checkerSources(output(evidence(actual, Stage.MYPY_DISTRIBUTION)),
                actual.checkerSitePackages() == null ? null : Path.of(actual.checkerSitePackages()));
        if (engine.isEmpty() || !engine.equals(actual.checkerSourcePins()) || !engine.equals(actual.checkerSourcePostPins())) throw new IOException("Exact installed mypy engine differs before/after");
        if (!fixtureOutputs(work).equals(actual.fixtureOutputs())) throw new IOException("Complete fresh fixture output custody differs");
        PytestCounts counts = readPytest(Path.of(actual.junitRef().path()), Path.of(evidence(actual, Stage.CORE_34_AND_SUPPLEMENTAL_2).stdoutRef().path()), allRuntimeModules());
        if (!counts.equals(actual.pytestCounts())) throw new IOException("Actual parent/subtest counts differ");
        requirePassed(counts); return ControlBuild.FileRef.measure(receipt);
    }
    private static SourceInventory readInventory(ControlBuild.FileRef ref) throws IOException {
        return ControlBuild.strictMapper().readValue(readBytes(Path.of(ref.path())), SourceInventory.class);
    }

    /** Exact producer XML plus pytest summary; multiple failures stay attributed to their one parent. */
    static PytestCounts readPytest(Path xml, Path stdout, List<String> expectedModules) throws IOException {
        expectedModules.forEach(SupplementalFixtureCi::requireModule);
        Set<String> expected = new HashSet<>(expectedModules);
        if (expected.isEmpty() || expected.size() != expectedModules.size()) throw new IOException("Unique nonempty complete module inventory required");
        Summary summary = summary(readText(stdout));
        int tests = 0, parentCount = 0, failed = 0, errors = 0, skipped = 0, failureElements = 0, errorElements = 0, skippedElements = 0;
        Map<String, Integer> modules = new TreeMap<>(); Set<String> ids = new HashSet<>();
        try {
            var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
            factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            if (Files.size(xml) > METADATA_LIMIT) throw new IOException("Bounded pytest XML required");
            var document = factory.newDocumentBuilder().parse(xml.toFile());
            var suites = document.getElementsByTagName("testsuite");
            if (suites.getLength() < 1 || suites.getLength() > 64) throw new IOException("Actual pytest suites required");
            for (int i = 0; i < suites.getLength(); i++) {
                Element suite = (Element) suites.item(i);
                if (suite.getElementsByTagName("testsuite").getLength() != 0) throw new IOException("Nested duplicate pytest suite refused");
                int suiteFailures = count(suite, "failures"), suiteErrors = count(suite, "errors"), suiteSkipped = count(suite, "skipped");
                if (suiteFailures != suite.getElementsByTagName("failure").getLength() || suiteErrors != suite.getElementsByTagName("error").getLength()
                        || suiteSkipped != suite.getElementsByTagName("skipped").getLength()) throw new IOException("Actual XML outcome counters differ from bodies");
                tests = Math.addExact(tests, count(suite, "tests"));
                failureElements = Math.addExact(failureElements, suiteFailures); errorElements = Math.addExact(errorElements, suiteErrors);
                skippedElements = Math.addExact(skippedElements, suiteSkipped);
                var cases = suite.getElementsByTagName("testcase");
                for (int c = 0; c < cases.getLength(); c++) {
                    Element item = (Element) cases.item(c); parentCount++;
                    String classname = item.getAttribute("classname"), name = item.getAttribute("name");
                    if (classname.isBlank() || name.isBlank() || !ids.add(classname + "\n" + name)) throw new IOException("Unique actual parent identity required");
                    List<String> matches = expectedModules.stream().filter(path -> {
                        String stem = Path.of(path).getFileName().toString().replaceFirst("\\.py$", "");
                        return classname.equals(stem) || classname.startsWith(stem + ".") || classname.contains("." + stem + ".") || classname.endsWith("." + stem);
                    }).toList();
                    if (matches.size() != 1) throw new IOException("Actual parent is outside one selected complete module: " + classname);
                    modules.merge(matches.getFirst(), 1, Math::addExact);
                    boolean hasFailure = item.getElementsByTagName("failure").getLength() != 0;
                    boolean hasError = item.getElementsByTagName("error").getLength() != 0;
                    boolean hasSkipped = item.getElementsByTagName("skipped").getLength() != 0;
                    if (hasFailure && hasError) throw new IOException("Mixed parent failure/error requires explicit diagnosis");
                    if (hasFailure) failed++; if (hasError) errors++; if (hasSkipped) skipped++;
                }
            }
        } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException | NumberFormatException error) {
            throw new IOException("Invalid actual pytest XML", error);
        }
        int passed = summary.passed();
        int parentSkipped = parentCount - passed - failed - errors;
        int subSkipped = skippedElements - parentSkipped;
        if (parentSkipped < 0 || subSkipped < 0) throw new IOException("Parent/subtest skipped counts differ");
        bindFailureIdentities(readText(stdout), xml, expectedModules);
        if (!modules.keySet().equals(expected) || parentCount == 0 || summary.passed() != passed || summary.failed() != failureElements
                || summary.errors() != errorElements || summary.skipped() != skippedElements
                || summary.parentFailureLines() != failed || summary.subFailureLines() != failureElements - failed
                || summary.subSkipped() != 0 || summary.deselected() != 0 || summary.xfailed() != 0 || summary.xpassed() != 0
                || tests != parentCount + summary.subPassed() + summary.subFailureLines() + subSkipped) {
            throw new IOException("Actual JUnit/summary/parent/subtest/module counts differ");
        }
        List<ModuleCount> moduleCounts = expectedModules.stream().map(path -> new ModuleCount(path, modules.get(path))).toList();
        return new PytestCounts(tests, parentCount, passed, failed, errors, parentSkipped, summary.subPassed(), summary.subFailureLines(),
                subSkipped, summary.failed(), summary.errors(), moduleCounts);
    }
    private static void bindFailureIdentities(String output, Path xml, List<String> expectedModules) throws IOException {
        final org.w3c.dom.Document document;
        try {
            var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
            factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            document = factory.newDocumentBuilder().parse(xml.toFile());
        } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException error) { throw new IOException("Invalid actual pytest XML", error); }
        Set<String> rows = new HashSet<>(); Set<String> parents = new HashSet<>();
        for (String raw : output.lines().toList()) {
            boolean parent = raw.startsWith("FAILED "), child = raw.startsWith("SUBFAILED(") || raw.startsWith("SUBFAILED ") || raw.startsWith("SUBFAILED[");
            if (!parent && !child) continue;
            String line = raw.replace((char) 92, '/');
            if (!rows.add(line)) throw new IOException("Duplicate parent/subtest failure summary row");
            List<String> matches = expectedModules.stream().filter(module -> line.contains(" " + module + "::")).toList();
            if (matches.size() != 1) throw new IOException("Failure summary selects an unknown module");
            String module = matches.getFirst(), node = line.substring(line.indexOf(" " + module + "::") + 1).split(" - ", 2)[0];
            if (parent && !parents.add(node)) throw new IOException("Duplicate parent failure identity");
            String[] pieces = node.substring(module.length() + 2).split("::", 2);
            String name = pieces.length == 1 ? pieces[0] : pieces[1];
            String stem = Path.of(module).getFileName().toString().replaceFirst("\\.py$", ""); int found = 0;
            var cases = document.getElementsByTagName("testcase");
            for (int index = 0; index < cases.getLength(); index++) {
                Element item = (Element) cases.item(index); String cls = item.getAttribute("classname");
                if (item.getAttribute("name").equals(name) && (cls.equals(stem) || cls.startsWith(stem + ".") || cls.contains("." + stem + ".") || cls.endsWith("." + stem))
                        && (pieces.length == 1 || cls.endsWith("." + pieces[0])) && item.getElementsByTagName("failure").getLength() > 0) found++;
            }
            if (found != 1) throw new IOException("Failure summary does not identify exactly one failed XML parent");
        }
    }
    static void requirePassed(PytestCounts counts) throws IOException {
        if (counts.parentPassed() < 1 || counts.parentFailed() != 0 || counts.parentErrors() != 0 || counts.parentSkipped() != 0
                || counts.subtestsFailed() != 0 || counts.subtestsSkipped() != 0 || counts.aggregateFailed() != 0 || counts.aggregateErrors() != 0) {
            throw new IOException("Complete actual pytest group failed/empty/skipped: " + counts);
        }
    }
    private record Summary(int passed, int failed, int errors, int skipped, int subPassed, int subSkipped,
            int deselected, int xfailed, int xpassed, int parentFailureLines, int subFailureLines) {}
    private static Summary summary(String output) throws IOException {
        String duration = " in [0-9]{1,7}(?:\\.[0-9]{1,6})?s(?: \\([0-9]{1,3}:[0-5][0-9]:[0-5][0-9]\\))?(?: =+)?$";
        List<String> endings = output.lines().map(String::trim).filter(line -> line.matches("(?:=+ )?[0-9]+ .+" + duration)).toList();
        if (endings.size() != 1) throw new IOException("Exactly one actual pytest terminal summary required");
        var pretty = Pattern.compile(" in ([0-9]{1,7}(?:\\.[0-9]{1,6})?)s \\(([0-9]{1,3}):([0-5][0-9]):([0-5][0-9])\\)(?: =+)?$").matcher(endings.getFirst());
        if (pretty.find()) {
            double seconds = Double.parseDouble(pretty.group(1));
            long whole = Long.parseLong(pretty.group(2)) * 3600 + Long.parseLong(pretty.group(3)) * 60 + Long.parseLong(pretty.group(4));
            if (whole < 60 || seconds < whole || seconds > whole + 1.005) throw new IOException("Actual pytest elapsed representations differ");
        }
        String line = endings.getFirst().replaceFirst("^=+ ", "").replaceFirst(duration, "");
        Map<String, Integer> values = new TreeMap<>();
        Pattern token = Pattern.compile("([0-9]{1,7}) (passed|failed|errors?|skipped|subtests passed|subtests skipped|deselected|xfailed|xpassed|warnings?)");
        for (String part : line.split(", ")) {
            var match = token.matcher(part);
            if (!match.matches() || values.putIfAbsent(match.group(2).replace("errors", "error").replace("warnings", "warning"), Integer.parseInt(match.group(1))) != null) {
                throw new IOException("Unknown/duplicate actual pytest terminal count: " + part);
            }
        }
        int parentLines = Math.toIntExact(output.lines().filter(value -> value.startsWith("FAILED ")).count());
        int subLines = Math.toIntExact(output.lines().filter(value -> value.startsWith("SUBFAILED(") || value.startsWith("SUBFAILED ") || value.startsWith("SUBFAILED[")).count());
        return new Summary(values.getOrDefault("passed", 0), values.getOrDefault("failed", 0), values.getOrDefault("error", 0),
                values.getOrDefault("skipped", 0), values.getOrDefault("subtests passed", 0), values.getOrDefault("subtests skipped", 0),
                values.getOrDefault("deselected", 0), values.getOrDefault("xfailed", 0), values.getOrDefault("xpassed", 0), parentLines, subLines);
    }
    private static int count(Element item, String field) throws IOException {
        String value = item.getAttribute(field);
        if (!value.matches("[0-9]{1,7}")) throw new IOException("Exact bounded XML integer required: " + field);
        return Integer.parseInt(value);
    }
    private static SourceInventory inventory(Path root, Instant review) throws IOException {
        List<ControlBuild.FileRef> refs = new ArrayList<>();
        Instant limit = Instant.now().plusSeconds(120); if (review.isBefore(limit)) limit = review;
        final Instant deadline = limit; final int[] entries = {0};
        for (String relative : List.of("ck3_autonomous_player/src", "ck3_autonomous_player/tests")) {
            SharedSourceFiles.plainAncestors(root.resolve(relative));
            Files.walkFileTree(root.resolve(relative), new SimpleFileVisitor<Path>() {
                private void check(Path path) throws IOException {
                    if (++entries[0] > 100000 || !Instant.now().isBefore(deadline)) throw new IOException("Source inventory metadata/deadline bound exceeded");
                    SharedSourceFiles.plainAncestors(path);
                }
                @Override public FileVisitResult preVisitDirectory(Path path, BasicFileAttributes attributes) throws IOException {
                    check(path); return excludedSource(root.relativize(path)) ? FileVisitResult.SKIP_SUBTREE : FileVisitResult.CONTINUE;
                }
                @Override public FileVisitResult visitFile(Path path, BasicFileAttributes attributes) throws IOException {
                    check(path);
                    if (attributes.isRegularFile() && path.toString().endsWith(".py")) {
                        if (!path.toRealPath().startsWith(root.toRealPath())) throw new IOException("Outside source refused");
                        refs.add(ControlBuild.FileRef.measure(path.toRealPath()));
                        if (refs.size() > 20000) throw new IOException("Source inventory exceeds bounded CI profile");
                    }
                    return FileVisitResult.CONTINUE;
                }
            });
        }
        for (String name : List.of("ck3_autonomous_player/pyproject.toml", ".github/workflows/static-ci.yml", "pyproject.toml", "pytest.ini", "setup.cfg", "conftest.py")) {
            Path config = root.resolve(name); SharedSourceFiles.plainAncestors(config);
            if (Files.isRegularFile(config, LinkOption.NOFOLLOW_LINKS)) refs.add(ControlBuild.FileRef.measure(config.toRealPath()));
        }
        refs.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if (refs.stream().mapToLong(ControlBuild.FileRef::bytes).sum() > (512L << 20)) throw new IOException("Source inventory exceeds bounded CI profile");
        return new SourceInventory(INVENTORY_SCHEMA, refs);
    }
    private static boolean excludedSource(Path relative) {
        for (Path part : relative) if (Set.of(".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".git").contains(part.toString())) return true;
        return false;
    }
    private static CommandEvidence evidence(Actual actual, Stage stage) throws IOException {
        return actual.commands().stream().filter(row -> row.stage() == stage).findFirst().orElseThrow(() -> new IOException("Required actual command missing: " + stage));
    }
    /** A fresh cache namespace makes -B execute pinned source instead of ambient timestamp bytecode. */
    static void requireUnusedPycache(Path work) throws IOException {
        Path cache = work.resolve("scratch/pycache-no-read"); SharedSourceFiles.plainAncestors(cache);
        try {
            BasicFileAttributes attributes = Files.readAttributes(cache, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!attributes.isDirectory()) throw new IOException("Owned Python cache prefix must remain absent or empty");
            try (var entries = Files.list(cache)) {
                if (entries.findAny().isPresent()) throw new IOException("Python bytecode must not enter pinned source qualification");
            }
            SharedSourceFiles.plainAncestors(cache);
        } catch (java.nio.file.NoSuchFileException absent) { /* -B leaves the fresh namespace absent. */ }
    }
    private static void requirePath(ControlBuild.FileRef ref, Path expected) throws IOException {
        if (ref == null || !Path.of(ref.path()).toRealPath().equals(expected.toRealPath())) throw new IOException("Evidence is outside exact owned output: " + expected);
        SharedSourceFiles.plainAncestors(expected);
    }
    private static List<FixtureEvidence> fixtureOutputs(Path work) throws IOException {
        List<FixtureEvidence> outputs = new ArrayList<>();
        for (OutputSlot slot : outputSlots()) {
            Path file = work.resolve(slot.directory()).resolve("cases.json"); SharedSourceFiles.plainAncestors(file);
            if (!Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Actual fresh fixture output missing: " + slot.kind());
            outputs.add(new FixtureEvidence(slot.kind(), ControlBuild.FileRef.measure(file.toRealPath())));
        }
        return List.copyOf(outputs);
    }
    /** Existing pip metadata identifies the installed engine without an additional Python adapter. */
    static List<ControlBuild.FileRef> checkerSources(String metadata, Path explicitSite) throws IOException {
        List<String> lines = metadata.lines().toList();
        if (lines.stream().filter(line -> line.equals("Name: mypy")).count() != 1
                || lines.stream().filter(line -> line.equals("Version: 1.15.0")).count() != 1) throw new IOException("Exact installed mypy distribution required");
        List<String> locations = lines.stream().filter(line -> line.startsWith("Location: ")).map(line -> line.substring(10).trim()).toList();
        if (locations.size() != 1 || !Path.of(locations.getFirst()).isAbsolute()) throw new IOException("Explicit installed checker location required");
        Path site = Path.of(locations.getFirst()).toRealPath(); SharedSourceFiles.plainAncestors(site);
        if (explicitSite != null && !site.equals(explicitSite.toRealPath())) throw new IOException("Actual mypy distribution differs from explicit checker site");
        int files = lines.indexOf("Files:"); if (files < 0) throw new IOException("Actual installed checker file list required");
        List<ControlBuild.FileRef> refs = new ArrayList<>(); Set<String> paths = new HashSet<>(); Instant stop = Instant.now().plusSeconds(120);
        for (String line : lines.subList(files + 1, lines.size())) {
            String relative = line.trim().replace((char) 92, '/');
            if (!(relative.startsWith("mypy/") || relative.startsWith("mypy-1.15.0.dist-info/")
                    || relative.matches("[A-Za-z0-9_]+_mypyc[.][A-Za-z0-9_.-]+[.]pyd")) || relative.contains("__pycache__") || relative.endsWith(".pyc")) continue;
            if (refs.size() >= 10000 || !Instant.now().isBefore(stop)) throw new IOException("Exact checker metadata/deadline bound exceeded");
            Path path = site.resolve(relative).normalize();
            if (!path.startsWith(site) || !paths.add(path.toString())) throw new IOException("Duplicate/outside exact checker source");
            SharedSourceFiles.plainAncestors(path); refs.add(ControlBuild.FileRef.measure(path.toRealPath()));
        }
        for (String file : List.of("mypy/__main__.py", "mypy/main.py", "mypy/build.py")) {
            if (!paths.contains(site.resolve(file).toString())) throw new IOException("Actual checker engine entry source missing: " + file);
        }
        refs.sort(Comparator.comparing(ControlBuild.FileRef::path)); return List.copyOf(refs);
    }
    private static byte[] readBytes(Path path) throws IOException {
        if (!Files.isRegularFile(path) || Files.size(path) > METADATA_LIMIT) throw new IOException("Bounded CI metadata required");
        return Files.readAllBytes(path);
    }
    private static String readText(Path path) throws IOException { return new String(readBytes(path), StandardCharsets.UTF_8); }
    private static void write(Path path, Record value) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value);
        if (bytes.length > METADATA_LIMIT) throw new IOException("Bounded CI metadata required");
        if (value instanceof Actual actual) {
            if (bytes.length > (1 << 20)) throw new IOException("Bounded final command evidence required");
            try { guardOutput(path.getParent(), bytes.length); }
            catch (IOException limit) {
                var node = ControlBuild.strictMapper().valueToTree(actual);
                if (!(node instanceof com.fasterxml.jackson.databind.node.ObjectNode row)) throw new IOException("Actual object required");
                row.put("status", Status.RED.name()); row.put("error", append(actual.error(), "Final output guard: " + limit.getMessage()));
                Actual red = ControlBuild.strictMapper().treeToValue(row, Actual.class);
                bytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(red);
            }
            if (bytes.length > (1 << 20)) throw new IOException("Bounded final RED command evidence required");
            try { SharedSourceFiles.plainAncestors(path); guardOutput(path.getParent(), bytes.length); }
            catch (IOException unavailable) {
                System.err.println(new String(bytes, StandardCharsets.UTF_8)); throw unavailable;
            }
        } else guardOutput(path.getParent(), Math.addExact(bytes.length, FINAL_METADATA_RESERVE));
        SharedSourceFiles.plainAncestors(path);
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
    }
    private static String append(String current, String next) { return current == null ? next : current + "; " + next; }
    private static void guardOutput(Path root) throws IOException { guardOutput(root, 0); }
    private static void guardOutput(Path root, long additionalBytes) throws IOException {
        final long[] total = {additionalBytes}; final int[] entries = {0}; Instant stop = Instant.now().plusSeconds(120);
        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            private void check(Path path) throws IOException {
                if (++entries[0] > 100000 || !Instant.now().isBefore(stop)) throw new IOException("Output inventory metadata/deadline bound exceeded");
                SharedSourceFiles.plainAncestors(path);
            }
            @Override public FileVisitResult preVisitDirectory(Path path, BasicFileAttributes attributes) throws IOException {
                check(path); return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFile(Path path, BasicFileAttributes attributes) throws IOException {
                check(path); if (attributes.isRegularFile()) total[0] = Math.addExact(total[0], attributes.size());
                if (total[0] > OUTPUT_LIMIT) throw new IOException("Supplemental CI output budget exceeded");
                return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFileFailed(Path path, IOException error) throws IOException {
                if (error instanceof java.nio.file.NoSuchFileException) return FileVisitResult.CONTINUE;
                throw error;
            }
        });
        if (total[0] > OUTPUT_LIMIT) throw new IOException("Supplemental CI output budget exceeded");
    }
    /** A finite caller of the same shared producer; the launching owner supplies its execution resource card. */
    public static void main(String[] arguments) throws IOException, InterruptedException {
        System.out.println("SUPPLEMENTAL_FIXTURE_ACCEPTED " + run(parseArguments(arguments)));
    }
    static Config parseArguments(String[] arguments) throws IOException {
        Set<String> required = Set.of("--repo-root", "--work-root", "--python-executable", "--temporary-root", "--review-at-utc", "--machine-id");
        Set<String> allowed = new HashSet<>(required); allowed.add("--checker-site-packages");
        if (arguments.length != required.size() * 2 && arguments.length != allowed.size() * 2) throw new IOException("Exact finite supplemental CI arguments required");
        Map<String, String> values = new TreeMap<>();
        for (int index = 0; index < arguments.length; index += 2) {
            if (!allowed.contains(arguments[index]) || arguments[index + 1].isBlank()
                    || values.putIfAbsent(arguments[index], arguments[index + 1]) != null) throw new IOException("Unknown/empty/duplicate supplemental argument");
        }
        if (!values.keySet().containsAll(required)) throw new IOException("All supplemental CI arguments required");
        for (String key : List.of("--repo-root", "--work-root", "--python-executable", "--temporary-root")) {
            if (!Path.of(values.get(key)).isAbsolute()) throw new IOException("Absolute supplemental CI path required: " + key);
            SharedSourceFiles.plainAncestors(Path.of(values.get(key)));
        }
        if (values.containsKey("--checker-site-packages") && !Path.of(values.get("--checker-site-packages")).isAbsolute()) throw new IOException("Absolute explicit checker site required");
        if (values.containsKey("--checker-site-packages")) SharedSourceFiles.plainAncestors(Path.of(values.get("--checker-site-packages")));
        return new Config(Path.of(values.get("--repo-root")).toRealPath(), Path.of(values.get("--work-root")).toAbsolutePath().normalize(),
                Path.of(values.get("--python-executable")).toRealPath(), Path.of(values.get("--temporary-root")).toRealPath(),
                Instant.parse(values.get("--review-at-utc")), values.get("--machine-id"),
                values.containsKey("--checker-site-packages") ? Path.of(values.get("--checker-site-packages")).toRealPath() : null);
    }
}
