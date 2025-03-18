import pdfplumber
import re
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class Artwork:
    """Data class for artwork information."""
    id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    dimensions: Optional[str] = None
    material: Optional[str] = None
    year: Optional[str] = None
    description: Optional[str] = None
    page_number: int = 0
    confidence: float = 0.0

class PDFArtworkExtractor:
    """Extract artwork information from PDF files."""
    
    def __init__(self):
        # Regular expressions for identifying artwork information
        self.title_patterns = [
            r"Title:\s*(.*?)(?:\n|$)",
            r"\"(.*?)\"",
            r"'(.*?)'",
        ]
        
        self.artist_patterns = [
            r"Artist:\s*(.*?)(?:\n|$)",
            r"By\s+(.*?)(?:,|\n|$)",
            r"(.*?)\s+\(\d{4}-\d{4}\)",
        ]
        
        self.dimensions_patterns = [
            r"Dimensions:\s*(.*?)(?:\n|$)",
            r"Size:\s*(.*?)(?:\n|$)",
            r"(\d+\.?\d*\s*[x×]\s*\d+\.?\d*\s*[x×]?\s*\d*\.?\d*\s*(?:cm|in|mm))",
        ]
        
        self.material_patterns = [
            r"Material(?:s)?:\s*(.*?)(?:\n|$)",
            r"Medium:\s*(.*?)(?:\n|$)",
            r"(?:Oil on canvas|Acrylic on paper|Mixed media|Sculpture|Photography|Digital print|Watercolor)",
        ]
        
        self.year_patterns = [
            r"Year:\s*(\d{4})",
            r"Date:\s*(.*?)(?:\n|$)",
            r"(\d{4})\s*(?:\-\s*\d{4})?",
        ]

    def extract_with_pattern(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract information using a list of regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def extract_artworks(self, pdf_path: str) -> List[Artwork]:
        """Extract artwork information from a PDF file."""
        artworks = []
        artwork_id = 1
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                # Extract images
                images = page.images
                
                # Process page content
                paragraphs = text.split('\n\n')
                
                for para_idx, paragraph in enumerate(paragraphs):
                    # Simple heuristic: if paragraph contains potential artwork info
                    if any(term in paragraph.lower() for term in ['title', 'artist', 'oil', 'canvas', 'cm', 'inch']):
                        title = self.extract_with_pattern(paragraph, self.title_patterns)
                        artist = self.extract_with_pattern(paragraph, self.artist_patterns)
                        dimensions = self.extract_with_pattern(paragraph, self.dimensions_patterns)
                        material = self.extract_with_pattern(paragraph, self.material_patterns)
                        year = self.extract_with_pattern(paragraph, self.year_patterns)
                        
                        # Only create artwork if we have at least a title or artist
                        if title or artist:
                            artwork = Artwork(
                                id=f"art_{artwork_id}",
                                title=title,
                                artist=artist,
                                dimensions=dimensions,
                                material=material,
                                year=year,
                                description=paragraph,
                                page_number=page_num,
                                confidence=self._calculate_confidence(title, artist, dimensions, material, year)
                            )
                            artworks.append(artwork)
                            artwork_id += 1
        
        return artworks
    
    def _calculate_confidence(self, title, artist, dimensions, material, year):
        """Calculate confidence score based on completeness of extracted data."""
        total_fields = 5
        found_fields = sum(1 for field in [title, artist, dimensions, material, year] if field)
        return found_fields / total_fields