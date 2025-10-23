import firebase_admin
from firebase_admin import credentials, messaging
import os, json
from django.conf import settings
from notifications.models import StaffFCMToken
from hooks.prettyprint import pretty_print_json
from hooks.cache_helpers import get_cached_response, set_cached_response

def get_user_and_device(data, token_value):
    """
    Returns (name, deviceID) for the given token_value.
    Works for both:
    - a single dict
    - a list of dicts
    """

    # ✅ Case 1: Single dict
    if isinstance(data, dict):
        if data.get("token") == token_value:
            return (
                data.get("name"),
                data.get("mobile"),
                data.get("browser"),
                data.get("summary"),
            )
        return None

    # ✅ Case 2: List of dicts
    elif isinstance(data, list):
        for item in data:
            if item.get("token") == token_value:
                return (
                    item.get("name"),
                    item.get("mobile"),
                    item.get("browser"),
                    item.get("summary"),
                )
        return None

    else:
        raise TypeError("Data must be a dict or a list of dicts")

def get_tokens():
    """
    Fetches all staff FCM tokens from the database.
    Returns a list of dictionaries: [{username: token}, ...]
    """

    cache_name = 'staff_fcm_tokens'

    # Check cache first
    cached_data, cache_key, tracked_keys = get_cached_response(
            cache_name, request=None, key_suffix=f"list",
            no_page_size=True,
        )
    if cached_data:
        return cached_data

    tokens = []
    staff_tokens = StaffFCMToken.objects.select_related('user').all()
    for staff in staff_tokens:
        if staff.fcm_token:
            print(f"Found token for {staff.user.first_name}: {staff.fcm_token[:10]}...")
            tokens.append({
                "name": staff.user.first_name,
                "token": staff.fcm_token,
                "deviceID": staff.device_id,
                "mobile": staff.mobile,
                "browser": staff.browserName,
                "summary": staff.readableSummary,
                })
        else:
            print(f"No token found for {staff.user.first_name} (user ID: {staff.user.id})")

    # Cache the new data
    set_cached_response(
        cache_name,
        cache_key,
        tracked_keys,
        tokens,
    )
    return tokens


# # usage:

# data = {
#     "title": "New Order Received 🚀",
#     "body": "A user just placed a new order.",
# }
# send_fcm_notification(data) # to a single device
# send_fcm_notification_bulk(data) # to multiple devices


# Initialize Firebase once (usually in settings.py or a utils module)
if not firebase_admin._apps:
    print("Initializing Firebase Admin SDK")
    cred = credentials.Certificate(
        os.path.join(settings.BASE_DIR, "notifications", "firebase_setup", "online-store-staff-firebase-adminsdk.json")  # adjust path if needed
    )
    firebase_admin.initialize_app(cred)

def send_fcm_notification(data):
    """
    Sends a push notification to a specific device using FCM v1.
    tokens = {uname: token}
    """

    token = get_tokens()
    print(f"All tokens from DB")
    pretty_print_json(token)

    if not token or len(token) == 0:
        print("No tokens provided.")
        return

    just_token = token[0]["token"]  # just take the first token for single send
    print(f"Token sent down: {just_token[:10]}")

    print(f"Sending notification with token: {just_token[:10]}")
    print(f"Sending notification to: {token[0]['name']}")
    print(f"Sending to: {token[0]['summary']}")

    message = messaging.Message(
        notification=messaging.Notification(
            title=data["title"],
            body=data["body"],
        ),
        token=just_token,  # this is the user's device FCM token from frontend
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon="/famepropertiesng_repo/logo192.png",  # optional
                # click_action="/"  # where the user should go when they click
            )
        )
    )

    try:
        response = messaging.send(message)
        # print("Notification sent successfully:", response)
        name, device, browser, summary = get_user_and_device(token, just_token)
        print(f"✅ Successfully sent to {name} on {device} device → {response}")
        return response
    except Exception as e:
        print("🚨 Error sending notification:", e)
        return None

