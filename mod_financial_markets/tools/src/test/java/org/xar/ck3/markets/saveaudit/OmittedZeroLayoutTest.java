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
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
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

/** Exact-pinned actual discovery envelopes plus explicit software negative mutations.
 * Reconstructed Clausewitz bodies are software projections, not the physical SAVE or a cold load.
 */
final class OmittedZeroLayoutTest {
    @TempDir Path directory;
    private static final String MACHINE = "4-8e1c2f1861";
    private static final String DISCOVERY_SHA = "2147b527455eb3b9eee2d83b4eb78cc3506c69d54de97e6e8610a5b85819bc15";
    private static final String FIVE = "{\"gameVersion\":\"1.21.0\",\"saveFormat\":\"19\",\"numericScale\":100000,\"storyReferenceType\":\"story\",\"characterReferenceType\":\"char\"}";
    private static final LayoutHypothesis STRICT = new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char");
    private static final LayoutHypothesis ZERO = new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char", NumberIdentityEncoding.omittedZero);

    @Test void legacyFiveFieldNamedRequestStaysStrictAndExplicitModeRoundTrips() throws Exception {
        Path old = directory.resolve("legacy-request.json"); Files.writeString(old, request(FIVE));
        assertEquals(NumberIdentityEncoding.identityRequired, SaveAuditCommand.readRequest(old).audit().layout().numberIdentityEncoding());
        Path opted = directory.resolve("opted-request.json"); Files.writeString(opted, request(withEncoding("\"omittedZero\"")));
        var parsed = SaveAuditCommand.readRequest(opted);
        assertEquals(NumberIdentityEncoding.omittedZero, parsed.audit().layout().numberIdentityEncoding());
        assertEquals(directory.resolve("request-software-local-save.txt").toRealPath(), Path.of(parsed.audit().firstSave().path()));
        assertEquals(directory.resolve("request-software-repository").toAbsolutePath(), Path.of(parsed.repository()));
        assertNotEquals(actualDiscovery().get("save").get("sha256").textValue(), parsed.audit().firstSave().sha256(),
                "request decode uses an authored local software pin, not the physical CK3 SAVE pin");
        assertEquals(parsed, SaveJson.read(SaveJson.write(parsed), SaveAuditCommand.Request.class));
        assertEquals(NumberIdentityEncoding.identityRequired, STRICT.numberIdentityEncoding());
        assertEquals(ZERO, SaveJson.read(SaveJson.write(ZERO), LayoutHypothesis.class));
    }

