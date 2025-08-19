"""
Diff service for pull request functionality
Handles text diffing operations using difflib
"""

import difflib
from typing import List, Dict, Any, Optional
from app.models.pr import DiffResult, DiffHunk, DiffFormat


class DiffService:
    """Service for handling text diffs"""
    
    def __init__(self):
        """Initialize diff service"""
        pass
    
    def generate_unified_diff(self, old_text: str, new_text: str, filename: str = "content.md") -> str:
        """
        Generate unified diff between old and new text
        
        Args:
            old_text: Original text
            new_text: New text
            filename: Filename for diff header
            
        Returns:
            Unified diff string
        """
        if old_text == new_text:
            return ""
        
        # Split into lines for diffing
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        
        return "\n".join(diff_lines)
    
    def generate_side_by_side_diff(self, old_text: str, new_text: str) -> Dict[str, Any]:
        """
        Generate side-by-side diff
        
        Args:
            old_text: Original text
            new_text: New text
            
        Returns:
            Side-by-side diff structure
        """
        if old_text == new_text:
            return {
                "has_changes": False,
                "old_lines": [],
                "new_lines": [],
                "changes": []
            }
        
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        # Use difflib to get line-by-line differences
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        changes = []
        old_side = []
        new_side = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are the same
                for k in range(i1, i2):
                    old_side.append({
                        "line": k + 1,
                        "content": old_lines[k],
                        "type": "unchanged"
                    })
                    new_side.append({
                        "line": j1 + (k - i1) + 1,
                        "content": new_lines[j1 + (k - i1)],
                        "type": "unchanged"
                    })
            elif tag == 'replace':
                # Lines were replaced
                changes.append({
                    "type": "replace",
                    "old_start": i1 + 1,
                    "old_end": i2,
                    "new_start": j1 + 1,
                    "new_end": j2
                })
                
                # Add old lines
                for k in range(i1, i2):
                    old_side.append({
                        "line": k + 1,
                        "content": old_lines[k],
                        "type": "deleted"
                    })
                
                # Add new lines
                for k in range(j1, j2):
                    new_side.append({
                        "line": k + 1,
                        "content": new_lines[k],
                        "type": "added"
                    })
            elif tag == 'delete':
                # Lines were deleted
                changes.append({
                    "type": "delete",
                    "old_start": i1 + 1,
                    "old_end": i2
                })
                
                for k in range(i1, i2):
                    old_side.append({
                        "line": k + 1,
                        "content": old_lines[k],
                        "type": "deleted"
                    })
            elif tag == 'insert':
                # Lines were inserted
                changes.append({
                    "type": "insert",
                    "new_start": j1 + 1,
                    "new_end": j2
                })
                
                for k in range(j1, j2):
                    new_side.append({
                        "line": k + 1,
                        "content": new_lines[k],
                        "type": "added"
                    })
        
        return {
            "has_changes": True,
            "old_lines": old_side,
            "new_lines": new_side,
            "changes": changes
        }
    
    def generate_html_diff(self, old_text: str, new_text: str) -> str:
        """
        Generate HTML diff
        
        Args:
            old_text: Original text
            new_text: New text
            
        Returns:
            HTML diff string
        """
        if old_text == new_text:
            return "<div class='diff-no-changes'>No changes</div>"
        
        # Use difflib's HtmlDiff
        differ = difflib.HtmlDiff()
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        html_diff = differ.make_file(old_lines, new_lines)
        
        # Clean up the HTML (remove table tags, keep only the diff content)
        # This is a simplified version - you might want to customize the HTML output
        return html_diff
    
    def generate_diff_result(self, old_text: str, new_text: str, filename: str = "content.md") -> DiffResult:
        """
        Generate complete diff result
        
        Args:
            old_text: Original text
            new_text: New text
            filename: Filename for diff
            
        Returns:
            Complete diff result
        """
        if old_text == new_text:
            return DiffResult(
                hunks=[],
                unified_diff="",
                has_changes=False,
                lines_added=0,
                lines_removed=0
            )
        
        # Generate unified diff
        unified_diff = self.generate_unified_diff(old_text, new_text, filename)
        
        # Parse unified diff into hunks
        hunks = self._parse_unified_diff_to_hunks(unified_diff)
        
        # Count lines
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        lines_added = sum(j2 - j1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag in ('insert', 'replace'))
        lines_removed = sum(i2 - i1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag in ('delete', 'replace'))
        
        return DiffResult(
            hunks=hunks,
            unified_diff=unified_diff,
            has_changes=True,
            lines_added=lines_added,
            lines_removed=lines_removed
        )
    
    def _parse_unified_diff_to_hunks(self, unified_diff: str) -> List[DiffHunk]:
        """
        Parse unified diff string into hunks
        
        Args:
            unified_diff: Unified diff string
            
        Returns:
            List of diff hunks
        """
        hunks = []
        current_hunk = None
        
        for line in unified_diff.splitlines():
            if line.startswith('@@'):
                # New hunk header
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Parse hunk header: @@ -old_start,old_lines +new_start,new_lines @@
                try:
                    header = line[3:-3]  # Remove @@
                    ranges = header.split(' ')
                    old_range = ranges[0][1:]  # Remove -
                    new_range = ranges[1][1:]  # Remove +
                    
                    old_start, old_lines = map(int, old_range.split(','))
                    new_start, new_lines = map(int, new_range.split(','))
                    
                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                        content=[]
                    )
                except (ValueError, IndexError):
                    # Skip malformed hunk headers
                    continue
            elif current_hunk:
                current_hunk.content.append(line)
        
        # Add the last hunk
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def has_conflicts(self, base_text: str, current_text: str, proposed_text: str) -> bool:
        """
        Check if there are merge conflicts between three versions
        
        Args:
            base_text: Base version text
            current_text: Current version text
            proposed_text: Proposed version text
            
        Returns:
            True if there are conflicts
        """
        # Simple conflict detection: if both current and proposed changed the same lines
        # This is a simplified version - real conflict detection would be more sophisticated
        
        base_lines = base_text.splitlines()
        current_lines = current_text.splitlines()
        proposed_lines = proposed_text.splitlines()
        
        # Find differences between base and current
        current_matcher = difflib.SequenceMatcher(None, base_lines, current_lines)
        current_changes = set()
        for tag, i1, i2, j1, j2 in current_matcher.get_opcodes():
            if tag in ('replace', 'delete', 'insert'):
                for k in range(i1, i2):
                    current_changes.add(k)
        
        # Find differences between base and proposed
        proposed_matcher = difflib.SequenceMatcher(None, base_lines, proposed_lines)
        proposed_changes = set()
        for tag, i1, i2, j1, j2 in proposed_matcher.get_opcodes():
            if tag in ('replace', 'delete', 'insert'):
                for k in range(i1, i2):
                    proposed_changes.add(k)
        
        # Check for overlapping changes
        conflicts = current_changes.intersection(proposed_changes)
        return len(conflicts) > 0
    
    def three_way_merge(self, base_text: str, current_text: str, proposed_text: str) -> Dict[str, Any]:
        """
        Perform three-way merge
        
        Args:
            base_text: Base version text
            current_text: Current version text
            proposed_text: Proposed version text
            
        Returns:
            Merge result with success status and conflicts
        """
        if not self.has_conflicts(base_text, current_text, proposed_text):
            # No conflicts, can merge
            return {
                "success": True,
                "merged_text": proposed_text,
                "conflicts": []
            }
        
        # For now, return conflict - in a real implementation, you'd do more sophisticated merging
        return {
            "success": False,
            "merged_text": None,
            "conflicts": [
                {
                    "type": "conflict",
                    "message": "Manual merge required",
                    "base_text": base_text,
                    "current_text": current_text,
                    "proposed_text": proposed_text
                }
            ]
        }


# Global instance
diff_service = DiffService()
