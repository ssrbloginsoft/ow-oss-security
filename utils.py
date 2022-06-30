import re


def diff_list(list1: list, list2: list) -> list:
    return list(set(list1) - set(list2)) + list(set(list2) - set(list1))


def validate_url(url):
    import re
    regex = re.compile(
        r'^https?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


def check_and_create_collections(db):
    collections = db.list_collection_names()
    if not "cves" in collections:
        db.create_collection("cves")

    if not "links" in collections:
        db.create_collection("links")

    if not "keyword_included_links" in collections:
        db.create_collection("keyword_included_links")

    print("==> Created all the required collections")


def find_all_using_pattern(pattern, str):
    return re.findall(pattern, str)


def unique(data):

    # insert the list to the set
    data_set = set(data)
    # convert the set to the list
    unique_list = (list(data_set))
    return unique_list


def get_chunks(list_obj, length):
    for i in range(0, len(list_obj), length):
        yield list_obj[i:i + length]
