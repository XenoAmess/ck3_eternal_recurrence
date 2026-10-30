package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.events.sourcecatalog.EventSourceCatalogue;

/** Actual read-only registry/source/facts validation and the existing annotation consumer chain. */
public final class SourceReviewedEventConsumer {
    static final String SCHEMA = "xar.vanilla-event-offline-source-known/v1";
    static final String CLASSIFICATION = "offline-source-reviewed-user-first-rendered-policy";
    static final String BACKEND = "ck3-1.20.0.4-native-event-window-v1";
    static final String FACTION_SOURCE = "eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd";
    static final String POPULIST_OPTIONS = "5c76ae1a7cc44883f5d4af07e6f5c2e59986b9b0c6d6ca9cb379ac7ce298bace";
    static final String POPULIST_POLICY = "exact_12004_populist_letter_seven_roles_v1";
    static final Map<String, String> BUILDS = Map.of(
        "1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        "1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
        "1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
    private SourceReviewedEventConsumer() { }

    public enum KnowledgeStatus { NOT_REQUESTED, UNKNOWN, SOURCE_REVIEWED }
    public enum FollowupPresence { MISSING, NULL, VALUE }
    public record OfflineFollowupRequirement(FollowupPresence presence, Boolean required) {
        public OfflineFollowupRequirement {
            Objects.requireNonNull(presence);
            require((presence == FollowupPresence.VALUE) == (required != null), "followup field presence/value differs");
        }
    }
    /** Constructor is private: caller-provided known/qualified flags cannot create this result. */
    public static final class ReviewedPlan {
        private final ObjectValue plan;
        private final KnowledgeStatus status;
        private ReviewedPlan(ObjectValue plan, KnowledgeStatus status) { this.plan = plan; this.status = status; }
        public ObjectValue plan() { return plan; }
        public KnowledgeStatus status() { return status; }
        public OfflineFollowupRequirement offlineFollowupRequired() {
            ObjectValue capture = o(plan, "unhandled_event_fallback");
            if (capture == null || !capture.contains("offline_followup_required")) return new OfflineFollowupRequirement(FollowupPresence.MISSING, null);
            Boolean flag = RetainedJson.bool(v(capture, "offline_followup_required"));
            return flag == null ? new OfflineFollowupRequirement(FollowupPresence.NULL, null) : new OfflineFollowupRequirement(FollowupPresence.VALUE, flag);
        }
        public boolean actionAuthorized() { return false; }
        public boolean replayAllowed() { return false; }
        public byte[] encode() { return RetainedJson.encode(plan); }
    }
    record NativeBinding(String build, String exeSha256, String backend, String eventKey,
                         BigInteger calculatedId, BigInteger optionCount) {
        ObjectValue json() {
            return obj(f("ck3_build", s(build)), f("required_ck3_exe_sha256", s(exeSha256)), f("native_backend_id", s(backend)),
                f("event_definition_key", s(eventKey)), f("calculated_event_id", RetainedJson.value(calculatedId)), f("native_option_count", RetainedJson.value(optionCount)));
        }
    }
    private record Candidate(Path path, byte[] raw, ObjectValue entry, ObjectValue facts) { }
    private record Knowledge(Candidate known, ObjectValue audit) { }
    public record ReviewReference(String fingerprint, Path entryPath, String entrySha256) { }
    public record ReviewLookup(java.util.Optional<ObjectValue> entry, ObjectValue audit) {
        public ReviewLookup { Objects.requireNonNull(entry); Objects.requireNonNull(audit); }
        public byte[] encode() {
            return RetainedJson.encode(obj(f("schema", s("xar.events-source-reviewed-lookup-result/v1")),
                f("entry", entry.<Value>map(value -> value).orElse(NULL)), f("audit", audit)));
        }
    }
    /** Full old reader ABI, with the same exact/rebind and current source guards as planning. */
    public static ReviewLookup lookup(ObjectValue capture, TrustedEventSourceContext trusted) {
        Objects.requireNonNull(capture); Objects.requireNonNull(trusted); trusted.verifyCurrentRoots();
        Knowledge result = load(trusted.stateDirectory(), capture, trusted); trusted.verifyCurrentRoots();
        return new ReviewLookup(java.util.Optional.ofNullable(result.known()).map(Candidate::entry), result.audit());
    }
    /** Exact, versioned transport wrapper. Roots and known flags convey no authority. */
    public static ReviewLookup lookup(byte[] raw, TrustedEventSourceContext trusted) {
        ObjectValue wrapper = RetainedJson.object(RetainedJson.parse(raw));
        require(wrapper.fields().keySet().equals(Set.of("schema", "capture"))
            && eq(wrapper, "schema", s("xar.events-source-reviewed-lookup-input/v1")),
            "exact event source lookup wrapper required");
        ObjectValue capture = o(wrapper, "capture"); require(capture != null, "event source lookup capture object required");
        return lookup(capture, trusted);
    }

    public static java.util.Optional<ReviewReference> reviewedReference(ObjectValue capture, TrustedEventSourceContext trusted) {
        Objects.requireNonNull(capture); Objects.requireNonNull(trusted); trusted.verifyCurrentRoots();
        Candidate candidate = load(trusted.stateDirectory(), capture, trusted).known();
        return candidate == null ? java.util.Optional.empty() : java.util.Optional.of(new ReviewReference(stem(candidate.path()), candidate.path(), sha(candidate.raw())));
    }

    /** Offline publisher reuses the complete existing exact/rebind reader, without trusting capture known flags. */
    public static KnowledgeStatus reviewStatus(ObjectValue capture, TrustedEventSourceContext trusted) {
        Objects.requireNonNull(capture); Objects.requireNonNull(trusted);
        trusted.verifyCurrentRoots();
        return load(trusted.stateDirectory(), capture, trusted).known() == null ? KnowledgeStatus.UNKNOWN : KnowledgeStatus.SOURCE_REVIEWED;
    }

    public static ReviewedPlan annotate(UnhandledEventFallback.Plan proposal, Path stateDirectory) {
        Objects.requireNonNull(proposal, "proposal");
        return annotate(UnhandledEventCodec.legacyPlan(proposal), stateDirectory);
    }
    /** Strict legacy JSON boundary; no writer, registry publication or native submission occurs. */
    public static ReviewedPlan annotate(byte[] legacyPlan, Path stateDirectory) {
        return annotate(RetainedJson.object(RetainedJson.parse(legacyPlan)), stateDirectory);
    }
    public static ReviewedPlan continueWithExistingPolicies(UnhandledEventFallback.Plan proposal,
            UnhandledEventFallback.Request request, Path stateDirectory) {
        ReviewedPlan annotated = annotate(proposal, stateDirectory);
        ObjectValue snapshot = request.snapshot() == null ? null : request.snapshot().originalSnapshot();
        ObjectValue result = ExistingFactionEventPolicies.choose(annotated.plan(), snapshot, request.actionSteps());
        KnowledgeStatus status = eq(o(result, "unhandled_event_fallback"), "registry_known", b(true))
            ? KnowledgeStatus.SOURCE_REVIEWED : annotated.status();
        return new ReviewedPlan(result, status);
    }
    public static ReviewedPlan continueWithExistingPlan(ObjectValue plan, ObjectValue snapshot, List<String> actionSteps,
            TrustedEventSourceContext trusted) {
        Objects.requireNonNull(plan, "existing plan"); Objects.requireNonNull(actionSteps, "action steps");
        Objects.requireNonNull(trusted, "trusted source context");
        trusted.verifyCurrentRoots();
        ReviewedPlan annotated = annotate(plan, trusted.stateDirectory(), trusted);
        ObjectValue result = ExistingFactionEventPolicies.choose(annotated.plan(), snapshot, List.copyOf(actionSteps));
        KnowledgeStatus status = eq(o(result, "unhandled_event_fallback"), "registry_known", b(true))
            ? KnowledgeStatus.SOURCE_REVIEWED : annotated.status();
        trusted.verifyCurrentRoots();
        return new ReviewedPlan(result, status);
    }
    private static ReviewedPlan annotate(ObjectValue plan, Path stateDirectory) {
        return annotate(plan, stateDirectory, null);
    }
    private static ReviewedPlan annotate(ObjectValue plan, Path stateDirectory, TrustedEventSourceContext trusted) {
        ObjectValue capture = o(plan, "unhandled_event_fallback");
        if (capture == null || stateDirectory == null) return new ReviewedPlan(plan, KnowledgeStatus.NOT_REQUESTED);
        Knowledge knowledge = load(stateDirectory, capture, trusted);
        boolean known = knowledge.known() != null;
        ObjectValue nextCapture = put(capture, f("registry_known", b(known)), f("offline_followup_required", b(!known)), f("source_knowledge", knowledge.audit()));
        ObjectValue decision = o(plan, "event_decision"); ObjectValue summary = o(plan, "active_event");
        require(decision != null && summary != null, "source-review plan decision/summary objects required");
        String classification = known ? text(knowledge.known().entry(), "classification") : null;
        decision = put(decision, f("source_registry_known", b(known)), f("source_classification", s(classification)),
            f("registry_contract_accepted", b(false)), f("material_effects_verified", b(false)));
        summary = put(summary, f("source_registry_known", b(known)), f("source_knowledge_status", s(known ? "source_reviewed_known" : "unknown")));
        ObjectValue result = put(plan, f("unhandled_event_fallback", nextCapture), f("event_decision", decision), f("active_event", summary));
        if (known) {
            decision = put(decision, f("status", s("source_reviewed_known")), f("registry_known", b(true)), f("classification", s(classification)));
            String phase = text(plan, "phase"); require(phase != null, "event phase required");
            result = put(result, f("event_decision", decision), f("phase", s(phase.replace("active_event_unhandled_", "active_event_source_reviewed_"))));
            if (v(plan, "selected_step") instanceof NullValue) {
                result = result.with("reason", s(!EventOptionAvailability.selectionAllowed(o(capture,"window_context"),o(capture,"selection"))
                    ? eq(o(capture, "selection"), "selection_order", s(UnhandledEventFallback.DisplayPolicy.FIRST_DISPLAYED.wire()))
                        ? "Source-reviewed event: the first displayed native option is disabled."
                        : "Source-reviewed event: no shown native option is enabled."
                    : "Source-reviewed event: its first shown enabled option lacks an advertised native selection step."));
            } else {
                result = put(result, f("phase", s("active_event_source_reviewed_first_rendered_option")),
                    f("reason", s("Source-reviewed event: choose its current first shown enabled option under the owner's policy; material effects remain unverified.")));
            }
        }
        return new ReviewedPlan(result, known ? KnowledgeStatus.SOURCE_REVIEWED : KnowledgeStatus.UNKNOWN);
    }
    private static Knowledge load(Path stateDirectory, ObjectValue capture, TrustedEventSourceContext trusted) {
        NativeBinding current;
        try { current = nativeBinding(capture); if (trusted != null) trusted.requireBuild(current.build()); }
        catch (IllegalArgumentException error) { return new Knowledge(null, obj(f("status", s("unknown")), f("reason", s(error.getMessage())))); }
        List<Value> rejected = new ArrayList<>(); List<Candidate> candidates = new ArrayList<>(); boolean exactSeen = false;
        Path directory = stateDirectory.resolve("evidence/event-source-registry");
        List<Path> paths;
        try {
            paths = trusted == null ? registryEntries(directory) : trusted.registryEntries();
        } catch (IOException error) { throw new IllegalArgumentException("event registry enumeration unavailable", error); }
        ObjectValue binding = current.json();
        for (Path path : paths) {
            try {
                byte[] raw = read(path, 65_536, trusted, TrustedEventSourceContext.FileRole.REGISTRY_ENTRY); ObjectValue entry = RetainedJson.object(RetainedJson.parse(raw));
                ObjectValue old = o(entry, "binding");
                if (!eq(old, "event_definition_key", s(current.eventKey()))) continue;
                boolean exact = binding.fields().entrySet().stream().allMatch(field -> eq(old, field.getKey(), field.getValue()));
                exactSeen |= exact;
                require(eq(entry, "schema", s(SCHEMA)) && eq(entry, "fingerprint", s(stem(path))), "event source registry schema/fingerprint differs");
                if (!exact && List.of("ck3_build", "required_ck3_exe_sha256", "native_backend_id", "event_definition_key", "native_option_count")
                        .stream().anyMatch(key -> !v(old, key).equals(v(binding, key)))) continue;
                Candidate candidate = validated(path, raw, entry, trusted);
                if (exact) return new Knowledge(candidate, audit(candidate, "exact"));
                candidates.add(candidate);
            } catch (IOException | IllegalArgumentException error) {
                if (rejected.size() < 8) rejected.add(obj(f("entry", s(path.getFileName().toString())), f("reason", s(error.getMessage()))));
            }
        }
        if (exactSeen) return new Knowledge(null, obj(f("status", s("unknown")), f("reason", s("exact event binding failed validation")), f("rejected_entries", new ArrayValue(rejected))));
        if (!candidates.isEmpty() && rejected.isEmpty()) {
            Set<List<Value>> pairs = new HashSet<>();
            for (Candidate candidate : candidates) {
                ObjectValue old = o(candidate.entry(), "binding"); pairs.add(List.of(v(old, "source_sha256"), v(old, "option_catalogue_sha256")));
            }
            if (pairs.size() == 1) {
                Candidate candidate = candidates.getFirst();
                try {
                    String event = current.eventKey();
                    boolean letter = ReviewedLetterSourceRebind.KEYS.contains(event); boolean populist = "faction_demand.1001".equals(event);
                    ObjectValue shape = letter ? ReviewedLetterSourceRebind.shape(capture, candidate.facts(), current, trusted)
                        : populist ? populistShape(capture, candidate.facts(), current) : rootShape(capture, candidate.facts(), current, "character_event");
                    ObjectValue old = o(candidate.entry(), "binding");
                    ObjectValue fresh = put(binding, f("source_sha256", v(old, "source_sha256")), f("option_catalogue_sha256", v(old, "option_catalogue_sha256")));
                    ObjectValue result = put(audit(candidate, letter ? "reviewed_letter_source_rebound" : populist ? "populist1001_source_rebound" : "source_rebound"),
                        f("fresh_binding", fresh), f("fresh_binding_fingerprint", s(fingerprint(fresh))),
                        f("adapted_from", obj(f("fingerprint", s(stem(candidate.path()))), f("calculated_event_id", v(old, "calculated_event_id")), f("entry_sha256", s(sha(candidate.raw()))))),
                        f("equivalent_source_fingerprints", new ArrayValue(candidates.stream().map(row -> s(stem(row.path()))).toList())), f("root_scope_shape", shape));
                    if (populist) result = result.with("source_rebind_policy", v(shape, "source_rebind_policy"));
                    if (letter) for (String key : List.of("source_rebind_policy", "knowledge_scope", "scope_identity_gaps", "current_role_identities",
                            "gui_source_sha256", "loaded_gui_bytes_verified", "execution_contract_qualified", "semantic_decision_ready")) result = result.with(key, v(shape, key));
                    return new Knowledge(candidate, result);
                } catch (IOException | IllegalArgumentException error) {
                    rejected.add(obj(f("entry", s(candidate.path().getFileName().toString())), f("reason", s(error.getMessage()))));
                }
            } else rejected.add(obj(f("reason", s("conflicting source or option catalogue bindings"))));
        }
        return new Knowledge(null, obj(f("status", s("unknown")), f("rejected_entries", new ArrayValue(rejected))));
    }
    private static Candidate validated(Path path, byte[] raw, ObjectValue entry, TrustedEventSourceContext trusted) throws IOException {
        ObjectValue binding = o(entry, "binding"), factsRef = o(entry, "source_facts");
        require(binding != null && factsRef != null, "durable event source review changed");
        String factsPath = text(factsRef, "path"), sourcePath = text(entry, "source_path");
        require(factsPath != null && sourcePath != null, "durable event source review changed");
        byte[] factsRaw = read(Path.of(factsPath), 1_048_576, trusted, TrustedEventSourceContext.FileRole.FACTS);
        ObjectValue facts = RetainedJson.object(RetainedJson.parse(factsRaw));
        byte[] source = read(Path.of(sourcePath), 2_097_152, trusted, TrustedEventSourceContext.FileRole.SOURCE);
        require(eq(binding, "source_sha256", s(sha(source))) && eq(factsRef, "sha256", s(sha(factsRaw)))
            && eq(facts, "binding", binding) && v(facts, "fingerprint").equals(v(entry, "fingerprint"))
            && eq(entry, "fingerprint", s(fingerprint(binding))) && eq(binding, "option_catalogue_sha256", s(fingerprint(v(facts, "options"))))
            && eq(entry, "classification", s(CLASSIFICATION)), "durable event source review changed");
        return new Candidate(path, raw.clone(), entry, facts);
    }
    private static ObjectValue audit(Candidate candidate, String mode) {
        return obj(f("status", s("offline-source-reviewed")), f("binding_mode", s(mode)), f("fingerprint", s(stem(candidate.path()))),
            f("entry_path", s(candidate.path().toString())), f("entry_sha256", s(sha(candidate.raw()))), f("material_effects_verified", b(false)), f("registry_contract_accepted", b(false)));
    }
    static NativeBinding nativeBinding(ObjectValue capture) {
        ObjectValue context = o(capture, "window_context");
        require(EventOptionAvailability.supportedContext(context), "not a native vanilla event-card context");
        String key = text(context, "event_definition_key"), build = build(context); BigInteger calculated = number(context, "calculated_event_id");
        String backend = text(o(context, "provenance"), "backend_id");
        require(key != null && key.matches("[A-Za-z0-9_]+\\.[0-9]+") && eq(capture, "event_definition_key", s(key)) && positive(calculated)
            && BUILDS.containsKey(build) && ("ck3-" + build + "-native-event-window-v1").equals(backend), "event/build/native provider identity unavailable");
        BigInteger count = number(capture, "snapshot_option_count");
        List<ObjectValue> shown = objects(context, "options").stream().filter(row -> yes(row, "shown")).toList();
        require(positive(count) && !shown.isEmpty() && shown.stream().allMatch(row -> {
            BigInteger index = number(row, "native_option_index"); return index != null && index.signum() >= 0 && index.compareTo(count) < 0;
        }), "native event option identity incomplete");
        return new NativeBinding(build, BUILDS.get(build), backend, key, calculated, count);
    }
    static String build(ObjectValue context) {
        Value explicit = v(context, "ck3_build"); if (explicit instanceof StringValue value) return value.value();
        ObjectValue provenance = o(context, "provenance"); explicit = v(provenance, "ck3_build");
        if (explicit instanceof StringValue value) return value.value();
        String backend = text(provenance, "backend_id");
        for (String version : BUILDS.keySet()) if (("ck3-" + version + "-native-event-window-v1").equals(backend)) return version;
        return "";
    }
    static ObjectValue rootShape(ObjectValue capture, ObjectValue facts, NativeBinding current, String eventType) {
        ObjectValue context = o(capture, "window_context"), frame = o(capture, "binding");
        require(context != null && frame != null, "fresh event/frame binding unavailable");
        BigInteger instance = number(context, "current_event_instance_id");
        require(positive(instance) && eq(capture, "current_event_instance_id", RetainedJson.value(instance))
            && number(context, "snapshot_revision") != null && v(context, "snapshot_revision").equals(v(frame, "native_revision"))
            && number(context, "date_raw") != null && v(context, "date_raw").equals(v(frame, "date_raw")), "fresh event instance or semantic frame differs");
        ObjectValue readiness = o(context, "readiness");
        require(eq(context, "status", s("available")) && readiness != null && List.of("event_definition_identity_ready", "root_scope_ready", "saved_scopes_ready", "option_presentation_ready")
            .stream().allMatch(key -> yes(readiness, key)), "fresh event context is not fully bound");
        String definition = text(facts, "definition");
        require(definition != null && EventSourceCatalogue.scalars(definition, "type").equals(List.of(eventType)), "source-declared event root differs");
        ObjectValue root = o(context, "root_scope"), identity = o(root, "typed_identity"); BigInteger actor = number(frame, "actor_character_id");
        require(eq(root, "status", s("available")) && eq(root, "raw_type_index", i(4)) && eq(root, "type_key", s("character")) && eq(root, "subtype", i(0))
            && eq(identity, "status", s("available")) && eq(identity, "kind", s("character")) && positive(actor) && eq(identity, "character_id", RetainedJson.value(actor)), "fresh native root scope shape or actor differs");
        List<ObjectValue> source = objects(facts, "options"), nativeOptions = objects(context, "options");
        require(BigInteger.valueOf(source.size()).equals(current.optionCount()) && !nativeOptions.isEmpty(), "source/native option catalogue shape differs");
        for (int index = 0; index < source.size(); index++) require(eq(source.get(index), "native_option_index", i(index)), "source/native option catalogue shape differs");
        Set<BigInteger> indexes = new HashSet<>();
        for (ObjectValue row : nativeOptions) {
            BigInteger index = number(row, "native_option_index");
            require(index != null && index.signum() >= 0 && index.compareTo(BigInteger.valueOf(source.size())) < 0 && indexes.add(index), "fresh native option indexes are not unique source indexes");
        }
        List<ObjectValue> shown = nativeOptions.stream().filter(row -> yes(row, "shown")).toList(); Set<BigInteger> rendered = new HashSet<>();
        require(!shown.isEmpty(), "fresh shown option order is unavailable");
        for (ObjectValue row : shown) {
            BigInteger index = number(row, "rendered_index"); require(index != null && index.signum() >= 0 && rendered.add(index), "fresh shown option order is unavailable");
        }
        ObjectValue selection = o(capture, "selection");
        boolean firstDisplayed = eq(selection, "selection_order", s(UnhandledEventFallback.DisplayPolicy.FIRST_DISPLAYED.wire()));
        List<ObjectValue> enabled = shown.stream().filter(row -> EventOptionAvailability.selectionAllowed(context,row)).toList();
        ObjectValue first = (firstDisplayed || enabled.isEmpty() ? shown : enabled).stream().min(Comparator.comparing(row -> number(row, "rendered_index"))).orElseThrow();
        BigInteger nativeIndex = number(first, "native_option_index");
        require(selection != null && v(selection, "native_option_index").equals(v(first, "native_option_index")) && v(selection, "rendered_index").equals(v(first, "rendered_index"))
            && eq(selection, "option_number", RetainedJson.value(nativeIndex.add(BigInteger.ONE))) && v(selection, "enabled").equals(v(first, "enabled")) && EventOptionAvailability.observation(context,selection).equals(EventOptionAvailability.observation(context,first)), "recorded display policy differs from the bound native option");
        return obj(f("source_event_type", s(eventType)), f("raw_type_index", i(4)), f("type_key", s("character")), f("subtype", i(0)),
            f("typed_identity_kind", s("character")), f("actor_character_id", RetainedJson.value(actor)));
    }
    private static ObjectValue populistShape(ObjectValue capture, ObjectValue facts, NativeBinding current) {
        ObjectValue source = o(facts, "binding");
        require(current.build().equals("1.20.0.4") && current.eventKey().equals("faction_demand.1001") && current.backend().equals(BACKEND)
            && current.optionCount().equals(BigInteger.valueOf(4)) && eq(source, "source_sha256", s(FACTION_SOURCE)) && eq(source, "option_catalogue_sha256", s(POPULIST_OPTIONS)), "reviewed populist letter source/catalogue differs");
        ObjectValue shape = rootShape(capture, facts, current, "letter_event"), context = o(capture, "window_context"), frame = o(capture, "binding");
        require(yes(frame, "paused") && yes(frame, "map_ready") && eq(frame, "snapshot_id", s("native:" + number(frame, "native_revision")))
            && positive(number(frame, "bridge_pid")) && positive(number(frame, "connection_generation")) && text(frame, "episode_run_id") != null && !text(frame, "episode_run_id").isEmpty()
            && eq(context, "window_match_count", i(1)) && ExistingFactionEventPolicies.recognizesPopulist(context, number(frame, "actor_character_id"), number(capture, "snapshot_option_count")), "fresh populist letter frame/roles unavailable");
        Map<BigInteger, ObjectValue> options = ExistingFactionEventPolicies.byNative(objects(context, "options"));
        require(eq(options.get(BigInteger.TWO), "rendered_index", i(0)) && eq(options.get(BigInteger.valueOf(3)), "rendered_index", i(1)), "reviewed populist letter rendered layout differs");
        Map<String, ObjectValue> roles = roles(context, false, false);
        for (ExistingFactionEventPolicies.Role role : ExistingFactionEventPolicies.POPULIST_IDENTITIES)
            require(identity(o(roles.get(role.name()), "scope"), role.kind(), role.field()) != null, "fresh populist letter native scope identity unavailable");
        return shape.with("source_rebind_policy", s(POPULIST_POLICY));
    }
    static List<Path> registryEntries(Path directory) throws IOException {
        if (!Files.exists(directory)) return List.of();
        try (var entries = Files.list(directory)) {
            List<Path> scanned = entries.limit(1_025).toList();
            require(scanned.size() <= 1_024, "event source registry directory scan exceeds 1024 entries");
            List<Path> paths = scanned.stream().filter(path -> path.getFileName().toString().endsWith(".json"))
                .sorted(Comparator.comparing(Path::toString)).toList();
            require(paths.size() <= 128, "event source registry exceeds 128 entry files");
            return paths;
        }
    }
    static byte[] read(Path path, int maximum, TrustedEventSourceContext trusted,
            TrustedEventSourceContext.FileRole role) throws IOException {
        return trusted == null ? read(path, maximum) : trusted.read(path, maximum, role);
    }
    static byte[] read(Path path, int maximum) throws IOException {
        BasicFileAttributes before = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        require(before.isRegularFile() && !before.isSymbolicLink() && before.fileKey() != null, "regular identity-bearing source file required");
        require(before.size() <= maximum, "offline incident/source receipt exceeds its bounded JSON input");
        try (InputStream stream = Files.newInputStream(path)) {
            byte[] raw = stream.readNBytes(maximum + 1);
            BasicFileAttributes after = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
            require(raw.length <= maximum, "offline incident/source receipt exceeds its bounded JSON input");
            require(after.isRegularFile() && !after.isSymbolicLink() && Objects.equals(before.fileKey(), after.fileKey())
                && before.size() == after.size() && raw.length == after.size() && before.lastModifiedTime().equals(after.lastModifiedTime()), "source file identity/content changed during read");
            return raw;
        }
    }
    private static String stem(Path path) { String name = path.getFileName().toString(); return name.substring(0, name.length() - 5); }
}
