import asyncio
import os
import random
import requests
import re
from dotenv import load_dotenv
from atproto import Client
from crontab import CronTab
from pathlib import Path

load_dotenv()

# Create a Bluesky Client
client = Client()

LOCATION_LIST = [
    "art_gallery",
    "art_studio",
    "cultural_landmark",
    "historical_place",
    "monument",
    "museum",
    "performing_arts_theater",
    "sculpture",
    "library",
    "adventure_sports_center",
    "bowling_alley",
    "comedy_club",
    "community_center",
    "concert_hall",
    "convention_center",
    "cultural_center",
    "cycling_park",
    "dog_park",
    "hiking_area",
    "historical_landmark",
    "movie_theater",
    "park",
    "skateboard_park",
    "state_park",
    "tourist_attraction",
    "visitor_center",
    "city_hall",
    "courthouse",
    "fire_station",
    "police",
    "post_office",
    "apartment_building",
    "apartment_complex",
    "church",
    "hindu_temple",
    "mosque",
    "synagogue",
    "bicycle_store",
    "book_store",
    "athletic_field",
    "ice_skating_rink",
    "swimming_pool",
    "sports_complex",
    "sports_club",
    "bus_station",
]

RETURN_FIELDS = (
    "places.shortFormattedAddress,places.displayName,places.photos,places.location"
)

def get_random_place_in_city(city: str) -> tuple[str, str, str] | None:
    api_key = os.getenv("GOOGLE_API_KEY")
    places_url = "https://places.googleapis.com/v1/places:searchNearby"
    randomized_locations = random.sample(LOCATION_LIST, 3)

    try:
        response = requests.post(
            places_url,
            headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": RETURN_FIELDS},
            json={
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": 44.0582, "longitude": -121.31531},
                        "radius": 7000,
                    }
                },
                "includedPrimaryTypes": randomized_locations,
            },
        )

        data = response.json()
        print("response.data:", data)

        if response.status_code == 200:
            places = data["places"]
            if places:
                while places:
                    random_place = random.choice(places)
                    short_address = random_place.get("shortFormattedAddress")
                    display_name = random_place.get("displayName", "").get("text", "")
                    photo_name = random_place.get("photos", [])[0].get("name", "")

                    if short_address and display_name and photo_name:
                        return short_address, display_name, photo_name
                    else:
                        places.remove(random_place)
            else:
                print("No places found")
                return None
        else:
            print(f"Places API error: {data['status']}")
            return None

    except Exception as error:
        print("Error fetching places data:", error)
        return None


def get_place_photo(photo_name: str, location_name: str) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    params = {"maxHeightPx": 1920, "key": api_key}

    response = requests.get(url, params=params)

    # Create images directory if it doesn't exist
    images_dir = Path(__file__).parent / "images"
    images_dir.mkdir(exist_ok=True)

    # Create safe filename from photo reference
    safe_filename = re.sub(r"[^a-zA-Z0-9]", "_", location_name) + ".jpg"
    image_path = images_dir / safe_filename

    image_path.write_bytes(response.content)
    return str(image_path)


def main():
    # Login to Bluesky
    client.login(os.getenv("BLUESKY_USERNAME"), os.getenv("BLUESKY_PASSWORD"))

    address, location_name, photo_name = get_random_place_in_city("Bend, OR")
    if not address:
        print("Failed to get a valid address.")
        return

    image_path = get_place_photo(photo_name, location_name)

    with open(image_path, "rb") as f:
        image_data = f.read()

    client.send_image(
        text=f"{location_name + ' at ' if location_name else ''}{address}",
        image=image_data,
        image_alt=f"An image from Google Maps of {location_name} at {address}",
    )

    # Remove the image file after posting
    os.remove(image_path)

    print("Just posted!")


main()