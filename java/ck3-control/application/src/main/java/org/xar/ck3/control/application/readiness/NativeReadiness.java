package org.xar.ck3.control.application.readiness;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.LongSupplier;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Original native_auto_run readiness predicate and stable application-main pump gate. No action authority. */
public final class NativeReadiness {
    private NativeReadiness() { }
    public enum Status { READY, WAITING, INCOMPLETE, FATAL }
    public record Policy(boolean coldCheckpoint, boolean allowTerminal, Optional<BigInteger> expectedActor,
            Duration stableFor, boolean requirePostReadyPump) {
        public Policy {
            Objects.requireNonNull(expectedActor); Objects.requireNonNull(stableFor);
            expectedActor.ifPresent(NativeCharacterId::of);
            require(!stableFor.isNegative() && stableFor.compareTo(Duration.ofDays(1)) <= 0, "finite readiness stability window required");
        }
        public boolean pumpRequired() { return coldCheckpoint || requirePostReadyPump; }
    }
    public record StableKey(String machineId, org.xar.ck3.control.contracts.GameGeneration game, String sessionId,
            BigInteger bridgePid, BigInteger connectionGeneration, String snapshotId, BigInteger revision,
            BigInteger nativeRevision, BigInteger dateRaw, String episodeRunId, BigInteger playedActor, BigInteger episodeActor) { }
    public record Assessment(Status status, String reason, boolean terminal, Optional<StableKey> key,
            Optional<BigInteger> pumpEpoch) {
        public Assessment {
            Objects.requireNonNull(status); org.xar.ck3.control.contracts.StrictJson.text(reason);
            Objects.requireNonNull(key); Objects.requireNonNull(pumpEpoch);
            require(status != Status.READY || key.isPresent(), "ready assessment requires its real stable frame key");
        }
        public boolean ready() { return status == Status.READY; }
    }
    private static final class Gap extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        Gap(String field) { super(field); }
    }
    private static final class Hold extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        Hold(String reason) { super(reason); }
    }
    /** Dynamic JSON is checked here once; absent, null, false and wrong token types remain distinct. */
    public static Assessment assess(Complete frame, Obj capabilities, Policy policy) {
        Objects.requireNonNull(frame); Objects.requireNonNull(capabilities); Objects.requireNonNull(policy);
        boolean terminal = false;
        try {
            Obj snapshot = frame.semantic();
            check(string(capabilities, "mode").equals("native-headless"), "mode is not native-headless");
            check(string(capabilities, "backend_id").equals("native-headless"), "backend is not native-headless");
            check(!flag(capabilities, "visual_fallback"), "visual fallback is not disabled");
            check(flag(capabilities, "transport_ready"), "native transport is not ready");
            Obj diagnostics = objectField(capabilities, "diagnostics");
            Value fatal = present(diagnostics, "transport_fatal_error");
            if (fatal instanceof Text message && !message.value().isEmpty())
                return result(Status.FATAL, message.value(), false);
            if (fatal != Nil.INSTANCE && !(fatal instanceof Text)) throw new Gap("transport_fatal_error must be string or explicit null");
            check(flag(diagnostics, "connected"), "bridge is disconnected");
            check(flag(diagnostics, "semantic_state_available"), "semantic state is unavailable");
            check(flag(capabilities, "snapshot"), "snapshot capability is unavailable");
            Obj snapshotDiagnostics = objectField(snapshot, "diagnostics");
            BigInteger bridge = positive(diagnostics, "bridge_pid");
            BigInteger connection = positive(diagnostics, "connection_generation");
            check(bridge.equals(positive(snapshotDiagnostics, "bridge_pid"))
                    && connection.equals(positive(snapshotDiagnostics, "connection_generation")), "capability and snapshot transports differ");
            check(bridge.equals(BigInteger.valueOf(frame.identity().game().pid()))
                    && connection.equals(frame.connectionGeneration()), "capability and held Game transports differ");
            Obj hello = objectField(diagnostics, "hello");
            if (!flag(hello, "ck3_build_match") || string(hello, "game_adapter_status").equals("unsupported_build"))
                return result(Status.FATAL, "CK3 exact-build adapter is not ready", false);
            check(string(hello, "game_adapter_status").equals("ready"), "game adapter status is not ready");
            Obj heartbeat = objectField(diagnostics, "last_heartbeat");
            nonnegative(heartbeat, "sequence");
            check(!flag(heartbeat, "startup_failure_containment_enabled"), "startup containment is not disabled");
            check(!flag(heartbeat, "startup_particle2_stage_recorder_enabled"), "startup stage recorder is not disabled");
            Obj mailbox = objectField(heartbeat, "main_thread_query_mailbox_v1");
            check(flag(mailbox, "installed"), "main-thread mailbox is not installed");
            check(!flag(mailbox, "stop"), "main-thread mailbox is stopping");
            check(nonnegative(mailbox, "failure").signum() == 0, "main-thread mailbox reports failure");
            check(flag(mailbox, "ready"), "main-thread mailbox is not ready");
            check(flag(mailbox, "executor_submission_enabled"), "main-thread mailbox executor is disabled");
            check(flag(snapshot, "map_ready"), "map is not ready");
            check(flag(snapshot, "paused"), "map is not paused");
            check(!flag(snapshot, "episode_identity_pending"), "episode identity is pending");
            BigInteger episodeActor = character(snapshot, "episode_character_id");
            String episode = string(snapshot, "episode_run_id");
            Obj control = objectField(capabilities, "native_session_control");
            String binding = activeBinding(control);
            BigInteger date = nonnegative(snapshot, "date_raw");
            check(nonnegative(mailbox, "date_raw").equals(date), "mailbox date differs from paused snapshot");
            check(flag(mailbox, "paused"), "mailbox did not observe paused state");
            boolean terminalFlag = flag(snapshot, "one_life_terminal");
            Value terminalReason = present(snapshot, "one_life_terminal_reason");
            if (terminalReason != Nil.INSTANCE && !(terminalReason instanceof Text)) throw new Gap("one_life_terminal_reason must be string or explicit null");
            terminal = terminalFlag || terminalReason instanceof Text;
            Obj player = objectField(snapshot, "played_character");
            BigInteger playedActor = character(player, "character_id");
            boolean alive = flag(player, "alive");
            if (!(terminal && policy.allowTerminal())) {
                check(alive, "played character is not alive");
                check(episodeActor.equals(playedActor), "played character differs from episode character");
            }
            if (policy.expectedActor().isPresent()) {
                check(episodeActor.equals(policy.expectedActor().orElseThrow()), "episode character does not match expected character");
                check(playedActor.equals(policy.expectedActor().orElseThrow()), "played character does not match expected character");
            }
            if (policy.coldCheckpoint()) {
                requireColdCheckpoint(control, binding);
            }
            StableKey key = new StableKey(frame.identity().machineId(), frame.identity().game(), frame.sessionId(), bridge, connection,
                    string(snapshot, "snapshot_id"), positive(snapshot, "revision"), positive(snapshot, "native_revision"),
                    date, episode, playedActor, episodeActor);
            BigInteger pump = nonnegative(mailbox, "pump_epochs");
            return new Assessment(Status.READY, "ready", terminal, Optional.of(key), Optional.of(pump));
        } catch (Hold hold) { return result(Status.WAITING, hold.getMessage(), terminal); }
        catch (IllegalArgumentException | ArithmeticException incomplete) { return result(Status.INCOMPLETE, incomplete.getMessage(), terminal); }
    }
    /** Actual presentation fields only; accepting this DATA branch creates no private Root/operator authority. */
    static String activeBinding(Obj control) {
        String binding = string(control, "episode_binding_state");
        if (binding.equals("active_operator_rebind"))
            check(string(control, "driver_state_restore_kind").equals("operator_played_character_rebind"),
                    "operator binding does not have its actual driver restore kind");
        else check(List.of("active_new", "active_resumed", "active_natural_successor").contains(binding), "episode identity is not active");
        return binding;
    }
    /** Same pre-existing cold qualification: an operator rebind is never a checkpoint restore. */
    static void requireColdCheckpoint(Obj control, String binding) {
        check(flag(control, "driver_state_restored"), "cold driver state was not restored");
        check(string(control, "driver_state_restore_kind").equals("cold_checkpoint"), "cold restore kind is not checkpoint");
        check(binding.equals("active_resumed"), "cold episode was not resumed");
        check(present(control, "cold_candidate_rejection") == Nil.INSTANCE, "cold checkpoint candidate was rejected");
    }
    /** State is local to one owned provider; false/missing observations reset both stability and pump baseline. */
    public static final class StableGate {
        private final Policy policy;
        private final LongSupplier monotonicClock;
        private StableKey key;
        private BigInteger pumpBaseline;
        private long stableSince;
        private long previousTick;
        private boolean tickSeen;
        public StableGate(Policy policy) { this(policy, System::nanoTime); }
        public StableGate(Policy policy, LongSupplier monotonicClock) {
            this.policy = Objects.requireNonNull(policy); this.monotonicClock = Objects.requireNonNull(monotonicClock);
        }
        public synchronized Assessment observe(Assessment assessment) {
            Objects.requireNonNull(assessment); long now = monotonicClock.getAsLong();
            if (tickSeen && now - previousTick < 0) { reset(); return result(Status.INCOMPLETE, "readiness monotonic clock regressed", assessment.terminal()); }
            previousTick = now; tickSeen = true;
            if (!assessment.ready()) { reset(); return assessment; }
            StableKey current = assessment.key().orElseThrow();
            if (!current.equals(key)) {
                key = current; stableSince = now; pumpBaseline = assessment.pumpEpoch().orElse(null);
            }
            if (policy.pumpRequired() && (pumpBaseline == null || assessment.pumpEpoch().isEmpty()
                    || assessment.pumpEpoch().orElseThrow().compareTo(pumpBaseline) <= 0))
                return new Assessment(Status.WAITING, "application-main pump has not advanced after readiness", assessment.terminal(), assessment.key(), assessment.pumpEpoch());
            if (now - stableSince < policy.stableFor().toNanos())
                return new Assessment(Status.WAITING, "native readiness frame is not stable for the configured duration", assessment.terminal(), assessment.key(), assessment.pumpEpoch());
            return assessment;
        }
        public synchronized void reset() { key = null; pumpBaseline = null; }
    }
    private static Assessment result(Status status, String reason, boolean terminal) {
        return new Assessment(status, reason == null || reason.isEmpty() ? "readiness input is incomplete" : reason, terminal, Optional.empty(), Optional.empty());
    }
    private static void check(boolean passed, String reason) { if (!passed) throw new Hold(reason); }
    static Value present(Obj row, String field) { if (!row.members().containsKey(field)) throw new Gap("missing readiness field: " + field); return row.get(field); }
    static Obj objectField(Obj row, String field) { return object(present(row, field), field); }
    static boolean flag(Obj row, String field) { return bool(present(row, field), field); }
    static String string(Obj row, String field) { return text(present(row, field), field); }
    static BigInteger nonnegative(Obj row, String field) { BigInteger value = integer(present(row, field), field); require(value.signum() >= 0, "nonnegative " + field + " required"); return value; }
    static BigInteger positive(Obj row, String field) { BigInteger value = nonnegative(row, field); require(value.signum() > 0, "positive " + field + " required"); return value; }
    static BigInteger character(Obj row, String field) { return NativeCharacterId.of(integer(present(row, field), field)).asBigInteger(); }
}
