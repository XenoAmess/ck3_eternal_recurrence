package org.xar.ck3.control.wave2.events.interactionbefore;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.events.interactionfallback.InteractionFallbackCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence.Frame;

/** Current primary reply channel derived from the exact stock GUI condition and same-frame native routing. */
public final class CurrentInteractionPresentation {
    public static final String SCHEMA = "xar.pending-primary-reply-presentation/v1";
    public static final String CAPTURE_SCHEMA="xar.pending-interaction-left-reply/v1";
    public static final String CAPTURE_POLICY="user-authorized-native-gui-left-reply";
    private static final Set<String> STEPS = Set.of("reject-pending-character-interaction", "accept-pending-character-interaction",
            "acknowledge-pending-character-interaction", "block-pending-character-interaction");
    private CurrentInteractionPresentation() { }

    public enum Channel { NORMAL_REPLY, AUTO_ACCEPT_ACK }
    public enum Reply {
        REJECT("reject", "left", 0, "reject_button", "GetAnswerRejectText"),
        ACCEPT("accept", "right", 1, "accept_button", "GetAnswerAcceptText"),
        ACKNOWLEDGE("acknowledge", "only", 0, "acknowledge_button", "GetAnswerAcknowledgeText");
        private final String action, position, widget, label;
        private final int index;
        Reply(String action, String position, int index, String widget, String label) {
            this.action=action;this.position=position;this.index=index;this.widget=widget;this.label=label;
        }
        public String step() { return action+"-pending-character-interaction"; }
    }
    public record Legality(boolean available, Boolean allowed, String reason) {
        public boolean legal() { return available && Boolean.TRUE.equals(allowed); }
    }
    public record Button(Reply reply, Legality legality, boolean reachable) {
        public Button { Objects.requireNonNull(reply);Objects.requireNonNull(legality); }
    }
    public record Presentation(Frame binding, NativePendingInteraction.Pending pending, String definition,
            BigInteger definitionHash, int recipient, int intermediary, Channel channel,
            List<Button> buttons, List<String> availableSteps, Legality block) {
        public Presentation {
            Objects.requireNonNull(binding);Objects.requireNonNull(pending);Objects.requireNonNull(definition);
            Objects.requireNonNull(definitionHash);Objects.requireNonNull(channel);Objects.requireNonNull(block);
            buttons=List.copyOf(buttons);availableSteps=List.copyOf(availableSteps);
            require(!definition.isEmpty()&&definition.length()<=512&&definitionHash.signum()>=0&&definitionHash.bitLength()<=32,
                    "bounded current interaction definition required");
            NativeCharacterId.of(recipient);
            if (intermediary != -1) NativeCharacterId.of(intermediary);
            require(pending.autoAcceptNotification()==(channel==Channel.AUTO_ACCEPT_ACK),"typed presentation channel differs");
            require(buttons.stream().map(Button::reply).toList().equals(channel==Channel.NORMAL_REPLY?List.of(Reply.REJECT,Reply.ACCEPT):List.of(Reply.ACKNOWLEDGE)),
                    "typed presentation must retain the actual primary GUI channel order");
            require(availableSteps.size()<=4&&Set.copyOf(availableSteps).size()==availableSteps.size()
                    &&availableSteps.stream().allMatch(STEPS::contains),"bounded actual pending capabilities required");
        }
    }

