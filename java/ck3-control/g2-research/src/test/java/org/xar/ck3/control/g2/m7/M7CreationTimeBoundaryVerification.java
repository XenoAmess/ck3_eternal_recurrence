package org.xar.ck3.control.g2.m7;

import java.util.List;

/** Test-only calls through the shared production parser. No process query or game operation. */
public final class M7CreationTimeBoundaryVerification {
    public record Verification(int negativeCases, int positiveCases, int equalityCases) { }
    private M7CreationTimeBoundaryVerification() { }
    public static void main(String[] args) {
        if (args.length != 0) { throw new IllegalArgumentException("no runtime inputs accepted"); }
        Verification actual = verify();
        System.out.println("{\"schema\":\"xar.g2.m7.creation-time-boundary-test/v1\",\"synthetic\":true,\"negative_cases\":"
                + actual.negativeCases() + ",\"positive_cases\":" + actual.positiveCases()
                + ",\"equality_cases\":" + actual.equalityCases() + ",\"game_calls\":0,\"cold_authority_granted\":false}");
    }
    public static Verification verify() {
        List<String> rejected = List.of("00000101000000.000000+000", "0000-01-01T00:00:00.0000000Z",
                "00010101000000.000000+840", "99991231235959.999999-840", "unknown", "null", "",
                "2026-10-23T04:30:45.1234561Z", "20261023123045.123456+841", "20260230043045.123456+000");
        for (String value : rejected) {
            boolean refused = false;
            try { new CheckpointContinuity.GameIdentity(10, value, "D:\\synthetic\\ck3.exe"); }
            catch (IllegalArgumentException error) { refused = true; }
            if (!refused) { throw new IllegalStateException("original unsupported process birth was admitted: " + value); }
        }
        List<String> accepted = List.of("20261023123045.123456+480", "2026-10-23T04:30:45.1234560Z",
                "00010101000000.000000+000", "99991231235959.999999+000");
        for (String value : accepted) { new CheckpointContinuity.GameIdentity(10, value, "D:\\synthetic\\ck3.exe"); }
        var first = new CheckpointContinuity.GameIdentity(10, accepted.get(0), "D:\\synthetic\\ck3.exe");
        var second = new CheckpointContinuity.GameIdentity(10, accepted.get(1), "d:/synthetic/ck3.exe");
        if (!CheckpointContinuity.sameGameIdentity(first, second)) { throw new IllegalStateException("exact offset-equivalent birth differs"); }
        return new Verification(rejected.size(), accepted.size(), 1);
    }
}
