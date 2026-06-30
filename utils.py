"""
Utility functions for the Bookmark Manager
"""
import re
from datetime import datetime
from typing import List
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """
    Validate if a string is a proper URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing trailing slashes and www prefix
    """
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    
    # Remove www prefix
    parsed = urlparse(url)
    if parsed.netloc.startswith('www.'):
        parsed = parsed._replace(netloc=parsed.netloc[4:])
        url = parsed.geturl()
    
    return url


def get_valid_tags(tags_str: str) -> List[str]:
    """
    Parse and validate tags from comma-separated string
    """
    if not tags_str.strip():
        return []
    
    # Split by comma, strip whitespace, remove empty, convert to lowercase
    tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    
    return unique_tags


def format_time_ago(dt: datetime) -> str:
    """
    Format datetime as time ago string (e.g., "2 hours ago")
    """
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def get_valid_url_from_user(url: str) -> str:
    """
    Get a valid URL, adding https:// if no scheme is present
    """
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    return url


def truncate_string(text: str, max_length: int = 50) -> str:
    """
    Truncate a string to max_length and add ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def is_valid_tag(tag: str) -> bool:
    """
    Validate if a tag is valid (alphanumeric, hyphens, underscores, and spaces)
    """
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    return bool(re.match(pattern, tag))


def clean_tag(tag: str) -> str:
    """
    Clean a tag by removing extra spaces and converting to lowercase
    """
    return ' '.join(tag.strip().split()).lower()
