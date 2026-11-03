package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.MessageDigestSpi;
import java.security.NoSuchAlgorithmException;
import java.security.Provider;
import java.security.ProviderException;
import java.security.Security;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One standalone public DATA compatibility case; no native, writer or Session issuer. */
public final class KnownConstructorDigestInputMutationWitness {
    private static final String PROVIDER_NAME = "KnownConstructorDigestInputMutationWitnessProvider";
    private static final byte[] EXPECTED_WIRE = "{\"format_version\":2,\"pipe_name\":\"digest_input_pipe\",\"bridge_pid\":123,\"episode_character_id\":73,\"episode_run_id\":\"digest_input_episode\",\"command_history\":[],\"last_checkpoint\":null,\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":null}".getBytes(StandardCharsets.UTF_8);
    private static final String EXPECTED_SHA = "b7531a5e14e29bb92e48885b55c03e6fa67042a35dcfc957e3c16762137cf0c6";
    private static final byte[] EXPECTED_DIGEST = HexFormat.of().parseHex(EXPECTED_SHA);
    private static final String METADATA_SHA = "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a";
    private static volatile Probe activeProbe;

    private KnownConstructorDigestInputMutationWitness() { }

    public static void main(String[] args) throws Exception {
        if (args.length == 1 && "baseline321".equals(args[0])) {
            distinctEqualDriversSurviveCorrectDigestInputMutation(true);
            System.out.println("PUBLIC_KNOWN_JCA_INPUT_MUTATION_BASELINE321 cases=1 EXPECTED_REJECTION_PASS");
        } else {
            require(args.length == 0, "only noargs selected mode or baseline321 is accepted");
            distinctEqualDriversSurviveCorrectDigestInputMutation();
            System.out.println("PUBLIC_KNOWN_JCA_INPUT_MUTATION_ONLY cases=1 PASS");
        }
    }

    public static void distinctEqualDriversSurviveCorrectDigestInputMutation() throws Exception {
        distinctEqualDriversSurviveCorrectDigestInputMutation(false);
    }

    private static void distinctEqualDriversSurviveCorrectDigestInputMutation(boolean baseline321) throws Exception {
        require(activeProbe == null, "another digest-input witness is active");
        require(Security.getProvider(PROVIDER_NAME) == null, "witness provider name is occupied");
        Provider[] originalOrder = Security.getProviders();
        Provider originalProvider = MessageDigest.getInstance("SHA-256").getProvider();
        byte[] authenticDigest = MessageDigest.getInstance("SHA-256", originalProvider).digest(EXPECTED_WIRE.clone());
        require(Arrays.equals(authenticDigest, EXPECTED_DIGEST), "original provider must produce literal authentic SHA-256");
        DriverStateSnapshot.Complete driver = driver();
        DriverStateSnapshot.Complete observedDriver = driver();
        require(driver != observedDriver, "two distinct Complete objects are required");
        require(driver.session().actorId().getClass() == BigInteger.class
                && observedDriver.session().actorId().getClass() == BigInteger.class, "standard actors only");
        require(Arrays.equals(driver.encode(), EXPECTED_WIRE), "literal current Driver wire differs");
        require(Arrays.equals(observedDriver.encode(), EXPECTED_WIRE), "literal observed Driver wire differs");
        var game = new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE));
        var stamp = new DriverSnapshotFacts.Stamp(7, 3, game, "digest_input_episode", EXPECTED_SHA);
        var basis = new ExactRef("software/reference-data/known-digest/driver.json", 350, EXPECTED_SHA);
        var evidence = new ExactRef("software/reference-data/known-digest/observation.json", 2, METADATA_SHA);
        var sourceRef = new ExactRef("software/reference-data/known-digest/source.json", 2, METADATA_SHA);
        var source = new G2Source("software-digest", "2026-11-04T00:00:00Z", "public-data-only", sourceRef);
        var transport = new NativeObservationPort.TransportSession("software-digest", game, BigInteger.ONE, "digest_input_session");
        var auxiliary = new OpportunityJson.Obj(Map.of());
        var observation = new DriverObservationFacts(observedDriver, 7, 3, transport, "digest_input_snapshot",
                BigInteger.ONE, METADATA_SHA, BigInteger.ONE, 1, source, auxiliary, evidence);
        var probe = new Probe(originalProvider);
        var wrapper = new MutationProvider();
        boolean constructorAttempted = false;
        activeProbe = probe;
        try {
            require(Security.insertProviderAt(wrapper, 1) == 1, "provider was not inserted at preference one");
            require(Security.getProvider(PROVIDER_NAME) == wrapper, "installed provider identity differs");
            require(MessageDigest.getInstance("SHA-256").getProvider() == wrapper, "default SHA-256 did not select witness provider");
            constructorAttempted = true;
            DriverSnapshotFacts.Known known;
            try {
                known = new DriverSnapshotFacts.Known(driver, stamp, basis, List.of(), auxiliary,
                        Optional.empty(), Optional.of(observation));
            } catch (ContractViolationException failure) {
                if (!baseline321) throw failure;
                require(failure.getClass() == ContractViolationException.class,
                        "baseline321 must throw the exact production ContractViolationException");
                require("semantic facts crossed Driver version".equals(failure.getMessage()),
                        "baseline321 must reject at the exact original semantic comparison");
                return;
            }
            require(!baseline321, "baseline321 unexpectedly accepted the cached mutated bytes");
            require(known.driver() == driver && known.observation().orElseThrow() == observation,
                    "actual public Known constructor must retain both supplied identities");
            require(Arrays.equals(driver.encode(), EXPECTED_WIRE), "provider must not change the typed Driver");
            require(Arrays.equals(observedDriver.encode(), EXPECTED_WIRE), "provider must not change the observed Driver");
        } finally {
            try {
                if (constructorAttempted) requireActualMutation(probe);
            } finally {
                try {
                    if (Security.getProvider(PROVIDER_NAME) == wrapper) Security.removeProvider(PROVIDER_NAME);
                    requireProvidersRestored(originalOrder);
                } finally {
                    activeProbe = null;
                }
            }
        }
    }

    private static DriverStateSnapshot.Complete driver() {
        var session = new DriverStateSnapshot.Session("digest_input_pipe", 123,
                new BigInteger("73"), "digest_input_episode");
        var nil = new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(session, List.of(), nil, nil, nil, nil, nil, nil, nil);
    }

    private static void requireActualMutation(Probe probe) {
        require(probe.targetUpdates == 1 && probe.correctDigests == 1 && probe.mutations == 1,
                "actual production SHA must consume and mutate exactly one target array");
        require(Arrays.equals(probe.returnedDigest, EXPECTED_DIGEST), "provider returned a false digest");
        byte[] mutated = EXPECTED_WIRE.clone();
        mutated[0] ^= 1;
        require(probe.receivedInput != EXPECTED_WIRE && Arrays.equals(probe.receivedInput, mutated),
                "SPI did not mutate its received input array after authentic hashing");
    }

    private static void requireProvidersRestored(Provider[] originalOrder) {
        Provider[] current = Security.getProviders();
        require(current.length == originalOrder.length, "provider count was not restored");
        for (int index = 0; index < current.length; index++) {
            require(current[index] == originalOrder[index], "provider identity/order was not restored");
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static final class Probe {
        final Provider originalProvider;
        int targetUpdates;
        int correctDigests;
        int mutations;
        byte[] receivedInput;
        byte[] returnedDigest;
        Probe(Provider originalProvider) { this.originalProvider = originalProvider; }
    }

    public static final class MutationProvider extends Provider {
        private static final long serialVersionUID = 1L;
        public MutationProvider() {
            super(PROVIDER_NAME, "1.0", "Authentic delegated SHA-256 with observable consumed-input mutation");
            putService(new Service(this, "MessageDigest", "SHA-256", MutationSpi.class.getName(), List.of(), Map.of()));
        }
    }

    public static final class MutationSpi extends MessageDigestSpi {
        private final Probe probe;
        private final MessageDigest delegate;
        private byte[] pendingTarget;
        public MutationSpi() {
            probe = activeProbe;
            if (probe == null) throw new ProviderException("witness context is absent");
            try {
                delegate = MessageDigest.getInstance("SHA-256", probe.originalProvider);
            } catch (NoSuchAlgorithmException error) {
                throw new ProviderException("captured original SHA-256 is unavailable", error);
            }
        }
        @Override protected void engineUpdate(byte input) {
            pendingTarget = null;
            delegate.update(input);
        }
        @Override protected void engineUpdate(byte[] input, int offset, int length) {
            boolean target = offset == 0 && length == input.length && Arrays.equals(input, EXPECTED_WIRE);
            delegate.update(input, offset, length);
            pendingTarget = target ? input : null;
            if (target) probe.targetUpdates++;
        }
        @Override protected byte[] engineDigest() {
            byte[] digest = delegate.digest();
            byte[] target = pendingTarget;
            pendingTarget = null;
            if (target != null) {
                require(Arrays.equals(digest, EXPECTED_DIGEST), "delegate digest is not the literal authentic SHA-256");
                probe.correctDigests++;
                probe.returnedDigest = digest.clone();
                probe.receivedInput = target;
                target[0] ^= 1;
                probe.mutations++;
            }
            return digest;
        }
        @Override protected void engineReset() {
            delegate.reset();
            pendingTarget = null;
        }
        @Override protected int engineGetDigestLength() { return delegate.getDigestLength(); }
    }
}
