# Installed CK3 relic source excerpts

machine_id: `4-8e1c2f1861`  
observed_at_utc: `2026-10-17T09:16:58.891024+00:00`  
status: `SOURCE_REVIEWED_STATIC`; no live qualification. Full file hashes are in sources.json.

## S01: common/artifacts/templates/_templates.info

SHA-256 `6cdaf0ac1518c57a9343ae82ef2f05d7a7edf1a59823aa9ee62fbc8139407c0d`, 1709 bytes.

```text
6: 	# Can this character equip this artifact?
7: 	# Root scope: character
8: 	# scope:artifact = the artifact.
9: 	can_equip = {
10: 		always = yes
11: 	}
12: 
13: 	# Can this character benefit from the full modifiers of the artifact?
14: 	# Root scope: character
15: 	# scope:artifact = the artifact.
16: 	can_benefit = {
17: 		is_christian_trigger = yes
```

```text
34: 	# Is this artifact a holy relic for a faith?
35: 	# Relics can be enshrined into holy sites
36: 	#
37: 	# Root scope: faith to enshrine for
38: 	# scope:artifact = the artifact
39: 	is_holy_relic = {
40: 		always = no
41: 	}
```

## S02: common/scripted_rules/02_holy_sites.txt

SHA-256 `02dafa910b976b6428725775cfb14fdcfc345032fd2fdf77a5bbec0dd42e6054`, 2090 bytes.

```text
1: # Whether an artifact can be enshrined in a specific holy site.
2: # root            = the artifact being considered for enshrining
3: # scope:actor     = the character who would perform the enshrinement
4: # scope:holy_site = the target holy site
5: # scope:replacing = the artifact being replaced (if any)
6: can_enshrine_artifact = {
7: 	custom_description = {
8: 		text = holy_site_not_holder_or_top_liege
9: 
10: 		scope:holy_site.holy_site_county = {
11: 			OR = {
12: 				holder = scope:actor
13: 				holder.top_liege = scope:actor
14: 				clerical_region_title.holder = scope:actor
15: 			}
16: 		}
17: 	}
18: 	# Controlling another faith's holy site does not make it a shrine of yours
19: 	custom_description = {
20: 		text = holy_site_of_actor_faith
21: 
22: 		scope:actor.faith = {
23: 			is_faith_holy_site = scope:holy_site
24: 		}
25: 	}
26: }
27: 
28: # Whether a character can create a new dynamic holy site.
29: # root                 = the character creating the holy site
30: # scope:title          = the barony the holy site would be placed in
31: # scope:holy_site_type = the holy site type being created
32: # scope:faith          = the faith the holy site is created for
33: can_create_dynamic_holy_site = {
34: 	can_manage_faith_holy_sites_trigger = yes
35: 
36: 	# This is a command, not a decision, so the variable cooldown is set in on_character_holy_site_created
37: 	custom_description = {
38: 		text = holy_site_creation_on_cooldown_tt
39: 		NOT = { has_variable = holy_site_creation_cooldown }
40: 	}
41: 
42: 	scope:faith = {
43: 		faith_can_use_holy_site_kingdom_trigger = { BARONY = scope:title }
44: 	}
45: }
46: 
47: # Whether an enshrined artifact can be removed from a holy site.
48: # root            = the enshrined artifact
49: # scope:holy_site = the holy site it sits in
50: # scope:actor     = the character who would perform the removal
51: # scope:replacing = the artifact being replaced (if any)
52: can_remove_enshrined_artifact = {
53: 	custom_description = {
54: 		text = holy_site_not_holder_or_top_liege
55: 
56: 		scope:holy_site.holy_site_county = {
57: 			OR = {
58: 				holder = scope:actor
59: 				holder.top_liege = scope:actor
60: 				clerical_region_title.holder = scope:actor
61: 			}
62: 		}
63: 	}
64: }
```

## S03: gui/window_holy_site.gui

SHA-256 `23542c54dd73b0c349e008649f201b1459ef833070fb6071e089dcd210642fb2`, 32840 bytes.

```text
425: 							datamodel = "[HolySiteWindow.GetSlots]"
426: 							item = {
427: 								widget_holy_site_slot = {}
428: 							}
429: 						}
430: 
431: 						hbox = {
432: 							layoutpolicy_horizontal = expanding
433: 							margin_bottom = 6
434: 
435: 							hbox = {
436: 								spacing = 1
437: 								datamodel = "[GetSegmentedProgressTargetBar( GetDefine( 'NReligion','MAX_HOLY_SITE_RARITY_TOTAL' ), HolySite.GetTotalActiveArtifactRarity, HolySite.GetTotalActiveArtifactRarity)]"
```

```text
518: 							datacontext = "[HolySite.GetCounty.GetHolder.GetFaith]"
519: 
520: 							vbox_holy_site_effects = {
521: 								spacing = 10
522: 							}
523: 
524: 							vbox = {
525: 								datamodel = "[HolySiteWindow.GetActiveHolySiteFaiths]"
526: 								visible = "[Not( IsDataModelEmpty( HolySiteWindow.GetActiveHolySiteFaiths ) )]"
527: 								layoutpolicy_horizontal = expanding
528: 								margin_top = 20
529: 
530: 								text_label_center = {
531: 									layoutpolicy_horizontal = expanding
532: 									min_height = 26 # This helps with weird auto-layouting issues
533: 									autoresize = no # This helps with weird auto-layouting issues
534: 									text =  "HOLY_SITE_WINDOW_HOLY_SITE_FAITHS_HEADER"
535: 								}
536: 
537: 								item = {
538: 									holy_site_faith_item = {}
539: 								}
540: 							}
541: 
542: 							vbox = {
543: 								datamodel = "[HolySiteWindow.GetInactiveHolySiteFaiths]"
544: 								visible = "[Not( IsDataModelEmpty( HolySiteWindow.GetInactiveHolySiteFaiths ) )]"
545: 								layoutpolicy_horizontal = expanding
546: 								margin_top = 20
547: 
548: 								text_label_center = {
549: 									layoutpolicy_horizontal = expanding
550: 									text =  "HOLY_SITE_WINDOW_HOLY_SITE_FAITHS_INACTIVE_HEADER"
551: 								}
552: 
553: 								item = {
554: 									holy_site_faith_item = {}
555: 								}
556: 							}
557: 						}
558: 					}
559: 				}
```

```text
740: 									datamodel = "[HolySiteWindow.GetEnshrinableArtifacts]"
741: 									layoutpolicy_horizontal = expanding
742: 
743: 									addcolumn = 560
744: 									addrow = 116
745: 
746: 									item = {
747: 										widget_artifact_entry = {
748: 											blockoverride "background_button_overrides" {
749: 												onclick = "[HolySiteWindow.SelectArtifact( Artifact.Self )]"
750: 												down = "[HolySiteWindow.IsArtifactSelected( Artifact.Self )]"
751: 												onrightclick = "[ToggleGameViewData( 'artifact_details', Artifact.GetID )]"
752: 												onrightclick = "[LocalPlayerNewArtifacts.RemoveNewArtifact( Artifact.Self )]"
753: 												button_ignore = none
754: 											}
755: 										}
756: 									}
757: 								}
758: 							}
759: 
760: 							blockoverride "scrollbox_empty"
761: 							{
762: 								visible = "[IsDataModelEmpty( HolySiteWindow.GetEnshrinableArtifacts )]"
763: 								text = "HOLY_SITE_NO_ENSHRINEABLE_ARTIFACTS"
```

```text
852: 						### Action buttons
853: 						hbox = {
854: 							layoutpolicy_horizontal = expanding
855: 							spacing = 8
856: 							margin_top = 8
857: 
858: 							expand = {}
859: 
860: 							button_standard = {
861: 								text = "HOLY_SITE_ACTION_BUTTON_REMOVE"
862: 								enabled = "[HolySiteWindow.IsRemoveButtonEnabled]"
863: 								tooltip = "[HolySiteWindow.GetRemoveButtonTooltip]"
864: 								onclick = "[HolySiteWindow.OnRemoveButtonClicked]"
865: 								shortcut = "holy_site_remove_artifact"
866: 							}
867: 
868: 							button_primary = {
869: 								text = "HOLY_SITE_ACTION_BUTTON_SWAP"
870: 								visible = "[HolySiteWindow.HasSelectedFilledSlot]"
871: 								enabled = "[HolySiteWindow.IsEnshrineButtonEnabled]"
872: 								tooltip = "[HolySiteWindow.GetEnshrineButtonTooltip]"
873: 								onclick = "[HolySiteWindow.OnEnshrineButtonClicked]"
874: 							}
875: 
876: 							button_primary = {
877: 								text = "HOLY_SITE_ACTION_BUTTON_ENSHRINE"
878: 								visible = "[Not( HolySiteWindow.HasSelectedFilledSlot )]"
879: 								enabled = "[HolySiteWindow.IsEnshrineButtonEnabled]"
880: 								tooltip = "[HolySiteWindow.GetEnshrineButtonTooltip]"
881: 								onclick = "[HolySiteWindow.OnEnshrineButtonClicked]"
```

