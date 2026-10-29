package org.xar.ck3.control.wave2.military.warexitterms;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.HashSet;
import java.util.List;

/** Complete observed claim-CB preview. This value has no action or qualification authority. */
public record WarExitTerms(int warId, int dateRaw, int casusBelliDatabaseIndex,
                          int primaryAttackerCharacterId, int primaryDefenderCharacterId,
                          int claimantCharacterId, List<Integer> targetTitleIds, List<Claim> claims,
                          List<ResourceAmount> primaryResourceBalances, List<MonthlyGoldIncome> primaryMonthlyGoldIncome,
                          Outcome whitePeace, Outcome attackerDefeat, String nativeContractSha256) {
    public static final int SCALE = 100_000;
    public static final String SLICE = "claim_cb_exit_terms_v2";
    public static final String CAPABILITY = "game.command.query-war-termination-exit-terms-v2-N";
    public static final String QUERY_PREFIX = "query-war-termination-exit-terms-v2-";
    /** Original loaded-effect truce preview AV at CK3 RVA 0x334C668 remains unresolved. */
    public static final boolean PRODUCTION_ENABLED = false;

    public WarExitTerms {
        positive(warId); positive(primaryAttackerCharacterId); positive(primaryDefenderCharacterId);
        positive(claimantCharacterId);
        require(casusBelliDatabaseIndex >= 0, "nonnegative CB database index required");
        require(primaryAttackerCharacterId != primaryDefenderCharacterId, "distinct primary characters required");
        targetTitleIds = List.copyOf(targetTitleIds);
        require(!targetTitleIds.isEmpty() && targetTitleIds.size() <= 4096
                && new HashSet<>(targetTitleIds).size() == targetTitleIds.size(), "unique nonempty declared titles required");
        targetTitleIds.forEach(WarExitTerms::positive);
        claims = List.copyOf(claims);
        require(claims.size() == targetTitleIds.size(), "complete declared target claims required");
        for (int index = 0; index < claims.size(); index++) {
            require(claims.get(index).titleId() == targetTitleIds.get(index), "claim title ordering required");
        }
        primaryResourceBalances = List.copyOf(primaryResourceBalances);
        validateResources(primaryResourceBalances, primaryAttackerCharacterId, primaryDefenderCharacterId, true);
        primaryMonthlyGoldIncome = List.copyOf(primaryMonthlyGoldIncome);
        require(primaryMonthlyGoldIncome.size() == 2
                && primaryMonthlyGoldIncome.get(0).characterId() == primaryAttackerCharacterId
                && primaryMonthlyGoldIncome.get(1).characterId() == primaryDefenderCharacterId,
                "ordered complete primary monthly income required");
        require(whitePeace != null && attackerDefeat != null, "both complete outcomes required");
        Disposition whitePeaceDisposition = claims.stream().anyMatch(row -> !row.strong())
                ? Disposition.RETAIN_AND_STRENGTHEN_WEAK : Disposition.RETAIN_ALREADY_STRONG;
        validateOutcome(whitePeace, whitePeaceDisposition, primaryAttackerCharacterId, primaryDefenderCharacterId, dateRaw, false);
        validateOutcome(attackerDefeat, Disposition.REMOVE_DECLARED_TARGET_CLAIMS,
                primaryAttackerCharacterId, primaryDefenderCharacterId, dateRaw, true);
        require(whitePeace.cbPrestigeFactorRaw() == attackerDefeat.cbPrestigeFactorRaw(), "same CB factor across outcomes required");
        require(nativeContractSha256 != null && nativeContractSha256.matches("[0-9A-F]{64}"), "uppercase native contract SHA256 required");
    }

    public record Claim(int titleId, boolean strong, boolean implicit) {
        public Claim { positive(titleId); }
        public String state() { return (strong ? "strong_" : "weak_") + (implicit ? "implicit" : "explicit"); }
    }

    public enum ResourceKind {
        GOLD("gold"), PRESTIGE("prestige"), PRESTIGE_EXPERIENCE("prestige_experience"),
        PIETY("piety"), PIETY_EXPERIENCE("piety_experience"), LEGITIMACY("legitimacy"), STRESS("stress");
        private final String wire;
        ResourceKind(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static ResourceKind fromWire(String value) {
            for (ResourceKind candidate : values()) { if (candidate.wire.equals(value)) { return candidate; } }
            throw new org.xar.ck3.control.contracts.ContractViolationException("unknown resource kind");
        }
    }

    public record ResourceAmount(int characterId, ResourceKind resourceKind, long raw) {
        public ResourceAmount { positive(characterId); require(resourceKind != null, "typed resource required"); }
    }
    public record MonthlyGoldIncome(int characterId, long raw) {
        public MonthlyGoldIncome { positive(characterId); }
    }
    public enum Disposition {
        RETAIN_AND_STRENGTHEN_WEAK("retain_and_strengthen_weak"),
        RETAIN_ALREADY_STRONG("retain_no_strength_change_already_strong"),
        REMOVE_DECLARED_TARGET_CLAIMS("remove_declared_target_claims");
        private final String wire;
        Disposition(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Disposition fromWire(String value) {
            for (Disposition candidate : values()) { if (candidate.wire.equals(value)) { return candidate; } }
            throw new org.xar.ck3.control.contracts.ContractViolationException("unknown claim disposition");
        }
    }
    public enum DecisionStatus {
        STATUS_ZERO(0), STATUS_ONE(1), REJECT(2);
        private final int raw;
        DecisionStatus(int raw) { this.raw = raw; }
        public int raw() { return raw; }
        public static DecisionStatus fromRaw(int raw) {
            for (DecisionStatus candidate : values()) { if (candidate.raw == raw) { return candidate; } }
            throw new org.xar.ck3.control.contracts.ContractViolationException("recipient decision unavailable or invalid");
        }
    }
    public record RecipientResponse(long acceptanceRaw, DecisionStatus decisionStatus, boolean wouldAcceptNow, boolean autoAccept) {
        public RecipientResponse {
            require(decisionStatus != null && wouldAcceptNow == (decisionStatus != DecisionStatus.REJECT),
                    "recipient response must match native decision status");
        }
    }
    public record GoldTransfer(int fromCharacterId, int toCharacterId, long raw) {
        public GoldTransfer { positive(fromCharacterId); positive(toCharacterId); require(raw >= 0, "nonnegative gold transfer required"); }
    }
    public record Truce(int ownerCharacterId, int towardCharacterId, int evaluatedDays, int currentDateRaw, int expiryDateRaw) {
        public Truce {
            positive(ownerCharacterId); positive(towardCharacterId);
            long expiry = (long) currentDateRaw + 24L * evaluatedDays;
            require(evaluatedDays >= 0 && expiry >= Integer.MIN_VALUE && expiry <= Integer.MAX_VALUE
                    && expiryDateRaw == expiry, "native directed truce expiry inconsistent");
        }
    }
    public record PrisonerRelease(int jailerCharacterId, int prisonerCharacterId, String reason) {
        public PrisonerRelease {
            positive(jailerCharacterId); positive(prisonerCharacterId);
            require(jailerCharacterId != prisonerCharacterId && reason != null && reason.matches("[a-z0-9_]{1,80}"),
                    "distinct prisoner/jailer and bounded ASCII reason required");
        }
    }
    public record Outcome(Disposition claimDisposition, RecipientResponse recipientResponse, long cbPrestigeFactorRaw,
                          List<GoldTransfer> primaryGoldTransfers, List<ResourceAmount> primaryResourceDeltas,
                          Truce truce, List<PrisonerRelease> prisonerReleases) {
        public Outcome {
            require(claimDisposition != null && recipientResponse != null && truce != null && cbPrestigeFactorRaw >= 0,
                    "complete observed outcome required");
            primaryGoldTransfers = List.copyOf(primaryGoldTransfers);
            primaryResourceDeltas = List.copyOf(primaryResourceDeltas);
            prisonerReleases = List.copyOf(prisonerReleases);
            require(prisonerReleases.size() <= 64 && new HashSet<>(prisonerReleases).size() == prisonerReleases.size(),
                    "bounded unique prisoner releases required");
        }
    }

    private static void validateOutcome(Outcome outcome, Disposition disposition, int attacker, int defender, int date, boolean defeat) {
        require(outcome.claimDisposition() == disposition, "claim disposition disagrees with observed claims/outcome");
        require(outcome.primaryGoldTransfers().size() == (defeat ? 1 : 0), "complete outcome-specific gold transfers required");
        if (defeat) {
            GoldTransfer transfer = outcome.primaryGoldTransfers().get(0);
            require(transfer.fromCharacterId() == attacker && transfer.toCharacterId() == defender, "attacker-to-defender gold required");
        }
        validateResources(outcome.primaryResourceDeltas(), attacker, defender, false);
        require(outcome.truce().ownerCharacterId() == attacker && outcome.truce().towardCharacterId() == defender
                && outcome.truce().currentDateRaw() == date, "same-date attacker-to-defender truce required");
    }
    private static void validateResources(List<ResourceAmount> rows, int attacker, int defender, boolean balances) {
        int kinds = balances ? 7 : 6;
        require(rows.size() == 2 * kinds, "complete primary resource matrix required");
        for (int index = 0; index < rows.size(); index++) {
            ResourceAmount row = rows.get(index);
            require(row.characterId() == (index < kinds ? attacker : defender)
                    && row.resourceKind() == ResourceKind.values()[index % kinds + (balances ? 0 : 1)],
                    "stable attacker/defender resource ordering required");
        }
    }
    static void positive(int value) { require(value > 0, "positive int32 identity required"); }
}
