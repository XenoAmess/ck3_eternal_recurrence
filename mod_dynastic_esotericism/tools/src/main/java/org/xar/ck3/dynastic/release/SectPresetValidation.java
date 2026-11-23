package org.xar.ck3.dynastic.release;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Certification of the two finite static definitions; this is not a CK3 engine interpreter. */
public final class SectPresetValidation {
    private static final Set<String> FAITH_FIELDS = Set.of("main_rite", "faith_details", "origin", "historical", "eminent_holy_sites", "holy_sites", "doctrines");
    private static final Set<String> DETAIL_FIELDS = Set.of("religion", "color", "icon", "graphical_faith", "religious_head");
    private static final Set<String> RITE_FIELDS = Set.of("name", "desc", "faith", "create", "convert", "color", "icon", "tenets", "doctrines");
    private static final String DOCTRINE_FILE = "common/religion/doctrine_types/des_doctrines.txt";
    private static final String DOCTRINE_GROUP_FILE = "common/religion/doctrine_group_types/des_doctrine_groups.txt";
    private static final Pattern TOKEN = Pattern.compile("\"(?:[^\"\\\\\\r\\n]|\\\\.)*\"|[A-Za-z0-9_.:-]+|[{}=]|\\s+|#[^\\r\\n]*");
    private static final Pattern HEAD_SCRIPT_TOKEN = Pattern.compile("\"(?:[^\"\\\\\\r\\n]|\\\\.)*\"|[A-Za-z0-9_.$:-]+|>=|<=|!=|\\?=|[{}=<>]|\\s+|#[^\\r\\n]*");
    // Finite reviewed Florin 1.21.0.3 compatibility overrides. Token contracts are not an engine interpreter.
    private static final String HEAD_TRIGGER_TOKENS = "7ca7657282ba68277d2a5e6c58184c98e55007afe0d35edfbb39d644768c6fc7";
    private static final String HEAD_EFFECT_TOKENS = "5411680d82f15ad24f78372e3e4a4d9e711aceb62e18f908cd0f480829d173de";
    private static final Pattern COLOR = Pattern.compile("(?:0(?:\\.[0-9]+)?|1(?:\\.0+)?)");

    private SectPresetValidation() { }

    public static void validate(ReleaseProduct product, Path root) throws IOException {
        if (!product.productId().equals(ReleaseProduct.PRODUCT_ID)) return;
        validateDoctrineSelection(root);
        validateNewGamePresetClergy(root);
        validateProcreationPresetMigration(root);
        validateAnnualMaintenancePolicy(root);
        Map<String, Value> faiths = assignments(read(root, SectPreset.FAITH_FILE), "faith definitions");
        Map<String, Value> rites = assignments(read(root, SectPreset.RITE_FILE), "rite definitions");
        Map<String, Value> coats = assignments(read(root, SectPreset.COAT_OF_ARMS_FILE), "coat of arms definitions");
        Map<String, Value> headTitles = assignments(read(root, SectPreset.HEAD_TITLE_FILE), "head of faith titles");
        requireKeys(faiths, Set.of(SectPreset.PROCREATION.faithId(), SectPreset.VIVHITE.faithId()), "faith IDs");
        validateFaithHistory(root);
        requireKeys(rites, Set.of(SectPreset.PROCREATION.riteId(), SectPreset.VIVHITE.riteId()), "rite IDs");
        requireKeys(coats, Set.of(SectPreset.PROCREATION.coatOfArmsId(), SectPreset.VIVHITE.coatOfArmsId(),
                SectPreset.PROCREATION.headTitleId(), SectPreset.VIVHITE.headTitleId()), "Rite and HoF title coat of arms IDs");
        requireKeys(headTitles, Set.of(SectPreset.PROCREATION.headTitleId(), SectPreset.VIVHITE.headTitleId()), "empire head title IDs");
        validateHeadScript(root, SectPreset.TEMPORAL_HEAD_TRIGGER_FILE, HEAD_TRIGGER_TOKENS);
        validateHeadScript(root, SectPreset.TEMPORAL_HEAD_EFFECT_FILE, HEAD_EFFECT_TOKENS);
        for (SectPreset preset : SectPreset.values()) {
            Map<String, Value> faith = assignments(block(faiths.get(preset.faithId()), preset.faithId()), preset.faithId());
            requireKeys(faith, FAITH_FIELDS, preset.faithId());
            requireScalar(faith, "main_rite", preset.riteId());
            requireScalar(faith, "origin", "catholic");
            requireScalar(faith, "historical", "no");
            requireList(faith, "eminent_holy_sites", List.of("jerusalem", "rome", "santiago"));
            requireList(faith, "holy_sites", List.of("cologne", "kent"));
            requireList(faith, "doctrines", List.of("special_doctrine_is_western_christian_faith"));
            Map<String, Value> details = assignments(block(faith.get("faith_details"), "faith_details"), "faith_details");
            requireKeys(details, DETAIL_FIELDS, "faith_details");
            requireScalar(details, "religion", SectPreset.RELIGION);
            requireScalar(details, "icon", preset.icon());
            requireScalar(details, "graphical_faith", "catholic_gfx");
            requireScalar(details, "religious_head", preset.headTitleId());
            validateHeadTitle(headTitles.get(preset.headTitleId()), preset);

            Map<String, Value> rite = assignments(block(rites.get(preset.riteId()), preset.riteId()), preset.riteId());
            requireKeys(rite, RITE_FIELDS, preset.riteId());
            requireScalar(rite, "name", preset.riteId());
            requireScalar(rite, "desc", preset.riteId() + "_desc");
            requireScalar(rite, "faith", preset.faithId());
            requireScalar(rite, "create", "yes");
            requireScalar(rite, "convert", "yes");
            requireScalar(rite, "icon", preset.icon());
            requireList(rite, "tenets", preset.tenets());
            requireList(rite, "doctrines", preset.doctrines());
            if (!color(details.get("color")).equals(color(rite.get("color")))) {
                throw new IllegalArgumentException("Faith and main Rite colors differ: " + preset);
            }
            StaticValidation.validateBytes(preset.iconPath(), Files.readAllBytes(root.resolve(preset.iconPath())));
            validateCoatOfArms(root, coats.get(preset.coatOfArmsId()), preset, preset.coatOfArmsId());
            requireScalar(coats, preset.headTitleId(), preset.coatOfArmsId());
        }
    }

