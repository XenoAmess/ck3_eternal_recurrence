package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeConstructionEffects;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyAdapters;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncomeJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;

/** The original-body cold/completion reducer. No native call, file operation, writer or UNKNOWN resolution. */
public final class ConstructionMaterialReducer {
    public static final String LEGACY_SCHEMA = "xar.construction-material-reducer-input/v1";
    public static final String SCHEMA = "xar.construction-material-reducer-input/v2";
    public static final int MAX_INPUT_BYTES = 4_194_304;
    public static final BigInteger MONTH = BigInteger.valueOf(720);
    public enum Disposition { MATERIAL_UPDATED, PRIOR_MATERIAL_RETAINED, RESTORED_BEFORE_ACTION }
    public enum InputVersion { LEGACY_V1, REFRESH_V2 }
    public enum RefreshKind { COLD_MATERIAL, COMPLETED_CASH, COMPLETED_PROVINCE, MONTHLY_COMPLETION, PREPARED_ZERO_DISPATCH }
    public record Input(InputVersion version, Optional<RefreshKind> refreshKind, ConstructionLedgerCodec.Ledger ledger,
            String actionRequestId, Obj queryObservation, Optional<Obj> root, Optional<Obj> cash) {
        public Input { Objects.requireNonNull(version); Objects.requireNonNull(refreshKind);
            require((version == InputVersion.LEGACY_V1) == refreshKind.isEmpty(), "material version and refresh kind differ");
            Objects.requireNonNull(ledger); require(actionRequestId != null && !actionRequestId.isEmpty(), "original action identity required");
            Objects.requireNonNull(queryObservation); Objects.requireNonNull(root); Objects.requireNonNull(cash); }
    }
    public record Reduced(Disposition disposition, Obj originalBody, Obj observation, Optional<Obj> receipt) {
        public Reduced { Objects.requireNonNull(disposition); Objects.requireNonNull(originalBody); Objects.requireNonNull(observation);
            Objects.requireNonNull(receipt); ConstructionLedgerCodec.validateLedger(encode(originalBody)); }
    }
    private ConstructionMaterialReducer() { }

