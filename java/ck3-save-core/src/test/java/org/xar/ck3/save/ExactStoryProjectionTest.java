package org.xar.ck3.save;

import static org.junit.jupiter.api.Assertions.*;
import java.io.StringReader;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.SaveContracts.*;

final class ExactStoryProjectionTest {
    private static ProjectionSelection story(String id) { return ProjectionSelection.exactStory("selected_story", id, 512 * 1024, true); }
    private static Selection selection(ProjectionSelection p) { return new Selection(List.of(), List.of(p), true, false, List.of()); }
    @Test void exactStoryPathUsesActualStreamingCaptureAndMetadata() throws Exception {
        Projection result = new SaveStream(new StringReader("meta_data={version=\"1.21.0\" save_game_version=19} stories={active={1={unselected=\"" + "x".repeat(600000) + "\"} 50331650={story_cycle=xfm_news_entry value=7}}}"), selection(story("50331650"))).read();
        assertEquals(1, result.projections().size()); assertEquals(List.of("stories", "active", "50331650"), result.projections().getFirst().path());
        assertEquals("xfm_news_entry", result.projections().getFirst().ast().atom("story_cycle", ""));
        assertTrue(result.selectedTokenBytes() < 1024); assertEquals(ScopeKind.METADATA, result.scopes().getFirst().kind());
    }
    @Test void zeroAndLastValidUint32AreExactWithoutBroadNumericPaths() {
        assertEquals("0", story("0").path().getLast()); assertEquals("4294967294", story("4294967294").path().getLast());
        for (String id : List.of("-1", "01", "1.0", "true", "false", "null", "story_name", "", "4294967295", "4294967296", "18446744073709551616"))
            assertThrows(IllegalArgumentException.class, () -> story(id), "exactStory factory must reject id=" + id);
        assertThrows(IllegalArgumentException.class, () -> story(null), "exactStory factory must reject null ID");
        assertThrows(IllegalArgumentException.class, () -> new ProjectionSelection("bad", ProjectionKind.OTHER, List.of("characters", "active", "1"), 1, 1024, true));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionSelection("bad", ProjectionKind.OTHER, List.of("stories", "active", "1", "variables"), 1, 1024, true));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionSelection("bad", ProjectionKind.GLOBAL_VARIABLES, List.of("stories", "active", "1"), 1, 1024, true));
        assertThrows(IllegalArgumentException.class, () -> new ProjectionSelection("bad", ProjectionKind.OTHER, List.of("stories", "active", "1"), 2, 1024, true));
    }
    @Test void oldTableCensusAndNamedProjectionDomainsStayStrict() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> new TableSelection(ScopeKind.ACTOR, List.of("stories", "active", "1"), List.of(), true));
        assertThrows(IllegalArgumentException.class, () -> new Selection(List.of(), List.of(), true, true, List.of(List.of("stories", "active", "1"))));
        assertEquals(List.of("meta_data"), new ProjectionSelection("metadata", ProjectionKind.OTHER, List.of("meta_data"), 1, 512 * 1024, true).path());
        // "true" remains a literal named segment in the pre-existing generic
        // projection contract. It is not an exact Story identity request.
        ProjectionSelection legacy = new ProjectionSelection("legacy_named", ProjectionKind.OTHER, List.of("stories", "active", "true"), 1, 1024, true);
        Projection legacyRead = new SaveStream(new StringReader("meta_data={} stories={active={true={literal=kept}}}"), selection(legacy)).read();
        assertEquals("kept", legacyRead.projections().getFirst().ast().atom("literal", ""), "legacy named OTHER true path must retain its old reader semantics");
        assertThrows(IllegalArgumentException.class, () -> new ProjectionSelection("large", ProjectionKind.OTHER, List.of("stories", "active", "1"), 1, 512 * 1024 + 1, true));
    }
    @Test void sharedStrictJsonRejectsNonTextNumericPathComponents() throws Exception {
        String json = new String(SaveJson.write(story("1")), java.nio.charset.StandardCharsets.UTF_8);
        for (String lexical : List.of("1", "1.0", "true", "null")) {
            String bad = json.replace("\"1\"", lexical);
            assertThrows(java.io.IOException.class, () -> SaveJson.read(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8), ProjectionSelection.class),
                    "generic Projection JSON must reject non-text path component=" + lexical);
        }
        assertEquals(story("1"), SaveJson.read(json.getBytes(java.nio.charset.StandardCharsets.UTF_8), ProjectionSelection.class));
    }
    @Test void duplicateMissingMalformedAndOversizeSelectedRecordRemainErrors() {
        for (String source : List.of("meta_data={} stories={active={1={} 1={}}}", "meta_data={} stories={active={2={}}}",
                "meta_data={} stories={active={1={broken=}}}", "stories={active={1={}}}",
                "meta_data={} stories={active={1={payload=\"" + "x".repeat(524289) + "\"}}}"))
            assertThrows(java.io.IOException.class, () -> new SaveStream(new StringReader(source), selection(story("1"))).read());
    }
}
