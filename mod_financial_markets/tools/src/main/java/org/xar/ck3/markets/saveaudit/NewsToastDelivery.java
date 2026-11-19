package org.xar.ck3.markets.saveaudit;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.ProducerSources;
import org.xar.ck3.save.SaveContracts;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveDecoder;
import org.xar.ck3.save.SaveJson;

/** Bounded offline join of a source-pinned public toast with its exact saved news/source records. */
public final class NewsToastDelivery {
    private NewsToastDelivery() { }
    private static final BigInteger U32_INVALID = BigInteger.valueOf(0xFFFFFFFFL);
    private static final BigInteger SCALE = BigInteger.valueOf(100000);
    private static final String EXE = "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
    private static final FinancialProjector.LayoutHypothesis LAYOUT = new FinancialProjector.LayoutHypothesis(
            "1.21.0", "19", SCALE, "story", "char", FinancialProjector.NumberIdentityEncoding.unsigned64OmittedZero);
    public enum Kind { CHARACTER, STORY, UNSUPPORTED }
    public enum Stage { UNAVAILABLE, EMPTY, HIDDEN, VISIBLE_PENDING_FRAME, VISIBLE }
    public enum Assessment { UNAVAILABLE, MISMATCH, LOCAL_NATIVE_JOIN_MATCH }
    public enum Reason {
        NATIVE_OBJECT_NOT_VISIBLE, REQUIRED_NAMED_IDENTITY_UNAVAILABLE, RECIPIENT_DIFFERS_FROM_VIEWER,
        ACTOR_DIFFERS_FROM_NEWS, SOURCE_EVENT_NO_LONGER_CURRENT, SOURCE_FACT_DIFFERS_FROM_NEWS, NONE
    }
    // Internal report model: kind/availability disambiguate explicit empty
    // text from an actual identity. Public04 wire nulls remain unchanged.
    public record ScopeIdentity(String name, Kind kind, int observedTag, boolean available, String identity, String unavailableReason) {
        public ScopeIdentity {
            if (name == null || name.isEmpty() || !name.matches("[!-~]{1,192}") || kind == null || identity == null || unavailableReason == null)
                throw new IllegalArgumentException("complete internal saved identity required");
            if (kind == Kind.UNSUPPORTED) {
                if (observedTag < 0 || observedTag > 65535 || observedTag == 4 || observedTag == 22 || available
                        || !identity.isEmpty() || !unavailableReason.equals("scope_tag_not_admitted"))
                    throw new IllegalArgumentException("explicit unsupported internal identity required");
            } else {
                if (!available || observedTag != (kind == Kind.CHARACTER ? 4 : 22) || identity.isEmpty() || !unavailableReason.isEmpty())
                    throw new IllegalArgumentException("complete internal canonical identity required");
                if (kind == Kind.STORY) storyId(identity); else characterId(identity);
            }
        }
    }
    public record NativeIdentity(String snapshotId, String nativeRevision, String publicRevision,
                                 long gamePid, String connectionGeneration, String querySequence,
                                 long ownerThreadId, String completedApplicationFrame, int viewerCharacterId, int dateRaw) { }
    public record ToastObservation(NativeIdentity identity, Stage stage, String title, String description,
                                   List<ScopeIdentity> guiScopes, List<ScopeIdentity> scriptScopes) {
        public ToastObservation { guiScopes = List.copyOf(guiScopes); scriptScopes = List.copyOf(scriptScopes); }
    }
    public record Request(int schemaVersion, String machineId, String repository, Pin toast, Pin save, Pin decoder) {
        public Request {
            if (schemaVersion != 1 || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")
                    || repository == null || !Path.of(repository).isAbsolute() || toast == null || toast.bytes() > 256 * 1024 || save == null || decoder == null)
                throw new IllegalArgumentException("version1 source-pinned offline news join required");
        }
    }
    public record NewsEntry(String storyId, String sourceStoryId, String newsId, String eventId,
                            int kind, String day, int scene, int actorCharacterId) { }
    public record SourceFact(String storyId, String storyCycle, String factCounter, String lastFact,
                             int kind, int scene, int actorCharacterId) { }
    public record SelectedRecord(String name, List<String> path, String canonicalTokenSha256) {
        public SelectedRecord { path = List.copyOf(path); }
    }
    public record PassEvidence(Inspection.Request request, ProducerSources.Binding producer,
                               String streamSha256, String streamBytes, List<SelectedRecord> selected) {
        public PassEvidence { selected = List.copyOf(selected); }
    }
    public record Report(String schema, String machineId, Request request, SaveAuditSources.Binding producers,
                         List<Pin> newsScriptSources, ToastObservation toast, Assessment assessment, Reason reason,
                         List<NewsEntry> entries, List<SourceFact> sources, List<PassEvidence> passes,
                         boolean sourceJoinMatched, boolean deliveryConfirmed, boolean allHumanDeliveryConfirmed,
                         boolean gameStarted, boolean financialCertified) {
        public Report {
            newsScriptSources = List.copyOf(newsScriptSources); passes = List.copyOf(passes);
            entries = List.copyOf(entries); sources = List.copyOf(sources);
            if (!"xfm-news-toast-source-join-candidate-v1".equals(schema) || request == null || producers == null || toast == null
                    || assessment == null || reason == null || !request.machineId().equals(machineId)
                    || deliveryConfirmed || allHumanDeliveryConfirmed || gameStarted || financialCertified
                    || sourceJoinMatched != (assessment == Assessment.LOCAL_NATIVE_JOIN_MATCH)
                    || entries.size() > 1 || sources.size() > 1
                    || sourceJoinMatched && (entries.size() != 1 || sources.size() != 1 || passes.size() != 3 || reason != Reason.NONE))
                throw new IllegalArgumentException("unqualified source join report required");
        }
    }

