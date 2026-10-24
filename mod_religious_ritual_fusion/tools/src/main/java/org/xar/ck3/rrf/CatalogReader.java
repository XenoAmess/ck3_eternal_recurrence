package org.xar.ck3.rrf;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Definition;
import org.xar.ck3.rrf.Contracts.Group;
import org.xar.ck3.rrf.Contracts.Kind;
import org.xar.ck3.rrf.Contracts.SourceFile;

/** Reads the installed definition producer and binds every projected rule to its original SHA. */
public final class CatalogReader {
    public Catalog read(Path game, String machineId) throws IOException {
        List<SourceFile> sources = new ArrayList<>();
        Map<String, Clausewitz.Block> helpers = new LinkedHashMap<>();
        for (Path file : files(game.resolve("common/scripted_triggers"))) {
            source(sources, game, file);
            for (Clausewitz.Entry entry : Clausewitz.parse(Files.readString(file, StandardCharsets.UTF_8)).entries()) {
                if (entry.value() instanceof Clausewitz.Block body) helpers.put(entry.key(), body);
            }
        }
        List<Group> groups = new ArrayList<>();
        for (Path file : files(game.resolve("common/religion/doctrine_group_types"))) {
            source(sources, game, file);
            for (Clausewitz.Entry entry : Clausewitz.parse(Files.readString(file, StandardCharsets.UTF_8)).entries()) {
                Clausewitz.Block body = requireBlock(entry);
                groups.add(new Group(entry.key(), body.atom("category", "special"), body.atom("doctrine_lock", "none"), body.block("is_available_on_create").body()));
            }
        }
        List<Definition> definitions = new ArrayList<>();
        for (Kind kind : Kind.values()) {
            String directory = kind == Kind.TENET ? "tenet_types" : "doctrine_types";
            for (Path file : files(game.resolve("common/religion/" + directory))) {
                source(sources, game, file);
                for (Clausewitz.Entry entry : Clausewitz.parse(Files.readString(file, StandardCharsets.UTF_8)).entries()) {
                    Clausewitz.Block body = requireBlock(entry);
                    String groupId = kind == Kind.DOCTRINE ? body.atom("doctrine_group_type", "") : "";
                    String shown = body.block("is_shown").body(); String canPick = body.block("can_pick").body();
                    Set<String> reasons = new LinkedHashSet<>();
                    if (kind == Kind.DOCTRINE) {
                        Group group = groups.stream().filter(g -> g.id().equals(groupId)).findFirst().orElseThrow(() -> new IllegalArgumentException("unknown doctrine group: " + groupId));
                        if (group.category().equals("not_creatable")) reasons.add("group_not_creatable");
                        if (group.lock().equals("rite")) reasons.add("rite_lock_cleared_on_creation");
                        inspect(Clausewitz.parse(group.availableOnCreate()), helpers, reasons, new LinkedHashSet<>());
                    }
                    boolean visible = body.atom("visible", "yes").equals("yes");
                    if (!visible) reasons.add("hidden_definition");
                    inspect(Clausewitz.parse(shown), helpers, reasons, new LinkedHashSet<>());
                    inspect(Clausewitz.parse(canPick), helpers, reasons, new LinkedHashSet<>());
                    String dlc = body.atom("requires_dlc_flag", "");
                    definitions.add(new Definition(kind, entry.key(), groupId, relative(game, file), shown, canPick, dlc, visible, List.copyOf(reasons)));
                }
            }
        }
        return new Catalog(1, machineId, Instant.now().toString(), sources, groups, definitions);
    }
    private static Clausewitz.Block requireBlock(Clausewitz.Entry entry) {
        if (entry.operator().equals("=") && entry.value() instanceof Clausewitz.Block body) return body;
        throw new IllegalArgumentException("definition is not a block: " + entry.key());
    }
    private static void inspect(Clausewitz.Block body, Map<String, Clausewitz.Block> helpers, Set<String> reasons, Set<String> visiting) {
        for (Clausewitz.Entry entry : body.entries()) {
            inspectToken(entry.key(), reasons, false);
            if (entry.value() instanceof Clausewitz.Block child) inspect(child, helpers, reasons, visiting);
            else inspectToken(((Clausewitz.Atom) entry.value()).token(), reasons, false);
            Clausewitz.Block helper = helpers.get(entry.key());
            if (helper != null && visiting.add(entry.key())) {
                // External scripted triggers retain CK3 root. Calls depending on their root/prev cannot be safely projected.
                inspectHelper(helper, helpers, reasons, visiting);
                visiting.remove(entry.key());
            }
        }
    }
    private static void inspectHelper(Clausewitz.Block body, Map<String, Clausewitz.Block> helpers, Set<String> reasons, Set<String> visiting) {
        for (Clausewitz.Entry e : body.entries()) {
            inspectToken(e.key(), reasons, true);
            if (e.value() instanceof Clausewitz.Atom atom) inspectToken(atom.token(), reasons, true);
            else inspectHelper((Clausewitz.Block) e.value(), helpers, reasons, visiting);
            if (helpers.containsKey(e.key()) && visiting.add(e.key())) { inspectHelper(helpers.get(e.key()), helpers, reasons, visiting); visiting.remove(e.key()); }
        }
    }
    private static void inspectToken(String token, Set<String> reasons, boolean helper) {
        if (token.startsWith("\"")) return;
        String lower = token.toLowerCase(java.util.Locale.ROOT);
        if (lower.equals("prev") || lower.startsWith("prev.")) reasons.add("unsupported_prev_context");
        if (helper && (lower.equals("root") || lower.startsWith("root."))) reasons.add("scripted_trigger_depends_on_native_root");
        if (lower.startsWith("scope:") && !lower.equals("scope:actor") && !lower.startsWith("scope:actor.")) reasons.add("unbound_scope:" + token);
        if (token.contains("$") && !helper) reasons.add("unbound_script_parameter");
    }
    private static List<Path> files(Path directory) throws IOException {
        if (!Files.isDirectory(directory)) throw new IllegalArgumentException("missing game directory: " + directory);
        try (var files = Files.list(directory)) { return files.filter(p -> p.getFileName().toString().endsWith(".txt")).sorted().toList(); }
    }
    private static void source(List<SourceFile> sources, Path game, Path file) throws IOException { sources.add(new SourceFile(relative(game, file), ReleaseBuilder.sha256(Files.readAllBytes(file)))); }
    private static String relative(Path game, Path file) { return game.relativize(file).toString().replace('\\', '/'); }
}
