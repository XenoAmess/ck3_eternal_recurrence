package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.FormalReleaseProducer;

/** Actual managed-Git -> private pure producer -> existing LS quote. Physical admitted writer is covered by its owner. */
final class FormalReleaseProductionChainTest {
    @Test void actualCleanTaggedProducerFeedsTheExistingSoleBootstrapQuote()throws Exception{
        try(var fixture=FormalReleaseTestFixture.create(FormalReleaseProducer.Mode.PUBLISH_RELEASE)){
            var actual=fixture.actual();var phase=RootProfileBootstrapInputs.formalRelease(actual);
            assertTrue(phase.quote().stream().anyMatch(row->row.fileName().endsWith("/gfx/interface/icons/traits/_stars_10.dds")));
            actual.verifyOriginals();assertEquals(actual.outputRoot(),phase.assetRoot());
            assertEquals(actual.payload().size(),phase.quote().size());
            assertEquals(actual.outputDirectories(),phase.outputDirectories());
            assertEquals("v1.0.2",actual.manifest().gitTag());
            assertTrue(actual.payload().stream().noneMatch(row->row.target().toString().contains("xar_acceptance_events")));
            assertTrue(actual.payload().stream().filter(row->row.role()==FormalReleaseProducer.PayloadRole.PRODUCTION_FILE)
                    .anyMatch(row->row.target().getFileName().toString().equals("actual.txt")&&new String(row.bytes(),StandardCharsets.UTF_8).equals("real=yes\n")));
            assertFalse(Files.exists(actual.request().productionRoot()));
            assertFalse(Files.exists(actual.request().manifestTarget()));
        }
    }
    @Test void actualPrivatePreparationRejectsSourceMutationBeforeAnyPayloadWrite()throws Exception{
        try(var fixture=FormalReleaseTestFixture.create(FormalReleaseProducer.Mode.PROFILE_STAGING)){
            var actual=fixture.actual();assertNull(actual.manifest().gitTag());
            Files.writeString(actual.request().sourceRoot().resolve("common/scripted_effects/actual.txt"),"changed=yes\n",StandardCharsets.UTF_8);
            assertThrows(IOException.class,actual::verifyOriginals);
            assertFalse(Files.exists(actual.request().productionRoot()));
        }
    }
    @Test void actualDirtyWorktreeIsReobservedBeforeTheSoleWriter()throws Exception{
        try(var fixture=FormalReleaseTestFixture.create(FormalReleaseProducer.Mode.PUBLISH_RELEASE)){
            var actual=fixture.actual();
            Files.writeString(actual.request().repository().resolve("untracked-after-prepare.txt"),"actual dirty worktree\n",StandardCharsets.UTF_8);
            actual.verifyOriginals();
            assertThrows(IOException.class,()->actual.verifyGitCurrent(org.xar.ck3.control.build.FormalReleaseGit.Phase.BEFORE_WRITE));
            assertFalse(Files.exists(actual.request().productionRoot()));
            assertFalse(Files.exists(actual.request().manifestTarget()));
        }
    }
    @Test void actualTagAtHeadIsReobservedBeforeTheSoleWriter()throws Exception{
        try(var fixture=FormalReleaseTestFixture.create(FormalReleaseProducer.Mode.PUBLISH_RELEASE)){
            var actual=fixture.actual();fixture.removeReleaseTagForTest();actual.verifyOriginals();
            assertThrows(IOException.class,()->actual.verifyGitCurrent(org.xar.ck3.control.build.FormalReleaseGit.Phase.BEFORE_WRITE));
            assertFalse(Files.exists(actual.request().productionRoot()));
            assertFalse(Files.exists(actual.request().manifestTarget()));
        }
    }
}

