



from typing import Iterable
from galaxy_wrappers.scraping.revisions import get_revisions_in_repo
from galaxy_wrappers.scraping.wrappers import Revision
from galaxy_wrappers.wrappers.WrapperCache import WrapperCache
import galaxy_wrappers.scraping.utils as utils


# SCRAPING
def scrape_single_repo(owner: str, repo: str) -> None:
    print(f'scraping toolshed for {repo} wrappers')
    do_revisions_scrape(owner, repo)
    do_wrappers_scrape(owner, repo)

def do_revisions_scrape(owner: str, repo: str) -> None:
    revisions_data = utils.load_data(utils.REVISION_DATA_PATH) # load
    revisions_data[owner][repo] = get_revisions_in_repo(owner, repo) # alter
    utils.save_data(utils.REVISION_DATA_PATH, revisions_data) # save

def do_wrappers_scrape(owner: str, repo: str) -> None:
    cache = WrapperCache(utils.WRAPPER_DATA_PATH) # load
    
    for revision in scrapable_revisions(owner, repo):
        wrappers = revision.get_wrappers()
        for wrapper in wrappers:
            cache.add(wrapper)  # save

def scrapable_revisions(owner: str, repo: str) -> Iterable[Revision]:
    revision_data = utils.load_data(utils.REVISION_DATA_PATH)
    for revision in revision_data[owner][repo]: # should never have key errors
        yield Revision(
            owner=owner,
            repo=repo,
            revision=revision['revision'],
            date_created=revision['date_created'],
        )







    