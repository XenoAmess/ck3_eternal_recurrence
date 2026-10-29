package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryReader;
import org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;

/** Original post-batch interaction catalogue: actual source/GUI bytes, no reply or material authority. */
public final class OfflineInteractionSourceAnalyzer {
    private static final int SOURCE_MAXIMUM = 2_097_152;
    private static final String ANALYSIS = "Exact source bodies retained including conditional scopes and costs; no branch is assumed executed. User policy chooses authored left, not a claimed optimal or native-AI decision.";
    public static final String REASON = "Source-catalogued interaction; use the user's authored-left reply policy. Exact on_accept/on_decline effects are retained offline; reply ACK does not prove those effects.";
    private OfflineInteractionSourceAnalyzer() { }

    public record Analysis(InteractionRegistry.Facts facts, ExactRef source, ExactRef gui) {
        public Analysis {
            Objects.requireNonNull(facts); Objects.requireNonNull(source); Objects.requireNonNull(gui);
            require(facts.fingerprint().equals(InteractionRegistryCodec.fingerprint(facts.binding()))
                    && facts.paths().sourcePath().equals(source.path()) && facts.paths().guiPath().equals(gui.path())
                    && facts.binding().sourceSha256().equals(source.sha256()) && facts.binding().guiSha256().equals(gui.sha256()),
                    "interaction analysis source pins differ");
        }
    }
    private record Loaded(Path path, byte[] raw, InteractionSourceBlocks.AuthoredEffects effects) {
        private Loaded { raw = raw.clone(); }
        @Override public byte[] raw() { return raw.clone(); }
    }

    public static InteractionRegistry.Result reviewed(ObjectValue before, TrustedEventSourceContext trusted) {
        Objects.requireNonNull(trusted); InteractionRegistry.Lookup lookup = lookup(before);
        SourceReviewedInteractionContinuation.verifyGui(trusted);
        return new InteractionRegistryReader(trusted.machineId()).load(trusted, lookup);
    }

    public static Analysis analyze(ObjectValue before, TrustedEventSourceContext trusted) throws IOException {
        Objects.requireNonNull(trusted); InteractionRegistry.Lookup lookup = lookup(before);
        trusted.requireBuild(lookup.build().version());
        Path guiPath = trusted.stockGameDirectory().resolve(InteractionFallback.GUI_SOURCE);
        byte[] gui = trusted.readGuiSource(guiPath, SOURCE_MAXIMUM);
        require(sha(gui).equals(lookup.guiSha256()), "captured interaction GUI source SHA changed");
        Path directory = trusted.stockGameDirectory().resolve("common/character_interactions");
        List<Path> paths;
        try (var walk = Files.walk(directory)) { paths = walk.limit(65_537).toList(); }
        require(paths.size() <= 65_536, "bounded original interaction source scan exceeded");
        Pattern candidate = Pattern.compile("^\\s*" + Pattern.quote(lookup.definition().canonicalKey()) + "\\s*=\\s*\\{",
                Pattern.MULTILINE | Pattern.UNIX_LINES | Pattern.UNICODE_CHARACTER_CLASS);
        Loaded found = null;
        for (Path path : paths.stream().sorted(Comparator.comparing(Path::toString)).toList()) {
            if (!path.getFileName().toString().endsWith(".txt") || !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) continue;
            byte[] raw = trusted.readInteractionSource(path, SOURCE_MAXIMUM);
            // Like the original rg scan, discover candidates lexically; strictly decode only a selected source.
            String lexical = new String(raw, StandardCharsets.UTF_8); if (lexical.startsWith("\ufeff")) lexical = lexical.substring(1);
            if (!candidate.matcher(lexical).find()) continue;
            Optional<InteractionSourceBlocks.AuthoredEffects> effects = InteractionSourceBlocks.catalogueUtf8(raw, lookup.definition().canonicalKey());
            if (effects.isEmpty()) continue;
            require(found == null, "original interaction definition missing or ambiguous");
            found = new Loaded(path, raw, effects.orElseThrow());
        }
        require(found != null, "original interaction definition missing or ambiguous");
        Path sourcePath = found.path().toAbsolutePath().normalize(); byte[] source = found.raw();
        InteractionSourceBlocks.AuthoredEffects effects = found.effects();
        InteractionRegistry.Binding binding = new InteractionRegistry.Binding(lookup.build(), lookup.definition(), sha(source), sha(gui));
        String fingerprint = InteractionRegistryCodec.fingerprint(binding);
        InteractionRegistry.SourcePaths sourcePaths = new InteractionRegistry.SourcePaths(sourcePath.toString(), guiPath.toString());
        String relative = trusted.stockGameDirectory().relativize(sourcePath).toString().replace('\\', '/');
        InteractionRegistry.Facts facts = new InteractionRegistry.Facts(fingerprint, binding, sourcePaths, relative,
                effects.category(), effects.definition(), effects.onAccept(), effects.onDecline(),
                RiteDeclineSourceKnowledge.appendAnalysis(ANALYSIS, binding, effects.onDecline()));
        require(Arrays.equals(source, trusted.readInteractionSource(sourcePath, SOURCE_MAXIMUM))
                && Arrays.equals(gui, trusted.readGuiSource(guiPath, SOURCE_MAXIMUM)), "interaction source changed during analysis");
        return new Analysis(facts, new ExactRef(sourcePath.toString(), source.length, sha(source)), new ExactRef(guiPath.toString(), gui.length, sha(gui)));
    }

    private static InteractionRegistry.Lookup lookup(ObjectValue before) {
        require(before != null && eq(before, "schema", s("xar.pending-interaction-left-reply/v1"))
                && eq(before, "kind", s("pending_character_interaction")), "original interaction before receipt required");
        ObjectValue context = o(before, "context"), definition = o(context, "definition"), build = o(context, "build"), gui = o(before, "gui_binding");
        require(context != null && definition != null && build != null && gui != null
                && build.fields().keySet().equals(Set.of("version", "exe_sha256")), "native interaction definition/build missing");
        String action = text(o(before, "selection"), "action");
        require("reject".equals(action) || "acknowledge".equals(action), "offline catalogue cannot introduce another reply policy");
        BigInteger pending = number(before, "pending_interaction_id"), keyHash = number(definition, "deterministic_key_hash");
        require(pending != null && pending.bitLength() <= 31 && !pending.equals(BigInteger.valueOf(-1))
                && keyHash != null && keyHash.signum() >= 0 && keyHash.bitLength() <= 32, "signed pending and uint32 definition identities required");
        require(eq(gui, "source", s(InteractionFallback.GUI_SOURCE)) && eq(gui, "sha256", s(InteractionFallback.GUI_SHA256)),
                "captured original interaction GUI binding differs");
        return new InteractionRegistry.Lookup(new InteractionRegistry.BuildIdentity(text(build, "version"), text(build, "exe_sha256")),
                new InteractionRegistry.Definition(text(definition, "canonical_key"), keyHash.longValueExact()), text(gui, "sha256"));
    }
}
