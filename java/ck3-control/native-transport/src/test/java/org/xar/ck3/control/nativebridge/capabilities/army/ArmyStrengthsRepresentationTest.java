package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.*;

final class ArmyStrengthsRepresentationTest {
    @TempDir Path temporary;
    @Test void explicitWidePathsPreserveNativeDomainAndOnlyConvertDeclaredMixedArraySlot() {
        RawJson original = raw("{\"events\":[{\"sequence\":18446744073709551615,\"raw\":-9223372036854775808}],\"writes\":[{\"value\":22},{\"value\":9223372036854775807}],\"returns\":[18446744073709551615,null],\"optional\":null}");
        RawJson projected = encode(original, List.of(new Rule("/events/*/sequence", Domain.UNSIGNED_64), new Rule("/events/*/raw", Domain.SIGNED_64),
                new Rule("/writes/1/value", Domain.SIGNED_64), new Rule("/returns/*", Domain.UNSIGNED_64),
                new Rule("/optional/raw", Domain.SIGNED_64), new Rule("/absent/value", Domain.UNSIGNED_64), new Rule("/writes/99/value", Domain.SIGNED_64)));
        var nativeTree = ArmyStrengthsCodec.parseValue(original); var publicTree = ArmyStrengthsCodec.parseValue(projected);
        assertTrue(nativeTree.get("events").get(0).get("sequence").isIntegralNumber());
        assertEquals("18446744073709551615", publicTree.get("events").get(0).get("sequence").textValue());
        assertEquals("-9223372036854775808", publicTree.get("events").get(0).get("raw").textValue());
        assertTrue(publicTree.get("writes").get(0).get("value").isIntegralNumber());
        assertEquals("9223372036854775807", publicTree.get("writes").get(1).get("value").textValue());
        assertTrue(publicTree.get("returns").get(1).isNull()); assertTrue(publicTree.get("optional").isNull()); assertFalse(publicTree.has("absent"));
        assertEquals(publicTree, ArmyStrengthsCodec.parseValue(new RawJson(projected.bytes())));
    }
    @Test void declaredWideFieldsRejectWrongJsonTypesOverflowAndAmbiguousPaths() {
        for (String token : List.of("true", "1.0", "\"1\"", "18446744073709551616", "-1"))
            assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"identity\":" + token + "}"), List.of(new Rule("/identity", Domain.UNSIGNED_64))));
        assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"raw\":9223372036854775808}"), List.of(new Rule("/raw", Domain.SIGNED_64))));
        assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"events\":{}}"), List.of(new Rule("/events/*/sequence", Domain.UNSIGNED_64))));
        for (String path : List.of("raw", "/items/01/raw", "/items/-1/raw", "/items/~1/raw")) assertThrows(IllegalArgumentException.class, () -> new Rule(path, Domain.INTEGER));
        assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"raw\":1}"), List.of(new Rule("/raw", Domain.INTEGER), new Rule("/raw", Domain.INTEGER))));
    }
    private record Observed(List<Integer> regimentIds, long rawValue) { private Observed { regimentIds = List.copyOf(regimentIds); } }
    @Test void familyProducerReceivesActualImmutableRegimentContextAndOwnsBothEncodings() throws Exception {
        Path reviewed = temporary.resolve("controlled-context-source.txt"); Files.writeString(reviewed, "controlled contract fixture, no native qualification");
        byte[] bytes = Files.readAllBytes(reviewed); ExactRef source = new ExactRef(reviewed.toString(), bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        var registry = new ArmyStrengthsFamilies.Registry();
        registry.register(ArmyStrengthsFamilies.Key.ACTUAL_LOSS_WRITER_OBSERVATIONS_V1, Observed.class, (actual, context) -> {
            if (!(context.regiments() instanceof Present<List<Regiment>> present)) throw new IllegalArgumentException("controlled producer requires actual regiment rows");
            return new Present<>(new Observed(present.value().stream().map(Regiment::armyRegimentId).toList(), ArmyJson.i64(ArmyStrengthsCodec.parseValue(ArmyStrengthsCodec.present(actual)).get("raw"))));
        }, observed -> nativeValue(ArmyStrengthsCodec.present(observed)),
                observed -> encode(nativeValue(ArmyStrengthsCodec.present(observed)), List.of(new Rule("/raw", Domain.SIGNED_64))), source);
        registry.freeze();
        var original = new ArrayList<>(List.of(new Regiment(7, 10, 20, new Missing<>(), new Missing<>())));
        Core core = new Core(Status.AVAILABLE, new PublicUnitId(0), new Present<>(new FullId(0)), Role.PLAYER, List.of(), new Present<>(1), new Present<>(10), new Present<>(20), new Present<>(1L), new NullValue<>());
        RowContext context = new RowContext(core, new Present<>(original)); original.clear();
        var value = registry.normalize(ArmyStrengthsFamilies.Key.ACTUAL_LOSS_WRITER_OBSERVATIONS_V1, new Present<>(raw("{\"raw\":9223372036854775807}")), context);
        Observed observed = Observed.class.cast(ArmyStrengthsCodec.present(value.value())); assertEquals(List.of(7), observed.regimentIds());
        assertTrue(ArmyStrengthsCodec.parseValue(value.normalizedJson()).get("raw").isIntegralNumber());
        assertEquals("9223372036854775807", ArmyStrengthsCodec.parseValue(value.publicV2Json()).get("raw").textValue());
        assertThrows(ArmyStrengthsFamilies.MissingMigration.class, registry::requireCompleteRich);
    }
    private static RawJson nativeValue(Observed value) { return new RawJson(ArmyJson.bytes(ArmyJson.empty().put("raw", value.rawValue()))); }
    private static RawJson raw(String json) { return new RawJson(json.getBytes(StandardCharsets.UTF_8)); }
}
