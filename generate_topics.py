"""
Generate new law topics from around the world using AI when topics.txt runs low.

This script:
1. Tracks used topics in used_topics.txt
2. When available topics drop below 20, generates fresh, fascinating ancient & medieval law topics
3. Ensures NO topic is EVER repeated by checking against used topics
4. Cleans and maintains topics.txt with only fresh, unused topics
"""

import os
import re
import time
import requests
from urllib.parse import quote
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Curated fallback topics to guarantee there is never a zero-topic situation
CURATED_FALLBACK_TOPICS = [
    "[ANCIENT] Code of Ur-Nammu Earliest Known Law Code",
    "[ANCIENT] Code of Lipit-Ishtar Mesopotamian Legal Reform",
    "[ANCIENT] Laws of Eshnunna Ancient Babylonian Civil Statutes",
    "[ANCIENT] Solon's Constitutional Reforms in Archaic Athens",
    "[ANCIENT] Cleisthenes and the Birth of Athenian Democratic Law",
    "[ANCIENT] Gortyn Code Ancient Cretan Civil Law",
    "[ANCIENT] Law of the Twelve Tables Early Roman Republic",
    "[ANCIENT] Lex Aquilia Roman Law on Property Damage",
    "[ANCIENT] Praetorian Edicts and the Evolution of Roman Equity",
    "[ANCIENT] Justinian Code Corpus Juris Civilis",
    "[ANCIENT] Institutes of Gaius Foundations of Roman Legal Education",
    "[ANCIENT] Ashoka's Edicts Moral and Legal Governance in India",
    "[ANCIENT] Arthashastra Ancient Indian Statecraft and Penalties",
    "[ANCIENT] Qin Dynasty Legalism and Strict State Decrees",
    "[ANCIENT] Han Dynasty Legal Synthesis and Confucian Justice",
    "[ANCIENT] Tang Dynasty Penal Code Benchmark of Asian Jurisprudence",
    "[ANCIENT] Mosaic Covenant Code and Deuteronomic Legal Tradition",
    "[ANCIENT] Egyptian Vizier Rechmire's Duties of Administration and Justice",
    "[ANCIENT] Hittite Telepinu Proclamation on Royal Succession Law",
    "[ANCIENT] Assyrian Middle Laws on Women, Marriage, and Property",
    "[MEDIEVAL] Salic Law Frankish Legal Tradition and Female Succession",
    "[MEDIEVAL] Lex Visigothorum Visigothic Code of Equal Application",
    "[MEDIEVAL] Brehon Laws Ancient Gaelic Irish Legal Restitution",
    "[MEDIEVAL] Laws of Hywel Dda Medieval Welsh Legal System",
    "[MEDIEVAL] Assize of Clarendon King Henry II and the Jury System",
    "[MEDIEVAL] Constitutions of Clarendon Church versus Crown Jurisdiction",
    "[MEDIEVAL] Magna Carta 1215 Clause 39 Due Process Origins",
    "[MEDIEVAL] Charter of the Forest Protection of Commoners Rights",
    "[MEDIEVAL] Sachsenspiegel Medieval German Saxon Customary Law",
    "[MEDIEVAL] Schwabenspiegel Southern German Regional Legal Code",
    "[MEDIEVAL] Siete Partidas King Alfonso X's Spanish Legal Masterpiece",
    "[MEDIEVAL] Coutumes de Beauvaisis Philippe de Beaumanoir Customary Law",
    "[MEDIEVAL] Gratian's Decretum Harmony of Medieval Discordant Canons",
    "[MEDIEVAL] Golden Bull of 1356 Holy Roman Emperor Election Law",
    "[MEDIEVAL] Golden Bull of 1222 Hungarian Constitutional Protections",
    "[MEDIEVAL] Statute of Laborers 1351 Post-Plague Wage Controls",
    "[MEDIEVAL] Hanseatic League Maritime Law and Merchant Guild Courts",
    "[MEDIEVAL] Rolls of Oleron Western European Admiralty and Maritime Code",
    "[MEDIEVAL] Consulate of the Sea Mediterranean Maritime Law Code",
    "[MEDIEVAL] Wisby Sea Laws Baltic Trade and Shipping Regulations",
    "[MEDIEVAL] Venetian Council of Ten State Security and Judicial Tribunals",
    "[MEDIEVAL] Icelandic Althing Lawspeaker and Commonwealth Assemblies",
    "[MEDIEVAL] Medieval Scandinavian Gulathing Provincial Legal Code",
    "[MEDIEVAL] King Magnus the Lawmender's Norwegian National Code of 1274",
    "[MEDIEVAL] Russkaya Pravda Kievan Rus Legal System of Monetary Fines",
    "[MEDIEVAL] Sudebnik of 1497 Ivan III's Centralized Russian Legal Code",
    "[MEDIEVAL] Dushan's Code Emperor Stefan Dushan's Serbian Constitution",
    "[MEDIEVAL] Kanun of Leke Dukagjini Albanian Customary Law of Honor",
    "[MEDIEVAL] Mali Empire Kouroukan Fouga Constitutional Charter of 1235",
    "[MEDIEVAL] Aztec Supreme Judicial Council and Texcoco Legal Decrees",
]

def clean_topic_line(line: str) -> str:
    """Clean a generated topic string."""
    cleaned = line.strip()
    for prefix in ['- ', '* ', '• ', '> ']:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    cleaned = re.sub(r'^\d+[\.\:\)]\s*', '', cleaned).strip()
    cleaned = cleaned.strip('"\'*`')
    return cleaned