```text
924: 			using = tooltip_es
925: 
926: 			onclick = "[HolySiteWindow.SelectArtifact( Artifact.Self )]"
927: 			onclick = "[HolySiteWindow.ToggleSelectedSlot( InventorySlot.Self )]"
928: 			onrightclick = "[ToggleGameViewData( 'artifact_details', Artifact.GetID )]"
929: 			onrightclick = "[LocalPlayerNewArtifacts.RemoveNewArtifact( Artifact.Self )]"
930: 			button_ignore = none
931: 			down = "[Or( HolySiteWindow.IsArtifactSelected( Artifact.Self ), HolySiteWindow.IsSelectedSlot( InventorySlot.Self ) )]"
932: 
933: 			icon = {
934: 				visible = "[Not( Artifact.IsHolyRelicFor( HolySite.GetCounty.GetHolder.GetFaith.Self ) )]"
935: 				parentanchor = hcenter|bottom
936: 				size = { 25 25 }
937: 				alwaystransparent = yes
938: 
939: 				texture = "gfx/interface/icons/symbols/icon_warning.dds"
940: 			}
941: 
942: 			blockoverride "rarity_level" {
943: 				hbox_artifact_rarity_level = {}
944: 			}
945: 
946: 			blockoverride "not_holy" {
947: 				hbox = {
948: 					layoutpolicy_horizontal = expanding
949: 					datacontext = "[HolySite.GetCounty.GetHolder.GetFaith]"
950: 					spacing = 5
951: 
952: 					icon = {
953: 						visible = "[Not( Artifact.IsHolyRelicFor( HolySite.GetCounty.GetHolder.GetFaith.Self ) )]"
954: 						size = { 20 20 }
955: 						texture = "gfx/interface/icons/symbols/icon_warning.dds"
956: 					}
957: 
958: 					text_single = {
959: 						text =  "ARTIFACT_IS_HOLY_RELIC"
960: 						max_width = 350
```

```text
1006: 			button_round = {
1007: 				name = "remove_button"
1008: 				parentanchor = top|right
1009: 				size = { 30 30 }
1010: 
1011: 				enabled = "[HolySiteWindow.CanRemoveEnshrinedArtifact( Artifact.Self )]"
1012: 				alpha = 0
```

```text
1125: 		### warnings
1126: 		text_multi = {
1127: 			block "show_wrong_faith" {
1128: 				visible = "[Not( HolySiteItem.IsHeldByFaith )]"
1129: 			}
1130: 			layoutpolicy_horizontal = expanding
1131: 			text = "[HolySiteItem.GetControlDesc]"
1132: 			align = center|nobaseline
1133: 			max_width = 440
1134: 			autoresize = yes
1135: 		}
1136: 
1137: 		text_multi = {
1138: 			visible = "[IsZero( HolySite.GetTotalActiveArtifactRarity )]"
1139: 			layoutpolicy_horizontal = expanding
1140: 			text = "HOLY_SITE_WINDOW_HOLY_SITE_NO_ENSHRINED_ARTIFACTS"
1141: 			align = center|nobaseline
1142: 			max_width = 440
1143: 			autoresize = yes
1144: 		}
1145: 
1146: 		### headers
1147: 		hbox = {
1148: 			layoutpolicy_horizontal = expanding
1149: 
1150: 			text_label_center = {
1151: 				visible = "[HolySite.IsActive]"
1152: 
1153: 				text = "HOLY_SITE_WINDOW_HOLY_SITE_EFFECTS_HEADER"
1154: 				block "active_effects_format" {
1155: 					layoutpolicy_horizontal = expanding
1156: 				}
1157: 			}
1158: 
1159: 			text_label_center = {
1160: 				visible = "[Not( HolySite.IsActive )]"
1161: 				text = "HOLY_SITE_WINDOW_HOLY_SITE_INACTIVE_EFFECTS_HEADER"
1162: 				block "inactive_effects_format" {
1163: 					layoutpolicy_horizontal = expanding
1164: 				}
1165: 			}
1166: 
1167: 			expand = {}
1168: 		}
1169: 
1170: 		# inactive effects
1171: 		text_multi = {
1172: 			visible = "[Not( HolySite.IsActive )]"
1173: 			layoutpolicy_horizontal = expanding
1174: 			text = "[HolySite.GetInactiveEffectDesc( Faith.Self )]"
1175: 			max_width = 440
1176: 			autoresize = yes
1177: 			alpha = 0.6
1178: 		}
1179: 
1180: 		# active effects
1181: 		vbox = {
1182: 			visible = "[HolySite.IsActive]"
1183: 			layoutpolicy_horizontal = expanding
1184: 			spacing = 10
1185: 
1186: 			# regular effects
1187: 			text_multi = {
1188: 				layoutpolicy_horizontal = expanding
1189: 				visible = "[Not( StringIsEmpty( HolySite.GetType.GetRegularEffectDesc( HolySiteItem.GetFaith.Self, HolySiteItem.GetHolySite.GetBarony.Self, IntToFixedPoint( HolySite.GetTotalActiveArtifactRarity ) ) ) )]"
1190: 
1191: 				text = "[HolySite.GetType.GetRegularEffectDesc( Faith.Self, HolySiteItem.GetHolySite.GetBarony.Self, IntToFixedPoint( HolySite.GetTotalActiveArtifactRarity ) )]"
1192: 				max_width = 440
1193: 				autoresize = yes
1194: 			}
1195: 
1196: 			# eminent effects
1197: 			vbox = {
1198: 				layoutpolicy_horizontal = expanding
1199: 				spacing = 10
1200: 
1201: 				divider_light = {
1202: 					visible = "[And( HolySiteItem.IsHeldByFaith, Faith.IsEminentHolySite( HolySite.Self ) )]"
1203: 					layoutpolicy_horizontal = expanding
1204: 				}
1205: 
1206: 				hbox = {
1207: 					layoutpolicy_horizontal = expanding
1208: 					visible = "[Or( Not( Faith.IsEminentHolySite( HolySite.Self ) ), Not( HolySiteItem.IsHeldByFaith ) )]"
1209: 
1210: 					text_label_center = {
1211: 						text = "HOLY_SITE_WINDOW_HOLY_SITE_INACTIVE_EFFECTS_HEADER"
1212: 						block "inactive_effects_format" {
1213: 							layoutpolicy_horizontal = expanding
1214: 						}
1215: 					}
1216: 					expand = {}
1217: 				}
1218: 
1219: 				text_multi = {
1220: 					layoutpolicy_horizontal = expanding
1221: 					max_width = 440
1222: 					autoresize = yes
1223: 
1224: 					text = "[HolySite.GetType.GetEminentEffectDesc( Faith.Self, HolySiteItem.GetHolySite.GetBarony.Self, IntToFixedPoint( HolySite.GetTotalActiveArtifactRarity ) )]"
1225: 					alpha = "[Select_float( And( Faith.IsEminentHolySite( HolySite.Self ), HolySiteItem.IsHeldByFaith), '(float)1.0', '(float)0.6' )]"
```

## S04: common/religion/holy_site_types/_holy_site_types.info

SHA-256 `b7f321911c857a5214eb2681d48a700020c125377df0d7d4936928a500b6f33e`, 3329 bytes.

