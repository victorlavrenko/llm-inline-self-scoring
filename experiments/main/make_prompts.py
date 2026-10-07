#!/usr/bin/env python3
import json
from pathlib import Path

WRAPPER = (
    "Write a short social-network post suitable for Facebook or a similar platform. "
    "The post should be understandable to a general audience and should read like "
    "something a person might genuinely publish, not like an encyclopedia entry or "
    "formal essay. Use approximately 5-8 sentences."
)

TOPICS = {
"history": [
"A history account wants to mark October 4, 1957 without assuming readers know the date. Write a short social-media post explaining what happened and why the event changed the technological and political climate of its era.",
"What happened on April 12, 1961? Turn the answer into a concise post for a general audience, including why the event mattered beyond the achievement itself.",
"Imagine someone sees November 9, 1989 on an anniversary calendar and asks why it matters. Write a brief post that identifies the event, gives enough context to understand it, and explains its historical significance.",
"Write a short historical post centered on November 11, 1918. Explain what changed that day and why the date became symbolically important in several countries.",
"August 15, 1947 is a major date in modern history. Explain what happened in a compact social-media post and mention one consequence that helps a reader understand why the date still matters.",
"Why would an aviation-history page post about December 17, 1903? Explain the event associated with that date and what made it different from earlier attempts at flight.",
"Write a short anniversary post about April 26, 1986. Describe the major event connected with the date and explain why its consequences extended far beyond the immediate location.",
"July 20, 1969 is instantly recognizable to many people but not everyone knows the details. Write a short post explaining what occurred and why it became a global cultural milestone.",
"What made October 24, 1929 historically significant? Explain the day in a social-media post that distinguishes the event itself from the larger economic crisis that followed.",
"A museum account is preparing a post for July 14. Explain the major event associated with July 14, 1789 and why it became a lasting political symbol rather than just another episode of unrest."
],
"science": [
"Sometimes you can smell rain before the rain reaches you. Write a short post explaining where that smell comes from and how it can arrive before the first drops.",
"Why can a metal bench feel much colder than a wooden bench even when both have been outside at exactly the same temperature? Explain it in a way that would work in a short science post.",
"Lightning is seen before thunder is heard, even though both come from the same event. Write a concise social-media explanation of the delay and what determines how long it lasts.",
"People often say the Moon has a 'dark side.' Write a short post explaining what is misleading about that phrase and why we keep seeing nearly the same lunar face from Earth.",
"Why does ice float instead of sinking in liquid water? Explain the unusual property behind it and why it matters beyond a glass of iced water.",
"Write a short post correcting the idea that Earth's seasons are caused mainly by being closer to or farther from the Sun. Explain the real mechanism without using equations.",
"A pressure cooker can prepare food faster even though the heater itself is not necessarily hotter. Explain why in a compact post for curious non-specialists.",
"Why does a sunset often look red or orange while the daytime sky looks blue? Write a short explanation that connects both colors to the same physical process.",
"Microwave ovens often leave some parts of food hotter than others. Explain in a short post why uneven heating happens and why the rotating plate helps.",
"If the Sun disappeared instantaneously in a thought experiment, Earth would not notice immediately. Write a short post explaining the delay and why the change in gravity would not arrive sooner than the change in light."
],
"biology_medicine": [
"Why can someone with a rising fever feel cold enough to shiver even while their body temperature is already high? Explain the apparent contradiction in a short general-audience post.",
"Muscles can hurt more the day after unfamiliar exercise than immediately after it. Write a brief post explaining delayed-onset muscle soreness and correcting the common idea that it is simply 'lactic acid left in the muscles.'",
"Many people notice that one nostril seems more blocked than the other and that the sides can switch over time. Explain the normal nasal cycle in a short post without turning it into medical advice.",
"What actually causes hiccups? Write a concise post explaining the basic reflex involved and why the characteristic sound happens.",
"Fingers wrinkle after spending time in water. Write a short post explaining why this is not simply skin soaking up water and what role the nervous system appears to play.",
"Some people sneeze when they suddenly step into bright sunlight. Explain this phenomenon in a short post and make clear that it is a real inherited reflex rather than an allergy to light.",
"Why don't antibiotics cure ordinary viral infections such as most colds? Write a short explanatory post that distinguishes what antibiotics target from what viruses are.",
"Healing cuts often become itchy. Write a short post explaining several biological reasons this can happen as tissue repairs itself.",
"Jet lag is more than just being tired after a flight. Explain in a short post what happens to the body's circadian timing and why crossing several time zones can make sleep feel wrong at the destination.",
"Why do humans still get goosebumps even though they have relatively little body hair? Write a brief evolutionary explanation suitable for a general social-media audience."
],
"technology": [
"Deleting a file does not always mean its data vanishes from a drive at that instant. Write a short post explaining what deletion usually changes and why recovery can sometimes still be possible.",
"Private or incognito browser mode is often mistaken for online anonymity. Write a concise post explaining what it actually hides, what it does not hide, and who may still be able to see network activity.",
"QR codes can remain readable even when part of the pattern is scratched or covered. Explain in a short post how that is possible without diving into mathematical details.",
"Why can a ZIP file dramatically shrink some files but barely shrink others such as JPEG photos or MP4 videos? Write a short explanation of compression and already-compressed formats.",
"Your browser may show an old version of a website even after the site has been updated. Explain the role of caching in a short post and why refreshing can sometimes fix the mismatch.",
"A phone can estimate where you are without sending a signal to GPS satellites. Write a short post explaining, at a high level, how satellite positioning works and why the phone is mainly listening rather than 'asking the satellite where it is.'",
"What does end-to-end encryption actually mean in a messaging app? Write a compact explanation of who should be able to read the message and what the phrase does not automatically guarantee.",
"Good websites should not need to store your actual password in readable form. Write a short post explaining password hashing and why a stolen password database can still be dangerous.",
"A phone saying '20% battery remaining' is not the same as directly measuring that exactly one fifth of the battery's energy is left. Explain in a short post why battery percentage is an estimate.",
"People talk about putting files 'in the cloud' as if they stop existing on physical computers. Write a short social-media explanation of what cloud storage really means in practical terms."
],
"economics": [
"Inflation can fall while supermarket prices continue to rise. Write a short post explaining how both statements can be true, using a simple everyday example.",
"Why does compound interest become much more noticeable over long periods than over the first few years? Explain the idea in a social-media post without relying on a formula.",
"A currency can strengthen against another currency while people in that country do not suddenly become proportionally richer. Write a short post distinguishing exchange rates from purchasing power and living standards.",
"Central banks raise interest rates partly to cool inflation, but the same move can make mortgages and business loans more expensive. Explain this trade-off in a concise post for non-economists.",
"Write a short post explaining opportunity cost using a normal everyday decision rather than a business-school definition.",
"People often keep spending on a bad plan because they have already invested money or time in it. Explain the sunk-cost fallacy in a short post and why past spending should not determine the next decision.",
"GDP per capita is often used to compare countries, but it is not the same thing as the income of an average resident. Write a short post explaining the difference and why the distinction matters.",
"Falling prices may sound universally good, yet sustained deflation can create problems for an economy. Explain why in a brief social-media post without making it sound like cheaper goods are inherently bad.",
"Someone receives a 5% pay rise during a year when prices rise by 7%. Write a short post explaining the difference between nominal pay and real purchasing power.",
"A very cheap airline ticket can end up costing more than a higher advertised fare once baggage, seat selection, and other extras are added. Use this example to explain why headline price and total economic cost are not always the same thing."
],
"geography": [
"People often use 'Holland' and 'the Netherlands' as if they were exactly the same thing. Write a short post explaining the geographical difference without making the terminology sound more complicated than it is.",
"Great Britain, the United Kingdom, and England are not interchangeable names. Write a concise social-media explanation of how they differ.",
"Chile is unusually long and narrow. Write a short post explaining the major geographical forces and boundaries that helped produce that shape.",
"A monsoon is often described simply as 'a season of heavy rain.' Write a short post explaining what a monsoon actually is and why wind patterns are central to the concept.",
"Norway's coastline contains thousands of fjords. Explain in a short post how glaciers created these landscapes and why the valleys later filled with seawater.",
"Why do many places around the Mediterranean have relatively mild, wet winters and hot, dry summers? Write a concise post describing the broad climate pattern.",
"The surface of the Dead Sea is far below global sea level. Write a short post explaining how a lake can sit below sea level without the world's oceans simply flowing into it.",
"Tokyo and Seoul are both huge East Asian metropolitan areas, but their physical geography and urban form are not identical. Write a short comparison focusing on two or three concrete differences rather than stereotypes.",
"Why are time zones politically irregular instead of forming 24 perfectly straight vertical strips around Earth? Explain in a short post using borders and practical coordination as part of the answer.",
"Iceland and Greenland have names that can sound geographically backwards to a modern visitor. Write a short post explaining where the names came from and why the simple 'one is icy, one is green' joke misses the history."
],
"food_culture": [
"Japanese and Korean cuisines are sometimes grouped together simply because both come from East Asia. Write a short post comparing their typical flavor profiles, staple ingredients, and dining traditions without reducing either cuisine to stereotypes.",
"Espresso and filter coffee can start with the same beans but taste and feel very different. Write a concise post explaining the main differences in brewing method, concentration, and serving style.",
"A sourdough starter can stay alive for years if it is maintained. Write a short post explaining what organisms live in it and why regular feeding matters.",
"Kimchi, sauerkraut, and yogurt are very different foods, yet fermentation is central to all of them. Write a short post explaining what fermentation is and what the microbes are doing.",
"Kosher and halal dietary rules are sometimes treated as interchangeable. Write a careful short post explaining a few important similarities and differences without trying to summarize either religious tradition completely.",
"Sushi does not simply mean 'raw fish.' Write a short post explaining what actually defines sushi and why some common sushi contains no raw seafood at all.",
"People often describe umami as a mysterious 'fifth taste.' Write a concise post explaining what the term refers to, which compounds are involved, and where people commonly encounter it in food.",
"Tea culture in Britain and Japan both gives social importance to tea, but the traditions developed in very different ways. Write a short comparison focused on preparation, setting, and social meaning.",
"Indian food is sometimes described as if there were one national cuisine. Write a short post explaining why regional variation matters, using a few concrete examples of ingredients or cooking traditions.",
"Tacos and burritos are both associated internationally with Mexican food, but they are not simply the same dish in different sizes. Write a short post explaining the basic structural and cultural differences."
],
"language": [
"Japanese uses kanji, hiragana, and katakana in the same writing system. Write a short post explaining what each one is mainly used for and why Japanese did not simply choose one script.",
"English spelling often preserves traces of older pronunciations. Write a short post using one or two examples to explain why spelling and modern pronunciation can diverge so much.",
"Some languages assign grammatical gender to ordinary objects. Write a concise post explaining what grammatical gender is and why it should not be confused with believing that objects literally have biological sex.",
"False friends can make two related languages look deceptively easy to understand. Write a short post explaining the idea with a clear example from any language pair.",
"Arabic writing often leaves short vowels unwritten in everyday text. Explain in a short post how fluent readers can still understand words and when vowel marks are more likely to appear.",
"Many Hebrew words are built around consonantal roots. Write a short social-media explanation of how a root can connect families of related words without implying that every word fits the pattern perfectly.",
"People sometimes call Mandarin and Cantonese 'dialects' and assume that means speakers can automatically understand one another. Write a short post explaining why the linguistic and political terminology is more complicated.",
"Turkish can build long words by adding a sequence of suffixes. Write a concise post explaining agglutination and why one Turkish word can express information that English might need several words to convey.",
"Sign language is not one universal language used everywhere. Write a short post explaining why different sign languages exist and why American Sign Language and British Sign Language are not simply signed versions of the same spoken language.",
"Languages constantly borrow words from one another. Write a short post explaining why borrowed vocabulary does not mean a language is becoming 'less authentic,' and give one familiar example."
],
"arts_culture": [
"Why did Impressionist paintings look so radical to many nineteenth-century viewers? Write a short post explaining what the painters were doing differently and how exhibition practices helped shape the movement.",
"Picasso's Guernica is often reproduced as an anti-war image. Write a concise post explaining the historical event behind the painting and a few features that contribute to its impact.",
"The Mona Lisa was famous before it was stolen in 1911, but the theft changed its public profile dramatically. Write a short post explaining why the painting became such a global icon without reducing the answer to one cause.",
"Bauhaus design is associated with simple geometry and functionalism, but it was more than a visual style. Write a short post explaining what the school was trying to do and why its influence spread so widely.",
"Jazz improvisation does not mean musicians are simply making random notes up on the spot. Write a short post explaining how improvisation works within harmony, rhythm, style, and shared musical conventions.",
"Older films were made for many different screen shapes. Write a short post explaining what an aspect ratio is and why cropping a classic film to fill a modern television can remove part of the original composition.",
"A work entering the public domain does not mean nobody created it or that every later version is automatically free to copy. Write a short post explaining the basic distinction between an original work and newer adaptations or recordings.",
"Film restoration can involve much more than making an old movie sharper. Write a short post explaining what restorers may need to repair, reconstruct, or decide when working from damaged historical material.",
"Ancient Greek theatre used masks, but not merely as decoration. Write a short post explaining some practical and dramatic functions masks served in large outdoor performances.",
"A book can become culturally important even if it was not an immediate bestseller. Write a short post using one well-known example to explain how reputation can grow through later readers, critics, schools, adaptations, or historical events."
],
"misconceptions": [
"People say lightning never strikes the same place twice. Write a short post explaining why the saying is physically wrong and why tall structures can be struck repeatedly.",
"Goldfish are often said to have a memory of only a few seconds. Write a concise post explaining what research and ordinary training observations tell us about that claim.",
"Many parents have heard that sugar reliably makes children hyperactive. Write a careful short post explaining why the evidence is much weaker than the popular belief suggests.",
"Does cracking your knuckles cause arthritis? Write a short post separating what is known about the popping sound from what evidence says about the arthritis claim.",
"Shaving is often said to make hair grow back thicker and darker. Write a brief post explaining why regrowth can look or feel different without the hair follicle actually becoming thicker.",
"Bats are not actually blind. Write a short post explaining what echolocation adds to their senses and why the phrase 'blind as a bat' is misleading.",
"The Great Wall of China is often described as visible from the Moon with the naked eye. Write a short post explaining why that claim is misleading and what astronauts actually report about seeing human-made structures from space.",
"Swallowed chewing gum is sometimes said to stay in the stomach for seven years. Write a concise post explaining what normally happens to gum after it is swallowed.",
"Cold weather by itself does not create a viral infection, yet respiratory infections often become more common in colder seasons. Write a short post explaining why both statements can be true.",
"A popular claim says toilets always swirl in opposite directions in the northern and southern hemispheres. Write a short post explaining why household toilets are dominated by their design and initial water motion rather than the Coriolis effect."
]
}

rows = []
idx = 1
for domain, topics in TOPICS.items():
    assert len(topics) == 10, (domain, len(topics))
    for topic in topics:
        task = f"{WRAPPER}\n\nTOPIC:\n{topic}"
        rows.append({"prompt_id": f"p{idx:03d}", "language": "en", "subset": "primary_english", "domain": domain, "task": task})
        idx += 1
assert len(rows) == 100
out = Path(__file__).with_name("prompts.jsonl")
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print(f"wrote {len(rows)} prompts to {out}")
