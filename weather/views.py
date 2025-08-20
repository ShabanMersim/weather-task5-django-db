import os, random, statistics, requests
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localtime

from .models import City, WeatherSnapshot

API_KEY = os.getenv("OWM_API_KEY", "YOUR_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
UNITS_DEFAULT = "metric"

CITY_POOL = [
    "Sofia,BG","Plovdiv,BG","Varna,BG","Burgas,BG",
    "London,GB","Paris,FR","Berlin,DE","Rome,IT","Madrid,ES",
    "New York,US","Los Angeles,US","Toronto,CA","Vancouver,CA",
    "Tokyo,JP","Seoul,KR","Beijing,CN","Sydney,AU","Melbourne,AU",
    "Cairo,EG","Istanbul,TR","Athens,GR","Stockholm,SE","Oslo,NO",
    "Dubai,AE","Singapore,SG","Bangkok,TH","Rio de Janeiro,BR","Buenos Aires,AR"
]

def interpret_condition(d):
    main = d["weather"][0]["main"]
    clouds = d.get("clouds", {}).get("all", 0)
    if main in ("Rain","Drizzle","Thunderstorm"):
        return "🌧️ Вали"
    if main == "Snow":
        return "❄️ Сняг"
    if main == "Clear":
        return "☀️ Слънчево"
    if clouds >= 50:
        return "☁️ Облачно"
    return f"🌤️ {d['weather'][0]['description']}"

def fetch_and_store(city_query: str, units: str = UNITS_DEFAULT, source: str = "api"):
    r = requests.get(
        BASE_URL,
        params={"q": city_query, "appid": API_KEY, "units": units, "lang": "bg"},
        timeout=10
    )
    r.raise_for_status()
    d = r.json()

    # normalize result
    item = {
        "name": d["name"],
        "temp": float(d["main"]["temp"]),
        "humidity": int(d["main"]["humidity"]),
        "condition": interpret_condition(d),
    }

    # upsert City
    city_obj, _ = City.objects.get_or_create(
        query=city_query,
        defaults={
            "name": d.get("name") or city_query.split(",")[0],
            "country": d.get("sys", {}).get("country", ""),
            "lat": (d.get("coord") or {}).get("lat"),
            "lon": (d.get("coord") or {}).get("lon"),
        },
    )
    # optional refresh of meta
    changed = False
    if city_obj.name != d.get("name", city_obj.name):
        city_obj.name = d.get("name", city_obj.name); changed = True
    if city_obj.country != d.get("sys", {}).get("country", city_obj.country):
        city_obj.country = d.get("sys", {}).get("country", city_obj.country); changed = True
    if changed:
        city_obj.save()

    # store snapshot
    WeatherSnapshot.objects.create(
        city=city_obj,
        units=units,
        temp=item["temp"],
        humidity=item["humidity"],
        condition=item["condition"],
        raw=d,
        source=source,
    )
    return item

def index(request):
    warn = None if os.getenv("OWM_API_KEY") else "⚠️ Задай OWM_API_KEY преди ползване."
    return render(request, "weather/index.html", {"warning": warn})

def api_refresh_random(request):
    units = request.GET.get("units", UNITS_DEFAULT)
    cities = random.sample(CITY_POOL, 5)
    items = []
    for c in cities:
        try:
            items.append(fetch_and_store(c, units, source="random"))
        except requests.RequestException:
            pass

    stats = None
    if items:
        coldest = min(items, key=lambda x: x["temp"])
        avg = statistics.mean(x["temp"] for x in items)
        stats = {"coldest_city": coldest["name"], "coldest_temp": coldest["temp"], "avg_temp": avg}

    return JsonResponse({"items": items, "stats": stats, "units": units})

def api_refresh_city(request):
    q = request.GET.get("q", "").strip()
    units = request.GET.get("units", UNITS_DEFAULT)
    if not q:
        return JsonResponse({"error": "Missing ?q=City,CC"}, status=400)
    try:
        item = fetch_and_store(q, units, source="manual")
        return JsonResponse({"item": item, "units": units})
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=400)

def api_history(request):
    q = request.GET.get("q", "").strip()
    limit = int(request.GET.get("limit", 10))
    if not q:
        return JsonResponse({"error": "Missing ?q=City,CC"}, status=400)
    try:
        city_obj = City.objects.get(query=q)
    except City.DoesNotExist:
        return JsonResponse({"error": "No history for this city yet."}, status=404)

    snaps = list(city_obj.snapshots.order_by("-fetched_at")[:limit])
    if not snaps:
        return JsonResponse({"error": "No history records yet."}, status=404)

    items = [{
        "fetched_at": localtime(s.fetched_at).isoformat(),
        "temp": s.temp,
        "humidity": s.humidity,
        "condition": s.condition,
        "units": s.units,
    } for s in snaps]

    temps = [x["temp"] for x in items]
    hums  = [x["humidity"] for x in items]
    stats = {
        "temp": {"min": min(temps), "max": max(temps), "avg": sum(temps)/len(temps)},
        "humidity": {"min": min(hums), "max": max(hums), "avg": sum(hums)/len(hums)},
    }
    return JsonResponse({
        "city": {"query": city_obj.query, "name": city_obj.name, "country": city_obj.country},
        "count": len(items),
        "items": items,
        "stats": stats,
    })