    /** Reviewed finite lifecycle contract; an AST check does not certify engine callback timing. */
    private static void validateNewGamePresetClergy(Path root) throws IOException {
        String pending = "des_new_game_preset_clergy_pending";
        String correction = "des_reconcile_new_game_preset_clergy_effect";
        var actions = org.xar.ck3.save.Clausewitz.parse(StaticValidation.text(Files.readAllBytes(root.resolve("common/on_action/des_on_actions.txt"))));
        var effects = org.xar.ck3.save.Clausewitz.parse(StaticValidation.text(Files.readAllBytes(root.resolve("common/scripted_effects/des_initialization_effects.txt"))));
        requireScriptBlock(actions, "on_game_start", "on_actions = { des_new_game_initialize }");
        requireScriptBlock(actions, "on_game_start_after_lobby", "on_actions = { des_new_game_reconcile }");
        requireScriptBlock(actions, "des_new_game_initialize", """
                effect = {
                    set_global_variable = { name = des_new_game_preset_clergy_pending value = yes }
                    des_initialize_world_effect = yes
                    set_global_variable = { name = des_leadership_024_checked value = yes }
                }
                """);
        requireScriptBlock(actions, "des_new_game_reconcile", """
                effect = {
                    des_initialize_world_effect = yes
                    des_reconcile_new_game_preset_clergy_effect = yes
                    des_maintenance_effect = yes
                }
                """);
        requireScriptBlock(effects, correction, """
                if = {
                    limit = { has_global_variable = des_new_game_preset_clergy_pending }
                    rite:des_procreation_rite = {
                        if = {
                            limit = { NOT = { rite_has_doctrine = doctrine_clerical_succession_temporal_appointment } }
                            change_rite_doctrine = doctrine_clerical_succession_temporal_appointment
                        }
                    }
                    rite:des_vivhite_rite = {
                        if = {
                            limit = { NOT = { rite_has_doctrine = doctrine_clerical_succession_temporal_appointment } }
                            change_rite_doctrine = doctrine_clerical_succession_temporal_appointment
                        }
                    }
                    remove_global_variable = des_new_game_preset_clergy_pending
                }
                """);
        for (var entry : actions.entries()) {
            if (!Set.of("des_new_game_initialize", "des_new_game_reconcile").contains(entry.key())) {
                rejectClergyReference(entry, pending, correction);
            }
        }
        for (var entry : effects.entries()) {
            if (!entry.key().equals(correction)) rejectClergyReference(entry, pending, correction);
        }
    }

