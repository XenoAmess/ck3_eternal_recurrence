package org.xar.ck3.dynastic.release;

import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;

/** Reviewed product identity and runtime inventory; never inferred from a glob. */
public record ReleaseProduct(String productId, Path source, String tagPrefix, List<String> runtimeFiles,
        LocalizationMode localizationMode) {
    public static final String PRODUCT_ID = "mod_dynastic_esotericism";
    public static final String TAG_PREFIX = "dynastic-esotericism-v";
    public static final Pattern VERSION = Pattern.compile("[0-9]+(?:\\.[0-9]+){0,3}(?:[-+][A-Za-z0-9.-]+)?");
    public static final Pattern REVISION = Pattern.compile("[0-9a-f]{40}");
    public static final Pattern DIGEST = Pattern.compile("[0-9a-f]{64}");
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    public enum LocalizationMode { DEVELOPMENT, RELEASE_LOCALIZATION }

    public enum Language {
        ENGLISH("english"), SIMP_CHINESE("simp_chinese"), FRENCH("french"), GERMAN("german"),
        JAPANESE("japanese"), KOREAN("korean"), POLISH("polish"), RUSSIAN("russian"), SPANISH("spanish");

        private final String folder;
        Language(String folder) { this.folder = folder; }
        public String header() { return "l_" + folder + ":"; }
        public String relativePath() { return "localization/" + folder + "/des_l_" + folder + ".yml"; }
    }
    private static final List<String> RUNTIME_FILES = List.of(
            "common/decisions/des_initialization_decisions.txt",
            "common/on_action/des_on_actions.txt",
            "common/opinion_modifiers/des_opinions.txt",
            "common/religion/doctrine_group_types/des_doctrine_groups.txt",
            "common/religion/doctrine_types/des_doctrines.txt",
            "common/scripted_effects/des_binding_effects.txt",
            "common/scripted_effects/des_character_effects.txt",
            "common/scripted_effects/des_crime_effects.txt",
            "common/scripted_effects/des_initialization_effects.txt",
            "common/scripted_effects/des_maintenance_effects.txt",
            "common/scripted_triggers/des_dynastic_triggers.txt",
            "common/traits/des_traits.txt",
            "descriptor.mod",
            "gfx/interface/icons/faith_doctrine_groups/des_dynastic_membership.dds",
            "localization/english/des_l_english.yml",
            "localization/simp_chinese/des_l_simp_chinese.yml",
            "thumbnail.png");

    public ReleaseProduct {
        Objects.requireNonNull(productId, "productId");
        Objects.requireNonNull(source, "source");
        Objects.requireNonNull(tagPrefix, "tagPrefix");
        Objects.requireNonNull(runtimeFiles, "runtimeFiles");
        Objects.requireNonNull(localizationMode, "localizationMode");
        if (!productId.matches("[a-z][a-z0-9_]*") || tagPrefix.isBlank() || tagPrefix.chars().anyMatch(Character::isWhitespace)) {
            throw new IllegalArgumentException("invalid product identity or tag prefix");
        }
        source = source.toAbsolutePath().normalize();
        runtimeFiles = runtimeFiles.stream().map(ReleaseProduct::relativePath).sorted().toList();
        if (!runtimeFiles.contains("descriptor.mod") || runtimeFiles.isEmpty()
                || Set.copyOf(runtimeFiles.stream().map(value -> value.toLowerCase(Locale.ROOT)).toList()).size() != runtimeFiles.size()) {
            throw new IllegalArgumentException("runtime inventory must be unique and include descriptor.mod");
        }
        if (runtimeFiles.stream().anyMatch(ReleaseProduct::sourceOnly)) {
            throw new IllegalArgumentException("source-only content cannot enter the runtime inventory");
        }
    }

    public ReleaseProduct(String productId, Path source, String tagPrefix, List<String> runtimeFiles) {
        this(productId, source, tagPrefix, runtimeFiles, LocalizationMode.DEVELOPMENT);
    }

    public static ReleaseProduct official(Path source) {
        return official(source, LocalizationMode.DEVELOPMENT);
    }

    public static ReleaseProduct official(Path source, LocalizationMode mode) {
        List<String> files = mode == LocalizationMode.DEVELOPMENT ? RUNTIME_FILES
                : java.util.stream.Stream.concat(RUNTIME_FILES.stream(), additionalLocalizationFiles().stream()).toList();
        return new ReleaseProduct(PRODUCT_ID, source, TAG_PREFIX, files, mode);
    }

    /** These seven known source files do not enter or gate the ordinary two-language build. */
    public static Set<String> additionalLocalizationFiles() {
        return Set.of(Language.FRENCH.relativePath(), Language.GERMAN.relativePath(), Language.JAPANESE.relativePath(),
                Language.KOREAN.relativePath(), Language.POLISH.relativePath(), Language.RUSSIAN.relativePath(), Language.SPANISH.relativePath());
    }

    public static String relativePath(String raw) {
        Objects.requireNonNull(raw, "relative path");
        if (raw.isEmpty() || raw.indexOf('\\') >= 0 || raw.indexOf(':') >= 0 || raw.startsWith("/")) {
            throw new IllegalArgumentException("runtime path must be a relative POSIX path: " + raw);
        }
        for (String part : raw.split("/", -1)) {
            if (part.isEmpty() || part.equals(".") || part.equals("..")) {
                throw new IllegalArgumentException("noncanonical runtime path: " + raw);
            }
        }
        return raw;
    }

    public static boolean sourceOnly(String relative) {
        return relative.equals("README.md") || relative.equals("docs") || relative.startsWith("docs/")
                || relative.equals("tools") || relative.startsWith("tools/");
    }

    /** Nullable only before the first real Workshop creation; never represented by a number. */
    public static String workshopItemId(String value) {
        if (value != null && (!value.matches("[1-9][0-9]*") || new BigInteger(value).compareTo(UINT64_MAX) > 0)) {
            throw new IllegalArgumentException("Workshop ID must be a canonical positive uint64 decimal string or null");
        }
        return value;
    }
}
