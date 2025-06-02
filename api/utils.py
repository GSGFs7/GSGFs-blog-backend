import re
from typing import Dict, List

import yaml
from jieba import analyse as jieba_analyse


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from a string.

    Args:
        text (str): The input string containing HTML tags.

    Returns:
        str: The input string with HTML tags removed.
    """
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def remove_markdown(text: str) -> str:
    """
    Remove Markdown syntax from a string.

    Args:
        text (str): The input string containing Markdown syntax.

    Returns:
        str: The input string with Markdown syntax removed.
    """
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove headers
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Remove links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
    # Remove emphasis
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    # Remove math
    text = re.sub(r"\$([^\$\n]+?)\$", "", text)
    text = re.sub(r"\$\$([\s\S]*?)\$\$", "", text)
    text = re.sub(r"\\\[([\s\S]*?)\\\]", "", text)
    text = re.sub(r"\\\(([\s\S]*?)\\\)", "", text)
    # Remove front matter
    text = re.sub(r"^---\s*\n(.*?)\n---\s*\n", "", text, flags=re.DOTALL)
    return text.strip()


def extract_front_matter(text: str) -> Dict[str, str]:
    """
    Extract front matter from a string.

    Args:
        text (str): The input string containing front matter.

    Returns:
        str: The extracted front matter as a string.
    """
    front_matter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    matched = front_matter_pattern.match(text)

    if matched:
        yaml_content = matched.group(1)
        try:
            front_matter = yaml.safe_load(yaml_content)
            if front_matter is None:
                front_matter = {}
            return front_matter
        except yaml.YAMLError:
            return {}

    # If not have front matter
    return {}


def remove_code_blocks(text: str) -> str:
    """
    Remove code blocks from a string.

    Args:
        text (str): The input string containing code blocks.

    Returns:
        str: The input string with code blocks removed.
    """
    # Remove fenced code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove HTML code blocks
    text = re.sub(r"<pre[\s\S]*?<\/pre>", "", text)
    text = re.sub(r"<code[\s\S]*?<\/code>", "", text)
    return text.strip()


def extract_keywords(text: str, num_keywords=5) -> str:
    """
    Extract keywords from a string using a simple frequency-based method.

    Args:
        text (str): The input string from which to extract keywords.
        num_keywords (int): The number of keywords to extract.

    Returns:
        str: A comma-separated string of extracted keywords.
    """
    # Get front matter if exists
    front_matter = extract_front_matter(text)

    # Remove HTML tags and Markdown syntax
    text = remove_code_blocks(text)
    text = remove_markdown(text)
    text = remove_html_tags(text)

    keywords_list: List[str] = []
    if "keywords" in front_matter:
        keywords_list.extend(front_matter["keywords"])
    if "tags" in front_matter:
        keywords_list.extend(front_matter["tags"])
    if "tag" in front_matter:
        keywords_list.extend(front_matter["tag"])

    most_common = jieba_analyse.extract_tags(text, topK=num_keywords)
    # Ensure most_common is a list of strings (extract the first element if tuples)
    if most_common and isinstance(most_common[0], tuple):
        most_common = [item[0] for item in most_common]
    else:
        most_common = [str(item) for item in most_common]
    keywords_list.extend(most_common)

    # Return the most common words as a comma-separated string
    return ",".join(keywords_list[:num_keywords])