```text
32: 	### Brief: faith_character_modifier ( modifiers )
33: 	# Modifiers applied to all characters of any faith with this holy site when the holder of the barony is of their faith.
34: 	# Will only be applied if the holy site is an Eminent holy site for the Faith
35: 	# Ex: { development_growth_factor = 0.1, church_holding_build_gold_cost = -0.1 }
36: 	#
37: 	faith_character_modifier = {
38: 		<modifier>
39: 	}
40: 
41: 	### Brief: faith_character_modifier_scaled ( scalable modifier list, repeatable )
42: 	# Optional, repeatable. Each entry defines a character modifier whose values
43: 	# multiply by a script-evaluated scale and is applied to all characters of the faith.
44: 	# Will only be applied if the holy site is an Eminent holy site for the Faith.
45: 	#
46: 	# The `scale` field is a script value evaluated with the holy_site as the top
47: 	# scope. The built-in `holy_site_total_artifact_rarity` returns the sum of
48: 	# Rarity values across artifacts whose is_holy_relic trigger is true.
49: 	# (1=Common, 2=Masterwork, 3=Famed, 4=Illustrious).
50: 	#
51: 	faith_character_modifier_scaled = {
52: 		scale = holy_site_total_artifact_rarity
53: 		monthly_piety_gain_mult = 0.05
54: 	}
55: 
56: 	### Brief: character_modifier ( modifiers )
57: 	# Modifiers applied to holder of county of holy site, if same faith.
58: 	# Will be applied if Regular or Eminent holy site of faith.
59: 	#
60: 	county_holder_character_modifier = {
61: 		<modifier>
62: 	}
63: 
64: 	### Brief: county_modifier_scaled ( scalable modifier list, repeatable )
65: 	# Optional, repeatable. Each entry defines a county modifier whose values
66: 	# multiply by a script-evaluated scale and is applied to the holy site's
67: 	# county.
68: 	# Will be applied if Regular or Eminent holy site of faith.
69: 	#
70: 	# The `scale` field is a script value evaluated with the holy_site as the top
71: 	# scope. The built-in `holy_site_total_artifact_rarity` returns the sum of
72: 	# Rarity values across artifacts whose can_benefit_holy_site trigger
73: 	# passes (1=Common, 2=Masterwork, 3=Famed, 4=Illustrious; 0 if none qualify).
74: 	#
75: 	county_modifier_scaled = {
76: 		scale = holy_site_total_artifact_rarity
77: 		monthly_county_control_growth_factor = 0.01
78: 	}
```

## S05: common/artifacts/templates/00_historical_artifacts_templates.txt

SHA-256 `81572177df33ab1cd834721966046f99cde67f1f10037e86e8f59cfe32cf2cf0`, 25747 bytes.

```text
1: ark_covenant_template = {
2: 	can_equip = {
3: 		always = yes
4: 	}
5: 
6: 	# can this character benefit from the full modifiers of the artifact?
7: 	can_benefit = {
8: 		OR = {
9: 			jewish_artifact_access_trigger = yes
10: 			christian_artifact_access_trigger = yes
11: 			islamic_artifact_access_trigger = yes
12: 		}
13: 	}
14: 
15: 	is_holy_relic = {
16: 		OR = {
17: 			religion = religion:judaism_religion
18: 			religion = religion:christianity_religion
19: 			religion = religion:islam_religion
20: 			main_rite = { rite_has_parameter = jewish_syncretic_actor }
21: 			main_rite = { rite_has_parameter = christian_syncretic_actor }
22: 			main_rite = { rite_has_parameter = islamic_syncretic_actor }
23: 		}
24: 	}
25: 
26: 	# if a given character does not pass the "can_benefit" trigger then this modifier will be applied instead.
27: 	fallback = {
28: 		court_grandeur_baseline_add = 6
29: 		monthly_dynasty_prestige_mult = 0.05
30: 	}
31: 
32: 	unique = yes
33: }
34: 
35: banner_thankfulness = {
36: 	can_equip = {
37: 		always = yes
38: 	}
39: 
40: 	# can this character benefit from the full modifiers of the artifact?
41: 	can_benefit = {
42: 		islamic_artifact_access_trigger = yes
43: 	}
44: 
45: 	is_holy_relic = {
46: 		OR = {
47: 			religion = religion:islam_religion
48: 			main_rite = { rite_has_parameter = islamic_syncretic_actor }
49: 		}
50: 	}
```

```text
134: 	# Deliberately not a holy relic: the tiara is Papal regalia, so it cannot be enshrined or targeted by relic wars
135: 
136: 	# if a given character does not pass the "can_benefit" trigger then this modifier will be applied instead.
137: 	fallback = {
138: 		court_grandeur_baseline_add = 4
139: 		monthly_prestige = 1
140: 	}
141: 
142: 	unique = yes
143: }
144: 
145: al_taj_template = {
146: 	can_equip = {
147: 		always = yes
148: 	}
149: 
150: 	# can this character benefit from the full modifiers of the artifact?
151: 	can_benefit = {
152: 		OR = {
153: 			has_title = title:d_shiite
154: 			any_liege_or_above = {
155: 				has_title = title:d_shiite
156: 			}
157: 		}
158: 	}
159: 
160: 	is_holy_relic = {
161: 		OR = {
162: 			religion = religion:islam_religion
163: 			main_rite = { rite_has_parameter = islamic_syncretic_actor }
164: 		}
165: 		main_rite = { rite_has_doctrine = muhammad_succession_shia_doctrine }
```

```text
984: 	is_holy_relic = {
985: 		scope:artifact = { has_variable = statue_religion }
986: 		religion = scope:artifact.var:statue_religion
987: 	}
988: 
989: 	fallback = {
990: 		monthly_prestige = 0.2
991: 	}
992: }
993: 
994: saintly_bones_template = {
995: 	can_equip = {
996: 		scope:artifact = { has_variable = saint_bone_faith }
997: 		saintly_bones_faith_trigger = yes
998: 	}
999: 
1000: 	can_benefit = {
1001: 		scope:artifact = { has_variable = saint_bone_faith }
1002: 		saintly_bones_faith_trigger = yes
1003: 	}
1004: 
1005: 	is_holy_relic = {
1006: 		scope:artifact = { has_variable = saint_bone_faith }
1007: 		OR = {
1008: 			religion = religion:christianity_religion
1009: 			main_rite = { rite_has_parameter = christian_syncretic_actor }
1010: 		}
1011: 	}
```

## S06: common/artifacts/templates/pam_saint_relic_templates.txt

SHA-256 `e7b568e6d42f78aa10b834877ce1a164ff982deea09d2cd0d110c175711f329f`, 1651 bytes.

```text
6: # var:pam_saint_relic_saint is set at extraction
7: pam_saint_relic_template = {
8: 	can_equip = {
9: 		always = yes
10: 	}
11: 
12: 	can_benefit = {
13: 		# One readable line; the has_variable guard stays inside so the raw variable check isn't shown.
14: 		custom_description = {
15: 			text = pam_saint_relic_benefit_faith_tt
16: 			# subject exposes the buried saint to the loc as CHARACTER.
17: 			subject = scope:artifact.var:pam_saint_relic_saint
18: 			scope:artifact = { has_variable = pam_saint_relic_saint }
19: 			faith.religion = scope:artifact.var:pam_saint_relic_saint.religion
20: 		}
21: 	}
22: 
23: 	is_holy_relic = {
24: 		custom_description = {
25: 			subject = scope:artifact.var:pam_saint_relic_saint
26: 			text = pam_saint_relic_benefit_faith_tt
27: 
28: 			scope:artifact = { has_variable = pam_saint_relic_saint	}
29: 			religion = scope:artifact.var:pam_saint_relic_saint.religion
30: 		}
31: 	}
32: 
33: 	fallback = {
34: 		court_grandeur_baseline_add = 3
35: 	}
36: 
37: 	unique = yes
```

## S07: common/artifacts/slots/01_holy_site.txt

SHA-256 `748a4c2f87bfea5959843c88456f38851eb968e507ef376bff0a725a6ac425df`, 321 bytes.

```text
1: ###################
2: # HOLY SITE SLOTS #
3: ###################
4: # Artifact slots available on holy sites
5: ###
6: 
7: holy_relic_1 = {
8: 	holy_site = yes
9: 	allow_any_type_or_category = yes
10: }
11: 
12: holy_relic_2 = {
13: 	holy_site = yes
14: 	allow_any_type_or_category = yes
15: }
16: 
17: holy_relic_3 = {
18: 	holy_site = yes
19: 	allow_any_type_or_category = yes
20: }
```

## S08: common/defines/00_defines.txt

SHA-256 `8e430d77eb6e8767030f34b1c53d5dae84277fb354bd73cc42f93dc500be8982`, 125400 bytes.

```text
919: 	# How many eminent holy sites can a Faith have? (unless overridden by Religion)
920: 	FAITH_EMINENT_HOLY_SITES_MAX_DEFAULT = 3
921: 	# How many holy sites in total, eminent ones included, can a Faith have? (unless overridden by Religion)
922: 	FAITH_HOLY_SITES_MAX_DEFAULT = 9
923: 	# Minimum number of eminent holy sites a Faith must retain (unless overridden by Religion)
924: 	FAITH_EMINENT_HOLY_SITES_MIN_DEFAULT = 1
925: 	# Minimum number of holy sites in total a Faith must retain (unless overridden by Religion)
926: 	FAITH_HOLY_SITES_MIN_DEFAULT = 1
927: 
928: 	# How many rarity levels are required for a Ruler to create a holy site
929: 	CREATE_HOLY_SITE_RARITY_REQUIRED = 3
930: 
931: 	# How many rarity levels can be used to scale holy site effects (should match with holy site slots)
932: 	MAX_HOLY_SITE_RARITY_TOTAL = 12
```

