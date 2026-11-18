package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.saveaudit.FinancialProjector.LayoutHypothesis;
import org.xar.ck3.markets.saveaudit.FinancialProjector.NumberIdentityEncoding;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.NumberField;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.ReferenceField;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Severity;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.NativeId;
import org.xar.ck3.save.SaveJson;

/** Pinned actual R0013 native75/96 envelopes; reconstructed text and negative mutations are software only. */
final class Unsigned64LayoutTest {
    @TempDir Path directory;
    private static final String MACHINE = "4-8e1c2f1861";
    private static final String DISCOVERY_SHA = "6435749508278093a3e726801b388ecc14dda89c9225216adaee2c0c04707dcb";
    private static final String SENTINEL = "18446744073709451616";
    private static final String U64_MAX = "18446744073709551615";
    private static final LayoutHypothesis UNSIGNED = layout(NumberIdentityEncoding.unsigned64OmittedZero);
    private static final LayoutHypothesis OMITTED = layout(NumberIdentityEncoding.omittedZero);
    private static final LayoutHypothesis STRICT = layout(NumberIdentityEncoding.identityRequired);

    @Test void actualBothNegativeSentinelsDecodeOnlyInExplicitUnsignedMode() throws Exception {
        JsonNode discovery = discovery();
        assertEquals("a011b34847901f93760813d318e9b797e2393cbd53d4d8d86e92a4af32393c74", discovery.path("save").path("sha256").textValue());
        assertEquals(2, discovery.path("complete_passes").intValue());
        Map<String, String> recordPins = Map.of("75", "62093dbfe72c7a88ee0ca78c443e758742092ee47adb13e0eb1854800fe53845",
                "96", "48ac6ec31901c3eba3c65a76d5f294de01cb7ab99044484a7fbd583f68b5b9de");
        for (String id : List.of("75", "96")) {
            JsonNode row = record(discovery, "xfm_futures_contract", id);
            assertEquals(recordPins.get(id), row.path("canonical_lexical_sha256").textValue());
            assertEquals(SENTINEL, variable(row, "xfm_last_daily_day").path("identity_raw").textValue());
            assertEquals("value", variable(row, "xfm_last_daily_day").path("type_raw").textValue());
            assertEquals(SENTINEL, variable(row, "xfm_execution_day").path("identity_raw").textValue());
            var projected = FinancialProjector.projectRecord(new NativeId(id), body(row), UNSIGNED);
            assertTrue(projected.issues().isEmpty(), id);
            assertEquals(BigInteger.valueOf(-1), projected.story().orElseThrow().number(NumberField.LAST_DAILY_DAY).orElseThrow());
            assertEquals(id.equals("75") ? "1" : "2", projected.story().orElseThrow().permanentId().orElseThrow().value());
            assertEquals(id.equals("75") ? "57" : "56", projected.story().orElseThrow().reference(ReferenceField.COIN).orElseThrow().nativeId().value());
            assertTrue(FinancialProjector.projectRecord(new NativeId(id), body(row), OMITTED).issues().stream()
                    .anyMatch(issue -> issue.field().equals("xfm_last_daily_day") && issue.detail().contains("Fractional")), "legacy mode must not silently change");
        }
    }

    @Test void signedBoundaryLatticeScalesExactlyAndRawExtremaRemainFractional() {
        assertNumber("0", BigInteger.ZERO);
        assertNumber("100000", BigInteger.ONE);
        assertNumber(SENTINEL, BigInteger.valueOf(-1));
        // Nearest exactly-scaled integral values inside the signed64 extrema.
        assertNumber("9223372036854700000", new BigInteger("92233720368547"));
        assertNumber("9223372036854851616", new BigInteger("-92233720368547"));
        for (String fractional : List.of("1", "9223372036854775807", "9223372036854775808", U64_MAX)) {
            var projection = numeric(fractional, UNSIGNED);
            assertTrue(projection.story().orElseThrow().number(NumberField.LAST_DAILY_DAY).isEmpty());
            assertTrue(projection.issues().stream().anyMatch(issue -> issue.detail().contains("Fractional")), fractional);
        }
    }

    @Test void unsignedRangeAndCanonicalSpellingRejectRatherThanWrapOrCoerce() {
        for (String raw : List.of("18446744073709551616", "18446744073709651616", "999999999999999999999999999999999999",
                "-100000", "-0", "+100000", "0100000", "100000.0", "1e5", "\"100000\"", "true")) {
            var projection = numeric(raw, UNSIGNED);
            assertTrue(projection.story().orElseThrow().number(NumberField.LAST_DAILY_DAY).isEmpty(), raw);
            assertTrue(projection.issues().stream().anyMatch(issue -> issue.severity() == Severity.INCOMPLETE), raw);
        }
        assertTrue(numeric("18446744073709651616", UNSIGNED).issues().stream().anyMatch(issue -> issue.detail().contains("out of range")));
        assertEquals(BigInteger.valueOf(-1), numeric("-100000", STRICT).story().orElseThrow().number(NumberField.LAST_DAILY_DAY).orElseThrow());
        assertEquals(BigInteger.valueOf(-1), numeric("-100000", OMITTED).story().orElseThrow().number(NumberField.LAST_DAILY_DAY).orElseThrow());
    }

