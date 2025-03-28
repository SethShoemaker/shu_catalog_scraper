import asyncio
from typing import List
import aiohttp
from bs4 import BeautifulSoup

_host = "https://catalog.setonhill.edu"

_mobile_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QQ3A.200805.001) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",  # Do Not Track
}
async def _get_soup(url: str) -> BeautifulSoup:
    # creates a BeautifulSoup instance for the webpage at the given url
    async with aiohttp.ClientSession(headers=_mobile_headers) as session:
        async with session.get(url) as resp:
            text = await resp.read()
            return BeautifulSoup(text.decode('utf-8'), features="html.parser")

async def get_course_prefix_list() -> List[str]:
    # gets the course prefixes listed on the catalog website
    soup: BeautifulSoup = await _get_soup(f"{_host}/search_advanced.php")
    prefix_list = []
    spans = (soup
        .find('div', {'id': 'course_options'})
        .find('div', {'id': 'prefix_box'})
        .find_all('span', {'class': '.prefix_box_list'}))
    for span in spans:
        prefix_list.append(str(span.text).replace(u'\xa0', '').strip())
    return prefix_list

def _search_url(course_prefix: str, page: int) -> str:
    return f"{_host}/search_advanced.php?cur_cat_oid=17&ecpage={page}&cpage=1&ppage=1&pcpage=1&spage=1&tpage=1&search_database=Search&filter%5Bkeyword%5D={course_prefix}&filter%5B3%5D=1&filter%5B31%5D=1"

async def _process_course_page(show_url: str, courses: List[object]):
    courses.append(await parse_course_page(show_url))

async def get_courses_with_prefix(prefix: str) -> List[object]:
    courses = []
    tasks = []
    page = 1
    while True:
        soup = await _get_soup(_search_url(prefix, page))
        results = (soup
            .find(lambda tag: tag.name == 'td' and 'Courses - Prefix/Code Matches' in tag)
            .parent
            .parent
            .find_all(lambda tag: tag.name == 'a' and tag.text.startswith(prefix)))
        if len(results) == 0:
            return courses
        for result in results:
            if result is None:
                continue
            tasks.append(_process_course_page(f"{_host}/{result.attrs.get('href')}", courses))
        await asyncio.gather(*tasks)
        tasks = []
        page+=1

async def parse_course_page(show_url: str) -> object:
    # parses data from a course show page
    soup = await _get_soup(show_url)
    course_code = _get_course_code(soup)
    course_name = _get_course_name(soup)
    credits = _get_credits(soup)
    when_offered = _get_when_offered(soup)
    prerequisites = _get_prerequisites(soup)
    liberal_arts_cirriculum = _get_liberal_arts_cirriculum(soup)
    return {
        "link": show_url,
        "code": course_code,
        "name": course_name,
        "credits": credits,
        "when_offered": when_offered,
        "prerequisites": prerequisites,
        "liberal_arts_cirriculum": liberal_arts_cirriculum
    }

def _get_course_code(soup: BeautifulSoup) -> str|None:
    title = soup.find('h1', {'id': 'course_preview_title'})
    if title is None:
        return None
    return title.text.split('-')[0].strip()

def _get_course_name(soup: BeautifulSoup) -> str|None:
    title = soup.find('h1', {'id': 'course_preview_title'})
    if title is None:
        return None
    return title.text.split('-')[1].strip()

def _get_credits(soup: BeautifulSoup) -> str|None:
    try:
        raw = str(soup)
        end = raw.index('<strong>Credit(s)</strong>')
        beg = raw.rindex('<strong>', 0, end)
        return raw[beg + 8:end - 10]
    except ValueError:
        return None

def _get_when_offered(soup: BeautifulSoup) -> str|None:
    try:
        raw = str(soup)
        beg = raw.index('<strong>When Offered:</strong>') + 30
        end = raw.index('<br/>', beg)
        return raw[beg:end].strip().strip('.')
    except ValueError:
        return None

def _get_prerequisites(soup: BeautifulSoup) -> List[object]:
    links = soup.find_all(lambda tag: tag.name == 'a' and tag.attrs.get('href') and tag.attrs.get('href').startswith('preview_course_nopop.php?catoid='))
    return [{"code": link.text, "link":f"{_host}/{link.attrs.get('href')}"} for link in links]

def _get_liberal_arts_cirriculum(soup: BeautifulSoup) -> str|None:
    try:
        raw = str(soup)
        beg = raw.index('<strong>Liberal Arts Curriculum:</strong>') + 41
        end = raw.index('<br/>', beg)
        return raw[beg:end].strip().strip('.')
    except ValueError:
        return None