```text
1577: 	ARTIFACT_DURABILITY_DECAY_EQUIPPED = 1.0 # yearly decay, equipped to person
1578: 	ARTIFACT_DURABILITY_DECAY_DISPLAY = 0.0 # yearly decay, on display in court
1579: 	ARTIFACT_DURABILITY_DECAY_ENSHRINED = 0.0 # yearly decay, enshrined in a holy site (disabled in code too)
```

## S09: gui/window_holy_site_creation.gui

SHA-256 `7e6cd0cf6cc70616fa1f3137dca1c229f60c68a7f18bb3d43cd44dd9bf367310`, 23400 bytes.

```text
293: 								datamodel = "[GetSegmentedProgressTargetBar( GetDefine( 'NReligion','MAX_HOLY_SITE_RARITY_TOTAL' ), FixedPointToInt( HolySiteCreationWindow.GetSelectedArtifactsRaritySum ), FixedPointToInt( HolySiteCreationWindow.GetSelectedArtifactsRaritySum ) )]"
```

```text
511: 								datamodel = "[HolySiteCreationWindow.GetEnshrinableArtifacts]"
512: 
513: 								addcolumn = 560
514: 								addrow = 116
515: 
516: 								item = {
517: 									widget_artifact_entry = {
518: 										blockoverride "background_button_overrides"
519: 										{
520: 											onclick = "[HolySiteCreationWindow.SelectArtifact( Artifact.Self )]"
521: 											down = "[HolySiteCreationWindow.IsArtifactSelected( Artifact.Self )]"
522: 										}
523: 										blockoverride "artifact_click_info" {}
524: 										blockoverride "artifact_click_text" {
525: 											text = "[HolySiteCreationWindow.GetEnshrineTooltip( Artifact.Self )]"
```

```text
534: 								datamodel = "[HolySiteCreationWindow.GetEnshrinableArtifacts]"
535: 
536: 								addcolumn = 100
537: 								addrow = 100
538: 								flipdirection = yes
539: 								datamodel_wrap = 5
540: 
541: 								item = {
542: 									button_standard_hover = {
543: 										size = { 90 90 }
544: 										down = "[HolySiteCreationWindow.IsArtifactSelected( Artifact.Self )]"
545: 
546: 										button_artifact = {
547: 											blockoverride "on_click" {
548: 												onclick = "[HolySiteCreationWindow.SelectArtifact( Artifact.Self )]"
549: 
550: 												onrightclick = "[ToggleGameViewData( 'artifact_details', Artifact.GetID )]"
551: 												onrightclick = "[LocalPlayerNewArtifacts.RemoveNewArtifact( Artifact.Self )]"
552: 												button_ignore = none
553: 											}
554: 											blockoverride "artifact_click_info" {}
555: 											blockoverride "artifact_click_text" {
556: 												text = "[HolySiteCreationWindow.GetEnshrineTooltip( Artifact.Self )]"
557: 												default_format = "#I"
558: 											}
559: 										}
560: 									}
561: 								}
562: 							}
563: 						}
564: 
565: 						blockoverride "scrollbox_empty"
566: 						{
567: 							visible = "[IsDataModelEmpty( HolySiteCreationWindow.GetEnshrinableArtifacts )]"
568: 							text = "HOLY_SITE_NO_ENSHRINEABLE_ARTIFACTS"
```

```text
697: 
698: 					expand = {}
699: 
700: 					hbox = {
701: 						min_width = 200
702: 
703: 						cost_breakdown_vbox = {
704: 							datacontext = "[HolySiteCreationWindow.AccessCostBreakdown]"
705: 						}
706: 					}
707: 
708: 
709: 					button_primary = {
710: 						size = { 250 33 }
711: 						text = "HOLY_SITE_CREATION_ACTION_BUTTON_CREATE"
712: 						enabled = "[HolySiteCreationWindow.IsCreateButtonEnabled]"
713: 						tooltip = "HOLY_SITE_CREATION_CREATE_BUTTON_TT"
714: 						onclick = "[HolySiteCreationWindow.OnCreateButtonClicked]"
```

## S10: common/scripted_triggers/pam_scripted_triggers.txt

SHA-256 `0ad98f123b6739593b9ab2c170d0e8c9b3d9d941baa9d3580296dd2139b2ea6e`, 186187 bytes.

```text
1292: # The acting character is the scope, and on the puppet action path that is the puppet
1293: # A puppet standing in for a missing Head of Faith defers to its puppeteer
1294: can_manage_faith_holy_sites_trigger = {
1295: 	trigger_if = {
1296: 		limit = { exists = faith.religious_head }
1297: 		custom_tooltip = {
1298: 			text = manage_holy_sites_hof_or_puppet_tt
1299: 			OR = {
1300: 				faith.religious_head ?= this
1301: 				puppet:theological_agent_puppet ?= faith.religious_head
1302: 				puppet:external_theological_agent_puppet ?= faith.religious_head
1303: 			}
1304: 		}
1305: 	}
1306: 	trigger_else = {
1307: 		trigger_if = {
1308: 			limit = { exists = puppeteer }
1309: 			puppeteer = { can_manage_faith_holy_sites_without_hof_trigger = yes }
1310: 		}
1311: 		trigger_else = {
1312: 			can_manage_faith_holy_sites_without_hof_trigger = yes
1313: 		}
1314: 	}
1315: }
1316: 
1317: # Substitute authority for a faith with no head of faith: a realm priest puppet plus piety standing.
1318: can_manage_faith_holy_sites_without_hof_trigger = {
1319: 	OR = {
1320: 		custom_tooltip = {
1321: 			text = manage_holy_sites_realm_priest_puppet_tt
1322: 			# puppet: errors on non-playable characters, so we only check playable ones and tooltips never run it
1323: 			trigger_if = {
1324: 				limit = { is_playable_character = yes }
1325: 				exists = puppet:theological_agent_puppet
1326: 			}
1327: 			trigger_else = {
1328: 				always = no
1329: 			}
1330: 		}
1331: 		government_has_flag = government_is_theocracy
1332: 	}
1333: 	custom_tooltip = {
1334: 		text = manage_holy_sites_piety_level_tt
1335: 		piety_level >= 4
1336: 	}
1337: }
```

## S11: common/scripted_triggers/00_religious_triggers.txt

SHA-256 `e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2`, 88549 bytes.

```text
2000: # BARONY = the candidate holy site's barony title, in faith scope
2001: # One created or adopted holy site per de jure kingdom
2002: faith_holy_site_kingdom_unused_trigger = {
2003: 	trigger_if = {
2004: 		limit = {
2005: 			has_variable_list = dynamic_holy_site_kingdoms
2006: 			exists = $BARONY$.kingdom
2007: 		}
2008: 		NOT = {
2009: 			is_target_in_variable_list = {
2010: 				name = dynamic_holy_site_kingdoms
2011: 				target = $BARONY$.kingdom
2012: 			}
2013: 		}
2014: 	}
2015: }
2016: 
2017: # As above, with the player-facing requirement line. Root must be the acting character.
2018: faith_can_use_holy_site_kingdom_trigger = {
2019: 	custom_tooltip = {
2020: 		text = holy_site_kingdom_already_used_tt
2021: 		faith_holy_site_kingdom_unused_trigger = { BARONY = $BARONY$ }
2022: 	}
2023: }
```

## S12: common/on_action/religion_on_actions.txt

SHA-256 `ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d`, 59475 bytes.

```text
2040: # Called when a Character creates a new Holy Site.
2041: # Note: Also used to show effects in GUI before creation
2042: #
2043: # Root scope: Character creating holy site
2044: # scope:title - barony title of location where holy site is created
2045: # scope:holy_site_type - holy site type being created
2046: # scope:faith - Faith the holy site is created for
2047: # scope:artifacts - List of artifacts being enshrined
2048: on_character_holy_site_created = {
2049: 	effect = {
2050: 		# Same holy-site slot rules as game start
2051: 		scope:title.title_province = {
2052: 			add_holy_site_fallback_special_building_slot_effect = { FAITH = scope:faith }
2053: 		}
2054: 		hidden_effect = {
2055: 			if = {
2056: 				limit = { scope:faith = { faith_has_free_holy_site_action_trigger = yes } }
2057: 				scope:faith = { consume_free_holy_site_action_effect = yes }
2058: 			}
2059: 			else = {
2060: 				set_variable = {
2061: 					name = holy_site_creation_cooldown
2062: 					years = holy_site_action_cooldown_years
2063: 				}
2064: 			}
2065: 		}
```

## S13: common/decisions/50_holy_site_decisions.txt

SHA-256 `80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4`, 19759 bytes.

