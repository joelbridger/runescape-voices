package com.jamesondaines.gielinorvoices;

import java.text.Normalizer;
import java.util.Locale;
import net.runelite.client.util.Text;

final class SpeakerKeys
{
	private SpeakerKeys()
	{
	}

	static String npc(String name, int fallbackId)
	{
		String normalized = normalize(name == null ? null : Text.removeTags(name));
		return normalized.isEmpty() ? "npc-id:" + fallbackId : "npc:" + normalized;
	}

	static String localPlayer()
	{
		return "player:local";
	}

	private static String normalize(String value)
	{
		if (value == null)
		{
			return "";
		}
		String decomposed = Normalizer.normalize(value, Normalizer.Form.NFKD)
			.toLowerCase(Locale.ROOT);
		StringBuilder result = new StringBuilder();
		boolean previousDash = false;
		for (int index = 0; index < decomposed.length(); index++)
		{
			char character = decomposed.charAt(index);
			if (Character.isLetterOrDigit(character))
			{
				result.append(character);
				previousDash = false;
			}
			else if (!previousDash && result.length() > 0)
			{
				result.append('-');
				previousDash = true;
			}
		}
		while (result.length() > 0 && result.charAt(result.length() - 1) == '-')
		{
			result.deleteCharAt(result.length() - 1);
		}
		return result.toString();
	}
}
