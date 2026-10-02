"""
@file: rag_knowledge.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

﻿"""
DEM3T3R V1 RAG Knowledge Base.
Provides vector-style semantic matching over agricultural plant pathology
and pest management knowledge documents across all 16 crops.
"""
import re
from typing import List, Dict, Any

PATHOLOGY_DATABASE = [
    {
        "crop": "tomato",
        "disease": "tomato_early_blight",
        "pathogen": "Alternaria solani",
        "organic_treatment": "Apply copper sulfate or Bacillus subtilis spray. Remove lower infected foliage to enhance air circulation.",
        "chemical_treatment": "Mancozeb 75 WP (2g/L) or Chlorothalonil 75 WP (2g/L). Alternate with Azoxystrobin to prevent resistance.",
        "cultural_practices": "Mulch soil surface, avoid overhead irrigation, ensure 60cm row spacing."
    },
    {
        "crop": "tomato",
        "disease": "tomato_late_blight",
        "pathogen": "Phytophthora infestans",
        "organic_treatment": "Copper octanoate spray; immediately destroy severely infected plants.",
        "chemical_treatment": "Metalaxyl-M + Mancozeb (Ridomil Gold) at 2.5g/L or Cymoxanil.",
        "cultural_practices": "Ensure proper drainage, avoid working in wet fields, plant resistant cultivars."
    },
    {
        "crop": "potato",
        "disease": "potato_late_blight",
        "pathogen": "Phytophthora infestans",
        "organic_treatment": "Preventative copper hydroxide applications before canopy closure.",
        "chemical_treatment": "Chlorothalonil (2.0 L/ha) or Dimethomorph + Mancozeb.",
        "cultural_practices": "Hilling up to protect tubers, certified disease-free seed tubers."
    },
    {
        "crop": "rice",
        "disease": "rice_blast",
        "pathogen": "Magnaporthe oryzae",
        "organic_treatment": "Seed treatment with Pseudomonas fluorescens (10g/kg).",
        "chemical_treatment": "Tricyclazole 75 WP (0.6g/L) or Isoprothiolane 40 EC (1.5ml/L).",
        "cultural_practices": "Avoid excess nitrogen fertilizer, maintain recommended standing water level."
    },
    {
        "crop": "chilli",
        "disease": "chilli_leaf_curl",
        "pathogen": "Chilli Leaf Curl Virus (Begomovirus transmitted by Whitefly)",
        "organic_treatment": "Neem oil 1% spray to manage whitefly vector populations.",
        "chemical_treatment": "Imidacloprid 17.8 SL (0.3ml/L) or Diafenthiuron 50 WP (1g/L) to control vectors.",
        "cultural_practices": "Yellow sticky traps (15 traps/acre), barrier crops like maize."
    },
    {
        "crop": "tea",
        "disease": "tea_blister_blight",
        "pathogen": "Exobasidium vexans",
        "organic_treatment": "Regulate tea shade canopy to allow sunlight penetration.",
        "chemical_treatment": "Copper oxychloride (COC) + Nickel chloride mixture (1:1 at 200g/ha).",
        "cultural_practices": "Maintain regular 5-7 day plucking rounds, avoid harvesting wet leaves."
    },
    {
        "crop": "corn",
        "disease": "corn_northern_leaf_blight",
        "pathogen": "Exserohilum turcicum",
        "organic_treatment": "Bio-fungicide Trichoderma harzianum soil application.",
        "chemical_treatment": "Azoxystrobin + Difenoconazole (0.1%) or Propiconazole 25 EC (1ml/L).",
        "cultural_practices": "Deep tillage of crop residues, crop rotation with non-gramineous crops."
    },
    {
        "crop": "anthurium",
        "disease": "anthurium_bacterial_blight",
        "pathogen": "Xanthomonas axonopodis pv. dieffenbachiae",
        "organic_treatment": "Strict sanitation; sanitize shears in 70% alcohol between cuts.",
        "chemical_treatment": "Streptomycin sulphate + Tetracycline hydrochloride (0.5g/L) preventative.",
        "cultural_practices": "Reduce overhead sprinkler moisture, keep greenhouse relative humidity below 80%."
    }
]

class RAGKnowledgeBase:
    def __init__(self):
        self.documents = PATHOLOGY_DATABASE

    def query(self, crop: str, query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Keyword / similarity search over pathology knowledge base."""
        crop_lower = crop.lower()
        query_words = set(re.findall(r'\w+', query_text.lower()))
        
        scored_docs = []
        for doc in self.documents:
            score = 0.0
            if doc["crop"] == crop_lower:
                score += 5.0
            
            doc_text = f"{doc['disease']} {doc['pathogen']} {doc['organic_treatment']} {doc['chemical_treatment']}".lower()
            for word in query_words:
                if word in doc_text:
                    score += 2.0
                    
            if score > 0:
                scored_docs.append((score, doc))
                
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]
