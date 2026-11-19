package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
final class SavedPlanningConstructorProvenanceTest {
    @Test void ordinarySavedWithoutOriginalImportDoesNotRequestTheMenuConstructorLane(){
        assertFalse(RootInstalledCatalog.requiresNativeCampaignConstructor(false,InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,false));
    }
    @Test void actualOriginalSavedImportStillSelectsTheStrictExistingFrozenConstructorLane(){
        assertTrue(RootInstalledCatalog.requiresNativeCampaignConstructor(false,InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,true));
    }
    @Test void privateRestoredOriginStillSelectsTheExistingRestoredConstructorLane(){
        assertTrue(RootInstalledCatalog.requiresNativeCampaignConstructor(true,InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,false));
        assertTrue(RootInstalledCatalog.requiresNativeCampaignConstructor(true,InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,true));
    }
    @Test void otherLifecycleDataCannotSelectThisSavedConstructorLaneAndNullIsRefused(){
        for(var lifecycle:InitialEpisodePolicy.Lifecycle.values())if(lifecycle!=InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED){
            assertFalse(RootInstalledCatalog.requiresNativeCampaignConstructor(false,lifecycle,false));
            assertFalse(RootInstalledCatalog.requiresNativeCampaignConstructor(false,lifecycle,true));
        }
        assertThrows(NullPointerException.class,()->RootInstalledCatalog.requiresNativeCampaignConstructor(false,null,false));
    }
    @Test void actualMaterializedSavedConfigurationAndGenuineCatalogDoNotClaimMenuStart()throws Exception {
        var type=RootInstalledCatalog.class;var location=java.nio.file.Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
        assertTrue(java.nio.file.Files.isRegularFile(location),"genuine whole archive required");assertTrue(java.nio.file.Files.size(location)>1_048_576);
        var input=new org.xar.ck3.control.contracts.ExactRef(System.getProperty("xar.saved.planning.configuration.path"),
                Long.parseLong(System.getProperty("xar.saved.planning.configuration.bytes")),System.getProperty("xar.saved.planning.configuration.sha256"));
        var actual=RootSavedRuntimeConfigurationInputs.readSource(input);
        assertEquals(InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,actual.initialPolicy().kind());
        assertTrue(actual.initialPolicy().isMaterializedSaved());
        assertFalse(RootInstalledCatalog.requiresNativeCampaignConstructor(false,actual.initialPolicy().kind(),false));
    }
}