    public static Input decode(byte[] raw) {
        Obj input = DriverJson.object(raw, MAX_INPUT_BYTES);
        InputVersion version;
        Optional<RefreshKind> kind;
        if (new Text(LEGACY_SCHEMA).equals(input.get("schema"))) {
            require(input.members().keySet().equals(Set.of("schema", "ledger", "action_request_id", "query_observation", "root", "cash")), "exact legacy material input required");
            version = InputVersion.LEGACY_V1; kind = Optional.empty();
        } else {
            require(new Text(SCHEMA).equals(input.get("schema"))
                    && input.members().keySet().equals(Set.of("schema", "refresh_kind", "ledger", "action_request_id", "query_observation", "root", "cash")), "exact refresh material input required");
            version = InputVersion.REFRESH_V2;
            kind = Optional.of(RefreshKind.valueOf(text(input.get("refresh_kind"), "material refresh kind")));
        }
        return new Input(version, kind, ConstructionLedgerCodec.decodeLedger(encode(object(input.get("ledger"), "actual original ledger"))),
                text(input.get("action_request_id"), "actual action identity"), object(input.get("query_observation"), "actual native observation"),
                optionalObject(input.get("root"), "root"), optionalObject(input.get("cash"), "cash"));
    }
    public static Obj input(RefreshKind kind, ConstructionLedgerCodec.Ledger ledger, String actionRequestId, Obj queryObservation,
            Optional<Obj> root, Optional<Obj> cash) {
        Obj value = obj("schema", new Text(SCHEMA), "refresh_kind", new Text(Objects.requireNonNull(kind).name()),
                "ledger", ledger.original(), "action_request_id", new Text(actionRequestId),
                "query_observation", queryObservation, "root", root.<Value>map(row -> row).orElse(Nil.INSTANCE),
                "cash", cash.<Value>map(row -> row).orElse(Nil.INSTANCE));
        decode(encode(value)); return value;
    }
    public static Reduced reduce(byte[] originalInput) { return reduce(decode(originalInput)); }
    public static Reduced reduce(Input input) {
        var ledger = input.ledger();
        require(input.refreshKind().filter(kind -> kind == RefreshKind.PREPARED_ZERO_DISPATCH).isEmpty(),
                "prepared zero-dispatch uses its separate canonical-absence reducer");
        boolean completedCash = input.refreshKind().filter(kind -> kind == RefreshKind.COMPLETED_CASH).isPresent();
        require(ledger.pending().isEmpty(), "cold material publication cannot clear or replace an unresolved submit");
        List<ConstructionLedgerCodec.Receipt> matches = new ArrayList<>(ledger.prior()); ledger.applied().ifPresent(matches::add);
        matches = matches.stream().filter(row -> row.identity().actionRequestId().equals(input.actionRequestId())).toList();
        require(matches.size() == 1, "exactly one original applied construction body required");
        var previous = matches.getFirst(); Obj prior = previous.original();
        require(!completedCash || previous.completed(), "completed-cash refresh requires the original completed receipt");
        require(new Bool(true).equals(prior.get("postcondition_verified")) || new Text("observed_mismatched_construction").equals(prior.get("status")),
                "cold follow-up requires already verified material; unknown intent is not adopted");
        Obj queryInput = input.queryObservation();
        require(new Bool(true).equals(queryInput.get("material_receipt")) && new Bool(false).equals(queryInput.get("wartime_observation")), "actual material query mode required");
        Obj query = DriverJson.object(ConstructionQueryCodec.finalizeObservation(encode(queryInput)), ConstructionQueryCodec.MAX_BYTES);
        require(new Text("material_source").equals(query.get("status")), "actual material native source unavailable");
        Obj frame = object(query.get("source_frame"), "actual material source frame"), snapshot = object(queryInput.get("starting_snapshot"), "actual source snapshot");
        require(new Text(previous.identity().episode()).equals(frame.get("episode_run_id"))
                && new IntegerValue(previous.identity().actor()).equals(frame.get("actor_character_id")), "material crossed the original episode or actor");
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
            require(Objects.equals(frame.get(field), snapshot.get(field)), "material source snapshot drift: " + field);
        Obj diagnostic = object(snapshot.get("diagnostics"), "actual process diagnostics");
        BigInteger pid = integer(diagnostic.get("bridge_pid"), "bridge_pid"); positive(pid);
        String birth = text(diagnostic.get("bridge_creation_date"), "actual process birth"); require(!birth.isEmpty(), "actual process birth required");
        Obj source = frame.with("bridge_pid", new IntegerValue(pid)).with("bridge_creation_date", new Text(birth));
        BigInteger date = integer(frame.get("date_raw"), "date_raw"), revision = integer(frame.get("native_revision"), "native_revision"); positive(revision);
        BigInteger preDate = integer(prior.get("pre_date_raw"), "original action date"); require(date.compareTo(preDate) >= 0, "material predates original action");
        BigInteger proof = integer(query.get("proof_epoch"), "actual material proof"); positive(proof);
        Obj world = object(query.get("world"), "actual native material world");
        require(new IntegerValue(previous.identity().actor()).equals(world.get("player_character_id")) && new IntegerValue(revision).equals(world.get("snapshot_revision"))
                && new IntegerValue(date).equals(world.get("date_raw")), "actual material world frame drift");
        BigInteger wallet = integer(world.get("player_gold_raw"), "actual native wallet"); require(wallet.signum() >= 0 && wallet.bitLength() <= 63, "actual wallet range");
        Obj candidate = object(prior.get("candidate"), "original complete candidate");
        Obj wanted = new Text("observed_mismatched_construction").equals(prior.get("status"))
                ? object(prior.get("observed_material_tuple"), "original actually observed different material") : candidate;
        ConstructionLedgerCodec.Tuple target = tuple(wanted);
        List<Obj> active = rows(world.get("active_constructions"), "actual construction rows");
        List<Obj> matchingActive = active.stream().filter(row -> new Bool(true).equals(row.get("active")))
                .filter(row -> new IntegerValue(previous.identity().actor()).equals(row.get("initiator_character_id")))
                .filter(row -> tuple(row).equals(target)).toList();
        boolean completedObserved = bool(world.get("completed_buildings_observed"), "actual completed inventory availability");
        List<Obj> completed = completedObserved ? rows(world.get("completed_buildings"), "actual completed inventory") : List.of();
        if (!completedObserved) require(world.get("completed_buildings") == Nil.INSTANCE, "unobserved completed inventory must remain explicit null");
        List<Obj> matchingCompleted = completed.stream().filter(row -> tuple(row).equals(target)).toList();
        require(matchingActive.size() <= 1 && matchingCompleted.size() <= 1 && (matchingActive.isEmpty() || matchingCompleted.isEmpty()), "duplicate or active/completed material conflict");
        BigInteger beforeWallet = integer(candidate.get("gold_before_raw"), "original wallet"), cost = integer(candidate.get("stock_gold_cost_raw"), "original cost");
        positive(cost); require(beforeWallet.signum() >= 0 && beforeWallet.compareTo(cost) >= 0, "original native quote resources invalid");
        if (!matchingActive.isEmpty() && date.equals(preDate)) require(wallet.equals(beforeWallet.subtract(cost)), "same-date construction wallet debit not observed");
        if (matchingActive.isEmpty() && matchingCompleted.isEmpty()) {
            if (completedObserved && date.compareTo(integer(prior.get("post_date_raw"), "original post date")) <= 0 && wallet.equals(beforeWallet)) {
                Obj observation = obj("status", new Text("restored_before_action"), "postcondition_verified", new Bool(true),
                        "action_request_id", new Text(input.actionRequestId()), "episode_run_id", new Text(previous.identity().episode()),
                        "source_frame", source, "native_query_request_id", query.get("native_query_request_id"), "native_submit_calls", number(0), "replay_allowed", new Bool(false));
                Obj body = replace(ledger, input.actionRequestId(), Optional.empty()).with("last_restore_resolution", observation);
                return new Reduced(Disposition.RESTORED_BEFORE_ACTION, body, observation, Optional.empty());
            }
            require(new Text("applied").equals(prior.get("status")) && new Bool(true).equals(prior.get("postcondition_verified")), "unobserved mismatched material requires original recovery");
            Value held = world.get("directly_held_barony_provinces");
            boolean covered = !(held instanceof Arr) || rows(held, "direct holdings").stream().anyMatch(row -> sameHolding(row, candidate));
            Obj observation = obj("schema", new Text("xar.construction-material-observation-unavailable.v1"), "status", new Text("unavailable"),
                    "read_only", new Bool(true), "business_submission", new Bool(false), "native_submit_calls", number(0),
                    "action_request_id", new Text(input.actionRequestId()), "source_frame", source, "native_query_request_id", query.get("native_query_request_id"),
                    "native_proof_epoch", new IntegerValue(proof), "reason", new Text(covered ? "tracked_tuple_not_observed_in_current_material_projection" : "subject_outside_current_direct_holding_projection"),
                    "retry_not_before_date_raw", new IntegerValue(date.add(MONTH)), "prior_material_receipt_retained", new Bool(true));
            Obj retained = prior.with("completion_last_check_date_raw", new IntegerValue(date)).with("material_observation_unavailable_v1", observation);
            return new Reduced(Disposition.PRIOR_MATERIAL_RETAINED, replace(ledger, input.actionRequestId(), Optional.of(retained)), observation, Optional.of(retained));
        }
        boolean complete = !matchingCompleted.isEmpty();
        Obj provinceInput = obj("schema", new Text(ConstructionProvinceIncomeJson.SCHEMA), "operation", new Text("receipt_income"),
                "world", world, "candidate", wanted, "source_frame", frame, "prior_receipt", prior, "cold_recheck", new Bool(true), "completed", new Bool(complete));
        Obj province = DriverJson.object(ConstructionProvinceIncomeJson.project(encode(provinceInput)), ConstructionQueryCodec.MAX_BYTES);
        Optional<BigInteger> currentRootIncome = input.root().flatMap(root -> income(root, frame));
        Optional<BigInteger> income = currentRootIncome;
        Optional<BigInteger> incomeDate = income.isPresent() ? Optional.of(date) : Optional.empty();
        boolean preserveIncomeFields = false, attachCash = !completedCash;
        if (completedCash) {
            require(income.filter(raw -> raw.bitLength() > 63).isEmpty(), "actual monthly income requires signed64 raw");
            income = ConstructionLedgerCodec.optionalInteger(prior, "observed_player_monthly_gold_income_raw");
            incomeDate = ConstructionLedgerCodec.optionalInteger(prior, "income_observed_date_raw");
            preserveIncomeFields = true;
            if (complete && input.cash().isPresent()) {
                var packet = ConstructionEconomyCodec.decodeCash(encode(input.cash().orElseThrow()));
                require(packet.frame().actor().filter(previous.identity().actor()::equals).isPresent()
                        && packet.frame().snapshotRevision().filter(revision::equals).isPresent()
                        && packet.frame().date().filter(date::equals).isPresent(), "post-completion cash crossed material frame");
                var gross = packet.value(org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.CashField.GROSS);
                attachCash = packet.sameFrameReady() && gross.ready() && gross.raw().isPresent();
                if (income.isEmpty() && attachCash) {
                    income = gross.raw(); incomeDate = packet.frame().date(); preserveIncomeFields = false;
                }
            }
            // The existing material collector also holds a separately verified same-frame ROOT read.
            // This is the original missing-income fallback, never replacement of an earlier observation.
            if (complete && income.isEmpty() && currentRootIncome.isPresent()) {
                income = currentRootIncome; incomeDate = Optional.of(date); preserveIncomeFields = false;
            }
        } else if (complete && previous.completed() && income.isEmpty()) {
            income = ConstructionLedgerCodec.optionalInteger(prior, "observed_player_monthly_gold_income_raw");
            incomeDate = income.isPresent() ? ConstructionLedgerCodec.optionalInteger(prior, "income_observed_date_raw")
                    .or(() -> ConstructionLedgerCodec.optionalInteger(prior, "post_date_raw")) : Optional.empty();
        }
        BigInteger check = date;
        Optional<BigInteger> oldCheck = previous.lastCheck();
        if (!complete && !previous.completed() && oldCheck.filter(old -> old.compareTo(date) <= 0 && date.compareTo(old.add(MONTH)) < 0).isPresent()) check = oldCheck.orElseThrow();
        Obj progress = matchingActive.isEmpty() ? obj("status", new Text("not_active"), "native_remaining_work_raw", Nil.INSTANCE, "native_progress_divisor_raw", Nil.INSTANCE) : progress(matchingActive.getFirst());
        progress = progress.with("snapshot_id", frame.get("snapshot_id")).with("native_revision", new IntegerValue(revision)).with("date_raw", new IntegerValue(date));
        var retainedMembers = new java.util.LinkedHashMap<>(prior.members());
        Value oldUnavailable = retainedMembers.remove("material_observation_unavailable_v1");
        if (oldUnavailable != null) retainedMembers.put("prior_material_observation_unavailable_v1", oldUnavailable);
        Obj updated = new Obj(retainedMembers).with("completion_status", new Text(complete ? "completed" : "in_progress"))
                .with("construction_progress_observation", progress).with("construction_province_income_observation", province)
                .with("completion_last_check_date_raw", new IntegerValue(check))
                .with("completion_observed_date_raw", complete ? prior.get("completion_observed_date_raw") instanceof IntegerValue old ? old : new IntegerValue(date)
                        : prior.get("completion_observed_date_raw") == null ? Nil.INSTANCE : prior.get("completion_observed_date_raw"))
                .with("observed_player_monthly_gold_income_raw", optionalNumber(income)).with("income_observed_date_raw", optionalNumber(incomeDate))
                .with("observed_player_monthly_income_delta_raw", complete ? delta(ConstructionLedgerCodec.optionalInteger(prior, "pre_player_monthly_gold_income_raw"), income) : Nil.INSTANCE)
                .with("observed_province_monthly_income_delta_raw", complete ? delta(provinceValue(prior.get("pre_province_income_observation")), provinceValue(province)) : Nil.INSTANCE)
                .with("post_snapshot_id", frame.get("snapshot_id")).with("post_public_revision", frame.get("revision"))
                .with("post_native_revision", new IntegerValue(revision)).with("post_date_raw", new IntegerValue(date)).with("post_proof_epoch", new IntegerValue(proof))
                .with("post_player_gold_raw", new IntegerValue(wallet)).with("post_bridge_pid", new IntegerValue(pid)).with("post_bridge_creation_date", new Text(birth))
                .with("start_receipt", prior.get("start_receipt") instanceof Obj original ? original : prior)
                .with("readonly_material_recheck", obj("schema", new Text("xar.construction-readonly-material-recheck.v1"), "native_query_request_id", query.get("native_query_request_id"),
                        "source_frame", source, "post_bridge_pid", new IntegerValue(pid), "post_bridge_creation_date", new Text(birth), "post_proof_epoch", new IntegerValue(proof),
                        "original_action_counters_preserved", new Bool(true), "native_submit_calls", number(0)));
        if (preserveIncomeFields) {
            var fields = new java.util.LinkedHashMap<>(updated.members());
            for (String field : List.of("observed_player_monthly_gold_income_raw", "income_observed_date_raw")) {
                if (prior.members().containsKey(field)) fields.put(field, prior.get(field)); else fields.remove(field);
            }
            updated = new Obj(fields);
        }
        if (complete && input.cash().isPresent() && attachCash) {
            Obj cash = input.cash().orElseThrow(); var packet = ConstructionEconomyCodec.decodeCash(encode(cash));
            require(packet.frame().actor().filter(previous.identity().actor()::equals).isPresent()
                    && packet.frame().snapshotRevision().filter(revision::equals).isPresent() && packet.frame().date().filter(date::equals).isPresent(), "post-completion cash crossed material frame");
            var fields = ConstructionEconomyAdapters.completed(ConstructionEconomyCodec.decodeReceipt(encode(updated)), packet, packet.frame().gameVersion());
            Obj composed = DriverJson.object(ConstructionEconomyCodec.encodeCompleted(fields), 4_194_304);
            updated = object(composed.get("receipt"), "shared completed receipt");
        }
        return new Reduced(Disposition.MATERIAL_UPDATED, replace(ledger, input.actionRequestId(), Optional.of(updated)),
                obj("status", new Text("material_updated"), "source_frame", source, "native_query_request_id", query.get("native_query_request_id"), "native_submit_calls", number(0)), Optional.of(updated));
    }

