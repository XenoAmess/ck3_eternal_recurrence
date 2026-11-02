package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.WindowsFileIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;

/** Pure captured DATA compatibility; this issues no lease or filesystem authority. */
final class LedgerIdentityComparison314Test {
    private static final String MODIFIED = "2026-11-02T16:00:00Z";

    private record Captured(WindowsFileIdentity key, String modified, long bytes) { }

    @Test
    void exactAndDifferentFieldsPreserveOriginalRecordEquality() {
        FileIdentity expected = new FileIdentity("1", "2", "3", MODIFIED, 99);
        List<Captured> cases = new ArrayList<>();
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "3"), MODIFIED, 99));
        cases.add(new Captured(new WindowsFileIdentity(new String(new char[] {'1'}),
                new String(new char[] {'2'}), new String(new char[] {'3'})), MODIFIED, 99));
        cases.add(new Captured(new WindowsFileIdentity("4", "2", "3"), MODIFIED, 99));
        cases.add(new Captured(new WindowsFileIdentity("1", "4", "3"), MODIFIED, 99));
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "4"), MODIFIED, 99));
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "3"), "2026-11-02T16:00:01Z", 99));
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "3"), "2026-11-02T16:00:00.000Z", 99));
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "3"), MODIFIED, 98));
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "3"), MODIFIED, 0));
        cases.add(new Captured(new WindowsFileIdentity("1", "2", "3"), MODIFIED, StrictJson.MAX_SAFE_INTEGER));
        for (Captured captured : cases) {
            boolean original = expected.equals(new FileIdentity(captured.key().volumeSerialDecimal(),
                    captured.key().fileIdDecimal(), captured.key().creationFiletimeDecimal(),
                    captured.modified(), captured.bytes()));
            assertEquals(original, LedgerFiles.LeasedDocument.matchesIdentity(expected, captured.key(),
                    captured.modified(), captured.bytes()), captured.toString());
        }
        WindowsFileIdentity wide = new WindowsFileIdentity("18446744073709551615",
                "340282366920938463463374607431768211455", "18446744073709551615");
        FileIdentity wideExpected = new FileIdentity(wide.volumeSerialDecimal(), wide.fileIdDecimal(),
                wide.creationFiletimeDecimal(), MODIFIED, StrictJson.MAX_SAFE_INTEGER);
        assertEquals(true, LedgerFiles.LeasedDocument.matchesIdentity(wideExpected, wide,
                MODIFIED, StrictJson.MAX_SAFE_INTEGER));
    }

    @Test
    void malformedCapturedValuesKeepOriginalExceptionClassMessageAndPrecedence() {
        FileIdentity expected = new FileIdentity("1", "2", "3", MODIFIED, 99);
        WindowsFileIdentity key = new WindowsFileIdentity("1", "2", "3");
        List<Captured> cases = List.of(
                new Captured(key, "not-an-instant", 99),
                new Captured(key, "", 99),
                new Captured(key, null, 99),
                new Captured(key, MODIFIED, -1),
                new Captured(key, MODIFIED, Long.MIN_VALUE),
                new Captured(key, MODIFIED, StrictJson.MAX_SAFE_INTEGER + 1),
                new Captured(key, MODIFIED, Long.MAX_VALUE),
                new Captured(key, "not-an-instant", -1));
        for (Captured captured : cases) {
            RuntimeException original = assertThrows(RuntimeException.class,
                    () -> new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(),
                            key.creationFiletimeDecimal(), captured.modified(), captured.bytes()));
            RuntimeException actual = assertThrows(RuntimeException.class,
                    () -> LedgerFiles.LeasedDocument.matchesIdentity(expected, captured.key(),
                            captured.modified(), captured.bytes()));
            assertEquals(original.getClass(), actual.getClass(), captured.toString());
            assertEquals(original.getMessage(), actual.getMessage(), captured.toString());
        }
    }
}
