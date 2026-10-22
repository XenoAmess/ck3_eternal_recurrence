package org.xar.ck3.control.score;

import java.util.List;
import java.util.Objects;

/** Fixed order and weights: L/E/M/U/D/H. No missing-domain renormalization. */
public record DomainScores(ScoreInterval land, ScoreInterval economy, ScoreInterval military,
        ScoreInterval stability, ScoreInterval dynasty, ScoreInterval heirs) {
    public DomainScores {
        Objects.requireNonNull(land); Objects.requireNonNull(economy); Objects.requireNonNull(military);
        Objects.requireNonNull(stability); Objects.requireNonNull(dynasty); Objects.requireNonNull(heirs);
    }
    public List<ScoreInterval> ordered() { return List.of(land, economy, military, stability, dynasty, heirs); }
}