```text
636: # AI only - decision to enshrine holy relics into holy sites they have access to.
637: ai_enshrine_artifact_decision = {
638: 	picture = {
639: 		reference = "gfx/interface/illustrations/event_scenes/temple.dds"
640: 	}
641: 
642: 	ai_check_interval_by_tier = {
643: 		barony = 0
644: 		county = 24
645: 		duchy = 12
646: 		kingdom = 12
647: 		empire = 12
648: 		hegemony = 12
649: 	}
650: 
651: 	is_shown = {
652: 		is_ai = yes
653: 	}
654: 
655: 	is_valid = {
656: 		is_available_ai_adult = yes
657: 		has_any_artifact = yes
658: 
659: 		any_character_artifact = {
660: 			is_holy_relic = yes
661: 			is_holy_relic_for = root.faith
662: 
663: 			save_temporary_scope_as = artifact_to_enshrine
664: 			root.faith = {
665: 				any_holy_site = {
666: 					root = {
667: 						can_enshrine_holy_site_artifact = {
668: 							holy_site = prev
669: 							artifact = scope:artifact_to_enshrine
670: 						}
671: 					}
672: 				}
673: 			}
674: 		}
675: 	}
676: 
677: 	effect = {
678: 		# Get highest rarity relic owned
679: 		ordered_character_artifact = {
680: 			limit = {
681: 				is_holy_relic_for = root.faith
682: 			}
683: 			max = 1
684: 			order_by = artifact_rarity
685: 			save_scope_as = artifact_to_enshrine
686: 		}
687: 
688: 		if = {
689: 			limit = { exists = scope:artifact_to_enshrine }
690: 
691: 			# Empty Eminent site preferred
692: 			root.faith = {
693: 				random_eminent_holy_site = {
694: 					limit = {
695: 						total_active_artifact_rarity_sum = 0
696: 						root = {
697: 							can_enshrine_holy_site_artifact = {
698: 								holy_site = prev
699: 								artifact = scope:artifact_to_enshrine
700: 							}
701: 						}
702: 					}
703: 					save_scope_as = target_holy_site
704: 				}
705: 
706: 				# Fall back to random mix of eminent/regular sites
707: 				if = {
708: 					limit = {
709: 						NOT = { exists = scope:target_holy_site }
710: 					}
711: 					random_holy_site = {
712: 						limit = {
713: 							root = {
714: 								can_enshrine_holy_site_artifact = {
715: 									holy_site = prev
716: 									artifact = scope:artifact_to_enshrine
717: 								}
718: 							}
719: 						}
720: 						save_scope_as = target_holy_site
721: 					}
722: 				}
723: 			}
724: 		}
725: 
726: 		enshrine_holy_site_artifact = {
727: 			holy_site = scope:target_holy_site
728: 			artifact = scope:artifact_to_enshrine
729: 		}
730: 	}
731: 
732: 	ai_potential = {
733: 		has_any_artifact = yes
734: 	}
735: 	ai_will_do = { base = 100 }
```

```text
738: # AI only - decision for zealots to strip hostile-faith relics out of holy sites in counties they directly hold.
739: #
740: # Sweep removes every matching artifact in one firing.
741: ai_remove_enshrined_artifact_decision = {
742: 	picture = {
743: 		reference = "gfx/interface/illustrations/event_scenes/temple.dds"
744: 	}
745: 
746: 	ai_check_interval_by_tier = {
747: 		barony = 0
748: 		county = 24
749: 		duchy = 12
750: 		kingdom = 12
751: 		empire = 12
752: 		hegemony = 12
753: 	}
754: 
755: 	is_shown = {
756: 		is_ai = yes
757: 	}
758: 
759: 	is_valid = {
760: 		is_available_ai_adult = yes
761: 
762: 		# Faith-aligned with top liege (independents pass: top_liege is themselves)
763: 		faith = top_liege.faith
764: 		# Don't mess with top lieges/faiths where player has a say
765: 		top_liege = {
766: 			is_ai = yes
767: 		}
768: 		faith = {
769: 			OR = {
770: 				NOT = { exists = religious_head }
771: 				religious_head = { is_ai = yes }
772: 			}
773: 		}
774: 
775: 		any_held_county = {
776: 			any_county_holy_site = {
777: 				holy_site_has_artifact = yes
778: 				save_temporary_scope_as = target_holy_site
779: 
780: 				OR = {
781: 					# Case A: own-faith site holds a non-relic-for-us artifact.
782: 					AND = {
783: 						any_holy_site_faith = {
784: 							this = root.faith
785: 						}
786: 						any_holy_site_enshrined_artifact = {
787: 							NOT = { is_holy_relic_for = root.faith }
788: 							root = {
789: 								can_remove_holy_site_artifact = {
790: 									holy_site = scope:target_holy_site
791: 									artifact = prev
792: 								}
793: 							}
794: 						}
795: 					}
796: 					# Case B: hostile-faith site holds a hostile-faith relic.
797: 					AND = {
798: 						any_holy_site_faith = {
799: 							this != root.faith
800: 							num_county_followers > 0
801: 							save_temporary_scope_as = target_faith
802: 							root.faith = {
803: 								faith_hostility_level = {
804: 									target = scope:target_faith
805: 									value >= faith_hostile_level
806: 								}
807: 							}
808: 							scope:target_holy_site = {
809: 								any_holy_site_enshrined_artifact = {
810: 									is_holy_relic_for = scope:target_faith
811: 									root = {
812: 										can_remove_holy_site_artifact = {
813: 											holy_site = scope:target_holy_site
814: 											artifact = prev
815: 										}
816: 									}
817: 								}
818: 							}
819: 						}
820: 					}
821: 				}
822: 			}
823: 		}
```

```text
834: 	effect = {
835: 		every_held_county = {
836: 			save_temporary_scope_as = held_county
837: 			every_county_holy_site = {
838: 				limit = {
839: 					holy_site_has_artifact = yes
840: 				}
841: 				save_temporary_scope_as = target_holy_site
842: 				every_holy_site_faith = {
843: 					save_temporary_scope_as = target_faith
844: 
845: 					# Case A: our faith — remove any artifact that is not a
846: 					# relic for our faith.
847: 					if = {
848: 						limit = {
849: 							this = root.faith
850: 						}
851: 						scope:target_holy_site = {
852: 							every_holy_site_enshrined_artifact = {
853: 								limit = {
854: 									NOT = { is_holy_relic_for = root.faith }
855: 								}
856: 								save_temporary_scope_as = target_artifact
857: 								root = {
858: 									remove_holy_site_artifact = {
859: 										holy_site = scope:target_holy_site
860: 										artifact = scope:target_artifact
861: 									}
862: 								}
863: 							}
864: 						}
865: 					}
866: 					# Case B: not our faith — remove artifacts that are
867: 					# relics for a hostile faith the site recognizes.
868: 					else_if = {
869: 						limit = {
870: 							num_county_followers > 0
871: 							root.faith = {
872: 								faith_hostility_level = {
873: 									target = scope:target_faith
874: 									value >= faith_hostile_level
875: 								}
876: 							}
877: 						}
878: 						scope:target_holy_site = {
879: 							every_holy_site_enshrined_artifact = {
880: 								limit = {
881: 									is_holy_relic_for = scope:target_faith
882: 									# Avoid removing a relic from your own holy site just because someone else you hate also likes it. Don't be like that.
883: 									NOT = {
884: 										is_holy_relic_for = root.faith
885: 										scope:target_holy_site = {
886: 											any_holy_site_faith = {
887: 												this = root.faith
888: 											}
889: 										}
890: 									}
891: 								}
892: 								save_temporary_scope_as = target_artifact
893: 								root = {
894: 									remove_holy_site_artifact = {
895: 										holy_site = scope:target_holy_site
896: 										artifact = scope:target_artifact
897: 									}
898: 								}
899: 							}
900: 						}
901: 					}
902: 				}
903: 			}
904: 		}
905: 	}
```

## S14: common/on_action/inventory_on_actions.txt

SHA-256 `fcab2d2e740d32f3e8b5cb4058196dd3592153343ea3ae7a41c980fc0a334f67`, 13630 bytes.

