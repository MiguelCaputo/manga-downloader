import urllib.request as req
from urllib.error import HTTPError
from urllib.parse import urlparse as parse
from bs4 import BeautifulSoup as bsoup
import os, csv, re, time

# Get the HTML of the requested URL
def get_soup(url):
    
    request = req.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = req.urlopen(request, timeout = 10)
    page_html = response.read()
    response.close()
    page_soup = bsoup(page_html, "html.parser")
    
    return page_soup

# Get all images from the website
def get_images(append, img_class, url):
    
    chapter_url = append + url['href']
    chapter_soup = get_soup(chapter_url)
    container = chapter_soup.find("div", {"class":img_class})
    images = container.findAll("img")  
    
    return images

# Creating an opener in order to be able to use headers while downloading images
def create_opener(referer):
    opener=req.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36'), ('Referer', referer)]
    req.install_opener(opener)

# Parsing the url and downloading the chapters
def parseurl(url, chapters, title, path):
    
    img_class = ''
    referer = ''
    append = ''
    fanfox = parse(url).netloc == 'fanfox.net'
    kakalot = parse(url).netloc == 'mangakakalot.com' or parse(url).netloc == 'manganelo.com'
    
    # Making the changes according to the used URL
    if kakalot:
        img_class = 'container-chapter-reader'
        referer = 'mangakakalot.com'
        
    elif fanfox:
        img_class = 'reader-main'
        referer = 'fanfox.net'
        append = 'https://fanfox.net/'
        
    create_opener(referer)
    
    # Creating the main folder
    folder = create_manga_folder(path, title)
      
    # Get the info for each chapter
    for chapter in chapters:
        download_chapters(chapter, append, img_class, title, url, folder)
        time.sleep(2)

# Download all the chapters for the given url
def download_chapters(chapter, append, img_class, title, url, folder):
    counter = 1
        
    # Get the images
    images = get_images(append, img_class, chapter.a)

    # Get the name for the chapter
    name = get_chapter_name(chapter, url, title)

    # Creating the folder
    chapter_folder = create_chapter_folder(folder, name)

    print("Downloading", name, end = ".......... ")

    # Downloading all the images
    for img in images:
        save_image(img["src"], chapter_folder,"{0}.jpg".format(counter))
        counter += 1
        time.sleep(0.5)

    print("Done!")

# Create the main folder for the manga
def create_manga_folder(path, title):
    
    # Cleaning the title so it can be used as a folder name
    clean_title = re.sub(r'[\\/*?:"<>|]',"",title)

    # Creating the folder for the manga
    folder = os.path.join(path, clean_title)
    
    # If the folder already exist create a copy with a different number
    if not os.path.exists(folder):
        os.mkdir(folder)
    
    return folder

# Creating the folder for the chapters
def create_chapter_folder(path, name):
    
    folder = os.path.join(path, name)
        
    count = 1
    new_path = folder
    
    # If a folder with that name already exists create a copy
    while os.path.isdir(new_path):
        new_path = folder + " (" + str(count) + ")"
        count += 1
        
    folder = new_path
    os.mkdir(folder)
    
    return folder

# Save the images on the pc
def save_image(url, path, name):
    
    file = os.path.join(path, name)
    while True:
        try:
            req.urlretrieve(url,file)
        except HTTPError:
            time.sleep(3)
            print(",")
            continue
        else:
            break              

# Check if the given filepath is correct
def check_filepath(curr):
    
    while True: 
        
        try:
            path = input('Enter a File path where you want to download (Leave empty for current path): ')
            
            # If path is not give, use the current one
            if path == "":
                path = curr
                
            elif not os.path.exists(path):
                raise Exception('Enter a valid file path')
                                
        except Exception as err:
            print(err)
            continue
                                
        else:
            break
            
    return path

# Get the title of the manga
def get_title(url, page_soup):
    
    title = ''
    
    # Getting the title according to each website
    if parse(url).netloc == 'mangakakalot.com':
        title = page_soup.find("title").text.replace(" Manga - Mangakakalot.com","")

    elif parse(url).netloc == 'manganelo.com':
        title = page_soup.find("title").text.replace(" Manga Online Free - Manganelo","")

    elif parse(url).netloc == 'fanfox.net':
        title = page_soup.find("span", {'class': 'detail-info-right-title-font'}).text
    
    return title

# Get all the chapters for each manga
def get_chapters(url, page_soup):
    
    chapters = []
    
    # If works differently for every server
    if parse(url).netloc == 'mangakakalot.com':
        chapters = page_soup.findAll("div", {"class":"row"})
        if len(chapters) > 0:
            chapters.pop(0)

    elif parse(url).netloc == 'manganelo.com':
        chapters = page_soup.findAll("li", {"class":"a-h"})

    elif parse(url).netloc == 'fanfox.net':
        chapters = page_soup.ul.findAll("li")

    # Fix the list
    chapters.reverse()

    return chapters