    /** Finite source contract; this does not certify engine load timing. */
    private static void validateProcreationPresetMigration(Path root) throws IOException {
        var effects = org.xar.ck3.save.Clausewitz.parse(StaticValidation.text(Files.readAllBytes(root.resolve("common/scripted_effects/des_initialization_effects.txt"))));
        var gui = org.xar.ck3.save.Clausewitz.parse(StaticValidation.text(Files.readAllBytes(root.resolve("common/scripted_guis/des_saved_game_initialization.txt"))));
        requireScriptBlock(effects, "des_reconcile_procreation_preset_023_effect", """
                if = {
                        limit = {
                            NOT = { has_global_variable = des_procreation_preset_023_checked }
                            exists = rite:des_procreation_rite
                        }
                        # Consume before doctrine callbacks can reenter this effect.
                        set_global_variable = { name = des_procreation_preset_023_checked value = yes }
                        rite:des_procreation_rite = {
                            if = {
                                limit = {
                                    rite_has_tenet = tenet_be_fruitful_and_multiply
                                    rite_has_tenet = tenet_carnal_exaltation
                                    rite_has_tenet = tenet_sacred_childbirth
                                    NOT = { any_rite_tenet = { count >= 4 } }
                                    rite_has_doctrine = doctrine_funeral_sky_burial
                                }
                                remove_rite_tenet = tenet_be_fruitful_and_multiply
                                remove_rite_tenet = tenet_sacred_childbirth
                                add_rite_tenet = tenet_ancestor_worship
                                add_rite_tenet = tenet_pursuit_of_power
                                change_rite_doctrine = doctrine_funeral_mummification
                            }
                        }
                    }
                """);
        requireScriptBlock(effects, "des_initialize_loaded_game_effect", """
                if = {
                        limit = {
                            is_ai = no
                            is_alive = yes
                            OR = {
                                NOT = { has_global_variable = des_initialized }
                                NOT = { has_global_variable = des_leadership_024_checked }
                                AND = {
                                    exists = rite:des_procreation_rite
                                    NOT = { has_global_variable = des_procreation_preset_023_checked }
                                }
                            }
                        }
                        if = {
                            limit = { NOT = { has_global_variable = des_initialized } }
                            des_initialize_world_effect = yes
                            des_maintenance_effect = yes
                        }
                        des_reconcile_procreation_preset_023_effect = yes
                        des_reconcile_loaded_leadership_024_effect = yes
                    }
                """);
        requireScriptBlock(gui, "des_saved_game_initialize_gui", """
                scope = character
                    is_shown = {
                        is_ai = no
                        is_alive = yes
                        OR = {
                            NOT = { has_global_variable = des_initialized }
                            NOT = { has_global_variable = des_leadership_024_checked }
                            AND = {
                                exists = rite:des_procreation_rite
                                NOT = { has_global_variable = des_procreation_preset_023_checked }
                            }
                        }
                    }
                    effect = { des_initialize_loaded_game_effect = yes }
                """);
        if (effects.block("des_initialize_world_effect").named("des_reconcile_procreation_preset_023_effect").size() != 1) {
            throw new IllegalArgumentException("world initialization must check the preset migration exactly once");
        }
        var leadership = org.xar.ck3.save.Clausewitz.parse(StaticValidation.text(Files.readAllBytes(root.resolve("common/scripted_effects/des_leadership_effects.txt"))));
        requireScriptBlock(leadership, "des_reconcile_loaded_leadership_024_effect", """
                if = {
                    limit = {
                        has_global_variable = des_initialized
                        NOT = { has_global_variable = des_leadership_024_checked }
                    }
                    set_global_variable = { name = des_leadership_024_checked value = yes }
                    every_religion_global = {
                        every_faith = {
                            every_faith_rite = {
                                if = {
                                    limit = { OR = { has_variable = des_bound_dynasty has_variable = des_join_house } }
                                    des_repair_rite_binding_effect = yes
                                    des_sync_created_dynasty_leadership_effect = yes
                                }
                            }
                        }
                    }
                }
                """);
    }

