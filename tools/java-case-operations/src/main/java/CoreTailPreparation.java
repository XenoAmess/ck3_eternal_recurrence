import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.OpinionInspection;
import org.xar.ck3.save.SaveContracts;
import org.xar.ck3.save.SaveContracts.NativeId;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveContracts.ScopeKind;
import org.xar.ck3.save.SaveContracts.Selection;
import org.xar.ck3.save.SaveContracts.TableSelection;

/** External operation preparation only. The frozen queue, CaseClient and Save reader own all business. */
public final class CoreTailPreparation {
    public record Binding(int schemaVersion, String machineId, String sourceHead,
                          @com.fasterxml.jackson.databind.annotation.JsonSerialize(using = PlainPathSerializer.class) Path base,
                          @com.fasterxml.jackson.databind.annotation.JsonSerialize(using = PlainPathSerializer.class) Path runtimeRoot,
                          @com.fasterxml.jackson.databind.annotation.JsonSerialize(using = PlainPathSerializer.class) Path ownRoot,
                          Pin sourceAuthority, Pin sourceFacts) {
        public Binding {
            need(schemaVersion == 1, "binding schemaVersion1 required");
            need(machineId != null && machineId.matches("[a-z0-9-]+"), "explicit machine ID required");
            need(sourceHead != null && sourceHead.matches("[0-9a-f]{40}"), "exact source Git SHA required");
            for (Path path : List.of(base, runtimeRoot, ownRoot))
                need(path.isAbsolute() && path.normalize().equals(path), "absolute normalized binding root required");
            need(!runtimeRoot.equals(base) && runtimeRoot.startsWith(base)
                    && !ownRoot.equals(base) && ownRoot.startsWith(base), "binding runtime/output roots within explicit base");
            Objects.requireNonNull(sourceAuthority, "adopted source authority Pin required");
            Objects.requireNonNull(sourceFacts, "actual source facts Pin required");
        }
    }
    public static final class PlainPathSerializer extends com.fasterxml.jackson.databind.JsonSerializer<Path> {
        @Override public void serialize(Path value, com.fasterxml.jackson.core.JsonGenerator output,
                                        com.fasterxml.jackson.databind.SerializerProvider provider) throws IOException {
            output.writeString(value.toString());
        }
    }
    private final Binding binding;
    private final String MACHINE, HEAD;
    private final Path BASE, A20, ADMIN, RUNTIME, OWN;
    private static final long SAVE_PEAK = 230686720L;
    private static final ObjectMapper JSON = JsonMapper.builder()
            .disable(MapperFeature.ALLOW_COERCION_OF_SCALARS)
            .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT)
            .enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .addModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            .enable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
            .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES).build();
    private CoreTailPreparation(Binding value) {
        binding = Objects.requireNonNull(value);
        MACHINE = value.machineId(); HEAD = value.sourceHead(); BASE = value.base();
        A20 = BASE.resolve("resume-product-a20"); ADMIN = A20.resolve("core-a30-administration");
        RUNTIME = value.runtimeRoot(); OWN = value.ownRoot();
    }
    public Binding binding() { return binding; }
    public static CoreTailPreparation open(Path path) throws Exception {
        CoreTailPreparation engine = new CoreTailPreparation(readBinding(path));
        engine.validateBinding();
        return engine;
    }
    static Binding readBinding(Path path) throws Exception {
        JsonNode value = read(path, 65536);
        Set<String> expected = Set.of("schemaVersion", "machineId", "sourceHead", "base", "runtimeRoot", "ownRoot", "sourceAuthority", "sourceFacts");
        Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        need(value.isObject() && actual.equals(expected), "exact binding fields required");
        long version = integer(value, "schemaVersion"); need(version == 1, "binding version1");
        return new Binding((int) version, text(value, "machineId"), text(value, "sourceHead"),
                Path.of(text(value, "base")), Path.of(text(value, "runtimeRoot")), Path.of(text(value, "ownRoot")),
                capacityAuthority(value.get("sourceAuthority")), capacityAuthority(value.get("sourceFacts")));
    }
    private void validateBinding() throws Exception {
        for (Path path : List.of(BASE, RUNTIME, OWN))
            need(Files.isDirectory(path) && path.toRealPath().equals(path), "actual ordinary resolved binding roots required");
        checkedPin(binding.sourceAuthority()); checkedPin(binding.sourceFacts());
        JsonNode runtime = read(RUNTIME.resolve("runtime.json"), 8L * 1024 * 1024);
        need(MACHINE.equals(text(runtime, "machine_id"))
                && Path.of(text(runtime.path("paths"), "source_root")).equals(RUNTIME.resolve("source"))
                && Path.of(text(runtime, "repo_root")).equals(BASE.resolve("main12"))
                && Path.of(text(runtime, "artifacts_root")).equals(RUNTIME.resolve("runs")),
                "actual runtime belongs to explicit machine/root binding");
        checkedPin(capacityAuthority(runtime.get("manifest")));
        JsonNode authority = read(Path.of(binding.sourceAuthority().path()), 512 * 1024);
        need(MACHINE.equals(text(authority, "machine_id")) && HEAD.equals(text(authority, "source_HEAD"))
                && yes(authority, "passed"), "source authority must match configured machine/source");
        Pin qualification = capacityAuthority(authority.get("source_continuation_build_code_qualification"));
        checkedPin(qualification);
        SharedSourceCapacity.consumeFacts(MACHINE, HEAD, binding.sourceFacts(), qualification,
                Path.of(qualification.path()).getParent().resolve("facts-consumer-" + java.util.UUID.randomUUID()));
    }

    public enum Stage {
        CREATE_PREPARE_CONFIRMATION, CREATE_CONFIRM_ONCE, CREATE_COLLECT_ORIGINAL, CREATE_VERIFY_ORIGINAL,
        BIRTH_SAVE, BIRTH_PLUS24_SAVE, PIN_ORIGINAL_HEIR, HEIR_PREPARE, HEIR_SETTLED_SAVE, HEIR_READBACK,
        OLD_EDIT_INPUT_PREPARE, OLD_EDIT_INPUT_SAVE, OLD_EDIT_INPUT_READBACK, OLD_EDIT_OPEN_SELECT,
        OLD_EDIT_PREPARE_CONFIRMATION, OLD_EDIT_CONFIRM_ONCE, EVENT_OBSERVE, EVENT_FIRST_OPTION,
        EDIT_COLLECT_ORIGINAL, EDIT_VERIFY_ORIGINAL, OLD_CLOSED_READBACK, OLD_CLOSED_SAVE,
        PRIMARY_DEATH_STAGE, PRIMARY_INHERIT_ONE_DAY, SUCCESSOR_OBSERVE_SAVE, SUCCESSOR_READBACK,
        NEW_EDIT_INPUT_PREPARE, NEW_EDIT_INPUT_SAVE, NEW_EDIT_INPUT_READBACK, NEW_EDIT_OPEN_SELECT,
        NEW_EDIT_PREPARE_CONFIRMATION, NEW_EDIT_CONFIRM_ONCE, NEW_REOPENED_READBACK,
        PARDON_PREPARE, PARDON_CANDIDATE_SAVE, PARDON_QUERY, PARDON_INITIATE_ONCE,
        PARDON_OBSERVE, PARDON_CONSUMED_SAVE, PARDON_PLUS31_SAVE, COLD_ANCHOR, FINAL_SAVE
    }
    public enum Gate {
        ACTUAL_BIRTH_NATIVE, BIRTH_NATIVE_SAVE_CONSUMED,
        ALL_BIRTH_SHORT_TIMER_FOUNDER_CRIME_PROOFS, HEIR_SETTLED_NATIVE_SAVE,
        OLD_EDIT_INPUT_NATIVE_SAVE, OLD_CLOSED_NATIVE_SAVE,
        SUCCESSOR_NATIVE_SAVE, NEW_EDIT_INPUT_NATIVE_SAVE,
        ORIGINAL_EDIT_VERIFIED, EVENT_POLICY_RECORDED,
        PARDON_CANDIDATE_NATIVE_SAVE, PARDON_ACTUAL_POSTSTATE,
        PARDON_CONSUMED_NATIVE_SAVE, PARDON_PLUS31_NATIVE_SAVE, COLD_ANCHOR_OBSERVED
    }
    public record Frame(long actorId, long dateRaw, long revision, long nativeRevision,
                        long bridgePid, long connectionGeneration, String managedRunId) { }
    public record Ids(Long predecessor, Long heir, Long originalTitle, Long rite, Long faith, Long target) { }
    public record Anchors(Long birthDateRaw, Long pardonObserveDateRaw) { }
    public record Action(String observationStepId, String previewIdentity, String actionRequestId) { }
    public record Capacity(Pin fresh, Pin originalWait, Pin authority) { }
    public record Input(int schemaVersion, String machineId, String sourceHead, String runId,
                        Stage stage, String prefix, String live, Frame currentFrame, Ids ids,
                        Anchors anchors, Action action, Pin rootReview, Capacity capacity) { }
    public record RootReview(int schemaVersion, String machine_id, String source_HEAD, String run_id,
                             String reviewer, Stage forStage, List<Gate> gates, List<Pin> evidence,
                             String scope_note) { }
    public enum EarlyDecision {
        CAPTURE_CREATED("des_acceptance_capture_created_decision"),
        HEAD_CELLS("des_acceptance_head_cells_decision"),
        SAME_FAITH("des_acceptance_same_faith_decision"),
        PRISON_CONTROL("des_acceptance_prisoner_control_decision"),
        CROSS_FAITH("des_acceptance_cross_faith_decision"), REPENT("des_acceptance_repent_decision"),
        EXTENDED_START("des_acceptance_extended_start_decision"), SECOND_RITE("des_acceptance_second_rite_decision"),
        FOUNDER_DEATH("des_acceptance_founder_death_decision"), CROSS_RITES("des_acceptance_cross_rites_decision"),
        CROSS_MIGRATION("des_acceptance_cross_migration_decision"), STOCK_CRIME_PREPARE("des_acceptance_stock_crime_prepare_decision"),
        STOCK_CRIME("des_acceptance_stock_crime_decision"), STOCK_REPENT("des_acceptance_stock_repent_decision");
        private final String key;
        EarlyDecision(String key) { this.key = key; }
        public String key() { return key; }
    }
    public record EarlyInput(Input binding, EarlyDecision decision, int expectedPriorSubmissions) { }
    public enum ArgumentField {
        faith_id, expected_source_rite_id, recipient_id, title_id, requested_title_id,
        release_material_target_character_id, expected_preview_identity, action_request_id;
        public boolean numeric() { return this != expected_preview_identity && this != action_request_id; }
    }
    public record ArgumentBinding(ArgumentField field, Long integerValue, String textValue) { }
    public record DonorInput(Input binding, Pin donorPlan, List<ArgumentBinding> arguments) { }
    public record DonorPrepared(String schema, String machine_id, String source_HEAD, String run_id,
                                Pin input, Pin donor_plan, Pin generated_plan, String scope,
                                boolean game_started, boolean business_pass) { }
    public record DonorEntry(Pin originalPlan, List<ArgumentField> requiredDynamicFields, boolean save,
                              String scope) { }
    public record DonorIndex(String schema, String machine_id, String source_HEAD, List<DonorEntry> plans,
                              String scope) { }
    public sealed interface Arguments permits Empty, Title, Faith, Window, Decision, ConfirmDecision,
            RiteQuery, RiteWrite, EventQuery, EventSelect, Ordinary, Collect, Verify { }
    public record Empty() implements Arguments { }
    public record Title(long title_id) implements Arguments { }
    public record Faith(long faith_id) implements Arguments { }
    public record Window(String window_kind) implements Arguments { }
    public record Decision(String decision_key) implements Arguments { }
    public record ConfirmDecision(String decision_key, String expected_outcome) implements Arguments { }
    public record RiteQuery(long expected_source_rite_id, String observation) implements Arguments { }
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record RiteWrite(String operation, long expected_source_rite_id, String group_key,
                             String doctrine_key, String expected_preview_identity,
                             String expected_outcome_kind) implements Arguments { }
    public record EventQuery(long event_instance_id) implements Arguments { }
    public record EventSelect(long event_instance_id, int option_number) implements Arguments { }
    public record Ordinary(String interaction_key, long recipient_id) implements Arguments { }
    public record Collect(String action_request_id, double timeout_seconds) implements Arguments { }
    public record Verify(String action_request_id) implements Arguments { }
    public sealed interface Step permits Tool, Day { String id(); }
    public record Tool(String id, String tool, Arguments args, boolean fresh_revision) implements Step { }
    public record Day(String id, String kind, int days, int timeout,
                      boolean allow_event_boundary, boolean allow_actor_change) implements Step { }
    /** Queue's real parser requires exactly one top-level key, steps. Metadata lives in companion. */
    public record Plan(List<Step> steps) { public Plan { steps = List.copyOf(steps); } }
    public record Materialized(String schema, String machine_id, String source_HEAD, String run_id,
                                Instant observed_at_utc, Stage stage, Pin input, Pin native_report,
                                Pin plan, List<String> existing_queue_argv, List<Gate> review_gates,
                                String scope, boolean game_started, boolean business_pass) { }
    public enum ActorPath {
        LIVING, DEAD_UNPRUNABLE, DEAD_PRUNABLE;
        public List<String> segments() { return switch (this) {
            case LIVING -> List.of("living");
            case DEAD_UNPRUNABLE -> List.of("dead_unprunable");
            case DEAD_PRUNABLE -> List.of("characters", "dead_prunable");
        }; }
    }
    public record SelectedInput(int schemaVersion, RetainedSaveOperator20261027.RunBinding binding,
                                RetainedSaveOperator20261027.Retained retained, Pin operatorProof,
                                ActorPath actorPath, List<NativeId> actors, boolean actorsRequired,
                                List<NativeId> rites, List<NativeId> dynasties, List<NativeId> houses,
                                List<NativeId> titles, boolean metadataRequired) { }
    public record OpinionsInput(int schemaVersion, RetainedSaveOperator20261027.RunBinding binding,
                                RetainedSaveOperator20261027.Retained retained, Pin operatorProof,
                                RetainedSaveOperator20261027.References references,
                                List<OpinionInspection.Pair> pairs) { }
    public record ReaderOutput(String schema, String machine_id, String source_HEAD, String run_id,
                               Pin input, Pin operator_input, String scope, boolean decoder_started,
                               boolean business_pass) { }
    public record StageRow(Stage stage, List<Gate> requiredRootReview, String resultDependency,
                            String next, boolean save, String exactDate) { }
    public record Catalog(String schema, String machine_id, String source_HEAD, List<StageRow> stages,
                           List<String> requirements, String scope) { }
    public record ProcessWait(String schema, String machine_id, String source_HEAD, List<String> argv,
                               String cwd, Instant started_at_utc, Instant finished_at_utc,
                               boolean actual_original_Process_waitFor, int exit_code,
                               boolean timed_out, Pin stdout, Pin stderr) { }
    public record SchemaFixtures(String machine_id, String source_HEAD, String scope, List<Plan> plans, List<JsonNode> donorPlans) { }
    public record Templates(String schema, String machine_id, String source_HEAD, String scope,
                             JsonNode materializeInput, JsonNode rootReview, JsonNode selectedInput,
                             JsonNode opinionsInput, JsonNode earlyInput, JsonNode donorInput) { }
    public record RealNativeRegression(String schema, String machine_id, String source_HEAD, Instant observed_at_utc,
                                        Pin original_native_evidence, Frame extracted_actual_frame,
                                        List<Pin> original_pre_post_sources, Ids actual_precreation_ids, long actual_new_primary_rite,
                                        List<String> checks, Pin existing_queue_original_wait,
                                        String scope, boolean game_started, boolean business_pass) { }
    public record FrameInputReceipt(String schema, String machine_id, String source_HEAD, String run_id,
                                     Pin native_report, Pin frame_input, String scope) { }
    public record Tests(String schema, String machine_id, String source_HEAD, Instant observed_at_utc,
                         int positiveStages, List<String> negativeAndContractChecks,
                         Pin compatibilityWait, boolean game_started, boolean decoder_started,
                         boolean business_pass) { }

    private static void need(boolean value, String message) { if (!value) throw new IllegalArgumentException(message); }
    private static JsonNode read(Path path, long cap) throws IOException {
        need(Files.size(path) <= cap, "bounded JSON input required");
        return JSON.readTree(Files.readAllBytes(path));
    }
    private static Pin pin(Path path) throws Exception {
        return new Pin(path.toAbsolutePath().toString(), Files.size(path),
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
    }
    private static void checkedPin(Pin value) throws Exception { need(value != null && value.equals(pin(Path.of(value.path()))), "exact input pin changed"); }
    private static void writeNew(Path path, Object value) throws Exception {
        byte[] bytes = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(value);
        need(bytes.length <= 128 * 1024, "bounded preparation output required");
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }
    private static long integer(JsonNode node, String key) {
        JsonNode value = node.path(key);
        need(value.isIntegralNumber() && value.canConvertToLong(), "literal integral field required: " + key);
        return value.longValue();
    }
    private static String text(JsonNode node, String key) {
        JsonNode value = node.path(key); need(value.isTextual() && !value.textValue().isBlank(), "text required: " + key); return value.textValue();
    }
    private boolean yes(JsonNode node, String key) { return node.path(key).isBoolean() && node.path(key).booleanValue(); }
    private boolean no(JsonNode node, String key) { return node.path(key).isBoolean() && !node.path(key).booleanValue(); }
    private boolean absent(JsonNode node, String key) { return node.path(key).isMissingNode() || node.path(key).isNull(); }
    private JsonNode latest(JsonNode report) {
        JsonNode steps = report.path("steps"); need(steps.isArray(), "report steps array required");
        for (int index = steps.size() - 1; index >= 0; index--) {
            JsonNode row = steps.get(index);
            if (!absent(row, "finished_at") && yes(row, "ok") && !absent(row, "after_snapshot")) return row.path("after_snapshot");
        }
        return report.path("readiness");
    }
    private boolean permitsEvent(Stage stage) { return stage == Stage.EVENT_OBSERVE || stage == Stage.EVENT_FIRST_OPTION; }
    private boolean isSave(Stage stage) { return switch (stage) {
        case BIRTH_SAVE, BIRTH_PLUS24_SAVE, HEIR_SETTLED_SAVE, OLD_EDIT_INPUT_SAVE, NEW_EDIT_INPUT_SAVE,
                OLD_CLOSED_SAVE, SUCCESSOR_OBSERVE_SAVE,
                PARDON_CANDIDATE_SAVE, PARDON_CONSUMED_SAVE, PARDON_PLUS31_SAVE, FINAL_SAVE -> true;
        default -> false;
    }; }
    private List<Gate> gates(Stage stage) { return switch (stage) {
        case BIRTH_SAVE -> List.of(Gate.ACTUAL_BIRTH_NATIVE);
        case BIRTH_PLUS24_SAVE -> List.of(Gate.BIRTH_NATIVE_SAVE_CONSUMED);
        case HEIR_PREPARE -> List.of(Gate.ALL_BIRTH_SHORT_TIMER_FOUNDER_CRIME_PROOFS);
        case HEIR_READBACK, OLD_EDIT_INPUT_PREPARE -> List.of(Gate.HEIR_SETTLED_NATIVE_SAVE);
        case OLD_EDIT_INPUT_READBACK, OLD_EDIT_OPEN_SELECT -> List.of(Gate.OLD_EDIT_INPUT_NATIVE_SAVE);
        case OLD_CLOSED_READBACK, NEW_REOPENED_READBACK -> List.of(Gate.ORIGINAL_EDIT_VERIFIED);
        case PRIMARY_DEATH_STAGE, PRIMARY_INHERIT_ONE_DAY -> List.of(Gate.OLD_CLOSED_NATIVE_SAVE);
        case SUCCESSOR_READBACK, NEW_EDIT_INPUT_PREPARE -> List.of(Gate.SUCCESSOR_NATIVE_SAVE);
        case NEW_EDIT_INPUT_READBACK, NEW_EDIT_OPEN_SELECT -> List.of(Gate.NEW_EDIT_INPUT_NATIVE_SAVE);
        case EVENT_FIRST_OPTION -> List.of(Gate.EVENT_POLICY_RECORDED);
        case PARDON_PREPARE, PARDON_QUERY -> List.of(Gate.ORIGINAL_EDIT_VERIFIED);
        case PARDON_INITIATE_ONCE -> List.of(Gate.PARDON_CANDIDATE_NATIVE_SAVE);
        case PARDON_OBSERVE -> List.of(Gate.PARDON_ACTUAL_POSTSTATE);
        case PARDON_PLUS31_SAVE -> List.of(Gate.PARDON_CONSUMED_NATIVE_SAVE);
        case COLD_ANCHOR -> List.of(Gate.PARDON_PLUS31_NATIVE_SAVE);
        case FINAL_SAVE -> List.of(Gate.COLD_ANCHOR_OBSERVED);
        default -> List.of();
    }; }
    private String fixtureKey(Stage stage) { return switch (stage) {
        case HEIR_PREPARE -> "des_acceptance_primary_heir_prepare_decision";
        case HEIR_READBACK -> "des_acceptance_primary_heir_readback_decision";
        case OLD_EDIT_INPUT_PREPARE, NEW_EDIT_INPUT_PREPARE -> "des_acceptance_edit_input_prepare_decision";
        case OLD_EDIT_INPUT_READBACK, NEW_EDIT_INPUT_READBACK -> "des_acceptance_edit_input_readback_decision";
        case OLD_CLOSED_READBACK -> "des_acceptance_closed_readback_decision";
        case PRIMARY_DEATH_STAGE -> "des_acceptance_primary_death_stage_decision";
        case SUCCESSOR_READBACK -> "des_acceptance_successor_readback_decision";
        case NEW_REOPENED_READBACK -> "des_acceptance_reopened_readback_decision";
        case PARDON_PREPARE -> "des_acceptance_pardon_prepare_decision";
        case PARDON_OBSERVE -> "des_acceptance_pardon_observe_decision";
        case COLD_ANCHOR -> "des_acceptance_cold_anchor_decision";
        default -> null;
    }; }
    private boolean oldActor(Stage stage) { return switch (stage) {
        case CREATE_PREPARE_CONFIRMATION, CREATE_CONFIRM_ONCE, CREATE_COLLECT_ORIGINAL, CREATE_VERIFY_ORIGINAL,
                PIN_ORIGINAL_HEIR, HEIR_PREPARE, HEIR_SETTLED_SAVE, HEIR_READBACK, OLD_EDIT_INPUT_PREPARE, OLD_EDIT_INPUT_SAVE,
                OLD_EDIT_INPUT_READBACK, OLD_EDIT_OPEN_SELECT, OLD_EDIT_PREPARE_CONFIRMATION,
                OLD_EDIT_CONFIRM_ONCE, OLD_CLOSED_READBACK, OLD_CLOSED_SAVE,
                PRIMARY_DEATH_STAGE, PRIMARY_INHERIT_ONE_DAY -> true;
        default -> false;
    }; }
    private boolean newActor(Stage stage) { return switch (stage) {
        case SUCCESSOR_OBSERVE_SAVE, SUCCESSOR_READBACK, NEW_EDIT_INPUT_PREPARE, NEW_EDIT_INPUT_SAVE,
                NEW_EDIT_INPUT_READBACK, NEW_EDIT_OPEN_SELECT, NEW_EDIT_PREPARE_CONFIRMATION,
                NEW_EDIT_CONFIRM_ONCE, NEW_REOPENED_READBACK, PARDON_PREPARE,
                PARDON_CANDIDATE_SAVE, PARDON_QUERY, PARDON_INITIATE_ONCE, PARDON_OBSERVE,
                PARDON_CONSUMED_SAVE, PARDON_PLUS31_SAVE, COLD_ANCHOR, FINAL_SAVE -> true;
        default -> false;
    }; }
    private void validate(Input input, JsonNode report) {
        need(input.schemaVersion() == 1 && MACHINE.equals(input.machineId()) && HEAD.equals(input.sourceHead()), "exact preparation machine/source/version required");
        need(input.stage() != null && input.prefix() != null && input.prefix().matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,100}"), "explicit unused prefix required");
        need(input.live() != null && Path.of(input.live()).isAbsolute() && Path.of(input.live()).getFileName().toString().equals(input.runId()), "actual absolute run path required");
        need(Path.of(input.live()).toAbsolutePath().normalize().getParent().equals(RUNTIME.resolve("runs").toAbsolutePath().normalize()), "actual run must belong to explicit bound runtime");
        need(input.runId().matches(MACHINE + "--dynastic-esotericism--R[0-9]{4,8}"), "allocated same-machine Core run ID required");
        Frame expect = Objects.requireNonNull(input.currentFrame()); Ids ids = Objects.requireNonNull(input.ids());
        need(expect.actorId() > 0 && expect.dateRaw() > 0 && expect.revision() > 0 && expect.nativeRevision() > 0 && expect.bridgePid() > 0 && expect.connectionGeneration() > 0, "strict positive frame required");
        id(ids.predecessor(), false, "actual predecessor", true);
        id(ids.heir(), false, "heir", false); id(ids.originalTitle(), false, "original title", false);
        id(ids.faith(), false, "faith", false); id(ids.target(), false, "target", false); id(ids.rite(), true, "Rite", false);
        need(ids.heir() == null || !ids.predecessor().equals(ids.heir()), "distinct original predecessor/heir required");
        if (newActor(input.stage())) id(ids.heir(), false, "actual pinned successor", true);
        if (isSave(input.stage()) || input.stage() == Stage.HEIR_PREPARE || input.stage() == Stage.HEIR_READBACK || input.stage() == Stage.PRIMARY_DEATH_STAGE || input.stage() == Stage.PRIMARY_INHERIT_ONE_DAY) {
            id(ids.originalTitle(), false, "pinned original title", true); id(ids.rite(), true, "actual Rite", true);
        }
        if (Set.of(Stage.HEIR_PREPARE, Stage.HEIR_READBACK, Stage.PRIMARY_DEATH_STAGE, Stage.PRIMARY_INHERIT_ONE_DAY).contains(input.stage())) id(ids.heir(), false, "pinned original heir", true);
        if (Set.of(Stage.OLD_EDIT_OPEN_SELECT, Stage.NEW_EDIT_OPEN_SELECT).contains(input.stage())) id(ids.faith(), false, "actual Faith", true);
        if (Set.of(Stage.OLD_EDIT_OPEN_SELECT, Stage.NEW_EDIT_OPEN_SELECT, Stage.OLD_EDIT_PREPARE_CONFIRMATION, Stage.NEW_EDIT_PREPARE_CONFIRMATION,
                Stage.OLD_EDIT_CONFIRM_ONCE, Stage.NEW_EDIT_CONFIRM_ONCE, Stage.EDIT_COLLECT_ORIGINAL, Stage.EDIT_VERIFY_ORIGINAL,
                Stage.CREATE_PREPARE_CONFIRMATION, Stage.CREATE_CONFIRM_ONCE, Stage.CREATE_COLLECT_ORIGINAL, Stage.CREATE_VERIFY_ORIGINAL).contains(input.stage())) id(ids.rite(), true, "actual source Rite", true);
        if (input.stage() == Stage.PARDON_QUERY || input.stage() == Stage.PARDON_INITIATE_ONCE) id(ids.target(), false, "actual pardon target", true);
        need("hold".equals(report.path("phase").asText()) && absent(report, "error") && absent(report, "finished_at") && !yes(report, "cleanup_ok"), "active healthy original hold required");
        for (JsonNode row : report.path("steps")) need(!absent(row, "finished_at") && yes(row, "ok") && absent(row, "error"), "original in-flight/error/UNKNOWN row is never replayable");
        JsonNode frame = latest(report), actor = frame.path("played_character"), diagnostic = frame.path("diagnostics");
        need(yes(frame, "paused") && yes(frame, "map_ready") && yes(actor, "alive"), "living paused actual frame required");
        need(integer(actor, "character_id") == expect.actorId() && integer(frame, "date_raw") == expect.dateRaw()
                && integer(frame, "revision") == expect.revision() && integer(frame, "native_revision") == expect.nativeRevision()
                && integer(diagnostic, "bridge_pid") == expect.bridgePid() && integer(diagnostic, "connection_generation") == expect.connectionGeneration()
                && text(frame.path("managed_campaign_run_binding"), "run_id").equals(expect.managedRunId())
                && expect.managedRunId().equals(input.runId()), "current frame/managed run changed; refresh actual observations");
        need(permitsEvent(input.stage()) || absent(frame, "active_event"), "consume actual event before dependent action");
        need(absent(frame, "pending_character_interaction"), "handle actual notification through established native policy first");
        if (oldActor(input.stage())) need(expect.actorId() == ids.predecessor(), "old-head stage requires actual original predecessor");
        if (newActor(input.stage())) need(expect.actorId() == ids.heir(), "new-head stage requires actual pinned heir");
        if (input.stage() == Stage.BIRTH_SAVE || input.stage() == Stage.BIRTH_PLUS24_SAVE) {
            need(input.anchors() != null && input.anchors().birthDateRaw() != null, "actual birth Native date required");
            long expected = input.anchors().birthDateRaw() + (input.stage() == Stage.BIRTH_SAVE ? 0 : 24);
            need(expect.dateRaw() == expected, "birth anchor must be exactly B or B+24; no delayed-marker relabel");
        }
        if (input.stage() == Stage.PARDON_PLUS31_SAVE) {
            need(input.anchors() != null && input.anchors().pardonObserveDateRaw() != null, "actual pardon-observe input date O required");
            need(expect.dateRaw() == input.anchors().pardonObserveDateRaw() + 31 * 24, "pardon anchor must be exact O+31 real days");
        }
        String key = fixtureKey(input.stage());
        for (JsonNode row : report.path("steps")) {
            JsonNode plan = row.path("plan"), arguments = plan.path("args");
            long actorId = row.path("after_snapshot").path("played_character").path("character_id").asLong(-1);
            if (key != null && actorId == expect.actorId() && "ck3_confirm_ingame_decision_outcome_v1".equals(plan.path("tool").asText()) && key.equals(arguments.path("decision_key").asText()))
                throw new IllegalArgumentException("fixture input already submitted for this actor; never replay");
            if ((input.stage() == Stage.OLD_EDIT_CONFIRM_ONCE || input.stage() == Stage.NEW_EDIT_CONFIRM_ONCE || input.stage() == Stage.CREATE_CONFIRM_ONCE)
                    && actorId == expect.actorId() && "ck3_execute_player_rite_creation_action_v1".equals(plan.path("tool").asText()) && "confirm_once".equals(arguments.path("operation").asText())
                    && arguments.path("expected_source_rite_id").asLong(-1) == ids.rite()
                    && (input.stage() == Stage.CREATE_CONFIRM_ONCE ? "create_rite" : "edit_rite").equals(arguments.path("expected_outcome_kind").asText()))
                throw new IllegalArgumentException("original edit confirm already submitted for this actor; never replay");
            if (input.stage() == Stage.PARDON_INITIATE_ONCE && actorId == expect.actorId()
                    && "ck3_initiate_character_interaction_ordinary_v1".equals(plan.path("tool").asText())
                    && arguments.path("recipient_id").asLong(-1) == ids.target() && "pardon_interaction".equals(arguments.path("interaction_key").asText()))
                throw new IllegalArgumentException("original pardon already submitted; never replay");
        }
    }
    private void id(Long value, boolean zero, String label, boolean required) {
        need(value != null || !required, label + " required by this stage; do not invent a bootstrap ID");
        if (value != null) need(value >= (zero ? 0 : 1) && value <= 0xFFFFFFFEL, "literal bounded Native " + label + " required");
    }
    public Frame actualFrame(JsonNode frame) {
        return new Frame(integer(frame.path("played_character"), "character_id"), integer(frame, "date_raw"), integer(frame, "revision"), integer(frame, "native_revision"),
                integer(frame.path("diagnostics"), "bridge_pid"), integer(frame.path("diagnostics"), "connection_generation"), text(frame.path("managed_campaign_run_binding"), "run_id"));
    }
    private JsonNode originalObservation(Input input, JsonNode report, String tool) {
        need(input.action() != null && input.action().observationStepId() != null, "actual original observation step ID required");
        List<JsonNode> found = new ArrayList<>();
        for (JsonNode row : report.path("steps")) if (input.action().observationStepId().equals(row.path("id").asText())) found.add(row);
        need(found.size() == 1 && tool.equals(found.getFirst().path("plan").path("tool").asText()), "original observation tool/step mismatch");
        JsonNode row = found.getFirst(), frame = row.path("after_snapshot");
        need(integer(frame.path("played_character"), "character_id") == input.currentFrame().actorId()
                && integer(frame, "date_raw") == input.currentFrame().dateRaw()
                && integer(frame, "revision") == input.currentFrame().revision(), "observation is not the current actor/date/revision");
        return row;
    }
    private String preview(Input input, JsonNode report, boolean confirmation, boolean creation) {
        JsonNode leaf = originalObservation(input, report, "ck3_query_player_rite_creation_action_context_v1").path("result").path("rite_creation_action");
        need(yes(leaf.path("full_can"), creation ? "can_create" : "can_edit") && yes(leaf.path("quote"), "has_enough_piety")
                && (creation ? "create_rite" : "edit_rite").equals(leaf.path("draft").path("actual_outcome_kind").asText())
                && integer(leaf.path("draft"), "source_rite_id") == input.ids().rite(), "actual original edit Can/quote/source/outcome required");
        String token = text(leaf, "preview_identity");
        need(token.matches("[0-9a-f]{64}") && token.equals(input.action().previewIdentity()), "actual preview identity mismatch");
        if (confirmation) need("confirmation".equals(leaf.path("modal").path("stage").asText()) && yes(leaf.path("modal"), "active")
                && yes(leaf.path("modal"), "native_can_accept") && yes(leaf.path("modal"), "same_draft_window_bound"), "actual legal same-draft confirmation modal required");
        return token;
    }
    private String claim(Input input, JsonNode report) {
        need(input.action() != null && input.action().actionRequestId() != null && input.action().actionRequestId().matches("rite-action-[0-9a-f]{32}"), "original typed action_request_id required");
        for (JsonNode row : report.path("steps")) {
            if (input.action().actionRequestId().equals(row.path("result").path("action_request_id").asText())) {
                need("confirm_once".equals(row.path("plan").path("args").path("operation").asText())
                        && row.path("plan").path("args").path("expected_source_rite_id").asLong(-1) == input.ids().rite()
                        && row.path("after_snapshot").path("played_character").path("character_id").asLong(-1) == input.currentFrame().actorId(), "request does not belong to this actor/Rite original confirm");
                return input.action().actionRequestId();
            }
        }
        throw new IllegalArgumentException("original confirm request not found; never invent or resend");
    }
    private Tool tool(Input input, String suffix, String name, Arguments arguments) { return new Tool(input.prefix() + "-" + suffix, name, arguments, true); }
    private void fixture(Input input, List<Step> result, String key) {
        result.add(tool(input, "open", "ck3_open_ingame_decisions_v1", new Empty()));
        result.add(tool(input, "available", "ck3_query_ingame_decision_item_v1", new Decision(key)));
        result.add(tool(input, "select", "ck3_select_ingame_decision_item_v1", new Decision(key)));
        result.add(tool(input, "detail", "ck3_query_ingame_decision_item_v1", new Decision(key)));
        result.add(tool(input, "confirm-once", "ck3_confirm_ingame_decision_outcome_v1", new ConfirmDecision(key, "decision_closed")));
        result.add(tool(input, "post", "ck3_take_snapshot", new Empty()));
    }
    private void observe(Input input, List<Step> result, boolean save) {
        if (save) result.add(tool(input, "save", "ck3_save_checkpoint", new Empty()));
        result.add(tool(input, "root", "ck3_query_campaign_root_context_v1", new Empty()));
        result.add(tool(input, "original-title", "ck3_query_title_holder_v1", new Title(input.ids().originalTitle())));
        result.add(tool(input, "religion", "ck3_query_player_religion_context_v1", new Empty()));
        result.add(tool(input, "rite", "ck3_query_player_rite_creation_action_context_v1", new RiteQuery(input.ids().rite(), "current_rite")));
        result.add(tool(input, "members", "ck3_query_player_rite_members_v1", new Empty()));
    }
    public Plan plan(Input input, JsonNode report) {
        validate(input, report); List<Step> result = new ArrayList<>(); String key = fixtureKey(input.stage());
        if (key != null) fixture(input, result, key);
        else if (input.stage() == Stage.PIN_ORIGINAL_HEIR) {
            result.add(tool(input, "root", "ck3_query_campaign_root_context_v1", new Empty()));
            result.add(tool(input, "religion", "ck3_query_player_religion_context_v1", new Empty()));
            result.add(tool(input, "reform", "ck3_query_player_religion_reform_context_v1", new Empty()));
            result.add(tool(input, "members", "ck3_query_player_rite_members_v1", new Empty()));
        }
        else if (isSave(input.stage())) observe(input, result, true);
        else switch (input.stage()) {
            case OLD_EDIT_OPEN_SELECT, NEW_EDIT_OPEN_SELECT -> {
                result.add(tool(input, "faith", "ck3_open_faith_window_v1", new Faith(input.ids().faith())));
                result.add(tool(input, "visible", "ck3_query_ingame_ui_window_v1", new Window("faith")));
                result.add(tool(input, "open", "ck3_execute_player_rite_creation_action_v1", new RiteWrite("open_edit_current_rite_draft", input.ids().rite(), null, null, null, null)));
                result.add(tool(input, "doctrine", "ck3_execute_player_rite_creation_action_v1", new RiteWrite("select_doctrine", input.ids().rite(), "des_dynastic_membership", input.stage() == Stage.OLD_EDIT_OPEN_SELECT ? "des_doctrine_none" : "des_doctrine_dynastic", null, null)));
                result.add(tool(input, "draft", "ck3_query_player_rite_creation_action_context_v1", new RiteQuery(input.ids().rite(), "draft")));
            }
            case OLD_EDIT_PREPARE_CONFIRMATION, NEW_EDIT_PREPARE_CONFIRMATION, OLD_EDIT_CONFIRM_ONCE, NEW_EDIT_CONFIRM_ONCE,
                    CREATE_PREPARE_CONFIRMATION, CREATE_CONFIRM_ONCE -> {
                boolean confirm = input.stage() == Stage.OLD_EDIT_CONFIRM_ONCE || input.stage() == Stage.NEW_EDIT_CONFIRM_ONCE || input.stage() == Stage.CREATE_CONFIRM_ONCE;
                boolean creation = input.stage() == Stage.CREATE_PREPARE_CONFIRMATION || input.stage() == Stage.CREATE_CONFIRM_ONCE;
                result.add(tool(input, "once", "ck3_execute_player_rite_creation_action_v1", new RiteWrite(confirm ? "confirm_once" : "prepare_confirmation", input.ids().rite(), null, null, preview(input, report, confirm, creation), creation ? "create_rite" : "edit_rite")));
                result.add(confirm ? tool(input, "after", "ck3_take_snapshot", new Empty()) : tool(input, "modal", "ck3_query_player_rite_creation_action_context_v1", new RiteQuery(input.ids().rite(), "draft")));
            }
            case EVENT_OBSERVE -> {
                long event = integer(latest(report).path("active_event"), "instance_id");
                result.add(tool(input, "context", "ck3_query_current_event_window_context_v1", new EventQuery(event)));
            }
            case EVENT_FIRST_OPTION -> {
                long event = integer(latest(report).path("active_event"), "instance_id");
                JsonNode context = originalObservation(input, report, "ck3_query_current_event_window_context_v1").path("result").path("current_event_window_context");
                need(integer(context, "current_event_instance_id") == event, "event context instance changed");
                JsonNode first = null;
                for (JsonNode option : context.path("options")) if (yes(option, "shown")) { first = option; break; }
                need(first != null && yes(first, "enabled"), "first actual displayed option is disabled/missing");
                int option = Math.toIntExact(integer(first, "native_option_index") + 1); need(option > 0, "native displayed option index required");
                for (JsonNode row : report.path("steps")) need(!("ck3_select_event_option".equals(row.path("plan").path("tool").asText())
                        && row.path("plan").path("args").path("event_instance_id").asLong(-1) == event), "event option already submitted; never replay");
                result.add(tool(input, "select-once", "ck3_select_event_option", new EventSelect(event, option)));
                result.add(tool(input, "gone", "ck3_take_snapshot", new Empty()));
            }
            case EDIT_COLLECT_ORIGINAL, CREATE_COLLECT_ORIGINAL -> result.add(new Tool(input.prefix() + "-collect", "ck3_collect_player_rite_creation_action_result_v1", new Collect(claim(input, report), 0.0), false));
            case EDIT_VERIFY_ORIGINAL, CREATE_VERIFY_ORIGINAL -> {
                result.add(tool(input, "verify", "ck3_verify_player_rite_creation_action_completed_v1", new Verify(claim(input, report))));
                if (input.stage() == Stage.CREATE_VERIFY_ORIGINAL) {
                    result.add(tool(input, "religion", "ck3_query_player_religion_context_v1", new Empty()));
                    result.add(tool(input, "reform", "ck3_query_player_religion_reform_context_v1", new Empty()));
                    result.add(tool(input, "members", "ck3_query_player_rite_members_v1", new Empty()));
                } else result.add(tool(input, "persisted-rite", "ck3_query_player_rite_creation_action_context_v1", new RiteQuery(input.ids().rite(), "current_rite")));
            }
            case PRIMARY_INHERIT_ONE_DAY -> result.add(new Day(input.prefix() + "-actual-day", "advance_day", 1, 300, true, true));
            case PARDON_QUERY -> result.add(tool(input, "query", "ck3_query_character_interaction_ordinary_v1", new Ordinary("pardon_interaction", input.ids().target())));
            case PARDON_INITIATE_ONCE -> {
                JsonNode row = originalObservation(input, report, "ck3_query_character_interaction_ordinary_v1");
                need("pardon_interaction".equals(row.path("plan").path("args").path("interaction_key").asText())
                        && row.path("plan").path("args").path("recipient_id").asLong(-1) == input.ids().target()
                        && yes(row.path("result").path("character_interaction_ordinary_context"), "ready_to_initiate"), "actual legal ordinary pardon query for same target required");
                result.add(tool(input, "initiate-once", "ck3_initiate_character_interaction_ordinary_v1", new Ordinary("pardon_interaction", input.ids().target())));
                result.add(tool(input, "after", "ck3_take_snapshot", new Empty()));
            }
            default -> throw new IllegalArgumentException("stage has no qualified existing route");
        }
        Set<String> ids = new HashSet<>(); for (Step step : result) need(ids.add(step.id()), "duplicate generated step ID");
        for (JsonNode row : report.path("steps")) need(!ids.contains(row.path("id").asText()), "generated ID already consumed");
        return new Plan(result);
    }
    private void review(Input input) throws Exception {
        List<Gate> required = gates(input.stage());
        if (required.isEmpty()) return;
        checkedPin(input.rootReview()); RootReview review = JSON.treeToValue(read(Path.of(input.rootReview().path()), 512 * 1024), RootReview.class);
        need(review.schemaVersion() == 1 && MACHINE.equals(review.machine_id()) && HEAD.equals(review.source_HEAD())
                && input.runId().equals(review.run_id()) && "/root".equals(review.reviewer()) && review.forStage() == input.stage(), "current Root review identity/stage mismatch");
        need(review.gates() != null && new HashSet<>(review.gates()).size() == review.gates().size() && review.gates().containsAll(required), "Root has not consumed every exact stage prerequisite");
        need(review.evidence() != null && !review.evidence().isEmpty() && review.evidence().size() <= 64 && review.scope_note() != null && !review.scope_note().isBlank(), "bounded original Root evidence required");
        for (Pin evidence : review.evidence()) checkedPin(evidence);
    }
    /** Decode only the shared authority Pin; JSON integer node width does not change its contract. */
    static Pin capacityAuthority(JsonNode value) {
        need(value != null && value.isObject(), "capacity authority Pin object required");
        Set<String> fields = new HashSet<>(); value.fieldNames().forEachRemaining(fields::add);
        need(fields.equals(Set.of("path", "bytes", "sha256")), "capacity authority exact Pin fields required");
        String pathText = text(value, "path"), sha = text(value, "sha256");
        Path pathValue = Path.of(pathText);
        need(pathValue.isAbsolute() && pathValue.normalize().equals(pathValue), "capacity authority absolute normalized path required");
        long bytes = integer(value, "bytes");
        need(bytes >= 0 && sha.matches("[0-9a-f]{64}"), "capacity authority nonnegative EOF/canonical SHA required");
        return new Pin(pathText, bytes, sha);
    }
    /** Source/capacity identity belongs to the shared producer and its strict receipt consumer. */
    private void capacityIdentity(Capacity capacity, JsonNode fresh) throws Exception {
        need(capacity.authority().equals(binding.sourceAuthority()), "capacity authority matches explicit binding");
        SharedSourceCapacity.validateFreshBinding(fresh, MACHINE, HEAD,
                binding.sourceAuthority(), binding.sourceFacts());
    }
    private void capacity(Input input) throws Exception { capacity(input, isSave(input.stage())); }
    private void capacity(Input input, boolean required) throws Exception {
        if (!required) return;
        Capacity capacity = Objects.requireNonNull(input.capacity(), "fresh Save capacity required");
        checkedPin(capacity.fresh()); checkedPin(capacity.originalWait()); checkedPin(capacity.authority());
        JsonNode fresh = read(Path.of(capacity.fresh().path()), 512 * 1024), wait = read(Path.of(capacity.originalWait().path()), 128 * 1024);
        capacityIdentity(capacity, fresh);
        need(integer(fresh, "minimum_next_write_bytes") >= SAVE_PEAK, "single-Save peak required");
        need(integer(wait, "exit_code") == 0 && no(wait, "timed_out") && (yes(wait, "actual_original_popen_wait") || yes(wait, "actual_original_Process_waitFor")), "original full capacity wait0 required");
        long age = Duration.between(Instant.parse(text(fresh, "observed_at_utc")), Instant.now()).toSeconds();
        need(age >= 0 && age < 180, "Save capacity observation stale");
    }
    /** Rebind an existing exact native plan shape, never Python source or its assertions. */
    private void donor(Path inputPath, Path output, boolean early) throws Exception {
        JsonNode value = read(inputPath, 128 * 1024);
        Input input = JSON.treeToValue(value.path("binding"), Input.class);
        need(input.stage() == Stage.PIN_ORIGINAL_HEIR, "early/donor binding uses neutral old-actor PIN_ORIGINAL_HEIR guard only");
        Path live = Path.of(input.live()).toAbsolutePath(), reportPath = live.resolve("native-report.json");
        need(!Files.exists(output) && output.toAbsolutePath().startsWith(live.resolve("operator-inputs")), "new actual live/operator-inputs output required");
        Pin reportPin = pin(reportPath); JsonNode report = read(reportPath, 256L * 1024 * 1024); validate(input, report);
        need(input.runId().equals(read(live.resolve("frozen-argv.json"), 32 * 1024 * 1024).path("run_id").asText()), "actual frozen allocated run required");
        JsonNode generated; Pin donorPin = null;
        if (early) {
            EarlyInput request = JSON.treeToValue(value, EarlyInput.class); generated = JSON.valueToTree(earlyPlan(request, report));
        } else {
            DonorInput request = JSON.treeToValue(value, DonorInput.class); checkedPin(request.donorPlan()); donorPin = request.donorPlan();
            generated = rebindNative(request, read(Path.of(donorPin.path()), 128 * 1024));
            boolean save = false; for (JsonNode step : generated.path("steps")) save |= "ck3_save_checkpoint".equals(step.path("tool").asText());
            capacity(input, save);
        }
        Set<String> generatedIds = new HashSet<>(); for (JsonNode step : generated.path("steps")) need(generatedIds.add(text(step, "id")), "unique rebound IDs required");
        for (JsonNode row : report.path("steps")) need(!generatedIds.contains(row.path("id").asText()), "original generated IDs already consumed");
        need(reportPin.equals(pin(reportPath)), "native report changed during rebinding");
        writeNew(output, generated);
        writeNew(output.resolveSibling(output.getFileName() + ".preparation.json"), new DonorPrepared("xar.core-early-plan-preparation.v1", MACHINE, HEAD, input.runId(), pin(inputPath), donorPin, pin(output),
                "JSON_PLAN_ONLY; Root consumes current-source fixture prerequisites and original native results. No old dates/assertions/Python source copied; existing queue owns schema/once/current admission.", false, false));
    }
    public Plan earlyPlan(EarlyInput request, JsonNode report) {
        Input input = request.binding(); validate(input, report); need(request.decision() != null, "declared early fixture decision required");
        need(request.expectedPriorSubmissions() >= 0 && request.expectedPriorSubmissions() <= (request.decision() == EarlyDecision.HEAD_CELLS ? 1 : 0), "only original head-cells permits its second disclosed input");
        long previous = 0;
        for (JsonNode row : report.path("steps")) if ("ck3_confirm_ingame_decision_outcome_v1".equals(row.path("plan").path("tool").asText())
                && request.decision().key().equals(row.path("plan").path("args").path("decision_key").asText())) previous++;
        need(previous == request.expectedPriorSubmissions(), "existing fixture attempt count differs; never replay UNKNOWN");
        List<Step> steps = new ArrayList<>(); fixture(input, steps, request.decision().key()); return new Plan(steps);
    }
    public JsonNode rebindNative(DonorInput request, JsonNode original) {
        Input input = request.binding(); need(original.isObject() && original.size() == 1 && original.path("steps").isArray(), "exact pinned original queue plan required");
        need(request.arguments() != null, "explicit argument binding list required");
        Set<ArgumentField> supplied = new HashSet<>(), used = new HashSet<>();
        for (ArgumentBinding item : request.arguments()) {
            need(item.field() != null && supplied.add(item.field()), "unique declared dynamic argument binding required");
            need(item.field().numeric() ? item.integerValue() != null && item.integerValue() >= (item.field() == ArgumentField.expected_source_rite_id ? 0 : 1) && item.integerValue() <= 0xFFFFFFFEL && item.textValue() == null : item.integerValue() == null && item.textValue() != null, "strict typed dynamic argument required");
            if (item.field() == ArgumentField.expected_preview_identity) need(item.textValue().matches("[0-9a-f]{64}"), "preview SHA required");
            if (item.field() == ArgumentField.action_request_id) need(item.textValue().matches("rite-action-[0-9a-f]{32}"), "original claim ID required");
        }
        ObjectNode rebound = JSON.createObjectNode(); var steps = rebound.putArray("steps"); int index = 0;
        Set<String> names = Set.of("ck3_take_snapshot", "ck3_get_capabilities", "ck3_save_checkpoint", "ck3_query_normal_exit_context_v1", "ck3_open_faith_window_v1", "ck3_query_ingame_ui_window_v1", "ck3_query_campaign_root_context_v1", "ck3_query_title_holder_v1", "ck3_query_player_religion_context_v1", "ck3_query_player_religion_doctrines_v1", "ck3_query_player_religion_reform_context_v1", "ck3_query_player_religion_draft_groups_v1", "ck3_query_player_religion_draft_doctrine_choices_v1", "ck3_query_player_religion_draft_resource_costs_v1", "ck3_query_player_rite_creation_action_context_v1", "ck3_execute_player_rite_creation_action_v1", "ck3_query_player_rite_members_v1", "ck3_query_player_prisoner_collection_private_v1", "ck3_query_character_interaction_ordinary_v1", "ck3_query_engine_log_literals_v1");
        Set<String> numericSelectors = Set.of("faith_id", "expected_source_rite_id", "recipient_id", "title_id", "requested_title_id", "release_material_target_character_id");
        for (JsonNode source : original.path("steps")) {
            need(!source.has("kind") || "tool".equals(source.path("kind").asText()), "donor day/lifecycle routes are retired; use existing CaseClient");
            String tool = text(source, "tool"); need(names.contains(tool), "donor action is outside early Native allowlist");
            ObjectNode step = source.deepCopy(), args = step.withObject("args");
            if (tool.equals("ck3_execute_player_rite_creation_action_v1")) {
                String operation = text(args, "operation");
                need(Set.of("open_create_draft", "open_edit_current_rite_draft", "cancel_draft", "select_doctrine", "set_name_field").contains(operation), "preview/confirm require typed stage, no donor bypass");
                if (operation.equals("select_doctrine")) need("des_dynastic_membership".equals(args.path("group_key").asText()) && Set.of("des_doctrine_none", "des_doctrine_dynastic").contains(args.path("doctrine_key").asText()), "only original product membership choice allowed");
            }
            for (String field : numericSelectors) if (args.has(field)) need(supplied.contains(ArgumentField.valueOf(field)), "historical ID lacks actual binding: " + field);
            args.properties().forEach(entry -> need(!entry.getKey().endsWith("_id") || numericSelectors.contains(entry.getKey()), "unrecognized historical ID field is not silently retained: " + entry.getKey()));
            for (ArgumentBinding item : request.arguments()) if (args.has(item.field().name())) {
                used.add(item.field()); if (item.field().numeric()) args.put(item.field().name(), item.integerValue()); else args.put(item.field().name(), item.textValue());
            }
            args.remove("expected_revision"); step.remove("bind_previous_revision"); step.put("fresh_revision", true);
            step.put("id", input.prefix() + "-" + (++index)); steps.add(step);
        }
        need(!steps.isEmpty() && used.equals(supplied), "nonempty plan and all dynamic bindings used exactly by declared fields required");
        return rebound;
    }
    public void materialize(Path inputPath, Path output) throws Exception {
        Input input = JSON.treeToValue(read(inputPath, 128 * 1024), Input.class);
        Path live = Path.of(input.live()).toAbsolutePath(), reportPath = live.resolve("native-report.json");
        need(!Files.exists(output) && output.toAbsolutePath().startsWith(live.resolve("operator-inputs")), "new output directory inside current live/operator-inputs required");
        Pin before = pin(reportPath); JsonNode report = read(reportPath, 256L * 1024 * 1024);
        JsonNode frozen = read(live.resolve("frozen-argv.json"), 32 * 1024 * 1024);
        need(input.runId().equals(frozen.path("run_id").asText()), "frozen run differs from current input");
        review(input); capacity(input); Plan plan = plan(input, report);
        need(before.equals(pin(reportPath)), "native report changed during preparation; refresh before dispatch");
        Files.createDirectory(output); Path planPath = output.resolve("plan.json"); writeNew(planPath, plan);
        String python = text(read(RUNTIME.resolve("runtime.json"), 8 * 1024 * 1024), "python");
        List<String> argv = List.of(python, "-B", "-X", "utf8", RUNTIME.resolve("source/tools/ck3_mod_acceptance_queue.py").toString(), "--live", live.toString(), "--plan", planPath.toString(), "--name", input.prefix() + ".json", "--timeout-seconds", "30");
        writeNew(output.resolve("materialized.actual.json"), new Materialized("xar.core-tail-preparation-materialized.v1", MACHINE, HEAD, input.runId(), Instant.now(), input.stage(), pin(inputPath), before, pin(planPath), argv, gates(input.stage()),
                "PLAN_ONLY. Existing queue must independently admit current ownership/metadata/once ledger. ACK is not outcome. Root consumes actual terminal rows and independent evidence before any dependent stage.", false, false));
    }
    private void addTable(List<TableSelection> tables, ScopeKind kind, List<String> path, List<NativeId> ids) {
        need(ids != null, "explicit ID array required; empty differs from missing");
        if (!ids.isEmpty()) tables.add(new TableSelection(kind, path, ids, true));
    }
    public RetainedSaveOperator20261027.Request selected(SelectedInput input) {
        need(input.schemaVersion() == 1 && MACHINE.equals(input.binding().machineId()) && HEAD.equals(input.binding().sourceHead()), "current selected request identity required");
        need(input.actorPath() != null && input.actors() != null && !input.actors().isEmpty() && input.actors().size() <= 16, "one actual actor location and <=16 IDs required");
        List<TableSelection> tables = new ArrayList<>();
        tables.add(new TableSelection(ScopeKind.ACTOR, input.actorPath().segments(), input.actors(), input.actorsRequired()));
        addTable(tables, ScopeKind.RITE, List.of("jens_180", "database"), input.rites());
        addTable(tables, ScopeKind.DYNASTY, List.of("dynasties", "dynasties"), input.dynasties());
        addTable(tables, ScopeKind.HOUSE, List.of("dynasties", "dynasty_house"), input.houses());
        addTable(tables, ScopeKind.TITLE, List.of("landed_titles", "landed_titles"), input.titles());
        Selection selection = new Selection(tables, List.of(), input.metadataRequired(), false, List.of());
        Inspection.Request request = new Inspection.Request(4, MACHINE, input.binding().repository(), input.retained().save(), input.retained().decoder(), selection);
        return new RetainedSaveOperator20261027.Request(1, input.binding(), input.retained(), input.operatorProof(), new RetainedSaveOperator20261027.SelectedWork(request));
    }
    public RetainedSaveOperator20261027.Request opinions(OpinionsInput input) {
        need(input.schemaVersion() == 1 && MACHINE.equals(input.binding().machineId()) && HEAD.equals(input.binding().sourceHead()), "current opinions request identity required");
        OpinionInspection.Selection selection = new OpinionInspection.Selection(List.of("opinions", "active_opinions"), "des_apostasy_opinion", "-100", "-100", input.pairs(), 16384, 65536, 16);
        OpinionInspection.Request request = new OpinionInspection.Request(1, MACHINE, input.binding().repository(), input.retained().save(), input.retained().decoder(), selection);
        return new RetainedSaveOperator20261027.Request(1, input.binding(), input.retained(), input.operatorProof(), new RetainedSaveOperator20261027.OpinionWork(request, input.references()));
    }
    private void reader(Path input, Path output, boolean opinion) throws Exception {
        need(!Files.exists(output), "new unused reader input output required");
        RetainedSaveOperator20261027.Request value = opinion ? opinions(JSON.treeToValue(read(input, 128 * 1024), OpinionsInput.class)) : selected(JSON.treeToValue(read(input, 128 * 1024), SelectedInput.class));
        checkedPin(value.operatorProof());
        for (Pin item : List.of(value.retained().save(), value.retained().sdkPinFile(), value.retained().custodyFile(), value.retained().decoder(), value.binding().runtime(), value.binding().runtimeManifest(), value.binding().sourceIndex(), value.binding().nativeSourceIndex(), value.binding().nativeDll(), value.binding().injector())) checkedPin(item);
        writeNew(output, value);
        writeNew(output.resolveSibling(output.getFileName() + ".preparation.json"), new ReaderOutput("xar.core-tail-reader-input-preparation.v1", MACHINE, HEAD, value.binding().runId(), pin(input), pin(output),
                "INPUT_ONLY. Existing RetainedSaveOperator owns OS custody/SDK/producer/source validation and sole parsing. No missing record proves death; merge only uniquely sourced FULL_RECORD originals. No business qualification.", false, false));
    }
    private Catalog catalog() {
        List<StageRow> rows = Arrays.stream(Stage.values()).map(stage -> new StageRow(stage, gates(stage), switch (stage) {
            case OLD_EDIT_PREPARE_CONFIRMATION, NEW_EDIT_PREPARE_CONFIRMATION, CREATE_PREPARE_CONFIRMATION -> "Fill action.observationStepId + previewIdentity from actual draft query; native Can/quote/source/outcome checked before generation.";
            case OLD_EDIT_CONFIRM_ONCE, NEW_EDIT_CONFIRM_ONCE, CREATE_CONFIRM_ONCE -> "Fill actual modal query step+preview; original same-draft modal required. Never resend UNKNOWN confirm.";
            case EDIT_COLLECT_ORIGINAL, EDIT_VERIFY_ORIGINAL -> "Fill original current-actor actionRequestId; result must originate in this report's confirm_once.";
            case EVENT_FIRST_OPTION -> "Fill actual context step. Native first shown enabled option selected; actual gone proof remains required.";
            case PARDON_INITIATE_ONCE -> "Fill actual ordinary query step. ready_to_initiate and exact target are checked. Initiate once; then actual poststate.";
            case PRIMARY_INHERIT_ONE_DAY -> "Existing public kind=advance_day; allow_actor_change=true. No native same-actor fast day, SetPlayed or fixture player selection.";
            default -> "Consume actual original terminal row, fixture/log predicate and independent required Save evidence before dependent input.";
        }, switch (stage) {
            case BIRTH_SAVE -> "Retain immutable Save/sdk/custody; exactly one existing fresh-before CaseClient day; BIRTH_PLUS24_SAVE.";
            case BIRTH_PLUS24_SAVE -> "Consume B/B+24 independent proofs and delayed .41 birth_verified separately; all prerequisites before HEIR_PREPARE.";
            case OLD_CLOSED_SAVE -> "Consume independent closed pre-death Save before PRIMARY_DEATH_STAGE.";
            case SUCCESSOR_OBSERVE_SAVE -> "Prove old predecessor dead and actual player==pinned heir==Native Rite head, same original title, None, never edited; SUCCESSOR_READBACK.";
            case PARDON_CONSUMED_SAVE -> "Advance existing fresh-before single days to original pardon-observe O+31; PARDON_PLUS31_SAVE.";
            case PARDON_PLUS31_SAVE -> "Consume reasons absent while trait/opinion/pair persist; COLD_ANCHOR then FINAL_SAVE.";
            case FINAL_SAVE -> "Consume final independent graph; exact original P5/P6 assertions and normal closure. New process cold_reload remains separate.";
            default -> "Use dependency order in README; no entire skeleton enqueued across an observation boundary.";
        }, isSave(stage), stage == Stage.BIRTH_SAVE ? "B" : stage == Stage.BIRTH_PLUS24_SAVE ? "B+24 Native hours" : stage == Stage.PARDON_PLUS31_SAVE ? "O+31*24 Native hours" : "actual current paused date")).toList();
        return new Catalog("xar.core-tail-preparation-catalog.v1", MACHINE, HEAD, rows, List.of(
                "One Game writer. Original 400 days/9000s hold/180s Quit reserve unchanged. No runtime/SDK edits.",
                "Every normal day uses existing R33-existing-public-days-prefix/CaseClient fresh-before. Stop at actual birth; after birth remove already-seen birth literal from whole-log stop set.",
                "Save capacity must be fresh adopted current authority and original wait0. No C31/C32 authority is granted by this tool.",
                "Exact queue parser accepts {steps} only. Machine/source and plan/input pins live in companion materialized receipt.",
                "Review gates acknowledge Root consumption; they do not evaluate or grant CK3 business predicates. Existing fixture/native/Save reader still enforce contracts.",
                "P1-4 and P5 prefix are reused through indexed historical shapes after new-run binding; never execute historical R33/R32 files wholesale."), "EXTERNAL_JAVA_SUPPORT_ONLY; existing Maven/Quarkus F15 classpath reused, no new service or business implementation.");
    }
    private ObjectNode pinTemplate() {
        ObjectNode pin = JSON.createObjectNode(); pin.put("path", "<absolute-current-original-path>"); pin.put("bytes", "<literal-integer-byte-length>"); pin.put("sha256", "<actual-lowercase-SHA256>"); return pin;
    }
    private Templates templates() {
        ObjectNode input = JSON.valueToTree(fixtureInput(Stage.PIN_ORIGINAL_HEIR));
        input.put("runId", "<actual-allocated-run-id>"); input.put("prefix", "<new-unused-label>"); input.put("live", "<actual-allocated-absolute-LIVE>");
        ObjectNode frame = (ObjectNode) input.path("currentFrame");
        for (String key : List.of("actorId", "dateRaw", "revision", "nativeRevision", "bridgePid", "connectionGeneration")) frame.put(key, "<actual-literal-integer>");
        frame.put("managedRunId", "<actual-managed_campaign_run_binding.run_id>"); ObjectNode ids = (ObjectNode) input.path("ids");
        for (String key : List.of("predecessor", "heir", "originalTitle", "rite", "faith", "target")) ids.put(key, "<actual-literal-Native-integer-ID>");
        ObjectNode anchors = (ObjectNode) input.path("anchors"); anchors.put("birthDateRaw", "<actual-B-Native-hours-or-null>"); anchors.put("pardonObserveDateRaw", "<actual-O-Native-hours-or-null>");
        ObjectNode action = (ObjectNode) input.path("action"); action.put("observationStepId", "<actual-original-observation-step-or-null>"); action.put("previewIdentity", "<actual-preview-SHA-or-null>"); action.put("actionRequestId", "<original-current-actor-claim-or-null>");
        input.set("rootReview", pinTemplate()); ObjectNode capacity = input.putObject("capacity"); capacity.set("fresh", pinTemplate()); capacity.set("originalWait", pinTemplate()); capacity.set("authority", pinTemplate());
        ObjectNode review = JSON.createObjectNode(); review.put("schemaVersion", 1); review.put("machine_id", MACHINE); review.put("source_HEAD", HEAD); review.put("run_id", "<actual-allocated-run-id>"); review.put("reviewer", "/root"); review.put("forStage", "HEIR_PREPARE"); review.putArray("gates").add("ALL_BIRTH_SHORT_TIMER_FOUNDER_CRIME_PROOFS"); review.putArray("evidence").add(pinTemplate()); review.put("scope_note", "<actual consumed independent proof scope; no blanket business credit>");
        ObjectNode binding = JSON.createObjectNode(); binding.put("machineId", MACHINE); binding.put("sourceHead", HEAD); binding.put("runId", "<actual-allocated-run-id>"); binding.put("repository", BASE.resolve("main12").toString());
        for (String key : List.of("runtime", "runtimeManifest", "sourceIndex", "nativeSourceIndex", "nativeDll", "injector")) binding.set(key, pinTemplate());
        ObjectNode retained = JSON.createObjectNode(); for (String key : List.of("save", "sdkPinFile", "custodyFile", "decoder")) retained.set(key, pinTemplate());
        ObjectNode selected = JSON.createObjectNode(); selected.put("schemaVersion", 1); selected.set("binding", binding); selected.set("retained", retained); selected.set("operatorProof", pinTemplate()); selected.put("actorPath", "LIVING"); selected.put("actorsRequired", false); selected.put("metadataRequired", true);
        for (String key : List.of("actors", "rites", "dynasties", "houses", "titles")) selected.putArray(key).add("<actual-canonical-decimal-ID-string;or-explicit-empty-array>");
        ObjectNode opinions = JSON.createObjectNode(); opinions.put("schemaVersion", 1); opinions.set("binding", binding); opinions.set("retained", retained); opinions.set("operatorProof", pinTemplate());
        ObjectNode refs = opinions.putObject("references"); refs.set("observation", pinTemplate()); refs.put("root", "<actual-current-root-canonical-decimal-string>"); refs.putArray("variablesPath").add("alive_data").add("variables").add("data"); refs.put("targetFlag", "des_test_ref_target"); refs.put("peerFlag", "des_test_ref_peer"); refs.put("outsiderFlag", "des_test_ref_outsider");
        ObjectNode pair = opinions.putArray("pairs").addObject(); pair.put("owner", "<actual-current-observer-ID-string>"); pair.put("target", "<actual-target-ID-string>"); pair.put("expectation", "EXACT_ONE");
        ObjectNode early = JSON.createObjectNode(); early.set("binding", input); early.put("decision", "CAPTURE_CREATED"); early.put("expectedPriorSubmissions", 0);
        ObjectNode donor = JSON.createObjectNode(); donor.set("binding", input); donor.set("donorPlan", pinTemplate()); ObjectNode argument = donor.putArray("arguments").addObject(); argument.put("field", "expected_source_rite_id"); argument.put("integerValue", "<actual-literal-source-Rite-integer>"); argument.putNull("textValue");
        return new Templates("xar.core-tail-preparation-templates.v1", MACHINE, HEAD, "TEMPLATE_ONLY. Angle-bracket fields intentionally fail runtime validation until actual observation replaces them. For unused nullable action/anchors/review/capacity use JSON null; list fields require explicit arrays. No run allocated here.", input, review, selected, opinions, early, donor);
    }
    private Input fixtureInput(Stage stage) {
        long actor = newActor(stage) ? 22 : 11;
        return new Input(1, MACHINE, HEAD, MACHINE + "--dynastic-esotericism--R9999", stage,
                "synthetic-" + stage.name().toLowerCase(), OWN.resolve(MACHINE + "--dynastic-esotericism--R9999").toString(),
                new Frame(actor, 1000, 7, 7, 33, 2, MACHINE + "--dynastic-esotericism--R9999"), new Ids(11L, 22L, 44L, 55L, 66L, 77L),
                new Anchors(stage == Stage.BIRTH_PLUS24_SAVE ? 976L : 1000L, 256L),
                new Action("observed", "a".repeat(64), "rite-action-" + "b".repeat(32)), null, null);
    }
    private void frameInput(Path live, Path output) throws Exception {
        Path reportPath = live.resolve("native-report.json"); Pin before = pin(reportPath); JsonNode report = read(reportPath, 256L * 1024 * 1024);
        Frame frame = actualFrame(latest(report));
        Input input = new Input(1, MACHINE, HEAD, live.getFileName().toString(), Stage.PIN_ORIGINAL_HEIR, "REPLACE-UNUSED-PREFIX", live.toAbsolutePath().toString(), frame,
                new Ids(frame.actorId(), null, null, null, null, null), new Anchors(null, null), new Action(null, null, null), null, null);
        validate(input, report); need(before.equals(pin(reportPath)), "actual report changed while reading frame input"); writeNew(output, input);
        writeNew(output.resolveSibling(output.getFileName() + ".frame-source.json"), new FrameInputReceipt("xar.core-tail-v2-actual-frame-input.v1", MACHINE, HEAD, input.runId(), before, pin(output),
                "READ_ONLY_FRAME_INPUT. Replace unused prefix; then query actual campaign root before filling title/heir, and B0 full Root typed refs before target. No Game action or business admission."));
    }
    private void dispatch(String[] args) throws Exception {
        need(args.length >= 2, "--catalog OUTPUT | --templates OUTPUT | --materialize INPUT NEW_DIR | --selected INPUT NEW_OUTPUT | --opinions INPUT NEW_OUTPUT");
        switch (args[0]) {
            case "--catalog" -> writeNew(Path.of(args[1]), catalog());
            case "--templates" -> writeNew(Path.of(args[1]), templates());
            case "--frame-input" -> { need(args.length == 3, "actual LIVE and new output required"); frameInput(Path.of(args[1]), Path.of(args[2])); }
            case "--materialize" -> { need(args.length == 3, "input and output required"); materialize(Path.of(args[1]), Path.of(args[2])); }
            case "--selected" -> { need(args.length == 3, "input and output required"); reader(Path.of(args[1]), Path.of(args[2]), false); }
            case "--opinions" -> { need(args.length == 3, "input and output required"); reader(Path.of(args[1]), Path.of(args[2]), true); }
            case "--early-fixture" -> { need(args.length == 3, "typed EarlyInput and new output required"); donor(Path.of(args[1]), Path.of(args[2]), true); }
            case "--rebind-native-plan" -> { need(args.length == 3, "typed DonorInput and new output required"); donor(Path.of(args[1]), Path.of(args[2]), false); }
            default -> throw new IllegalArgumentException("unsupported operation");
        }
    }
    public static void main(String[] args) throws Exception {
        need(args.length >= 4 && "--binding".equals(args[0]), "--binding ACTUAL_BINDING_JSON existing-operation required");
        CoreTailPreparation engine = open(Path.of(args[1]));
        engine.dispatch(Arrays.copyOfRange(args, 2, args.length));
    }
}
