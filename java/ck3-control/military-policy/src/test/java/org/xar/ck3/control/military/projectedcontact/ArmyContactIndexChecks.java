package org.xar.ck3.control.military.projectedcontact;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Capture;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.CapturedRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryKey;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRequired;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Request;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Scope;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Selection;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Side;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Snapshot;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Transition;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.UnusableRow;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.HistoryIdentity;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Invalidation;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Lookup;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.SourceIdentity;

/** Offline regression main. Baseline comparisons invoke the existing compiled production selector. */
public final class ArmyContactIndexChecks {
    private static int assertions;
    private static int comparisons;
    private static long baselineVisits;
    private static long indexedVisits;
    private static final BigInteger NATIVE = new BigInteger("9007199254740997");
    private static final SourceIdentity SOURCE = new SourceIdentity("fixture-machine", "fixture-build",
            "1".repeat(64), "2".repeat(64), "3".repeat(64));
    private static final HistoryIdentity HISTORY = new HistoryIdentity("restored-branch-A",
            BigInteger.valueOf(11), new BigInteger("9007199254741011"));
    private ArmyContactIndexChecks() { }

    public static void main(String[] arguments) {
        require(arguments.length == 0, "no filesystem or runtime arguments accepted");
        Current current = context(snapshot("public:frame", BigInteger.valueOf(41), NATIVE,
                BigInteger.valueOf(9), "episode-A", 24000));
        differential(current);
        newestBindingAndIdentity(current);
        exactContextInvalidation(current);
        transitionAndImmutability(current);
        invalidContracts(current);
        measuredRowVisits(current);
        System.out.println("{\"schema\":\"xar.army-contact-index-checks/v1\",\"status\":\"PASS\","
                + "\"assertions\":" + assertions + ",\"differential_comparisons\":" + comparisons
                + ",\"baseline_history_row_visits\":" + baselineVisits
                + ",\"index_build_plus_lookup_row_visits\":" + indexedVisits
                + ",\"native_calls\":0,\"game_days\":0,\"deployed\":false,\"full_vanilla_ai_equivalence\":false}");
    }

    private static void differential(Current current) {
        Random random = new Random(20261023L);
        List<QueryRow> rows = new ArrayList<>();
        Snapshot stale = snapshot("old", BigInteger.valueOf(40), NATIVE.subtract(BigInteger.ONE),
                BigInteger.valueOf(9), "episode-A", 24000);
        for (int index = 0; index < 2048; index++) {
            if (index % 5 == 0) { rows.add(new UnusableRow()); continue; }
            QueryKey key = new QueryKey(random.nextInt(24), 2585 + random.nextInt(16), 2500 + random.nextInt(4));
            Snapshot frame = index % 7 == 0 ? stale : current.snapshot();
            rows.add(new CapturedRow(key, frame.capture(), scope(frame, key,
                    20 + random.nextInt(3), 7 + random.nextInt(3), Transition.NONE, Side.NONE)));
        }
        SourceBoundContactIndex index = SourceBoundContactIndex.build(current, rows);
        List<Request> requests = new ArrayList<>();
        for (int n = 0; n < 2400; n++) {
            Request request = new Request(new QueryKey(random.nextInt(26), 2585 + random.nextInt(18),
                    2500 + random.nextInt(5)), 20 + random.nextInt(3), n % 3 == 0 ? null : 7 + random.nextInt(3));
            requests.add(request); compare(current, rows, index, request);
        }
        List<Lookup> all = index.selectAll(current, requests);
        require(all.size() == requests.size(), "candidate occurrence count changed");
        for (int n = 0; n < all.size(); n++) {
            require(all.get(n).selection().key().equals(requests.get(n).key()), "candidate identity/order changed");
        }
        expectFailure(() -> all.add(all.getFirst()), "exported selection list mutable");
    }

