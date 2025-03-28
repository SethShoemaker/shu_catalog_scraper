import asyncio
import lib
import jsonpickle

async def main():
    courses = []
    prefix_list = await lib.get_course_prefix_list()
    for prefix in prefix_list:
        courses.extend(await lib.get_courses_with_prefix(prefix))
    print(jsonpickle.encode(courses))

if __name__ == "__main__":
    asyncio.run(main())