package org.xar.ck3.control.application.session;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;

/**
 * Independent new public immutable Driver input fixture, frozen before this source.
 * It does not invoke Journal replay, a writer Session, Root authority, or Native.
 * No candidate or previous Test expectation was used.
 */
public final class JournalReplayPublicEncodeInputManual {
    private JournalReplayPublicEncodeInputManual() { }
    private static final String INPUT = "{\"campaign_goal\":{\"goal\":\"independent_public_data\",\"id\":2147483647},\"episode_run_id\":\"independent-public-fixture-20261104\",\"managed_restore_transaction\":null,\"episode_character_id\":-2147483648,\"format_version\":2,\"command_history\":[{\"index\":1,\"command\":\"fixture_read_one\",\"opaque\":{\"minus_zero\":-0.0,\"large_decimal\":1.2300e+4000}},{\"index\":2,\"command\":\"fixture_read_two\",\"floating\":[9.00,-0e+0,1E-4000]}],\"succession_expectation\":{\"expected\":false,\"number\":9.00},\"pipe_name\":\"fixture-independent-read\",\"rollback_war_failure\":{\"failures\":[-0.0,1e4000,1.2300E+004]},\"last_checkpoint\":null,\"bridge_pid\":41743}";
    private static final String EXPECTED = "{\"format_version\":2,\"pipe_name\":\"fixture-independent-read\",\"bridge_pid\":41743,\"episode_character_id\":-2147483648,\"episode_run_id\":\"independent-public-fixture-20261104\",\"command_history\":[{\"index\":1,\"command\":\"fixture_read_one\",\"opaque\":{\"minus_zero\":-0.0,\"large_decimal\":1.2300e+4000}},{\"index\":2,\"command\":\"fixture_read_two\",\"floating\":[9.00,-0e+0,1E-4000]}],\"last_checkpoint\":null,\"rollback_war_failure\":{\"failures\":[-0.0,1e4000,1.2300E+004]},\"managed_restore_transaction\":null,\"succession_expectation\":{\"expected\":false,\"number\":9.00},\"campaign_goal\":{\"goal\":\"independent_public_data\",\"id\":2147483647}}";
    private static final String ROW_ONE = "{\"index\":1,\"command\":\"fixture_read_one\",\"opaque\":{\"minus_zero\":-0.0,\"large_decimal\":1.2300e+4000}}";

    public static void main(String[] args) {
        byte[] callerInput = INPUT.getBytes(StandardCharsets.UTF_8);
        DriverStateSnapshot.Complete parsed = DriverStateSnapshot.decodeComplete(callerInput);
        var suppliedHistory = new ArrayList<>(parsed.commandHistory());
        DriverStateSnapshot.Complete complete = new DriverStateSnapshot.Complete(
            parsed.session(), suppliedHistory, parsed.lastCheckpoint(), parsed.rollbackWarFailure(),
            parsed.managedRestoreTransaction(), parsed.successionExpectation(), parsed.successionLifecycle(),
            parsed.campaignGoal(), parsed.rollbackWarFailures());
        callerInput[0] = '!';
        suppliedHistory.clear();
        check(complete.commandHistory().size() == 2, "public constructor retained detached ordered history");
        check(complete.session().actorId().intValueExact() == Integer.MIN_VALUE, "exact signed native actor");
        check(complete.successionLifecycle() instanceof DriverStateSnapshot.Missing, "lifecycle remains absent");
        check(complete.rollbackWarFailures() instanceof DriverStateSnapshot.Missing, "failures slot remains absent");
        check(complete.lastCheckpoint() instanceof DriverStateSnapshot.NullValue, "checkpoint remains explicit null");
        check(complete.managedRestoreTransaction() instanceof DriverStateSnapshot.NullValue, "restore remains explicit null");

        byte[] expected = EXPECTED.getBytes(StandardCharsets.UTF_8);
        byte[] first = complete.encode();
        check(Arrays.equals(first, expected), "complete exact public encoding including original decimal tokens");
        byte[] second = complete.encode();
        check(first != second, "separate public encode arrays");
        check(Arrays.equals(second, expected), "repeat encode exact");
        first[0] = '!';
        byte[] rowCopy = complete.commandHistory().get(0).originalRow().json();
        rowCopy[0] = '!';
        check(Arrays.equals(complete.commandHistory().get(0).originalRow().json(),
            ROW_ONE.getBytes(StandardCharsets.UTF_8)), "Value accessor returns detached immutable original row");
        check(Arrays.equals(complete.encode(), expected), "caller array mutations cannot alter public DATA");
        System.out.println("JournalReplayPublicEncodeInputManual: public DATA passed");
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }
}
