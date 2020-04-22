import asyncio
import threading
from queue import Queue  # thread safe
from dynamic_crauler_api import DynamicAPI


async def main():
    api = await (DynamicAPI().init())
    start_list = Queue()
    found_endpoints = set()
    found_urls = set()
    start_list.put({'url': 'http://security-crawl-maze.app/javascript/frameworks/polymer/'})
    while not start_list.empty():
        task = start_list.get()
        print(task)
        await api.add_task(task)
        results = await api.get_results()
        for result in results:
            print(result)
            for link in result['links']:
                if link.startswith('http://security-crawl-maze.app/'):
                    start_list.put({'url': link})
            for url in result['requestedUrls']:
                found_endpoints.add(url)
            for url in result['urlChanges']:
                found_urls.add(url)
            # for url in result['redirectChain']:
                # print(url)
                # found_urls.add(url)
            print(len(found_endpoints))
    print(found_endpoints)
    print(found_urls)


if __name__ == '__main__':
    asyncio.run(main())
