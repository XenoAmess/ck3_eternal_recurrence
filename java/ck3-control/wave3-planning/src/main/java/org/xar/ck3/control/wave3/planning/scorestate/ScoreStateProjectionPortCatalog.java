package org.xar.ck3.control.wave3.planning.scorestate;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.score.DomainScores;

/** Existing state scoring in the one host, using the shared decimal model and 64 KiB caps. */
public final class ScoreStateProjectionPortCatalog implements ProjectionPortCatalog {
    public ScoreStateProjectionPortCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new ProjectionPort<StateScoreInput, DomainScores>() {
            @Override public ProjectionOperation operation() { return ProjectionOperation.CAMPAIGN_STATE_SCORE; }
            @Override public int inputMaximumBytes() { return 65536; }
            @Override public int outputMaximumBytes() { return 65536; }
            @Override public StateScoreInput decode(byte[] raw) {
                StateScoreInput input = StateScoreCodec.decode(raw);
                StateScore.validateInput(input);
                return input;
            }
            @Override public DomainScores project(StateScoreInput input) { return StateScore.evaluate(input); }
            @Override public byte[] encode(DomainScores result) { return StateScoreCodec.encode(result); }
        }));
    }
}
