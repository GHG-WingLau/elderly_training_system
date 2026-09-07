import os
from pathlib import Path

def bundle_project_to_markdown(output_filename="project_reference.md", ignore_dirs=None, extensions=None):
    """
    Bundles local project files into a single, clean Markdown document.
    """
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules', '.idea', '.vscode'}
    if extensions is None:
        extensions = {'.py', '.sql', '.md', '.txt', '.json', '.ini', '.yaml', '.yml'}
        
    project_root = Path.cwd()
    
    def generate_tree(dir_path, prefix=""):
        """Generates a visual text-based directory tree."""
        tree_lines = []
        try:
            items = sorted(list(dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return tree_lines
            
        items = [item for item in items if item.name not in ignore_dirs]
        
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                tree_lines.append(f"{prefix}{connector}{item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                tree_lines.extend(generate_tree(item, new_prefix))
            else:
                if item.suffix.lower() in extensions:
                    tree_lines.append(f"{prefix}{connector}{item.name}")
        return tree_lines

    markdown_sections = []
    
    # 1. Header & Summary
    markdown_sections.append("# Project Reference Document\n")
    markdown_sections.append("## 1. Executive Summary & Tech Stack\n- **Language:** Python\n- **Database:** SQLite\n- **Generated On:** Automated Script\n")
    
    # 2. Directory Tree
    markdown_sections.append("## 2. Project Directory Tree Structure\n```text")
    markdown_sections.append(project_root.name + "/")
    markdown_sections.extend(generate_tree(project_root))
    markdown_sections.append("```\n")
    
    # 3. Source Code Files
    markdown_sections.append("## 3. Complete Source Code")
    
    # Walk through files to grab code
    for root, dirs, files in os.walk(project_root):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in sorted(files):
            file_path = Path(root) / file
            if file_path.suffix.lower() in extensions and file_path.name != output_filename:
                relative_path = file_path.relative_to(project_root)
                
                # Determine language for markdown syntax highlighting
                lang = file_path.suffix.lower().replace('.', '')
                if lang in ['txt', 'ini']:
                    lang = 'text'
                elif lang == 'sql':
                    lang = 'sql'
                elif lang == 'py':
                    lang = 'python'
                
                markdown_sections.append(f"### File: `{relative_path}`")
                markdown_sections.append(f"```{lang}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    markdown_sections.append(content)
                except Exception as e:
                    markdown_sections.append(f"/* Error reading file: {str(e)} */")
                    
                markdown_sections.append("```\n")
                
    # 4. Templates for placeholder fields
    markdown_sections.append("## 4. Modification Log")
    markdown_sections.append("| Date | Change Summary | Author | Impact |\n|---|---|---|---|\n| [Date] | Initial code bundling | Automation | Compiled all local modules |\n")
    markdown_sections.append("## 5. Run & Verification Guide\n1. **Environment Setup:** Ensure Python 3.x is installed.\n2. **Database Initialization:** The SQLite database will auto-initialize upon running the main entry script.\n3. **Execution:** Run the primary application file (e.g., `python app.py`).")

    # Write out the Markdown file
    output_path = project_root / output_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_sections))
        
    print(f"Successfully generated reference document at: {output_path}")

if __name__ == '__main__':
    bundle_project_to_markdown()
