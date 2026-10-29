package org.xar.ck3.control.nativebridge.capabilities.gui;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;

/** Original independent presentation diagnostics. No timer worker, gameplay claim, or action authority is introduced. */
public final class GuiCameraCapabilities {
    public record Binding(long requestSequence,int actor,int submittedDateRaw,String episodeRunId){public Binding{
        GuiJson.need(requestSequence>=0&&requestSequence<=0xffff_fffeL&&(requestSequence&1)==0&&episodeRunId!=null&&!episodeRunId.isBlank(),"original even camera request/source binding required");org.xar.ck3.control.contracts.NativeCharacterId.of(actor);}}
    public record RealmStatus(boolean requested,Optional<NativeCameraObserver.Capture> nativeActual){public RealmStatus{nativeActual=Objects.requireNonNull(nativeActual);}public boolean sameFrameGameplayClaim(){return false;}}
    public record FollowStatus(Optional<NativeCameraObserver.Capture> latestActual,boolean workerInstalled,String detail){public FollowStatus{latestActual=Objects.requireNonNull(latestActual);}}
    public enum PreparationStatus { PRESENTATION_ACTION_ORIGIN_NOT_INSTALLED }
    public record RealmPreparation(PreparationStatus status,GuiModels.Context source,boolean queryOnly,String actualChannel){ }
    private final NativeCameraObserver observer;private LandedProvinceIndex installedIndex;
    public GuiCameraCapabilities(NativeCameraObserver observer){this.observer=Objects.requireNonNull(observer);}
    /** Preparation truthfully stops before submission until the sole host authority owns mmap presentation origins. */
    public RealmPreparation center_map_on_player_realm_v1(GuiModels.Context source,boolean queryOnly){
        GuiJson.need(source.build()==GuiModels.Build.CROZIER4,"original realm enumeration requires exact .4 executable");
        return new RealmPreparation(PreparationStatus.PRESENTATION_ACTION_ORIGIN_NOT_INSTALLED,source,queryOnly,"Local\\XarCK3CameraPresentationV1-{actualPid}");
    }
    public RealmStatus realm_camera_status_v1(Optional<Binding> originalSubmission)throws IOException{
        if(originalSubmission.isEmpty())return new RealmStatus(false,Optional.empty());Binding binding=originalSubmission.orElseThrow();var capture=observer.observe();
        if(capture.isEmpty())return new RealmStatus(true,Optional.empty());var actual=capture.orElseThrow().result();
        boolean bound=actual.requestSequence()==binding.requestSequence()&&actual.actor()==binding.actor()
            &&actual.dateRaw()>=binding.submittedDateRaw()&&actual.dateRaw()<=(long)binding.submittedDateRaw()+7*24;
        if(actual.status()==NativeCameraObserver.Status.SETTLED)bound&=actual.cameraPostconditionVerified();
        return new RealmStatus(true,bound?capture:Optional.empty());
    }
    public FollowStatus auto_camera_follow_status()throws IOException{return new FollowStatus(observer.observe(),false,"readonly actual mapping sample; original automatic follow worker and tracking tail are not installed");}
    public synchronized void bind_war_hotspot_camera_index(LandedProvinceIndex actualInstalledIndex)throws IOException{Objects.requireNonNull(actualInstalledIndex).verifySourcesUnchanged();installedIndex=actualInstalledIndex;}
    public synchronized Optional<LandedProvinceIndex> installedWarHotspotIndex(){return Optional.ofNullable(installedIndex);}
}

