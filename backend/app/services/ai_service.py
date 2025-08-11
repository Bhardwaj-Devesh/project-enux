import google.generativeai as genai
from typing import List, Dict, Any, Optional
import asyncio
import aiofiles
import PyPDF2
import pandas as pd
import json
import markdown
from io import BytesIO
import zipfile
import os
import numpy as np
from app.config import settings


class AIService:
    def __init__(self):
        self._model = None
        self._embedding_model = None
        self._configured = False
    
    def _configure(self):
        """Lazy configuration of Gemini models"""
        if not self._configured:
            genai.configure(api_key=settings.google_api_key)
            self._configured = True
    
    @property
    def model(self):
        """Lazy initialization of Gemini model"""
        if self._model is None:
            self._configure()
            self._model = genai.GenerativeModel(settings.gemini_model)
        return self._model
    
    @property
    def embedding_model(self):
        """Lazy initialization of Gemini embedding model"""
        if self._embedding_model is None:
            self._configure()
            self._embedding_model = genai.GenerativeModel('embedding-001')
        return self._embedding_model
    
    async def extract_text_from_file(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Extract text content from various file types"""
        try:
            if content_type == "application/pdf":
                return await self._extract_text_from_pdf(file_content)
            elif content_type in ["text/plain", "text/markdown"]:
                return file_content.decode('utf-8')
            elif content_type in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                return await self._extract_text_from_spreadsheet(file_content, content_type)
            elif content_type in ["application/json"]:
                return await self._extract_text_from_json(file_content)
            elif content_type in ["application/zip", "application/x-zip-compressed"]:
                return await self._extract_text_from_zip(file_content)
            else:
                # Try to decode as text
                try:
                    return file_content.decode('utf-8')
                except:
                    return f"Binary file: {filename}"
        except Exception as e:
            return f"Error extracting text from {filename}: {str(e)}"
    
    async def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    async def _extract_text_from_spreadsheet(self, file_content: bytes, content_type: str) -> str:
        """Extract text from spreadsheet files"""
        try:
            if content_type == "text/csv":
                df = pd.read_csv(BytesIO(file_content))
            else:
                df = pd.read_excel(BytesIO(file_content))
            
            # Convert to string representation
            return df.to_string()
        except Exception as e:
            return f"Error extracting spreadsheet text: {str(e)}"
    
    async def _extract_text_from_json(self, file_content: bytes) -> str:
        """Extract text from JSON file"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error extracting JSON text: {str(e)}"
    
    async def _extract_text_from_zip(self, file_content: bytes) -> str:
        """Extract text from ZIP file"""
        try:
            text_content = ""
            with zipfile.ZipFile(BytesIO(file_content), 'r') as zip_file:
                for file_info in zip_file.filelist:
                    if not file_info.is_dir():
                        filename = file_info.filename
                        if filename.endswith(('.txt', '.md', '.csv', '.json')):
                            with zip_file.open(filename) as file:
                                content = file.read()
                                try:
                                    text_content += f"\n--- {filename} ---\n"
                                    text_content += content.decode('utf-8')
                                except:
                                    text_content += f"\n--- {filename} (binary) ---\n"
            return text_content
        except Exception as e:
            return f"Error extracting ZIP text: {str(e)}"
    
    async def generate_summary(self, text_content: str, title: str) -> str:
        """Generate a summary of the playbook content using Gemini"""
        try:
            prompt = f"""
            Analyze the following playbook content and create a comprehensive summary.
            
            Playbook Title: {title}
            
            Content:
            {text_content[:8000]}  # Limit content to avoid token limits
            
            Please provide a concise but comprehensive summary that includes:
            1. Main topics and themes
            2. Key strategies or methodologies
            3. Target audience or use cases
            4. Important insights or recommendations
            
            Summary:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def extract_tags(self, text_content: str, title: str, description: str) -> List[str]:
        """Extract relevant tags from playbook content using Gemini"""
        try:
            prompt = f"""
            Analyze the following playbook and extract relevant tags.
            
            Title: {title}
            Description: {description}
            Content: {text_content[:4000]}
            
            Extract 3-8 relevant tags that best describe this playbook. Consider:
            - Business domains (e.g., GTM, fundraising, marketing, sales)
            - Company stages (e.g., pre-seed, seed, Series A, growth)
            - Functional areas (e.g., strategy, operations, finance)
            - Industry focus (e.g., SaaS, e-commerce, healthcare)
            
            Return only the tags as a comma-separated list, no explanations.
            """
            
            response = self.model.generate_content(prompt)
            tags_text = response.text.strip()
            tags = [tag.strip() for tag in tags_text.split(',')]
            return [tag for tag in tags if tag]  # Remove empty tags
        except Exception as e:
            return ["business", "strategy"]  # Default tags
    
    async def classify_stage(self, text_content: str, title: str, description: str) -> str:
        """Classify the recommended stage for the playbook using Gemini"""
        try:
            prompt = f"""
            Analyze the following playbook and determine the recommended company stage.
            
            Title: {title}
            Description: {description}
            Content: {text_content[:3000]}
            
            Classify into one of these stages:
            - pre-seed: Very early stage, idea validation, MVP development
            - seed: Early stage, initial funding, product-market fit
            - Series A: Growth stage, scaling, market expansion
            - Series B+: Later stage, optimization, international expansion
            - growth: General growth strategies for any stage
            
            Return only the stage name, no explanations.
            """
            
            response = self.model.generate_content(prompt)
            stage = response.text.strip().lower()
            valid_stages = ["pre-seed", "seed", "series a", "series b+", "growth"]
            return stage if stage in valid_stages else "growth"
        except Exception as e:
            return "growth"  # Default stage
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create vector embedding for text using Gemini"""
        try:
            # Combine title, description, and content for embedding
            combined_text = text[:8000]  # Limit to avoid token limits
            
            # Use Gemini's embedding model
            embedding = self.embedding_model.embed_content(combined_text)
            
            # Convert to list of floats
            return embedding.embedding
        except Exception as e:
            # Return zero vector as fallback
            return [0.0] * settings.vector_dimension
    
    async def process_playbook_files(self, files: List[Dict[str, Any]], title: str, description: str) -> Dict[str, Any]:
        """Process all files in a playbook and generate AI insights"""
        try:
            # Extract text from all files
            all_text = ""
            for file_info in files:
                text_content = await self.extract_text_from_file(
                    file_info['content'],
                    file_info['filename'],
                    file_info['content_type']
                )
                all_text += f"\n\n--- {file_info['filename']} ---\n{text_content}"
            
            # Generate AI insights in parallel
            summary_task = self.generate_summary(all_text, title)
            tags_task = self.extract_tags(all_text, title, description)
            stage_task = self.classify_stage(all_text, title, description)
            embedding_task = self.create_embedding(f"{title}\n{description}\n{all_text}")
            
            # Wait for all tasks to complete
            summary, tags, stage, embedding = await asyncio.gather(
                summary_task, tags_task, stage_task, embedding_task
            )
            
            return {
                "summary": summary,
                "tags": tags,
                "stage": stage,
                "embedding": embedding,
                "processed_text": all_text[:1000]  # Store first 1000 chars for reference
            }
        except Exception as e:
            return {
                "summary": f"Error processing files: {str(e)}",
                "tags": ["business", "strategy"],
                "stage": "growth",
                "embedding": [0.0] * settings.vector_dimension,
                "processed_text": ""
            }


# Global instance
ai_service = AIService() 