    private static void newestBindingAndIdentity(Current current) {
        QueryKey key = new QueryKey(0, 2585, 2500);
        Request request = new Request(key, 20, 7);
        Scope correct = scope(current.snapshot(), key, 20, 7, Transition.CREATE_NEW, Side.ATTACKER);
        Scope badOwner = scope(current.snapshot(), key, 20, 8, Transition.NONE, Side.NONE);
        Scope badCurrent = scope(current.snapshot(), key, 21, 7, Transition.NONE, Side.NONE);
        Scope badNativeRevision = scope(new Snapshot(new Capture("scope-only-old", BigInteger.valueOf(41),
                current.snapshot().capture().revision(), BigInteger.valueOf(9), "episode-A"), 24000),
                key, 20, 7, Transition.NONE, Side.NONE);
        Scope badSubject = scope(current.snapshot(), new QueryKey(11, 2585, 2500), 20, 7,
                Transition.NONE, Side.NONE);
        List<QueryRow> rows = new ArrayList<>(List.of(new CapturedRow(key, current.snapshot().capture(), correct),
                new CapturedRow(key, current.snapshot().capture(), badOwner),
                new CapturedRow(key, current.snapshot().capture(), badCurrent),
                new CapturedRow(key, current.snapshot().capture(), badNativeRevision),
                new CapturedRow(key, current.snapshot().capture(), badSubject)));
        SourceBoundContactIndex index = SourceBoundContactIndex.build(current, rows);
        Lookup result = index.select(current, request);
        require(result.inspectedRows() == 5, "newer incompatible binding incorrectly shadowed old valid row");
        require(result.selection() instanceof Available available && available.projection().equals(correct), "wrong valid row");
        Available available = (Available) result.selection();
        require(available.projection().subjectArmyId() == 0 && available.projection().subjectNativeCarmyId() == 201,
                "public zero and native Army identity mixed");
        require(available.projection().snapshotRevision().equals(NATIVE), "uint64 precision lost");
        require(!current.snapshot().capture().revision().equals(NATIVE), "fixture failed to split public/native revisions");
        rows.clear();
        require(index.select(current, request).equals(result), "input mutation changed built index");
        require(!result.authorizesCommandReplay() && !result.actualArrivalObserved(), "query result acquired action credit");
        SourceBoundContactIndex onlyBad = SourceBoundContactIndex.build(current,
                List.of(new CapturedRow(key, current.snapshot().capture(), badNativeRevision)));
        require(onlyBad.select(current, request).selection() instanceof QueryRequired,
                "public wrapper revision substituted for native scope binding");
    }

