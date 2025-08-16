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
import time
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
            # Use the correct embedding model name
            self._embedding_model = 'models/embedding-001'
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
        """Extract text from PDF file (optimized for speed)"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            
            # Limit to first 5 pages for faster processing
            max_pages = min(5, len(pdf_reader.pages))
            
            for i in range(max_pages):
                page_text = pdf_reader.pages[i].extract_text()
                text += page_text + "\n"
                
                # Limit total text length for faster AI processing
                if len(text) > 3000:
                    text = text[:3000] + "..."
                    break
            
            return text
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    async def _extract_text_from_spreadsheet(self, file_content: bytes, content_type: str) -> str:
        """Extract text from spreadsheet files (optimized for speed)"""
        try:
            if content_type == "text/csv":
                df = pd.read_csv(BytesIO(file_content))
            else:
                df = pd.read_excel(BytesIO(file_content))
            
            # Limit rows and columns for faster processing
            if len(df) > 50:
                df = df.head(50)  # First 50 rows
            if len(df.columns) > 10:
                df = df.iloc[:, :10]  # First 10 columns
            
            # Convert to string representation with limited output
            text = df.to_string(max_rows=20, max_cols=5)
            
            # Limit total length
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            return text
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
    
    async def generate_summary_optimized(self, content: str, title: str) -> str:
        """Generate a summary using optimized, minimal content"""
        try:
            start_time = time.time()
            
            # Use only the first 500 characters for ultra-fast processing
            short_content = content[:500] if len(content) > 500 else content
            
            prompt = f"Summarize: {title} - {short_content}"
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            print(f"📝 Summary generated in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def generate_summary(self, text_content: str, title: str) -> str:
        """Generate a summary of the playbook content using Gemini"""
        try:
            start_time = time.time()
            
            # Preprocess and limit content for faster processing
            processed_content = self._preprocess_content_for_ai(text_content[:2000])  # Reduced from 8000
            
            prompt = f"""
            Create a concise summary of this playbook.
            
            Title: {title}
            Content: {processed_content}
            
            Summary (2-3 sentences):
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            print(f"📝 Summary generated in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def extract_tags_optimized(self, content: str, title: str) -> List[str]:
        """Extract tags using optimized, minimal content"""
        try:
            start_time = time.time()
            
            # Use only the first 300 characters for ultra-fast processing
            short_content = content[:300] if len(content) > 300 else content
            
            prompt = f"Tags for '{title}': {short_content}"
            
            response = self.model.generate_content(prompt)
            tags_text = response.text.strip()
            tags = [tag.strip() for tag in tags_text.split(',')]
            result = [tag for tag in tags if tag][:6]  # Limit to 6 tags
            
            print(f"🏷️ Tags extracted in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            return ["business", "strategy"]  # Default tags
    
    async def extract_tags(self, text_content: str, title: str, description: str) -> List[str]:
        """Extract relevant tags from playbook content using Gemini"""
        try:
            start_time = time.time()
            
            # Preprocess and limit content for faster processing
            processed_content = self._preprocess_content_for_ai(text_content[:1000])  # Reduced from 4000
            
            prompt = f"""
            Extract 3-6 tags for this playbook.
            
            Title: {title}
            Description: {description}
            Content: {processed_content}
            
            Return only tags as comma-separated list (e.g., sales,strategy,startup):
            """
            
            response = self.model.generate_content(prompt)
            tags_text = response.text.strip()
            tags = [tag.strip() for tag in tags_text.split(',')]
            result = [tag for tag in tags if tag][:6]  # Limit to 6 tags
            
            print(f"🏷️ Tags extracted in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            return ["business", "strategy"]  # Default tags
    
    async def process_playbook_combined(self, content: str, title: str, description: str) -> Dict[str, Any]:
        """Process playbook with single combined AI call for maximum efficiency"""
        try:
            start_time = time.time()
            
            # Use optimized content length
            short_content = content[:800] if len(content) > 800 else content
            
            prompt = f"""
You are an assistant. Given the playbook content below:

Title: {title}
Description: {description}
Content: {short_content}

Return a JSON with fields:
- summary: concise 2-3 sentences
- tags: list of 3-6 keywords
- stage: one of ["pre-seed","seed","series a","series b+","growth"]

JSON response:
"""
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            try:
                # Clean the response text to extract JSON
                response_text = response.text.strip()
                
                # Find JSON in the response (in case there's extra text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # Fallback parsing if JSON structure is not found
                    raise ValueError("No JSON structure found in response")
                
                # Validate and clean the results
                summary = result.get("summary", "No summary available")
                tags = result.get("tags", ["business", "strategy"])
                stage = result.get("stage", "growth")
                
                # Ensure tags is a list and limit to 6
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(',')]
                tags = [tag for tag in tags if tag][:6]
                
                # Validate stage
                valid_stages = ["pre-seed", "seed", "series a", "series b+", "growth"]
                if stage not in valid_stages:
                    stage = "growth"
                
                print(f"🚀 Combined AI processing completed in {time.time() - start_time:.2f}s")
                
                return {
                    "summary": summary,
                    "tags": tags,
                    "stage": stage
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ JSON parsing failed: {e}")
                # Fallback to default values
                return {
                    "summary": f"Summary for {title}",
                    "tags": ["business", "strategy"],
                    "stage": "growth"
                }
                
        except Exception as e:
            print(f"❌ Combined AI processing failed: {e}")
            # Return default values
            return {
                "summary": f"Summary for {title}",
                "tags": ["business", "strategy"],
                "stage": "growth"
            }
    
    async def classify_stage_optimized(self, content: str, title: str) -> str:
        """Classify stage using optimized, minimal content"""
        try:
            start_time = time.time()
            
            # Use only the first 200 characters for ultra-fast processing
            short_content = content[:200] if len(content) > 200 else content
            
            prompt = f"Stage for '{title}': {short_content}"
            
            response = self.model.generate_content(prompt)
            stage = response.text.strip().lower()
            valid_stages = ["pre-seed", "seed", "series a", "series b+", "growth"]
            result = stage if stage in valid_stages else "growth"
            
            print(f"📈 Stage classified in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            return "growth"  # Default stage
    
    async def classify_stage(self, text_content: str, title: str, description: str) -> str:
        """Classify the recommended stage for the playbook using Gemini"""
        try:
            start_time = time.time()
            
            # Preprocess and limit content for faster processing
            processed_content = self._preprocess_content_for_ai(text_content[:800])  # Reduced from 3000
            
            prompt = f"""
            Classify this playbook's stage.
            
            Title: {title}
            Description: {description}
            Content: {processed_content}
            
            Return only: pre-seed, seed, series a, series b+, or growth
            """
            
            response = self.model.generate_content(prompt)
            stage = response.text.strip().lower()
            valid_stages = ["pre-seed", "seed", "series a", "series b+", "growth"]
            result = stage if stage in valid_stages else "growth"
            
            print(f"📈 Stage classified in {time.time() - start_time:.2f}s")
            return result
        except Exception as e:
            return "growth"  # Default stage
    
    def _preprocess_content_for_ai(self, content: str) -> str:
        """Preprocess content for faster AI processing"""
        try:
            # Remove excessive whitespace and newlines
            content = ' '.join(content.split())
            
            # Remove common noise patterns
            content = content.replace('---', '')
            content = content.replace('###', '')
            content = content.replace('##', '')
            content = content.replace('#', '')
            
            # Limit to reasonable length for AI processing
            if len(content) > 1500:
                # Take first 1000 chars and last 500 chars to preserve context
                content = content[:1000] + " ... " + content[-500:]
            
            return content.strip()
        except Exception as e:
            return content[:1500] if len(content) > 1500 else content
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding vector for better similarity calculations
        
        Args:
            embedding: Raw embedding vector
            
        Returns:
            Normalized embedding vector
        """
        try:
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                normalized = embedding_array / norm
                return normalized.tolist()
            return embedding
        except Exception as e:
            print(f"Error normalizing embedding: {str(e)}")
            return embedding
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create vector embedding for text using Gemini"""
        try:
            # Combine title, description, and content for embedding
            combined_text = text[:8000]  # Limit to avoid token limits
            
            # Use Gemini's embedding model with the correct method
            embedding_result = genai.embed_content(
                model=self.embedding_model,
                content=combined_text
            )
            
            # Convert to list of floats and normalize
            embedding_vector = embedding_result['embedding']
            
            # Normalize the embedding for better similarity calculations
            normalized_embedding = self._normalize_embedding(embedding_vector)
            
            return normalized_embedding
        except Exception as e:
            print(f"Error creating embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 768  # Gemini embedding dimension
    
    async def process_playbook_files(self, files: List[Dict[str, Any]], title: str, description: str, blog_content: Optional[str] = None) -> Dict[str, Any]:
        """Process all files in a playbook and generate AI insights (synchronous for summary, tags, stage)"""
        try:
            # Extract text from all files (for background embedding only)
            text_start_time = time.time()
            all_text = ""
            for file_info in files:
                file_start = time.time()
                text_content = await self.extract_text_from_file(
                    file_info['content'],
                    file_info['filename'],
                    file_info['content_type']
                )
                print(f"📄 Extracted text from {file_info['filename']} in {time.time() - file_start:.2f}s ({len(text_content)} chars)")
                all_text += f"\n\n--- {file_info['filename']} ---\n{text_content}"
            
            print(f"📚 Total text extraction completed in {time.time() - text_start_time:.2f}s")
            
            # Use blog_content as primary context for AI processing (much faster)
            primary_context = blog_content if blog_content else description
            if blog_content and description:
                primary_context = f"{description}\n\n{blog_content}"
            
            print(f"🎯 Using primary context: {len(primary_context)} chars (blog_content + description)")
            
            # Generate AI insights with single combined call
            ai_start_time = time.time()
            print("🚀 Starting combined AI processing (summary, tags, stage)...")
            
            try:
                ai_results = await self.process_playbook_combined(primary_context, title, description)
                summary = ai_results["summary"]
                tags = ai_results["tags"]
                stage = ai_results["stage"]
            except Exception as e:
                print(f"⚠️ Combined AI processing failed, falling back to individual methods: {e}")
                # Fallback to individual methods if combined fails
                summary, tags, stage = await asyncio.gather(
                    self.generate_summary_optimized(primary_context, title),
                    self.extract_tags_optimized(primary_context, title),
                    self.classify_stage_optimized(primary_context, title)
                )
            
            print(f"✅ Combined AI processing completed in {time.time() - ai_start_time:.2f}s")
            
            return {
                "summary": summary,
                "tags": tags,
                "stage": stage,
                "embedding": None,  # Will be calculated in background
                "processed_text": all_text[:1000]  # Store first 1000 chars for reference
            }
        except Exception as e:
            return {
                "summary": f"Error processing files: {str(e)}",
                "tags": ["business", "strategy"],
                "stage": "growth",
                "embedding": None,
                "processed_text": ""
            }


    async def process_playbook_embedding_background(self, playbook_id: str, title: str, description: str, all_text: str, blog_content: Optional[str] = None):
        """Process playbook embedding in background (for similarity search)"""
        try:
            print(f"🔄 Starting background embedding processing for playbook {playbook_id}...")
            start_time = time.time()
            
            # Combine description and blog_content for processing
            combined_description = description
            if blog_content:
                combined_description += f"\n\nBlog Content:\n{blog_content}"
            
            # Create embedding
            embedding = await self.create_embedding(f"{title}\n{combined_description}\n{all_text}")
            
            print(f"✅ Background embedding completed in {time.time() - start_time:.2f}s")
            print(f"🔢 Embedding dimensions: {len(embedding)}")
            
            # Update playbook with embedding
            from app.services.supabase_service import supabase_service
            update_data = {
                "vector_embedding": embedding
            }
            await supabase_service.update_playbook(playbook_id, update_data)
            print(f"💾 Updated playbook {playbook_id} with vector embedding")
            
        except Exception as e:
            print(f"❌ Background embedding processing failed for playbook {playbook_id}: {str(e)}")
            # Try to update with error information
            try:
                from app.services.supabase_service import supabase_service
                error_update = {
                    "vector_embedding": None
                }
                await supabase_service.update_playbook(playbook_id, error_update)
            except:
                pass


# Global instance
ai_service = AIService() 