    @Test void missingDuplicateMalformedAndUnknownValueBodiesCannotBecomeZero() {
        for (String data : List.of("", "identity=0", "type=story", "type=value identity={}", "type=value identity=0 identity=0",
                "type=value type=value", "type=value unknown=0", "type=value identity=100000 unknown=0")) {
            var projection = project(contract("{flag=xfm_last_daily_day data={" + data + "}}"), UNSIGNED);
            assertTrue(projection.story().orElseThrow().number(NumberField.LAST_DAILY_DAY).isEmpty(), data);
        }
        for (String variable : List.of("", "{flag=xfm_last_daily_day}", "{flag=xfm_last_daily_day data=0}"))
            assertTrue(project(contract(variable), UNSIGNED).story().orElseThrow().number(NumberField.LAST_DAILY_DAY).isEmpty());
        assertEquals(BigInteger.ZERO, project(contract("{flag=xfm_last_daily_day data={type=value}}"), UNSIGNED)
                .story().orElseThrow().number(NumberField.LAST_DAILY_DAY).orElseThrow());
        var duplicate = project(contract("{flag=xfm_last_daily_day data={type=value}} {flag=xfm_last_daily_day data={type=value}}"), UNSIGNED);
        assertTrue(duplicate.issues().stream().anyMatch(issue -> issue.severity() == Severity.VIOLATION));
    }

    @Test void referencesAndPositivePermanentIdsNeverUseNumericTwosComplement() {
        var reference = project(contract("{flag=xfm_coin data={type=story identity=" + U64_MAX + "}} {flag=xfm_holder data={type=char identity=" + U64_MAX + "}}"), UNSIGNED);
        assertEquals(U64_MAX, reference.story().orElseThrow().reference(ReferenceField.COIN).orElseThrow().nativeId().value());
        assertEquals(U64_MAX, reference.story().orElseThrow().reference(ReferenceField.HOLDER).orElseThrow().nativeId().value());
        for (String value : List.of("type=story", "type=story identity=-1", "type=story identity=18446744073709551616", "type=value identity=" + SENTINEL)) {
            var invalid = project(contract("{flag=xfm_coin data={" + value + "}}"), UNSIGNED);
            assertTrue(invalid.story().orElseThrow().reference(ReferenceField.COIN).isEmpty(), value);
        }
        var id = project(Clausewitz.parse("story_cycle=xfm_futures_contract variables={data={{flag=xfm_contract_id data={type=value identity=" + SENTINEL + "}}}}"), UNSIGNED);
        assertTrue(id.issues().stream().anyMatch(issue -> issue.field().equals("permanent_id") && issue.severity() == Severity.VIOLATION));
        var cash = project(Clausewitz.parse("story_cycle=xfm_finance_account variables={data={{flag=xfm_account_id data={type=value identity=100000}} {flag=xfm_free_cents data={type=value identity=" + SENTINEL + "}}}}"), UNSIGNED);
        var snapshot = new FinancialSnapshot(MACHINE, "0".repeat(64), "1.21.0", "19", "1066.9.16", List.of(cash.story().orElseThrow()), cash.issues());
        assertTrue(FinancialAudit.audit(snapshot).issues().stream().anyMatch(issue -> issue.field().equals("xfm_free_cents") && issue.severity() == Severity.VIOLATION),
                "decoding a signed amount does not forgive negative cash");
    }