```text
129: # Fired when an artifact has been enshrined in a holy site (whether the slot was empty
130: # or an existing artifact was replaced).
131: # root             = the artifact that was enshrined
132: # scope:holy_site  = the holy site receiving the artifact
133: # scope:actor      = the character who initiated the enshrining
134: # scope:replacing  = the artifact that was replaced in the slot, if any
135: on_holy_site_artifact_enshrined = {
136: 	effect = {
137: 		# Save if we're improving the artifact level with a replace
138: 		if = {
139: 			limit = {
140: 				scope:replacing ?= {
141: 					is_holy_relic_for = scope:actor.faith
142: 					rarity_level >= root.rarity_level
143: 				}
144: 			}
145: 			save_scope_value_as = {
146: 				name = replacing_with_better_artifact
147: 				value = no
148: 			}
149: 		}
150: 		else = {
151: 			save_scope_value_as = {
152: 				name = replacing_with_better_artifact
153: 				value = yes
154: 			}
155: 		}
156: 
157: 
158: 		# If this is a relic of your faith
159: 		if = {
160: 			limit = {
161: 				is_holy_relic_for = scope:actor.faith
162: 
163: 				# Don't gain things from replacing with a worse/equal level artifact
164: 				scope:replacing_with_better_artifact = no
165: 			}
166: 
167: 			save_scope_value_as = {
168: 				name = replace_piety_value
169: 				value = 0
170: 			}
171: 			scope:replacing ?= {
172: 				switch = {
173: 					trigger = rarity
174: 					illustrious = {
175: 						scope:actor = {
176: 							save_scope_value_as = {
177: 								name = replace_piety_value
178: 								value = massive_piety_loss
179: 							}
180: 						}
181: 					}
182: 					famed = {
183: 						scope:actor = {
184: 							save_scope_value_as = {
185: 								name = replace_piety_value
186: 								value = major_piety_loss
187: 							}
188: 						}
189: 					}
190: 					masterwork = {
191: 						scope:actor = {
192: 							save_scope_value_as = {
193: 								name = replace_piety_value
194: 								value = medium_piety_loss
195: 							}
196: 						}
197: 					}
198: 					common = {
199: 						scope:actor = {
200: 							save_scope_value_as = {
201: 								name = replace_piety_value
202: 								value = minor_piety_loss
203: 							}
204: 						}
205: 					}
206: 				}
207: 			}
208: 
209: 			switch = {
210: 				trigger = rarity
211: 				illustrious = {
212: 					scope:actor = {
213: 						add_piety = {
214: 							value = massive_piety_value
215: 							add = scope:replace_piety_value
216: 						}
217: 					}
218: 				}
219: 				famed = {
220: 					scope:actor = {
221: 						add_piety = {
222: 							value = major_piety_value
223: 							add = scope:replace_piety_value
224: 						}
225: 					}
226: 				}
227: 				masterwork = {
228: 					scope:actor = {
229: 						add_piety = {
230: 							value = medium_piety_value
231: 							add = scope:replace_piety_value
232: 						}
233: 					}
234: 				}
235: 				common = {
236: 					scope:actor = {
237: 						add_piety = {
238: 							value = minor_piety_value
239: 							add = scope:replace_piety_value
240: 						}
241: 					}
242: 				}
243: 			}
244: 
245: 			# Your zealous vassals like it
246: 			scope:actor = {
247: 				every_vassal = {
248: 					vassal_stance = zealot
249: 					limit = {
250: 						root = {
251: 							is_holy_relic_for = prev.faith
252: 						}
253: 					}
254: 					add_opinion = {
255: 						modifier = enshrined_holy_relic_at_holy_site
256: 						target = scope:actor
257: 					}
258: 				}
259: 
260: 				# Zealot lieges like it
261: 				every_liege_or_above = {
262: 					limit = {
263: 						OR = {
264: 							ai_zeal >= 50
265: 							has_trait = devoted
266: 							has_trait = zealous
267: 						}
268: 						root = {
269: 							is_holy_relic_for = prev.faith
270: 						}
271: 					}
272: 					add_opinion = {
273: 						modifier = enshrined_holy_relic_at_holy_site
274: 						target = scope:actor
275: 					}
276: 				}
277: 				# your head of faith likes it
278: 				faith = {
279: 					religious_head ?= {
280: 						if = {
281: 							limit = {
282: 								this != scope:actor
283: 								root = {
284: 									is_holy_relic_for = prev.faith
285: 								}
286: 							}
287: 
288: 							add_opinion = {
289: 								modifier = enshrined_holy_relic_at_holy_site
290: 								target = scope:actor
291: 							}
292: 						}
293: 					}
294: 				}
295: 			}
```

```text
322: # Fired when an artifact has been removed from a holy site (back into the actor's inventory).
323: # Also fires for the artifact replaced by a swap-style enshrining — in that
324: # (Only fired from explicit enshrining/removing effects, not generic inventory effects)
325: # case scope:replacing is the artifact that took its place.
326: # root             = the artifact that was removed
327: # scope:holy_site  = the holy site the artifact was taken from
328: # scope:actor      = the character who initiated the removal
329: # scope:replacing  = the artifact taking this one's place, if removal is part of a swap
330: on_holy_site_artifact_removed = {
331: 	effect = {
332: 		# Save if we're improving the artifact level with a replace
333: 		if = {
334: 			limit = {
335: 				is_holy_relic_for = scope:actor.faith
336: 				OR = {
337: 					NOT = { exists = scope:replacing }
338: 					scope:replacing ?= {
339: 						rarity_level < root.rarity_level
340: 					}
341: 				}
342: 			}
343: 			save_scope_value_as = {
344: 				name = replacing_with_better_artifact
345: 				value = no
346: 			}
347: 		}
348: 		else = {
349: 			save_scope_value_as = {
350: 				name = replacing_with_better_artifact
351: 				value = yes
352: 			}
353: 		}
354: 
355: 		# Heads of Faith don't like this.
356: 		if = {
357: 			limit = {
358: 				# Don't lose things from replacing with a better/equal level artifact
359: 				scope:replacing_with_better_artifact = no
360: 			}
361: 			scope:holy_site = {
362: 				every_holy_site_faith = {
363: 					limit = {
364: 						num_county_followers > 0
365: 					}
366: 					religious_head ?= {
367: 						if = {
368: 							limit = {
369: 								this != scope:actor
370: 								root = {
371: 									is_holy_relic_for = prev.faith
372: 								}
373: 							}
374: 
375: 							add_opinion = {
376: 								modifier = removed_holy_relic_from_holy_site
377: 								target = scope:actor
378: 							}
379: 						}
380: 					}
381: 				}
382: 			}
383: 		}
384: 
385: 		# If this is a relic of your faith
386: 		if = {
387: 			limit = {
388: 				is_holy_relic_for = scope:actor.faith
389: 				scope:replacing_with_better_artifact = no
390: 			}
391: 
392: 			# Costs Piety if it is your faith
393: 			switch = {
394: 				trigger = rarity
395: 				illustrious = { scope:actor = { add_piety_and_experience = massive_piety_loss } }
396: 				famed = { scope:actor = { add_piety_and_experience = major_piety_loss } }
397: 				masterwork = { scope:actor = { add_piety_and_experience = medium_piety_loss } }
398: 				common = { scope:actor = { add_piety_and_experience = minor_piety_loss } }
399: 			}
400: 
401: 			# Your zealous / minority vassals don't like it
402: 			scope:actor = {
403: 				every_vassal = {
404: 					custom = every_zealot_vassal
405: 					vassal_stance = zealot
406: 					limit = {
407: 						faith = scope:actor.faith
408: 					}
409: 					add_opinion = {
410: 						modifier = removed_holy_relic_from_holy_site
411: 						target = scope:actor
412: 					}
413: 				}
414: 				every_vassal = {
415: 					custom = every_minority_vassal
416: 					vassal_stance = minority
417: 					limit = {
418: 						faith = scope:actor.faith
419: 					}
420: 					add_opinion = {
421: 						modifier = removed_holy_relic_from_holy_site
422: 						target = scope:actor
423: 					}
424: 				}
425: 
426: 				if = {
427: 					limit = { liege != this }
428: 					# Fellow zealous vassals don't like it
429: 					liege = {
430: 						every_vassal = {
431: 							custom = every_zealot_fellow_vassal
432: 							vassal_stance = zealot
433: 							limit = {
434: 								faith = scope:actor.faith
435: 							}
436: 							add_opinion = {
437: 								modifier = removed_holy_relic_from_holy_site
438: 								target = scope:actor
439: 							}
440: 						}
441: 					}
442: 					# Lieges don't like it
443: 					every_liege_or_above = {
444: 						limit = {
445: 							OR = {
446: 								ai_zeal >= 50
447: 								has_trait = devoted
448: 								has_trait = zealous
449: 							}
450: 							root = {
451: 								is_holy_relic_for = prev.faith
452: 							}
453: 						}
454: 						add_opinion = {
455: 							modifier = removed_holy_relic_from_holy_site
456: 							target = scope:actor
457: 						}
458: 					}
459: 				}
460: 			}
461: 		}
462: 		else_if = {
463: 		 	# If this is not a relic of your faith
464: 			save_scope_as = artifact
465: 			custom_tooltip = {
466: 				text = holy_site_relic_will_get_reclaim_relic_cb
467: 			}
468: 
469: 			# Your vassals / fellow vassals / liege doesn't like it
470: 			scope:actor = {
471: 				every_vassal = {
472: 					limit = {
473: 						OR = {
474: 							faith != scope:actor.faith
475: 							scope:replacing_with_better_artifact = no
476: 						}
477: 						root = {
478: 							is_holy_relic_for = prev.faith
479: 						}
480: 					}
481: 					add_opinion = {
482: 						modifier = removed_holy_relic_from_holy_site
483: 						target = scope:actor
484: 					}
485: 				}
486: 				if = {
487: 					limit = { liege != this }
488: 					liege = {
489: 						every_vassal = {
490: 							limit = {
491: 								OR = {
492: 									faith != scope:actor.faith
493: 									scope:replacing_with_better_artifact = no
494: 								}
495: 								root = {
496: 									is_holy_relic_for = prev.faith
497: 								}
498: 							}
499: 							add_opinion = {
500: 								modifier = removed_holy_relic_from_holy_site
501: 								target = scope:actor
502: 							}
503: 						}
504: 					}
505: 					every_liege_or_above = {
506: 						limit = {
507: 							OR = {
508: 								faith != scope:actor.faith
509: 								scope:replacing_with_better_artifact = no
510: 							}
511: 							root = {
512: 								is_holy_relic_for = prev.faith
513: 							}
514: 						}
515: 						add_opinion = {
516: 							modifier = removed_holy_relic_from_holy_site
517: 							target = scope:actor
518: 						}
519: 					}
520: 				}
521: 			}
522: 		}
```

