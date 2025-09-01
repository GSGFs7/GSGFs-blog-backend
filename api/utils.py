import hashlib
import re
from typing import Dict, List, Optional, TypedDict

import yaml
from django.utils.text import Truncator
from jieba import analyse as jieba_analyse
from pypinyin import Style, lazy_pinyin


class MetadataResult(TypedDict):
    keywords: str
    tags: List[str]
    description: str
    title: Optional[str]
    slug: Optional[str]
    category: Optional[str]
    cover_image: Optional[str]
    header_image: Optional[str]


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
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    # Remove images
    text = re.sub(r"!\[([^]]*)]\([^)]+\)", r"\1", text)
    # Remove emphasis
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    # Remove math
    text = re.sub(r"\$([^$\n]+?)\$", "", text)
    text = re.sub(r"\$\$([\s\S]*?)\$\$", "", text)
    text = re.sub(r"\\\[([\s\S]*?)\\]", "", text)
    text = re.sub(r"\\\(([\s\S]*?)\\\)", "", text)
    # Remove front matter
    text = re.sub(r"^---\s*\n(.*?)\n---\s*\n", "", text, flags=re.DOTALL)
    return text.strip()


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
    text = re.sub(r"<pre[\s\S]*?</pre>", "", text)
    text = re.sub(r"<code[\s\S]*?</code>", "", text)
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


def extract_first_image(text: str) -> Optional[str]:
    """
    Extracts the URL of the first image found in the given text.

    The function searches for images in Markdown format (`![alt](url)`) first,
    and if none are found, it searches for images in HTML format (`<img src="url">`).
    Returns the URL of the first image found, or None if no image is present.

    Args:
        text (str): The input text to search for image URLs.

    Returns:
        Optional[str]: The URL of the first image found, or None if no image is present.
    """

    markdown_img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
    match_result = re.search(markdown_img_pattern, text)
    if not match_result is None:
        return match_result.group(2)

    html_img_pattern = r'<img[^>]*src=["\']([^"\']+)["\']'
    match_result = re.search(html_img_pattern, text)
    if not match_result is None:
        return match_result.group(1)

    return None


def extract_metadata(text: str, num_keywords=5) -> MetadataResult:
    """
    Extracts metadata from a given text, including keywords, tags, category, title, slug, cover image, and header image.
    The function processes the input text by:
    - Extracting front matter metadata if present.
    - Identifying the first image in the text.
    - Removing code blocks, Markdown syntax, and HTML tags from the text.
    - Collecting keywords and tags from front matter and by analyzing the text content.
    - Determining the category from front matter fields.
    - Extracting cover and header images from front matter using common field names.
    Args:
        text (str): The input text from which metadata is to be extracted.
        num_keywords (int, optional): The maximum number of keywords to extract. Defaults to 5.
    Returns:
        MetadataResult: A dictionary containing extracted metadata fields:
            - keywords (str): Comma-separated keywords.
            - tags (List[str]): List of tags.
            - title (Optional[str]): Title from front matter.
            - slug (Optional[str]): Slug from front matter.
            - category (Optional[str]): Category from front matter.
            - cover_image (Optional[str]): Cover image URL or path.
            - header_image (Optional[str]): Header image URL or path.
    """

    # Get front matter if exists
    front_matter = extract_front_matter(text)

    first_image = extract_first_image(text)

    # Remove HTML tags and Markdown syntax
    text = remove_code_blocks(text)
    text = remove_markdown(text)
    text = remove_html_tags(text)

    # === tags ===
    tags_list: List[str] = []
    if "tags" in front_matter:
        field_value = front_matter["tags"]
        if isinstance(field_value, list):
            tags_list.extend(field_value)
        if isinstance(field_value, str):
            tags_list.append(field_value)
    if "tag" in front_matter:
        field_value = front_matter["tag"]
        if isinstance(field_value, list):
            tags_list.extend(field_value)
        if isinstance(field_value, str):
            tags_list.append(field_value)

    # === keywords ===
    keywords_list: List[str] = []
    if "keywords" in front_matter:
        keywords_list.extend(front_matter["keywords"])
    if "tags" in front_matter:
        keywords_list.extend(tags_list)
    most_common = jieba_analyse.extract_tags(text, topK=num_keywords)
    # Ensure most_common is a list of strings (extract the first element if tuples)
    if most_common and isinstance(most_common[0], tuple):
        most_common = [item[0] for item in most_common if item[0] not in keywords_list]
    else:
        most_common = [
            str(item) for item in most_common if str(item) not in keywords_list
        ]
    keywords_list.extend(most_common)

    # === category ===
    category: str | None = None
    if "category" in front_matter:
        field_value = front_matter["category"]
        if isinstance(field_value, list) and field_value:
            category = field_value[0]
        if isinstance(field_value, str):
            category = field_value
    if "categories" in front_matter and category is None:
        field_value = front_matter["categories"]
        if isinstance(field_value, list) and field_value:
            category = field_value[0]
        if isinstance(field_value, str):
            category = field_value

    # === cover image ===
    cover_image: str | None = None
    cover_image_names: List[str] = [
        "cover_image",
        "cover-image",
        "cover_img",
        "cover-img",
        "cover",
    ]
    for name in cover_image_names:
        cover_image = front_matter.get(name)
        if not cover_image is None:  # if found
            break

    # === header_image ===
    # now used as og image
    header_image: str | None = None
    header_image_names: List[str] = [
        "header_image",
        "header-image",
        "og_image",
        "og-image",
    ]
    for name in header_image_names:
        header_image = front_matter.get(name)
        if not header_image is None:  # if found
            break
    if header_image is None and first_image:
        header_image = first_image

    # === description ===
    description = Truncator(text).chars(150)

    # Return the most common words as a comma-separated string
    return {
        "keywords": ",".join(keywords_list[:num_keywords]),
        "tags": tags_list,
        "title": front_matter.get("title"),
        "slug": front_matter.get("slug"),
        "category": category,
        "cover_image": cover_image,
        "header_image": header_image,
        "description": description,
    }


def chinese_slugify(title: str, max_length: int = 50) -> str:
    """
    Generates a URL-friendly slug from a given title, supporting Chinese and English text.

    This function converts Chinese characters to their pinyin representation and lowercases English words.
    Non-alphanumeric characters are removed, and words are joined by hyphens. If the resulting slug exceeds
    the specified maximum length, it is truncated and appended with a hash suffix for uniqueness.

    Args:
        title (str): The input string to be slugified.
        max_length (int, optional): The maximum length of the resulting slug. Defaults to 50.

    Returns:
        str: The slugified string suitable for URLs.
    """

    if not title:
        return "untitled"

    # have some problem when Chinese and English are mixed
    # slug = django_slugify(title)

    cleaned = re.sub(r"[^\w\s\u4e00-\u9fff\-]", " ", title)

    parts = []
    for word in cleaned.split():
        if re.search(r"[\u4e00-\u9fff]", word):
            pinyin_parts = lazy_pinyin(word, style=Style.NORMAL)
            parts.extend([p.lower() for p in pinyin_parts])
        else:
            clean_word = re.sub(r"[^\w\-]", "", word.lower())
            if clean_word:
                parts.append(clean_word)

    slug = "-".join(parts)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if len(slug) > max_length:
        hash_suffix = hashlib.md5(title.encode()).hexdigest()[:6]
        available_length = max_length - 7
        slug = slug[:available_length] + "-" + hash_suffix

    return slug or "untitled"