# Check if the url is supported
def url_validation():
    
    while True: 
        url = input("Enter page URL (We support mangakakalot.com, manganelo.com): ")
        title = ""
        try:
            
            page_soup = get_soup(url)

            fanfox = parse(url).netloc == 'fanfox.net'
            kakalot = parse(url).netloc == 'mangakakalot.com' or parse(url).netloc == 'manganelo.com'
            
            if not (kakalot or fanfox):
                raise Exception("Incorrect url")
                
            chapters = get_chapters(url, page_soup)
            title = get_title(url, page_soup)
                
            if len(chapters) == 0:
                raise Exception('Incorrect manga url or manga not available in that url')
                    
        except Exception as err:
            print(err)
            continue
            
        else:
            break
            
    return url, chapters, title

# Download the given manga
def download_manga(chapters, url, title):
    
    curr_path = os.path.abspath(os.getcwd())
    
    if len(chapters) == 0:
        print("Chapters not available for", title)
        return

    while True:
        
        print("\nWhat do you want to download?")
        print("1. The whole manga")
        print("2. One Chapter")
        print("3. A range of Chapters")
        print("4. Print chapter list")
        print("5. Go back\n")
        new_chapters = chapters

        choice = validate_input(1 , 5)
        
        if choice == 1:
            break 
            
        # Download a single chapter
        elif choice == 2:
            print("\n1. Enter a chapter index")
            print("2. Go back")
            choice = validate_input(1,2)
            if choice == 1:
                chapter = validate_input(0, len(chapters) - 1, "Chapter index: ", "Select a valid chapter index")
            else:
                continue
            new_chapters = chapters[chapter:chapter+1]
            break
            
        # Download a range of chapters
        elif choice == 3:
            print("\n1. Enter a chapter index range")
            print("2. Go back")
            choice = validate_input(1,2)
            
            if choice == 1:
                start = validate_input(0, len(chapters) - 1, "Starting index: ", "Select a valid starting index")
                end = validate_input(start, len(chapters) - 1, "Ending index: ", "Select a valid ending index")
                
            else:
                continue
                
            new_chapters = chapters[start:end+1]
            break
    
        # Print the chapters
        elif choice == 4:
            print_chapters(chapters, url, title)
            
        else:
            return
    
    # Finishing the downloading 
    path = check_filepath(curr_path)
    print("Downloading.....")
    parseurl(url ,new_chapters, title, path)    

# Get the name of a chapter
def get_chapter_name(chapter, url, title):
    
    fanfox = parse(url).netloc == 'fanfox.net'
    kakalot = parse(url).netloc == 'mangakakalot.com' or parse(url).netloc == 'manganelo.com'
    name = ''
    
    if kakalot:
        name = re.sub(r'[\\/*?:"<>|]',"",chapter.a.text).rstrip(' .')
    elif fanfox:
        name = re.sub(r'[\\/*?:"<>|]',"",chapter["title"].replace(title + ' ', '')).rstrip(' .')
        
    return name

# Print all the given chapters
def print_chapters(chapters, url, title):
    
    for i in range(len(chapters)):
        print("[{0}] {1}".format(i,get_chapter_name(chapters[i], url, title)))

# Validate user input
def validate_input(start, end, message = 'Enter your choice: ', error = 'Enter a correct choice.'):
    while True:
            try:
                choice = int(input(message))
                if choice < start or choice > end:
                    raise ValueError("Error")        
            except ValueError:
                print(error)
                continue
            else:
                break
    return choice

# Search the manga in the given URL
def search_manga_url(curr_path):
    
    # Check for a correct url
    url, chapters, title = url_validation()
    
    # Print the info
    print("\nManga Title:", title)
    print("Manga Chapters Available:", len(chapters))
    
    while True:
        print("\nWhat do you want to do?")
        print("1. Print chapter list")
        print("2. Download manga")
        print("3. Search another manga")
        print("4. Exit\n")

        # Get the user choice
        manga_choice = validate_input(1, 4)

        if manga_choice == 1:
            print_chapters(chapters, url, title)
            
        elif manga_choice == 2: 
            download_manga(chapters, url, title)   
                    
        elif manga_choice == 3:
            break

        else:
            finish = True
            break            
            
    return finish

# Get the info for every manga
def get_db_info(manga):
    chapter = manga.find('a', {'class': 'list-story-item-wrap-chapter'}).text 
    title = manga.h3.a['title']
    link = manga.h3.a['href']
    description = manga.p.text.replace('\n', '')

    if chapter == '':
        chapter = 'N/A'
    elif title == '':
        title = 'N/A'

    return title, link, chapter, description

