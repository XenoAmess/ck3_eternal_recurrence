package org.xar.ck3.control.wave2.military.holycost;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.Choice;

/** Selected native CB-only cost evidence. Neither a total declaration price nor execution permission. */
public record HolyCostObservation(Build build, String originalExecutableSha256, boolean available,
                                  String unavailableReason, BigInteger captureEpoch, BigInteger publicRevision,
                                  BigInteger nativeRevision, int dateRaw, int playedCharacterId, String declarationId,
                                  Choice selectedDeclaration, ContextRoles roles, Boolean finalCanSend, CBOnlyQuote cbCost) {
    public HolyCostObservation {
        Objects.requireNonNull(build); Objects.requireNonNull(originalExecutableSha256);
        Objects.requireNonNull(selectedDeclaration); Objects.requireNonNull(roles); Objects.requireNonNull(cbCost);
    }
    public enum Build {
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String gameVersion;
        private final String executableSha256;
        Build(String gameVersion, String executableSha256) { this.gameVersion = gameVersion; this.executableSha256 = executableSha256; }
        public String gameVersion() { return gameVersion; }
        public String executableSha256() { return executableSha256; }
    }
    public record ContextRoles(Integer actorCharacterId, Integer recipientCharacterId,
                               Integer additionalRoleCharacterId, Integer claimantCharacterId,
                               Boolean recipientUsesNativeFallback, Boolean additionalRoleUsesNativeFallback,
                               Boolean claimantUsesNativeFallback) { }
    public enum Resource {
        GOLD("gold"), PRESTIGE("prestige"), PIETY("piety"), RENOWN("renown"), INFLUENCE("influence"),
        HERD("herd"), TREASURY("treasury"), TREASURY_OR_GOLD("treasury_or_gold"), MERIT("merit"), BARTER_GOODS("barter_goods");
        private final String wire;
        Resource(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public sealed interface CBOnlyQuote permits KnownQuote, UnavailableQuote { boolean available(); }
    public record KnownQuote(List<Long> resourceCostsRaw) implements CBOnlyQuote {
        public KnownQuote {
            resourceCostsRaw = List.copyOf(resourceCostsRaw);
            if (resourceCostsRaw.size() != Resource.values().length) throw new IllegalArgumentException("ten resource costs required");
        }
        @Override public boolean available() { return true; }
        public long cost(Resource resource) { return resourceCostsRaw.get(resource.ordinal()); }
    }
    public record UnavailableQuote(String unavailableReason) implements CBOnlyQuote {
        public UnavailableQuote {
            if (unavailableReason == null || unavailableReason.isEmpty()) throw new IllegalArgumentException("unavailable CB quote reason required");
        }
        @Override public boolean available() { return false; }
    }
    public enum TotalCost { UNKNOWN }
    public TotalCost totalCost() { return TotalCost.UNKNOWN; }
}
