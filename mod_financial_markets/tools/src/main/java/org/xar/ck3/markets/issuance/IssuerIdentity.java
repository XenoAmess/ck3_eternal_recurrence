package org.xar.ck3.markets.issuance;

import java.util.Objects;
import java.util.Set;

/** A political succession changes control, never the asset ID or its obligations. */
public record IssuerIdentity(String permanentId, Kind kind, String boundEntityId,
                             String controllerId, String originalControllerId,
                             long nextIssueDay, long unpaidDebtCents, Set<String> disclosedDefaults) {
    public enum Kind { PERSONAL, HOUSE, DYNASTY, POLITY, FAITH, COMPANY, CONCEPT }
    public IssuerIdentity {
        requireId(permanentId); requireId(boundEntityId); requireId(controllerId); requireId(originalControllerId);
        Objects.requireNonNull(kind, "kind");
        if (nextIssueDay < 0 || unpaidDebtCents < 0) throw new IllegalArgumentException("negative issue day or debt");
        disclosedDefaults = Set.copyOf(disclosedDefaults);
    }
    public IssuerIdentity succession(String successorId) {
        requireId(successorId);
        return new IssuerIdentity(permanentId, kind, boundEntityId, successorId, originalControllerId,
                nextIssueDay, unpaidDebtCents, disclosedDefaults);
    }
    public boolean mayAct(String actorId, Set<String> authorizedEntityIds) {
        return controllerId.equals(actorId) && authorizedEntityIds.contains(boundEntityId);
    }
    public boolean mayIssue(long currentDay, int activePersonalIssues, int pendingApplications) {
        if (currentDay < 0 || activePersonalIssues < 0 || pendingApplications < 0) throw new IllegalArgumentException("negative admission input");
        return currentDay >= nextIssueDay && pendingApplications == 0
                && (kind != Kind.PERSONAL || activePersonalIssues == 0);
    }
    private static void requireId(String id) {
        if (id == null || id.isBlank() || id.length() > 128) throw new IllegalArgumentException("nonblank bounded identity required");
    }
}
