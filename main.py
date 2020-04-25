import asyncio
import threading
from queue import Queue  # thread safe
from dynamic_crauler_api import DynamicAPI


async def main():
    api = await (DynamicAPI().init())
    visited_urls = set()
    urls_queue = Queue()
    found_endpoints = set()
    found_urls = set()
    start_url = 'http://security-crawl-maze.app/javascript/frameworks/polymer/'
    urls_queue.put(start_url)
    visited_urls.add(start_url)
    while not urls_queue.empty():
        url = urls_queue.get()
        print(url)
        await api.add_url(url)
        results = await api.get_results()
        visited_urls.add(url)

        for result in results:
            print(result)
            for link in result['links']:
                if link.startswith('http://security-crawl-maze.app/'):
                    if link not in visited_urls:
                        urls_queue.put(link)
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
    await api.destroy()


if __name__ == '__main__':
    asyncio.run(main())
