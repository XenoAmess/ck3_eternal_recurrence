package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.wave2.military.coalition.CoalitionRiskJsonAdapter;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;

/** Exact registered readonly contracts for original war collectors; no world action or prefix permission. */
public final class WarExitReads {
    public enum Kind { OPTIONS, TERMS, POWER, PREWAR_COALITION }
    public record Key(Kind kind, int subject) { public Key { Objects.requireNonNull(kind); require(subject >= 0, "nonnegative collector subject required"); } }
    public record Query(Key key, ObjectNode envelope, PlanningReadReceipt receipt) {
        public Query { Objects.requireNonNull(key); envelope = envelope.deepCopy(); Objects.requireNonNull(receipt); }
        @Override public ObjectNode envelope() { return envelope.deepCopy(); }
    }
    public record Registered(Key key, ReadContract<Query> contract) {
        public Registered { Objects.requireNonNull(key); Objects.requireNonNull(contract); }
    }
    @FunctionalInterface public interface QueryPublication {
        /** Archive the actual read and publish its typed same-frame query cache; never synthesize a whole snapshot. */
        void publish(Query query);
    }
    @FunctionalInterface public interface DeclarationLeaseSource {
        DeclarationLeaseResult forRequest(PlanningRequest request);
    }
    public sealed interface DeclarationLeaseResult permits AvailableDeclarationLease, UnavailableDeclarationLease { }
    public record AvailableDeclarationLease(DeclarationLease lease) implements DeclarationLeaseResult {
        public AvailableDeclarationLease { Objects.requireNonNull(lease); }
    }
    public record UnavailableDeclarationLease(String reason) implements DeclarationLeaseResult {
        public UnavailableDeclarationLease { StrictJson.text(reason); }
    }
    /** Original five-field catalogue cache lease, issued from the actual registered read packet, never an array index. */
    public static final class DeclarationLease {
        private final PlanningReadReceipt receipt;
        private final BigInteger sequence;
        private final List<DeclarationContract.Choice> declarations;
        private final java.util.Optional<CurrentProof> currentProof;
        private DeclarationLease(PlanningReadReceipt receipt, BigInteger sequence, List<DeclarationContract.Choice> declarations) {
            this(receipt,sequence,declarations,java.util.Optional.empty());
        }
        private DeclarationLease(PlanningReadReceipt receipt, BigInteger sequence, List<DeclarationContract.Choice> declarations,
                java.util.Optional<CurrentProof> currentProof) {
            this.receipt = Objects.requireNonNull(receipt); this.sequence = Objects.requireNonNull(sequence);
            this.declarations = List.copyOf(declarations); this.currentProof = Objects.requireNonNull(currentProof);
        }
        public static DeclarationLease fromActualDeclarationRead(PlanningReadReceipt receipt) {
            Objects.requireNonNull(receipt);
            require(receipt.request().operation().value().equals(DeclarationContract.QUERY_DECLARABLE_WARS_STEP),
                    "actual declaration query operation required");
            require(receipt.before().paused() && receipt.after().paused()
                    && receipt.before().binding().observed().equals(receipt.after().binding().observed())
                    && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration())
                    && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "declaration read crossed its actual paused lease");
            ObjectNode top = objectFrame(receipt);
            ObjectNode result = WarExitEvidence.object(top.get("result"), "actual declaration result");
            require(WarExitEvidence.textIs(result.get("step"), DeclarationContract.QUERY_DECLARABLE_WARS_STEP)
                    && WarExitEvidence.trueValue(result.get("accepted")), "actual declaration query was not accepted");
            BigInteger sequence = StrictJson.integer(result.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
            return new DeclarationLease(receipt, sequence, DeclarationContract.normalize(result.get("declarable_wars")));
        }
        /**
         * The actual publisher alone qualifies a READ-only current extension.
         * Keep its original read/sequence/choices; never manufacture a current receipt.
         */
        public static <T> DeclarationLease fromCurrentCanonicalRead(ContinuityStorePort.Session same,
                DriverReadHistoryPublisher.CanonicalRead<T> witness, ReadContract<T> identicalCurrent,
                PlanningReadRequest actualCurrent, PlanningRequest current) throws IOException {
            Objects.requireNonNull(same); Objects.requireNonNull(witness); Objects.requireNonNull(identicalCurrent);
            Objects.requireNonNull(actualCurrent); Objects.requireNonNull(current);
            require(actualCurrent.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                    && actualCurrent.before().equals(current.before()) && actualCurrent.source().equals(current.source())
                    && actualCurrent.sessionId().equals(current.sessionId())
                    && !actualCurrent.deadline().isAfter(current.deadline())
                    && current.observations().paused() && current.observations().mapReady(),
                    "canonical declaration query must be the exact current ordinary planning request");
            PlanningReadResult.Known<T> original = witness.requireCurrent(same,identicalCurrent,actualCurrent);
            DeclarationLease retained = fromActualDeclarationRead(original.receipt());
            CurrentProof proof = new CurrentCanonical<>(same,witness,identicalCurrent,actualCurrent,current.withHistory(List.of()));
            return new DeclarationLease(retained.receipt,retained.sequence,retained.declarations,java.util.Optional.of(proof));
        }
        public PlanningReadReceipt originalRead() { return receipt; }
        public BigInteger querySequence() { return sequence; }
        public List<DeclarationContract.Choice> declarations() { return declarations; }
        public boolean matches(PlanningRequest request) {
            Objects.requireNonNull(request);
            if (currentProof.isPresent()) return currentProof.orElseThrow().matches(request,receipt);
            var source = receipt.before().binding();
            return receipt.before().paused() && request.observations().paused() && source.observed().equals(request.before())
                    && source.sessionId().equals(request.sessionId()) && source.source().equals(request.source())
                    && request.observations().snapshot().get("diagnostics") instanceof OpportunityJson.Obj diagnostics
                    && diagnostics.get("connection_generation") instanceof OpportunityJson.IntegerValue generation
                    && generation.value().equals(source.connectionGeneration());
        }
        public DeclarationContract.Choice selected(String declarationId) {
            List<DeclarationContract.Choice> matches = declarations.stream().filter(row -> row.declarationId().equals(declarationId)).toList();
            require(matches.size() == 1, "lease lacks exactly one selected native declaration"); return matches.getFirst();
        }
        private sealed interface CurrentProof permits CurrentCanonical {
            boolean matches(PlanningRequest current, PlanningReadReceipt original);
        }
        /** Stored only in memory. Cold eligibility must be rebuilt through the actual publisher. */
        private record CurrentCanonical<T>(ContinuityStorePort.Session same,
                DriverReadHistoryPublisher.CanonicalRead<T> witness, ReadContract<T> contract,
                PlanningReadRequest query, PlanningRequest nonHistory) implements CurrentProof {
            @Override public boolean matches(PlanningRequest current, PlanningReadReceipt original) {
                if (!current.withHistory(List.of()).equals(nonHistory)) return false;
                try { return witness.requireCurrent(same,contract,query).receipt().equals(original); }
                catch (IOException | IllegalArgumentException | IllegalStateException unavailable) { return false; }
            }
        }
    }
    /**
     * Root uses its already installed ArmyWarReads/ArmyForecastReads objects.
     * The delegate owns canonical reuse/publication; this seam installs no contract.
     */
    @FunctionalInterface public interface ActualReader {
        PlanningReadResult<Query> read(PlanningRequest current, Key key, OpportunityJson.Obj arguments);
    }
    private final java.util.Optional<ActualReader> actual;
    private final PlanningReadPort port;
    private final List<Registered> registered;
    private final QueryPublication publication;