# Get the manga list into a csv file
def create_csv(manga_list, path):
    
    manga_list.sort()
    manga_list.insert(0,['title', 'url', 'last_chapter', 'description'])
    
    path = create_file(path, 'manga_data', '.csv')
    
    with open(path, "w", newline="\n", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(manga_list)

# Download info about all the mangas
def get_manga_db(curr_path):
    
    print("\n1. Select where to download the manga DB (it will take some time)")
    print("2. Go back")
    
    choice = validate_input(1,2)
    
    if choice == 2:
        return 
    
    # Check the file path
    path = check_filepath(curr_path)
    
    # Find the last available page
    soup = get_soup('https://mangakakalot.com/manga_list?type=latest&category=all&state=all&page=1')
    last_page = int(soup.find('a', {'class':'page_blue page_last'}).text.replace('Last(','').replace(')','')) + 1
    
    manga_list = []
    n = int(last_page / 10)
    percentage = 0
    print('\nDownloading Database......')
    
    for i in range(1, last_page):
        
        # Find all mangas in the page
        page_soup = get_soup('https://mangakakalot.com/manga_list?type=latest&category=all&state=all&page={0}'.format(i))
        mangas = page_soup.findAll('div', {'class': 'list-truyen-item-wrap'})
                
        if i % n == 0:
            percentage += 10
            print('Downloading Database......{0}%'.format(percentage))
            
        for manga in mangas:
            
            # Get the info
            title, link, chapter, description = get_db_info(manga)
            manga_list.append([title, link, chapter, description])
          
    # Save the file
    create_csv(manga_list, path)
    print("Done!")

# Create a file
def create_file(path, name, ext):
    file = os.path.join(path, name)
        
    count = 1
    new_path = file + ext
    
    # If the file name already exist, create a copy
    while os.path.isfile(new_path):
        new_path = file + "(" + str(count) + ")" + ext
        count += 1

    return new_path

# Get all mangas in the url
def get_all_mangas_by_name(url):
    return get_soup(url).findAll('div', {'class' : 'search-story-item'})

# Get the info for all the mangas in the url
def get_mangas_info(mangas):
    lista = []
    for manga in mangas:
        a = manga.find('a', {'class':'item-img'})
        link = a['href']
        name = a['title']
        info = {
            'title': name,
            'url': link
        }
        lista.append(info)
    return lista

# Print titles of the found mangas
def print_titles(mangas):
    for i in range(len(mangas)):
        print("[{0}] {1}".format(i,mangas[i]['title']))

# Sanitaze the user input
def sanitaze_input(string):
    return ''.join([c for c in string if c.isalnum() or c.isspace()]).replace(' ', "_").lower()   

# Search all mangas with a given keyword
def search_keywords(keyword):
    
    name = sanitaze_input(keyword)
    url = 'https://manganelo.com/search/story/{0}'.format(name)
    
    mangas = get_all_mangas_by_name(url)
    info = get_mangas_info(mangas)
    
    # If no mangas are found
    if len(info) == 0:
        print("No mangas available with that keyword")
        
    else: 
        print("\nShowing Top {0} mangas with that keyword".format(len(mangas)))
        print("If your manga is not on the list try being more specific with the name")
        print_titles(info)
        
    return info

# Download the manga in the list
def download_manga_by_name(mangas):
    
    index = validate_input(0, len(mangas)-1, 'Manga index: ', 'Please select a correct index')
    title = mangas[index]['title']
    url = mangas[index]['url']
    
    chapters = get_chapters(url, get_soup(url))
    
    download_manga(chapters, url, title)

# Search mangas by a given keyword
def search_manga_name():
    

    while True:    
        print("\nWhat do you want to do?")
        print("1. Search Manga by Keyword")
        print("2. Go back\n")  
        
        mangas = []
        choice = validate_input(1,2)
       
        if choice == 2:
            return 
        
        else:
            # Find the mangas
            keyword = input("Keyword to search: ")
            mangas = search_keywords(keyword)
            
            while True:
                
                # If no mangas are found
                if len(mangas) == 0:
                    break
                
                print("\n1. Print list again")
                print("2. Download manga from the list")
                print("3. Search another manga")
                print("4. Go back\n")
                
                choice = validate_input(1,4)

                if choice == 1:
                    print_titles(mangas)
                    
                elif choice == 2:
                    download_manga_by_name(mangas)
                    
                elif choice == 3:
                    break
            
                else: return                

def main():
    
    # Get the path of the current directory
    curr_path = os.path.abspath(os.getcwd())
    
    while True:
        
        finish = False
        print("\n1. Search Manga by Link")
        print("2. Search Manga by Name")
        print("3. Donwload Manga Database Information")
        print("4. Exit\n")
        
        # Check if the choice is correct
        choice = validate_input(1, 4)
        
        if choice == 1:
            finish = search_manga_url(curr_path)
        
        elif choice == 2:
            search_manga_name()
 
        elif choice == 3:
            get_manga_db(curr_path)
            
        # Exit
        elif choice == 4:
            break
        
        if finish:
            break
            
    print("Thank you for using the program!")

if __name__ == "__main__":
    main()