    /** Data projection only. The caller verifies the actual GUI source through TrustedEventSourceContext first. */
    public static Presentation derive(JsonNode binding, NativePendingInteraction.Pending pending,
            JsonNode originalContext, Set<String> actualActionSteps) {
        ObjectNode nativeContext=object(originalContext);
        Objects.requireNonNull(pending);Objects.requireNonNull(actualActionSteps);
        Frame frame=InteractionBeforeComposer.frame(binding);
        require(frame.paused()&&frame.mapReady(),"current pending presentation requires the paused map");
        require("available".equals(text(nativeContext,"status")),"available original pending context required");
        require(integer(nativeContext.get("pending_interaction_id"),Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact()==pending.instanceId()
                &&number(nativeContext,"snapshot_revision").equals(frame.nativeRevision())
                &&number(nativeContext,"date_raw").equals(frame.dateRaw()),"pending presentation crossed native instance/frame");
        ObjectNode roles=object(nativeContext.get("roles")),routing=object(nativeContext.get("routing")),definition=object(nativeContext.get("definition"));
        int sender=character(roles,"actor_character_id"),recipient=character(roles,"recipient_character_id");
        int intermediary=integer(roles.get("intermediary_character_id"),Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact();
        require(pending.senderCharacterId().equals(BigInteger.valueOf(sender)),"pending presentation sender/roles differ from original snapshot");
        int kind=integer(routing.get("kind"),0,2).intValueExact();String responder=kind==1?"intermediary":"recipient";
        require(character(routing,"played_character_id")==frame.actorCharacterId()
                &&frame.actorCharacterId()==(kind==1?intermediary:recipient)
                &&responder.equals(text(routing,"current_responder_role"))&&responder.equals(text(routing,"reply_execution_channel"))
                &&bool(routing.get("local_route")),"pending presentation is not routed to this actual player");
        require(bool(routing.get("auto_accept_notification"))==pending.autoAcceptNotification(),"pending presentation notification channel changed");
        String key=text(definition,"canonical_key");require(!key.isEmpty()&&key.length()<=512&&key.chars().noneMatch(c->c<0x20),"bounded native interaction definition required");
        BigInteger hash=integer(definition.get("deterministic_key_hash"),BigInteger.ZERO,new BigInteger("4294967295"));
        List<String> steps=actualActionSteps.stream().filter(STEPS::contains).sorted().toList();
        ObjectNode legalities=object(nativeContext.get("legality"));List<Button> buttons=new ArrayList<>();
        for(Reply reply:pending.autoAcceptNotification()?List.of(Reply.ACKNOWLEDGE):List.of(Reply.REJECT,Reply.ACCEPT))
            buttons.add(new Button(reply,legality(legalities.get(reply.action)),steps.contains(reply.step())));
        return new Presentation(frame,pending,key,hash,recipient,intermediary,
                pending.autoAcceptNotification()?Channel.AUTO_ACCEPT_ACK:Channel.NORMAL_REPLY,buttons,steps,legality(legalities.get("block")));
    }

    public static ObjectNode encode(Presentation actual) {
        Objects.requireNonNull(actual);ObjectNode root=StrictJson.object().put("schema",SCHEMA)
                .put("basis","source_condition_with_same_native_routing").put("gui_source",InteractionFallback.GUI_SOURCE)
                .put("gui_sha256",InteractionFallback.GUI_SHA256).put("channel",actual.channel().name())
                .put("primary_channel_complete",true).put("full_widget_visibility_observed",false);
        root.set("binding",frame(actual.binding()));root.set("native_pending",NativePendingInteraction.encode(Optional.of(actual.pending())));
        root.putObject("definition").put("canonical_key",actual.definition()).put("deterministic_key_hash",actual.definitionHash());
        root.putObject("participants").put("sender_character_id",actual.pending().senderCharacterId())
                .put("recipient_character_id",actual.recipient()).put("intermediary_character_id",actual.intermediary())
                .put("played_character_id",actual.binding().actorCharacterId());
        var steps=root.putArray("available_steps");actual.availableSteps().forEach(steps::add);
        var buttons=root.putArray("buttons");
        for(Button button:actual.buttons()) {
            Reply reply=button.reply();ObjectNode row=buttons.addObject().put("button",reply.widget).put("action",reply.action)
                    .put("step",reply.step()).put("position",reply.position).put("rendered_index",reply.index).put("shown",true)
                    .put("source_visibility",actual.channel()==Channel.NORMAL_REPLY?"Not(CharacterInteractionNotificationWindow.IsAutoAcceptNotification)":"CharacterInteractionNotificationWindow.IsAutoAcceptNotification")
                    .put("label_source_expression","CharacterInteractionNotificationWindow."+reply.label)
                    .putNull("resolved_label").put("native_legal",button.legality().legal()).put("action_reachable",button.reachable());
            if(button.legality().available()&&button.legality().allowed()!=null)row.put("enabled",button.legality().allowed());else row.putNull("enabled");
            row.set("native_legality",legality(button.legality()));
        }
        // The native reply validator does not expose CanPotentiallyBeBlocked. Preserve that actual gap.
        ObjectNode block=root.putObject("supplemental_block").put("button","block_button")
                .put("source_visibility","CharacterInteractionNotificationWindow.CanPotentiallyBeBlocked")
                .putNull("shown").putNull("rendered_index").put("visibility_observed",false)
                .put("action_reachable",actual.availableSteps().contains("block-pending-character-interaction"));
        block.set("native_legality",legality(actual.block()));return root;
    }

    /** Old capture bytes remain legacy. Current source-reviewed submissions require this complete typed projection. */
    public static Optional<Presentation> validateCapture(JsonNode originalCapture,String selectedStep,boolean currentRequired) {
        ObjectNode capture=object(originalCapture);
        require(CAPTURE_SCHEMA.equals(text(capture,"schema"))&&"pending_character_interaction".equals(text(capture,"kind"))
                &&CAPTURE_POLICY.equals(text(capture,"policy")),"source-reviewed native reply capture contract differs");
        ObjectNode gui=object(capture.get("gui_binding"));JsonNode original=gui.get("current_presentation");
        if(original==null) { require(!currentRequired,"current native reply presentation is absent");return Optional.empty(); }
        ObjectNode current=object(original);
        require(InteractionFallback.GUI_SOURCE.equals(text(gui,"source"))&&InteractionFallback.GUI_SHA256.equals(text(gui,"sha256")),"current GUI source pin differs");
        ObjectNode authoredGui=gui.deepCopy();authoredGui.remove("current_presentation");
        require(jsonEquals(authoredGui,InteractionFallbackCodec.guiBinding()),"captured source GUI fields/order changed");
        JsonNode originalOptions=capture.get("reply_options"),normal=authoredGui.get("normal_channel"),contextLegality=object(capture.get("context")).get("legality");
        require(originalOptions!=null&&originalOptions.isArray()&&originalOptions.size()==2,"complete source normal reply vector required");
        for(int i=0;i<2;i++) {
            ObjectNode row=object(originalOptions.get(i)),sourceRow=object(normal.get(i));ObjectNode sourceFields=row.deepCopy();sourceFields.remove("native_legality");
            require(jsonEquals(sourceFields,sourceRow),"original reply button source fields changed");
            JsonNode legalityToken=contextLegality==null?null:contextLegality.get(text(sourceRow,"action"));
            require(row.has("native_legality")&&jsonEquals(row.get("native_legality"),legalityToken==null?com.fasterxml.jackson.databind.node.NullNode.instance:legalityToken),
                    "captured reply legality differs from actual context");
        }
        NativePendingInteraction.Pending pending=NativePendingInteraction.decode(current.path("native_pending")).orElseThrow(()->new IllegalArgumentException("current native pending evidence absent"));
        require(integer(capture.get("pending_interaction_id"),Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact()==pending.instanceId(),"capture native instance differs");
        JsonNode rawSteps=current.get("available_steps");require(rawSteps!=null&&rawSteps.isArray()&&rawSteps.size()<=4,"exact bounded native reply capability list required");
        var steps=new java.util.HashSet<String>();for(JsonNode token:rawSteps)require(token.isTextual()&&STEPS.contains(token.textValue())&&steps.add(token.textValue()),"native reply capability list is malformed");
        Presentation expected=derive(object(capture.get("binding")),pending,object(capture.get("context")),steps);
        require(jsonEquals(current,encode(expected)),"current native reply presentation changed its original fields/types/source");
        Button first=expected.buttons().getFirst();ObjectNode selection=object(capture.get("selection"));
        require(first.reply().action.equals(text(selection,"action"))&&first.reply().widget.equals(text(selection,"button"))&&first.reply().step().equals(text(selection,"step"))
                &&first.reply().position.equals(text(selection,"position"))
                &&integer(selection.get("rendered_index"),0,0).signum()==0
                &&bool(selection.get("native_legal"))==first.legality().legal()
                &&bool(selection.get("action_reachable"))==first.reachable(),"capture selected a different native GUI reply");
        if(selectedStep!=null)require(first.reply().step().equals(selectedStep)&&first.legality().legal()&&first.reachable(),"disabled or unavailable left reply cannot become a submission");
        return Optional.of(expected);
    }

    public static Presentation requireSubmission(JsonNode capture,String actualStep,int originalInstance) {
        Objects.requireNonNull(actualStep);
        Presentation actual=validateCapture(capture,actualStep,true).orElseThrow();
        require(actual.pending().instanceId()==originalInstance,"submission changed the original full pending identity");
        return actual;
    }

    private static ObjectNode frame(Frame f) {
        return StrictJson.object().put("snapshot_id",f.snapshotId()).put("revision",f.revision()).put("native_revision",f.nativeRevision())
                .put("date_raw",f.dateRaw()).put("episode_run_id",f.episodeRunId()).put("paused",f.paused()).put("map_ready",f.mapReady())
                .put("actor_character_id",f.actorCharacterId()).put("connection_generation",f.connectionGeneration()).put("bridge_pid",f.bridgePid());
    }
    private static Legality legality(JsonNode original) {
        if(original==null||original.isNull())return new Legality(false,null,null);
        ObjectNode row=StrictJson.object(original,Set.of("status","allowed","reason"));String status=text(row,"status");
        require(Set.of("available","unavailable","invalid").contains(status),"unknown native reply legality status");
        JsonNode allowed=row.get("allowed"),reason=row.get("reason");require(allowed!=null&&(allowed.isNull()||allowed.isBoolean()),"native reply allowed must be boolean or null");
        require(reason!=null&&(reason.isNull()||reason.isTextual()),"native reply reason must be string or null");
        return new Legality(status.equals("available"),allowed.isNull()?null:allowed.booleanValue(),reason.isNull()?null:reason.textValue());
    }
    private static ObjectNode legality(Legality actual) {
        ObjectNode result=StrictJson.object().put("available",actual.available());
        if(actual.allowed()==null)result.putNull("allowed");else result.put("allowed",actual.allowed());
        if(actual.reason()==null)result.putNull("reason");else result.put("reason",actual.reason());return result;
    }
    private static boolean jsonEquals(JsonNode first,JsonNode second) {
        return RetainedJson.parse(StrictJson.canonical(first)).equals(RetainedJson.parse(StrictJson.canonical(second)));
    }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode,"current native presentation object required");return (ObjectNode)value; }
    private static String text(JsonNode row,String field) { return StrictJson.text(row.get(field)); }
    private static BigInteger number(JsonNode row,String field) { return integer(row.get(field),BigInteger.ZERO,StrictJson.UINT64_MAX); }
    private static int character(JsonNode row,String field) { return NativeCharacterId.fromJson(row.get(field)).value(); }
    private static BigInteger integer(JsonNode value,long low,long high) { return integer(value,BigInteger.valueOf(low),BigInteger.valueOf(high)); }
    private static BigInteger integer(JsonNode value,BigInteger low,BigInteger high) { return StrictJson.integer(value,low,high); }
    private static boolean bool(JsonNode value) { require(value!=null&&value.isBoolean(),"native presentation boolean required");return value.booleanValue(); }
    private static void require(boolean condition,String message) { StrictJson.require(condition,message); }
}
