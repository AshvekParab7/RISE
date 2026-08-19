def chunk_text(text, size=1200, overlap=150):
    clean = ' '.join(text.split())
    if not clean: return []
    chunks = []; start = 0; index = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        chunks.append({'text': clean[start:end], 'chunk_index': index})
        if end == len(clean): break
        start = end - overlap; index += 1
    return chunks