    private static void exactContextInvalidation(Current current) {
        QueryKey key = new QueryKey(0, 2585, 2500); Request request = new Request(key, 20, 7);
        SourceBoundContactIndex index = SourceBoundContactIndex.build(current,
                List.of(new CapturedRow(key, current.snapshot().capture(), scope(current.snapshot(), key, 20, 7,
                        Transition.NONE, Side.NONE))));
        for (Invalidation invalidation : Invalidation.values()) {
            if (invalidation != Invalidation.NONE) {
                Lookup result = index.select(new Current(current.source(), current.snapshot(), current.history(), invalidation), request);
                require(result.selection() instanceof QueryRequired && result.inspectedRows() == 0,
                        "ACK/unknown/restore/advance reused old read: " + invalidation);
            }
        }
        Capture c = current.snapshot().capture();
        List<Snapshot> changed = List.of(
                snapshot("other", c.revision(), c.nativeRevision(), c.connectionGeneration(), c.episodeRunId(), 24000),
                snapshot(c.snapshotId(), c.revision().add(BigInteger.ONE), c.nativeRevision(), c.connectionGeneration(), c.episodeRunId(), 24000),
                snapshot(c.snapshotId(), c.revision(), c.nativeRevision().add(BigInteger.ONE), c.connectionGeneration(), c.episodeRunId(), 24000),
                snapshot(c.snapshotId(), c.revision(), c.nativeRevision(), c.connectionGeneration().add(BigInteger.ONE), c.episodeRunId(), 24000),
                snapshot(c.snapshotId(), c.revision(), c.nativeRevision(), c.connectionGeneration(), "episode-B", 24000),
                new Snapshot(c, 24024));
        for (Snapshot frame : changed) {
            require(index.select(context(frame), request).selection() instanceof QueryRequired, "frame component drift accepted");
        }
        List<SourceIdentity> sources = List.of(
                new SourceIdentity("other-machine", SOURCE.buildVersion(), "1".repeat(64), "2".repeat(64), "3".repeat(64)),
                new SourceIdentity(SOURCE.machineId(), "other-build", "1".repeat(64), "2".repeat(64), "3".repeat(64)),
                new SourceIdentity(SOURCE.machineId(), SOURCE.buildVersion(), "4".repeat(64), "2".repeat(64), "3".repeat(64)),
                new SourceIdentity(SOURCE.machineId(), SOURCE.buildVersion(), "1".repeat(64), "4".repeat(64), "3".repeat(64)),
                new SourceIdentity(SOURCE.machineId(), SOURCE.buildVersion(), "1".repeat(64), "2".repeat(64), "4".repeat(64)));
        for (SourceIdentity source : sources) {
            require(index.select(new Current(source, current.snapshot(), HISTORY, Invalidation.NONE), request)
                    .selection() instanceof QueryRequired, "source drift accepted");
        }
        for (HistoryIdentity history : List.of(
                new HistoryIdentity("other-branch", HISTORY.latestCompletedAdvanceIndex(), HISTORY.observedHistoryTailIndex()),
                new HistoryIdentity(HISTORY.restoredBranchIdentity(), BigInteger.valueOf(12), HISTORY.observedHistoryTailIndex()),
                new HistoryIdentity(HISTORY.restoredBranchIdentity(), HISTORY.latestCompletedAdvanceIndex(), HISTORY.observedHistoryTailIndex().add(BigInteger.ONE)))) {
            require(index.select(new Current(SOURCE, current.snapshot(), history, Invalidation.NONE), request)
                    .selection() instanceof QueryRequired, "effective history drift accepted");
        }
        Lookup unknown = index.select(new SourceBoundContactIndex.Unknown("current source unavailable"), request);
        require(unknown.selection() instanceof QueryRequired && unknown.inspectedRows() == 0, "unknown became empty/current");
    }

    private static void transitionAndImmutability(Current current) {
        QueryKey key = new QueryKey(0, 2585, 2500); Request request = new Request(key, 20, 7);
        for (Transition transition : Transition.values()) {
            for (Side side : transition == Transition.NONE ? List.of(Side.NONE) : List.of(Side.ATTACKER, Side.DEFENDER)) {
                Scope scope = scope(current.snapshot(), key, 20, 7, transition, side);
                List<QueryRow> rows = List.of(new CapturedRow(key, current.snapshot().capture(), scope));
                SourceBoundContactIndex index = SourceBoundContactIndex.build(current, rows);
                compare(current, rows, index, request);
                Available available = (Available) index.select(current, request).selection();
                require(available.projection().equals(scope), "native transition/selected combat/side order changed");
                require(!available.actualArrivalObserved() && !available.futureContactAuthorized(), "hypothetical result became future credit");
                if (!scope.defenderArmyIds().isEmpty()) {
                    expectFailure(() -> scope.defenderArmyIds().add(42), "native side array mutable");
                }
            }
        }
    }

    private static void invalidContracts(Current current) {
        expectFailure(() -> new SourceIdentity("m", "build", "unknown", "2".repeat(64), "3".repeat(64)), "bad source SHA accepted");
        expectFailure(() -> new SourceIdentity("", "build", "1".repeat(64), "2".repeat(64), "3".repeat(64)), "missing machine accepted");
        expectFailure(() -> new SourceIdentity("unknown", "build", "1".repeat(64), "2".repeat(64), "3".repeat(64)), "unknown source accepted as current");
        expectFailure(() -> new HistoryIdentity("branch", BigInteger.TEN, BigInteger.ONE), "reversed indices accepted");
        expectFailure(() -> SourceBoundContactIndex.build(new Current(SOURCE, current.snapshot(), HISTORY,
                Invalidation.UNKNOWN_COMMAND_RESULT), List.of()), "built unknown command cache");
        expectFailure(() -> new SourceBoundContactIndex.Lookup(new QueryRequired(new QueryKey(0, 2585, 2500)),
                SourceBoundContactIndex.Outcome.AVAILABLE, 0), "contradictory outcome accepted");
    }

