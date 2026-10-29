package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks;
import org.xar.ck3.control.wave2.events.sourcecatalog.EventSourceCatalogue;
import org.xar.ck3.control.wave2.events.sourcecatalog.SourceCatalogueCodec;

/** Actual source-body review, after a bounded loader has established the source path and any index pin. */
public final class OfflineEventSourceAnalyzer {
    private OfflineEventSourceAnalyzer() { }
    public record Analysis(String fingerprint, ObjectValue binding, ObjectValue facts) { }

    public static Analysis analyze(ObjectValue before, Path sourcePath, String relative, byte[] sourceRaw) {
        return analyze(SourceReviewedEventConsumer.nativeBinding(before), sourcePath, relative, sourceRaw);
    }

    /** Historical binding is preserved after the real consumer establishes a legal exact/source rebind. */
    static Analysis analyzeReviewedBinding(ObjectValue binding, ObjectValue before, Path sourcePath, String relative, byte[] sourceRaw) {
        SourceReviewedEventConsumer.NativeBinding current = SourceReviewedEventConsumer.nativeBinding(before);
        ObjectValue identity = current.json();
        for (String key : java.util.List.of("ck3_build", "required_ck3_exe_sha256", "native_backend_id", "event_definition_key", "native_option_count")) {
            require(v(binding, key).equals(v(identity, key)), "historical source review crossed its exact build/event identity");
        }
        require(positive(number(binding, "calculated_event_id")), "historical calculated definition identity required");
        return analyze(new SourceReviewedEventConsumer.NativeBinding(current.build(), current.exeSha256(), current.backend(), current.eventKey(),
                number(binding, "calculated_event_id"), current.optionCount()), sourcePath, relative, sourceRaw);
    }

    private static Analysis analyze(SourceReviewedEventConsumer.NativeBinding nativeBinding, Path sourcePath, String relative, byte[] sourceRaw) {
        require(sourcePath != null && sourcePath.isAbsolute(), "absolute installed source path required");
        require(relative != null && relative.startsWith("events/") && !relative.contains("\\") && !relative.contains(":")
                && !Path.of(relative).isAbsolute() && !java.util.Arrays.asList(relative.split("/", -1)).contains(".."), "bounded POSIX source-relative path required");
        require(sourceRaw != null && sourceRaw.length > 0 && sourceRaw.length <= 2_097_152, "exact source byte bound required");
        String source;
        try { source = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(sourceRaw)).toString(); }
        catch (java.nio.charset.CharacterCodingException malformed) { throw new IllegalArgumentException("invalid original source UTF-8", malformed); }
        if (source.startsWith("\ufeff")) source = source.substring(1);
        InteractionSourceBlocks.Block block = InteractionSourceBlocks.extractEventDefinition(source, nativeBinding.eventKey());
        require(block instanceof InteractionSourceBlocks.Found, "exact source event block absent");
        String definition = ((InteractionSourceBlocks.Found) block).text();
        EventSourceCatalogue.Catalogue catalogue = EventSourceCatalogue.catalogue(definition, nativeBinding.optionCount().intValueExact());
        ObjectValue reviewed = RetainedJson.object(RetainedJson.parse(SourceCatalogueCodec.encode(new SourceCatalogueCodec.CatalogueValue(catalogue))));
        ObjectValue binding = put(nativeBinding.json(), f("source_sha256", s(sha(sourceRaw))), f("option_catalogue_sha256", s(fingerprint(v(reviewed, "options")))));
        String fingerprint = fingerprint(binding);
        ObjectValue facts = obj(f("schema", s("xar.vanilla-event-offline-source-facts/v1")), f("fingerprint", s(fingerprint)),
                f("binding", binding), f("source_path", s(sourcePath.normalize().toString())), f("source_relative", s(relative)),
                f("definition", s(definition)), f("options", v(reviewed, "options")), f("immediate", v(reviewed, "immediate")), f("after", v(reviewed, "after")),
                f("analysis", s("All native-indexed source options reviewed as exact script bodies with trigger/scope/effect statements preserved. Conditions and scripted-effect callees are not evaluated. User policy chooses first rendered option, without claiming optimality or native AI equivalence.")),
                f("material_effects_verified", b(false)), f("registry_contract_accepted", b(false)));
        return new Analysis(fingerprint, binding, facts);
    }
}
