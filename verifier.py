import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup



# ------------------------------------
# TRUSTED ORGANIZATION DOMAINS
# ------------------------------------

TRUSTED_DOMAINS = [

    "google.com",
    "microsoft.com",
    "ibm.com",
    "un.org",
    "worldbank.org",
    "afdb.org",
    "mastercardfoundation.org",
    "nssfug.org",
    "gov",
    "edu"

]



# ------------------------------------
# BLOCKED DOMAINS
# ------------------------------------

BLOCKED_DOMAINS = [

    "medium.com",
    "linkedin.com",
    "facebook.com",
    "reddit.com",
    "wordpress.com",
    "blogspot.com",
    "scholarshipportal.com",
    "opportunitiesforafricans.com"

]



# ------------------------------------
# CHECK DOMAIN
# ------------------------------------

def check_domain(url):

    domain = urlparse(
        url
    ).netloc.lower()


    for blocked in BLOCKED_DOMAINS:

        if blocked in domain:

            return False



    return True



# ------------------------------------
# CHECK HTTPS
# ------------------------------------

def check_security(url):

    return url.startswith(
        "https://"
    )



# ------------------------------------
# CHECK PAGE CONTENT
# ------------------------------------

def check_application_page(url):

    keywords = [

        "apply",
        "application",
        "register",
        "submit",
        "eligibility",
        "deadline",
        "requirements"

    ]


    try:

        response = requests.get(

            url,

            timeout=10

        )


        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )


        text = soup.get_text().lower()



        matches = 0


        for word in keywords:

            if word in text:

                matches += 1



        return matches >= 2



    except:

        return False



# ------------------------------------
# VERIFICATION SCORE
# ------------------------------------

def verify_link(url):

    score = 0


    reasons = []



    # Domain check

    if check_domain(url):

        score += 30

        reasons.append(
            "Domain accepted"
        )

    else:

        reasons.append(
            "Suspicious domain"
        )



    # HTTPS

    if check_security(url):

        score += 20

        reasons.append(
            "Secure HTTPS connection"
        )



    # Page content

    if check_application_page(url):

        score += 50

        reasons.append(
            "Application page detected"
        )



    if score >= 70:

        status = "Verified Official Portal"


    elif score >= 40:

        status = "Needs Review"


    else:

        status = "Rejected"



    return {

        "Verification Score":

        score,


        "Status":

        status,


        "Reasons":

        ", ".join(reasons)

    }



# ------------------------------------
# TEST
# ------------------------------------

if __name__ == "__main__":


    test_url = (

        "https://careers.microsoft.com/"

    )


    result = verify_link(
        test_url
    )


    print(result)
