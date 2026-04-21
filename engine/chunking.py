from __future__ import annotations

import re
from typing import Dict, Iterable, List


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_paragraphs(text: str) -> List[str]:
    normalized = _normalize_whitespace(text)
    return [p.strip() for p in normalized.split("\n\n") if p.strip()]


def _slugify(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    stem = stem.lower().replace("-", "_").replace(" ", "_")
    stem = re.sub(r"[^a-z0-9_]", "", stem)
    return stem


def semantic_chunk_document(
    source_name: str,
    text: str,
    max_chars: int = 1000,
    overlap_paragraphs: int = 1,
) -> List[Dict]:
    """
    Build semantically coherent chunks using paragraph grouping.
    This preserves section meaning better than fixed-size character splits.
    """
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    source_stem = _slugify(source_name)
    chunks: List[Dict] = []

    i = 0
    chunk_index = 0
    while i < len(paragraphs):
        current_parts: List[str] = []
        current_len = 0
        j = i

        while j < len(paragraphs):
            para = paragraphs[j]
            additional = len(para) + (2 if current_parts else 0)
            if current_parts and current_len + additional > max_chars:
                break

            current_parts.append(para)
            current_len += additional
            j += 1

            if not current_parts and len(para) >= max_chars:
                break

        chunk_text = "\n\n".join(current_parts).strip()
        chunk_id = f"{source_stem}_{chunk_index}"

        chunks.append(
            {
                "chunk_id": chunk_id,
                "source": source_name,
                "source_stem": source_stem,
                "chunk_index": chunk_index,
                "text": chunk_text,
                "char_length": len(chunk_text),
            }
        )

        chunk_index += 1
        if j >= len(paragraphs):
            break

        i = max(j - overlap_paragraphs, i + 1)

    return chunks


def semantic_chunk_corpus(
    docs: Dict[str, str],
    max_chars: int = 1000,
    overlap_paragraphs: int = 1,
) -> List[Dict]:
    all_chunks: List[Dict] = []
    for source_name, text in docs.items():
        all_chunks.extend(
            semantic_chunk_document(
                source_name=source_name,
                text=text,
                max_chars=max_chars,
                overlap_paragraphs=overlap_paragraphs,
            )
        )
    return all_chunks


def build_chunk_lookup(chunks: Iterable[Dict]) -> Dict[str, Dict]:
    return {chunk["chunk_id"]: chunk for chunk in chunks}
