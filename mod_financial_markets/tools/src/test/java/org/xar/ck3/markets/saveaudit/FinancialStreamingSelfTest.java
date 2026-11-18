package org.xar.ck3.markets.saveaudit;

import java.io.IOException;
import java.io.StringReader;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveContracts.*;
import org.xar.ck3.save.SaveDecoder;
import org.xar.ck3.save.SaveStream;

/** New growth/failure regressions; generated data is never real-save qualification. */
public final class FinancialStreamingSelfTest {
    private FinancialStreamingSelfTest() { }
    private static final String MACHINE = "synthetic-streaming-audit-fixture";
    private static final FinancialProjector.LayoutHypothesis LAYOUT = new FinancialProjector.LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");
    private static int assertions;
    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory(Path.of(args[0]), "streaming-regression-");
        String expanded = expandedScene(2500);
        check(expanded.getBytes(StandardCharsets.UTF_8).length > 512 * 1024, "fixture genuinely crosses old whole-table cap");
        Path large = write(directory, "many-accounts", expanded);
        FinancialSaveReader.Readback largeRead = FinancialSaveReader.read(large, MACHINE, LAYOUT);
        FinancialSnapshot accounts = FinancialProjector.project(largeRead, LAYOUT);
        check(FinancialAudit.audit(accounts).assessment() == FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, "all positive/zero-explicit funded accounts reconcile beyond 512KiB");
        check(largeRead.coverage().selectedFinancialRecords() == 2505 && accounts.stories().size() == 2505, "no selected account silently truncated");
        check(FinancialAudit.audit(accounts).ledgerCashStockCents().cents().equals("12800"), "all additional real-valued fixture balances contribute exactly to cash stock");
        check(largeRead.coverage().streamedFinancialTokenBytes() > 512 * 1024 && largeRead.projection().selectedTokenBytes() < 4096,
                "streamed work is separate from retained metadata/global projections");
        check(!largeRead.sourceLayoutQualified() && !FinancialAudit.audit(accounts).financialCertified(), "growth regression cannot qualify live financial data");
        Selection old = new Selection(List.of(), List.of(new ProjectionSelection("old-stories", ProjectionKind.OTHER,
                List.of("stories", "active"), 1, 512 * 1024, true)), true, false, List.of());
        rejects(() -> new SaveStream(new StringReader(expanded), old).read(), "legacy whole-block cap still rejects same large table");
        FinancialSaveReader.Readback beyondRetained = FinancialSaveReader.read(write(directory, "beyond-4MiB", expandedScene(15000)), MACHINE, LAYOUT);
        check(beyondRetained.coverage().streamedFinancialTokenBytes() > 4 * 1024 * 1024 && beyondRetained.projection().selectedTokenBytes() < 4096,
                "more than original 4MiB retained cap can stream without accumulating record ASTs");
        check(FinancialAudit.audit(FinancialProjector.project(beyondRetained, LAYOUT)).ledgerCashStockCents().cents().equals("25300")
                && beyondRetained.financialStories().size() == 15005, "larger financial stream preserves every account ID and exact cent");

        String giant = "900000={payload=\"" + "v".repeat(900 * 1024) + "\" story_cycle=vanilla_large_story} ";
        Path nonFinancial = write(directory, "large-vanilla-late-type", append(FinancialSaveAuditSelfTest.scene(), giant));
        FinancialSaveReader.Readback skipped = FinancialSaveReader.read(nonFinancial, MACHINE, LAYOUT);
        check(skipped.coverage().tableRecords() == 6 && skipped.coverage().selectedFinancialRecords() == 5, "900KiB nonfinancial story with late type is traversed but not captured");
        check(FinancialAudit.compareCold(FinancialProjector.project(FinancialSaveReader.read(write(directory, "base", FinancialSaveAuditSelfTest.scene()), MACHINE, LAYOUT), LAYOUT),
                FinancialProjector.project(skipped, LAYOUT)).exactSelectedFinancialState(), "large vanilla payload leaves exact financial identities and cents unchanged");
        check(skipped.coverage().streamedFinancialTokenBytes() < 4096, "nonfinancial payload does not consume financial retention/work budget");
        String malformed = append(FinancialSaveAuditSelfTest.scene(), "900000={story_cycle=vanilla_large payload={ broken= }} ");
        rejects(() -> FinancialSaveReader.read(write(directory, "malformed-vanilla", malformed), MACHINE, LAYOUT), "ignored vanilla record syntax still validated");