    /** Exact public DTO boundary; null, bool, float, aliases and surplus fields are not coerced. */
    public static ToastObservation readToast(byte[] bytes) throws IOException {
        if (bytes.length > 256 * 1024) throw new IOException("public toast exceeds256KiB");
        JsonNode raw = SaveJson.read(bytes, JsonNode.class);
        Set<String> fields = Set.of("schema", "step", "game_version", "executable_sha256", "adapter_id", "backend", "status", "accepted",
                "snapshot_id", "native_revision", "connection_generation", "query_sequence", "owner_thread_id",
                "application_main_observed", "full_snapshot_before_verified", "full_snapshot_after_verified", "source_abi_pins_verified",
                "read_only", "effect_attempted", "stage", "completed_application_frame", "queue_count", "title", "description",
                "saved_gui_scopes", "saved_script_scopes", "recipient_identity_available", "news_origin_available", "delivery_confirmed",
                "unavailable_reason", "public_revision", "game_pid", "viewer_played_character_id", "date_raw");
        exactKeys(raw, fields);
        equalsText(raw, "schema", "ck3_1210_current_interface_toast_result_v1");
        equalsText(raw, "step", "query-current-interface-toast-v1"); equalsText(raw, "game_version", "1.21.0");
        equalsText(raw, "executable_sha256", EXE); equalsText(raw, "adapter_id", "ck3-1.21.0-msvc-x64");
        equalsText(raw, "backend", "ck3-1.21.0-native-headless-main-thread");
        for (String key : List.of("effect_attempted", "recipient_identity_available", "news_origin_available", "delivery_confirmed")) flag(raw, key, false);
        flag(raw, "read_only", true);
        String status = text(raw, "status", 32); boolean available = status.equals("available");
        if (!available && !status.equals("unavailable")) throw new IllegalArgumentException("unknown toast status");
        flag(raw, "accepted", available);
        Stage stage = switch (text(raw, "stage", 32)) {
            case "unavailable" -> Stage.UNAVAILABLE; case "empty" -> Stage.EMPTY; case "hidden" -> Stage.HIDDEN;
            case "visible_pending_frame" -> Stage.VISIBLE_PENDING_FRAME; case "visible" -> Stage.VISIBLE;
            default -> throw new IllegalArgumentException("unknown toast stage");
        };
        for (String key : List.of("application_main_observed", "full_snapshot_before_verified", "full_snapshot_after_verified", "source_abi_pins_verified")) {
            if (!raw.get(key).isBoolean() || available && !raw.get(key).booleanValue()) throw new IllegalArgumentException("actual native proof flag required");
        }
        String revision = decimal(raw, "native_revision", false), generation = decimal(raw, "connection_generation", !available);
        equalsText(raw, "snapshot_id", "native:" + revision);
        String publicRevision = decimal(raw, "public_revision", false), sequence = decimal(raw, "query_sequence", !available);
        String frame = decimal(raw, "completed_application_frame", !available);
        long owner = integer(raw, "owner_thread_id", available ? 1 : 0, 0xFFFFFFFFL);
        long pid = integer(raw, "game_pid", 1, 0xFFFFFFFFL);
        int viewer = Math.toIntExact(integer(raw, "viewer_played_character_id", Integer.MIN_VALUE, Integer.MAX_VALUE));
        if (viewer == -1) throw new IllegalArgumentException("invalid viewer CharacterID");
        int date = Math.toIntExact(integer(raw, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE));
        int count = Math.toIntExact(integer(raw, "queue_count", 0, 64));
        String title = text(raw, "title", 8192), description = text(raw, "description", 32768);
        List<ScopeIdentity> gui = scopes(raw.get("saved_gui_scopes")), script = scopes(raw.get("saved_script_scopes"));
        if (gui.size() + script.size() > 64) throw new IllegalArgumentException("combined64 saved scope limit");
        Map<String, ScopeIdentity> names = new HashMap<>();
        for (ScopeIdentity scope : gui) names.put(scope.name(), scope);
        for (ScopeIdentity scope : script) if (names.containsKey(scope.name()) && !names.get(scope.name()).equals(scope))
            throw new IllegalArgumentException("cross-context saved identity mismatch");
        JsonNode why = raw.get("unavailable_reason");
        if (available) {
            if (stage == Stage.UNAVAILABLE || !why.isNull() || (stage == Stage.EMPTY ? count != 0 || !title.isEmpty() || !description.isEmpty() || !gui.isEmpty() || !script.isEmpty() : count == 0))
                throw new IllegalArgumentException("available toast contradicts stage");
        } else if (stage != Stage.UNAVAILABLE || !frame.equals("0") || count != 0 || !title.isEmpty() || !description.isEmpty()
                || !gui.isEmpty() || !script.isEmpty() || !why.isTextual() || why.textValue().isEmpty() || why.textValue().length() > 1024)
            throw new IllegalArgumentException("unavailable toast has partial output");
        return new ToastObservation(new NativeIdentity("native:" + revision, revision, publicRevision, pid, generation, sequence,
                owner, frame, viewer, date), stage, title, description, gui, script);
    }

