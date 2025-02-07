import requests
from SPARQLWrapper import JSON
from config import SPARQL
import wikipedia
from db import create_mysql_connection
import mysql.connector as mydb

def get_coordinates_from_qid(qid):
    SPARQL.setQuery(f"""
        SELECT ?coordinate WHERE {{
            wd:{qid} wdt:P625 ?coordinate.
        }}
        LIMIT 1
    """)
    SPARQL.setReturnFormat(JSON)
    
    try:
        results = SPARQL.query().convert()
        if results["results"]["bindings"]:
            return results["results"]["bindings"][0]["coordinate"]["value"]
    except Exception as e:
        print(f"Error in get_coordinates_from_qid: {e}")
    
    return None

def get_location_details(location):
    print(f"Searching for location: {location}")
    
    url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'search': location,
        'language': 'ja',
        'format': 'json',
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'search' in data and len(data['search']) > 0:
            qid = data['search'][0]['id']
            
            # SPARQLクエリで詳細情報を取得
            SPARQL.setQuery(f"""
                SELECT ?label ?description WHERE {{
                    wd:{qid} rdfs:label ?label .
                    OPTIONAL {{ wd:{qid} schema:description ?description . }}
                    FILTER (lang(?label) = "ja")
                    FILTER (lang(?description) = "ja")
                }}
                LIMIT 1
            """)
            SPARQL.setReturnFormat(JSON)
            results = SPARQL.query().convert()

            if results["results"]["bindings"]:
                label = results["results"]["bindings"][0]["label"]["value"]
                description = results["results"]["bindings"][0].get("description", {}).get("value", "")
            else:
                label = data['search'][0]['label']
                description = data['search'][0].get('description', '')
            
            # 座標情報の取得
            coordinate = get_coordinates_from_qid(qid)
            
            print(f"Found location: {label}, Description: {description}, Coordinate: {coordinate}")
            return label, description, coordinate
        else:
            print("No location found")
            return None, None, None

    except Exception as e:
        print(f"Error in get_location_details: {e}")
        return None, None, None

def get_wikipedia_summary(place_label):
    try:
        summary = wikipedia.summary(place_label, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"DisambiguationError: {e.options}")
        return None
    except wikipedia.exceptions.PageError:
        print(f"No Wikipedia page found for {place_label}")
        return None
    except Exception as e:
        print(f"Error getting Wikipedia summary for {place_label}: {e}")
        return None

def save_location_details(post_id, location):
    place_label, description, coordinate = get_location_details(location)
    if place_label:
        try:
            # Wikipediaの概要取得
            wikipedia_summary = get_wikipedia_summary(place_label)
            conn = create_mysql_connection()
            cursor = conn.cursor()
            sql = """
                INSERT INTO location_details (post_id, location, description, coordinate, wikipedia_summary)
                VALUES (%s, %s, %s, %s, %s)
            """
            val = (post_id, place_label, description, coordinate, wikipedia_summary)
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Location details saved for post ID {post_id}")
        except mydb.Error as e:
            print(f"Error saving location details: {e}")
