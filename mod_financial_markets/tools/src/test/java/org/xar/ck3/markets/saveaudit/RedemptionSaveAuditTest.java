package org.xar.ck3.markets.saveaudit;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.function.UnaryOperator;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.*;
import org.xar.ck3.save.SaveJson;
import org.xar.ck3.save.FilePins;

/** Authored plain/ZIP fixtures exercise the real two-pass shared reader, never CK3 layout qualification. */
final class RedemptionSaveAuditTest {
    @TempDir Path directory;
    private static final String MACHINE = "synthetic-redemption-save-audit";
    private static final FinancialProjector.LayoutHypothesis LAYOUT = new FinancialProjector.LayoutHypothesis("synthetic", "999", BigInteger.valueOf(100000), "story", "char");
    private int counter;

    @Test void twoPassReaderRecognizesPermanentWindowsReceiptsAndCountsOnlyPhysicalAccounts() throws Exception {
        Path file = write(scene()); FinancialSaveReader.Readback read = FinancialSaveReader.read(file, MACHINE, LAYOUT);
        FinancialSnapshot snapshot = FinancialProjector.project(read, LAYOUT); FinancialAudit.Report report = FinancialAudit.audit(snapshot);
        assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, report.assessment(), () -> report.issues().toString());
        assertEquals(12, read.coverage().selectedFinancialRecords()); assertEquals(2, read.coverage().passes());
        assertEquals(2, snapshot.stories().stream().filter(s -> s.type() == Type.REDEMPTION_WINDOW).count());
        assertEquals(2, snapshot.stories().stream().filter(s -> s.type() == Type.REDEMPTION_RECEIPT).count());
        assertEquals("13000", report.ledgerCashStockCents().cents());
        assertFalse(report.financialCertified()); assertFalse(read.sourceLayoutQualified());
        Story window = snapshot.stories().stream().filter(s -> s.type() == Type.REDEMPTION_WINDOW && s.nativeId().value().equals("13")).findFirst().orElseThrow();
        assertEquals("2", window.permanentId().orElseThrow().value()); assertEquals(BigInteger.valueOf(300), window.number(NumberField.REMAINING_CENTS).orElseThrow());
    }

    @Test void historicalClosedWindowMayReuseEscrowWhileCurrentPhysicalBudgetMustReconcile() throws Exception {
        assertHold(scene());
        assertViolation(mutate(scene(), escrow(), s -> s.replace(number("free_cents", 300), number("free_cents", 301))), "remaining_cents");
        assertViolation(mutate(scene(), escrow(), s -> s.replace(number("reserved_cents", 0), number("reserved_cents", 1))), "reserved_cents");
        assertViolation(mutate(scene(), firstWindow(), s -> s.replace(number("remaining_cents", 0), number("remaining_cents", 1))), "remaining_cents");
        assertViolation(mutate(scene(), secondWindow(), s -> s.replace(number("initial_cents", 500), number("initial_cents", 501))), "initial_cents");
        assertViolation(mutate(scene(), escrow(), s -> s.replace(number("redemption_only", 1), number("redemption_only", 0))), "redemption_only");
        assertViolation(mutate(scene(), escrow(), s -> s.replace(reference("legal_entity", "story", 4), reference("legal_entity", "story", 1))), "legal_entity");
        assertViolation(mutate(scene(), coin(), s -> s.replace(reference("issuer_account", "story", 10), reference("issuer_account", "story", 11))), "issuer_account");
        assertViolation(mutate(scene(), coin(), s -> s.replace(reference("redemption_account", "story", 11), reference("market_maker_account", "story", 11) + reference("redemption_account", "story", 11))), "redemption_account");
        assertViolation(mutate(scene(), coin(), s -> s.replace(reference("redemption_account", "story", 11), reference("redemption_account", "story", 10))), "redemption_only");
        assertViolation(mutate(scene(), coin(), s -> s.replace(number("redemption_next_publish_day", 34), number("redemption_next_publish_day", 33))), "redemption_next_publish_day");
        assertViolation(mutate(scene(), secondWindow(), s -> s.replace(number("created_day", 17), number("created_day", 16))), "expiry_day");
    }

    @Test void receiptIdsReferencesTermsUnitsAndPaidPartyCannotBeSubstituted() throws Exception {
        for (String field : List.of("coin_id", "window_id", "payer_account_id", "payee_account_id")) {
            String old = switch (field) { case "coin_id", "payee_account_id" -> number(field, 1); case "window_id" -> number(field, 2); default -> number(field, 3); };
            assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(old, number(field, 99))), field);
        }
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(reference("payer_account", "story", 11), reference("payer_account", "story", 10))), "payer_account");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(reference("payee_account", "story", 2), reference("payee_account", "story", 11))), "payer_account");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(number("paid_units", 200), number("paid_units", 201))), "paid_units/paid_cents");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(number("price_cents", 100), number("price_cents", 101))), "price_cents");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(number("status", 1), number("status", 2))), "status");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(reference("holder", "char", 31254), reference("holder", "char", 20000))), "holder");
    }

    @Test void exactPreviousReceiptChainAndBudgetAfterSequenceRejectDuplicatesAndCycles() throws Exception {
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(number("receipt_id", 2), number("receipt_id", 1))), "permanent_id");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(reference("previous_receipt", "story", 14), reference("previous_receipt", "story", 15))), "previous_receipt");
        assertViolation(mutate(scene(), secondReceipt(), s -> s.replace(number("budget_after_cents", 300), number("budget_after_cents", 299))), "budget_after_cents");
        assertViolation(mutate(scene(), coin(), s -> s.replace(reference("redemption_last_receipt", "story", 15), reference("redemption_last_receipt", "story", 14))), "redemption_last_receipt");
        assertIncomplete(mutate(scene(), secondReceipt(), s -> s.replace(reference("previous_receipt", "story", 14), "")), "previous_receipt");
        assertIncomplete(mutate(scene(), secondReceipt(), s -> s.replace(reference("previous_receipt", "story", 14), reference("previous_receipt", "story", 999))), "previous_receipt");
    }

    @Test void missingMalformedUnknownAndWrongScopeFieldsStayIncompleteRatherThanZero() throws Exception {
        assertIncomplete(mutate(scene(), secondReceipt(), s -> s.replace(number("paid_cents", 200), "")), "xfm_paid_cents");
        assertIncomplete(mutate(scene(), secondWindow(), s -> s.replace(number("remaining_cents", 300), "")), "xfm_remaining_cents");
        assertIncomplete(mutate(scene(), secondReceipt(), s -> s.replace(number("paid_units", 200), "{flag=xfm_paid_units data={type=value identity=true}} ")), "xfm_paid_units");
        assertIncomplete(mutate(scene(), secondReceipt(), s -> s.replace(number("paid_cents", 200), "{flag=xfm_paid_cents data={type=value identity=1}} ")), "xfm_paid_cents");
        assertIncomplete(mutate(scene(), firstWindow(), s -> s.replace(reference("publisher", "char", 20000), reference("publisher", "story", 20000))), "xfm_publisher");
        assertIncomplete(scene().replace("xfm_finance_redemption_receipt", "xfm_finance_redemption_unknown"), "story_cycle");
        assertIncomplete(mutate(scene(), exchange(), s -> s.replace(number("next_redemption_receipt_id", 2), "")), "xfm_next_redemption_receipt_id");
        assertViolation(mutate(scene(), exchange(), s -> s.replace(number("next_redemption_window_id", 2), number("next_redemption_window_id", 1))), "permanent_id");
        FinancialSnapshot absentCash = snapshot(mutate(scene(), escrow(), s -> s.replace(number("free_cents", 300), "")));
        assertFalse(FinancialAudit.audit(absentCash).ledgerCashStockCents().known());
        assertTrue(absentCash.stories().stream().filter(s -> s.nativeId().value().equals("11")).findFirst().orElseThrow().number(NumberField.FREE_CENTS).isEmpty());
        FinancialAudit.Report unknown = FinancialAudit.audit(snapshot(scene().replace("xfm_finance_redemption_receipt", "xfm_finance_redemption_unknown")));
        assertFalse(unknown.issues().stream().anyMatch(i -> i.severity() == Severity.VIOLATION && i.detail().contains("receipt sum")), "Unknown receipt census cannot be silently summed as empty/zero.");
    }

    @Test void samePausedColdPlainZipAndJsonRoundTripsPreserveEveryRedemptionTerm() throws Exception {
        Path plain = write(scene());
        FinancialSnapshot before = FinancialProjector.project(FinancialSaveReader.read(plain, MACHINE, LAYOUT), LAYOUT); Path zip = directory.resolve("cold.ck3");
        try (ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(zip))) { out.putNextEntry(new ZipEntry("gamestate")); out.write(scene().getBytes(StandardCharsets.UTF_8)); out.closeEntry(); }
        FinancialSnapshot after = FinancialProjector.project(FinancialSaveReader.read(zip, MACHINE, LAYOUT), LAYOUT);
        assertTrue(FinancialAudit.compareCold(before, after).exactSelectedFinancialState());
        FinancialSaveAuditMain.Output output = FinancialSaveAuditMain.inspect(new FinancialSaveAuditMain.Inputs(MACHINE, FilePins.pin(plain), List.of(FilePins.pin(zip)), LAYOUT, List.of()));
        FinancialSaveAuditMain.Output json = SaveJson.read(SaveJson.write(output), FinancialSaveAuditMain.Output.class);
        assertEquals(output, json); assertTrue(json.coldComparison().getFirst().exactSelectedFinancialState());
        assertTrue(json.first().stories().stream().filter(s -> s.type().equals("xfm_finance_redemption_receipt")).allMatch(s -> s.exactIntegers().get("xfm_receipt_id").matches("[1-9][0-9]*")));
        assertFalse(FinancialAudit.compareCold(before, after).financialCertified());
        for (String field : List.of("price_cents", "initial_cents", "created_day", "expiry_day")) {
            String original = switch (field) { case "price_cents" -> number(field, 100); case "initial_cents" -> number(field, 500); case "created_day" -> number(field, 17); default -> number(field, 27); };
            FinancialSnapshot changed = snapshot(mutate(scene(), secondWindow(), s -> s.replace(original, number(field, 21))));
            assertFalse(FinancialAudit.compareCold(before, changed).exactSelectedFinancialState(), field);
        }
        FinancialSnapshot publisherChanged = snapshot(mutate(scene(), firstWindow(), s -> s.replace(reference("publisher", "char", 20000), reference("publisher", "char", 20001))));
        assertFalse(FinancialAudit.compareCold(before, publisherChanged).exactSelectedFinancialState());
    }

    @Test void historicalPaymentActorsDoNotBecomeCurrentInheritedAccountHolders() throws Exception {
        String changed = scene().replace(reference("controller", "char", 20000) + reference("redemption_account", "story", 11), reference("controller", "char", 20001) + reference("redemption_account", "story", 11));
        changed = changed.replace(reference("holder", "char", 31254) + reference("beneficial_owner", "char", 31254), reference("holder", "char", 31255) + reference("beneficial_owner", "char", 31255));
        assertHold(changed);
        FinancialSnapshot snapshot = snapshot(changed);
        Story receipt = snapshot.stories().stream().filter(s -> s.type() == Type.REDEMPTION_RECEIPT).findFirst().orElseThrow();
        assertEquals("31254", receipt.reference(ReferenceField.HOLDER).orElseThrow().nativeId().value());
        assertEquals("20000", receipt.reference(ReferenceField.CONTROLLER).orElseThrow().nativeId().value());
    }

    private void assertHold(String text) throws Exception { FinancialAudit.Report report = FinancialAudit.audit(snapshot(text)); assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, report.assessment(), () -> report.issues().toString()); assertFalse(report.financialCertified()); }
    private void assertViolation(String text, String field) throws Exception { FinancialAudit.Report report = FinancialAudit.audit(snapshot(text)); assertEquals(FinancialAudit.Assessment.VIOLATION, report.assessment(), () -> report.issues().toString()); assertTrue(report.issues().stream().anyMatch(i -> i.severity() == Severity.VIOLATION && diagnosticField(i.field()).equals(diagnosticField(field))), () -> field + " " + report.issues()); }
    private void assertIncomplete(String text, String field) throws Exception { FinancialAudit.Report report = FinancialAudit.audit(snapshot(text)); assertTrue(report.issues().stream().anyMatch(i -> i.severity() == Severity.INCOMPLETE && diagnosticField(i.field()).equals(diagnosticField(field))), () -> field + " " + report.issues()); assertFalse(report.financialCertified()); }
    private static String diagnosticField(String field) { return field.startsWith("xfm_") ? field.substring(4) : field; }
    private FinancialSnapshot snapshot(String text) throws Exception { return FinancialProjector.project(FinancialSaveReader.read(write(text), MACHINE, LAYOUT), LAYOUT); }
    private Path write(String text) throws Exception { Path file = directory.resolve("snapshot-" + ++counter + ".txt"); Files.writeString(file, text); return file; }
    private static String mutate(String source, String original, UnaryOperator<String> action) { assertTrue(source.contains(original)); return source.replace(original, action.apply(original)); }
    private static String number(String name, long n) { return "{flag=xfm_" + name + " data={type=value identity=" + BigInteger.valueOf(n).multiply(BigInteger.valueOf(100000)) + "}} "; }
    private static String reference(String name, String type, long n) { return "{flag=xfm_" + name + " data={type=" + type + " identity=" + n + "}} "; }
    private static String story(long id, String type, String variables) { return id + "={story_cycle=" + type + " owner=31254 variables={data={" + variables + "}}} "; }
    private static String exchange() { return story(1, "xfm_finance_exchange", number("day", 18) + number("fee_cents", 0) + number("next_account_id", 3) + number("next_reservation_id", 1) + number("next_coin_id", 1) + number("next_redemption_window_id", 2) + number("next_redemption_receipt_id", 2)); }
    private static String coin() { return story(4, "xfm_finance_coin", number("coin_id", 1) + number("supply_units", 1000) + number("maximum_supply_units", 1000) + reference("issuer_account", "story", 10) + reference("controller", "char", 20000) + reference("redemption_account", "story", 11) + reference("redemption_window", "story", 13) + reference("redemption_last_receipt", "story", 15) + number("redemption_lifetime_paid_cents", 400) + number("redemption_lifetime_units", 400) + number("redemption_next_publish_day", 34)); }
    private static String escrow() { return story(11, "xfm_finance_account", number("account_id", 3) + number("free_cents", 300) + number("reserved_cents", 0) + number("system_account", 1) + number("redemption_only", 1) + reference("holder", "char", 20000) + reference("beneficial_owner", "char", 20000) + reference("legal_entity", "story", 4)); }
    private static String firstWindow() { return window(12, 1, 1000, 0, 800, 2, 10, 4); }
    private static String secondWindow() { return window(13, 2, 500, 300, 0, 17, 27, 1); }
    private static String window(long nativeId, long id, long initial, long remaining, long reclaimed, long created, long expiry, long status) {
        return story(nativeId, "xfm_finance_redemption_window", number("window_id", id) + reference("coin", "story", 4) + number("coin_id", 1) + reference("redemption_account", "story", 11) + number("redemption_account_id", 3) + reference("issuer_account", "story", 10) + number("issuer_account_id", 2) + reference("publisher", "char", 20000) + number("price_cents", 100) + number("initial_cents", initial) + number("remaining_cents", remaining) + number("paid_cents", 200) + number("paid_units", 200) + number("reclaimed_cents", reclaimed) + number("created_day", created) + number("expiry_day", expiry) + number("status", status));
    }
    private static String firstReceipt() { return receipt(14, 1, 12, 1, 800, 3, ""); }
    private static String secondReceipt() { return receipt(15, 2, 13, 2, 300, 18, reference("previous_receipt", "story", 14)); }
    private static String receipt(long nativeId, long id, long windowNative, long windowId, long budgetAfter, long day, String previous) {
        return story(nativeId, "xfm_finance_redemption_receipt", number("receipt_id", id) + reference("coin", "story", 4) + number("coin_id", 1) + reference("window", "story", windowNative) + number("window_id", windowId) + reference("payer_account", "story", 11) + reference("payee_account", "story", 2) + number("payer_account_id", 3) + number("payee_account_id", 1) + reference("holder", "char", 31254) + reference("controller", "char", 20000) + number("paid_cents", 200) + number("paid_units", 200) + number("price_cents", 100) + number("budget_after_cents", budgetAfter) + number("day", day) + number("status", 1) + previous);
    }
    private static String scene() {
        String privateAccount = story(2, "xfm_finance_account", number("account_id", 1) + number("free_cents", 10400) + number("reserved_cents", 300) + number("system_account", 0) + reference("holder", "char", 31254) + reference("beneficial_owner", "char", 31254));
        String reservation = story(3, "xfm_finance_reservation", number("reservation_id", 1) + number("remaining_cents", 300) + number("status", 1) + reference("account", "story", 2));
        String holderPosition = story(5, "xfm_finance_position", number("quantity_units", 600) + number("reserved_units", 0) + reference("account", "story", 2) + reference("coin", "story", 4));
        String escrowPosition = story(16, "xfm_finance_position", number("quantity_units", 400) + number("reserved_units", 0) + reference("account", "story", 11) + reference("coin", "story", 4));
        String issuer = story(10, "xfm_finance_account", number("account_id", 2) + number("free_cents", 2000) + number("reserved_cents", 0) + number("system_account", 1) + reference("holder", "char", 20000) + reference("beneficial_owner", "char", 20000) + reference("legal_entity", "story", 4));
        return "CK3txt meta_data={save_game_version=999 version=\"synthetic\" meta_date=1066.9.16} date=1066.9.16 variables={data={" + reference("exchange", "story", 1) + "}} stories={active={" + exchange() + privateAccount + reservation + coin() + holderPosition + issuer + escrow() + firstWindow() + secondWindow() + firstReceipt() + secondReceipt() + escrowPosition + "}}";
    }
}
