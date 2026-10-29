package org.xar.ck3.control.wave2.military.prewaradmission;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Field;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.QueryEnvelope;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Snapshot;

/** Outer current-query lease gate. Assessable means call the actual coalition validator, never DECLARE. */
public final class PrewarAdmissionGate {
    private static final BigInteger INT32_MIN = BigInteger.ONE.shiftLeft(31).negate();
    private static final BigInteger INT32_MAX = BigInteger.ONE.shiftLeft(31).subtract(BigInteger.ONE);
    private static final Set<String> RECEIPT_FIELDS = Set.of("ticket", "query_sequence", "capture_epoch");

    private PrewarAdmissionGate() { }

    public enum Reason {
        CURRENT_SNAPSHOT_REQUIRED("current_snapshot_required"),
        CURRENT_PAUSED_LIVING_ACTOR_REQUIRED("current_paused_living_actor_required"),
        CURRENT_NATIVE_BUILD_REQUIRED("current_native_build_required"),
        CURRENT_SNAPSHOT_BINDING_REQUIRED("current_snapshot_binding_required"),
        CURRENT_DECLARATION_IDENTITY_REQUIRED("current_declaration_identity_required"),
        CURRENT_FORCE_COALITION_QUERY_REQUIRED("current_force_coalition_query_required"),
        FORCE_COALITION_QUERY_SCOPE_STALE("force_coalition_query_scope_stale"),
        FORCE_COALITION_QUERY_NOT_ACCEPTED("force_coalition_query_not_accepted"),
        INDEPENDENT_FORCE_COALITION_RECEIPT_REQUIRED("independent_force_coalition_receipt_required"),
        FORCE_COALITION_COVERAGE_PARTIAL("force_coalition_coverage_partial");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public sealed interface Outcome permits Stopped, Assessable { }
    public record RequiredQuery(String declarationId, BigInteger expectedRevision) {
        public RequiredQuery { Objects.requireNonNull(declarationId); Objects.requireNonNull(expectedRevision); }
        public String profile() { return "v2"; }
    }
    public record Stopped(Reason reason, RequiredQuery requiredQuery) implements Outcome {
        public Stopped { Objects.requireNonNull(reason); }
    }
    public record Assessable(PrewarAdmissionInput input) implements Outcome {
        public Assessable { Objects.requireNonNull(input); }
    }

    public static Outcome evaluate(PrewarAdmissionInput input) {
        Objects.requireNonNull(input, "input");
        if (!input.snapshot().hasValue()) { return stop(Reason.CURRENT_SNAPSHOT_REQUIRED); }
        Snapshot snapshot = input.snapshot().value();
        if (!trueValue(snapshot.paused()) || !trueValue(snapshot.mapReady())
                || !snapshot.playedCharacter().hasValue()
                || !trueValue(snapshot.playedCharacter().value().alive())
                || !nonnegative(snapshot.playedCharacter().value().characterId())
                || snapshot.playedCharacter().value().characterId().value().signum() == 0
                || !snapshot.diagnostics().hasValue()) {
            return stop(Reason.CURRENT_PAUSED_LIVING_ACTOR_REQUIRED);
        }
        var diagnostics = snapshot.diagnostics().value();
        if (!diagnostics.hello().hasValue()
                || !textEquals(diagnostics.hello().value().bridgeVersion(), "0.1.0.4")) {
            return stop(Reason.CURRENT_NATIVE_BUILD_REQUIRED);
        }
        if (!nonempty(snapshot.snapshotId()) || !nonnegative(snapshot.revision())
                || !nonnegative(snapshot.nativeRevision()) || !nonnegative(diagnostics.connectionGeneration())
                || !dateRaw(snapshot.dateRaw())
                || (snapshot.episodeRunId().hasValue() && snapshot.episodeRunId().value().isEmpty())) {
            return stop(Reason.CURRENT_SNAPSHOT_BINDING_REQUIRED);
        }
        if (!nonempty(input.declaration().declarationId())) { return stop(Reason.CURRENT_DECLARATION_IDENTITY_REQUIRED); }
        if (!snapshot.query().hasValue()) {
            return new Stopped(Reason.CURRENT_FORCE_COALITION_QUERY_REQUIRED,
                    new RequiredQuery(input.declaration().declarationId().value(), snapshot.revision().value()));
        }
        QueryEnvelope query = snapshot.query().value();
        if (!same(query.queriedSnapshotId(), snapshot.snapshotId()) || !same(query.queriedRevision(), snapshot.revision())
                || !same(query.queriedNativeRevision(), snapshot.nativeRevision()) || !same(query.queriedDateRaw(), snapshot.dateRaw())
                || !same(query.queriedActorCharacterId(), snapshot.playedCharacter().value().characterId())
                || !same(query.queriedConnectionGeneration(), diagnostics.connectionGeneration())
                || !sameNullableEpisode(query.queriedEpisodeRunId(), snapshot.episodeRunId())
                || !nonnegative(query.queriedRevision()) || !nonnegative(query.queriedNativeRevision())
                || !nonnegative(query.queriedActorCharacterId()) || !nonnegative(query.queriedConnectionGeneration())
                || !dateRaw(query.queriedDateRaw())) {
            return stop(Reason.FORCE_COALITION_QUERY_SCOPE_STALE);
        }
        if (!trueValue(query.accepted())) { return stop(Reason.FORCE_COALITION_QUERY_NOT_ACCEPTED); }
        if (!query.executionReceipt().hasValue() || !nonempty(query.nativeRequestId()) || !query.coverage().hasValue()) {
            return stop(Reason.INDEPENDENT_FORCE_COALITION_RECEIPT_REQUIRED);
        }
        Set<String> receiptFields = new HashSet<>();
        query.executionReceipt().value().copy().fieldNames().forEachRemaining(receiptFields::add);
        if (!receiptFields.equals(RECEIPT_FIELDS)) { return stop(Reason.INDEPENDENT_FORCE_COALITION_RECEIPT_REQUIRED); }
        if (!textEquals(query.status(), "available")) { return stop(Reason.FORCE_COALITION_COVERAGE_PARTIAL); }
        return new Assessable(input);
    }

    private static Stopped stop(Reason reason) { return new Stopped(reason, null); }
    private static boolean trueValue(Field<Boolean> field) { return field.hasValue() && field.value(); }
    private static boolean textEquals(Field<String> field, String text) { return field.hasValue() && field.value().equals(text); }
    private static boolean nonempty(Field<String> field) { return field.hasValue() && !field.value().isEmpty(); }
    private static boolean nonnegative(Field<BigInteger> field) { return field.hasValue() && field.value().signum() >= 0; }
    private static boolean dateRaw(Field<BigInteger> field) {
        return field.hasValue() && field.value().compareTo(INT32_MIN) >= 0 && field.value().compareTo(INT32_MAX) <= 0;
    }
    private static <T> boolean same(Field<T> actual, Field<T> expected) {
        return actual.isPresent() && Objects.equals(actual.value(), expected.value());
    }
    private static boolean sameNullableEpisode(Field<String> actual, Field<String> expected) {
        return actual.isPresent() && Objects.equals(actual.value(), expected.value());
    }
}
