import hashlib
import hmac
import subprocess
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def verify_signature(request):
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    signature = request.headers.get('X-Hub-Signature-256', '')
    body = request.body
    expected = 'sha256=' + hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


@csrf_exempt
@require_POST
def github_webhook(request):
    if not verify_signature(request):
        logger.warning("Signature xato!")
        return HttpResponseForbidden("Forbidden")

    try:
        result = subprocess.run(
            ['bash', '/home/loceats1/loyha3/loyha/deploy.sh'],
            capture_output=True,
            text=True,
            timeout=120
        )
        # Logga yozamiz
        with open('/home/loceats1/loyha3/loyha/deploy.log', 'a') as f:
            f.write(f"\n=== STDOUT ===\n{result.stdout}")
            f.write(f"\n=== STDERR ===\n{result.stderr}")
            f.write(f"\n=== RETURN CODE: {result.returncode} ===\n")

        if result.returncode != 0:
            return HttpResponse(result.stderr, status=500)
    except Exception as e:
        with open('/home/loceats1/loyha3/loyha/deploy.log', 'a') as f:
            f.write(f"\n=== EXCEPTION: {str(e)} ===\n")
        return HttpResponse(str(e), status=500)

    return HttpResponse("OK")