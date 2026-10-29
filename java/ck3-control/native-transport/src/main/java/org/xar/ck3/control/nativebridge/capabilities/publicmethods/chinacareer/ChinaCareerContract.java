package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_career.*;

/** Six original public requests, retaining their distinct owner/subject shapes and original typed domain frames. */
public final class ChinaCareerContract {
    private ChinaCareerContract() { }
    public enum Kind {
        CAREER_HC("career-hc-workforce-postcondition", "career_hc_workforce_postcondition", "ZhongGuo career-HC/workforce", true, false),
        MANAGER_GOVERNANCE("manager-governance-snapshot", "manager_governance_snapshot", "ZhongGuo manager-governance", true, true),
        MANAGER_SELECTOR("manager-subordinate-selector", "manager_subordinate_selector", "ZhongGuo manager/subordinate selector", false, false),
        COLLECTIVE("workforce-collective-snapshot", "workforce_collective_snapshot", "ZhongGuo Workforce collective", true, false),
        NORMAL_EXIT("workforce-normal-exit-snapshot", "workforce_normal_exit_snapshot", "ZhongGuo Workforce normal-exit", true, false),
        OWNER("workforce-owner-snapshot", "workforce_owner_snapshot", "ZhongGuo Workforce owner", false, false);
        private final String suffix, publicSuffix, label;
        private final boolean owner, subject;
        Kind(String suffix, String publicSuffix, String label, boolean owner, boolean subject) {
            this.suffix = suffix; this.publicSuffix = publicSuffix; this.label = label; this.owner = owner; this.subject = subject;
        }
        public String step() { return "query-zhongguo-" + suffix + "-v1"; }
        public String capability() { return "game.command." + step(); }
        public String publicName() { return "ck3_query_zhongguo_" + publicSuffix + "_v1"; }
        public String payload() { return "zhongguo_" + publicSuffix; }
        public String label() { return label; }
        public boolean ownerArgument() { return owner; }
        public boolean subjectArgument() { return subject; }
    }
    public record Request(Kind kind, String requestNonce, BigInteger expectedRevision,
            OptionalInt ownerCharacterId, OptionalInt subjectCharacterId) {
        public Request {
            Objects.requireNonNull(kind); Objects.requireNonNull(requestNonce);
            Objects.requireNonNull(ownerCharacterId); Objects.requireNonNull(subjectCharacterId);
            PublicUnsigned64.canonical(expectedRevision, PublicUnsigned64.Minimum.ZERO);
            StrictJson.require(ownerCharacterId.isPresent() == kind.ownerArgument()
                    && subjectCharacterId.isPresent() == kind.subjectArgument(), "exact original owner/subject argument shape required");
            ownerCharacterId.ifPresent(ChinaCareerContract::positive);
            subjectCharacterId.ifPresent(ChinaCareerContract::positive);
            // The original service validates nonce after its current frame guards.
            // Its JSON string type is checked on entry; bounded ASCII syntax is
            // checked in the service at that original point in the sequence.
        }
        public int owner(Frame frame) { return ownerCharacterId.orElse(frame.playerId()); }
        public int subject(Frame frame) { return subjectCharacterId.orElse(frame.playerId()); }
    }
    /** Actual Root supplies this inside its current physical/readiness scope. Software construction grants no native permission. */
    public record Frame(String snapshotId, BigInteger publicRevision, BigInteger nativeRevision,
            BigInteger generation, int dateRaw, int playerId, boolean paused, boolean mapReady,
            String episode, NativeWire.Hello originalHello, ExactRef helloOriginal) {
        public Frame {
            StrictJson.text(snapshotId); StrictJson.text(episode); positive(playerId);
            PublicUnsigned64.canonical(publicRevision, PublicUnsigned64.Minimum.ZERO);
            PublicUnsigned64.canonical(nativeRevision, PublicUnsigned64.Minimum.ONE);
            PublicUnsigned64.canonical(generation, PublicUnsigned64.Minimum.ONE);
            Objects.requireNonNull(originalHello); Objects.requireNonNull(helloOriginal);
            var bytes = NativeRequestChronology.PacketIdentity.of(originalHello.packet().value());
            StrictJson.require(bytes.bytes() == helloOriginal.bytes() && bytes.sha256().equals(helloOriginal.sha256())
                    && originalHello.connectionGeneration().equals(generation), "China career HELLO DATA hash/generation changed");
            try {
                NativeWire.Frame parsed = NativeWire.decode(originalHello.packet().value());
                StrictJson.require(parsed instanceof NativeWire.Hello, "original capability packet must be HELLO");
                NativeWire.Hello value = (NativeWire.Hello) parsed;
                StrictJson.require(value.pid() == originalHello.pid() && value.connectionGeneration().equals(generation)
                        && value.capabilities().equals(originalHello.capabilities()) && value.gameSha256().equals(originalHello.gameSha256())
                        && value.adapterId().equals(originalHello.adapterId()) && value.adapterStatus().equals(originalHello.adapterStatus())
                        && value.bridgeVersion().equals(originalHello.bridgeVersion()) && value.buildMatch() == originalHello.buildMatch(),
                        "China career typed HELLO differs from original packet");
            } catch (java.io.IOException failure) { throw new IllegalArgumentException("malformed original China career HELLO", failure); }
        }
        public CareerJson.FrameBinding binding(Request request) {
            return new CareerJson.FrameBinding(request.requestNonce(), snapshotId, publicRevision, nativeRevision,
                    generation, dateRaw, playerId, request.subject(this), request.owner(this));
        }
    }
    public sealed interface DomainFrame permits Career, Governance, Selector, Collective, NormalExit, Owner {
        CareerJson.Header header();
    }
    public record Career(OwnerCareerFrames.Career value) implements DomainFrame {
        public Career { Objects.requireNonNull(value); }
        @Override public CareerJson.Header header() { return value.header(); }
    }
    public record Governance(ManagerGovernanceFrame value) implements DomainFrame {
        public Governance { Objects.requireNonNull(value); }
        @Override public CareerJson.Header header() { return value.header(); }
    }
    public record Selector(ManagerSelectorFrame value) implements DomainFrame {
        public Selector { Objects.requireNonNull(value); }
        @Override public CareerJson.Header header() { return value.header(); }
    }
    public record Collective(CollectiveWorkforceFrame value) implements DomainFrame {
        public Collective { Objects.requireNonNull(value); }
        @Override public CareerJson.Header header() { return value.header(); }
    }
    public record NormalExit(NormalExitWorkforceFrame value) implements DomainFrame {
        public NormalExit { Objects.requireNonNull(value); }
        @Override public CareerJson.Header header() { return value.header(); }
    }
    public record Owner(OwnerCareerFrames.Owner value) implements DomainFrame {
        public Owner { Objects.requireNonNull(value); }
        @Override public CareerJson.Header header() { return value.header(); }
    }
    public record NativeObservation(Kind kind, CareerJson.FrameBinding binding, DomainFrame domain,
            RawJson originalFrame, BigInteger querySequence, String backendId) {
        public NativeObservation {
            Objects.requireNonNull(kind); Objects.requireNonNull(binding); Objects.requireNonNull(domain); Objects.requireNonNull(originalFrame);
            PublicUnsigned64.canonical(querySequence, PublicUnsigned64.Minimum.ONE); StrictJson.text(backendId);
        }
    }
    public record Response(Request request, Frame frame, NativeObservation nativeObservation, RawJson publicJson) {
        public Response {
            Objects.requireNonNull(request); Objects.requireNonNull(frame); Objects.requireNonNull(nativeObservation); Objects.requireNonNull(publicJson);
        }
    }
    public enum ErrorKind { BRIDGE_UNAVAILABLE, UNSUPPORTED_STEP, VALUE_ERROR }
    public record Fault(ErrorKind kind, String originalMessage, Optional<ExactRef> originalRead) {
        public Fault { Objects.requireNonNull(kind); StrictJson.text(originalMessage); Objects.requireNonNull(originalRead); }
        public String pythonName() { return switch (kind) {
            case BRIDGE_UNAVAILABLE -> "BridgeUnavailableError";
            case UNSUPPORTED_STEP -> "UnsupportedStepError";
            case VALUE_ERROR -> "ValueError";
        }; }
    }
    public static final class Failure extends RuntimeException {
        private static final long serialVersionUID = 1L;
        // In-process typed diagnostic; Java serialization of the domain Fault is unsupported.
        @SuppressWarnings("serial")
        private final Fault fault;
        public Failure(Fault fault) { super(Objects.requireNonNull(fault).originalMessage()); this.fault = fault; }
        public Fault fault() { return fault; }
    }
    public static void positive(int id) { StrictJson.require(id > 0, "positive int32 character identity required"); }
}