    @Test void explicitModeRoundTripsInNestedPortableRequestAndRequiresExactDeclaredTuple() throws Exception {
        Path source = directory.resolve("software-request-only.txt"); Files.writeString(source, "Authored request fixture, not physical SAVE.");
        var request = new SaveAuditCommand.Request(1, directory.toAbsolutePath().toString(),
                new FinancialSaveAuditMain.Inputs(MACHINE, FilePins.pin(source), List.of(), UNSIGNED, List.of()));
        assertEquals(request, SaveJson.read(SaveJson.write(request), SaveAuditCommand.Request.class));
        String json = new String(SaveJson.write(UNSIGNED), StandardCharsets.UTF_8);
        for (String malformed : List.of(json.replace("1.21.0", "1.21.1"), json.replace("\"19\"", "\"18\""), json.replace("100000", "1"),
                json.replace("\"unsigned64OmittedZero\"", "null"), json.replace("\"unsigned64OmittedZero\"", "true"), json.replace("unsigned64OmittedZero", "unsigned32OmittedZero")))
            assertThrows(IOException.class, () -> SaveJson.read(malformed.getBytes(StandardCharsets.UTF_8), LayoutHypothesis.class));
        assertEquals(NumberIdentityEncoding.identityRequired, new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char").numberIdentityEncoding());
    }

    @Test void sharedTwoPassReaderUsesActualSentinelsAndChecksCompleteHeaderBeforeProjection() throws Exception {
        JsonNode discovered = discovery();
        String text = "CK3txt meta_data={version=\"1.21.0\" save_game_version=19 meta_date=1066.9.16} variables={data={{flag=xfm_exchange data={type=story identity=52}}}} stories={active={"
                + "52=" + body(record(discovered, "xfm_finance_exchange", "52")).render()
                + "75=" + body(record(discovered, "xfm_futures_contract", "75")).render()
                + "96=" + body(record(discovered, "xfm_futures_contract", "96")).render() + "}}";
        Path source = directory.resolve("observed-envelopes-software-projection.txt"); Files.writeString(source, text);
        var read = FinancialSaveReader.read(source, MACHINE, UNSIGNED);
        assertEquals(2, read.coverage().passes()); assertEquals(3, read.financialStories().size()); assertTrue(read.financialIssues().isEmpty());
        assertFalse(read.sourceLayoutQualified());
        assertEquals(2, FinancialSaveReader.read(source, MACHINE, OMITTED).financialIssues().size(), "preserve the two old fractional sentinel issues");
        int i = 0;
        for (String bad : List.of(text.replace("1.21.0", "1.20.0.4"), text.replace("save_game_version=19", "save_game_version=18"),
                text.replace("version=\"1.21.0\"", "version=\"1.21.0\" version={}"), text.replace("save_game_version=19", "save_game_version=19 save_game_version={}"),
                text.replace("version=\"1.21.0\"", ""), text.replace("save_game_version=19", "save_game_version={}"))) {
            Path malformed = directory.resolve("bad-header-" + i++ + ".txt"); Files.writeString(malformed, bad);
            assertThrows(IOException.class, () -> FinancialSaveReader.read(malformed, MACHINE, UNSIGNED));
        }
    }

    private static LayoutHypothesis layout(NumberIdentityEncoding encoding) { return new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char", encoding); }
    private static FinancialProjector.RecordProjection numeric(String raw, LayoutHypothesis layout) { return project(contract("{flag=xfm_last_daily_day data={type=value identity=" + raw + "}}"), layout); }
    private static FinancialProjector.RecordProjection project(Block body, LayoutHypothesis layout) { return FinancialProjector.projectRecord(new NativeId("75"), body, layout); }
    private static Block contract(String variable) { return Clausewitz.parse("story_cycle=xfm_futures_contract variables={data={{flag=xfm_contract_id data={type=value identity=100000}} " + variable + "}}"); }
    private static void assertNumber(String raw, BigInteger expected) { assertEquals(expected, numeric(raw, UNSIGNED).story().orElseThrow().number(NumberField.LAST_DAILY_DAY).orElseThrow(), raw); }
    private static JsonNode discovery() throws IOException {
        byte[] bytes;
        try (var input = Unsigned64LayoutTest.class.getResourceAsStream("/saveaudit/r0013-zero-wallet-layout-discovery.actual.json")) { assertNotNull(input); bytes = input.readAllBytes(); }
        assertEquals(57640, bytes.length); assertEquals(DISCOVERY_SHA, FilePins.sha256(bytes)); return new ObjectMapper().readTree(bytes);
    }
    private static JsonNode record(JsonNode discovery, String type, String id) {
        for (JsonNode row : discovery.path("coverage").path("representative_records").path(type)) if (row.path("native_story_id").asText().equals(id)) return row;
        throw new AssertionError("missing actual record " + type + "/" + id);
    }
    private static JsonNode variable(JsonNode row, String name) {
        for (JsonNode variable : row.path("variables")) if (variable.path("flag").asText().equals(name)) return variable;
        throw new AssertionError("missing actual variable " + name);
    }
    private static Block body(JsonNode row) {
        List<Entry> entries = new ArrayList<>(), variables = new ArrayList<>();
        for (JsonNode scalar : row.path("direct_scalar_tokens")) entries.add(new Entry(scalar.path("key").textValue(), "=", new Atom(scalar.path("raw").textValue())));
        for (JsonNode variable : row.path("variables")) {
            assertTrue(variable.path("other_scalar_tokens").isEmpty()); assertTrue(variable.path("nested_field_names").isEmpty());
            List<Entry> data = new ArrayList<>();
            if (!variable.get("type_raw").isNull()) data.add(new Entry("type", "=", new Atom(variable.get("type_raw").textValue())));
            if (variable.path("identity_present").booleanValue()) data.add(new Entry("identity", "=", new Atom(variable.get("identity_raw").textValue())));
            variables.add(new Entry("", "", new Block(List.of(new Entry("flag", "=", new Atom(variable.path("flag").textValue())), new Entry("data", "=", new Block(data))))));
        }
        entries.add(new Entry("variables", "=", new Block(List.of(new Entry("data", "=", new Block(variables)))))); return new Block(entries);
    }
}
