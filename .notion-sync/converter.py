#!/usr/bin/env python3
"""Notion to GitHub Pages 변환 스크립트"""

import re
from datetime import datetime
from pathlib import Path
import yaml


class NotionToGitHubPages:
    def __init__(self, repo_path=None):
        if repo_path is None:
            repo_path = Path(__file__).parent.parent
        else:
            repo_path = Path(repo_path)
        
        self.posts_dir = repo_path / "_posts"
        self.posts_dir.mkdir(exist_ok=True)
    
    def clean_filename(self, title):
        """파일명 생성 (영문/숫자만)"""
        cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        cleaned = re.sub(r'\s+', '-', cleaned.strip())
        cleaned = re.sub(r'-+', '-', cleaned)
        return cleaned.lower() or "untitled"
    
    def convert_markdown(self, content):
        """Notion Markdown → Jekyll Markdown"""
        
        # Callout 변환
        def replace_callout(match):
            icon = match.group(1) or "💡"
            color = match.group(2) or "gray_bg"
            text = match.group(3).strip().replace('<br>', '\n>')
            
            alert_map = {
                'gray_bg': 'info', 'blue_bg': 'info',
                'green_bg': 'tip', 'yellow_bg': 'warning',
                'red_bg': 'danger'
            }
            alert = alert_map.get(color, 'info')
            
            return f"> {icon} **{alert.upper()}**\n>\n> {text}\n{{: .prompt-{alert} }}\n"
        
        content = re.sub(
            r'<callout icon="([^"]*)" color="([^"]*)">(.+?)</callout>',
            replace_callout, content, flags=re.DOTALL
        )
        
        content = re.sub(r'```c\+\+', '```cpp', content)
        content = re.sub(r'\{\{(https?://[^\}]+)\}\}', r'\1', content)
        content = content.replace('<br>', '\n')
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def create_post(self, title, content, categories=None, tags=None, date=None):
        """Jekyll 포스트 생성"""
        
        if date is None:
            date = datetime.now()
        
        filename = f"{date.strftime('%Y-%m-%d')}-{self.clean_filename(title)}.md"
        filepath = self.posts_dir / filename
        
        front_matter = {
            'title': title,
            'date': date.strftime('%Y-%m-%d %H:%M:%S +0900'),
            'categories': categories or ['Uncategorized'],
            'tags': tags or [],
        }
        
        jekyll_content = self.convert_markdown(content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('---\n')
            f.write(yaml.dump(front_matter, allow_unicode=True, sort_keys=False))
            f.write('---\n\n')
            f.write(jekyll_content)
        
        print(f"✅ 포스트 생성: {filepath}")
        return filepath


if __name__ == "__main__":
    print("개인 블로그용 Notion 변환 스크립트")
    print("Claude에게 'Notion 글을 GitHub Pages로 옮겨줘' 요청하세요.")