    public WarExitReads(PlanningReadPort port, List<Registered> registered, QueryPublication publication) {
        this.actual = java.util.Optional.empty();
        this.port = Objects.requireNonNull(port); this.registered = List.copyOf(registered);
        this.publication = Objects.requireNonNull(publication);
        Set<Key> keys = new HashSet<>();
        for (Registered entry : registered) require(keys.add(entry.key()), "duplicate exact war collector key");
    }

    /** Retain the sole Root dispatcher and its original typed catalogue. No shadow registry is created. */
    public WarExitReads(ActualReader actual) {
        this.actual = java.util.Optional.of(Objects.requireNonNull(actual));
        this.port = null; this.registered = List.of(); this.publication = query -> { };
    }

    /** The composition root must install these exact same contract objects into PlanningReadCoordinator. */
    public static List<Registered> contractsFor(PlanningRequest request, ExactRef implementationSource) {
        List<Registered> result = new ArrayList<>(); Set<Integer> opponents = new HashSet<>();
        for (WarExitEvidence.War war : WarExitEvidence.wars(WarExitEvidence.snapshot(request))) {
            result.add(contract(new Key(Kind.OPTIONS, war.warId()), implementationSource));
            result.add(contract(new Key(Kind.TERMS, war.warId()), implementationSource));
            war.opponent().filter(value -> value > 0).ifPresent(opponents::add);
        }
        for (int opponent : opponents.stream().sorted().toList()) result.add(contract(new Key(Kind.POWER, opponent), implementationSource));
        result.add(contract(new Key(Kind.PREWAR_COALITION, 0), implementationSource));
        return List.copyOf(result);
    }

