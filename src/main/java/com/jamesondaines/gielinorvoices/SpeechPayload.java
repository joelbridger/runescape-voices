package com.jamesondaines.gielinorvoices;

import java.util.Objects;

final class SpeechPayload
{
	static final int MAX_TEXT_LENGTH = 1_200;
	static final int MAX_NAME_LENGTH = 120;

	private final String speakerKey;
	private final String speakerName;
	private final String text;
	private final String kind;
	private final long sequence;
	private final double volume;

	SpeechPayload(
		String speakerKey,
		String speakerName,
		String text,
		String kind,
		long sequence,
		double volume)
	{
		this.speakerKey = requireText(speakerKey, "speakerKey", MAX_NAME_LENGTH);
		this.speakerName = requireText(speakerName, "speakerName", MAX_NAME_LENGTH);
		this.text = requireText(text, "text", MAX_TEXT_LENGTH);
		this.kind = requireText(kind, "kind", 40);
		if (sequence < 0)
		{
			throw new IllegalArgumentException("sequence must not be negative");
		}
		if (!Double.isFinite(volume) || volume < 0.0 || volume > 1.0)
		{
			throw new IllegalArgumentException("volume must be between zero and one");
		}
		this.sequence = sequence;
		this.volume = volume;
	}

	String getSpeakerKey()
	{
		return speakerKey;
	}

	String getSpeakerName()
	{
		return speakerName;
	}

	String getText()
	{
		return text;
	}

	String getKind()
	{
		return kind;
	}

	long getSequence()
	{
		return sequence;
	}

	double getVolume()
	{
		return volume;
	}

	private static String requireText(String value, String field, int maxLength)
	{
		String clean = Objects.requireNonNull(value, field).trim();
		if (clean.isEmpty() || clean.length() > maxLength)
		{
			throw new IllegalArgumentException(field + " has an invalid length");
		}
		for (int index = 0; index < clean.length(); index++)
		{
			char character = clean.charAt(index);
			if (Character.isISOControl(character) && !Character.isWhitespace(character))
			{
				throw new IllegalArgumentException(field + " contains a control character");
			}
		}
		return clean;
	}
}

