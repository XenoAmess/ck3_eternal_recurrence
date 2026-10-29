package org.xar.ck3.control.wave2.events.sourcecatalog;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks;

/** Strict transport of source-only operations; no file, native or knowledge-publishing authority. */
public final class SourceCatalogueCodec {
    public static final String SCHEMA = "xar.ck3.event-source-catalogue-input/v1";
    private SourceCatalogueCodec() { }
    public sealed interface Request permits ChildBlocks, Scalars, CatalogueInput { }
    public record ChildBlocks(String source, String wanted) implements Request {
        public ChildBlocks { validSource(source); validSource(wanted); }
    }
    public record Scalars(String source, String wanted) implements Request {
        public Scalars { validSource(source); validSource(wanted); }
    }
    public record CatalogueInput(String source, int nativeOptionCount) implements Request {
        public CatalogueInput { validSource(source); StrictJson.require(nativeOptionCount > 0, "positive native option count"); }
    }
    public sealed interface Value permits StringValues, CatalogueValue { }
    public record StringValues(List<String> values) implements Value {
        public StringValues { values = List.copyOf(values); }
    }
    public record CatalogueValue(EventSourceCatalogue.Catalogue catalogue) implements Value {
        public CatalogueValue { Objects.requireNonNull(catalogue, "catalogue"); }
    }
    public static Request decode(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES),
            Set.of("schema", "operation", "source", "wanted", "native_option_count"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(node.get("schema"))), "source catalogue schema");
        String operation = StrictJson.text(node.get("operation"));
        StrictJson.require(node.get("source").isTextual(), "source string token required");
        String source = node.get("source").textValue();
        return switch (operation) {
            case "blocks", "scalars" -> {
                StrictJson.require(node.get("wanted").isTextual() && node.get("native_option_count").isNull(), "child source request fields");
                String wanted = node.get("wanted").textValue();
                yield operation.equals("blocks") ? new ChildBlocks(source, wanted) : new Scalars(source, wanted);
            }
            case "catalogue" -> {
                StrictJson.require(node.get("wanted").isNull(), "catalogue wanted must be explicit null");
                yield new CatalogueInput(source, (int) StrictJson.integer(node.get("native_option_count"), 1, Integer.MAX_VALUE));
            }
            default -> throw new ContractViolationException("unsupported source-only operation");
        };
    }
    public static Value evaluate(Request request) {
        Objects.requireNonNull(request, "request");
        return switch (request) {
            case ChildBlocks blocks -> new StringValues(EventSourceCatalogue.blocks(blocks.source(), blocks.wanted()));
            case Scalars scalars -> new StringValues(EventSourceCatalogue.scalars(scalars.source(), scalars.wanted()));
            case CatalogueInput catalogue -> new CatalogueValue(EventSourceCatalogue.catalogue(catalogue.source(), catalogue.nativeOptionCount()));
        };
    }
    public static byte[] encode(Request request) {
        ObjectNode root = StrictJson.object().put("schema", SCHEMA);
        switch (request) {
            case ChildBlocks blocks -> root.put("operation", "blocks").put("source", blocks.source()).put("wanted", blocks.wanted()).putNull("native_option_count");
            case Scalars scalars -> root.put("operation", "scalars").put("source", scalars.source()).put("wanted", scalars.wanted()).putNull("native_option_count");
            case CatalogueInput catalogue -> root.put("operation", "catalogue").put("source", catalogue.source()).putNull("wanted").put("native_option_count", catalogue.nativeOptionCount());
        }
        return StrictJson.canonical(root, StrictJson.EXPLICIT_MAX_BYTES);
    }
    public static byte[] encode(Value value) {
        if (value instanceof StringValues strings) {
            ArrayNode array = StrictJson.object().putArray("values");
            strings.values().forEach(array::add);
            return StrictJson.canonical(array, StrictJson.EXPLICIT_MAX_BYTES);
        }
        EventSourceCatalogue.Catalogue catalogue = ((CatalogueValue) value).catalogue();
        ObjectNode root = StrictJson.object();
        ArrayNode types = root.putArray("event_types"); catalogue.sourceEventTypes().forEach(types::add);
        ArrayNode options = root.putArray("options");
        for (EventSourceCatalogue.Option option : catalogue.options()) {
            ObjectNode row = options.addObject().put("native_option_index", option.nativeOptionIndex());
            ArrayNode names = row.putArray("source_name_keys"); option.sourceNameKeys().forEach(names::add);
            ArrayNode conditional = row.putArray("conditional_name_source"); option.conditionalNameSource().forEach(conditional::add);
            row.put("source_option", option.sourceOption()).put("trigger", option.trigger());
            ArrayNode effects = row.putArray("direct_effect_statements");
            option.directEffectStatements().forEach(statement -> effects.addObject().put("effect", statement.effect()).put("source_value", statement.sourceValue()));
        }
        root.put("immediate", catalogue.immediate()).put("after", catalogue.after());
        return StrictJson.canonical(root, StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static void validSource(String text) {
        Objects.requireNonNull(text, "source text");
        try {
            int bytes = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(text)).remaining();
            StrictJson.require(bytes <= InteractionSourceBlocks.MAX_SOURCE_BYTES, "original source byte bound");
        } catch (CharacterCodingException error) { throw new ContractViolationException("invalid source Unicode", error); }
    }
}
