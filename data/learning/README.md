# NITRO AI — Local Learning Memory

NITRO stores chat history in the browser's local storage under `nitro-chat-v1`.
User-approved learned facts are stored as JSON under `nitro-learning-v1`.

## Teach NITRO

In chat, send a message beginning with one of these phrases:

- `یاد بگیر که SCP-999 موجودی دوستانه است`
- `به خاطر بسپار که پروژه من NITRO AI نام دارد`

NITRO saves the fact in the browser profile and can recall it in later chats on the same browser and website origin. Use the **حافظه نیترو** sidebar item to review or delete saved facts and export/import `nitro-memory.json`.

## Important limitations

- Browser local storage is persistent browser data, not a file automatically written into a Windows folder. Export JSON to create a portable file on the PC.
- Chat messages are retained as conversation history (the latest 250 message snippets are also logged in the learning store); they are not automatically treated as verified facts. This avoids turning every question, typo, or incorrect claim into permanent knowledge.
- Local matching is keyword-based. It is not model training and does not create a new language model.
- Clearing browser site data can erase local memory unless it was exported first.
- GitHub Pages is static hosting; it cannot write to arbitrary files on the user's PC.