    public PlanningReadResult<Query> read(PlanningRequest request, Key key, OpportunityJson.Obj arguments) {
        Objects.requireNonNull(request); Objects.requireNonNull(key); Objects.requireNonNull(arguments);
        if (actual.isPresent()) {
            PlanningReadResult<Query> result = Objects.requireNonNull(actual.orElseThrow().read(request, key, arguments));
            if (result instanceof PlanningReadResult.Known<Query> known) {
                Query query = known.value(); var receipt = known.receipt();
                require(query.key().equals(key) && query.receipt().equals(receipt),
                        "actual war collector changed the key or original receipt");
                require(receipt.request().operation().equals(new OperationKey(step(key))),
                        "actual war collector returned another original operation");
                var binding = receipt.before().binding();
                require(binding.observed().equals(request.before()) && binding.source().equals(request.source())
                        && binding.sessionId().equals(request.sessionId())
                        && receipt.request().before().equals(request.before())
                        && receipt.request().source().equals(request.source())
                        && receipt.request().sessionId().equals(request.sessionId()),
                        "actual war collector crossed its original planning frame/source/session");
                require(receipt.before().paused() && receipt.after().paused()
                        && receipt.before().binding().observed().equals(receipt.after().binding().observed())
                        && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration())
                        && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                        "actual war collector crossed the paused native lease");
            }
            return result;
        }
        Registered selected = registered.stream().filter(entry -> entry.key().equals(key)).findFirst().orElseThrow(
                () -> new IllegalArgumentException("exact war query contract was not installed for this observed subject"));
        PlanningReadResult<Query> result = port.read(selected.contract(), new PlanningReadRequest(request.before(), request.source(), request.sessionId(),
                selected.contract().operation(), arguments, request.deadline()));
        if (result instanceof PlanningReadResult.Known<Query> known) publication.publish(known.value());
        return result;
    }

    public static String step(Key key) {
        return switch (key.kind()) {
            case OPTIONS -> "query-war-termination-options-" + positive(key.subject());
            case TERMS -> "query-war-termination-terms-v1-" + positive(key.subject());
            case POWER -> "query-war-entry-assessments-v1-1-" + positive(key.subject());
            case PREWAR_COALITION -> "query-prewar-force-coalition-coverage-v2";
        };
    }
    public static String capability(Kind kind) {
        return switch (kind) {
            case OPTIONS -> "game.command.query-war-termination-options-N";
            case TERMS -> "game.command.query-war-termination-terms-v1-N";
            case POWER -> "game.command.query-war-entry-assessments-v1-N";
            case PREWAR_COALITION -> "game.command.query-prewar-force-coalition-coverage-v2-N";
        };
    }

    private static Registered contract(Key key, ExactRef source) {
        String operation = step(key);
        ReadContract<Query> contract = new ReadContract<>("ordinary-war-read:" + key.kind().name() + ":" + key.subject(),
                new OperationKey(operation), java.util.Optional.of(capability(key.kind())), "ordinary-war-collector",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                request -> prepare(key, request), receipt -> decode(key, receipt));
        return new Registered(key, contract);
    }

    private static NativeRequest prepare(Key key, PlanningReadRequest request) {
        ObjectNode args = WarExitEvidence.object(OpportunityJson.toNode(request.arguments()), "war read arguments");
        ObjectNode fields = StrictJson.object();
        if (key.kind() == Kind.PREWAR_COALITION) {
            StrictJson.object(args, Set.of("declaration_id", "selected_declaration", "declaration_query_sequence"));
            String id = StrictJson.text(args.get("declaration_id"));
            ObjectNode selected = StrictJson.object(args.get("selected_declaration"), Set.of("target_character_id", "casus_belli_index",
                    "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids"));
            // The original declaration producer, not a label or array position, supplies this complete identity.
            require(StrictJson.integer(selected.get("target_character_id"), 1, Integer.MAX_VALUE) > 0, "declaration target required");
            StrictJson.integer(selected.get("casus_belli_index"), 0, Integer.MAX_VALUE);
            StrictJson.text(selected.get("casus_belli_key"));
            StrictJson.integer(selected.get("configuration_index"), -1, Integer.MAX_VALUE);
            StrictJson.integer(selected.get("claimant_character_id"), -1, Integer.MAX_VALUE);
            JsonNode titles = selected.get("target_title_ids"); require(titles.isArray() && titles.size() <= 4096, "bounded declared targets required");
            for (JsonNode title : titles) StrictJson.integer(title, 0, Integer.MAX_VALUE);
            StrictJson.integer(args.get("declaration_query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
            fields.put("expected_public_revision", request.before().frame().revision());
            fields.put("declaration_id", id); fields.set("selected_declaration", selected);
        } else {
            StrictJson.object(args, Set.of());
        }
        return new NativeRequest(step(key), capability(key.kind()), new RawJson(StrictJson.canonical(fields)));
    }

    private static Query decode(Key key, PlanningReadReceipt receipt) {
        ObjectNode top = objectFrame(receipt);
        ObjectNode envelope = WarExitEvidence.object(top.get("result"), "native query result").deepCopy();
        require(WarExitEvidence.textIs(envelope.get("step"), step(key)) && WarExitEvidence.trueValue(envelope.get("accepted")),
                "native query did not accept the exact readonly step");
        var observed = receipt.before().binding().observed(); var frame = observed.frame();
        envelope.put("queried_snapshot_id", frame.snapshotId()); envelope.put("queried_revision", frame.revision());
        envelope.put("queried_native_revision", frame.identity().nativeRevision()); envelope.put("queried_date_raw", frame.identity().dateRaw());
        envelope.put("queried_actor_character_id", frame.identity().player());
        envelope.put("queried_connection_generation", receipt.before().binding().connectionGeneration());
        envelope.put("queried_episode_run_id", frame.episodeRunId()); envelope.put("episode_run_id", frame.episodeRunId());
        if (key.kind() == Kind.OPTIONS) {
            ObjectNode normalized = NativeTerminationOptions.normalizeNativePacket(envelope.get("war_termination_options"), key.subject()).normalized();
            normalized.put("query_sequence", StrictJson.integer(envelope.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX));
            for (String name : List.of("queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_connection_generation", "episode_run_id"))
                normalized.set(name, envelope.get(name));
            NativeTerminationOptions.fromCache(normalized, key.subject()); envelope.set("war_termination_options", normalized);
        } else if (key.kind() == Kind.TERMS) {
            require(WarExitEvidence.textIs(envelope.get("status"), "available") || WarExitEvidence.textIs(envelope.get("status"), "unsupported"),
                    "unknown native terms availability");
            ObjectNode terms = WarExitEvidence.object(envelope.get("war_termination_terms"), "actual native war terms");
            require(WarExitEvidence.integerIs(terms.get("war_id"), key.subject()), "native terms full WarID differs");
            // Six-domain sessions are not present in this native ACK. The actual M0 producer must report that gap.
        } else if (key.kind() == Kind.POWER) {
            require(WarExitEvidence.textIs(envelope.get("status"), "available"), "power query unavailable");
            StrictJson.integer(envelope.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
            require(envelope.get("war_entry_assessments") != null, "actual power payload missing");
            // Complete power/source validation belongs to the shared actual recommendation factory.
        } else {
            StrictJson.object(top, Set.of("type", "protocol_version", "request_id", "ok", "execution_receipt", "result"));
            ObjectNode originalResult = StrictJson.object(top.get("result"), Set.of("step", "accepted", "status", "private_build", "read_only", "advertised", "domain_key", "prewar_force_coalition_coverage_v2"));
            require(WarExitEvidence.falseValue(originalResult.get("private_build")) && WarExitEvidence.trueValue(originalResult.get("read_only"))
                    && WarExitEvidence.trueValue(originalResult.get("advertised"))
                    && WarExitEvidence.textIs(originalResult.get("domain_key"), "prewar_force_coalition_coverage_v2")
                    && (WarExitEvidence.textIs(originalResult.get("status"), "available") || WarExitEvidence.textIs(originalResult.get("status"), "partial")),
                    "formal prewar result envelope differs");
            ObjectNode execution = StrictJson.object(top.get("execution_receipt"), Set.of("ticket", "query_sequence", "capture_epoch"));
            for (String name : List.of("ticket", "query_sequence", "capture_epoch")) StrictJson.integer(execution.get(name), BigInteger.ONE, StrictJson.UINT64_MAX);
            require(execution.get("ticket").bigIntegerValue().equals(execution.get("query_sequence").bigIntegerValue()), "prewar execution sequence differs from ticket");
            envelope.set("execution_receipt", execution); envelope.put("native_request_id", receipt.requestId());
            ObjectNode args = WarExitEvidence.object(OpportunityJson.toNode(receipt.request().arguments()), "prewar request source");
            ObjectNode selected = WarExitEvidence.object(args.get("selected_declaration"), "selected declaration").deepCopy();
            selected.set("declaration_id", args.get("declaration_id"));
            envelope.set("selected_declaration_source", selected);
            envelope.set("declaration_query_sequence", args.get("declaration_query_sequence"));
        }
        return new Query(key, envelope, receipt);
    }

    private static ObjectNode objectFrame(PlanningReadReceipt receipt) {
        ObjectNode top = WarExitEvidence.object(StrictJson.parse(receipt.original().originalFrame().bytes(), StrictJson.EXPLICIT_MAX_BYTES), "original native query frame");
        require(WarExitEvidence.textIs(top.get("type"), "command_result") && WarExitEvidence.integerIs(top.get("protocol_version"), 1)
                && WarExitEvidence.textIs(top.get("request_id"), receipt.requestId()) && WarExitEvidence.trueValue(top.get("ok")),
                "native query request binding differs");
        return top;
    }

    private static int positive(int value) { require(value > 0, "positive actual query subject required"); return value; }
}

