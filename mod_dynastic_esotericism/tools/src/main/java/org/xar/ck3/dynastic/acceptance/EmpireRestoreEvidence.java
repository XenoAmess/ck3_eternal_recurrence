package org.xar.ck3.dynastic.acceptance;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Stream;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SelectedInspection;

/** Read-only ordinary stock UI evidence reducer. It never submits a Game action.
 * Raw SDK documents and an independently re-decoded Save are the inputs, not Root booleans.
 * Layout selectors are explicit input, and their record identities are checked before use.
 */
public final class EmpireRestoreEvidence {
    private EmpireRestoreEvidence() { }
    private static final JsonMapper JSON = JsonMapper.builder()
            .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
            .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
            .enable(DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES)
            .enable(DeserializationFeature.FAIL_ON_NULL_CREATOR_PROPERTIES)
            .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT)
            .disable(MapperFeature.ALLOW_COERCION_OF_SCALARS).build();
    private static final String EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final String TITLE_GUI = "c030230fa9468b02b94f65ef6895a48dad9157aa7292d55c94a35d0288518be3";
    private static final String DIALOG_GUI = "b83ca05ff9aab1eab38d079512c4e1a2c0154b9a8f12c0082c652ca7eef6fa16";
    private static final long MAX_PACKAGE = 128L * 1024 * 1024;
    public enum Phase { PREPARE, PRE_CONFIRM, VERIFY }
    public enum Origin { STOCK_TITLE_UI_COMMAND }
    public enum PopupObservation { UNKNOWN, HIDDEN_OBSERVED, VISIBLE_OBSERVED }
    public enum CaseId {
        empire_heads_procreation_restore("e_des_procreation_papacy"),
        empire_heads_vivhite_restore("e_des_vivhite_papacy");
        private final String title;
        CaseId(String title) { this.title = title; }
        public String title() { return title; }
    }
    public record Wire(Pin file, String pointer) {
        public Wire {
            Objects.requireNonNull(file);
            if (pointer == null || pointer.length() > 512 || !pointer.isEmpty() && !pointer.startsWith("/"))
                throw new IllegalArgumentException("bounded explicit JSON pointer required");
        }
    }
    public record Subject(long actor, long faith, long rite, long title, long otherTitle, long coatOfArms) {
        public Subject {
            for (long id : List.of(actor, faith, rite, title, otherTitle, coatOfArms)) u32(id);
            require(title != otherTitle, "another real title is required");
        }
    }
    /** A selector cannot relabel an unrelated record as a Title/actor/Faith observation. */
    public record Selector(ScopeKind kind, NativeId id, List<String> path) {
        public Selector {
            Objects.requireNonNull(kind); Objects.requireNonNull(id); path = List.copyOf(path);
            require(!path.isEmpty() && path.size() <= 16 && path.stream().allMatch(p -> p.matches("[A-Za-z_][A-Za-z0-9_]*")),
                    "explicit bounded named AST path required");
        }
    }
    public record Layout(Selector titleKey, Selector titleHolder, Selector titleHistory, Selector titleCoa,
            Selector otherKey, Selector otherHolder, Selector primaryTitle, Selector riteFaith, Selector actorRite,
            Selector faithTitle, Selector riteData) { }
    public record State(Wire snapshot, Wire process, Wire religionContext, Wire titleHolder, Wire saveProof, Inspection.Request inspection) { }
    public record Stock(Pin titleGui, Pin dialogGui) { }
    public record Chain(Origin origin, Subject subject, Layout layout, Stock stock, State before, State after,
            Wire titleWindow, List<Wire> popupBefore, Wire destroyQuery, Wire destroyAction,
            Wire popupAfter, Wire acceptAction, List<Wire> popupClosed, List<Pin> widgetClaims, Restoration acquisition) { }
    public record Restoration(State before, State after, Wire selectedTerms, Wire decisionOutcome) { }
    public record Request(String schema, Phase phase, String machineId, String caseId, String runId,
            Pin verifierPackage, Pin startupSave, Chain chain, List<State> loaded, List<Wire> loadedTerms, List<Restoration> restoration) {
        public Request {
            require("ck3-empire-restore-evidence-request-v1".equals(schema), "wrong request schema");
            Objects.requireNonNull(phase); text(machineId); CaseId.valueOf(caseId); text(runId);
            Objects.requireNonNull(verifierPackage); Objects.requireNonNull(startupSave); Objects.requireNonNull(chain);
            loaded = List.copyOf(loaded); loadedTerms = List.copyOf(loadedTerms); restoration = List.copyOf(restoration);
            require(loadedTerms.size() == loaded.size(), "loaded terms cardinality differs");
            require(loaded.size() == (phase == Phase.PREPARE ? 0 : 1), "loaded state cardinality differs from phase");
            require(restoration.size() == (phase == Phase.VERIFY ? 1 : 0), "restoration cardinality differs from phase");
        }
    }
    public record Result(String schema, String machineId, String caseId, String runId, Phase phase,
            Pin request, Pin verifierPackage, Pin s1Save, Subject subject, List<Pin> evidence,
            List<SelectedInspection.Report> saveInspections, long destroyPrestigeRaw, List<Long> restoreResourceDeltaRaw, boolean qualified,
            boolean titleLossPostconditionQualified, boolean restoredTitlePostconditionQualified,
            boolean domainTypedDestroyTargetObserved, boolean destroyExactPrequoteObserved,
            PopupObservation popupBeforeState, PopupObservation popupAfterState,
            boolean nativePopupInstanceIdentityObserved, boolean originalPopupInstanceGoneQualified,
            boolean gameStarted, boolean businessPass, boolean productReleasePass) {
        public Result { evidence = List.copyOf(evidence); saveInspections = List.copyOf(saveInspections); restoreResourceDeltaRaw = List.copyOf(restoreResourceDeltaRaw); }
    }
    public record PackageFile(String relative, Pin pin) {
        public PackageFile { EmpireRestoreEvidence.relative(relative); Objects.requireNonNull(pin); }
    }
    public record VerifierPackage(String schema, String machineId, Pin javaExecutable, Pin entrypoint,
            List<PackageFile> files, List<PackageFile> producerSources) {
        public VerifierPackage {
            require("ck3-empire-restore-verifier-package-v1".equals(schema), "wrong verifier package schema");
            text(machineId); Objects.requireNonNull(javaExecutable); Objects.requireNonNull(entrypoint);
            files = List.copyOf(files); producerSources = List.copyOf(producerSources);
            require(!files.isEmpty() && files.size() <= 512 && !producerSources.isEmpty()
                    && producerSources.size() <= 512, "bounded complete package required");
            require(files.stream().anyMatch(f -> f.relative().equals("quarkus-run.jar") && f.pin().equals(entrypoint)),
                    "the package must contain its actual Quarkus entrypoint");
            unique(files); unique(producerSources);
            require(producerSources.stream().anyMatch(f -> f.relative().endsWith("/EmpireRestoreEvidence.java")),
                    "shared reducer source is absent");
        }
    }
    private record Frame(long pid, String birth, long actor, long date, long revision, String connection, String run) { }
    private record Saved(State source, Frame frame, long faith, long rite, long mainRite, long titleId, Long holder, String titleKey, SelectedInspection.Report selected) { }
    private static final class Reads {
        private final List<Pin> pins = new ArrayList<>();
        private final List<Saved> saved = new ArrayList<>();
        byte[] bytes(Pin pin, long limit) throws IOException {
            checkPath(pin);
            Path p = Path.of(pin.path());
            BasicFileAttributes before = Files.readAttributes(p, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            require(before.isRegularFile() && !before.isSymbolicLink() && before.size() == pin.bytes()
                    && before.size() <= limit, "file size/type exceeds bound: " + p);
            byte[] bytes = Files.readAllBytes(p);
            BasicFileAttributes after = Files.readAttributes(p, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            require(Objects.equals(before.fileKey(), after.fileKey()) && before.size() == after.size()
                    && before.lastModifiedTime().equals(after.lastModifiedTime())
                    && bytes.length == pin.bytes() && sha(bytes).equals(pin.sha256()), "file changed: " + p);
            if (!pins.contains(pin)) pins.add(pin);
            return bytes;
        }
        JsonNode json(Wire wire) throws IOException {
            JsonNode n = JSON.readTree(bytes(wire.file(), 2 * 1024 * 1024)).at(wire.pointer());
            require(n.isObject(), "actual wire object unavailable at explicit pointer");
            return n;
        }
        void unchanged() throws IOException {
            for (Pin p : List.copyOf(pins)) {
                // Saves may exceed the small JSON bound; hash via the streaming Pin implementation.
                require(pin(Path.of(p.path())).equals(p), "evidence changed after reduction");
            }
        }
    }
    public static Result reduce(Request request, Pin requestPin) throws IOException {
        return reduce(request, requestPin, org.xar.ck3.save.SaveDecoder::launch);
    }
    /** Shared real producer seam; authored tests supply a decoder, never a second business reducer. */
    public static Result reduce(Request q, Pin requestPin, org.xar.ck3.save.SaveDecoder.Launcher launcher)
            throws IOException {
        return reduce(q, requestPin, launcher, EmpireRestoreEvidence::stock);
    }
    @FunctionalInterface interface StockVerifier { void verify(Stock value) throws IOException; }
    private static void stock(Stock value) throws IOException {
        require(pin(Path.of(value.titleGui().path())).equals(value.titleGui())
                && pin(Path.of(value.dialogGui().path())).equals(value.dialogGui())
                && value.titleGui().sha256().equals(TITLE_GUI) && value.dialogGui().sha256().equals(DIALOG_GUI),
                "stock callback definitions changed");
    }
    static Result reduce(Request q, Pin requestPin, org.xar.ck3.save.SaveDecoder.Launcher launcher,
            StockVerifier stockVerifier) throws IOException {
        Reads reads = new Reads();
        VerifierPackage pkg = readPackage(q.verifierPackage());
        require(pkg.machineId().equals(q.machineId()), "verifier machine differs");
        CaseId kind = CaseId.valueOf(q.caseId());
        Chain c = q.chain(); require(q.startupSave().equals(c.after().inspection().save()), "startup Save differs from S1");
        require(c.origin() == Origin.STOCK_TITLE_UI_COMMAND, "unsupported preparation origin");
        Subject s = c.subject(); validateLayout(c.layout(), s);
        reads.bytes(c.stock().titleGui(), 1024 * 1024); reads.bytes(c.stock().dialogGui(), 1024 * 1024);
        stockVerifier.verify(c.stock());
        Saved before = state(c.before(), q.machineId(), reads, launcher);
        Saved after = state(c.after(), q.machineId(), reads, launcher);
        sameScene(before.frame(), after.frame(), true);
        if (q.phase() == Phase.PREPARE) require(q.runId().equals(after.frame().run()), "preallocation must bind the original S1 producer run");
        require(before.frame().actor() == s.actor(), "preparation actor changed");
        holders(before, c.layout(), s, kind, false);
        Restoration acquisition = c.acquisition();
        Saved acquiredBefore = state(acquisition.before(), q.machineId(), reads, launcher);
        Saved acquired = state(acquisition.after(), q.machineId(), reads, launcher);
        sameScene(acquiredBefore.frame(), acquired.frame(), true);
        require(acquired.frame().actor() == s.actor() && acquired.frame().date() <= before.frame().date(),
                "paid acquisition identity/date differs");
        target(acquiredBefore, c.layout(), s, kind, true, false);
        target(acquired, c.layout(), s, kind, false);
        paid(acquisition, acquiredBefore.frame(), reads);
        history(acquired, before, c.layout().titleHistory()); coa(acquired, before, s, kind);
        holders(after, c.layout(), s, kind, true);
        history(before, after, c.layout().titleHistory());
        destroyedHistory(before, after, c.layout().titleHistory());
        coa(before, after, s, kind);
        require(doctrines(before, c.layout()).equals(doctrines(after, c.layout())),
                "Rite doctrines changed");
        JsonNode title = reads.json(c.titleWindow());
        build(title);
        require(string(title, "schema").equals("ck3-ingame-ui-window-v1")
                && string(title, "window_kind").equals("title"), "wrong title window");
        yes(title, "available", "accepted", "paused", "window_exists", "effective_visible", "subject_id_available",
                "application_owner_thread_verified", "gui_owner_binding_verified");
        not(title, "dispatch_invoked", "verification_pending");
        require(string(title, "status").equals("observed")
                && integer(title, "played_character_id") == before.frame().actor()
                && integer(title, "date_raw") == before.frame().date(), "selected title window actor/date changed");
        require(integer(title, "current_subject_id") == s.title(), "selected full TitleID changed");
        PopupObservation prior = popupObservation(c.popupBefore(), reads, before.frame());
        require(prior != PopupObservation.VISIBLE_OBSERVED, "known visible prior confirmation must be resolved first");
        JsonNode destroy = query(reads.json(c.destroyQuery()), "title_view_window", before.frame(), true);
        require(integer(title, "native_revision") <= integer(destroy, "native_revision"),
                "title selection was observed after the command query");
        if (!c.popupBefore().isEmpty()) require(integer(reads.json(c.popupBefore().getFirst()), "native_revision") <= integer(destroy, "native_revision"),
                "prior popup observation was captured after destroy");
        JsonNode button = uniqueButton(destroy, "destroy_title");
        action(reads.json(c.destroyAction()), destroy, button, before.frame());
        JsonNode popup = query(reads.json(c.popupAfter()), "basic_confirmation_popup", before.frame(), true);
        if (prior == PopupObservation.HIDDEN_OBSERVED) increasing(reads.json(c.popupBefore().getFirst()), destroy);
        increasing(destroy, popup);
        JsonNode accept = uniqueButton(popup, "accept_button");
        action(reads.json(c.acceptAction()), popup, accept, before.frame());
        require(!c.destroyAction().file().equals(c.acceptAction().file()), "the two actions cannot share one receipt");
        PopupObservation closed = popupObservation(c.popupClosed(), reads, after.frame());
        if (!c.popupClosed().isEmpty()) require(integer(reads.json(c.popupClosed().getFirst()), "native_revision") >= integer(popup, "native_revision")
                && integer(reads.json(c.popupClosed().getFirst()), "native_revision") <= after.frame().revision(),
                "post-popup observation crossed the independent after frame");
        if (closed != PopupObservation.UNKNOWN) increasing(popup, reads.json(c.popupClosed().getFirst()));
        widgetClaims(c, reads, destroy, popup, button, accept, before.frame());
        long destroyCost = Math.subtractExact(wallet(reads.json(c.before().snapshot()), "prestige"),
                wallet(reads.json(c.after().snapshot()), "prestige"));
        require(destroyCost > 0, "ordinary destruction did not deduct observed prestige");
        require(!c.before().inspection().save().equals(c.after().inspection().save()), "S0 and S1 Save are the same input");
        for (State load : q.loaded()) {
            Saved current = state(load, q.machineId(), reads, launcher);
            require(current.frame().run().equals(q.runId()) && current.frame().actor() == s.actor(), "loaded actor/run changed");
            require(current.frame().date() == after.frame().date(), "loaded S1 date changed");
            history(after, current, c.layout().titleHistory());
            holders(current, c.layout(), s, kind, true); coa(after, current, s, kind);
            require(doctrines(after, c.layout()).equals(doctrines(current, c.layout())), "loaded doctrines changed");
            quote(reads.json(q.loadedTerms().getFirst()), current.frame());
        }
        List<Long> deltas = List.of();
        if (q.phase() == Phase.VERIFY) {
            Restoration r = q.restoration().getFirst();
            Saved rb = state(r.before(), q.machineId(), reads, launcher);
            Saved ra = state(r.after(), q.machineId(), reads, launcher);
            sameScene(rb.frame(), ra.frame(), true);
            require(rb.frame().run().equals(q.runId()) && rb.frame().actor() == s.actor(), "restore run/actor changed");
            Saved loaded = state(q.loaded().getFirst(), q.machineId(), reads, launcher);
            require(rb.frame().date() >= loaded.frame().date() && ra.frame().date() - loaded.frame().date() <= 48,
                    "restore exceeded two natural days");
            holders(rb, c.layout(), s, kind, true); holders(ra, c.layout(), s, kind, false);
            history(after, ra, c.layout().titleHistory()); coa(after, ra, s, kind);
            require(doctrines(after, c.layout()).equals(doctrines(ra, c.layout())), "restored doctrines changed");
            require(r.before().equals(q.loaded().getFirst()) && r.selectedTerms().equals(q.loadedTerms().getFirst()),
                    "confirmation source differs from public pre-confirm qualification");
            deltas = paid(r, rb.frame(), reads);
        }
        require(readPackage(q.verifierPackage()).equals(pkg), "verifier package changed during reduction");
        reads.unchanged();
        return new Result("ck3-empire-restore-evidence-result-v1", q.machineId(), q.caseId(), q.runId(), q.phase(),
                requestPin, q.verifierPackage(), c.after().inspection().save(), s, reads.pins,
                reads.saved.stream().map(Saved::selected).toList(), destroyCost, deltas,
                true, true, q.phase() == Phase.VERIFY, false, false, prior, closed, false, false, false, false, false);
    }
    private static Saved state(State s, String machine, Reads reads, org.xar.ck3.save.SaveDecoder.Launcher launcher)
            throws IOException {
        for (Saved cached : reads.saved) if (cached.source().equals(s)) return cached;
        require(s.inspection().machineId().equals(machine), "Save producer machine differs");
        JsonNode snapshot = reads.json(s.snapshot());
        JsonNode process = reads.json(s.process());
        Frame f = snapshot(snapshot, process, machine);
        JsonNode religion = reads.json(s.religionContext()); build(religion);
        require(string(religion, "schema").equals("ck3_12004_religion_context_v1"), "wrong current religion context");
        yes(religion, "available");
        require(integer(religion, "played_character_id") == f.actor() && integer(religion, "date_raw") == f.date()
                && integer(religion, "capture_epoch") > 0 && integer(religion, "raw_scale") == 100000
                && religion.has("unavailable_reason") && religion.get("unavailable_reason").isNull(), "current religion context changed");
        JsonNode proof = reads.json(s.saveProof());
        require(string(proof, "status").equals("verified")
                && string(proof, "scope").equals("producer_materialization_and_native_bracketing"), "Save proof is not ordinary");
        yes(proof, "independent_after_request", "same_retained_case_client", "consumer_rehashed_file");
        require(integer(proof, "actor") == f.actor() && integer(proof, "bridge_pid") == f.pid()
                && integer(proof, "connection_generation") == Long.parseUnsignedLong(f.connection())
                && string(proof, "managed_run_id").equals(f.run()), "Save owner/instance changed");
        JsonNode file = object(proof, "file");
        Pin save = new Pin(string(file, "path"), integer(file, "bytes"), string(file, "sha256"));
        require(save.equals(s.inspection().save()) && integer(file, "date_raw") == f.date(), "Save identity/date changed");
        require(pin(Path.of(save.path())).equals(save), "actual Save differs");
        if (!reads.pins.contains(save)) reads.pins.add(save);
        require(pin(Path.of(s.inspection().decoder().path())).equals(s.inspection().decoder()), "decoder differs");
        if (!reads.pins.contains(s.inspection().decoder())) reads.pins.add(s.inspection().decoder());
        SelectedInspection.Report selected = SelectedInspection.inspect(s.inspection(), launcher);
        require(selected.decoder().originalWait().exitCode() == 0 && selected.decoder().completeStream() && selected.decoder().saveUnchanged(), "Save decode did not finish");
        JsonNode holder = reads.json(s.titleHolder()); build(holder);
        require(string(holder, "schema").equals("xar.ck3.title-holder.v1")
                && integer(holder, "schema_version") == 1 && string(holder, "status").equals("available"),
                "current native title holder unavailable");
        yes(holder, "available", "title_key_available");
        require(integer(holder, "title_tier_raw") == 5 && string(holder, "title_tier_key").equals("empire")
                && string(holder, "title_key_status").equals("available")
                && holder.has("unavailable_reason") && holder.get("unavailable_reason").isNull()
                && holder.has("title_key_unavailable_reason") && holder.get("title_key_unavailable_reason").isNull(),
                "native target tier/key availability differs");
        require(integer(holder, "actor_character_id") == f.actor() && integer(holder, "date_raw") == f.date()
                && integer(holder, "snapshot_revision") == f.revision(), "native title holder frame changed");
        long titleId = u32(integer(holder, "title_id"));
        // Existing v1 holder tool is int32-bounded. Preserve the full incoming TitleID and refuse
        // unsupported high IDs; never truncate/reinterpret a uint32 TitleView observation.
        require(titleId <= Integer.MAX_VALUE, "existing holder tool cannot qualify this full TitleID");
        JsonNode held = holder.get("holder_character_id");
        require(held != null, "holder null observation is missing");
        Long owner = held.isNull() ? null : u32(integral(held));
        require(bool(holder, "holder_is_player") == (owner != null && owner == f.actor()), "native holder identity differs");
        require(owner == null ? !bool(holder, "holder_in_player_realm") : bool(holder, "holder_in_player_realm"),
                "native holder realm observation differs");
        Saved result = new Saved(s, f, u32(integer(religion, "faith_id")), u32(integer(religion, "rite_id")),
                u32(integer(religion, "faith_main_rite_id")), titleId, owner, string(holder, "title_key"), selected);
        reads.saved.add(result); return result;
    }
    private static Frame snapshot(JsonNode n, JsonNode process, String machine) {
        require(string(n, "episode_projection").equals("native_campaign")
                && string(n, "source").equals("injected-dll-named-pipe")
                && string(n, "backend_id").equals("native-headless"), "ordinary native snapshot required");
        yes(n, "paused", "map_ready");
        JsonNode a = object(n, "played_character"); yes(a, "alive");
        require(string(a, "source").equals("native"), "actor is not native");
        JsonNode d = object(n, "diagnostics"); yes(d, "connected");
        JsonNode hello = object(d, "hello"); yes(hello, "ck3_build_match");
        require(string(hello, "expected_ck3_version").equals("1.20.0.4")
                && string(hello, "expected_ck3_sha256").equalsIgnoreCase(EXE), "snapshot exact build differs");
        JsonNode run = object(n, "managed_campaign_run_binding");
        require(string(d, "pipe_name").equals(string(run, "bridge_pipe")), "native run pipe differs");
        require(string(process, "machine_id").equals(machine)
                && string(process, "run_id").equals(string(run, "run_id"))
                && integer(process, "pid") == integer(d, "bridge_pid"), "actual OS process differs");
        String birth = decimal(process, "birth_filetime");
        return new Frame(integer(d, "bridge_pid"), birth, u32(integer(a, "character_id")), integer(n, "date_raw"),
                integer(n, "native_revision"), Long.toUnsignedString(integer(d, "connection_generation")), string(run, "run_id"));
    }
    private static JsonNode query(JsonNode n, String root, Frame f, boolean visible) {
        build(n); yes(n, "available", "complete", "owner_thread_verified", "source_abi_pins_verified", "frame_verified");
        not(n, "truncated");
        require(string(n, "schema").equals("ck3-native-scripted-widget-controls-v1")
                && string(n, "root_name").equals(root) && string(n, "unavailable_reason").isEmpty(), "wrong/unavailable root query");
        wireFrame(n, f);
        decimal(n, "query_generation");
        JsonNode rows = n.get("widgets"); require(rows != null && rows.isArray() && rows.size() <= 8192, "bounded widget rows required");
        Set<String> ids = new HashSet<>(), paths = new HashSet<>();
        int roots = 0;
        for (JsonNode row : rows) {
            require(ids.add(decimal(row, "widget_id")) && paths.add(string(row, "child_path")), "duplicate control");
            if (string(row, "child_path").isEmpty()) {
                roots++; require(string(row, "runtime_name").equals(root)
                        && bool(row, "effective_visible") == visible, "root visibility changed");
            }
        }
        require(roots == 1, "one complete root required; root_unavailable is not absence");
        return n;
    }
    private static JsonNode uniqueButton(JsonNode n, String name) {
        List<JsonNode> rows = new ArrayList<>();
        for (JsonNode row : n.get("widgets")) if (string(row, "runtime_name").equals(name)
                && bool(row, "effective_visible")) rows.add(row);
        require(rows.size() == 1, "visible native button is not unique");
        JsonNode row = rows.getFirst(); yes(row, "enabled", "clickable"); return row;
    }
    private static void action(JsonNode n, JsonNode query, JsonNode target, Frame f) {
        build(n); wireFrame(n, f);
        require(string(n, "schema").equals("ck3-native-scripted-widget-control-action-v1")
                && string(n, "root_name").equals(string(query, "root_name"))
                && decimal(n, "query_generation").equals(decimal(query, "query_generation"))
                && decimal(n, "widget_id").equals(decimal(target, "widget_id"))
                && string(n, "unavailable_reason").isEmpty(), "action is stale/unknown or has a different target");
        yes(n, "available", "dispatch_attempted", "dispatch_invoked", "native_handled", "verification_pending",
                "owner_thread_verified", "source_abi_pins_verified", "frame_verified");
        not(n, "postcondition_verified");
        require(integer(n, "native_revision") == integer(query, "native_revision"), "action crossed query revision");
    }
    private static void wireFrame(JsonNode n, Frame f) {
        require(integer(n, "game_pid") == f.pid() && integer(n, "played_character_id") == f.actor()
                && integer(n, "date_raw") == f.date()
                && decimal(n, "connection_generation").equals(f.connection()), "native frame/instance changed");
    }
    private static void widgetClaims(Chain chain, Reads reads, JsonNode destroy, JsonNode popup,
            JsonNode destroyButton, JsonNode acceptButton, Frame frame) throws IOException {
        List<Pin> pins = List.copyOf(chain.widgetClaims());
        require(!pins.isEmpty() && pins.size() <= 1024, "bounded complete SDK claim inventory required");
        Path directory = Path.of(pins.getFirst().path()).getParent();
        JsonNode snapshot = reads.json(chain.before().snapshot());
        Path state = Path.of(string(object(snapshot, "managed_campaign_run_binding"), "state_dir")).toAbsolutePath().normalize();
        require(directory.startsWith(state) && directory.getFileName().toString().equals("scripted-widget-controls"),
                "claim directory is outside the actual source scene");
        Set<Path> supplied = new HashSet<>();
        for (Pin p : pins) require(supplied.add(Path.of(p.path())) && Path.of(p.path()).getParent().equals(directory),
                "duplicate or cross-directory claim");
        Set<Path> actual = new HashSet<>();
        try (var stream = Files.newDirectoryStream(directory, "*.claim.json")) {
            for (Path p : stream) { require(actual.size() < 1024, "SDK claim inventory exceeded"); actual.add(p); }
        }
        require(actual.equals(supplied), "SDK claim inventory has extra/missing entries");
        int destroyMatches = 0, acceptMatches = 0;
        for (Pin p : pins) {
            JsonNode claim = reads.json(new Wire(p, ""));
            require(string(claim, "schema").equals("ck3-scripted-widget-once-claim-v1")
                    && string(claim, "status").equals("claimed_result_unknown_no_retry"), "wrong SDK widget claim");
            JsonNode identity = object(claim, "action_identity");
            if (integer(identity, "game_pid") != frame.pid()
                    || integer(identity, "played_character_id") != frame.actor()) continue;
            boolean target = sameControl(identity, destroy, destroyButton) || sameControl(identity, popup, acceptButton);
            if (!target) continue;
            String leaf = Path.of(p.path()).getFileName().toString();
            Path dispatchPath = directory.resolve(leaf.substring(0, leaf.length() - 5) + ".dispatch.json");
            JsonNode dispatch = reads.json(new Wire(pin(dispatchPath), ""));
            require(string(dispatch, "request_id").equals(string(claim, "request_id")), "widget dispatch claim changed");
            JsonNode result = object(dispatch, "result"); yes(result, "available", "dispatch_invoked");
            String generation = decimal(claim, "query_generation");
            if (generation.equals(decimal(destroy, "query_generation"))) {
                require(decimal(claim, "widget_id").equals(decimal(destroyButton, "widget_id")), "destroy claim target differs");
                destroyMatches++;
            }
            if (generation.equals(decimal(popup, "query_generation"))) {
                require(decimal(claim, "widget_id").equals(decimal(acceptButton, "widget_id")), "accept claim target differs");
                acceptMatches++;
            }
            require(decimal(result, "query_generation").equals(generation)
                    && decimal(result, "widget_id").equals(decimal(claim, "widget_id")), "dispatch references differ");
            // Original SDK persistence uses exact native integers; public MCP uses decimal strings.
            // Compare against the explicit serialization conversion, without a field-name alias.
            com.fasterxml.jackson.databind.node.ObjectNode publicResult = ((com.fasterxml.jackson.databind.node.ObjectNode) result).deepCopy();
            publicResult.put("native_revision", Long.toString(integral(result.get("native_revision"))));
            publicResult.put("connection_generation", Long.toString(integral(result.get("connection_generation"))));
            if (generation.equals(decimal(destroy, "query_generation")))
                require(publicResult.equals(reads.json(chain.destroyAction())), "original destroy dispatch differs");
            if (generation.equals(decimal(popup, "query_generation")))
                require(publicResult.equals(reads.json(chain.acceptAction())), "original accept dispatch differs");
        }
        require(destroyMatches == 1 && acceptMatches == 1, "not exactly one original destroy and accept claim");
    }
    private static boolean sameControl(JsonNode identity, JsonNode query, JsonNode button) {
        return string(identity, "root_name").equals(string(query, "root_name"))
                && string(identity, "runtime_name").equals(string(button, "runtime_name"))
                && string(identity, "child_path").equals(string(button, "child_path"))
                && integer(identity, "vtable_rva") == integer(button, "vtable_rva");
    }
    private static void increasing(JsonNode first, JsonNode second) {
        require(new java.math.BigInteger(decimal(second, "query_generation")).compareTo(
                new java.math.BigInteger(decimal(first, "query_generation"))) > 0, "query replay/order changed");
        require(integer(second, "native_revision") >= integer(first, "native_revision"), "revision moved backwards");
    }
    private static PopupObservation popupObservation(List<Wire> observations, Reads reads, Frame frame) throws IOException {
        require(observations != null && observations.size() <= 1, "at most one explicit popup observation per boundary");
        if (observations.isEmpty()) return PopupObservation.UNKNOWN;
        JsonNode n = reads.json(observations.getFirst()); build(n);
        require(string(n, "schema").equals("ck3-native-scripted-widget-controls-v1")
                && string(n, "root_name").equals("basic_confirmation_popup"), "wrong popup diagnostic source");
        wireFrame(n, frame);
        yes(n, "owner_thread_verified", "source_abi_pins_verified", "frame_verified");
        if (!bool(n, "available")) {
            // Failure to resolve a root never proves absence, invisibility, an old instance
            // disappearing, or a successful action. Preserve it solely as UNKNOWN.
            require(string(n, "unavailable_reason").equals("scripted_widget_root_unavailable")
                    && string(n, "query_generation").equals("0") && !bool(n, "complete")
                    && n.get("widgets") != null && n.get("widgets").isArray() && n.get("widgets").isEmpty(),
                    "popup unavailable for another reason, incomplete source or identity drift");
            return PopupObservation.UNKNOWN;
        }
        JsonNode rows = n.get("widgets");
        require(rows != null && rows.isArray(), "popup rows unavailable");
        List<JsonNode> roots = new ArrayList<>();
        for (JsonNode row : rows) if (string(row, "child_path").isEmpty()) roots.add(row);
        require(roots.size() == 1, "ambiguous popup root");
        boolean visible = bool(roots.getFirst(), "effective_visible");
        query(n, "basic_confirmation_popup", frame, visible);
        return visible ? PopupObservation.VISIBLE_OBSERVED : PopupObservation.HIDDEN_OBSERVED;
    }
    private static void build(JsonNode n) {
        require(string(n, "game_version").equals("1.20.0.4")
                && string(n, "executable_sha256").equalsIgnoreCase(EXE), "native build drift");
    }
    private static List<Long> quote(JsonNode outer, Frame f) {
        build(outer);
        require(string(outer, "schema").equals("ck3-ingame-decision-item-v1")
                && string(outer, "decision_key").equals("create_hof_decision")
                && integer(outer, "matching_row_count") == 1
                && integer(outer, "played_character_id") == f.actor()
                && integer(outer, "detail_actor_reference_key") == f.actor()
                && integer(outer, "game_pid") == f.pid()
                && integer(outer, "connection_generation") == Long.parseUnsignedLong(f.connection())
                && integer(outer, "date_raw") == f.date(), "selected outer model identity differs");
        yes(outer, "available", "owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified",
                "detail_definition_matches_target", "detail_tree_complete", "detail_root_visible", "detail_actor_binding_verified");
        JsonNode n = object(outer, "selected_terms");
        build(n);
        require(string(n, "schema").equals("ck3-selected-decision-terms-v1")
                && string(n, "decision_key").equals("create_hof_decision"), "wrong terms");
        yes(n, "available", "read_only", "context_verified", "requirements_bypass_observed",
                "ordinary_legality_observed", "ordinary_can_confirm", "can_confirm",
                "requirements_description_available", "cost_description_available", "resource_quote_available");
        not(n, "action_ready", "decision_confirm_invoked");
        require(integer(n, "requirements_bypass_raw") == 0 && integer(n, "played_character_id") == f.actor()
                && integer(n, "date_raw") == f.date(), "ordinary full terms/actor unavailable");
        require(string(n, "context_adapter").equals("actual_create_hof_stock_default_parameter_only")
                && integer(n, "named_parameter_count") == 1 && integer(n, "capture_epoch") > 0,
                "stock default parameter context required");
        JsonNode parameter = object(n, "stock_default_parameter");
        require(string(parameter, "token_source").equals("stock_detail_default_token_slot_0x5D4C0D8")
                && integer(parameter, "canonical_token") > 0 && integer(parameter, "key") > 0
                && integer(parameter, "scope_kind") == 4 && integer(parameter, "scope_flags") == 0
                && integer(parameter, "scope_payload") == 0xffffffffL, "stock parameter identity differs");
        yes(parameter, "no_custom_controller");
        JsonNode q = object(n, "resource_quote"); yes(q, "native_affordable");
        require(integer(q, "raw_scale") == 100000, "resource scale differs");
        JsonNode vector = q.get("resource_vector_raw");
        require(vector != null && vector.isArray() && vector.size() == 10, "full ten resource quote required");
        List<Long> values = new ArrayList<>();
        for (JsonNode v : vector) values.add(integral(v));
        return List.copyOf(values);
    }
    private static List<Long> paid(Restoration r, Frame f, Reads reads) throws IOException {
        List<Long> quote = quote(reads.json(r.selectedTerms()), f);
        JsonNode outcome = reads.json(r.decisionOutcome()); build(outcome);
        require(string(outcome, "schema").equals("ck3-ingame-decision-outcome-confirm-v1")
                && string(outcome, "step").equals("confirm-ingame-decision-outcome-v1")
                && string(outcome, "action").equals("confirm_outcome")
                && string(outcome, "status").equals("observed_decision_detail_closed")
                && string(outcome, "decision_key").equals("create_hof_decision"), "wrong decision outcome");
        JsonNode ack = object(outcome, "native_ack");
        yes(ack, "verification_pending", "no_blocking_modal_verified"); not(ack, "postcondition_verified");
        require(string(ack, "status").equals("acknowledged_verification_pending"), "decision ACK missing");
        JsonNode detail = object(outcome, "later_actual_observation");
        require(string(detail, "schema").equals("ck3-native-gui-window-tree-inspection-v1")
                && string(detail, "window_kind").equals("decision_detail")
                && string(detail, "scope_root_name").equals("decisiondetail_view"), "wrong later original detail census");
        yes(detail, "root_available", "read_only"); not(detail, "truncated");
        JsonNode rows = detail.get("widgets"); require(rows != null && rows.isArray()
                && integer(detail, "widget_count") == rows.size(), "incomplete later original census");
        int roots = 0;
        for (JsonNode row : rows) if (string(row, "child_path").isEmpty()) {
            roots++; require(string(row, "runtime_name").equals("decisiondetail_view"), "wrong decision root");
            not(row, "effective_visible");
        }
        require(roots == 1, "decision detail is not independently closed");
        Path claimPath = Path.of(string(outcome, "action_claim_path"));
        JsonNode claim = reads.json(new Wire(pin(claimPath), ""));
        require(string(claim, "schema").equals("ck3-ingame-decision-outcome-once-claim-v1")
                && string(claim, "request_id").equals(string(outcome, "action_request_id"))
                && string(claim, "decision_key").equals("create_hof_decision")
                && string(claim, "expected_outcome").equals("decision_closed"), "original decision claim differs");
        String leaf = claimPath.getFileName().toString();
        require(leaf.endsWith(".json"), "original decision claim path differs");
        Path verifiedPath = claimPath.resolveSibling(leaf.substring(0, leaf.length() - 5) + ".verified.json");
        JsonNode verified = reads.json(new Wire(pin(verifiedPath), ""));
        require(string(verified, "schema").equals("ck3-ingame-decision-action-independent-verification-v1")
                && string(verified, "request_id").equals(string(outcome, "action_request_id"))
                && object(verified, "result").equals(outcome), "original independent verified claim differs");
        yes(outcome, "postcondition_verified"); not(outcome, "verification_pending");
        require(string(outcome, "expected_outcome").equals("decision_closed")
                && integer(outcome, "played_character_id") == f.actor()
                && integer(outcome, "game_pid") == f.pid()
                && integer(outcome, "connection_generation") == Long.parseUnsignedLong(f.connection())
                && integer(outcome, "date_raw") == f.date(), "wrong original outcome/owner");
        List<Long> observed = new ArrayList<>();
        JsonNode bs = reads.json(r.before().snapshot()), as = reads.json(r.after().snapshot());
        for (String resource : List.of("gold", "prestige", "piety"))
            observed.add(Math.subtractExact(wallet(bs, resource), wallet(as, resource)));
        for (int i = 0; i < 10; i++) require(quote.get(i) == (i < 3 ? observed.get(i) : 0L),
                "full ten quote differs from actual wallet delta or an unobserved nonzero resource");
        require(observed.stream().anyMatch(v -> v > 0), "free creation is not paid restoration");
        return List.copyOf(observed);
    }
    private static long wallet(JsonNode snapshot, String resource) {
        JsonNode value = object(snapshot, "played_character_" + resource);
        require(integer(value, "scale") == 100000, "wallet scale differs"); return integer(value, "raw");
    }
    private static void validateLayout(Layout l, Subject s) {
        for (Selector v : List.of(l.titleKey(), l.titleHolder(), l.titleHistory(), l.titleCoa()))
            selector(v, "TITLE", s.title());
        for (Selector v : List.of(l.otherKey(), l.otherHolder())) selector(v, "TITLE", s.otherTitle());
        for (Selector v : List.of(l.primaryTitle(), l.actorRite())) selector(v, "ACTOR", s.actor());
        selector(l.faithTitle(), "FAITH", s.faith());
        for (Selector v : List.of(l.riteFaith(), l.riteData())) selector(v, "RITE", s.rite());
        require(l.primaryTitle().path().equals(List.of("landed_data", "domain"))
                && l.actorRite().path().equals(List.of("jens_179"))
                && l.riteFaith().path().equals(List.of("faith"))
                && l.faithTitle().path().equals(List.of("religious_head"))
                && l.riteData().path().equals(List.of("data")), "observed exact-build Save layout differs");
        require(l.titleKey().path().equals(List.of("key")) && l.titleHolder().path().equals(List.of("holder"))
                && l.titleHistory().path().equals(List.of("history")) && l.titleCoa().path().equals(List.of("coat_of_arms_id"))
                && l.otherKey().path().equals(List.of("key")) && l.otherHolder().path().equals(List.of("holder")),
                "TITLE selectors differ from the observed 1.20.0.4 layout");
    }
    private static void selector(Selector v, String kind, long id) {
        require(v.kind().name().equals(kind) && v.id().value().equals(Long.toString(id)), "selector record identity differs");
    }
    private static Clausewitz.Value value(Saved s, Selector selector, boolean missingAllowed) {
        List<Scope> found = s.selected().selected().scopes().stream().filter(scope -> scope.kind() == selector.kind()
                && scope.coverage() == Coverage.FULL_RECORD && scope.path().getLast().equals(selector.id().value())).toList();
        require(found.size() == 1, "full independent selected record required");
        List<String> prefix = switch (selector.kind()) {
            case TITLE -> List.of("landed_titles", "landed_titles");
            case ACTOR -> List.of("living");
            case RITE -> List.of("jens_180", "database");
            case FAITH -> List.of("faiths", "database");
            default -> throw new IllegalArgumentException("unsupported exact-build selector table");
        };
        List<String> expected = new ArrayList<>(prefix); expected.add(selector.id().value());
        require(found.getFirst().path().equals(expected), "selected record table differs from actual observed layout");
        Clausewitz.Value value = found.getFirst().ast();
        for (int i = 0; i < selector.path().size(); i++) {
            require(value instanceof Clausewitz.Block, "selector traversed a scalar");
            List<Clausewitz.Entry> entries = ((Clausewitz.Block) value).named(selector.path().get(i));
            if (entries.isEmpty() && missingAllowed && i == selector.path().size() - 1) return new Clausewitz.Atom("none");
            require(entries.size() == 1, "selected Save field missing/ambiguous");
            value = entries.getFirst().value();
        }
        return value;
    }
    private static String atom(Saved s, Selector p, boolean missing) {
        Clausewitz.Value v = value(s, p, missing);
        require(v instanceof Clausewitz.Atom, "selected Save atom required");
        String token = ((Clausewitz.Atom) v).token();
        return token.startsWith("\"") && token.endsWith("\"") ? token.substring(1, token.length() - 1) : token;
    }
    private static void holders(Saved state, Layout l, Subject s, CaseId kind, boolean headless) {
        target(state, l, s, kind, headless);
        String other = atom(state, l.otherKey(), false);
        require((other.startsWith("e_") || other.startsWith("h_")) && !other.equals(kind.title()), "another Empire/higher required");
        require(atom(state, l.otherHolder(), false).equals(Long.toString(s.actor()))
                && domainPrimary(state, l.primaryTitle()).equals(Long.toString(s.otherTitle())), "other title holder/primary changed");
    }
    private static void target(Saved state, Layout l, Subject s, CaseId kind, boolean headless) {
        target(state, l, s, kind, headless, true);
    }
    private static void target(Saved state, Layout l, Subject s, CaseId kind, boolean headless, boolean requireCoa) {
        require(state.faith() == s.faith() && state.rite() == s.rite() && state.mainRite() == s.rite(),
                "current Faith/Rite is not the qualified main Rite");
        require(state.titleId() == s.title() && state.titleKey().equals(kind.title()), "native target identity changed");
        require(headless ? state.holder() == null : state.holder() != null && state.holder() == s.actor(),
                "current native target holder differs");
        require(atom(state, l.titleKey(), false).equals(kind.title()), "wrong static target title");
        require(atom(state, l.riteFaith(), false).equals(Long.toString(s.faith()))
                && atom(state, l.actorRite(), false).equals(Long.toString(s.rite())), "actor Faith/Rite changed");
        if (requireCoa) require(atom(state, l.titleCoa(), false).equals(Long.toString(s.coatOfArms())), "fixed title CoA changed");
        require(atom(state, l.faithTitle(), false).equals(Long.toString(s.title())), "Faith title pointer changed");
        doctrines(state, l);
        String holder = atom(state, l.titleHolder(), headless);
        if (headless) require(holder.equals("none"), "Save is not holderless/headless");
        else require(holder.equals(Long.toString(s.actor())), "Save holder/head differs");
    }
    private static String domainPrimary(Saved state, Selector selector) {
        Clausewitz.Value v = value(state, selector, false);
        require(v instanceof Clausewitz.Block, "actual actor domain list unavailable");
        List<Clausewitz.Entry> entries = ((Clausewitz.Block) v).entries();
        require(!entries.isEmpty() && entries.getFirst().key().isEmpty()
                && entries.getFirst().value() instanceof Clausewitz.Atom, "actual first domain title unavailable");
        return ((Clausewitz.Atom) entries.getFirst().value()).token();
    }
    private static Set<String> doctrines(Saved state, Layout layout) {
        Clausewitz.Value v = value(state, layout.riteData(), false);
        require(v instanceof Clausewitz.Block, "actual Rite data unavailable");
        Set<String> result = new HashSet<>();
        for (Clausewitz.Entry e : ((Clausewitz.Block) v).named("doctrine")) {
            require(e.value() instanceof Clausewitz.Atom && result.add(((Clausewitz.Atom) e.value()).token()),
                    "actual Rite doctrine missing/duplicated");
        }
        require(result.contains("\"doctrine_theocracy_temporal\"") && result.contains("\"doctrine_temporal_head\""),
                "user's clergy/temporal-head doctrine pair changed");
        return Set.copyOf(result);
    }
    private static void history(Saved before, Saved after, Selector selector) {
        Clausewitz.Value a = value(before, selector, false), b = value(after, selector, false);
        require(a instanceof Clausewitz.Block && b instanceof Clausewitz.Block, "real persisted history required");
        List<Clausewitz.Entry> old = ((Clausewitz.Block) a).entries(), now = ((Clausewitz.Block) b).entries();
        require(old.stream().anyMatch(e -> e.value() instanceof Clausewitz.Atom atom
                && atom.token().equals(Long.toString(before.frame().actor()))), "title lacks the original actor's actual acquisition history");
        require(!old.isEmpty() && now.size() >= old.size() && now.subList(0, old.size()).equals(old), "title history lost/rewritten");
    }
    private static void destroyedHistory(Saved before, Saved after, Selector selector) {
        List<Clausewitz.Entry> old = ((Clausewitz.Block) value(before, selector, false)).entries();
        List<Clausewitz.Entry> now = ((Clausewitz.Block) value(after, selector, false)).entries();
        require(now.subList(old.size(), now.size()).stream().anyMatch(e ->
                e.value() instanceof Clausewitz.Block block && block.atom("type", "").equals("destroyed")),
                "S1 lacks a newly persisted ordinary destruction history entry");
    }
    private static void coa(Saved before, Saved after, Subject s, CaseId kind) {
        List<Scope> a = before.selected().selected().scopes().stream().filter(v -> v.kind() == ScopeKind.COAT_OF_ARMS
                && v.path().getLast().equals(Long.toString(s.coatOfArms()))).toList();
        List<Scope> b = after.selected().selected().scopes().stream().filter(v -> v.kind() == ScopeKind.COAT_OF_ARMS
                && v.path().getLast().equals(Long.toString(s.coatOfArms()))).toList();
        require(a.size() == 1 && b.size() == 1 && a.getFirst().coverage() == Coverage.FULL_RECORD
                && b.getFirst().coverage() == Coverage.FULL_RECORD
                && a.getFirst().path().equals(List.of("coat_of_arms", "coat_of_arms_manager_database", Long.toString(s.coatOfArms())))
                && b.getFirst().path().equals(a.getFirst().path())
                && a.getFirst().ast().equals(b.getFirst().ast()), "CoA content changed/unobserved");
        List<Clausewitz.Entry> emblems = a.getFirst().ast().named("textured_emblem");
        require(emblems.size() == 1 && emblems.getFirst().value() instanceof Clausewitz.Block, "supplied textured emblem unavailable");
        String texture = ((Clausewitz.Block) emblems.getFirst().value()).atom("texture", "");
        require(texture.equals(kind == CaseId.empire_heads_procreation_restore
                ? "\"des_procreation.dds\"" : "\"des_vivhite.dds\""), "selected Save does not retain the fixed Faith DDS");
    }
    private static void sameScene(Frame a, Frame b, boolean sameDate) {
        require(a.pid() == b.pid() && a.birth().equals(b.birth()) && a.actor() == b.actor() && a.connection().equals(b.connection())
                && a.run().equals(b.run()) && (!sameDate || a.date() == b.date())
                && b.revision() >= a.revision(), "native instance/role/date drift");
    }
    public static int run(String[] args) {
        return run(args, org.xar.ck3.save.SaveDecoder::launch, EmpireRestoreEvidence::stock);
    }
    static int run(String[] args, org.xar.ck3.save.SaveDecoder.Launcher launcher, StockVerifier stockVerifier) {
        try {
            require(args.length == 4 && args[0].equals("--inputs") && args[2].equals("--output"),
                    "empire-restore requires --inputs request.json --output unused-result.json");
            Path input = Path.of(args[1]).toAbsolutePath().normalize(), out = Path.of(args[3]).toAbsolutePath().normalize();
            require(Files.size(input) <= 65536 && !Files.exists(out, LinkOption.NOFOLLOW_LINKS), "bounded request/unused output required");
            Pin requestPin = pin(input);
            Request request = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(input), Request.class);
            Result result = reduce(request, requestPin, launcher, stockVerifier);
            require(pin(input).equals(requestPin), "request changed while reducing");
            Files.createDirectories(out.getParent());
            byte[] report = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(result);
            require(report.length <= 8 * 1024 * 1024, "finite reducer output exceeded");
            Files.write(out, report, StandardOpenOption.CREATE_NEW);
            System.out.println(JSON.writeValueAsString(pin(out))); return 0;
        } catch (IOException | IllegalArgumentException | ArithmeticException error) {
            System.err.println("EMPIRE RESTORE EVIDENCE REJECTED: " + error.getMessage()); return 1;
        }
    }
    public static int packageRun(String[] args) {
        try {
            require(args.length == 10 && args[0].equals("--repo-root") && args[2].equals("--app-root")
                    && args[4].equals("--java-executable") && args[6].equals("--output") && args[8].equals("--machine-id"),
                    "exact package options required");
            Pin result = packageArtifact(Path.of(args[1]).toRealPath(), Path.of(args[3]).toRealPath(),
                    Path.of(args[5]).toRealPath(), Path.of(args[7]).toAbsolutePath().normalize(), args[9]);
            System.out.println(JSON.writeValueAsString(result)); return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("EMPIRE RESTORE PACKAGE REJECTED: " + error.getMessage()); return 1;
        }
    }
    public static VerifierPackage readPackage(Pin declaration) throws IOException {
        checkPath(declaration); require(Files.size(Path.of(declaration.path())) <= 262144, "package metadata bound exceeded");
        require(pin(Path.of(declaration.path())).equals(declaration), "package metadata differs");
        VerifierPackage p = org.xar.ck3.save.SaveJson.read(Files.readAllBytes(Path.of(declaration.path())), VerifierPackage.class);
        require(pin(Path.of(p.javaExecutable().path())).equals(p.javaExecutable()), "Java executable differs");
        Path app = Path.of(p.entrypoint().path()).getParent();
        Set<Path> expectedFiles = new HashSet<>();
        long total = 0;
        for (PackageFile f : p.files()) {
            Path exact = app.resolve(f.relative()).normalize();
            require(exact.startsWith(app) && exact.equals(Path.of(f.pin().path())), "artifact escaped declared package path");
            total = Math.addExact(total, f.pin().bytes());
            require(pin(exact).equals(f.pin()) && expectedFiles.add(exact), "verifier artifact differs/duplicates");
        }
        Set<Path> actualFiles = new HashSet<>();
        try (Stream<Path> stream = Files.walk(app)) {
            for (Path f : stream.toList()) {
                require(!Files.isSymbolicLink(f), "symlink in verifier package");
                if (Files.isRegularFile(f, LinkOption.NOFOLLOW_LINKS) && !f.equals(Path.of(declaration.path())))
                    require(actualFiles.add(f) && actualFiles.size() <= 512, "verifier file inventory exceeded");
            }
        }
        require(expectedFiles.equals(actualFiles) && total <= MAX_PACKAGE, "finite complete verifier closure differs");
        for (PackageFile f : p.producerSources()) require(pin(Path.of(f.pin().path())).equals(f.pin()), "verifier producer source differs");
        return p;
    }
    /** Called only by the existing composer; no Game/Native qualification is granted. */
    public static Pin freezePackage(Pin declaration, Path repository, Path frozenSource, Path output, String machine)
            throws IOException {
        VerifierPackage old = readPackage(declaration);
        require(old.machineId().equals(machine), "package machine differs");
        require(!Files.exists(output, LinkOption.NOFOLLOW_LINKS), "fresh verifier destination required");
        List<PackageFile> sources = new ArrayList<>(), files = new ArrayList<>();
        require(sourceFiles(repository).equals(old.producerSources()), "incomplete/noncanonical producer source closure");
        for (PackageFile f : old.producerSources()) {
            require(pin(repository.resolve(f.relative())).equals(f.pin()), "package source is not current canonical source");
            Pin actual = pin(frozenSource.resolve(f.relative()));
            require(actual.bytes() == f.pin().bytes() && actual.sha256().equals(f.pin().sha256()), "frozen source differs");
            sources.add(new PackageFile(f.relative(), actual));
        }
        Files.createDirectory(output);
        Pin entrypoint = null;
        for (PackageFile f : old.files()) {
            Path target = output.resolve(f.relative()); Files.createDirectories(target.getParent());
            Files.copy(Path.of(f.pin().path()), target, StandardCopyOption.COPY_ATTRIBUTES);
            Pin copied = pin(target);
            require(copied.bytes() == f.pin().bytes() && copied.sha256().equals(f.pin().sha256()), "copied verifier differs");
            files.add(new PackageFile(f.relative(), copied));
            if (f.relative().equals("quarkus-run.jar")) entrypoint = copied;
        }
        require(entrypoint != null, "entrypoint missing");
        VerifierPackage result = new VerifierPackage(old.schema(), machine, old.javaExecutable(), entrypoint, files, sources);
        Path meta = output.resolve("verifier-package.json");
        Files.write(meta, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(result), StandardOpenOption.CREATE_NEW);
        return pin(meta);
    }
    /** Inventory construction is source/build binding only, not a successful build/live assertion. */
    public static Pin packageArtifact(Path repo, Path app, Path java, Path output, String machine) throws IOException {
        require(!Files.exists(output, LinkOption.NOFOLLOW_LINKS), "unused package metadata required");
        List<PackageFile> files = new ArrayList<>(), sources = new ArrayList<>();
        try (Stream<Path> stream = Files.walk(app)) {
            for (Path f : stream.filter(Files::isRegularFile).sorted().toList())
                files.add(new PackageFile(app.relativize(f).toString().replace('\\', '/'), pin(f)));
        }
        sources.addAll(sourceFiles(repo));
        VerifierPackage pkg = new VerifierPackage("ck3-empire-restore-verifier-package-v1", machine,
                pin(java), pin(app.resolve("quarkus-run.jar")), files, sources);
        Files.createDirectories(output.getParent());
        Files.write(output, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(pkg), StandardOpenOption.CREATE_NEW);
        Pin result = pin(output); readPackage(result); return result;
    }
    private static List<PackageFile> sourceFiles(Path repo) throws IOException {
        List<PackageFile> sources = new ArrayList<>();
        for (String root : List.of("mod_dynastic_esotericism/tools/src/main/java", "java/ck3-save-core/src/main/java")) {
            try (Stream<Path> stream = Files.walk(repo.resolve(root))) {
                for (Path f : stream.filter(p -> p.toString().endsWith(".java")).sorted().toList())
                    sources.add(new PackageFile(repo.relativize(f).toString().replace('\\', '/'), pin(f)));
            }
        }
        for (String f : List.of("mod_dynastic_esotericism/tools/pom.xml", "java/ck3-save-core/pom.xml"))
            sources.add(new PackageFile(f, pin(repo.resolve(f))));
        return List.copyOf(sources);
    }
    private static void unique(List<PackageFile> files) {
        Set<String> names = new HashSet<>();
        for (PackageFile f : files) require(names.add(f.relative()), "duplicate package relative path");
    }
    private static String relative(String p) {
        require(p != null && !p.isEmpty() && !p.contains("\\") && !p.contains(":")
                && !p.startsWith("/") && List.of(p.split("/", -1)).stream().noneMatch(x -> x.isEmpty() || x.equals(".") || x.equals("..")),
                "canonical relative package path required"); return p;
    }
    public static Pin pin(Path path) throws IOException {
        Path p = path.toAbsolutePath().normalize();
        BasicFileAttributes a = Files.readAttributes(p, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        require(a.isRegularFile() && !a.isSymbolicLink(), "regular non-symlink file required");
        MessageDigest digest = digest();
        try (var in = Files.newInputStream(p)) { byte[] b = new byte[65536]; for (int n; (n = in.read(b)) != -1;) digest.update(b, 0, n); }
        BasicFileAttributes b = Files.readAttributes(p, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        require(Objects.equals(a.fileKey(), b.fileKey()) && a.size() == b.size()
                && a.lastModifiedTime().equals(b.lastModifiedTime()), "file changed while pinning");
        return new Pin(p.toString(), a.size(), HexFormat.of().formatHex(digest.digest()));
    }
    private static void checkPath(Pin pin) {
        Path p = Path.of(pin.path());
        require(p.isAbsolute() && p.normalize().equals(p), "absolute normalized Pin required");
    }
    private static JsonNode object(JsonNode n, String key) { JsonNode v = n.get(key); require(v != null && v.isObject(), "missing object " + key); return v; }
    private static String string(JsonNode n, String key) { JsonNode v = n.get(key); require(v != null && v.isTextual(), "missing string " + key); return v.textValue(); }
    private static String decimal(JsonNode n, String key) {
        JsonNode v = n.get(key);
        // Scripted-widget persisted JSON uses native uint64 integers; its public MCP wire uses decimal strings.
        // This reducer accepts the public MCP wire only, except native_revision is a bounded JSON integer
        // in the original title-window provider and is checked by integer() at that boundary.
        require(v != null && v.isTextual() && v.textValue().matches("[1-9][0-9]{0,19}")
                && new java.math.BigInteger(v.textValue()).bitLength() <= 64, "canonical uint64 string required: " + key);
        return v.textValue();
    }
    private static long integral(JsonNode v) { require(v != null && v.isIntegralNumber() && v.canConvertToLong(), "exact int64 required"); return v.longValue(); }
    private static long integer(JsonNode n, String key) {
        // Public scripted-widget native_revision is a decimal string; no bool/float coercion or alias.
        if (key.equals("native_revision") && n.has("query_generation")) return new java.math.BigInteger(decimal(n, key)).longValueExact();
        return integral(n.get(key));
    }
    private static boolean bool(JsonNode n, String key) { JsonNode v = n.get(key); require(v != null && v.isBoolean(), "exact boolean required: " + key); return v.booleanValue(); }
    private static void yes(JsonNode n, String... keys) { for (String k : keys) require(bool(n, k), "native guard false: " + k); }
    private static void not(JsonNode n, String... keys) { for (String k : keys) require(!bool(n, k), "native guard true: " + k); }
    private static long u32(long value) { require(value > 0 && value < 0xffffffffL, "complete uint32 ID required"); return value; }
    private static void text(String v) { require(v != null && !v.isEmpty() && v.length() <= 1024, "bounded text required"); }
    private static void require(boolean ok, String why) { if (!ok) throw new IllegalArgumentException(why); }
    private static MessageDigest digest() { try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); } }
    private static String sha(byte[] b) { return HexFormat.of().formatHex(digest().digest(b)); }
}
