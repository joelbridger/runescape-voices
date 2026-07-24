package com.jamesondaines.gielinorvoices;

import com.jamesondaines.runescapecoach.RuneScapeCoachPlugin;
import net.runelite.client.RuneLite;
import net.runelite.client.externalplugins.ExternalPluginManager;

public class GielinorVoicesPluginTest
{
	@SuppressWarnings("unchecked")
	public static void main(String[] args) throws Exception
	{
		ExternalPluginManager.loadBuiltin(RuneScapeCoachPlugin.class);
		ExternalPluginManager.loadBuiltin(GielinorVoicesPlugin.class);
		RuneLite.main(args);
	}
}

