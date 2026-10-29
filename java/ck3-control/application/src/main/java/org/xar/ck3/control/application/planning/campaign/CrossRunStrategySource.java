package org.xar.ck3.control.application.planning.campaign;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The original persisted state and the actual lifecycle result view have explicitly different fields. */
public final class CrossRunStrategySource {
    private CrossRunStrategySource() { }
    private static final Set<String> REQUIRED=Set.of("format_version","mode","continue_as_heir_after_death","episodes","next_run_plan");
    private static final Set<String> OPTIONAL=Set.of("updated_at","path","recorded_episode");
    /** path and recorded_episode are producer result metadata, never alternate persistent state names. */
    public record View(CrossRunPlanning.State state,Optional<String> path,Optional<CrossRunPlanning.Episode> recordedEpisode) {
        public View {
            Objects.requireNonNull(state);Objects.requireNonNull(path);Objects.requireNonNull(recordedEpisode);path.ifPresent(StrictJson::text);
            recordedEpisode.ifPresent(episode->StrictJson.require(state.episodes().stream().filter(value->value.runId().equals(episode.runId())).toList().equals(List.of(episode)),
                    "actual recorded episode must be the identical retained state entry"));
        }
    }
    public static View decode(byte[] original) {
        Objects.requireNonNull(original);StrictJson.require(original.length>0&&original.length<=CrossRunPlanning.MAX_BYTES,"bounded actual strategy source required");
        return decode(OpportunityJson.object(OpportunityJson.parse(original),"actual one-life strategy source"));
    }
    public static View decode(Obj original) {
        Objects.requireNonNull(original);StrictJson.require(original.members().keySet().containsAll(REQUIRED)
                && original.members().keySet().stream().allMatch(key->REQUIRED.contains(key)||OPTIONAL.contains(key)),"exact persisted state/result metadata contract required");
        Obj persisted=new Obj(original.members().entrySet().stream().filter(entry->!entry.getKey().equals("path")&&!entry.getKey().equals("recorded_episode"))
                .collect(java.util.stream.Collectors.toUnmodifiableMap(java.util.Map.Entry::getKey,java.util.Map.Entry::getValue)));
        CrossRunPlanning.State state=CrossRunPlanning.decodeState(OpportunityJson.encode(persisted));
        Optional<String> path=original.get("path")==null?Optional.empty():Optional.of(OpportunityJson.text(original.get("path"),"path"));
        Optional<CrossRunPlanning.Episode> recorded=Optional.empty();
        if(original.get("recorded_episode")!=null) {
            Obj actual=OpportunityJson.object(original.get("recorded_episode"),"actual recorded episode");
            Obj one=persisted.with("episodes",new Arr(List.of(actual)));
            recorded=Optional.of(CrossRunPlanning.decodeState(OpportunityJson.encode(one)).episodes().getFirst());
        }
        return new View(state,path,recorded);
    }
    /** The lifecycle reducer already recorded the life. This validates its persisted result and explicit metadata. */
    public static CrossRunPlanning.State terminal(CrossRunPlanning.State previous,String episodeId,Obj actualTerminal,Instant producedAt) {
        Objects.requireNonNull(previous);StrictJson.text(episodeId);Objects.requireNonNull(actualTerminal);Objects.requireNonNull(producedAt);
        CrossRunPlanning.Terminal terminal=CrossRunPlanning.parseTerminal(actualTerminal);
        StrictJson.require(terminal.score()!=Nil.INSTANCE,"actual final score must be present before publishing cross-run state");
        StrictJson.require(actualTerminal.get("settlement_status") instanceof Text status&&status.value().equals("complete"),"canonical terminal must carry its complete actual settlement");
        View view=decode(OpportunityJson.object(actualTerminal.get("cross_run_strategy"),"actual lifecycle-produced cross-run strategy"));
        CrossRunPlanning.Episode recorded=view.recordedEpisode().orElseThrow(()->new IllegalArgumentException("actual lifecycle recorded_episode result is absent"));
        StrictJson.require(recorded.runId().equals(episodeId)&&recorded.finishedAt().equals(producedAt)
                && recorded.terminalReason().equals(terminal.reason())&&recorded.technicalSettlementHandoff()==terminal.technicalSettlementHandoff()
                && recorded.score().equals(terminal.score())&&view.state().updatedAt().equals(Optional.of(producedAt)),
                "actual terminal score/subject/time differs from the lifecycle's recorded state");
        List<CrossRunPlanning.Episode> expected=new ArrayList<>(previous.episodes().stream().filter(value->!value.runId().equals(episodeId)).toList());expected.add(recorded);
        StrictJson.require(view.state().episodes().equals(expected)&&view.state().nextRunPlan().equals(CrossRunPlanning.nextRunPlan(recorded.achievements())),
                "actual lifecycle state changed another retained life or its derived next-run plan");
        return view.state();
    }
    /** Replays the sole shared history reducer as validation; this never publishes or records another life. */
    public static CrossRunPlanning.State terminal(CrossRunPlanning.State previous,String episodeId,
            List<Obj> completeOriginalBefore,Obj actualTerminal,Instant producedAt) {
        CrossRunPlanning.State published=terminal(previous,episodeId,actualTerminal,producedAt);
        CrossRunPlanning.State expected=CrossRunPlanning.recordScoredTerminal(previous,episodeId,
                List.copyOf(completeOriginalBefore),actualTerminal,producedAt);
        StrictJson.require(published.equals(expected),
                "actual lifecycle strategy differs from the sole reducer replay of its complete original history");
        return published;
    }
}
