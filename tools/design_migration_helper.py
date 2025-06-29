# pinpoint/tools/design_migration_helper.py
"""
Helper tool to extract hardcoded styles from existing code
and generate design system files.
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Set


class StyleExtractor(ast.NodeVisitor):
    """AST visitor to extract style-related code."""
    
    def __init__(self):
        self.styles = []
        self.colors = set()
        self.sizes = set()
        self.fonts = set()
        
    def visit_Call(self, node):
        """Extract style-related method calls."""
        if isinstance(node.func, ast.Attribute):
            # Check for setStyleSheet calls
            if node.func.attr == 'setStyleSheet' and node.args:
                if isinstance(node.args[0], ast.Str):
                    self.styles.append({
                        'type': 'stylesheet',
                        'value': node.args[0].s,
                        'line': node.lineno
                    })
                    
            # Check for setFixedSize, setFixedWidth, setFixedHeight
            elif node.func.attr in ['setFixedSize', 'setFixedWidth', 'setFixedHeight']:
                if node.args:
                    self.styles.append({
                        'type': node.func.attr,
                        'value': self._extract_value(node.args),
                        'line': node.lineno
                    })
                    
            # Check for color-related calls
            elif node.func.attr in ['setColor', 'setBackground', 'setPalette']:
                self.styles.append({
                    'type': node.func.attr,
                    'value': self._extract_value(node.args),
                    'line': node.lineno
                })
                
        self.generic_visit(node)
        
    def _extract_value(self, args):
        """Extract value from AST arguments."""
        values = []
        for arg in args:
            if isinstance(arg, ast.Num):
                values.append(arg.n)
            elif isinstance(arg, ast.Str):
                values.append(arg.s)
            elif isinstance(arg, ast.Name):
                values.append(arg.id)
        return values


class DesignMigrationHelper:
    """Helps migrate from hardcoded styles to design system."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.extracted_data = {
            'stylesheets': {},
            'sizes': {},
            'colors': set(),
            'fonts': set(),
            'properties': {}
        }
        
    def extract_all_styles(self):
        """Extract styles from all Python files."""
        for py_file in self.source_dir.rglob("*.py"):
            if "refactored" not in str(py_file):  # Skip refactored files
                self._extract_from_file(py_file)
                
    def _extract_from_file(self, file_path: Path):
        """Extract styles from a single file."""
        print(f"Extracting from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            tree = ast.parse(content)
            extractor = StyleExtractor()
            extractor.visit(tree)
            
            # Extract colors from stylesheets
            for style in extractor.styles:
                if style['type'] == 'stylesheet':
                    self._extract_colors_from_css(style['value'])
                    self._extract_sizes_from_css(style['value'])
                    
            # Extract hardcoded sizes
            self._extract_hardcoded_sizes(content)
            
            # Store extracted data
            relative_path = file_path.relative_to(self.source_dir)
            self.extracted_data['stylesheets'][str(relative_path)] = extractor.styles
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    def _extract_colors_from_css(self, css: str):
        """Extract color values from CSS."""
        # Hex colors
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}', css)
        self.extracted_data['colors'].update(hex_colors)
        
        # RGB/RGBA colors
        rgb_colors = re.findall(r'rgba?\([^)]+\)', css)
        self.extracted_data['colors'].update(rgb_colors)
        
    def _extract_sizes_from_css(self, css: str):
        """Extract size values from CSS."""
        # Pixel values
        px_sizes = re.findall(r'\d+px', css)
        for size in px_sizes:
            self.extracted_data['sizes'][size] = int(size.replace('px', ''))
            
    def _extract_hardcoded_sizes(self, content: str):
        """Extract hardcoded size values."""
        # Look for patterns like setFixedSize(60, 60)
        size_patterns = [
            r'setFixedSize\((\d+),\s*(\d+)\)',
            r'setFixedWidth\((\d+)\)',
            r'setFixedHeight\((\d+)\)',
            r'resize\((\d+),\s*(\d+)\)',
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    for val in match:
                        if val.isdigit():
                            self.extracted_data['sizes'][f"{val}px"] = int(val)
                else:
                    if match.isdigit():
                        self.extracted_data['sizes'][f"{match}px"] = int(match)
                        
    def generate_design_files(self):
        """Generate design system files from extracted data."""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate color constants
        colors = self._generate_color_mapping()
        
        # Generate size constants  
        sizes = self._generate_size_mapping()
        
        # Generate main design file
        main_design = {
            "version": "1.0.0",
            "metadata": {
                "name": "Migrated Design",
                "description": "Auto-generated from existing styles",
                "created": "2024-01-01"
            },
            "constants": {
                "colors": colors,
                "spacing": sizes,
                "fonts": {
                    "default": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif",
                    "mono": "'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace"
                }
            }
        }
        
        # Write main design file
        with open(self.output_dir / "main.json", 'w', encoding='utf-8') as f:
            json.dump(main_design, f, indent=2)
            
        # Generate styles directory
        styles_dir = self.output_dir / "styles"
        styles_dir.mkdir(exist_ok=True)
        
        # Generate class styles
        self._generate_class_styles(styles_dir)
        
        # Generate ID styles
        self._generate_id_styles(styles_dir)
        
        print(f"Design files generated in: {self.output_dir}")
        
    def _generate_color_mapping(self) -> Dict[str, str]:
        """Generate color constant mapping from extracted colors."""
        color_map = {}
        
        # Common color mappings
        common_mappings = {
            "#1a1a1a": "bg_primary",
            "#242424": "bg_secondary",
            "#2a2a2a": "bg_tertiary",
            "#303030": "bg_hover",
            "#0d7377": "bg_selected",
            "#e0e0e0": "text_primary",
            "#999999": "text_secondary",
            "#666666": "text_muted",
            "#14ffec": "accent",
            "#00e5d6": "accent_hover",
            "#333333": "border_subtle",
            "#555555": "border_strong"
        }
        
        # Start with common mappings
        for color in self.extracted_data['colors']:
            if color.lower() in common_mappings:
                color_name = common_mappings[color.lower()]
                color_map[color_name] = color.lower()
            else:
                # Generate a name for unknown colors
                if color.startswith('#'):
                    color_name = f"custom_color_{color[1:]}"
                else:
                    color_name = f"custom_color_{hash(color) % 10000}"
                color_map[color_name] = color
                
        return color_map
        
    def _generate_size_mapping(self) -> Dict[str, int]:
        """Generate size constant mapping from extracted sizes."""
        size_map = {
            "none": 0,
            "xs": 8,
            "sm": 16,
            "md": 24,
            "lg": 32,
            "xl": 40,
            "xxl": 48
        }
        
        # Add extracted sizes
        for size_str, size_val in self.extracted_data['sizes'].items():
            if size_val == 60:
                size_map['sidebar_width'] = size_val
            elif size_val == 250:
                size_map['tile_default_width'] = size_val
            elif size_val == 150:
                size_map['tile_default_height'] = size_val
            elif size_val not in size_map.values():
                size_map[f'custom_{size_val}'] = size_val
                
        return size_map
        
    def _generate_class_styles(self, styles_dir: Path):
        """Generate widget class styles from extracted stylesheets."""
        class_styles = {}
        
        # Parse extracted stylesheets
        for file_path, styles in self.extracted_data['stylesheets'].items():
            for style in styles:
                if style['type'] == 'stylesheet':
                    css = style['value']
                    # Extract widget class styles
                    self._parse_css_to_classes(css, class_styles)
                    
        # Write class styles
        with open(styles_dir / "classes.json", 'w', encoding='utf-8') as f:
            json.dump(class_styles, f, indent=2)
            
    def _generate_id_styles(self, styles_dir: Path):
        """Generate widget ID styles from extracted stylesheets."""
        id_styles = {}
        
        # Parse extracted stylesheets for ID selectors
        for file_path, styles in self.extracted_data['stylesheets'].items():
            for style in styles:
                if style['type'] == 'stylesheet':
                    css = style['value']
                    # Extract ID styles
                    self._parse_css_to_ids(css, id_styles)
                    
        # Write ID styles
        with open(styles_dir / "ids.json", 'w', encoding='utf-8') as f:
            json.dump(id_styles, f, indent=2)
            
    def _parse_css_to_classes(self, css: str, class_styles: Dict):
        """Parse CSS and extract class-based styles."""
        # Simple regex to find QPushButton { ... } patterns
        pattern = r'(Q\w+)\s*{([^}]+)}'
        matches = re.findall(pattern, css)
        
        for class_name, style_content in matches:
            if class_name not in class_styles:
                class_styles[class_name] = {"default": ""}
                
            # Clean up the style content
            style_content = style_content.strip()
            class_styles[class_name]["default"] = f"{class_name} {{ {style_content} }}"
            
        # Look for pseudo-selectors
        pseudo_pattern = r'(Q\w+):(\w+)\s*{([^}]+)}'
        pseudo_matches = re.findall(pseudo_pattern, css)
        
        for class_name, pseudo, style_content in pseudo_matches:
            if class_name not in class_styles:
                class_styles[class_name] = {}
            style_content = style_content.strip()
            class_styles[class_name][pseudo] = f"{class_name}:{pseudo} {{ {style_content} }}"
            
    def _parse_css_to_ids(self, css: str, id_styles: Dict):
        """Parse CSS and extract ID-based styles."""
        # Pattern for #id or QWidget#id selectors
        pattern = r'(?:Q\w+)?#(\w+)\s*{([^}]+)}'
        matches = re.findall(pattern, css)
        
        for widget_id, style_content in matches:
            if widget_id not in id_styles:
                id_styles[widget_id] = {"default": ""}
                
            style_content = style_content.strip()
            id_styles[widget_id]["default"] = f"#{widget_id} {{ {style_content} }}"
            
    def generate_migration_report(self) -> str:
        """Generate a report of what was extracted and needs manual review."""
        report = []
        report.append("# Design Migration Report\n")
        report.append(f"## Files Processed: {len(self.extracted_data['stylesheets'])}\n")
        
        report.append("## Extracted Colors")
        for color in sorted(self.extracted_data['colors']):
            report.append(f"- {color}")
        report.append("")
        
        report.append("## Extracted Sizes")
        for size, value in sorted(self.extracted_data['sizes'].items()):
            report.append(f"- {size}: {value}")
        report.append("")
        
        report.append("## Files with Styles")
        for file_path, styles in self.extracted_data['stylesheets'].items():
            if styles:
                report.append(f"\n### {file_path}")
                for style in styles[:5]:  # Show first 5
                    report.append(f"- Line {style['line']}: {style['type']}")
                if len(styles) > 5:
                    report.append(f"- ... and {len(styles) - 5} more")
                    
        report.append("\n## Manual Review Required")
        report.append("- Review generated color names and update with semantic names")
        report.append("- Check size constants and update with semantic names")
        report.append("- Review complex stylesheets that may need manual parsing")
        report.append("- Update widget IDs to match refactored code")
        
        return "\n".join(report)


def main():
    """Run the migration helper."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python design_migration_helper.py <source_dir> <output_dir>")
        sys.exit(1)
        
    source_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        sys.exit(1)
        
    helper = DesignMigrationHelper(source_dir, output_dir)
    
    print("Extracting styles from existing code...")
    helper.extract_all_styles()
    
    print("Generating design files...")
    helper.generate_design_files()
    
    # Generate report
    report = helper.generate_migration_report()
    report_path = output_dir / "migration_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"Migration report saved to: {report_path}")
    print("Done! Please review the generated files and update as needed.")


if __name__ == "__main__":
    main()