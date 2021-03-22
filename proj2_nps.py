#################################
##### Name:
##### Uniqname:
#################################

from bs4 import BeautifulSoup
import requests
import json
import p2_secrets as secrets # file that contains your API key

CACHE_FILENAME = "nationalsite_cache.json"
#CACHE_DICT = {}

map_quest_url = "http://www.mapquestapi.com/search/v2/radius"
national_site_url = 'https://www.nps.gov'

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, url):
        CACHE_DICT = open_cache()
        if url in CACHE_DICT.keys():
            html_text = CACHE_DICT[url]
            print("Using Cache")
        else:
            page = requests.get(url)
            html_text = page.text
            CACHE_DICT[url] = html_text
            save_cache(CACHE_DICT)
            print("Fetching")
        soup = BeautifulSoup(html_text, 'html.parser')
        zipcode = soup.find_all('span', class_="postal-code")
        if len(zipcode) != 0:
            self.zipcode = zipcode[0].contents[0].strip()
        else:
            self.zipcode = "no zipcode"
        phone = soup.find_all('span', class_="tel")
        if len(phone) != 0:
            self.phone = phone[0].contents[0].strip()
        else:
            self.phone = "no phone"
        city = soup.find_all('span', itemprop="addressLocality")
        if len(city) != 0:
            self.address = (city[0].contents[0].strip())
        else:
            self.address = "no city"
        state = soup.find_all('span', itemprop="addressRegion")
        self.address += ', '
        if len(state) != 0:
            self.address += state[0].contents[0].strip()
        else:
            self.address += "no state"
        name = soup.find_all('a', class_="Hero-title")
        if len(name) != 0:
            self.name = str(name[0].contents[0])
        else:
            self.name = "no name"
            #print('+++++++++', name[0].contents[0])
        category = soup.find_all('span', class_="Hero-designation")
        #print("__________", category)
        if len(category[0].contents) != 0:
            self.category = str(category[0].contents[0])
        else:
            self.category = ""
    
    def info(self):
        '''Get the info of the national site

         Parameters
    ----------
    None

    Returns
    -------
    str
        the formatted string that has information about the national site
    '''
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    #TODO Implement function
    result = baseurl + '?'
    for k, v in params.items():
        result += ("_" + str(k) + "_" + str(v))
    
    return result


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    #pass
    URL = national_site_url
    result = {}
    CACHE_DICT = open_cache()
    if URL in CACHE_DICT.keys():
        result = json.loads(CACHE_DICT[URL])
        print("Using Cache")
    else:
        print("Fetching")
        page = requests.get(URL)
        html_text = page.text
        soup = BeautifulSoup(html_text, 'html.parser')
        all_states = soup.find_all('ul', class_="dropdown-menu SearchBar-keywordSearch")
        for state in all_states[0].find_all('li'):
            state_name = str(state.find('a').contents[0].lower())
            sub_url = str(state.find('a')['href'])
            result[state_name] = URL+sub_url
        result_txt = json.dumps(result)
        CACHE_DICT[URL] = result_txt
        save_cache(CACHE_DICT)
    return result
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    park = NationalSite(site_url)
    return park


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    #pass
    CACHE_DICT = open_cache()
    if state_url in CACHE_DICT.keys():
        html_text = CACHE_DICT[state_url]
        print("Using Cache")
    else:
        page = requests.get(state_url)
        html_text = page.text
        CACHE_DICT[state_url] = html_text
        save_cache(CACHE_DICT)
        print("Fetching")
    site_inst_list = []
    soup = BeautifulSoup(html_text, 'html.parser')
    site_list = soup.find_all('h3', class_="")
    for one_site in site_list:
        href = one_site.find('a')['href']
        href = national_site_url + href + "index.htm"
        new_site = get_site_instance(href)
        site_inst_list.append(new_site)
    return site_inst_list
    




def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    if not site_object.zipcode.isnumeric():
        raise RuntimeError
    params={
        'key': secrets.API_KEY,
        'origin': site_object.zipcode,
        'radius': 10,
        'units': 'm',
        'maxMatches': 10,
        'ambiguities': 'ignore',
        'outFormat': 'json' 
    }

    response = requests.get(map_quest_url, params=params)
    response_dict = json.loads(response.text)
    return response_dict



def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def formatted_printing_nearby(nearby_dict):
    ''' Print the formatted information of the nearby place
    
    Parameters
    ----------
    nearby_dict: dict
        The dictionary that contains the nearby place information

    Returns
    -------
    None
    '''
    nearby_place = nearby_dict['searchResults']
    number_print = min(10, len(nearby_place))
    for i in range(number_print):
        name = nearby_place[i]['name']
        fields = nearby_place[i]['fields']
        address = ""
        cat = ""
        city = ""
        if 'address' in fields.keys():
            address = fields['address']
        if len(address) == 0:
            address = "no address"
        if 'city' in fields.keys():
            city = fields['city']
        if len(city) == 0:
            city = "no city"
        if 'group_sic_code_name_ext' in fields.keys():
            cat = fields['group_sic_code_name_ext']
        if len(cat) == 0:
            cat = "no category"

        print(f'- {name} ({cat}): {address}, {city}')


def formatted_printing(site_list, state_name):
    ''' Print the formatted information of sites in the given state
    
    Parameters
    ----------
    site_list: list
        The list of national site
    state_name: str
        The name of stet
    
    Returns
    -------
    None
    '''

    print('---------------------------------')
    print(f'List of natinal sites in {state_name}')
    print('---------------------------------')
    counter = 1
    for site in site_list:
        print(f'[{counter}]', site.info())
        counter += 1

    


if __name__ == "__main__":
    CACHE_DICT = open_cache()
    asking_text = 'Enter a state name (e.g. Michigan, michigan) or "exit"\n: '
    state_url_dict = build_state_url_dict()
    exit_flag = False
    while(True):
        if exit_flag:
            break
        user_in = input(asking_text)
        if user_in == "exit":
            exit_flag = True
            break
        else:
            state = user_in.lower()
            if state not in state_url_dict.keys():
                asking_text = f'[Error] Enter proper state name\nEnter a state name (e.g. Michigan, michigan) or "exit"\n: '
                continue
            state_url = state_url_dict[state]
            site_list = get_sites_for_state(state_url)
            formatted_printing(site_list, state)
            while(True):
                inner_asking_text = 'Choose the number for detail search or "exit" or "back"\n:'
                inner_user_in = input(user_in)
                if inner_user_in == 'back':
                    break
                elif inner_user_in == 'exit':
                    exit_flag = True
                    break
                try:
                    input_idx = int(inner_user_in)
                    if input_idx <= 0:
                        raise RuntimeError
                    site_nearby = site_list[input_idx-1]
                    f_string = f"Places near {site_nearby.name}"
                    result = get_nearby_places(site_nearby)
                    print('-'*(len(f_string)+5))
                    print(f"Places near {site_nearby.name}")
                    print('-'*(len(f_string)+5))
                    formatted_printing_nearby(result)
                except:
                    print("[Error] Invalid input")
                    print('-------------------------------------------')
                    
                    

    # site_mi2 = get_site_instance('https://www.nps.gov/slbe/index.htm')
    # site_wy2 = get_site_instance('https://www.nps.gov/fobu/index.htm')
    # near_mi = get_nearby_places(site_mi2)
    #print(len(near_mi))