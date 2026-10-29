package org.xar.ck3.control.application.ritecreation;

import java.math.BigDecimal;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact original .4 candidate data. These types do not qualify the native controller or a business outcome. */
public final class RiteCreationContract {
    public static final String STEP="player-rite-creation-action-v1", CAPABILITY="player_rite_creation_action_v1";
    public static final String SCHEMA="ck3_12004_rite_creation_action_v1", BACKEND="ck3-1.20.0.4-native-rite-creation-action-v1";
    public static final String VERSION="1.20.0.4", SHA="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final BigInteger U64=new BigInteger("18446744073709551615");
    private RiteCreationContract() { }
    public static RiteCreation parseRiteCreation(String value){for(RiteCreation op:RiteCreation.values())if(op.wire().equals(value))return op;throw new IllegalArgumentException("unknown original Rite operation: "+value);}
    public enum NameField { NAME,ADJECTIVE,ADHERENT,ADHERENT_PLURAL,DESCRIPTION;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);} public static NameField parse(String value){return named(values(),value);}
    }
    public enum Outcome { CREATE_FAITH,CREATE_RITE,EDIT_RITE;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);} public static Outcome parse(String value){return named(values(),value);}
    }
    public enum ModalStage { UNKNOWN,NONE,CONFIRMATION;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);} public static ModalStage parse(String value){return named(values(),value);}
    }
    public enum ModalKind { CREATE,EDIT;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);} public static ModalKind parse(String value){return named(values(),value);}
    }
    private static <E extends Enum<E>> E named(E[] values,String text){for(E v:values)if(v.name().toLowerCase(java.util.Locale.ROOT).equals(text))return v;throw new IllegalArgumentException("unknown finite Rite value: "+text);}
    public record SourceRite(long value){public SourceRite{need(value>=0&&value<0xffff_ffffL,"complete uint32 source Rite; sentinel is not an ID");}}
    public record Definition(String value){public Definition{need(value!=null&&value.matches("[a-z0-9_]{1,128}"),"bounded original definition selector required");}}
    public record Identity(String value){public Identity{need(value!=null&&value.matches("[0-9a-f]{64}"),"original native SHA256 identity required");}}
    public record ActionId(String value){public ActionId{need(value!=null&&value.matches("rite-action-[0-9a-f]{32}"),"original public Rite action identity required");}}
    public record Query(BigInteger expectedRevision,SourceRite source){public Query{revision(expectedRevision);Objects.requireNonNull(source);}}
    public record Execute(BigInteger expectedRevision,SourceRite source,Write action){public Execute{revision(expectedRevision);Objects.requireNonNull(source);Objects.requireNonNull(action);}}
    public record Collect(ActionId action,Duration timeout){public Collect{Objects.requireNonNull(action);Objects.requireNonNull(timeout);need(!timeout.isNegative()&&timeout.compareTo(Duration.ofSeconds(30))<=0,"bounded original result collection timeout required");}}
    public sealed interface Write permits OpenCreate,OpenEdit,CoreTenet,Doctrine,Name,Prepare,Confirm {RiteCreation operation();}
    public record OpenCreate() implements Write{public RiteCreation operation(){return RiteCreation.OPEN_CREATE_DRAFT;}}
    public record OpenEdit() implements Write{public RiteCreation operation(){return RiteCreation.OPEN_EDIT_CURRENT_RITE_DRAFT;}}
    public record CoreTenet(int slot,Definition tenet) implements Write{public CoreTenet{need(slot>=0&&slot<64,"original core slot0..63 required");Objects.requireNonNull(tenet);}public RiteCreation operation(){return RiteCreation.SELECT_CORE_TENET;}}
    public record Doctrine(Definition group,Definition doctrine) implements Write{public Doctrine{Objects.requireNonNull(group);Objects.requireNonNull(doctrine);}public RiteCreation operation(){return RiteCreation.SELECT_DOCTRINE;}}
    public record Name(NameField field,String text) implements Write{
        public Name{Objects.requireNonNull(field);Objects.requireNonNull(text);int bytes=text.getBytes(StandardCharsets.UTF_8).length;
            need(bytes<=(field==NameField.DESCRIPTION?4096:256),"bounded original UTF8 name input required");
            for(int i=0;i<text.length();i++){char c=text.charAt(i);if(Character.isHighSurrogate(c)){need(i+1<text.length()&&Character.isLowSurrogate(text.charAt(++i)),"unpaired UTF16 surrogate cannot enter native UTF8");continue;}need(!Character.isLowSurrogate(c),"unpaired UTF16 surrogate cannot enter native UTF8");need(c>=32||(field==NameField.DESCRIPTION&&(c==10||c==9)),"original name control character forbidden");}}
        public RiteCreation operation(){return RiteCreation.SET_NAME_FIELD;}
    }
    public record Prepare(Identity preview,Outcome outcome) implements Write{public Prepare{Objects.requireNonNull(preview);Objects.requireNonNull(outcome);}public RiteCreation operation(){return RiteCreation.PREPARE_CONFIRMATION;}}
    public record Confirm(Identity preview,Outcome outcome) implements Write{public Confirm{Objects.requireNonNull(preview);Objects.requireNonNull(outcome);}public RiteCreation operation(){return RiteCreation.CONFIRM_ONCE;}}
    public sealed interface Scope permits EpisodeScope,ManagedScope {String kind();String stableKey();}
    public record EpisodeScope(String episode) implements Scope{public EpisodeScope{StrictJson.text(episode);}public String kind(){return "actual_episode_v1";}public String stableKey(){return episode;}}
    /** Construct only after the actual managed-campaign binding verifier has validated the persistent state directory. */
    public record ManagedScope(String verifiedCanonicalStateDirectory) implements Scope{public ManagedScope{StrictJson.text(verifiedCanonicalStateDirectory);}public String kind(){return "managed_campaign_state_v1";}public String stableKey(){return verifiedCanonicalStateDirectory;}}
    public interface ExpectedNativeBinding {BigInteger nativeRevision();BigInteger connectionGeneration();BigInteger nativeActor();BigInteger nativeDate();}
    public record Frame(String snapshotId,BigInteger publicRevision,BigInteger nativeRevision,BigInteger connectionGeneration,
            long gamePid,int actor,int dateRaw,Scope scope) implements ExpectedNativeBinding{
        public Frame{StrictJson.text(snapshotId);revision(publicRevision);revision(nativeRevision);revision(connectionGeneration);need(gamePid>0&&gamePid<=0xffff_ffffL&&actor>0,"actual positive PID/played Character required");Objects.requireNonNull(scope);}
        public BigInteger nativeActor(){return BigInteger.valueOf(actor);}
        public BigInteger nativeDate(){return BigInteger.valueOf(dateRaw);}
    }
    public record NativeFields(RiteCreation operation,SourceRite source,Optional<Write> write,Optional<String> originalProtocolRequestId){
        public NativeFields{Objects.requireNonNull(operation);Objects.requireNonNull(source);Objects.requireNonNull(write);Objects.requireNonNull(originalProtocolRequestId);
            need((operation==RiteCreation.PREVIEW)==write.isEmpty(),"only preview has no finite mutation");write.ifPresent(v->need(v.operation()==operation,"Rite operation/selector mismatch"));
            need((operation==RiteCreation.CONFIRM_ONCE)==originalProtocolRequestId.isPresent(),"only final confirm binds its actual original protocol request ID");
            originalProtocolRequestId.ifPresent(v->need(v.matches("[A-Za-z0-9_.:-]{1,128}"),"native original control request ID required"));}
        public static NativeFields preview(SourceRite source){return new NativeFields(RiteCreation.PREVIEW,source,Optional.empty(),Optional.empty());}
    }
    public record NativeFrame(BigInteger connectionGeneration,BigInteger nativeRevision,BigInteger captureEpoch,int dateRaw,int actor){
        public NativeFrame{revision(connectionGeneration);revision(nativeRevision);revision(captureEpoch);need(actor>0,"actual played Character required");}
    }
    public record Names(Optional<String> name,Optional<String> adjective,Optional<String> adherent,Optional<String> adherentPlural,Optional<String> description){
        public Names{Objects.requireNonNull(name);Objects.requireNonNull(adjective);Objects.requireNonNull(adherent);Objects.requireNonNull(adherentPlural);Objects.requireNonNull(description);}
        public boolean complete(){return List.of(name,adjective,adherent,adherentPlural,description).stream().allMatch(Optional::isPresent);}
    }
    public record Tenet(int slot,Definition key){public Tenet{need(slot>=0&&slot<64,"bounded native tenet slot required");Objects.requireNonNull(key);}}
    public record SelectedDoctrine(Definition group,Definition key){public SelectedDoctrine{Objects.requireNonNull(group);Objects.requireNonNull(key);}}
    public record Draft(boolean observed,Optional<SourceRite> source,Optional<SourceRite> faith,Optional<SourceRite> actorFaith,
            Optional<Outcome> outcome,Names names,Optional<List<Tenet>> tenets,Optional<List<SelectedDoctrine>> doctrines){
        public Draft{Objects.requireNonNull(source);Objects.requireNonNull(faith);Objects.requireNonNull(actorFaith);Objects.requireNonNull(outcome);Objects.requireNonNull(names);
            tenets=Objects.requireNonNull(tenets).map(List::copyOf);doctrines=Objects.requireNonNull(doctrines).map(List::copyOf);
            need(tenets.map(v->v.size()<=64).orElse(true)&&doctrines.map(v->v.size()<=64).orElse(true),"bounded original selected row extent required");}
    }
    public record Modal(boolean observed,ModalStage stage,Optional<ModalKind> kind,Optional<Boolean> active,Optional<Boolean> sameDraft,Optional<Boolean> nativeCanAccept){
        public Modal{Objects.requireNonNull(stage);Objects.requireNonNull(kind);Objects.requireNonNull(active);Objects.requireNonNull(sameDraft);Objects.requireNonNull(nativeCanAccept);}}
    public record FullCan(boolean observed,Optional<Boolean> create,Optional<Boolean> edit,Optional<String> createReason,Optional<String> editReason){
        public FullCan{Objects.requireNonNull(create);Objects.requireNonNull(edit);Objects.requireNonNull(createReason);Objects.requireNonNull(editReason);need(observed||create.isEmpty()&&edit.isEmpty()&&createReason.isEmpty()&&editReason.isEmpty(),"unobserved original full Can must remain null");}}
    public record Quote(boolean observed,Optional<Long> cost,Optional<Long> missing,Optional<Boolean> enough){
        public Quote{Objects.requireNonNull(cost);Objects.requireNonNull(missing);Objects.requireNonNull(enough);need(observed||cost.isEmpty()&&missing.isEmpty()&&enough.isEmpty(),"unobserved original quote must remain null");}}
    public record Result(RiteCreation operation,boolean available,String status,Optional<String> unavailableReason,NativeFrame frame,
            Draft draft,Modal modal,FullCan can,Quote quote,Optional<Identity> preview,boolean completePayload,boolean originalWriterInputs,
            Optional<BigInteger> nativeCommandTextBytes,Optional<Identity> nativeCommandTextSha,
            boolean attempted,boolean invoked,boolean verificationPending,boolean mayHaveQueued,Optional<String> originalProtocolActionId,RawJson original){
        public Result{Objects.requireNonNull(operation);StrictJson.text(status);Objects.requireNonNull(unavailableReason);Objects.requireNonNull(frame);Objects.requireNonNull(draft);Objects.requireNonNull(modal);Objects.requireNonNull(can);Objects.requireNonNull(quote);Objects.requireNonNull(preview);Objects.requireNonNull(nativeCommandTextBytes);Objects.requireNonNull(nativeCommandTextSha);Objects.requireNonNull(originalProtocolActionId);Objects.requireNonNull(original);
            need(available==unavailableReason.isEmpty()&&unavailableReason.map(v->!v.isEmpty()).orElse(true),"available/unavailable original diagnostic differs");need(!invoked||attempted,"original dispatch flags disagree");need(!mayHaveQueued||operation==RiteCreation.CONFIRM_ONCE,"preparing modal cannot queue final writer");
            if(preview.isPresent())need(completePayload&&originalWriterInputs&&nativeCommandTextBytes.filter(v->v.signum()>0).isPresent()&&nativeCommandTextSha.isPresent()&&draft.observed()&&draft.source().isPresent()&&draft.faith().isPresent()&&draft.actorFaith().isPresent()&&draft.outcome().isPresent()&&draft.names().complete()&&draft.tenets().isPresent()&&draft.doctrines().isPresent()&&modal.observed()&&modal.stage()!=ModalStage.UNKNOWN&&can.observed()&&can.create().isPresent()&&can.edit().isPresent()&&quote.observed()&&quote.cost().isPresent()&&quote.missing().isPresent()&&quote.enough().isPresent(),"native preview identity lacks original complete inputs");}
        public boolean knownNoDispatch(){return !attempted&&!mayHaveQueued;}
        public boolean businessOutcomeVerified(){return false;}public boolean actionReady(){return false;}
        public void requireFinalPreview(Confirm requested){need(operation==RiteCreation.PREVIEW&&preview.equals(Optional.of(requested.preview()))&&draft.outcome().equals(Optional.of(requested.outcome()))
                &&modal.stage()==ModalStage.CONFIRMATION&&modal.active().orElse(false)&&modal.sameDraft().orElse(false)&&modal.nativeCanAccept().orElse(false)
                &&(requested.outcome()==Outcome.EDIT_RITE?can.edit():can.create()).orElse(false),"actual post-modal preview/full Can proof is unavailable");}
    }
    public static void revision(BigInteger value){need(value!=null&&value.signum()>0&&value.compareTo(U64)<=0,"positive exact uint64 revision/generation required");}
    public static Duration timeout(BigDecimal seconds){need(seconds!=null&&seconds.signum()>=0&&seconds.compareTo(BigDecimal.valueOf(30))<=0,"bounded finite original collect timeout required");return Duration.ofNanos(seconds.movePointRight(9).setScale(0,java.math.RoundingMode.CEILING).longValueExact());}
    public static void need(boolean value,String reason){if(!value)throw new IllegalArgumentException(reason);}
}