    /** Merge an independently verified start result with the exact original intent; never manufacture intent from an ACK. */
    public static Obj confirmedStart(ConstructionLedgerCodec.Intent intent, Obj effect, Obj actualSnapshot) {
        require(effect.members().keySet().equals(Set.of("status", "postcondition_verified", "completion_status", "action_request_id", "episode_run_id",
                "actor_character_id", "post_player_gold_raw", "post_proof_epoch", "post_native_revision", "post_date_raw", "candidate", "native_query_request_id")),
                "exact registered start material result fields required");
        require(new Text("applied").equals(effect.get("status")) && new Bool(true).equals(effect.get("postcondition_verified")), "independent requested material result required");
        require(List.of(new Text("in_progress"), new Text("completed")).contains(effect.get("completion_status")), "closed actual material completion branch required");
        require(!text(effect.get("native_query_request_id"), "independent material read identity").isEmpty(), "independent material read identity required");
        require(new Text(intent.identity().actionRequestId()).equals(effect.get("action_request_id"))
                && new Text(intent.identity().episode()).equals(effect.get("episode_run_id"))
                && new IntegerValue(intent.identity().actor()).equals(effect.get("actor_character_id"))
                && tuple(object(effect.get("candidate"), "actual material tuple")).equals(intent.identity().candidate()), "material result differs from exact original intent");
        Obj diagnostic = object(actualSnapshot.get("diagnostics"), "actual process diagnostics");
        require(new IntegerValue(intent.source().process().pid()).equals(diagnostic.get("bridge_pid"))
                && new Text(intent.source().process().legacyCreationToken()).equals(diagnostic.get("bridge_creation_date")), "verified start crossed its original Game process");
        Obj receipt = intent.original();
        for (var entry : effect.members().entrySet()) if (!entry.getKey().equals("candidate")) receipt = receipt.with(entry.getKey(), entry.getValue());
        receipt = receipt.with("post_bridge_pid", diagnostic.get("bridge_pid")).with("post_bridge_creation_date", diagnostic.get("bridge_creation_date"));
        require(Objects.equals(actualSnapshot.get("date_raw"), receipt.get("post_date_raw")) && Objects.equals(actualSnapshot.get("native_revision"), receipt.get("post_native_revision"))
                && new Text(intent.identity().episode()).equals(actualSnapshot.get("episode_run_id")), "actual start snapshot frame drift");
        require(new Bool(true).equals(actualSnapshot.get("paused")) && new Bool(true).equals(actualSnapshot.get("map_ready"))
                && new Bool(true).equals(object(actualSnapshot.get("played_character"), "actual start player").get("alive"))
                && new IntegerValue(intent.identity().actor()).equals(object(actualSnapshot.get("played_character"), "actual start player").get("character_id")), "actual start requires original living paused player map");
        var candidate = new NativeConstructionEffects.Candidate(new NativeConstructionEffects.Tuple(intent.identity().candidate().barony().longValueExact(),
                intent.identity().candidate().province().longValueExact(), intent.identity().candidate().building().longValueExact(), intent.identity().candidate().slot().longValueExact()),
                integer(object(intent.original().get("candidate"), "original candidate").get("gold_before_raw"), "wallet"),
                integer(object(intent.original().get("candidate"), "original candidate").get("stock_gold_cost_raw"), "cost"), intent.proofEpoch());
        require(integer(receipt.get("post_proof_epoch"), "material proof").compareTo(candidate.preProofEpoch()) > 0, "start material proof did not advance");
        require(integer(receipt.get("post_native_revision"), "material revision").compareTo(intent.source().nativeRevision()) > 0
                && integer(receipt.get("post_date_raw"), "material date").compareTo(intent.source().dateRaw()) >= 0, "start material requires its later native frame");
        if (new Text("in_progress").equals(effect.get("completion_status")) && effect.get("post_date_raw").equals(intent.original().get("pre_date_raw")))
            require(new IntegerValue(candidate.goldBefore().subtract(candidate.cost())).equals(effect.get("post_player_gold_raw")), "start exact wallet debit not observed");
        ConstructionLedgerCodec.receipt(receipt); return receipt;
    }
    private static Obj replace(ConstructionLedgerCodec.Ledger ledger, String id, Optional<Obj> replacement) {
        if (ledger.applied().filter(row -> row.identity().actionRequestId().equals(id)).isPresent())
            return ledger.original().with("applied", replacement.<Value>map(row -> row).orElse(Nil.INSTANCE));
        List<Value> prior = new ArrayList<>(); int count = 0;
        for (var row : ledger.prior()) if (row.identity().actionRequestId().equals(id)) { count++; replacement.ifPresent(prior::add); } else prior.add(row.original());
        require(count == 1, "original historical receipt identity changed"); return ledger.original().with("applied_prior", new Arr(prior));
    }
    private static Optional<BigInteger> income(Obj root, Obj source) {
        require(new Text("available").equals(root.get("status")), "actual root status unavailable");
        require(Objects.equals(root.get("player_character_id"), source.get("actor_character_id")) && Objects.equals(root.get("snapshot_revision"), source.get("native_revision"))
                && Objects.equals(root.get("date_raw"), source.get("date_raw")), "actual income root frame drift");
        Value value = root.get("player_monthly_gold_income");
        if (value == null || value == Nil.INSTANCE) return Optional.empty();
        Obj row = object(value, "actual monthly income"); require(number(100000).equals(row.get("scale")), "actual monthly income scale drift");
        return ConstructionLedgerCodec.optionalInteger(row, "raw");
    }
    private static Obj progress(Obj row) {
        Optional<BigInteger> work = ConstructionLedgerCodec.optionalInteger(row, "native_remaining_work_raw"), divisor = ConstructionLedgerCodec.optionalInteger(row, "native_progress_divisor_raw");
        return obj("status", new Text(work.isPresent() && divisor.isPresent() ? "observed" : "unavailable"), "native_remaining_work_raw", optionalNumber(work), "native_progress_divisor_raw", optionalNumber(divisor));
    }
    private static Optional<BigInteger> provinceValue(Value raw) {
        if (!(raw instanceof Obj row) || !new Text("observed").equals(row.get("status"))) return Optional.empty();
        return ConstructionLedgerCodec.optionalInteger(row, "native_province_monthly_income_raw");
    }
    private static ConstructionLedgerCodec.Tuple tuple(Obj row) { return new ConstructionLedgerCodec.Tuple(integer(row.get("barony_title_id"), "barony"), integer(row.get("province_id"), "province"), integer(row.get("building_type_id"), "building"), integer(row.get("slot_index"), "slot")); }
    private static boolean sameHolding(Obj a, Obj b) { return Objects.equals(a.get("barony_title_id"), b.get("barony_title_id")) && Objects.equals(a.get("province_id"), b.get("province_id")); }
    private static List<Obj> rows(Value raw, String field) { List<Obj> result = new ArrayList<>(); for (Value value : array(raw, field)) result.add(object(value, field)); return List.copyOf(result); }
    private static Optional<Obj> optionalObject(Value value, String field) { require(value != null, "required nullable field missing: " + field); return value == Nil.INSTANCE ? Optional.empty() : Optional.of(object(value, field)); }
    private static Value delta(Optional<BigInteger> before, Optional<BigInteger> after) { return before.isPresent() && after.isPresent() ? new IntegerValue(after.orElseThrow().subtract(before.orElseThrow())) : Nil.INSTANCE; }
    private static Value optionalNumber(Optional<BigInteger> value) { return value.<Value>map(IntegerValue::new).orElse(Nil.INSTANCE); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static void positive(BigInteger value) { require(value.signum() > 0, "positive exact material integer required"); }
}
