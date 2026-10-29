package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Source-pinned existing Python differential. Native signed-actor corrections are asserted separately from legacy parity. */
final class NativePlayedCharacterOriginalProducerTest {
    private static final String PRODUCER_SHA256 = "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String TRAITS_SHA256 = "d45db52c93332ee47208db976aea18bb64133b4c7b86476ad7a173400f194afb";
    private static final String VERSION_SHA256 = "9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086";
    private static final String SCRIPT = """
            import ast, hashlib, json, pathlib, sys
            source = pathlib.Path(sys.argv[1]).resolve()
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != sys.argv[2]: raise ValueError('actual native_driver producer SHA differs')
            inputs = {'player_event_trait_membership_contract.py': sys.argv[3], 'version_identity.py': sys.argv[4]}
            before = {}
            for name, expected in inputs.items():
                data = source.with_name(name).read_bytes()
                if hashlib.sha256(data).hexdigest() != expected: raise ValueError('actual sibling producer SHA differs: ' + name)
                before[name] = data
            sys.path.insert(0, str(source.parents[2]))
            from xar_autoplayer.bridge import player_event_trait_membership_contract as traits
            if pathlib.Path(traits.__file__).resolve() != source.with_name('player_event_trait_membership_contract.py'): raise ValueError('imported another trait producer')
            tree = ast.parse(raw.decode('utf-8-sig'))
            actual = [item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == '_played_character']
            if len(actual) != 1: raise ValueError('unique original played_character definition required')
            scope = {'normalize_player_event_trait_membership_v1': traits.normalize_player_event_trait_membership_v1}
            exec(compile(ast.fix_missing_locations(ast.Module(body=actual, type_ignores=[])), str(source), 'exec'), scope)
            result = []
            for case in json.load(sys.stdin):
                try:
                    value = scope['_played_character'](case.get('value'), native_revision=case['native_revision'], date_raw=case.get('date_raw'))
                    result.append({'accepted': True, 'value': value})
                except ValueError:
                    result.append({'accepted': False})
            if source.read_bytes() != raw: raise ValueError('actual native_driver changed during oracle')
            for name, data in before.items():
                if source.with_name(name).read_bytes() != data: raise ValueError('actual sibling producer changed during oracle')
            json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
            """;

    @Test void commonDomainValidAndMalformedWiresMatchTheActualOriginalPlayedAndTraitProducers() throws Exception {
        List<NativePlayedCharacterTest.Case> cases = new ArrayList<>(NativePlayedCharacterTest.validCases());
        cases.addAll(NativePlayedCharacterTest.invalidCases());
        ArrayNode expected = oracle(cases);
        assertEquals(cases.size(), expected.size()); int accepted = 0, rejected = 0;
        for (int index = 0; index < cases.size(); index++) {
            var test = cases.get(index); JsonNode row = expected.get(index);
            assertTrue(row.get("accepted").isBoolean());
            if (row.get("accepted").booleanValue()) {
                JsonNode actual = NativePlayedCharacter.normalize(test.value(), test.revision(), test.date());
                assertEquals(row.get("value"), StrictJson.parse(actual.toString().getBytes(StandardCharsets.UTF_8),
                        StrictJson.EXPLICIT_MAX_BYTES), test.name());
                accepted++;
            } else {
                assertThrows(IllegalArgumentException.class, () -> NativePlayedCharacter.normalize(test.value(), test.revision(), test.date()), test.name());
                rejected++;
            }
        }
        assertTrue(accepted >= 15 && rejected >= 50, "actual complete positive and malformed producer branches must execute");
    }