    public static Report inspect(Request request) throws IOException { return inspect(request, SaveDecoder::launch); }
    public static Report inspect(Request request, SaveDecoder.Launcher launcher) throws IOException {
        Path repository = Path.of(request.repository()).toRealPath();
        SaveAuditSources.Binding producers = SaveAuditSources.verify(repository);
        List<Pin> scripts = scriptPins(repository);
        FilePins.verify(Path.of(request.toast().path()), request.toast());
        ToastObservation toast = readToast(readBounded(Path.of(request.toast().path()), 256 * 1024));
        List<PassEvidence> passes = new ArrayList<>();
        Assessment assessment = Assessment.UNAVAILABLE; Reason reason = Reason.NATIVE_OBJECT_NOT_VISIBLE;
        NewsEntry entry = null; SourceFact source = null;
        if (toast.stage() == Stage.VISIBLE) {
            ScopeIdentity recipient = named(toast, "xfm_news_recipient", Kind.CHARACTER);
            ScopeIdentity display = named(toast, "xfm_news_display_entry", Kind.STORY);
            ScopeIdentity actor = named(toast, "xfm_news_actor", Kind.CHARACTER);
            reason = Reason.REQUIRED_NAMED_IDENTITY_UNAVAILABLE;
            if (recipient != null && display != null && actor != null) {
                if (Integer.parseInt(recipient.identity()) != toast.identity().viewerCharacterId()) {
                    assessment = Assessment.MISMATCH; reason = Reason.RECIPIENT_DIFFERS_FROM_VIEWER;
                } else {
                    // One exact discovery read is necessary because the source ID lives
                    // inside the observed entry. Then the complete entry+source+metadata
                    // selection is decoded twice. No whole story table is retained.
                    Inspection.Report discovery = inspection(request, List.of(display.identity()), launcher);
                    passes.add(evidence(discovery)); verifyMetadata(discovery);
                    entry = entry(display.identity(), selected(discovery, "story_" + display.identity()).ast());
                    List<String> ids = entry.storyId().equals(entry.sourceStoryId()) ? List.of(entry.storyId()) : List.of(entry.storyId(), entry.sourceStoryId());
                    Inspection.Report first = inspection(request, ids, launcher), second = inspection(request, ids, launcher);
                    passes.add(evidence(first)); passes.add(evidence(second)); verifyMetadata(first); verifyMetadata(second);
                    if (!sameStream(discovery, first) || !sameStream(first, second) || !first.decoded().projection().equals(second.decoded().projection())
                            || !selected(discovery, "story_" + display.identity()).equals(selected(first, "story_" + display.identity())))
                        throw new IOException("exact news/source selection changed between complete reads");
                    NewsEntry current = entry(display.identity(), selected(second, "story_" + display.identity()).ast());
                    if (!entry.equals(current)) throw new IOException("news projection changed");
                    source = source(entry.sourceStoryId(), selected(second, "story_" + entry.sourceStoryId()).ast());
                    if (Integer.parseInt(actor.identity()) != entry.actorCharacterId()) {
                        assessment = Assessment.MISMATCH; reason = Reason.ACTOR_DIFFERS_FROM_NEWS;
                    } else if (!entry.eventId().equals(source.factCounter()) || !entry.eventId().equals(source.lastFact())) {
                        assessment = Assessment.UNAVAILABLE; reason = Reason.SOURCE_EVENT_NO_LONGER_CURRENT;
                    } else if (entry.kind() != source.kind() || entry.scene() != source.scene() || entry.actorCharacterId() != source.actorCharacterId()) {
                        assessment = Assessment.MISMATCH; reason = Reason.SOURCE_FACT_DIFFERS_FROM_NEWS;
                    } else { assessment = Assessment.LOCAL_NATIVE_JOIN_MATCH; reason = Reason.NONE; }
                }
            }
        }
        FilePins.verify(Path.of(request.toast().path()), request.toast());
        if (!producers.equals(SaveAuditSources.verify(repository)) || !scripts.equals(scriptPins(repository))) throw new IOException("loaded news join/parser or scripts changed");
        return new Report("xfm-news-toast-source-join-candidate-v1", request.machineId(), request, producers, scripts, toast,
                assessment, reason, entry == null ? List.of() : List.of(entry), source == null ? List.of() : List.of(source),
                passes, assessment == Assessment.LOCAL_NATIVE_JOIN_MATCH, false, false, false, false);
    }
    private static Inspection.Report inspection(Request r, List<String> ids, SaveDecoder.Launcher launcher) throws IOException {
        List<SaveContracts.ProjectionSelection> projections = new ArrayList<>();
        projections.add(new SaveContracts.ProjectionSelection("complete_metadata", SaveContracts.ProjectionKind.OTHER, List.of("meta_data"), 1, 512 * 1024, true));
        for (String id : ids) {
            storyId(id);
            projections.add(SaveContracts.ProjectionSelection.exactStory("story_" + id, id, 512 * 1024, true));
        }
        return Inspection.inspect(new Inspection.Request(4, r.machineId(), r.repository(), r.save(), r.decoder(),
                new SaveContracts.Selection(List.of(), projections, true, false, List.of())), launcher);
    }
    private static boolean sameStream(Inspection.Report a, Inspection.Report b) {
        return a.producer().equals(b.producer()) && a.decoded().save().equals(b.decoded().save()) && a.decoded().decoder().equals(b.decoded().decoder())
                && a.decoded().streamSha256().equals(b.decoded().streamSha256()) && a.decoded().streamBytes().equals(b.decoded().streamBytes());
    }
    private static PassEvidence evidence(Inspection.Report report) {
        return new PassEvidence(report.request(), report.producer(), report.decoded().streamSha256(), report.decoded().streamBytes(),
                report.decoded().projection().projections().stream().map(p -> new SelectedRecord(p.name(), p.path(), p.canonicalTokenSha256())).toList());
    }
    private static SaveContracts.ProjectionScope selected(Inspection.Report report, String name) {
        List<SaveContracts.ProjectionScope> selected = report.decoded().projection().projections().stream().filter(p -> p.name().equals(name)).toList();
        if (selected.size() != 1 || selected.getFirst().occurrence() != 0) throw new IllegalArgumentException("one exact selected record required");
        return selected.getFirst();
    }
    private static void verifyMetadata(Inspection.Report report) {
        Clausewitz.Block metadata = selected(report, "complete_metadata").ast();
        if (!FinancialProjector.unquote(requiredAtom(metadata, "version")).equals("1.21.0") || !requiredAtom(metadata, "save_game_version").equals("19")
                || requiredAtom(metadata, "meta_date").isBlank()) throw new IllegalArgumentException("complete actual1.21/19 SAVE metadata required");
    }
    private static NewsEntry entry(String id, Clausewitz.Block body) {
        if (!FinancialProjector.unquote(requiredAtom(body, "story_cycle")).equals("xfm_news_entry")) throw new IllegalArgumentException("selected Story is not a news entry");
        Map<String, Clausewitz.Block> vars = variables(body);
        return new NewsEntry(id, reference(vars, "xfm_news_source", "story"), positive(vars, "xfm_news_id").toString(), positive(vars, "xfm_news_event_id").toString(),
                bounded(vars, "xfm_news_kind", 1, 10).intValueExact(), nonnegative(vars, "xfm_news_day").toString(), bounded(vars, "xfm_news_scene", 1, 20).intValueExact(), character(vars, "xfm_news_actor"));
    }
    private static SourceFact source(String id, Clausewitz.Block body) {
        String cycle = FinancialProjector.unquote(requiredAtom(body, "story_cycle"));
        if (!cycle.matches("xfm_[A-Za-z0-9_]+")) throw new IllegalArgumentException("news source is not a financial source Story");
        Map<String, Clausewitz.Block> vars = variables(body);
        BigInteger scene = vars.containsKey("xfm_news_scene") ? bounded(vars, "xfm_news_scene", 1, 20) : BigInteger.valueOf(20);
        return new SourceFact(id, cycle, positive(vars, "xfm_news_fact_counter").toString(), positive(vars, "xfm_news_last_fact").toString(), bounded(vars, "xfm_news_kind", 1, 10).intValueExact(), scene.intValueExact(), character(vars, "xfm_news_actor"));
    }
    private static Map<String, Clausewitz.Block> variables(Clausewitz.Block body) {
        Clausewitz.Block list = requiredBlock(requiredBlock(body, "variables"), "data"); Map<String, Clausewitz.Block> result = new HashMap<>();
        if (list.entries().size() > 4096) throw new IllegalArgumentException("bounded saved variable list required");
        for (Clausewitz.Entry e : list.entries()) {
            if (!e.key().isEmpty() || !(e.value() instanceof Clausewitz.Block variable)) throw new IllegalArgumentException("actual saved variable envelope required");
            String name = FinancialProjector.unquote(requiredAtom(variable, "flag")); Clausewitz.Block value = requiredBlock(variable, "data");
            if (result.putIfAbsent(name, value) != null) throw new IllegalArgumentException("duplicate saved variable");
        }
        return Map.copyOf(result);
    }
    private static BigInteger number(Map<String, Clausewitz.Block> vars, String name) {
        Clausewitz.Block value = vars.get(name); if (value == null) throw new IllegalArgumentException("required saved news number missing: " + name);
        return FinancialProjector.exactNumber(value, LAYOUT);
    }
    private static BigInteger positive(Map<String, Clausewitz.Block> vars, String name) {
        BigInteger value = number(vars, name); if (value.signum() <= 0) throw new IllegalArgumentException("positive saved news number required"); return value;
    }
    private static BigInteger nonnegative(Map<String, Clausewitz.Block> vars, String name) {
        BigInteger value = number(vars, name); if (value.signum() < 0) throw new IllegalArgumentException("nonnegative saved news day required"); return value;
    }
    private static BigInteger bounded(Map<String, Clausewitz.Block> vars, String name, int low, int high) {
        BigInteger value = number(vars, name); if (value.compareTo(BigInteger.valueOf(low)) < 0 || value.compareTo(BigInteger.valueOf(high)) > 0)
            throw new IllegalArgumentException("saved news number outside domain"); return value;
    }
    private static String reference(Map<String, Clausewitz.Block> vars, String name, String type) {
        Clausewitz.Block data = vars.get(name); if (data == null || data.entries().size() != 2 || !requiredAtom(data, "type").equals(type))
            throw new IllegalArgumentException("complete observed saved news reference required");
        String id = requiredAtom(data, "identity"); storyId(id); return id;
    }
    private static int character(Map<String, Clausewitz.Block> vars, String name) {
        // Actual known boundary is a canonical uint32 SAVE char identity.
        // Do not reduce an unobserved unsigned64/sign-extended form modulo32.
        long bits = Long.parseLong(reference(vars, name, "char")); return (int) bits;
    }
    private static ScopeIdentity named(ToastObservation toast, String name, Kind kind) {
        ScopeIdentity found = null;
        for (List<ScopeIdentity> collection : List.of(toast.guiScopes(), toast.scriptScopes())) for (ScopeIdentity scope : collection)
            if (scope.name().equals(name) && scope.kind() == kind && scope.available()) {
                if (found != null && !found.equals(scope)) throw new IllegalArgumentException("ambiguous named identity"); found = scope;
            }
        return found;
    }
    private static List<Pin> scriptPins(Path repository) throws IOException {
        return List.of(FilePins.pin(repository.resolve("mod_financial_markets/common/scripted_effects/xfm_news_queue.txt")),
                FilePins.pin(repository.resolve("mod_financial_markets/common/scripted_effects/xfm_news_dispatch.txt")));
    }
    private static String requiredAtom(Clausewitz.Block body, String key) { return FinancialProjector.atom(body, key).orElseThrow(() -> new IllegalArgumentException("required atom absent: " + key)); }
    private static Clausewitz.Block requiredBlock(Clausewitz.Block body, String key) {
        List<Clausewitz.Entry> entries = body.named(key);
        if (entries.size() != 1 || !entries.getFirst().operator().equals("=") || !(entries.getFirst().value() instanceof Clausewitz.Block block))
            throw new IllegalArgumentException("one assigned block required: " + key); return block;
    }
    private static List<ScopeIdentity> scopes(JsonNode node) {
        if (node == null || !node.isArray() || node.size() > 64) throw new IllegalArgumentException("bounded saved scope array required");
        List<ScopeIdentity> result = new ArrayList<>(); Set<String> names = new HashSet<>();
        for (JsonNode row : node) {
            exactKeys(row, Set.of("name", "kind", "observed_tag", "identity_available", "identity", "unavailable_reason"));
            String name = text(row, "name", 192);
            if (name.isEmpty() || !name.matches("[!-~]+") || !names.add(name)) throw new IllegalArgumentException("unique actual scope name required");
            int tag = Math.toIntExact(integer(row, "observed_tag", 0, 65535)); JsonNode available = row.get("identity_available");
            if (!available.isBoolean()) throw new IllegalArgumentException("exact scope availability boolean required");
            Kind kind = switch (text(row, "kind", 16)) { case "character" -> Kind.CHARACTER; case "story" -> Kind.STORY; case "unsupported" -> Kind.UNSUPPORTED;
                default -> throw new IllegalArgumentException("unknown canonical scope kind"); };
            String id = "", reason = "";
            if (kind == Kind.UNSUPPORTED) {
                if (tag == 4 || tag == 22 || available.booleanValue() || !row.get("identity").isNull()) throw new IllegalArgumentException("unknown scope cannot grant an identity");
                equalsText(row, "unavailable_reason", "scope_tag_not_admitted"); reason = "scope_tag_not_admitted";
            } else {
                if (!available.booleanValue() || tag != (kind == Kind.CHARACTER ? 4 : 22) || !row.get("unavailable_reason").isNull())
                    throw new IllegalArgumentException("known canonical scope lacks identity proof");
                id = text(row, "identity", 11);
                if (kind == Kind.STORY) storyId(id);
                else characterId(id);
            }
            result.add(new ScopeIdentity(name, kind, tag, available.booleanValue(), id, reason));
        }
        return List.copyOf(result);
    }
    private static void storyId(String id) {
        if (id == null || !id.matches("0|[1-9][0-9]{0,9}") || new BigInteger(id).compareTo(U32_INVALID) >= 0)
            throw new IllegalArgumentException("canonical valid uint32 identity required");
    }
    private static void characterId(String id) {
        if (id == null || !id.matches("0|-?[1-9][0-9]{0,9}") || new BigInteger(id).compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) < 0
                || new BigInteger(id).compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0 || id.equals("-1"))
            throw new IllegalArgumentException("exact signed32 CharacterID required");
    }
    private static void exactKeys(JsonNode node, Set<String> expected) {
        if (node == null || !node.isObject()) throw new IllegalArgumentException("JSON object required"); Set<String> actual = new HashSet<>();
        node.fieldNames().forEachRemaining(actual::add); if (!actual.equals(expected)) throw new IllegalArgumentException("closed public field contract required");
    }
    private static void equalsText(JsonNode node, String key, String expected) { if (!text(node, key, 256).equals(expected)) throw new IllegalArgumentException("exact " + key + " required"); }
    private static String text(JsonNode node, String key, int max) {
        JsonNode value = node.get(key);
        if (value == null || !value.isTextual() || value.textValue().indexOf('\0') >= 0 || value.textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8).length > max)
            throw new IllegalArgumentException("bounded exact text required: " + key);
        try { java.nio.charset.StandardCharsets.UTF_8.newEncoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).encode(java.nio.CharBuffer.wrap(value.textValue())); }
        catch (java.nio.charset.CharacterCodingException malformed) { throw new IllegalArgumentException("well-formed UTF-8 text required", malformed); }
        return value.textValue();
    }
    private static void flag(JsonNode node, String key, boolean expected) {
        JsonNode value = node.get(key); if (value == null || !value.isBoolean() || value.booleanValue() != expected) throw new IllegalArgumentException("exact boolean required: " + key);
    }
    private static long integer(JsonNode node, String key, long min, long max) {
        JsonNode value = node.get(key); if (value == null || !value.isIntegralNumber() || !value.canConvertToLong() || value.longValue() < min || value.longValue() > max)
            throw new IllegalArgumentException("exact bounded integer required: " + key); return value.longValue();
    }
    private static String decimal(JsonNode node, String key, boolean zero) {
        String value = text(node, key, 20);
        if (!value.matches("0|[1-9][0-9]{0,19}") || new BigInteger(value).bitLength() > 64 || !zero && value.equals("0"))
            throw new IllegalArgumentException("canonical u64 decimal string required: " + key); return value;
    }
    static byte[] readBounded(Path path, int maximum) throws IOException {
        if (maximum < 1 || maximum > 256 * 1024) throw new IllegalArgumentException("bounded news input limit required");
        try (var input = Files.newInputStream(path)) {
            byte[] bytes = input.readNBytes(maximum + 1);
            if (bytes.length > maximum) throw new IOException("news input exceeds byte limit"); return bytes;
        }
    }
}