## S15: common/script_values/00_basic_values.txt

SHA-256 `c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef`, 50566 bytes.

```text
1130: #PIETY
1131: miniscule_piety_value = 25
1132: minor_piety_value = 50
1133: medium_piety_value = 100
1134: major_piety_value = 250
1135: massive_piety_value = 500
1136: monumental_piety_value = 1000
1137: 
1138: 
1139: miniscule_piety_loss = {
1140: 	value = 0
1141: 	subtract = miniscule_piety_value
1142: }
1143: minor_piety_loss = {
1144: 	value = 0
1145: 	subtract = minor_piety_value
1146: }
1147: medium_piety_loss = {
1148: 	value = 0
1149: 	subtract = medium_piety_value
1150: }
1151: major_piety_loss = {
1152: 	value = 0
1153: 	subtract = major_piety_value
1154: }
1155: massive_piety_loss = {
1156: 	value = 0
1157: 	subtract = massive_piety_value
```

## S16: common/opinion_modifiers/pam_opinions.txt

SHA-256 `68cdfc641a32a38daf6e9de6651634278b522b26c2886fbf6b55341ce7e09b52`, 4274 bytes.

```text
111: removed_holy_relic_from_holy_site = {
112: 	opinion = -20
113: 	years = 10
114: 	decaying = yes
115: }
116: 
117: enshrined_holy_relic_at_holy_site = {
118: 	opinion = 15
119: 	years = 10
120: 	decaying = yes
```

## S17: localization/english/gui/holy_site_window_l_english.yml

SHA-256 `7c0929203d6019e80607ab7cc57641e7eb649726de6c686678d0b4b37978fdf5`, 9969 bytes.

```text
12:  HOLY_SITE_WINDOW_HOLY_SITE_INACTIVE: "#weak @warning_icon! This [holy_site|E] is not active#!"
13:  HOLY_SITE_WINDOW_HOLY_SITE_NO_ENSHRINED_ARTIFACTS: "@warning_icon! #X [holy_site|E] is not active, it has no [enshrined|E] [holy_relics|E] of its [faith|E]#!"
14:  HOLY_SITE_WINDOW_HOLY_SITE_INACTIVE_EFFECTS_HEADER: "Inactive Effects"
15:  HOLY_SITE_WINDOW_HOLY_SITE_ARTIFACT_EFFECTS: "Artifact Effects"
16:  HOLY_SITE_WINDOW_HOLY_SITE_FAITHS_HEADER: "Holy Site for [faiths|E] #weak ([GetDataModelSize( HolySiteWindow.GetActiveHolySiteFaiths )])#!"
17:  HOLY_SITE_WINDOW_HOLY_SITE_FAITHS_INACTIVE_HEADER: "Holy Site for inactive [faiths|E] #weak ([GetDataModelSize( HolySiteWindow.GetInactiveHolySiteFaiths )])#!"
```

```text
30:  HOLY_SITE_ARTIFACT_SLOT_BULLET_FILLED: "$MODIFIER_BULLET$ #high [Artifact.GetName]#! (#weak [Artifact.GetRarityFull]#!)[AddLocalizationIf( Not( Artifact.IsHolyRelicFor( Faith.Self ) ), 'HOLY_SITE_ARTIFACT_SLOT_BULLET_FILLED_NOT_RELIC' )]"
31:  HOLY_SITE_ARTIFACT_SLOT_BULLET_FILLED_NOT_RELIC: " - $HOLY_SITE_ARTIFACT_SLOT_BULLET_FILLED_NOT_RELIC_TT$"
32:  HOLY_SITE_ARTIFACT_SLOT_BULLET_FILLED_NOT_RELIC_TT: " #X Not [holy_relic|E] for [Faith.GetName]#!"
33:  HOLY_SITE_ENSHRINE_REQUIRES_OWNERSHIP: "@warning_icon!#X You must own an artifact to enshrine it.#!"
34:  HOLY_SITE_REMOVE_REQUIRES_HOLDER: "@warning_icon!#X You must hold this Holy Site's county to remove the enshrined relic.#!"
35:  HOLY_SITE_ACTION_BUTTON_ENSHRINE: "Enshrine Relic"
36:  HOLY_SITE_ACTION_BUTTON_REMOVE: "Remove Relic"
37:  HOLY_SITE_ACTION_BUTTON_SWAP: "Swap Relic"
38:  HOLY_SITE_ACTION_BUTTON_NO_SELECTION_TT: "#weak Select an artifact from your inventory to enshrine, or an enshrined relic to remove.#!"
39:  HOLY_SITE_ENSHRINE_BUTTON_ALREADY_ENSHRINED_TT: "#weak This artifact is already enshrined here.#!"
40:  HOLY_SITE_REMOVE_BUTTON_NOT_ENSHRINED_TT: "#weak Select an enshrined relic from this Holy Site to remove.#!"
41:  HOLY_SITE_ACTION_EFFECTS_HEADER: "Action effects"
42:  HOLY_SITE_INVENTORY_BULLET_ENSHRINE: "$MODIFIER_BULLET$[ARTIFACT.GetName] becomes [enshrined|E] at [HOLY_SITE.GetName].\n$MODIFIER_BULLET$You are no longer the owner of [ARTIFACT.GetName].\n"
43:  HOLY_SITE_INVENTORY_BULLET_REMOVE: "$MODIFIER_BULLET$$SET_ARTIFACT_OWNER_FIRST$"
44:  HOLY_SITE_COUNTY_MODIFIER_CHANGE_HEADER: "\n#bold [holy_site|E] County:#! #weak (total [holy_relic|E] rarity change: #high $CURRENT_SUM$#! to #high $NEW_SUM$#!)#!\n"
45:  HOLY_SITE_FAITH_CHARACTER_MODIFIER_CHANGE_HEADER: "\n#bold All [Faith.GetAdherentNamePlural]:#! #weak ([holy_relics|E] rarity change: #high $CURRENT_SUM$#! to #high $NEW_SUM$#!)#!\n"
```

```text
89:  holy_site_creation_rarity_level_too_low: "@warning_icon! #X [enshrined|E] Artifacts have too few rarity levels to create a [holy_site|E]: Total is $RARITY_LEVELS_GIVEN|V0$, required is $RARITY_LEVELS_REQUIRED|V0$#!"
90:  holy_site_creation_too_many_artifacts: "@warning_icon! #X Too many Artifacts selected to [enshrine|E]: Total is $ARTIFACTS_GIVEN|V0$, maximum is $ARTIFACTS_MAX|V0$#!"
91:  holy_site_creation_faith_has_too_many_holy_sites: "@warning_icon! #X [Faith.GetName] has too many [holy_sites|E]: Current is $HOLY_SITES|V0$, maximum is $HOLY_SITES_MAX|V0$#!"
92: 
93:  holy_site_not_holder_or_top_liege: "County [holder|E], [top_liege|E], or [clerical_region|E] ruler of [holy_site|E]"
94:  not_holy_site_not_holder_or_top_liege_third: "Not county [holder|E], [top_liege|E], or [clerical_region|E] ruler of [holy_site|E]"
95:  holy_site_of_actor_faith: "A [holy_site|E] of your [faith|E]"
96:  not_holy_site_of_actor_faith_third: "Not a [holy_site|E] of their [faith|E]"
97: 
98:  holy_site_relic_will_get_reclaim_relic_cb: "Different [faith|E] [rulers|E] who consider the [artifact.GetName] a [holy_relic|E] will gain a [GetCasusBelliType('reclaim_relic_artifact_war').GetName] [casus_belli|E] against you"
```

