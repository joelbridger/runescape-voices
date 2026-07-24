package com.jamesondaines.gielinorvoices;

import static org.junit.Assert.assertEquals;

import com.google.gson.Gson;
import org.junit.Test;

public class SpeechPayloadTest
{
	@Test
	public void preservesExactVisibleTextInJson()
	{
		SpeechPayload payload = new SpeechPayload(
			"npc:zanik",
			"Zanik",
			"We'll find a way!",
			"npc-dialogue",
			7,
			0.85);

		String json = new Gson().toJson(payload);
		assertEquals("We'll find a way!", new Gson().fromJson(json, SpeechPayload.class).getText());
		assertEquals("npc:zanik", payload.getSpeakerKey());
	}

	@Test(expected = IllegalArgumentException.class)
	public void rejectsControlCharacters()
	{
		new SpeechPayload("npc:test", "Test", "unsafe\u0000text", "npc-dialogue", 1, 1.0);
	}

	@Test(expected = IllegalArgumentException.class)
	public void rejectsInvalidVolume()
	{
		new SpeechPayload("npc:test", "Test", "Hello", "npc-dialogue", 1, 1.1);
	}
}

