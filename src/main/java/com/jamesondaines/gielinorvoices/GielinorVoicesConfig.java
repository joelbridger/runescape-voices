package com.jamesondaines.gielinorvoices;

import net.runelite.client.config.Config;
import net.runelite.client.config.ConfigGroup;
import net.runelite.client.config.ConfigItem;
import net.runelite.client.config.Range;

@ConfigGroup(GielinorVoicesConfig.GROUP)
public interface GielinorVoicesConfig extends Config
{
	String GROUP = "gielinorVoices";

	@ConfigItem(
		keyName = "enabled",
		name = "Voice acting",
		description = "Speak visible dialogue using the private local voice service",
		position = 0
	)
	default boolean enabled()
	{
		return true;
	}

	@ConfigItem(
		keyName = "npcDialogue",
		name = "NPC dialogue",
		description = "Speak NPC dialogue boxes",
		position = 1
	)
	default boolean npcDialogue()
	{
		return true;
	}

	@ConfigItem(
		keyName = "playerDialogue",
		name = "Your dialogue",
		description = "Speak your character's dialogue boxes",
		position = 2
	)
	default boolean playerDialogue()
	{
		return true;
	}

	@ConfigItem(
		keyName = "npcOverhead",
		name = "NPC overhead speech",
		description = "Speak words shown above NPCs outside dialogue boxes",
		position = 3
	)
	default boolean npcOverhead()
	{
		return true;
	}

	@ConfigItem(
		keyName = "cutOffOnSkip",
		name = "Stop when dialogue is skipped",
		description = "Stop the current performance when the dialogue box closes",
		position = 4
	)
	default boolean cutOffOnSkip()
	{
		return true;
	}

	@Range(min = 0, max = 100)
	@ConfigItem(
		keyName = "volume",
		name = "Voice volume",
		description = "Voice playback volume",
		position = 5
	)
	default int volume()
	{
		return 85;
	}
}