def send_fcm_notification_bulk(data):
    """
    Sends a push notification to multiple devices using FCM.
    Each token represents a device/browser belonging to a staff member.
    tokens = [{uname: token}]
    """

    tokens = get_tokens()
    print(f"All tokens from DB")
    pretty_print_json(tokens)

    if not tokens or len(tokens) == 0:
        print("No tokens provided.")
        return

    just_tokens = [t["token"] for t in tokens]
    print(f"Tokens sent down: {just_tokens}")
    print('data to sent:')
    pretty_print_json(data)
    # 🔹 Ensure just_tokens is a list (even if a single string is passed)
    # if isinstance(just_tokens, str):
    #     just_tokens = [just_tokens]

    print(f"Sending notification to {len(just_tokens)} device(s)...")

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=data["title"],
            body=data["body"],
        ),
        tokens=just_tokens,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon="/famepropertiesng_repo/logo192.png",
            ),
            data={  # ✅ put custom fields here
                "id": str(data.get("id")),
                "status": data.get("status", "pending"),
                "shipping_status": data.get("shipping_status"), # opti
                "user": json.dumps(data["user"]),
                "amount": json.dumps(data["amount"]),
                "url": "/",  # optional: for click actions
            },
        ),
    )

    try:
        # 🔹 Send all messages in a single batch (up to 500 per call)
        # response = messaging.send_all(messages)

        response = messaging.send_each_for_multicast(message)

        # print(f"✅ Successfully sent to {response.success_count} device(s)")
        # print(f"❌ Failed to send to {response.failure_count} device(s)")

        # Analyze results
        success_count = sum(1 for r in response.responses if r.success)
        failed_tokens = [
            just_tokens[i]
            for i, r in enumerate(response.responses)
            if not r.success
        ]

        print(f"✅ Successfully sent to {success_count} device(s)")
        # if failed_tokens:
        #     print(f"❌ Failed tokens ({len(failed_tokens)}): {failed_tokens}")
        for i, r in enumerate(response.responses):
            name, device, browser, summary = get_user_and_device(tokens, just_tokens[i])
            if not r.success:
                print(f" - ❌ User: {name}, Device: {device}, device-summary: {summary}, Token: {just_tokens[i][:10]}, Error: {r.exception}")
            else:
                print(f" - ✅ User: {name}, Device: {device}, device-summary: {summary}, Token: {just_tokens[i][:10]}, Message ID: {r.message_id}")

        return {
            "success_count": success_count,
            "failure_count": len(failed_tokens),
            "failed_tokens": failed_tokens,
        }

    except Exception as e:
        print("🚨 Error sending notifications:", e)
        return {
            "success_count": 0,
            "failure_count": len(just_tokens),
            "failed_tokens": just_tokens,
            "error": str(e),
        }

def send_warmup_notification(token):
    """Send a silent notification to verify token registration with FCM."""
    try:
        print(f"Sending warm-up ping to token: {token[:15]}...")
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(
                title="token_warmup",
                body="ping",  # you can name anything here
            ),
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    silent=True,  # <--- important (no visible popup)
                    require_interaction=False,
                )
            ),
        )
        response = messaging.send(message)
        print(f"✅ Warm-up sent successfully for token: {token[:15]}... → {response}")
    except Exception as e:
        print(f"⚠️ Warm-up failed for {token[:15]}... → {e}")

