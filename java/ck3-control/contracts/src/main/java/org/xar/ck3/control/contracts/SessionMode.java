package org.xar.ck3.control.contracts;

import java.math.BigInteger;
import java.util.Objects;

/** Explicit session identity DATA. Root's private physical allocator proof remains a separate required authority. */
public sealed interface SessionMode permits SessionMode.OneLife, SessionMode.NativeCampaign, SessionMode.UnboundData {
    record OneLife(BigInteger episodeCharacterId, String episodeRunId) implements SessionMode {
        public OneLife {
            Objects.requireNonNull(episodeCharacterId); Objects.requireNonNull(episodeRunId);
            StrictJson.require(episodeCharacterId.signum() > 0 && !episodeRunId.isEmpty(), "bound one-life character/run required");
        }
    }
    record NativeCampaign(ManagedCampaignRunBinding binding) implements SessionMode {
        public NativeCampaign { Objects.requireNonNull(binding); }
    }
    /** Original null/null episode state also occurs before one-life binding; it never identifies a managed campaign. */
    enum UnboundData implements SessionMode { INSTANCE }
}
