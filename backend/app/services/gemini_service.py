"""
Gemini AI service for PR analysis and file diff summaries
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.config import settings
from app.models.pr import FileChangeAnalysis, PRAnalysis


class GeminiService:
    """Service for interacting with Google's Gemini AI for PR analysis"""
    
    def __init__(self):
        """Initialize Gemini service with API configuration"""
        # Configure Gemini API
        try:
            if hasattr(settings, 'google_api_key') and settings.google_api_key:
                genai.configure(api_key=settings.google_api_key)
                model_name = getattr(settings, 'gemini_model', 'gemini-1.5-flash')
                
                # Try to create model - handle different versions
                if hasattr(genai, 'GenerativeModel'):
                    self.model = genai.GenerativeModel(model_name)
                elif hasattr(genai, 'generate_text'):
                    self.model = genai  # Use module directly for older versions
                else:
                    raise Exception("Unsupported google.generativeai version")
                
                self.enabled = True
                print("✅ Gemini AI service initialized successfully")
            else:
                print("Warning: Gemini API key not configured. AI analysis will be mocked.")
                self.model = None
                self.enabled = False
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini AI ({e}). AI analysis will be mocked.")
            self.model = None
            self.enabled = False
    
    async def analyze_file_change(
        self, 
        file_path: str,
        main_content: Optional[str],
        fork_content: Optional[str], 
        user_content: str,
        change_type: str
    ) -> FileChangeAnalysis:
        """
        Analyze a single file change and generate summary with risk flags
        
        Args:
            file_path: Path to the file being changed
            main_content: Current content in master/main branch
            fork_content: Content in user's fork before changes
            user_content: New content user wants to submit
            change_type: Type of change (added/modified/deleted)
        
        Returns:
            FileChangeAnalysis with changelog, risk flags, and confidence
        """
        if not self.enabled:
            return self._mock_file_analysis(file_path, change_type)
        
        try:
            prompt = self._build_file_analysis_prompt(
                file_path, main_content, fork_content, user_content, change_type
            )
            
            response = await self._call_gemini_async(prompt)
            return self._parse_file_analysis_response(response, file_path)
            
        except Exception as e:
            print(f"Gemini file analysis error: {e}")
            return self._mock_file_analysis(file_path, change_type)
    
    async def analyze_pr_overall(
        self, 
        file_analyses: List[FileChangeAnalysis],
        commit_message: str,
        pr_title: str = "",
        pr_description: str = ""
    ) -> PRAnalysis:
        """
        Generate overall PR analysis combining all file changes
        
        Args:
            file_analyses: List of individual file analyses
            commit_message: User's commit message
            pr_title: Optional user-provided PR title
            pr_description: Optional user-provided PR description
        
        Returns:
            PRAnalysis with overall PR summary and recommendations
        """
        if not self.enabled:
            return self._mock_pr_analysis(file_analyses, commit_message)
        
        try:
            prompt = self._build_pr_analysis_prompt(
                file_analyses, commit_message, pr_title, pr_description
            )
            
            response = await self._call_gemini_async(prompt)
            return self._parse_pr_analysis_response(response)
            
        except Exception as e:
            print(f"Gemini PR analysis error: {e}")
            return self._mock_pr_analysis(file_analyses, commit_message)
    
    def _build_file_analysis_prompt(
        self, 
        file_path: str,
        main_content: Optional[str],
        fork_content: Optional[str],
        user_content: str,
        change_type: str
    ) -> str:
        """Build prompt for individual file analysis"""
        
        main_text = main_content[:4000] if main_content else "No main content (new file)"
        fork_text = fork_content[:4000] if fork_content else "No fork content"
        user_text = user_content[:4000] if user_content else "File deleted"
        
        prompt = f"""You are a professional reviewer that writes concise changelogs and flags potential risks in business documents. Respond with valid JSON only.

File being analyzed: {file_path}
Change type: {change_type}

Provided are three relevant contexts:
- MAIN_CURRENT: {main_text}
- FORK_CURRENT: {fork_text}  
- USER_CHANGED: {user_text}

Task:
1) Produce a one-line changelog summarizing USER_CHANGED relative to MAIN_CURRENT.
2) Produce a short list of "risk_flags" if the change removes or alters legal/financial/compliance sections (examples: GDPR, ESOP, tax, investor terms, security policies, data handling, privacy). Flags should be short strings.
3) Provide "confidence" (0-1) representing how confident you are in your analysis.

Return JSON exactly in this format:
{{
  "file_path": "{file_path}",
  "changelog": "Brief description of what changed",
  "risk_flags": ["flag1", "flag2"],
  "confidence": 0.85
}}"""
        
        return prompt
    
    def _build_pr_analysis_prompt(
        self,
        file_analyses: List[FileChangeAnalysis],
        commit_message: str,
        pr_title: str,
        pr_description: str
    ) -> str:
        """Build prompt for overall PR analysis"""
        
        files_summary = []
        for analysis in file_analyses:
            files_summary.append({
                "file_path": analysis.file_path,
                "changelog": analysis.changelog,
                "risk_flags": analysis.risk_flags,
                "confidence": analysis.confidence
            })
        
        prompt = f"""You are an assistant that writes clear PR descriptions for maintainers.

Here are the per-file summaries:
{json.dumps(files_summary, indent=2)}

User commit message: "{commit_message}"
User PR title: "{pr_title}"
User PR description: "{pr_description}"

Task:
1) Write a short PR title (max 10 words) - improve user's title if provided.
2) Write a 3–5 sentence PR description: what changed, why it matters, potential impacts.
3) Provide a bullet list of high-risk items from risk_flags and suggested reviewer attention.
4) Provide a short merge checklist with actionable items.

Respond with valid JSON exactly in this format:
{{
  "pr_title": "Concise title describing the changes",
  "pr_description": "Clear description of what changed and why it matters",
  "high_risks": ["risk1", "risk2"],
  "merge_checklist": ["check1", "check2", "check3"]
}}"""
        
        return prompt
    
    async def _call_gemini_async(self, prompt: str) -> str:
        """Make async call to Gemini API"""
        try:
            # Run the blocking Gemini call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._call_gemini_sync, prompt)
            return response
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")
    
    def _call_gemini_sync(self, prompt: str) -> str:
        """Synchronous call to Gemini API"""
        try:
            if hasattr(self.model, 'generate_content'):
                # New API style
                response = self.model.generate_content(prompt)
                return response.text
            elif hasattr(self.model, 'generate_text'):
                # Older API style
                response = self.model.generate_text(prompt=prompt)
                return response.result
            else:
                raise Exception("Unsupported Gemini API version")
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")
    
    def _parse_file_analysis_response(self, response: str, file_path: str) -> FileChangeAnalysis:
        """Parse Gemini response for file analysis"""
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            data = json.loads(response_clean)
            
            return FileChangeAnalysis(
                file_path=data.get("file_path", file_path),
                changelog=data.get("changelog", "File modified"),
                risk_flags=data.get("risk_flags", []),
                confidence=float(data.get("confidence", 0.7))
            )
        except Exception as e:
            print(f"Failed to parse file analysis response: {e}")
            return self._mock_file_analysis(file_path, "modified")
    
    def _parse_pr_analysis_response(self, response: str) -> PRAnalysis:
        """Parse Gemini response for PR analysis"""
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            data = json.loads(response_clean)
            
            return PRAnalysis(
                pr_title=data.get("pr_title", "Update files"),
                pr_description=data.get("pr_description", "Updated multiple files with changes"),
                high_risks=data.get("high_risks", []),
                merge_checklist=data.get("merge_checklist", ["Review changes", "Test functionality"])
            )
        except Exception as e:
            print(f"Failed to parse PR analysis response: {e}")
            return self._mock_pr_analysis([], "")
    
    def _mock_file_analysis(self, file_path: str, change_type: str) -> FileChangeAnalysis:
        """Generate mock analysis when Gemini is not available"""
        changelog_map = {
            "added": f"Added new file {file_path}",
            "modified": f"Modified {file_path}",
            "deleted": f"Deleted {file_path}"
        }
        
        # Mock risk detection based on file path
        risk_flags = []
        sensitive_patterns = [
            'legal', 'gdpr', 'privacy', 'terms', 'policy', 'compliance',
            'security', 'financial', 'tax', 'investor', 'esop'
        ]
        
        file_lower = file_path.lower()
        for pattern in sensitive_patterns:
            if pattern in file_lower:
                risk_flags.append(pattern)
        
        return FileChangeAnalysis(
            file_path=file_path,
            changelog=changelog_map.get(change_type, f"Changed {file_path}"),
            risk_flags=risk_flags,
            confidence=0.6  # Lower confidence for mock analysis
        )
    
    def _mock_pr_analysis(self, file_analyses: List[FileChangeAnalysis], commit_message: str) -> PRAnalysis:
        """Generate mock PR analysis when Gemini is not available"""
        file_count = len(file_analyses)
        
        # Aggregate risk flags
        all_risks = []
        for analysis in file_analyses:
            all_risks.extend(analysis.risk_flags)
        high_risks = list(set(all_risks))  # Remove duplicates
        
        # Generate basic title and description
        if file_count == 1:
            title = f"Update {file_analyses[0].file_path}"
        else:
            title = f"Update {file_count} files"
        
        description = f"This PR updates {file_count} file(s). {commit_message}"
        
        checklist = [
            "Review all file changes",
            "Verify no sensitive data is exposed",
            "Test affected functionality"
        ]
        
        if high_risks:
            checklist.append("Review changes to sensitive sections")
        
        return PRAnalysis(
            pr_title=title,
            pr_description=description,
            high_risks=high_risks,
            merge_checklist=checklist
        )


# Global instance
gemini_service = GeminiService()