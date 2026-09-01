package com.xenoamess.kaishek.profile;

/** Source-directory families understood by a schema profile. */
public enum ScriptDomain {
    EVENTS, ON_ACTION, SCRIPTED_EFFECTS, SCRIPTED_TRIGGERS, SCRIPTED_VALUES,
    DECISIONS, INTERACTIONS, ACTIVITIES, SCRIPTED_GUI, CUSTOMIZABLE_LOCALIZATION,
    GUI_REGISTRATION, UNKNOWN;

    /** Classify a conventional Paradox source path without a game-specific dependency. */
    public static ScriptDomain fromPath(String sourcePath) {
        if (sourcePath == null || sourcePath.isBlank()) return UNKNOWN;
        String p = sourcePath.replace('\\', '/').toLowerCase(java.util.Locale.ROOT);
        if (p.contains("/events/") || p.startsWith("events/")) return EVENTS;
        if (p.contains("/on_action/") || p.contains("/on_actions/")
                || p.startsWith("on_action/") || p.startsWith("on_actions/")) return ON_ACTION;
        if (p.contains("/scripted_effect") || p.startsWith("scripted_effect")) return SCRIPTED_EFFECTS;
        if (p.contains("/scripted_trigger") || p.startsWith("scripted_trigger")) return SCRIPTED_TRIGGERS;
        // CK3 uses both `scripted_values` in vanilla terminology and
        // `script_values` in the shipped mod corpus.  They share one schema
        // domain; silently classifying the latter as UNKNOWN would make a
        // valid profile path look unsupported.
        if (p.contains("/scripted_value") || p.contains("/script_values/")
                || p.startsWith("scripted_value") || p.startsWith("script_values/")) return SCRIPTED_VALUES;
        if (p.contains("/decisions/") || p.startsWith("decisions/")) return DECISIONS;
        if (p.contains("/interactions/") || p.contains("/character_interactions/")
                || p.startsWith("interactions/") || p.startsWith("character_interactions/")) return INTERACTIONS;
        if (p.contains("/activities/") || p.startsWith("activities/")) return ACTIVITIES;
        if (p.contains("/scripted_gui") || p.startsWith("scripted_gui")) return SCRIPTED_GUI;
        if (p.contains("customizable_localization")) return CUSTOMIZABLE_LOCALIZATION;
        if (p.contains("/gui/") || p.startsWith("gui/")) return GUI_REGISTRATION;
        return UNKNOWN;
    }
}