        int cap = 512 * 1024;
        String boundaryBody = paddedBody(cap);
        List<StreamedRecord> records = new ArrayList<>();
        SaveStream exact = stream("stories={active={1={" + boundaryBody + "}}}", List.of(new NativeId("1")), cap, 2L * cap, records);
        exact.read();
        check(records.size() == 1 && records.getFirst().canonicalTokenBytes() == cap, "single financial record exact 512KiB boundary succeeds");
        check(records.getFirst().ast().block("variables").block("data").entries().size() == 1, "boundary parser preserves actual financial variable envelope");
        check(exact.streamingObservation().streamedTokenBytes() == cap, "canonical UTF8 byte budget is measured exactly");
        rejects(() -> stream("stories={active={1={" + boundaryBody.replace("pad=\"", "pad=\"x") + "}}}", List.of(new NativeId("1")), cap, 2L * cap, new ArrayList<>()).read(), "single financial record cap plus one is rejected");
        rejects(() -> stream("stories={active={1={" + paddedBody(1024).replaceFirst("v", "é") + "}}}", List.of(new NativeId("1")), 1024, cap, new ArrayList<>()).read(), "multibyte financial payload obeys UTF8 bytes rather than character count");
        String oversizedFinancial = append(FinancialSaveAuditSelfTest.scene(), "900000={pad=\"" + "v".repeat(600 * 1024) + "\" story_cycle=xfm_finance_account} ");
        rejects(() -> FinancialSaveReader.read(write(directory, "oversized-financial-late-type", oversizedFinancial), MACHINE, LAYOUT), "late financial type cannot evade per-record budget");