    @Test void jsonEncodingOptInRejectsWrongTuplesAndWrongTypesWithoutRelaxingBoundary() {
        List<String> invalid = new ArrayList<>();
        for (String encoding : List.of("null", "true", "1", "1.0", "[]", "{}", "\"unknown\"", "\"OMITTED_ZERO\"")) invalid.add(withEncoding(encoding));
        for (String scale : List.of("\"100000\"", "100000.0", "true", "null")) invalid.add(withEncoding("\"omittedZero\"").replace(":100000,", ":" + scale + ","));
        invalid.add(withEncoding("\"omittedZero\"").replace("1.21.0", "1.21.1"));
        invalid.add(withEncoding("\"omittedZero\"").replace("\"19\"", "\"18\""));
        invalid.add(withEncoding("\"omittedZero\"").replace(":100000,", ":1,"));
        invalid.add(withEncoding("\"omittedZero\"").replace("\"numberIdentityEncoding\"", "\"unknownField\""));
        invalid.add(FIVE.replace("\"storyReferenceType\":\"story\",", ""));
        invalid.add(FIVE.replace("\"gameVersion\":\"1.21.0\"", "\"gameVersion\":true"));
        invalid.add(withEncoding("\"omittedZero\"").replace("\"numberIdentityEncoding\":", "\"numberIdentityEncoding\":\"identityRequired\",\"numberIdentityEncoding\":"));
        for (String text : invalid) assertThrows(IOException.class, () -> SaveJson.read(text.getBytes(StandardCharsets.UTF_8), LayoutHypothesis.class), text);
        assertThrows(IllegalArgumentException.class, () -> new LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char", NumberIdentityEncoding.omittedZero));
        assertThrows(IllegalArgumentException.class, () -> new LayoutHypothesis("1.21.0", "19", BigInteger.valueOf(100000), "story", "char", null));
    }

    @Test void actualR0013PositiveAndOmittedZeroEnvelopesProjectOnlyWithOptIn() throws Exception {
        Map<String, Block> records = actualBodies();
        var oldFund = FinancialProjector.projectRecord(new NativeId("53"), records.get("53"), STRICT);
        assertTrue(oldFund.story().orElseThrow().number(NumberField.FREE_CENTS).isEmpty());
        assertTrue(oldFund.issues().stream().anyMatch(issue -> issue.field().equals("xfm_free_cents") && issue.severity() == Severity.INCOMPLETE));
        var fund = FinancialProjector.projectRecord(new NativeId("53"), records.get("53"), ZERO);
        var primary = FinancialProjector.projectRecord(new NativeId("54"), records.get("54"), ZERO);
        var exchange = FinancialProjector.projectRecord(new NativeId("52"), records.get("52"), ZERO);
        assertTrue(fund.issues().isEmpty()); assertTrue(primary.issues().isEmpty()); assertTrue(exchange.issues().isEmpty());
        assertEquals("1", fund.story().orElseThrow().permanentId().orElseThrow().value());
        assertEquals(BigInteger.ZERO, fund.story().orElseThrow().number(NumberField.FREE_CENTS).orElseThrow());
        assertEquals(BigInteger.ONE, fund.story().orElseThrow().number(NumberField.SYSTEM_ACCOUNT).orElseThrow());
        assertEquals("2", primary.story().orElseThrow().permanentId().orElseThrow().value());
        assertEquals(BigInteger.valueOf(1000), primary.story().orElseThrow().number(NumberField.FREE_CENTS).orElseThrow());
        assertEquals(BigInteger.ZERO, primary.story().orElseThrow().number(NumberField.RESERVED_CENTS).orElseThrow());
        assertEquals("31254", primary.story().orElseThrow().reference(ReferenceField.HOLDER).orElseThrow().nativeId().value());
        assertEquals(BigInteger.ZERO, exchange.story().orElseThrow().number(NumberField.DAY).orElseThrow());
        assertEquals(BigInteger.TWO, exchange.story().orElseThrow().number(NumberField.NEXT_ACCOUNT_ID).orElseThrow());
        assertEquals(BigInteger.valueOf(1000), FinancialProjector.projectRecord(new NativeId("54"), records.get("54"), STRICT)
                .story().orElseThrow().number(NumberField.FREE_CENTS).orElseThrow());
    }

    @Test void missingVariableDataTypeAndMalformedIdentityAreNeverOmittedZero() {
        List<String> invalidData = List.of("", "identity=0", "type=story", "type=value identity={}",
                "type=value identity=0 identity=0", "type=value type=value", "type=value identity=00",
                "type=value identity=0.0", "type=value identity=\"0\"", "type=value identity=true",
                "type=value unexpected=100000");
        for (String data : invalidData) {
            var projection = FinancialProjector.projectRecord(new NativeId("54"), account("{flag=xfm_free_cents data={" + data + "}}"), ZERO);
            assertTrue(projection.story().orElseThrow().number(NumberField.FREE_CENTS).isEmpty(), data);
            assertTrue(projection.issues().stream().anyMatch(issue -> issue.severity() == Severity.INCOMPLETE), data);
        }
        for (String missing : List.of("", "{flag=xfm_free_cents}", "{flag=xfm_free_cents data=0}")) {
            var projection = FinancialProjector.projectRecord(new NativeId("54"), account(missing), ZERO);
            assertTrue(projection.story().orElseThrow().number(NumberField.FREE_CENTS).isEmpty());
        }
        assertEquals(BigInteger.ZERO, FinancialProjector.projectRecord(new NativeId("54"), account("{flag=xfm_free_cents data={type=value identity=0}}"), STRICT)
                .story().orElseThrow().number(NumberField.FREE_CENTS).orElseThrow());
    }

    @Test void referenceOmissionsAndDuplicateFinancialVariablesStayRejected() {
        for (String reference : List.of("{flag=xfm_holder data={type=char}}", "{flag=xfm_legal_entity data={type=story}}")) {
            var projection = FinancialProjector.projectRecord(new NativeId("54"), account(reference), ZERO);
            assertTrue(projection.story().orElseThrow().references().isEmpty());
            assertTrue(projection.issues().stream().anyMatch(issue -> issue.severity() == Severity.INCOMPLETE));
        }
        var duplicate = FinancialProjector.projectRecord(new NativeId("54"), account(
                "{flag=xfm_free_cents data={type=value}} {flag=xfm_free_cents data={type=value}}"), ZERO);
        assertTrue(duplicate.issues().stream().anyMatch(issue -> issue.severity() == Severity.VIOLATION));
    }

    @Test void sharedReaderBindsOptInToActualHeaderAndStrictModeKeepsOldBehavior() throws Exception {
        String body = actualScene(); Path proper = directory.resolve("observed-envelope-projection.txt"); Files.writeString(proper, body);
        var observed = FinancialSaveReader.read(proper, MACHINE, ZERO);
        assertEquals(3, observed.financialStories().size()); assertTrue(observed.financialIssues().isEmpty());
        assertFalse(observed.sourceLayoutQualified());
        Path wrong = directory.resolve("wrong-version.txt"); Files.writeString(wrong, body.replace("\"1.21.0\"", "\"1.20.0.4\""));
        assertThrows(IOException.class, () -> FinancialSaveReader.read(wrong, MACHINE, ZERO));
        Path wrongFormat = directory.resolve("wrong-format.txt"); Files.writeString(wrongFormat, body.replace("save_game_version=19", "save_game_version=18"));
        assertThrows(IOException.class, () -> FinancialSaveReader.read(wrongFormat, MACHINE, ZERO));
        assertTrue(FinancialSaveReader.read(wrong, MACHINE, STRICT).financialIssues().stream().anyMatch(issue -> issue.field().equals("xfm_free_cents")));
    }

    @Test void fullHeaderRejectsDuplicateBlockMissingAndMalformedMetadataBeforeZeroProjection() throws Exception {
        String body = actualScene();
        List<String> invalid = List.of(
                body.replace("version=\"1.21.0\"", "version=\"1.21.0\" version={}"),
                body.replace("save_game_version=19", "save_game_version=19 save_game_version={}"),
                body.replace("version=\"1.21.0\"", "version=\"1.21.0\" version=\"1.21.0\""),
                body.replace("save_game_version=19", "save_game_version=19 save_game_version=19"),
                body.replace("version=\"1.21.0\"", ""),
                body.replace("save_game_version=19", ""),
                body.replace("version=\"1.21.0\"", "version={}"),
                body.replace("save_game_version=19", "save_game_version={}"),
                body.replace("version=\"1.21.0\"", "version=true"),
                body.replace("save_game_version=19", "save_game_version=\"19\""));
        int index = 0;
        for (String malformed : invalid) {
            Path path = directory.resolve("malformed-metadata-" + index++ + ".txt"); Files.writeString(path, malformed);
            assertThrows(IOException.class, () -> FinancialSaveReader.read(path, MACHINE, ZERO));
        }
        Path strict = directory.resolve("legacy-block-header.txt"); Files.writeString(strict, invalid.getFirst());
        assertTrue(FinancialSaveReader.read(strict, MACHINE, STRICT).financialIssues().stream()
                .anyMatch(issue -> issue.field().equals("xfm_free_cents")), "strict mode keeps its previous read behavior");
        Path nested = directory.resolve("valid-nested-metadata.txt");
        Files.writeString(nested, body.replace("meta_date=", "other_metadata={key=value} meta_date="));
        var read = FinancialSaveReader.read(nested, MACHINE, ZERO);
        assertEquals(2, read.coverage().passes());
        var full = read.projection().projections().stream().filter(p -> p.name().equals("number_encoding_metadata")).findFirst().orElseThrow();
        assertTrue(full.ast().named("other_metadata").getFirst().value() instanceof Block);
        assertTrue(read.financialIssues().isEmpty());
        Path oversized = directory.resolve("bounded-metadata.txt");
        Files.writeString(oversized, body.replace("meta_date=", "padding=\"" + "x".repeat(512 * 1024) + "\" meta_date="));
        assertThrows(IOException.class, () -> FinancialSaveReader.read(oversized, MACHINE, ZERO), "existing shared metadata/projection caps remain enforced");
    }

    private static String withEncoding(String value) { return FIVE.substring(0, FIVE.length() - 1) + ",\"numberIdentityEncoding\":" + value + '}'; }
    private static Block account(String variable) { return Clausewitz.parse("story_cycle=xfm_finance_account variables={data={" + variable + "}}"); }
    private static JsonNode actualDiscovery() throws IOException {
        byte[] bytes;
        try (var stream = OmittedZeroLayoutTest.class.getResourceAsStream("/saveaudit/r0013-wallet-layout-discovery.actual.json")) {
            assertNotNull(stream); bytes = stream.readAllBytes();
        }
        assertEquals(21371, bytes.length); assertEquals(DISCOVERY_SHA, FilePins.sha256(bytes));
        return new ObjectMapper().readTree(bytes);
    }
    private String request(String layout) throws IOException {
        // Request decoding is host-local software coverage. Keep the real discovery resource unchanged.
        Path repository = Files.createDirectories(directory.resolve("request-software-repository")).toAbsolutePath();
        Path softwareSave = directory.resolve("request-software-local-save.txt").toAbsolutePath();
        Files.writeString(softwareSave, "Authored local request-decode fixture; not a physical CK3 SAVE.");
        String repositoryJson = new String(SaveJson.write(repository.toString()), StandardCharsets.UTF_8);
        String pinJson = new String(SaveJson.write(FilePins.pin(softwareSave)), StandardCharsets.UTF_8);
        return "{\"schemaVersion\":1,\"repository\":" + repositoryJson + ",\"audit\":{\"machineId\":\"" + MACHINE
                + "\",\"firstSave\":" + pinJson + ",\"coldSave\":[],\"decoder\":[],\"layout\":" + layout + "}}";
    }
    private static Map<String, Block> actualBodies() throws IOException {
        Map<String, Block> result = new LinkedHashMap<>();
        for (JsonNode group : actualDiscovery().path("coverage").path("representative_records")) for (JsonNode row : group) {
            List<Entry> body = new ArrayList<>();
            for (JsonNode scalar : row.path("direct_scalar_tokens")) body.add(new Entry(scalar.path("key").textValue(), "=", new Atom(scalar.path("raw").textValue())));
            List<Entry> variables = new ArrayList<>();
            for (JsonNode variable : row.path("variables")) {
                assertTrue(variable.path("other_scalar_tokens").isEmpty()); assertTrue(variable.path("nested_field_names").isEmpty());
                List<Entry> data = new ArrayList<>();
                if (!variable.get("type_raw").isNull()) data.add(new Entry("type", "=", new Atom(variable.get("type_raw").textValue())));
                if (variable.path("identity_present").booleanValue()) data.add(new Entry("identity", "=", new Atom(variable.get("identity_raw").textValue())));
                variables.add(new Entry("", "", new Block(List.of(new Entry("flag", "=", new Atom(variable.path("flag").textValue())), new Entry("data", "=", new Block(data))))));
            }
            body.add(new Entry("variables", "=", new Block(List.of(new Entry("data", "=", new Block(variables))))));
            result.put(row.path("native_story_id").textValue(), new Block(body));
        }
        assertEquals(3, result.size()); return result;
    }
    private static String actualScene() throws IOException {
        StringBuilder result = new StringBuilder("CK3txt meta_data={version=\"1.21.0\" save_game_version=19 meta_date=1066.9.15} variables={data={{flag=xfm_exchange data={type=story identity=52}}}} stories={active={");
        for (var entry : new TreeMap<>(actualBodies()).entrySet()) result.append(entry.getKey()).append('=').append(entry.getValue().render());
        return result.append("}}").toString();
    }
}
