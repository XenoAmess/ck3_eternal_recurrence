package org.xar.ck3.markets.saveaudit;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.xar.ck3.save.SaveJson;

/** Offline, synthetic selector/invariant regressions. These are never game-layout qualification. */
public final class FinancialSaveAuditSelfTest {
    private FinancialSaveAuditSelfTest() { }
    private static final String MACHINE = "synthetic-financial-audit-fixture";
    private static final FinancialProjector.LayoutHypothesis LAYOUT = new FinancialProjector.LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");
    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory(Path.of(args[0]), "audit-regression-");
        Path plain = directory.resolve("scene.txt"); Files.writeString(plain, scene());
        FinancialSnapshot initial = snapshot(plain);
        check(FinancialAudit.audit(initial).assessment() == FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, "complete synthetic snapshot");
        check(!FinancialAudit.audit(initial).financialCertified(), "synthetic cannot certify funds");
        check(FinancialAudit.audit(initial).ledgerCashStockCents().cents().equals("10300"), "cash is exact account sum plus fee stock");
        Path zip = directory.resolve("scene.ck3");
        try (var output = new ZipOutputStream(Files.newOutputStream(zip))) {
            output.putNextEntry(new ZipEntry("gamestate")); output.write(scene().getBytes(StandardCharsets.UTF_8)); output.closeEntry();
        }
        FinancialSnapshot zipped = snapshot(zip);
        check(FinancialAudit.compareCold(initial, zipped).exactSelectedFinancialState(), "zip/plain equivalent projection and cold identities");
        check(!FinancialAudit.compareCold(initial, zipped).financialCertified(), "equality is not funds certification");
        Path prefixed = directory.resolve("prefixed.ck3");
        Files.writeString(prefixed, "SAV0102syntheticheader\nmeta_data={version=\"synthetic\"}\n");
        Files.write(prefixed, Files.readAllBytes(zip), java.nio.file.StandardOpenOption.APPEND);
        check(FinancialAudit.compareCold(initial, snapshot(prefixed)).exactSelectedFinancialState(), "physical SAV-prefixed ZIP is recognized through its central directory");
        FinancialSnapshot noIdentity = variant(directory, "missing", scene().replace("flag=xfm_free_cents data={type=value identity=1000000000}", "flag=xfm_free_cents data={type=value}"));
        check(FinancialAudit.audit(noIdentity).assessment() == FinancialAudit.Assessment.INCOMPLETE && !FinancialAudit.audit(noIdentity).ledgerCashStockCents().known(), "missing balance identity stays unknown");
        FinancialSnapshot fractional = variant(directory, "fraction", scene().replace("flag=xfm_free_cents data={type=value identity=1000000000}", "flag=xfm_free_cents data={type=value identity=1}"));
        check(FinancialAudit.audit(fractional).assessment() == FinancialAudit.Assessment.INCOMPLETE, "fractional cent rejected without rounding");
        FinancialSnapshot reserveMismatch = variant(directory, "reserve", scene().replace("flag=xfm_remaining_cents data={type=value identity=30000000}", "flag=xfm_remaining_cents data={type=value identity=29900000}"));
        check(FinancialAudit.audit(reserveMismatch).assessment() == FinancialAudit.Assessment.VIOLATION, "reserve sum mismatch detected");
        FinancialSnapshot supplyMismatch = variant(directory, "supply", scene().replace("flag=xfm_quantity_units data={type=value identity=100000000}", "flag=xfm_quantity_units data={type=value identity=99900000}"));
        check(FinancialAudit.audit(supplyMismatch).assessment() == FinancialAudit.Assessment.VIOLATION, "supply mismatch detected");
        FinancialSnapshot changed = variant(directory, "changed", scene().replace("flag=xfm_free_cents data={type=value identity=1000000000}", "flag=xfm_free_cents data={type=value identity=999900000}"));
        check(!FinancialAudit.compareCold(initial, changed).exactSelectedFinancialState(), "same-count changed money does not pass cold reload");
        FinancialSnapshot duplicate = variant(directory, "duplicate", scene().replace("flag=xfm_free_cents data={type=value identity=1000000000}", "flag=xfm_free_cents data={type=value identity=1000000000}} {flag=xfm_free_cents data={type=value identity=1000000000}"));
        check(FinancialAudit.audit(duplicate).assessment() == FinancialAudit.Assessment.VIOLATION, "duplicate financial variable rejected");
        FinancialSnapshot futures = variant(directory, "paired-futures", futuresScene());
        check(FinancialAudit.audit(futures).assessment() == FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, "genuine two account/two margin reference shape");
        FinancialSnapshot reusedMargin = variant(directory, "reused-margin", futuresScene().replace(reference("short_reservation", "story", 8), reference("short_reservation", "story", 9)));
        check(FinancialAudit.audit(reusedMargin).assessment() == FinancialAudit.Assessment.VIOLATION, "paired sides cannot pledge one reservation twice");
        FinancialSnapshot absentPositionId = variant(directory, "absent-position-id", futuresScene().replace(number("position_id", 1), ""));
        check(FinancialAudit.audit(absentPositionId).assessment() == FinancialAudit.Assessment.INCOMPLETE, "stable position ID is required, not a count");
        FinancialSnapshot debt = variant(directory, "debt", debtScene(1, 70));
        check(FinancialAudit.audit(debt).assessment() == FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, "winner unpaid and fund recourse split preserve one obligation");
        FinancialSnapshot wrongSplit = variant(directory, "wrong-debt-split", debtScene(1, 80));
        check(FinancialAudit.audit(wrongSplit).assessment() == FinancialAudit.Assessment.VIOLATION, "winner claim plus fund recourse must equal outstanding");
        FinancialSnapshot insuredFunding = variant(directory, "insured-funding", debtScene(2, 70));
        check(FinancialAudit.audit(insuredFunding).assessment() == FinancialAudit.Assessment.VIOLATION, "funding may not consume fund insurance");
        Path malformed = directory.resolve("malformed.txt"); Files.writeString(malformed, scene() + "broken={");
        boolean rejected = false;
        try { FinancialSaveReader.read(malformed, MACHINE, LAYOUT); } catch (IOException expected) { rejected = true; }
        check(rejected, "unselected malformed tail is rejected by shared full-stream parser");
        Path report = directory.resolve("report.json");
        FinancialSaveAuditMain.main(new String[]{plain.toString(), report.toString(), MACHINE, "synthetic", "999", "100000", "story", "char", "--unqualified-candidate", zip.toString()});
        var json = SaveJson.read(Files.readAllBytes(report), com.fasterxml.jackson.databind.JsonNode.class);
        check(!json.get("financialCertified").asBoolean(), "CLI hard-false certification");
        check(json.get("first").get("stories").get(1).get("exactIntegers").get("xfm_account_id").isTextual(), "JSON identities remain decimal strings");
        System.out.println("SYNTHETIC_SELF_TEST assertions=21 status=PASS directory=" + directory);
    }
    private static FinancialSnapshot snapshot(Path path) throws IOException { return FinancialProjector.project(FinancialSaveReader.read(path, MACHINE, LAYOUT), LAYOUT); }
    private static FinancialSnapshot variant(Path directory, String name, String text) throws IOException { Path path = directory.resolve(name + ".txt"); Files.writeString(path, text); return snapshot(path); }
    private static void check(boolean condition, String label) { if (!condition) throw new AssertionError(label); }
    private static String number(String name, long value) { return "{flag=xfm_" + name + " data={type=value identity=" + BigInteger.valueOf(value).multiply(BigInteger.valueOf(100000)) + "}} "; }
    private static String reference(String name, String type, long value) { return "{flag=xfm_" + name + " data={type=" + type + " identity=" + value + "}} "; }
    private static String story(int nativeId, String type, String variables) { return nativeId + "={story_cycle=" + type + " owner=31254 variables={data={" + variables + "}}} "; }
    static String scene() {
        String exchange = number("day", 2) + number("fee_cents", 0) + number("next_account_id", 1) + number("next_reservation_id", 1) + number("next_coin_id", 1);
        String account = number("account_id", 1) + number("free_cents", 10000) + number("reserved_cents", 300) + reference("holder", "char", 31254);
        String reservation = number("reservation_id", 1) + number("remaining_cents", 300) + number("status", 1) + reference("account", "story", 2);
        String coin = number("coin_id", 1) + number("supply_units", 1000) + number("maximum_supply_units", 1000);
        String position = number("quantity_units", 1000) + number("reserved_units", 0) + reference("account", "story", 2) + reference("coin", "story", 4);
        return "CK3txt meta_data={save_game_version=999 version=\"synthetic\" meta_date=1066.9.16} date=1066.9.16 variables={data={"
                + reference("exchange", "story", 1) + "}} stories={active={" + story(1, "xfm_finance_exchange", exchange)
                + story(2, "xfm_finance_account", account) + story(3, "xfm_finance_reservation", reservation)
                + story(4, "xfm_finance_coin", coin) + story(5, "xfm_finance_position", position) + "}}";
    }
    private static String appendStories(String source, String extra) { return source.substring(0, source.length() - 2) + extra + "}}"; }
    private static String futuresScene() {
        String contract = number("contract_id", 1) + number("created_day", 2) + number("perpetual", 0) + number("expiry_day", 32) + number("status", 0) + reference("coin", "story", 4);
        String account = number("account_id", 2) + number("free_cents", 5000) + number("reserved_cents", 200) + reference("holder", "char", 30000);
        String shortReservation = number("reservation_id", 2) + number("remaining_cents", 200) + number("status", 1) + reference("account", "story", 7);
        String longReservation = number("reservation_id", 3) + number("remaining_cents", 100) + number("status", 1) + reference("account", "story", 2);
        String position = number("position_id", 1) + number("contract_id", 1) + number("created_day", 2) + number("lots", 1) + number("mark_cents", 1000) + number("status", 0)
                + number("last_settled_day", 2) + number("long_leverage", 10) + number("short_leverage", 5) + reference("coin", "story", 4) + reference("contract", "story", 6)
                + reference("long_account", "story", 2) + reference("short_account", "story", 7) + reference("long_reservation", "story", 9) + reference("short_reservation", "story", 8);
        String base = scene().replace(number("next_account_id", 1), number("next_account_id", 2) + number("next_futures_contract_id", 1) + number("next_futures_position_id", 1))
                .replace(number("next_reservation_id", 1), number("next_reservation_id", 3)).replace(number("reserved_cents", 300), number("reserved_cents", 400));
        return appendStories(base, story(6, "xfm_futures_contract", contract) + story(7, "xfm_finance_account", account) + story(8, "xfm_finance_reservation", shortReservation)
                + story(9, "xfm_finance_reservation", longReservation) + story(10, "xfm_futures_position", position));
    }
    private static String debtScene(int kind, int winnerUnpaid) {
        String debt = number("debt_id", 1) + number("source_day", 1) + number("source_kind", kind) + number("original_cents", 100) + number("outstanding_cents", 100)
                + number("winner_unpaid_cents", winnerUnpaid) + number("fund_paid_cents", 30) + number("fund_recourse_cents", 30) + number("repaid_cents", 0) + number("written_off_cents", 0) + number("state", 1)
                + reference("source", "story", 10) + reference("debtor_account", "story", 7) + reference("creditor_account", "story", 2) + reference("fund_account", "story", 12);
        String fund = number("account_id", 3) + number("free_cents", 0) + number("reserved_cents", 0) + reference("holder", "char", 31254);
        String base = futuresScene().replace(number("next_account_id", 2), number("next_account_id", 3) + number("debt_counter", 1));
        return appendStories(base, story(11, "xfm_debt_claim", debt) + story(12, "xfm_finance_account", fund));
    }
}
