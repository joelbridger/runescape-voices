package com.jamesondaines.gielinorvoices;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class SpeakerKeysTest
{
	@Test
	public void givesNamedNpcsAStableKey()
	{
		assertEquals("npc:king-roald", SpeakerKeys.npc("<col=ff0000>King Roald</col>", 12));
		assertEquals("npc:king-roald", SpeakerKeys.npc("King Roald", 99));
	}

	@Test
	public void fallsBackToTheModelIdWhenNameIsMissing()
	{
		assertEquals("npc-id:321", SpeakerKeys.npc("", 321));
	}
}

