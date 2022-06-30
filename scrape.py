from time import sleep
from typing import List
from main import Scrapper, Page, connect_to_db
from bs4 import BeautifulSoup
from lxml import etree
import threading

from utils import check_and_create_collections, find_all_using_pattern, get_chunks, unique

# scrapper = Scrapper()
base_url = "https://www.openwall.com/lists/oss-security/"
# page = Page(base_url)


def get_links(tree, base_url):
    links = []
    table = tree.xpath("/html/body/table[3]")[0]
    soup = BeautifulSoup(etree.tostring(table), "html.parser")
    tr_elements = soup.find_all('tr')
    for i, tr in enumerate(tr_elements):
        if(i != 0):
            td_elements = tr.find_all('td')
            for td in td_elements:
                a_tag = td.find('a')
                if(a_tag and a_tag.find('b') == None):
                    href = a_tag['href']
                    total_links = int(a_tag.text)
                    link = base_url+href
                    links.append((link, total_links))
    return links


def page_handler1(tree):
    db = connect_to_db()
    check_and_create_collections(db)
    links_Collection = db.links
    cves_collection = db.cves

    links = []
    main_tree_links_config = get_links(tree, base_url)
    for main_tree_link_config in main_tree_links_config:
        main_tree_link = main_tree_link_config[0]
        sub_tree = Page(main_tree_link).get_page()
        sub_tree_links_config = get_links(sub_tree, main_tree_link)
        for sub_tree_link_config in sub_tree_links_config:
            base_url_sub_tree = sub_tree_link_config[0]
            total_sub_tree_links = sub_tree_link_config[1]
            for i in range(total_sub_tree_links):
                link = base_url_sub_tree+str(i+1)
                links.append(link)
    for link in links:
        unique_id = link[44:]
        if links_Collection.find_one({"un_id": unique_id}) is None:
            link_obj = {
                "un_id": unique_id,
                "link": link
            }
            links_Collection.insert_one(link_obj)


# scrapper.create_and_register_plugin("OW", page, page_handler1)

# for exec in scrapper.execute_all():
#     # print(exec)
#     pass


def scrape():
    db = connect_to_db()
    check_and_create_collections(db)

    links_Collection = db.links
    links = list(links_Collection.find().skip(6140))

    # chunks_gen = get_chunks(list(links), 20)
    count = 0
    ids = []

    print("==> Started assigning threads")

    while True:
        if(count == len(links)):
            print("==> Completed the scrapping")
            break

        link_config = links[count]

        if(count == 1000):
            print("==> Creating new MongoClient")
            db = connect_to_db()

        if(len(ids) == 40):
            sleep(5)
            ids = remove_dead_thread_ids(ids)
            if(len(ids) == 40):
                print('==> All 40 threads are still alive sleeping for 10s')
                sleep(2)
                continue

        t1 = threading.Thread(target=insert_data,
                              args=(link_config, db), name='t1')
        t1.start()

        print(f"Created and started thread {count+1} with pid:{t1.ident}")

        ids.append(t1)
        count += 1


def remove_dead_thread_ids(ids: List[threading.Thread]):

    print(f'Trying to remove dead threads')

    active_threads = list(filter(lambda id: id.is_alive() == True, ids))

    if(len(active_threads) < 40):
        print(f'Removed {40-len(active_threads)}...!')

    return active_threads


def insert_data(link_config, db):
    link = link_config['link']

    tree = Page(link).get_page()
    if(tree != None):
        pre = tree.xpath('/html/body/pre')[0]
        soup = BeautifulSoup(etree.tostring(pre), "html.parser")

        cve_pattern = r'CVE-\d+-\d+'
        keyword_pattern = r'SECURITY -'

        matches = find_all_using_pattern(cve_pattern, soup.text)
        keyword_matches = find_all_using_pattern(keyword_pattern, soup.text)

        store_info(matches=matches, keyword_matches=keyword_matches,
                   link_config=link_config, db=db)
        print(f'completed scrapping for url: {link}')
    else:
        file_r = open("failed_urls.txt", 'a')
        file_r.write(link+'\n')
        file_r.close()


def store_info(matches: list, keyword_matches: list, link_config, db):

    date = link_config['un_id'][:-2]
    link = link_config['link']

    cves_collection = db.test_cves
    keyword_included_links_c = db.test_keyword_included_links

    if(matches == None or len(matches) == 0):
        if(keyword_matches != None and len(keyword_matches) != 0):
            keyword_included_links_c.insert_one({
                "link": link,
                "date": date
            })
    else:
        unique_cve_matches = unique(matches)
        for match in unique_cve_matches:
            cve = cves_collection.find_one({'cve_id': match})
            if cve is not None:
                if not link in cve['links']:
                    cves_collection.update_one(
                        {'cve_id': match}, {'$inc': {'count': 1}, '$push': {'links': link}})
            else:
                cves_collection.insert_one(
                    {'cve_id': match, 'count': 1, "links": [link]})


scrape()
