package org.xar.ck3.markets.savefingerprint;

import java.io.IOException;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.Type;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveJson;
import org.xar.ck3.save.SaveStream;
import static org.junit.jupiter.api.Assertions.*;

final class FinancialStoryDigestTest {
    @TempDir Path directory;
    private int next;
    private static final String DATE = "1066.12.21";
    private static String scene(String records) {
        return "date=" + DATE + " meta_data={version=\"1.21.0\" save_game_version=19} stories={active={" + records + "}}";
    }
    private static String record(String id, Type type, String extra) {
        String permanent = type.permanentField().map(field -> "{flag=" + field.wire() + " data={type=value identity=100000}}").orElse("");
        return id + "={story_cycle=" + type.wire() + " owner=31254 variables={data={" + permanent + "}" + extra + "}}";
    }
    private Path save(String text) throws Exception {
        Path save = directory.resolve("fixture-" + next++ + ".ck3"); Files.writeString(save, text); return save;
    }
    private FinancialStoryDigest.Result read(String text) throws Exception {
        Path save = save(text);
        return FinancialStoryDigest.read(save, FilePins.pin(save), "synthetic-whole-digest-machine", DATE,
                FinancialStoryDigest.Limits.standard(), List.of());
    }
    private static String hash(FinancialStoryDigest.Result result) { return result.records().getFirst().canonicalTokenSha256(); }

