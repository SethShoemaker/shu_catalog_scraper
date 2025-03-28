import asyncio
import lib
import jsonpickle
from rich.panel import Panel
from rich.columns import Columns
from catalog_scraper import console

async def main():
    console.log(f"[bold yellow]Fetching Course Prefixes[/]")
    prefixes = await lib.get_course_prefix_list()
    console.log(f"[bold green]Fetch complete[/]")
    console.log(Panel(Columns(prefixes, equal=True, expand=True), title="[bold]Course Prefixes[/]"))

    courses = []
    console.log(f"[bold yellow]Fetching Classes[/]")
    for i, prefix in enumerate(prefixes):
        console.log(f"[bold yellow]{prefix}[/] ({i + 1} out of {len(prefixes)})")
        courses.extend(await lib.get_courses_with_prefix(prefix))
    console.log("[bold green]Fetch Complete[/]")

    console.log("[bold yellow]Uploading[/]")
    output = open('output.json', 'w')
    output.write(jsonpickle.encode(courses, indent=4))
    output.close()
    console.log("[bold green]Upload Complete[/]")

if __name__ == "__main__":
    asyncio.run(main())