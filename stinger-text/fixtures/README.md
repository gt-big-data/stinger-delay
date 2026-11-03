# Fixtures notes

## A7 decisions (personal Apple ID)
1. Trigger word: stinger
2. Judges text the owner's own number; ADMIN_HANDLES is a teammate's iPhone
3. Plain follow-ups allowed for 10 min after a triggered message: yes (matches default code)
4. Reply to a bare trigger word: no, stay silent
5. /bot off and /bot on: not added
6. ALLOWED_HANDLES allowlist: not added

All six A7 decisions match the default code; no gate changes needed.

## Observed (real scrubbed captures: bb_text, bb_maplink, bb_from_me)
- Event type string: `new-message`; `data` is an object.
- guid = `data.guid`; text = `data.text`; sender = `data.handle.address` (E.164; also `data.handle.uncanonicalizedId`, `country`, `service`).
- Chat guid = `data.chats[0].guid`; `isFromMe` = `data.isFromMe`.
- No `isGroup` key is present.
- Attachments = `data.attachments[]` with `guid`, `transferName`, `mimeType`, `uti`.
- `text` is non-null on the captured text messages.
- DM chat guid shape: `any;-;<handle>`. Group guid shape is the placeholder `iMessage;+;chat<id>`, NOT captured.

## Differences from the placeholders
(a) Real Apple Maps share link is `https://maps.apple.com/place?coordinate=<lat>,<lng>&name=..&map=..`, not `?ll=`; parser extended.
(b) Link messages carry 3 attachments named `*.pluginPayloadAttachment` with null mimeType and a `dyn.*` uti, which the parser correctly ignores.
(c) Chat guid prefix is `any;` not `iMessage;`.
(d) BlueBubbles sometimes delivers two events in the same second (batching) and retries POSTs when the listener returns non-2xx.
(e) Location-pin (`.loc.vcf`) payload NOT yet captured; the CL fixture is still a placeholder.
(f) Group payload not captured.

## Send body
`{chatGuid, tempGuid, message, method: "apple-script"}` confirmed working on 2 Nov (S4).

(g) Real iOS "Send My Current Location" is a Find My share: balloonBundleId contains `findmy.FindMyMessagesApp`, text is only U+FFFC, no attachments, payloadData null, so NO coordinates reach us. Pipeline replies with guidance; users share a pin from Apple Maps (map link) or name a building. A `.loc.vcf` pin (older style) is still parsed but only the synthetic placeholder exists.
