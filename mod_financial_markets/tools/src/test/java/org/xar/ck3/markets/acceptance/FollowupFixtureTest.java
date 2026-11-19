package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.acceptance.FollowupContracts.*;

/** Software qualification only. Generated predicates still require actual CK3 business readback. */
final class FollowupFixtureTest {
    @TempDir Path temporary;
    private static Path repository() { return Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent(); }
    private static Request request(Profile profile, int epoch) {
        var targets = new Targets("1", profile == Profile.COLD_RELOAD ? null : "2", null, null,
                profile == Profile.LIFECYCLE || profile == Profile.INHERITANCE || profile == Profile.NEWS_CRISIS ? "3" : null, null);
        return new Request(2, profile, epoch, new ActorBinding(ActorMode.CURRENT_PLAYER, null), targets,
                profile == Profile.COLD_RELOAD ? new ColdBaseline(7, new AccountBaseline(1000, 200, 0, 0, 0), null, null, null) : null,
                profile == Profile.AI_CAPACITY ? ScaleTier.SMOKE : null);
    }

    @Test void allFollowupProfilesRoundTripThroughActualEmitterAndExistingManifestContract() throws IOException {
        Set<String> allMarkers = new HashSet<>();
        for (Profile profile : Profile.values()) {
            Request input = request(profile, 11);
            Path wire = temporary.resolve(profile.wire() + ".json");
            Files.write(wire, FixtureEmitter.JSON.writeValueAsBytes(input));
            assertEquals(input, FixtureEmitter.readInput(wire));
            var emission = FixtureEmitter.emit(repository(), temporary.resolve(profile.wire()), "synthetic-fixture-machine", FixtureEmitter.readInput(wire));
            var manifest = FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emission.manifest().path())));
            assertEquals(profile.wire(), manifest.path("case_id").textValue());
            assertEquals(6, manifest.path("producer_source_pins").size());
            assertFalse(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
            assertFalse(emission.gameStarted()); assertEquals("NOT_RUN", emission.businessAcceptance());
            assertEquals(input.markers(), FixtureEmitter.JSON.convertValue(manifest.path("receipt").path("required_markers"),
                    FixtureEmitter.JSON.getTypeFactory().constructCollectionType(List.class, String.class)));
            assertEquals(input, FixtureEmitter.readInput(Path.of(emission.fixture()).resolve("_xfma_request.json")));
            for (String marker : input.markers()) assertTrue(allMarkers.add(marker), "cross-profile marker collision");
            String scripts = text(FollowupObservationScripts.render(input));
            for (String marker : input.markers()) assertEquals(1, occurrences(scripts, "debug_log = \"" + marker + "\""), marker);
            assertFalse(scripts.contains("XFMAT: TEST PASS fixture_ready"));
            assertFalse(scripts.contains("${"), "unresolved script substitution");
            var names = manifest.path("files").fieldNames();
            while (names.hasNext()) {
                String name = names.next(); var pin = FixtureEmitter.pin(Path.of(emission.fixture()).resolve(name));
                assertEquals(pin.bytes(), manifest.path("files").path(name).path("bytes").longValue());
                assertEquals(pin.sha256(), manifest.path("files").path(name).path("sha256").textValue());
            }
        }
    }

    @Test void everyGeneratedMutationIsObservationOnlyAndEveryArtifactHasBomAndBalancedSyntax() {
        Pattern writes = Pattern.compile("(?:set_variable|change_variable|remove_variable)\\s*=\\s*\\{\\s*name\\s*=\\s*([a-z0-9_]+)");
        Pattern businessCall = Pattern.compile("\\bxfm_[a-z0-9_]+_effect\\s*=");
        Pattern businessCreate = Pattern.compile("create_story\\s*=\\s*\\{\\s*type\\s*=\\s*([a-z0-9_]+)");
        for (Profile profile : Profile.values()) {
            Request input = request(profile, 21);
            FollowupObservationScripts.render(input).forEach((name, bytes) -> {
                assertArrayEquals(new byte[]{(byte)0xef, (byte)0xbb, (byte)0xbf}, java.util.Arrays.copyOf(bytes, 3));
                String source = new String(bytes, StandardCharsets.UTF_8);
                assertFalse(businessCall.matcher(source).find(), name);
                var mutations = writes.matcher(source);
                while (mutations.find()) assertTrue(mutations.group(1).startsWith("xfma_"), mutations.group(1));
                var creates = businessCreate.matcher(source);
                while (creates.find()) assertEquals(input.prefix() + "_observer", creates.group(1));
                for (String forbidden : List.of("add_gold", "change_gold", "set_stress", "add_stress", "set_global_variable", "add_to_global_variable_list", "trigger_event", "on_game_start_after_lobby")) assertFalse(source.contains(forbidden), name + ": " + forbidden);
                assertFalse(Pattern.compile("\\bdeath\\s*=").matcher(source).find(), name);
                balanced(source, name);
                if (profile != Profile.INHERITANCE) assertFalse(source.contains("make_story_owner"), name);
            });
        }
    }

    @Test void schemaOneRemainsClosedAndCoreMarkersAreUnchanged() throws IOException {
        var old = new AcceptanceContracts.Request(1, "1128");
        Path wire = temporary.resolve("core.json"); Files.write(wire, FixtureEmitter.JSON.writeValueAsBytes(old));
        assertEquals(old, FixtureEmitter.readRequest(wire));
        assertEquals(new LegacyInput(old), FixtureEmitter.readInput(wire));
        assertEquals(Set.of("schemaVersion", "actorHistoryId"), fields(FixtureEmitter.JSON.readTree(Files.readAllBytes(wire))));
        assertEquals(List.of("XFMAT: TEST PASS fixture_ready", "XFMAT: TEST PASS registered_owned_coin",
                "XFMAT: TEST PASS selected_coin_supply_conserved", "XFMAT: TEST PASS selected_coin_two_trades", "XFMAT: TEST PASS nonnegative_accounts"), ObservationScripts.MARKERS);
        assertTrue(text(ObservationScripts.render(old)).contains("observer_actor_died"));
        assertEquals(9, ObservationScripts.render(old).size(), "current core scripts plus request must remain ten files");
        assertFalse(ObservationScripts.render(old).containsKey("common/on_action/xfma_start.txt"));
    }

    @Test void eachFollowupEmissionReachesCurrentSharedSavedInventoryAndHostCopyConsumer() throws Exception {
        Path shared = Path.of(System.getProperty("xfm.shared.source", repository().toString())).toAbsolutePath().normalize();
        Path consumer = repository().resolve("mod_financial_markets/tools/src/test/resources/acceptance/verify_saved_observer_inventory.py");
        for (Profile profile : Profile.values()) {
            var emission = FixtureEmitter.emit(repository(), temporary.resolve("saved-" + profile.wire()),
                    "synthetic-fixture-machine", request(profile, 71));
            Path scratch = temporary.resolve("consumer-" + profile.wire());
            Path log = temporary.resolve("consumer-" + profile.wire() + ".log");
            var process = new ProcessBuilder(System.getProperty("xfm.python", "python"), "-B", "-X", "utf8",
                    consumer.toString(), "--repo-root", repository().toString(), "--shared-source", shared.toString(),
                    "--manifest", emission.manifest().path(), "--scratch", scratch.toString())
                    .directory(shared.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            assertTrue(process.waitFor(90, TimeUnit.SECONDS), "Shared Saved consumer timed out for " + profile);
            String output = Files.readString(log);
            assertEquals(0, process.exitValue(), profile + ": " + output);
            var result = FixtureEmitter.JSON.readTree(Files.readAllBytes(scratch.resolve("actual-result.json")));
            assertEquals("case_fixture", result.path("source_role").textValue());
            assertTrue(result.path("saved_inventory_verified").booleanValue());
            assertTrue(result.path("host_copy_readback_verified").booleanValue());
            assertFalse(result.path("game_started").booleanValue());
            assertFalse(result.path("business_acceptance_proven").booleanValue());
        }
    }

    @Test void epochsSeparateSavedObservationStateAndInheritanceUsesOnlyActualPrimaryHeir() {
        String first = text(FollowupObservationScripts.render(request(Profile.INHERITANCE, 31)));
        String second = text(FollowupObservationScripts.render(request(Profile.INHERITANCE, 32)));
        assertTrue(first.contains("xfma_inheritance_e31_armed"));
        assertTrue(second.contains("xfma_inheritance_e32_armed"));
        assertFalse(second.contains("xfma_inheritance_e31"));
        assertTrue(first.contains("primary_heir = { save_scope_as = xfma_next_operator }"));
        assertTrue(first.contains("make_story_owner = scope:xfma_next_operator"));
        assertTrue(first.contains("var:xfm_holder = scope:xfma_context.var:xfma_heir_before"));
        assertFalse(first.contains("observer_actor_died"));
    }

    @Test void coldBaselineChecksZeroValuedFieldsAndFullWatchedPositionAndDebtWithoutWritingThem() {
        var targets = new Targets("1", "2", "3", "4", "5", null);
        var baseline = new ColdBaseline(40, new AccountBaseline(0, 0, 0, 1, 0), new CoinBaseline(10000, 4, 12),
                new PositionBaseline(3, 900, 0, 10, 40, "1", "6", 7, 8, 0, 200),
                new DebtBaseline(1000, 900, 500, 400, 400, 100, 0, 30, 3, 30, "1", "6"));
        var input = new Request(2, Profile.COLD_RELOAD, 41, new ActorBinding(ActorMode.CURRENT_PLAYER, null), targets, baseline, null);
        String scripts = text(FollowupObservationScripts.render(input));
        assertTrue(scripts.contains("has_variable = xfm_free_cents var:xfm_free_cents = 0"));
        assertTrue(scripts.contains("has_variable = xfm_position_id var:xfm_position_id = 4"));
        assertTrue(scripts.contains("has_variable = xfm_contract_id var:xfm_contract_id = 3"));
        assertTrue(scripts.contains("has_variable = xfm_source_day var:xfm_source_day = 30"));
        assertTrue(scripts.contains("var:xfma_refreshes >= 2"));
        assertTrue(scripts.contains("cold_watched_sample_mismatch_or_date_advanced"));
        assertFalse(scripts.contains("name = xfm_"));
    }

    @Test void malformedSchemaTwoInputsRejectBeforeAnyEmissionOrScriptSubstitution() throws IOException {
        String valid = FixtureEmitter.JSON.writeValueAsString(request(Profile.LIFECYCLE, 51));
        List<String> malformed = List.of(
                valid.replace("\"schemaVersion\":2", "\"schemaVersion\":true"),
                valid.replace("\"observationEpoch\":51", "\"observationEpoch\":51.0"),
                valid.replace("\"observationEpoch\":51", "\"observationEpoch\":null"),
                valid.replace("\"caseId\":\"lifecycle\"", "\"caseId\":\"core\""),
                valid.replace("\"mode\":\"CURRENT_PLAYER\"", "\"mode\":0"),
                valid.replace("\"accountId\":\"1\"", "\"accountId\":1"),
                valid.replace("\"accountId\":\"1\"", "\"accountId\":\"01\""),
                valid.replace("\"accountId\":\"1\"", "\"accountId\":\"1 } add_gold = 10 {\""),
                valid.replace("\"debtId\":\"3\"", "\"debtId\":null"),
                valid.replace("\"targets\":{", "\"host\":\"other\",\"targets\":{"),
                valid.replace("\"coinId\":\"2\"", "\"coinId\":\"2\",\"coinId\":\"2\""));
        int index = 0;
        for (String input : malformed) {
            assertNotEquals(valid, input, "malformed test must really differ");
            Path path = temporary.resolve("bad-" + index++ + ".json"); Files.writeString(path, input);
            assertThrows(IOException.class, () -> FixtureEmitter.readInput(path), input);
        }
        assertThrows(IllegalArgumentException.class, () -> new Targets("1000000001", null, null, null, null, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.AI_CAPACITY, 1, new ActorBinding(ActorMode.CURRENT_PLAYER, null), new Targets("1", "2", null, null, null, null), null, null));
    }

    @Test void capacityRetainsWholeWindowAndMissingSamplesCannotGrantWindowMarker() {
        String source = text(FollowupObservationScripts.render(request(Profile.AI_CAPACITY, 61)));
        assertTrue(source.contains("var:xfma_daily_samples >= 395 var:xfma_measured_samples >= 365"));
        assertTrue(source.contains("NOT = { has_variable = xfma_sample_gap }"));
        assertTrue(source.contains("name = xfma_sample_gap value = 1"));
        assertFalse(source.contains("TEST PASS performance"));
        assertFalse(source.contains("xfm_processed_count"));
    }

    @Test void derivativesCanBindRealModelIndexesWithoutInventingCoinOrOracleState() throws IOException {
        for (String indexId : List.of("1", "2", "3")) {
            var input = new Request(2, Profile.DERIVATIVES, 81, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                    new Targets("1", null, null, null, null, null, indexId), null, null);
            String scripts = text(FollowupObservationScripts.render(input));
            assertTrue(scripts.contains("variable = xfm_index_registry"));
            assertTrue(scripts.contains("var:xfm_index_id = " + indexId));
            assertFalse(scripts.contains("variable = xfm_coin_registry"));
            assertFalse(scripts.contains("name = xfm_"));
            Path wire = temporary.resolve("index-" + indexId + ".json");
            Files.write(wire, FixtureEmitter.JSON.writeValueAsBytes(input));
            assertEquals(input, FixtureEmitter.readInput(wire));
        }
        assertThrows(IllegalArgumentException.class, () -> new Targets("1", "2", null, null, null, null, "1"));
        assertThrows(IllegalArgumentException.class, () -> new Targets("1", null, null, null, null, null, "4"));
    }

    @Test void configuredConservativeBoundaryIsReachableAndStandardRemainsDistinct() throws IOException {
        Path shared = Path.of(System.getProperty("xfm.shared.source", repository().toString()));
        Block config = parse(Files.readString(shared.resolve("mod_financial_markets/common/script_values/xfm_config_values.txt")));
        long conservativeCap = numericScript(config.block("xfm_config_futures_position_capacity_value"), Set.of("xfm_capacity_conservative"));
        long standardCap = numericScript(config.block("xfm_config_futures_position_capacity_value"), Set.of());
        assertEquals(1024, conservativeCap);
        assertEquals(1024, ScaleTier.CONSERVATIVE.positions());
        assertEquals(4000, ScaleTier.STANDARD.positions());
        assertTrue(ScaleTier.STANDARD.positions() <= standardCap);
        var input = new Request(2, Profile.AI_CAPACITY, 91, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("1", "2", null, null, null, null), null, ScaleTier.CONSERVATIVE);
        Block predicate = markerLimit(FollowupObservationScripts.render(input), input, "declared_inventory_readback");
        Node root = new Node("observer"); Node exchange = new Node("exchange");
        exchange.number("xfm_active_coin_count", 2048).number("xfm_futures_open_positions_count", 1023);
        assertFalse(matches(predicate, root, root, exchange));
        exchange.number("xfm_futures_open_positions_count", 1024);
        assertTrue(matches(predicate, root, root, exchange));
        assertFalse(ScaleTier.STANDARD.positions() <= conservativeCap, "do not relabel conservative as standard");
    }

    @Test void emittedAssociationPredicateRejectsCrossAssetCrossContractAndUnrelatedClaimFixtures() {
        var input = new Request(2, Profile.DERIVATIVES, 92, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("1", "2", "3", "4", "5", null), null, null);
        var scripts = FollowupObservationScripts.render(input);
        Block predicate = parse(new String(scripts.get("common/scripted_triggers/" + input.prefix() + ".txt"), StandardCharsets.UTF_8)).block(input.prefix() + "_associations_trigger");
        Node root = new Node("observer"); Node asset = new Node("coin"); Node otherAsset = new Node("coin");
        Node account = new Node("account"); Node shortAccount = new Node("account"); Node unrelatedAccount = new Node("account");
        Node contract = new Node("contract").reference("xfm_coin", asset);
        Node position = new Node("xfm_futures_position").reference("xfm_coin", asset).reference("xfm_contract", contract)
                .reference("xfm_long_account", account).reference("xfm_short_account", shortAccount);
        Node debt = new Node("claim").reference("xfm_source", position).reference("xfm_coin", asset)
                .reference("xfm_debtor_account", account).reference("xfm_creditor_account", shortAccount);
        root.reference("xfma_coin", asset).reference("xfma_account", account).reference("xfma_contract", contract)
                .reference("xfma_position", position).reference("xfma_debt", debt);
        assertTrue(matches(predicate, root, root, null));
        root.reference("xfma_coin", otherAsset);
        assertFalse(matches(predicate, root, root, null), "coin A cannot claim pair B");
        root.reference("xfma_coin", asset).reference("xfma_contract", new Node("contract").reference("xfm_coin", asset));
        assertFalse(matches(predicate, root, root, null), "pinned contract cannot be replaced by selected position");
        root.reference("xfma_contract", contract);
        debt.reference("xfm_source", new Node("xfm_futures_position"));
        assertFalse(matches(predicate, root, root, null), "unrelated historical source cannot supply claim credit");
        debt.reference("xfm_source", position).reference("xfm_creditor_account", unrelatedAccount);
        assertFalse(matches(predicate, root, root, null), "claim parties must be the actual pair");
        debt.reference("xfm_creditor_account", account).reference("xfm_debtor_account", shortAccount);
        assertTrue(matches(predicate, root, root, null), "the opposite payment direction is valid");
        String text = text(scripts);
        assertTrue(text.contains("followup_target_association_mismatch"));
        var fallback = new Request(2, Profile.DERIVATIVES, 93, input.actor(), new Targets("1", "2", "3", null, null, null), null, null);
        assertFalse(text(FollowupObservationScripts.render(fallback)).contains("name = xfma_contract value = prev.var:xfm_contract"));
    }

    @Test void actualEmittedArmValidityRejectsInheritedStoryAndCarriedArmedFlag() {
        Request input = request(Profile.INHERITANCE, 94);
        var scripts = FollowupObservationScripts.render(input);
        Block valid = parse(new String(scripts.get("common/scripted_guis/" + input.prefix() + ".txt"), StandardCharsets.UTF_8))
                .block(input.prefix() + "_arm_gui").block("is_valid");
        Node heir = new Node("character").number("is_ai", 0).number("is_alive", 1);
        assertTrue(matches(valid, heir, heir, null));
        heir.reference(input.prefix() + "_story", new Node("observer"));
        assertFalse(matches(valid, heir, heir, null), "a carried valid observer prevents rearming even without a flag");
        heir.variables.remove(input.prefix() + "_story");
        heir.number(input.prefix() + "_armed", 1);
        assertFalse(matches(valid, heir, heir, null));
        assertTrue(text(scripts).contains("name = " + input.prefix() + "_armed value = 1"));
    }

    @Test void spotRejectsHistoricalWrongAccountAndWrongCoinOrdersAfterNewEpoch() {
        var input = new Request(2, Profile.SPOT, 101, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", null, null, null, null), null, null);
        Block predicate = markerLimit(FollowupObservationScripts.render(input), input, "new_buy_filled_readback");
        Node account = new Node("xfm_finance_account"), coin = new Node("xfm_finance_coin");
        Node context = new Node("observer").number("xfma_start_order_id", 152).reference("xfma_account", account).reference("xfma_coin", coin);
        Node order = new Node("xfm_spot_order").number("xfm_order_id", 153).number("xfm_side", 1).number("xfm_filled_lots", 1)
                .reference("xfm_account", account).reference("xfm_coin", coin);
        context.reference("xfma_buy_order", order);
        assertTrue(matches(predicate, context, context, null));
        order.number("xfm_order_id", 152);
        assertFalse(matches(predicate, context, context, null), "saved pre-arm fills cannot supply a new observation");
        order.number("xfm_order_id", 153).reference("xfm_account", new Node("xfm_finance_account"));
        assertFalse(matches(predicate, context, context, null));
        order.reference("xfm_account", account).reference("xfm_coin", new Node("xfm_finance_coin"));
        assertFalse(matches(predicate, context, context, null));
        order.reference("xfm_coin", coin).number("xfm_filled_lots", 0);
        assertFalse(matches(predicate, context, context, null), "accepted unfilled order is not a trade");
    }

    @Test void spotPartialCancelRequiresActualNewPartialTerminalOrderAndRejectsWrongSchemaTargets() {
        var input = new Request(2, Profile.SPOT, 102, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", null, null, null, null), null, null);
        Block predicate = markerLimit(FollowupObservationScripts.render(input), input, "partial_cancelled_readback");
        Node account = new Node("xfm_finance_account"), coin = new Node("xfm_finance_coin");
        Node context = new Node("observer").number("xfma_start_order_id", 152).reference("xfma_account", account).reference("xfma_coin", coin);
        Node order = new Node("xfm_spot_order").number("xfm_order_id", 153).number("xfm_original_lots", 10).number("xfm_filled_lots", 4)
                .number("xfm_cancelled_lots", 6).number("xfm_remaining_lots", 0).number("xfm_status", 3).number("xfm_finalized", 1)
                .reference("xfm_account", account).reference("xfm_coin", coin);
        context.reference("xfma_partial_order", order);
        assertTrue(matches(predicate, context, context, null));
        order.number("xfm_filled_lots", 0);
        assertFalse(matches(predicate, context, context, null), "cancel without fill is not partial-fill cancellation");
        order.number("xfm_filled_lots", 4).number("xfm_status", 1);
        assertFalse(matches(predicate, context, context, null), "still-open order has not released its obligations");
        order.number("xfm_status", 3).number("xfm_order_id", 152);
        assertFalse(matches(predicate, context, context, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.SPOT, 103, input.actor(),
                new Targets("2", null, null, null, null, null, "1"), null, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.SPOT, 103, input.actor(),
                new Targets("2", "1", "3", null, null, null), null, null));
        String scripts = text(FollowupObservationScripts.render(input));
        assertFalse(scripts.contains("XFMAT: TEST PASS fixture_ready"));
        assertFalse(scripts.contains("registered_owned_coin"));
        assertFalse(scripts.contains("name = xfm_"));
        assertFalse(scripts.contains("var:xfma_last_sample_day add = 1 } }"));
        assertTrue(scripts.contains("xfma_spot_e102_next_sample_day_value"));
        assertTrue(scripts.contains("var:xfm_fee_paid_cents >= xfma_spot_e102_spot_expected_fee_value"));
        assertTrue(scripts.contains("var:xfm_fee_paid_cents <= xfma_spot_e102_spot_expected_fee_value"));
    }

    // Test-only evaluator consumes the emitted trigger tree and actual production capacity script.
    // It implements only this explicitly exercised subset; unknown constructs fail rather than pass.
    private sealed interface Expr permits Atom, Block { }
    private record Atom(String word) implements Expr { }
    private record Entry(String key, String operator, Expr value) { }
    private record Block(List<Entry> entries) implements Expr {
        Block block(String key) { return entries.stream().filter(entry -> entry.key.equals(key)).map(entry -> (Block)entry.value).findFirst().orElseThrow(); }
    }
    private sealed interface Datum permits NumberValue, NodeValue { }
    private record NumberValue(long value) implements Datum { }
    private record NodeValue(Node node) implements Datum { }
    private static final class Node {
        final String type;
        final Map<String, Datum> variables = new HashMap<>();
        Node(String type) { this.type = type; }
        Node number(String key, long value) { variables.put(key, new NumberValue(value)); return this; }
        Node reference(String key, Node value) { variables.put(key, new NodeValue(value)); return this; }
    }
    private static Block parse(String source) {
        var matcher = Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|!=|>=|<=|[{}=<>]|[^\\s{}=<>]+").matcher(source.replace("\ufeff", "").replaceAll("(?m)#.*$", ""));
        List<String> tokens = new ArrayList<>(); while (matcher.find()) tokens.add(matcher.group());
        int[] cursor = {0}; Block result = parseBlock(tokens, cursor, false);
        assertEquals(tokens.size(), cursor[0]); return result;
    }
    private static Block parseBlock(List<String> tokens, int[] cursor, boolean nested) {
        List<Entry> entries = new ArrayList<>();
        while (cursor[0] < tokens.size()) {
            String key = tokens.get(cursor[0]++);
            if (key.equals("}")) { assertTrue(nested); return new Block(entries); }
            String operator = tokens.get(cursor[0]++); String token = tokens.get(cursor[0]++);
            Expr value = token.equals("{") ? parseBlock(tokens, cursor, true) : new Atom(token.startsWith("\"") ? token.substring(1, token.length() - 1) : token);
            entries.add(new Entry(key, operator, value));
        }
        assertFalse(nested, "unclosed emitted trigger"); return new Block(entries);
    }
    private static Block markerLimit(Map<String, byte[]> scripts, Request input, String observation) {
        Block profile = parse(new String(scripts.get("common/scripted_effects/" + input.prefix() + "_observe.txt"), StandardCharsets.UTF_8)).block(input.prefix() + "_profile_effect");
        for (Entry entry : profile.entries) if (entry.key.equals("if") && entry.value instanceof Block body) {
            if (body.entries.stream().anyMatch(child -> child.key.equals("debug_log") && child.value.equals(new Atom("XFMAT: TEST PASS " + input.caseId().scriptKey() + "_" + observation)))) return body.block("limit");
        }
        throw new AssertionError("missing emitted marker predicate");
    }
    private static boolean matches(Block block, Node node, Node context, Node exchange) {
        return block.entries.stream().allMatch(entry -> condition(entry, node, context, exchange));
    }
    private static boolean condition(Entry entry, Node node, Node context, Node exchange) {
        if (entry.key.equals("AND")) return matches((Block)entry.value, node, context, exchange);
        if (entry.key.equals("OR")) return ((Block)entry.value).entries.stream().anyMatch(child -> condition(child, node, context, exchange));
        if (entry.key.equals("NOT")) return !matches((Block)entry.value, node, context, exchange);
        String word = entry.value instanceof Atom atom ? atom.word : null;
        if (entry.key.equals("always")) return "yes".equals(word);
        if (entry.key.equals("has_variable")) return node.variables.containsKey(word);
        if (entry.key.equals("exists")) return resolve(word, node, context, exchange) != null;
        if (entry.key.equals("story_type")) return node.type.equals(word);
        Datum actual = entry.key.startsWith("var:") || entry.key.startsWith("global_var:") || entry.key.startsWith("scope:")
                ? resolve(entry.key, node, context, exchange) : node.variables.get(entry.key);
        if (entry.value instanceof Block child) return actual instanceof NodeValue reference && matches(child, reference.node, context, exchange);
        Datum expected = resolve(word, node, context, exchange);
        if (actual == null || expected == null) return false;
        if (actual instanceof NumberValue left && expected instanceof NumberValue right) return switch (entry.operator) {
            case "=" -> left.value == right.value; case "!=" -> left.value != right.value; case ">" -> left.value > right.value;
            case "<" -> left.value < right.value; case ">=" -> left.value >= right.value; case "<=" -> left.value <= right.value;
            default -> throw new AssertionError(entry.operator);
        };
        if (!entry.operator.equals("=") && !entry.operator.equals("!=")) throw new AssertionError("unsupported reference operator");
        boolean equal = actual.equals(expected); return entry.operator.equals("=") ? equal : !equal;
    }
    private static Datum resolve(String path, Node node, Node context, Node exchange) {
        if (path == null) return null;
        if (path.matches("-?[0-9]+")) return new NumberValue(Long.parseLong(path));
        if (path.equals("yes") || path.equals("no")) return new NumberValue(path.equals("yes") ? 1 : 0);
        String[] parts = path.split("\\.var:");
        Datum value = switch (parts[0]) {
            case "scope:xfma_context" -> new NodeValue(context);
            case "global_var:xfm_exchange" -> exchange == null ? null : new NodeValue(exchange);
            case "this" -> new NodeValue(node);
            default -> parts[0].startsWith("var:") ? node.variables.get(parts[0].substring(4)) : null;
        };
        for (int index = 1; index < parts.length; index++) value = value instanceof NodeValue reference ? reference.node.variables.get(parts[index]) : null;
        return value;
    }
    private static long numericScript(Block body, Set<String> rules) {
        long value = 0; boolean matched = false;
        for (Entry entry : body.entries) {
            if (entry.key.equals("value")) value = Long.parseLong(((Atom)entry.value).word);
            else if (entry.key.equals("if") || entry.key.equals("else_if")) {
                Block branch = (Block)entry.value;
                String rule = ((Atom)branch.block("limit").entries.getFirst().value).word;
                if (!matched && rules.contains(rule)) { value = numericScript(branch, rules); matched = true; }
            } else if (!entry.key.equals("limit")) throw new AssertionError("unsupported production capacity operation: " + entry.key);
        }
        return value;
    }

    private static String text(java.util.Map<String, byte[]> files) {
        return files.values().stream().map(bytes -> new String(bytes, StandardCharsets.UTF_8)).collect(java.util.stream.Collectors.joining("\n"));
    }
    private static int occurrences(String text, String needle) { return (text.length() - text.replace(needle, "").length()) / needle.length(); }
    private static Set<String> fields(com.fasterxml.jackson.databind.JsonNode node) { Set<String> keys = new HashSet<>(); node.fieldNames().forEachRemaining(keys::add); return keys; }
    private static void balanced(String text, String name) {
        int depth = 0; boolean quoted = false; boolean escaped = false; boolean comment = false;
        for (char value : text.toCharArray()) {
            if (comment) { if (value == '\n') comment = false; continue; }
            if (quoted) { if (escaped) escaped = false; else if (value == '\\') escaped = true; else if (value == '"') quoted = false; continue; }
            if (value == '#') comment = true;
            else if (value == '"') quoted = true;
            else if (value == '{') depth++;
            else if (value == '}') { depth--; assertTrue(depth >= 0, name); }
        }
        assertFalse(quoted, name); assertEquals(0, depth, name);
    }
}