    /** Finite scheduling and bulk-work source contract; no engine timing or performance claim. */
    private static void validateAnnualMaintenancePolicy(Path root) throws IOException {
        var actions = maintenanceScript(root, "common/on_action/des_on_actions.txt");
        var initialization = maintenanceScript(root, "common/scripted_effects/des_initialization_effects.txt");
        var maintenance = maintenanceScript(root, "common/scripted_effects/des_maintenance_effects.txt");
        var characters = maintenanceScript(root, "common/scripted_effects/des_character_effects.txt");
        var crime = maintenanceScript(root, "common/scripted_effects/des_crime_effects.txt");
        requireMaintenanceBlock(actions, "yearly_global_pulse",
                "on_actions = { des_annual_watchdog des_annual_cadet_recovery des_annual_house_leadership_recovery }");
        requireMaintenanceBlock(actions, "des_annual_watchdog", """
                effect = { if = { limit = { has_global_variable = des_initialized } des_maintenance_effect = yes } }
                """);
        requireMaintenanceBlock(actions, "des_monthly_maintenance", "effect = { remove_global_variable = des_maintenance_queued }");
        requireMaintenanceBlock(initialization, "des_ensure_maintenance_effect", "remove_global_variable = des_maintenance_queued");
        if (!actions.named("random_yearly_everyone_pulse").isEmpty()) {
            throw new IllegalArgumentException("DES must not register a world-wide per-character yearly watchdog");
        }
        rejectMaintenanceRecurrence(actions); rejectMaintenanceRecurrence(initialization);
        requireMaintenanceBlock(actions, "on_birth_child", "on_actions = { des_on_character_finalization }");
        requireMaintenanceBlock(actions, "on_character_created", "on_actions = { des_on_character_finalization }");
        requireMaintenanceBlock(actions, "des_on_character_finalization", """
                effect = { if = {
                    limit = { has_global_variable = des_initialized is_alive = yes }
                    des_teach_doctrines_effect = yes
                    trigger_event = { on_action = des_character_finalized days = 1 }
                } }
                """);
        requireMaintenanceBlock(actions, "on_rite_change", "on_actions = { des_on_rite_change }");
        requireMaintenanceBlock(actions, "on_death", "on_actions = { des_on_death }");
        var death = actions.block("des_on_death").block("effect").block("if");
        requireMaintenanceCalls(death, "des_remove_pair_effect", 1);
        requireMaintenanceCalls(death, "des_clear_apostasy_effect", 1);
        int outgoing = -1, incoming = -1;
        for (int i = 0; i < death.entries().size(); i++) {
            var entry = death.entries().get(i);
            if ("every_in_list".equals(entry.key())) outgoing = i;
            if ("des_clear_apostasy_effect".equals(entry.key())) incoming = i;
        }
        if (outgoing < 0 || incoming <= outgoing) {
            throw new IllegalArgumentException("Death must immediately retire outgoing and incoming apostasy relationships in order");
        }
        var title = actions.block("des_on_religious_head_title_gain");
        requireMaintenanceCalls(title, "des_teach_doctrines_effect", 1);
        requireMaintenanceCalls(title, "des_sync_created_dynasty_leadership_effect", 1);
        requireMaintenanceCalls(title, "des_sync_rite_effect", 0);

        var definitions = new java.util.HashMap<String, org.xar.ck3.save.Clausewitz.Block>();
        for (var script : List.of(maintenance, characters, crime)) {
            for (var entry : script.entries()) {
                if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block body
                        && definitions.putIfAbsent(entry.key(), body) != null) {
                    throw new IllegalArgumentException("Duplicate DES maintenance effect definition: " + entry.key());
                }
            }
        }
        for (String forbidden : List.of("des_sync_apostate_pairs_effect", "des_refresh_observer_effect", "des_ensure_pair_effect")) {
            rejectMaintenanceReachable("des_refresh_apostasy_state_effect", forbidden, definitions, new java.util.HashSet<>());
        }
        for (String forbidden : List.of("des_ensure_pair_effect", "every_faith_character")) {
            rejectMaintenanceReachable("des_prune_apostate_pairs_effect", forbidden, definitions, new java.util.HashSet<>());
        }
        var sync = maintenance.block("des_sync_rite_effect");
        var branches = sync.named("if");
        if (branches.size() != 3) throw new IllegalArgumentException("Bulk Rite migration, state and relevant-observer phases must remain explicit");
        var joins = (org.xar.ck3.save.Clausewitz.Block) branches.getFirst().value();
        requireMaintenanceCalls(joins, "des_join_rite_dynasty_effect", 1);
        requireMaintenanceCalls(joins, "des_refresh_apostasy_state_effect", 0);
        requireMaintenanceCalls(joins, "des_refresh_observer_effect", 0);
        var bound = (org.xar.ck3.save.Clausewitz.Block) branches.get(1).value();
        var passes = bound.named("every_in_list");
        if (passes.size() != 2) throw new IllegalArgumentException("Snapshot migration must finish before snapshot state and pruning");
        var migrate = (org.xar.ck3.save.Clausewitz.Block) passes.getFirst().value();
        var state = (org.xar.ck3.save.Clausewitz.Block) passes.get(1).value();
        requireMaintenanceCalls(migrate, "des_join_rite_dynasty_effect", 1);
        requireMaintenanceCalls(migrate, "des_refresh_apostasy_state_effect", 0);
        requireMaintenanceCalls(migrate, "des_refresh_observer_effect", 0);
        requireMaintenanceCalls(state, "des_join_rite_dynasty_effect", 0);
        requireMaintenanceCalls(state, "des_refresh_apostasy_state_effect", 1);
        requireMaintenanceCalls(state, "des_prune_apostate_pairs_effect", 1);
        requireMaintenanceCalls(state, "des_refresh_apostasy_effect", 0);
        if (state.named("variable").size() != 1 || !(state.named("variable").getFirst().value()
                instanceof org.xar.ck3.save.Clausewitz.Atom snapshot) || !snapshot.token().equals("des_sync_members")) {
            throw new IllegalArgumentException("Bulk state must use its original member snapshot");
        }
        // A different-Rite observer still needs its immediate directional update.
        var observerGuards = state.named("if").stream().map(e -> (org.xar.ck3.save.Clausewitz.Block)e.value())
                .filter(b -> countMaintenanceCalls(b, "des_refresh_observer_effect") > 0).toList();
        if (observerGuards.size() != 1 || !observerGuards.getFirst().equals(org.xar.ck3.save.Clausewitz.parse("""
                limit = { NOT = { rite = scope:des_sync_rite } }
                des_refresh_observer_effect = yes
                """))) throw new IllegalArgumentException("Bulk snapshot observer fanout escaped the foreign-Rite guard");
        var relevant = (org.xar.ck3.save.Clausewitz.Block) branches.get(2).value();
        requireMaintenanceBlock(relevant, "limit", """
                OR = {
                    rite_has_doctrine = des_doctrine_dynastic
                    has_variable = des_bound_dynasty
                    has_variable = des_join_house
                    has_variable_list = des_apostates
                }
                """);
        var finalObservers = relevant.block("faith").block("every_faith_character");
        requireMaintenanceCalls(finalObservers, "des_refresh_apostasy_state_effect", 1);
        requireMaintenanceCalls(finalObservers, "des_refresh_observer_effect", 1);
        requireMaintenanceCalls(sync, "des_refresh_apostasy_effect", 0);
        int finalFaith = -1, lastState = -1;
        for (int i = 0; i < sync.entries().size(); i++) {
            var entry = sync.entries().get(i);
            if (entry.equals(branches.get(2))) finalFaith = i;
            else if ("if".equals(entry.key()) || "every_in_list".equals(entry.key())) lastState = i;
        }
        if (finalFaith <= lastState) throw new IllegalArgumentException("Final observer pass must follow all migration and state snapshots");
        var global = maintenance.block("des_maintenance_effect");
        requireMaintenanceCalls(global, "des_refresh_apostasy_effect", 0);
        requireMaintenanceCalls(global, "des_sync_apostate_pairs_effect", 0);
        requireMaintenanceCalls(global, "des_refresh_observer_effect", 0);
        requireMaintenanceCalls(global, "des_refresh_apostasy_state_effect", 1);
        rejectPersistentRelationshipReset(sync);
        rejectPersistentRelationshipReset(global);
        rejectPersistentRelationshipReset(crime.block("des_prune_apostate_pairs_effect"));
    }

    private static org.xar.ck3.save.Clausewitz.Block maintenanceScript(Path root, String relative) throws IOException {
        return org.xar.ck3.save.Clausewitz.parse(StaticValidation.text(Files.readAllBytes(root.resolve(relative))));
    }
    private static void requireMaintenanceBlock(org.xar.ck3.save.Clausewitz.Block actual, String key, String expected) {
        if (actual.named(key).size() != 1 || !actual.named(key).getFirst().operator().equals("=")
                || !actual.block(key).equals(org.xar.ck3.save.Clausewitz.parse(expected))) {
            throw new IllegalArgumentException("Annual DES maintenance contract differs: " + key);
        }
    }
    private static int countMaintenanceCalls(org.xar.ck3.save.Clausewitz.Block block, String key) {
        int count = 0;
        for (var entry : block.entries()) {
            if (key.equals(entry.key())) count++;
            if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block child) count += countMaintenanceCalls(child, key);
        }
        return count;
    }
    private static void requireMaintenanceCalls(org.xar.ck3.save.Clausewitz.Block block, String key, int expected) {
        if (countMaintenanceCalls(block, key) != expected) throw new IllegalArgumentException("DES bulk phase call count differs: " + key);
    }
    private static void rejectMaintenanceReachable(String start, String forbidden,
            Map<String, org.xar.ck3.save.Clausewitz.Block> definitions, Set<String> visited) {
        if (start == null) return;
        if (start.equals(forbidden)) throw new IllegalArgumentException("DES state/pruning calls forbidden fanout: " + forbidden);
        if (!visited.add(start)) return;
        var body = definitions.get(start);
        if (body != null) rejectMaintenanceReachableBlock(body, forbidden, definitions, visited);
    }
    private static void rejectMaintenanceReachableBlock(org.xar.ck3.save.Clausewitz.Block body, String forbidden,
            Map<String, org.xar.ck3.save.Clausewitz.Block> definitions, Set<String> visited) {
        for (var entry : body.entries()) {
            rejectMaintenanceReachable(entry.key(), forbidden, definitions, visited);
            if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block child) rejectMaintenanceReachableBlock(child, forbidden, definitions, visited);
        }
    }
    private static void rejectMaintenanceRecurrence(org.xar.ck3.save.Clausewitz.Block block) {
        for (var entry : block.entries()) {
            if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block child) {
                if ("trigger_event".equals(entry.key()) && child.named("on_action").stream().anyMatch(e ->
                        e.value() instanceof org.xar.ck3.save.Clausewitz.Atom a
                        && Set.of("des_monthly_maintenance", "des_annual_watchdog").contains(a.token()))) {
                    throw new IllegalArgumentException("Retired DES maintenance callbacks must never be rescheduled");
                }
                if ("set_global_variable".equals(entry.key()) && child.named("name").stream().anyMatch(e ->
                        e.value() instanceof org.xar.ck3.save.Clausewitz.Atom a && a.token().equals("des_maintenance_queued"))) {
                    throw new IllegalArgumentException("Retired DES queue lease must never be renewed");
                }
                rejectMaintenanceRecurrence(child);
            }
        }
    }
    private static void rejectPersistentRelationshipReset(org.xar.ck3.save.Clausewitz.Block block) {
        for (var entry : block.entries()) {
            if (entry.key() != null && Set.of("clear_variable_list", "clear_global_variable_list").contains(entry.key())
                    && entry.value() instanceof org.xar.ck3.save.Clausewitz.Atom atom
                    && Set.of("des_observers", "des_apostates").contains(atom.token())) {
                throw new IllegalArgumentException("Bulk maintenance cannot clear/rebuild persistent crime relationship indexes");
            }
            if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block child) rejectPersistentRelationshipReset(child);
        }
    }

    private static void requireScriptBlock(org.xar.ck3.save.Clausewitz.Block actual, String key, String expected) {
        if (actual.named(key).size() != 1 || !actual.named(key).getFirst().operator().equals("=")
                || !actual.block(key).equals(org.xar.ck3.save.Clausewitz.parse(expected))) {
            throw new IllegalArgumentException("new-game-only preset clergy contract differs: " + key);
        }
    }

    private static void rejectClergyReference(org.xar.ck3.save.Clausewitz.Entry entry, String pending, String correction) {
        if (Set.of(pending, correction).contains(entry.key()) || entry.value() instanceof org.xar.ck3.save.Clausewitz.Atom atom
                && Set.of(pending, correction).contains(atom.token())) {
            throw new IllegalArgumentException("preset clergy correction escapes the new-game lifecycle");
        }
        if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block child) {
            for (var nested : child.entries()) rejectClergyReference(nested, pending, correction);
        }
    }

    private static void validateFaithHistory(Path root) throws IOException {
        Map<String, Value> histories = assignments(read(root, SectPreset.FAITH_HISTORY_FILE), "preset Faith history");
        requireKeys(histories, Set.of(SectPreset.PROCREATION.faithId(), SectPreset.VIVHITE.faithId()), "preset Faith history IDs");
        for (SectPreset preset : SectPreset.values()) {
            Map<String, Value> history = assignments(block(histories.get(preset.faithId()), preset.faithId()), "preset Faith history");
            requireKeys(history, Set.of("867.1.1"), "preset creation at the earliest supported bookmark");
            Map<String, Value> creation = assignments(block(history.get("867.1.1"), "867.1.1"), "preset Faith creation");
            requireKeys(creation, Set.of("created"), "preset Faith creation");
            requireScalar(creation, "created", "yes");
        }
    }

    private static void validateHeadTitle(Value value, SectPreset preset) {
        Map<String, Value> title = assignments(block(value, preset.headTitleId()), preset.headTitleId());
        requireKeys(title, Set.of("color", "definite_form", "ruler_uses_title_name", "no_automatic_claims", "always_follows_primary_heir",
                "destroy_if_invalid_heir", "can_be_named_after_dynasty", "can_use_nomadic_naming", "capital", "can_create", "can_create_on_partition"), preset.headTitleId());
        for (Map.Entry<String, String> entry : Map.of("definite_form", "yes", "ruler_uses_title_name", "no", "no_automatic_claims", "yes",
                "always_follows_primary_heir", "yes", "destroy_if_invalid_heir", "yes", "can_be_named_after_dynasty", "no",
                "can_use_nomadic_naming", "no", "capital", "c_roma").entrySet()) requireScalar(title, entry.getKey(), entry.getValue());
        if (!scalarList(title.get("color"), "head title color").equals(preset.headTitleColor().stream().map(String::valueOf).toList())) {
            throw new IllegalArgumentException("head title color differs: " + preset);
        }
        for (String key : List.of("can_create", "can_create_on_partition")) {
            Map<String, Value> gate = assignments(block(title.get(key), key), key);
            requireKeys(gate, Set.of("always"), key);
            requireScalar(gate, "always", "no");
        }
    }

    private static void validateHeadScript(Path root, String relative, String expectedDigest) throws IOException {
        byte[] bytes = Files.readAllBytes(root.resolve(relative));
        StaticValidation.validateBytes(relative, bytes);
        String source = StaticValidation.text(bytes);
        List<String> tokens = new ArrayList<>();
        Matcher matcher = HEAD_SCRIPT_TOKEN.matcher(source);
        int offset = 0;
        while (matcher.find()) {
            if (matcher.start() != offset) throw new IllegalArgumentException("unsupported HoF compatibility syntax: " + relative + " at " + offset);
            String token = matcher.group();
            if (!Character.isWhitespace(token.charAt(0)) && token.charAt(0) != '#') tokens.add(token);
            offset = matcher.end();
        }
        if (offset != source.length() || !ReleaseBuilder.sha256(String.join("\n", tokens).getBytes(StandardCharsets.UTF_8)).equals(expectedDigest)) {
            throw new IllegalArgumentException("reviewed stock HoF compatibility contract differs: " + relative);
        }
    }

    private static void validateDoctrineSelection(Path root) throws IOException {
        Map<String, Value> definitions = assignments(read(root, DOCTRINE_FILE), "dynastic doctrine definitions");
        requireKeys(definitions, Set.of("des_doctrine_none", "des_doctrine_dynastic"), "dynastic doctrine IDs");
        Map<String, Value> none = assignments(block(definitions.get("des_doctrine_none"), "des_doctrine_none"), "des_doctrine_none");
        requireKeys(none, Set.of("doctrine_group_type", "index", "divergence", "icon", "piety_cost", "visible", "is_shown"), "detail-hidden editor-selectable None doctrine");
        requireScalar(none, "doctrine_group_type", ReleaseProduct.DYNASTIC_ICON_STEM);
        requireScalar(none, "visible", "no");
        Map<String, Value> shown = assignments(block(none.get("is_shown"), "None is_shown"), "None editor visibility");
        requireKeys(shown, Set.of("always"), "None editor visibility");
        requireScalar(shown, "always", "yes");
        Map<String, Value> dynastic = assignments(block(definitions.get("des_doctrine_dynastic"), "des_doctrine_dynastic"), "des_doctrine_dynastic");
        requireKeys(dynastic, Set.of("doctrine_group_type", "index", "divergence", "icon", "piety_cost", "parameters", "can_pick"), "player-selected dynastic doctrine");
        requireScalar(dynastic, "doctrine_group_type", ReleaseProduct.DYNASTIC_ICON_STEM);
        requireScalar(dynastic, "icon", "\"" + ReleaseProduct.DYNASTIC_ICON_STEM + "\"");
        Map<String, Value> gate = assignments(block(dynastic.get("can_pick"), "can_pick"), "dynastic can_pick");
        requireKeys(gate, Set.of("exists", "scope:actor"), "dynastic choice legality");
        requireScalar(gate, "exists", "scope:actor");
        Map<String, Value> actor = assignments(block(gate.get("scope:actor"), "scope:actor"), "dynastic selecting actor");
        requireKeys(actor, Set.of("is_ai"), "dynastic selecting actor");
        requireScalar(actor, "is_ai", "no");
        Map<String, Value> groups = assignments(read(root, DOCTRINE_GROUP_FILE), "dynastic doctrine group");
        requireKeys(groups, Set.of(ReleaseProduct.DYNASTIC_ICON_STEM), "dynastic doctrine group IDs");
        Map<String, Value> group = assignments(block(groups.get(ReleaseProduct.DYNASTIC_ICON_STEM), "dynastic doctrine group"), "dynastic doctrine group");
        requireKeys(group, Set.of("category", "divergence", "doctrine_lock", "is_available_on_create"), "dynastic doctrine group");
        requireScalar(group, "category", "main_group");
        requireScalar(group, "divergence", "category");
        requireScalar(group, "doctrine_lock", "none");
        Map<String, Value> available = assignments(block(group.get("is_available_on_create"), "group availability"), "group availability");
        requireKeys(available, Set.of("always"), "group editor availability");
        requireScalar(available, "always", "yes");
        validateDynasticIcons(root);
    }

    private static void validateDynasticIcons(Path root) throws IOException {
        for (String relative : List.of(ReleaseProduct.DYNASTIC_GROUP_ICON, ReleaseProduct.DYNASTIC_DOCTRINE_ICON)) {
            byte[] data = Files.readAllBytes(root.resolve(relative));
            StaticValidation.validateBytes(relative, data);
            ByteBuffer header = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
            if (header.getInt(12) != 120 || header.getInt(16) != 120 || header.getInt(20) != 480
                    || header.getInt(28) != 0 || header.getInt(80) != 0x41 || header.getInt(84) != 0
                    || header.getInt(88) != 32 || header.getInt(92) != 0xff0000 || header.getInt(96) != 0xff00
                    || header.getInt(100) != 0xff || header.getInt(104) != 0xff000000) {
                throw new IllegalArgumentException("dynastic group/selected icon must use the 120x120 BGRA8 single-level producer layout: " + relative);
            }
            boolean transparent = false;
            boolean visible = false;
            for (int offset = 128; offset < data.length; offset += 4) {
                if (data[offset] != 0 || data[offset + 1] != 0 || data[offset + 2] != 0) {
                    throw new IllegalArgumentException("dynastic icon must be a black-RGB alpha mask: " + relative);
                }
                transparent |= data[offset + 3] == 0;
                visible |= data[offset + 3] != 0;
            }
            if (!transparent || !visible) throw new IllegalArgumentException("dynastic icon alpha must contain both shape and transparent exterior: " + relative);
        }
        if (Files.mismatch(root.resolve(ReleaseProduct.DYNASTIC_GROUP_ICON), root.resolve(ReleaseProduct.DYNASTIC_DOCTRINE_ICON)) != -1) {
            throw new IllegalArgumentException("dynastic group and selected doctrine icons must use identical artwork");
        }
    }

    private static void validateCoatOfArms(Path root, Value value, SectPreset preset, String coatId) throws IOException {
        Map<String, Value> coat = assignments(block(value, coatId), coatId);
        requireKeys(coat, Set.of("textured_emblem"), coatId);
        Map<String, Value> emblem = assignments(block(coat.get("textured_emblem"), "textured_emblem"), "textured_emblem");
        requireKeys(emblem, Set.of("texture", "instance"), "textured_emblem");
        requireScalar(emblem, "texture", "\"" + preset.icon() + ".dds\"");
        Map<String, Value> instance = assignments(block(emblem.get("instance"), "instance"), "instance");
        requireKeys(instance, Set.of("position", "scale"), "instance");
        if (!scalarList(instance.get("position"), "position").equals(List.of("0.5", "0.5"))
                || !scalarList(instance.get("scale"), "scale").equals(List.of("1.0", "1.0"))) {
            throw new IllegalArgumentException("preset textured emblem placement differs: " + preset);
        }
        StaticValidation.validateBytes(preset.coatOfArmsTexturePath(), Files.readAllBytes(root.resolve(preset.coatOfArmsTexturePath())));
        if (Files.mismatch(root.resolve(preset.iconPath()), root.resolve(preset.coatOfArmsTexturePath())) != -1) {
            throw new IllegalArgumentException("preset coat of arms texture differs from the Faith/Rite icon: " + preset);
        }
    }

    public static void validateLocalizationAliases(Map<String, String> entries) {
        for (SectPreset preset : SectPreset.values()) {
            for (String suffix : SectPreset.LOCALIZATION_SUFFIXES) {
                String key = preset.riteId() + suffix;
                String expected = "$" + preset.faithId() + suffix + "$";
                if (!expected.equals(entries.get(key))) throw new IllegalArgumentException("Rite localization must alias its own Faith: " + key);
            }
            if (!("$" + preset.faithId() + "_adj$").equals(entries.get(preset.headTitleId() + "_adj"))) {
                throw new IllegalArgumentException("HoF title adjective must alias its own Faith: " + preset.headTitleId());
            }
        }
    }

    private static Block read(Path root, String relative) throws IOException {
        byte[] bytes = Files.readAllBytes(root.resolve(relative));
        StaticValidation.validateBytes(relative, bytes);
        String source = StaticValidation.text(bytes);
        return fromShared(org.xar.ck3.save.Clausewitz.parse(source), relative);
    }
    /** Preserve the finite DES literal grammar while sharing the actual lexer/parser. */
    private static Block fromShared(org.xar.ck3.save.Clausewitz.Block block, String relative) {
        List<Element> elements = new ArrayList<>();
        for (org.xar.ck3.save.Clausewitz.Entry entry : block.entries()) {
            if (entry.operator().isEmpty()) {
                if (!(entry.value() instanceof org.xar.ck3.save.Clausewitz.Atom atom) || !TOKEN.matcher(atom.token()).matches()) throw new IllegalArgumentException("unsupported static preset syntax: " + relative);
                elements.add(new Atom(atom.token()));
            } else {
                if (!entry.operator().equals("=") || !TOKEN.matcher(entry.key()).matches()) throw new IllegalArgumentException("unsupported static preset syntax: " + relative);
                Value value;
                if (entry.value() instanceof org.xar.ck3.save.Clausewitz.Block child) value = fromShared(child, relative);
                else {
                    String token = ((org.xar.ck3.save.Clausewitz.Atom) entry.value()).token();
                    if (!TOKEN.matcher(token).matches()) throw new IllegalArgumentException("unsupported static preset syntax: " + relative);
                    value = new Scalar(token);
                }
                elements.add(new Assignment(entry.key(), value));
            }
        }
        return new Block(List.copyOf(elements));
    }

    private static Map<String, Value> assignments(Block block, String context) {
        Map<String, Value> result = new TreeMap<>();
        for (Element element : block.elements()) {
            if (!(element instanceof Assignment assignment)) throw new IllegalArgumentException("expected named fields: " + context);
            if (result.putIfAbsent(assignment.key(), assignment.value()) != null) throw new IllegalArgumentException("duplicate preset field: " + context + "/" + assignment.key());
        }
        return Map.copyOf(result);
    }

    private static Block block(Value value, String context) {
        if (!(value instanceof Block result)) throw new IllegalArgumentException("expected preset block: " + context);
        return result;
    }

    private static void requireKeys(Map<String, Value> actual, Set<String> expected, String context) {
        if (!actual.keySet().equals(expected)) throw new IllegalArgumentException("preset fields differ: " + context + " expected=" + expected + " actual=" + actual.keySet());
    }

    private static void requireScalar(Map<String, Value> fields, String key, String expected) {
        if (!(fields.get(key) instanceof Scalar scalar) || !scalar.token().equals(expected)) throw new IllegalArgumentException("preset scalar differs: " + key + " expected=" + expected);
    }

    private static List<String> scalarList(Value value, String key) {
        List<String> result = new ArrayList<>();
        for (Element element : block(value, key).elements()) {
            if (!(element instanceof Atom atom)) throw new IllegalArgumentException("expected preset scalar list: " + key);
            result.add(atom.token());
        }
        return List.copyOf(result);
    }

    private static void requireList(Map<String, Value> fields, String key, List<String> expected) {
        List<String> actual = scalarList(fields.get(key), key);
        if (actual.size() != expected.size() || new HashSet<>(actual).size() != actual.size() || !Set.copyOf(actual).equals(Set.copyOf(expected))) {
            throw new IllegalArgumentException("preset list differs: " + key + " expected=" + expected + " actual=" + actual);
        }
    }

    private static List<BigDecimal> color(Value value) {
        List<String> tokens = scalarList(value, "color");
        if (tokens.size() != 3 || tokens.stream().anyMatch(token -> !COLOR.matcher(token).matches())) throw new IllegalArgumentException("preset color must be three decimal RGB values in [0,1]");
        return tokens.stream().map(BigDecimal::new).map(BigDecimal::stripTrailingZeros).toList();
    }

    private sealed interface Value permits Scalar, Block { }
    private sealed interface Element permits Assignment, Atom { }
    private record Scalar(String token) implements Value { }
    private record Block(List<Element> elements) implements Value { }
    private record Assignment(String key, Value value) implements Element { }
    private record Atom(String token) implements Element { }

}
