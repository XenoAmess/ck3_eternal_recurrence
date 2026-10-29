package org.xar.ck3.control.nativebridge.capabilities.interactions;

import org.xar.ck3.control.contracts.NativeCharacterId;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Instant;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionArguments.contextCharacterId;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionArguments.nullableContextCharacterId;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionArguments.contextCharacterIds;

/** One complete Driver projection for ordinary, pending and guardian consumers. Missing data is unavailable. */
public final class RootInteractionContextProjection implements OrdinaryInitiationPreparation.SourceBoundProjection {
    private final Build qualifiedBuild;
    /** Root passes the build from its actual, source-qualified EXE metadata. */
    public RootInteractionContextProjection(Build actualQualifiedBuild) { qualifiedBuild=Objects.requireNonNull(actualQualifiedBuild); }
    @Override public Context project(Complete actual, Instant deadline) {
        Objects.requireNonNull(actual); Objects.requireNonNull(deadline);
        need(deadline.isAfter(actual.observedAt()), "interaction observation deadline predates its actual publication");
        JsonNode n=OpportunityJson.toNode(actual.semantic()); JsonNode player=field(n,"played_character");
        need(!player.isNull(),"interaction context requires an actual played character");
        JsonNode hello=field(field(n,"diagnostics"),"hello");
        // Retained Driver evidence has two explicit original formats; mixed profiles are rejected.
        boolean expected=hello.has("expected_ck3_version") || hello.has("expected_ck3_sha256");
        boolean nativeProfile=hello.has("game_version") || hello.has("executable_sha256");
        need(expected != nativeProfile,"ambiguous or absent original hello build profile");
        String version=expected?text(hello,"expected_ck3_version"):text(hello,"game_version");
        String sha=expected?text(hello,"expected_ck3_sha256"):text(hello,"executable_sha256");
        need(version.equals(qualifiedBuild.version()) && sha.equalsIgnoreCase(qualifiedBuild.sha256()),"interaction build differs from Root qualified EXE");
        need(contextCharacterId(player,"character_id")==actual.identity().frame().identity().player().longValueExact(),"interaction actor differs from actual Driver identity");
        JsonNode event=field(n,"active_event"), pendingNode=field(n,"pending_character_interaction");
        need(event.isNull() || event.isObject(),"actual event missing/null/value distinction changed");
        PendingSummary pending=NativePendingInteraction.decode(pendingNode).map(value->new PendingSummary(
                new PendingId(value.instanceId()),
                NativeCharacterId.of(value.senderCharacterId()),
                value.autoAcceptNotification())).orElse(null);
        List<Long> spouses=contextCharacterIds(player,"spouse_ids");
        need(new HashSet<>(spouses).size()==spouses.size(),"duplicate actual spouse identity");
        var controls=new ControlFrame(bool(n,"paused"),bool(n,"map_ready"),bool(player,"alive"),integer(n,"speed",0,5),
                nullablePlayer(n,"local_player_id"),contextCharacterId(n,"episode_character_id"),text(n,"episode_run_id"),!event.isNull(),pending,
                nullableContextCharacterId(player,"betrothed_id"),spouses);
        need(controls.episodeRunId().equals(actual.identity().frame().episodeRunId())
                && controls.episodeCharacterId()==actual.identity().frame().identity().player().longValueExact(),"interaction episode identity is unreconciled");
        return new Context(actual.identity(),actual.source(),actual.sessionId(),actual.connectionGeneration(),qualifiedBuild,deadline,controls);
    }
    public static void requireExact(Complete actual, Context supplied) {
        var projected=new RootInteractionContextProjection(supplied.build()).project(actual,supplied.deadline());
        need(projected.equals(supplied),"interaction context is not the exact full Driver projection");
    }
}
