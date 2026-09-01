package com.xenoamess.kaishek.runtime;

import java.util.Objects;

public record DeadlineTicket(String caseId, long serial, long revision, long dueEpochDay, ScopeRef owner, ScopeRef subject) {
    public DeadlineTicket {
        if (caseId == null || caseId.isBlank() || serial < 0 || revision < 0 || dueEpochDay < 0) throw new IllegalArgumentException("invalid deadline ticket");
        Objects.requireNonNull(owner); Objects.requireNonNull(subject);
    }
    public static DeadlineTicket forBinding(CaseBinding binding, long dueEpochDay) {
        Objects.requireNonNull(binding); return new DeadlineTicket(binding.caseId(), binding.serial(), binding.revision(), dueEpochDay, binding.owner(), binding.subject());
    }
    public boolean isDue(long epochDay) { return epochDay >= dueEpochDay; }
    public boolean isFresh(CaseBinding binding) {
        return binding != null && caseId.equals(binding.caseId()) && serial == binding.serial() && revision == binding.revision()
            && owner.equals(binding.owner()) && subject.equals(binding.subject());
    }
    public ExecutionStatus validate(CaseBinding binding, long epochDay) {
        if (!isFresh(binding)) return ExecutionStatus.STALE;
        return isDue(epochDay) ? ExecutionStatus.SUCCESS : ExecutionStatus.INVALID;
    }
}
