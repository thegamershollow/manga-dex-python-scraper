import os
import requests
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

def search_manga(query):
    url = "https://api.mangadex.org/manga"
    params = {"title": query, "limit": 5}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("data", [])
        if not results:
            print("No manga found.")
            return None
        
        for idx, manga in enumerate(results, start=1):
            title = manga["attributes"]["title"].get("en", list(manga["attributes"]["title"].values())[0])
            print(f"{idx}. {title} (ID: {manga['id']})")
        
        choice = int(input("Enter the number of the manga you want: ")) - 1
        return results[choice]["id"]
    else:
        print("Error fetching manga.")
        return None

def get_chapters(manga_id):
    url = f"https://api.mangadex.org/manga/{manga_id}/feed"
    params = {"translatedLanguage[]": "en", "order[chapter]": "asc", "limit": 100}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        chapters = {}
        for chapter in data.get("data", []):
            volume = chapter["attributes"].get("volume", "Unknown")
            chapter_num = chapter["attributes"].get("chapter", "Unknown")
            chapter_id = chapter["id"]
            
            if volume not in chapters:
                chapters[volume] = {}
            chapters[volume][chapter_num] = chapter_id
        return chapters
    else:
        print("Error fetching chapters.")
        return None

def download_image(page_url, folder, idx):
    response = requests.get(page_url, stream=True)
    if response.status_code == 200:
        with open(os.path.join(folder, f"{idx}.jpg"), "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

def download_chapter(chapter_id, manga_title, volume, chapter):
    url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        base_url = data["baseUrl"]
        chapter_hash = data["chapter"]["hash"]
        pages = data["chapter"]["data"]
        
        folder = os.path.join("Manga", manga_title, f"Volume {volume}", f"Chapter {chapter}")
        os.makedirs(folder, exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(tqdm(executor.map(lambda p: download_image(f"{base_url}/data/{chapter_hash}/{p[1]}", folder, p[0]), enumerate(pages, start=1)), total=len(pages), desc=f"Downloading Chapter {chapter}"))
        
        print(f"Chapter {chapter} downloaded successfully.")
    else:
        print("Error downloading chapter.")

def main():
    query = input("Enter manga title: ")
    manga_id = search_manga(query)
    if not manga_id:
        return
    
    chapters = get_chapters(manga_id)
    if not chapters:
        return
    
    print("Available volumes and chapters:")
    for volume, chapter_list in chapters.items():
        print(f"Volume {volume}: Chapters {', '.join(chapter_list.keys())}")
    
    option = input("Download (1) Entire Manga, (2) Specific Volume, (3) Specific Chapter: ")
    manga_title = query.replace(" ", "_")
    
    if option == "1":
        for volume, chapter_list in chapters.items():
            for chapter, chapter_id in chapter_list.items():
                download_chapter(chapter_id, manga_title, volume, chapter)
    elif option == "2":
        volume = input("Enter volume number: ")
        if volume in chapters:
            for chapter, chapter_id in chapters[volume].items():
                download_chapter(chapter_id, manga_title, volume, chapter)
        else:
            print("Volume not found.")
    elif option == "3":
        volume = input("Enter volume number: ")
        chapter = input("Enter chapter number: ")
        if volume in chapters and chapter in chapters[volume]:
            download_chapter(chapters[volume][chapter], manga_title, volume, chapter)
        else:
            print("Chapter not found.")
    else:
        print("Invalid option.")

if __name__ == "__main__":
    main()
