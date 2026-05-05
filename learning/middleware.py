import re
import json
import threading
import urllib.request

from django.utils import timezone

from .models import UserPresence

# ── Cache géo : {ip → {lat, lng, city, country, country_code, ts}} ────────────
_GEO_CACHE: dict = {}
_GEO_LOCK = threading.Lock()
_GEO_TTL = 3600  # secondes entre 2 rafraîchissements de la même IP


def _detect_device(ua: str) -> str:
    """Détecte mobile / tablet / desktop depuis le User-Agent."""
    ua = ua.lower()
    if 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    if re.search(r'mobile|android|iphone|ipod|blackberry|opera mini|windows phone', ua):
        return 'mobile'
    return 'desktop'


def _fetch_geo(ip: str) -> dict:
    """
    Retourne {'lat': ..., 'lng': ..., 'city': ..., 'country': ..., 'country_code': ...}
    depuis ip-api.com (API publique, gratuite, 100 req/min).
    Retourne {} pour les IPs locales ou en cas d'erreur.
    """
    if not ip or ip in ('127.0.0.1', '::1', 'localhost'):
        return {}
    parts = ip.split('.')
    if len(parts) == 4:
        try:
            a, b = int(parts[0]), int(parts[1])
            if a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168):
                return {}
        except ValueError:
            pass

    # Vérifie le cache
    now = timezone.now().timestamp()
    with _GEO_LOCK:
        cached = _GEO_CACHE.get(ip)
        if cached and (now - cached.get('ts', 0)) < _GEO_TTL:
            return cached

    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,lat,lon,city,country,countryCode'
        req = urllib.request.Request(url, headers={'User-Agent': 'PROMET/1.0'})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
        if data.get('status') == 'success':
            result = {
                'lat': data.get('lat'),
                'lng': data.get('lon'),
                'city': data.get('city', ''),
                'country': data.get('country', ''),
                'country_code': data.get('countryCode', ''),
                'ts': now,
            }
            with _GEO_LOCK:
                _GEO_CACHE[ip] = result
            return result
    except Exception:
        pass
    return {}


class TrackUserPresenceMiddleware:
    """Enregistre la presence des utilisateurs authentifies (page + dernier passage + geo + device)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated:
            return response

        path = request.path or '/'
        if path.startswith('/static/') or path.startswith('/media/'):
            return response

        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = xff.split(',')[0].strip() if xff else (request.META.get('REMOTE_ADDR', '') or '')

        ua = request.META.get('HTTP_USER_AGENT', '')
        device = _detect_device(ua)

        geo = _fetch_geo(ip)

        defaults = {
            'last_seen': timezone.now(),
            'current_path': path[:255],
            'ip_address': ip[:64],
            'device_type': device,
        }
        if geo:
            defaults.update({
                'latitude': geo.get('lat'),
                'longitude': geo.get('lng'),
                'city': geo.get('city', '')[:100],
                'country': geo.get('country', '')[:100],
                'country_code': geo.get('country_code', '')[:4],
            })

        UserPresence.objects.update_or_create(
            utilisateur=request.user,
            defaults=defaults,
        )

        return response

