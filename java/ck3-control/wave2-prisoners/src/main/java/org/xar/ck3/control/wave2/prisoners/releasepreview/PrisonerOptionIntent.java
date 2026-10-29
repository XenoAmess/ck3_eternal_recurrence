package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.ReleaseOption;

/** The original private collection distinguishes omitted options from an invalid null or empty request. */
public sealed interface PrisonerOptionIntent permits PrisonerOptionIntent.Unconditional, PrisonerOptionIntent.Negotiated {
    record Unconditional() implements PrisonerOptionIntent { }
    record Negotiated(List<ReleaseOption> options) implements PrisonerOptionIntent {
        public Negotiated {
            options = List.copyOf(options);
            StrictJson.require(!options.isEmpty() && options.size() <= ReleaseOption.values().length
                    && options.stream().distinct().count() == options.size(), "nonempty distinct authored release options required");
        }
        public int mask() {
            int result = 0;
            for (ReleaseOption option : options) result |= 1 << option.ordinal();
            return result;
        }
    }
    record Arguments(PrisonerOptionIntent options, OptionalLong materialTarget) {
        public Arguments {
            Objects.requireNonNull(options); Objects.requireNonNull(materialTarget);
            materialTarget.ifPresent(value -> StrictJson.require(value > 0 && value < 0xffff_ffffL,
                    "material target must be a valid positive full character ID"));
        }
    }
    static Arguments decode(byte[] bytes) { return decode(StrictJson.parse(bytes)); }
    static Arguments decode(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "prisoner arguments object required");
        Set<String> expected = new java.util.HashSet<>();
        if (node.has("release_option_keys")) expected.add("release_option_keys");
        if (node.has("release_material_target_character_id")) expected.add("release_material_target_character_id");
        StrictJson.object(node, expected);
        PrisonerOptionIntent intent = new Unconditional();
        if (node.has("release_option_keys")) {
            JsonNode keys = node.get("release_option_keys");
            StrictJson.require(keys.isArray() && !keys.isEmpty(), "null and empty negotiated options are invalid, never unconditional");
            List<ReleaseOption> options = new ArrayList<>();
            for (JsonNode key : keys) options.add(ReleaseOption.fromKey(StrictJson.text(key)));
            intent = new Negotiated(options);
        }
        OptionalLong target = node.has("release_material_target_character_id")
                ? OptionalLong.of(StrictJson.integer(node.get("release_material_target_character_id"), 1, 0xffff_fffeL))
                : OptionalLong.empty();
        return new Arguments(intent, target);
    }
    static byte[] encode(Arguments arguments) {
        Objects.requireNonNull(arguments); ObjectNode node = StrictJson.object();
        if (arguments.options() instanceof Negotiated negotiated) {
            var keys = node.putArray("release_option_keys");
            for (ReleaseOption option : negotiated.options()) keys.add(option.key());
        }
        arguments.materialTarget().ifPresent(value -> node.put("release_material_target_character_id", value));
        return StrictJson.canonical(node);
    }
}