    @Test void allThirteenTypesAreSelectedIncludingUnreferencedRecordsAndIdentityIsExplicit() throws Exception {
        StringBuilder records = new StringBuilder(); int id = 1;
        for (Type type : Type.values()) records.append(record(Integer.toString(id++), type, ""));
        var result = read(scene(records.toString()));
        assertEquals(13, result.records().size()); assertEquals(13, result.tableRecords());
        assertEquals(List.of(Type.values()).stream().map(Type::wire).toList(), result.records().stream().map(FinancialStoryDigest.RecordDigest::type).toList());
        for (var item : result.records()) {
            assertEquals(Type.fromWire(item.type()).orElseThrow().permanentField().isPresent(), item.permanentIdPresent());
            assertEquals(item.permanentIdPresent() ? "1" : "", item.permanentId());
        }
        assertEquals(result, SaveJson.read(SaveJson.write(result), FinancialStoryDigest.Result.class));
        assertFalse(result.financialCertified()); assertEquals(2, result.completePasses());
    }
    @Test void unknownNumericAndTypedScopeFieldsAreInsideWholeRecordDigest() throws Exception {
        String base = record("7", Type.COIN, "future_feature={value=1 reference={type=story identity=88}}");
        String first = hash(read(scene(base)));
        assertNotEquals(first, hash(read(scene(base.replace("value=1", "value=2")))));
        assertNotEquals(first, hash(read(scene(base.replace("type=story", "type=char")))));
        assertNotEquals(first, hash(read(scene(base.replace("identity=88", "identity=89")))));
        assertNotEquals(hash(read(scene(record("7", Type.COIN, "")))), hash(read(scene(record("7", Type.COIN, "unknown={}")))));
    }
    @Test void orderedListsAndRepeatedItemsAreNotNormalizedAway() throws Exception {
        String base = record("7", Type.COIN, "list={{name=\"xfm_subscriptions\" item={type=story identity=88} item={type=story identity=89}}}");
        String first = hash(read(scene(base)));
        assertNotEquals(first, hash(read(scene(base.replace("identity=88", "identity=90").replace("identity=89", "identity=88").replace("identity=90", "identity=89")))));
        assertNotEquals(first, hash(read(scene(base.replace("identity=89", "identity=88")))));
    }
    @Test void RealNewsPermanentIdAndUnknownBodyOrQueueLinkChangesArePreserved() throws Exception {
        // xfm_news_queue writes these actual fields; news remains separate from the 13 monetary Type enum.
        String news = "99={story_cycle=xfm_news_entry owner=31254 variables={data={"
                + "{flag=xfm_news_id data={type=value identity=200000}}"
                + "{flag=xfm_news_event_id data={type=value identity=100000}}"
                + "{flag=xfm_news_source data={type=story identity=55}}"
                + "{flag=xfm_news_next data={type=story identity=1617}}"
                + "{flag=xfm_future_news_body data={type=value identity=100000}}}}}";
        var result = read(scene(news)); var first = result.records().getFirst();
        assertEquals("xfm_news_entry", first.type()); assertTrue(first.permanentIdPresent()); assertEquals("2", first.permanentId());
        assertNotEquals(first.canonicalTokenSha256(), hash(read(scene(news.replace("identity=1617", "identity=1618")))));
        assertNotEquals(first.canonicalTokenSha256(), hash(read(scene(news.replace("flag=xfm_future_news_body data={type=value identity=100000}",
                "flag=xfm_future_news_body data={type=value identity=200000}")))));
        assertThrows(IOException.class, () -> read(scene(news.replace("flag=xfm_news_id", "flag=xfm_missing_news_id"))));
        assertEquals(13, Type.values().length);
    }
    @Test void SameTokensWithWhitespaceOrCommentsKeepTheProducerDigest() throws Exception {
        String base = scene(record("7", Type.COIN, "future=\"a b\""));
        assertEquals(hash(read(base)), hash(read(base.replace("=", " = ").replace(" owner", " # comment\n owner"))));
        assertNotEquals(hash(read(base)), hash(read(base.replace("\"a b\"", "\"a  b\""))));
    }
    @Test void NativeTombstoneIsSeparateAndDuplicateIdOrOtherScalarIsRejected() throws Exception {
        String real = record("7", Type.COIN, ""); var result = read(scene(real + "1288=none"));
        assertEquals(1, result.records().size()); assertEquals(1, result.tableRecords()); assertEquals(2, result.tableSlots());
        assertEquals("1288", result.tombstones().getFirst().id().value());
        for (String bad : List.of(real + real, real + "7=none", real + "1288=\"none\"", real + "1288=0"))
            assertThrows(IOException.class, () -> read(scene(bad)));
    }
    @Test void TruncationWrongDateAndWrongExpectedSavePinDoNotPublishAResult() throws Exception {
        String valid = scene(record("7", Type.COIN, ""));
        assertThrows(IOException.class, () -> read(valid.substring(0, valid.length() - 1)));
        Path save = save(valid); var pin = FilePins.pin(save);
        assertThrows(IOException.class, () -> FinancialStoryDigest.read(save, pin, "synthetic-whole-digest-machine", "1066.12.20", FinancialStoryDigest.Limits.standard(), List.of()));
        var wrong = new Pin(pin.path(), pin.bytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> FinancialStoryDigest.read(save, wrong, "synthetic-whole-digest-machine", DATE, FinancialStoryDigest.Limits.standard(), List.of()));
    }
    @Test void FinancialCountRecordAndStreamWorkBudgetsAreEnforcedByActualParser() throws Exception {
        Path save = save(scene(record("7", Type.COIN, "") + record("8", Type.ACCOUNT, ""))); var pin = FilePins.pin(save);
        for (var limits : List.of(new FinancialStoryDigest.Limits(1, 1, 512 * 1024, 64L * 1024 * 1024),
                new FinancialStoryDigest.Limits(10, 1, 512 * 1024, 64L * 1024 * 1024),
                new FinancialStoryDigest.Limits(10, 10, 11, 64L * 1024 * 1024),
                new FinancialStoryDigest.Limits(10, 10, 512 * 1024, 11)))
            assertThrows(IOException.class, () -> FinancialStoryDigest.read(save, pin, "synthetic-whole-digest-machine", DATE, limits, List.of()));
    }
    @Test void MissingTypeRequiresTheExactExistingClassifiedHashAndUnknownFinancialTypesFailClosed() throws Exception {
        String retired = "51={owner=31254 seed=1 variables={data={{flag=xfma_complete data={type=value identity=100000}}}}}";
        String text = scene(record("7", Type.COIN, "") + retired); List<FinancialStoryDigest.RetiredIdentity> evidence = new ArrayList<>();
        StreamingTableSink sink = new StreamingTableSink() {
            public void discriminator(NativeId id, String type) { }
            public void record(StreamedRecord record) { fail("empty selection must not capture typed records"); }
            public void missingDiscriminator(UntypedRecord value) { evidence.add(new FinancialStoryDigest.RetiredIdentity(value.id().value(), value.canonicalTokenSha256(), value.canonicalTokenBytes())); }
        };
        new SaveStream(new StringReader(text), new Selection(List.of(), List.of(), true, false, List.of()),
                new StreamingTable(List.of("stories", "active"), "story_cycle", List.of(), 10, 512 * 1024, 64L * 1024 * 1024, true, MissingDiscriminatorPolicy.CAPTURE_MISSING_BOUNDED), sink).read();
        Path save = save(text); var result = FinancialStoryDigest.read(save, FilePins.pin(save), "synthetic-whole-digest-machine", DATE, FinancialStoryDigest.Limits.standard(), evidence);
        assertEquals(evidence, result.admittedRetiredRecords()); assertEquals(1, result.records().size());
        assertThrows(IOException.class, () -> read(text));
        Path changed = save(text.replace("xfma_complete", "xfm_free_cents"));
        assertThrows(IOException.class, () -> FinancialStoryDigest.read(changed, FilePins.pin(changed), "synthetic-whole-digest-machine", DATE, FinancialStoryDigest.Limits.standard(), evidence));
        assertThrows(IOException.class, () -> read(scene("7={story_cycle=xfm_ipo_unknown owner=31254}")));
    }
}
