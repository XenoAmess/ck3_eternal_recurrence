package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.dynastic.release.ReleaseBuilder;
import org.xar.ck3.dynastic.release.ReleaseProduct;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveJson;
import static org.xar.ck3.dynastic.acceptance.EmpireRestoreEvidence.*;

/** Authored offline contract fixtures. No Game callback, native Can or business qualification.
 * The actual Java reducer and real decoder CHILD process produce the wire consumed by the public adapter.
 * Only the stock-source filesystem dependency is substituted in Driver; production CLI has no such flag.
 */
final class EmpireRestoreEvidenceTest {
    @TempDir Path temporary;
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String MACHINE = "authored-empire-machine";
    private static final String RUN = "authored-restore-run";
    private static final long T = 17681, E = 17690;
    private static final String EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static Path repository() { return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent(); }
    private static Path java() { return Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java"); }
    private record Authored(Request prepare, Request preConfirm, Request verify, Path runtime, Path bundle) { }
    private int serial;

    @Test void actualProducerWireReachesPublicPreparePhaseAndIndependentVerifyForBothTitles() throws Exception {
        Path packageRoot = executableFixtureJar();
        Pin pkg = packageArtifact(repository(), packageRoot, java(), temporary.resolve("package.json"), MACHINE);
        var release = new ReleaseBuilder().build(ReleaseProduct.official(repository().resolve("mod_dynastic_esotericism"),
                ReleaseProduct.LocalizationMode.RELEASE_LOCALIZATION), repository(), temporary.resolve("release"), "0".repeat(40), null, null);
        for (CaseId kind : CaseId.values()) {
            Path root = Files.createDirectory(temporary.resolve(kind.name()));
            Authored f = fixture(root, kind, pkg);
            var emission = FixtureEmitter.emit(repository(), root.resolve("fixture"), MACHINE,
                    FixtureEmitter.CaseKind.parse(kind.name()));
            ObjectNode b = (ObjectNode) JSON.readTree(Files.readAllBytes(f.bundle()));
            b.put("repository", repository().toString()); b.put("release", release.staging().toString());
            b.set("fixture", JSON.valueToTree(pin(emission.manifest())));
            Files.write(f.bundle(), JSON.writeValueAsBytes(b));
            Path log = root.resolve("public-wire.log");
            Process p = python(List.of(repository().resolve("tools/test_prebuilt_fixture_prepare.py").toString(),
                    "--empire-wire", f.bundle().toString())).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            try {
                assertTrue(p.waitFor(120, java.util.concurrent.TimeUnit.SECONDS), "public wire child timed out");
                String output = Files.readString(log);
                assertEquals(0, p.exitValue(), output);
                assertTrue(output.contains("actual shared Java producer -> public prepare/phase/verify"), output);
            } finally { if (p.isAlive()) { p.destroyForcibly(); p.waitFor(); } }
        }
    }

    @Test void unavailablePopupRemainsUnknownWhileIndependentTitleBusinessCanQualify() throws Exception {
        Pin pkg = packageArtifact(repository(), executableFixtureJar(), java(), temporary.resolve("package.json"), MACHINE);
        Path root = Files.createDirectory(temporary.resolve("unknown-popup"));
        Authored f = fixture(root, CaseId.values()[0], pkg);
        ObjectNode unavailable = JSON.createObjectNode(); build(unavailable);
        unavailable.put("schema", "ck3-native-scripted-widget-controls-v1").put("root_name", "basic_confirmation_popup")
                .put("game_pid", 77).put("played_character_id", 1).put("date_raw", 100)
                .put("connection_generation", "2").put("native_revision", "20")
                .put("available", false).put("query_generation", "0").put("complete", false)
                .put("owner_thread_verified", true).put("source_abi_pins_verified", true).put("frame_verified", true)
                .put("unavailable_reason", "scripted_widget_root_unavailable");
        unavailable.putArray("widgets");
        Wire unknownAfter = wire(root, unavailable);
        unavailable.put("native_revision", "10"); Wire unknownBefore = wire(root, unavailable);
        Chain c = f.prepare().chain();
        Chain chain = new Chain(c.origin(), c.subject(), c.layout(), c.stock(), c.before(), c.after(),
                c.titleWindow(), List.of(unknownBefore), c.destroyQuery(), c.destroyAction(), c.popupAfter(),
                c.acceptAction(), List.of(unknownAfter), c.widgetClaims(), c.acquisition());
        Request q = request(Phase.PREPARE, CaseId.values()[0], pkg, chain, List.of(), List.of(), List.of());
        Path request = Files.write(root.resolve("unknown-request.json"), SaveJson.write(q));
        Result result = reduce(q, pin(request),
                (decoder, save) -> new ProcessBuilder(java().toString(), "-cp", System.getProperty("java.class.path"),
                        Driver.class.getName(), "--decoder", save.toString()).start(), stock -> { });
        assertTrue(result.qualified()); assertEquals(PopupObservation.UNKNOWN, result.popupBeforeState());
        assertEquals(PopupObservation.UNKNOWN, result.popupAfterState());
        assertFalse(result.originalPopupInstanceGoneQualified()); assertFalse(result.businessPass());
        assertTrue(result.titleLossPostconditionQualified()); assertFalse(result.restoredTitlePostconditionQualified());
        assertFalse(result.domainTypedDestroyTargetObserved()); assertFalse(result.destroyExactPrequoteObserved());
        // Removing an original dispatch leaves UNKNOWN; a later query never makes it replayable.
        Path claim = Path.of(c.widgetClaims().getFirst().path());
        Files.delete(claim.resolveSibling(claim.getFileName().toString().replace(".json", ".dispatch.json")));
        assertThrows(IOException.class, () -> reduce(q, pin(request),
                (decoder, save) -> new ProcessBuilder(java().toString(), "-cp", System.getProperty("java.class.path"),
                        Driver.class.getName(), "--decoder", save.toString()).start(), stock -> { }));
    }

    @Test void productionStockPinsAndStrictTypedInputRefuseAuthoredOrMalformedClaims() throws Exception {
        Path app = executableFixtureJar();
        Pin pkg = packageArtifact(repository(), app, java(), temporary.resolve("package.json"), MACHINE);
        Authored f = fixture(Files.createDirectory(temporary.resolve("negative")), CaseId.values()[0], pkg);
        Path q = temporary.resolve("request.json");
        Files.write(q, SaveJson.write(f.prepare()));
        assertEquals(1, run(new String[]{"--inputs", q.toString(), "--output", temporary.resolve("must-not-exist.json").toString()}));
        assertFalse(Files.exists(temporary.resolve("must-not-exist.json")), "production CLI cannot accept authored stock source");
        for (String field : List.of("actor", "title", "otherTitle")) {
            ObjectNode raw = JSON.valueToTree(f.prepare());
            ((ObjectNode) raw.path("chain").path("subject")).put(field, true);
            assertThrows(IOException.class, () -> SaveJson.read(JSON.writeValueAsBytes(raw), Request.class));
            ((ObjectNode) raw.path("chain").path("subject")).put(field, 1.0);
            assertThrows(IOException.class, () -> SaveJson.read(JSON.writeValueAsBytes(raw), Request.class));
        }
        assertThrows(IllegalArgumentException.class, () -> new Subject(1, 11, 12, 0xffffffffL, E, 17));
        assertEquals(0xfffffe00L, SaveJson.read(SaveJson.write(new Subject(1, 11, 12, 0xfffffe00L, E, 17)), Subject.class).title());
    }

    private Authored fixture(Path root, CaseId kind, Pin pkg) throws Exception {
        Path oldState = Files.createDirectory(root.resolve("old-state"));
        Path newState = Files.createDirectory(root.resolve("new-state"));
        long money = 500000000L, price = 100000000L, destroyPrice = 120000000L;
        State initial = state(root, oldState, kind, "none", "", money, money, money + price, 77, 8, "old", "111");
        State held = state(root, oldState, kind, "1", "1066.1.1=1", money, money, money, 77, 10, "old", "111");
        State headless = state(root, oldState, kind, "none", "1066.1.1=1 1066.1.1={type=destroyed}",
                money, money - destroyPrice, money, 77, 20, "old", "111");
        State loaded = state(root, newState, kind, "none", "1066.1.1=1 1066.1.1={type=destroyed}",
                money, money - destroyPrice, money, 88, 30, RUN, "222");
        State restored = state(root, newState, kind, "1", "1066.1.1=1 1066.1.1={type=destroyed} 1066.1.1=1",
                money, money - destroyPrice, money - price, 88, 40, RUN, "222");
        Wire oldTerms = terms(root, 77, 8, price);
        Wire terms = terms(root, 88, 30, price);
        Wire oldOutcome = outcome(oldState, 77, 8, "acquisition");
        Wire outcome = outcome(newState, 88, 30, "restoration");
        Stock stock = new Stock(pin(Files.writeString(root.resolve("title.gui"), "AUTHORED_SOURCE_NOT_STOCK")),
                pin(Files.writeString(root.resolve("dialog.gui"), "AUTHORED_SOURCE_NOT_STOCK")));
        Layout layout = new Layout(sel(ScopeKind.TITLE, T, "key"), sel(ScopeKind.TITLE, T, "holder"),
                sel(ScopeKind.TITLE, T, "history"), sel(ScopeKind.TITLE, T, "coat_of_arms_id"),
                sel(ScopeKind.TITLE, E, "key"), sel(ScopeKind.TITLE, E, "holder"),
                new Selector(ScopeKind.ACTOR, new NativeId("1"), List.of("landed_data", "domain")),
                sel(ScopeKind.RITE, 12, "faith"), sel(ScopeKind.ACTOR, 1, "jens_179"),
                sel(ScopeKind.FAITH, 11, "religious_head"), sel(ScopeKind.RITE, 12, "data"));
        Wire prior = widget(root, "basic_confirmation_popup", 1, 10, false, "");
        Wire destroy = widget(root, "title_view_window", 2, 11, true, "destroy_title");
        Wire popup = widget(root, "basic_confirmation_popup", 3, 12, true, "accept_button");
        Wire closed = widget(root, "basic_confirmation_popup", 4, 13, false, "");
        Wire destroyAction = action(root, "title_view_window", 2, 11);
        Wire acceptAction = action(root, "basic_confirmation_popup", 3, 12);
        List<Pin> claims = List.of(claim(oldState, "title_view_window", "destroy_title", 2, destroyAction),
                claim(oldState, "basic_confirmation_popup", "accept_button", 3, acceptAction));
        ObjectNode title = JSON.createObjectNode(); build(title);
        title.put("schema", "ck3-ingame-ui-window-v1").put("window_kind", "title").put("available", true)
                .put("window_exists", true).put("effective_visible", true).put("subject_id_available", true)
                .put("current_subject_id", T).put("native_revision", 10).put("accepted", true).put("paused", true)
                .put("application_owner_thread_verified", true).put("gui_owner_binding_verified", true)
                .put("dispatch_invoked", false).put("verification_pending", false).put("status", "observed")
                .put("played_character_id", 1).put("date_raw", 100);
        Chain chain = new Chain(Origin.STOCK_TITLE_UI_COMMAND, new Subject(1, 11, 12, T, E, 17), layout, stock, held, headless,
                wire(root, title), List.of(prior), destroy, destroyAction, popup, acceptAction, List.of(closed), claims,
                new Restoration(initial, held, oldTerms, oldOutcome));
        Request prepare = request(Phase.PREPARE, kind, pkg, chain, List.of(), List.of(), List.of());
        Request pre = request(Phase.PRE_CONFIRM, kind, pkg, chain, List.of(loaded), List.of(terms), List.of());
        Request verify = request(Phase.VERIFY, kind, pkg, chain, List.of(loaded), List.of(terms),
                List.of(new Restoration(loaded, restored, terms, outcome)));
        Path runtime = Files.write(root.resolve("runtime.json"), JSON.writeValueAsBytes(JSON.createObjectNode()
                .put("machine_id", MACHINE).set("empire_restore_verifier", JSON.valueToTree(pkg))));
        ObjectNode b = JSON.createObjectNode().put("case", kind.name()).put("run_id", RUN);
        b.set("runtime", JSON.valueToTree(pin(runtime))); b.set("prepare", JSON.valueToTree(write(root, prepare)));
        b.set("pre_confirm", JSON.valueToTree(write(root, pre))); b.set("verify", JSON.valueToTree(write(root, verify)));
        b.set("before_snapshot", JSON.readTree(Files.readAllBytes(Path.of(loaded.snapshot().file().path()))));
        b.set("after_snapshot", JSON.readTree(Files.readAllBytes(Path.of(restored.snapshot().file().path()))));
        b.put("state", newState.toString());
        Path bundle = Files.write(root.resolve("bundle.json"), JSON.writeValueAsBytes(b));
        return new Authored(prepare, pre, verify, runtime, bundle);
    }
    private Request request(Phase phase, CaseId kind, Pin pkg, Chain chain, List<State> load, List<Wire> terms, List<Restoration> result) {
        return new Request("ck3-empire-restore-evidence-request-v1", phase, MACHINE, kind.name(), phase == Phase.PREPARE ? "old" : RUN,
                pkg, chain.after().inspection().save(), chain, load, terms, result);
    }
    private Pin write(Path root, Request q) throws IOException { return pin(Files.write(root.resolve("request-" + serial++ + ".json"), SaveJson.write(q))); }
    private Wire wire(Path root, ObjectNode n) throws IOException { return new Wire(pin(Files.write(root.resolve("wire-" + serial++ + ".json"), JSON.writeValueAsBytes(n))), ""); }
    private static Selector sel(ScopeKind kind, long id, String field) { return new Selector(kind, new NativeId(Long.toString(id)), List.of(field)); }
    private State state(Path root, Path state, CaseId kind, String holder, String history,
            long gold, long prestige, long piety, int pid, int revision, String run, String birth) throws IOException {
        ObjectNode snapshot = JSON.createObjectNode().put("episode_projection", "native_campaign").put("backend_id", "native-headless")
                .put("source", "injected-dll-named-pipe").put("paused", true).put("map_ready", true).put("date_raw", 100)
                .put("native_revision", revision).put("revision", revision).put("snapshot_id", "authored:" + revision);
        snapshot.putObject("played_character").put("character_id", 1).put("alive", true).put("source", "native");
        snapshot.putNull("active_event").putNull("pending_character_interaction");
        ObjectNode diagnostics = snapshot.putObject("diagnostics").put("connected", true).put("bridge_pid", pid)
                .put("connection_generation", 2).put("pipe_name", run);
        diagnostics.putObject("hello").put("ck3_build_match", true).put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", EXE);
        snapshot.putObject("managed_campaign_run_binding").put("run_id", run).put("bridge_pipe", run).put("state_dir", state.toString());
        for (String resource : List.of("gold", "prestige", "piety"))
            snapshot.putObject("played_character_" + resource).put("raw", resource.equals("gold") ? gold : resource.equals("prestige") ? prestige : piety).put("scale", 100000);
        Path save = root.resolve("save-" + serial++ + ".ck3");
        String h = holder.equals("none") ? "" : "holder=1";
        Files.writeString(save, "CK3txt meta_data={date=1066.1.1} living={1={jens_179=12 landed_data={domain={" + E + "}}}}"
                + " jens_180={database={12={faith=11 data={doctrine=\"doctrine_temporal_head\" doctrine=\"doctrine_theocracy_temporal\"}}}}"
                + " faiths={database={11={religious_head=" + T + "}}}"
                + " landed_titles={dynamic_templates={} landed_titles={" + T + "={key=\"" + kind.title() + "\" " + h
                + (history.isEmpty() ? "" : " history={" + history + "}") + " coat_of_arms_id=17} "
                + E + "={key=\"e_authored\" holder=1}} index={}} coat_of_arms={coat_of_arms_manager_database={17={textured_emblem={texture=\"" + (kind == CaseId.empire_heads_procreation_restore ? "des_procreation.dds" : "des_vivhite.dds") + "\"}}}}");
        Selection selection = new Selection(List.of(
                new TableSelection(ScopeKind.ACTOR, List.of("living"), List.of(new NativeId("1")), true),
                new TableSelection(ScopeKind.RITE, List.of("jens_180", "database"), List.of(new NativeId("12")), true),
                new TableSelection(ScopeKind.FAITH, List.of("faiths", "database"), List.of(new NativeId("11")), true),
                new TableSelection(ScopeKind.TITLE, List.of("landed_titles", "landed_titles"),
                        List.of(new NativeId(Long.toString(T)), new NativeId(Long.toString(E))), true),
                new TableSelection(ScopeKind.COAT_OF_ARMS, List.of("coat_of_arms", "coat_of_arms_manager_database"), List.of(new NativeId("17")), true)),
                List.of(), true, false, List.of());
        Pin savePin = pin(save);
        ObjectNode proof = JSON.createObjectNode().put("status", "verified").put("scope", "producer_materialization_and_native_bracketing")
                .put("actor", 1).put("bridge_pid", pid).put("connection_generation", 2).put("managed_run_id", run)
                .put("independent_after_request", true).put("same_retained_case_client", true).put("consumer_rehashed_file", true);
        proof.set("file", JSON.valueToTree(savePin)); ((ObjectNode) proof.get("file")).put("date_raw", 100);
        ObjectNode process = JSON.createObjectNode().put("machine_id", MACHINE).put("run_id", run).put("pid", pid).put("birth_filetime", birth);
        ObjectNode religion = JSON.createObjectNode(); build(religion);
        religion.put("schema", "ck3_12004_religion_context_v1").put("available", true).put("capture_epoch", 1)
                .put("played_character_id", 1).put("date_raw", 100).put("faith_id", 11).put("rite_id", 12).put("faith_main_rite_id", 12)
                .put("raw_scale", 100000).putNull("unavailable_reason");
        ObjectNode title = JSON.createObjectNode(); build(title);
        title.put("schema", "xar.ck3.title-holder.v1").put("schema_version", 1).put("status", "available")
                .put("available", true).put("title_key_available", true).put("actor_character_id", 1).put("date_raw", 100)
                .put("snapshot_revision", revision).put("title_id", T).put("title_key", kind.title()).put("holder_is_player", !holder.equals("none"))
                .put("holder_in_player_realm", !holder.equals("none")).put("title_tier_raw", 5).put("title_tier_key", "empire")
                .put("title_key_status", "available").putNull("title_key_unavailable_reason").putNull("unavailable_reason");
        if (holder.equals("none")) title.putNull("holder_character_id"); else title.put("holder_character_id", 1);
        return new State(wire(root, snapshot), wire(root, process), wire(root, religion), wire(root, title), wire(root, proof),
                new Inspection.Request(4, MACHINE, repository().toString(), savePin, pin(java()), selection));
    }
    private static void build(ObjectNode n) { n.put("game_version", "1.20.0.4").put("executable_sha256", EXE); }
    private Wire terms(Path root, int pid, int revision, long price) throws IOException {
        ObjectNode outer = JSON.createObjectNode(); build(outer);
        outer.put("schema", "ck3-ingame-decision-item-v1").put("available", true).put("decision_key", "create_hof_decision")
                .put("played_character_id", 1).put("game_pid", pid).put("connection_generation", 2).put("date_raw", 100)
                .put("native_revision", revision).put("matching_row_count", 1);
        for (String key : List.of("owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified",
                "detail_definition_matches_target", "detail_tree_complete", "detail_root_visible", "detail_actor_binding_verified"))
            outer.put(key, true);
        outer.put("detail_actor_reference_key", 1);
        ObjectNode n = outer.putObject("selected_terms"); build(n);
        n.put("schema", "ck3-selected-decision-terms-v1").put("decision_key", "create_hof_decision")
                .put("played_character_id", 1).put("date_raw", 100).put("action_ready", false).put("decision_confirm_invoked", false)
                .put("requirements_bypass_raw", 0).put("capture_epoch", 1).put("named_parameter_count", 1)
                .put("context_adapter", "actual_create_hof_stock_default_parameter_only");
        for (String key : List.of("available", "read_only", "context_verified", "requirements_bypass_observed",
                "ordinary_legality_observed", "ordinary_can_confirm", "can_confirm", "requirements_description_available",
                "cost_description_available", "resource_quote_available")) n.put(key, true);
        n.putObject("stock_default_parameter").put("token_source", "stock_detail_default_token_slot_0x5D4C0D8")
                .put("canonical_token", 42).put("key", 42).put("scope_kind", 4).put("scope_flags", 0)
                .put("scope_payload", 0xffffffffL).put("no_custom_controller", true);
        ObjectNode quote = n.putObject("resource_quote").put("raw_scale", 100000).put("native_affordable", true);
        var values = quote.putArray("resource_vector_raw");
        for (int i = 0; i < 10; i++) values.add(i == 2 ? price : 0);
        return wire(root, outer);
    }
    private Wire outcome(Path state, int pid, int revision, String name) throws IOException {
        ObjectNode n = JSON.createObjectNode(); build(n);
        n.put("schema", "ck3-ingame-decision-outcome-confirm-v1").put("step", "confirm-ingame-decision-outcome-v1")
                .put("action", "confirm_outcome").put("decision_key", "create_hof_decision").put("expected_outcome", "decision_closed")
                .put("status", "observed_decision_detail_closed").put("postcondition_verified", true).put("verification_pending", false)
                .put("played_character_id", 1).put("game_pid", pid).put("connection_generation", 2).put("date_raw", 100).put("native_revision", revision);
        n.putObject("native_ack").put("status", "acknowledged_verification_pending").put("verification_pending", true)
                .put("postcondition_verified", false).put("no_blocking_modal_verified", true);
        ObjectNode census = n.putObject("later_actual_observation").put("schema", "ck3-native-gui-window-tree-inspection-v1")
                .put("window_kind", "decision_detail").put("scope_root_name", "decisiondetail_view")
                .put("root_available", true).put("read_only", true).put("truncated", false).put("widget_count", 1);
        census.putArray("widgets").addObject().put("child_path", "").put("runtime_name", "decisiondetail_view").put("effective_visible", false);
        Path claim = state.resolve(name + ".claim.json");
        ObjectNode c = JSON.createObjectNode().put("schema", "ck3-ingame-decision-outcome-once-claim-v1")
                .put("request_id", name).put("decision_key", "create_hof_decision").put("expected_outcome", "decision_closed");
        n.put("action_claim_path", claim.toString()).put("action_request_id", name);
        Files.write(claim, JSON.writeValueAsBytes(c));
        ObjectNode verified = JSON.createObjectNode().put("schema", "ck3-ingame-decision-action-independent-verification-v1").put("request_id", name);
        verified.set("result", n); Files.write(claim.resolveSibling(name + ".claim.verified.json"), JSON.writeValueAsBytes(verified));
        return wire(state, n);
    }
    private ObjectNode widgetBase(String root, int generation, int revision) {
        ObjectNode n = JSON.createObjectNode(); build(n);
        n.put("game_pid", 77).put("played_character_id", 1).put("date_raw", 100)
                .put("native_revision", Integer.toString(revision)).put("connection_generation", "2").put("query_generation", Integer.toString(generation))
                .put("root_name", root).put("available", true).put("unavailable_reason", "")
                .put("owner_thread_verified", true).put("source_abi_pins_verified", true).put("frame_verified", true).put("public_revision", Integer.toString(revision));
        return n;
    }
    private Wire widget(Path root, String name, int generation, int revision, boolean visible, String button) throws IOException {
        ObjectNode n = widgetBase(name, generation, revision).put("schema", "ck3-native-scripted-widget-controls-v1")
                .put("step", "query-scripted-widget-controls-v1").put("complete", true).put("truncated", false).put("read_only", true);
        var rows = n.putArray("widgets");
        rows.addObject().put("widget_id", "1").put("runtime_name", name).put("child_path", "").put("vtable_rva", 1)
                .put("effective_visible", visible).put("enabled", true).put("clickable", false);
        if (!button.isEmpty()) rows.addObject().put("widget_id", "2").put("runtime_name", button).put("child_path", "0").put("vtable_rva", 2)
                .put("effective_visible", true).put("enabled", true).put("clickable", true);
        return wire(root, n);
    }
    private Wire action(Path root, String name, int generation, int revision) throws IOException {
        ObjectNode n = widgetBase(name, generation, revision).put("schema", "ck3-native-scripted-widget-control-action-v1")
                .put("step", "activate-scripted-widget-control-v1").put("widget_id", "2").put("dispatch_attempted", true)
                .put("dispatch_invoked", true).put("native_handled", true).put("verification_pending", true).put("postcondition_verified", false);
        return wire(root, n);
    }
    private Pin claim(Path state, String root, String name, int generation, Wire action) throws IOException {
        Path directory = state.resolve("scripted-widget-controls"); Files.createDirectories(directory);
        ObjectNode claim = JSON.createObjectNode().put("schema", "ck3-scripted-widget-once-claim-v1")
                .put("request_id", name).put("query_generation", Integer.toString(generation)).put("widget_id", "2")
                .put("status", "claimed_result_unknown_no_retry");
        claim.putObject("action_identity").put("game_pid", 77).put("played_character_id", 1).put("root_name", root)
                .put("runtime_name", name).put("child_path", "0").put("vtable_rva", 2);
        Path path = directory.resolve(name + ".claim.json"); Files.write(path, JSON.writeValueAsBytes(claim));
        ObjectNode stored = (ObjectNode) JSON.readTree(Files.readAllBytes(Path.of(action.file().path())));
        stored.put("native_revision", Long.parseLong(stored.path("native_revision").textValue())).put("connection_generation", 2);
        ObjectNode dispatch = JSON.createObjectNode().put("request_id", name); dispatch.set("result", stored);
        Files.write(directory.resolve(name + ".claim.dispatch.json"), JSON.writeValueAsBytes(dispatch)); return pin(path);
    }
    private static ProcessBuilder python(List<String> args) {
        List<String> command = new ArrayList<>(List.of(System.getProperty("dynastic.python", "python"), "-B", "-X", "utf8"));
        command.addAll(args); return new ProcessBuilder(command).directory(repository().toFile());
    }
    private Path executableFixtureJar() throws Exception {
        Path app = Files.createDirectory(temporary.resolve("app"));
        Path lib = Files.createDirectory(app.resolve("lib"));
        Set<Path> roots = new java.util.LinkedHashSet<>();
        for (Class<?> type : List.of(EmpireRestoreEvidence.class, EmpireRestoreEvidenceTest.class,
                Inspection.class, org.junit.jupiter.api.Test.class, ObjectMapper.class, com.fasterxml.jackson.core.JsonParser.class, com.fasterxml.jackson.annotation.JsonCreator.class))
            roots.add(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()));
        List<String> classpath = new ArrayList<>();
        for (Path p : roots) if (Files.isRegularFile(p)) {
            Path target = lib.resolve(p.getFileName()); Files.copy(p, target); classpath.add("lib/" + target.getFileName());
        }
        Manifest manifest = new Manifest(); manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS, Driver.class.getName());
        manifest.getMainAttributes().put(Attributes.Name.CLASS_PATH, String.join(" ", classpath));
        Set<String> entries = new HashSet<>();
        try (JarOutputStream out = new JarOutputStream(Files.newOutputStream(app.resolve("quarkus-run.jar")), manifest)) {
            for (Path root : roots) if (Files.isDirectory(root)) {
                try (var stream = Files.walk(root)) {
                    for (Path p : stream.filter(f -> f.toString().endsWith(".class")).toList()) {
                        String entry = root.relativize(p).toString().replace('\\', '/');
                        if (!entries.add(entry)) continue;
                        out.putNextEntry(new JarEntry(entry)); out.write(Files.readAllBytes(p)); out.closeEntry();
                    }
                }
            }
        }
        return app;
    }
    public static final class Driver {
        private Driver() { }
        public static void main(String[] args) throws Exception {
            if (args.length == 2 && args[0].equals("--decoder")) {
                System.out.write(Files.readAllBytes(Path.of(args[1]))); return;
            }
            if (args.length != 5 || !args[0].equals("empire-restore")) throw new IllegalArgumentException("fixture CLI args");
            Path jar = Path.of(Driver.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            int code = EmpireRestoreEvidence.run(java.util.Arrays.copyOfRange(args, 1, args.length),
                    (decoder, save) -> new ProcessBuilder(java().toString(), "-jar", jar.toString(), "--decoder", save.toString()).start(),
                    stock -> {
                        if (!pin(Path.of(stock.titleGui().path())).equals(stock.titleGui())
                                || !pin(Path.of(stock.dialogGui().path())).equals(stock.dialogGui()))
                            throw new IOException("authored stock fixture changed");
                    });
            System.exit(code);
        }
    }
}