def generate_new_topics(count=50, used_topics_set=None):
    """Generate new law topics covering ancient and medieval legal history."""
    if used_topics_set is None:
        used_topics_set = set()
    
    normalized_used = {t.lower().replace("[ancient] ", "").replace("[medieval] ", "").strip() for t in used_topics_set}
    
    api_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    all_new_topics = []
    
    system_prompt = (
        "You are a legal historian specializing in ancient and medieval laws worldwide. "
        "Create a list of unique topics about fascinating ancient and medieval legal history in English. "
        "Each topic must start with either [ANCIENT] or [MEDIEVAL], followed by 4 to 10 words describing a specific law, "
        "code, trial, court practice, or legal milestone. "
        "Cover diverse civilizations: Sumerian, Babylonian, Roman, Greek, Egyptian, Chinese dynasties, Indian (Vedic/Mauryan), "
        "Byzantine, Anglo-Saxon, Norse, Islamic Caliphates, Frankish, Gaelic, Spanish, Mesoamerican, African kingdoms, etc. "
        "Output ONLY topics, one per line, no numbers, no bullet points, no commentary."
    )
    user_prompt = f"Generate {count} unique, fascinating ancient and medieval law topics from different world civilizations."
    
    # Strategy 1: Pollinations Paid API (gen.pollinations.ai) if API key is present
    if api_key:
        print("[topics] Using Pollinations AI Chat API to generate fresh topics...")
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 1.0,
            "max_tokens": 1500
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        try:
            r = requests.post(
                "https://gen.pollinations.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            r.raise_for_status()
            data = r.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            for line in text.split("\n"):
                topic = clean_topic_line(line)
                if not topic or len(topic) < 10:
                    continue
                if not (topic.startswith("[ANCIENT]") or topic.startswith("[MEDIEVAL]")):
                    topic = f"[ANCIENT] {topic}"
                raw_norm = topic.lower().replace("[ancient] ", "").replace("[medieval] ", "").strip()
                if raw_norm not in normalized_used and topic not in all_new_topics:
                    all_new_topics.append(topic)
            print(f"[topics] Generated {len(all_new_topics)} topics via Pollinations API")
        except Exception as e:
            print(f"[topics] Pollinations Chat API error: {e}")
    
    # Strategy 2: Free endpoint fallback if needed
    if len(all_new_topics) < count:
        print("[topics] Trying text.pollinations.ai fallback...")
        try:
            free_url = "https://text.pollinations.ai/" + quote(user_prompt)
            r = requests.get(
                free_url,
                params={"system": system_prompt, "model": "openai", "temperature": 1.0},
                timeout=45
            )
            if r.status_code == 200 and r.text.strip():
                for line in r.text.strip().split("\n"):
                    topic = clean_topic_line(line)
                    if not topic or len(topic) < 10:
                        continue
                    if not (topic.startswith("[ANCIENT]") or topic.startswith("[MEDIEVAL]")):
                        topic = f"[MEDIEVAL] {topic}"
                    raw_norm = topic.lower().replace("[ancient] ", "").replace("[medieval] ", "").strip()
                    if raw_norm not in normalized_used and topic not in all_new_topics:
                        all_new_topics.append(topic)
                print(f"[topics] Total topics after free endpoint: {len(all_new_topics)}")
        except Exception as e:
            print(f"[topics] Fallback API error: {e}")
    
    # Strategy 3: Curated fallback list
    if len(all_new_topics) < count:
        print("[topics] Refilling with curated legal history topics...")
        for topic in CURATED_FALLBACK_TOPICS:
            raw_norm = topic.lower().replace("[ancient] ", "").replace("[medieval] ", "").strip()
            if raw_norm not in normalized_used and topic not in all_new_topics:
                all_new_topics.append(topic)
            if len(all_new_topics) >= count:
                break
    
    return all_new_topics[:count]

def check_and_update_topics(min_threshold=20, generate_count=50):
    """Check topics.txt and add more if needed, tracking used topics."""
    topics_file = Path('topics.txt')
    used_topics_file = Path('used_topics.txt')
    
    used_topics = set()
    if used_topics_file.exists():
        with open(used_topics_file, 'r', encoding='utf-8') as f:
            used_topics = set(line.strip() for line in f if line.strip())
    
    normalized_used = {u.lower().strip() for u in used_topics}
    
    existing_topics = []
    if topics_file.exists():
        with open(topics_file, 'r', encoding='utf-8') as f:
            for line in f:
                t = line.strip()
                if t and t.lower() not in normalized_used and t not in existing_topics:
                    existing_topics.append(t)
    
    print(f"[topics] Current available fresh topics: {len(existing_topics)}")
    print(f"[topics] Total used topics: {len(used_topics)}")
    
    # Check if we need more topics
    if len(existing_topics) < min_threshold:
        needed = max(generate_count, min_threshold - len(existing_topics) + 20)
        print(f"[topics] Low on topics ({len(existing_topics)} < {min_threshold})! Generating {needed} fresh topics...")
        
        new_topics = generate_new_topics(needed, used_topics)
        for t in new_topics:
            if t not in existing_topics:
                existing_topics.append(t)
        
        # Save refreshed list to topics_file
        with open(topics_file, 'w', encoding='utf-8') as f:
            for topic in existing_topics:
                f.write(f"{topic}\n")
        
        print(f"[topics] Refreshed topics.txt! Total available now: {len(existing_topics)}")
    else:
        # Write back filtered topics to keep topics.txt clean of already used ones
        with open(topics_file, 'w', encoding='utf-8') as f:
            for topic in existing_topics:
                f.write(f"{topic}\n")
        print(f"[topics] Enough topics available ({len(existing_topics)})")
    
    return existing_topics

if __name__ == '__main__':
    check_and_update_topics()