        String one = "story_cycle=xfm_finance_account variables={data={{flag=xfm_account_id data={type=value identity=100000}}}}";
        int oneBytes = canonicalBytes(one);
        String two = "stories={active={1={" + one + "} 2={" + one + "}}}";
        rejects(() -> stream(two, List.of(new NativeId("1"), new NativeId("2")), cap, 2L * oneBytes - 1, new ArrayList<>()).read(), "aggregate streamed byte budget remains finite");
        rejects(() -> stream("stories={active={1={story_cycle=vanilla} 1={story_cycle=vanilla}}}", List.of(), cap, cap, new ArrayList<>()).read(), "duplicate IDs rejected even for unselected vanilla records");
        rejects(() -> stream("stories={active={1={payload=untyped}}}", List.of(), cap, cap, new ArrayList<>()).read(), "missing direct discriminator is not silently skipped");
        rejects(() -> stream("stories={active={1={story_cycle=vanilla story_cycle=xfm_finance_account}}}", List.of(), cap, cap, new ArrayList<>()).read(), "ambiguous discriminator rejected");
        rejects(() -> stream("stories={active={1={story_cycle=vanilla story_cycle={bad=yes}}}}", List.of(), cap, cap, new ArrayList<>()).read(), "block discriminator cannot hide behind a scalar discriminator");
        rejects(() -> stream("stories={active={1=xfm_finance_account}}", List.of(), cap, cap, new ArrayList<>()).read(), "scalar record is unrecognized instead of empty table");
        rejects(() -> stream("stories={active={1={story_cycle=vanilla}}}", List.of(new NativeId("2")), cap, cap, new ArrayList<>()).read(), "selected record disappearance is rejected");
        FinancialSaveReader.Budgets lowCount = new FinancialSaveReader.Budgets(200000, 4, cap, 64L * 1024 * 1024, 1000000);
        rejects(() -> FinancialSaveReader.read(write(directory, "count-budget", FinancialSaveAuditSelfTest.scene()), MACHINE, LAYOUT, lowCount), "financial identity plan has an explicit count budget");
        FinancialSaveReader.Budgets lowFields = new FinancialSaveReader.Budgets(200000, 65536, cap, 64L * 1024 * 1024, 3);
        rejects(() -> FinancialSaveReader.read(write(directory, "field-budget", FinancialSaveAuditSelfTest.scene()), MACHINE, LAYOUT, lowFields), "typed field/issue projection has an explicit retained budget");
        FinancialSnapshot unknown = FinancialProjector.project(FinancialSaveReader.read(write(directory, "new-financial-type", append(FinancialSaveAuditSelfTest.scene(), "900000={story_cycle=xfm_finance_new_wallet}")), MACHINE, LAYOUT), LAYOUT);
        check(FinancialAudit.audit(unknown).assessment() == FinancialAudit.Assessment.INCOMPLETE, "unknown future finance subtype is captured as incomplete, not omitted");
        decoderOverload(directory, one);
        System.out.println("STREAMING_SYNTHETIC_SELF_TEST assertions=" + assertions + " status=PASS directory=" + directory);
    }

    private static void decoderOverload(Path directory, String body) throws Exception {
        Path save = write(directory, "decoder-fixture", "stories={active={1={" + body + "}}}");
        Path java = Path.of(System.getProperty("java.home"), "bin", "java.exe");
        StreamingTable table = new StreamingTable(List.of("stories", "active"), "story_cycle", List.of(new NativeId("1")), 32, 512 * 1024, 1024 * 1024, true);
        List<StreamedRecord> records = new ArrayList<>();
        var decoded = SaveDecoder.inspect(FilePins.pin(save), FilePins.pin(java), emptySelection(), new DecoderLimits(2 * 1024 * 1024, 65536, Duration.ofSeconds(10)),
                (executable, input) -> child(executable, input, false), table, sink(records));
        check(decoded.exitCode() == 0 && records.size() == 1, "shared decoder streaming overload delivers selected financial AST after normal child output");
        rejects(() -> SaveDecoder.inspect(FilePins.pin(save), FilePins.pin(java), emptySelection(), new DecoderLimits(2 * 1024 * 1024, 65536, Duration.ofSeconds(10)),
                (executable, input) -> child(executable, input, true), table, sink(new ArrayList<>())), "nonzero decoder remains failure despite provisional record callback");
    }
    private static Process child(Path executable, Path input, boolean fail) throws IOException {
        return new ProcessBuilder(executable.toString(), "-Xms16m", "-Xmx64m", "-cp", System.getProperty("surefire.test.class.path", System.getProperty("java.class.path")), Child.class.getName(), input.toString(), Boolean.toString(fail)).start();
    }
    public static final class Child {
        private Child() { }
        public static void main(String[] args) throws IOException { System.out.print(Files.readString(Path.of(args[0]))); if (Boolean.parseBoolean(args[1])) System.exit(7); }
    }
    private static Selection emptySelection() { return new Selection(List.of(), List.of(), false, false, List.of()); }
    private static SaveStream stream(String source, List<NativeId> selected, int recordBytes, long totalBytes, List<StreamedRecord> records) {
        return new SaveStream(new StringReader(source), emptySelection(), new StreamingTable(List.of("stories", "active"), "story_cycle", selected, 200000, recordBytes, totalBytes, true), sink(records));
    }
    private static StreamingTableSink sink(List<StreamedRecord> records) {
        return new StreamingTableSink() {
            @Override public void discriminator(NativeId id, String value) { }
            @Override public void record(StreamedRecord record) { records.add(record); }
        };
    }
    private static String paddedBody(int bytes) {
        String body = "pad=\"\" variables={data={{flag=xfm_account_id data={type=value identity=100000}}}} story_cycle=xfm_finance_account";
        return body.replace("pad=\"\"", "pad=\"" + "v".repeat(bytes - canonicalBytes(body)) + "\"");
    }
    private static int canonicalBytes(String body) { return ("record = " + Clausewitz.parse("record={" + body + "}").block("record").render() + ' ').getBytes(StandardCharsets.UTF_8).length; }
    private static String expandedScene(int count) {
        StringBuilder extra = new StringBuilder();
        for (int n = 0; n < count; n++) extra.append(1000 + n).append("={story_cycle=xfm_finance_account owner=31254 variables={data={")
                .append("{flag=xfm_account_id data={type=value identity=").append((n + 2L) * 100000).append("}}")
                .append("{flag=xfm_free_cents data={type=value identity=100000}}{flag=xfm_reserved_cents data={type=value identity=0}}{flag=xfm_holder data={type=char identity=31254}}}}} ");
        return append(FinancialSaveAuditSelfTest.scene().replace("flag=xfm_next_account_id data={type=value identity=100000}",
                "flag=xfm_next_account_id data={type=value identity=" + (count + 1L) * 100000 + "}"), extra.toString());
    }
    private static String append(String source, String story) { return source.substring(0, source.length() - 2) + story + "}}"; }
    private static Path write(Path directory, String name, String source) throws IOException { Path file = directory.resolve(name + ".txt"); Files.writeString(file, source); return file; }
    private static void check(boolean result, String label) { assertions++; if (!result) throw new AssertionError(label); }
    @FunctionalInterface private interface Work { void run() throws Exception; }
    private static void rejects(Work work, String label) throws Exception { boolean failed = false; try { work.run(); } catch (IOException expected) { failed = true; } check(failed, label); }
}
