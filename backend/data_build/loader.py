import os
import re
from typing import List, Dict, Any, Tuple

class MarkdownDocumentLoader:
    def __init__(self, sample_docs_dir: str = "knowledge_base/sample_docs"):
        self.sample_docs_dir = sample_docs_dir

    def parse_metadata_header(self, text: str, file_name: str) -> Tuple[Dict[str, Any], str]:
        """Parses standardized metadata headers from Markdown documents."""
        metadata = {
            "doc_id": file_name.replace(".md", ""),
            "doc_title": file_name.replace(".md", "").replace("_", " ").title(),
            "version": "1.0",
            "status": "CURRENT",
            "effective_date": "2025-01-01",
            "department": "General",
            "branch_id": "Global",
            "region": "Global",
            "classification": "Internal Policy",
            "file_name": file_name
        }
        
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if title_match:
            metadata["doc_title"] = title_match.group(1).strip()

        header_patterns = {
            "doc_id": r'\*\*Document ID\*\*:\s*(.+)',
            "version": r'\*\*Version\*\*:\s*(.+)',
            "status": r'\*\*Status\*\*:\s*(.+)',
            "effective_date": r'\*\*Effective Date\*\*:\s*(.+)',
            "department": r'\*\*Department\*\*:\s*(.+)',
            "branch_id": r'\*\*Branch ID\*\*:\s*(.+)',
            "region": r'\*\*Region\*\*:\s*(.+)',
            "classification": r'\*\*Classification\*\*:\s*(.+)'
        }
        
        for key, pattern in header_patterns.items():
            match = re.search(pattern, text)
            if match:
                metadata[key] = match.group(1).strip()
                
        body_start = text.find("---")
        body_text = text[body_start + 3:].strip() if body_start != -1 else text.strip()
        return metadata, body_text

    def _sliding_sentence_overlap_chunking(self, text: str, max_words: int = 80, overlap_sentences: int = 1) -> List[str]:
        """
        Sliding Window Chunking with Sentence Overlap:
        - Never breaks mid-sentence.
        - Includes 1-sentence overlap between consecutive chunks so context is never cut off.
        - Strictly operates WITHIN a single parent section (never bleeds into other sections).
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        all_sentences = []
        
        for p in paragraphs:
            s_list = re.split(r'(?<=[.!?])\s+', p)
            all_sentences.extend([s.strip() for s in s_list if s.strip()])
            
        if not all_sentences:
            return [text]

        chunks = []
        i = 0
        while i < len(all_sentences):
            current_chunk = []
            current_word_count = 0
            
            j = i
            while j < len(all_sentences):
                sentence = all_sentences[j]
                words_in_sentence = len(sentence.split())
                
                if current_word_count + words_in_sentence > max_words and current_chunk:
                    break
                    
                current_chunk.append(sentence)
                current_word_count += words_in_sentence
                j += 1
                
            chunks.append(' '.join(current_chunk))
            
            sentences_used = len(current_chunk)
            step = max(1, sentences_used - overlap_sentences)
            i += step
            
        return chunks if chunks else [text]

    def split_into_parents_and_children(self, text: str, file_name: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Guaranteed 2-Tier Chunking with Unique Versioned IDs:
        1. Parent Sections: Split by ## or ### Section headers (~150-300 words). Strict section firewalls.
        2. Child Chunks: Sliding Sentence Window (~50-80 words) with 1-sentence overlap WITHIN section.
        """
        doc_metadata, body_text = self.parse_metadata_header(text, file_name)
        
        # Format version string safely (e.g. v1.0 -> v1_0)
        safe_version = doc_metadata['version'].replace('.', '_')
        
        # Hard Firewall Split by ## or ### section headers
        sections = re.split(r'\n(?=#{2,3}\s+)', body_text)
        
        parents = []
        children = []
        
        for p_idx, sec in enumerate(sections):
            sec_clean = sec.strip()
            if not sec_clean:
                continue
                
            sec_title_match = re.search(r'^#{2,3}\s+(.+)$', sec_clean, re.MULTILINE)
            sec_title = sec_title_match.group(1).strip() if sec_title_match else f"Section {p_idx+1}"
            
            # UNIQUE PARENT ID: Includes doc_id + version to prevent duplicate IDs across doc versions!
            parent_id = f"{doc_metadata['doc_id']}_v{safe_version}_p{p_idx+1}"
            
            parent_obj = {
                "parent_id": parent_id,
                "section_title": sec_title,
                "content": sec_clean,
                "metadata": doc_metadata
            }
            parents.append(parent_obj)
            
            lines = sec_clean.split('\n')
            body_lines = '\n'.join(lines[1:]).strip() if lines[0].startswith('#') else sec_clean
            
            child_texts = self._sliding_sentence_overlap_chunking(body_lines, max_words=80, overlap_sentences=1)
            
            for c_idx, child_text in enumerate(child_texts):
                # UNIQUE CHILD ID
                child_id = f"{parent_id}_c{c_idx+1}"
                
                child_meta = {}
                for k, v in doc_metadata.items():
                    child_meta[k] = str(v) if v is not None else ""
                    
                child_meta["parent_id"] = str(parent_id)
                child_meta["section_title"] = str(sec_title)
                
                children.append({
                    "child_id": child_id,
                    "content": child_text,
                    "metadata": child_meta
                })
                
        return doc_metadata, parents, children