## S18: localization/english/dlc/pam/pam_game_concepts_l_english.yml

SHA-256 `46a618caa266a7a3bb2cbdf38734e24971bd4e5f334f32af58a202e4713f5121`, 47822 bytes.

```text
246:  game_concept_enshrined: "Enshrined"
247:  game_concept_enshrine: "Enshrine"
248:  game_concept_enshrined_desc: "An enshrined [holy_relic|E] at a [holy_site|E] activates holy site bonuses and improves the bonuses it grants, scaled by the total [rarity|E] levels of all enshrined artifacts.\n\nAn enshrined artifact is no longer owned by a character, but may be interacted with by the [holder|E], [top_liege|E], or [clerical_region|E] holder of the holy site. The artifact will no longer decay. You can enshrine only holy relics for your own [faith|E]; enshrined holy relics of other faiths will provide no benefits.\n\nThere may be rewards or costs associated with enshrining or removing an enshrined artifact."
249: 
250:  game_concept_holy_relic: "Holy Relic"
251:  game_concept_holy_relics: "Holy Relics"
252:  game_concept_holy_relic_desc: "A $game_concept_holy_relic$ is an [artifact|E] that holds religious significance for a [faith|E]. A $game_concept_holy_relic$ can be [enshrined|E] in a [holy_site|E] of that faith to gain benefits.\n\nSome artifacts are inherently holy for a faith, but artifacts can also be [sanctified|E] to become a holy relic."
```

## S19: common/character_interactions/sanctify_artifact_interaction.txt

SHA-256 `d9c04416d441c7cd531866be189408d9421f9745c0aacd16c03e0abb37d943df`, 10345 bytes.

```text
396: 	is_valid_showing_failures_only = {
397: 		scope:actor = {
398: 			is_imprisoned = no
399: 		}
400: 		scope:recipient = {
401: 			custom_tooltip = {
402: 				text = sanctify_artifact_has_eligible_artifact_tt
403: 				any_character_artifact = {
404: 					NOT = { is_sanctified_for_faith = scope:actor.faith }
405: 					sanctify_artifact_is_eligible_trigger = {
406: 						RITE = scope:actor.rite
407: 					}
408: 				}
409: 			}
410: 		}
411: 	}
412: 
413: 	can_be_picked_artifact = {
414: 		scope:target = {
415: 			custom_tooltip = {
416: 				text = sanctify_artifact_not_already_sanctified_tt
417: 				NOT = { is_sanctified_for_faith = scope:actor.faith }
418: 			}
419: 			custom_tooltip = {
420: 				text = sanctify_artifact_tenet_allows_tt
421: 				sanctify_artifact_is_eligible_trigger = {
422: 					RITE = scope:actor.rite
423: 				}
424: 			}
425: 		}
426: 	}
427: 
428: 	auto_accept = yes
429: 
430: 	on_accept = {
431: 		scope:target = {
432: 			if = {
433: 				limit = {
434: 					is_holy_relic = no
435: 				}
436: 				add_artifact_modifier = sanctified_artifact_modifier
437: 			}
438: 			sanctify_artifact_flavor_effect = { PRIEST = scope:actor }
439: 		}
440: 		scope:actor = {
441: 			send_interface_toast = {
442: 				type = event_toast_effect_good
443: 				title = sanctify_artifact_interaction_accept_toast
444: 				left_icon = scope:recipient
445: 				right_icon = scope:target
446: 
447: 				scope:target = {
448: 					add_sanctified_for_faith = scope:actor.faith
449: 				}
```

## S20: common/scripted_triggers/sanctify_artifact_triggers.txt

SHA-256 `46eeef121b6ecaa89d9b36662503c7d9306cff5302acf0f8afa84eac29bcd51c`, 6803 bytes.

```text
1: # Triggers used by sanctify_artifact_interaction.
2: # Root scope: the artifact being considered.
3: # RITE = Rite to consider it for
4: #
5: # Whether the actor's faith permits sanctifying this artifact.
6: # The first branch is the baseline open to every Rite; each later branch matches one
7: # sanctify_artifacts_* tenet parameter to a further category of artifact.
8: sanctify_artifact_is_eligible_trigger = {
9: 	# A Rite sworn to poverty may never consecrate an illustrious piece, whatever else it permits
10: 	trigger_if = {
11: 		limit = { $RITE$ = { rite_has_parameter = sanctify_artifacts_humble } }
12: 		NOT = { rarity = illustrious }
13: 	}
14: 
15: 	OR = {
16: 		# Shrine furniture and reliquary vessels
17: 		AND = {
18: 			rarity_level >= masterwork
19: 			OR = {
20: 				artifact_slot_type = book
21: 				artifact_type = goblet
22: 				artifact_type = jug
23: 				artifact_type = bowl
24: 				artifact_type = plate
25: 				artifact_type = urn
26: 				artifact_type = sculpture
27: 				artifact_type = chest
28: 			}
29: 		}
30: 
31: 		# Weapons, armor, war-shields (e.g. tenet_warmonger)
32: 		AND = {
33: 			$RITE$ = { rite_has_parameter = sanctify_artifacts_weapons }
34: 			rarity_level >= masterwork
35: 			OR = {
36: 				artifact_slot_type = primary_armament
37: 				artifact_slot_type = armor
38: 				artifact_type = wall_shield
39: 				artifact_type = wall_shield_special
40: 			}
41: 		}
```

```text
131: 		# Humble vessels and texts are allowed at any quality, in trade for the illustrious ban above
132: 		AND = {
133: 			$RITE$ = { rite_has_parameter = sanctify_artifacts_humble }
134: 			OR = {
135: 				artifact_type = bowl
136: 				artifact_type = plate
137: 				artifact_type = urn
138: 				artifact_slot_type = book
139: 			}
140: 		}
141: 
142: 		# Jewelry, goblets, crowns, gems, ornate regalia (e.g. tenet_hedonistic)
143: 		AND = {
144: 			$RITE$ = { rite_has_parameter = sanctify_artifacts_luxurious }
145: 			rarity_level >= masterwork
146: 			OR = {
147: 				artifact_type = brooch
148: 				artifact_type = brooch_pedestal
149: 				artifact_type = ring
150: 				artifact_type = necklace
151: 				artifact_type = necklace_pedestal
152: 				artifact_slot_type = regalia
153: 				artifact_slot_type = helmet # aka crown
154: 
155: 				has_artifact_feature_group = decoration_material_gem
156: 				# Specific Unique artifacts with big gems
157: 				has_variable = al_hafir
158: 				has_variable = al_yatima
159: 				has_variable = koh_i_noor
160: 				has_variable = great_diamond
161: 			}
162: 		}
```

```text
207: 		# Regalia and gilded artifacts (e.g. tenet_sun_worship )
208: 		AND = {
209: 			$RITE$ = { rite_has_parameter = sanctify_artifacts_regal }
210: 			rarity_level >= masterwork
211: 			OR = {
212: 				artifact_slot_type = regalia
213: 				artifact_slot_type = helmet
214: 				has_artifact_feature_group = decoration_material_wire
215: 				has_artifact_feature_group = decoration_material_gem
216: 			}
217: 		}
218: 
219: 		# Has had a Relic added to it of a specific faith (see event artifact.4090)
220: 		AND = {
221: 			has_variable = added_relic_faith
222: 			var:added_relic_faith = $RITE$.rite_faith
223: 		}
224: 	}
225: }
```

## S21: common/religion/holy_site_types/00_holy_site_types.txt

SHA-256 `0824df55d4cd0a7c6d2c2d8b45bf577cca9ec0e5e1b4a6f699848b8661b17b40`, 169446 bytes.

```text
840: # Isma'ili (Shia)
841: 
842: nadjaf = {
843: 	county = c_kufa
844: 	barony = b_an-najaf
845: 
846: 	county_holder_character_modifier = {
847: 		clergy_opinion = 3
848: 	}
849: 
850: 	county_modifier_scaled = {
851: 		scale = holy_site_total_artifact_rarity
852: 		development_growth_factor = 0.01
853: 		county_opinion_add = 1
854: 	}
855: 
856: 	faith_character_modifier = {
857: 		diplomacy_per_piety_level = 1
858: 		clergy_opinion = 5
859: 	}
860: 
861: 	faith_character_modifier_scaled = {
862: 		scale = holy_site_total_artifact_rarity
863: 		monthly_piety_gain_mult = 0.01
864: 	}
865: }
```
