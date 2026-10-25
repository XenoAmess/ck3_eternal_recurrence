package org.xar.ck3.dynastic.release;

import java.io.IOException;
import java.math.BigDecimal;
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
    private static final Set<String> DETAIL_FIELDS = Set.of("religion", "color", "icon", "graphical_faith");
    private static final Set<String> RITE_FIELDS = Set.of("name", "desc", "faith", "create", "convert", "color", "icon", "tenets", "doctrines");
    private static final Pattern TOKEN = Pattern.compile("\"(?:[^\"\\\\\\r\\n]|\\\\.)*\"|[A-Za-z0-9_.-]+|[{}=]|\\s+|#[^\\r\\n]*");
    private static final Pattern COLOR = Pattern.compile("(?:0(?:\\.[0-9]+)?|1(?:\\.0+)?)");

    private SectPresetValidation() { }

    public static void validate(ReleaseProduct product, Path root) throws IOException {
        if (!product.productId().equals(ReleaseProduct.PRODUCT_ID)) return;
        Map<String, Value> faiths = assignments(read(root, SectPreset.FAITH_FILE), "faith definitions");
        Map<String, Value> rites = assignments(read(root, SectPreset.RITE_FILE), "rite definitions");
        Map<String, Value> coats = assignments(read(root, SectPreset.COAT_OF_ARMS_FILE), "coat of arms definitions");
        requireKeys(faiths, Set.of(SectPreset.PROCREATION.faithId(), SectPreset.VIVHITE.faithId()), "faith IDs");
        requireKeys(rites, Set.of(SectPreset.PROCREATION.riteId(), SectPreset.VIVHITE.riteId()), "rite IDs");
        requireKeys(coats, Set.of(SectPreset.PROCREATION.coatOfArmsId(), SectPreset.VIVHITE.coatOfArmsId()), "coat of arms IDs");
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
            validateCoatOfArms(root, coats.get(preset.coatOfArmsId()), preset);
        }
    }

    private static void validateCoatOfArms(Path root, Value value, SectPreset preset) throws IOException {
        Map<String, Value> coat = assignments(block(value, preset.coatOfArmsId()), preset.coatOfArmsId());
        requireKeys(coat, Set.of("textured_emblem"), preset.coatOfArmsId());
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
        }
    }

    private static Block read(Path root, String relative) throws IOException {
        byte[] bytes = Files.readAllBytes(root.resolve(relative));
        StaticValidation.validateBytes(relative, bytes);
        String source = StaticValidation.text(bytes);
        List<String> tokens = new ArrayList<>();
        Matcher matcher = TOKEN.matcher(source);
        int offset = 0;
        while (matcher.find()) {
            if (matcher.start() != offset) throw new IllegalArgumentException("unsupported static preset syntax: " + relative + " at " + offset);
            String token = matcher.group();
            if (!Character.isWhitespace(token.charAt(0)) && token.charAt(0) != '#') tokens.add(token);
            offset = matcher.end();
        }
        if (offset != source.length()) throw new IllegalArgumentException("unsupported static preset syntax: " + relative + " at " + offset);
        return new Parser(tokens, relative).root();
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

    /** Deliberately accepts only the finite literal definition syntax used by these presets. */
    private static final class Parser {
        private final List<String> tokens;
        private final String relative;
        private int offset;
        private Parser(List<String> tokens, String relative) { this.tokens = List.copyOf(tokens); this.relative = relative; }
        private Block root() {
            Block result = body(false);
            if (offset != tokens.size()) throw invalid();
            return result;
        }
        private Block body(boolean nested) {
            List<Element> elements = new ArrayList<>();
            while (offset < tokens.size()) {
                String key = tokens.get(offset++);
                if (key.equals("}")) {
                    if (!nested) throw invalid();
                    return new Block(List.copyOf(elements));
                }
                if (key.equals("{") || key.equals("=")) throw invalid();
                if (offset < tokens.size() && tokens.get(offset).equals("=")) {
                    offset++;
                    if (offset == tokens.size()) throw invalid();
                    String value = tokens.get(offset++);
                    if (value.equals("=") || value.equals("}")) throw invalid();
                    elements.add(new Assignment(key, value.equals("{") ? body(true) : new Scalar(value)));
                } else elements.add(new Atom(key));
            }
            if (nested) throw invalid();
            return new Block(List.copyOf(elements));
        }
        private IllegalArgumentException invalid() { return new IllegalArgumentException("invalid static preset structure: " + relative + " at token " + offset); }
    }
}