    private static void measuredRowVisits(Current current) {
        List<QueryRow> rows = new ArrayList<>();
        List<Request> requests = new ArrayList<>();
        for (int n = 0; n < 128; n++) {
            QueryKey key = new QueryKey(n, 2585, 2500); requests.add(new Request(key, 20, 7));
            rows.add(new CapturedRow(key, current.snapshot().capture(), scope(current.snapshot(), key, 20, 7,
                    Transition.NONE, Side.NONE)));
        }
        for (int n = 0; n < 1920; n++) { rows.add(new UnusableRow()); }
        SourceBoundContactIndex index = SourceBoundContactIndex.build(current, rows);
        indexedVisits = index.sourceRowsVisited();
        for (Request request : requests) {
            Lookup result = index.select(current, request); indexedVisits += result.inspectedRows();
            baselineVisits += baselineInspections(current.snapshot(), rows, request);
            compare(current, rows, index, request);
        }
        require(baselineVisits == 254016 && indexedVisits == 2176, "complete construction/lookup cost accounting changed");
        require(indexedVisits < baselineVisits, "index did not reduce generated workload row visits");
    }

    private static int baselineInspections(Snapshot snapshot, List<QueryRow> rows, Request request) {
        int visits = 0;
        for (int n = rows.size() - 1; n >= 0; n--) {
            visits++;
            if (rows.get(n) instanceof CapturedRow row && row.key().equals(request.key())
                    && row.capture().equals(snapshot.capture()) && row.scope().matches(snapshot, request)) { return visits; }
        }
        return visits;
    }
    private static void compare(Current current, List<QueryRow> rows, SourceBoundContactIndex index, Request request) {
        Selection expected = ProjectedContactPolicy.select(current.snapshot(), rows, request);
        require(expected.equals(index.select(current, request).selection()), "compiled original selector differential mismatch");
        comparisons++;
    }
    private static Current context(Snapshot snapshot) { return new Current(SOURCE, snapshot, HISTORY, Invalidation.NONE); }
    private static Snapshot snapshot(String id, BigInteger publicRevision, BigInteger nativeRevision,
                                     BigInteger connection, String episode, int dateRaw) {
        return new Snapshot(new Capture(id, publicRevision, nativeRevision, connection, episode), dateRaw);
    }
    private static Scope scope(Snapshot frame, QueryKey key, int current, int owner, Transition transition, Side side) {
        List<Integer> attackers = List.of(); List<Integer> defenders = List.of();
        Integer combat = null; Integer combatIndex = null; boolean observable = false; Boolean isDefender = null;
        if (transition == Transition.CREATE_NEW) {
            observable = true; isDefender = side == Side.DEFENDER;
            attackers = side == Side.ATTACKER ? List.of(key.subjectArmyId()) : List.of(31, 21);
            defenders = side == Side.DEFENDER ? List.of(key.subjectArmyId()) : List.of(31, 21);
        } else if (transition == Transition.JOIN_EXISTING) {
            combat = 71; combatIndex = 1;
            attackers = side == Side.ATTACKER ? List.of(51, key.subjectArmyId()) : List.of(31, 21);
            defenders = side == Side.DEFENDER ? List.of(41, key.subjectArmyId()) : List.of(31, 21);
        }
        return new Scope(frame.capture().nativeRevision(), frame.dateRaw(), key.subjectArmyId(), 201, owner,
                current, key.targetProvinceId(), key.incomingEntryProvinceId(), List.of(31, 21), List.of(51, 71),
                transition, combat, combatIndex, side, observable, isDefender, 0, attackers, defenders);
    }
    private static void expectFailure(Runnable body, String message) {
        try { body.run(); } catch (IllegalArgumentException | UnsupportedOperationException | NullPointerException expected) {
            assertions++; return;
        }
        throw new AssertionError(message);
    }
    private static void require(boolean condition, String message) {
        assertions++; if (!condition) { throw new AssertionError(message); }
    }
}
