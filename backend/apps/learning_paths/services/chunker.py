def chunk_transcript(segments, max_seconds=480, max_characters=6000):
    chunks = []
    current = []
    current_chars = 0
    start = None
    for segment in segments:
        if start is None:
            start = segment['start']
        end = segment['start'] + segment['duration']
        exceeds_time = current and end - start > max_seconds
        exceeds_size = current and current_chars + len(segment['text']) > max_characters
        if exceeds_time or exceeds_size:
            chunks.append(_build_chunk(current))
            current = []
            current_chars = 0
            start = segment['start']
        current.append(segment)
        current_chars += len(segment['text']) + 1
    if current:
        chunks.append(_build_chunk(current))
    return chunks


def _build_chunk(segments):
    return {
        'start_seconds': segments[0]['start'],
        'end_seconds': round(segments[-1]['start'] + segments[-1]['duration'], 3),
        'text': ' '.join(segment['text'] for segment in segments),
        'segments': segments,
    }
