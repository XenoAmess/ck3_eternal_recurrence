// Included inside xar::game; the sealed Gov/Land minimum schema precedes code.
struct ContextSourceFollowing312a950GovernmentV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::string> selection;
  std::optional<std::string> selected_character_identity;
  std::optional<std::int32_t> selection_native_index;
  std::optional<std::string> government_identity;
  std::optional<std::uint32_t> flags_raw_u32;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing312a950GovernmentV1 &, const ContextSourceFollowing312a950GovernmentV1 &) = default;
};
struct ContextSourceFollowing312a950FirstLandV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::string> selection;
  std::optional<bool> living_present;
  std::optional<bool> death_present;
  std::optional<std::int32_t> count_raw;
  std::optional<bool> array_present;
  std::optional<std::int32_t> full_id_raw;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing312a950FirstLandV1 &, const ContextSourceFollowing312a950FirstLandV1 &) = default;
};
struct ContextSourceFollowing312a950LandResolutionV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::string> selection;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<std::int32_t> selected_full_id_raw;
  std::optional<std::string> object_identity;
  std::optional<std::uint32_t> magic_u32;
  std::optional<std::int32_t> full_id_raw;
  std::optional<bool> admitted;
  std::optional<std::int64_t> balance_raw_q64;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing312a950LandResolutionV1 &, const ContextSourceFollowing312a950LandResolutionV1 &) = default;
};
struct ContextSourceFollowing312a950Mode3V1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::int64_t> income_q64;
  std::optional<std::int32_t> index_raw_i32;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing312a950Mode3V1 &, const ContextSourceFollowing312a950Mode3V1 &) = default;
};
struct ContextSourceFollowing312a950ProviderV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> provider_loaded;
  std::optional<std::int32_t> count_raw;
  std::optional<std::string> selection;
  std::optional<std::string> definition_identity;
  std::optional<std::uint32_t> definition_magic_u32;
  std::optional<bool> admitted;
  ContextSourceAfterPcV1 pc{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing312a950ProviderV1 &, const ContextSourceFollowing312a950ProviderV1 &) = default;
};
struct ContextSourceFollowing312a950InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourceFollowing312a950GovernmentV1 government_source{};
  std::optional<bool> character_state_present;
  std::optional<ContextSourceFollowing312a950FirstLandV1> first_land_source;
  std::optional<ContextSourceFollowing312a950LandResolutionV1> land_resolution;
  std::optional<ContextSourceFollowing312a950Mode3V1> mode3_classifier;
  std::optional<ContextSourceFollowing312a950ProviderV1> provider_selection;
  std::optional<std::string> stage_selection;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing312a950InputsV1 &, const ContextSourceFollowing312a950InputsV1 &) = default;
};