def test_noti(idx=None):
    print(f'index received: {idx}')
    if not idx and (idx < 0 or idx > 2):
        print("Please provide a valid index (0 - 9).")
        return

    print(f"Testing notification for index: {idx}")
    data = [
        {
            "id": "202510161328498423527f4b57fdd0",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "John Doe just placed a new order worth ₦45,500.",
            "status": "pending",
            "shipping_status": "processing",
            "user": {
                "id": "12",
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe@example.com",
                "phone_code": "+234",
                "mobile_no": "08012345678"
            },
            "amount": {
                "subtotal": "45000.00",
                "shipping_fee": "500.00",
                "total": "45500.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd1",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Chioma Okafor just placed a new order worth ₦32,800.",
            "status": "pending",
            "shipping_status": "delivered",
            "user": {
                "id": "15",
                "first_name": "chichiamakankechiChioma",
                "last_name": "Okafor",
                "email": "chioma.okafor@example.com",
                "phone_code": "+234",
                "mobile_no": "08122334455"
            },
            "amount": {
                "subtotal": "32000.00",
                "shipping_fee": "800.00",
                "total": "32800.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd2",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Emeka Uche just placed a new order worth ₦27,000.",
            "status": "failed",
            "shipping_status": "shipped",
            "user": {
                "id": "18",
                "first_name": "Emeka",
                "last_name": "Uche",
                "email": "emeka.uche@example.com",
                "phone_code": "+234",
                "mobile_no": "09055667788"
            },
            "amount": {
                "subtotal": "27000.00",
                "shipping_fee": "0.00",
                "total": "27000.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd3",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Amina Bello just placed a new order worth ₦19,750.",
            "status": "pending",
            "shipping_status": "processing",
            "user": {
                "id": "21",
                "first_name": "Amina",
                "last_name": "Bello",
                "email": "amina.bello@example.com",
                "phone_code": "+234",
                "mobile_no": "07099887766"
            },
            "amount": {
                "subtotal": "19500.00",
                "shipping_fee": "250.00",
                "total": "19750.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd4",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Tunde Balogun just placed a new order worth ₦52,600.",
            "status": "pending",
            "shipping_status": "delivered",
            "user": {
                "id": "25",
                "first_name": "Tunde",
                "last_name": "Balogun",
                "email": "tunde.balogun@example.com",
                "phone_code": "+234",
                "mobile_no": "08044556677"
            },
            "amount": {
                "subtotal": "52000.00",
                "shipping_fee": "600.00",
                "total": "52600.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd5",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Adaeze Nwosu just placed a new order worth ₦61,200.",
            "status": "pending",
            "shipping_status": "processing",
            "user": {
                "id": "29",
                "first_name": "Adaeze",
                "last_name": "Nwosu",
                "email": "adaeze.nwosu@example.com",
                "phone_code": "+234",
                "mobile_no": "08133445566"
            },
            "amount": {
                "subtotal": "60000.00",
                "shipping_fee": "1200.00",
                "total": "61200.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd6",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Ibrahim Musa just placed a new order worth ₦14,500.",
            "status": "pending",
            "shipping_status": "processing",
            "user": {
                "id": "33",
                "first_name": "Ibrahim",
                "last_name": "Musa",
                "email": "ibrahim.musa@example.com",
                "phone_code": "+234",
                "mobile_no": "07022334455"
            },
            "amount": {
                "subtotal": "14000.00",
                "shipping_fee": "500.00",
                "total": "14500.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd7",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Ngozi Eze just placed a new order worth ₦38,900.",
            "status": "pending",
            "shipping_status": "shipped",
            "user": {
                "id": "37",
                "first_name": "Ngozi",
                "last_name": "Eze",
                "email": "ngozi.eze@example.com",
                "phone_code": "+234",
                "mobile_no": "08077889900"
            },
            "amount": {
                "subtotal": "38000.00",
                "shipping_fee": "900.00",
                "total": "38900.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd8",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Samuel Adeyemi just placed a new order worth ₦23,000.",
            "status": "failed",
            "shipping_status": "cancelled",
            "user": {
                "id": "40",
                "first_name": "Samuel",
                "last_name": "Adeyemi",
                "email": "samuel.adeyemi@example.com",
                "phone_code": "+234",
                "mobile_no": "08155667788"
            },
            "amount": {
                "subtotal": "23000.00",
                "shipping_fee": "0.00",
                "total": "23000.00"
            },
        },
        {
            "id": "202510161328498423527f4b57fdd9",
            "title": "New Order Placed - 7f4b57fdd0",
            "body": "Grace Alabi just placed a new order worth ₦41,400.",
            "status": "pending",
            "shipping_status": "processing",
            "user": {
                "id": "43",
                "first_name": "Grace",
                "last_name": "Alabi",
                "email": "grace.alabi@example.com",
                "phone_code": "+234",
                "mobile_no": "08066778899"
            },
            "amount": {
                "subtotal": "41000.00",
                "shipping_fee": "400.00",
                "total": "41400.00"
            },
        },
    ]
    send_fcm_notification_bulk(data[idx])


        # {
        #     "id": "FPX20251019-001", # use checkout.checkoutID here
        #     "type": "order_update",
        #     "title": "New Order Placed - FPX20251019-001",
        #     "body": "John Doe just placed a new order worth ₦45,500.",
        #     "checkoutID": "CHK_14E3A91B9C2D4",
        #     "status": "pending", #use checkout.payment_status here
        #     "shipping_status": "processing", #use checkout.shipping_status here
        #     "user": {
        #         "id": "12",
        #         "name": "John Doe",
        #         "email": "johndoe@example.com",
        #         "phone_code": "+234",
        #         "mobile_no": "08012345678"
        #     },
        #     "amount": {
        #         "subtotal": "45000.00",
        #         "shipping_fee": "500.00",
        #         "total": "45500.00"
        #     },
        #     "delivery": {
        #         "address": "12 Admiralty Way, Lekki Phase 1",
        #         "lga": "Eti-Osa",
        #         "subArea": "Lekki Phase 1",
        #         "city": "Lagos",
        #         "state": "Lagos",
        #         "country": "Nigeria"
        #     },
        #     "action_url": "/admin/orders/CHK_14E3A91B9C2D4",
        # },
        # {
        #     "id": "FPX20251019-001", # use checkout.checkoutID here
        #     "title": "New Order Placed - FPX20251019-001",
        #     "body": "John Doe just placed a new order worth ₦45,500.",
        #     "status": "pending", # use checkout.payment_status here
        #     "shipping_status": "processing", # use checkout.shipping_status here
        #     "user": {
        #         "id": "12",
        #         "first_name": "John",
        #         "last_name": "Doe",
        #         "email": "johndoe@example.com",
        #         "phone_code": "+234",
        #         "mobile_no": "08012345678"
        #     },
        #     "amount": {
        #         "subtotal": "45000.00",
        #         "shipping_fee": "500.00",
        #         "total": "45500.00"
        #     },
        # }