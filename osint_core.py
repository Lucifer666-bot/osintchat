import aiohttp, asyncio, re, os, json, subprocess, tempfile, shutil
from dotenv import load_dotenv
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

async def vazamentos_por_telefone(session, tel):
    tel = re.sub(r'\D', '', tel)
    url = "https://leak-lookup.com/api/search"
    data = {"key": "guest", "type": "phone", "query": tel}
    async with session.post(url, data=data) as resp:
        try:
            return await resp.json()
        except:
            return {}

async def social_links(session, query, site):
    q = f'site:{site} "{query}"'
    params = {"engine": "google", "q": q, "api_key": SERPAPI_KEY}
    async with session.get("https://serpapi.com/search", params=params) as resp:
        j = await resp.json()
        return [r["link"] for r in j.get("organic_results", []) if site in r["link"]]

async def run_maigret(username):
    tmp = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json")
    tmp.close()
    subprocess.run(["python", "-m", "maigret", username, "--json", tmp.name],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with open(tmp.name) as f:
            return json.load(f)
    except:
        return {}
    finally:
        os.unlink(tmp.name)

async def run_holehe(email):
    tmp = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json")
    tmp.close()
    subprocess.run(["holehe", email, "--json"], stdout=tmp, stderr=subprocess.DEVNULL)
    try:
        with open(tmp.name) as f:
            return json.load(f)
    except:
        return {}
    finally:
        os.unlink(tmp.name)

async def pipeline(target):
    tel = re.fullmatch(r"\d{10,11}", re.sub(r'\D', '', target))
    tipo = "telefone" if tel else "nome"
    result = {"input": target, "tipo": tipo}
    async with aiohttp.ClientSession() as session:
        if tipo == "telefone":
            result["vazamentos"] = await vazamentos_por_telefone(session, target)
        result["instagram"] = await social_links(session, target, "instagram.com")
        result["facebook"]  = await social_links(session, target, "facebook.com")
        username = target if not tel else ""
        if username:
            result["maigret"] = await run_maigret(username)
        emails = []
        if emails:
            result["holehe"] = await run_holehe(emails[0])
    return result