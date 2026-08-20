# Smart Tutor Frontend

The Smart Tutor frontend feature lives in this folder. It provides the PDF-first tutor experience, including PDF upload, document preview, chat, citations, and Markdown rendering.

## Files

- `ConnectedTutor.jsx`: Tutor page, upload flow, chat state, and API interaction.
- `PdfViewer.jsx`: PDF preview and citation page navigation.
- `smartTutorService.js`: Smart Tutor API client.
- `markdown.css`: Markdown content styles.

## API

The feature sends requests to:

```text
POST /api/smart-tutor/tutor/
```

Flashcard requests use:

```text
POST /api/smart-tutor/flashcards/
```

The chat recognizes requests such as `generate 5 flashcards on TCP`, sends the active PDF as reference, and shows a `Launch Flashcards` button when the cards are ready. The popup displays each question and flips horizontally to reveal its answer.

Requests such as `generate 4 MCQs on TCP` work the same way. The MCQ popup shows four options per question and gives immediate visual feedback when an option is selected.

PDF requests use `FormData` with:

- `message`: Student question.
- `file`: PDF document, up to 20 MB.

Responses are rendered as Markdown. GitHub-Flavored Markdown is supported, including tables and fenced code blocks.

## Development

From the `frontend` directory:

```bash
npm run dev
npm run lint
npm run build
```
