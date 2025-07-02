#!/usr/bin/env python3
"""
Line counter for PinPoint project.
Counts lines in code files and documentation files (.md).
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import json

# File extensions to count
CODE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'Header',
    '.hpp': 'Header',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.less': 'LESS',
    '.xml': 'XML',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.zsh': 'Shell',
    '.fish': 'Shell',
    '.ps1': 'PowerShell',
    '.bat': 'Batch',
    '.cmd': 'Batch',
}

DOC_EXTENSIONS = {
    '.md': 'Markdown',
    '.rst': 'reStructuredText',
    '.txt': 'Text',
    '.adoc': 'AsciiDoc',
}

# Directories to skip
SKIP_DIRS = {
    '__pycache__',
    '.git',
    '.svn',
    '.hg',
    'node_modules',
    'venv',
    'env',
    '.env',
    'dist',
    'build',
    '.idea',
    '.vscode',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'htmlcov',
    '.coverage',
    'egg-info',
}


class LineCounter:
    """Counts lines of code and documentation in a project."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.stats = {
            'code': {},
            'docs': {},
            'total_code_lines': 0,
            'total_doc_lines': 0,
            'total_files': 0,
            'files_by_type': {},
            'directories': set(),
        }
    
    def count_lines_in_file(self, file_path: Path) -> int:
        """Count lines in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0
    
    def should_skip_directory(self, dir_name: str) -> bool:
        """Check if directory should be skipped."""
        return dir_name in SKIP_DIRS or dir_name.startswith('.')
    
    def scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for code and doc files."""
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    if not self.should_skip_directory(item.name):
                        self.stats['directories'].add(str(item.relative_to(self.root_path)))
                        self.scan_directory(item)
                elif item.is_file():
                    self.process_file(item)
        except PermissionError:
            print(f"Permission denied: {directory}")
    
    def process_file(self, file_path: Path) -> None:
        """Process a single file and update statistics."""
        ext = file_path.suffix.lower()
        rel_path = file_path.relative_to(self.root_path)
        
        # Check if it's a code file
        if ext in CODE_EXTENSIONS:
            lines = self.count_lines_in_file(file_path)
            file_type = CODE_EXTENSIONS[ext]
            
            if file_type not in self.stats['code']:
                self.stats['code'][file_type] = {'files': 0, 'lines': 0, 'file_list': []}
            
            self.stats['code'][file_type]['files'] += 1
            self.stats['code'][file_type]['lines'] += lines
            self.stats['code'][file_type]['file_list'].append((str(rel_path), lines))
            self.stats['total_code_lines'] += lines
            self.stats['total_files'] += 1
            
            # Track by extension
            if ext not in self.stats['files_by_type']:
                self.stats['files_by_type'][ext] = 0
            self.stats['files_by_type'][ext] += 1
        
        # Check if it's a doc file
        elif ext in DOC_EXTENSIONS:
            lines = self.count_lines_in_file(file_path)
            file_type = DOC_EXTENSIONS[ext]
            
            if file_type not in self.stats['docs']:
                self.stats['docs'][file_type] = {'files': 0, 'lines': 0, 'file_list': []}
            
            self.stats['docs'][file_type]['files'] += 1
            self.stats['docs'][file_type]['lines'] += lines
            self.stats['docs'][file_type]['file_list'].append((str(rel_path), lines))
            self.stats['total_doc_lines'] += lines
            self.stats['total_files'] += 1
            
            # Track by extension
            if ext not in self.stats['files_by_type']:
                self.stats['files_by_type'][ext] = 0
            self.stats['files_by_type'][ext] += 1
    
    def run(self) -> Dict:
        """Run the line counter and return statistics."""
        print(f"Scanning {self.root_path}...")
        self.scan_directory(self.root_path)
        return self.stats
    
    def print_report(self, show_files: bool = False) -> None:
        """Print a formatted report of the statistics."""
        print("\n" + "="*60)
        print(f"LINE COUNT REPORT FOR: {self.root_path}")
        print("="*60)
        
        # Code files summary
        print("\nCODE FILES:")
        print("-"*40)
        for file_type, data in sorted(self.stats['code'].items()):
            print(f"{file_type:15} {data['files']:5} files   {data['lines']:7,} lines")
            if show_files:
                for file_path, lines in sorted(data['file_list']):
                    print(f"  - {file_path:50} {lines:6,} lines")
        
        # Documentation files summary
        print("\nDOCUMENTATION FILES:")
        print("-"*40)
        for file_type, data in sorted(self.stats['docs'].items()):
            print(f"{file_type:15} {data['files']:5} files   {data['lines']:7,} lines")
            if show_files:
                for file_path, lines in sorted(data['file_list']):
                    print(f"  - {file_path:50} {lines:6,} lines")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print("-"*40)
        print(f"Total files:          {self.stats['total_files']:,}")
        print(f"Total code lines:     {self.stats['total_code_lines']:,}")
        print(f"Total doc lines:      {self.stats['total_doc_lines']:,}")
        print(f"Total lines:          {self.stats['total_code_lines'] + self.stats['total_doc_lines']:,}")
        print(f"Directories scanned:  {len(self.stats['directories'])}")
        
        # File type distribution
        print("\nFILE TYPE DISTRIBUTION:")
        print("-"*40)
        for ext, count in sorted(self.stats['files_by_type'].items()):
            print(f"{ext:10} {count:5} files")
        
        print("="*60)
    
    def export_json(self, output_path: Path) -> None:
        """Export statistics to JSON file."""
        # Convert sets to lists for JSON serialization
        export_data = self.stats.copy()
        export_data['directories'] = sorted(list(export_data['directories']))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        print(f"\nExported statistics to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Count lines of code and documentation in PinPoint project"
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to scan (default: current directory)'
    )
    parser.add_argument(
        '--show-files',
        '-f',
        action='store_true',
        help='Show individual file statistics'
    )
    parser.add_argument(
        '--export',
        '-e',
        type=str,
        help='Export statistics to JSON file'
    )
    parser.add_argument(
        '--include-hidden',
        '-i',
        action='store_true',
        help='Include hidden directories (starting with .)'
    )
    
    args = parser.parse_args()
    
    # Get the path to scan
    scan_path = Path(args.path).resolve()
    
    # Look for pinpoint directory
    if scan_path.name != 'pinpoint' and (scan_path / 'pinpoint').exists():
        scan_path = scan_path / 'pinpoint'
        print(f"Found pinpoint directory at: {scan_path}")
    elif scan_path.name == 'pinpoint':
        print(f"Scanning pinpoint directory at: {scan_path}")
    else:
        print(f"Warning: Directory name is not 'pinpoint'. Scanning: {scan_path}")
    
    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1
    
    # Create and run counter
    counter = LineCounter(scan_path)
    
    # Modify skip behavior if including hidden directories
    if args.include_hidden:
        original_should_skip = counter.should_skip_directory
        counter.should_skip_directory = lambda d: d in SKIP_DIRS and not d.startswith('.')
    
    stats = counter.run()
    
    # Print report
    counter.print_report(show_files=args.show_files)
    
    # Export if requested
    if args.export:
        export_path = Path(args.export)
        counter.export_json(export_path)
    
    return 0


if __name__ == '__main__':
    exit(main())