    /** Intentional native-domain correction: old Python rejects negatives; no live negative packet is claimed. */
    @Test void actualOriginalProducerMakesTheIntentionalSignedNativeActorCorrectionExplicit() throws Exception {
        List<Difference> cases = List.of(
                new Difference(actorCase("signed native minus two", BigInteger.valueOf(-2)), false, true),
                new Difference(actorCase("signed native minimum", BigInteger.valueOf(Integer.MIN_VALUE)), false, true),
                new Difference(actorCase("above native signed maximum", BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)), true, false),
                new Difference(actorCase("unbounded legacy positive actor", BigInteger.ONE.shiftLeft(160)), true, false),
                new Difference(actorCase("native absent sentinel", BigInteger.valueOf(-1)), false, false),
                new Difference(unavailableActorCase("native minus two unavailable traits", -2), false, true),
                new Difference(unavailableActorCase("native minimum unavailable traits", Integer.MIN_VALUE), false, true),
                new Difference(unavailableActorCase("native zero unavailable traits", 0), false, true));
        ArrayNode old = oracle(cases.stream().map(Difference::test).toList());
        assertEquals(cases.size(), old.size());
        for (int index = 0; index < cases.size(); index++) {
            var difference = cases.get(index); var test = difference.test();
            JsonNode accepted = old.get(index).get("accepted");
            assertNotNull(accepted); assertTrue(accepted.isBoolean(), test.name());
            assertEquals(difference.legacyAccepted(), accepted.booleanValue(), test.name());
            if (difference.correctedAccepted()) {
                JsonNode actual = NativePlayedCharacter.normalize(test.value(), test.revision(), test.date());
                assertEquals(test.value().get("character_id").bigIntegerValue(), actual.get("character_id").bigIntegerValue());
                assertTrue(actual.get("character_id").isInt(), "signed JSON integer");
                assertEquals(actual, NativePlayedCharacter.normalize(
                        StrictJson.parse(actual.toString().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES),
                        test.revision(), test.date()), test.name());
                if (test.value().has("event_trait_membership"))
                    assertEquals(test.value().get("event_trait_membership").get("played_character_id").bigIntegerValue(),
                            actual.get("event_trait_membership").get("played_character_id").bigIntegerValue());
            } else {
                if (difference.legacyAccepted())
                    assertEquals(test.value().get("character_id").bigIntegerValue(), old.get(index).get("value").get("character_id").bigIntegerValue());
                assertThrows(IllegalArgumentException.class,
                        () -> NativePlayedCharacter.normalize(test.value(), test.revision(), test.date()), test.name());
            }
        }
    }
    private record Difference(NativePlayedCharacterTest.Case test, boolean legacyAccepted, boolean correctedAccepted) { }
    private static NativePlayedCharacterTest.Case actorCase(String name, BigInteger actor) {
        return new NativePlayedCharacterTest.Case(name, NativePlayedCharacterTest.actor().put("character_id", actor),
                NativePlayedCharacterTest.REVISION, NativePlayedCharacterTest.DATE);
    }
    private static NativePlayedCharacterTest.Case unavailableActorCase(String name, int actor) {
        var value = NativePlayedCharacterTest.actor().put("character_id", actor);
        var frame = new NativePlayerEventTraitMembership.Frame(NativePlayedCharacterTest.REVISION,
                BigInteger.valueOf(1000), BigInteger.valueOf(actor));
        value.set("event_trait_membership", NativePlayerEventTraitMembership.toJson(
                new NativePlayerEventTraitMembership.Unavailable(frame, "current_player_frame_unavailable")));
        return new NativePlayedCharacterTest.Case(name, value, NativePlayedCharacterTest.REVISION, NativePlayedCharacterTest.DATE);
    }

    private static ArrayNode oracle(List<NativePlayedCharacterTest.Case> cases) throws Exception {
        Path python = Path.of(required("xar.native.producer.python")), source = Path.of(required("xar.native.producer.source"));
        String suppliedSha = required("xar.native.producer.sha256");
        assertTrue(python.isAbsolute() && source.isAbsolute(), "NOT_RUN: explicit absolute original producer fixtures required");
        assertEquals(PRODUCER_SHA256, suppliedSha, "actual source selection and supplied original fixture must agree");
        assertTrue(Files.isRegularFile(python) && Files.isRegularFile(source), "NOT_RUN: actual original executable/source required");
        assertEquals(PRODUCER_SHA256, sha(Files.readAllBytes(source)));
        assertEquals(TRAITS_SHA256, sha(Files.readAllBytes(source.resolveSibling("player_event_trait_membership_contract.py"))));
        assertEquals(VERSION_SHA256, sha(Files.readAllBytes(source.resolveSibling("version_identity.py"))));
        ArrayNode input = StrictJson.object().putArray("cases");
        for (var test : cases) {
            var row = input.addObject().put("native_revision", test.revision());
            if (!test.value().isMissingNode()) row.set("value", test.value());
            if (!test.date().isMissingNode()) row.set("date_raw", test.date());
        }
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-X", "utf8", "-c", SCRIPT,
                source.toString(), suppliedSha, TRAITS_SHA256, VERSION_SHA256).redirectErrorStream(true);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process process = builder.start();
        try (var reader = Executors.newSingleThreadExecutor(Thread.ofVirtual().factory())) {
            var output = reader.submit(() -> process.getInputStream().readNBytes(StrictJson.EXPLICIT_MAX_BYTES + 1));
            try {
                try (var stdin = process.getOutputStream()) { stdin.write(originalInput(input)); }
                assertTrue(process.waitFor(30, TimeUnit.SECONDS), "NOT_RUN/FAIL: original played producer timed out");
                byte[] raw = output.get(5, TimeUnit.SECONDS);
                assertTrue(raw.length > 0 && raw.length <= StrictJson.EXPLICIT_MAX_BYTES, "bounded actual original result required");
                assertEquals(0, process.exitValue(), "actual original producer failed: "
                        + new String(raw, 0, Math.min(raw.length, 4096), StandardCharsets.UTF_8));
                return assertInstanceOf(ArrayNode.class, StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES));
            } finally {
                if (process.isAlive()) { process.destroyForcibly(); assertTrue(process.waitFor(5, TimeUnit.SECONDS), "original producer cleanup unproved"); }
            }
        }
    }
    /** Test transport preserves float tokens even after the production parser strips decimal zeroes. */
    private static byte[] originalInput(ArrayNode input) throws java.io.IOException {
        var bytes = new java.io.ByteArrayOutputStream();
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        try (var generator = new com.fasterxml.jackson.core.util.JsonGeneratorDelegate(mapper.getFactory().createGenerator(bytes)) {
            @Override public void writeNumber(java.math.BigDecimal value) throws java.io.IOException {
                String token = value.toString();
                super.writeNumber(token.indexOf('.') < 0 && token.indexOf('E') < 0 ? token + ".0" : token);
            }
        }) { mapper.writeTree(generator, input); }
        byte[] encoded = bytes.toByteArray();
        assertTrue(encoded.length > 0 && encoded.length <= StrictJson.EXPLICIT_MAX_BYTES, "bounded original producer input required");
        return encoded;
    }
    private static String required(String key) {
        String value = System.getProperty(key);
        assertNotNull(value, "NOT_RUN: required original fixture property " + key);
        assertFalse(value.isBlank(), "NOT_RUN: required original fixture property " + key); return value;
    }
    private static String sha(byte[] raw) throws java.security.NoSuchAlgorithmException {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
